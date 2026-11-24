import _path
import numpy as np, time
import lab_common as C, lab_blend as B, lab_set as S
from fastscore import Scorer, Post
sc=Scorer(C.EVR,np.ones(len(C.y),bool))
post=Post(C.d_tr,0.95,0.5,150,1.15,1.05); postte=Post(C.d_te,0.95,0.5,150,1.15,1.05)
CAND=["swA_sqrt","resA_dep","resB_dep","resB_c30","resB_p05","cnnres","cnn3_avg","cnn3_dir"]
w=np.load(C.CACHE/"w_nb9.npy")
btr=w@np.stack([B.ld(n)[0] for n in CAND]); bte=w@np.stack([B.ld(n)[1] for n in CAND])
base=post(btr); baset=postte(bte)
print("acuan nb8 lb_real=%.4f rnd=%.4f bias=%+.3f"%(sc(base),C.part_real(base,False),C.bias_rnd(base)))
t0=time.time()
corr,cte=S.run(btr,bte)
np.savez(C.CACHE/"set2.npz",corr=corr,cte=cte)
print("waktu %.0fs | koreksi sd=%.4f  mean_MR=%+.4f"%(time.time()-t0,corr.std(),corr[C.MR].mean()))
grid=[0.0,0.1,0.15,0.2,0.25,0.3,0.4,0.5,0.6,0.75]
Q=np.stack([post(btr+l*corr) for l in grid])
for l,q in zip(grid,Q):
    print("  lam=%.2f lb_real=%.4f dec=%.4f rnd=%.4f bias=%+.3f"
          %(l,sc(q),C.part_real(q,True),C.part_real(q,False),C.bias_rnd(q)))
uev=np.unique(C.ev); gains=[];sel=[]
for rep in range(6):
    r=np.random.RandomState(100+rep); perm=r.permutation(uev)
    h1=np.isin(C.ev,perm[:len(perm)//2])
    for keep in (h1,~h1):
        ss=Scorer(C.EVR,keep); sh=Scorer(C.EVR,~keep)
        v=np.array([ss(q) for q in Q]); i=v.argmin()
        gains.append(sh(Q[i])-sh(base)); sel.append(grid[i])
print("gain holdout jujur %+.5f (menang %d/12) lam: %s"%(np.mean(gains),sum(g<0 for g in gains),sel))
lam=float(np.median(sel))
qt=postte(bte+lam*cte)
print("lam median=%.2f -> test: mean_rnd=%.3f (nb8 %.3f)  sd_rnd=%.3f (nb8 %.3f)"
      %(lam,qt[C.MT].mean(),baset[C.MT].mean(),qt[C.rnd_te].std(),baset[C.rnd_te].std()))
