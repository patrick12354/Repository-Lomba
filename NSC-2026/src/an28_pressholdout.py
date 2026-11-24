"""The direct test section 130 should have run.

Build a split where the validation window's pressure really is outside the training range --
the private slice's condition -- and ask whether removing the pressure block helps there.
Days are ranked by mean pressure and the highest are held out, so the selection uses a
feature and never the target. This is not a forecasting split; it isolates one covariate
shift, which is the whole question.
"""
import sys, json, time
import numpy as np, pandas as pd
from scipy.optimize import nnls
sys.path[:0] = ['.', 'src']
import final_pipeline as fp

g = fp.load_grid(); F = fp.make_features(g); y = g[fp.TARGET]; idx = g.index
is_tr = (g.is_test == 0).values & y.notna().values
PRESS = sorted(set(F.columns) - set(fp.no_pressure(F)))
NOP = fp.no_pressure(F)
CORE = fp.stable_core(F, (g.is_test == 0).values, (g.is_test == 1).values)

tr_idx = idx[is_tr]
day = tr_idx.normalize()
pday = pd.Series(F.loc[tr_idx, 'pressure'].values, index=day).groupby(level=0).mean()

def fit(name, cols, trm, vam):
    c = cols or list(F.columns)
    return np.clip(fp.predict(fp.base_model(name), F.loc[trm, c], y[trm].values, F.loc[vam, c],
                   fp.es(F.loc[vam,'T'].values),
                   y[trm].values*fp.es(F.loc[trm,'T'].values)/100.0, fp.SEEDS_OOF), 5, 100)

MEMBERS = {'hbt': None, 'cat': None, 'ridge': None, 'enet': None, 'ridge_e': None,
           'l2': None, 'robust_hbt': CORE, 'bag_nopress': NOP}
V16 = list(fp.MODELS_L2)
V19 = [m for m in V16 if m != 'ridge'] + ['robust_hbt', 'bag_nopress']

def blend(meta, P, models, lam):
    U = np.ones(len(models))/len(models)
    w,_ = nnls(meta[models].values, meta.y.values); w = w/w.sum() if w.sum() else U.copy()
    w = (1-lam)*w + lam*U
    work = meta.copy(); work['blend'] = np.clip(work[models].values @ w,5,100)
    e, W = fp.tod_blend_weights(work, w, models=models, blend_shrink=lam)
    work['blend'] = np.clip(fp.apply_tod_blend(work[models].values, work.tod.values, e, W),5,100)
    pr = np.clip(fp.apply_tod_blend(P[models].values, P.tod.values, e, W),5,100)
    return np.clip(fp.apply_harm_bias(pr, P.tod.values, fp.harm_bias(work)),5,100), w

t0 = time.time(); out = {}
for frac in (0.20, 0.30):
    hi_days = set(pday.sort_values(ascending=False).index[:int(round(len(pday)*frac))])
    vam = is_tr & np.array([d in hi_days for d in idx.normalize()])
    trm = is_tr & ~vam
    A, B = F.loc[trm, PRESS], F.loc[vam, PRESS]
    lo, hh = A.quantile(.01), A.quantile(.99)
    sup = float((((B>=lo)&(B<=hh))|B.isna()).mean().mean())
    P = pd.DataFrame(index=idx[vam])
    for m, cols in MEMBERS.items():
        P[m] = fit(m, cols, trm, vam)
    P['tod'] = P.index.hour + P.index.minute/60.0
    P['y'] = y.reindex(P.index).values
    # meta rows: an inner split of the training side, so no validation row is ever fitted on
    inner = F.index[trm]
    cut = inner[int(len(inner)*0.65)]
    itr = trm & (idx <= cut); iva = trm & (idx > cut)
    Mrows = pd.DataFrame(index=idx[iva])
    for m, cols in MEMBERS.items():
        Mrows[m] = fit(m, cols, itr, iva)
    Mrows['tod'] = Mrows.index.hour + Mrows.index.minute/60.0
    Mrows['y'] = y.reindex(Mrows.index).values
    print("\nhold out the highest-pressure %d%% of days: %d valid rows, %d train rows"
          % (frac*100, vam.sum(), trm.sum()))
    print("  pressure-block support of the held-out window: %.3f   (private slice: 0.802)" % sup)
    print("  solo: hbt %.4f   bag_nopress %.4f   delta %+.4f"
          % (fp.rmse(P.y, P.hbt), fp.rmse(P.y, P.bag_nopress),
             fp.rmse(P.y, P.bag_nopress)-fp.rmse(P.y, P.hbt)))
    r = {}
    for nm, models, lam in (('v16 stack (floor 0.25, all see pressure)', V16, 0.25),
                            ('v19 stack (no floor, pressure in 41%)', V19, 0.00),
                            ('v20 stack (no floor, all see pressure)', V16, 0.00)):
        pr, w = blend(Mrows, P, models, lam)
        r[nm] = fp.rmse(P.y, pr)
        print("  %-42s RMSE %.4f" % (nm, r[nm]))
    out['frac_%.2f' % frac] = dict(support=sup, n_valid=int(vam.sum()), **{k: float(v) for k, v in r.items()})
    print("  v19 minus v16 %+.4f   v20 minus v16 %+.4f"
          % (r['v19 stack (no floor, pressure in 41%)'] - r['v16 stack (floor 0.25, all see pressure)'],
             r['v20 stack (no floor, all see pressure)'] - r['v16 stack (floor 0.25, all see pressure)']))
print("\n(%.0fs)" % (time.time()-t0))
json.dump(out, open('outputs/pressholdout.json','w'), indent=2)
