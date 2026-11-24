"""Do the re-tuned knobs stack? Confirm the winners on all three fold families."""
import warnings; warnings.filterwarnings('ignore')
import sys, json, numpy as np, pandas as pd
sys.path.insert(0, 'src')
from common import *
from featx import build_v7, TMIN_WINS_V7, CO2_WINS_V7
from ab7 import families, run, report, V7KW

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

CAND = {
    'ref(v7 knobs)':        {},
    'a2':                   dict(alpha=2.0),
    'a1':                   dict(alpha=1.0),
    'a1.5':                 dict(alpha=1.5),
    'a3':                   dict(alpha=3.0),
    'a2+nl11':              dict(alpha=2.0, num_leaves=11),
    'a2+nl11+ss0.6':        dict(alpha=2.0, num_leaves=11, subsample=0.6),
    'a2+slow':              dict(alpha=2.0, n_estimators=1800, learning_rate=0.015),
    'a2+nl11+slow':         dict(alpha=2.0, num_leaves=11, n_estimators=1800, learning_rate=0.015),
    'a2+cs1.0':             dict(alpha=2.0, colsample_bytree=1.0),
}
RES, REF = [], None
for n, kw in CAND.items():
    d = dict(V7KW); d.update(kw)
    Ds = {fam: run(F, y, is_tr, folds, kw=d) for fam, folds in FAM.items()}
    if REF is None:
        RES.append(report(n, Ds)); REF = Ds
    else:
        RES.append(report(n, Ds, refs=REF))
json.dump(RES, open('outputs/exp25_res.json', 'w'), indent=1, default=float)
print('\n=== RANKING by 3-family average ===', flush=True)
for r in sorted(RES, key=lambda r: r['avg']):
    print(f"  {r['name']:22s} avg {r['avg']:6.3f}", flush=True)
