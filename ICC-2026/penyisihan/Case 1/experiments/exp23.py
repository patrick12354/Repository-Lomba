import _path  # noqa: F401  -- menaruh Case 1/ di sys.path
import numpy as np
import lab_common as C
from fastscore import Scorer, Post
def ld(n):
    z=np.load(C.CACHE/f"{n}.npz"); return z["oof"],z["pte"]
OLD=["regA","swA_sqrt","resA_sqrt","resB","resB_sqrt","resB_c30","cnn_sqrt"]
SETS={"A_8kand":["swA_sqrt","resA_dep","resB_c30","resB_dep","resB_p05","cnn_sqrt","cnnres","spec_sqrt"],
      "B_tanpa_spec":["swA_sqrt","resA_dep","resB_c30","resB_dep","resB_p05","cnn_sqrt","cnnres"],
      "C_ramping5":["swA_sqrt","resA_dep","resB_dep","resB_c30","cnnres"]}
allc=sorted(set(sum(SETS.values(),[]))|set(OLD))
P={n:ld(n) for n in allc}
post=Post(C.d_tr,0.95,0.5,150,1.15,1.05)
Q6=post(np.load(C.CACHE/"w7_mean.npy")@np.stack([P[n][0] for n in OLD]))
sc=Scorer(C.EVR,np.ones(len(C.y),bool)); uev=np.unique(C.ev)
rng=np.random.RandomState(0)
for tag,CAND in SETS.items():
    On=np.stack([P[n][0] for n in CAND])
    W=np.vstack([rng.dirichlet(np.ones(len(CAND))*0.6,size=6000),np.eye(len(CAND))])
    Q=np.stack([post(x@On) for x in W])
    gains=[];opt=[];ws=[]
    for rep in range(6):
        r=np.random.RandomState(100+rep); perm=r.permutation(uev)
        h1=np.isin(C.ev,perm[:len(perm)//2])
        for keep in (h1,~h1):
            ssel=Scorer(C.EVR,keep); shold=Scorer(C.EVR,~keep)
            v=np.array([ssel(q) for q in Q]); i=v.argmin()
            gains.append(shold(Q[i])-shold(Q6)); opt.append(shold(Q[i])-v[i]); ws.append(W[i])
    wm=np.mean(ws,0); wm/=wm.sum(); qm=post(wm@On)
    print(f"{tag:>14}: gain vs nb6 {np.mean(gains):+.4f} (menang {sum(g<0 for g in gains):2d}/12) "
          f"optimisme {np.mean(opt)/np.sqrt(2):+.4f} | lb_real={sc(qm):.4f} jujur={sc(qm)+np.mean(opt)/np.sqrt(2):.4f} bias={C.bias_rnd(qm):+.3f}")
    print(f"                bobot: {dict(zip(CAND,np.round(wm,3)))}")
    np.save(C.CACHE/f"w_{tag}.npy",wm)
