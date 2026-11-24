import _path  # noqa: F401  -- menaruh Case 1/ di sys.path
import numpy as np, pandas as pd
import lab_common as C
from fastscore import Scorer, Post
def ld(n):
    z=np.load(C.CACHE/f"{n}.npz"); return z["oof"],z["pte"]
CAND=["regA","swA_sqrt","resA_sqrt","resB","resB_sqrt","resB_c30","cnn_sqrt"]
P={n:ld(n) for n in CAND}
w=np.load(C.CACHE/"w7_mean.npy")
Otr=np.stack([P[n][0] for n in CAND]); Ote=np.stack([P[n][1] for n in CAND])
po=Post(C.d_tr,0.95,0.5,150,1.15,1.05)(w@Otr)
pt=Post(C.d_te,0.95,0.5,150,1.15,1.05)(w@Ote)
sc=Scorer(C.EVR,np.ones(len(C.y),bool))
print(f"lb_real={sc(po):.4f}  bias_rnd={C.bias_rnd(po):+.4f}")
nb3=pd.read_csv("submission/notebook_3.csv").magnitude.values
nb5=pd.read_csv("submission/notebook_5.csv").magnitude.values
print("\nmodel sensitivitas LB (mean prediksi subset test depth-bulat <100km):")
for n,v,lb in [("nb3",nb3,"0,1996"),("nb5",nb5,"0,2063"),("baru",pt,"?")]:
    print(f"  {n:5s} mean={v[C.MT].mean():.3f}  sd_all={v.std():.4f} sd_rnd={v[C.rnd_te].std():.4f}  LB {lb}")
print(f"\nkorelasi baru vs nb3 = {np.corrcoef(pt,nb3)[0,1]:.4f}  MAD={np.abs(pt-nb3).mean():.4f}")
# sensitivitas FD
for fd in [0.43,0.46,0.49,0.52,0.55]:
    C.FD=fd; s=Scorer(C.EVR,np.ones(len(C.y),bool))
    print(f"  FD={fd}: lb_real_baru={s(po):.4f}")
C.FD=0.49
np.save(C.CACHE/"final_oof.npy",po); np.save(C.CACHE/"final_pte.npy",pt)
