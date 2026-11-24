"""Fast-component feature blocks on top of the v8 set, scored with the s=1.05 expansion
already applied so the comparison is against what will actually ship."""
import warnings; warnings.filterwarnings('ignore')
import sys, json, numpy as np, pandas as pd
sys.path.insert(0, 'src')
from common import *
from featx import build_v7, TMIN_WINS_V7, CO2_WINS_V7
import featx3
from ab7 import families, run, V7KW

g, _, _ = load_grid()
is_tr = pd.Series((g.is_test == 0).values, index=g.index)
y = g[TARGET]
c = clean_exog(g, k=6.0)
FAM = families(g.index[is_tr & y.notna()])
KW = dict(V7KW); KW['alpha'] = 2.0
S = 1.05


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

BLOCKS = {
    'farlag': featx3.farlag_block(c),
    'accel': featx3.accel_block(c),
    'phase': featx3.phase_block(c),
    'fastphys': featx3.fastphys_block(c),
}
VAR = {'v8_base': []}
for n in BLOCKS:
    VAR[f'+{n}'] = [n]
VAR['+farlag+accel'] = ['farlag', 'accel']
VAR['+all4'] = list(BLOCKS)


def score(name, F):
    F = F.replace([np.inf, -np.inf], np.nan)
    per = {}
    allD = {}
    for fam, folds in FAM.items():
        D = run(F, y, is_tr, folds, kw=KW)
        m = D.p.mean(); D['p'] = m + S * (D.p - m)
        D['se'] = (D.p - D.y) ** 2
        pf = D.groupby('fold').apply(lambda d: rmse(d.y, d.p))
        per[fam] = (float(pf.mean()), float(pf.max()))
        allD[fam] = D
    avg = float(np.mean([per[f][0] for f in FAM]))
    print(f'  {name:18s}({F.shape[1]:3d}) ' + ' '.join(f'{f} {per[f][0]:6.3f}/{per[f][1]:6.3f}' for f in FAM) +
          f'  avg {avg:6.3f}', flush=True)
    return dict(name=name, n=int(F.shape[1]), avg=avg, per={f: per[f] for f in FAM}), allD


RES = []
REF = None
for n, bl in VAR.items():
    F = V8 if not bl else pd.concat([V8] + [BLOCKS[b] for b in bl], axis=1)
    r, D = score(n, F)
    if REF is None:
        REF = D
    else:
        won = 0; tot = 0
        for fam in FAM:
            a = REF[fam].groupby('fold').apply(lambda d: rmse(d.y, d.p))
            b = D[fam].groupby('fold').apply(lambda d: rmse(d.y, d.p))
            won += int((b.values < a.values).sum()); tot += len(a)
        r['folds_won'] = f'{won}/{tot}'
        print(f'  {"":24s} folds won vs base: {won}/{tot}', flush=True)
    RES.append(r)
json.dump(RES, open('outputs/exp28_res.json', 'w'), indent=1, default=float)
print('\n=== RANKING ===', flush=True)
for r in sorted(RES, key=lambda r: r['avg']):
    print(f"  {r['name']:18s} avg {r['avg']:6.3f}  {r.get('folds_won','-')}", flush=True)
