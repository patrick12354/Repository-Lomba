import warnings; warnings.filterwarnings('ignore')
import sys, numpy as np, pandas as pd
sys.path.insert(0,'src')
from common import *
from runner import *
from sklearn.model_selection import KFold

g,_,_ = load_grid()
c = clean_exog(g); F = build_features(c); T = c['air_temperature']
is_tr = pd.Series((g.is_test==0).values, index=g.index); y = g[TARGET]
m = (is_tr & y.notna()).values
X, Y, idx = F[m], y[m], g.index[m]

import lightgbm as lgb
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
def L(): return lgb.LGBMRegressor(n_estimators=800,learning_rate=0.03,num_leaves=31,
    min_child_samples=25,subsample=0.8,subsample_freq=1,colsample_bytree=0.6,reg_lambda=3.,
    random_state=0,verbose=-1)
def R(): return make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),Ridge(alpha=20.))

print('=== (skipped random kfold) ===',flush=True)
for nm,mk in [('lgbm',L),('ridge',R)]:
    oof=np.full(len(Y),np.nan)
    for a,b in KFold(5,shuffle=True,random_state=0).split(X):
        mdl=mk(); mdl.fit(X.iloc[a],Y.iloc[a]); oof[b]=mdl.predict(X.iloc[b])
    print(f'  {nm:6s} random-kfold RMSE {rmse(Y,oof):.3f}',flush=True)

print('\n=== GENERALISATION GAP: contiguous 15-day blocks, train = everything else ===',flush=True)
# leave-one-block-out (uses future too) -> isolates "unseen time window" from "no future data"
blocks = pd.Series(((idx - idx.min()).days // 15).values, index=range(len(idx)))
for nm,mk in [('lgbm',L),('ridge',R)]:
    oof=np.full(len(Y),np.nan)
    for bl in sorted(blocks.unique()):
        v=(blocks==bl).values
        if v.sum()<50: continue
        mdl=mk(); mdl.fit(X[~v],Y[~v]); oof[v]=mdl.predict(X[v])
    print(f'  {nm:6s} leave-one-15d-block-out RMSE {rmse(Y[np.isfinite(oof)],oof[np.isfinite(oof)]):.3f}',flush=True)

print('\n=== FORWARD-ONLY 15-day blocks (the real setup) ===',flush=True)
folds = make_folds(idx, n_folds=5, val_days=15, step_days=5)
for nm,mk in [('lgbm',L),('ridge',R)]:
    rr=[]
    for (vs,ve) in folds:
        v=(idx>vs)&(idx<=ve); t=(idx<=vs)
        if t.sum()<300: continue
        mdl=mk(); mdl.fit(X[t],Y[t]); rr.append(rmse(Y[v],mdl.predict(X[v])))
    print(f'  {nm:6s} forward folds {[round(x,2) for x in rr]} mean {np.mean(rr):.3f}',flush=True)

print('\n=== fold F2 (Aug 4-19) autopsy: lgbm forward ===',flush=True)
vs,ve = folds[2]
v=(idx>vs)&(idx<=ve); t=(idx<=vs)
mdl=L(); mdl.fit(X[t],Y[t]); p=mdl.predict(X[v])
e=pd.DataFrame({'y':Y[v].values,'p':p,'err':p-Y[v].values},index=idx[v])
print('  window',vs,'->',ve,' n',v.sum(),' RMSE',round(rmse(e.y,e.p),3),' bias',round(e.err.mean(),3))
print('  by day:'); print(e.assign(d=e.index.date).groupby('d').agg(rmse=('err',lambda s: float(np.sqrt((s**2).mean()))),bias=('err','mean'),ytrue=('y','mean')).round(2).to_string())
print('\n  train-period y stats:',round(Y[t].mean(),2),round(Y[t].std(),2),' val-period:',round(Y[v].mean(),2),round(Y[v].std(),2))

print('\n=== feature importance (lgbm, full train) ===',flush=True)
mdl=L(); mdl.fit(X,Y)
imp=pd.Series(mdl.feature_importances_,index=X.columns).sort_values(ascending=False)
print(imp.head(25).to_string())
