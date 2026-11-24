"""E4: dissect the tmin block and re-test it on three independent fold families.

exp11 showed +tmin -0.39 and +tmin+ptend -0.48 on family P alone. ptend LOST on its own
and only helped in combination, which is the signature of noise, so nothing is adopted
here until it replicates on fold families that do not share P's validation windows.
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

def blocks(which):
    """Return dict name -> DataFrame of candidate columns."""
    out={}
    mn24=T.rolling(49,center=True,min_periods=8).min(); mx24=T.rolling(49,center=True,min_periods=8).max()
    mn48=T.rolling(97,center=True,min_periods=8).min(); mx48=T.rolling(97,center=True,min_periods=8).max()
    out['tmin24']  =pd.DataFrame({'T_min24h':mn24,'T_minus_min24h':T-mn24})
    out['tmax24']  =pd.DataFrame({'T_max24h':mx24,'T_rng24h':mx24-mn24})
    out['rhphys24']=pd.DataFrame({'rh_from_tmin24h':100*es(mn24.values)/es(T.values)},index=IDX)
    out['tmin48']  =pd.DataFrame({'T_min48h':mn48,'T_minus_min48h':T-mn48})
    out['tmax48']  =pd.DataFrame({'T_max48h':mx48,'T_rng48h':mx48-mn48})
    out['rhphys48']=pd.DataFrame({'rh_from_tmin48h':100*es(mn48.values)/es(T.values)},index=IDX)
    p=c['pressure']; pm=p.rolling(49,center=True,min_periods=8).mean()
    out['ptend']=pd.DataFrame({'p_tend24h':pm.diff(48),'p_tend48h':pm.diff(96),
                               'p_sd24h':p.rolling(49,center=True,min_periods=8).std(),
                               'co2_tend24h':c['co2'].rolling(49,center=True,min_periods=8).mean().diff(48)})
    return {k:out[k] for k in which}

def mk(which):
    b=blocks(which)
    return pd.concat([F0]+list(b.values()),axis=1).replace([np.inf,-np.inf],np.nan) if b else F0

def HBT(s=0): return lgb.LGBMRegressor(objective='huber',alpha=4.0,n_estimators=900,
    learning_rate=0.03,num_leaves=31,min_child_samples=25,subsample=0.8,subsample_freq=1,
    colsample_bytree=1.0,reg_lambda=3.,random_state=s,verbose=-1)

FAM={'P':origins(IDX[tr],n=9,val_days=15,step_days=2),
     'Q':origins(IDX[tr],n=6,val_days=15,step_days=3),
     'R':origins(IDX[tr],n=5,val_days=21,step_days=3)}

def run(tag,F,fam):
    rows=[]
    for fi,(vs,ve) in enumerate(FAM[fam]):
        v=tr&(IDX>vs)&(IDX<=ve); t=tr&(IDX<=vs)
        if t.sum()<300 or v.sum()<50: continue
        m=HBT(0); m.fit(F[t],y[t]); rows.append(pd.DataFrame(dict(fold=fi,dt=IDX[v],y=y[v].values,p=np.clip(m.predict(F[v]),5,100))))
    L=pd.concat(rows,ignore_index=True); pf=L.groupby('fold').apply(lambda d:rmse(d.y,d.p))
    return float(pf.mean()),float(pf.max())

t0=time.time()
CAND=[('base',[]),
      ('tmin24',['tmin24']),
      ('rhphys24',['rhphys24']),
      ('tmin24+rhphys24',['tmin24','rhphys24']),
      ('tmax24',['tmax24']),
      ('tmin24+tmax24+rhphys24',['tmin24','tmax24','rhphys24']),
      ('ALLtmin(exp11)',['tmin24','tmax24','rhphys24','tmin48','tmax48','rhphys48']),
      ('ALLtmin+ptend',['tmin24','tmax24','rhphys24','tmin48','tmax48','rhphys48','ptend']),
      ('tmin24+rhphys24+ptend',['tmin24','rhphys24','ptend']),
      ('ptend',['ptend'])]
print(f'{"variant":26s} {"nf":>4s} | {"P mean":>7s} {"P wst":>6s} | {"Q mean":>7s} {"Q wst":>6s} | {"R mean":>7s} {"R wst":>6s} | {"avg":>6s}',flush=True)
res={}
for tag,which in CAND:
    F=mk(which); out=[]
    for fam in ('P','Q','R'): out.append(run(tag,F,fam))
    avg=np.mean([o[0] for o in out]); res[tag]=(out,avg)
    print(f'{tag:26s} {F.shape[1]:4d} | '+' | '.join(f'{m:7.3f} {w:6.3f}' for m,w in out)+f' | {avg:6.3f}',flush=True)
print(f'\n{time.time()-t0:.0f}s',flush=True)
