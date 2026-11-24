"""E12: finish the window sweep -- 96h helped, so test whether it keeps going, and
whether the small co2 order-statistic gain survives on top of the deeper tmin set."""
import warnings; warnings.filterwarnings('ignore')
import sys, time, numpy as np, pandas as pd
sys.path.insert(0,'src')
from common import *
from featx import tmin_block, tend_block
from screen import origins
import lightgbm as lgb
g,_,_=load_grid(); is_tr=pd.Series((g.is_test==0).values,index=g.index); y=g[TARGET]
c=clean_exog(g,k=6.0); F0=build_features(c); F0=F0[feature_set(F0,'nosoil')]
IDX=g.index; tr=is_tr&y.notna(); PT=tend_block(c)
KW=dict(objective='huber',alpha=4.0,n_estimators=900,learning_rate=0.03,num_leaves=15,
        min_child_samples=25,subsample=0.8,subsample_freq=1,colsample_bytree=0.7,
        reg_lambda=3.0,verbose=-1)
FAM={'P':origins(IDX[tr],n=9,val_days=15,step_days=2),
     'Q':origins(IDX[tr],n=6,val_days=15,step_days=3),
     'R':origins(IDX[tr],n=5,val_days=21,step_days=3)}
def run(F,fam,seeds=(0,1,2)):
    rows=[]
    for fi,(vs,ve) in enumerate(FAM[fam]):
        v=tr&(IDX>vs)&(IDX<=ve); t=tr&(IDX<=vs)
        if t.sum()<300 or v.sum()<50: continue
        ps=[lgb.LGBMRegressor(random_state=s,**KW).fit(F[t],y[t]).predict(F[v]) for s in seeds]
        rows.append(pd.DataFrame(dict(fold=fi,y=y[v].values,p=np.clip(np.mean(ps,0),5,100))))
    L=pd.concat(rows,ignore_index=True); pf=L.groupby('fold').apply(lambda d:rmse(d.y,d.p))
    return float(pf.mean()),float(pf.max())
def show(tag,F):
    o=[run(F,f) for f in ('P','Q','R')]
    print(f'{tag:32s} {F.shape[1]:4d} | '+' | '.join(f'{m:6.3f}/{w:6.3f}' for m,w in o)+
          f' | avg {np.mean([x[0] for x in o]):6.3f} wst {np.mean([x[1] for x in o]):6.3f}',flush=True)
def ordstat(col,wins):
    s=c[col]; d={}
    for hrs in wins:
        w=int(hrs*2)+1
        mn=s.rolling(w,center=True,min_periods=6).min(); mx=s.rolling(w,center=True,min_periods=6).max()
        d[f'{col}_min{hrs}']=mn; d[f'{col}_max{hrs}']=mx; d[f'{col}_rng{hrs}']=mx-mn; d[f'{col}_minus_min{hrs}']=s-mn
    return pd.DataFrame(d,index=IDX)
def mk(*p): return pd.concat([F0]+list(p),axis=1).replace([np.inf,-np.inf],np.nan)
t0=time.time()
print(f'{"variant":32s} {"nf":>4s} | {"P":>13s} | {"Q":>13s} | {"R":>13s} |',flush=True)
show('tmin(18,48)+ptend   [v6]', mk(tmin_block(c,(18,48)),PT))
show('tmin(18,48,96)+ptend',     mk(tmin_block(c,(18,48,96)),PT))
show('tmin(18,48,96,144)+ptend', mk(tmin_block(c,(18,48,96,144)),PT))
show('tmin(18,48,72,96)+ptend',  mk(tmin_block(c,(18,48,72,96)),PT))
show('tmin(18,96)+ptend',        mk(tmin_block(c,(18,96)),PT))
show('tmin(18,48,96) no ptend',  mk(tmin_block(c,(18,48,96))))
show('tmin(18,48,96)+ptend+co2', mk(tmin_block(c,(18,48,96)),PT,ordstat('co2',(18,48))))
print(f'\n{time.time()-t0:.0f}s',flush=True)
