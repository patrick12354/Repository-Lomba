"""E9: combine the capacity-shrinking knobs from exp17, then verify on families Q and R.
Every single-knob winner in exp17 pointed the same way (fewer leaves, bigger leaves,
less column/row sampling) -- the reverse of sec 10, where colsample=1.0 won on the older
68-column set. Stronger features, so less tree capacity is needed."""
import warnings; warnings.filterwarnings('ignore')
import sys, time, numpy as np, pandas as pd
sys.path.insert(0,'src')
from common import *
from featx import build_v6
from screen import origins
import lightgbm as lgb

g,_,_=load_grid(); is_tr=pd.Series((g.is_test==0).values,index=g.index); y=g[TARGET]
c=clean_exog(g,k=6.0); F=build_v6(c); IDX=g.index; tr=is_tr&y.notna()
FAM={'P':origins(IDX[tr],n=9,val_days=15,step_days=2),
     'Q':origins(IDX[tr],n=6,val_days=15,step_days=3),
     'R':origins(IDX[tr],n=5,val_days=21,step_days=3)}
BASE=dict(objective='huber',alpha=4.0,n_estimators=900,learning_rate=0.03,num_leaves=31,
          min_child_samples=25,subsample=0.8,subsample_freq=1,colsample_bytree=1.0,
          reg_lambda=3.0,verbose=-1)
def run(kw,fam,seeds=(0,1)):
    rows=[]
    for fi,(vs,ve) in enumerate(FAM[fam]):
        v=tr&(IDX>vs)&(IDX<=ve); t=tr&(IDX<=vs)
        if t.sum()<300 or v.sum()<50: continue
        ps=[lgb.LGBMRegressor(random_state=s,**kw).fit(F[t],y[t]).predict(F[v]) for s in seeds]
        rows.append(pd.DataFrame(dict(fold=fi,y=y[v].values,p=np.clip(np.mean(ps,0),5,100))))
    L=pd.concat(rows,ignore_index=True); pf=L.groupby('fold').apply(lambda d:rmse(d.y,d.p))
    return float(pf.mean()),float(pf.max())
def show(tag,fams=('P',),**over):
    kw={**BASE,**over}; o=[run(kw,f) for f in fams]
    print(f'{tag:44s} '+' | '.join(f'{f} {m:6.3f}/{w:6.3f}' for f,(m,w) in zip(fams,o))+
          f' | avg {np.mean([x[0] for x in o]):6.3f}',flush=True)
    return np.mean([x[0] for x in o])
t0=time.time()
print('--- combinations, family P ---',flush=True)
show('reference')
show('nl15',num_leaves=15)
show('nl15+mc40',num_leaves=15,min_child_samples=40)
show('nl15+cs0.5',num_leaves=15,colsample_bytree=0.5)
show('nl15+cs0.7',num_leaves=15,colsample_bytree=0.7)
show('nl15+ss0.6',num_leaves=15,subsample=0.6)
show('nl15+mc40+cs0.7',num_leaves=15,min_child_samples=40,colsample_bytree=0.7)
show('nl15+mc40+cs0.5',num_leaves=15,min_child_samples=40,colsample_bytree=0.5)
show('nl15+mc40+cs0.7+ss0.6',num_leaves=15,min_child_samples=40,colsample_bytree=0.7,subsample=0.6)
show('nl8+mc40+cs0.7',num_leaves=8,min_child_samples=40,colsample_bytree=0.7)
show('nl15+mc40+cs0.7 slow',num_leaves=15,min_child_samples=40,colsample_bytree=0.7,
     n_estimators=2500,learning_rate=0.012)
print(f'\n{time.time()-t0:.0f}s',flush=True)
