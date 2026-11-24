import _path  # noqa: F401  -- menaruh Case 1/ di sys.path
import numpy as np, pandas as pd, itertools
import lab_common as C
from fastscore import Scorer, Post
exec(open("exp16.py").read().split("print(f\"{'sub'")[0])   # bangun `subs`
names=["nb1","nb2","nb3","nb5","nb6"]
LB=np.array([subs[k][1] for k in names]); BR=np.array([C.bias_rnd(subs[k][0]) for k in names])
print("bias_rnd rekonstruksi:", dict(zip(names,np.round(BR,3))))
core=[0,2,3,4]     # tanpa nb2
rows=[]
for chunk in [2,3,4,5,6,8,10,14,20]:
    C.EVR=[C.make_ev_real(s,chunk) for s in range(8)]
    for FD in [0.40,0.45,0.49,0.53,0.58,0.62]:
        C.FD=FD; sc=Scorer(C.EVR,np.ones(len(C.y),bool))
        v=np.array([sc(subs[k][0]) for k in names])
        a,b=np.polyfit(v[core],LB[core],1)
        rm=np.sqrt(((a*v[core]+b-LB[core])**2).mean()); r=np.corrcoef(v[core],LB[core])[0,1]
        # model 2-variabel dgn nb2 ikut: LB ~ a*metrik + c*bias_rnd + b
        A=np.column_stack([v,BR,np.ones(5)]); coef,*_=np.linalg.lstsq(A,LB,rcond=None)
        rm5=np.sqrt(((A@coef-LB)**2).mean())
        rows.append((rm,chunk,FD,r,a,rm5,coef,v.copy()))
rows.sort()
print(f"\n{'rmse4':>8}{'chunk':>7}{'FD':>6}{'korelasi4':>11}{'slope':>7}{'rmse5_2var':>12}")
for t in rows[:10]:
    print(f"{t[0]:8.5f}{t[1]:7d}{t[2]:6.2f}{t[3]:11.4f}{t[4]:7.2f}{t[5]:12.5f}   {np.round(t[7],4)}")
best=rows[0]
print(f"\nTERBAIK: chunk={best[1]} FD={best[2]}  korelasi 4 titik={best[3]:.4f}  slope={best[4]:.2f}")
print(f"model 2-variabel (semua 5 titik): LB = {best[6][0]:.3f}*metrik + {best[6][1]:.3f}*bias_rnd + {best[6][2]:.4f}, rmse={best[5]:.5f}")
np.save(C.CACHE/"calib.npy", np.array([best[1],best[2],best[4],*best[6]]))
