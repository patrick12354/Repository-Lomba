"""Session 36, Task 3: decide on the level-hybrid arms from one prediction artifact.

Reuses the population primitives repaired in `an77` -- the primary frame is B1+B2 with unique
timestamps, the matched calendar is selected FROM that frame, and the best-day guard drops one day
globally and pools SSE/n. Copying the session-33 versions would reintroduce four fixed bugs.

**The comparison that decides the hypothesis.** `C0` is the promotion gate: an arm must beat what
ships. `L0` is the control that separates the two-stage STRUCTURE from smooth NONLINEARITY -- S1
and S2 must beat L0 on the final output, or the spline is not what helped. An arm that only beats
C0 while losing to L0 has not supported the hypothesis this round was built to test, and `L0` is
not promoted in its place: it was the control, not a candidate.

    .venv/Scripts/python.exe src/an85_v21_level_hybrid_report.py
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
import v21_episode_anchors as ea

OUT = ROOT / 'outputs' / 'audit_v21_s36' / 'hybrid'
PREDS = OUT / 'preds_hybrid.pkl'
GATE = 'C0'
CONTROL = 'L0'
PRIMARY = rep.PRIMARY
SEVEN = ('H1_last7d', 'H2_last14d', 'H3_last21d')

BAR = dict(pooled_gain=0.02, b3_tolerance=0.05, h_tolerance=0.02, h1_tolerance=0.0,
           s2_over_s1=0.01, breakthrough_mse_fraction=0.05)
C0_POOLED = 5.535893870


def joined(P, arm, ref=GATE):
    a = P.loc[(P.arm == ref) & P.score].sort_values(['block', 'datetime']).reset_index(drop=True)
    b = P.loc[(P.arm == arm) & P.score].sort_values(['block', 'datetime']).reset_index(drop=True)
    assert len(a) and len(b), 'missing rows for %s or %s' % (arm, ref)
    k = a.merge(b[['block', 'datetime', 'z', 'q', 'g']], on=['block', 'datetime'],
                suffixes=('', '_q'), how='outer', validate='one_to_one', indicator=True)
    assert k['_merge'].eq('both').all(), '%s and %s differ in scored rows' % (arm, ref)
    return (k.drop(columns='_merge').rename(columns={'z': 'z_new', 'z_q': 'z_new_q'})
            .sort_values(['block', 'datetime']).reset_index(drop=True))


def primary(k):
    q = k.loc[k.block.isin(PRIMARY)].copy()
    assert not q.datetime.duplicated().any(), 'primary blocks must not share a timestamp'
    return q.sort_values('datetime').reset_index(drop=True)


def evaluate(P, arm, ref=GATE):
    k = joined(P, arm, ref)
    prim = primary(k)
    k7 = k.loc[k.family == '7d']
    per = {b: (fp.rmse(d.y, d.z_new), fp.rmse(d.y, d.z_new_q)) for b, d in k.groupby('block')}
    guard = ea.global_best_day_guard(prim.y, prim.z_new, prim.z_new_q, prim.datetime)
    direction = c.direction(prim.y.to_numpy(), prim.z_new.to_numpy(), prim.z_new_q.to_numpy())
    want = pd.DatetimeIndex(k7.datetime).unique()
    m = prim.loc[prim.datetime.isin(want).to_numpy()]

    res = dict(arm=arm, reference=ref, population='primary_B1_B2', n_primary=len(prim),
               pooled_base=rep.pooled_rmse(prim, True), pooled_cand=rep.pooled_rmse(prim, False),
               matched_n=len(m), matched_base=fp.rmse(m.y, m.z_new),
               matched_cand=fp.rmse(m.y, m.z_new_q),
               pooled7_base=fp.rmse(k7.y, k7.z_new), pooled7_cand=fp.rmse(k7.y, k7.z_new_q),
               rmse_member_cand=fp.rmse(prim.y, prim.q_q), rmse_member_base=fp.rmse(prim.y, prim.q),
               rmse_g_cand=(fp.rmse(prim.y, prim.g_q) if np.isfinite(prim.g_q).all() else np.nan),
               d_mse_excluding_best_day=guard['guard'], best_day=guard['dropped_day'],
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
    res['bar_h1'] = bool(res.get('d_H1_last7d', 0.0) <= BAR['h1_tolerance'])
    res['bar_worst_h'] = bool(worst_h <= BAR['h_tolerance'])
    res['guard_best_day'] = bool(res['d_mse_excluding_best_day'] < 0)
    res['promotable'] = bool(res['bar_pooled'] and res['bar_primary_blocks'] and res['bar_b3']
                             and res['bar_matched'] and res['bar_pooled7'] and res['bar_h1']
                             and res['bar_worst_h'] and res['guard_best_day'])
    res['breakthrough'] = bool(res['promotable'] and
                               res['local_mse_reduction'] >= BAR['breakthrough_mse_fraction'])
    return res


def choose(rows):
    """S1 is the candidate; S2 must buy its interactions; L0 is a control and is never promoted."""
    by = {r['arm']: r for r in rows}
    s1, s2, l0 = by.get('S1'), by.get('S2'), by.get('L0')
    passing = [r for r in (s1, s2) if r is not None and r['promotable']]
    if not passing:
        why = ('no spline arm clears the engineering bar against the shipped incumbent')
        if l0 is not None and l0['promotable']:
            why += ('; the L0 control DOES clear it, which is a result about two-stage structure '
                    'rather than about splines, and L0 is not promoted here because it was the '
                    'control for this round')
        return 'keep_v21', None, why
    # A spline arm must also beat the linear control, or the round has not shown what it tested.
    if l0 is not None:
        beats = [r for r in passing if r['pooled_cand'] < l0['pooled_cand']]
        if not beats:
            return ('keep_v21', None,
                    'the spline arms clear the bar against C0 but do not beat the L0 control, so '
                    'the smooth-nonlinearity hypothesis is not supported; promoting L0 instead '
                    'would be choosing a control after seeing the scores')
        passing = beats
    chosen = passing[0]
    if s1 is not None and s2 is not None and s1 in passing and s2 in passing:
        better = (s1['pooled_cand'] - s2['pooled_cand']) >= BAR['s2_over_s1']
        safe = all(s2['d_' + b] <= s1['d_' + b] for b in PRIMARY
                   if ('d_' + b) in s2 and ('d_' + b) in s1)
        chosen = s2 if (better and safe) else s1
    verdict = ('breakthrough_candidate' if chosen['breakthrough'] else
               'production_check_candidate')
    why = '%s clears every gate and beats the L0 control' % chosen['arm']
    return verdict, chosen, why


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--preds', default=str(PREDS))
    ap.add_argument('--out', default=str(OUT))
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    P = pd.read_pickle(a.preds)
    arms = [x for x in P.arm.unique() if x != GATE]

    rows = [evaluate(P, arm, GATE) for arm in arms]
    vs_l0 = [evaluate(P, arm, CONTROL) for arm in arms
             if arm != CONTROL and CONTROL in set(P.arm)]
    R, L = pd.DataFrame(rows), pd.DataFrame(vs_l0)
    R.to_csv(out / 'metrics.csv', index=False)
    if len(L):
        L.to_csv(out / 'metrics_vs_l0.csv', index=False)

    base = next((r for r in rows if r['arm'] == arms[0]), None)
    assert base is None or abs(base['pooled_base'] - C0_POOLED) < 1e-6, \
        'the control pooled RMSE is not the frozen 5.535893870'

    verdict, chosen, why = choose(rows)
    c.write_json(out / 'decision.json', dict(
        created=pd.Timestamp.now().isoformat(timespec='seconds'),
        verdict=verdict, chosen=None if chosen is None else chosen['arm'], reason=why,
        bar=BAR, gate=GATE, structure_control=CONTROL,
        populations=dict(primary='B1+B2 unique timestamps', sensitivity_15d='B3',
                         holdout_7d='H1+H2+H3'),
        arms=rows, arms_vs_l0=vs_l0,
        source=str(Path(a.preds)), source_md5=a47.md5(a.preds)))
    cols = ['arm', 'pooled_base', 'pooled_cand', 'd_pooled', 'd_matched', 'd_pooled7', 'worst_h',
            'rmse_member_cand', 'rmse_g_cand', 'local_mse_reduction', 'promotable']
    print(R[cols].to_string(index=False))
    if len(L):
        print('\nagainst the L0 control (isolating smooth nonlinearity):')
        print(L[['arm', 'd_pooled', 'd_matched', 'd_pooled7', 'worst_h']].to_string(index=False))
    print('\nverdict: %s (%s)\n  %s' % (verdict, chosen and chosen['arm'], why))
    print('wrote %s' % out)


if __name__ == '__main__':
    main()
