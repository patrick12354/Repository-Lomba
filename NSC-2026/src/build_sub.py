"""Score the full model zoo on the 9 rolling origins, then refit on all of train
and write a submission. Usage: build_sub.py <name> [--models a,b,c] [--seeds N]"""
import warnings; warnings.filterwarnings('ignore')
import sys, json, argparse, numpy as np, pandas as pd, pickle, os
sys.path.insert(0,'src')
from common import *
from screen import MK, origins, raw_oof, evaluate

ap=argparse.ArgumentParser()
ap.add_argument('name')
ap.add_argument('--models', default='lgbm,lgbm_hub,lgbm_sh,xgb,cat,et,ridge,enet')
ap.add_argument('--seeds', type=int, default=3)
ap.add_argument('--k', type=float, default=6.0)
ap.add_argument('--notes', default='')
ap.add_argument('--fset', default='full')
a=ap.parse_args()
MODELS=tuple(a.models.split(','))
SEEDS=tuple(range(a.seeds))

g,_,_=load_grid()
is_tr=pd.Series((g.is_test==0).values,index=g.index)
is_te=pd.Series((g.is_test==1).values,index=g.index)
y=g[TARGET]
c=clean_exog(g,k=a.k); F=build_features(c); T=c['air_temperature']
F=F[feature_set(F,a.fset)]
folds=origins(g.index[is_tr & y.notna()], n=9, val_days=15, step_days=2)

print(f'[{a.name}] models={MODELS} seeds={a.seeds} feats={F.shape[1]}',flush=True)
L,M=raw_oof(F,y,T,is_tr,target='rh',models=MODELS,folds=folds,seeds=(0,))
res=evaluate(a.name,L,M,smooth=0)
L.to_csv(f'outputs/oof_long_{a.name}.csv',index=False)

w=np.array([res['w'][m] for m in M])
print('\nrefit on full train + predict test...',flush=True)
tm=(is_tr & y.notna())
P={}
for m in M:
    ps=[]
    for sd in SEEDS:
        mdl=MK(sd)[m]; mdl.fit(F[tm],y[tm]); ps.append(mdl.predict(F[is_te]))
    P[m]=np.clip(np.mean(ps,axis=0),5,100)
Pt=pd.DataFrame(P,index=g.index[is_te])
pred=np.clip(Pt[list(M)].values @ w, 5, 100)

te=pd.read_csv(D+'test.csv',parse_dates=['datetime'])
sub=pd.DataFrame({'datetime':te.datetime})
sub['air_humidity']=pd.Series(pred,index=g.index[is_te]).reindex(te.datetime).values
assert sub.air_humidity.notna().all() and len(sub)==734
os.makedirs('outputs/submissions',exist_ok=True)
sub['datetime']=sub.datetime.dt.strftime('%Y-%m-%d %H:%M:%S')
sub.to_csv(f'outputs/submissions/{a.name}.csv',index=False)
Pt.to_csv(f'outputs/testpreds_{a.name}.csv')

print(f'\nwrote outputs/submissions/{a.name}.csv')
print('pred describe:'); print(sub.air_humidity.describe().round(2).to_string())
print('train  describe:'); print(y[tm].describe().round(2).to_string())
print('\npred daily mean:'); 
s=pd.Series(pred,index=g.index[is_te]); print(s.resample('D').mean().round(2).to_string())
rec=dict(name=a.name, cv_mean=res['mean'], cv_med=res['med'], cv_worst=res['worst'],
         folds=res['folds'], per_model=res['per_model'], weights=res['w'],
         models=list(M), seeds=a.seeds, despike_k=a.k, n_feats=int(F.shape[1]), fset=a.fset,
         notes=a.notes, pred_mean=float(sub.air_humidity.mean()), pred_std=float(sub.air_humidity.std()))
log_experiment(rec, OUT+'experiments2.jsonl')
print('\nlogged.')
