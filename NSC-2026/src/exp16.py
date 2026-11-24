"""E7: seed-stability. exp15's top variants sit within 0.11 of each other on single seeds,
and ontario_units flipped sign between exp14 and exp15 -- both are inside the seed lottery.
Re-score the finalists with 3 seeds per fold so the ranking means something."""
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
SEEDS=(0,1,2)
def run(F,fam):
    rows=[]
    for fi,(vs,ve) in enumerate(FAM[fam]):
        v=tr&(IDX>vs)&(IDX<=ve); t=tr&(IDX<=vs)
        if t.sum()<300 or v.sum()<50: continue
        ps=[]
        for s in SEEDS:
            m=HBT(s); m.fit(F[t],y[t]); ps.append(m.predict(F[v]))
        rows.append(pd.DataFrame(dict(fold=fi,y=y[v].values,p=np.clip(np.mean(ps,0),5,100))))
    L=pd.concat(rows,ignore_index=True); pf=L.groupby('fold').apply(lambda d:rmse(d.y,d.p))
    return float(pf.mean()),float(pf.max()),L
CAND=[('base (v5)',mk(None,False)),
      ('tmin[18]',mk([18],False)),
      ('tmin[18,48]',mk([18,48],False)),
      ('tmin[18,48]+ptend',mk([18,48],True)),
      ('tmin[24,48]+ptend',mk([24,48],True)),
      ('tmin[18,36]+ptend',mk([18,36],True)),
      ('tmin[18,24,48]+ptend',mk([18,24,48],True))]
t0=time.time(); store={}
print(f'{"variant":24s} {"nf":>4s} | {"P":>7s} {"Pw":>6s} | {"Q":>7s} {"Qw":>6s} | {"R":>7s} {"Rw":>6s} | {"avg":>6s} {"avgW":>6s}',flush=True)
for tag,F in CAND:
    o=[run(F,f) for f in ('P','Q','R')]
    store[tag]=o[0][2]
    a=np.mean([x[0] for x in o]); w=np.mean([x[1] for x in o])
    print(f'{tag:24s} {F.shape[1]:4d} | '+' | '.join(f'{m:7.3f} {ww:6.3f}' for m,ww,_ in o)+f' | {a:6.3f} {w:6.3f}',flush=True)
import pickle; pickle.dump(store,open('outputs/exp16_P.pkl','wb'))
print(f'\n{time.time()-t0:.0f}s',flush=True)
