"""Trace the v19-minus-v16 gain against the held-out window's pressure support, then read it
off at the private slice's own support of 0.802.

an27 found no relationship because every CV fold sits at pressure support 0.907-1.000, where
the block is in support and the mechanism cannot operate. an28 found a large one at 0.33-0.43.
Both can be true; what is needed is the curve between them, sampled at the value that matters.
Held-out sets are built from pressure ranks and a fixed RNG -- feature values only, never the
target.
"""
import sys, json, time
import numpy as np, pandas as pd
from scipy.optimize import nnls
sys.path[:0] = ['.', 'src']
import final_pipeline as fp

g = fp.load_grid(); F = fp.make_features(g); y = g[fp.TARGET]; idx = g.index
is_tr = (g.is_test == 0).values & y.notna().values
PRESS = sorted(set(F.columns) - set(fp.no_pressure(F)))
NOP = fp.no_pressure(F); CORE = fp.stable_core(F, (g.is_test==0).values, (g.is_test==1).values)
MEMBERS = {'hbt':None,'cat':None,'ridge':None,'enet':None,'ridge_e':None,'l2':None,
           'robust_hbt':CORE,'bag_nopress':NOP}
V16 = list(fp.MODELS_L2)
V19 = [m for m in V16 if m != 'ridge'] + ['robust_hbt','bag_nopress']

tr_idx = idx[is_tr]
pday = pd.Series(F.loc[tr_idx,'pressure'].values, index=tr_idx.normalize()).groupby(level=0).mean()
order = list(pday.sort_values(ascending=False).index)
rng = np.random.default_rng(11)

def make(kind, k, dilute=0):
    """k highest-pressure days, optionally diluted with `dilute` mid-pressure days."""
    days = list(order[:k])
    if dilute:
        mid = order[len(order)//3: 2*len(order)//3]
        days += list(rng.choice(mid, min(dilute, len(mid)), replace=False))
    return set(days)

def fit(name, cols, trm, vam):
    c = cols or list(F.columns)
    return np.clip(fp.predict(fp.base_model(name), F.loc[trm,c], y[trm].values, F.loc[vam,c],
                   fp.es(F.loc[vam,'T'].values),
                   y[trm].values*fp.es(F.loc[trm,'T'].values)/100.0, fp.SEEDS_OOF), 5, 100)

def blend(meta, P, models, lam):
    U = np.ones(len(models))/len(models)
    w,_ = nnls(meta[models].values, meta.y.values); w = w/w.sum() if w.sum() else U.copy()
    w = (1-lam)*w + lam*U
    work = meta.copy(); work['blend'] = np.clip(work[models].values @ w,5,100)
    e, W = fp.tod_blend_weights(work, w, models=models, blend_shrink=lam)
    work['blend'] = np.clip(fp.apply_tod_blend(work[models].values, work.tod.values, e, W),5,100)
    pr = np.clip(fp.apply_tod_blend(P[models].values, P.tod.values, e, W),5,100)
    return np.clip(fp.apply_harm_bias(pr, P.tod.values, fp.harm_bias(work)),5,100)

SPECS = [(8,0),(12,0),(18,0),(25,0),(8,10),(12,14),(6,18),(4,24),(3,30)]
t0=time.time(); rows=[]
for k, dil in SPECS:
    hold = make('p', k, dil)
    vam = is_tr & np.array([d in hold for d in idx.normalize()])
    trm = is_tr & ~vam
    if vam.sum() < 200 or trm.sum() < 1400: continue
    A,B = F.loc[trm,PRESS], F.loc[vam,PRESS]
    lo,hi = A.quantile(.01), A.quantile(.99)
    sup = float((((B>=lo)&(B<=hi))|B.isna()).mean().mean())
    P = pd.DataFrame(index=idx[vam])
    for m,c in MEMBERS.items(): P[m] = fit(m,c,trm,vam)
    P['tod']=P.index.hour+P.index.minute/60.0; P['y']=y.reindex(P.index).values
    inner = F.index[trm]; cut = inner[int(len(inner)*0.65)]
    itr = trm & (idx<=cut); iva = trm & (idx>cut)
    Mr = pd.DataFrame(index=idx[iva])
    for m,c in MEMBERS.items(): Mr[m] = fit(m,c,itr,iva)
    Mr['tod']=Mr.index.hour+Mr.index.minute/60.0; Mr['y']=y.reindex(Mr.index).values
    r16 = fp.rmse(P.y, blend(Mr,P,V16,0.25))
    r19 = fp.rmse(P.y, blend(Mr,P,V19,0.00))
    r20 = fp.rmse(P.y, blend(Mr,P,V16,0.00))
    rows.append(dict(k=k, dilute=dil, n=int(vam.sum()), sup=sup,
                     v16=r16, v19=r19, v20=r20, g19=r19-r16, g20=r20-r16))
    print("k=%2d dil=%2d  n=%3d  press support %.3f | v16 %.4f  v19 %.4f  v20 %.4f | v19-v16 %+.4f  v20-v16 %+.4f  (%.0fs)"
          % (k, dil, vam.sum(), sup, r16, r19, r20, r19-r16, r20-r16, time.time()-t0), flush=True)
R = pd.DataFrame(rows).sort_values('sup')
sl19 = np.polyfit(R.sup, R.g19, 1); sl20 = np.polyfit(R.sup, R.g20, 1)
print("\n  corr(pressure support, v19-v16 gain) = %+.3f" % np.corrcoef(R.sup, R.g19)[0,1])
print("  corr(pressure support, v20-v16 gain) = %+.3f" % np.corrcoef(R.sup, R.g20)[0,1])
A = F.loc[idx[is_tr], PRESS]; lo,hi = A.quantile(.01), A.quantile(.99)
te = F.loc[(g.is_test==1).values, PRESS]
def c(B): return float((((B>=lo)&(B<=hi))|B.isna()).mean().mean())
for nm, v in (('public 220', c(te.iloc[:220])), ('private 514', c(te.iloc[220:])),
              ('whole test', c(te))):
    print("  at %s (pressure support %.3f): v19-v16 %+.4f   v20-v16 %+.4f"
          % (nm, v, np.polyval(sl19, v), np.polyval(sl20, v)))
json.dump(dict(rows=R.to_dict('records'), slope19=float(sl19[0]), slope20=float(sl20[0])),
          open('outputs/presscurve.json','w'), indent=2)
