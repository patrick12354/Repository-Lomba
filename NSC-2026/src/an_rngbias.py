"""The wide-diurnal-range bias: is it a transferable relationship or a summer artefact?
s63 forbids conditioning on a variable whose band occupancy shifts, and T_rng48's does.
So test the relationship itself, hard, before considering it."""
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
for c in ['T_rng48','T']: A[c]=F.loc[pd.DatetimeIndex(A.dt),c].values
def fit_w(O):
    w,_=nnls(O[B].values,O.y.values); w=w/w.sum() if w.sum()>0 else np.ones(5)/5
    return (1-fp.BLEND_SHRINK)*w+fp.BLEND_SHRINK*np.ones(5)/5
def stack(tr_,va):
    w=fit_w(tr_); e,W=fp.tod_blend_weights(tr_,w)
    tr2=tr_.copy(); tr2['pred']=np.clip(fp.apply_tod_blend(tr_[B].values,tr_.tod.values,e,W),5,100)
    b=np.linalg.lstsq(np.c_[np.ones(len(tr2)),dz(tr2.tod.values)],(tr2.pred-tr2.y).values,rcond=None)[0][1:]
    tr2['pred']=np.clip(tr2.pred-0.5*(dz(tr2.tod.values)@b),5,100)
    p=np.clip(fp.apply_tod_blend(va[B].values,va.tod.values,e,W),5,100)
    return tr2, np.clip(p-0.5*(dz(va.tod.values)@b),5,100)
NB=6
ED=np.quantile(A.T_rng48,np.linspace(0,1,NB+1)); ED[0],ED[-1]=-np.inf,np.inf
print("band edges:",np.round(ED[1:-1],2))
print("\n--- 1. is the top-band bias stable across folds? (estimated per fold, own rows) ---")
recs=[]
for fam,fi in folds:
    tr_,_=stack(A[~((A.fam==fam)&(A.fold==fi))].copy(),A[(A.fam==fam)&(A.fold==fi)])
    b=np.digitize(tr_.T_rng48.values,ED[1:-1]); r=(tr_.pred-tr_.y).values
    recs.append(dict(fam=fam,fold=fi,T=tr_['T'].mean(),
                     **{f'b{i}':(r[b==i].mean() if (b==i).sum()>30 else np.nan) for i in range(NB)}))
C=pd.DataFrame(recs)
print(C.round(3).to_string(index=False))
print("\n top-band bias: mean %+.3f  sd %.3f  sign consistent %d/%d  corr with fold T %+.3f"%(
    C.b5.mean(),C.b5.std(),(C.b5>0).sum(),len(C),C.b5.corr(C['T'])))
print("\n--- 2. nested: correct the band bias, warm->cool transfer test ---")
out=[]
for fam,fi in folds:
    tr_,pv=stack(A[~((A.fam==fam)&(A.fold==fi))].copy(),A[(A.fam==fam)&(A.fold==fi)])
    va=A[(A.fam==fam)&(A.fold==fi)]
    bt=np.digitize(tr_.T_rng48.values,ED[1:-1]); bv=np.digitize(va.T_rng48.values,ED[1:-1])
    r=(tr_.pred-tr_.y).values
    m=np.array([r[bt==i].mean() if (bt==i).sum()>30 else r.mean() for i in range(NB)])-r.mean()
    Tf=tr_.groupby(['fam','fold'])['T'].mean(); warm=set(Tf[Tf>=Tf.median()].index)
    tw=tr_[[ (f,k) in warm for f,k in zip(tr_.fam,tr_.fold)]]
    bw=np.digitize(tw.T_rng48.values,ED[1:-1]); rw=(tw.pred-tw.y).values
    mw=np.array([rw[bw==i].mean() if (bw==i).sum()>30 else rw.mean() for i in range(NB)])-rw.mean()
    rec=dict(fam=fam,fold=fi,T=va['T'].mean(),base=fp.rmse(va.y,pv))
    for s in (0.25,0.5,0.75):
        rec[f'cor{s}']=fp.rmse(va.y,np.clip(pv-s*m[bv],5,100))
        rec[f'warm{s}']=fp.rmse(va.y,np.clip(pv-s*mw[bv],5,100))
    out.append(rec)
R=pd.DataFrame(out).sort_values('T')
for s in (0.25,0.5,0.75):
    d=R[f'cor{s}']-R.base; dw=R[f'warm{s}']-R.base; c=R.head(9)
    print(" shrink %.2f: all %+.4f (%2d/18) | coolest 9 %+.4f (%d/9) | warm-half estimate: all %+.4f (%2d/18), coolest 9 %+.4f (%d/9)"%(
        s,d.mean(),(d<0).sum(),(c[f'cor{s}']-c.base).mean(),((c[f'cor{s}']-c.base)<0).sum(),
        dw.mean(),(dw<0).sum(),(c[f'warm{s}']-c.base).mean(),((c[f'warm{s}']-c.base)<0).sum()))
print("\n--- 3. s46 occupancy guard, train vs the real test slices ---")
occ=lambda v: np.bincount(np.digitize(v,ED[1:-1]),minlength=NB)/len(v)
o_tr,o_pub,o_pri=occ(A.T_rng48.values),occ(F.loc[te,'T_rng48'].values[:220]),occ(F.loc[te,'T_rng48'].values[220:])
print(pd.DataFrame({'train':o_tr,'public':o_pub,'private':o_pri}).round(3).to_string())
print(" max shift train->public %.3f   train->private %.3f   (s63 bar: 0.05)"%(
    np.abs(o_pub-o_tr).max(),np.abs(o_pri-o_tr).max()))
