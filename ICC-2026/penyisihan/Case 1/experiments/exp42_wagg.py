"""Agregasi grup berbobot presisi, bukan median buta.

Setelah smoothing, seluruh record satu grup memakai satu nilai c, dan errornya |y - c|.
Jadi c seharusnya penduga TERBAIK dari y berdasarkan grup itu -- dan record tidak
sama kualitasnya: SNR tinggi, jarak dekat, tidak clipped = prediksi lebih dipercaya.
Median memperlakukan semuanya sama rata. Belum pernah diuji di repo ini.
"""
import _path
import numpy as np, pandas as pd
import lab_common as C, lab_blend as B
from fastscore import Scorer

sc=Scorer(C.EVR,np.ones(len(C.y),bool))
CAND=["swA_sqrt","resA_dep","resB_dep","resB_c30","resB_p05","cnnres","cnn3_avg","cnn3_dir"]
w=np.load(C.CACHE/"w_nb9.npy")
btr=w@np.stack([B.ld(n)[0] for n in CAND])
Ftr,_=C.get_feats()
snr=Ftr["snr_db"].values.astype(np.float64)
dist=Ftr["logdist"].values.astype(np.float64)
clip=Ftr["is_clipped"].values.astype(np.float64)
snr_z=(snr-snr.mean())/snr.std(); dist_z=(dist-dist.mean())/dist.std()

def agg_post(p, dep, rw, lam_dec=0.95, lam_deep=0.5, T_deep=150, a_dec=1.15, a_rnd=1.05):
    r=np.isclose(dep,np.round(dep))
    df=pd.DataFrame({"p":p,"w":rw,"d":dep})
    df["pw"]=df.p*df.w
    g=df.groupby("d")[["pw","w"]].transform("sum")
    gm=(g.pw/g.w).values
    lam=np.where(~r,lam_dec,np.where(dep>=T_deep,lam_deep,0.0))
    q=(1-lam)*p+lam*gm
    out=q.copy()
    for m,a in ((r,a_rnd),(~r,a_dec)):
        mu=q[m].mean(); out[m]=mu+a*(q[m]-mu)
    return out

from fastscore import Post
base=Post(C.d_tr,0.95,0.5,150,1.15,1.05)(btr)
print("acuan (median): lb_real=%.4f dec=%.4f"%(sc(base),C.part_real(base,True)))
print("agregasi rata-rata rata (a=b=c=0):", "%.4f"%sc(agg_post(btr,C.d_tr,np.ones(len(btr)))))
best=None; rows=[]
for a in [0.0,0.15,0.3,0.5,0.8]:
    for b in [0.0,0.15,0.3,0.5]:
        for c in [0.0,1.0,2.0]:
            rw=np.exp(a*snr_z - b*dist_z - c*clip)
            q=agg_post(btr,C.d_tr,rw); v=sc(q)
            rows.append((v,a,b,c,C.part_real(q,True),C.bias_rnd(q)))
rows.sort()
print("\n5 terbaik (a=bobot snr, b=penalti jarak, c=penalti clipped):")
for v,a,b,c,dec,bi in rows[:5]:
    print("  a=%.2f b=%.2f c=%.1f  lb_real=%.4f dec=%.4f bias=%+.3f"%(a,b,c,v,dec,bi))
# seleksi jujur
grid=[(a,b,c) for a in [0.0,0.15,0.3,0.5,0.8] for b in [0.0,0.15,0.3,0.5] for c in [0.0,1.0,2.0]]
Q=np.stack([agg_post(btr,C.d_tr,np.exp(a*snr_z-b*dist_z-c*clip)) for a,b,c in grid])
uev=np.unique(C.ev); gains=[];sel=[]
for rep in range(6):
    r=np.random.RandomState(100+rep); perm=r.permutation(uev)
    h1=np.isin(C.ev,perm[:len(perm)//2])
    for keep in (h1,~h1):
        ss=Scorer(C.EVR,keep); sh=Scorer(C.EVR,~keep)
        v=np.array([ss(q) for q in Q]); i=v.argmin()
        gains.append(sh(Q[i])-sh(base)); sel.append(grid[i])
print("\ngain holdout jujur %+.5f (menang %d/12)"%(np.mean(gains),sum(g<0 for g in gains)))
print("parameter terpilih:",sel)
