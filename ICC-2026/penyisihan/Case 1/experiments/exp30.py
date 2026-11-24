import _path  # noqa: F401  -- menaruh Case 1/ di sys.path
import numpy as np
import lab_common as C
from fastscore import Scorer, Post
def ld(n):
    z=np.load(C.CACHE/f"{n}.npz"); return z["oof"],z["pte"]
OLD=["regA","swA_sqrt","resA_sqrt","resB","resB_sqrt","resB_c30","cnn_sqrt"]
NEW=["swA_sqrt","resA_dep","resB_dep","resB_c30","resB_p05","cnnres","cnn3"]
P={n:ld(n) for n in set(OLD)|set(NEW)}
post=Post(C.d_tr,0.95,0.5,150,1.15,1.05)
Q6=post(np.load(C.CACHE/"w7_mean.npy")@np.stack([P[n][0] for n in OLD]))
On=np.stack([P[n][0] for n in NEW])
sc=Scorer(C.EVR,np.ones(len(C.y),bool))
print(f"nb6 acuan lb_real={sc(Q6):.4f} bias={C.bias_rnd(Q6):+.3f}  [LB 0,1952]")
rng=np.random.RandomState(0)
W=np.vstack([rng.dirichlet(np.ones(len(NEW))*0.6,size=8000),np.eye(len(NEW))])
Q=np.stack([post(x@On) for x in W])
uev=np.unique(C.ev); gains=[];opt=[];ws=[]
for rep in range(6):
    r=np.random.RandomState(100+rep); perm=r.permutation(uev)
    h1=np.isin(C.ev,perm[:len(perm)//2])
    for keep in (h1,~h1):
        ss=Scorer(C.EVR,keep); sh=Scorer(C.EVR,~keep)
        v=np.array([ss(q) for q in Q]); i=v.argmin()
        gains.append(sh(Q[i])-sh(Q6)); opt.append(sh(Q[i])-v[i]); ws.append(W[i])
print(f"gain vs nb6: {np.mean(gains):+.4f} (menang {sum(g<0 for g in gains)}/12)  optimisme {np.mean(opt)/np.sqrt(2):+.4f}")
wm=np.mean(ws,0); wm/=wm.sum()
print("bobot:", dict(zip(NEW,np.round(wm,3))))
qm=post(wm@On)
print(f"lb_real={sc(qm):.4f} jujur={sc(qm)+np.mean(opt)/np.sqrt(2):.4f} bias={C.bias_rnd(qm):+.3f}")
np.save(C.CACHE/"w_cnn3.npy",wm)
# dgn koreksi ekor c=0.1
qt=qm+0.1*np.maximum(0,qm-5.8)
print(f"+ koreksi ekor c=0,1: lb_real={sc(qt):.4f} bias={C.bias_rnd(qt):+.3f}")
