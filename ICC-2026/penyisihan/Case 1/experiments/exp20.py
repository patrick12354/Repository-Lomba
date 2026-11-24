"""Seberapa sensitif keputusan kita terhadap tebakan `chunk`?"""
import _path  # noqa: F401  -- menaruh Case 1/ di sys.path
import numpy as np, itertools
import lab_common as C
from fastscore import Scorer, Post
def ld(n): return np.load(C.CACHE/f"{n}.npz")["oof"]
CAND=["regA","swA_sqrt","resA_sqrt","resB","resB_sqrt","resB_c30","cnn_sqrt"]
O=np.stack([ld(n) for n in CAND]); w=np.load(C.CACHE/"w7_mean.npy")
base=w@O
print(f"{'chunk':>6}{'a_rnd terbaik':>15}{'lam_deep terbaik':>18}   lb_real di optimum")
for chunk in [3,5,8,14,25]:
    C.EVR=[C.make_ev_real(s,chunk) for s in range(8)]
    sc=Scorer(C.EVR,np.ones(len(C.y),bool))
    best=min(((sc(Post(C.d_tr,0.95,ldp,150,1.15,ar)(base)),ar,ldp)
              for ar in [0.95,1.0,1.05,1.1,1.15,1.25] for ldp in [0.0,0.35,0.5,0.8]))
    print(f"{chunk:6d}{best[1]:15.2f}{best[2]:18.2f}   {best[0]:.4f}")
# stabilitas bobot blend lintas chunk
print("\nbobot blend optimum lintas chunk:")
rng=np.random.RandomState(0); W=np.vstack([rng.dirichlet(np.ones(7)*0.6,size=3000),np.eye(7)])
post=Post(C.d_tr,0.95,0.5,150,1.15,1.05); Q=np.stack([post(x@O) for x in W])
for chunk in [3,8,20]:
    C.EVR=[C.make_ev_real(s,chunk) for s in range(6)]
    sc=Scorer(C.EVR,np.ones(len(C.y),bool))
    v=np.array([sc(q) for q in Q]); i=v.argmin()
    print(f"  chunk={chunk:2d}: {dict(zip(CAND,np.round(W[i],2)))}")
    print(f"           lb_real(bobot w7_mean)={sc(post(base)):.4f} vs optimum {v[i]:.4f}")
