"""Error analysis on the current best stack (v13 configuration: low-support filter +
per-band weights + harmonic bias), nested leave-one-fold-out."""
import numpy as np, pandas as pd, pickle, sys
sys.path.insert(0,'.'); import final_pipeline as fp
from scipy.optimize import nnls
B=fp.MODELS
res=pickle.load(open('outputs/dropblend_oof.pkl','rb'))
g=fp.load_grid(); F=fp.make_features(g); y=g[fp.TARGET]
folds=sorted({(k[0],k[1]) for k in res if (k[0],k[1],'drop85') in res})
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
A['pred']=pd.concat(P).sort_index(); A['res']=A.pred-A.y; A['se']=A.res**2
for c in ['T','rh_tmin48','T_rng48','co2','air_temperature_sd6h']:
    A[c]=F.loc[pd.DatetimeIndex(A.dt),c].values
print("current stack, nested LOO RMSE %.4f  bias %+.3f  n=%d"%(np.sqrt(A.se.mean()),A.res.mean(),len(A)))
s=A.se.sort_values(ascending=False)
print("concentration: top 1%% of rows hold %.1f%% of squared error, top 5%% %.1f%%, top 10%% %.1f%%"%(
    100*s.head(int(.01*len(s))).sum()/s.sum(),100*s.head(int(.05*len(s))).sum()/s.sum(),100*s.head(int(.10*len(s))).sum()/s.sum()))
def tab(k,q=6):
    b=pd.qcut(A[k],q,duplicates='drop')
    t=A.groupby(b,observed=True).agg(n=('se','size'),rmse=('se',lambda x:np.sqrt(x.mean())),bias=('res','mean'),sse=('se','sum'))
    t['share_%']=100*t.sse/A.se.sum(); return t.drop(columns='sse').round(3)
for k in ['T','y','tod','rh_tmin48','T_rng48']:
    print(f"\n--- by {k} ---"); print(tab(k).to_string())
# what fraction of the error is a slow day-level offset vs fast within-day?
A['day']=pd.DatetimeIndex(A.dt).date
dm=A.groupby(['fam','fold','day']).res.transform('mean')
print("\nvariance decomposition of the residual:")
print("   day-level offset (slow): %.2f  %.0f%% of MSE"%(dm.var(),100*(dm**2).mean()/A.se.mean()))
print("   within-day (fast)      : %.2f  %.0f%%"%((A.res-dm).var(),100*((A.res-dm)**2).mean()/A.se.mean()))
