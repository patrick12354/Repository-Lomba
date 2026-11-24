"""Blend-level test of the pressure-level drop.  s53 is the standing warning: a better
member has made this blend worse before, so the member screen in an_drop.py is not enough.
Computes all five members per fold for both arms, then scores the full v12 stack
(tod-blend + harmonic bias) nested leave-one-fold-out."""
import numpy as np, pandas as pd, pickle, sys, time, os
sys.path.insert(0,'.'); import final_pipeline as fp
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
d85=list(np.load('outputs/drop_85.npy',allow_pickle=True))
ARMS={'base':[], 'drop85':d85}
CACHE='outputs/dropblend_oof.pkl'
res=pickle.load(open(CACHE,'rb')) if os.path.exists(CACHE) else {}
t0=time.time()
for fam,folds in FAMS.items():
    for fi,(vs,ve) in enumerate(folds):
        vm=is_tr&(IDX>vs)&(IDX<=ve); tm=is_tr&(IDX<=vs)
        if vm.sum()<50 or tm.sum()<300: continue
        for arm,drop in ARMS.items():
            if (fam,fi,arm) in res: continue
            cols=[c for c in F.columns if c not in set(drop)]
            Xt,Xv=F.loc[tm,cols],F.loc[vm,cols]; yt=y[tm]
            esv=fp.es(F.loc[vm,'T'].values); estr=pd.Series(fp.es(F.loc[tm,'T'].values),index=IDX[tm])
            E=yt*estr/100.0
            P={m:np.clip(fp.predict(m,Xt,yt,Xv,esv,E,(0,1,2)),5,100) for m in fp.MODELS}
            res[(fam,fi,arm)]=pd.DataFrame(P,index=IDX[vm])
            pickle.dump(res,open(CACHE,'wb'))
        print(f"  {fam}{fi} ({time.time()-t0:.0f}s)",flush=True)
print("cached %d entries"%len(res))
