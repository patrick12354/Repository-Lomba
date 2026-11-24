"""Member-level screen of the CHU day-statistics block on family P, before spending
the 18-fold harness on it."""
import sys, time, numpy as np, pandas as pd
sys.path[:0] = ['.', 'src']
import final_pipeline as fp
from chu_block import chu_block

g = fp.load_grid(); c = fp.clean_exog(g)
F = fp.make_features(g)
C = chu_block(c, fp.es)
FC = pd.concat([F, C], axis=1).replace([np.inf, -np.inf], np.nan)
y = g[fp.TARGET]
is_tr = (g.is_test == 0).values & y.notna().values
idx = g.index

folds = fp.rolling_origins(idx[is_tr], n=9)
print("family P folds:", len(folds), " features %d -> %d" % (F.shape[1], FC.shape[1]))

def run(feats, name):
    t0 = time.time(); out = []
    for i, (vs, cut) in enumerate(folds):
        trm = is_tr & (idx <= vs)
        vam = is_tr & (idx > vs) & (idx <= cut)
        p = fp.predict(name, feats.loc[trm], y[trm].values, feats.loc[vam],
                       fp.es(feats.loc[vam, 'T'].values),
                       y[trm].values * fp.es(feats.loc[trm, 'T'].values) / 100.0,
                       fp.SEEDS_OOF)
        out.append(fp.rmse(y[vam].values, np.clip(p, 5, 100)))
    return np.array(out), time.time() - t0

for model in ('hbt', 'l2', 'ridge'):
    a, ta = run(F, model)
    b, tb = run(FC, model)
    d = b - a
    print("%-6s base %.4f  +chu %.4f  delta %+.4f  folds won %d/%d  worst %.3f -> %.3f  (%.0fs)"
          % (model, a.mean(), b.mean(), d.mean(), (d < 0).sum(), len(d), a.max(), b.max(), ta + tb))
    print("        per fold delta:", np.round(d, 3))
