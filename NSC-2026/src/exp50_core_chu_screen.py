"""Family-P screen of the robust core with and without the CHU day statistics.

The robust core drops every diurnal-range column because they leave training support on
the private slice. The CHU block puts that information back through a channel whose
private support is 1.000 rather than 0.818, so this is the one place the block should pay.
"""
import sys, time, numpy as np, pandas as pd
sys.path[:0] = ['.', 'src']
import final_pipeline as fp
from chu_block import chu_block, dejitter_daily
from robust_eval import feature_groups, support_fraction

g = fp.load_grid(); c = fp.clean_exog(g)
F = fp.make_features(g)
C = chu_block(c, fp.es)
y = g[fp.TARGET]; idx = g.index
is_tr = (g.is_test == 0).values & y.notna().values
is_te = (g.is_test == 1).values

cov = support_fraction(F.loc[is_tr], F.loc[is_te])
core = feature_groups(F.columns, cov)['stable_core']
FC = pd.concat([F, C], axis=1).replace([np.inf, -np.inf], np.nan)
covc = support_fraction(FC.loc[is_tr], FC.loc[is_te])
chu_ok = [k for k in C.columns if covc[k] >= 0.916]
print("stable core %d cols; CHU columns clearing the 0.916 bar: %s" % (len(core), chu_ok))

ARMS = {'full(118)': (F, list(F.columns)),
        'core': (F, core),
        'core+chu': (FC, core + chu_ok)}
folds = fp.rolling_origins(idx[is_tr], n=9)

def run(F, cols, name):
    out = []
    for vs, cut in folds:
        trm = is_tr & (idx <= vs); vam = is_tr & (idx > vs) & (idx <= cut)
        p = fp.predict(name, F.loc[trm, cols], y[trm].values, F.loc[vam, cols],
                       fp.es(F.loc[vam, 'T'].values),
                       y[trm].values * fp.es(F.loc[trm, 'T'].values) / 100.0, fp.SEEDS_OOF)
        out.append(fp.rmse(y[vam].values, np.clip(p, 5, 100)))
    return np.array(out)

for model in ('hbt', 'ridge'):
    t0 = time.time(); r = {k: run(Fx, cols, model) for k, (Fx, cols) in ARMS.items()}
    print("\n%s" % model)
    for k, v in r.items():
        d = v - r['core']
        print("  %-10s %.4f   vs core %+.4f (%d/9)   worst %.3f" % (k, v.mean(), d.mean(), (d < 0).sum(), v.max()))
    print("  [%.0fs]" % (time.time() - t0), flush=True)
