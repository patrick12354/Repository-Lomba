"""Model zoo + rolling-origin 15-day-block CV that mirrors the real test setup."""
import warnings, numpy as np, pandas as pd
warnings.filterwarnings('ignore')
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from common import *
from sklearn.linear_model import Ridge, ElasticNet, HuberRegressor
from sklearn.ensemble import ExtraTreesRegressor
from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from scipy.optimize import nnls
import lightgbm as lgb, xgboost as xgb, catboost as cb

SEED = 42

def make_models(which, seed=SEED):
    z = {}
    if 'lgbm' in which:
        z['lgbm'] = lgb.LGBMRegressor(n_estimators=1200, learning_rate=0.02, num_leaves=31,
            min_child_samples=25, subsample=0.8, subsample_freq=1, colsample_bytree=0.6,
            reg_lambda=3.0, random_state=seed, verbose=-1)
    if 'lgbm_huber' in which:
        z['lgbm_huber'] = lgb.LGBMRegressor(objective='huber', alpha=3.0, n_estimators=1400,
            learning_rate=0.02, num_leaves=31, min_child_samples=25, subsample=0.8,
            subsample_freq=1, colsample_bytree=0.6, reg_lambda=3.0, random_state=seed, verbose=-1)
    if 'lgbm_shallow' in which:
        z['lgbm_shallow'] = lgb.LGBMRegressor(n_estimators=2000, learning_rate=0.02, num_leaves=8,
            min_child_samples=40, subsample=0.8, subsample_freq=1, colsample_bytree=0.5,
            reg_lambda=5.0, random_state=seed, verbose=-1)
    if 'xgb' in which:
        z['xgb'] = xgb.XGBRegressor(n_estimators=1200, learning_rate=0.02, max_depth=5,
            min_child_weight=5, subsample=0.8, colsample_bytree=0.6, reg_lambda=3.0,
            random_state=seed, tree_method='hist', verbosity=0)
    if 'cat' in which:
        z['cat'] = cb.CatBoostRegressor(iterations=1500, learning_rate=0.03, depth=6,
            l2_leaf_reg=6.0, random_seed=seed, verbose=0, allow_writing_files=False)
    if 'et' in which:
        z['et'] = ExtraTreesRegressor(n_estimators=500, min_samples_leaf=3, max_features=0.5,
            n_jobs=-1, random_state=seed)
    if 'ridge' in which:
        z['ridge'] = make_pipeline(SimpleImputer(strategy='median'), StandardScaler(), Ridge(alpha=20.0))
    if 'enet' in which:
        z['enet'] = make_pipeline(SimpleImputer(strategy='median'), StandardScaler(),
                                  ElasticNet(alpha=0.05, l1_ratio=0.5, max_iter=8000))
    return z


def make_folds(dt_tr, n_folds=5, val_days=15, step_days=5):
    """Rolling origin: each fold trains on everything before a cut, validates the next
    `val_days`. Last fold's validation ends at the end of train, i.e. the slice that
    sits immediately before the real test window."""
    end = dt_tr.max()
    folds = []
    for i in range(n_folds):
        v_end = end - pd.Timedelta(days=step_days * i)
        v_start = v_end - pd.Timedelta(days=val_days)
        folds.append((v_start, v_end))
    return folds[::-1]


