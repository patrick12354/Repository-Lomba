"""Session 47: is `cat`'s level bias a property of the member or of the block?

The forward blocks and the OOD stress blocks disagree about the de-bias (progress.md 311). The
two instruments differ in one respect that matters for a LEVEL correction: the stress blocks are
3 days long, and a 3-day mean error is essentially one draw of the day-level error, whose standard
deviation section 163 measured at 2.5-4.2 %RH. So before reading either verdict, measure the
quantity both of them are actually arguing about --- `cat`'s own signed error on the block it is
scored on, against the offset its past-only inner frame predicts.

    .venv/Scripts/python.exe src/an102_v21_cat_bias_population.py
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
import an92_v21_capacity_stress as cap

OUT = ROOT / 'outputs' / 'audit_v21_s47'


def run():
    OUT.mkdir(parents=True, exist_ok=True)
    g = fp.load_grid()
    F = fp.make_features(g)
    y = g[fp.TARGET]
    is_tr = (g.is_test == 0).to_numpy() & y.notna().to_numpy()
    is_te = (g.is_test == 1).to_numpy()
    rows = []
    for sid, (ti, vi) in enumerate(cap.stress_splits(F, is_tr, is_te)):
        t0 = time.time()
        tr, va = pd.DatetimeIndex(ti), pd.DatetimeIndex(vi)
        pv = cap._fit('cat', None, F, y, tr, va)
        inner = []
        for t, v in cap.inner_folds(tr):
            p = cap._fit('cat', None, F, y, t, pd.DatetimeIndex(v))
            inner.append(p - y.loc[v].to_numpy())
        rows.append(dict(split=sid, start=str(va.min()), n=len(va),
                         cat_bias_inner=float(np.mean(np.concatenate(inner))),
                         cat_bias_outer=float(np.mean(pv - y.loc[va].to_numpy())),
                         cat_rmse_outer=fp.rmse(y.loc[va], pv)))
        print('  split %d  %s  [%.0f s]  inner %+.3f  outer %+.3f'
              % (sid, va.min().date(), time.time() - t0,
                 rows[-1]['cat_bias_inner'], rows[-1]['cat_bias_outer']), flush=True)
    d = pd.DataFrame(rows)
    d.to_csv(OUT / 'cat_bias_population.csv', index=False)
    print('\n%s' % d.round(4).to_string(index=False))
    print('\ncat under-predicts on %d of %d stress blocks; inner mean %+.3f, outer mean %+.3f'
          % (int((d.cat_bias_outer < 0).sum()), len(d),
             d.cat_bias_inner.mean(), d.cat_bias_outer.mean()))
    (OUT / 'cat_bias_population.json').write_text(json.dumps(rows, indent=2))
    return d


if __name__ == '__main__':
    run()
