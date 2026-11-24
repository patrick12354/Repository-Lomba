"""Final submission: config E.
  despiked exogenous -> 68 non-soil features -> {tuned huber-LGBM, huber-CatBoost,
  ridge, elastic-net} -> NNLS weights shrunk 25% toward equal -> clip [5,100]."""
import warnings; warnings.filterwarnings('ignore')
import sys, json, numpy as np, pandas as pd
sys.path.insert(0,'src')
from common import *
from screen import origins
import lightgbm as lgb, catboost as cb
from sklearn.linear_model import Ridge, ElasticNet
from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from scipy.optimize import nnls

NAME='v5_final'; SEEDS=(0,1,2); SHRINK=0.25
g,_,_=load_grid()
is_tr=pd.Series((g.is_test==0).values,index=g.index)
is_te=pd.Series((g.is_test==1).values,index=g.index)
y=g[TARGET]
c=clean_exog(g,k=6.0); F=build_features(c); F=F[feature_set(F,'nosoil')]
folds=origins(g.index[is_tr & y.notna()],n=9,val_days=15,step_days=2)
tr=(is_tr & y.notna()); IDX=F.index
print(f'features {F.shape[1]}  train rows {int(tr.sum())}  test rows {int(is_te.sum())}',flush=True)

def HBT(s=0): return lgb.LGBMRegressor(objective='huber',alpha=4.0,n_estimators=2500,
    learning_rate=0.01,num_leaves=31,min_child_samples=25,subsample=0.8,subsample_freq=1,
    colsample_bytree=1.0,reg_lambda=3.,random_state=s,verbose=-1)
def CATH(s=0): return cb.CatBoostRegressor(iterations=1200,learning_rate=0.035,depth=6,
    l2_leaf_reg=6.,loss_function='Huber:delta=4',random_seed=s,verbose=0,allow_writing_files=False)
def RID(s=0): return make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),Ridge(alpha=20.))
def ENE(s=0): return make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),
    ElasticNet(alpha=0.05,l1_ratio=0.5,max_iter=8000))
MODELS=[('hbt',HBT),('cat',CATH),('ridge',RID),('enet',ENE)]
MN=[m for m,_ in MODELS]

print('building OOF for blend weights...',flush=True)
per=[]
for fi,(vs,ve) in enumerate(folds):
    v=tr&(IDX>vs)&(IDX<=ve); t=tr&(IDX<=vs)
    P={}
    for mn,mk in MODELS:
        m=mk(0); m.fit(F[t],y[t]); P[mn]=np.clip(np.asarray(m.predict(F[v])).ravel(),5,100)
    per.append(pd.DataFrame(dict(fold=fi,dt=IDX[v],y=y[v].values,**P)))
O=pd.concat(per,ignore_index=True)
w,_=nnls(O[MN].values,O.y.values); w=w/w.sum() if w.sum()>0 else np.ones(len(MN))/len(MN)
u=np.ones(len(MN))/len(MN); w=(1-SHRINK)*w+SHRINK*u
print('weights:',{m:round(float(x),4) for m,x in zip(MN,w)},flush=True)
pf=O.groupby('fold').apply(lambda d: rmse(d.y, d[MN].values@w))
print(f'CV mean {pf.mean():.4f}  pooled {rmse(O.y,O[MN].values@w):.4f}  worst {pf.max():.4f}',flush=True)
print('  per fold:',[round(x,3) for x in pf.values],flush=True)
O.to_csv(f'outputs/oof_long_{NAME}.csv',index=False)

print('\nrefit on all training data, predict test...',flush=True)
Pt={}
for mn,mk in MODELS:
    ps=[]
    for sd in (SEEDS if mn in ('hbt','cat') else (0,)):
        m=mk(sd); m.fit(F[tr],y[tr]); ps.append(np.asarray(m.predict(F[is_te])).ravel())
    Pt[mn]=np.clip(np.mean(ps,axis=0),5,100)
Pt=pd.DataFrame(Pt,index=IDX[is_te])
pred=np.clip(Pt[MN].values@w,5,100)

te=pd.read_csv(D+'test.csv',parse_dates=['datetime'])
sub=pd.DataFrame({'datetime':te.datetime.dt.strftime('%Y-%m-%d %H:%M:%S'),
                  'air_humidity':pd.Series(pred,index=IDX[is_te]).reindex(te.datetime).values})
ss=pd.read_csv(D+'sample_submission.csv')
assert list(sub.columns)==list(ss.columns) and len(sub)==len(ss)
assert (sub.datetime.values==ss.datetime.values).all() and sub.air_humidity.notna().all()
sub.to_csv(f'outputs/submissions/{NAME}.csv',index=False)
Pt.to_csv(f'outputs/testpreds_{NAME}.csv')
print(f'wrote outputs/submissions/{NAME}.csv  (validated against sample_submission)',flush=True)
print('\npred:',sub.air_humidity.describe().round(2).to_dict())
print('\nagreement with earlier submissions (RMSE between prediction vectors):')
for old in ['v3_clean_zoo','v4_nosoil']:
    o=pd.read_csv(f'outputs/submissions/{old}.csv')
    print(f'  vs {old}: {rmse(sub.air_humidity, o.air_humidity):.3f}')
log_experiment(dict(name=NAME,cv_mean=float(pf.mean()),cv_pooled=rmse(O.y,O[MN].values@w),
    cv_worst=float(pf.max()),folds=[round(x,3) for x in pf.values],
    weights={m:round(float(x),4) for m,x in zip(MN,w)},n_feats=int(F.shape[1]),
    notes='config E: despike k6 + nosoil + huber-tuned lgbm + cat_huber + ridge + enet, shrink .25'),
    OUT+'experiments2.jsonl')
print('\nlogged.')
