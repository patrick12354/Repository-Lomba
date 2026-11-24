"""Is the dispersion correction just undoing huber alpha=2?

If a less robust loss removes the under-dispersion at no cost, prefer that -- one moving
part instead of two. Joint sweep over alpha x expansion factor, single hbt model,
all three fold families.
"""
import warnings; warnings.filterwarnings('ignore')
import sys, json, numpy as np, pandas as pd
sys.path.insert(0, 'src')
from common import *
from featx import build_v7, TMIN_WINS_V7, CO2_WINS_V7
from ab7 import families, run, V7KW

g, _, _ = load_grid()
is_tr = pd.Series((g.is_test == 0).values, index=g.index)
y = g[TARGET]
c = clean_exog(g, k=6.0)
FAM = families(g.index[is_tr & y.notna()])


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
print('features', F.shape[1], flush=True)

ROWS = []
CACHE = {}
for al in (2.0, 3.0, 4.0, 6.0):
    kw = dict(V7KW); kw['alpha'] = al
    for fam, folds in FAM.items():
        CACHE[(al, fam)] = run(F, y, is_tr, folds, kw=kw)
    print(f'  fitted alpha={al}', flush=True)

# L2 objective as the extreme non-robust end
kw = dict(V7KW); kw.pop('alpha'); kw['objective'] = 'regression'
for fam, folds in FAM.items():
    CACHE[('L2', fam)] = run(F, y, is_tr, folds, kw=kw)
print('  fitted L2', flush=True)

print(f'\n{"config":22s} ' + ' '.join(f'{f:>7s}' for f in FAM) + '     avg   slope  swing')
for al in (2.0, 3.0, 4.0, 6.0, 'L2'):
    for s in (1.00, 1.03, 1.05, 1.08):
        per, slopes, swings = {}, [], []
        for fam in FAM:
            D = CACHE[(al, fam)].copy()
            m = D.p.mean()
            D['adj'] = m + s * (D.p - m)
            pf = D.groupby('fold').apply(lambda d: rmse(d.y, d.adj))
            per[fam] = float(pf.mean())
            if s == 1.00:
                slopes.append(np.polyfit(D.p, D.y, 1)[0])
                D['day'] = D.dt.dt.date
                a = D.groupby(['fold', 'day']).agg(ay=('y', lambda x: x.max() - x.min()),
                                                   ap=('p', lambda x: x.max() - x.min()))
                swings.append(a.ap.mean() / a.ay.mean())
        avg = float(np.mean(list(per.values())))
        extra = (f'  {np.mean(slopes):.3f}  {np.mean(swings):.3f}' if s == 1.00 else '')
        ROWS.append(dict(alpha=str(al), s=s, avg=avg, per=per))
        print(f'  a={str(al):4s} s={s:.2f}        ' + ' '.join(f'{per[f]:7.3f}' for f in FAM) +
              f' {avg:7.3f}{extra}', flush=True)

json.dump(ROWS, open('outputs/exp27_res.json', 'w'), indent=1, default=float)
print('\n=== TOP 8 ===', flush=True)
for r in sorted(ROWS, key=lambda r: r['avg'])[:8]:
    print(f"  alpha={r['alpha']:4s} s={r['s']:.2f}  avg {r['avg']:6.3f}", flush=True)
