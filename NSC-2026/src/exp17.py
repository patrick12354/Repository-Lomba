"""E8: re-tune LightGBM on the v6 feature set. The sec 10/12 tuning (huber a=4,
colsample=1.0, n=2500 lr=0.01) was fitted to 68 columns; there are now 82."""
import warnings; warnings.filterwarnings('ignore')
import sys, time, numpy as np, pandas as pd
sys.path.insert(0,'src')
from common import *
from featx import build_v6
from screen import origins
import lightgbm as lgb

g,_,_=load_grid(); is_tr=pd.Series((g.is_test==0).values,index=g.index); y=g[TARGET]
c=clean_exog(g,k=6.0); F=build_v6(c); IDX=g.index; tr=is_tr&y.notna()
P=origins(IDX[tr],n=9,val_days=15,step_days=2)
print('features',F.shape[1],flush=True)

BASE=dict(objective='huber',alpha=4.0,n_estimators=900,learning_rate=0.03,num_leaves=31,
          min_child_samples=25,subsample=0.8,subsample_freq=1,colsample_bytree=1.0,
          reg_lambda=3.0,verbose=-1)
def run(tag,**over):
    kw={**BASE,**over}; rows=[]
    for fi,(vs,ve) in enumerate(P):
        v=tr&(IDX>vs)&(IDX<=ve); t=tr&(IDX<=vs)
        ps=[lgb.LGBMRegressor(random_state=s,**kw).fit(F[t],y[t]).predict(F[v]) for s in (0,1)]
        rows.append(pd.DataFrame(dict(fold=fi,y=y[v].values,p=np.clip(np.mean(ps,0),5,100))))
    L=pd.concat(rows,ignore_index=True); pf=L.groupby('fold').apply(lambda d:rmse(d.y,d.p))
    print(f'{tag:32s} mean {pf.mean():6.3f}  worst {pf.max():6.3f}',flush=True)
    return float(pf.mean())
t0=time.time()
run('reference')
for v in (0.5,0.7,0.85): run(f'colsample={v}',colsample_bytree=v)
for v in (2.0,3.0,6.0,8.0): run(f'huber alpha={v}',alpha=v)
for v in (15,63): run(f'num_leaves={v}',num_leaves=v)
for v in (10,15,40): run(f'min_child={v}',min_child_samples=v)
for v in (0.6,1.0): run(f'subsample={v}',subsample=v)
for v in (1.0,10.0): run(f'reg_lambda={v}',reg_lambda=v)
run('n=2500 lr=.01',n_estimators=2500,learning_rate=0.01)
run('n=1800 lr=.015',n_estimators=1800,learning_rate=0.015)
run('n=4000 lr=.006',n_estimators=4000,learning_rate=0.006)
print(f'\n{time.time()-t0:.0f}s',flush=True)
