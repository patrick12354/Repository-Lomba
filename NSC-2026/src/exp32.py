"""Warm-start, done so the model can actually learn it.

exp31's version was constant across every training row in a fold -- the training rows all
sit before the cut, so `hours since the cut` was always <= 0 and `RH at the cut` was one
number. LightGBM gave those columns zero splits and the result was bit-identical to base.

Fix: horizon-aware augmentation. Each training row gets a *pseudo-cut* drawn uniformly
from 0.5 h to 15 days before it, so the horizon varies across the training set with the
same distribution the validation window has. At validation the real cut is used. Only
training-period targets are ever read.
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
MAXH = 15 * 24.0


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


V8 = pd.concat([build_v7(c), qblock(c, TMIN_WINS_V7, 0.05),
                qblock(c, CO2_WINS_V7, 0.05, 'co2', rh=False)], axis=1)
V8 = V8.replace([np.inf, -np.inf], np.nan)
IDX = V8.index
tr_all = (is_tr & y.notna())

# pre-compute trailing statistics of the target on the 30-min grid; index i means
# "the target's behaviour up to and including position i"
yv = y.values
pos = pd.Series(np.arange(len(IDX)), index=IDX)
roll_mean72 = y.rolling(145, min_periods=6).mean().values
roll_min72 = y.rolling(145, min_periods=6).min().values
roll_max72 = y.rolling(145, min_periods=6).max().values


def ws_features(row_pos, cut_pos):
    """row_pos, cut_pos are integer positions on the grid; cut_pos <= row_pos."""
    h = (row_pos - cut_pos) * 0.5              # hours since the last observed target
    last = yv[cut_pos]
    m72 = roll_mean72[cut_pos]
    return np.column_stack([
        last,
        np.clip(h, 0, MAXH),
        last * np.exp(-np.clip(h, 0, MAXH) / 24.0),
        m72,
        roll_max72[cut_pos] - roll_min72[cut_pos],
    ])


WSCOLS = ['ws_last', 'ws_h', 'ws_decay', 'ws_mean72', 'ws_rng72']


def build_fold(t_mask, v_mask, cut_ts, rng, n_aug=2):
    tp = pos[t_mask].values
    vp = pos[v_mask].values
    cutp = int(pos.loc[cut_ts]) if cut_ts in pos.index else int(pos[pos.index <= cut_ts].iloc[-1])
    Xs, ys_ = [], []
    for _ in range(n_aug):
        # pseudo-cut uniform in (0.5h, 15d) before each training row, floored at the
        # first grid position that has an observed target
        hrs = rng.uniform(0.5, MAXH, size=len(tp))
        cp = np.maximum(tp - (hrs * 2).astype(int), 0)
        ok = np.isfinite(yv[cp])
        # walk back to the nearest observed target
        for _i in range(6):
            bad = ~np.isfinite(yv[cp])
            if not bad.any(): break
            cp[bad] = np.maximum(cp[bad] - 1, 0)
        ok = np.isfinite(yv[cp])
        W = ws_features(tp[ok], cp[ok])
        Xs.append(np.hstack([V8.values[tp[ok]], W]))
        ys_.append(yv[tp[ok]])
    Xtr = np.vstack(Xs); ytr = np.concatenate(ys_)
    Wv = ws_features(vp, np.full(len(vp), cutp))
    Xva = np.hstack([V8.values[vp], Wv])
    return Xtr, ytr, Xva


def run(folds, use_ws, seeds=(0, 1, 2), n_aug=2):
    out = []
    rng = np.random.default_rng(0)
    for fi, (vs, ve) in enumerate(folds):
        v = tr_all & (IDX > vs) & (IDX <= ve); t = tr_all & (IDX <= vs)
        if use_ws:
            Xtr, ytr, Xva = build_fold(t, v, vs, rng, n_aug)
            cols = list(V8.columns) + WSCOLS
        else:
            Xtr, ytr, Xva = V8.values[pos[t].values], yv[pos[t].values], V8.values[pos[v].values]
            cols = list(V8.columns)
        dtr = pd.DataFrame(Xtr, columns=cols); dva = pd.DataFrame(Xva, columns=cols)
        p = np.mean([lgb.LGBMRegressor(random_state=sd, **BASE).fit(dtr, ytr).predict(dva)
                     for sd in seeds], 0)
        p = np.clip(p, 5, 100); m = p.mean(); p = np.clip(m + S * (p - m), 5, 100)
        out.append(pd.DataFrame(dict(fold=fi, dt=IDX[v], y=yv[pos[v].values], p=p)))
    return pd.concat(out, ignore_index=True)


RES, REF = [], None
for name, ws, na in [('v9_base', False, 0), ('+warmstart aug x2', True, 2), ('+warmstart aug x4', True, 4)]:
    per, keep, Ds = {}, {}, {}
    for fam, folds in FAM.items():
        D = run(folds, ws, n_aug=na if na else 2)
        pf = D.groupby('fold').apply(lambda d: rmse(d.y, d.p))
        per[fam] = (float(pf.mean()), float(pf.max())); keep[fam] = pf; Ds[fam] = D
    avg = float(np.mean([per[f][0] for f in FAM]))
    line = f'  {name:20s} ' + ' '.join(f'{f} {per[f][0]:6.3f}/{per[f][1]:6.3f}' for f in FAM) + f'  avg {avg:6.3f}'
    if REF is None:
        REF = keep; REFD = Ds
    else:
        won = sum(int((keep[f].values < REF[f].values).sum()) for f in FAM)
        tot = sum(len(REF[f]) for f in FAM)
        line += f'  folds {won}/{tot}'
    print(line, flush=True)
    RES.append(dict(name=name, avg=avg))
    if ws:
        # does it help early in the window, where persistence should matter?
        D = Ds['P']; R = REFD['P']
        M = R[['fold', 'dt', 'y', 'p']].merge(D[['fold', 'dt', 'p']], on=['fold', 'dt'], suffixes=('_r', '_w'))
        M['h'] = (M.dt - M.groupby('fold').dt.transform('min')).dt.total_seconds() / 86400
        M['hb'] = pd.cut(M.h, [-.01, 1, 3, 7, 15.1], labels=['0-1d', '1-3d', '3-7d', '7-15d'])
        z = M.groupby('hb', observed=True).apply(lambda d: pd.Series(
            {'base': rmse(d.y, d.p_r), 'ws': rmse(d.y, d.p_w), 'n': len(d)}))
        z['delta'] = z.ws - z.base
        print(z.round(3).to_string(), flush=True)

json.dump(RES, open('outputs/exp32_res.json', 'w'), indent=1, default=float)
