"""Under distribution shift the standard defence is to shrink fitted weights toward a prior.
CV cannot adjudicate that (s77), but it CAN price it: how much in-regime RMSE does extra
shrinkage cost?  If the cost is near zero, extra shrinkage is cheap insurance."""
import numpy as np, pandas as pd, pickle, sys
sys.path.insert(0,'.'); import final_pipeline as fp
from scipy.optimize import nnls
B=fp.MODELS; S=(0,1,2)
cache=pickle.load(open('outputs/h7_oof.pkl','rb'))
g=fp.load_grid(); y=g[fp.TARGET]; IDX=g.index
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
        d['y']=y[v].values; d['tod']=IDX[v].hour+IDX[v].minute/60; d['fam']=fam; d['fold']=fi
        rows.append(d)
A=pd.concat(rows,ignore_index=True)
def dz(t):
    t=2*np.pi*np.asarray(t)/24; return np.column_stack([np.sin(t),np.cos(t)])
def run(bs,ts,hs):
    tot=[]
    for fam in FAMS:
        Af=A[A.fam==fam]
        for fo in sorted(Af.fold.unique()):
            tr_=Af[Af.fold!=fo].copy(); va=Af[Af.fold==fo]
            w,_=nnls(tr_[B].values,tr_.y.values); w=w/w.sum() if w.sum()>0 else np.ones(5)/5
            w=(1-bs)*w+bs*np.ones(5)/5
            e,W=fp.tod_blend_weights(tr_,w,shrink=ts)
            tr_['pred']=np.clip(fp.apply_tod_blend(tr_[B].values,tr_.tod.values,e,W),5,100)
            b=np.linalg.lstsq(np.c_[np.ones(len(tr_)),dz(tr_.tod.values)],(tr_.pred-tr_.y).values,rcond=None)[0][1:]
            p=np.clip(fp.apply_tod_blend(va[B].values,va.tod.values,e,W),5,100)
            tot.append(fp.rmse(va.y,np.clip(p-hs*(dz(va.tod.values)@b),5,100)))
    return np.array(tot)
base=run(0.25,0.50,0.50); print("shipped (blend 0.25 / band 0.50 / harmonic 0.50): %.4f"%base.mean())
print("\n%-42s %9s %9s"%("configuration","CV","cost"))
for bs in (0.25,0.40,0.55,0.70):
    for ts in (0.50,0.75):
        r=run(bs,ts,0.50)
        print("blend shrink %.2f / band shrink %.2f%-15s %9.4f %+9.4f"%(bs,ts,"",r.mean(),r.mean()-base.mean()))
print()
for hs in (0.25,0.35,0.50,0.65):
    r=run(0.25,0.50,hs)
    print("harmonic shrink %.2f%-24s %9.4f %+9.4f"%(hs,"",r.mean(),r.mean()-base.mean()))
