"""The widest-diurnal-range band carries a +4.38 bias and a third of all squared error.
Where do the public and private slices actually sit on that axis?"""
import numpy as np, pandas as pd, pickle, sys
sys.path.insert(0,'.'); import final_pipeline as fp
g=fp.load_grid(); F=fp.make_features(g); IDX=g.index
is_tr=(g.is_test==0).values; te=IDX[(g.is_test==1).values]
A=pd.read_pickle('outputs/an10_loo_oof.pkl') if False else None
import subprocess
# rebuild the OOF table from an_err11's cache
res=pickle.load(open('outputs/dropblend_oof.pkl','rb'))
y=g[fp.TARGET]
folds=sorted({(k[0],k[1]) for k in res if (k[0],k[1],'drop85') in res})
from scipy.optimize import nnls
B=fp.MODELS
def dz(t):
    t=2*np.pi*np.asarray(t)/24; return np.column_stack([np.sin(t),np.cos(t)])
A=[]
for fam,fi in folds:
    d=res[(fam,fi,'drop85')].copy(); d['y']=y.reindex(d.index).values
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
A['pred']=pd.concat(P).sort_index(); A['res']=A.pred-A.y
A['rng']=F.loc[pd.DatetimeIndex(A.dt),'T_rng48'].values
ed=np.quantile(A.rng,np.linspace(0,1,7)); ed[0],ed[-1]=-np.inf,np.inf
A['b']=np.digitize(A.rng,ed[1:-1])
t=A.groupby('b').agg(n=('res','size'),rmse=('res',lambda s:np.sqrt((s**2).mean())),bias=('res','mean'))
t['train_share']=t.n/len(A)
rte=F.loc[te,'T_rng48'].values; bte=np.digitize(rte,ed[1:-1])
t['public_share']=pd.Series(bte[:220]).value_counts(normalize=True).reindex(t.index).fillna(0)
t['private_share']=pd.Series(bte[220:]).value_counts(normalize=True).reindex(t.index).fillna(0)
t['edges']=[f"{ed[i]:.1f}-{ed[i+1]:.1f}" for i in t.index]
print("error by 48h diurnal temperature range, and where each slice sits:")
print(t.round(3).to_string())
for c in ['train_share','public_share','private_share']:
    print("  implied mean bias under %-14s %+.3f   implied RMSE %.3f"%(
        c+':',(t[c]*t.bias).sum(),np.sqrt((t[c]*t.rmse**2).sum())))
print("\nT_rng48 distribution:")
print("  train   ",np.round(np.percentile(A.rng,[5,25,50,75,95]),2))
print("  public  ",np.round(np.percentile(rte[:220],[5,25,50,75,95]),2))
print("  private ",np.round(np.percentile(rte[220:],[5,25,50,75,95]),2))
print("\nfraction of rows above the training 90th percentile of T_rng48:")
q90=np.percentile(A.rng,90)
print("  train 0.100 | public %.3f | private %.3f"%((rte[:220]>q90).mean(),(rte[220:]>q90).mean()))
