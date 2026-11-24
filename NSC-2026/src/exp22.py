import warnings; warnings.filterwarnings('ignore')
import sys, json, numpy as np, pandas as pd
sys.path.insert(0, 'src')
from common import *
import featx2
from ab7 import families, run, report

g, _, _ = load_grid()
is_tr = pd.Series((g.is_test == 0).values, index=g.index)
y = g[TARGET]
c = clean_exog(g, k=6.0)
FAM = families(g.index[is_tr & y.notna()])
print('folds:', {k: len(v) for k, v in FAM.items()}, flush=True)

VAR = {'V7_ref': (), 'V7+night': ('night',), 'V7+dir': ('dir',), 'V7+q': ('q',),
       'V7+night+dir': ('night', 'dir'), 'V7+all': ('night', 'dir', 'q')}
RES, REF = [], None
for n, bl in VAR.items():
    F = featx2.build(c, bl)
    Ds = {fam: run(F, y, is_tr, folds) for fam, folds in FAM.items()}
    if REF is None:
        RES.append(report(f'{n}({F.shape[1]})', Ds)); REF = Ds
    else:
        RES.append(report(f'{n}({F.shape[1]})', Ds, refs=REF))
json.dump(RES, open('outputs/exp22_res.json', 'w'), indent=1, default=float)
print('\n=== RANKING by 3-family average ===', flush=True)
for r in sorted(RES, key=lambda r: r['avg']):
    print(f"  {r['name']:24s} avg {r['avg']:6.3f}", flush=True)
