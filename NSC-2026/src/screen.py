"""Fast screening harness: rolling origins, cheap models, ranking only.

Fold windows overlap, so every fold's predictions are kept separately (a long
frame keyed by (fold, datetime)) instead of being written into one OOF series.
"""
import warnings; warnings.filterwarnings('ignore')
import sys, os, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
from common import *
import lightgbm as lgb
from sklearn.linear_model import Ridge, ElasticNet
from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import ExtraTreesRegressor
import xgboost as xgb_, catboost as cb_
from scipy.optimize import nnls

def MK(seed=0):
    return {
      'lgbm': lgb.LGBMRegressor(n_estimators=600, learning_rate=0.04, num_leaves=31,
          min_child_samples=25, subsample=0.8, subsample_freq=1, colsample_bytree=0.6,
          reg_lambda=3., random_state=seed, verbose=-1),
      'lgbm_hub': lgb.LGBMRegressor(objective='huber', alpha=4.0, n_estimators=700,
          learning_rate=0.04, num_leaves=31, min_child_samples=25, subsample=0.8,
          subsample_freq=1, colsample_bytree=0.6, reg_lambda=3., random_state=seed, verbose=-1),
      'ridge': make_pipeline(SimpleImputer(strategy='median'), StandardScaler(), Ridge(alpha=20.)),
      'enet': make_pipeline(SimpleImputer(strategy='median'), StandardScaler(),
                            ElasticNet(alpha=0.05, l1_ratio=0.5, max_iter=8000)),
      'lgbm_sh': lgb.LGBMRegressor(n_estimators=1400, learning_rate=0.03, num_leaves=8,
          min_child_samples=40, subsample=0.8, subsample_freq=1, colsample_bytree=0.5,
          reg_lambda=5., random_state=seed, verbose=-1),
      'xgb': xgb_.XGBRegressor(n_estimators=800, learning_rate=0.04, max_depth=5,
          min_child_weight=5, subsample=0.8, colsample_bytree=0.6, reg_lambda=3.,
          random_state=seed, tree_method='hist', verbosity=0, n_jobs=4),
      'cat': cb_.CatBoostRegressor(iterations=900, learning_rate=0.05, depth=6,
          l2_leaf_reg=6., random_seed=seed, verbose=0, allow_writing_files=False),
      'et': ExtraTreesRegressor(n_estimators=400, min_samples_leaf=3, max_features=0.5,
          n_jobs=-1, random_state=seed),
    }

def origins(idx, n=9, val_days=15, step_days=2, min_train_days=30):
    d0, end, outs = idx.min(), idx.max(), []
    for i in range(n):
        cut = end - pd.Timedelta(days=step_days * i)
        vs = cut - pd.Timedelta(days=val_days)
        if (vs - d0).days < min_train_days: break
        outs.append((vs, cut))
    return outs[::-1]


def raw_oof(F, y, T, is_tr, target='rh', models=('lgbm','lgbm_hub','ridge','enet'),
            folds=None, seeds=(0,)):
    """Return a long frame: one row per (fold, timestamp) with each model's prediction."""
    idx = F.index
    tr = is_tr & y.notna()
    if folds is None: folds = origins(idx[tr])
    ym = y if target == 'rh' else pd.Series(rh_to_td(y.values, T.values), index=idx)
    chunks = []
    for fi, (vs, ve) in enumerate(folds):
        v = tr & (idx > vs) & (idx <= ve); t = tr & (idx <= vs)
        if t.sum() < 300 or v.sum() < 50: continue
        d = pd.DataFrame({'fold': fi, 'dt': idx[v], 'y': y[v].values})
        for m in models:
            ps = []
            for sd in seeds:
                mdl = MK(sd)[m]; mdl.fit(F[t], ym[t]); ps.append(mdl.predict(F[v]))
            p = np.mean(ps, axis=0)
            if target == 'td': p = td_to_rh(p, T[v].values)
            d[m] = np.clip(p, 5, 100)
        chunks.append(d)
    return pd.concat(chunks, ignore_index=True), list(models)


def evaluate(name, L, models, smooth=0, verbose=True):
    """Score a long OOF frame. `smooth` applies a centered rolling mean within each fold."""
    L = L.copy()
    if smooth:
        for m in models:
            L[m] = L.groupby('fold')[m].transform(
                lambda s: s.rolling(smooth, center=True, min_periods=1).mean())
    A, yy = L[models].values, L['y'].values
    w, _ = nnls(A, yy); w = w / w.sum() if w.sum() > 0 else np.ones(len(models)) / len(models)
    L['blend'] = A @ w
    per = L.groupby('fold').apply(lambda d: rmse(d.y, d.blend))
    pm = {m: round(float(L.groupby('fold').apply(lambda d: rmse(d.y, d[m])).mean()), 3) for m in models}
    res = dict(name=name, smooth=smooth, mean=float(per.mean()), med=float(per.median()),
               worst=float(per.max()), folds=[round(x, 2) for x in per.values], per_model=pm,
               w={m: round(float(x), 3) for m, x in zip(models, w)})
    if verbose:
        print(f"{name:28s} mean {res['mean']:6.3f} med {res['med']:6.3f} worst {res['worst']:6.3f} | {res['folds']}", flush=True)
        print(f"{'':28s} {pm}  w={ {k: v for k, v in res['w'].items() if v > 0.02} }", flush=True)
    return res
