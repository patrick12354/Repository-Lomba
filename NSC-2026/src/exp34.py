"""Session 7, step 1: reproduce the v8 baseline inside the new harness.

Nothing new is tested here. The point is to confirm that h7 reproduces the numbers in
section 30 (v8: P 4.788, Q 4.606, R 4.937, avg 4.777) before any candidate is judged
against them.
"""
import json, time
import h7

t0 = time.time()
F, y, is_tr, g = h7.load()
print(f'features {F.shape[1]}  train rows {int(is_tr.sum())}  ({time.time()-t0:.0f}s)')

D = h7.oof(h7.BASE, F, y, is_tr)
for fam in ('P', 'Q', 'R'):
    print(f'  family {fam}: {D[fam].fold.nunique()} folds, {len(D[fam])} rows')

print()
ref = h7.report('v8 baseline', D, h7.BASE)
print()
for m in h7.BASE:
    r = h7.report(f'  solo {m}', D, [m], ref)

# residual correlation between members -- the diversity budget the blend has to work with
import pandas as pd
R = D['P'][h7.BASE].sub(D['P'].y, axis=0)
print('\nresidual correlations (family P):')
print(R.corr().round(3).to_string())

json.dump(ref, open('outputs/exp34_res.json', 'w'), indent=1)
print(f'\ntotal {time.time()-t0:.0f}s')
