"""Diagnostik koreksi set-transformer: apakah gain-nya nyata atau sekadar pergeseran?"""
import _path
import numpy as np, pandas as pd
import lab_common as C
from fastscore import Scorer, Post
import lab_blend as B
sc=Scorer(C.EVR,np.ones(len(C.y),bool))
post=Post(C.d_tr,0.95,0.5,150,1.15,1.05)
CAND=["swA_sqrt","resA_dep","resB_dep","resB_c30","resB_p05","cnnres","cnn3_avg","cnn3_dir"]
w=np.load(C.CACHE/"w_nb9.npy")
blend=w@np.stack([B.ld(n)[0] for n in CAND])
base=post(blend)
corr=np.load(C.CACHE/"set_corr.npy")
print("koreksi: mean=%+.4f sd=%.4f | pada MR(bulat<100): mean=%+.4f | desimal: mean=%+.4f"
      %(corr.mean(),corr.std(),corr[C.MR].mean(),corr[~C.rnd_tr].mean()))
print("korelasi koreksi vs residual sejati: %.3f"%np.corrcoef(corr,C.y-blend)[0,1])
print("  di MR saja: %.3f"%np.corrcoef(corr[C.MR],(C.y-blend)[C.MR])[0,1])

# kalau gain-nya cuma pergeseran rata-rata, versi ter-demean harus kehilangan gain
cd=corr.copy()
cd[C.rnd_tr]-=corr[C.rnd_tr].mean(); cd[~C.rnd_tr]-=corr[~C.rnd_tr].mean()
print("\nlam | penuh          | koreksi di-demean per subset")
for lam in [0.15,0.30,0.50]:
    q=post(blend+lam*corr); qd=post(blend+lam*cd)
    print("%.2f | %.4f b=%+.3f | %.4f b=%+.3f"%(lam,sc(q),C.bias_rnd(q),sc(qd),C.bias_rnd(qd)))

# ---- seleksi lam JUJUR: pilih di separuh event, ukur di separuh lain
grid=[0.0,0.1,0.15,0.2,0.25,0.3,0.4,0.5,0.6]
Q=np.stack([post(blend+l*corr) for l in grid])
Qd=np.stack([post(blend+l*cd) for l in grid])
uev=np.unique(C.ev)
for nm,QQ in (("penuh",Q),("demean",Qd)):
    gains=[];sel=[]
    for rep in range(6):
        r=np.random.RandomState(100+rep); perm=r.permutation(uev)
        h1=np.isin(C.ev,perm[:len(perm)//2])
        for keep in (h1,~h1):
            ss=Scorer(C.EVR,keep); sh=Scorer(C.EVR,~keep)
            v=np.array([ss(q) for q in QQ]); i=v.argmin()
            gains.append(sh(QQ[i])-sh(base)); sel.append(grid[i])
    print("\n[%s] gain holdout jujur %+.5f (menang %d/12)  lam terpilih: %s"
          %(nm,np.mean(gains),sum(g<0 for g in gains),sel))
