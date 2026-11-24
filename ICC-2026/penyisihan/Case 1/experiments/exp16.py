"""Kalibrasi metrik: cari (chunk, FD) yang paling akur memprediksi 5 titik LB nyata."""
import _path  # noqa: F401  -- menaruh Case 1/ di sys.path
import numpy as np, pandas as pd
import lab_common as C
from fastscore import Scorer, Post
def ld(n): 
    z=np.load(C.CACHE/f"{n}.npz"); return z["oof"]
P={n:ld(n) for n in ["regA","regB","resA","resB","regB_mask","resA_iw","resB_iw",
                     "swA_sqrt","resA_sqrt","resB_c30","resB_sqrt","cnn_sqrt"]}
def blend(d): return sum(w*P[n] for n,w in d.items())

# --- rekonstruksi tiap submission ---
subs={}
b13=blend({"regA":0.65,"regB":0.35})
subs["nb1"]=(C.expand_subset(C.smooth_gen(b13,C.d_tr,0.95,0.0),C.d_tr,1.15,1.15), 0.2005, 0.18263)
# nb1 pakai ekspansi GLOBAL
sm=C.smooth_gen(b13,C.d_tr,0.95,0.0); subs["nb1"]=(sm.mean()+1.15*(sm-sm.mean()), 0.2005, 0.18263)
b2=blend({"regA":0.55,"regB_mask":0.45})
subs["nb2"]=(Post(C.d_tr,0.9,0.5,100,1.2,1.1)(b2), 0.2262, 0.17895)
subs["nb3"]=(Post(C.d_tr,0.95,0.0,100,1.15,1.15)(b13), 0.1996, 0.18552)
wd={"regA":0.231,"regB":0.006,"resA":0.58,"resB":0.161,"resB_iw":0.015,"resA_iw":0.007}
wr={"regA":0.372,"regB":0.010,"resA":0.003,"resB":0.021,"resB_iw":0.575,"resA_iw":0.018}
b5=np.where(C.rnd_tr, blend(wr), blend(wd))
subs["nb5"]=(Post(C.d_tr,0.95,0.35,100,1.15,1.15)(b5), 0.2063, 0.17899)
C6=["regA","swA_sqrt","resA_sqrt","resB","resB_sqrt","resB_c30","cnn_sqrt"]
w6=np.load(C.CACHE/"w7_mean.npy")
subs["nb6"]=(Post(C.d_tr,0.95,0.5,150,1.15,1.05)(blend(dict(zip(C6,w6)))), 0.1952, 0.18031)

print(f"{'sub':>5}{'CV_lama_rekon':>15}{'CV_lama_catatan':>17}{'LB':>9}")
for k,(p,lb,cvrec) in subs.items():
    print(f"{k:>5}{C.eb_twmae(C.y,p,C.ev):15.5f}{cvrec:17.5f}{lb:9.4f}")

print("\n=== kalibrasi (chunk, FD) terhadap 5 titik LB ===")
LB=np.array([subs[k][1] for k in subs])
best=[]
for chunk in [3,5,8,12,20,40,100]:
    C.EVR=[C.make_ev_real(s,chunk) for s in range(8)]
    for FD in [0.40,0.45,0.49,0.53,0.58]:
        C.FD=FD
        sc=Scorer(C.EVR,np.ones(len(C.y),bool))
        v=np.array([sc(subs[k][0]) for k in subs])
        a,b=np.polyfit(v,LB,1); r=np.corrcoef(v,LB)[0,1]
        rmse=np.sqrt(((a*v+b-LB)**2).mean())
        best.append((rmse,chunk,FD,r,a,v.copy()))
best.sort()
print(f"{'rmse':>8}{'chunk':>7}{'FD':>6}{'korelasi':>10}{'slope':>8}   nilai metrik (nb1,nb2,nb3,nb5,nb6)")
for b in best[:8]:
    print(f"{b[0]:8.5f}{b[1]:7d}{b[2]:6.2f}{b[3]:10.4f}{b[4]:8.2f}   {np.round(b[5],4)}")
# pembanding: metrik LAMA
old=np.array([subs[k][2] for k in subs])
a,b=np.polyfit(old,LB,1)
print(f"\nmetrik LAMA (eb_twmae mentah): korelasi={np.corrcoef(old,LB)[0,1]:+.4f} rmse={np.sqrt(((a*old+b-LB)**2).mean()):.5f}")
