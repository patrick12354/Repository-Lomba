"""Horizon effect with CALENDAR TIME CONTROLLED.

Family P's 9 windows overlap heavily (2-day step, 15-day windows), so each timestamp is
scored at several different horizons. That lets horizon be separated from "was this a hard
week". For every timestamp, regress squared error on horizon within timestamp.
"""
import numpy as np, pandas as pd, pickle, sys
sys.path.insert(0, '.')
import final_pipeline as FP
from scipy.optimize import nnls

cache = pickle.load(open('outputs/h7_oof.pkl', 'rb'))
BASE = ['hbt', 'cat', 'ridge', 'enet', 'ridge_e']
S = (0, 1, 2)
g = FP.load_grid(); y = g[FP.TARGET]; IDX = g.index
is_tr = (g.is_test == 0).values & y.notna().values
idx = IDX[is_tr]; end = idx.max(); d0 = idx.min()
folds = [(end - pd.Timedelta(days=2 * i) - pd.Timedelta(days=15), end - pd.Timedelta(days=2 * i))
         for i in range(9)][::-1]

rows = []
for fi, (vs, ve) in enumerate(folds):
    v = is_tr & (IDX > vs) & (IDX <= ve)
    d = pd.DataFrame(dict(fold=fi, dt=IDX[v], y=y[v].values))
    for m in BASE:
        d[m] = cache[('P', fi, m, '', S)]
    d['h'] = (d.dt - vs).dt.total_seconds() / 86400.0   # days since the training cut
    rows.append(d)
P = pd.concat(rows, ignore_index=True)
w, _ = nnls(P[BASE].values, P.y.values); w = w / w.sum()
w = 0.75 * w + 0.25 * np.ones(5) / 5
P['blend'] = np.clip(P[BASE].values @ w, 5, 100)
P['e'] = P.blend - P.y
P['se'] = P.e ** 2

print('rows=%d  unique timestamps=%d  appearances per ts: %s'
      % (len(P), P.dt.nunique(), P.groupby('dt').size().value_counts().to_dict()))

# ---- within-timestamp: de-mean squared error by timestamp, then bin by horizon ----
P['se_dm'] = P.se - P.groupby('dt').se.transform('mean')
P['e_dm'] = P.e - P.groupby('dt').e.transform('mean')
multi = P[P.groupby('dt').dt.transform('size') > 1]

print('\n=== horizon effect, calendar-controlled (timestamps seen at >1 horizon) ===')
print('%12s %6s %12s %12s' % ('horizon(d)', 'n', 'dSE vs ts-mean', 'dBias'))
multi = multi.copy(); multi['hb'] = (multi.h // 2).astype(int) * 2
for b, d in multi.groupby('hb'):
    print('%6d-%-5d %6d %12.3f %12.3f' % (b, b + 2, len(d), d.se_dm.mean(), d.e_dm.mean()))

# implied RMSE at each horizon, anchored on the overall pooled MSE
base_mse = P.se.mean()
print('\nimplied RMSE by horizon (pooled MSE %.3f + within-ts horizon effect):' % base_mse)
for b, d in multi.groupby('hb'):
    print('  days %2d-%2d -> %.3f' % (b, b + 2, np.sqrt(max(base_mse + d.se_dm.mean(), 0.01))))

# ---- the same, restricted to the LAST fold only (closest calendar match to test) ----
print('\n=== last fold (2023-08-14 -> 08-29, the window that abuts the test set) ===')
L = P[P.fold == 8].copy()
L['hb'] = (L.h // 2).astype(int) * 2
for b, d in L.groupby('hb'):
    print('  days %2d-%2d n=%3d RMSE=%6.3f bias=%+6.3f pred_std=%5.2f y_std=%5.2f'
          % (b, b + 2, len(d), np.sqrt(d.se.mean()), d.e.mean(), d.blend.std(), d.y.std()))

# ---- naive persistence / climatology benchmark by horizon, for reference ----
print('\n=== how much of the error is a slow drift? (fold-level bias) ===')
for fi, d in P.groupby('fold'):
    print('  fold %d  RMSE=%6.3f  bias=%+6.3f  bias^2 share=%4.1f%%'
          % (fi, np.sqrt(d.se.mean()), d.e.mean(), 100 * d.e.mean() ** 2 / d.se.mean()))
