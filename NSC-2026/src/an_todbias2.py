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
        d['y']=y[v].values; d['tod']=IDX[v].hour+IDX[v].minute/60; d['fam']=fam; d['fold']=fi
        d['dt']=IDX[v]; rows.append(d)
A=pd.concat(rows,ignore_index=True)
def fit_w(O):
    w,_=nnls(O[B].values,O.y.values); w=w/w.sum() if w.sum()>0 else np.ones(5)/5
    return (1-fp.BLEND_SHRINK)*w+fp.BLEND_SHRINK*np.ones(5)/5
res=[]
for fam in FAMS:
    Af=A[A.fam==fam]
    for fo in sorted(Af.fold.unique()):
        tr_=Af[Af.fold!=fo].copy(); va=Af[Af.fold==fo].copy().sort_values('dt').reset_index(drop=True)
        w=fit_w(tr_); e,W=fp.tod_blend_weights(tr_,w)
        for D in (tr_,va): D['pred']=np.clip(fp.apply_tod_blend(D[B].values,D.tod.values,e,W),5,100)
        tr_['res']=tr_.pred-tr_.y
        ed=np.quantile(tr_.tod.values,np.linspace(0,1,4)); ed[0],ed[-1]=-np.inf,np.inf
        bt=np.digitize(tr_.tod.values,ed[1:-1]); bv=np.digitize(va.tod.values,ed[1:-1])
        bb=np.array([tr_.res[bt==i].mean() for i in range(3)]); gb=tr_.res.mean()
        cor=np.clip(va.pred-0.5*(bb-gb)[bv],5,100)
        n=len(va); k=int(round(.3*n)); mk=np.arange(n)<k
        res.append(dict(fam=fam,fold=fo,
            base=fp.rmse(va.y,va.pred), rel=fp.rmse(va.y,cor),
            base_pub=fp.rmse(va.y[mk],va.pred[mk]), rel_pub=fp.rmse(va.y[mk],cor[mk]),
            base_pri=fp.rmse(va.y[~mk],va.pred[~mk]), rel_pri=fp.rmse(va.y[~mk],cor[~mk])))
R=pd.DataFrame(res)
print("band-relative bias correction, shrink 0.5 -- by fold family:")
for fam,d in R.groupby('fam'):
    print(f"  {fam}: whole {d.rel.mean()-d.base.mean():+.4f} ({(d.rel<d.base).sum()}/{len(d)})"
          f"   near30% {d.rel_pub.mean()-d.base_pub.mean():+.4f} ({(d.rel_pub<d.base_pub).sum()}/{len(d)})"
          f"   far70% {d.rel_pri.mean()-d.base_pri.mean():+.4f} ({(d.rel_pri<d.base_pri).sum()}/{len(d)})")
print(f"  ALL: whole {R.rel.mean()-R.base.mean():+.4f} ({(R.rel<R.base).sum()}/18)"
      f"   near30% {R.rel_pub.mean()-R.base_pub.mean():+.4f} ({(R.rel_pub<R.base_pub).sum()}/18)"
      f"   far70% {R.rel_pri.mean()-R.base_pri.mean():+.4f} ({(R.rel_pri<R.base_pri).sum()}/18)")
# bootstrap CI on the per-fold delta
d=(R.rel-R.base).values; rng=np.random.default_rng(3)
bs=[rng.choice(d,len(d),replace=True).mean() for _ in range(20000)]
print("\nbootstrap 95%% CI on the per-fold delta: [%.4f, %.4f]"%(np.percentile(bs,2.5),np.percentile(bs,97.5)))
