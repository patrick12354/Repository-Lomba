"""Koreksi site term dari sidik-jari derau pre-P.
Percobaan lama gagal karena mengurangi residual mentah -- itu ikut membuang bias yang
memang DISENGAJA oleh weighted loss. Di sini koreksinya DIPUSATKAN (hanya simpangan
klaster terhadap rata-rata global) dan dishrink secara empirical-Bayes."""
import _path  # noqa: F401  -- menaruh Case 1/ di sys.path
import numpy as np, pandas as pd
from scipy import signal
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.model_selection import GroupKFold
import lab_common as C
from fastscore import Scorer, Post

f=C.CACHE/"noisefeat.npz"
if f.exists():
    z=np.load(f); Ntr,Nte=z["Ntr"],z["Nte"]
else:
    def nf(path):
        X=np.load(path)[:,:200,:].astype(np.float32)
        fr,P=signal.welch(X,fs=200,nperseg=128,axis=1)     # (N,F,3)
        L=np.log10(P.mean(2)+1e-20)
        L=L-L.mean(1,keepdims=True)                        # BENTUK spektrum saja, buang level
        return L.astype(np.float32)
    Ntr=nf(C.DATA/"train"/"train_waveforms.npy"); Nte=nf(C.DATA/"test"/"test_waveforms.npy")
    np.savez(f,Ntr=Ntr,Nte=Nte)
print("fitur derau:",Ntr.shape)
pca=PCA(n_components=12).fit(np.vstack([Ntr,Nte]))
Ztr,Zte=pca.transform(Ntr),pca.transform(Nte)
print("varians dijelaskan 12 PC:",round(pca.explained_variance_ratio_.sum(),3))

w=np.load(C.CACHE/"w7_mean.npy")
OLD=["regA","swA_sqrt","resA_sqrt","resB","resB_sqrt","resB_c30","cnn_sqrt"]
raw=w@np.stack([np.load(C.CACHE/f"{n}.npz")["oof"] for n in OLD])
po=Post(C.d_tr,0.95,0.5,150,1.15,1.05); sc=Scorer(C.EVR,np.ones(len(C.y),bool))
base=po(raw); print(f"baseline lb_real={sc(base):.4f} bias={C.bias_rnd(base):+.3f}")
res=C.y-raw

print(f"\n{'K':>5}{'shrink':>8}{'lb_real':>10}{'bias':>8}{'R2_klaster_OOF':>16}")
for K in [40,100,250]:
    km=KMeans(K,n_init=4,random_state=0).fit(np.vstack([Ztr,Zte]))
    ctr=km.labels_[:len(Ztr)]
    for shrink in [5,20,60]:
        corr=np.zeros(len(C.y)); r2s=[]
        for ti,vi in GroupKFold(5).split(Ztr,C.y,C.ev):
            d=pd.DataFrame({"c":ctr[ti],"r":res[ti],"w":C.SW[ti]})
            g=d.groupby("c").apply(lambda s: pd.Series(
                {"m":np.average(s.r,weights=s.w),"n":s.w.sum()}))
            gm=np.average(res[ti],weights=C.SW[ti])
            eff=((g.m-gm)*g.n/(g.n+shrink))                 # dipusatkan + shrink EB
            corr[vi]=pd.Series(ctr[vi]).map(eff).fillna(0).values
            r2s.append(1-np.var(res[vi]-corr[vi])/np.var(res[vi]))
        q=po(raw+corr)
        print(f"{K:5d}{shrink:8d}{sc(q):10.4f}{C.bias_rnd(q):+8.3f}{np.mean(r2s):16.4f}")
