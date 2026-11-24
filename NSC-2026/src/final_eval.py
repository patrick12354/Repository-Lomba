"""Decisive head-to-head: reproduce a proxy of the LB-4.755 baseline, then add one
change at a time. Two independent fold families + paired bootstrap over days."""
import warnings; warnings.filterwarnings('ignore')
import sys, json, numpy as np, pandas as pd, pickle
sys.path.insert(0,'src')
from common import *
import lightgbm as lgb, catboost as cb
from sklearn.linear_model import Ridge, ElasticNet
from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from scipy.optimize import nnls

g,_,_=load_grid(); is_tr=pd.Series((g.is_test==0).values,index=g.index); y=g[TARGET]

def interp_only(g):
    c=g.copy()
    for col in FAST+SOIL+DAILY: c[col]=c[col].interpolate('time',limit_direction='both')
    for col in CUMUL:
        s=c[col].interpolate('time',limit_direction='both'); c[col]=s
        c[col+'_rate']=s.diff().clip(lower=0).rolling(48,min_periods=1).sum()
    return c

C_RAW=interp_only(g); C_CLN=clean_exog(g)
F_RAW=build_features(C_RAW); F_CLN=build_features(C_CLN)
F_RAW_NS=F_RAW[feature_set(F_RAW,'nosoil')]; F_CLN_NS=F_CLN[feature_set(F_CLN,'nosoil')]

def L2(s=0):  return lgb.LGBMRegressor(n_estimators=700,learning_rate=0.04,num_leaves=31,
    min_child_samples=25,subsample=0.8,subsample_freq=1,colsample_bytree=0.6,reg_lambda=3.,
    random_state=s,verbose=-1)
def HBT(s=0): return lgb.LGBMRegressor(objective='huber',alpha=4.0,n_estimators=2500,
    learning_rate=0.01,num_leaves=31,min_child_samples=25,subsample=0.8,subsample_freq=1,
    colsample_bytree=1.0,reg_lambda=3.,random_state=s,verbose=-1)
def CATH(s=0): return cb.CatBoostRegressor(iterations=1200,learning_rate=0.035,depth=6,
    l2_leaf_reg=6.,loss_function='Huber:delta=4',random_seed=s,verbose=0,allow_writing_files=False)
def RID(s=0): return make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),Ridge(alpha=20.))
def ENE(s=0): return make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),
    ElasticNet(alpha=0.05,l1_ratio=0.5,max_iter=8000))

CONFIGS={
 'A_baseline_proxy': dict(F=F_RAW,    models=[('lgbm',L2),('cat',CATH),('ridge',RID),('enet',ENE)], shrink=0.0),
 'B_clean'         : dict(F=F_CLN,    models=[('lgbm',L2),('cat',CATH),('ridge',RID),('enet',ENE)], shrink=0.0),
 'C_clean_nosoil'  : dict(F=F_CLN_NS, models=[('lgbm',L2),('cat',CATH),('ridge',RID),('enet',ENE)], shrink=0.0),
 'D_tuned_single'  : dict(F=F_CLN_NS, models=[('hbt',HBT)],                                        shrink=0.0),
 'E_final_blend'   : dict(F=F_CLN_NS, models=[('hbt',HBT),('cat',CATH),('ridge',RID),('enet',ENE)], shrink=0.25),
}

def fold_family(idx,n,val_days,step_days,min_train_days=30):
    d0,end,out=idx.min(),idx.max(),[]
    for i in range(n):
        cut=end-pd.Timedelta(days=step_days*i); vs=cut-pd.Timedelta(days=val_days)
        if (vs-d0).days<min_train_days: break
        out.append((vs,cut))
    return out[::-1]

tr=(is_tr & y.notna()); IDX=g.index
FAMS={'P (9x15d step2)': fold_family(IDX[tr],9,15,2),
      'Q (6x15d step3, deeper)': fold_family(IDX[tr],6,15,3,min_train_days=36),
      'R (5x21d step3, stress)': fold_family(IDX[tr],5,21,3,min_train_days=28)}

