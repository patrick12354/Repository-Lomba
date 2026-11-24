"""Berapa headroom sebenarnya di bawah metrik terkoreksi?"""
import _path  # noqa: F401  -- menaruh Case 1/ di sys.path
import numpy as np, pandas as pd
import lab_common as C
from fastscore import Scorer, Post
def ld(n):
    z=np.load(C.CACHE/f"{n}.npz"); return z["oof"],z["pte"]
CAND=["regA","regB","resA","resB","swA_sqrt"]
w=np.load(C.CACHE/"w_full.npy"); O=np.stack([ld(n)[0] for n in CAND]); base=w@O
cur=Post(C.d_tr,0.95,0.5,150,1.15,1.05)(base)
sc=Scorer(C.EVR,np.ones(len(C.y),bool))
print(f"pipeline sekarang        lb_real={sc(cur):.4f}  dec={C.part_real(cur,True):.4f} rnd={C.part_real(cur,False):.4f}")

def smooth_by(p, e):
    s=pd.Series(p).groupby(pd.Series(e)).transform("median").values
    return s
# oracle: kalau event_id NYATA diketahui (pakai realisasi event yang sama dgn scorer)
def oracle_score(p, expand=1.0):
    out=[]
    for e in C.EVR:
        q=smooth_by(p,e)
        if expand!=1.0:
            r=C.rnd_tr; q=q.copy()
            for m in (r,~r):
                mu=q[m].mean(); q[m]=mu+expand*(q[m]-mu)
        s=Scorer([e],np.ones(len(C.y),bool)); out.append(s(q))
    return float(np.mean(out))
for a in [1.0,1.15,1.3]:
    print(f"ORACLE grouping sempurna (alpha={a}): lb_real={oracle_score(base,a):.4f}")
# oracle terpisah per sisi
for dec in (True,False):
    m=(~C.rnd_tr) if dec else C.rnd_tr
    vs=[]
    for e in C.EVR:
        q=smooth_by(base,e); q=1.15*(q-q[m].mean())+q[m].mean()
        vs.append(C.eb_twmae(C.y[m],q[m],e[m]))
    lbl="dec" if dec else "rnd"
    cs=C.part_real(cur,dec)
    print(f"  sisi {lbl}: sekarang {cs:.4f} -> oracle {np.mean(vs):.4f}  (headroom {cs-np.mean(vs):.4f})")
# batas per-record: kalau model sempurna? -> 0. Yang informatif: MAE per-record sekarang
print(f"\nMAE per-record (tanpa smoothing): dec={np.abs(C.y-base)[~C.rnd_tr].mean():.4f} rnd={np.abs(C.y-base)[C.rnd_tr].mean():.4f}")
