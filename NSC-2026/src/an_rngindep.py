"""The 18 folds overlap by 13 of 15 days, so '18/18' is not 18 independent measurements.
Estimate the band-5 bias on temporally DISJOINT stretches of training instead."""
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
for c in ['T_rng48','T']: A[c]=F.loc[pd.DatetimeIndex(A.dt),c].values
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
# deduplicate: each timestamp appears in several overlapping folds
U=A.groupby('dt').agg(res=('res','mean'),rng=('T_rng48','first'),T=('T','first'),y=('y','first')).reset_index()
print("unique timestamps in the OOF: %d (from %d fold-rows)"%(len(U),len(A)))
CUT=23.35
U['b5']=U.rng>CUT
print("\nband-5 bias on temporally DISJOINT stretches (calendar weeks):")
U['wk']=U.dt.dt.to_period('W')
t=U[U.b5].groupby('wk').agg(n=('res','size'),bias=('res','mean'),T=('T','mean'),rmse=('res',lambda s:np.sqrt((s**2).mean())))
t=t[t.n>=30]
print(t.round(2).to_string())
print("\n  weeks with data: %d   bias mean %+.3f   sd %.3f   positive in %d/%d"%(
    len(t),t.bias.mean(),t.bias.std(),(t.bias>0).sum(),len(t)))
print("  corr(week mean T, week band-5 bias) = %+.3f"%t['T'].corr(t.bias))
h=len(U)//2
for nm,sub in (('first half of training',U.iloc[:h]),('second half',U.iloc[h:])):
    s5=sub[sub.b5]
    print("  %-24s n=%4d  band-5 bias %+.3f | other bands %+.3f"%(nm,len(s5),s5.res.mean(),sub[~sub.b5].res.mean()))
print("\nis it training-set size?  band-5 bias by fold index within family P:")
pp=A[(A.fam=='P')&(A.T_rng48>CUT)].groupby('fold').res.agg(['size','mean'])
print(pp.round(3).to_string())
print("\nsanity: what does the model predict vs truth on band-5 rows?")
s5=U[U.b5]
print("  truth mean %.2f  sd %.2f | prediction mean %.2f  sd %.2f"%(
    s5.y.mean(),s5.y.std(),(s5.y+s5.res).mean(),(s5.y+s5.res).std()))
print("  non-band-5: truth %.2f  prediction %.2f"%(U[~U.b5].y.mean(),(U[~U.b5].y+U[~U.b5].res).mean()))
