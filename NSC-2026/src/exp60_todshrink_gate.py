"""Full gate for the band-shrinkage follow-on: families, bootstrap, worst fold, pooled,
and the OOD stress blocks."""
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

def stack(meta, valid, ts, nb):
    w,_ = nnls(meta[M].values, meta.y.values); w = w/w.sum() if w.sum() else U.copy()
    work = meta.copy(); work['blend'] = np.clip(work[M].values @ w,5,100)
    edges = np.quantile(work.tod.values, np.linspace(0,1,nb+1)); edges[0],edges[-1]=-np.inf,np.inf
    b = np.digitize(work.tod.values, edges[1:-1]); W={}
    for i in range(nb):
        d = work[b==i]
        if len(d)<150: W[i]=w; continue
        wi,_ = nnls(d[M].values, d.y.values); wi = wi/wi.sum() if wi.sum()>0 else U.copy()
        W[i] = (1-ts)*wi + ts*w
    work['blend'] = np.clip(fp.apply_tod_blend(work[M].values, work.tod.values, edges, W),5,100)
    pr = np.clip(fp.apply_tod_blend(valid[M].values, valid.tod.values, edges, W),5,100)
    return np.clip(fp.apply_harm_bias(pr, valid.tod.values, fp.harm_bias(work)),5,100)

def cv(ts, nb):
    out=[]
    for family, fold in frame[['family','fold']].drop_duplicates().itertuples(index=False,name=None):
        vm = (frame.family==family)&(frame.fold==fold)
        v = frame.loc[vm].copy(); v['pred'] = stack(frame.loc[~vm].copy(), v, ts, nb); out.append(v)
    return pd.concat(out, ignore_index=True)

def stress_scores(ts, nb):
    se, per = [], []
    for sid in sorted(stress):
        P = stress[sid]
        meta = frame[frame.datetime <= P.index.min()-pd.Timedelta(hours=96)].copy()
        pr = stack(meta, P, ts, nb); e = (pr-P.y.values)**2
        se.append(e); per.append(float(np.sqrt(e.mean())))
    return float(np.sqrt(np.concatenate(se).mean())), float(np.max(per)), per

ref = cv(fp.TOD_SHRINK, fp.TOD_BINS)
sb, wb, _ = stress_scores(fp.TOD_SHRINK, fp.TOD_BINS)
rng = np.random.default_rng(11)
print("reference v17 (tod-shrink 0.50, 3 bands): stress pooled %.4f  worst %.4f\n" % (sb, wb))
res={}
for ts, nb in ((0.25,3),(0.00,3),(0.50,6),(0.25,6)):
    s = cv(ts, nb); ps = paired_summary(ref, s)
    boot = np.array([rng.choice(ps.delta.values, len(ps), True).mean() for _ in range(20000)])
    fam = ps.groupby('family').delta.agg(['mean', lambda x: int((x<0).sum()), 'size'])
    sp, sw, per = stress_scores(ts, nb)
    ok = all(fam.loc[k,'mean'] < 0 for k in 'PQR') and (ps.delta<0).sum() > 9 and sp <= sb and sw <= wb
    print("shrink %.2f / %d bands  nested %.4f  delta %+.4f  %2d/18  CI [%+.4f,%+.4f]"
          % (ts, nb, ps.candidate.mean(), ps.delta.mean(), (ps.delta<0).sum(),
             np.percentile(boot,2.5), np.percentile(boot,97.5)))
    print("    P %+.4f (%d/9)  Q %+.4f (%d/4)  R %+.4f (%d/5)   worst fold %.4f"
          % (fam.loc['P','mean'],fam.loc['P','<lambda_0>'],fam.loc['Q','mean'],fam.loc['Q','<lambda_0>'],
             fam.loc['R','mean'],fam.loc['R','<lambda_0>'], ps.candidate.max()))
    print("    stress pooled %.4f (%+.4f)  worst block %.4f (%+.4f)   GATE: %s\n"
          % (sp, sp-sb, sw, sw-wb, "PASS" if ok else "FAIL"))
    res["%.2f_%d"%(ts,nb)] = dict(nested=float(ps.candidate.mean()), delta=float(ps.delta.mean()),
        won=int((ps.delta<0).sum()), ci=[float(np.percentile(boot,2.5)),float(np.percentile(boot,97.5))],
        families={k:[float(fam.loc[k,'mean']),int(fam.loc[k,'<lambda_0>'])] for k in 'PQR'},
        worst=float(ps.candidate.max()), stress_pooled=sp, stress_worst=sw, gate=bool(ok))
json.dump(res, open('outputs/todshrink_gate.json','w'), indent=2)
