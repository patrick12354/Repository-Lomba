"""Screen: does dropping the features that lack private-slice support cost anything in CV?
Selection is by COVERAGE (target-free), CV is only the verification -- the s7/s19.2 order,
not s38's prune-by-score trap."""
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
d916=list(np.load('outputs/drop_916.npy',allow_pickle=True))
d85 =list(np.load('outputs/drop_85.npy',allow_pickle=True))
press=[c for c in F.columns if c.startswith('pressure_s') or c in
       ('pressure','pressure_c1h','pressure_c6h','pressure_c24h')]
press=[c for c in press if c!='pressure_slope']
ARMS={'base':[], 'press10':press, 'drop85':d85, 'drop916':d916}
print({k:len(v) for k,v in ARMS.items()})
res=[]; t0=time.time()
for fam,folds in FAMS.items():
    for fi,(vs,ve) in enumerate(folds):
        vm=is_tr&(IDX>vs)&(IDX<=ve); tm=is_tr&(IDX<=vs)
        if vm.sum()<50 or tm.sum()<300: continue
        r=dict(fam=fam,fold=fi)
        for nm,drop in ARMS.items():
            cols=[c for c in F.columns if c not in set(drop)]
            Xt,Xv=F.loc[tm,cols],F.loc[vm,cols]; yt,yv=y[tm],y[vm]
            ph=np.mean([lgb.LGBMRegressor(random_state=s,**fp.LGB_KW).fit(Xt,yt).predict(Xv) for s in (0,1,2)],0)
            pr=fp._pipe(Ridge(alpha=20.0)).fit(Xt,yt).predict(Xv)
            pe=fp._pipe(ElasticNet(alpha=0.05,l1_ratio=0.5,max_iter=8000)).fit(Xt,yt).predict(Xv)
            r[f'hbt_{nm}']=fp.rmse(yv,np.clip(ph,5,100))
            r[f'rdg_{nm}']=fp.rmse(yv,np.clip(pr,5,100))
            r[f'ent_{nm}']=fp.rmse(yv,np.clip(pe,5,100))
        res.append(r); print(f"  {fam}{fi} ({time.time()-t0:.0f}s)",flush=True)
R=pd.DataFrame(res); R.to_csv('outputs/exp_drop.csv',index=False)
print("\nnested-free screen, %d folds.  delta vs the 118-feature base:"%len(R))
print("%-9s %22s %22s %22s"%("arm","hbt","ridge","enet"))
for nm in ARMS:
    if nm=='base': 
        print("%-9s %10.4f %11s %10.4f %11s %10.4f %11s"%('base',R.hbt_base.mean(),'-',R.rdg_base.mean(),'-',R.ent_base.mean(),'-')); continue
    out=[]
    for pre,b in (('hbt','hbt_base'),('rdg','rdg_base'),('ent','ent_base')):
        c=f'{pre}_{nm}'; out.append("%+10.4f %6d/%-4d"%(R[c].mean()-R[b].mean(),(R[c]<R[b]).sum(),len(R)))
    print("%-9s %s %s %s"%(nm,out[0],out[1],out[2]))
