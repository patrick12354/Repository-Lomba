"""Why does the quantile block help? If it is spike-robustness, replacing min/max should
be as good as adding alongside. If it is distributional information, the two should be
complementary and the q level should matter smoothly."""
import warnings; warnings.filterwarnings('ignore')
import sys, json, numpy as np, pandas as pd
sys.path.insert(0, 'src')
from common import *
from featx import build_v7, tmin_block, tend_block, ordstat_block, TMIN_WINS_V7, CO2_WINS_V7
from ab7 import families, run, report

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
        d[f'{col}_q{hrs}'] = lo
        d[f'{col}_qhi{hrs}'] = hi
        d[f'{col}_qrng{hrs}'] = hi - lo
        d[f'{col}_minus_q{hrs}'] = s - lo
        if rh:
            d[f'rh_q{hrs}'] = 100 * es(lo.values) / es(c['air_temperature'].values)
    return pd.DataFrame(d, index=idx)


def base_no_tminorder(c):
    """v7 minus the hard min/max columns, keeping everything else."""
    F = build_v7(c)
    drop = [x for x in F.columns if x.startswith(('T_min', 'T_max', 'T_rng', 'T_minus_min'))]
    return F.drop(columns=drop), drop


VAR = {}
VAR['V7_ref'] = lambda: build_v7(c)
for q in (0.02, 0.05, 0.10, 0.20):
    VAR[f'V7+q{q}'] = (lambda q=q: pd.concat([build_v7(c), qblock(c, TMIN_WINS_V7, q)], axis=1))
VAR['V7_qREPLACE_min'] = lambda: pd.concat([base_no_tminorder(c)[0], qblock(c, TMIN_WINS_V7, 0.05)], axis=1)
VAR['V7+q05+co2q'] = lambda: pd.concat([build_v7(c), qblock(c, TMIN_WINS_V7, 0.05),
                                        qblock(c, CO2_WINS_V7, 0.05, 'co2', rh=False)], axis=1)
VAR['V7+q05_wide'] = lambda: pd.concat([build_v7(c), qblock(c, (18, 48, 96, 144), 0.05)], axis=1)

RES, REF = [], None
for n, fn in VAR.items():
    F = fn().replace([np.inf, -np.inf], np.nan)
    Ds = {fam: run(F, y, is_tr, folds) for fam, folds in FAM.items()}
    if REF is None:
        RES.append(report(f'{n}({F.shape[1]})', Ds)); REF = Ds
    else:
        RES.append(report(f'{n}({F.shape[1]})', Ds, refs=REF))
json.dump(RES, open('outputs/exp23_res.json', 'w'), indent=1, default=float)
print('\n=== RANKING by 3-family average ===', flush=True)
for r in sorted(RES, key=lambda r: r['avg']):
    print(f"  {r['name']:26s} avg {r['avg']:6.3f}", flush=True)
