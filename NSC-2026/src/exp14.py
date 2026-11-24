"""E5: window-length sweep for the tmin block, plus an audit of the DAILY column block.

The 24h window was a guess. And the DAILY aggregates (ontario_units adv-AUC 0.83,
standard_day_degree, gdd-like accumulators) are the last block that was never pruned the
way the soil probes were in sec 8 -- test whether they are carrying their weight.
"""
import warnings; warnings.filterwarnings('ignore')
import sys, time, numpy as np, pandas as pd
sys.path.insert(0,'src')
from common import *
from screen import origins
import lightgbm as lgb

g,_,_=load_grid(); is_tr=pd.Series((g.is_test==0).values,index=g.index); y=g[TARGET]
c=clean_exog(g,k=6.0); F0=build_features(c); F0=F0[feature_set(F0,'nosoil')]
IDX=g.index; tr=is_tr&y.notna(); T=c['air_temperature']

def tmin_block(wins):
    d={}
    for hrs in wins:
        w=int(hrs*2)+1
        mn=T.rolling(w,center=True,min_periods=6).min(); mx=T.rolling(w,center=True,min_periods=6).max()
        d[f'T_min{hrs}']=mn; d[f'T_minus_min{hrs}']=T-mn; d[f'T_rng{hrs}']=mx-mn
        d[f'rh_tmin{hrs}']=pd.Series(100*es(mn.values)/es(T.values),index=IDX)
    return pd.DataFrame(d,index=IDX)

def HBT(s=0): return lgb.LGBMRegressor(objective='huber',alpha=4.0,n_estimators=900,
    learning_rate=0.03,num_leaves=31,min_child_samples=25,subsample=0.8,subsample_freq=1,
    colsample_bytree=1.0,reg_lambda=3.,random_state=s,verbose=-1)

FAM={'P':origins(IDX[tr],n=9,val_days=15,step_days=2),
     'Q':origins(IDX[tr],n=6,val_days=15,step_days=3),
     'R':origins(IDX[tr],n=5,val_days=21,step_days=3)}
def run(F,fam):
    rows=[]
    for fi,(vs,ve) in enumerate(FAM[fam]):
        v=tr&(IDX>vs)&(IDX<=ve); t=tr&(IDX<=vs)
        if t.sum()<300 or v.sum()<50: continue
        m=HBT(0); m.fit(F[t],y[t]); rows.append(pd.DataFrame(dict(fold=fi,y=y[v].values,p=np.clip(m.predict(F[v]),5,100))))
    L=pd.concat(rows,ignore_index=True); pf=L.groupby('fold').apply(lambda d:rmse(d.y,d.p))
    return float(pf.mean()),float(pf.max())

def show(tag,F):
    o=[run(F,f) for f in ('P','Q','R')]
    print(f'{tag:30s} {F.shape[1]:4d} | '+' | '.join(f'{m:7.3f} {w:6.3f}' for m,w in o)+
          f' | {np.mean([x[0] for x in o]):6.3f}',flush=True)
    return np.mean([x[0] for x in o])

t0=time.time()
print(f'{"variant":30s} {"nf":>4s} | {"P mean":>7s} {"P wst":>6s} | {"Q mean":>7s} {"Q wst":>6s} | {"R mean":>7s} {"R wst":>6s} | {"avg":>6s}',flush=True)
print('--- window sweep for the tmin block ---',flush=True)
show('base',F0)
for wins in ([12],[18],[24],[36],[48],[12,24],[24,48],[12,24,48],[6,12,24,48]):
    show('tmin '+str(wins),pd.concat([F0,tmin_block(wins)],axis=1).replace([np.inf,-np.inf],np.nan))

print('--- DAILY block audit (on top of the best tmin set so far: [12,24,48]) ---',flush=True)
B=pd.concat([F0,tmin_block([12,24,48])],axis=1).replace([np.inf,-np.inf],np.nan)
show('B = base+tmin[12,24,48]',B)
for drop,nm in ((['ontario_units'],'-ontario_units'),
                (['standard_day_degree'],'-standard_day_degree'),
                (['daily_max_reduction'],'-daily_max_reduction'),
                (DAILY,'-ALL daily'),
                ([c_ for c_ in DAILY if c_!='daily_mean_temperature'],'-daily except mean_temp')):
    keep=[x for x in B.columns if x not in drop]
    show(nm,B[keep])
print(f'\n{time.time()-t0:.0f}s',flush=True)
