"""Three last ideas, each tested on all three fold families with the s=1.05 expansion:

  A. warm-start / persistence. The target's own history has never been used. Every fold's
     validation window begins the instant its training window ends -- exactly the real
     test setup -- so "RH at the last observed timestamp" and "hours since then" are
     legitimate forecasting features. They must be built per fold, because they depend on
     where the training cut falls.
  B. soil temperature as an anomaly. The soil block was dropped wholesale for
     extrapolation reasons, but soil_temp LEVELS were 100% inside the training range; only
     the rolling-std columns were unsupported. Deep soil temperature is a multi-day
     low-pass of air temperature, i.e. air-mass memory.
  C. co2 quantiles at 96 h, matching the temperature windows.
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


V8 = pd.concat([build_v7(c), qblock(c, TMIN_WINS_V7, 0.05),
                qblock(c, CO2_WINS_V7, 0.05, 'co2', rh=False)], axis=1)

SOILT = ['soil_temp_line1', 'soil_temp_line2', 'soil_temp_line3']
soil_anom = {}
for col in SOILT:
    s = c[col]
    for hrs in (48, 96):
        w = int(hrs * 2) + 1
        soil_anom[f'{col}_a{hrs}'] = s - s.rolling(w, center=True, min_periods=6).mean()
    soil_anom[f'{col}_minus_T'] = s - c['air_temperature']
SOIL_BLK = pd.DataFrame(soil_anom, index=c.index)
CO2_96 = qblock(c, (96,), 0.05, 'co2', rh=False)


def warmstart(cut):
    """Features that depend on where the training cut falls. `cut` is the last timestamp
    whose target is known; everything after it is being predicted."""
    idx = c.index
    known = y.where(idx <= cut)
    last_val = known.dropna()
    if len(last_val) == 0:
        return pd.DataFrame(index=idx)
    lv = float(last_val.iloc[-1])
    horizon = (idx - cut).total_seconds() / 3600.0
    # RH at the same clock time on the last fully observed day before the cut
    prof = known.last('72H').groupby(known.last('72H').index.hour).mean()
    same_hour = pd.Series(idx.hour, index=idx).map(prof)
    d = {'ws_last': lv,
         'ws_horizon': np.clip(horizon, 0, None),
         'ws_decay': lv * np.exp(-np.clip(horizon, 0, None) / 24.0),
         'ws_samehour': same_hour.values,
         'ws_lastmean': float(known.last('72H').mean())}
    return pd.DataFrame(d, index=idx)


def run(Fbase, folds, use_ws=False, seeds=(0, 1, 2)):
    tr = (is_tr & y.notna()); IDX = Fbase.index
    out = []
    for fi, (vs, ve) in enumerate(folds):
        v = tr & (IDX > vs) & (IDX <= ve); t = tr & (IDX <= vs)
        if use_ws:
            Fx = pd.concat([Fbase, warmstart(vs)], axis=1)
        else:
            Fx = Fbase
        Fx = Fx.replace([np.inf, -np.inf], np.nan)
        p = np.mean([lgb.LGBMRegressor(random_state=sd, **BASE).fit(Fx[t], y[t]).predict(Fx[v])
                     for sd in seeds], 0)
        p = np.clip(p, 5, 100); m = p.mean(); p = np.clip(m + S * (p - m), 5, 100)
        out.append(pd.DataFrame(dict(fold=fi, dt=IDX[v], y=y[v].values, p=p)))
    return pd.concat(out, ignore_index=True)


VAR = {
    'v9_base': (V8, False),
    '+warmstart': (V8, True),
    '+soil_temp_anom': (pd.concat([V8, SOIL_BLK], axis=1), False),
    '+co2_q96': (pd.concat([V8, CO2_96], axis=1), False),
    '+soil+co2q96': (pd.concat([V8, SOIL_BLK, CO2_96], axis=1), False),
}
RES, REF = [], None
for name, (Fb, ws) in VAR.items():
    per, keep = {}, {}
    for fam, folds in FAM.items():
        D = run(Fb, folds, ws)
        pf = D.groupby('fold').apply(lambda d: rmse(d.y, d.p))
        per[fam] = (float(pf.mean()), float(pf.max())); keep[fam] = pf
    avg = float(np.mean([per[f][0] for f in FAM]))
    n = Fb.shape[1] + (5 if ws else 0)
    line = f'  {name:20s}({n:3d}) ' + ' '.join(f'{f} {per[f][0]:6.3f}/{per[f][1]:6.3f}' for f in FAM) + f'  avg {avg:6.3f}'
    if REF is None:
        REF = keep
    else:
        won = sum(int((keep[f].values < REF[f].values).sum()) for f in FAM)
        tot = sum(len(REF[f]) for f in FAM)
        line += f'  folds {won}/{tot}'
    print(line, flush=True)
    RES.append(dict(name=name, avg=avg))
json.dump(RES, open('outputs/exp31_res.json', 'w'), indent=1, default=float)
print('\n=== RANKING ===', flush=True)
for r in sorted(RES, key=lambda r: r['avg']):
    print(f"  {r['name']:22s} avg {r['avg']:6.3f}", flush=True)
