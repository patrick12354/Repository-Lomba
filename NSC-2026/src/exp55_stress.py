"""OOD stress gate for the shrinkage change and the robust-core member.

The stress blocks are the training blocks whose target-free descriptors sit closest to the
private slice's. Labels come only from train.csv; the private features are used only to
say which direction is 'stressed'.
"""
import pickle, sys, json, time
import numpy as np, pandas as pd
from scipy.optimize import nnls
sys.path[:0] = ['.', 'src']
import final_pipeline as fp
from robust_eval import (block_descriptors, feature_groups, make_stress_splits,
                         score_blocks_against_reference, support_fraction)

CACHE = 'outputs/stress_members.pkl'
g = fp.load_grid(); F = fp.make_features(g); y = g[fp.TARGET]; idx = g.index
is_tr = (g.is_test == 0).values & y.notna().values
is_te = (g.is_test == 1).values
cov = support_fraction(F.loc[is_tr], F.loc[is_te])
core = feature_groups(F.columns, cov)['stable_core']
M6 = list(fp.MODELS_L2)

trF = F.loc[is_tr]
desc = block_descriptors(trF, block_days=3)
priv = F.loc[is_te].iloc[220:]
ref = pd.Series({'pressure': priv.pressure.median(), 'temp_range': priv.T_rng48.median(),
                 'missing': priv.isna().mean().mean(),
                 'season': (priv.index.min() - trF.index.min()).total_seconds()/86400.0})
desc['stress_score'] = score_blocks_against_reference(desc, ref)
splits = make_stress_splits(trF.index, desc, n=5, embargo_hours=96, min_train_rows=1000)
print("stress splits:", [(str(v.min()), len(v)) for _, v in splits])

cache = pickle.load(open(CACHE,'rb')) if __import__('os').path.exists(CACHE) else {}
t0 = time.time()
for sid, (ti, vi) in enumerate(splits):
    if sid in cache and cache[sid].index.equals(pd.DatetimeIndex(vi)): continue
    trm = idx.isin(ti) & is_tr; vam = idx.isin(vi) & is_tr
    P = pd.DataFrame(index=idx[vam])
    for m in M6:
        P[m] = np.clip(fp.predict(m, F.loc[trm], y[trm].values, F.loc[vam],
                       fp.es(F.loc[vam,'T'].values),
                       y[trm].values*fp.es(F.loc[trm,'T'].values)/100.0, fp.SEEDS_OOF), 5, 100)
    P['robust_hbt'] = np.clip(fp.predict('hbt', F.loc[trm, core], y[trm].values, F.loc[vam, core],
                       fp.es(F.loc[vam,'T'].values),
                       y[trm].values*fp.es(F.loc[trm,'T'].values)/100.0, fp.SEEDS_OOF), 5, 100)
    P['tod'] = P.index.hour + P.index.minute/60.0
    P['y'] = y.reindex(P.index).values
    cache[sid] = P; pickle.dump(cache, open(CACHE,'wb'))
    print("stress %d fitted (%.0fs)" % (sid, time.time()-t0), flush=True)

A = pickle.load(open('outputs/robust_core_scored.pkl','rb')); frame = A['frame']

def predict_stack(meta, valid, models, glam, blam):
    U = np.ones(len(models))/len(models)
    w, _ = nnls(meta[models].values, meta.y.values)
    w = w/w.sum() if w.sum() else U.copy()
    w = (1-glam)*w + glam*U
    work = meta.copy(); work['blend'] = np.clip(work[models].values @ w, 5, 100)
    edges = np.quantile(work.tod.values, np.linspace(0,1,fp.TOD_BINS+1)); edges[0],edges[-1]=-np.inf,np.inf
    b = np.digitize(work.tod.values, edges[1:-1]); W={}
    for i in range(fp.TOD_BINS):
        d = work[b==i]
        if len(d)<150: W[i]=w; continue
        wi,_ = nnls(d[models].values, d.y.values); wi = wi/wi.sum() if wi.sum()>0 else U.copy()
        wi = (1-blam)*wi + blam*U
        W[i] = (1-fp.TOD_SHRINK)*wi + fp.TOD_SHRINK*w
    work['blend'] = np.clip(fp.apply_tod_blend(work[models].values, work.tod.values, edges, W),5,100)
    pr = np.clip(fp.apply_tod_blend(valid[models].values, valid.tod.values, edges, W),5,100)
    return np.clip(fp.apply_harm_bias(pr, valid.tod.values, fp.harm_bias(work)),5,100)

ARMS = [('v16 shipped   (0.25/0.25)', M6, 0.25, 0.25),
        ('v16           (0.05/0.05)', M6, 0.05, 0.05),
        ('v16           (0.00/0.00)', M6, 0.00, 0.00),
        ('v16+core      (0.25/0.25)', M6+['robust_hbt'], 0.25, 0.25),
        ('v16+core      (0.05/0.05)', M6+['robust_hbt'], 0.05, 0.05),
        ('v16+core      (0.00/0.00)', M6+['robust_hbt'], 0.00, 0.00)]
tab = {}
for name, models, gl, bl in ARMS:
    rs, oos = [], []
    for sid, (ti, vi) in enumerate(splits):
        P = cache[sid]
        meta = frame[frame.datetime <= ti.max()].copy()
        if 'robust_hbt' not in meta and 'robust_hbt' in models: raise SystemExit('missing')
        pr = predict_stack(meta, P, models, gl, bl)
        rs.append(fp.rmse(P.y.values, pr))
        # rows whose features leave the split-train 1-99 band -- the OOD subset
        lo, hi = F.loc[idx.isin(ti) & is_tr].quantile(.01), F.loc[idx.isin(ti) & is_tr].quantile(.99)
        Fv = F.loc[P.index]
        outside = (((Fv < lo) | (Fv > hi)) & Fv.notna()).mean(1) > 0.10
        oos.append(fp.rmse(P.y.values[outside.values], pr[outside.values]) if outside.sum() > 20 else np.nan)
    tab[name] = (np.array(rs), np.array(oos))
    print("%-27s mean %.4f  worst %.4f  |  out-of-support-row rmse %s"
          % (name, np.mean(rs), np.max(rs), np.round(oos,3)))
base = tab['v16 shipped   (0.25/0.25)'][0]
print("\ndeltas against v16 shipped:")
for k,(v,o) in tab.items():
    print("  %-27s mean %+.4f  worst %+.4f  blocks improved %d/%d"
          % (k, np.mean(v)-np.mean(base), np.max(v)-np.max(base), int((v<base).sum()), len(v)))
json.dump({k: dict(mean=float(np.mean(v)), worst=float(np.max(v)), per_block=list(map(float,v)))
           for k,(v,o) in tab.items()}, open('outputs/stress_eval.json','w'), indent=2)
