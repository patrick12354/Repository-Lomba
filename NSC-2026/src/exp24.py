"""Re-tune on the 118-column set. Session 2 found the v5 optimum inverted when the tmin
block arrived; check whether it moves again now the quantile block is in."""
import warnings; warnings.filterwarnings('ignore')
import sys, json, numpy as np, pandas as pd
sys.path.insert(0, 'src')
from common import *
from featx import build_v7, TMIN_WINS_V7, CO2_WINS_V7
from ab7 import families, run, V7KW
import lightgbm as lgb

g, _, _ = load_grid()
is_tr = pd.Series((g.is_test == 0).values, index=g.index)
y = g[TARGET]
c = clean_exog(g, k=6.0)
FAM = families(g.index[is_tr & y.notna()])


def qblock(c, wins, q, col='air_temperature', rh=True):
    s = c[col]; idx = c.index; d = {}
    for hrs in wins:
        w = int(hrs * 2) + 1
        lo = s.rolling(w, center=True, min_periods=6).quantile(q)
        hi = s.rolling(w, center=True, min_periods=6).quantile(1 - q)
        d[f'{col}_q{hrs}'] = lo; d[f'{col}_qhi{hrs}'] = hi
        d[f'{col}_qrng{hrs}'] = hi - lo; d[f'{col}_minus_q{hrs}'] = s - lo
        if rh:
            d[f'rh_q{hrs}'] = 100 * es(lo.values) / es(c['air_temperature'].values)
    return pd.DataFrame(d, index=idx)


F = pd.concat([build_v7(c), qblock(c, TMIN_WINS_V7, 0.05),
               qblock(c, CO2_WINS_V7, 0.05, 'co2', rh=False)], axis=1)
F = F.replace([np.inf, -np.inf], np.nan)
print('features', F.shape[1], flush=True)


def score(label, **kw):
    d = dict(V7KW); d.update(kw)
    D = run(F, y, is_tr, FAM['P'], seeds=(0, 1, 2), kw=d)
    pf = D.groupby('fold').apply(lambda x: rmse(x.y, x.p))
    print(f'  {label:34s} P {pf.mean():6.3f} worst {pf.max():6.3f}', flush=True)
    return dict(label=label, mean=float(pf.mean()), worst=float(pf.max()), kw=kw)


R = [score('reference (v7 knobs)')]
for nl in (7, 11, 21, 31):
    R.append(score(f'num_leaves={nl}', num_leaves=nl))
for mc in (15, 40, 60):
    R.append(score(f'min_child={mc}', min_child_samples=mc))
for cs in (0.4, 0.55, 0.85, 1.0):
    R.append(score(f'colsample={cs}', colsample_bytree=cs))
for ss in (0.6, 1.0):
    R.append(score(f'subsample={ss}', subsample=ss))
for al in (2.0, 8.0):
    R.append(score(f'alpha={al}', alpha=al))
for rl in (1.0, 10.0):
    R.append(score(f'reg_lambda={rl}', reg_lambda=rl))
for ne, lr in ((1800, 0.015), (3000, 0.01)):
    R.append(score(f'n={ne} lr={lr}', n_estimators=ne, learning_rate=lr))

json.dump(R, open('outputs/exp24_res.json', 'w'), indent=1, default=float)
print('\n=== TOP 10 ===', flush=True)
for r in sorted(R, key=lambda r: r['mean'])[:10]:
    print(f"  {r['label']:34s} P {r['mean']:6.3f} worst {r['worst']:6.3f}", flush=True)
