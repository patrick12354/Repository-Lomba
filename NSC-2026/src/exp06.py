import warnings; warnings.filterwarnings('ignore')
import sys, json, numpy as np, pandas as pd
sys.path.insert(0,'src')
from common import *
from screen import origins
import lightgbm as lgb

g,_,_=load_grid(); is_tr=pd.Series((g.is_test==0).values,index=g.index); y=g[TARGET]
c=clean_exog(g); F=build_features(c); F=F[feature_set(F,'nosoil')]
folds=origins(g.index[is_tr & y.notna()], n=9, val_days=15, step_days=2)
tr=(is_tr & y.notna()); idx=F.index
print('feats',F.shape[1],flush=True)

def cv(mk, label):
    sc=[]
    for vs,ve in folds:
        v=tr&(idx>vs)&(idx<=ve); t=tr&(idx<=vs)
        m=mk(); m.fit(F[t],y[t]); sc.append(rmse(y[v],np.clip(m.predict(F[v]),5,100)))
    print(f'  {label:44s} mean {np.mean(sc):6.3f}  worst {max(sc):6.3f}  {[round(x,2) for x in sc]}',flush=True)
    return dict(label=label, mean=float(np.mean(sc)), worst=float(max(sc)), folds=[round(x,3) for x in sc])

R=[]
base=dict(n_estimators=700,learning_rate=0.04,num_leaves=31,min_child_samples=25,
          subsample=0.8,subsample_freq=1,colsample_bytree=0.6,reg_lambda=3.,random_state=0,verbose=-1)
print('--- objective / robustness ---',flush=True)
R.append(cv(lambda: lgb.LGBMRegressor(**base),'l2 (reference)'))
for al in (1.0,2.0,4.0,8.0,16.0):
    R.append(cv(lambda al=al: lgb.LGBMRegressor(objective='huber',alpha=al,**base),f'huber alpha={al}'))
R.append(cv(lambda: lgb.LGBMRegressor(objective='fair',**base),'fair'))
R.append(cv(lambda: lgb.LGBMRegressor(objective='regression_l1',**base),'MAE'))

print('--- capacity (huber alpha=4) ---',flush=True)
def hb(**kw):
    d=dict(base); d.update(kw); return lgb.LGBMRegressor(objective='huber',alpha=4.0,**d)
for nl in (4,8,15,31,63):
    R.append(cv(lambda nl=nl: hb(num_leaves=nl),f'huber nl={nl}'))
for mcs in (10,25,50,100):
    R.append(cv(lambda mcs=mcs: hb(min_child_samples=mcs),f'huber min_child={mcs}'))
for cs in (0.3,0.45,0.6,0.85):
    R.append(cv(lambda cs=cs: hb(colsample_bytree=cs),f'huber colsample={cs}'))
for rl in (1.,3.,10.,30.):
    R.append(cv(lambda rl=rl: hb(reg_lambda=rl),f'huber reg_lambda={rl}'))
for ne,lr in ((400,0.06),(700,0.04),(1400,0.02),(2500,0.01)):
    R.append(cv(lambda ne=ne,lr=lr: hb(n_estimators=ne,learning_rate=lr),f'huber n={ne} lr={lr}'))
json.dump(R,open('outputs/exp06_res.json','w'),indent=1,default=float)
print('\n=== TOP 12 ===',flush=True)
for r in sorted(R,key=lambda r:r['mean'])[:12]:
    print(f"  {r['label']:44s} mean {r['mean']:6.3f} worst {r['worst']:6.3f}",flush=True)
