"""Sidik derau pre-P sebagai sinyal co-membership -> smoothing tetangga di sisi depth-bulat.

exp37 menunjukkan record satu event mengumpul di klaster derau yang sama jauh di atas
peluang acak. Di sini: (1) ukur AUC pasangan secara jujur, (2) pakai untuk smoothing
tetangga-terdekat DI DALAM grup depth-bulat, tempat median grup buta selama ini dipakai
atau tidak dipakai sama sekali.

Kunci vs nb7: jarak derau tidak memakai prediksi magnitudo sama sekali, jadi ia bisa
yakin untuk pasangan yang prediksinya BERBEDA -- justru pasangan yang berguna.
"""
import _path
import numpy as np, pandas as pd
import lab_common as C
from fastscore import Scorer, Post
import lab_blend as B

z=np.load(C.CACHE/"noisefp.npz"); Ztr=z["Ztr"]; Zte=z["Zte"]
Ztr=Ztr/np.linalg.norm(Ztr,axis=1,keepdims=True)
Zte=Zte/np.linalg.norm(Zte,axis=1,keepdims=True)
sc=Scorer(C.EVR,np.ones(len(C.y),bool))
base=B.nb8_ref()
print("acuan nb8: lb_real=%.4f dec=%.4f rnd=%.4f"%(sc(base),C.part_real(base,True),C.part_real(base,False)))

# ---- 1. AUC pasangan, sisi desimal (grup = event nyata), hanya pasangan SEDEPTH-mirip
dec=np.where(~C.rnd_tr)[0]
rs=np.random.RandomState(0)
sub=rs.choice(dec,3000,replace=False)
S=Ztr[sub]@Ztr[sub].T
same=(C.ev[sub][:,None]==C.ev[sub][None,:])
iu=np.triu_indices(len(sub),1)
s=S[iu]; lab=same[iu]
from sklearn.metrics import roc_auc_score
print("AUC co-membership dari jarak derau saja: %.4f  (n_pos=%d)"%(roc_auc_score(lab,s),lab.sum()))
# pembanding: AUC dari kemiripan prediksi
sp=-np.abs(base[sub][:,None]-base[sub][None,:])[iu]
print("AUC dari kemiripan prediksi saja     : %.4f"%roc_auc_score(lab,sp))
print("AUC gabungan (jumlah z-score)        : %.4f"
      %roc_auc_score(lab,(s-s.mean())/s.std()+(sp-sp.mean())/sp.std()))

# ---- 2. smoothing tetangga di dalam grup depth
def nbr_smooth(p, Z, dep, k=8, lam=0.4, only_rnd=True, thr=None):
    out=p.copy()
    for d in np.unique(dep):
        idx=np.where(dep==d)[0]
        if len(idx)<3: continue
        r=np.isclose(d,round(d))
        if only_rnd and not r: continue
        S=Z[idx]@Z[idx].T
        np.fill_diagonal(S,-9)
        kk=min(k,len(idx)-1)
        nb=np.argpartition(-S,kk-1,axis=1)[:,:kk]
        if thr is not None:
            w=(np.take_along_axis(S,nb,1)>thr).astype(float)
        else:
            w=np.ones_like(nb,dtype=float)
        num=(p[idx][nb]*w).sum(1); den=w.sum(1)
        m=den>0
        v=p[idx].copy(); v[m]=(1-lam)*p[idx][m]+lam*(num[m]/den[m])
        out[idx]=v
    return out

print("\nsmoothing tetangga derau, sisi depth-bulat saja:")
best=None
for k in [4,8,16,32]:
    for lam in [0.15,0.3,0.45,0.6]:
        q=nbr_smooth(base,Ztr,C.d_tr,k=k,lam=lam)
        v=sc(q)
        if best is None or v<best[0]: best=(v,k,lam)
        print("   k=%2d lam=%.2f  lb_real=%.4f  rnd=%.4f  bias=%+.3f"
              %(k,lam,v,C.part_real(q,False),C.bias_rnd(q)))
print("terbaik:",best)
