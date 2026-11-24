"""Fresh error analysis on the v8 out-of-fold residuals.
Where is the remaining error, and does anything about it look exploitable?"""
import warnings; warnings.filterwarnings('ignore')
import sys, pickle, numpy as np, pandas as pd
sys.path.insert(0, 'src')
from common import *
from scipy.optimize import nnls
pd.set_option('display.width', 230)

MS = ['hbt', 'cat', 'ridge', 'enet', 'ridge_e']
OOF = pickle.load(open('outputs/v8_oof.pkl', 'rb'))


def nested(O, shrink=0.25):
    out = []
    for k in sorted(O.fold.unique()):
        prev, cur = O[O.fold < k], O[O.fold == k].copy()
        if len(prev) < 200: continue
        w, _ = nnls(prev[MS].values, prev.y.values)
        w = w / w.sum() if w.sum() > 0 else np.ones(len(MS)) / len(MS)
        w = (1 - shrink) * w + shrink * np.ones(len(MS)) / len(MS)
        cur['p'] = cur[MS].values @ w
        out.append(cur)
    return pd.concat(out, ignore_index=True)


L8 = nested(OOF[('v8', 'P')]); L8['err'] = L8.p - L8.y
L7 = nested(OOF[('v7', 'P')]); L7['err'] = L7.p - L7.y
print(f'v8 pooled {np.sqrt((L8.err**2).mean()):.3f}   v7 pooled {np.sqrt((L7.err**2).mean()):.3f}')

print('\n=== 1. SLOW / FAST decomposition (24h centered MA of the residual) ===')


def split(L):
    r = []
    for f, d in L.groupby('fold'):
        d = d.sort_values('dt').copy()
        slow = d.err.rolling(49, center=True, min_periods=6).mean()
        r.append(pd.DataFrame({'fold': f, 'slow': slow, 'fast': d.err - slow, 'err': d.err}))
    return pd.concat(r)


for nm, L in [('v7', L7), ('v8', L8)]:
    S = split(L)
    print(f'  {nm}: total {np.sqrt((S.err**2).mean()):.3f}  slow {np.sqrt((S.slow**2).mean()):.3f}  '
          f'fast {np.sqrt((S.fast**2).mean()):.3f}  slow share of MSE '
          f'{(S.slow**2).mean()/(S.err**2).mean()*100:.1f}%')

print('\n=== 2. MSE concentration ===')
se = np.sort(L8.err.values ** 2)[::-1]
tot = se.sum()
for q in (0.01, 0.05, 0.10, 0.25, 0.50):
    n = int(len(se) * q)
    print(f'  worst {q*100:4.0f}% of rows carry {se[:n].sum()/tot*100:5.1f}% of MSE')

print('\n=== 3. per-day RMSE, worst 12 days (v8 vs v7) ===')
L8['day'] = L8.dt.dt.date; L7['day'] = L7.dt.dt.date
d8 = L8.groupby(['fold', 'day']).apply(lambda d: pd.Series(
    {'rmse': float(np.sqrt((d.err**2).mean())), 'bias': float(d.err.mean()), 'y': float(d.y.mean())}))
d7 = L7.groupby(['fold', 'day']).apply(lambda d: float(np.sqrt((d.err**2).mean())))
d8['v7'] = d7
print(f'  median day {d8.rmse.median():.2f}   p90 {d8.rmse.quantile(.9):.2f}   max {d8.rmse.max():.2f}')
print(d8.sort_values('rmse', ascending=False).head(12).round(2).to_string())

print('\n=== 4. bias / RMSE by hour ===')
L8['hr'] = L8.dt.dt.hour
h = L8.groupby('hr').agg(bias=('err', 'mean'), rmse=('err', lambda s: float(np.sqrt((s**2).mean()))),
                         y=('y', 'mean'))
print(h.round(2).T.to_string())

print('\n=== 5. residual autocorrelation within a fold (is there structure left?) ===')
for lag in (1, 2, 4, 8, 12, 24, 48):
    a = L8.groupby('fold').err.apply(lambda s: s.autocorr(lag)).mean()
    print(f'  lag {lag:3d} ({lag/2:5.1f}h): {a:+.3f}')

print('\n=== 6. does the error depend on the air-mass regime? ===')
g, _, _ = load_grid()
c = clean_exog(g, k=6.0)
T = c['air_temperature']
aux = pd.DataFrame({'dt': g.index, 'T': T.values,
                    'Tq05_48': T.rolling(97, center=True, min_periods=6).quantile(.05).values,
                    'Trng48': (T.rolling(97, center=True, min_periods=6).quantile(.95)
                               - T.rolling(97, center=True, min_periods=6).quantile(.05)).values})
M = L8.merge(aux, on='dt')
for col in ['T', 'Tq05_48', 'Trng48']:
    M['b'] = pd.qcut(M[col], 5, labels=False)
    r = M.groupby('b').agg(lo=(col, 'min'), hi=(col, 'max'), n=('err', 'size'),
                           bias=('err', 'mean'), rmse=('err', lambda s: float(np.sqrt((s**2).mean()))))
    print(f'\n  by {col}:'); print(r.round(2).to_string())

print('\n=== 7. how far from the physics ceiling? ===')
y = g[TARGET]
Td = pd.Series(rh_to_td(y.values, T.values), index=g.index)
val = g.index.isin(L8.dt)
for w in (13, 25, 49):
    rec = td_to_rh(Td.rolling(w, center=True, min_periods=1).mean(), T)
    print(f'  Td known at {w/2:4.1f}h resolution -> {rmse(y[val], rec[val]):.3f}')
print(f'  v8 achieves {np.sqrt((L8.err**2).mean()):.3f}')
