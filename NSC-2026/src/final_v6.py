"""Decisive head-to-head: v5 (shipped, LB 3.95445) vs the two v6 candidates, on three
independent fold families with NESTED blend weights, plus a paired day-level bootstrap.
Then refit on all training data and write the submission.

v5  = 68 non-soil features, huber a=4 / nl31 / colsample=1.0, {hbt,cat,ridge,enet}
v6  = + tmin[18,48] air-mass block + pressure/co2 tendency (82 cols),
      retuned to nl15 / colsample=0.7, {hbt,cat,ridge,enet,ridge_e}
"""
import warnings; warnings.filterwarnings('ignore')
import sys, time, json, numpy as np, pandas as pd
sys.path.insert(0,'src')
from common import *
from featx import build_v6
from screen import origins
import lightgbm as lgb, catboost as cb
from sklearn.linear_model import Ridge, ElasticNet
from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from scipy.optimize import nnls

SEEDS=(0,1,2); SHRINK=0.25
g,_,_=load_grid()
is_tr=pd.Series((g.is_test==0).values,index=g.index); is_te=pd.Series((g.is_test==1).values,index=g.index)
y=g[TARGET]; c=clean_exog(g,k=6.0); IDX=g.index; tr=is_tr&y.notna()
F6=build_v6(c); F5=F6[[x for x in build_features(c)[feature_set(build_features(c),'nosoil')].columns]]
T=c['air_temperature']; ESt=pd.Series(es(T.values),index=IDX); E=y*ESt/100.0
print(f'v5 feats {F5.shape[1]}   v6 feats {F6.shape[1]}   train {int(tr.sum())}  test {int(is_te.sum())}',flush=True)

KW5=dict(objective='huber',alpha=4.0,n_estimators=2500,learning_rate=0.01,num_leaves=31,
         min_child_samples=25,subsample=0.8,subsample_freq=1,colsample_bytree=1.0,reg_lambda=3.0,verbose=-1)
KW6=dict(objective='huber',alpha=4.0,n_estimators=900,learning_rate=0.03,num_leaves=15,
         min_child_samples=25,subsample=0.8,subsample_freq=1,colsample_bytree=0.7,reg_lambda=3.0,verbose=-1)
def pipe(e): return make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),e)

def predict(name,F,KW,t,v):
    if name=='hbt':  return np.mean([lgb.LGBMRegressor(random_state=s,**KW).fit(F[t],y[t]).predict(F[v]) for s in SEEDS],0)
    if name=='cat':  return np.mean([cb.CatBoostRegressor(iterations=1200,learning_rate=0.035,depth=6,
        l2_leaf_reg=6.,loss_function='Huber:delta=4',random_seed=s,verbose=0,
        allow_writing_files=False).fit(F[t],y[t]).predict(F[v]) for s in SEEDS],0)
    if name=='ridge':return pipe(Ridge(alpha=20.)).fit(F[t],y[t]).predict(F[v])
    if name=='enet': return pipe(ElasticNet(alpha=0.05,l1_ratio=0.5,max_iter=8000)).fit(F[t],y[t]).predict(F[v])
    if name=='ridge_e':
        m=pipe(Ridge(alpha=20.)).fit(F[t],E[t]); return 100.0*m.predict(F[v])/ESt[v].values
    raise ValueError(name)

FAM={'P':origins(IDX[tr],n=9,val_days=15,step_days=2),
     'Q':origins(IDX[tr],n=6,val_days=15,step_days=3),
     'R':origins(IDX[tr],n=5,val_days=21,step_days=3)}
CFG={'v5':(F5,KW5,['hbt','cat','ridge','enet']),
     'v6':(F6,KW6,['hbt','cat','ridge','enet','ridge_e'])}

t0=time.time(); OOF={}
for cn,(F,KW,MS) in CFG.items():
    for fam,folds in FAM.items():
        per=[]
        for fi,(vs,ve) in enumerate(folds):
            v=tr&(IDX>vs)&(IDX<=ve); t=tr&(IDX<=vs)
            if t.sum()<300 or v.sum()<50: continue
            d=pd.DataFrame(dict(fold=fi,dt=IDX[v],y=y[v].values))
            for m in MS: d[m]=np.clip(predict(m,F,KW,t,v),5,100)
            per.append(d)
        OOF[(cn,fam)]=pd.concat(per,ignore_index=True)
        print(f'  OOF {cn}/{fam} done ({time.time()-t0:.0f}s)',flush=True)
