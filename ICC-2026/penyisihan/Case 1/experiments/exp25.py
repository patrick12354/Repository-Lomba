"""Residual OOF punya tren sistematis vs SNR (-0,083 -> +0,012) dan vs Pd (-0,089 -> +0,006).
Bisa dikoreksi? Diuji dgn protokol jujur (pilih di separuh event, ukur di separuh lain)."""
import _path  # noqa: F401  -- menaruh Case 1/ di sys.path
import numpy as np, pandas as pd
import lab_common as C
from fastscore import Scorer, Post
def ld(n):
    z=np.load(C.CACHE/f"{n}.npz"); return z["oof"],z["pte"]
OLD=["regA","swA_sqrt","resA_sqrt","resB","resB_sqrt","resB_c30","cnn_sqrt"]
w=np.load(C.CACHE/"w7_mean.npy")
raw=w@np.stack([ld(n)[0] for n in OLD])
F,_=C.get_feats()
snr=F["snr_db"].values; snr_z=(snr-snr.mean())/snr.std()
pd2=F["Pd_2"].values; pd_z=(pd2-pd2.mean())/pd2.std()
post=Post(C.d_tr,0.95,0.5,150,1.15,1.05)
sc=Scorer(C.EVR,np.ones(len(C.y),bool))
base=post(raw); print(f"baseline lb_real={sc(base):.4f} bias={C.bias_rnd(base):+.3f}")

def make(dd,dr,bs,bp):
    q=raw + bs*snr_z + bp*pd_z
    q=q + np.where(C.rnd_tr,dr,dd)
    return post(q)
grid=[(dd,dr,bs,bp) for dd in [-0.04,-0.02,0,0.02] for dr in [-0.04,-0.02,0,0.02]
      for bs in [-0.03,0,0.03] for bp in [-0.03,0,0.03]]
Q=np.stack([make(*g) for g in grid])
v=np.array([sc(q) for q in Q]); i=v.argmin()
print(f"optimum data penuh: d_dec={grid[i][0]} d_rnd={grid[i][1]} b_snr={grid[i][2]} b_pd={grid[i][3]} -> {v[i]:.4f}")
uev=np.unique(C.ev); gains=[];sel=[]
for rep in range(6):
    r=np.random.RandomState(100+rep); perm=r.permutation(uev)
    h1=np.isin(C.ev,perm[:len(perm)//2])
    for keep in (h1,~h1):
        ss=Scorer(C.EVR,keep); sh=Scorer(C.EVR,~keep)
        vv=np.array([ss(q) for q in Q]); j=vv.argmin()
        gains.append(sh(Q[j])-sh(base)); sel.append(grid[j])
print(f"gain holdout jujur: {np.mean(gains):+.5f} (menang {sum(g<0 for g in gains)}/12)")
print("parameter terpilih tiap split:", sel[:6])
