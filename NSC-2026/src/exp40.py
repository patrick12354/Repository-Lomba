"""Session 7, step 7: the linear members, which were also never re-tuned.

Same reasoning that paid off for CatBoost in step 3. `ridge` (alpha 20) and `enet`
(alpha 0.05, l1_ratio 0.5) were picked in session 1 on a 144-column raw feature set and
carried unchanged through two feature rebuilds. Their out-of-fold residuals now correlate
**0.990** with each other, so the blend is effectively paying for one member twice.

Sweeps the regularisation, tries a robust linear member (Huber) and a PLS projection in
its place, and runs drop-one ablations to see whether the pair earns its keep at all.
Everything here is seconds per fold, unlike the CatBoost sweep.
"""
import json, sys, time
import numpy as np
import h7
from sklearn.linear_model import Ridge, ElasticNet, HuberRegressor
from sklearn.cross_decomposition import PLSRegression

FP = h7.FP
GRID = {
    'ridge_a5': lambda: Ridge(alpha=5.0),
    'ridge_a60': lambda: Ridge(alpha=60.0),
    'ridge_a200': lambda: Ridge(alpha=200.0),
    'enet_a02': lambda: ElasticNet(alpha=0.2, l1_ratio=0.5, max_iter=8000),
    'enet_l19': lambda: ElasticNet(alpha=0.05, l1_ratio=0.9, max_iter=8000),
    'hublin': lambda: HuberRegressor(epsilon=1.35, alpha=1e-3, max_iter=500),
    'pls12': lambda: PLSRegression(n_components=12, scale=False),
}
_orig = h7.fit_predict


def fit_predict(name, *a):
    if name in GRID:
        Xtr, ytr, Xva, esv, etr, seeds = a
        p = FP._pipe(GRID[name]()).fit(Xtr, ytr).predict(Xva)
        return np.asarray(p).ravel()
    return _orig(name, *a)


h7.fit_predict = fit_predict

if __name__ == '__main__':
    t0 = time.time()
    F, y, is_tr, g = h7.load()
    cand = sys.argv[1].split(',') if len(sys.argv) > 1 else list(GRID)
    fams = list(sys.argv[2]) if len(sys.argv) > 2 else ['P', 'Q', 'R']
    D = h7.oof(h7.BASE + cand, F, y, is_tr, fams=fams)
    res = {}

    for fam in fams:
        print(f'\nfamily {fam}, solo (all folds):')
        for base in ('ridge', 'enet'):
            r = np.array([h7.rmse(d.y, d[base]) for _, d in D[fam].groupby('fold')])
            print(f'  {base + " (shipped)":16s} mean {r.mean():6.3f}  worst {r.max():6.3f}')
        ref = np.array([h7.rmse(d.y, d['ridge']) for _, d in D[fam].groupby('fold')])
        for name in cand:
            per = np.array([h7.rmse(d.y, d[name]) for _, d in D[fam].groupby('fold')])
            won = int((per < ref).sum())
            res[f'solo {fam}:{name}'] = dict(mean=float(per.mean()), worst=float(per.max()),
                                             delta=float(per.mean() - ref.mean()),
                                             folds_won=f'{won}/{len(per)}')
            print(f'  {name:16s} mean {per.mean():6.3f}  worst {per.max():6.3f}  '
                  f'vs ridge {per.mean()-ref.mean():+.3f}  {won}/{len(per)}', flush=True)

    if set(fams) == {'P', 'Q', 'R'}:
        print('\nblend, nested NNLS weights:')
        ref_b = h7.report('v8 baseline', D, h7.BASE)
        print('  -- drop-one ablations:')
        for m in h7.BASE:
            res[f'drop:{m}'] = h7.report(f'  without {m}', D,
                                         [x for x in h7.BASE if x != m], ref_b)
        print('  -- swap the enet slot (the 0.990-correlated one):')
        for name in cand:
            res[f'swap_enet:{name}'] = h7.report(
                f'  enet -> {name}', D, [x for x in h7.BASE if x != 'enet'] + [name], ref_b)

    json.dump(res, open(f'outputs/exp40_res_{"".join(fams)}.json', 'w'), indent=1)
    print(f'\ntotal {time.time()-t0:.0f}s')
