"""Section 53's swap, re-taken.

Section 52 measured CatBoost's shipped `Huber:delta=4` as the largest single-member
mis-specification in the log -- plain MAE is 0.918 better solo. Section 53 nevertheless kept
the broken one, because SWAPPING it in made the blend worse: the repaired model's residual
correlates 0.93 with `hbt` while the broken one correlates 0.64, so `cat` was earning its
place by being wrong differently.

That test ran under the uniform floor, which had already decided every member got at least
1/5 of the blend regardless. exp61 has since shown `cat_mae` gets exactly zero weight as an
ADDITION. The swap is a different question and is still open.
"""
import pickle, sys, json
import numpy as np, pandas as pd
from scipy.optimize import nnls
sys.path[:0] = ['.', 'src']
import final_pipeline as fp
from robust_eval import paired_summary

frame = pickle.load(open('outputs/robust_core_scored.pkl','rb'))['frame'].copy()
zoo = pickle.load(open('outputs/zoo17_oof.pkl','rb'))
for nm in ('bag_nopress','cat_mae','lin','hbt_e','xt'):
    frame[nm] = np.nan
    for (n, fam, fold), v in zoo.items():
        if n != nm: continue
        m = (frame.family==fam)&(frame.fold==fold)
        frame.loc[m, nm] = v.reindex(pd.DatetimeIndex(frame.loc[m,'datetime'])).values
stress = pickle.load(open('outputs/stress_members.pkl','rb'))
V18 = list(fp.MODELS_L2) + ['robust_hbt', 'bag_nopress']

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

def stress_scores(models):
    have = set(stress[0].columns)
    if not set(models) <= have: return None, None
    se, per = [], []
    for sid in sorted(stress):
        P = stress[sid]
        meta = frame[frame.datetime <= P.index.min()-pd.Timedelta(hours=96)].copy()
        pr, _ = stack(meta, P, models); e = (pr-P.y.values)**2
        se.append(e); per.append(float(np.sqrt(e.mean())))
    return float(np.sqrt(np.concatenate(se).mean())), float(np.max(per))

STACKS = {
  'v18':                        V18,
  'v18, cat -> cat_mae':        [m if m!='cat' else 'cat_mae' for m in V18],
  'v18, drop cat':              [m for m in V18 if m!='cat'],
  'v18, drop hbt':              [m for m in V18 if m!='hbt'],
  'v18, drop robust_hbt':       [m for m in V18 if m!='robust_hbt'],
  'v18, drop enet':             [m for m in V18 if m!='enet'],
  'v18, drop l2':               [m for m in V18 if m!='l2'],
  'v18, drop ridge_e':          [m for m in V18 if m!='ridge_e'],
  'v18, drop ridge':            [m for m in V18 if m!='ridge'],
}
ref, _ = cv(V18); sb, wb = stress_scores(V18)
rng = np.random.default_rng(67); res={}
print("v18: nested %.4f  stress %.4f  worst %.4f\n"
      % (ref.groupby(['family','fold']).apply(lambda d: fp.rmse(d.y,d.pred), include_groups=False).mean(), sb, wb))
print("drop-one ablation and the section 53 swap (positive delta = the member is earning its place)\n")
for name, models in STACKS.items():
    s, gw = cv(models); ps = paired_summary(ref, s)
    fam = ps.groupby('family').delta.agg(['mean', lambda x: int((x<0).sum())])
    sp, sw = stress_scores(models)
    print("%-24s nested %.4f  delta %+.4f  %2d/18  P %+.4f Q %+.4f R %+.4f  stress %s"
          % (name, ps.candidate.mean(), ps.delta.mean(), (ps.delta<0).sum(),
             fam.loc['P','mean'], fam.loc['Q','mean'], fam.loc['R','mean'],
             ("%.4f (%+.4f)" % (sp, sp-sb)) if sp else "n/a"))
    res[name] = dict(nested=float(ps.candidate.mean()), delta=float(ps.delta.mean()),
        won=int((ps.delta<0).sum()), stress=sp,
        families={k: float(fam.loc[k,'mean']) for k in 'PQR'})
json.dump(res, open('outputs/cat_swap.json','w'), indent=2)
