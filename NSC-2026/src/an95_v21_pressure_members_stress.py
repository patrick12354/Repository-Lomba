"""Session 42: the OTHER components of the abandoned v17/v18 bundle, isolated on the v21 backbone.

`--drop-ridge` was the first component of that bundle to be tested on its own and it scored public
**2.85383** against 2.86595 — ΔMSE −0.06932, against the −0.069 §127 measured for the same step on
the v18 backbone. The same change, two different backbones, the same public ΔMSE to three decimals.

That has two consequences, and this module follows from both.

**1. The bundle hid at least one real component, so the others deserve isolation too.** `v18` and
`v17` also carried `--bag-nopress` (a member fitted without the pressure block, §115) and
`--robust-core` (a member on the stable-column core, §108). Neither has ever been run alone on the
v21 backbone. They attack the SAME mechanism drop-`ridge` exploited — §80 identified the
out-of-support pressure block as what damages members on the private slice — but additively: rather
than removing the member that block hurts, add one that never sees it.

**2. The OOD stress gate is the instrument that called it right.** Three instruments predicted the
public direction of drop-`ridge`. The stress blocks said better (−0.0520) and were right. The
forward blocks said worse on the public-like populations (B1 +0.029, H1 +0.035) and were wrong.
§282's pressure-support curve said **+0.0137** at public support and was wrong in sign. That is one
observation, not a law, but it is the only out-of-sample check any of the three has, and it is why
this round leads with the stress gate instead of the forward blocks.

Every member is fitted once per split and every arm re-stacks identical predictions, so no arm can
differ from another by a fit.

    .venv/Scripts/python.exe src/an95_v21_pressure_members_stress.py
"""
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
import final_pipeline as fp
import an36_increment_production as a36
import an92_v21_capacity_stress as cap

OUT = ROOT / 'outputs' / 'audit_v21_s42'
M = list(fp.MODELS_L2)
MR = [m for m in M if m != 'ridge']


def arms():
    """`control` and `drop_ridge` are both carried: drop_ridge is now a POSITIVE control with a
    known public result, so a run that fails to reproduce its −0.052 is a run to distrust."""
    return {
        'control': M,
        'drop_ridge': MR,
        'nopress': M + [fp.NOPRESS],
        'robustcore': M + [fp.ROBUST],
        'drop_ridge_nopress': MR + [fp.NOPRESS],
        'drop_ridge_robustcore': MR + [fp.ROBUST],
        'drop_ridge_both': MR + [fp.NOPRESS, fp.ROBUST],
    }


def run():
    OUT.mkdir(parents=True, exist_ok=True)
    g = fp.load_grid()
    F = fp.make_features(g)
    y = g[fp.TARGET]
    is_tr = (g.is_test == 0).to_numpy() & y.notna().to_numpy()
    is_te = (g.is_test == 1).to_numpy()
    # Column subsets are the shipped ones, derived from the real test window exactly as
    # production derives them -- test EXOGENOUS only, which is §47's transductive policy.
    cols = {m: None for m in M}
    cols[fp.NOPRESS] = fp.no_pressure(F)
    cols[fp.ROBUST] = fp.stable_core(F, is_tr, is_te)
    print('nopress %d cols, robust-core %d cols, full %d'
          % (len(cols[fp.NOPRESS]), len(cols[fp.ROBUST]), F.shape[1]), flush=True)

    ARMS = arms()
    members = sorted({m for a in ARMS.values() for m in a})
    splits = cap.stress_splits(F, is_tr, is_te)
    print('stress splits: %s' % [(str(v.min().date()), len(v)) for _, v in splits], flush=True)

    def fit(m, tr, va):
        c = cols.get(m) or list(F.columns)
        return cap._fit(fp.base_model(m), None, F[c], y, tr, va)

    per_arm, rows = {a: [] for a in ARMS}, []
    for sid, (ti, vi) in enumerate(splits):
        t0 = time.time()
        tr, va = pd.DatetimeIndex(ti), pd.DatetimeIndex(vi)
        folds = cap.inner_folds(tr)
        V = pd.DataFrame({m: fit(m, tr, va) for m in members}, index=va)
        V['y'] = y.loc[va].to_numpy()
        V['tod'] = va.hour + va.minute / 60.0
        O = []
        for t, v in folds:
            d = pd.DataFrame({m: fit(m, t, v) for m in members}, index=pd.DatetimeIndex(v))
            d['y'] = y.loc[v].to_numpy()
            d['tod'] = pd.DatetimeIndex(v).hour + pd.DatetimeIndex(v).minute / 60.0
            O.append(d.reset_index(names='dt'))
        O = pd.concat(O, ignore_index=True)
        for arm, models in ARMS.items():
            p = a36.stack(O, V, models, fp.BLEND_SHRINK)
            per_arm[arm].append((V.y.to_numpy(), p))
            rows.append(dict(split=sid, arm=arm, n=len(va), start=str(va.min()),
                             rmse=fp.rmse(V.y, p)))
        print('  split %d %s [%.0f s] %s' % (sid, va.min().date(), time.time() - t0,
                                             '  '.join('%s %.4f' % (a, fp.rmse(*per_arm[a][-1]))
                                                       for a in ARMS)), flush=True)

    pd.DataFrame(rows).to_csv(OUT / 'pressure_members_stress.csv', index=False)
    base = cap.pooled_rmse(per_arm['control'])
    base_worst = max(fp.rmse(a, b) for a, b in per_arm['control'])
    summary = {}
    print('\n%-24s %10s %10s %10s %10s  improved' % ('arm', 'pooled', 'd_pooled', 'worst',
                                                     'd_worst'))
    for arm in ARMS:
        pl = cap.pooled_rmse(per_arm[arm])
        wo = max(fp.rmse(a, b) for a, b in per_arm[arm])
        imp = sum(fp.rmse(a, b) < fp.rmse(c, d)
                  for (a, b), (c, d) in zip(per_arm[arm], per_arm['control']))
        summary[arm] = dict(pooled=pl, d_pooled=pl - base, worst=wo, d_worst=wo - base_worst,
                            blocks_improved=int(imp), n_blocks=len(splits))
        print('%-24s %10.5f %+10.5f %10.5f %+10.5f  %d/%d'
              % (arm, pl, pl - base, wo, wo - base_worst, imp, len(splits)))
    (OUT / 'pressure_members_stress.json').write_text(json.dumps(summary, indent=2))
    d = summary['drop_ridge']['d_pooled']
    print('\npositive control drop_ridge: %+.5f (session 41 measured -0.05196 on the same blocks)'
          % d)
    return summary


if __name__ == '__main__':
    run()
