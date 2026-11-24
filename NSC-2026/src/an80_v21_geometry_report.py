"""Session 34, Task 4: decide on the geometry arms from one prediction artifact.

Reuses the population primitives repaired in `an77` -- the primary frame is B1+B2 with unique
timestamps, the matched calendar is selected FROM that frame, direction and the bootstrap are
computed on it, and the best-day guard pools SSE over n. Copying the session-33 versions of those
would reintroduce four bugs that were just removed.

**The comparison structure.** `C0` is the shipped incumbent and the promotion gate: an arm has to
beat what actually ships. `C1` is the same L2 objective through the geometry arms' own plumbing,
so `G - C1` is what isolates the objective from the feature-draw difference documented in
`v21_geometry_boosting`. Both are reported for every arm; the gate is against C0.

**The surrogate check.** The objective minimises `||B r||^2`, which is not the final RH loss --
the cross-term `2 e0^T B r` is omitted. If an arm lowers `||B r||^2` on the holdout and still
loses on RH, the decomposition says whether the cross-term is where it went. That is a real
result about the surrogate, not a reason to add a correction on top of it.

    .venv/Scripts/python.exe src/an80_v21_geometry_report.py
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
import final_pipeline as fp
import an47_v21_forward_benchmark as a47
import an59_v21_candidate_contract as c
import an77_v21_shape_report as rep

OUT = ROOT / 'outputs' / 'audit_v21_s34' / 'geometry'
PREDS = OUT / 'preds_geometry.pkl'
ARMS_CSV = OUT / 'geometry_arms.csv'
GATE = 'C0'
ISOLATING = 'C1'
PRIMARY = rep.PRIMARY
SEVEN = ('H1_last7d', 'H2_last14d', 'H3_last21d')

# The engineering bar, unchanged from the shape round, plus the two guards session 33 added.
BAR = dict(pooled_gain=0.02, b3_tolerance=0.05, worst_h_tolerance=0.02, h1_tolerance=0.0,
           g2_over_g1=0.01)
# Public MSE reduction needed to move 2.86595 to 2.60, quoted so a local gain is not mistaken
# for it. The two are not mappable onto one another and the report says so.
PUBLIC_TARGET = dict(incumbent=2.86595, target=2.60,
                     mse_reduction_needed=1.0 - (2.60 ** 2) / (2.86595 ** 2))


def joined(P, arm, ref=GATE):
    a = P.loc[P.arm == ref].sort_values(['block', 'datetime']).reset_index(drop=True)
    b = P.loc[P.arm == arm].sort_values(['block', 'datetime']).reset_index(drop=True)
    assert len(a) and len(b), 'missing rows for %s or %s' % (arm, ref)
    k = a.merge(b[['block', 'datetime', 'z']], on=['block', 'datetime'], suffixes=('', '_q'),
                how='outer', validate='one_to_one', indicator=True)
    assert k['_merge'].eq('both').all(), '%s and %s differ in scored rows' % (arm, ref)
    k = k.drop(columns='_merge').rename(columns={'z': 'z_new', 'z_q': 'z_new_q'})
    return k.loc[k.score].sort_values(['block', 'datetime']).reset_index(drop=True)


def primary(k):
    q = k.loc[k.block.isin(PRIMARY)].copy()
    assert not q.datetime.duplicated().any(), 'primary blocks must not share a timestamp'
    return q.sort_values('datetime').reset_index(drop=True)


def evaluate(P, arm, ref=GATE):
    k = joined(P, arm, ref)
    prim = primary(k)
    k7 = k.loc[k.family == '7d']
    per = {b: (fp.rmse(d.y, d.z_new), fp.rmse(d.y, d.z_new_q)) for b, d in k.groupby('block')}
    day = rep.daily(prim)
    guard, best_day, guard_n = rep.guard_excluding_best_day(prim, day)
    direction = c.direction(prim.y.to_numpy(), prim.z_new.to_numpy(), prim.z_new_q.to_numpy())
    want = pd.DatetimeIndex(k7.datetime).unique()
    m = prim.loc[prim.datetime.isin(want).to_numpy()]

    res = dict(arm=arm, reference=ref, population='primary_B1_B2', n_primary=len(prim),
               pooled_base=rep.pooled_rmse(prim, True), pooled_cand=rep.pooled_rmse(prim, False),
               matched_n=len(m), matched_base=fp.rmse(m.y, m.z_new),
               matched_cand=fp.rmse(m.y, m.z_new_q),
               pooled7_base=fp.rmse(k7.y, k7.z_new), pooled7_cand=fp.rmse(k7.y, k7.z_new_q),
               best_day=best_day, guard_n=guard_n, d_mse_excluding_best_day=guard,
               days=int(len(day)), days_improved=int((day.d_sse < 0).sum()),
               **{'d_' + b: v[1] - v[0] for b, v in per.items()},
               **{'direction_' + kk: v for kk, v in direction.items()})
    res['d_pooled'] = res['pooled_cand'] - res['pooled_base']
    res['d_mse_pooled'] = res['pooled_cand'] ** 2 - res['pooled_base'] ** 2
    res['d_matched'] = res['matched_cand'] - res['matched_base']
    res['d_pooled7'] = res['pooled7_cand'] - res['pooled7_base']
    res['local_mse_reduction'] = -res['d_mse_pooled'] / res['pooled_base'] ** 2
    assert abs(res['direction_d_mse'] - res['d_mse_pooled']) < 1e-9, \
        'direction and pooled disagree: the populations have drifted apart'
    for days in (3, 7):
        for kk, v in rep.bootstrap(prim, days).items():
            res['boot%dd_%s' % (days, kk)] = v
    worst_h = max(res['d_' + b] for b in SEVEN if ('d_' + b) in res)
    res['worst_h'] = worst_h
    res['bar_pooled'] = bool(res['d_pooled'] <= -BAR['pooled_gain'])
    res['bar_primary_blocks'] = bool(all(res['d_' + b] < 0 for b in PRIMARY))
    res['bar_b3'] = bool(res.get('d_B3_shift7d', 0.0) <= BAR['b3_tolerance'])
    res['bar_matched'] = bool(res['d_matched'] <= 0)
    res['bar_pooled7'] = bool(res['d_pooled7'] <= 0)
    res['bar_worst_h'] = bool(worst_h <= BAR['worst_h_tolerance'])
    res['guard_h1'] = bool(res.get('d_H1_last7d', 0.0) <= BAR['h1_tolerance'])
    res['guard_best_day'] = bool(res['d_mse_excluding_best_day'] < 0)
    res['promotable'] = bool(res['bar_pooled'] and res['bar_primary_blocks'] and res['bar_b3']
                             and res['bar_matched'] and res['bar_pooled7'] and res['bar_worst_h'])
    res['strong'] = bool(res['promotable'] and res['guard_h1'] and res['guard_best_day']
                         and res['boot3d_hi'] < 0 and res['boot7d_hi'] < 0)
    return res


def choose(rows):
    """G1 is the simpler arm and wins ties. Beating G2 but losing to C0 is still a failure."""
    passing = [r for r in rows if r['promotable']]
    strong = [r for r in rows if r['strong']]
    if not passing:
        return 'keep_v21', None, ('no geometry arm clears the engineering bar against the shipped '
                                  'incumbent; the solver-geometry objective does not replace v21 '
                                  'this round')
    g1 = next((r for r in passing if r['arm'] == 'G1'), None)
    g2 = next((r for r in passing if r['arm'] == 'G2'), None)
    if g1 is not None and g2 is not None:
        better = (g1['pooled_cand'] - g2['pooled_cand']) >= BAR['g2_over_g1']
        safe = all(g2['d_' + b] <= g1['d_' + b] for b in list(PRIMARY) + ['H1_last7d']
                   if ('d_' + b) in g2 and ('d_' + b) in g1)
        chosen = g2 if (better and safe) else g1
        why = ('G2 beats G1 by >= %.2f pooled without hurting G1 on B1/B2/H1' % BAR['g2_over_g1']
               if chosen is g2 else 'G1 is the simpler arm and G2 does not buy the coupling')
    else:
        chosen = passing[0]
        why = 'the only arm clearing the bar'
    verdict = 'production_check_candidate' if chosen in strong else 'weak_candidate'
    if chosen not in strong:
        why += ('; the bootstrap interval crosses zero or a stress guard disagrees, so it is not '
                'a strong recommendation')
    return verdict, chosen, why


def surrogate_table(A):
    """Did the surrogate move, and did RH follow? The decomposition must reconstruct the MSE."""
    out = []
    for _i, r in A.iterrows():
        rec = dict(arm=r.arm, block=r.block, n=int(r.n), rmse=r.rmse,
                   inc_rmse_h1=r.inc_rmse_h1, inc_rmse_h4=r.inc_rmse_h4,
                   Br_mse=r.Br_mse, cross=r.cross, e0_mse=r.e0_mse,
                   pre_clip_mse=r.pre_clip_mse,
                   sum_check=r.e0_mse + r.cross + r.Br_mse - r.pre_clip_mse,
                   cancel_rmse=r.cancel_rmse)
        out.append(rec)
    T = pd.DataFrame(out)
    assert T.sum_check.abs().max() < 1e-8, 'the loss decomposition does not sum to the MSE'
    return T


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--preds', default=str(PREDS))
    ap.add_argument('--arms-csv', default=str(ARMS_CSV))
    a = ap.parse_args()
    P = pd.read_pickle(a.preds)
    A = pd.read_csv(a.arms_csv)
    arms = [x for x in P.arm.unique() if x != GATE]

    rows, iso = [], []
    for arm in arms:
        rows.append(evaluate(P, arm, GATE))
        if arm not in (GATE, ISOLATING) and ISOLATING in set(P.arm):
            iso.append(evaluate(P, arm, ISOLATING))
    R, I = pd.DataFrame(rows), pd.DataFrame(iso)
    T = surrogate_table(A)
    R.to_csv(OUT / 'metrics.csv', index=False)
    if len(I):
        I.to_csv(OUT / 'metrics_vs_c1.csv', index=False)
    T.to_csv(OUT / 'surrogate.csv', index=False)

    cand = [r for r in rows if r['arm'] in ('G1', 'G2')]
    verdict, chosen, why = choose(cand)
    surrogate_note = []
    for arm in ('G1', 'G2'):
        s = T.loc[T.arm == arm]
        b = T.loc[T.arm == GATE]
        if len(s) and len(b):
            dBr = float(s.set_index('block').Br_mse.sub(b.set_index('block').Br_mse).mean())
            dX = float(s.set_index('block').cross.sub(b.set_index('block').cross).mean())
            row = next((r for r in cand if r['arm'] == arm), None)
            if row is not None and dBr < 0 and row['d_pooled'] > 0:
                surrogate_note.append(
                    '%s lowered the surrogate ||Br||^2/n by %.5f on average and still lost %.5f '
                    'RMSE; the omitted cross-term moved %+.5f. The surrogate is the wrong '
                    'objective here, and this closes it for this round rather than inviting a '
                    'correction on top of it.' % (arm, -dBr, row['d_pooled'], dX))
    c.write_json(OUT / 'decision.json', dict(
        created=pd.Timestamp.now().isoformat(timespec='seconds'),
        verdict=verdict, chosen=None if chosen is None else chosen['arm'], reason=why,
        bar=BAR, gate=GATE, objective_isolating=ISOLATING,
        public_context=PUBLIC_TARGET,
        surrogate_findings=surrogate_note,
        arms=rows, arms_vs_c1=iso,
        source=str(Path(a.preds)), source_md5=a47.md5(a.preds)))

    cols = ['arm', 'pooled_base', 'pooled_cand', 'd_pooled', 'd_matched', 'd_pooled7',
            'worst_h', 'local_mse_reduction', 'promotable', 'strong']
    print(R[cols].to_string(index=False))
    if len(I):
        print('\nagainst C1 (objective isolated):')
        print(I[['arm', 'd_pooled', 'd_matched', 'd_pooled7', 'worst_h']].to_string(index=False))
    print('\nsurrogate vs final:')
    print(T[['arm', 'block', 'rmse', 'Br_mse', 'cross', 'e0_mse']].to_string(index=False))
    for n in surrogate_note:
        print('\nNOTE: ' + n)
    print('\nverdict: %s (%s)\n  %s' % (verdict, chosen and chosen['arm'], why))
    print('\nA %.3f%% local primary MSE reduction would be needed to reach the pooled bar; '
          'moving public 2.86595 to 2.60 needs %.3f%% of PUBLIC MSE. These are different '
          'populations and do not map onto one another.'
          % (100 * (1 - ((R.pooled_base.iloc[0] - BAR['pooled_gain']) ** 2)
                    / R.pooled_base.iloc[0] ** 2),
             100 * PUBLIC_TARGET['mse_reduction_needed']))
    print('wrote %s' % OUT)


if __name__ == '__main__':
    main()
