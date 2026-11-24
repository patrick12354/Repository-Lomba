"""Session-7 harness: model-class diversity on the frozen v8 feature set.

Features come from `final_pipeline.make_features` verbatim, so every experiment here is
scored on exactly the columns the shipped model uses. Three fold families, nested NNLS
blend weights (fit on folds < k, score on fold k) -- the section 22/30 protocol.
"""
import warnings; warnings.filterwarnings('ignore')
import os, sys, pickle, time
import numpy as np, pandas as pd
from scipy.optimize import nnls

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)
import final_pipeline as FP

CACHE = 'outputs/h7_oof.pkl'
BASE = ['hbt', 'cat', 'ridge', 'enet', 'ridge_e']
SHRINK = 0.25


def rmse(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    m = np.isfinite(a) & np.isfinite(b)
    return float(np.sqrt(np.mean((a[m] - b[m]) ** 2)))


def load():
    g = FP.load_grid()
    F = FP.make_features(g)
    y = g[FP.TARGET]
    is_tr = (g.is_test == 0).values & y.notna().values
    return F, y, pd.Series(is_tr, index=g.index), g


def families(idx):
    def fam(n, val_days, step_days, min_train_days=30):
        d0, end, out = idx.min(), idx.max(), []
        for i in range(n):
            cut = end - pd.Timedelta(days=step_days * i)
            vs = cut - pd.Timedelta(days=val_days)
            if (vs - d0).days < min_train_days:
                break
            out.append((vs, cut))
        return out[::-1]
    return {'P': fam(9, 15, 2), 'Q': fam(6, 15, 3, 36), 'R': fam(5, 21, 3, 28)}


# ------------------------------------------------------------------ model zoo
def fit_predict(name, Xtr, ytr, Xva, esv, etr, seeds):
    """`name` in BASE delegates to the shipped pipeline so the baseline is bit-identical.
    Anything else is a session-7 candidate."""
    import lightgbm as lgb
    if name in BASE:
        return FP.predict(name, Xtr, ytr, Xva, esv, etr, seeds)

    if name == 'lin':
        # piecewise-LINEAR leaves. Constant-leaf ensembles compress the predicted spread
        # (s35) and cannot extrapolate at all; linear leaves do both differently.
        kw = dict(FP.LGB_KW); kw.update(linear_tree=True, num_leaves=7, reg_lambda=30.0,
                                        linear_lambda=10.0, n_estimators=600,
                                        learning_rate=0.04)
        return np.mean([lgb.LGBMRegressor(random_state=s, **kw).fit(Xtr, ytr).predict(Xva)
                        for s in seeds], 0)
    if name == 'hbt_e':
        # the hbt model fitted in vapour-pressure space, converted back. Same trick that
        # made ridge_e the one decorrelated linear member (s22), applied to the tree.
        kw = dict(FP.LGB_KW); kw.update(alpha=0.5)
        p = np.mean([lgb.LGBMRegressor(random_state=s, **kw).fit(Xtr, etr).predict(Xva)
                     for s in seeds], 0)
        return 100.0 * p / esv
    if name == 'dart':
        kw = dict(FP.LGB_KW); kw.update(boosting_type='dart', drop_rate=0.1,
                                        n_estimators=700)
        return np.mean([lgb.LGBMRegressor(random_state=s, **kw).fit(Xtr, ytr).predict(Xva)
                        for s in seeds], 0)
    if name == 'xt':
        from sklearn.ensemble import ExtraTreesRegressor
        from sklearn.impute import SimpleImputer
        im = SimpleImputer(strategy='median').fit(Xtr)
        return np.mean([ExtraTreesRegressor(n_estimators=400, min_samples_leaf=4,
                                            max_features=0.5, random_state=s, n_jobs=-1)
                        .fit(im.transform(Xtr), ytr).predict(im.transform(Xva))
                        for s in seeds], 0)
    if name == 'mlp':
        from sklearn.neural_network import MLPRegressor
        return np.mean([FP._pipe(MLPRegressor(hidden_layer_sizes=(128, 64), alpha=3.0,
                                              learning_rate_init=3e-3, max_iter=600,
                                              early_stopping=True, n_iter_no_change=25,
                                              random_state=s))
                        .fit(Xtr, ytr).predict(Xva) for s in seeds], 0)
    if name == 'krr':
        from sklearn.kernel_ridge import KernelRidge
        return FP._pipe(KernelRidge(alpha=3.0, kernel='rbf', gamma=1.0 / Xtr.shape[1])) \
            .fit(Xtr, ytr).predict(Xva)
    raise ValueError(name)


# ------------------------------------------------------------------ oof driver
def oof(models, F=None, y=None, is_tr=None, seeds=(0, 1, 2), fams=None, tag=''):
    """Returns {family: DataFrame(fold, dt, y, <model columns>)}. Cached per
    (family, fold, model, tag) so adding a candidate never recomputes the baseline."""
    if F is None:
        F, y, is_tr, _ = load()
    cache = pickle.load(open(CACHE, 'rb')) if os.path.exists(CACHE) else {}
    IDX = F.index
    tr = is_tr.values
    esT = pd.Series(FP.es(F['T'].values), index=IDX)
    E = y * esT / 100.0
    FAM = families(IDX[tr])
    out, dirty = {}, False
    for fam, folds in FAM.items():
        if fams and fam not in fams:
            continue
        rows = []
        for fi, (vs, ve) in enumerate(folds):
            v = tr & (IDX > vs) & (IDX <= ve)
            t = tr & (IDX <= vs)
            if t.sum() < 300 or v.sum() < 50:
                continue
            d = pd.DataFrame(dict(fold=fi, dt=IDX[v], y=y[v].values))
            for m in models:
                key = (fam, fi, m, tag, seeds)
                if key not in cache:
                    t0 = time.time()
                    p = fit_predict(m, F[t], y[t], F[v], esT[v].values, E[t], seeds)
                    cache[key] = np.clip(p, 5, 100)
                    dirty = True
                    print(f'    computed {fam}{fi} {m} ({time.time()-t0:.0f}s)', flush=True)
                d[m] = cache[key]
            if dirty:
                # checkpoint per fold: a long run that dies should never lose fits
                pickle.dump(cache, open(CACHE + '.tmp', 'wb'))
                os.replace(CACHE + '.tmp', CACHE)
                dirty = False
            rows.append(d)
        out[fam] = pd.concat(rows, ignore_index=True)
    return out


def nested(D, models, shrink=SHRINK):
    """NNLS weights fitted on folds < k only, scored on fold k. Fold 0 is unscoreable."""
    per, wlast = [], None
    for k in sorted(D.fold.unique()):
        prev, cur = D[D.fold < k], D[D.fold == k]
        if len(prev) == 0:
            continue
        w, _ = nnls(prev[models].values, prev.y.values)
        w = w / w.sum() if w.sum() > 0 else np.ones(len(models)) / len(models)
        w = (1 - shrink) * w + shrink * np.ones(len(models)) / len(models)
        wlast = w
        per.append(rmse(cur.y, cur[models].values @ w))
    return np.array(per), wlast


def report(name, Ds, models, ref=None):
    means, worst, allfolds = {}, {}, []
    line = f'{name:24s}'
    for fam in ('P', 'Q', 'R'):
        pf, _ = nested(Ds[fam], models)
        means[fam], worst[fam] = float(pf.mean()), float(pf.max())
        allfolds.append(pf)
        line += f' {fam} {pf.mean():6.3f}/{pf.max():6.3f}'
    avg = float(np.mean([means[f] for f in means]))
    line += f'  avg {avg:6.3f}'
    res = dict(name=name, means=means, worst=worst, avg=avg,
               folds=[float(x) for p in allfolds for x in p])
    if ref is not None:
        won = sum(int(a < b) for a, b in zip(res['folds'], ref['folds']))
        res['folds_won'] = f"{won}/{len(res['folds'])}"
        res['delta'] = avg - ref['avg']
        line += f"  | d {res['delta']:+.3f}  {res['folds_won']}"
    print(line, flush=True)
    return res
