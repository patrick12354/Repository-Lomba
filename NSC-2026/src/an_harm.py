"""Is a smooth harmonic diurnal correction better than three step bands?
Same nested protocol as s69: 18 folds, three families, correction estimated on the other
folds only, every variant scored against a random conditioner with the same parameter count."""
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
def fit_w(O):
    w,_=nnls(O[B].values,O.y.values); w=w/w.sum() if w.sum()>0 else np.ones(5)/5
    return (1-fp.BLEND_SHRINK)*w+fp.BLEND_SHRINK*np.ones(5)/5
def design(tod,K):
    return np.column_stack([f(2*np.pi*k*np.asarray(tod)/24) for k in range(1,K+1) for f in (np.sin,np.cos)])
def band_corr(res,btr,bva,nb):
    m=np.array([res[btr==i].mean() if (btr==i).sum()>20 else res.mean() for i in range(nb)])
    return (m-res.mean())[bva]
SHR=0.5; rng=np.random.default_rng(23)
res=[]
for fam in FAMS:
    Af=A[A.fam==fam]
    for fo in sorted(Af.fold.unique()):
        tr_=Af[Af.fold!=fo].copy(); va=Af[Af.fold==fo].copy()
        w=fit_w(tr_); e,W=fp.tod_blend_weights(tr_,w)
        for D in (tr_,va): D['pred']=np.clip(fp.apply_tod_blend(D[B].values,D.tod.values,e,W),5,100)
        r=(tr_.pred-tr_.y).values
        rec=dict(fam=fam,fold=fo,none=fp.rmse(va.y,va.pred))
        for nb in (2,3,4,6,8):
            ed=np.quantile(tr_.tod.values,np.linspace(0,1,nb+1)); ed[0],ed[-1]=-np.inf,np.inf
            c=band_corr(r,np.digitize(tr_.tod.values,ed[1:-1]),np.digitize(va.tod.values,ed[1:-1]),nb)
            rec[f'band{nb}']=fp.rmse(va.y,np.clip(va.pred-SHR*c,5,100))
        for K in (1,2,3,4):
            X=design(tr_.tod.values,K); Xv=design(va.tod.values,K)
            b=np.linalg.lstsq(np.c_[np.ones(len(X)),X],r,rcond=None)[0][1:]   # intercept dropped
            rec[f'harm{K}']=fp.rmse(va.y,np.clip(va.pred-SHR*(Xv@b),5,100))
        for npar in (3,4,6):     # random conditioner controls at matching parameter counts
            rb=rng.integers(0,npar,len(tr_)); rv=rng.integers(0,npar,len(va))
            rec[f'rand{npar}']=fp.rmse(va.y,np.clip(va.pred-SHR*band_corr(r,rb,rv,npar),5,100))
        res.append(rec)
R=pd.DataFrame(res); base=R.none.mean()
print("nested LOO CV, 18 folds, shrink 0.5.  baseline (v10 tod-blend) = %.4f"%base)
print("%-10s %9s %8s %7s"%("variant","delta","folds","params"))
par={'band2':1,'band3':2,'band4':3,'band6':5,'band8':7,'harm1':2,'harm2':4,'harm3':6,'harm4':8,
     'rand3':2,'rand4':3,'rand6':5}
for c in ['band2','band3','band4','band6','band8','harm1','harm2','harm3','harm4','rand3','rand4','rand6']:
    print("%-10s %+9.4f %6d/18 %7d"%(c,R[c].mean()-base,(R[c]<R.none).sum(),par[c]))
R.to_csv('outputs/exp_harm.csv',index=False)
d=(R.harm2-R.band3).values
print("\nharm2 vs the shipped band3: mean %+.4f  (%d/18 folds better)"%(d.mean(),(d<0).sum()))
rngb=np.random.default_rng(5); bs=[rngb.choice(d,len(d),replace=True).mean() for _ in range(20000)]
print("bootstrap 95%% CI: [%.4f, %.4f]"%(np.percentile(bs,2.5),np.percentile(bs,97.5)))
