"""Koreksi ekor: p' = p + c*max(0, p - t). Dipilih & diukur dengan split by event."""
import _path  # noqa: F401  -- menaruh Case 1/ di sys.path
import numpy as np, pandas as pd
import lab_common as C
from fastscore import Scorer, Post
w=np.load(C.CACHE/"w7_mean.npy")
OLD=["regA","swA_sqrt","resA_sqrt","resB","resB_sqrt","resB_c30","cnn_sqrt"]
raw=w@np.stack([np.load(C.CACHE/f"{n}.npz")["oof"] for n in OLD])
rawt=w@np.stack([np.load(C.CACHE/f"{n}.npz")["pte"] for n in OLD])
po=Post(C.d_tr,0.95,0.5,150,1.15,1.05); pt=Post(C.d_te,0.95,0.5,150,1.15,1.05)
base=po(raw); baset=pt(rawt)
sc=Scorer(C.EVR,np.ones(len(C.y),bool))
print(f"baseline lb_real={sc(base):.4f} bias={C.bias_rnd(base):+.3f}")
# lihat ekor lebih halus
wt=C.mag_weight(C.y)/C.cnt
top=base>5.7
q=pd.qcut(base[top],5,duplicates="drop"); yy=C.y[top]; ww=wt[top]; bb=base[top]
def wmed(y,w):
    o=np.argsort(y); y,w=y[o],w[o]; c=np.cumsum(w); return y[np.searchsorted(c,c[-1]/2)]
print("\ndetail ekor (prediksi > 5,7):")
for k,idx in pd.Series(range(top.sum())).groupby(q,observed=True):
    i=idx.values
    print(f"  pred~{bb[i].mean():.2f} n={len(i):4d} y_wmedian={wmed(yy[i],ww[i]):.2f} koreksi={wmed(yy[i],ww[i])-bb[i].mean():+.3f}")
grid=[(t,c) for t in [5.4,5.6,5.8,6.0] for c in [0.0,0.1,0.2,0.35,0.5]]
def lift(p,t,c): return p + c*np.maximum(0.0,p-t)
Q=np.stack([lift(base,*g) for g in grid])
v=np.array([sc(q) for q in Q]); i=v.argmin()
print(f"\noptimum data penuh: t={grid[i][0]} c={grid[i][1]} -> lb_real {v[i]:.4f} (dari {sc(base):.4f})")
uev=np.unique(C.ev); gains=[];sel=[]
for rep in range(6):
    r=np.random.RandomState(100+rep); perm=r.permutation(uev)
    h1=np.isin(C.ev,perm[:len(perm)//2])
    for keep in (h1,~h1):
        ss=Scorer(C.EVR,keep); sh=Scorer(C.EVR,~keep)
        vv=np.array([ss(q) for q in Q]); j=vv.argmin()
        gains.append(sh(Q[j])-sh(base)); sel.append(grid[j])
print(f"gain holdout jujur: {np.mean(gains):+.5f} (menang {sum(g<0 for g in gains)}/12)")
print("parameter terpilih:", sel)
t,c=grid[i]
print(f"\nefek di test (t={t}, c={c}):")
lt=lift(baset,t,c)
print(f"  mean subset bulat<100: {baset[C.MT].mean():.3f} -> {lt[C.MT].mean():.3f}")
print(f"  sd sisi bulat:         {baset[C.rnd_te].std():.3f} -> {lt[C.rnd_te].std():.3f}")
print(f"  bias_rnd OOF:          {C.bias_rnd(base):+.3f} -> {C.bias_rnd(lift(base,t,c)):+.3f}")
print(f"  n record test terkena: {(baset>t).sum()} dari 2300")
