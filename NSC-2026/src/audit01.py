"""Compliance audit, risk 1: do any TRAINING-row features reach into the test window?

Centered rolling windows are legitimate for test rows (test.csv supplies the exogenous
sensors and the task description says to use them). But a centered window on a training
row within 48 h of the boundary also reaches forward into the test period, which sits
awkwardly with "only train.csv may be used to train the model".

Measure the blast radius, then price the strict alternative: build training-row features
from a train-only grid, and test-row features from the full grid.
"""
import warnings; warnings.filterwarnings('ignore')
import sys, numpy as np, pandas as pd
sys.path.insert(0, 'src')
from common import *
from featx import build_v7, TMIN_WINS_V7, CO2_WINS_V7

g, _, _ = load_grid()
is_tr = (g.is_test == 0).values
is_te = (g.is_test == 1).values
IDX = g.index
y = g[TARGET]


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


def features(grid):
    c = clean_exog(grid, k=6.0)
    F = pd.concat([build_v7(c), qblock(c, TMIN_WINS_V7, 0.05),
                   qblock(c, CO2_WINS_V7, 0.05, 'co2', rh=False)], axis=1)
    return F.replace([np.inf, -np.inf], np.nan)


F_full = features(g)                      # current pipeline: one joint grid
# Truncate at the boundary, keeping the 13 grid-filler rows so the 30-min spacing (and
# therefore every positional rolling window) is preserved.
BOUND = IDX[is_tr][-1]
g_tr = g[IDX <= BOUND].copy()
F_tronly = features(g_tr)

print('=== how many training rows change if the test window is hidden during training? ===')
common = [c for c in F_full.columns if c in F_tronly.columns]
A = F_full.loc[F_tronly.index, common]
B = F_tronly[common]
diff = ~np.isclose(A.values, B.values, rtol=0, atol=1e-9, equal_nan=True)
rows_changed = diff.any(axis=1)
print(f'  training rows total          : {len(B)}')
print(f'  training rows with any change: {int(rows_changed.sum())} ({rows_changed.mean()*100:.2f}%)')
if rows_changed.any():
    first = B.index[rows_changed][0]
    print(f'  earliest affected timestamp  : {first}  (boundary is {IDX[is_tr][-1]})')
    print(f'  reach back from boundary     : {(IDX[is_tr][-1]-first).total_seconds()/3600:.1f} h')
cols_changed = pd.Series(diff.sum(0), index=common)
cols_changed = cols_changed[cols_changed > 0].sort_values(ascending=False)
print(f'  columns affected             : {len(cols_changed)} of {len(common)}')
print('  worst affected columns       :', list(cols_changed.head(8).index))

print('\n=== magnitude of the change, on affected cells only ===')
vals_a = A.values[diff]; vals_b = B.values[diff]
sd = A.std().replace(0, np.nan)
print(f'  affected cells: {int(diff.sum())} of {diff.size} ({diff.sum()/diff.size*100:.4f}%)')
print(f'  median |delta| : {np.nanmedian(np.abs(vals_a - vals_b)):.4f}')
print(f'  max    |delta| : {np.nanmax(np.abs(vals_a - vals_b)):.4f}')

print('\n=== does hiding the test window change the fitted model materially? ===')
import lightgbm as lgb
from ab7 import V7KW
KW = dict(V7KW); KW['alpha'] = 2.0
tr_mask = pd.Series(is_tr, index=IDX) & y.notna()
Xte = F_full[is_te]
preds = {}
for name, Xtr in [('joint grid (current)', F_full.loc[tr_mask[tr_mask].index]),
                  ('train-only grid (strict)', F_tronly.loc[tr_mask[tr_mask].index][F_full.columns])]:
    p = np.mean([lgb.LGBMRegressor(random_state=s, **KW).fit(Xtr, y[tr_mask]).predict(Xte)
                 for s in (0, 1, 2)], 0)
    preds[name] = np.clip(p, 5, 100)
    print(f'  {name:26s} test pred mean {preds[name].mean():.4f} std {preds[name].std():.4f}')
a, b = preds['joint grid (current)'], preds['train-only grid (strict)']
print(f'  RMSE between the two test prediction vectors: {np.sqrt(np.mean((a-b)**2)):.4f}')
print(f'  max abs difference on any test row         : {np.max(np.abs(a-b)):.4f}')
