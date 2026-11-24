"""Adversarially-weighted CV.  Train a classifier to tell training rows from the 514
PRIVATE-slice rows (features only -- no targets, so this is legitimate), then re-score every
adopted change with CV rows weighted by p/(1-p), i.e. by how private-like they are.

This answers the question ordinary CV cannot: does each change still help in the regime the
private slice actually occupies?"""
import numpy as np, pandas as pd, pickle, sys
sys.path.insert(0,'.'); import final_pipeline as fp
import lightgbm as lgb
from sklearn.model_selection import cross_val_predict, StratifiedKFold
from scipy.optimize import nnls
B=fp.MODELS; S=(0,1,2)
g=fp.load_grid(); F=fp.make_features(g); y=g[fp.TARGET]; IDX=g.index
is_tr=(g.is_test==0).values & y.notna().values; idx=IDX[is_tr]
te=IDX[(g.is_test==1).values]; pri=te[220:]; pub=te[:220]
for name,tgt in (('PRIVATE',pri),('public',pub)):
    X=pd.concat([F.loc[idx],F.loc[tgt]]); lab=np.r_[np.zeros(len(idx)),np.ones(len(tgt))]
    clf=lgb.LGBMClassifier(n_estimators=300,learning_rate=0.05,num_leaves=15,
                           min_child_samples=30,subsample=0.8,subsample_freq=1,
                           colsample_bytree=0.7,verbose=-1,random_state=0)
    p=cross_val_predict(clf,X,lab,cv=StratifiedKFold(5,shuffle=True,random_state=0),method='predict_proba')[:,1]
    from sklearn.metrics import roc_auc_score
    print("%s: adversarial AUC vs train = %.3f"%(name,roc_auc_score(lab,p)))
    if name=='PRIVATE':
        ptr=np.clip(p[:len(idx)],1e-4,1-1e-4)
        w=ptr/(1-ptr); w=np.clip(w,0,np.quantile(w,0.99)); w=w/w.mean()
        W=pd.Series(w,index=idx)
        print("   weight: ESS = %.0f of %d rows (%.0f%%)"%(w.sum()**2/(w**2).sum(),len(w),
              100*w.sum()**2/(w**2).sum()/len(w)))
        clf.fit(X,lab)
        imp=pd.Series(clf.feature_importances_,index=F.columns).sort_values(ascending=False)
        print("   features that most separate train from the private slice:")
        print("   "+", ".join(imp.head(10).index))
np.save('outputs/adv_w_private.npy',W.values)
pd.Series(W.values,index=idx).to_pickle('outputs/adv_w_private.pkl')
print("\nsaved outputs/adv_w_private.pkl")
