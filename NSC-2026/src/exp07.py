import warnings; warnings.filterwarnings('ignore')
import sys, json, numpy as np, pandas as pd
sys.path.insert(0,'src')
from common import *
from screen import origins
import lightgbm as lgb
from sklearn.neural_network import MLPRegressor
from sklearn.neighbors import KNeighborsRegressor
from sklearn.kernel_ridge import KernelRidge
from sklearn.cross_decomposition import PLSRegression
from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, QuantileTransformer

g,_,_=load_grid(); is_tr=pd.Series((g.is_test==0).values,index=g.index); y=g[TARGET]
c=clean_exog(g); F=build_features(c); F=F[feature_set(F,'nosoil')]
folds=origins(g.index[is_tr & y.notna()], n=9, val_days=15, step_days=2)
tr=(is_tr & y.notna()); idx=F.index

def cv(mk,label,seeds=(0,),keep=None):
    sc=[]; store={}
    for fi,(vs,ve) in enumerate(folds):
        v=tr&(idx>vs)&(idx<=ve); t=tr&(idx<=vs)
        ps=[]
        for sd in seeds:
            m=mk(sd); m.fit(F[t],y[t]); ps.append(np.asarray(m.predict(F[v])).ravel())
        p=np.clip(np.mean(ps,axis=0),5,100)
        sc.append(rmse(y[v],p))
        if keep is not None: store[fi]=pd.Series(p,index=idx[v])
    print(f'  {label:40s} mean {np.mean(sc):6.3f} worst {max(sc):6.3f} {[round(x,2) for x in sc]}',flush=True)
    if keep is not None: keep[label]=store
    return dict(label=label,mean=float(np.mean(sc)),worst=float(max(sc)),folds=[round(x,3) for x in sc])

def HB(seed=0,**kw):
    d=dict(objective='huber',alpha=4.0,n_estimators=700,learning_rate=0.04,num_leaves=31,
           min_child_samples=25,subsample=0.8,subsample_freq=1,colsample_bytree=0.6,
           reg_lambda=3.,random_state=seed,verbose=-1); d.update(kw)
    return lgb.LGBMRegressor(**d)

R=[]; KEEP={}
print('--- combining the individual wins ---',flush=True)
R.append(cv(lambda s: HB(s),'ref alpha4',keep=KEEP))
R.append(cv(lambda s: HB(s,colsample_bytree=0.85),'cs.85',keep=KEEP))
R.append(cv(lambda s: HB(s,colsample_bytree=0.85,n_estimators=2500,learning_rate=0.01),'cs.85+slow',keep=KEEP))
R.append(cv(lambda s: HB(s,colsample_bytree=0.85,n_estimators=2500,learning_rate=0.01,num_leaves=15),'cs.85+slow+nl15',keep=KEEP))
R.append(cv(lambda s: HB(s,colsample_bytree=0.85,n_estimators=1400,learning_rate=0.02,num_leaves=15),'cs.85+med+nl15',keep=KEEP))
R.append(cv(lambda s: HB(s,colsample_bytree=1.0,n_estimators=2500,learning_rate=0.01),'cs1.0+slow',keep=KEEP))
R.append(cv(lambda s: HB(s,alpha=8.0,colsample_bytree=0.85,n_estimators=2500,learning_rate=0.01),'a8+cs.85+slow',keep=KEEP))
R.append(cv(lambda s: HB(s,colsample_bytree=0.85,n_estimators=2500,learning_rate=0.01,subsample=1.0),'cs.85+slow+nosub',keep=KEEP))
print('--- seed averaging on the best-so-far ---',flush=True)
R.append(cv(lambda s: HB(s,colsample_bytree=0.85,n_estimators=2500,learning_rate=0.01),'cs.85+slow x5seeds',seeds=(0,1,2,3,4),keep=KEEP))

print('--- diverse learners (for blend diversity) ---',flush=True)
PRE=lambda: [SimpleImputer(strategy='median'),StandardScaler()]
R.append(cv(lambda s: make_pipeline(*PRE(),MLPRegressor(hidden_layer_sizes=(128,64),alpha=1.0,
        max_iter=1200,early_stopping=True,random_state=s)),'MLP 128-64',seeds=(0,1,2),keep=KEEP))
R.append(cv(lambda s: make_pipeline(*PRE(),KNeighborsRegressor(n_neighbors=25,weights='distance')),'KNN25',keep=KEEP))
R.append(cv(lambda s: make_pipeline(*PRE(),KNeighborsRegressor(n_neighbors=60,weights='distance')),'KNN60',keep=KEEP))
R.append(cv(lambda s: make_pipeline(SimpleImputer(strategy='median'),
        QuantileTransformer(output_distribution='normal',n_quantiles=500,random_state=0),
        KernelRidge(alpha=1.0,kernel='rbf',gamma=0.01)),'KernelRidge rbf',keep=KEEP))
R.append(cv(lambda s: make_pipeline(*PRE(),PLSRegression(n_components=12)),'PLS12',keep=KEEP))

json.dump(R,open('outputs/exp07_res.json','w'),indent=1,default=float)
import pickle; pickle.dump(KEEP,open('outputs/exp07_preds.pkl','wb'))
print('\n=== RANKING ===',flush=True)
for r in sorted(R,key=lambda r:r['mean']): print(f"  {r['label']:40s} mean {r['mean']:6.3f} worst {r['worst']:6.3f}",flush=True)
