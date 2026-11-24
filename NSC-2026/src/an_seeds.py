"""How much Monte-Carlo seed noise is left in the shipped 5-seed test prediction?"""
import numpy as np, pandas as pd, sys, time, pickle
sys.path.insert(0,'.'); import final_pipeline as fp
import lightgbm as lgb, catboost as cb
g=fp.load_grid(); F=fp.make_features(g); y=g[fp.TARGET]; IDX=F.index
tr=IDX[(g.is_test==0).values & y.notna().values]; te=IDX[(g.is_test==1).values]
X,yy,Xt=F.loc[tr],y.loc[tr],F.loc[te]
N=20; t0=time.time()
H=np.zeros((N,len(te))); C=np.zeros((N,len(te)))
for s in range(N):
    H[s]=lgb.LGBMRegressor(random_state=s,**fp.LGB_KW).fit(X,yy).predict(Xt)
    C[s]=cb.CatBoostRegressor(iterations=1200,learning_rate=0.035,depth=6,l2_leaf_reg=6.0,
        loss_function='Huber:delta=4',random_seed=s,verbose=0,allow_writing_files=False).fit(X,yy).predict(Xt)
    if s%5==4: print(f"  seed {s} ({time.time()-t0:.0f}s)",flush=True)
np.save('outputs/seed_preds_hbt.npy',H); np.save('outputs/seed_preds_cat.npy',C)
for nm,M in (('hbt',H),('cat',C)):
    print(f"\n{nm}: per-row std across 20 single-seed fits = {M.std(0).mean():.3f} %RH (max {M.std(0).max():.2f})")
    for m in (1,3,5,10,20):
        # Monte-Carlo noise remaining in an m-seed average, estimated by disjoint subsets
        reps=[M[i*m:(i+1)*m].mean(0) for i in range(N//m)]
        if len(reps)<2: 
            print(f"   {m:2d} seeds: residual MC noise ~ {M.std(0).mean()/np.sqrt(m):.3f} (analytic)"); continue
        R=np.array(reps); print(f"   {m:2d} seeds: residual MC noise = {R.std(0).mean():.3f} %RH  ({len(reps)} disjoint reps)")
h5,h20=H[:5].mean(0),H.mean(0); c5,c20=C[:5].mean(0),C.mean(0)
print("\nshipped 5-seed vs 20-seed average, RMS difference:  hbt %.3f   cat %.3f"%(
    np.sqrt(((h5-h20)**2).mean()), np.sqrt(((c5-c20)**2).mean())))
w=dict(zip(fp.MODELS,[0.480,0.228,0.050,0.192,0.050]))
d=w['hbt']*(h5-h20)+w['cat']*(c5-c20)
print("blend-level RMS difference from seeds alone: %.3f %%RH  (max %.2f)"%(np.sqrt((d**2).mean()),np.abs(d).max()))
print("\nimplied RMSE cost of stopping at 5 seeds, if MC noise is independent of the error:")
var5=(w['hbt']**2*(H.std(0).mean()**2)+w['cat']**2*(C.std(0).mean()**2))/5
print("   blend MC variance at 5 seeds = %.4f -> at 20 seeds = %.4f"%(var5,var5/4))
for base in (3.03,):
    print("   RMSE %.3f -> %.3f  (delta %+.4f)"%(base,np.sqrt(base**2-var5+var5/4),np.sqrt(base**2-var5+var5/4)-base))
