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
        d['y']=y[v].values; d['dt']=IDX[v]; d['fam']=fam; d['fold']=fi
        d['tod']=IDX[v].hour+IDX[v].minute/60
        for c in ['T','rh_tmin48','rh_q48','pressure','co2','T_rng48']: d[c]=F.loc[IDX[v],c].values
        rows.append(d)
A=pd.concat(rows,ignore_index=True)
def fit_w(O):
    w,_=nnls(O[B].values,O.y.values); w=w/w.sum() if w.sum()>0 else np.ones(5)/5
    return (1-fp.BLEND_SHRINK)*w+fp.BLEND_SHRINK*np.ones(5)/5
preds=[]
for fam in FAMS:
    Af=A[A.fam==fam]
    for fo in sorted(Af.fold.unique()):
        tr_=Af[Af.fold!=fo]; va=Af[Af.fold==fo]
        w=fit_w(tr_); e,W=fp.tod_blend_weights(tr_,w)
        preds.append(pd.Series(np.clip(fp.apply_tod_blend(va[B].values,va.tod.values,e,W),5,100),index=va.index))
A['pred']=pd.concat(preds).sort_index()
A['res']=A.pred-A.y; A['ae']=A.res.abs(); A['se']=A.res**2
print("overall LOO-blend RMSE %.4f   bias %+.3f   n=%d"%(np.sqrt(A.se.mean()),A.res.mean(),len(A)))

def tab(key,q=6,lab=None):
    b=pd.qcut(A[key],q,duplicates='drop')
    t=A.groupby(b,observed=True).agg(n=('se','size'),rmse=('se',lambda s:np.sqrt(s.mean())),
            bias=('res','mean'),share=('se','sum'))
    t['share_%']=100*t.share/A.se.sum(); return t.drop(columns='share').round(3)
for k in ['T','y','tod','T_rng48','pressure']:
    print(f"\n--- error by {k} ---"); print(tab(k).to_string())
# concentration
s=A.se.sort_values(ascending=False)
print("\nerror concentration: top 1%% of rows hold %.1f%% of total SE; top 5%%: %.1f%%; top 10%%: %.1f%%"%(
    100*s.head(int(.01*len(s))).sum()/s.sum(),100*s.head(int(.05*len(s))).sum()/s.sum(),100*s.head(int(.10*len(s))).sum()/s.sum()))
# residual autocorrelation within fold
ac=[]
for (fa,fo),d in A.groupby(['fam','fold']):
    r=d.sort_values('dt').res.values; ac.append(np.corrcoef(r[:-1],r[1:])[0,1])
print("residual lag-1 autocorr (mean over folds): %.3f"%np.mean(ac))
# how well does the physics referee cover the biggest errors
A['ref_gap']=A.pred-(0.764*A.rh_tmin48+13.11)
print("\ncorr(|error|, |pred - physics referee|) = %+.3f"%A.ae.corr(A.ref_gap.abs()))
big=A.nlargest(int(.05*len(A)),'ae')
print("top-5%% error rows: mean |pred-ref| %.2f vs %.2f for the rest"%(big.ref_gap.abs().mean(),A.ref_gap.abs().mean()))
A.to_pickle('outputs/an10_loo_oof.pkl')
