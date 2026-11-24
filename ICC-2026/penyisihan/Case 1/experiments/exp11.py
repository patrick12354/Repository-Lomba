"""Validasi soft grouping di sisi desimal dengan depth DISEMBUNYIKAN."""
import _path  # noqa: F401  -- menaruh Case 1/ di sys.path
import numpy as np, pandas as pd
from sklearn.model_selection import GroupKFold
from sklearn.metrics import roc_auc_score
import lab_common as C, lab_group as G

Ftr,_=C.get_feats()
w=np.load(C.CACHE/"w_full.npy")
CAND=["regA","regB","resA","resB","swA_sqrt"]
O=np.stack([np.load(C.CACHE/f"{n}.npz")["oof"] for n in CAND]); base=w@O

dec=~C.rnd_tr; idx=np.where(dec)[0]
dep=C.d_tr[idx]; band=np.floor(dep/12).astype(int)
PF=G.PairFeat(Ftr, base)
rng=np.random.RandomState(0)
uev=np.unique(C.ev[idx])

def ev_score(p, sel):
    m=np.zeros(len(C.y),bool); m[idx[sel]]=True
    return C.eb_twmae(C.y[m],p[m],C.ev[m])

res={}
oof_soft=base.copy()
for f,(ti,vi) in enumerate(GroupKFold(3).split(idx,None,C.ev[idx])):
    pools_tr=[idx[ti][band[ti]==b] for b in np.unique(band[ti])]
    I,J,lab=G.sample_pairs(pools_tr, C.ev, rng)
    clf=G.train_pair_clf(PF,I,J,lab)
    pools_va=[idx[vi][band[vi]==b] for b in np.unique(band[vi])]
    Iv,Jv,lv=G.sample_pairs(pools_va,C.ev,np.random.RandomState(1))
    auc=roc_auc_score(lv,clf.predict_proba(PF(Iv,Jv))[:,1])
    res[f]=(clf,pools_va,vi,auc)
    print(f"fold{f}: AUC_holdout={auc:.4f} n_pool={len(pools_va)} n_rec={len(vi)}", flush=True)

print(f"\nbaseline (tanpa smoothing) dec={np.mean([ev_score(base,r[2]) for r in res.values()]):.4f}")
# oracle: smoothing pakai depth asli (=event asli)
orc=base.copy()
gm=pd.Series(base).groupby(pd.Series(C.d_tr)).transform("median").values
orc[idx]=gm[idx]
print(f"oracle (smoothing by depth asli) dec={np.mean([ev_score(orc,r[2]) for r in res.values()]):.4f}")
print(f"\n{'lam':>5}{'gamma':>7}{'topk':>6}{'dec_score':>11}{'% oracle direbut':>18}")
b0=np.mean([ev_score(base,r[2]) for r in res.values()])
b1=np.mean([ev_score(orc,r[2]) for r in res.values()])
for lam in [0.4,0.6,0.8,1.0]:
    for gamma in [1.0,3.0,6.0]:
        for topk in [8,15,None]:
            sc=[]
            for f,(clf,pools,vi,_) in res.items():
                q=G.soft_smooth(base,PF,clf,pools,lam,gamma,topk)
                sc.append(ev_score(q,vi))
            s=np.mean(sc)
            print(f"{lam:5.1f}{gamma:7.1f}{str(topk):>6}{s:11.4f}{(b0-s)/(b0-b1)*100:17.1f}%", flush=True)
