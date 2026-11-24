"""Is the wide-range bias a T_rng48 relationship, or a confound with absolute temperature?
Training band-5 days and private band-5 days are only the same object if they sit in the
same place on every other axis."""
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
AX=['T_rng48','T','rh_tmin48','co2','T_min48','T_max48']
for c in AX: A[c]=F.loc[pd.DatetimeIndex(A.dt),c].values
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
CUT=23.35
tr5=A[A.T_rng48>CUT]
pri=F.loc[te[220:]]; pri5=pri[pri.T_rng48>CUT]; pub=F.loc[te[:220]]
print("band-5 rows (T_rng48 > %.2f): %d in the OOF, %d in the private slice, %d in public"%(
    CUT,len(tr5),len(pri5),(pub.T_rng48>CUT).sum()))
print("\nwhere those rows sit on every other axis:")
rows=[]
for c in AX:
    rows.append(dict(axis=c, train_band5=tr5[c].mean(), private_band5=pri5[c].mean(),
                     train_all=A[c].mean(), private_all=pri[c].mean()))
print(pd.DataFrame(rows).round(2).to_string(index=False))
print("\nband-5 T percentiles:  train %s"%np.round(np.percentile(tr5['T'],[5,25,50,75,95]),1))
print("                     private %s"%np.round(np.percentile(pri5['T'],[5,25,50,75,95]),1))
ov=((pri5['T']>=np.percentile(tr5['T'],1))&(pri5['T']<=np.percentile(tr5['T'],99))).mean()
print("  fraction of private band-5 rows inside the train band-5 T 1-99%% range: %.3f"%ov)
print("\nbias inside band 5, split by absolute temperature (train quartiles of band-5 T):")
q=np.percentile(tr5['T'],[0,25,50,75,100]); q[0],q[-1]=-np.inf,np.inf
b=np.digitize(tr5['T'],q[1:-1])
bp=np.digitize(pri5['T'],q[1:-1])
t=pd.DataFrame({'n_train':np.bincount(b,minlength=4),
                'bias':[tr5.res[b==i].mean() for i in range(4)],
                'rmse':[np.sqrt((tr5.res[b==i]**2).mean()) for i in range(4)],
                'private_share':np.bincount(bp,minlength=4)/len(bp)})
t['T_range']=[f"{q[i]:.1f}-{q[i+1]:.1f}" for i in range(4)]
print(t.round(3).to_string())
print("\n  implied band-5 bias under the TRAIN temperature mix   : %+.3f"%(t.n_train/t.n_train.sum()*t.bias).sum())
print("  implied band-5 bias under the PRIVATE temperature mix : %+.3f"%(t.private_share*t.bias).sum())