ALL={}
for fam,folds in FAMS.items():
    print(f'\n########## FOLD FAMILY {fam}: {[(str(a)[:10],str(b)[:10]) for a,b in folds]}',flush=True)
    rows=[]
    for cname,cfg in CONFIGS.items():
        F=cfg['F']; per=[]
        for fi,(vs,ve) in enumerate(folds):
            v=tr&(IDX>vs)&(IDX<=ve); t=tr&(IDX<=vs)
            P={}
            for mn,mk in cfg['models']:
                m=mk(0); m.fit(F[t],y[t]); P[mn]=np.clip(np.asarray(m.predict(F[v])).ravel(),5,100)
            per.append(pd.DataFrame(dict(fold=fi,dt=IDX[v],y=y[v].values,**P)))
        D=pd.concat(per,ignore_index=True)
        mn_list=[m for m,_ in cfg['models']]
        if len(mn_list)==1:
            D['pred']=D[mn_list[0]]
        else:   # nested weights: fit on earlier folds only
            preds=[]
            for k in sorted(D.fold.unique()):
                past=D[D.fold<k]; cur=D[D.fold==k]
                if len(past)<200: w=np.ones(len(mn_list))/len(mn_list)
                else:
                    w,_=nnls(past[mn_list].values,past.y.values)
                    w=w/w.sum() if w.sum()>0 else np.ones(len(mn_list))/len(mn_list)
                    u=np.ones(len(mn_list))/len(mn_list); lam=cfg['shrink']; w=(1-lam)*w+lam*u
                preds.append(pd.Series(cur[mn_list].values@w,index=cur.index))
            D['pred']=pd.concat(preds).sort_index()
        D['se']=(D.pred-D.y)**2
        pf=D.groupby('fold').apply(lambda d: rmse(d.y,d.pred))
        rows.append((cname,D,pf))
        print(f'  {cname:18s} mean {pf.mean():6.3f} pooled {rmse(D.y,D.pred):6.3f} worst {pf.max():6.3f} | {[round(x,2) for x in pf.values]}',flush=True)
    ALL[fam]=rows
pickle.dump(ALL,open('outputs/final_eval.pkl','wb'))

print('\n\n################ PAIRED EVIDENCE (family P) ################',flush=True)
rows=ALL['P (9x15d step2)']; name2D={n:D for n,D,_ in rows}
A=name2D['A_baseline_proxy']; E=name2D['E_final_blend']; Dd=name2D['D_tuned_single']
for lbl,X in [('E_final_blend',E),('D_tuned_single',Dd),('C_clean_nosoil',name2D['C_clean_nosoil']),
              ('B_clean',name2D['B_clean'])]:
    m=A[['fold','dt','y']].merge(X[['fold','dt','se']].rename(columns={'se':'se_x'}),on=['fold','dt'])
    m=m.merge(A[['fold','dt','se']].rename(columns={'se':'se_a'}),on=['fold','dt'])
    m['day']=m.dt.dt.date
    dd=m.groupby(['fold','day']).agg(se_a=('se_a','mean'),se_x=('se_x','mean')).reset_index()
    win=(dd.se_x<dd.se_a).mean()
    pf_a=m.groupby('fold').se_a.mean()**.5; pf_x=m.groupby('fold').se_x.mean()**.5
    rng=np.random.default_rng(0); diffs=[]
    keys=dd.index.values
    for _ in range(4000):
        s=rng.choice(keys,len(keys),replace=True)
        diffs.append(np.sqrt(dd.se_x.values[s].mean())-np.sqrt(dd.se_a.values[s].mean()))
    diffs=np.array(diffs)
    print(f'\n  {lbl} vs A_baseline_proxy')
    print(f'    pooled RMSE {np.sqrt(m.se_x.mean()):.3f} vs {np.sqrt(m.se_a.mean()):.3f}  '
          f'(delta {np.sqrt(m.se_x.mean())-np.sqrt(m.se_a.mean()):+.3f})')
    print(f'    folds won  {int((pf_x<pf_a).sum())}/{len(pf_a)}   days won {win*100:.1f}%')
    print(f'    bootstrap over days: delta {diffs.mean():+.3f}  95% CI [{np.percentile(diffs,2.5):+.3f}, {np.percentile(diffs,97.5):+.3f}]  P(better) {(diffs<0).mean()*100:.1f}%')
