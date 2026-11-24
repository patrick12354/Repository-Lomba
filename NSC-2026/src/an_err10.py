"""What is left after the harmonic diurnal fix?  Nested LOO residuals, and a scan of
candidate second conditioners -- each judged on nested gain, cross-fold sign stability, and
the s46 occupancy guard between train and the actual test window."""
import numpy as np, pandas as pd, pickle, sys
sys.path.insert(0,'.'); import final_pipeline as fp
from scipy.optimize import nnls
B=fp.MODELS; S=(0,1,2)
cache=pickle.load(open('outputs/h7_oof.pkl','rb'))
g=fp.load_grid(); F=fp.make_features(g); y=g[fp.TARGET]; IDX=g.index
is_tr=(g.is_test==0).values & y.notna().values; idx=IDX[is_tr]; end=idx.max()
te=IDX[(g.is_test==1).values]
def famdef(n,vd,sd,mtd=30):
    out=[]
    for i in range(n):
        cut=end-pd.Timedelta(days=sd*i); vs=cut-pd.Timedelta(days=vd)
        if (vs-idx.min()).days<mtd: break
        out.append((vs,cut))
    return out[::-1]
FAMS={'P':famdef(9,15,2),'Q':famdef(6,15,3,36),'R':famdef(5,21,3,28)}
AX=['T','pressure','co2','T_rng48','air_temperature_sd6h','rh_tmin48','p_tend24h','co2_c24h']
rows=[]
for fam,folds in FAMS.items():
    for fi,(vs,ve) in enumerate(folds):
        v=is_tr&(IDX>vs)&(IDX<=ve)
        if v.sum()<50 or (fam,fi,B[0],'',S) not in cache: continue
        d=pd.DataFrame({m:cache[(fam,fi,m,'',S)] for m in B})
        d['y']=y[v].values; d['tod']=IDX[v].hour+IDX[v].minute/60; d['fam']=fam; d['fold']=fi
        for c in AX: d[c]=F.loc[IDX[v],c].values
        rows.append(d)
A=pd.concat(rows,ignore_index=True)
def fit_w(O):
    w,_=nnls(O[B].values,O.y.values); w=w/w.sum() if w.sum()>0 else np.ones(5)/5
    return (1-fp.BLEND_SHRINK)*w+fp.BLEND_SHRINK*np.ones(5)/5
def dz(tod):
    t=2*np.pi*np.asarray(tod)/24; return np.column_stack([np.sin(t),np.cos(t)])
outs=[]; rng=np.random.default_rng(31)
NB=4
for fam in FAMS:
    Af=A[A.fam==fam]
    for fo in sorted(Af.fold.unique()):
        tr_=Af[Af.fold!=fo].copy(); va=Af[Af.fold==fo].copy()
        w=fit_w(tr_); e,W=fp.tod_blend_weights(tr_,w)
        for D in (tr_,va): D['pred']=np.clip(fp.apply_tod_blend(D[B].values,D.tod.values,e,W),5,100)
        rt=(tr_.pred-tr_.y).values
        b=np.linalg.lstsq(np.c_[np.ones(len(tr_)),dz(tr_.tod.values)],rt,rcond=None)[0][1:]
        for D,rr in ((tr_,None),(va,None)):
            D['pred2']=np.clip(D.pred.values-0.5*(dz(D.tod.values)@b),5,100)
        tr_['res2']=tr_.pred2-tr_.y
        rec=dict(fam=fam,fold=fo,base=fp.rmse(va.y,va.pred2))
        for ax in AX+['rand']:
            if ax=='rand':
                bt=rng.integers(0,NB,len(tr_)); bv=rng.integers(0,NB,len(va))
            else:
                ed=np.nanquantile(tr_[ax].values,np.linspace(0,1,NB+1)); ed[0],ed[-1]=-np.inf,np.inf
                bt=np.digitize(tr_[ax].values,ed[1:-1]); bv=np.digitize(va[ax].values,ed[1:-1])
                rec[f'occ_{ax}']=np.abs(np.bincount(bt,minlength=NB)/len(bt)
                                        -np.bincount(bv,minlength=NB)/len(bv)).max()
            m=np.array([tr_.res2[bt==i].mean() if (bt==i).sum()>20 else tr_.res2.mean() for i in range(NB)])
            m=m-tr_.res2.mean()
            rec[f'g_{ax}']=fp.rmse(va.y,np.clip(va.pred2-0.5*m[bv],5,100))-rec['base']
            if ax!='rand': rec[f'sd_{ax}']=m.std()
        outs.append(rec)
R=pd.DataFrame(outs)
print("baseline after tod-blend + harmonic bias: %.4f\n"%R.base.mean())
# occupancy shift train -> REAL test window
Ftr=F.loc[idx]; occ={}
for ax in AX:
    ed=np.nanquantile(Ftr[ax].values,np.linspace(0,1,NB+1)); ed[0],ed[-1]=-np.inf,np.inf
    a=np.bincount(np.digitize(Ftr[ax].values,ed[1:-1]),minlength=NB)/len(Ftr)
    b_=np.bincount(np.digitize(F.loc[te,ax].values,ed[1:-1]),minlength=NB)/len(te)
    occ[ax]=np.abs(a-b_).max()
print("%-22s %10s %8s %12s"%("second conditioner","nested d","folds","train->TEST occupancy shift"))
for ax in AX:
    print("%-22s %+10.4f %5d/18 %12.3f%s"%(ax,R[f'g_{ax}'].mean(),(R[f'g_{ax}']<0).sum(),occ[ax],
          "  <-- FAILS s46 guard" if occ[ax]>0.05 else ""))
print("%-22s %+10.4f %5d/18 %12s"%("random (control)",R['g_rand'].mean(),(R['g_rand']<0).sum(),"-"))
