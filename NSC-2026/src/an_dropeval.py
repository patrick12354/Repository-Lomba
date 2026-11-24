"""Evaluate the cached two-arm OOF at blend level, nested leave-one-fold-out, through the
full v12 stack: NNLS weights -> per-band weights -> harmonic bias."""
import numpy as np, pandas as pd, pickle, sys
sys.path.insert(0,'.'); import final_pipeline as fp
from scipy.optimize import nnls
B=fp.MODELS
res=pickle.load(open('outputs/dropblend_oof.pkl','rb'))
g=fp.load_grid(); y=g[fp.TARGET]
arms=sorted({k[2] for k in res}); folds=sorted({(k[0],k[1]) for k in res if all((k[0],k[1],a) in res for a in arms)})
print("arms %s   complete folds %d"%(arms,len(folds)))
def dz(t):
    t=2*np.pi*np.asarray(t)/24; return np.column_stack([np.sin(t),np.cos(t)])
tab={}
for arm in arms:
    A=[]
    for fam,fi in folds:
        d=res[(fam,fi,arm)].copy(); d['y']=y.reindex(d.index).values
        d['tod']=d.index.hour+d.index.minute/60; d['fam']=fam; d['fold']=fi
        A.append(d.reset_index(drop=True))
    tab[arm]=pd.concat(A,ignore_index=True)
def fit_w(O):
    w,_=nnls(O[B].values,O.y.values); w=w/w.sum() if w.sum()>0 else np.ones(5)/5
    return (1-fp.BLEND_SHRINK)*w+fp.BLEND_SHRINK*np.ones(5)/5
out=[]
for fam,fi in folds:
    r=dict(fam=fam,fold=fi)
    for arm in arms:
        A=tab[arm]; tr_=A[~((A.fam==fam)&(A.fold==fi))].copy(); va=A[(A.fam==fam)&(A.fold==fi)].copy()
        w=fit_w(tr_); e,W=fp.tod_blend_weights(tr_,w)
        tr_['pred']=np.clip(fp.apply_tod_blend(tr_[B].values,tr_.tod.values,e,W),5,100)
        b=np.linalg.lstsq(np.c_[np.ones(len(tr_)),dz(tr_.tod.values)],(tr_.pred-tr_.y).values,rcond=None)[0][1:]
        p10=np.clip(fp.apply_tod_blend(va[B].values,va.tod.values,e,W),5,100)
        r[f'{arm}_v8']=fp.rmse(va.y,np.clip(va[B].values@w,5,100))
        r[f'{arm}_v10']=fp.rmse(va.y,p10)
        r[f'{arm}_v12']=fp.rmse(va.y,np.clip(p10-0.5*(dz(va.tod.values)@b),5,100))
        for m in B: r[f'{arm}_{m}']=fp.rmse(va.y,va[m])
        if arm==arms[-1]: r['w_'+arm]=None
    out.append(r)
R=pd.DataFrame(out); R.to_csv('outputs/exp_dropeval.csv',index=False)
print("\nmembers, mean RMSE over %d folds:"%len(R))
print("%-9s %9s %9s %10s %8s"%("member","base","drop85","delta","folds"))
for m in B:
    a,b_=f'base_{m}',f'drop85_{m}'
    print("%-9s %9.4f %9.4f %+10.4f %5d/%d"%(m,R[a].mean(),R[b_].mean(),R[b_].mean()-R[a].mean(),(R[b_]<R[a]).sum(),len(R)))
print("\nBLEND, nested leave-one-fold-out:")
print("%-9s %9s %9s %10s %8s"%("stack","base","drop85","delta","folds"))
for st in ['v8','v10','v12']:
    a,b_=f'base_{st}',f'drop85_{st}'
    print("%-9s %9.4f %9.4f %+10.4f %5d/%d"%(st,R[a].mean(),R[b_].mean(),R[b_].mean()-R[a].mean(),(R[b_]<R[a]).sum(),len(R)))
d=(R.drop85_v12-R.base_v12).values
rng=np.random.default_rng(4); bs=[rng.choice(d,len(d),replace=True).mean() for _ in range(20000)]
print("\nv12 stack, drop85 vs base: %+.4f  bootstrap 95%% CI [%.4f, %.4f]"%(d.mean(),np.percentile(bs,2.5),np.percentile(bs,97.5)))
for fam,sub in R.groupby('fam'):
    print("  family %s: %+.4f (%d/%d)"%(fam,(sub.drop85_v12-sub.base_v12).mean(),
          (sub.drop85_v12<sub.base_v12).sum(),len(sub)))
A=tab['base']; Ad=tab['drop85']
for nm,A_ in (('base',A),('drop85',Ad)):
    w=fit_w(A_); print("  %s pooled blend weights: %s"%(nm,{m:round(float(x),3) for m,x in zip(B,w)}))
