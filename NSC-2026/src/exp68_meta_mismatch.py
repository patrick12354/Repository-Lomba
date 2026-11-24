"""Two ways the meta-learner is fitted on something other than what gets deployed.

(a) Training size. The blend weights are fitted on out-of-fold rows pooled across folds
    whose training sets run from 1445 to 2213 rows, while the shipped members are fitted on
    all 2933. Early folds therefore teach NNLS about a weaker ensemble than the one it will
    weight. Section 20 rejected recency weighting of TRAINING rows; this is a different
    object -- weighting META rows by how closely they resemble deployment -- but it is close
    enough to the same objection that it needs the stress gate, not just CV.

(b) Seed count. OOF members use three seeds, the shipped members five. Section 68 measured
    per-row seed sd at 0.37 %RH for `hbt` and 5.49 for `cat`, so the OOF `cat` carries about
    3.2 %RH of Monte-Carlo noise against the shipped 2.5. NNLS sees a noisier `cat` than it
    will deploy and under-weights it. Section 71 already calls this class of thing a defect
    rather than a hyper-parameter. Part (b) needs new fits and lives in exp69.

Predeclared meta-weighting schemes for (a): all folds equal (shipped), folds at or above the
median training size only, and weight proportional to training size.
"""
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
    m = (frame.family == fam) & (frame.fold == fold)
    frame.loc[m, 'bag_nopress'] = v.reindex(pd.DatetimeIndex(frame.loc[m,'datetime'])).values
stress = pickle.load(open('outputs/stress_members.pkl','rb'))
M = list(fp.MODELS_L2) + ['robust_hbt', 'bag_nopress']

# each fold's training size, counted against the real labelled grid rather than against the
# fold cache -- the cache holds validation rows only, so counting inside it understates every
# fold by a factor of three and turns the scheme into plain fold recency.
_g = fp.load_grid()
_lab = _g.index[(_g.is_test == 0).values & _g[fp.TARGET].notna().values]
start = frame.groupby(['family','fold']).datetime.min().rename('start')
trsize = start.apply(lambda t: int((_lab < t).sum())).rename('trsize')
frame = frame.merge(trsize.reset_index(), on=['family','fold'])
print("fold training sizes: %d - %d, median %d"
      % (trsize.min(), trsize.max(), int(trsize.median())))

def wnnls(A, y, sw):
    r = np.sqrt(sw)[:, None]
    w, _ = nnls(A * r, y * np.sqrt(sw))
    return w

def stack(meta, valid, scheme):
    if scheme == 'equal':      sw = np.ones(len(meta))
    elif scheme == 'late':     sw = (meta.trsize.values >= trsize.median()).astype(float)
    elif scheme == 'prop':     sw = meta.trsize.values / float(trsize.max())
    else: raise ValueError(scheme)
    if sw.sum() < 500: sw = np.ones(len(meta))
    U = np.ones(len(M))/len(M)
    w = wnnls(meta[M].values, meta.y.values, sw); w = w/w.sum() if w.sum() else U.copy()
    work = meta.copy(); work['sw'] = sw
    work['blend'] = np.clip(work[M].values @ w,5,100)
    edges = np.quantile(work.tod.values, np.linspace(0,1,fp.TOD_BINS+1)); edges[0],edges[-1]=-np.inf,np.inf
    b = np.digitize(work.tod.values, edges[1:-1]); W={}
    for i in range(fp.TOD_BINS):
        d = work[b==i]
        if len(d)<150 or d.sw.sum() < 150: W[i]=w; continue
        wi = wnnls(d[M].values, d.y.values, d.sw.values)
        wi = wi/wi.sum() if wi.sum()>0 else U.copy()
        W[i] = (1-fp.TOD_SHRINK)*wi + fp.TOD_SHRINK*w
    work['blend'] = np.clip(fp.apply_tod_blend(work[M].values, work.tod.values, edges, W),5,100)
    pr = np.clip(fp.apply_tod_blend(valid[M].values, valid.tod.values, edges, W),5,100)
    return np.clip(fp.apply_harm_bias(pr, valid.tod.values, fp.harm_bias(work)),5,100), w

def cv(scheme):
    out, gw = [], []
    for family, fold in frame[['family','fold']].drop_duplicates().itertuples(index=False,name=None):
        vm = (frame.family==family)&(frame.fold==fold)
        v = frame.loc[vm].copy()
        v['pred'], w = stack(frame.loc[~vm].copy(), v, scheme); gw.append(w); out.append(v)
    return pd.concat(out, ignore_index=True), np.array(gw)

def stress_scores(scheme):
    se, per = [], []
    for sid in sorted(stress):
        P = stress[sid]
        meta = frame[frame.datetime <= P.index.min()-pd.Timedelta(hours=96)].copy()
        pr, _ = stack(meta, P, scheme); e = (pr-P.y.values)**2
        se.append(e); per.append(float(np.sqrt(e.mean())))
    return float(np.sqrt(np.concatenate(se).mean())), float(np.max(per))

ref, gw0 = cv('equal'); sb, wb = stress_scores('equal')
print("v18 reference: nested %.4f   stress pooled %.4f  worst %.4f\n"
      % (ref.groupby(['family','fold']).apply(lambda d: fp.rmse(d.y,d.pred), include_groups=False).mean(), sb, wb))
rng = np.random.default_rng(53); res={}
for scheme in ('equal','late','prop'):
    s, gw = cv(scheme); ps = paired_summary(ref, s)
    fam = ps.groupby('family').delta.agg(['mean', lambda x: int((x<0).sum())])
    boot = np.array([rng.choice(ps.delta.values, len(ps), True).mean() for _ in range(20000)])
    sp, sw2 = stress_scores(scheme)
    ok = all(fam.loc[k,'mean']<0 for k in 'PQR') and (ps.delta<0).sum()>9 and sp<=sb and sw2<=wb
    print("%-6s nested %.4f  delta %+.4f  %2d/18  CI [%+.4f,%+.4f]  P %+.4f Q %+.4f R %+.4f"
          % (scheme, ps.candidate.mean(), ps.delta.mean(), (ps.delta<0).sum(),
             np.percentile(boot,2.5), np.percentile(boot,97.5),
             fam.loc['P','mean'], fam.loc['Q','mean'], fam.loc['R','mean']))
    print("       stress %.4f (%+.4f)  worst %.4f (%+.4f)   GATE %s"
          % (sp, sp-sb, sw2, sw2-wb, "PASS" if ok else "FAIL"))
    print("       weights " + " ".join("%s=%.3f"%(m,x) for m,x in zip(M, gw.mean(0)) if x>0.001) + "\n")
    res[scheme] = dict(nested=float(ps.candidate.mean()), delta=float(ps.delta.mean()),
        won=int((ps.delta<0).sum()), stress=sp, stress_worst=sw2, gate=bool(ok),
        families={k: float(fam.loc[k,'mean']) for k in 'PQR'})
json.dump(res, open('outputs/meta_mismatch.json','w'), indent=2)
