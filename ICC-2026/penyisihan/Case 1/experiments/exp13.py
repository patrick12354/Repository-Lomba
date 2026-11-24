import _path  # noqa: F401  -- menaruh Case 1/ di sys.path
import numpy as np, sys
import lab_common as C
from fastscore import Scorer, Post
def ld(n):
    z=np.load(C.CACHE/f"{n}.npz"); return z["oof"],z["pte"]
CAND=["regA","swA_sqrt","resA_sqrt","resB","resB_sqrt","resB_c30","cnn_sqrt"]
P={n:ld(n) for n in CAND}; O=np.stack([P[n][0] for n in CAND])
LD,TD,AD,AR = 0.5,150,1.15,1.05
post=Post(C.d_tr,0.95,LD,TD,AD,AR)
rng=np.random.RandomState(0)
W=np.vstack([rng.dirichlet(np.ones(len(CAND))*0.6,size=6000), np.eye(len(CAND))])
Q=np.stack([post(w@O) for w in W])
w5=np.load(C.CACHE/"w_full.npy")
O5=np.stack([ld(n)[0] for n in ["regA","regB","resA","resB","swA_sqrt"]])
Q5=post(w5@O5); Qfix=post(0.65*P["regA"][0]+0.35*ld("regB")[0])
Qnb3=Post(C.d_tr,0.95,0.0,100,1.15,1.15)(0.65*P["regA"][0]+0.35*ld("regB")[0])
sc_all=Scorer(C.EVR,np.ones(len(C.y),bool))
print(f"nb3 apa adanya           lb_real={sc_all(Qnb3):.4f}  [LB aktual 0,1996]")
print(f"bobot tetap + post baru  lb_real={sc_all(Qfix):.4f}")
print(f"blend 5-kandidat         lb_real={sc_all(Q5):.4f}")
uev=np.unique(C.ev); gains=[];opt=[];ws=[]
print(f"\n{'split':>6}{'sel':>9}{'hold':>9}{'blend5':>9}{'gain':>9}")
for rep in range(6):
    r=np.random.RandomState(100+rep); perm=r.permutation(uev)
    h1=np.isin(C.ev,perm[:len(perm)//2])
    for keep,tag in ((h1,f"{rep}a"),(~h1,f"{rep}b")):
        ssel=Scorer(C.EVR,keep); shold=Scorer(C.EVR,~keep)
        v=np.array([ssel(q) for q in Q]); i=v.argmin()
        sh=shold(Q[i]); s5=shold(Q5)
        gains.append(sh-s5); opt.append(sh-v[i]); ws.append(W[i])
        print(f"{tag:>6}{v[i]:9.4f}{sh:9.4f}{s5:9.4f}{sh-s5:+9.4f}")
print(f"\ngain vs blend5: {np.mean(gains):+.4f} (menang {sum(g<0 for g in gains)}/12)")
print(f"optimisme: {np.mean(opt):+.4f} -> koreksi penuh {np.mean(opt)/np.sqrt(2):+.4f}")
print("bobot rata2 lintas split:", dict(zip(CAND,np.round(np.mean(ws,0),3))))
v=np.array([sc_all(q) for q in Q]); i=v.argmin()
wf=W[i]
print(f"\nbobot data penuh: {dict(zip(CAND,np.round(wf,3)))}")
print(f"lb_real mentah={v[i]:.4f} jujur={v[i]+np.mean(opt)/np.sqrt(2):.4f} bias_rnd={C.bias_rnd(Q[i]):+.3f}")
# alternatif stabil: rata-rata bobot lintas split (lebih tahan derau seleksi)
wm=np.mean(ws,0); wm/=wm.sum(); qm=post(wm@O)
print(f"bobot rata2-split : lb_real={sc_all(qm):.4f} bias_rnd={C.bias_rnd(qm):+.3f}")
np.save(C.CACHE/"w7_full.npy",wf); np.save(C.CACHE/"w7_mean.npy",wm)
