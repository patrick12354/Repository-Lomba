"""Pseudo-labeling test set untuk CNN v3.

Alasan mekanistiknya spesifik untuk case ini: proporsi depth-bulat 32% di train tapi 51%
di test. Semua model dilatih pada distribusi yang salah. Menambahkan record test dengan
pseudo-label menggeser distribusi training ke arah test -- dan yang lebih penting,
memberi CNN akses ke grup depth sisi test yang sebenarnya.

Beda dari koreksi density-ratio nb7 (gagal): itu reweighting record train yang sudah ada;
ini menambah record baru dari distribusi target.
"""
import _path
import numpy as np, torch, time
import lab_common as C, lab_cnn3 as N3
from fastscore import Scorer, Post

sc=Scorer(C.EVR,np.ones(len(C.y),bool))
z=np.load(C.CACHE/"cnn_input.npz")
Wtr,Str,Wte,Ste=z["Wtr"],z["Str"],z["Wte"],z["Ste"]
CAND=["swA_sqrt","resA_dep","resB_dep","resB_c30","resB_p05","cnnres","cnn3_avg","cnn3_dir"]
def ld(n):
    zz=np.load(C.CACHE/f"{n}.npz"); return zz["oof"],zz["pte"]
w=np.load(C.CACHE/"w_nb9.npy")
post_te=Post(C.d_te,0.95,0.5,150,1.15,1.05)
pl = post_te(w@np.stack([ld(n)[1] for n in CAND]))   # pseudo-label test
print("pseudo-label test: mean=%.3f sd=%.3f"%(pl.mean(),pl.std()))
np.save(C.CACHE/"pseudo_te.npy", pl)
