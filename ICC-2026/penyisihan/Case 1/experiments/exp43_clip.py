"""Record clipped: 1,7% di train tapi 3,8% di test -- dua kali lipat.

Clipping memotong puncak amplitudo, dan amplitudo adalah prediktor utama magnitudo.
Sekarang `is_clipped` cuma fitur biner. Kalau modelnya bias sistematis di sana, efeknya
di test dua kali lebih besar dari yang terlihat di CV.
"""
import _path
import numpy as np, pandas as pd
import lab_common as C, lab_blend as B
from fastscore import Scorer, Post
sc=Scorer(C.EVR,np.ones(len(C.y),bool))
post=Post(C.d_tr,0.95,0.5,150,1.15,1.05)
CAND=["swA_sqrt","resA_dep","resB_dep","resB_c30","resB_p05","cnnres","cnn3_avg","cnn3_dir"]
w=np.load(C.CACHE/"w_nb9.npy")
btr=w@np.stack([B.ld(n)[0] for n in CAND]); base=post(btr)
cl=C.train.is_clipped.values.astype(bool)
wt=C.mag_weight(C.y)/C.cnt
def wmean(v,m): return float((v[m]*wt[m]).sum()/wt[m].sum())
print("n clipped train=%d (%.1f%%)  test=%d (%.1f%%)"
      %(cl.sum(),100*cl.mean(),C.test.is_clipped.sum(),100*C.test.is_clipped.mean()))
print("residual (y - pred) berbobot:  clipped=%+.4f  tidak=%+.4f"
      %(wmean(C.y-base,cl),wmean(C.y-base,~cl)))
print("MAE berbobot:                  clipped=%.4f   tidak=%.4f"
      %(wmean(np.abs(C.y-base),cl),wmean(np.abs(C.y-base),~cl)))
print("mean magnitudo:                clipped=%.3f   tidak=%.3f"%(C.y[cl].mean(),C.y[~cl].mean()))
print("\nkoreksi geser untuk record clipped:")
for s in [0.0,0.05,0.1,0.15,0.2,-0.05]:
    q=post(btr+s*cl); print("  s=%+.2f lb_real=%.4f bias=%+.3f"%(s,sc(q),C.bias_rnd(q)))
grid=[0.0,0.05,0.1,0.15,0.2,-0.05,-0.1]
Q=np.stack([post(btr+s*cl) for s in grid])
uev=np.unique(C.ev); gains=[];sel=[]
for rep in range(6):
    r=np.random.RandomState(100+rep); perm=r.permutation(uev)
    h1=np.isin(C.ev,perm[:len(perm)//2])
    for keep in (h1,~h1):
        ss=Scorer(C.EVR,keep); sh=Scorer(C.EVR,~keep)
        v=np.array([ss(q) for q in Q]); i=v.argmin()
        gains.append(sh(Q[i])-sh(base)); sel.append(grid[i])
print("gain holdout jujur %+.5f (menang %d/12) s: %s"%(np.mean(gains),sum(g<0 for g in gains),sel))
