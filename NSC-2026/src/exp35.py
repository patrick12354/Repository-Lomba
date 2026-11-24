"""Session 7, step 2: does a genuinely different model class buy anything?

Section 42 closed the feature routes and pointed here. Six candidates, each judged three
ways: how it scores alone, how decorrelated its residual is from the current blend, and
what the blend does when it is added as a sixth member (nested NNLS weights).

A candidate that scores badly alone can still earn weight -- ridge_e does exactly that
(section 22) -- so the solo column is context, not the verdict.
"""
import json, time
import numpy as np
import h7

CANDIDATES = ['lin', 'hbt_e', 'dart', 'xt', 'mlp', 'krr']

t0 = time.time()
F, y, is_tr, g = h7.load()
D = h7.oof(h7.BASE, F, y, is_tr)
ref = h7.report('v8 baseline (5 models)', D, h7.BASE)
print()

res = {'ref': ref, 'cand': {}}
for c in CANDIDATES:
    try:
        Dc = h7.oof(h7.BASE + [c], F, y, is_tr)
    except Exception as e:
        print(f'{c:24s} FAILED: {type(e).__name__}: {e}', flush=True)
        continue
    solo = h7.report(f'  solo {c}', Dc, [c], ref)
    # residual decorrelation against the baseline blend, family P. A low number here is
    # what earns a weak model its weight (section 22).
    P = Dc['P']
    bl = P[h7.BASE].values @ h7.nested(P, h7.BASE)[1]
    corr = float(np.corrcoef(P[c].values - P.y.values, bl - P.y.values)[0, 1])
    add = h7.report(f'  +{c} in blend', Dc, h7.BASE + [c], ref)
    add['solo'] = solo['avg']
    add['resid_corr'] = corr
    print(f'{"":24s}   solo {solo["avg"]:.3f}   residual corr vs blend {corr:+.3f}\n', flush=True)
    res['cand'][c] = add

json.dump(res, open('outputs/exp35_res.json', 'w'), indent=1)
print(f'total {time.time()-t0:.0f}s')
