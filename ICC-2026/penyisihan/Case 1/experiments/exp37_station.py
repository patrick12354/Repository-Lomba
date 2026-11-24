"""Apakah jendela pre-P menyimpan identitas stasiun?

Dataset tidak punya station_id, tapi derau ambient sebelum P adalah sidik jari situs:
spektrum derau ditentukan geologi lokal + instrumen, dan stabil antar-event. Kalau
record bisa diklaster jadi "stasiun", dua konsekuensi:

  (a) site term -> fitur koreksi baru (satu stasiun bias tinggi/rendah secara sistematis)
  (b) BATASAN NEGATIF untuk grouping: dalam satu gempa, satu stasiun muncul paling banyak
      sekali. Dua record dari stasiun sama TIDAK MUNGKIN satu event.

(b) belum pernah dipakai. Classifier co-membership nb7 hanya punya sinyal positif.

Uji validitas: pada sisi depth-DESIMAL (grup di sana ~event sungguhan), apakah record
dalam satu event lebih jarang seklaster daripada peluang acak?
"""
import _path
import numpy as np, pandas as pd
from scipy import signal
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
import lab_common as C

W=np.load(C.DATA/"train"/"train_waveforms.npy").astype(np.float32)
Wte=np.load(C.DATA/"test"/"test_waveforms.npy").astype(np.float32)

def noisefp(X):
    """sidik jari derau: PSD ternormalisasi jendela pre-P (bentuk spektrum, bukan level)."""
    pre=X[:,:C.P_IDX,:]
    f,P=signal.welch(pre,fs=C.FS,nperseg=128,axis=1)      # (n, nf, 3)
    Pm=P.mean(2)
    Pm=np.log10(Pm+1e-20)
    Pm=Pm-Pm.mean(1,keepdims=True)                        # buang level -> bentuk saja
    # tambah rasio antar-komponen (respons instrumen H vs V)
    hv=np.log10(P[:,:,:2].mean(2)+1e-20)-np.log10(P[:,:,2]+1e-20)
    hv=hv-hv.mean(1,keepdims=True)
    return np.concatenate([Pm,hv],1).astype(np.float32), f

Ftr,ffreq=noisefp(W); Fte_,_=noisefp(Wte)
A=np.vstack([Ftr,Fte_])
A=(A-A.mean(0))/(A.std(0)+1e-8)
pc=PCA(24,random_state=0).fit(A)
Z=pc.transform(A)
print("PCA var 24 komp: %.3f"%pc.explained_variance_ratio_.sum())
Ztr=Z[:len(Ftr)]; Zte=Z[len(Ftr):]

for K in [40,80,150,300]:
    km=KMeans(K,n_init=4,random_state=0).fit(Z)
    lab=km.labels_[:len(Ftr)]
    # uji: sisi depth-desimal, grup = event nyata
    dec=~C.rnd_tr
    df=pd.DataFrame({"e":C.ev[dec],"k":lab[dec]})
    g=df.groupby("e").k
    n_rec=g.size(); n_uni=g.nunique()
    m=n_rec>=4
    frac_uni=(n_uni[m]/n_rec[m]).mean()
    # baseline acak: label diacak
    rs=np.random.RandomState(0); lab_s=rs.permutation(lab)
    df2=pd.DataFrame({"e":C.ev[dec],"k":lab_s[dec]}); g2=df2.groupby("e").k
    frac_rand=(g2.nunique()[m]/n_rec[m]).mean()
    print("K=%3d  frac_klaster_unik dalam event: nyata=%.4f  acak=%.4f  selisih=%+.4f"
          %(K,frac_uni,frac_rand,frac_uni-frac_rand))
np.savez(C.CACHE/"noisefp.npz", Ztr=Ztr, Zte=Zte)
