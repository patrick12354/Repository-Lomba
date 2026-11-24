"""Session 47: the OOD stress gate for the `cat` level de-bias (progress.md 310).

Same five 3-day stress splits as an92/an93 -- ranked by target-free distance to the private
slice's descriptors, 96-hour embargo, past-only training, blend weights refitted per split from
that split's own inner folds. All six members are fitted once per split and every arm re-stacks
the same predictions, so no arm can differ by a fit.

What varies is one scalar: the mean signed error of `cat` measured on the split's own inner frame,
subtracted from `cat` before the stack is fitted. `wrong_sign` adds it instead, and `debias_enet`
points the same machinery at a member with no bias to remove.

This is the instrument that called `--drop-ridge` correctly (progress.md 286) and `--inc-physics`
incorrectly (progress.md 294), so it is 1-for-2 and is reported beside the in-regime arm rather
than above it.

    .venv/Scripts/python.exe src/an101_v21_member_bias_stress.py
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
import an100_v21_member_bias_arm as arm

OUT = ROOT / 'outputs' / 'audit_v21_s47'
M = list(fp.MODELS_L2)
MR = [m for m in M if m != 'ridge']


def run():
    OUT.mkdir(parents=True, exist_ok=True)
    g = fp.load_grid()
    F = fp.make_features(g)
    y = g[fp.TARGET]
    is_tr = (g.is_test == 0).to_numpy() & y.notna().to_numpy()
    is_te = (g.is_test == 1).to_numpy()
    splits = cap.stress_splits(F, is_tr, is_te)
    print('stress splits: %s' % [(str(v.min().date()), len(v)) for _, v in splits], flush=True)

    per_arm, rows = {a[0]: [] for a in arm.ARMS}, []
    for sid, (ti, vi) in enumerate(splits):
        t0 = time.time()
        tr, va = pd.DatetimeIndex(ti), pd.DatetimeIndex(vi)
        V = pd.DataFrame({m: cap._fit(m, None, F, y, tr, va) for m in M}, index=va)
        V['y'] = y.loc[va].to_numpy()
        V['tod'] = va.hour + va.minute / 60.0
        O = []
        for t, v in cap.inner_folds(tr):
            d = pd.DataFrame({m: cap._fit(m, None, F, y, t, v) for m in M},
                             index=pd.DatetimeIndex(v))
            d['y'] = y.loc[v].to_numpy()
            d['tod'] = pd.DatetimeIndex(v).hour + pd.DatetimeIndex(v).minute / 60.0
            O.append(d.reset_index(names='dt'))
        O = pd.concat(O, ignore_index=True)
        for label, member, strength in arm.ARMS:
            O2, V2, b = arm.shifted(O, V, member, strength)
            p = a36.stack(O2, V2, MR, fp.BLEND_SHRINK)
            per_arm[label].append((V.y.to_numpy(), p))
            rows.append(dict(split=sid, arm=label, n=len(va), start=str(va.min()),
                             offset=b, rmse=fp.rmse(V.y, p)))
        print('  split %d  %s  [%.0f s]  %s'
              % (sid, va.min().date(), time.time() - t0,
                 '  '.join('%s %.4f' % (a[0], fp.rmse(*per_arm[a[0]][-1])) for a in arm.ARMS)),
              flush=True)

    pd.DataFrame(rows).to_csv(OUT / 'member_bias_stress.csv', index=False)
    base = cap.pooled_rmse(per_arm['control'])
    base_worst = max(fp.rmse(a, b) for a, b in per_arm['control'])
    summary = {}
    print('\n%-16s %10s %10s %10s %10s  blocks improved'
          % ('arm', 'pooled', 'd_pooled', 'worst', 'd_worst'))
    for label, _, _ in arm.ARMS:
        pl = cap.pooled_rmse(per_arm[label])
        wo = max(fp.rmse(a, b) for a, b in per_arm[label])
        imp = sum(fp.rmse(a, b) < fp.rmse(c, d)
                  for (a, b), (c, d) in zip(per_arm[label], per_arm['control']))
        summary[label] = dict(pooled=pl, d_pooled=pl - base, worst=wo, d_worst=wo - base_worst,
                              blocks_improved=int(imp), n_blocks=len(splits))
        print('%-16s %10.5f %+10.5f %10.5f %+10.5f  %d/%d'
              % (label, pl, pl - base, wo, wo - base_worst, imp, len(splits)))
    (OUT / 'member_bias_stress.json').write_text(json.dumps(summary, indent=2))
    return summary


if __name__ == '__main__':
    run()
