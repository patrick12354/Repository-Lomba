"""Compliance audit, risk 2: the dispersion correction.

v9 multiplies the blended prediction by a hand-chosen 1.05 about its own mean. Under a
rule banning "post-processing modification without a model basis", a hand-picked constant
is the wrong shape of object even though it was validated. A calibrator *fitted* on the
model's own out-of-fold predictions is standard stacked generalisation and is part of the
model.

Price the alternatives, all nested (fit on folds < k, score on fold k), all three families.
"""
import warnings; warnings.filterwarnings('ignore')
import sys, json, pickle, numpy as np, pandas as pd
sys.path.insert(0, 'src')
from common import *
from scipy.optimize import nnls
from sklearn.linear_model import LinearRegression, HuberRegressor

MS = ['hbt', 'cat', 'ridge', 'enet', 'ridge_e']
OOF = pickle.load(open('outputs/v8_oof.pkl', 'rb'))
FAMS = ['P', 'Q', 'R']


def base_nested(O, shrink=0.25):
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


def fit_slope(past):
    """Least-squares dispersion slope about the past predictions' own mean."""
    c = past.p.mean()
    num = ((past.y - c) * (past.p - c)).sum()
    den = ((past.p - c) ** 2).sum()
    return float(num / den) if den > 0 else 1.0


SCHEMES = {}
SCHEMES['none'] = lambda past, cur: cur.p.values
SCHEMES['fixed s=1.05 (current v9)'] = lambda past, cur: (
    cur.p.mean() + 1.05 * (cur.p.values - cur.p.mean()))
SCHEMES['fitted slope (OLS, free)'] = lambda past, cur: (
    cur.p.mean() + fit_slope(past) * (cur.p.values - cur.p.mean()))
SCHEMES['fitted slope, shrunk 0.5'] = lambda past, cur: (
    cur.p.mean() + (1 + 0.5 * (fit_slope(past) - 1)) * (cur.p.values - cur.p.mean()))
SCHEMES['fitted slope, shrunk 0.7'] = lambda past, cur: (
    cur.p.mean() + (1 + 0.7 * (fit_slope(past) - 1)) * (cur.p.values - cur.p.mean()))


def lin_cal(past, cur):
    m = LinearRegression().fit(past[['p']].values, past.y.values)
    return m.predict(cur[['p']].values)


SCHEMES['linear calibrator (a*p+b)'] = lin_cal


def lin_cal_shrunk(past, cur):
    m = LinearRegression().fit(past[['p']].values, past.y.values)
    a = 1 + 0.5 * (m.coef_[0] - 1)
    b = past.y.mean() - a * past.p.mean()
    return a * cur.p.values + b


SCHEMES['linear calibrator, shrunk 0.5'] = lin_cal_shrunk


def stack_cal(past, cur):
    m = LinearRegression(positive=True).fit(past[MS].values, past.y.values)
    return m.predict(cur[MS].values)


SCHEMES['stacked linear on 5 models'] = stack_cal

RES = []
for name, fn in SCHEMES.items():
    per, wins, tot = {}, 0, 0
    slopes = []
    for fam in FAMS:
        L = base_nested(OOF[('v8', fam)])
        pb, pa = [], []
        for k in sorted(L.fold.unique()):
            past, cur = L[L.fold < k], L[L.fold == k].copy()
            if len(past) < 400: continue
            cur['adj'] = np.clip(fn(past, cur), 5, 100)
            pb.append(rmse(cur.y, cur.p)); pa.append(rmse(cur.y, cur.adj))
            wins += (pa[-1] < pb[-1]); tot += 1
            if fam == 'P': slopes.append(fit_slope(past))
        per[fam] = float(np.mean(pa))
    avg = float(np.mean(list(per.values())))
    sl = f'  (fitted slope ranged {min(slopes):.3f}-{max(slopes):.3f})' if 'fitted' in name or 'linear' in name else ''
    print(f'  {name:30s} ' + ' '.join(f'{f} {per[f]:6.3f}' for f in FAMS) +
          f'  avg {avg:6.3f}  folds {wins}/{tot}{sl}', flush=True)
    RES.append(dict(name=name, avg=avg, folds=f'{wins}/{tot}'))

json.dump(RES, open('outputs/exp33_res.json', 'w'), indent=1, default=float)
print('\n=== RANKING ===', flush=True)
for r in sorted(RES, key=lambda r: r['avg']):
    print(f"  {r['name']:32s} avg {r['avg']:6.3f}  folds {r['folds']}", flush=True)
