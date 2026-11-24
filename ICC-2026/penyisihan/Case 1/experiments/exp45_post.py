"""Sapuan GABUNGAN parameter post-processing di bawah metrik terkoreksi.

Setelan (lam_dec 0,95 / lam_deep 0,5 / T_deep 150 / a_dec 1,15 / a_rnd 1,05) diwarisi dari
notebook_6. Model dasarnya sudah berubah banyak sejak itu (CNN v3 masuk dengan bobot 0,53),
jadi optimumnya belum tentu masih di sana. nb8 hanya menyapu a_rnd sendirian.
Ditambah: kuantil agregasi grup, bukan median tepat.
"""
import _path
import numpy as np, pandas as pd, itertools
import lab_common as C, lab_blend as B
from fastscore import Scorer
sc=Scorer(C.EVR,np.ones(len(C.y),bool))
CAND=["swA_sqrt","resA_dep","resB_dep","resB_c30","resB_p05","cnnres","cnn3_avg","cnn3_dir"]
w=np.load(C.CACHE/"w_nb9.npy")
btr=w@np.stack([B.ld(n)[0] for n in CAND])

class PostQ:
    def __init__(s,dep,lam_dec,lam_deep,T_deep,a_dec,a_rnd,q=0.5):
        r=np.isclose(dep,np.round(dep))
        s.lam=np.where(~r,lam_dec,np.where(dep>=T_deep,lam_deep,0.0))
        o=np.argsort(dep,kind="stable"); s.o=o
        ds=dep[o]; bnd=np.flatnonzero(np.diff(ds))+1
        s.sl=np.concatenate([[0],bnd,[len(ds)]]); s.r=r; s.ad=a_dec; s.ar=a_rnd; s.q=q
    def __call__(s,p):
        ps=p[s.o]; gm=np.empty_like(ps)
        for i in range(len(s.sl)-1):
            gm[s.sl[i]:s.sl[i+1]]=np.quantile(ps[s.sl[i]:s.sl[i+1]],s.q)
        g=np.empty_like(p); g[s.o]=gm
        q=(1-s.lam)*p+s.lam*g; out=q.copy()
        for m,a in ((s.r,s.ar),(~s.r,s.ad)):
            mu=q[m].mean(); out[m]=mu+a*(q[m]-mu)
        return out

base=PostQ(C.d_tr,0.95,0.5,150,1.15,1.05)(btr)
print("acuan nb8 lb_real=%.4f"%sc(base))
grid=list(itertools.product([0.85,0.95,1.0],[0.3,0.5,0.7],[120,150,200],
                            [1.05,1.15,1.25],[0.95,1.05,1.15],[0.45,0.5,0.55]))
print("n konfigurasi",len(grid))
Q=np.stack([PostQ(C.d_tr,*g)(btr) for g in grid])
v=np.array([sc(q) for q in Q]); i=v.argmin()
print("optimum data penuh: %s -> %.4f (dari %.4f)"%(str(grid[i]),v[i],sc(base)))
uev=np.unique(C.ev); gains=[];sel=[]
for rep in range(6):
    r=np.random.RandomState(100+rep); perm=r.permutation(uev)
    h1=np.isin(C.ev,perm[:len(perm)//2])
    for keep in (h1,~h1):
        ss=Scorer(C.EVR,keep); sh=Scorer(C.EVR,~keep)
        vv=np.array([ss(q) for q in Q]); j=vv.argmin()
        gains.append(sh(Q[j])-sh(base)); sel.append(grid[j])
print("gain holdout jujur %+.5f (menang %d/12)"%(np.mean(gains),sum(g<0 for g in gains)))
S=pd.DataFrame(sel,columns=["lam_dec","lam_deep","T_deep","a_dec","a_rnd","q"])
print(S.median().to_dict())
print(S.to_string())
