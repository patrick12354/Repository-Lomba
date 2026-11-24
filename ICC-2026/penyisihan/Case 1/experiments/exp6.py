import _path  # noqa: F401  -- menaruh Case 1/ di sys.path
import numpy as np, itertools
import lab_common as C
from fastscore import Scorer, Post
def ld(n):
    z=np.load(C.CACHE/f"{n}.npz"); return z["oof"],z["pte"]
CAND=["regA","regB","resA","resB","swA_sqrt"]
P={n:ld(n) for n in CAND}
O=np.stack([P[n][0] for n in CAND])
post=Post(C.d_tr)
rng=np.random.RandomState(0)
W=np.vstack([rng.dirichlet(np.ones(len(CAND))*0.7,size=3000), np.eye(len(CAND))])
Q=np.stack([post(w@O) for w in W])     # precompute sekali, dipakai semua split
Qfix=post(0.65*P["regA"][0]+0.35*P["regB"][0])
Qnb3=Post(C.d_tr,lam_deep=0.0,a_rnd=1.15)(0.65*P["regA"][0]+0.35*P["regB"][0])

uev=np.unique(C.ev); ALL=np.ones(len(C.y),bool)
sc_all=Scorer(C.EVR,ALL)
print(f"referensi nb3 apa adanya      lb_real={sc_all(Qnb3):.4f}   [LB aktual 0,1996]")
print(f"bobot tetap 0,65/0,35 + post baru lb_real={sc_all(Qfix):.4f}")
print(f"\n{'split':>6}{'sel':>9}{'hold':>9}{'tetap':>9}{'gain':>9}   bobot terpilih")
gains=[];opt=[]
for rep in range(6):
    r=np.random.RandomState(100+rep); perm=r.permutation(uev)
    h1=np.isin(C.ev,perm[:len(perm)//2])
    for keep_sel,tag in ((h1,f"{rep}a"),(~h1,f"{rep}b")):
        ssel=Scorer(C.EVR,keep_sel); shold=Scorer(C.EVR,~keep_sel)
        v=np.array([ssel(q) for q in Q]); i=v.argmin()
        s_hold=shold(Q[i]); s_fix=shold(Qfix)
        gains.append(s_hold-s_fix); opt.append(s_hold-v[i])
        print(f"{tag:>6}{v[i]:9.4f}{s_hold:9.4f}{s_fix:9.4f}{s_hold-s_fix:+9.4f}   {np.round(W[i],2)}")
print(f"\ngain vs bobot tetap: {np.mean(gains):+.4f}  (menang {sum(g<0 for g in gains)}/{len(gains)})")
print(f"optimisme seleksi (separuh data): {np.mean(opt):+.4f} -> koreksi penuh {np.mean(opt)/np.sqrt(2):+.4f}")
v=np.array([sc_all(q) for q in Q]); i=v.argmin()
print(f"\nbobot data penuh: {dict(zip(CAND,np.round(W[i],3)))}")
print(f"lb_real mentah={v[i]:.4f}  jujur={v[i]+np.mean(opt)/np.sqrt(2):.4f}")
np.save(C.CACHE/"w_full.npy",W[i])
