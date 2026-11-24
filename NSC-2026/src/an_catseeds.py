"""Per-fold CatBoost predictions at 20 individual seeds, all three fold families.
Everything else is reused from the h7 cache, so the only thing that changes is cat's
seed count -- a controlled comparison."""
import numpy as np, pandas as pd, pickle, sys, time
sys.path.insert(0,'.'); import final_pipeline as fp
import catboost as cb, os
res_pre = pickle.load(open('outputs/cat_seed_oof.pkl','rb')) if os.path.exists('outputs/cat_seed_oof.pkl') else {}
g=fp.load_grid(); F=fp.make_features(g); y=g[fp.TARGET]; IDX=g.index
is_tr=(g.is_test==0).values & y.notna().values
idx=IDX[is_tr]; end=idx.max()
def famdef(n,vd,sd,mtd=30):
    out=[]
    for i in range(n):
        cut=end-pd.Timedelta(days=sd*i); vs=cut-pd.Timedelta(days=vd)
        if (vs-idx.min()).days<mtd: break
        out.append((vs,cut))
    return out[::-1]
FAMS={'P':famdef(9,15,2),'Q':famdef(6,15,3,36),'R':famdef(5,21,3,28)}
N=20; res=dict(res_pre); t0=time.time()
for fam,folds in FAMS.items():
    for fi,(vs,ve) in enumerate(folds):
        vm=is_tr&(IDX>vs)&(IDX<=ve); tm=is_tr&(IDX<=vs)
        if vm.sum()<50 or tm.sum()<300: continue
        if (fam,fi) in res: print(f"  {fam}{fi} cached",flush=True); continue
        Xt,yt,Xv=F[tm],y[tm],F[vm]
        P=np.zeros((N,int(vm.sum())))
        for s in range(N):
            P[s]=cb.CatBoostRegressor(iterations=1200,learning_rate=0.035,depth=6,
                l2_leaf_reg=6.0,loss_function='Huber:delta=4',random_seed=s,verbose=0,
                allow_writing_files=False).fit(Xt,yt).predict(Xv)
        res[(fam,fi)]=P
        pickle.dump(res,open('outputs/cat_seed_oof.pkl','wb'))   # checkpoint every fold
        print(f"  {fam}{fi} done  n={vm.sum()}  seedstd={P.std(0).mean():.2f}  {time.time()-t0:.0f}s",flush=True)
print("saved outputs/cat_seed_oof.pkl  (%d folds)"%len(res))
