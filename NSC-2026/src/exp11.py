"""E2: slow air-mass features aimed at the 55% of MSE that lives in the 24h-smoothed error.

Physical hook: on a moist night the air cools until it reaches its dewpoint and stalls, so
the daily MINIMUM temperature is a dewpoint proxy -- and es(Tmin)/es(T) is then a direct,
parameter-free RH estimate. The current feature set stops at 24h centered means and has
no min/max/range at all. Also adds multi-day (48/72/120h) means, the diurnal temperature
range (clear dry days swing wide, humid cloudy days do not) and pressure tendency.
"""
import warnings; warnings.filterwarnings('ignore')
import sys, time, numpy as np, pandas as pd
sys.path.insert(0,'src')
from common import *
from screen import origins
import lightgbm as lgb
from scipy.optimize import nnls

g,_,_=load_grid(); is_tr=pd.Series((g.is_test==0).values,index=g.index); y=g[TARGET]
c=clean_exog(g,k=6.0); F0=build_features(c); F0=F0[feature_set(F0,'nosoil')]
IDX=g.index; tr=is_tr&y.notna()
folds=origins(IDX[tr],n=9,val_days=15,step_days=2)
T=c['air_temperature']

def add(F,which):
    f=F.copy()
    if 'tmin' in which:
        # centered daily min/max/range of T -- Tmin is the dewpoint proxy
        for w,nm in ((49,'24h'),(97,'48h')):
            mn=T.rolling(w,center=True,min_periods=8).min()
            mx=T.rolling(w,center=True,min_periods=8).max()
            f[f'T_min{nm}']=mn; f[f'T_max{nm}']=mx; f[f'T_rng{nm}']=mx-mn
            f[f'rh_from_tmin{nm}']=100.0*es(mn.values)/es(T.values)   # RH if Td==Tmin
            f[f'T_minus_min{nm}']=T-mn
        f['rh_tmin_x_esratio']=f['rh_from_tmin24h']
    if 'slow' in which:
        for col in ('air_temperature','co2','pressure'):
            s=c[col]
            for w,nm in ((97,'48h'),(145,'72h'),(241,'120h')):
                m=s.rolling(w,center=True,min_periods=12).mean()
                f[f'{col}_c{nm}']=m; f[f'{col}_a{nm}']=s-m
    if 'ptend' in which:
        p=c['pressure']
        f['p_tend24h']=p.rolling(49,center=True,min_periods=8).mean().diff(48)
        f['p_tend48h']=p.rolling(49,center=True,min_periods=8).mean().diff(96)
        f['p_sd24h']=p.rolling(49,center=True,min_periods=8).std()
        f['co2_tend24h']=c['co2'].rolling(49,center=True,min_periods=8).mean().diff(48)
    return f.replace([np.inf,-np.inf],np.nan)

def HBT(s=0): return lgb.LGBMRegressor(objective='huber',alpha=4.0,n_estimators=900,
    learning_rate=0.03,num_leaves=31,min_child_samples=25,subsample=0.8,subsample_freq=1,
    colsample_bytree=1.0,reg_lambda=3.,random_state=s,verbose=-1)

def run(tag,F):
    rows=[]
    for fi,(vs,ve) in enumerate(folds):
        v=tr&(IDX>vs)&(IDX<=ve); t=tr&(IDX<=vs)
        m=HBT(0); m.fit(F[t],y[t]); p=np.clip(m.predict(F[v]),5,100)
        rows.append(pd.DataFrame(dict(fold=fi,dt=IDX[v],y=y[v].values,p=p)))
    L=pd.concat(rows,ignore_index=True); pf=L.groupby('fold').apply(lambda d:rmse(d.y,d.p))
    # slow/fast split of the residual
    L=L.sort_values(['fold','dt']); e=L.p-L.y
    sl=L.assign(e=e).groupby('fold').e.transform(lambda s:s.rolling(48,center=True,min_periods=12).mean())
    print(f'{tag:30s} n={F.shape[1]:3d} mean {pf.mean():6.3f} worst {pf.max():6.3f} '
          f'| slow {np.sqrt((sl**2).mean()):5.2f} fast {np.sqrt(((e-sl)**2).mean()):5.2f} '
          f'| {[round(x,2) for x in pf.values]}',flush=True)
    return float(pf.mean()),L

t0=time.time()
base,_=run('BASE (v5 68 feats)',F0)
for w in (['tmin'],['slow'],['ptend'],['tmin','slow'],['tmin','ptend'],['tmin','slow','ptend']):
    run('+'+'+'.join(w),add(F0,w))
print(f'\n{time.time()-t0:.0f}s')

# sanity: how good is the parameter-free physics estimate on its own?
mn=T.rolling(49,center=True,min_periods=8).min()
phys=100.0*es(mn.values)/es(T.values)
print('\nparameter-free  RH ~ 100*es(Tmin24h)/es(T):  train RMSE %.3f  corr %.3f'%(
    rmse(y[tr],np.clip(phys,5,100)[tr.values]), np.corrcoef(y[tr],phys[tr.values])[0,1]))
