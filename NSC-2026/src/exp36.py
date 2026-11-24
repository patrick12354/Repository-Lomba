"""Session 7, step 3: tune the CatBoost member, which no session ever did.

Sections 21 and 29 re-tuned LightGBM after each feature change and both times the optimum
had moved. CatBoost has carried blend weight since section 22 on knobs picked in session 2
and never revisited, on a feature set that has changed twice since. One knob at a time on
family P, the section 29 protocol; the winner is then confirmed on Q and R and in the blend.

The reference is the shipped `cat` member itself, reused from the harness cache, so the
comparison is against the model that is actually in the submission rather than a rebuild.
"""
import json, sys, time
import numpy as np
import h7
import catboost as cb

REF = dict(iterations=1200, learning_rate=0.035, depth=6, l2_leaf_reg=6.0,
           loss_function='Huber:delta=4', verbose=0, allow_writing_files=False)

GRID = {
    'cat_a2': dict(loss_function='Huber:delta=2'),
    'cat_a8': dict(loss_function='Huber:delta=8'),
    'cat_rmse': dict(loss_function='RMSE'),
    'cat_d4': dict(depth=4),
    'cat_d8': dict(depth=8),
    'cat_l20': dict(l2_leaf_reg=20.0),
    'cat_slow': dict(iterations=2400, learning_rate=0.018),
    'cat_rsm': dict(rsm=0.6),
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
    fams = list(sys.argv[1]) if len(sys.argv) > 1 else ['P']
    D = h7.oof(['cat'] + list(GRID), F, y, is_tr, fams=fams)

    res = {}
    for fam in fams:
        print(f'\nsolo CatBoost scores, family {fam} (no blending):')
        ref = np.array([h7.rmse(d.y, d['cat']) for _, d in D[fam].groupby('fold')])
        print(f'  {"cat (shipped)":14s} mean {ref.mean():6.3f}  worst {ref.max():6.3f}')
        for name in GRID:
            per = np.array([h7.rmse(d.y, d[name]) for _, d in D[fam].groupby('fold')])
            won = int((per < ref).sum())
            res[f'{fam}:{name}'] = dict(mean=float(per.mean()), worst=float(per.max()),
                                        delta=float(per.mean() - ref.mean()),
                                        folds_won=f'{won}/{len(per)}')
            print(f'  {name:14s} mean {per.mean():6.3f}  worst {per.max():6.3f}  '
                  f'vs ref {per.mean()-ref.mean():+.3f}  {won}/{len(per)}', flush=True)

    json.dump(res, open(f'outputs/exp36_res_{"".join(fams)}.json', 'w'), indent=1)
    print(f'\ntotal {time.time()-t0:.0f}s')
