"""Score the seed-matched stack against v19 on both gates."""
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
seed5 = pickle.load(open('outputs/seed5_oof.pkl','rb'))
f5 = frame.copy()
for name in ('hbt','cat','l2','robust_hbt','bag_nopress'):
    for (n, fam, fold), v in seed5.items():
        if n != name: continue
        m = (f5.family==fam)&(f5.fold==fold)
        f5.loc[m, name] = v.reindex(pd.DatetimeIndex(f5.loc[m,'datetime'])).values
    assert f5[name].notna().all(), name

V19 = [m for m in (list(fp.MODELS_L2) + ['robust_hbt','bag_nopress']) if m != 'ridge']
stress = pickle.load(open('outputs/stress_members.pkl','rb'))

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

def cv(fr, models):
    out, gw = [], []
    for family, fold in fr[['family','fold']].drop_duplicates().itertuples(index=False,name=None):
        vm = (fr.family==family)&(fr.fold==fold)
        v = fr.loc[vm].copy()
        v['pred'], w = stack(fr.loc[~vm].copy(), v, models); gw.append(w); out.append(v)
    return pd.concat(out, ignore_index=True), np.array(gw)

def stress_scores(fr, models):
    se, per = [], []
    for sid in sorted(stress):
        P = stress[sid]
        meta = fr[fr.datetime <= P.index.min()-pd.Timedelta(hours=96)].copy()
        pr, _ = stack(meta, P, models); e = (pr-P.y.values)**2
        se.append(e); per.append(float(np.sqrt(e.mean())))
    return float(np.sqrt(np.concatenate(se).mean())), float(np.max(per))

ref, gw3 = cv(frame, V19); sb, wb = stress_scores(frame, V19)
r3 = ref.groupby(['family','fold']).apply(lambda d: fp.rmse(d.y,d.pred), include_groups=False)
print("v19, OOF at 3 seeds (shipped): nested %.4f  worst %.4f  stress %.4f / %.4f"
      % (r3.mean(), r3.max(), sb, wb))
print("   weights " + " ".join("%s=%.3f"%(m,x) for m,x in zip(V19, gw3.mean(0))))

s, gw5 = cv(f5, V19)
ps = paired_summary(ref, s)
fam = ps.groupby('family').delta.agg(['mean', lambda x: int((x<0).sum())])
rng = np.random.default_rng(97)
boot = np.array([rng.choice(ps.delta.values, len(ps), True).mean() for _ in range(20000)])
sp, sw = stress_scores(f5, V19)
print("\nv19, OOF at 5 seeds:            nested %.4f  worst %.4f  stress %.4f / %.4f"
      % (ps.candidate.mean(), ps.candidate.max(), sp, sw))
print("   weights " + " ".join("%s=%.3f"%(m,x) for m,x in zip(V19, gw5.mean(0))))
print("\ndelta %+.5f  %2d/18  CI [%+.4f,%+.4f]  P %+.4f Q %+.4f R %+.4f   stress %+.4f  worst %+.4f"
      % (ps.delta.mean(), (ps.delta<0).sum(), np.percentile(boot,2.5), np.percentile(boot,97.5),
         fam.loc['P','mean'], fam.loc['Q','mean'], fam.loc['R','mean'], sp-sb, sw-wb))
ok = all(fam.loc[k,'mean']<0 for k in 'PQR') and (ps.delta<0).sum()>9 and sp<=sb and sw<=wb
print("GATE %s" % ("PASS" if ok else "FAIL"))
# how much of the member-level error was Monte-Carlo noise?
print("\nsolo RMSE, 3 seeds -> 5 seeds:")
for m in V19:
    print("  %-12s %7.4f -> %7.4f" % (m, fp.rmse(frame.y, frame[m]), fp.rmse(f5.y, f5[m])))
json.dump(dict(delta=float(ps.delta.mean()), won=int((ps.delta<0).sum()),
               nested3=float(r3.mean()), nested5=float(ps.candidate.mean()),
               stress3=sb, stress5=sp, gate=bool(ok),
               families={k: float(fam.loc[k,'mean']) for k in 'PQR'},
               weights3=dict(zip(V19, map(float, gw3.mean(0)))),
               weights5=dict(zip(V19, map(float, gw5.mean(0))))),
          open('outputs/seedmatch.json','w'), indent=2)
