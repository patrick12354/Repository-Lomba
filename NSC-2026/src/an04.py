"""Two follow-ups on the v8 residuals:
  (a) is the diurnal amplitude genuinely compressed, or is that optimal shrinkage?
  (b) do post-hoc corrections survive nested validation this time? (they did not for v5)
"""
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


L = nested(OOF[('v8', 'P')])
L['err'] = L.p - L.y
L['hr'] = L.dt.dt.hour
L['day'] = L.dt.dt.date
print(f'v8 pooled {np.sqrt((L.err**2).mean()):.4f}')

print('\n=== (a) calibration by true-RH decile ===')
L['q'] = pd.qcut(L.y, 10, labels=False)
print(L.groupby('q').agg(ytrue=('y', 'mean'), pred=('p', 'mean'), bias=('err', 'mean'),
                         rmse=('err', lambda s: float(np.sqrt((s**2).mean())))).round(2).to_string())
a, b = np.polyfit(L.p, L.y, 1)
print(f'  OLS truth on prediction: y = {a:.4f}*p {b:+.3f}   (1.0, 0 = calibrated)')

print('\n=== diurnal amplitude: within-day swing, predicted vs actual ===')
amp = L.groupby(['fold', 'day']).agg(amp_y=('y', lambda s: s.max() - s.min()),
                                     amp_p=('p', lambda s: s.max() - s.min()))
print(f'  mean actual swing {amp.amp_y.mean():.2f}   mean predicted swing {amp.amp_p.mean():.2f}'
      f'   ratio {amp.amp_p.mean()/amp.amp_y.mean():.4f}')
print(f'  correlation of swings {amp.amp_y.corr(amp.amp_p):.3f}')

print('\n=== per-fold hour-block bias (is the pattern stable?) ===')
L['hb'] = pd.cut(L.hr, [-1, 5, 9, 13, 17, 23], labels=['00-05', '06-09', '10-13', '14-17', '18-23'])
print(L.pivot_table(index='fold', columns='hb', values='err', aggfunc='mean', observed=True).round(2).to_string())

print('\n=== (b) NESTED post-hoc corrections (fit on folds < k, apply to fold k) ===')
folds = sorted(L.fold.unique())


def score(fn, label):
    tot = []
    for k in folds:
        if k < 3: continue
        past, cur = L[L.fold < k], L[L.fold == k].copy()
        cur['adj'] = fn(past, cur)
        tot.append((rmse(cur.y, cur.p), rmse(cur.y, cur.adj)))
    base = np.mean([t[0] for t in tot]); adj = np.mean([t[1] for t in tot])
    print(f'  {label:38s} {base:.4f} -> {adj:.4f}  ({adj-base:+.4f})')


score(lambda p, c: c.p, 'no correction')
score(lambda p, c: c.p - p.err.mean(), 'constant bias')
score(lambda p, c: c.p - c.hr.map(p.groupby('hr').err.mean()).fillna(0).values, 'hourly bias')
score(lambda p, c: c.p - 0.5 * c.hr.map(p.groupby('hr').err.mean()).fillna(0).values, 'hourly bias x0.5')
for s in (1.02, 1.05, 1.08):
    score(lambda p, c, s=s: c.p.mean() + s * (c.p - c.p.mean()), f'global variance inflate x{s}')
for s in (1.02, 1.05, 1.10):
    def f(p, c, s=s):
        m = c.groupby('day').p.transform('mean')
        return m + s * (c.p - m)
    score(f, f'diurnal amplitude inflate x{s}')


def lincal(p, c):
    a, b = np.polyfit(p.p, p.y, 1); return a * c.p + b


score(lincal, 'linear recalibration')
