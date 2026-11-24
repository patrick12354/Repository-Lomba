"""Does a public-30% ranking predict the private-70% ranking?
Many candidate models, all scored on the SAME slices of the same fold -- which is how a
leaderboard actually works."""
import numpy as np, pandas as pd, pickle, sys
sys.path.insert(0,'.'); import final_pipeline as fp
from scipy.optimize import nnls
from scipy.stats import spearmanr
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
rng=np.random.default_rng(7)
WPERT=[rng.dirichlet(np.ones(5)*3) for _ in range(14)]
recs=[]; pairs=[]
for fam in FAMS:
    Af=A[A.fam==fam]
    for fo in sorted(Af.fold.unique()):
        tr_=Af[Af.fold!=fo]; va=Af[Af.fold==fo].reset_index(drop=True)
        w=fit_w(tr_); e,W=fp.tod_blend_weights(tr_,w)
        P=va[B].values
        cand={'blend_glob':P@w,'blend_tod':fp.apply_tod_blend(P,va.tod.values,e,W)}
        for m in B: cand[m]=va[m].values
        for i,wp in enumerate(WPERT): cand[f'p{i}']=P@wp
        n=len(va); k=int(round(0.30*n)); mk=np.arange(n)<k
        sc={c:(fp.rmse(va.y[mk],np.clip(p,5,100)[mk]),fp.rmse(va.y[~mk],np.clip(p,5,100)[~mk]),
               fp.rmse(va.y,np.clip(p,5,100))) for c,p in cand.items()}
        s=pd.DataFrame(sc,index=['pub','pri','all']).T
        recs.append(dict(fam=fam,fold=fo,rho=spearmanr(s.pub,s.pri).statistic,
                         rho_pub_all=spearmanr(s.pub,s['all']).statistic,
                         rho_pri_all=spearmanr(s.pri,s['all']).statistic))
        nm=list(s.index)
        for i in range(len(nm)):
            for j in range(len(nm)):
                if i>=j: continue
                pairs.append((s.pub[nm[i]]-s.pub[nm[j]], s.pri[nm[i]]-s.pri[nm[j]], s['all'][nm[i]]-s['all'][nm[j]]))
D=pd.DataFrame(recs); Pr=pd.DataFrame(pairs,columns=['dpub','dpri','dall'])
print("Spearman rank correlation of %d candidate models, within fold:"%(2+len(B)+len(WPERT)))
print("  public30 vs private70 : mean %+.3f  median %+.3f  (min %+.3f max %+.3f)"%(D.rho.mean(),D.rho.median(),D.rho.min(),D.rho.max()))
print("  public30 vs whole     : mean %+.3f"%D.rho_pub_all.mean())
print("  private70 vs whole    : mean %+.3f"%D.rho_pri_all.mean())
print("\nGiven model X looks better than Y on the public 30%% by delta, P(X really is better on private 70%%):")
for lo,hi in [(0.0,0.05),(0.05,0.10),(0.10,0.20),(0.20,0.40),(0.40,1.0),(1.0,99)]:
    m=(Pr.dpub.abs()>=lo)&(Pr.dpub.abs()<hi)
    if m.sum()<50: continue
    agree=(np.sign(Pr.dpub[m])==np.sign(Pr.dpri[m])).mean()
    agree_all=(np.sign(Pr.dpub[m])==np.sign(Pr.dall[m])).mean()
    print(f"  public gap {lo:.2f}-{hi:.2f}: P(same sign on private) = {agree:.2f}   "
          f"P(same sign on the whole window) = {agree_all:.2f}   n={m.sum()}")
print("\nper fold rho(public,private):"); print(D[['fam','fold','rho']].round(3).to_string(index=False))
