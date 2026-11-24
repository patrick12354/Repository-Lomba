"""E10: blend composition for v6, scored with NESTED weights (fit on folds < k, applied
to fold k) so the weighting itself is never scored in-sample -- the sec 9 protocol.
Includes a ridge fitted in vapour-pressure space: exp10 showed it beats the RH-space
ridge (7.12 vs 7.41) even though trees lose badly there, so it is the one genuinely
decorrelated learner found so far."""
import warnings; warnings.filterwarnings('ignore')
import sys, time, itertools, numpy as np, pandas as pd
sys.path.insert(0,'src')
from common import *
from featx import build_v6
from screen import origins
import lightgbm as lgb, catboost as cb
from sklearn.linear_model import Ridge, ElasticNet
from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from scipy.optimize import nnls

g,_,_=load_grid(); is_tr=pd.Series((g.is_test==0).values,index=g.index); y=g[TARGET]
c=clean_exog(g,k=6.0); F=build_v6(c); IDX=g.index; tr=is_tr&y.notna()
T=c['air_temperature']; ESt=pd.Series(es(T.values),index=IDX); E=y*ESt/100.0
P=origins(IDX[tr],n=9,val_days=15,step_days=2)
print('features',F.shape[1],flush=True)

LGKW=dict(objective='huber',alpha=4.0,n_estimators=900,learning_rate=0.03,num_leaves=15,
          min_child_samples=25,subsample=0.8,subsample_freq=1,colsample_bytree=0.7,
          reg_lambda=3.0,verbose=-1)
def pipe(est): return make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),est)

def fit_predict(name,t,v,seeds=(0,1,2)):
    if name=='hbt':
        ps=[lgb.LGBMRegressor(random_state=s,**LGKW).fit(F[t],y[t]).predict(F[v]) for s in seeds]
        return np.mean(ps,0)
    if name=='lgb_l2':
        kw={**LGKW,'objective':'regression'}
        ps=[lgb.LGBMRegressor(random_state=s,**kw).fit(F[t],y[t]).predict(F[v]) for s in seeds]
        return np.mean(ps,0)
    if name=='cat':
        ps=[cb.CatBoostRegressor(iterations=1200,learning_rate=0.035,depth=6,l2_leaf_reg=6.,
            loss_function='Huber:delta=4',random_seed=s,verbose=0,allow_writing_files=False
            ).fit(F[t],y[t]).predict(F[v]) for s in seeds]
        return np.mean(ps,0)
    if name=='ridge':  return pipe(Ridge(alpha=20.)).fit(F[t],y[t]).predict(F[v])
    if name=='enet':   return pipe(ElasticNet(alpha=0.05,l1_ratio=0.5,max_iter=8000)).fit(F[t],y[t]).predict(F[v])
    if name=='ridge_e':
        m=pipe(Ridge(alpha=20.)).fit(F[t],E[t]); return 100.0*m.predict(F[v])/ESt[v].values
    raise ValueError(name)

ALL=['hbt','cat','ridge','enet','ridge_e','lgb_l2']
t0=time.time(); per=[]
for fi,(vs,ve) in enumerate(P):
    v=tr&(IDX>vs)&(IDX<=ve); t=tr&(IDX<=vs)
    d=pd.DataFrame(dict(fold=fi,dt=IDX[v],y=y[v].values))
    for m in ALL: d[m]=np.clip(fit_predict(m,t,v),5,100)
    per.append(d); print(f'  fold {fi} done ({time.time()-t0:.0f}s)',flush=True)
O=pd.concat(per,ignore_index=True); O.to_csv('outputs/oof_v6_models.csv',index=False)

print('\nper-model CV mean:',{m:round(float(O.groupby("fold").apply(lambda d:rmse(d.y,d[m])).mean()),3) for m in ALL},flush=True)
print('\ncorrelation of residuals:'); R=O[ALL].sub(O.y,axis=0); print(R.corr().round(3).to_string(),flush=True)

def nested(models,shrink):
    """Fit NNLS on folds < k, score fold k. Never scores its own weights."""
    sc=[]
    for k in sorted(O.fold.unique()):
        prev=O[O.fold<k]; cur=O[O.fold==k]
        if len(prev)<200: continue
        w,_=nnls(prev[models].values,prev.y.values)
        w=w/w.sum() if w.sum()>0 else np.ones(len(models))/len(models)
        u=np.ones(len(models))/len(models); w=(1-shrink)*w+shrink*u
        sc.append(rmse(cur.y,cur[models].values@w))
    return float(np.mean(sc)),float(np.max(sc))

print(f'\n{"model set":38s} {"shrink":>6s} {"nested":>7s} {"worst":>7s}',flush=True)
SETS=[['hbt'],['hbt','cat'],['hbt','cat','ridge','enet'],['hbt','cat','ridge','enet','ridge_e'],
      ['hbt','cat','ridge_e'],['hbt','cat','ridge','enet','ridge_e','lgb_l2'],
      ['hbt','cat','lgb_l2'],['hbt','ridge_e']]
best=None
for ms in SETS:
    for sh in (0.0,0.25,0.5):
        m,w=nested(ms,sh)
        print(f'{"+".join(ms):38s} {sh:6.2f} {m:7.3f} {w:7.3f}',flush=True)
        if best is None or m<best[0]: best=(m,ms,sh)
        if len(ms)==1: break
print('\nbest:',best,flush=True)
print(f'{time.time()-t0:.0f}s',flush=True)
