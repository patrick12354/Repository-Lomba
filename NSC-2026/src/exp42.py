"""Session 7, step 9: a last sweep of the one member that carries the blend.

The drop-one ablation in step 7 is unambiguous: removing `hbt` costs +0.369 while removing
either linear member costs nothing. Whatever headroom is left is in that model. Sections 21
and 29 swept it one knob at a time and found only the Huber delta mattered, but both stopped
at the obvious knobs. This tries the ones neither session touched -- LightGBM's randomised
splitting, per-node feature sampling, leaf-value path smoothing, histogram resolution -- plus
the two-knob combinations that a one-at-a-time sweep cannot see.

Family P first, cheap. Anything that survives goes to Q and R before it is believed.
"""
import json, sys, time
import numpy as np
import h7
import lightgbm as lgb

GRID = {
    'h_xt': dict(extra_trees=True),
    'h_ffnode': dict(feature_fraction_bynode=0.6),
    'h_smooth': dict(path_smooth=10.0),
    'h_bin63': dict(max_bin=63),
    'h_bin511': dict(max_bin=511),
    'h_hess': dict(min_sum_hessian_in_leaf=20.0),
    'h_nl31_mc50': dict(num_leaves=31, min_child_samples=50),
    'h_nl9': dict(num_leaves=9),
    'h_deep_slow': dict(num_leaves=31, min_child_samples=50, n_estimators=2000,
                        learning_rate=0.012),
    'h_xt_ffnode': dict(extra_trees=True, feature_fraction_bynode=0.6),
    'h_xt_smooth': dict(extra_trees=True, path_smooth=10.0),
    'h_col50': dict(colsample_bytree=0.5),
}
_orig = h7.fit_predict


def fit_predict(name, *a):
    if name in GRID:
        Xtr, ytr, Xva, esv, etr, seeds = a
        kw = dict(h7.FP.LGB_KW); kw.update(GRID[name])
        return np.mean([lgb.LGBMRegressor(random_state=s, **kw).fit(Xtr, ytr).predict(Xva)
                        for s in seeds], 0)
    return _orig(name, *a)


h7.fit_predict = fit_predict

if __name__ == '__main__':
    t0 = time.time()
    F, y, is_tr, g = h7.load()
    cand = sys.argv[1].split(',') if len(sys.argv) > 1 else list(GRID)
    fams = list(sys.argv[2]) if len(sys.argv) > 2 else ['P']
    D = h7.oof(h7.BASE + cand, F, y, is_tr, fams=fams)
    res = {}

    for fam in fams:
        print(f'\nfamily {fam}, solo (all folds):')
        ref = np.array([h7.rmse(d.y, d['hbt']) for _, d in D[fam].groupby('fold')])
        print(f'  {"hbt (shipped)":14s} mean {ref.mean():6.3f}  worst {ref.max():6.3f}')
        for name in cand:
            per = np.array([h7.rmse(d.y, d[name]) for _, d in D[fam].groupby('fold')])
            won = int((per < ref).sum())
            res[f'solo {fam}:{name}'] = dict(mean=float(per.mean()), worst=float(per.max()),
                                             delta=float(per.mean() - ref.mean()),
                                             folds_won=f'{won}/{len(per)}')
            print(f'  {name:14s} mean {per.mean():6.3f}  worst {per.max():6.3f}  '
                  f'vs hbt {per.mean()-ref.mean():+.3f}  {won}/{len(per)}', flush=True)

    if set(fams) == {'P', 'Q', 'R'}:
        print('\nblend, nested NNLS weights:')
        ref_b = h7.report('v8 baseline', D, h7.BASE)
        others = [m for m in h7.BASE if m != 'hbt']
        for name in cand:
            res[f'swap:{name}'] = h7.report(f'  hbt -> {name}', D, others + [name], ref_b)

    json.dump(res, open(f'outputs/exp42_res_{"".join(fams)}.json', 'w'), indent=1)
    print(f'\ntotal {time.time()-t0:.0f}s')
