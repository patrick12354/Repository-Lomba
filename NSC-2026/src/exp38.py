"""Session 7, step 5: transductive self-training (pseudo-labelling).

The one standard technique this project has never tried. The mechanism it would exploit is
real: the test window sits at the cool edge of the training feature distribution, trees
cannot extrapolate, so predictions there are pinned to whatever leaf the boundary rows fall
in. Refitting with the unlabelled window included -- carrying the model's own predictions
as soft labels -- lets the ensemble build structure in that region.

No target ever crosses the cut. Round 1 fits on training rows only; round 2 adds the
validation rows labelled with round 1's own output, down-weighted. In cross-validation the
validation window stands in for the test window exactly as it does at inference time.
"""
import json, sys, time
import numpy as np, pandas as pd
import h7
import lightgbm as lgb

WEIGHTS = {'pl_w20': 0.2, 'pl_w50': 0.5, 'pl_w100': 1.0}
_orig = h7.fit_predict


def selftrain(Xtr, ytr, Xva, w, seeds=(0, 1, 2)):
    kw = dict(h7.FP.LGB_KW)
    p1 = np.mean([lgb.LGBMRegressor(random_state=s, **kw).fit(Xtr, ytr).predict(Xva)
                  for s in seeds], 0)
    Xa = pd.concat([Xtr, Xva])
    ya = np.concatenate([ytr.values, np.clip(p1, 5, 100)])
    sw = np.concatenate([np.ones(len(Xtr)), np.full(len(Xva), w)])
    return np.mean([lgb.LGBMRegressor(random_state=s, **kw)
                    .fit(Xa, ya, sample_weight=sw).predict(Xva) for s in seeds], 0)


def fit_predict(name, *a):
    Xtr, ytr, Xva, esv, etr, seeds = a
    if name in WEIGHTS:
        return selftrain(Xtr, ytr, Xva, WEIGHTS[name], seeds)
    return _orig(name, *a)


h7.fit_predict = fit_predict

if __name__ == '__main__':
    t0 = time.time()
    F, y, is_tr, g = h7.load()
    fams = list(sys.argv[1]) if len(sys.argv) > 1 else ['P']
    D = h7.oof(['hbt'] + list(WEIGHTS), F, y, is_tr, fams=fams)

    res = {}
    for fam in fams:
        print(f'\nfamily {fam}, solo scores (self-training applied to the hbt member):')
        ref = np.array([h7.rmse(d.y, d['hbt']) for _, d in D[fam].groupby('fold')])
        print(f'  {"hbt (shipped)":14s} mean {ref.mean():6.3f}  worst {ref.max():6.3f}')
        for name in WEIGHTS:
            per = np.array([h7.rmse(d.y, d[name]) for _, d in D[fam].groupby('fold')])
            won = int((per < ref).sum())
            res[f'{fam}:{name}'] = dict(mean=float(per.mean()), worst=float(per.max()),
                                        delta=float(per.mean() - ref.mean()),
                                        folds_won=f'{won}/{len(per)}')
            print(f'  {name:14s} mean {per.mean():6.3f}  worst {per.max():6.3f}  '
                  f'vs hbt {per.mean()-ref.mean():+.3f}  {won}/{len(per)}', flush=True)

    json.dump(res, open(f'outputs/exp38_res_{"".join(fams)}.json', 'w'), indent=1)
    print(f'\ntotal {time.time()-t0:.0f}s')
