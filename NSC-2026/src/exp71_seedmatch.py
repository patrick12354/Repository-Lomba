"""The out-of-fold members are fitted with three seeds; the shipped ones with five.

Section 68 measured per-row seed sd at 0.37 %RH for `hbt` and 5.49 for `cat`, so the OOF
`cat` carries about 3.17 %RH of Monte-Carlo error against the shipped 2.45. NNLS is therefore
shown a noisier `cat` than the one it will weight, and `cat` is the load-bearing member of
v19 (drop-one +0.215). Section 71 already classes this as a defect rather than a
hyper-parameter: matching the counts adds no free parameter and can only remove bias.

This refits every stochastic member out-of-fold at five seeds and rescores. `ridge`, `enet`
and `ridge_e` are deterministic and are reused unchanged.
"""
import os, pickle, sys, time
import numpy as np, pandas as pd
sys.path[:0] = ['.', 'src']
import final_pipeline as fp

CACHE = 'outputs/seed5_oof.pkl'
SEEDS5 = (0, 1, 2, 3, 4)
g = fp.load_grid(); F = fp.make_features(g); y = g[fp.TARGET]; idx = g.index
is_tr = (g.is_test == 0).values & y.notna().values
is_te = (g.is_test == 1).values
CORE = fp.stable_core(F, (g.is_test == 0).values, is_te)
NOPRESS = fp.no_pressure(F)
VIEWS = {'hbt': None, 'cat': None, 'l2': None, 'robust_hbt': CORE, 'bag_nopress': NOPRESS}

frame = pickle.load(open('outputs/robust_core_scored.pkl','rb'))['frame']
FOLDS = [(f, int(k), pd.DatetimeIndex(frame.loc[(frame.family==f)&(frame.fold==k),'datetime']))
         for f, k in frame[['family','fold']].drop_duplicates().itertuples(index=False, name=None)]
cache = pickle.load(open(CACHE,'rb')) if os.path.exists(CACHE) else {}
t0 = time.time()
for name, cols in VIEWS.items():
    c = cols or list(F.columns)
    for family, fold, vi in FOLDS:
        key = (name, family, fold)
        if key in cache and cache[key].index.equals(vi):
            continue
        cut = vi.min() - pd.Timedelta(minutes=30)
        trm = is_tr & (idx <= cut); vam = idx.isin(vi)
        p = fp.predict(fp.base_model(name), F.loc[trm, c], y[trm].values, F.loc[vam, c],
                       fp.es(F.loc[vam,'T'].values),
                       y[trm].values*fp.es(F.loc[trm,'T'].values)/100.0, SEEDS5)
        cache[key] = pd.Series(np.clip(p, 5, 100), index=idx[vam])
        pickle.dump(cache, open(CACHE,'wb'))
    print("%-12s refitted at 5 seeds (%.0fs)" % (name, time.time()-t0), flush=True)
print("done, %d keys" % len(cache))