def run_cv(name, feats, y_rh, T_clean, is_tr, models=('lgbm','lgbm_huber','cat','et','ridge','enet'),
           target='rh', folds=None, seeds=(SEED,), notes='', save_oof=True, log=True):
    """feats/y_rh/T_clean indexed by the full 30-min grid. is_tr marks labelled rows."""
    idx = feats.index
    tr_mask = is_tr & y_rh.notna()
    dt_tr = idx[tr_mask]
    if folds is None:
        folds = make_folds(dt_tr)

    y_model = y_rh if target == 'rh' else pd.Series(rh_to_td(y_rh.values, T_clean.values), index=idx)

    oof = {m: pd.Series(np.nan, index=idx) for m in models}
    fold_ids = pd.Series(np.nan, index=idx)
    per_fold = {}

    for fi, (vs, ve) in enumerate(folds):
        vm = tr_mask & (idx > vs) & (idx <= ve)
        tm = tr_mask & (idx <= vs)
        if tm.sum() < 300 or vm.sum() < 50:
            continue
        Xtr, Xva = feats[tm], feats[vm]
        ytr = y_model[tm]
        fold_ids[vm] = fi
        for mname in models:
            preds = []
            for sd in seeds:
                mdl = make_models([mname], sd)[mname]
                mdl.fit(Xtr, ytr)
                preds.append(mdl.predict(Xva))
            p = np.mean(preds, axis=0)
            if target == 'td':
                p = td_to_rh(p, T_clean[vm].values)
            oof[mname][vm] = np.clip(p, 5, 100)
        per_fold[f'F{fi}'] = dict(start=str(vs)[:10], end=str(ve)[:10], n=int(vm.sum()))

    O = pd.DataFrame(oof)
    valid = O.notna().all(axis=1) & tr_mask
    ytrue = y_rh[valid]

    per_model = {}
    for m in models:
        pf = [rmse(y_rh[valid & (fold_ids == f)], O[m][valid & (fold_ids == f)])
              for f in sorted(fold_ids[valid].unique())]
        per_model[m] = dict(mean_cv=float(np.mean(pf)), pooled=rmse(ytrue, O[m][valid]),
                            folds=[round(x, 4) for x in pf])

    # non-negative least squares blend on pooled OOF
    A = O[list(models)][valid].values
    w, _ = nnls(A, ytrue.values)
    if w.sum() > 0:
        w = w / w.sum()
    else:
        w = np.ones(len(models)) / len(models)
    blend = pd.Series(np.nan, index=idx)
    blend[valid] = A @ w
    bf = [rmse(y_rh[valid & (fold_ids == f)], blend[valid & (fold_ids == f)])
          for f in sorted(fold_ids[valid].unique())]

    rec = dict(name=name, target=target, n_feats=feats.shape[1], models=list(models),
               seeds=len(seeds), notes=notes,
               mean_cv=float(np.mean(bf)), last_fold=float(bf[-1]), std_cv=float(np.std(bf)),
               pooled=rmse(ytrue, blend[valid]), folds=[round(x, 4) for x in bf],
               weights={m: round(float(x), 4) for m, x in zip(models, w)},
               per_model={m: per_model[m]['mean_cv'] for m in models},
               fold_spans=per_fold)
    if log:
        log_experiment(rec, OUT + 'experiments2.jsonl')
    if save_oof:
        os.makedirs(OUT + 'oof2', exist_ok=True)
        out = O.copy(); out['blend'] = blend; out['y'] = y_rh; out['fold'] = fold_ids
        out[valid].to_csv(f'{OUT}oof2/{name}.csv')
    return rec, O, blend, fold_ids, w


def fit_predict_test(feats, y_rh, T_clean, is_tr, is_te, models, weights, target='rh', seeds=(SEED,)):
    idx = feats.index
    tm = is_tr & y_rh.notna()
    y_model = y_rh if target == 'rh' else pd.Series(rh_to_td(y_rh.values, T_clean.values), index=idx)
    P = {}
    for mname in models:
        ps = []
        for sd in seeds:
            mdl = make_models([mname], sd)[mname]
            mdl.fit(feats[tm], y_model[tm])
            ps.append(mdl.predict(feats[is_te]))
        p = np.mean(ps, axis=0)
        if target == 'td':
            p = td_to_rh(p, T_clean[is_te].values)
        P[mname] = np.clip(p, 5, 100)
    M = pd.DataFrame(P, index=idx[is_te])
    return M[list(models)].values @ np.asarray(weights), M


def fmt(rec):
    f = ' '.join(f'{x:6.3f}' for x in rec['folds'])
    w = ' '.join(f'{k}={v:.2f}' for k, v in rec['weights'].items() if v > 0.01)
    return f"{rec['name']:24s} [{f}] mean {rec['mean_cv']:.4f} pooled {rec['pooled']:.4f} | {w}"