import pickle; pickle.dump(OOF,open('outputs/v6_oof.pkl','wb'))

def nested_pred(O,models,shrink=SHRINK):
    """Blend fold k using weights fitted only on folds < k. Returns the scored subset."""
    out=[]
    for k in sorted(O.fold.unique()):
        prev=O[O.fold<k]; cur=O[O.fold==k].copy()
        if len(prev)<200: continue
        w,_=nnls(prev[models].values,prev.y.values)
        w=w/w.sum() if w.sum()>0 else np.ones(len(models))/len(models)
        u=np.ones(len(models))/len(models); w=(1-shrink)*w+shrink*u
        cur['p']=cur[models].values@w; out.append(cur)
    return pd.concat(out,ignore_index=True)

CAND={'v5_shipped':('v5',['hbt','cat','ridge','enet']),
      'v6_full'   :('v6',['hbt','cat','ridge','enet','ridge_e']),
      'v6_compact':('v6',['hbt','cat','ridge_e']),
      'v6_single' :('v6',['hbt'])}
print(f'\n{"candidate":14s} '+' '.join(f'{f+" mean":>9s} {f+" wst":>8s}' for f in FAM)+f' {"avg":>7s}',flush=True)
SCORE={}
for nm,(cn,ms) in CAND.items():
    row=[]
    for fam in FAM:
        L=nested_pred(OOF[(cn,fam)],ms); pf=L.groupby('fold').apply(lambda d:rmse(d.y,d.p))
        row.append((float(pf.mean()),float(pf.max()))); SCORE[(nm,fam)]=L
    print(f'{nm:14s} '+' '.join(f'{m:9.3f} {w:8.3f}' for m,w in row)+f' {np.mean([r[0] for r in row]):7.3f}',flush=True)

print('\n########## PAIRED DAY-LEVEL BOOTSTRAP (family P, v6 vs v5) ##########',flush=True)
rng=np.random.default_rng(0)
A=SCORE[('v5_shipped','P')].copy(); A['day']=A.dt.dt.date
for nm in ('v6_full','v6_compact'):
    B=SCORE[(nm,'P')].copy(); B['day']=B.dt.dt.date
    M=A[['fold','dt','y','p','day']].merge(B[['fold','dt','p']],on=['fold','dt'],suffixes=('_a','_b'))
    days=M.day.unique()
    fa=M.groupby('fold').apply(lambda d:rmse(d.y,d.p_a)); fb=M.groupby('fold').apply(lambda d:rmse(d.y,d.p_b))
    dsq=M.assign(sa=(M.p_a-M.y)**2,sb=(M.p_b-M.y)**2).groupby('day')[['sa','sb']].mean()
    boot=[]
    for _ in range(4000):
        s=dsq.loc[rng.choice(days,len(days),replace=True)]
        boot.append(np.sqrt(s.sb.mean())-np.sqrt(s.sa.mean()))
    boot=np.array(boot); lo,hi=np.percentile(boot,[2.5,97.5])
    dwon=float((dsq.sb<dsq.sa).mean())
    print(f'  {nm} vs v5_shipped: pooled {rmse(M.y,M.p_b):.3f} vs {rmse(M.y,M.p_a):.3f} '
          f'(delta {rmse(M.y,M.p_b)-rmse(M.y,M.p_a):+.3f})',flush=True)
    print(f'     folds won {int((fb<fa).sum())}/{len(fa)}  days won {dwon*100:.1f}%  '
          f'bootstrap delta {boot.mean():+.3f}  95% CI [{lo:+.3f}, {hi:+.3f}]  P(better) {(boot<0).mean()*100:.1f}%',flush=True)
print(f'\n{time.time()-t0:.0f}s',flush=True)
pickle.dump(SCORE,open('outputs/v6_scored.pkl','wb'))
