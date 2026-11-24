"""Session 41: the OOD stress gate for dropping a zero-weight blend member.

**Why this is reopened.** §122 adopted `--drop-ridge` on a drop-one ablation, a nested CI excluding
zero, and an OOD stress improvement of −0.0374 pooled and −0.083 on the worst block. It then rode
into `v19` alongside the pressure removal, the bundle lost 0.10 on public, and the line was
abandoned for `v16 + --increment`. But §127's own decomposition separates the components, and the
`v18 -> v19` row — the drop-`ridge` step alone — has **α\* = +25.8** and ΔMSE **−0.069**: on the
public slice that step was a large improvement in the right direction, hugely under-stepped. What
lost was `v16 -> v18` at α\* = −1.84. §89 already cost this log one verdict to a bundling artefact;
this is the second, and it is still live because `v21` never picked the component back up.

**Why it needs this gate rather than the campaign one.** On the repaired forward blocks
drop-`ridge` is pooled −0.0111 with B1 **+0.029** — below the bar and worsening a primary block, so
the in-regime gate says no. Family J (§275) just showed that in-regime and out-of-regime can point
in opposite directions, and it was rejected for gaining inside and losing outside. Drop-`ridge` is
the mirror case: §122 measured it losing slightly inside and gaining outside. The competition is
decided on the private 70 %, which is the out-of-regime slice, so the mirror case deserves the same
measurement rather than the same verdict.

**What varies.** Only the member list handed to the blend. All six members are fitted once per
stress split and every arm re-stacks the same predictions, so no arm can differ by a fit.

    .venv/Scripts/python.exe src/an93_v21_member_drop_stress.py
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

OUT = ROOT / 'outputs' / 'audit_v21_s41'
M = list(fp.MODELS_L2)
# The three members NNLS gives exactly zero raw weight to in every block (all sit on the
# 0.0417 shrinkage floor), plus the control that drops nothing.
ARMS = {
    'control': M,
    'drop_ridge': [m for m in M if m != 'ridge'],
    'drop_ridge_e': [m for m in M if m != 'ridge_e'],
    'drop_l2': [m for m in M if m != 'l2'],
    'drop_ridge_and_ridge_e': [m for m in M if m not in ('ridge', 'ridge_e')],
}


def run():
    OUT.mkdir(parents=True, exist_ok=True)
    g = fp.load_grid()
    F = fp.make_features(g)
    y = g[fp.TARGET]
    is_tr = (g.is_test == 0).to_numpy() & y.notna().to_numpy()
    is_te = (g.is_test == 1).to_numpy()
    splits = cap.stress_splits(F, is_tr, is_te)
    print('stress splits: %s' % [(str(v.min().date()), len(v)) for _, v in splits], flush=True)

    per_arm, rows = {a: [] for a in ARMS}, []
    for sid, (ti, vi) in enumerate(splits):
        t0 = time.time()
        tr, va = pd.DatetimeIndex(ti), pd.DatetimeIndex(vi)
        folds = cap.inner_folds(tr)
        V = pd.DataFrame({m: cap._fit(m, None, F, y, tr, va) for m in M}, index=va)
        V['y'] = y.loc[va].to_numpy()
        V['tod'] = va.hour + va.minute / 60.0
        O = []
        for t, v in folds:
            d = pd.DataFrame({m: cap._fit(m, None, F, y, t, v) for m in M},
                             index=pd.DatetimeIndex(v))
            d['y'] = y.loc[v].to_numpy()
            d['tod'] = pd.DatetimeIndex(v).hour + pd.DatetimeIndex(v).minute / 60.0
            O.append(d.reset_index(names='dt'))
        O = pd.concat(O, ignore_index=True)
        for arm, models in ARMS.items():
            p = a36.stack(O, V, models, fp.BLEND_SHRINK)
            per_arm[arm].append((V.y.to_numpy(), p))
            rows.append(dict(split=sid, arm=arm, n=len(va), start=str(va.min()),
                             rmse=fp.rmse(V.y, p)))
        print('  split %d  %s  [%.0f s]  %s'
              % (sid, va.min().date(), time.time() - t0,
                 '  '.join('%s %.4f' % (a, fp.rmse(*per_arm[a][-1])) for a in ARMS)), flush=True)

    pd.DataFrame(rows).to_csv(OUT / 'member_drop_stress.csv', index=False)
    base = cap.pooled_rmse(per_arm['control'])
    base_worst = max(fp.rmse(a, b) for a, b in per_arm['control'])
    summary = {}
    print('\n%-24s %10s %10s %10s %10s  blocks improved' % ('arm', 'pooled', 'd_pooled',
                                                            'worst', 'd_worst'))
    for arm in ARMS:
        pl = cap.pooled_rmse(per_arm[arm])
        wo = max(fp.rmse(a, b) for a, b in per_arm[arm])
        imp = sum(fp.rmse(a, b) < fp.rmse(c, d)
                  for (a, b), (c, d) in zip(per_arm[arm], per_arm['control']))
        summary[arm] = dict(pooled=pl, d_pooled=pl - base, worst=wo, d_worst=wo - base_worst,
                            blocks_improved=int(imp), n_blocks=len(splits))
        print('%-24s %10.5f %+10.5f %10.5f %+10.5f  %d/%d'
              % (arm, pl, pl - base, wo, wo - base_worst, imp, len(splits)))
    (OUT / 'member_drop_stress.json').write_text(json.dumps(summary, indent=2))
    return summary


if __name__ == '__main__':
    run()
