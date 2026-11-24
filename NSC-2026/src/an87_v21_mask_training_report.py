"""Session 37, Task 3: decide on the masking arm, against two references.

`C0` is the promotion gate -- an arm has to beat what ships. `D0` is the duplication control:
concatenating a frame with itself already changes a tree's binning, bagging and leaf minimums, so
`M1 - D0` is what isolates the change of sensor VIEW from the change of row count. An arm that
beats C0 while losing to D0 has not shown that masking did anything, and `D0` is never promoted in
its place -- it was the control.

Natural validation decides. The stress columns are reported separately, per seed, and never pooled
into the primary population: a synthetic corruption of the scored horizon is a diagnostic about
sensitivity, not a score. A model that moves less under stress is not thereby better -- a constant
predictor moves not at all -- so stress is only read alongside the natural result.

Population primitives come from the repaired `an77`: primary is B1+B2 on 1 440 unique timestamps,
matched is selected from that frame, and the best-day guard drops one day globally and pools
SSE/n.

    .venv/Scripts/python.exe src/an87_v21_mask_training_report.py
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

OUT = ROOT / 'outputs' / 'audit_v21_s37'
GATE = 'C0'
CONTROL = 'D0'
CANDIDATE = 'M1'
PRIMARY = rep.PRIMARY
SEVEN = ('H1_last7d', 'H2_last14d', 'H3_last21d')
BAR = dict(pooled_gain=0.02, b3_tolerance=0.05, h_tolerance=0.02, h1_tolerance=0.0,
           breakthrough_mse_fraction=0.05)
C0_POOLED = 5.535893870


def joined(P, arm, ref=GATE):
    a = P.loc[(P.arm == ref) & P.score].sort_values(['block', 'datetime']).reset_index(drop=True)
    b = P.loc[(P.arm == arm) & P.score].sort_values(['block', 'datetime']).reset_index(drop=True)
    assert len(a) and len(b), 'missing rows for %s or %s' % (arm, ref)
    k = a.merge(b[['block', 'datetime', 'z', 'q']], on=['block', 'datetime'],
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
               rmse_member_base=fp.rmse(prim.y, prim.q), rmse_member_cand=fp.rmse(prim.y, prim.q_q),
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


def choose(vs_c0, vs_d0):
    """M1 must clear the bar against C0 AND beat the D0 control. D0 is never promoted."""
    m = next((r for r in vs_c0 if r['arm'] == CANDIDATE), None)
    d = next((r for r in vs_c0 if r['arm'] == CONTROL), None)
    md = next((r for r in vs_d0 if r['arm'] == CANDIDATE), None)
    if m is None or not m['promotable']:
        why = 'M1 does not clear the engineering bar against the shipped incumbent'
        if d is not None and d['promotable']:
            why += ('; the D0 duplication control does, which would be a result about row '
                    'duplication rather than about masking, and D0 was the control')
        return 'keep_v21', None, why
    # Fail closed. The earlier version skipped this check when the D0 reference was absent, so a
    # run without the control could have promoted M1 on the strength of C0 alone -- the exact
    # confound the control exists to remove. A missing control is a reason to refuse, not to pass.
    if md is None:
        return ('keep_v21', None,
                'the D0 duplication control is missing, so the change of sensor view cannot be '
                'separated from the change of row count; refusing to promote without it')
    if md['d_pooled'] >= 0:
        return ('keep_v21', None,
                'M1 clears the bar against C0 but does not beat the D0 duplication control, so '
                'the change of sensor view is not what produced it')
    verdict = 'breakthrough_candidate' if m['breakthrough'] else 'production_check_candidate'
    return verdict, m, 'M1 clears every gate against C0 and beats the D0 control'


def stress_table(S):
    """Per arm and per stress seed, never pooled into the primary metric."""
    if not len(S):
        return pd.DataFrame()
    keep = S.loc[S.block.isin(PRIMARY)]
    out = []
    for (arm, seed), d in keep.groupby(['arm', 'stress_seed']):
        out.append(dict(population='primary', arm=arm, stress_seed=int(seed), n_blocks=len(d),
                        rms_dq=float(np.sqrt(np.mean(d.rms_dq ** 2))),
                        rms_dz=float(np.sqrt(np.mean(d.rms_dz ** 2))),
                        d_mse_vs_natural=float(d.d_mse_vs_natural.mean())))
    return pd.DataFrame(out).sort_values(['arm', 'stress_seed'])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--preds', default=str(OUT / 'preds_mask.pkl'))
    ap.add_argument('--stress', default=str(OUT / 'mask_stress.csv'))
    ap.add_argument('--out', default=str(OUT))
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    P = pd.read_pickle(a.preds)
    S = pd.read_csv(a.stress) if Path(a.stress).exists() else pd.DataFrame()

    vs_c0 = [evaluate(P, arm, GATE) for arm in P.arm.unique() if arm != GATE]
    vs_d0 = ([evaluate(P, arm, CONTROL) for arm in P.arm.unique()
              if arm not in (GATE, CONTROL)] if CONTROL in set(P.arm) else [])
    R, L = pd.DataFrame(vs_c0), pd.DataFrame(vs_d0)
    T = stress_table(S)
    R.to_csv(out / 'metrics.csv', index=False)
    if len(L):
        L.to_csv(out / 'metrics_vs_d0.csv', index=False)
    if len(T):
        T.to_csv(out / 'stress_summary.csv', index=False)

    assert abs(vs_c0[0]['pooled_base'] - C0_POOLED) < 1e-6, \
        'the control pooled RMSE is not the frozen 5.535893870'
    verdict, chosen, why = choose(vs_c0, vs_d0)
    c.write_json(out / 'decision.json', dict(
        created=pd.Timestamp.now().isoformat(timespec='seconds'),
        verdict=verdict, chosen=None if chosen is None else chosen['arm'], reason=why,
        bar=BAR, gate=GATE, duplication_control=CONTROL, candidate=CANDIDATE,
        populations=dict(primary='B1+B2 unique timestamps', sensitivity_15d='B3',
                         holdout_7d='H1+H2+H3',
                         stress='diagnostic only; never pooled into primary'),
        arms=vs_c0, arms_vs_d0=vs_d0, stress=T.to_dict('records') if len(T) else [],
        source=str(Path(a.preds)), source_md5=a47.md5(a.preds)))
    cols = ['arm', 'pooled_base', 'pooled_cand', 'd_pooled', 'd_matched', 'd_pooled7', 'worst_h',
            'rmse_member_cand', 'promotable']
    print(R[cols].to_string(index=False))
    if len(L):
        print('\nagainst the D0 duplication control (isolating the view change):')
        print(L[['arm', 'd_pooled', 'd_matched', 'd_pooled7', 'worst_h']].to_string(index=False))
    if len(T):
        print('\nstress diagnostic (primary blocks, per seed; NOT a score):')
        print(T.to_string(index=False))
    print('\nverdict: %s (%s)\n  %s' % (verdict, chosen and chosen['arm'], why))
    print('wrote %s' % out)


if __name__ == '__main__':
    main()
