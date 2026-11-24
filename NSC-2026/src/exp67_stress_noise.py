"""How large is a stress-evaluation delta before it means anything?

The gate rejects a candidate whose stress score regresses. exp66 puts bag_nopress at
+0.0068 and lin at +0.0855 against v17, and those two numbers should not be treated the
same way. Bootstrap the stress rows to get the paired standard error, and add the null
member as a scale: whatever a member with no information does to the stress score is the
resolution floor of this instrument.
"""
import pickle, sys, json
import numpy as np, pandas as pd
from scipy.optimize import nnls
sys.path[:0] = ['.', 'src']
import final_pipeline as fp

frame = pickle.load(open('outputs/robust_core_scored.pkl','rb'))['frame'].copy()
zoo = pickle.load(open('outputs/zoo17_oof.pkl','rb'))
for nm in ('bag_nopress', 'lin'):
    frame[nm] = np.nan
    for (n, fam, fold), v in zoo.items():
        if n != nm: continue
        m = (frame.family == fam) & (frame.fold == fold)
        frame.loc[m, nm] = v.reindex(pd.DatetimeIndex(frame.loc[m,'datetime'])).values
rs = np.random.default_rng(4242)
frame['noise_hbt'] = frame['hbt'] + rs.normal(0, frame['hbt'].std()*0.02, len(frame))
stress = pickle.load(open('outputs/stress_members.pkl','rb'))
for sid in stress:
    P = stress[sid]
    if 'noise_hbt' not in P:
        P.insert(len(P.columns)-2, 'noise_hbt',
                 P['hbt'].values + np.random.default_rng(sid).normal(0, P['hbt'].std()*0.02, len(P)))
V17 = list(fp.MODELS_L2) + ['robust_hbt']

def stack(meta, valid, models):
    U = np.ones(len(models))/len(models)
    w,_ = nnls(meta[models].values, meta.y.values); w = w/w.sum() if w.sum() else U.copy()
    work = meta.copy(); work['blend'] = np.clip(work[models].values @ w,5,100)
    edges = np.quantile(work.tod.values, np.linspace(0,1,fp.TOD_BINS+1)); edges[0],edges[-1]=-np.inf,np.inf
    b = np.digitize(work.tod.values, edges[1:-1]); W={}
    for i in range(fp.TOD_BINS):
        d = work[b==i]
        if len(d)<150: W[i]=w; continue
        wi,_ = nnls(d[models].values, d.y.values); wi = wi/wi.sum() if wi.sum()>0 else U.copy()
        W[i] = (1-fp.TOD_SHRINK)*wi + fp.TOD_SHRINK*w
    work['blend'] = np.clip(fp.apply_tod_blend(work[models].values, work.tod.values, edges, W),5,100)
    pr = np.clip(fp.apply_tod_blend(valid[models].values, valid.tod.values, edges, W),5,100)
    return np.clip(fp.apply_harm_bias(pr, valid.tod.values, fp.harm_bias(work)),5,100)

def sqerr(models):
    out = []
    for sid in sorted(stress):
        P = stress[sid]
        meta = frame[frame.datetime <= P.index.min()-pd.Timedelta(hours=96)].copy()
        pr = stack(meta, P, models)
        out.append(pd.DataFrame({'block': sid, 'se': (pr-P.y.values)**2}))
    return pd.concat(out, ignore_index=True)

base = sqerr(V17)
rng = np.random.default_rng(77)
print("stress pooled RMSE of v17: %.4f on %d rows, %d blocks\n"
      % (np.sqrt(base.se.mean()), len(base), base.block.nunique()))
res = {}
for nm in ('noise_hbt', 'bag_nopress', 'lin'):
    cand = sqerr(V17 + [nm])
    d = np.sqrt(cand.se.mean()) - np.sqrt(base.se.mean())
    # paired block bootstrap: resample whole blocks, which is the unit that is independent
    blocks = sorted(base.block.unique())
    bs = []
    for _ in range(5000):
        pick = rng.choice(blocks, len(blocks), replace=True)
        b = np.concatenate([base.se.values[base.block.values == p] for p in pick])
        c = np.concatenate([cand.se.values[cand.block.values == p] for p in pick])
        bs.append(np.sqrt(c.mean()) - np.sqrt(b.mean()))
    bs = np.array(bs)
    print("%-12s stress delta %+.4f   block-bootstrap sd %.4f   95%% CI [%+.4f,%+.4f]   P(worse) %.3f"
          % (nm, d, bs.std(), np.percentile(bs,2.5), np.percentile(bs,97.5), (bs>0).mean()))
    res[nm] = dict(delta=float(d), sd=float(bs.std()),
                   ci=[float(np.percentile(bs,2.5)), float(np.percentile(bs,97.5))],
                   p_worse=float((bs>0).mean()))
json.dump(res, open('outputs/stress_noise.json','w'), indent=2)
print("\nresolution floor: a member carrying no information moves the stress score by %+.4f"
      % res['noise_hbt']['delta'])
