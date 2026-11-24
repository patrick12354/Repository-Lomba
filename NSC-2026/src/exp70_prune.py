"""Section 53's rule says judge members by the drop-one ablation and nothing else. Applied
to v18 it says `hbt` (-0.0039) and `ridge` (-0.0009) contribute nothing: `bag_nopress`
supersedes `hbt` on 108 of the same 118 columns, and `ridge` has had zero global weight since
the floor came off. Test removing them, singly and together, against both gates."""
import pickle, sys, json
import numpy as np, pandas as pd
from scipy.optimize import nnls
sys.path[:0] = ['.', 'src']
import final_pipeline as fp
from robust_eval import paired_summary

frame = pickle.load(open('outputs/robust_core_scored.pkl','rb'))['frame'].copy()
zoo = pickle.load(open('outputs/zoo17_oof.pkl','rb'))
frame['bag_nopress'] = np.nan
for (n, fam, fold), v in zoo.items():
    if n != 'bag_nopress': continue
    m = (frame.family==fam)&(frame.fold==fold)
    frame.loc[m,'bag_nopress'] = v.reindex(pd.DatetimeIndex(frame.loc[m,'datetime'])).values
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
    return np.clip(fp.apply_harm_bias(pr, valid.tod.values, fp.harm_bias(work)),5,100)

def cv(models):
    out=[]
    for family, fold in frame[['family','fold']].drop_duplicates().itertuples(index=False,name=None):
        vm = (frame.family==family)&(frame.fold==fold)
        v = frame.loc[vm].copy(); v['pred'] = stack(frame.loc[~vm].copy(), v, models); out.append(v)
    return pd.concat(out, ignore_index=True)

def stress_scores(models):
    se, per = [], []
    for sid in sorted(stress):
        P = stress[sid]
        meta = frame[frame.datetime <= P.index.min()-pd.Timedelta(hours=96)].copy()
        pr = stack(meta, P, models); e = (pr-P.y.values)**2
        se.append(e); per.append(float(np.sqrt(e.mean())))
    return float(np.sqrt(np.concatenate(se).mean())), float(np.max(per)), np.concatenate(se)

ref = cv(V18); sb, wb, sse = stress_scores(V18)
rng = np.random.default_rng(83); res={}
print("v18: nested %.4f  stress pooled %.4f  worst block %.4f\n"
      % (ref.groupby(['family','fold']).apply(lambda d: fp.rmse(d.y,d.pred), include_groups=False).mean(), sb, wb))
for name, drop in (('drop ridge', ['ridge']), ('drop hbt', ['hbt']),
                   ('drop hbt + ridge', ['hbt','ridge']),
                   ('drop hbt + ridge + l2', ['hbt','ridge','l2'])):
    models = [m for m in V18 if m not in drop]
    s = cv(models); ps = paired_summary(ref, s)
    fam = ps.groupby('family').delta.agg(['mean', lambda x: int((x<0).sum())])
    boot = np.array([rng.choice(ps.delta.values, len(ps), True).mean() for _ in range(20000)])
    sp, sw, cse = stress_scores(models)
    # block bootstrap on the stress delta
    blocks = np.repeat(np.arange(len(stress)), [len(stress[i]) for i in sorted(stress)])
    bs=[]
    for _ in range(4000):
        pick = rng.choice(np.arange(len(stress)), len(stress), True)
        bi = np.concatenate([np.where(blocks==p)[0] for p in pick])
        bs.append(np.sqrt(cse[bi].mean())-np.sqrt(sse[bi].mean()))
    bs=np.array(bs)
    ok = all(fam.loc[k,'mean']<=0 for k in 'PQR') and (ps.delta<0).sum()>=9 and sp<=sb and sw<=wb
    print("%-24s nested %.4f  delta %+.5f  %2d/18  CI [%+.4f,%+.4f]  P %+.4f Q %+.4f R %+.4f"
          % (name, ps.candidate.mean(), ps.delta.mean(), (ps.delta<0).sum(),
             np.percentile(boot,2.5), np.percentile(boot,97.5),
             fam.loc['P','mean'], fam.loc['Q','mean'], fam.loc['R','mean']))
    print("     stress %.4f (%+.4f, block-bootstrap CI [%+.4f,%+.4f])  worst %.4f (%+.4f)   %s\n"
          % (sp, sp-sb, np.percentile(bs,2.5), np.percentile(bs,97.5), sw, sw-wb,
             "GATE PASS" if ok else "GATE FAIL"))
    res[name] = dict(nested=float(ps.candidate.mean()), delta=float(ps.delta.mean()),
        won=int((ps.delta<0).sum()), stress=sp, stress_delta=float(sp-sb),
        stress_ci=[float(np.percentile(bs,2.5)),float(np.percentile(bs,97.5))],
        stress_worst=sw, gate=bool(ok), families={k: float(fam.loc[k,'mean']) for k in 'PQR'})
json.dump(res, open('outputs/prune.json','w'), indent=2)
