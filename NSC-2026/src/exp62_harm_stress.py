"""Put the harmonic correction through the OOD stress gate.

Section 25 rules post-hoc corrections a default no, and the reason is section 46: the
dispersion correction won 13 of 13 folds across three families and lost 0.237 on the
leaderboard, because nothing available could measure whether it TRANSFERRED. That is no
longer true. Section 110 has just shown the stress blocks reject changes that every CV gate
accepts, so the question can be asked instead of assumed.

Also included: the amplitude guard of section 69.1 -- the ratio of the correction's
amplitude to the blend's own diurnal amplitude, which must stay inside the CV range.
"""
import pickle, sys, json
import numpy as np, pandas as pd
from scipy.optimize import nnls
sys.path[:0] = ['.', 'src']
import final_pipeline as fp
from robust_eval import paired_summary

frame = pickle.load(open('outputs/robust_core_scored.pkl','rb'))['frame'].copy()
stress = pickle.load(open('outputs/stress_members.pkl','rb'))
M = list(fp.MODELS_L2) + ['robust_hbt']
U = np.ones(len(M))/len(M)

def stack(meta, valid, hs):
    w,_ = nnls(meta[M].values, meta.y.values); w = w/w.sum() if w.sum() else U.copy()
    work = meta.copy(); work['blend'] = np.clip(work[M].values @ w, 5, 100)
    edges = np.quantile(work.tod.values, np.linspace(0,1,fp.TOD_BINS+1)); edges[0],edges[-1]=-np.inf,np.inf
    b = np.digitize(work.tod.values, edges[1:-1]); W={}
    for i in range(fp.TOD_BINS):
        d = work[b==i]
        if len(d)<150: W[i]=w; continue
        wi,_ = nnls(d[M].values, d.y.values); wi = wi/wi.sum() if wi.sum()>0 else U.copy()
        W[i] = (1-fp.TOD_SHRINK)*wi + fp.TOD_SHRINK*w
    work['blend'] = np.clip(fp.apply_tod_blend(work[M].values, work.tod.values, edges, W),5,100)
    pr = np.clip(fp.apply_tod_blend(valid[M].values, valid.tod.values, edges, W),5,100)
    h = fp.harm_bias(work, shrink=hs)
    return np.clip(fp.apply_harm_bias(pr, valid.tod.values, h),5,100), h

def cv(hs):
    out=[]; amps=[]
    for family, fold in frame[['family','fold']].drop_duplicates().itertuples(index=False,name=None):
        vm = (frame.family==family)&(frame.fold==fold)
        v = frame.loc[vm].copy()
        v['pred'], h = stack(frame.loc[~vm].copy(), v, hs)
        amps.append(float(np.hypot(*h)))
        out.append(v)
    return pd.concat(out, ignore_index=True), np.array(amps)

def stress_scores(hs):
    se, per = [], []
    for sid in sorted(stress):
        P = stress[sid]
        meta = frame[frame.datetime <= P.index.min()-pd.Timedelta(hours=96)].copy()
        pr, _ = stack(meta, P, hs)
        e = (pr-P.y.values)**2; se.append(e); per.append(float(np.sqrt(e.mean())))
    return float(np.sqrt(np.concatenate(se).mean())), float(np.max(per))

ref, _ = cv(fp.HARM_SHRINK)
sb, wb = stress_scores(fp.HARM_SHRINK)
rng = np.random.default_rng(23)
print("v17 reference (harm 0.50): nested %.4f  stress pooled %.4f  worst block %.4f\n"
      % (ref.groupby(['family','fold']).apply(lambda d: fp.rmse(d.y,d.pred), include_groups=False).mean(), sb, wb))
res={}
for hs in (0.35, 0.50, 0.65, 0.80, 1.00):
    s, amps = cv(hs); ps = paired_summary(ref, s)
    boot = np.array([rng.choice(ps.delta.values, len(ps), True).mean() for _ in range(20000)])
    fam = ps.groupby('family').delta.agg(['mean', lambda x: int((x<0).sum())])
    sp, sw = stress_scores(hs)
    ok = all(fam.loc[k,'mean']<0 for k in 'PQR') and (ps.delta<0).sum()>9 and sp<=sb and sw<=wb
    print("harm %.2f  nested %.4f  delta %+.4f  %2d/18  CI [%+.4f,%+.4f]  P %+.4f Q %+.4f R %+.4f"
          % (hs, ps.candidate.mean(), ps.delta.mean(), (ps.delta<0).sum(),
             np.percentile(boot,2.5), np.percentile(boot,97.5),
             fam.loc['P','mean'], fam.loc['Q','mean'], fam.loc['R','mean']))
    print("    amplitude %.3f-%.3f %%RH over folds   stress pooled %.4f (%+.4f)  worst %.4f (%+.4f)   GATE %s\n"
          % (amps.min(), amps.max(), sp, sp-sb, sw, sw-wb, "PASS" if ok else "FAIL"))
    res["%.2f"%hs] = dict(nested=float(ps.candidate.mean()), delta=float(ps.delta.mean()),
        won=int((ps.delta<0).sum()), ci=[float(np.percentile(boot,2.5)),float(np.percentile(boot,97.5))],
        families={k:[float(fam.loc[k,'mean']),int(fam.loc[k,'<lambda_0>'])] for k in 'PQR'},
        amp=[float(amps.min()),float(amps.max())], stress_pooled=sp, stress_worst=sw, gate=bool(ok))
json.dump(res, open('outputs/harm_stress.json','w'), indent=2)
