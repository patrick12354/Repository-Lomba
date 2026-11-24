"""Per-time-of-day-band bias correction, scored nested, against the §63 controls."""
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
rng=np.random.default_rng(11)
SHR=[0.0,0.25,0.5,0.75,1.0]
res=[]; bandtab=[]
for fam in FAMS:
    Af=A[A.fam==fam]
    for fo in sorted(Af.fold.unique()):
        tr_=Af[Af.fold!=fo].copy(); va=Af[Af.fold==fo].copy()
        w=fit_w(tr_); e,W=fp.tod_blend_weights(tr_,w)
        for D in (tr_,va): D['pred']=np.clip(fp.apply_tod_blend(D[B].values,D.tod.values,e,W),5,100)
        tr_['res']=tr_.pred-tr_.y
        ed=np.quantile(tr_.tod.values,np.linspace(0,1,4)); ed[0],ed[-1]=-np.inf,np.inf
        bt=np.digitize(tr_.tod.values,ed[1:-1]); bv=np.digitize(va.tod.values,ed[1:-1])
        bb=np.array([tr_.res[bt==i].mean() for i in range(3)]); gb=tr_.res.mean()
        bandtab.append(dict(fam=fam,fold=fo,glob=gb,b0=bb[0],b1=bb[1],b2=bb[2]))
        rb=rng.integers(0,3,len(tr_)); rbv=rng.integers(0,3,len(va))
        rr=np.array([tr_.res[rb==i].mean() for i in range(3)])
        r=dict(fam=fam,fold=fo,none=fp.rmse(va.y,va.pred))
        for s in SHR:
            r[f'band{s}']=fp.rmse(va.y,np.clip(va.pred-s*bb[bv],5,100))
            r[f'rel{s}'] =fp.rmse(va.y,np.clip(va.pred-s*(bb-gb)[bv],5,100))
            r[f'glob{s}']=fp.rmse(va.y,np.clip(va.pred-s*gb,5,100))
            r[f'rand{s}']=fp.rmse(va.y,np.clip(va.pred-s*rr[rbv],5,100))
        res.append(r)
R=pd.DataFrame(res); B_=pd.DataFrame(bandtab)
print("per-fold band biases estimated on the OTHER folds (stability check):")
print(B_.round(3).to_string(index=False))
print("\nband-relative bias (band - global), per fold:")
rel=B_[['b0','b1','b2']].sub(B_.glob,axis=0); rel.insert(0,'fold',B_.fold); rel.insert(0,'fam',B_.fam)
print(rel.round(3).to_string(index=False))
print("  sign consistency: b0<0 in %d/18, b1>0 in %d/18, b2<0 in %d/18"%(
    (rel.b0<0).sum(),(rel.b1>0).sum(),(rel.b2<0).sum()))
base=R.none.mean()
print("\n=== nested LOO CV, 18 folds.  baseline (v10 tod-blend) = %.4f ==="%base)
for kind in ['glob','rel','band','rand']:
    line=[]
    for s in SHR:
        c=f'{kind}{s}'; line.append(f"s={s}: {R[c].mean()-base:+.4f} ({(R[c]<R.none).sum():2d}/18)")
    print(f"  {kind:5s} " + "   ".join(line))
R.to_csv('outputs/exp_todbias.csv',index=False)
