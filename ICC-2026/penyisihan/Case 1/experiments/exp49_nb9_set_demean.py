"""exp49 — bangun notebook_9: koreksi set-transformer Kaggle, di-demean per subset
saat apply. Demean di dalam training tidak cukup; model memulihkan prior katalog
lewat fitur (mean koreksi di MR +0,0556). Demean ulang saat apply menahan bias_rnd
di +0,029 dengan ongkos 0,0004 lb_real. Hasil: lb_real 0,1718, gain -0,0042, 12/12."""
import sys, os, json, numpy as np, pandas as pd
sys.path.insert(0, os.path.abspath("lab"))
import lab_common as C
from fastscore import Scorer, Post
post_tr=Post(C.d_tr,0.95,0.5,150,1.15,1.05); post_te=Post(C.d_te,0.95,0.5,150,1.15,1.05)
sc=Scorer(C.EVR,np.ones(len(C.y),bool))
R=np.load("belum_run/ref/nb8_ref.npz",allow_pickle=True)
CAND=[str(x) for x in R["__cand__"]]
btr=R["__w__"]@np.stack([R[f"{n}__oof"].astype(np.float64) for n in CAND])
bte=R["__w__"]@np.stack([R[f"{n}__pte"].astype(np.float64) for n in CAND])
base=post_tr(btr)
def dm(c,r):
    c=c.copy()
    for m in (r,~r): c[m]-=c[m].mean()
    return c
Z=np.load("cache/set2.npz")
ctr=dm(Z["corr"].astype(np.float64),C.rnd_tr); cte=dm(Z["cte"].astype(np.float64),C.rnd_te)
grid=[0.0,0.1,0.15,0.2,0.25,0.3,0.4,0.5,0.6,0.75]
Q=np.stack([post_tr(btr+l*ctr) for l in grid])
uev=np.unique(C.ev); sel=[]; gains=[]
for rep in range(6):
    h1=np.isin(C.ev,np.random.RandomState(100+rep).permutation(uev)[:len(uev)//2])
    for keep in (h1,~h1):
        ss=Scorer(C.EVR,keep); sh=Scorer(C.EVR,~keep)
        v=np.array([ss(q) for q in Q]); i=int(v.argmin())
        sel.append(grid[i]); gains.append(sh(Q[i])-sh(base))
lam=float(np.median(sel))
print("lam terpilih (median 12 belahan) =",lam," sebaran:",sorted(sel))
o=post_tr(btr+lam*ctr); p=post_te(bte+lam*cte)
res=dict(lam=lam, lb_real=float(sc(o)), dec=C.part_real(o,True), rnd=C.part_real(o,False),
         gain=float(np.mean(gains)), menang=int(sum(g<0 for g in gains)),
         bias_rnd=C.bias_rnd(o), mean_rnd_te=float(p[C.MT].mean()),
         sd_rnd_te=float(p[C.rnd_te].std()), est_lb=float(sc(o))+0.0082,
         basis="notebook_8 blend + koreksi set-transformer DI-DEMEAN per subset saat apply")
print(json.dumps(res,indent=2))
sub=pd.read_csv("submission/notebook_8.csv")
sub["magnitude"]=np.round(p,3)
sub.to_csv("submission/notebook_9.csv",index=False)
json.dump(res,open("submission/notebook_9_score.json","w"),indent=2)
np.savez("cache/blend_nb9.npz", oof=o, pte=p, lam=lam)
print("tertulis: submission/notebook_9.csv")
