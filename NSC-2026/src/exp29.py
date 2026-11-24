"""Two cheap remaining levers, both scored with the s=1.05 expansion applied:
  1. averaging over the hyper-parameter plateau instead of standing on one point
  2. pruning the 118 columns by gain importance
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

BASE = dict(V7KW); BASE['alpha'] = 2.0
PLATEAU = [dict(alpha=2.0, num_leaves=15), dict(alpha=2.0, num_leaves=11),
           dict(alpha=3.0, num_leaves=15), dict(alpha=2.0, num_leaves=21, colsample_bytree=1.0)]


def run_multi(Fx, cfgs, seeds, folds):
    out = []
    for fi, (vs, ve) in enumerate(folds):
        v = tr & (IDX > vs) & (IDX <= ve); t = tr & (IDX <= vs)
        ps = []
        for cf in cfgs:
            kw = dict(BASE); kw.update(cf)
            for sd in seeds:
                ps.append(lgb.LGBMRegressor(random_state=sd, **kw).fit(Fx[t], y[t]).predict(Fx[v]))
        p = np.clip(np.mean(ps, 0), 5, 100)
        m = p.mean(); p = np.clip(m + S * (p - m), 5, 100)
        out.append(pd.DataFrame(dict(fold=fi, dt=IDX[v], y=y[v].values, p=p)))
    return pd.concat(out, ignore_index=True)


def score(name, Fx, cfgs, seeds, ref=None):
    per, keep = {}, {}
    for fam, folds in FAM.items():
        D = run_multi(Fx, cfgs, seeds, folds)
        pf = D.groupby('fold').apply(lambda d: rmse(d.y, d.p))
        per[fam] = (float(pf.mean()), float(pf.max())); keep[fam] = pf
    avg = float(np.mean([per[f][0] for f in FAM]))
    line = f'  {name:30s}({Fx.shape[1]:3d}) ' + ' '.join(f'{f} {per[f][0]:6.3f}' for f in FAM) + f'  avg {avg:6.3f}'
    if ref is not None:
        won = sum(int((keep[f].values < ref[f].values).sum()) for f in FAM)
        tot = sum(len(ref[f]) for f in FAM)
        line += f'  folds {won}/{tot}'
    print(line, flush=True)
    return dict(name=name, avg=avg, n=int(Fx.shape[1])), keep


RES = []
r, REF = score('single config, 3 seeds', F, [{}], (0, 1, 2)); RES.append(r)
r, _ = score('single config, 6 seeds', F, [{}], tuple(range(6)), REF); RES.append(r)
r, _ = score('plateau avg (4 cfg x 2 seeds)', F, PLATEAU, (0, 1), REF); RES.append(r)
r, _ = score('plateau avg (4 cfg x 3 seeds)', F, PLATEAU, (0, 1, 2), REF); RES.append(r)

imp = np.zeros(F.shape[1])
for sd in (0, 1, 2):
    m = lgb.LGBMRegressor(random_state=sd, **BASE).fit(F[tr], y[tr])
    imp += m.booster_.feature_importance('gain')
order = pd.Series(imp, index=F.columns).sort_values(ascending=False)
print('\n  top 12 by gain:', list(order.head(12).index), flush=True)
print('  bottom 12 by gain:', list(order.tail(12).index), flush=True)
for k in (20, 40, 60):
    keepc = list(order.head(F.shape[1] - k).index)
    r, _ = score(f'prune bottom {k}', F[keepc], [{}], (0, 1, 2), REF); RES.append(r)

json.dump(RES, open('outputs/exp29_res.json', 'w'), indent=1, default=float)
print('\n=== RANKING ===', flush=True)
for r in sorted(RES, key=lambda r: r['avg']):
    print(f"  {r['name']:32s} avg {r['avg']:6.3f}", flush=True)
