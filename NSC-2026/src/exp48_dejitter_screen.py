"""Family-P member screen: de-jittered daily block, and de-jitter + CHU."""
import sys, time, numpy as np, pandas as pd
sys.path[:0] = ['.', 'src']
import final_pipeline as fp
from chu_block import chu_block, dejitter_daily

g = fp.load_grid()
y = g[fp.TARGET]; idx = g.index
is_tr = (g.is_test == 0).values & y.notna().values

def build(dejit, chu):
    c = fp.clean_exog(g)
    if dejit:
        c = dejitter_daily(c, fp.DAILY)
    base = fp.build_features(c)
    base = base[fp.drop_soil(base)]
    F = pd.concat([base, fp.tmin_block(c), fp.tend_block(c),
                   fp.ordstat_block(c, 'co2', fp.CO2_WINS),
                   fp.qblock(c, fp.TMIN_WINS), fp.qblock(c, fp.CO2_WINS, col='co2', rh=False)], axis=1)
    if chu:
        F = pd.concat([F, chu_block(c, fp.es)], axis=1)
    return F.replace([np.inf, -np.inf], np.nan)

ARMS = {'base': build(False, False), 'dejitter': build(True, False),
        'dejitter+chu': build(True, True)}
print({k: v.shape[1] for k, v in ARMS.items()})
# sanity: de-jitter must not touch the target and must be identical if the target is wiped
folds = fp.rolling_origins(idx[is_tr], n=9)

def run(F, name):
    out = []
    for vs, cut in folds:
        trm = is_tr & (idx <= vs); vam = is_tr & (idx > vs) & (idx <= cut)
        p = fp.predict(name, F.loc[trm], y[trm].values, F.loc[vam],
                       fp.es(F.loc[vam, 'T'].values),
                       y[trm].values * fp.es(F.loc[trm, 'T'].values) / 100.0, fp.SEEDS_OOF)
        out.append(fp.rmse(y[vam].values, np.clip(p, 5, 100)))
    return np.array(out)

for model in ('hbt', 'cat', 'l2', 'ridge', 'enet', 'ridge_e'):
    t0 = time.time(); res = {k: run(F, model) for k, F in ARMS.items()}
    b = res['base']
    print("%-8s base %.4f" % (model, b.mean()), end='')
    for k in ('dejitter', 'dejitter+chu'):
        d = res[k] - b
        print("   | %s %.4f (%+.4f, %d/9)" % (k, res[k].mean(), d.mean(), (d < 0).sum()), end='')
    print("   [%.0fs]" % (time.time() - t0), flush=True)
