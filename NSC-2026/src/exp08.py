import warnings; warnings.filterwarnings('ignore')
import sys, json, numpy as np, pandas as pd, pickle
sys.path.insert(0,'src')
from common import *
from screen import origins
import lightgbm as lgb, catboost as cb
from sklearn.linear_model import Ridge, ElasticNet, HuberRegressor
from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from scipy.optimize import nnls

g,_,_=load_grid(); is_tr=pd.Series((g.is_test==0).values,index=g.index); y=g[TARGET]
c=clean_exog(g); F=build_features(c); F=F[feature_set(F,'nosoil')]
folds=origins(g.index[is_tr & y.notna()], n=9, val_days=15, step_days=2)
tr=(is_tr & y.notna()); idx=F.index

def cv(mk,label,seeds=(0,),KEEP=None):
    sc=[]; rows=[]
    for fi,(vs,ve) in enumerate(folds):
        v=tr&(idx>vs)&(idx<=ve); t=tr&(idx<=vs)
        ps=[]
        for sd in seeds:
            m=mk(sd); m.fit(F[t],y[t]); ps.append(np.asarray(m.predict(F[v])).ravel())
        p=np.clip(np.mean(ps,axis=0),5,100); sc.append(rmse(y[v],p))
        rows.append(pd.DataFrame({'fold':fi,'dt':idx[v],'y':y[v].values,label:p}))
    print(f'  {label:34s} mean {np.mean(sc):6.3f} worst {max(sc):6.3f} {[round(x,2) for x in sc]}',flush=True)
    if KEEP is not None: KEEP[label]=pd.concat(rows,ignore_index=True)
    return dict(label=label,mean=float(np.mean(sc)),worst=float(max(sc)),folds=[round(x,3) for x in sc])

def HB(seed=0,**kw):
    d=dict(objective='huber',alpha=4.0,n_estimators=2500,learning_rate=0.01,num_leaves=31,
           min_child_samples=25,subsample=0.8,subsample_freq=1,colsample_bytree=1.0,
           reg_lambda=3.,random_state=seed,verbose=-1); d.update(kw)
    return lgb.LGBMRegressor(**d)

R=[];K={}
print('--- refine around cs1.0+slow (6.088) ---',flush=True)
R.append(cv(lambda s: HB(s),'ref cs1.0 n2500 lr.01',KEEP=K))
for ne,lr in ((4000,0.007),(6000,0.005),(1500,0.017)):
    R.append(cv(lambda s,ne=ne,lr=lr: HB(s,n_estimators=ne,learning_rate=lr),f'n{ne} lr{lr}'))
for nl in (15,63,127):
    R.append(cv(lambda s,nl=nl: HB(s,num_leaves=nl),f'nl{nl}'))
for mc in (15,40,60):
    R.append(cv(lambda s,mc=mc: HB(s,min_child_samples=mc),f'min_child{mc}'))
for ss in (0.6,1.0):
    R.append(cv(lambda s,ss=ss: HB(s,subsample=ss),f'subsample{ss}'))
for al in (3.0,6.0):
    R.append(cv(lambda s,al=al: HB(s,alpha=al),f'alpha{al}'))
for rl in (0.5,10.0):
    R.append(cv(lambda s,rl=rl: HB(s,reg_lambda=rl),f'reg_lambda{rl}'))

print('\n--- blend partners on the same feature set ---',flush=True)
cv(lambda s: HB(s,objective='regression',alpha=None) if False else lgb.LGBMRegressor(
     n_estimators=2500,learning_rate=0.01,num_leaves=31,min_child_samples=25,subsample=0.8,
     subsample_freq=1,colsample_bytree=1.0,reg_lambda=3.,random_state=s,verbose=-1),'lgbm_l2 tuned',KEEP=K)
cv(lambda s: cb.CatBoostRegressor(iterations=2500,learning_rate=0.02,depth=6,l2_leaf_reg=6.,
     loss_function='Huber:delta=4',random_seed=s,verbose=0,allow_writing_files=False),'cat_huber',KEEP=K)
cv(lambda s: make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),Ridge(alpha=20.)),'ridge',KEEP=K)
cv(lambda s: make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),
     ElasticNet(alpha=0.05,l1_ratio=0.5,max_iter=8000)),'enet',KEEP=K)
cv(lambda s: make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),
     HuberRegressor(epsilon=1.35,alpha=1e-3,max_iter=800)),'huber_lin',KEEP=K)

J=None
for k_,v_ in K.items():
    J = v_ if J is None else J.merge(v_,on=['fold','dt','y'])
J.to_csv('outputs/oof_exp08.csv',index=False)
MM=[k_ for k_ in K]
print('\n--- nested blend test (fit weights on folds<k) ---',flush=True)
def wf(P,lam):
    A=P[MM].values; w,_=nnls(A,P.y.values); w=w/w.sum() if w.sum()>0 else np.ones(len(MM))/len(MM)
    u=np.ones(len(MM))/len(MM); return (1-lam)*w+lam*u
for lam in (0.0,0.25,0.5,0.75,1.0):
    sc=[rmse(J[J.fold==k].y, J[J.fold==k][MM].values@wf(J[J.fold<k],lam)) for k in sorted(J.fold.unique()) if k>=3]
    print(f'  shrink {lam:.2f}: nested mean {np.mean(sc):.4f}',flush=True)
sc=[rmse(J[J.fold==k].y, J[J.fold==k]['ref cs1.0 n2500 lr.01']) for k in sorted(J.fold.unique()) if k>=3]
print(f'  single best model alone: nested mean {np.mean(sc):.4f}',flush=True)
json.dump(R,open('outputs/exp08_res.json','w'),indent=1,default=float)
print('\n=== TOP ===',flush=True)
for r in sorted(R,key=lambda r:r['mean'])[:10]: print(f"  {r['label']:34s} mean {r['mean']:6.3f} worst {r['worst']:6.3f}",flush=True)
