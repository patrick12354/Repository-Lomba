import _path  # noqa: F401  -- menaruh Case 1/ di sys.path
import numpy as np, itertools
import lab_common as C
from fastscore import Scorer, Post
def ld(n):
    z=np.load(C.CACHE/f"{n}.npz"); return z["oof"],z["pte"]
CAND=["regA","regB","resA","resB","swA_sqrt"]
w=np.load(C.CACHE/"w_full.npy")
O=np.stack([ld(n)[0] for n in CAND]); base=w@O
sc=Scorer(C.EVR,np.ones(len(C.y),bool))
best=[]
for lam_dec in [0.85,0.95,1.0]:
  for lam_deep in [0.0,0.35,0.6,0.85]:
    for T in [100,150]:
      for ad in [1.05,1.10,1.15,1.20]:
        for ar in [0.95,1.00,1.05,1.10]:
            q=Post(C.d_tr,lam_dec,lam_deep,T,ad,ar)(base)
            best.append((sc(q),lam_dec,lam_deep,T,ad,ar,C.bias_rnd(q)))
best.sort()
print(f"{'lb_real':>9}{'lam_dec':>9}{'lam_deep':>10}{'T':>5}{'a_dec':>7}{'a_rnd':>7}{'bias':>8}")
for b in best[:10]: print(f"{b[0]:9.4f}{b[1]:9.2f}{b[2]:10.2f}{b[3]:5d}{b[4]:7.2f}{b[5]:7.2f}{b[6]:+8.3f}")
print("...")
for b in best[-3:]: print(f"{b[0]:9.4f}{b[1]:9.2f}{b[2]:10.2f}{b[3]:5d}{b[4]:7.2f}{b[5]:7.2f}{b[6]:+8.3f}")
# stabilitas: apakah argmin sama di dua belahan event?
uev=np.unique(C.ev)
for rep in range(4):
    r=np.random.RandomState(200+rep); perm=r.permutation(uev)
    h=np.isin(C.ev,perm[:len(perm)//2])
    for keep,tag in ((h,"a"),(~h,"b")):
        s=Scorer(C.EVR,keep)
        v=[(s(Post(C.d_tr,*b[1:6])(base)),b[1:6]) for b in best[:200]]
        v.sort(); print(f"  split {rep}{tag}: argmin={v[0][1]}")
