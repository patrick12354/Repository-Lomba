"""Session 7, step 4: two-stage slow/fast decomposition of the TARGET.

Section 34 splits the residual into a 24 h slow component and a fast one and finds the fast
part is now 60 % of MSE. Section 36 then attacked it with fast *features* and failed. This
tries the other handle: split the *target* instead, so one learner fits the air-mass level
and a second fits the within-day excursion around it, each on the features that suit it.

The slow target is a centered 24 h mean of RH computed inside the fold's training window
only, so a training row near the cut gets a right-truncated window rather than a peek at
validation targets. Verified by construction: `y[t]` is sliced before the rolling call.
"""
import json, sys, time
import numpy as np, pandas as pd
import h7
import lightgbm as lgb

SLOW_HINTS = ('_c24h', '_c6h', '_min', '_max', '_rng', '_q', 'rh_q', 'rh_tmin',
              'tend', 'daily', 'gdd', 'ontario', 'standard_day', 'esT_ratio')
FAST_HINTS = ('_a1h', '_a6h', '_a24h', '_s-', '_s1', '_s2', '_s4', '_slope',
              '_sd6h', 'sin', 'cos', 'tod', '_minus_')


def split_cols(cols):
    slow = [c for c in cols if any(h in c for h in SLOW_HINTS)
            and not any(h in c for h in ('_a1h', '_a6h', '_a24h'))]
    fast = [c for c in cols if any(h in c for h in FAST_HINTS)]
    return slow, fast


_orig = h7.fit_predict


def two_stage(Xtr, ytr, Xva, split_features, win=49):
    ys = ytr.rolling(win, center=True, min_periods=6).mean()
    yf = ytr - ys
    slow_c, fast_c = split_cols(Xtr.columns)
    Xs, Xf = (Xtr[slow_c], Xtr[fast_c]) if split_features else (Xtr, Xtr)
    Vs, Vf = (Xva[slow_c], Xva[fast_c]) if split_features else (Xva, Xva)
    kws = dict(h7.FP.LGB_KW)
    kwf = dict(h7.FP.LGB_KW); kwf.update(alpha=1.0, num_leaves=31, learning_rate=0.04)
    ps = np.mean([lgb.LGBMRegressor(random_state=s, **kws).fit(Xs, ys).predict(Vs)
                  for s in (0, 1, 2)], 0)
    pf = np.mean([lgb.LGBMRegressor(random_state=s, **kwf).fit(Xf, yf).predict(Vf)
                  for s in (0, 1, 2)], 0)
    return ps + pf


def fit_predict(name, *a):
    Xtr, ytr, Xva, esv, etr, seeds = a
    if name == 'ts_all':
        return two_stage(Xtr, ytr, Xva, split_features=False)
    if name == 'ts_split':
        return two_stage(Xtr, ytr, Xva, split_features=True)
    return _orig(name, *a)


h7.fit_predict = fit_predict

if __name__ == '__main__':
    t0 = time.time()
    F, y, is_tr, g = h7.load()
    slow_c, fast_c = split_cols(F.columns)
    print(f'feature split: {len(slow_c)} slow, {len(fast_c)} fast, '
          f'{F.shape[1]} total ({len(set(slow_c) & set(fast_c))} in both)')

    fams = list(sys.argv[1]) if len(sys.argv) > 1 else ['P']
    cand = ['ts_all', 'ts_split']
    D = h7.oof(h7.BASE + cand, F, y, is_tr, fams=fams)

    res = {}
    for fam in fams:
        print(f'\nfamily {fam}, solo scores:')
        ref = np.array([h7.rmse(d.y, d['hbt']) for _, d in D[fam].groupby('fold')])
        print(f'  {"hbt (shipped)":14s} mean {ref.mean():6.3f}  worst {ref.max():6.3f}')
        for name in cand:
            per = np.array([h7.rmse(d.y, d[name]) for _, d in D[fam].groupby('fold')])
            won = int((per < ref).sum())
            res[f'{fam}:{name}'] = dict(mean=float(per.mean()), worst=float(per.max()),
                                        delta=float(per.mean() - ref.mean()),
                                        folds_won=f'{won}/{len(per)}')
            print(f'  {name:14s} mean {per.mean():6.3f}  worst {per.max():6.3f}  '
                  f'vs hbt {per.mean()-ref.mean():+.3f}  {won}/{len(per)}', flush=True)

    if set(fams) == {'P', 'Q', 'R'}:
        ref_b = h7.report('v8 baseline', D, h7.BASE)
        for name in cand:
            res[f'blend:{name}'] = h7.report(f'  +{name}', D, h7.BASE + [name], ref_b)

    json.dump(res, open(f'outputs/exp37_res_{"".join(fams)}.json', 'w'), indent=1)
    print(f'\ntotal {time.time()-t0:.0f}s')
