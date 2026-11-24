"""Covariate-shift reweighting.  The test window is dominated by the coldest temperature
band, which is where this model is worst (OOF RMSE 7.30 vs 3.05 warmest) and which is only
16.7% of training rows.  Standard fix: weight training rows by p_val(T)/p_train(T).

Honest analogue in CV: reweight each fold's TRAINING rows toward that fold's own VALIDATION
temperature distribution, then score the fold.  If that works across folds it should
transfer to the test window, whose distribution is known (T is a concurrent sensor).
"""
import numpy as np, pandas as pd, sys, time
sys.path.insert(0,'.'); import final_pipeline as fp
import lightgbm as lgb
from sklearn.linear_model import Ridge, ElasticNet
g=fp.load_grid(); F=fp.make_features(g); y=g[fp.TARGET]; IDX=g.index
is_tr=(g.is_test==0).values & y.notna().values; idx=IDX[is_tr]; end=idx.max()
def famdef(n,vd,sd,mtd=30):
    out=[]
    for i in range(n):
        cut=end-pd.Timedelta(days=sd*i); vs=cut-pd.Timedelta(days=vd)
        if (vs-idx.min()).days<mtd: break
        out.append((vs,cut))
    return out[::-1]
FAMS={'P':famdef(9,15,2),'Q':famdef(6,15,3,36),'R':famdef(5,21,3,28)}
EDGES=np.quantile(F.loc[idx,'T'].values,np.linspace(0,1,11))
EDGES[0],EDGES[-1]=-np.inf,np.inf
def ratio_w(Ttr,Tva,alpha,clip):
    btr=np.digitize(Ttr,EDGES[1:-1]); bva=np.digitize(Tva,EDGES[1:-1])
    ptr=np.bincount(btr,minlength=10)/len(btr); pva=np.bincount(bva,minlength=10)/len(bva)
    r=np.where(ptr>0,pva/np.maximum(ptr,1e-9),1.0)
    w=np.clip(r[btr]**alpha,1/clip,clip)
    return w/w.mean()
CFG=[(0.0,1.0),(0.25,3.0),(0.5,3.0),(0.5,5.0),(1.0,3.0),(1.0,5.0)]
res=[]; t0=time.time()
for fam,folds in FAMS.items():
    for fi,(vs,ve) in enumerate(folds):
        vm=is_tr&(IDX>vs)&(IDX<=ve); tm=is_tr&(IDX<=vs)
        if vm.sum()<50 or tm.sum()<300: continue
        Xt,yt,Xv,yv=F[tm],y[tm],F[vm],y[vm]
        Tt,Tv=F.loc[tm,'T'].values,F.loc[vm,'T'].values
        r=dict(fam=fam,fold=fi,ess_frac=np.nan)
        for a,c in CFG:
            w=ratio_w(Tt,Tv,a,c)
            ess=w.sum()**2/(w**2).sum()/len(w)
            p_h=lgb.LGBMRegressor(random_state=0,**fp.LGB_KW).fit(Xt,yt,sample_weight=w).predict(Xv)
            pr=fp._pipe(Ridge(alpha=20.0)).fit(Xt,yt,ridge__sample_weight=w).predict(Xv)
            r[f'hbt_a{a}_c{c}']=fp.rmse(yv,np.clip(p_h,5,100))
            r[f'rdg_a{a}_c{c}']=fp.rmse(yv,np.clip(pr,5,100))
            if a>0: r[f'ess_a{a}_c{c}']=ess
        res.append(r); print(f"  {fam}{fi} ({time.time()-t0:.0f}s)",flush=True)
R=pd.DataFrame(res); R.to_csv('outputs/exp_reweight.csv',index=False)
b_h,b_r='hbt_a0.0_c1.0','rdg_a0.0_c1.0'
print("\nunweighted baseline: hbt %.4f   ridge %.4f  (%d folds)"%(R[b_h].mean(),R[b_r].mean(),len(R)))
print("%-14s %10s %8s | %10s %8s | %s"%("config","hbt delta","folds","ridge delta","folds","mean ESS"))
for a,c in CFG:
    if a==0: continue
    hc,rc,ec=f'hbt_a{a}_c{c}',f'rdg_a{a}_c{c}',f'ess_a{a}_c{c}'
    print("%-14s %+10.4f %5d/%d | %+10.4f %5d/%d | %.2f"%(f"alpha={a} clip={c}",
        R[hc].mean()-R[b_h].mean(),(R[hc]<R[b_h]).sum(),len(R),
        R[rc].mean()-R[b_r].mean(),(R[rc]<R[b_r]).sum(),len(R),R[ec].mean()))
