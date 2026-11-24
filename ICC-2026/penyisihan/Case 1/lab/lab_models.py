"""Model runner + cache OOF/test preds."""
import numpy as np, pandas as pd, time, hashlib, json
from pathlib import Path
from sklearn.model_selection import GroupKFold
from sklearn.linear_model import Ridge
import lightgbm as lgb
import lab_common as C

PARAMS=dict(objective="mae",learning_rate=0.02,num_leaves=31,min_child_samples=50,
            subsample=0.8,subsample_freq=1,colsample_bytree=0.7,reg_lambda=1.0,
            n_jobs=-1,verbose=-1)
NFOLD, SEEDS = 5, (0,1,2)
A_BASE=["Cd_2","Cv_2","Ca_4","logdist","loghypo","logE","snr_db"]

def cv_lgb(Xtr, Xte, resid=False, sw=None, seeds=SEEDS, Ftr=None, Fte=None, params=None, nfold=None):
    if sw is None: sw=C.SW
    p0=dict(PARAMS); 
    if params: p0.update(params)
    y, ev = C.y, C.ev
    nf = nfold or NFOLD
    oof=np.zeros(len(y)); pte=np.zeros(len(Xte))
    if resid:
        Xa=Ftr[A_BASE].values.astype(np.float64); Xa_te=Fte[A_BASE].values.astype(np.float64)
    for seed in seeds:
        o=np.zeros(len(y))
        for ti,vi in GroupKFold(n_splits=nf).split(Xtr,y,ev):
            p=dict(p0); p["seed"]=seed
            m=lgb.LGBMRegressor(n_estimators=4000,**p)
            if resid:
                rg=Ridge(alpha=1.0).fit(Xa[ti],y[ti],sample_weight=sw[ti])
                tgt=y-rg.predict(Xa)
                m.fit(Xtr.iloc[ti],tgt[ti],sample_weight=sw[ti],
                      eval_set=[(Xtr.iloc[vi],tgt[vi])],eval_sample_weight=[sw[vi]],
                      callbacks=[lgb.early_stopping(200,verbose=False)])
                o[vi]=m.predict(Xtr.iloc[vi])+rg.predict(Xa[vi])
                pte+=(m.predict(Xte)+rg.predict(Xa_te))/(nf*len(seeds))
            else:
                m.fit(Xtr.iloc[ti],y[ti],sample_weight=sw[ti],
                      eval_set=[(Xtr.iloc[vi],y[vi])],eval_sample_weight=[sw[vi]],
                      callbacks=[lgb.early_stopping(200,verbose=False)])
                o[vi]=m.predict(Xtr.iloc[vi]); pte+=m.predict(Xte)/(nf*len(seeds))
        oof+=o/len(seeds)
    return oof, pte

def cached(name, fn):
    f = C.CACHE/f"{name}.npz"
    if f.exists():
        z=np.load(f); return z["oof"], z["pte"]
    t0=time.time(); oof,pte = fn(); np.savez(f, oof=oof, pte=pte)
    print(f"  [{name}] {time.time()-t0:.0f}s  cv={C.eb_twmae(C.y,oof,C.ev):.4f}")
    return oof,pte
