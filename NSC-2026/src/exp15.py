"""E6: settle the feature set. exp14 says an 18h window alone beats multi-window sets;
exp13 says ptend helps on top of the full tmin block. Cross those two, plus the
ontario_units drop, on all three fold families."""
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
        d[f'T_min{hrs}']=mn; d[f'T_max{hrs}']=mx; d[f'T_minus_min{hrs}']=T-mn; d[f'T_rng{hrs}']=mx-mn
        d[f'rh_tmin{hrs}']=pd.Series(100*es(mn.values)/es(T.values),index=IDX)
    return pd.DataFrame(d,index=IDX)

def ptend_block():
    p=c['pressure']; pm=p.rolling(49,center=True,min_periods=8).mean()
    return pd.DataFrame({'p_tend24h':pm.diff(48),'p_tend48h':pm.diff(96),
        'p_sd24h':p.rolling(49,center=True,min_periods=8).std(),
        'co2_tend24h':c['co2'].rolling(49,center=True,min_periods=8).mean().diff(48)},index=IDX)
PT=ptend_block()

def mk(wins,ptend,drop=()):
    parts=[F0]+([tmin_block(wins)] if wins else [])+([PT] if ptend else [])
    F=pd.concat(parts,axis=1).replace([np.inf,-np.inf],np.nan)
    return F[[x for x in F.columns if x not in drop]]

def HBT(s=0): return lgb.LGBMRegressor(objective='huber',alpha=4.0,n_estimators=900,
    learning_rate=0.03,num_leaves=31,min_child_samples=25,subsample=0.8,subsample_freq=1,
    colsample_bytree=1.0,reg_lambda=3.,random_state=s,verbose=-1)

FAM={'P':origins(IDX[tr],n=9,val_days=15,step_days=2),
     'Q':origins(IDX[tr],n=6,val_days=15,step_days=3),
     'R':origins(IDX[tr],n=5,val_days=21,step_days=3)}
def run(F,fam,seeds=(0,)):
    rows=[]
    for fi,(vs,ve) in enumerate(FAM[fam]):
        v=tr&(IDX>vs)&(IDX<=ve); t=tr&(IDX<=vs)
        if t.sum()<300 or v.sum()<50: continue
        ps=[]
        for s in seeds:
            m=HBT(s); m.fit(F[t],y[t]); ps.append(m.predict(F[v]))
        rows.append(pd.DataFrame(dict(fold=fi,y=y[v].values,p=np.clip(np.mean(ps,0),5,100))))
    L=pd.concat(rows,ignore_index=True); pf=L.groupby('fold').apply(lambda d:rmse(d.y,d.p))
    return float(pf.mean()),float(pf.max())
def show(tag,F,seeds=(0,)):
    o=[run(F,f,seeds) for f in ('P','Q','R')]
    a=float(np.mean([x[0] for x in o])); wa=float(np.mean([x[1] for x in o]))
    print(f'{tag:34s} {F.shape[1]:4d} | '+' | '.join(f'{m:7.3f} {w:6.3f}' for m,w in o)+
          f' | avg {a:6.3f} wst {wa:6.3f}',flush=True)
    return a

t0=time.time()
print(f'{"variant":34s} {"nf":>4s} | {"P mean":>7s} {"P wst":>6s} | {"Q mean":>7s} {"Q wst":>6s} | {"R mean":>7s} {"R wst":>6s} |',flush=True)
show('base',mk(None,False))
show('tmin[18]',mk([18],False))
show('tmin[18]+ptend',mk([18],True))
show('tmin[18,36]+ptend',mk([18,36],True))
show('tmin[12,18,24]+ptend',mk([12,18,24],True))
show('tmin[18,48]+ptend',mk([18,48],True))
show('tmin[24,48]+ptend',mk([24,48],True))
show('tmin[18]+ptend -ontario',mk([18],True,drop=('ontario_units',)))
show('tmin[18,36]+ptend -ontario',mk([18,36],True,drop=('ontario_units',)))
show('tmin[18]+ptend -ALLdaily',mk([18],True,drop=tuple(DAILY)))
print(f'\n{time.time()-t0:.0f}s',flush=True)
