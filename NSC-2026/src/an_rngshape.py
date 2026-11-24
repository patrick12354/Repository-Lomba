"""What is the shape of the bias against T_rng48?  A genuine threshold, or a few rows?"""
import numpy as np, pandas as pd, pickle, sys
sys.path.insert(0,'.'); import final_pipeline as fp
from scipy.optimize import nnls
B=fp.MODELS
res=pickle.load(open('outputs/dropblend_oof.pkl','rb'))
g=fp.load_grid(); F=fp.make_features(g); y=g[fp.TARGET]; IDX=g.index
te=IDX[(g.is_test==1).values]
folds=sorted({(k[0],k[1]) for k in res if (k[0],k[1],'drop85') in res})
def dz(t):
    t=2*np.pi*np.asarray(t)/24; return np.column_stack([np.sin(t),np.cos(t)])
A=[]
for fam,fi in folds:
    d=res[(fam,fi,'drop85')].copy(); d['y']=y.reindex(d.index).values
    d['tod']=d.index.hour+d.index.minute/60; d['fam']=fam; d['fold']=fi; d['dt']=d.index
    A.append(d.reset_index(drop=True))
A=pd.concat(A,ignore_index=True)
A['T_rng48']=F.loc[pd.DatetimeIndex(A.dt),'T_rng48'].values
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
A['pred']=pd.concat(P).sort_index(); A['res']=A.pred-A.y
A['dt']=pd.DatetimeIndex(A.dt)
U=A.groupby('dt').agg(res=('res','mean'),rng=('T_rng48','first')).reset_index()
print("bias against T_rng48, on the %d UNIQUE timestamps (20 equal-count bins):"%len(U))
U['b']=pd.qcut(U.rng,20,labels=False,duplicates='drop')
t=U.groupby('b').agg(n=('res','size'),rng_lo=('rng','min'),rng_hi=('rng','max'),bias=('res','mean'),
                     se=('res',lambda s:s.std()/np.sqrt(max(len(s)/12,1))))   # /12 for autocorrelation
print(t.round(2).to_string())
print("\nhow many distinct DAYS supply the top bins?")
U['day']=U.dt.dt.date
for lo in (22.5,23.0,23.35,23.8):
    s=U[U.rng>lo]
    print("  T_rng48 > %.2f : %4d rows, %2d distinct days, bias %+.2f"%(lo,len(s),s.day.nunique(),s.res.mean()))
print("\nprivate slice, same cuts:")
pr=F.loc[te[220:],'T_rng48']
prd=pd.Series(pr.values,index=te[220:]); 
for lo in (22.5,23.0,23.35,23.8):
    s=prd[prd>lo]
    print("  T_rng48 > %.2f : %4d rows (%.1f%% of private), %2d distinct days"%(
        lo,len(s),100*len(s)/len(prd),len(set(s.index.date))))
