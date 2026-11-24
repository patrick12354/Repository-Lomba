"""Varian terakhir grouping: hanya pasangan berkeyakinan sangat tinggi (threshold keras)."""
import _path  # noqa: F401  -- menaruh Case 1/ di sys.path
import numpy as np, pandas as pd
from sklearn.model_selection import GroupKFold
import lab_common as C, lab_group as G
Ftr,_=C.get_feats()
w=np.load(C.CACHE/"w_full.npy"); CAND=["regA","regB","resA","resB","swA_sqrt"]
base=w@np.stack([np.load(C.CACHE/f"{n}.npz")["oof"] for n in CAND])
dec=~C.rnd_tr; idx=np.where(dec)[0]; band=np.floor(C.d_tr[idx]/12).astype(int)
PF=G.PairFeat(Ftr,base); rng=np.random.RandomState(0)
def ev_score(p,vi):
    m=np.zeros(len(C.y),bool); m[idx[vi]]=True
    return C.eb_twmae(C.y[m],p[m],C.ev[m])
folds=[]
for ti,vi in GroupKFold(3).split(idx,None,C.ev[idx]):
    pools_tr=[idx[ti][band[ti]==b] for b in np.unique(band[ti])]
    I,J,lab=G.sample_pairs(pools_tr,C.ev,rng)
    folds.append((G.train_pair_clf(PF,I,J,lab),[idx[vi][band[vi]==b] for b in np.unique(band[vi])],vi))
b0=np.mean([ev_score(base,f[2]) for f in folds])
print(f"baseline dec={b0:.4f}  oracle=0.1584")
def hard(p,PF,clf,pools,t,lam,maxn=6):
    out=p.copy()
    for wpool in pools:
        n=len(wpool)
        if n<3: continue
        Pm=np.empty((n,n),dtype=np.float32)
        for s in range(0,n,400):
            e=min(s+400,n); I=np.repeat(wpool[s:e],n); J=np.tile(wpool,e-s)
            Pm[s:e]=clf.predict_proba(PF(I,J))[:,1].reshape(e-s,n)
        Pm=(Pm+Pm.T)/2; np.fill_diagonal(Pm,1.0)
        M=(Pm>=t).astype(np.float32); np.fill_diagonal(M,1.0)
        cntM=M.sum(1); too=cntM>maxn
        if too.any():
            for i in np.where(too)[0]:
                keep=np.argsort(-Pm[i])[:maxn]; M[i]=0; M[i,keep]=1; M[i,i]=1
        sm=(M@p[wpool])/M.sum(1)
        out[wpool]=(1-lam)*p[wpool]+lam*sm
    return out
print(f"{'t':>6}{'lam':>6}{'maxn':>6}{'dec':>10}{'%oracle':>9}{'presisi_pasangan':>18}")
for t in [0.5,0.7,0.85,0.95]:
    # presisi pasangan di atas threshold (holdout)
    prec=[]
    for clf,pools,vi in folds:
        Iv,Jv,lv=G.sample_pairs(pools,C.ev,np.random.RandomState(2))
        pr=clf.predict_proba(PF(Iv,Jv))[:,1]; m=pr>=t
        prec.append(lv[m].mean() if m.sum()>20 else np.nan)
    for lam in [0.6,1.0]:
        for maxn in [3,6]:
            sc=np.mean([ev_score(hard(base,PF,clf,pools,t,lam,maxn),vi) for clf,pools,vi in folds])
            print(f"{t:6.2f}{lam:6.1f}{maxn:6d}{sc:10.4f}{(b0-sc)/(b0-0.1584)*100:8.1f}%{np.nanmean(prec):18.3f}",flush=True)
