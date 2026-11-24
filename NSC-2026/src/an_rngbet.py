"""Price the wide-range correction as a bet.  Day-level resampling, because T_rng48 is a
48h rolling statistic and the effective sample is DAYS, not rows."""
import numpy as np, pandas as pd, pickle, sys
sys.path.insert(0,'.'); import final_pipeline as fp
from scipy.optimize import nnls
B=fp.MODELS
res=pickle.load(open('outputs/dropblend_oof.pkl','rb'))
g=fp.load_grid(); F=fp.make_features(g); y=g[fp.TARGET]; IDX=g.index; te=IDX[(g.is_test==1).values]
folds=sorted({(k[0],k[1]) for k in res if (k[0],k[1],'drop85') in res})
def dz(t):
    t=2*np.pi*np.asarray(t)/24; return np.column_stack([np.sin(t),np.cos(t)])
A=[]
for fam,fi in folds:
    d=res[(fam,fi,'drop85')].copy(); d['y']=y.reindex(d.index).values
    d['tod']=d.index.hour+d.index.minute/60; d['fam']=fam; d['fold']=fi; d['dt']=d.index
    A.append(d.reset_index(drop=True))
A=pd.concat(A,ignore_index=True); A['rng']=F.loc[pd.DatetimeIndex(A.dt),'T_rng48'].values
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
A['pred']=pd.concat(P).sort_index(); A['res']=A.pred-A.y; A['dt']=pd.DatetimeIndex(A.dt)
U=A.groupby('dt').agg(res=('res','mean'),rng=('rng','first')).reset_index(); U['day']=U.dt.dt.date
CUT=23.35; S=U[U.rng>CUT]
days=sorted(S.day.unique())
per=S.groupby('day').res.agg(['size','mean'])
print("the %d training days that carry the whole effect:"%len(days))
print(per.round(2).to_string())
rng=np.random.default_rng(0)
bs=[S[S.day.isin(rng.choice(days,len(days),replace=True))].res.mean() for _ in range(20000)]
bs=np.array(bs)
print("\nday-level bootstrap of the bias: mean %+.2f  sd %.2f  95%% CI [%+.2f, %+.2f]  P(bias>0)=%.3f"%(
    S.res.mean(),bs.std(),np.percentile(bs,2.5),np.percentile(bs,97.5),(bs>0).mean()))
share=0.304; base=3.6
print("\nprivate slice: %.1f%% of rows in the band, private RMSE %.2f"%(100*share,base))
print("%-9s %9s %11s %11s %11s %9s"%("shrink","subtract","if bias=4.11","if bias=CI-lo","if bias=0","P(helps)"))
for s in (0.15,0.25,0.35,0.50,0.75):
    c=s*S.res.mean()
    def newr(b): return np.sqrt(max(base**2+share*(c**2-2*b*c),0.01))
    ph=(bs>c/2).mean()
    print("%-9.2f %9.2f %11.3f %11.3f %11.3f %9.3f"%(s,c,newr(4.11)-base,newr(np.percentile(bs,2.5))-base,newr(0)-base,ph))
print("\n(P(helps) = P(true bias > half the correction), from the day-level bootstrap.)")
pr=pd.Series(F.loc[te[220:],'T_rng48'].values,index=te[220:])
print("\nprivate band days: %s"%sorted({str(d) for d in pr[pr>CUT].index.date}))
