"""Does the diurnal bias depend on the regime?  (progress.md s59's warning applied to s67)"""
import numpy as np, pandas as pd, pickle, sys
sys.path.insert(0,'.'); import final_pipeline as fp
from scipy.optimize import nnls
B=fp.MODELS; S=(0,1,2)
cache=pickle.load(open('outputs/h7_oof.pkl','rb'))
g=fp.load_grid(); F=fp.make_features(g); y=g[fp.TARGET]; IDX=g.index
is_tr=(g.is_test==0).values & y.notna().values; idx=IDX[is_tr]; end=idx.max()
def famdef(n,vd,sd,mtd=30):
    out=[]
    for i in range(n):
        cut=end-pd.Timedelta(days=sd*i); vs=cut-pd.Timedelta(days=vd)
        if (vs-idx.min()).days<mtd: break
        out.append((vs,cut))
    return out[::-1]
FAMS={'P':famdef(9,15,2),'Q':famdef(6,15,3,36),'R':famdef(5,21,3,28)}
rows=[]
for fam,folds in FAMS.items():
    for fi,(vs,ve) in enumerate(folds):
        v=is_tr&(IDX>vs)&(IDX<=ve)
        if v.sum()<50 or (fam,fi,B[0],'',S) not in cache: continue
        d=pd.DataFrame({m:cache[(fam,fi,m,'',S)] for m in B})
        d['y']=y[v].values; d['tod']=IDX[v].hour+IDX[v].minute/60
        d['T']=F.loc[IDX[v],'T'].values; d['fam']=fam; d['fold']=fi; rows.append(d)
A=pd.concat(rows,ignore_index=True)
w,_=nnls(A[B].values,A.y.values); w=w/w.sum(); w=0.75*w+0.25*np.ones(5)/5
A['pred']=np.clip(A[B].values@w,5,100); A['res']=A.pred-A.y
ed=np.quantile(A.tod.values,np.linspace(0,1,4)); ed[0],ed[-1]=-np.inf,np.inf
A['band']=np.digitize(A.tod.values,ed[1:-1])
recs=[]
for (fa,fo),d in A.groupby(['fam','fold']):
    gb=d.res.mean()
    r=dict(fam=fa,fold=fo,T=d['T'].mean(),RH=d.y.mean(),swing=d.y.groupby(d.band).mean().max()-d.y.groupby(d.band).mean().min())
    for i in range(3): r[f'rel{i}']=d.res[d.band==i].mean()-gb
    recs.append(r)
C=pd.DataFrame(recs)
print("per-fold band-relative bias vs fold regime:")
print(C.round(3).to_string(index=False))
print("\ncorrelation of each band's relative bias with the fold's mean temperature:")
for i in range(3): print(f"  band{i}: r(T) = {C[f'rel{i}'].corr(C['T']):+.3f}   r(mean RH) = {C[f'rel{i}'].corr(C.RH):+.3f}   r(diurnal swing) = {C[f'rel{i}'].corr(C.swing):+.3f}")
print("\namplitude of the correction (band1 - band0) vs regime:  r(T) = %+.3f"%((C.rel1-C.rel0).corr(C['T'])))
te=g.index[(g.is_test==1).values]
print("\nregime comparison: CV folds mean T range %.1f-%.1f  |  test window %.1f  (public %.1f, private %.1f)"%(
    C['T'].min(),C['T'].max(),F.loc[te,'T'].mean(),F.loc[te,'T'][:220].mean(),F.loc[te,'T'][220:].mean()))
