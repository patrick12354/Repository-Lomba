"""The two survivors, alone and together, and whether they make robust_hbt redundant.

Predeclared set -- six stacks, not a scan. bag_nopress is section 80's low-support filter
applied to ONE member instead of to all of them, and it overlaps robust_hbt (which also
drops the pressure block), so the redundancy question has to be asked explicitly.
"""
import pickle, sys, json
import numpy as np, pandas as pd
from scipy.optimize import nnls
sys.path[:0] = ['.', 'src']
import final_pipeline as fp
from robust_eval import paired_summary

frame = pickle.load(open('outputs/robust_core_scored.pkl','rb'))['frame'].copy()
zoo = pickle.load(open('outputs/zoo17_oof.pkl','rb'))
for nm in ('bag_nopress', 'lin'):
    frame[nm] = np.nan
    for (n, fam, fold), v in zoo.items():
        if n != nm: continue
        m = (frame.family == fam) & (frame.fold == fold)
        frame.loc[m, nm] = v.reindex(pd.DatetimeIndex(frame.loc[m,'datetime'])).values
    assert frame[nm].notna().all()

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
    return np.clip(fp.apply_harm_bias(pr, valid.tod.values, fp.harm_bias(work)),5,100), w

def cv(models):
    out, gw = [], []
    for family, fold in frame[['family','fold']].drop_duplicates().itertuples(index=False,name=None):
        vm = (frame.family==family)&(frame.fold==fold)
        v = frame.loc[vm].copy()
        v['pred'], w = stack(frame.loc[~vm].copy(), v, models); gw.append(w); out.append(v)
    return pd.concat(out, ignore_index=True), np.array(gw)

STACKS = {
 'v17 (7 members)':                 V17,
 '+bag_nopress':                    V17 + ['bag_nopress'],
 '+lin':                            V17 + ['lin'],
 '+bag_nopress +lin':               V17 + ['bag_nopress', 'lin'],
 '+bag_nopress +lin, no robust':    [m for m in V17 if m != 'robust_hbt'] + ['bag_nopress','lin'],
 '+bag_nopress, no robust':         [m for m in V17 if m != 'robust_hbt'] + ['bag_nopress'],
}
ref, _ = cv(V17)
rng = np.random.default_rng(41); res = {}
for name, models in STACKS.items():
    s, gw = cv(models)
    ps = paired_summary(ref, s)
    boot = np.array([rng.choice(ps.delta.values, len(ps), True).mean() for _ in range(20000)])
    fam = ps.groupby('family').delta.agg(['mean', lambda x: int((x<0).sum())])
    print("%-32s nested %.4f  delta %+.4f  %2d/18  CI [%+.4f,%+.4f]  P %+.4f Q %+.4f R %+.4f  worst %.4f"
          % (name, ps.candidate.mean(), ps.delta.mean(), (ps.delta<0).sum(),
             np.percentile(boot,2.5), np.percentile(boot,97.5),
             fam.loc['P','mean'], fam.loc['Q','mean'], fam.loc['R','mean'], ps.candidate.max()))
    print("     weights " + " ".join("%s=%.3f" % (m, x) for m, x in zip(models, gw.mean(0)) if x > 0.001))
    res[name] = dict(nested=float(ps.candidate.mean()), delta=float(ps.delta.mean()),
        won=int((ps.delta<0).sum()), ci=[float(np.percentile(boot,2.5)),float(np.percentile(boot,97.5))],
        families={k:[float(fam.loc[k,'mean']),int(fam.loc[k,'<lambda_0>'])] for k in 'PQR'},
        worst=float(ps.candidate.max()),
        weights={m: float(x) for m, x in zip(models, gw.mean(0))})
json.dump(res, open('outputs/combo.json','w'), indent=2)
