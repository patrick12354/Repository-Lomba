"""Adversarial validation: which features let a classifier tell train from test?
Those are the ones whose distribution shifted, i.e. the extrapolation risks."""
import warnings; warnings.filterwarnings('ignore')
import sys, numpy as np, pandas as pd
sys.path.insert(0,'src')
from common import *
import lightgbm as lgb
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import roc_auc_score

g,_,_=load_grid()
is_tr=(g.is_test==0).values; is_te=(g.is_test==1).values
c=clean_exog(g); F=build_features(c)
m=is_tr|is_te
X=F[m]; Y=is_te[m].astype(int)

def auc_of(cols):
    p=np.zeros(len(Y))
    for a,b in StratifiedKFold(5,shuffle=True,random_state=0).split(X[cols],Y):
        mdl=lgb.LGBMRegressor(n_estimators=250,learning_rate=0.05,num_leaves=15,
             min_child_samples=30,colsample_bytree=0.7,random_state=0,verbose=-1)
        mdl.fit(X[cols].iloc[a],Y[a]); p[b]=mdl.predict(X[cols].iloc[b])
    return roc_auc_score(Y,p)

print('all-features AUC (1.0 = perfectly separable):',round(auc_of(list(X.columns)),4),flush=True)
print('\nper-feature AUC (single-feature classifier):',flush=True)
rows=[]
for col in X.columns:
    a=X[col].values; f=np.isfinite(a)
    if f.sum()<100: continue
    try: s=roc_auc_score(Y[f],a[f])
    except Exception: continue
    rows.append((col, max(s,1-s),
                 float(np.nanmedian(a[(Y==0)&f])), float(np.nanmedian(a[(Y==1)&f]))))
R=pd.DataFrame(rows,columns=['feat','auc','train_med','test_med']).sort_values('auc',ascending=False)
print(R.head(40).round(3).to_string(index=False),flush=True)
R.to_csv('outputs/adv_auc.csv',index=False)
print('\nfeatures with AUC>0.90:',int((R.auc>0.90).sum()),' >0.80:',int((R.auc>0.80).sum()),
      ' >0.70:',int((R.auc>0.70).sum()),' total:',len(R))
