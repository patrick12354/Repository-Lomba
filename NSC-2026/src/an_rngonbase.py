"""The wide-range correction was validated on the drop85 arm.  v15 would ship it on the BASE
feature set (v12), so re-run the nested test there -- and re-run the day-level pricing at the
cut the pipeline actually uses."""
import numpy as np, pandas as pd, pickle, sys
sys.path.insert(0,'.'); import final_pipeline as fp
from scipy.optimize import nnls
B=fp.MODELS
res=pickle.load(open('outputs/dropblend_oof.pkl','rb'))
g=fp.load_grid(); F=fp.make_features(g); y=g[fp.TARGET]; IDX=g.index; te=IDX[(g.is_test==1).values]
is_tr=(g.is_test==0).values & y.notna().values
folds=sorted({(k[0],k[1]) for k in res if (k[0],k[1],'base') in res})
CUT=float(np.quantile(F.loc[IDX[is_tr],'T_rng48'].values,5/6))
print("pipeline cut (5/6 quantile of training T_rng48) = %.2f C"%CUT)
def dz(t):
    t=2*np.pi*np.asarray(t)/24; return np.column_stack([np.sin(t),np.cos(t)])
def build(arm):
    A=[]
    for fam,fi in folds:
        d=res[(fam,fi,arm)].copy(); d['y']=y.reindex(d.index).values
        d['tod']=d.index.hour+d.index.minute/60; d['fam']=fam; d['fold']=fi; d['dt']=d.index
        A.append(d.reset_index(drop=True))
    A=pd.concat(A,ignore_index=True); A['rng']=F.loc[pd.DatetimeIndex(A.dt),'T_rng48'].values
    return A
def fit_w(O):
    w,_=nnls(O[B].values,O.y.values); w=w/w.sum() if w.sum()>0 else np.ones(5)/5
    return (1-fp.BLEND_SHRINK)*w+fp.BLEND_SHRINK*np.ones(5)/5
for arm in ('base','drop85'):
    A=build(arm); out=[]; biases=[]
    for fam,fi in folds:
        tr_=A[~((A.fam==fam)&(A.fold==fi))].copy(); va=A[(A.fam==fam)&(A.fold==fi)]
        w=fit_w(tr_); e,W=fp.tod_blend_weights(tr_,w)
        tr_['pred']=np.clip(fp.apply_tod_blend(tr_[B].values,tr_.tod.values,e,W),5,100)
        b=np.linalg.lstsq(np.c_[np.ones(len(tr_)),dz(tr_.tod.values)],(tr_.pred-tr_.y).values,rcond=None)[0][1:]
        tr_['pred']=np.clip(tr_.pred-0.5*(dz(tr_.tod.values)@b),5,100)
        r=(tr_.pred-tr_.y).values; m=tr_.rng.values>CUT
        c=0.25*(r[m].mean()-r.mean()); biases.append(r[m].mean()-r.mean())
        p=np.clip(fp.apply_tod_blend(va[B].values,va.tod.values,e,W),5,100)
        p=np.clip(p-0.5*(dz(va.tod.values)@b),5,100)
        rec=dict(fam=fam,fold=fi,base=fp.rmse(va.y,p))
        for s in (0.15,0.25,0.35,0.50):
            cs=s*(r[m].mean()-r.mean())
            rec[f's{s}']=fp.rmse(va.y,np.clip(np.where(va.rng.values>CUT,p-cs,p),5,100))
        out.append(rec)
    R=pd.DataFrame(out)
    print("\n=== %s feature set ===  (band bias estimated per fold: mean %+.3f, sd %.3f)"%(arm,np.mean(biases),np.std(biases)))
    for s in (0.15,0.25,0.35,0.50):
        d=R[f's{s}']-R.base
        print("   shrink %.2f: %+.4f  (%2d/%d folds)"%(s,d.mean(),(d<0).sum(),len(R)))
    for fam,sub in R.groupby('fam'):
        d=sub['s0.25']-sub.base
        print("     family %s at 0.25: %+.4f (%d/%d)"%(fam,d.mean(),(d<0).sum(),len(sub)))
# day-level pricing at the shipped cut, on the base arm
A=build('base')
P=[]
for fam,fi in folds:
    tr_=A[~((A.fam==fam)&(A.fold==fi))].copy(); va=A[(A.fam==fam)&(A.fold==fi)]
    w=fit_w(tr_); e,W=fp.tod_blend_weights(tr_,w)
    tr_['pred']=np.clip(fp.apply_tod_blend(tr_[B].values,tr_.tod.values,e,W),5,100)
    b=np.linalg.lstsq(np.c_[np.ones(len(tr_)),dz(tr_.tod.values)],(tr_.pred-tr_.y).values,rcond=None)[0][1:]
    p=np.clip(fp.apply_tod_blend(va[B].values,va.tod.values,e,W),5,100)
    P.append(pd.Series(np.clip(p-0.5*(dz(va.tod.values)@b),5,100),index=va.index))
A['pred']=pd.concat(P).sort_index(); A['res']=A.pred-A.y; A['dt']=pd.DatetimeIndex(A.dt)
U=A.groupby('dt').agg(res=('res','mean'),rng=('rng','first')).reset_index(); U['day']=U.dt.dt.date
S=U[U.rng>CUT]; days=sorted(S.day.unique())
print("\nband days on the base arm: %d   rows %d   bias %+.3f"%(len(days),len(S),S.res.mean()-U.res.mean()))
print(S.groupby('day').res.agg(['size','mean']).round(2).to_string())
rg=np.random.default_rng(1)
bs=np.array([S[S.day.isin(rg.choice(days,len(days),replace=True))].res.mean()-U.res.mean() for _ in range(20000)])
print("day-level bootstrap: %+.2f  95%% CI [%+.2f, %+.2f]  P(>0)=%.3f"%(S.res.mean()-U.res.mean(),
      np.percentile(bs,2.5),np.percentile(bs,97.5),(bs>0).mean()))
