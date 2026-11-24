"""Redo of an_residstruct.py.  The first version let the stage-2 model see the same
timestamps in train and validation, because the 18 folds overlap by 13 of 15 days -- s5's
harness bug in new clothes.  Here: deduplicate to unique timestamps, then split by TIME."""
import numpy as np, pandas as pd, pickle, sys
sys.path.insert(0,'.'); import final_pipeline as fp
import lightgbm as lgb
from sklearn.linear_model import Ridge
from scipy.optimize import nnls
B=fp.MODELS
res=pickle.load(open('outputs/dropblend_oof.pkl','rb'))
g=fp.load_grid(); F=fp.make_features(g); y=g[fp.TARGET]; IDX=g.index
folds=sorted({(k[0],k[1]) for k in res if (k[0],k[1],'base') in res})
def dz(t):
    t=2*np.pi*np.asarray(t)/24; return np.column_stack([np.sin(t),np.cos(t)])
A=[]
for fam,fi in folds:
    d=res[(fam,fi,'base')].copy(); d['y']=y.reindex(d.index).values
    d['tod']=d.index.hour+d.index.minute/60; d['fam']=fam; d['fold']=fi; d['dt']=d.index
    A.append(d.reset_index(drop=True))
A=pd.concat(A,ignore_index=True)
def fit_w(O):
    w,_=nnls(O[B].values,O.y.values); w=w/w.sum() if w.sum()>0 else np.ones(5)/5
    return (1-fp.BLEND_SHRINK)*w+fp.BLEND_SHRINK*np.ones(5)/5
P=[]
for fam,fi in folds:
    tr_=A[~((A.fam==fam)&(A.fold==fi))].copy(); va=A[(A.fam==fam)&(A.fold==fi)]
    w=fit_w(tr_); e,W=fp.tod_blend_weights(tr_,w)
    tr_['pred']=np.clip(fp.apply_tod_blend(tr_[B].values,tr_.tod.values,e,W),5,100)
    b=np.linalg.lstsq(np.c_[np.ones(len(tr_)),dz(tr_.tod.values)],(tr_.pred-tr_.y).values,rcond=None)[0][1:]
    p=np.clip(fp.apply_tod_blend(va[B].values,va.tod.values,e,W),5,100)
    P.append(pd.Series(np.clip(p-0.5*(dz(va.tod.values)@b),5,100),index=va.index))
A['pred']=pd.concat(P).sort_index(); A['dt']=pd.DatetimeIndex(A.dt)
U=A.groupby('dt').agg(pred=('pred','mean'),y=('y','first')).sort_index()
U['r']=U.pred-U.y
X=F.loc[U.index]
print("unique timestamps %d   pooled RMSE %.4f"%(len(U),np.sqrt((U.r**2).mean())))
KW=dict(objective='huber',alpha=2.0,n_estimators=400,learning_rate=0.03,num_leaves=15,
        min_child_samples=40,subsample=0.8,subsample_freq=1,colsample_bytree=0.7,
        reg_lambda=5.0,verbose=-1)
end=U.index.max(); out=[]
for i in range(8):
    cut=end-pd.Timedelta(days=2*i); vs=cut-pd.Timedelta(days=15)
    vm=(U.index>vs)&(U.index<=cut); tm=U.index<=vs
    if tm.sum()<300 or vm.sum()<80: continue
    Xt,rt=X[tm],U.r[tm]; Xv=X[vm]; yv=U.y[vm]; pv=U.pred[vm]
    gp=lgb.LGBMRegressor(random_state=0,**KW).fit(Xt,rt).predict(Xv)
    rd=fp._pipe(Ridge(alpha=50.0)).fit(Xt,rt).predict(Xv)
    rec=dict(fold=i,n=int(vm.sum()),base=fp.rmse(yv,pv))
    for nm,c in (('lgb',gp),('ridge',rd)):
        for s in (0.25,0.5,1.0):
            rec[f'{nm}{s}']=fp.rmse(yv,np.clip(pv-s*c,5,100))
    out.append(rec)
R=pd.DataFrame(out)
print("\nstage-2 residual model, TIME-blocked, no shared timestamps (%d folds):"%len(R))
print("%-12s %10s %8s"%("stage-2","delta","folds"))
for nm in ('lgb','ridge'):
    for s in (0.25,0.5,1.0):
        c=f'{nm}{s}'; d=R[c]-R.base
        print("%-12s %+10.4f %5d/%d"%(f"{nm} x{s}",d.mean(),(d<0).sum(),len(R)))
print("\nbaseline mean %.4f"%R.base.mean())
print(R.round(3).to_string(index=False))
