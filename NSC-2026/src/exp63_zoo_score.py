"""Score every zoo candidate as an addition to v17, under the corrected shrinkage,
against the null floor and the OOD stress gate."""
import pickle, sys, json, itertools
import numpy as np, pandas as pd
from scipy.optimize import nnls
sys.path[:0] = ['.', 'src']
import final_pipeline as fp
from robust_eval import paired_summary

frame = pickle.load(open('outputs/robust_core_scored.pkl','rb'))['frame'].copy()
zoo = pickle.load(open('outputs/zoo17_oof.pkl','rb'))
dup = pickle.load(open('outputs/dilution_control_oof.pkl','rb'))

names = sorted({k[0] for k in zoo})
for nm in names:
    frame[nm] = np.nan
    for (n, fam, fold), v in zoo.items():
        if n != nm: continue
        m = (frame.family == fam) & (frame.fold == fold)
        frame.loc[m, nm] = v.reindex(pd.DatetimeIndex(frame.loc[m, 'datetime'])).values
    assert frame[nm].notna().all(), nm
frame['dup_hbt'] = np.nan
for (fam, fold), v in dup.items():
    m = (frame.family == fam) & (frame.fold == fold)
    frame.loc[m, 'dup_hbt'] = v.reindex(pd.DatetimeIndex(frame.loc[m, 'datetime'])).values

BASE = list(fp.MODELS_L2) + ['robust_hbt']

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
    return np.clip(fp.apply_harm_bias(pr, valid.tod.values, fp.harm_bias(work)),5,100), w, W

def cv(models):
    out, gw, bw = [], [], []
    for family, fold in frame[['family','fold']].drop_duplicates().itertuples(index=False,name=None):
        vm = (frame.family==family)&(frame.fold==fold)
        v = frame.loc[vm].copy()
        v['pred'], w, W = stack(frame.loc[~vm].copy(), v, models)
        gw.append(w); bw.append(np.array([W[i] for i in sorted(W)])); out.append(v)
    return pd.concat(out, ignore_index=True), np.array(gw), np.array(bw)

ref, _, _ = cv(BASE)
rng = np.random.default_rng(31)
print("v17 reference: nested %.4f\n"
      % ref.groupby(['family','fold']).apply(lambda d: fp.rmse(d.y,d.pred), include_groups=False).mean())
print("%-13s %8s %9s %7s %19s %8s %8s %8s %7s %7s"
      % ("candidate","nested","delta","folds","95% CI","P","Q","R","w_glob","w_max"))
res = {}
for nm in names + ['dup_hbt']:
    s, gw, bw = cv(BASE + [nm])
    ps = paired_summary(ref, s)
    boot = np.array([rng.choice(ps.delta.values, len(ps), True).mean() for _ in range(20000)])
    fam = ps.groupby('family').delta.agg(['mean', lambda x: int((x<0).sum())])
    rho = float(np.corrcoef(frame[nm]-frame.y, frame['hbt']-frame.y)[0,1])
    solo = fp.rmse(frame.y, frame[nm])
    print("%-13s %8.4f %+9.4f %4d/18  [%+.4f,%+.4f] %+8.4f %+8.4f %+8.4f %7.3f %7.3f"
          % (nm, ps.candidate.mean(), ps.delta.mean(), (ps.delta<0).sum(),
             np.percentile(boot,2.5), np.percentile(boot,97.5),
             fam.loc['P','mean'], fam.loc['Q','mean'], fam.loc['R','mean'],
             gw.mean(0)[-1], bw.mean(0)[:, -1].max()))
    res[nm] = dict(nested=float(ps.candidate.mean()), delta=float(ps.delta.mean()),
        won=int((ps.delta<0).sum()), ci=[float(np.percentile(boot,2.5)),float(np.percentile(boot,97.5))],
        families={k:[float(fam.loc[k,'mean']),int(fam.loc[k,'<lambda_0>'])] for k in 'PQR'},
        w_global=float(gw.mean(0)[-1]), w_band_max=float(bw.mean(0)[:,-1].max()),
        resid_corr_hbt=rho, solo_rmse=float(solo))
print("\nsolo RMSE and residual correlation with hbt:")
for nm in names + ['dup_hbt']:
    print("  %-13s solo %7.3f   resid corr with hbt %+.3f" % (nm, res[nm]['solo_rmse'], res[nm]['resid_corr_hbt']))
json.dump(res, open('outputs/zoo_score.json','w'), indent=2)
