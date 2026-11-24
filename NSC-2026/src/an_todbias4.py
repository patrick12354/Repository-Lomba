"""Does a pooled per-band correction still help on the COOLEST folds -- the ones nearest
the test window's regime?  And does it help most where the correction was estimated from
warmer folds only (the hardest version of the transfer)?"""
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
def fit_w(O):
    w,_=nnls(O[B].values,O.y.values); w=w/w.sum() if w.sum()>0 else np.ones(5)/5
    return (1-fp.BLEND_SHRINK)*w+fp.BLEND_SHRINK*np.ones(5)/5
res=[]
for fam in FAMS:
    Af=A[A.fam==fam]
    for fo in sorted(Af.fold.unique()):
        tr_=Af[Af.fold!=fo].copy(); va=Af[Af.fold==fo].copy()
        w=fit_w(tr_); e,W=fp.tod_blend_weights(tr_,w)
        for D in (tr_,va): D['pred']=np.clip(fp.apply_tod_blend(D[B].values,D.tod.values,e,W),5,100)
        tr_['res']=tr_.pred-tr_.y
        ed=np.quantile(tr_.tod.values,np.linspace(0,1,4)); ed[0],ed[-1]=-np.inf,np.inf
        bt=np.digitize(tr_.tod.values,ed[1:-1]); bv=np.digitize(va.tod.values,ed[1:-1])
        rel=np.array([tr_.res[bt==i].mean() for i in range(3)])-tr_.res.mean()
        # harder variant: estimate the correction from the WARMEST half of the other folds only
        Tf=tr_.groupby('fold')['T'].mean(); warm=Tf[Tf>=Tf.median()].index
        tw=tr_[tr_.fold.isin(warm)]; bw=np.digitize(tw.tod.values,ed[1:-1])
        relw=np.array([tw.res[bw==i].mean() for i in range(3)])-tw.res.mean()
        r=dict(fam=fam,fold=fo,T=va['T'].mean(),base=fp.rmse(va.y,va.pred))
        r['rel']  =fp.rmse(va.y,np.clip(va.pred-0.5*rel[bv],5,100))
        r['relw'] =fp.rmse(va.y,np.clip(va.pred-0.5*relw[bv],5,100))
        res.append(r)
R=pd.DataFrame(res); R['d']=R.rel-R.base; R['dw']=R.relw-R.base
R=R.sort_values('T')
print("sorted by fold mean temperature (test window = 24.6 C, cooler than all of them):")
print(R[['fam','fold','T','base','rel','d','dw']].round(4).to_string(index=False))
c=R.head(9); h=R.tail(9)
print("\ncoolest 9 folds (T %.1f-%.1f): mean delta %+.4f  (%d/9 better)"%(c['T'].min(),c['T'].max(),c.d.mean(),(c.d<0).sum()))
print("warmest 9 folds (T %.1f-%.1f): mean delta %+.4f  (%d/9 better)"%(h['T'].min(),h['T'].max(),h.d.mean(),(h.d<0).sum()))
print("\ncorr(fold temperature, gain from the correction) = %+.3f  (negative = helps MORE when cool)"%R['T'].corr(R.d))
print("\nhardest transfer -- correction estimated on the WARMEST half of the other folds only:")
print("  all 18: %+.4f (%d/18)   coolest 9: %+.4f (%d/9)"%(R.dw.mean(),(R.dw<0).sum(),c.dw.mean(),(c.dw<0).sum()))
