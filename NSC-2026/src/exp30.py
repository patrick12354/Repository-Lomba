"""Feature pruning done honestly.

exp29 ranked features by gain importance fitted on ALL training rows, then scored folds
whose validation rows were inside that fit -- the selection saw the targets it was later
judged on. Here the ranking is recomputed inside each fold from that fold's training rows
only, so the choice of columns never sees the validation window.
"""
import warnings; warnings.filterwarnings('ignore')
import sys, json, numpy as np, pandas as pd
sys.path.insert(0, 'src')
from common import *
from featx import build_v7, TMIN_WINS_V7, CO2_WINS_V7
from ab7 import families, V7KW
import lightgbm as lgb

g, _, _ = load_grid()
is_tr = pd.Series((g.is_test == 0).values, index=g.index)
y = g[TARGET]
c = clean_exog(g, k=6.0)
FAM = families(g.index[is_tr & y.notna()])
S = 1.05
BASE = dict(V7KW); BASE['alpha'] = 2.0


def qblock(c, wins, q, col='air_temperature', rh=True):
    s = c[col]; d = {}
    for hrs in wins:
        w = int(hrs * 2) + 1
        lo = s.rolling(w, center=True, min_periods=6).quantile(q)
        hi = s.rolling(w, center=True, min_periods=6).quantile(1 - q)
        d[f'{col}_q{hrs}'] = lo; d[f'{col}_qhi{hrs}'] = hi
        d[f'{col}_qrng{hrs}'] = hi - lo; d[f'{col}_minus_q{hrs}'] = s - lo
        if rh:
            d[f'rh_q{hrs}'] = 100 * es(lo.values) / es(c['air_temperature'].values)
    return pd.DataFrame(d, index=c.index)


F = pd.concat([build_v7(c), qblock(c, TMIN_WINS_V7, 0.05),
               qblock(c, CO2_WINS_V7, 0.05, 'co2', rh=False)], axis=1)
F = F.replace([np.inf, -np.inf], np.nan)
tr = (is_tr & y.notna()); IDX = F.index
print('features', F.shape[1], flush=True)


def run_pruned(keep_n, folds, seeds=(0, 1, 2)):
    out = []
    sel_hist = []
    for fi, (vs, ve) in enumerate(folds):
        v = tr & (IDX > vs) & (IDX <= ve); t = tr & (IDX <= vs)
        if keep_n is None:
            cols = list(F.columns)
        else:
            imp = np.zeros(F.shape[1])
            for sd in (0, 1):
                m = lgb.LGBMRegressor(random_state=sd, **BASE).fit(F[t], y[t])
                imp += m.booster_.feature_importance('gain')
            cols = list(pd.Series(imp, index=F.columns).sort_values(ascending=False).head(keep_n).index)
        sel_hist.append(set(cols))
        p = np.mean([lgb.LGBMRegressor(random_state=sd, **BASE).fit(F.loc[t, cols], y[t])
                     .predict(F.loc[v, cols]) for sd in seeds], 0)
        p = np.clip(p, 5, 100); m_ = p.mean(); p = np.clip(m_ + S * (p - m_), 5, 100)
        out.append(pd.DataFrame(dict(fold=fi, dt=IDX[v], y=y[v].values, p=p)))
    return pd.concat(out, ignore_index=True), sel_hist


RES = []
REF = None
for keep_n in (None, 98, 78, 58, 44, 32):
    per, keep = {}, {}
    stab = None
    for fam, folds in FAM.items():
        D, sel = run_pruned(keep_n, folds)
        pf = D.groupby('fold').apply(lambda d: rmse(d.y, d.p))
        per[fam] = (float(pf.mean()), float(pf.max())); keep[fam] = pf
        if fam == 'P' and keep_n is not None:
            inter = set.intersection(*sel); union = set.union(*sel)
            stab = len(inter) / len(union)
    avg = float(np.mean([per[f][0] for f in FAM]))
    name = 'no pruning' if keep_n is None else f'keep top {keep_n} (nested)'
    line = f'  {name:26s} ' + ' '.join(f'{f} {per[f][0]:6.3f}/{per[f][1]:6.3f}' for f in FAM) + f'  avg {avg:6.3f}'
    if REF is None:
        REF = keep
    else:
        won = sum(int((keep[f].values < REF[f].values).sum()) for f in FAM)
        tot = sum(len(REF[f]) for f in FAM)
        line += f'  folds {won}/{tot}'
    if stab is not None:
        line += f'  sel-stability {stab:.2f}'
    print(line, flush=True)
    RES.append(dict(name=name, avg=avg, keep_n=keep_n))

json.dump(RES, open('outputs/exp30_res.json', 'w'), indent=1, default=float)
print('\n=== RANKING ===', flush=True)
for r in sorted(RES, key=lambda r: r['avg']):
    print(f"  {r['name']:28s} avg {r['avg']:6.3f}", flush=True)
