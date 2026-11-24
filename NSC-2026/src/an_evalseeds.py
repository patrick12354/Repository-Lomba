"""Controlled test: only CatBoost's seed count changes. Blend weights are fitted
leave-one-fold-out, so every score is honest."""
import numpy as np, pandas as pd, pickle, sys
sys.path.insert(0,'.'); import final_pipeline as fp
from scipy.optimize import nnls
B=fp.MODELS; S=(0,1,2)
cache=pickle.load(open('outputs/h7_oof.pkl','rb'))
cs=pickle.load(open('outputs/cat_seed_oof.pkl','rb'))
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
        if v.sum()<50 or (fam,fi,B[0],'',S) not in cache or (fam,fi) not in cs: continue
        d=pd.DataFrame({m:cache[(fam,fi,m,'',S)] for m in B})
        d['y']=y[v].values; d['tod']=IDX[v].hour+IDX[v].minute/60
        d['fam']=fam; d['fold']=fi
        P=cs[(fam,fi)]
        for m in (1,3,5,10,20): d[f'cat{m}']=P[:m].mean(0)
        rows.append(d)
A=pd.concat(rows,ignore_index=True)
print("folds %d  rows %d"%(A.groupby(['fam','fold']).ngroups,len(A)))
print("cached-cat vs recomputed cat3 (should be near-identical): RMS diff %.3f"%np.sqrt(((A.cat-A.cat3)**2).mean()))
def fit_w(O,catcol):
    M=O[[catcol if b=='cat' else b for b in B]].values
    w,_=nnls(M,O.y.values); w=w/w.sum() if w.sum()>0 else np.ones(5)/5
    return (1-fp.BLEND_SHRINK)*w+fp.BLEND_SHRINK*np.ones(5)/5
def cols(catcol): return [catcol if b=='cat' else b for b in B]
res=[]
for fam in FAMS:
    Af=A[A.fam==fam]
    for fo in sorted(Af.fold.unique()):
        tr_=Af[Af.fold!=fo]; va=Af[Af.fold==fo]
        r=dict(fam=fam,fold=fo)
        # A) weights fitted on 3-seed cat (exactly as shipped), test-time cat seed count varies
        w3=fit_w(tr_,'cat3'); e3,W3=fp.tod_blend_weights(tr_.assign(**{}).rename(columns={'cat3':'cat'}) if False else tr_.assign(cat=tr_.cat3), w3)
        for m in (1,3,5,10,20):
            Pm=va[cols(f'cat{m}')].values
            r[f'glob{m}']=fp.rmse(va.y,np.clip(Pm@w3,5,100))
            r[f'tod{m}'] =fp.rmse(va.y,np.clip(fp.apply_tod_blend(Pm,va.tod.values,e3,W3),5,100))
        # B) weights ALSO refitted on 20-seed cat
        w20=fit_w(tr_,'cat20'); e20,W20=fp.tod_blend_weights(tr_.assign(cat=tr_.cat20), w20)
        P20=va[cols('cat20')].values
        r['glob20_rw']=fp.rmse(va.y,np.clip(P20@w20,5,100))
        r['tod20_rw'] =fp.rmse(va.y,np.clip(fp.apply_tod_blend(P20,va.tod.values,e20,W20),5,100))
        r['w20_cat']=w20[1]; r['w3_cat']=w3[1]
        res.append(r)
R=pd.DataFrame(res)
print("\n=== mean LOO CV RMSE (18 folds) ===")
base=R.tod5.mean()
for c in ['glob3','glob5','glob10','glob20','tod3','tod5','tod10','tod20','glob20_rw','tod20_rw']:
    print(f"  {c:11s} {R[c].mean():.4f}   vs shipped tod5: {R[c].mean()-base:+.4f}   folds better: {(R[c]<R.tod5).sum()}/{len(R)}")
print("\ncat blend weight: fitted on 3-seed %.3f  -> on 20-seed %.3f"%(R.w3_cat.mean(),R.w20_cat.mean()))
print("\ntod-blend advantage (tod - glob) at each seed count:")
for m in (3,5,10,20): print(f"  {m:2d} seeds: {(R[f'tod{m}']-R[f'glob{m}']).mean():+.4f}  ({(R[f'tod{m}']<R[f'glob{m}']).sum()}/{len(R)} folds)")
print("\nper-fold, shipped tod5 -> tod20:")
print(R[['fam','fold','tod5','tod20','tod20_rw']].assign(d=R.tod20-R.tod5).round(4).to_string(index=False))
R.to_csv('outputs/exp_seedcount.csv',index=False)
