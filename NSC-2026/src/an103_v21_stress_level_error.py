"""Session 47: decompose the stress blocks' level error into member offset and block offset.

`an102` found the thing that matters: on the five OOD stress blocks `cat`'s past-only inner bias is
-3.33 on average while its bias on the block it is scored on averages **-0.29**, positive on three
of the five. On the six forward blocks the same two quantities are -3.74 and -2.89. Either `cat`'s
offset evaporates on those blocks, or the blocks carry a large common level error of their own that
the 144-row measurement cannot separate from it.

This separates them. Every member is fitted on each stress split, inner and outer, so

    cat_rel = bias(cat) - mean over the other members of bias(m)

is the member-specific offset with the block's common error removed, and `blend_bias` is the common
error the de-bias would have to overcome.

    .venv/Scripts/python.exe src/an103_v21_stress_level_error.py
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
    rows = []
    for sid, (ti, vi) in enumerate(cap.stress_splits(F, is_tr, is_te)):
        t0 = time.time()
        tr, va = pd.DatetimeIndex(ti), pd.DatetimeIndex(vi)
        V = pd.DataFrame({m: cap._fit(m, None, F, y, tr, va) for m in M}, index=va)
        V['y'] = y.loc[va].to_numpy()
        V['tod'] = va.hour + va.minute / 60.0
        O = []
        for t, v in cap.inner_folds(tr):
            d = pd.DataFrame({m: cap._fit(m, None, F, y, t, pd.DatetimeIndex(v)) for m in M},
                             index=pd.DatetimeIndex(v))
            d['y'] = y.loc[v].to_numpy()
            d['tod'] = pd.DatetimeIndex(v).hour + pd.DatetimeIndex(v).minute / 60.0
            O.append(d.reset_index(names='dt'))
        O = pd.concat(O, ignore_index=True)
        p = a36.stack(O, V, MR, fp.BLEND_SHRINK)
        r = dict(split=sid, start=str(va.min()), n=len(va),
                 blend_bias=float(np.mean(p - V.y.to_numpy())), blend_rmse=fp.rmse(V.y, p))
        for m in M:
            r['in_' + m] = float((O[m] - O.y).mean())
            r['out_' + m] = float((V[m] - V.y).mean())
        others = [m for m in MR if m != 'cat']
        r['cat_rel_in'] = r['in_cat'] - float(np.mean([r['in_' + m] for m in others]))
        r['cat_rel_out'] = r['out_cat'] - float(np.mean([r['out_' + m] for m in others]))
        rows.append(r)
        print('  split %d  %s  [%.0f s]  blend_bias %+.3f  cat_rel in %+.3f out %+.3f'
              % (sid, va.min().date(), time.time() - t0, r['blend_bias'],
                 r['cat_rel_in'], r['cat_rel_out']), flush=True)
    d = pd.DataFrame(rows)
    d.to_csv(OUT / 'stress_level_error.csv', index=False)
    pd.set_option('display.width', 220)
    print('\n%s' % d[['split', 'start', 'blend_bias', 'blend_rmse', 'in_cat', 'out_cat',
                      'cat_rel_in', 'cat_rel_out']].round(4).to_string(index=False))
    print('\nblend bias: mean %+.3f, negative on %d of %d blocks'
          % (d.blend_bias.mean(), int((d.blend_bias < 0).sum()), len(d)))
    print('cat_rel   : inner mean %+.3f, outer mean %+.3f, negative outer on %d of %d'
          % (d.cat_rel_in.mean(), d.cat_rel_out.mean(),
             int((d.cat_rel_out < 0).sum()), len(d)))
    (OUT / 'stress_level_error.json').write_text(json.dumps(rows, indent=2))
    return d


if __name__ == '__main__':
    run()
