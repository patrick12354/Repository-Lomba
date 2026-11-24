"""OOD stress gate for the session-17 candidates. Pooled aggregation, per section 109."""
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
stress = pickle.load(open('outputs/stress_members.pkl','rb'))
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

def scores(models):
    se, per = [], []
    for sid in sorted(stress):
        P = stress[sid]
        meta = frame[frame.datetime <= P.index.min()-pd.Timedelta(hours=96)].copy()
        pr = stack(meta, P, models); e = (pr-P.y.values)**2
        se.append(e); per.append(float(np.sqrt(e.mean())))
    return float(np.sqrt(np.concatenate(se).mean())), float(np.max(per)), per

def cvmean(models):
    ses = []
    for family, fold in frame[['family','fold']].drop_duplicates().itertuples(index=False,name=None):
        vm = (frame.family==family)&(frame.fold==fold)
        v = frame.loc[vm].copy()
        pr = stack(frame.loc[~vm].copy(), v, models)
        ses.append(pd.DataFrame({'family':family,'fold':fold,'se':(pr-v.y.values)**2}))
    R = pd.concat(ses); f = R.groupby(['family','fold']).se.mean().pow(.5)
    return float(f.mean()), float(np.sqrt(R.se.mean())), float(f.max())

STACKS = {'v16 shipped': (list(fp.MODELS_L2), 0.25),
          'v17': (V17, 0.0),
          'v17 +bag_nopress': (V17+['bag_nopress'], 0.0),
          'v17 +lin': (V17+['lin'], 0.0),
          'v17 +bag_nopress +lin': (V17+['bag_nopress','lin'], 0.0)}
sb = wb = None; res = {}
print("%-24s %9s %9s %8s | %9s %9s" % ("stack","cv mean","cv pooled","cv worst","stress","st worst"))
for name, (models, lam) in STACKS.items():
    if lam:   # v16 needs the old floor; rebuild it here rather than branching stack()
        import types
        U = np.ones(len(models))/len(models)
        def stack16(meta, valid, models=models, U=U):
            w,_ = nnls(meta[models].values, meta.y.values); w = w/w.sum() if w.sum() else U.copy()
            w = 0.75*w + 0.25*U
            work = meta.copy(); work['blend']=np.clip(work[models].values@w,5,100)
            e2, W = fp.tod_blend_weights(work, w, models=models, blend_shrink=0.25)
            work['blend']=np.clip(fp.apply_tod_blend(work[models].values, work.tod.values,e2,W),5,100)
            pr=np.clip(fp.apply_tod_blend(valid[models].values, valid.tod.values,e2,W),5,100)
            return np.clip(fp.apply_harm_bias(pr, valid.tod.values, fp.harm_bias(work)),5,100)
        g0 = globals()['stack']; globals()['stack'] = stack16
        cvm, cvp, cvw = cvmean(models); sp, sw, per = scores(models)
        globals()['stack'] = g0
    else:
        cvm, cvp, cvw = cvmean(models); sp, sw, per = scores(models)
    if sb is None: sb, wb = sp, sw
    print("%-24s %9.4f %9.4f %8.4f | %9.4f %9.4f" % (name, cvm, cvp, cvw, sp, sw))
    res[name] = dict(cv_mean=cvm, cv_pooled=cvp, cv_worst=cvw, stress=sp, stress_worst=sw, per_block=per)
print()
b = res['v17']
print("deltas against v17 (the current recommendation):")
for k, v in res.items():
    print("  %-24s cv %+.4f  cv pooled %+.4f  stress %+.4f  stress worst %+.4f   %s"
          % (k, v['cv_mean']-b['cv_mean'], v['cv_pooled']-b['cv_pooled'],
             v['stress']-b['stress'], v['stress_worst']-b['stress_worst'],
             "GATE PASS" if (v['cv_mean']<b['cv_mean'] and v['stress']<=b['stress']
                             and v['stress_worst']<=b['stress_worst']) else ""))
json.dump(res, open('outputs/stress_gate2.json','w'), indent=2)
