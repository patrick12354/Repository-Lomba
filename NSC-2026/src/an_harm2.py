"""s69's full gate set, applied to the single-harmonic diurnal correction."""
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
        d['T']=F.loc[IDX[v],'T'].values; d['dt']=IDX[v]; d['fam']=fam; d['fold']=fi
        rows.append(d)
A=pd.concat(rows,ignore_index=True)
def fit_w(O):
    w,_=nnls(O[B].values,O.y.values); w=w/w.sum() if w.sum()>0 else np.ones(5)/5
    return (1-fp.BLEND_SHRINK)*w+fp.BLEND_SHRINK*np.ones(5)/5
def design(tod): 
    t=2*np.pi*np.asarray(tod)/24; return np.column_stack([np.sin(t),np.cos(t)])
def coef(res,tod):
    X=design(tod); return np.linalg.lstsq(np.c_[np.ones(len(X)),X],res,rcond=None)[0][1:]
res=[]; coefs=[]
for fam in FAMS:
    Af=A[A.fam==fam]
    for fo in sorted(Af.fold.unique()):
        tr_=Af[Af.fold!=fo].copy(); va=Af[Af.fold==fo].copy().sort_values('dt').reset_index(drop=True)
        w=fit_w(tr_); e,W=fp.tod_blend_weights(tr_,w)
        for D in (tr_,va): D['pred']=np.clip(fp.apply_tod_blend(D[B].values,D.tod.values,e,W),5,100)
        r=(tr_.pred-tr_.y).values
        b=coef(r,tr_.tod.values); coefs.append(dict(fam=fam,fold=fo,T=va['T'].mean(),sin=b[0],cos=b[1],
                                                    amp=np.hypot(*b),peak=(np.degrees(np.arctan2(b[0],b[1]))%360)/15))
        cor=np.clip(va.pred-0.5*(design(va.tod.values)@b),5,100)
        # band3 for reference
        ed=np.quantile(tr_.tod.values,np.linspace(0,1,4)); ed[0],ed[-1]=-np.inf,np.inf
        bt=np.digitize(tr_.tod.values,ed[1:-1]); bv=np.digitize(va.tod.values,ed[1:-1])
        bb=np.array([r[bt==i].mean() for i in range(3)])-r.mean()
        b3=np.clip(va.pred-0.5*bb[bv],5,100)
        # warm-half-only estimate
        Tf=tr_.groupby('fold')['T'].mean(); warm=Tf[Tf>=Tf.median()].index; tw=tr_[tr_.fold.isin(warm)]
        bw=coef((tw.pred-tw.y).values,tw.tod.values)
        corw=np.clip(va.pred-0.5*(design(va.tod.values)@bw),5,100)
        n=len(va); k=int(round(.3*n)); mk=np.arange(n)<k
        res.append(dict(fam=fam,fold=fo,T=va['T'].mean(),base=fp.rmse(va.y,va.pred),
            band3=fp.rmse(va.y,b3), harm=fp.rmse(va.y,cor), harm_warm=fp.rmse(va.y,corw),
            base_pub=fp.rmse(va.y[mk],va.pred[mk]), harm_pub=fp.rmse(va.y[mk],cor[mk]),
            base_pri=fp.rmse(va.y[~mk],va.pred[~mk]), harm_pri=fp.rmse(va.y[~mk],cor[~mk])))
R=pd.DataFrame(res); C=pd.DataFrame(coefs)
print("fitted harmonic, per fold (amplitude %RH, peak hour of the correction):")
print(C.round(3).to_string(index=False))
print("\nsign stability: sin>0 in %d/18, cos<0 in %d/18 ; amplitude %.3f - %.3f"%(
    (C.sin>0).sum(),(C.cos<0).sum(),C.amp.min(),C.amp.max()))
print("corr(fold mean T, correction amplitude) = %+.3f"%C['T'].corr(C.amp))
print("\n--- gates ---")
print("vs v10 baseline: %+.4f (%d/18)   vs shipped band3: %+.4f (%d/18)"%(
    R.harm.mean()-R.base.mean(),(R.harm<R.base).sum(),R.harm.mean()-R.band3.mean(),(R.harm<R.band3).sum()))
for fam,d in R.groupby('fam'):
    print("  family %s: %+.4f (%d/%d)"%(fam,d.harm.mean()-d.base.mean(),(d.harm<d.base).sum(),len(d)))
print("  near 30%%: %+.4f (%d/18)   far 70%%: %+.4f (%d/18)"%(
    R.harm_pub.mean()-R.base_pub.mean(),(R.harm_pub<R.base_pub).sum(),
    R.harm_pri.mean()-R.base_pri.mean(),(R.harm_pri<R.base_pri).sum()))
Rs=R.sort_values('T'); c=Rs.head(9)
print("  coolest 9 folds: %+.4f (%d/9)"%((c.harm-c.base).mean(),((c.harm-c.base)<0).sum()))
print("  estimated on the WARMEST half only: all %+.4f (%d/18), coolest 9 %+.4f (%d/9)"%(
    (R.harm_warm-R.base).mean(),((R.harm_warm-R.base)<0).sum(),
    (c.harm_warm-c.base).mean(),((c.harm_warm-c.base)<0).sum()))
d=(R.harm-R.base).values; rng=np.random.default_rng(9)
bs=[rng.choice(d,len(d),replace=True).mean() for _ in range(20000)]
print("  bootstrap 95%% CI vs baseline: [%.4f, %.4f]"%(np.percentile(bs,2.5),np.percentile(bs,97.5)))
