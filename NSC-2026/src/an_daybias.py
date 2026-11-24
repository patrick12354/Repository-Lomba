"""I killed the physics referee in s66c on a ROW-level correlation (+0.003). That answers
'can it localise individual errors' -- not 'can it detect a day-level systematic bias',
which is a different question and the one that matters for a 10-day private slice."""
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
        d['y']=y[v].values; d['tod']=IDX[v].hour+IDX[v].minute/60; d['dt']=IDX[v]
        d['fam']=fam; d['fold']=fi
        for c in ['rh_q48','rh_tmin48','T']: d[c]=F.loc[IDX[v],c].values
        rows.append(d)
A=pd.concat(rows,ignore_index=True)
def fit_w(O):
    w,_=nnls(O[B].values,O.y.values); w=w/w.sum() if w.sum()>0 else np.ones(5)/5
    return (1-fp.BLEND_SHRINK)*w+fp.BLEND_SHRINK*np.ones(5)/5
def dz(t): 
    t=2*np.pi*np.asarray(t)/24; return np.column_stack([np.sin(t),np.cos(t)])
preds=[]
for fam in FAMS:
    Af=A[A.fam==fam]
    for fo in sorted(Af.fold.unique()):
        tr_=Af[Af.fold!=fo].copy(); va=Af[Af.fold==fo]
        w=fit_w(tr_); e,W=fp.tod_blend_weights(tr_,w)
        tr_['pred']=np.clip(fp.apply_tod_blend(tr_[B].values,tr_.tod.values,e,W),5,100)
        b=np.linalg.lstsq(np.c_[np.ones(len(tr_)),dz(tr_.tod.values)],(tr_.pred-tr_.y).values,rcond=None)[0][1:]
        p=np.clip(fp.apply_tod_blend(va[B].values,va.tod.values,e,W),5,100)
        preds.append(pd.Series(np.clip(p-0.5*(dz(va.tod.values)@b),5,100),index=va.index))
A['pred']=pd.concat(preds).sort_index()
# referee calibrated on TRAIN rows only (as the pipeline would)
cal={}
for c in ['rh_q48','rh_tmin48']:
    x=F.loc[idx,c].values; t=y.loc[idx].values; m=np.isfinite(x)&np.isfinite(t)
    cal[c]=np.polyfit(x[m],t[m],1)
A['ref']=np.mean([np.polyval(cal[c],A[c].values) for c in cal],0)
A['gap']=A.pred-A.ref; A['err']=A.pred-A.y
print("ROW level:   corr(gap, error) = %+.3f    corr(|gap|,|error|) = %+.3f"%(
    A.gap.corr(A.err), A.gap.abs().corr(A.err.abs())))
A['day']=A.dt.dt.date
D=A.groupby(['fam','fold','day']).agg(gap=('gap','mean'),err=('err','mean'),n=('err','size'),
                                      T=('T','mean')).query('n>=40').reset_index()
print("DAY level:   corr(gap, bias) = %+.3f   n=%d fold-days"%(D.gap.corr(D.err),len(D)))
import numpy.linalg as la
X=np.c_[np.ones(len(D)),D.gap]; b,*_=la.lstsq(X,D.err.values,rcond=None)
r2=1-((D.err-X@b)**2).sum()/((D.err-D.err.mean())**2).sum()
print("             bias = %.3f + %.3f * gap    R2 = %.3f"%(b[0],b[1],r2))
print("             residual sd of day bias: %.2f  (raw sd %.2f)"%(
    (D.err-X@b).std(), D.err.std()))
# same at 3-day resolution
A['blk']=A.dt.dt.floor('3D')
E=A.groupby(['fam','fold','blk']).agg(gap=('gap','mean'),err=('err','mean'),n=('err','size')).query('n>=100').reset_index()
print("3-DAY level: corr(gap, bias) = %+.3f   n=%d"%(E.gap.corr(E.err),len(E)))
# read it off on the real test window
te=IDX[(g.is_test==1).values]
ref_te=np.mean([np.polyval(cal[c],F.loc[te,c].values) for c in cal],0)
for nm in ['v8_qblock','v10_todblend','v11_seed5','v12_harmbias']:
    p=pd.read_csv(f'outputs/submissions/{nm}.csv',parse_dates=['datetime']).set_index('datetime')['air_humidity'].reindex(te).values
    gp=pd.Series(p-ref_te,index=te)
    pub,pri=gp[:220].mean(),gp[220:].mean()
    print("  %-13s mean gap: public %+6.2f -> implied bias %+5.2f | private %+6.2f -> implied bias %+5.2f"%(
        nm,pub,b[0]+b[1]*pub,pri,b[0]+b[1]*pri))
gp=pd.Series(pd.read_csv('outputs/submissions/v11_seed5.csv',parse_dates=['datetime']).set_index('datetime')['air_humidity'].reindex(te).values-ref_te,index=te)
print("\nv11 gap by day (implied day-level bias in brackets):")
for d,vv in gp.groupby(gp.index.date).mean().items():
    print("  %s  gap %+6.2f   implied bias %+5.2f"%(d,vv,b[0]+b[1]*vv))
