"""Session 7, step 6: follow up the CatBoost loss finding.

Step 3 found plain RMSE beats `Huber:delta=4` for the CatBoost member by 0.598 solo on
family P, 7/9 folds, with the worst fold falling 9.25 -> 7.82. Two questions remain before
anything is adopted: does it hold on families Q and R, and does a solo gain in the most
decorrelated blend member actually reach the blend?

Depth is swept alongside it because the two interact -- `cat_d4` was neutral on the mean but
cut the worst fold by more than a point, which is the profile of a member whose old loss was
masking an overfitting problem.
"""
import json, sys, time
import numpy as np
import h7
import catboost as cb

REF = dict(iterations=1200, learning_rate=0.035, depth=6, l2_leaf_reg=6.0,
           loss_function='Huber:delta=4', verbose=0, allow_writing_files=False)

GRID = {
    'cat_rmse': dict(loss_function='RMSE'),
    'cat_rmse_d4': dict(loss_function='RMSE', depth=4),
    'cat_rmse_d5': dict(loss_function='RMSE', depth=5),
    'cat_rmse_l20': dict(loss_function='RMSE', l2_leaf_reg=20.0),
    'cat_mae': dict(loss_function='MAE'),
}
_orig = h7.fit_predict


def fit_predict(name, *a):
    if name in GRID:
        Xtr, ytr, Xva, esv, etr, seeds = a
        kw = dict(REF); kw.update(GRID[name])
        return np.mean([cb.CatBoostRegressor(random_seed=s, **kw)
                        .fit(Xtr, ytr).predict(Xva) for s in seeds], 0)
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
        ref = np.array([h7.rmse(d.y, d['cat']) for _, d in D[fam].groupby('fold')])
        print(f'  {"cat (shipped)":14s} mean {ref.mean():6.3f}  worst {ref.max():6.3f}')
        for name in cand:
            per = np.array([h7.rmse(d.y, d[name]) for _, d in D[fam].groupby('fold')])
            won = int((per < ref).sum())
            res[f'solo {fam}:{name}'] = dict(mean=float(per.mean()), worst=float(per.max()),
                                             delta=float(per.mean() - ref.mean()),
                                             folds_won=f'{won}/{len(per)}')
            print(f'  {name:14s} mean {per.mean():6.3f}  worst {per.max():6.3f}  '
                  f'vs ref {per.mean()-ref.mean():+.3f}  {won}/{len(per)}', flush=True)

    if set(fams) == {'P', 'Q', 'R'}:
        print('\nblend, nested NNLS weights:')
        ref_b = h7.report('v8 baseline', D, h7.BASE)
        others = [m for m in h7.BASE if m != 'cat']
        for name in cand:
            # replace the cat member outright
            res[f'swap:{name}'] = h7.report(f'  cat -> {name}', D, others + [name], ref_b)
        for name in cand:
            # or keep both, and let NNLS decide
            res[f'add:{name}'] = h7.report(f'  cat + {name}', D, h7.BASE + [name], ref_b)

    json.dump(res, open(f'outputs/exp39_res_{"".join(fams)}.json', 'w'), indent=1)
    print(f'\ntotal {time.time()-t0:.0f}s')
