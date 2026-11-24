"""Re-open the member question under the corrected blend.

Every member verdict in sections 50-53 was taken with BLEND_SHRINK at 0.25, where section
105 has since measured the adoption floor at -0.013 -- roughly the size of the effects those
sections were weighing. With the floor at 0.000 and NNLS free to allocate, the same
candidates are worth re-running, and so are the two plan routes nobody has tried.

Candidates are fixed here before anything is scored. Each has a stated mechanism:

  lin          piecewise-LINEAR leaves. Constant-leaf ensembles compress the predicted
               spread (s35) and cannot extrapolate; linear leaves do neither. s50 measured
               -0.014 at 11/15, which is inside what the old floor gave away for free.
  cat_mae      CatBoost with plain MAE. s52 found the shipped Huber:delta=4 costs it 0.918
               solo. s53 rejected the swap because the repaired model correlates 0.926 with
               hbt -- but that was a SWAP under a uniform floor, not an addition under free
               NNLS.
  hbt_e        the tree fitted in vapour-pressure space. Residual correlation with hbt is
               0.682, the lowest of any tree candidate in this log.
  xt           extra-trees. Different variance profile, same feature set.
  bag_nopress  hbt without the ten pressure level and lag columns   (plan task 4,
  bag_norange  hbt without the diurnal-range block                   feature-group bagging)
  core_chu     the robust core plus the section 104 day-statistics block. The core throws
               away every range column; the CHU columns put that information back through a
               channel whose private support is 1.000 instead of 0.818.
  recent45     hbt trained only on the 45 days before the fold cut (plan task 5, temporal
               bagging). Tests concept drift without per-row recency weighting, which s20
               rejected.
"""
from __future__ import annotations
import os, pickle, sys, time
import numpy as np, pandas as pd
sys.path[:0] = ['.', 'src']
import final_pipeline as fp
import lightgbm as lgb, catboost as cb
from chu_block import chu_block
from robust_eval import feature_groups, support_fraction

CACHE = 'outputs/zoo17_oof.pkl'
g = fp.load_grid(); c = fp.clean_exog(g)
F = fp.make_features(g)
CHU = chu_block(c, fp.es)
FC = pd.concat([F, CHU], axis=1).replace([np.inf, -np.inf], np.nan)
y = g[fp.TARGET]; idx = g.index
is_tr = (g.is_test == 0).values & y.notna().values
is_te = (g.is_test == 1).values

cov = support_fraction(F.loc[is_tr], F.loc[is_te])
G = feature_groups(F.columns, cov)
covc = support_fraction(FC.loc[is_tr], FC.loc[is_te])
CHU_OK = [k for k in CHU.columns if covc[k] >= 0.916]
CORE = G['stable_core']
print("groups: full %d  no_pressure %d  no_range %d  stable_core %d  chu kept %s"
      % (len(G['full']), len(G['no_pressure']), len(G['no_shifted_range']), len(CORE), CHU_OK))

SPEC = {
    'lin':         dict(frame='F',  cols=None,                      kind='lin'),
    'cat_mae':     dict(frame='F',  cols=None,                      kind='cat_mae'),
    'hbt_e':       dict(frame='F',  cols=None,                      kind='hbt_e'),
    'xt':          dict(frame='F',  cols=None,                      kind='xt'),
    'bag_nopress': dict(frame='F',  cols=G['no_pressure'],           kind='hbt'),
    'bag_norange': dict(frame='F',  cols=G['no_shifted_range'],      kind='hbt'),
    'core_chu':    dict(frame='FC', cols=CORE + CHU_OK,              kind='hbt'),
    'recent45':    dict(frame='F',  cols=None,                       kind='hbt', window=45),
}

def fit(kind, Xtr, ytr, Xva, esv, etr, seeds=fp.SEEDS_OOF):
    if kind == 'hbt':
        return fp.predict('hbt', Xtr, ytr, Xva, esv, etr, seeds)
    if kind == 'lin':
        kw = dict(fp.LGB_KW); kw.update(linear_tree=True, num_leaves=7, reg_lambda=30.0,
                                        linear_lambda=10.0, n_estimators=600, learning_rate=0.04)
        return np.mean([lgb.LGBMRegressor(random_state=s, **kw).fit(Xtr, ytr).predict(Xva)
                        for s in seeds], 0)
    if kind == 'hbt_e':
        kw = dict(fp.LGB_KW); kw.update(alpha=0.5)
        p = np.mean([lgb.LGBMRegressor(random_state=s, **kw).fit(Xtr, etr).predict(Xva)
                     for s in seeds], 0)
        return 100.0 * p / esv
    if kind == 'cat_mae':
        return np.mean([cb.CatBoostRegressor(iterations=1200, learning_rate=0.035, depth=6,
                        l2_leaf_reg=6.0, loss_function='MAE', random_seed=s, verbose=0,
                        allow_writing_files=False).fit(Xtr, ytr).predict(Xva) for s in seeds], 0)
    if kind == 'xt':
        from sklearn.ensemble import ExtraTreesRegressor
        from sklearn.impute import SimpleImputer
        im = SimpleImputer(strategy='median').fit(Xtr)
        return np.mean([ExtraTreesRegressor(n_estimators=400, min_samples_leaf=4,
                        max_features=0.5, random_state=s, n_jobs=-1)
                        .fit(im.transform(Xtr), ytr).predict(im.transform(Xva))
                        for s in seeds], 0)
    raise ValueError(kind)

frame = pickle.load(open('outputs/robust_core_scored.pkl', 'rb'))['frame']
folds = frame[['family', 'fold']].drop_duplicates().itertuples(index=False, name=None)
FOLDS = [(f, int(k), pd.DatetimeIndex(frame.loc[(frame.family == f) & (frame.fold == k), 'datetime']))
         for f, k in folds]
cache = pickle.load(open(CACHE, 'rb')) if os.path.exists(CACHE) else {}
t0 = time.time()
for name, spec in SPEC.items():
    X = FC if spec['frame'] == 'FC' else F
    cols = spec['cols'] or list(X.columns)
    for family, fold, vi in FOLDS:
        key = (name, family, fold)
        if key in cache and cache[key].index.equals(vi):
            continue
        cut = vi.min() - pd.Timedelta(minutes=30)
        trm = is_tr & (idx <= cut)
        if spec.get('window'):
            trm = trm & (idx > cut - pd.Timedelta(days=spec['window']))
        vam = idx.isin(vi)
        if trm.sum() < 1000:
            raise SystemExit("%s %s%d: only %d training rows" % (name, family, fold, trm.sum()))
        p = fit(spec['kind'], X.loc[trm, cols], y[trm].values, X.loc[vam, cols],
                fp.es(X.loc[vam, 'T'].values),
                y[trm].values * fp.es(X.loc[trm, 'T'].values) / 100.0)
        cache[key] = pd.Series(np.clip(p, 5, 100), index=idx[vam])
        pickle.dump(cache, open(CACHE, 'wb'))
    print("%-12s done (%.0fs, %d train rows last fold)" % (name, time.time() - t0, trm.sum()), flush=True)
print("cached keys:", len(cache))
