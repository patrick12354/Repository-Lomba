"""Blend final nb7: kandidat baru, protokol optimisme sama seperti nb6."""
import _path  # noqa: F401  -- menaruh Case 1/ di sys.path
import numpy as np
import lab_common as C
from fastscore import Scorer, Post
def ld(n):
    z=np.load(C.CACHE/f"{n}.npz"); return z["oof"],z["pte"]
OLD=["regA","swA_sqrt","resA_sqrt","resB","resB_sqrt","resB_c30","cnn_sqrt"]
NEW=["swA_sqrt","resA_dep","resB_c30","resB_dep","resB_p05","cnn_sqrt","cnnres","spec_sqrt"]
Po={n:ld(n) for n in set(OLD)|set(NEW)}
Oo=np.stack([Po[n][0] for n in OLD]); On=np.stack([Po[n][0] for n in NEW])
wo=np.load(C.CACHE/"w7_mean.npy")
post=Post(C.d_tr,0.95,0.5,150,1.15,1.05)
Q6=post(wo@Oo)
rng=np.random.RandomState(0)
W=np.vstack([rng.dirichlet(np.ones(len(NEW))*0.6,size=8000),np.eye(len(NEW))])
Q=np.stack([post(x@On) for x in W])
sc=Scorer(C.EVR,np.ones(len(C.y),bool))
print(f"nb6 (bobot lama)  lb_real={sc(Q6):.4f}  bias={C.bias_rnd(Q6):+.3f}   [LB 0,1952]")
uev=np.unique(C.ev); gains=[];opt=[];ws=[]
print(f"\n{'split':>6}{'sel':>9}{'hold':>9}{'nb6':>9}{'gain':>9}")
for rep in range(6):
    r=np.random.RandomState(100+rep); perm=r.permutation(uev)
    h1=np.isin(C.ev,perm[:len(perm)//2])
    for keep,tag in ((h1,f"{rep}a"),(~h1,f"{rep}b")):
        ssel=Scorer(C.EVR,keep); shold=Scorer(C.EVR,~keep)
        v=np.array([ssel(q) for q in Q]); i=v.argmin()
        sh=shold(Q[i]); s6=shold(Q6)
        gains.append(sh-s6); opt.append(sh-v[i]); ws.append(W[i])
        print(f"{tag:>6}{v[i]:9.4f}{sh:9.4f}{s6:9.4f}{sh-s6:+9.4f}")
print(f"\ngain vs nb6: {np.mean(gains):+.4f} (menang {sum(g<0 for g in gains)}/12)")
print(f"optimisme: {np.mean(opt):+.4f} -> koreksi penuh {np.mean(opt)/np.sqrt(2):+.4f}")
wm=np.mean(ws,0); wm/=wm.sum()
print("bobot rata2 lintas split:", dict(zip(NEW,np.round(wm,3))))
qm=post(wm@On)
print(f"lb_real(bobot rata2-split)={sc(qm):.4f} jujur={sc(qm)+np.mean(opt)/np.sqrt(2):.4f} bias={C.bias_rnd(qm):+.3f}")
np.save(C.CACHE/"w8_mean.npy",wm)
