"""Build the v6 submission.

Recipe: Hampel despike (w=7,k=6) -> interpolate on the joint train+test grid ->
68 non-soil features + tmin[18,48] air-mass block + pressure/co2 tendency (82 cols) ->
{huber-LGBM(nl15,cs0.7), huber-CatBoost, ridge, elastic-net, ridge-in-vapour-pressure}
-> NNLS weights from the family-P OOF, shrunk 25% toward equal -> clip [5,100].
"""
import warnings; warnings.filterwarnings('ignore')
import sys, pickle, numpy as np, pandas as pd
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

NAME='v6_airmass'; SEEDS=(0,1,2,3,4); SHRINK=0.25
MS=['hbt','cat','ridge','enet','ridge_e']
g,_,_=load_grid()
is_tr=pd.Series((g.is_test==0).values,index=g.index); is_te=pd.Series((g.is_test==1).values,index=g.index)
y=g[TARGET]; c=clean_exog(g,k=6.0); F=build_v6(c); IDX=g.index; tr=is_tr&y.notna()
T=c['air_temperature']; ESt=pd.Series(es(T.values),index=IDX); E=y*ESt/100.0
print(f'features {F.shape[1]}  train {int(tr.sum())}  test {int(is_te.sum())}',flush=True)
print('NaNs in test features:',int(F[is_te].isna().sum().sum()),'/',F[is_te].size,flush=True)

KW=dict(objective='huber',alpha=4.0,n_estimators=900,learning_rate=0.03,num_leaves=15,
        min_child_samples=25,subsample=0.8,subsample_freq=1,colsample_bytree=0.7,
        reg_lambda=3.0,verbose=-1)
def pipe(e): return make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),e)
def predict(name,t,v,seeds):
    if name=='hbt': return np.mean([lgb.LGBMRegressor(random_state=s,**KW).fit(F[t],y[t]).predict(F[v]) for s in seeds],0)
    if name=='cat': return np.mean([cb.CatBoostRegressor(iterations=1200,learning_rate=0.035,depth=6,
        l2_leaf_reg=6.,loss_function='Huber:delta=4',random_seed=s,verbose=0,
        allow_writing_files=False).fit(F[t],y[t]).predict(F[v]) for s in seeds],0)
    if name=='ridge': return pipe(Ridge(alpha=20.)).fit(F[t],y[t]).predict(F[v])
    if name=='enet':  return pipe(ElasticNet(alpha=0.05,l1_ratio=0.5,max_iter=8000)).fit(F[t],y[t]).predict(F[v])
    if name=='ridge_e':
        m=pipe(Ridge(alpha=20.)).fit(F[t],E[t]); return 100.0*m.predict(F[v])/ESt[v].values

# weights from the family-P OOF already computed in final_v6.py
O=pickle.load(open('outputs/v6_oof.pkl','rb'))[('v6','P')]
w,_=nnls(O[MS].values,O.y.values); w=w/w.sum() if w.sum()>0 else np.ones(len(MS))/len(MS)
w=(1-SHRINK)*w+SHRINK*np.ones(len(MS))/len(MS)
print('weights:',{m:round(float(x),4) for m,x in zip(MS,w)},flush=True)
pf=O.groupby('fold').apply(lambda d: rmse(d.y,d[MS].values@w))
print(f'family-P CV (pooled weights): mean {pf.mean():.4f}  worst {pf.max():.4f}  '
      f'per fold {[round(x,3) for x in pf.values]}',flush=True)

print('\nrefit on all training data, predict test...',flush=True)
Pt=pd.DataFrame({m:np.clip(predict(m,tr,is_te,SEEDS if m in ('hbt','cat') else (0,)),5,100) for m in MS},
                index=IDX[is_te])
pred=np.clip(Pt[MS].values@w,5,100)
te=pd.read_csv(D+'test.csv',parse_dates=['datetime'])
sub=pd.DataFrame({'datetime':te.datetime.dt.strftime('%Y-%m-%d %H:%M:%S'),
                  'air_humidity':pd.Series(pred,index=IDX[is_te]).reindex(te.datetime).values})
ss=pd.read_csv(D+'sample_submission.csv')
assert list(sub.columns)==list(ss.columns) and len(sub)==len(ss)==734
assert (sub.datetime.values==ss.datetime.values).all()
assert sub.air_humidity.notna().all() and sub.air_humidity.between(0,100).all()
sub.to_csv(f'outputs/submissions/{NAME}.csv',index=False)
Pt.to_csv(f'outputs/testpreds_{NAME}.csv')
print(f'wrote outputs/submissions/{NAME}.csv  (734 rows, datetimes match sample_submission)',flush=True)
print('\npred:',sub.air_humidity.describe().round(2).to_dict())
print('train y:',y[tr].describe().round(2).to_dict())
print('\nper-model test-prediction spread:'); print(Pt.describe().round(2).to_string())
print('\nRMSE between prediction vectors:')
for old in ['v5_final','v4_nosoil']:
    o=pd.read_csv(f'outputs/submissions/{old}.csv')
    print(f'  vs {old}: {rmse(sub.air_humidity,o.air_humidity):.3f}')
log_experiment(dict(name=NAME,n_feats=int(F.shape[1]),models=MS,
    weights={m:round(float(x),4) for m,x in zip(MS,w)},
    cv_P_mean=float(pf.mean()),cv_P_worst=float(pf.max()),
    notes='v6: v5 + tmin[18,48] airmass block + p/co2 tendency, retuned nl15/cs0.7, +ridge_e'),
    OUT+'experiments2.jsonl')
print('\nlogged.')
