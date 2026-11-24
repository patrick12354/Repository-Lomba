"""E3: two levers that both stay in RH space (so the L2 loss is never distorted).

(a) Physics-anchored residual. Fit the model to  y - RH_phys  where
    RH_phys = 100*es(Tmin_24h)/es(T) is the parameter-free "Td == daily minimum T"
    estimate, then add the anchor back. Unlike the e/Td reparameterisation this is an
    ADDITIVE shift in RH space, so L2 on the residual is exactly L2 on RH.

(b) Regime-similarity weighting. The test window is cool (T 19-26 C) against a training
    body at 27-33 C. Down-weighting training rows whose air-mass regime is far from the
    target window is covariate-shift correction, not recency weighting -- and unlike a
    time index it is measurable in CV, because every fold's validation window has its own
    regime and the weights are recomputed per fold from exogenous data only.
"""
import warnings; warnings.filterwarnings('ignore')
import sys, time, numpy as np, pandas as pd
sys.path.insert(0,'src')
from common import *
from screen import origins
import lightgbm as lgb

g,_,_=load_grid(); is_tr=pd.Series((g.is_test==0).values,index=g.index); y=g[TARGET]
c=clean_exog(g,k=6.0); F=build_features(c); F=F[feature_set(F,'nosoil')]
IDX=g.index; tr=is_tr&y.notna(); T=c['air_temperature']
folds=origins(IDX[tr],n=9,val_days=15,step_days=2)

Tmin=T.rolling(49,center=True,min_periods=8).min()
RHP=pd.Series(np.clip(100.0*es(Tmin.values)/es(T.values),5,100),index=IDX)
T24=T.rolling(49,center=True,min_periods=8).mean()
print('anchor RH_phys: train RMSE %.3f  corr %.3f  bias %+.2f'%(
    rmse(y[tr],RHP[tr]), np.corrcoef(y[tr],RHP[tr])[0,1], (RHP[tr]-y[tr]).mean()),flush=True)

def HBT(s=0): return lgb.LGBMRegressor(objective='huber',alpha=4.0,n_estimators=900,
    learning_rate=0.03,num_leaves=31,min_child_samples=25,subsample=0.8,subsample_freq=1,
    colsample_bytree=1.0,reg_lambda=3.,random_state=s,verbose=-1)

def run(tag,mode='plain',bw=None,anchor_scale=1.0):
    rows=[]
    for fi,(vs,ve) in enumerate(folds):
        v=tr&(IDX>vs)&(IDX<=ve); t=tr&(IDX<=vs)
        a=anchor_scale*RHP if mode=='anchor' else 0.0
        ytr=y[t]-(a[t] if mode=='anchor' else 0.0)
        sw=None
        if bw is not None:                       # regime weight from the *validation* window's T
            tgt=T24[v].mean()
            sw=np.exp(-((T24[t].values-tgt)/bw)**2)
            sw=np.clip(sw,0.02,None); sw=sw/sw.mean()
        m=HBT(0); m.fit(F[t],ytr,sample_weight=sw)
        p=np.asarray(m.predict(F[v])).ravel()
        if mode=='anchor': p=p+a[v].values
        rows.append(pd.DataFrame(dict(fold=fi,dt=IDX[v],y=y[v].values,p=np.clip(p,5,100))))
    L=pd.concat(rows,ignore_index=True); pf=L.groupby('fold').apply(lambda d:rmse(d.y,d.p))
    L=L.sort_values(['fold','dt']); e=L.p-L.y
    sl=L.assign(e=e).groupby('fold').e.transform(lambda s:s.rolling(48,center=True,min_periods=12).mean())
    print(f'{tag:34s} mean {pf.mean():6.3f} worst {pf.max():6.3f} | slow {np.sqrt((sl**2).mean()):5.2f} '
          f'fast {np.sqrt(((e-sl)**2).mean()):5.2f} | {[round(x,2) for x in pf.values]}',flush=True)
    return float(pf.mean())

t0=time.time()
run('BASE')
run('anchor x1.0','anchor',anchor_scale=1.0)
run('anchor x0.5','anchor',anchor_scale=0.5)
for bw in (3.0,5.0,8.0):
    run(f'regime-weight bw={bw}',bw=bw)
print(f'\n{time.time()-t0:.0f}s',flush=True)
