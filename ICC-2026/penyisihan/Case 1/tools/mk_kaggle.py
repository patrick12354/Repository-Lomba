# -*- coding: utf-8 -*-
"""Generator notebook Kaggle di `kaggle/`.

Tiap notebook berdiri sendiri: tidak mengimpor apapun dari `lab/`, karena di Kaggle
folder itu tidak ada. Kode inti (metrik lb_real, ekstraksi fitur, input CNN, protokol
blend) disalin apa adanya supaya hasilnya sebanding dengan run lokal.
"""
import _path  # noqa: F401
import json
from pathlib import Path

OUT = _path.ROOT / "kaggle"
OUT.mkdir(exist_ok=True)


def md(s):
    return {"cell_type": "markdown", "metadata": {}, "source": s.splitlines(True)}


def co(s):
    return {"cell_type": "code", "execution_count": None, "metadata": {},
            "outputs": [], "source": s.splitlines(True)}


def nb(cells):
    return {"cells": cells,
            "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python",
                                        "name": "python3"},
                         "language_info": {"name": "python", "version": "3.11"}},
            "nbformat": 4, "nbformat_minor": 5}


# ---------------------------------------------------------------- prelude bersama
P_SETUP = '''import os, sys, time, warnings, json, zipfile, glob
from pathlib import Path
import numpy as np, pandas as pd
from scipy import signal, stats
warnings.filterwarnings("ignore")

KG = "/kaggle/input/competitions/ai-innovation-case-task-1-seismic-magnitude-prediction/seismic-dataset"
DATA = Path(KG) if os.path.exists(KG) else Path("seismic-dataset")
OUT  = Path("/kaggle/working") if os.path.isdir("/kaggle/working") else Path("cache")
OUT.mkdir(exist_ok=True, parents=True)

# nb8_ref.npz = prediksi 8 kandidat notebook_8 (OOF + test) + bobot blend-nya.
# Diperlukan untuk memberi VERDIKT terhadap target LB. Upload folder `belum_run/ref/`
# sebagai Kaggle Dataset, atau taruh nb8_ref.npz di mana saja di bawah /kaggle/input.
# Lokasi yang sudah diketahui lebih dulu, baru penelusuran rekursif sebagai cadangan
# (kalau slug dataset-nya berubah, atau dijalankan di lokal).
REF_KNOWN = ["/kaggle/input/datasets/timotiuspatrick/nb8-ref/nb8_ref.npz",
             "/kaggle/input/nb8-ref/nb8_ref.npz"]
def _find_ref():
    for p in REF_KNOWN:
        if os.path.exists(p): return Path(p)
    for root in ("/kaggle/input", "/kaggle/working", ".", "..",
                 "kaggle/ref", "../kaggle/ref"):
        if not os.path.isdir(root): continue
        for dp, _, fs in os.walk(root):
            if "nb8_ref.npz" in fs: return Path(dp)/"nb8_ref.npz"
    return None
REFP = _find_ref()
print("DATA :", DATA, "| ada:", DATA.exists())
print("REF  :", REFP)
if REFP is None:
    print()
    print("!"*72)
    print("nb8_ref.npz TIDAK DITEMUKAN -- notebook 01 akan berhenti di sel Training.")
    print("!"*72)
    print("File ini (334 KB) berisi prediksi OOF + test 8 kandidat notebook_8 beserta")
    print("bobot blend-nya. Tanpa itu tidak ada acuan untuk dibandingkan, dan notebook 01")
    print("tidak punya apa-apa untuk dikoreksi.")
    print()
    print("Cara memasangnya:")
    print("  1. Di repo lokal, ambil  Case 1/belum_run/ref/nb8_ref.npz")
    print("  2. Kaggle -> Datasets -> New Dataset -> upload file itu -> Create")
    print("  3. Balik ke notebook ini -> panel kanan -> Input -> + Add Input")
    print("     -> tab Datasets -> cari dataset barusan -> tanda +")
    print("  4. Run All lagi. Baris REF di atas harus berubah jadi sebuah path.")
    print()
    print("Isi /kaggle/input sekarang:")
    if os.path.isdir("/kaggle/input"):
        for d in sorted(os.listdir("/kaggle/input")): print("   -", d)
    else:
        print("   (/kaggle/input tidak ada -- ini bukan lingkungan Kaggle)")
    print("!"*72)
import torch
DEV = "cuda" if torch.cuda.is_available() else "cpu"
print("DEV  :", DEV, torch.cuda.get_device_name(0) if DEV=="cuda" else "")
if DEV != "cuda":
    print("PERINGATAN: GPU tidak aktif. Settings -> Accelerator -> GPU.")
'''

P_METRIK = '''FS, P_IDX, EPS = 200, 200, 1e-15
train = (pd.read_csv(DATA/"train"/"train_meta.csv")
           .merge(pd.read_csv(DATA/"train"/"train_labels.csv"), on="sample_id"))
test  = pd.read_csv(DATA/"test"/"test_meta.csv")
y   = train.magnitude.values.astype(np.float64)
# Tidak ada event_id di dataset, padahal metriknya per-event. Rekonstruksi heuristik:
ev  = train.groupby(["depth_km","magnitude"]).ngroup().values
cnt = pd.Series(ev).map(pd.Series(ev).value_counts()).values

def mag_weight(m):
    m=np.asarray(m); return np.where(m<5.5,1.0,np.where(m<6.0,1.5,np.where(m<6.5,2.0,2.5)))
def eb_twmae(yt,yp,e):
    df=pd.DataFrame({"y":yt,"p":yp,"e":e}); df["err"]=np.abs(df.y-df.p)
    g=df.groupby("e").agg(mae=("err","mean"),m=("y","first"))
    w=mag_weight(g.m.values); return float((w*g.mae.values).sum()/w.sum())

SW   = mag_weight(y)/cnt
d_tr = train.depth_km.values; d_te = test.depth_km.values
rnd_tr = np.isclose(d_tr, np.round(d_tr)); rnd_te = np.isclose(d_te, np.round(d_te))
MR = rnd_tr & (d_tr < 100); MT = rnd_te & (d_te < 100)
FD = 0.49   # proporsi event depth-desimal di test

# ---- METRIK lb_real -------------------------------------------------------------
# eb_twmae mentah CACAT di sisi depth-bulat: groupby(depth_km, magnitude) melebur record
# depth-bulat jadi pseudo-event sampai 401 record, sehingga CV over-weight ekor ~3x.
# lb_real memecah pseudo-event depth-bulat DANGKAL jadi chunk seukuran event nyata.
# JANGAN pernah menilai kandidat dengan eb_twmae mentah.
def make_ev_real(seed, chunk=8):
    rng=np.random.RandomState(seed); e2=ev.copy(); nxt=ev.max()+1
    split_me = rnd_tr & (d_tr < 100)     # >=100 km: grup 67-100% murni, jangan dipecah
    for eid in np.unique(ev[split_me]):
        idx=np.where(ev==eid)[0]
        if len(idx) <= chunk*1.5: continue
        rng.shuffle(idx); k=max(2,int(round(len(idx)/chunk)))
        for j,part in enumerate(np.array_split(idx,k)):
            if j>0: e2[part]=nxt; nxt+=1
    return e2
EVR = [make_ev_real(s) for s in range(8)]
def part_real(p, dec):
    m=(~rnd_tr) if dec else rnd_tr
    return float(np.mean([eb_twmae(y[m],p[m],e[m]) for e in EVR]))
def lb_real(p):  return FD*part_real(p,True)+(1-FD)*part_real(p,False)
def bias_rnd(p): return float(p[MR].mean()-y[MR].mean())
def make_sw(cap=None, power=1.0):
    c=cnt.astype(float)
    if cap is not None: c=np.minimum(c,cap)
    return mag_weight(y)/(c**power)

# KALIBRASI lb_real -> LB, dari 3 titik submission nyata (R2 0,92):
#   nb3 0,1945 -> 0,1996 | nb6 0,1845 -> 0,1952 | nb8 0,1762 -> 0,1849
# Kalibrasi lb_real -> LB, 5 titik:
#   nb3 +0,0051 | nb6 +0,0107 | nb8 +0,0087 | nb9 +0,0138 (OUTLIER) | nb10 +0,0098
# Tanpa nb9: mean +0,0086, sd 0,0025 -- cukup rapat. nb9 satu-satunya kegagalan ARAH,
# dan sebabnya spesifik (set-transformer menyeragamkan prediksi dalam grup depth).
LB_OFFSET = 0.0086          # mean 4 titik tanpa outlier nb9, sd 0,0025
LB_JUARA  = 0.1762          # lb_real notebook_8 (LB 0,1849). Kandidat harus MENGALAHKAN ini.
def lb_hat(v): return v + LB_OFFSET
print("event efektif:", len(np.unique(ev)), "| record:", len(y))
'''

P_FASTSCORE = '''class Scorer:
    """eb_twmae versi bincount atas banyak realisasi event -- ~5000x lebih cepat."""
    def __init__(self, evs, keep):
        self.parts=[]
        for dec,f in ((True,FD),(False,1-FD)):
            m = keep & ((~rnd_tr) if dec else rnd_tr)
            idx=np.where(m)[0]; per=[]
            for e in evs:
                _,inv=np.unique(e[idx],return_inverse=True)
                nrec=np.bincount(inv).astype(float)
                mm=np.zeros(len(nrec)); mm[inv]=y[idx]
                w=mag_weight(mm); per.append((inv,nrec,w,w.sum(),len(nrec)))
            self.parts.append((idx,f,per))
        self.n=len(evs)
    def __call__(self, p):
        tot=0.0
        for idx,f,per in self.parts:
            err=np.abs(y[idx]-p[idx]); s=0.0
            for inv,nrec,w,wsum,ne in per:
                s+=(w*(np.bincount(inv,weights=err,minlength=ne)/nrec)).sum()/wsum
            tot+=f*s/self.n
        return tot

class Post:
    """smoothing per grup depth + ekspansi varians PER SUBSET.

    Ekspansi harus dipusatkan per subset: versi global mendorong subset depth-bulat
    (yang rata-ratanya di atas mean keseluruhan) ikut naik dan memperbesar bias_rnd.
    Memusatkan per subset memangkas bias_rnd +0,076 -> +0,047 dengan ongkos CV 0,003."""
    def __init__(self, dep, lam_dec=0.95, lam_deep=0.5, T_deep=150, a_dec=1.15, a_rnd=1.05):
        r=np.isclose(dep,np.round(dep))
        self.lam=np.where(~r, lam_dec, np.where(dep>=T_deep, lam_deep, 0.0))
        order=np.argsort(dep,kind="stable"); self.order=order
        ds=dep[order]; bnd=np.flatnonzero(np.diff(ds))+1
        self.slices=np.concatenate([[0],bnd,[len(ds)]])
        self.r=r; self.a_dec=a_dec; self.a_rnd=a_rnd
    def __call__(self, p):
        ps=p[self.order]; gm=np.empty_like(ps); sl=self.slices
        for i in range(len(sl)-1): gm[sl[i]:sl[i+1]]=np.median(ps[sl[i]:sl[i+1]])
        g=np.empty_like(p); g[self.order]=gm
        q=(1-self.lam)*p+self.lam*g; out=q.copy()
        for m,a in ((self.r,self.a_rnd),(~self.r,self.a_dec)):
            mu=q[m].mean(); out[m]=mu+a*(q[m]-mu)
        return out

class SideScorer:
    """eb_twmae di SATU sisi saja. Dipakai untuk DIAGNOSTIK KE-4 (uji sisi-desimal).

    notebook_9 lulus ketiga diagnostik transfer lama, `lb_real`-nya membaik -0,0044, ia
    menang 12/12 belahan -- dan LB-nya tetap MEMBURUK (0,1849 -> 0,1856). Sebabnya:
    `lb_real` memperbaiki BOBOT metrik tapi bukan LABEL-nya. Record dari gempa berbeda
    yang berbagi (depth, magnitude) tetap punya `y` identik, jadi metode apa pun yang
    menyeragamkan prediksi di dalam satu grup depth dibayar berlebihan di sisi bulat.

    Sisi desimal tidak punya masalah itu (event-nya nyata, 98% murni). Jadi: perubahan
    yang menang di sisi bulat tapi RUGI di sisi desimal adalah bendera merah."""
    def __init__(self, dec, keep):
        m = keep & ((~rnd_tr) if dec else rnd_tr)
        self.idx=np.where(m)[0]; self.per=[]
        for e in EVR:
            _,inv=np.unique(e[self.idx],return_inverse=True)
            nrec=np.bincount(inv).astype(float)
            mm=np.zeros(len(nrec)); mm[inv]=y[self.idx]
            w=mag_weight(mm); self.per.append((inv,nrec,w,w.sum(),len(nrec)))
    def __call__(self, p):
        err=np.abs(y[self.idx]-p[self.idx]); s=0.0
        for inv,nrec,w,wsum,ne in self.per:
            s+=(w*(np.bincount(inv,weights=err,minlength=ne)/nrec)).sum()/wsum
        return s/len(self.per)

sc      = Scorer(EVR, np.ones(len(y), bool))
post_tr = Post(d_tr); post_te = Post(d_te)
'''

P_FITUR = '''def _hp(a,f=0.075,order=2):
    b,aa=signal.butter(order,f/(FS/2),btype="high")
    return signal.filtfilt(b,aa,a,axis=1).astype(np.float32)
def L(x): return np.log10(np.abs(x)+EPS).astype(np.float32)
WINS=[0.25,0.5,1.0,1.5,2.0,3.0,4.0]

def extract(X, meta):
    t0=time.time(); out={}
    A=X.astype(np.float32); V=np.cumsum(_hp(A),axis=1)/FS; D=np.cumsum(_hp(V),axis=1)/FS
    def hv(W): return np.sqrt(W[:,:,0]**2+W[:,:,1]**2), np.abs(W[:,:,2])
    for nm,W in [("a",A),("v",V),("d",D)]:
        H,Vt=hv(W); allc=np.abs(W).max(axis=2)
        for s in WINS:
            n=int(s*FS)
            out[f"P{nm}_{s:g}"]=L(allc[:,P_IDX:P_IDX+n].max(1))
            out[f"P{nm}H_{s:g}"]=L(H[:,P_IDX:P_IDX+n].max(1))
            out[f"P{nm}V_{s:g}"]=L(Vt[:,P_IDX:P_IDX+n].max(1))
        out[f"pre_{nm}"]=L(allc[:,:P_IDX].max(1))
        out[f"snr_{nm}"]=out[f"P{nm}_4"]-out[f"pre_{nm}"]
        for s in [1.0,2.0,4.0]:
            n=int(s*FS)
            out[f"rms{nm}_{s:g}"]=L(np.sqrt((W[:,P_IDX:P_IDX+n,:]**2).mean(axis=(1,2))))
        out[f"hv_{nm}"]=L(H[:,P_IDX:].max(1))-L(Vt[:,P_IDX:].max(1))
    e=(A[:,P_IDX:,:]**2).sum(axis=2); ce=np.cumsum(e,axis=1); tot=ce[:,-1:]+EPS
    frac=ce/tot; out["logE"]=L(tot[:,0])
    for q in [0.1,0.25,0.5,0.75,0.9]:
        out[f"tE{int(q*100)}"]=(np.argmax(frac>=q,axis=1)/FS).astype(np.float32)
    out["E_slope"]=(out["tE90"]-out["tE10"]).astype(np.float32)
    for nm,W in [("a",A),("d",D)]:
        ab=np.abs(W[:,P_IDX:,:]).max(axis=2); tp=ab.argmax(axis=1)/FS
        out[f"tpk_{nm}"]=tp.astype(np.float32)
        out[f"rise_{nm}"]=(L(ab.max(1))/(tp+0.05)).astype(np.float32)
    n3=600
    num=(V[:,P_IDX:P_IDX+n3,:]**2).sum(1); den=(D[:,P_IDX:P_IDX+n3,:]**2).sum(1)
    out["tauc"]=L(2*np.pi*np.sqrt((den/(num+1e-30)).mean(1)))
    for s in [1.0,2.0]:
        n=int(s*FS); nu=(V[:,P_IDX:P_IDX+n,:]**2).sum(1)
        dv=np.gradient(V[:,P_IDX:P_IDX+n,:],1/FS,axis=1)
        out[f"taup_{s:g}"]=L(2*np.pi*np.sqrt((nu/((dv**2).sum(1)+1e-30)).mean(1)))
    for nm,W in [("a",A),("d",D)]:
        f,Pxx=signal.welch(W[:,P_IDX:,:],fs=FS,nperseg=256,axis=1)
        Pm=Pxx.mean(axis=2); tote=Pm.sum(1)+EPS
        for lo,hi in [(0.1,1),(1,3),(3,5),(5,10),(10,20),(20,50),(50,100)]:
            m=(f>=lo)&(f<hi)
            out[f"bd{nm}_{lo:g}_{hi:g}"]=L(Pm[:,m].sum(1))
            out[f"bdr{nm}_{lo:g}_{hi:g}"]=(Pm[:,m].sum(1)/tote).astype(np.float32)
        out[f"cent_{nm}"]=((Pm*f).sum(1)/tote).astype(np.float32)
        out[f"fdom_{nm}"]=f[Pm.argmax(1)].astype(np.float32)
        out[f"lhr_{nm}"]=L(Pm[:,(f>=0.1)&(f<3)].sum(1))-L(Pm[:,(f>=10)&(f<50)].sum(1))
    seg=A[:,P_IDX:,:]
    out["kurt"]=stats.kurtosis(seg,axis=1).mean(1).astype(np.float32)
    out["skew"]=np.abs(stats.skew(seg,axis=1)).mean(1).astype(np.float32)
    out["zcr"]=(np.diff(np.sign(seg),axis=1)!=0).mean(axis=(1,2)).astype(np.float32)
    Sg=seg-seg.mean(1,keepdims=True)
    evl=np.linalg.eigvalsh(np.einsum("nti,ntj->nij",Sg,Sg)/Sg.shape[1])
    evl=np.maximum(evl,0)+1e-30
    out["rectilin"]=(1-(evl[:,0]+evl[:,1])/(2*evl[:,2])).astype(np.float32)
    out["planarity"]=(1-2*evl[:,0]/(evl[:,1]+evl[:,2])).astype(np.float32)
    F=pd.DataFrame(out)
    dist=meta.distance_km.values.astype(np.float32); dep=meta.depth_km.values.astype(np.float32)
    F["distance_km"]=dist; F["depth_km"]=dep
    F["snr_db"]=meta.snr_db.values.astype(np.float32)
    F["is_clipped"]=meta.is_clipped.values.astype(np.int8)
    F["logdist"]=np.log10(dist+1); F["logdep"]=np.log10(dep+1)
    F["hypo"]=np.sqrt(dist**2+dep**2); F["loghypo"]=np.log10(F.hypo+1)
    for nm in ["a","v","d"]:
        for s in WINS:
            F[f"C{nm}_{s:g}"]=F[f"P{nm}_{s:g}"]+F["loghypo"]
            F[f"C{nm}d_{s:g}"]=F[f"P{nm}_{s:g}"]+1.5*F["logdist"]
        for s1,s2 in [(0.5,1.0),(1.0,2.0),(2.0,4.0),(0.5,4.0)]:
            F[f"g{nm}_{s1:g}_{s2:g}"]=F[f"P{nm}_{s2:g}"]-F[f"P{nm}_{s1:g}"]
    print("  extract %.0fs -> %d fitur"%(time.time()-t0,F.shape[1]))
    return F.astype(np.float32)

def build_input(X, meta):
    """Input CNN gaya MagNet: BENTUK gelombang dinormalisasi per-record, lalu skala
    amplitudo disuntikkan balik sebagai skalar.

    Catatan lama 'jangan normalisasi amplitudo per-record' benar untuk fitur pohon dan
    SALAH TOTAL untuk CNN -- waveform mentah membentang 5 orde magnitudo dan konvolusi
    tidak bisa belajar apapun dari itu. Aturan tanpa cakupan itu menahan model deep
    selama empat notebook."""
    A=X.astype(np.float32); V=np.cumsum(_hp(A),axis=1)/FS; D=np.cumsum(_hp(V),axis=1)/FS
    chans=[]; scales=[]
    for W in (A,V,D):
        mx=np.abs(W).max(axis=(1,2),keepdims=True)+1e-20
        chans.append((W/mx).transpose(0,2,1)); scales.append(np.log10(mx[:,0,0]))
    Wn=np.concatenate(chans,axis=1).astype(np.float32)
    dist=meta.distance_km.values.astype(np.float32); dep=meta.depth_km.values.astype(np.float32)
    S=np.stack([*scales, np.log10(dist+1), np.log10(dep+1),
                np.log10(np.sqrt(dist**2+dep**2)+1),
                meta.snr_db.values.astype(np.float32)/40.0,
                meta.is_clipped.values.astype(np.float32)],axis=1).astype(np.float32)
    return Wn, S

Xtr_raw = np.load(DATA/"train"/"train_waveforms.npy")
Xte_raw = np.load(DATA/"test"/"test_waveforms.npy")
t0=time.time()
Ftr = extract(Xtr_raw, train); Fte = extract(Xte_raw, test)
Wtr, Str = build_input(Xtr_raw, train)
Wte, Ste = build_input(Xte_raw, test)
del Xtr_raw, Xte_raw
print("siap %.0fs | Wtr %s  Str %s"%(time.time()-t0, Wtr.shape, Str.shape))

# ---------------------------------------------------------------------------------
# SIDIK JARI INPUT -- memisahkan "beda data" dari "beda training" kalau hasilnya meleset.
#
# Notebook 09 menghasilkan model 0,0049 lebih buruk dari run lokal untuk resep yang
# IDENTIK, dengan korelasi OOF cuma 0,9722 (antar-paket 3-seed lokal: 0,9875). Kode
# `extract()` dan `build_input()` sudah dibandingkan baris demi baris dan sama persis,
# jadi tersangkanya versi library -- tapi itu tidak pernah bisa dibuktikan karena
# tidak ada satu pun angka input yang tercetak untuk dibandingkan.
#
# Kalau angka di bawah COCOK dengan acuan lokal, inputnya identik dan selisih hasil apa
# pun lahir di training (torch/cuDNN). Kalau TIDAK cocok, inputnya sendiri yang beda dan
# tidak ada gunanya menyalahkan training.
import scipy as _sp
print("\\nversi: numpy %s | scipy %s | torch %s"%(np.__version__, _sp.__version__, torch.__version__))
print("acuan lokal: numpy 1.26.4 | scipy 1.17.1 | torch 2.6.0+cu124")
_ACUAN = {"Wtr": 1.964203e+07, "Str": 1.907536e+05,
          "Wte": 4.208731e+06, "Ste": 4.244618e+04, "A_BASE": 4.658112e+05}
print("\\nSIDIK JARI INPUT            terhitung        acuan lokal   selisih")
_ada_beda = False
_AB = ["Cd_2","Cv_2","Ca_4","logdist","loghypo","logE","snr_db"]   # = A_BASE, didefinisikan
for _nm, _a in [("Wtr",Wtr), ("Str",Str), ("Wte",Wte), ("Ste",Ste),   # di sel berikutnya
                ("A_BASE", Ftr[_AB].values)]:
    _v = float(np.nansum(np.abs(np.asarray(_a, dtype=np.float64))))
    _rel = (_v-_ACUAN[_nm])/_ACUAN[_nm]
    if abs(_rel) > 1e-5: _ada_beda = True   # 1e-5: longgar thd urutan penjumlahan float
    print("  %-8s %18.6e %18.6e  %+9.2e"%(_nm, _v, _ACUAN[_nm], _rel))
print("  nonfinite di Ftr:", int((~np.isfinite(Ftr.values.astype(np.float64))).sum()),
      " (acuan lokal: 18, semuanya dari `kurt`)")
print("  -> " + ("INPUT BEDA dari lokal. Selisih hasil lahir di sini, bukan di training."
                 if _ada_beda else
                 "input identik dengan lokal. Selisih hasil apa pun lahir di training."))
'''

P_ARCH = '''import torch.nn as nn
from sklearn.model_selection import GroupKFold
from sklearn.linear_model import Ridge
A_BASE=["Cd_2","Cv_2","Ca_4","logdist","loghypo","logE","snr_db"]

class Blk(nn.Module):
    def __init__(s, ci, co, k=7, pool=4):
        super().__init__()
        s.c1=nn.Conv1d(ci,co,k,padding=k//2); s.b1=nn.BatchNorm1d(co)
        s.c2=nn.Conv1d(co,co,k,padding=k//2); s.b2=nn.BatchNorm1d(co)
        s.se=nn.Sequential(nn.AdaptiveAvgPool1d(1),nn.Conv1d(co,max(4,co//8),1),nn.SiLU(),
                           nn.Conv1d(max(4,co//8),co,1),nn.Sigmoid())
        s.sk=nn.Conv1d(ci,co,1) if ci!=co else nn.Identity()
        s.act=nn.SiLU(); s.pool=nn.MaxPool1d(pool)
    def forward(s,x):
        h=s.act(s.b1(s.c1(x))); h=s.b2(s.c2(h)); h=h*s.se(h)
        return s.pool(s.act(h+s.sk(x)))

class Net3(nn.Module):
    """CNN v3 notebook_8 (LB 0,1849). Acuan, bukan yang diuji di sini."""
    def __init__(s, n_scalar, w=64):
        super().__init__()
        s.body=nn.Sequential(Blk(9,w),Blk(w,w*2),Blk(w*2,w*3),Blk(w*3,w*4,k=5,pool=2),
                             Blk(w*4,w*4,k=3,pool=2))
        s.trunk=nn.Sequential(nn.Linear(w*8+n_scalar,256), nn.SiLU(), nn.Dropout(0.25),
                              nn.Linear(256,96), nn.SiLU())
        s.mag=nn.Linear(96,1); s.dep=nn.Linear(96,1)
    def forward(s,x,sc_):
        h=s.body(x); h=torch.cat([h.mean(-1),h.amax(-1),sc_],dim=1); h=s.trunk(h)
        return s.mag(h).squeeze(-1), s.dep(h).squeeze(-1)

def run(Wtr,Str,Wte,Ste, sw, seeds=(0,1,2), epochs=80, bs=128, lr=2.5e-3,
        avg_last=10, resid=True, arch=None):
    """Loop training CNN v3 persis seperti notebook_8.

    Empat hal yang membuat v3 menang: (1) kepala kedua memprediksi log10(depth), dihitung
    HANYA untuk record depth-desimal (di sana depth adalah inversi sungguhan, bukan default
    katalog); (2) augmentasi derau FISIK -- tempel jendela pre-P record lain, jadi derau
    stasiun sungguhan bukan Gaussian sintetis; (3) blok Squeeze-Excitation; (4) jadwal
    panjang + rata-rata bobot 10 epoch terakhir."""
    Xa=Ftr[A_BASE].values.astype(np.float64); Xa_te=Fte[A_BASE].values.astype(np.float64)
    dep_t=np.log10(d_tr+1).astype(np.float32); dep_ok=(~rnd_tr).astype(np.float32)
    noise=Wtr[:,:,:200].copy()
    oof=np.zeros(len(y)); pte=np.zeros(len(Wte))
    Xte_t=torch.tensor(Wte).to(DEV); Ste_t=torch.tensor(Ste).to(DEV)
    nf=0; t0=time.time()
    for seed in seeds:
        torch.manual_seed(seed); np.random.seed(seed)
        for ti,vi in GroupKFold(5).split(Wtr,y,ev):
            if resid:
                rg=Ridge(alpha=1.0).fit(Xa[ti],y[ti],sample_weight=sw[ti])
                tgt=(y-rg.predict(Xa)).astype(np.float32)
                off_v=rg.predict(Xa[vi]); off_t=rg.predict(Xa_te)
            else:
                tgt=y.astype(np.float32); off_v=0; off_t=0
            net=(arch or Net3)(Str.shape[1]).to(DEV)
            opt=torch.optim.AdamW(net.parameters(),lr=lr,weight_decay=2e-2)
            sch=torch.optim.lr_scheduler.OneCycleLR(opt,max_lr=lr,
                    total_steps=epochs*max(1,len(ti)//bs),pct_start=0.2)
            Xt=torch.tensor(Wtr[ti]); St=torch.tensor(Str[ti]); Nz=torch.tensor(noise[ti])
            tt=torch.tensor(tgt[ti]); wt=torch.tensor(sw[ti],dtype=torch.float32)
            dt=torch.tensor(dep_t[ti]); dk=torch.tensor(dep_ok[ti])
            Xv=torch.tensor(Wtr[vi]).to(DEV); Sv=torch.tensor(Str[vi]).to(DEV)
            av=np.zeros(len(vi)); at=np.zeros(len(Wte))
            for ep in range(epochs):
                net.train(); perm=torch.randperm(len(ti))
                for i in range(0,len(ti)-bs+1,bs):
                    b=perm[i:i+bs]; xb=Xt[b].clone(); sb=St[b].to(DEV)
                    th=torch.rand(len(b))*2*np.pi; cs,sn=torch.cos(th),torch.sin(th)
                    for k in (0,3,6):
                        e_,n_=xb[:,k].clone(),xb[:,k+1].clone()
                        xb[:,k]=cs[:,None]*e_-sn[:,None]*n_; xb[:,k+1]=sn[:,None]*e_+cs[:,None]*n_
                    if torch.rand(1).item()<0.5:
                        for k in (2,5,8): xb[:,k]*=-1
                    if torch.rand(1).item()<0.5:
                        j=torch.randint(0,len(ti),(len(b),))
                        amp=(torch.rand(len(b),1,1)*0.6)
                        xb=xb+amp*Nz[j].repeat(1,1,5)[:,:,:xb.shape[2]]
                    xb=xb.to(DEV)
                    pm,pdep=net(xb,sb)
                    lm=(wt[b].to(DEV)*(pm-tt[b].to(DEV)).abs()).sum()/wt[b].sum().to(DEV)
                    dkb=dk[b].to(DEV)
                    ld=((pdep-dt[b].to(DEV)).abs()*dkb).sum()/(dkb.sum()+1e-6)
                    opt.zero_grad(); (lm+0.15*ld).backward(); opt.step(); sch.step()
                if ep>=epochs-avg_last:
                    net.eval()
                    with torch.no_grad():
                        av+=net(Xv,Sv)[0].cpu().numpy()
                        at+=np.concatenate([net(Xte_t[i:i+512],Ste_t[i:i+512])[0].cpu().numpy()
                                            for i in range(0,len(Wte),512)])
            oof[vi]+=(av/avg_last+off_v)/len(seeds)
            pte+=(at/avg_last+off_t)/(5*len(seeds))
            nf+=1
            print("    fold %2d/%d selesai  (%.0f menit terpakai, ~%.0f menit tersisa)"
                  %(nf,5*len(seeds),(time.time()-t0)/60,
                    (time.time()-t0)/nf*(5*len(seeds)-nf)/60), flush=True)
    return oof,pte
'''

P_BLEND = '''REF = np.load(REFP, allow_pickle=True) if REFP else None
CAND = [str(x) for x in REF["__cand__"]] if REF is not None else []

def ref_stack():
    O=np.stack([REF[f"{n}__oof"].astype(np.float64) for n in CAND])
    E=np.stack([REF[f"{n}__pte"].astype(np.float64) for n in CAND])
    return O,E

# Validasi ref SEKARANG, bukan berjam-jam kemudian setelah training selesai.
# Kalau file-nya benar, blend 8 kandidat itu harus mereproduksi lb_real notebook_8.
if REF is not None:
    _o = post_tr(REF["__w__"] @ ref_stack()[0]); _v = sc(_o)
    print("ref termuat: %d kandidat -> lb_real %.4f  (nb8 seharusnya 0,1762)"%(len(CAND),_v))
    print("   " + ("COCOK -- verdikt bisa dipercaya." if abs(_v-0.1762) < 0.0005 else
                   "TIDAK COCOK -- file ref salah/rusak, verdikt tidak bisa dipercaya."))
    del _o, _v

def blend_search(names, Otr, Ote, ref_oof, nsamp=8000, alpha=0.6, seed=0):
    """Protokol nb6/nb8: cari bobot di separuh event, ukur di separuh LAIN, 12 belahan;
    bobot final = rata-rata lintas belahan (bukan argmin di data penuh).

    Ini perlu. Waktu MLP divergen (OOF 0,778) ikut jadi kandidat di nb5, pencarian bobot
    tetap memberinya 0,36 dan 'memperbaiki' skor. Jaga kandidat tetap sedikit."""
    rng=np.random.RandomState(seed)
    W=np.vstack([rng.dirichlet(np.ones(len(names))*alpha,size=nsamp),np.eye(len(names))])
    Q=np.stack([post_tr(x@Otr) for x in W])
    uev=np.unique(ev); gains=[];opt=[];ws=[];dgains=[]
    for rep in range(6):
        r=np.random.RandomState(100+rep); perm=r.permutation(uev)
        h1=np.isin(ev,perm[:len(perm)//2])
        for keep in (h1,~h1):
            ss=Scorer(EVR,keep); sh=Scorer(EVR,~keep); shd=SideScorer(True,~keep)
            v=np.array([ss(q) for q in Q]); i=v.argmin()
            gains.append(sh(Q[i])-sh(ref_oof)); opt.append(sh(Q[i])-v[i]); ws.append(W[i])
            dgains.append(shd(Q[i])-shd(ref_oof))     # DIAGNOSTIK 4: gain di sisi desimal
    wm=np.mean(ws,0); wm/=wm.sum()
    o=post_tr(wm@Otr); p=post_te(wm@Ote); om=float(np.mean(opt))/np.sqrt(2)
    return dict(w=wm, oof=o, pte=p, lb_real=float(sc(o)), jujur=float(sc(o))+om,
                optimisme=om, gain=float(np.mean(gains)), menang=int(sum(g<0 for g in gains)),
                bias=bias_rnd(o), dec=part_real(o,True), rnd=part_real(o,False),
                dec_gain=float(np.mean(dgains)),
                dec_menang=int(sum(g<0 for g in dgains)),
                mean_rnd_te=float(p[MT].mean()), sd_rnd_te=float(p[rnd_te].std()))

TARGET = [("peringkat 1 (Kingpul)", 0.1837), ("0,1800", 0.1800),
          ("0,1750", 0.1750), ("0,1700", 0.1700), ("0,1600", 0.1600)]

def verdikt(res, nama):
    """Cetak diagnostik transfer + verdikt target. Tiga diagnostik wajib sebelum submit."""
    est = lb_hat(res["lb_real"])
    print("="*70); print("VERDIKT -- %s"%nama); print("="*70)
    print("  lb_real        %.4f   (notebook_8 = 0,1762)"%res["lb_real"])
    print("  lb_real jujur  %.4f   (+optimisme seleksi %.4f)"%(res["jujur"],res["optimisme"]))
    print("  gain vs nb8    %+.4f  (menang %d/12 belahan)"%(res["gain"],res["menang"]))
    print("  dec %.4f  rnd %.4f   (nb8: 0,1437 / 0,2074)"%(res["dec"],res["rnd"]))
    print()
    print("  --- diagnostik transfer (SEMUA wajib aman sebelum submit) ---")
    ok1 = res["bias"] <= 0.05
    ok2 = abs(res["mean_rnd_te"]-5.272) <= 0.03
    ok3 = res["sd_rnd_te"] <= 0.42
    ok4 = res["lb_real"] < LB_JUARA
    print("  bias_rnd            %+.3f   %s  (tolak kalau > 0,05; nb8 +0,031)"
          %(res["bias"], "AMAN " if ok1 else "BAHAYA"))
    print("  mean test bulat<100 %.3f    %s  (optimum ~5,272; nb8 5,259)"
          %(res["mean_rnd_te"], "AMAN " if ok2 else "AWAS  "))
    print("  sd test sisi bulat  %.3f    %s  (naik = LB memburuk; nb8 0,396)"
          %(res["sd_rnd_te"], "AMAN " if ok3 else "AWAS  "))
    print("  lb_real vs juara    %.4f   %s  (harus < %.4f = notebook_8)"
          %(res["lb_real"], "AMAN " if ok4 else "BAHAYA", LB_JUARA))
    print()
    print("  --- informasi saja, BUKAN kriteria seleksi ---")
    print("  gain sisi desimal   %+.4f  (menang %d/12)"
          %(res.get("dec_gain",float("nan")), res.get("dec_menang",-1)))
    print("  Jangan pakai angka ini untuk menerima/menolak model per-record. Aturan lama")
    print("  'gain sisi desimal harus negatif' DICABUT: notebook_10 dibangun untuk")
    print("  memaksimalkannya dan LB-nya rugi 0,0022 (0,1849 -> 0,1871). Sisi desimal")
    print("  sudah menyentuh oracle (0,1437 vs ~0,1488); mengoptimalkannya cuma")
    print("  mengorbankan sisi bulat, yaitu 51% metrik dan seluruh headroom tersisa.")
    print()
    print("  ESTIMASI LB = lb_real + 0,0096 = %.4f   (sd 0,0036 -- TIDAK STABIL)"%est)
    print("  --- verdikt target ---")
    for nm,t in TARGET:
        d=est-t
        print("    %-22s %.4f   %s (selisih %+.4f)"
              %(nm,t,"TERCAPAI" if d<=0 else "belum   ",d))
    print("="*70)
    if not ok4:
        print("BAHAYA -- lb_real blend ini TIDAK mengalahkan notebook_8 (0,1762).")
        print("JANGAN disubmit. `notebook_10` melanggar aturan ini atas dasar teori dan")
        print("rugi 0,0022. Satu kegagalan LB bukan dasar cukup untuk membatalkan metrik")
        print("peringkat yang benar 4 dari 5 kali.")
    if not (ok1 and ok2 and ok3):
        print("PERINGATAN: diagnostik transfer tidak aman. `lb_real` mengukur data TRAIN;")
        print("`bias_rnd` dan mean subset mengukur JARAK KE TEST. Kalau bertabrakan, yang")
        print("kedua menang -- notebook_2 dan notebook_5 dua-duanya CV-nya membaik lalu")
        print("LB-nya memburuk karena aturan ini dilanggar.")
    return est

HASIL = []          # file yang dihasilkan notebook ini, untuk dibundel di akhir

def catat(p):
    p = str(p)
    if p not in HASIL: HASIL.append(p)
    return p

def simpan(nama, oof, pte, res=None):
    catat(OUT/f"{nama}.npz"); np.savez(OUT/f"{nama}.npz", oof=oof, pte=pte)
    print("tersimpan:", OUT/f"{nama}.npz")
    if res is not None:
        sub=pd.DataFrame({"sample_id":test.sample_id,"magnitude":np.round(res["pte"],3)})
        sub.to_csv(catat(OUT/f"{nama}_submission.csv"), index=False)
        json.dump({k:(v if isinstance(v,str) else np.asarray(v).tolist() if not np.isscalar(v) else float(v))
                   for k,v in res.items() if k not in ("oof","pte")},
                  open(catat(OUT/f"{nama}_score.json"),"w"), indent=2)
        print("tersimpan:", OUT/f"{nama}_submission.csv")

def bundel(nama_zip):
    """Bungkus hasil notebook INI jadi satu zip supaya gampang diunduh dari Kaggle.

    Hanya file yang dicatat lewat `catat()` yang ikut -- waveform dan input CNN yang
    berukuran ratusan MB sengaja ditinggal, karena yang dibutuhkan di lokal cuma .npz
    prediksi, .csv submission, dan .json skor."""
    z = OUT/f"{nama_zip}.zip"
    files = [f for f in HASIL if os.path.exists(f)]
    if not files:
        print("tidak ada file untuk dibundel."); return None
    with zipfile.ZipFile(z,"w",zipfile.ZIP_DEFLATED) as zf:
        for f in files: zf.write(f, arcname=os.path.basename(f))
    tot = sum(os.path.getsize(f) for f in files)/1024
    print("\\n" + "="*70)
    print("BUNDEL SIAP DIUNDUH: %s   (%d file, %.0f KB)"%(z, len(files), tot))
    for f in files: print("   -", os.path.basename(f))
    print("="*70)
    print("Unduh zip itu dari panel Output di kanan, lalu ekstrak .npz-nya ke")
    print("`Case 1/cache/` supaya bisa dipakai blend berikutnya di lokal.")
    return z
'''

HEAD_UMUM = """## Cara pakai

1. **Settings -> Accelerator -> GPU** (T4 atau P100).
2. Tambahkan kompetisinya lewat **Add Input**.
3. Upload folder `belum_run/ref/` sebagai **Kaggle Dataset**, lalu Add Input juga.
   Isinya `nb8_ref.npz` — prediksi 8 kandidat notebook_8. Tanpa file itu notebook tetap
   jalan, tapi hanya bisa melaporkan skor model tunggal dan **tidak bisa memberi verdikt
   terhadap target LB**.
4. Run All.
5. Sel terakhir membungkus semua hasil jadi **satu file zip** di `/kaggle/working/`.
   Unduh zip itu dari panel Output, ekstrak `.npz`-nya ke `Case 1/cache/`.

## Yang perlu dibaca sebelum percaya angka apapun

`eb_twmae` mentah **cacat** di sisi depth-bulat: rekonstruksi event lewat
`groupby(depth_km, magnitude)` melebur record depth-bulat jadi pseudo-event sampai
**401 record**, sehingga CV over-weight ekor sekitar **3x**. Notebook ini memakai
`lb_real`, bukan `eb_twmae`.

Dan `lb_real` sendiri mengukur **data train**. `bias_rnd` serta mean dan sd prediksi
subset depth-bulat mengukur **jarak ke test**. Kalau keduanya bertabrakan, **yang kedua
menang** — `notebook_2` dan `notebook_5` dua-duanya memperbaiki CV lalu memburuk di LB.
"""

TARGET_MD = """## Aritmatika target — baca ini dulu

Kalibrasi dari 3 submission nyata (R2 0,92): **LB ≈ `lb_real` + 0,0082** (sd 0,0028).

| Target LB | butuh `lb_real` | Δ dari nb8 (0,1762) |
|---|---|---|
| 0,1837 (peringkat 1) | 0,1755 | −0,0007 |
| 0,1800 | 0,1718 | −0,0044 |
| 0,1750 | 0,1668 | −0,0094 |
| **0,1700** | **0,1618** | **−0,0144** |
| **0,1600** | **0,1518** | −0,0244 |

Terobosan terbesar yang pernah ditemukan di repo ini — CNN v3 di `notebook_8` — bernilai
**−0,0070**. Jadi **LB 0,17 butuh dua kali lipat terobosan terbesar itu**.

**LB 0,16 butuh `lb_real` 0,1518, dan itu di BAWAH batas oracle-grouping 0,1543** — yaitu
skor yang dicapai kalau kita *tahu persis* record mana milik event mana. Post-processing
tidak bisa menembusnya dengan model dasar sekarang; hanya model per-record yang jauh lebih
akurat yang bisa. Perlakukan **0,16 sebagai di luar jangkauan** pendekatan ini.

Karena itu tiap notebook mencetak verdikt eksplisit terhadap kelima ambang di atas.
"""


def prelude_cells(judul, deskripsi, extra_head=""):
    return [
        md("# %s\n\n%s" % (judul, deskripsi)),
        md(TARGET_MD),
        md(HEAD_UMUM + extra_head),
        md("---\n## 0. Setup, metrik, fitur\n\nSemua kode inti disalin apa adanya dari "
           "`lab/` supaya angkanya sebanding dengan run lokal."),
        co(P_SETUP), co(P_METRIK), co(P_FASTSCORE), co(P_FITUR), co(P_ARCH), co(P_BLEND),
    ]


# ---------------------------------------------------------------- arsitektur
ARCH_SRC = {}

ARCH_SRC["cnn8"] = ('''class _Inc(nn.Module):
    def __init__(s, ci, co, pool=4):
        super().__init__()
        b=co//4
        s.br=nn.ModuleList([nn.Conv1d(ci,b,k,padding=k//2) for k in (3,9,21,41)])
        s.bn=nn.BatchNorm1d(co)
        s.se=nn.Sequential(nn.AdaptiveAvgPool1d(1),nn.Conv1d(co,max(4,co//8),1),nn.SiLU(),
                           nn.Conv1d(max(4,co//8),co,1),nn.Sigmoid())
        s.sk=nn.Conv1d(ci,co,1); s.act=nn.SiLU(); s.pool=nn.MaxPool1d(pool)
    def forward(s,x):
        h=s.bn(torch.cat([b(x) for b in s.br],1)); h=h*s.se(h)
        return s.pool(s.act(h+s.sk(x)))

class Net8(nn.Module):
    """Inception 1D: tiap blok melihat empat skala waktu sekaligus -- kernel 3/9/21/41
    sampel = 15/45/105/205 ms pada 200 Hz.

    Kandungan frekuensi gelombang P berbeda tajam antar magnitudo (`tauc` dan `taup`
    adalah fitur EEW klasik justru karena itu), dan gempa besar melepas energi pada skala
    waktu yang jauh lebih panjang. Net3 memakai satu ukuran kernel per tingkat; ini
    melihat empat skala paralel di setiap tingkat."""
    def __init__(s, n_scalar, w=64):
        super().__init__()
        s.body=nn.Sequential(_Inc(9,w),_Inc(w,w*2),_Inc(w*2,w*3),_Inc(w*3,w*4,pool=2),
                             _Inc(w*4,w*4,pool=2))
        s.trunk=nn.Sequential(nn.Linear(w*8+n_scalar,288), nn.SiLU(), nn.Dropout(0.25),
                              nn.Linear(288,96), nn.SiLU())
        s.mag=nn.Linear(96,1); s.dep=nn.Linear(96,1)
    def forward(s,x,sc_):
        h=s.body(x); h=torch.cat([h.mean(-1),h.amax(-1),sc_],dim=1); h=s.trunk(h)
        return s.mag(h).squeeze(-1), s.dep(h).squeeze(-1)
''', "Net8", dict(epochs=85, lr=2e-3, avg_last=12), "~1,5-2,5 jam")

ARCH_SRC["cnn7"] = ('''class Net7(nn.Module):
    """TCN dilatasi: reseptif lebar TANPA pooling sama sekali.

    Net3 dan Net5 membuang resolusi waktu lewat MaxPool bertingkat (faktor 256 total).
    Net7 memakai dilatasi (1,2,4,8,16,32,64): satu stride-2 di depan, lalu resolusi
    bertahan penuh sampai kepala. Kalau detail waktu halus memang penting untuk magnitudo
    -- dan onset P adalah kejadian berskala milidetik -- model ini melihat sesuatu yang
    Net3 buang."""
    def __init__(s, n_scalar, w=72):
        super().__init__()
        s.inp=nn.Sequential(nn.Conv1d(9,w,9,stride=2,padding=4), nn.BatchNorm1d(w), nn.SiLU())
        L=[]
        for d in (1,2,4,8,16,32,64):
            L.append(nn.Sequential(
                nn.Conv1d(w,w,5,padding=2*d,dilation=d), nn.BatchNorm1d(w), nn.SiLU(),
                nn.Conv1d(w,w,1), nn.BatchNorm1d(w)))
        s.blocks=nn.ModuleList(L); s.act=nn.SiLU()
        s.head=nn.Sequential(nn.Conv1d(w,w*2,1), nn.BatchNorm1d(w*2), nn.SiLU())
        s.trunk=nn.Sequential(nn.Linear(w*4+n_scalar,256), nn.SiLU(), nn.Dropout(0.25),
                              nn.Linear(256,96), nn.SiLU())
        s.mag=nn.Linear(96,1); s.dep=nn.Linear(96,1)
    def forward(s,x,sc_):
        h=s.inp(x)
        for b in s.blocks: h=s.act(h+b(h))
        h=s.head(h)
        h=torch.cat([h.mean(-1),h.amax(-1),sc_],dim=1); h=s.trunk(h)
        return s.mag(h).squeeze(-1), s.dep(h).squeeze(-1)
''', "Net7", dict(epochs=85, lr=2e-3, avg_last=12), "~1-2 jam")

ARCH_SRC["cnn5"] = ('''class Net5(nn.Module):
    """v3 diperlebar (w=64 -> 80, 5 -> 6 blok) dan satu tingkat pooling dilepas di awal:
    blok pertama memampatkan 2x, bukan 4x.

    Yang kedua itulah biayanya -- blok pertama mengerjakan 80 kanal pada panjang penuh
    1000 sampel, kira-kira 4x biaya v3 keseluruhan. Taruhannya: resolusi waktu di lapisan
    awal memang berharga untuk onset P."""
    def __init__(s, n_scalar, w=80):
        super().__init__()
        s.body=nn.Sequential(Blk(9,w,k=9,pool=2), Blk(w,w*2,k=7,pool=4),
                             Blk(w*2,w*3,k=7,pool=2), Blk(w*3,w*3,k=5,pool=2),
                             Blk(w*3,w*4,k=5,pool=2), Blk(w*4,w*4,k=3,pool=2))
        s.trunk=nn.Sequential(nn.Linear(w*8+n_scalar,320), nn.SiLU(), nn.Dropout(0.3),
                              nn.Linear(320,128), nn.SiLU())
        s.mag=nn.Linear(128,1); s.dep=nn.Linear(128,1)
    def forward(s,x,sc_):
        h=s.body(x); h=torch.cat([h.mean(-1),h.amax(-1),sc_],dim=1); h=s.trunk(h)
        return s.mag(h).squeeze(-1), s.dep(h).squeeze(-1)
''', "Net5", dict(epochs=100, lr=2e-3, avg_last=12), "~4-6 jam (PALING MAHAL)")

ARCH_SRC["cnn6"] = ('''class Net6(nn.Module):
    """Frontend konvolusi pendek (1000 -> 62 token) lalu 3 lapis transformer encoder.

    Bedanya dengan Net3 bukan sekadar kapasitas: Net3 mengagregasi lewat mean/max global
    atas seluruh waktu, sedangkan attention bisa MEMILIH jendela waktu mana yang penting
    per-record -- menimbang onset P berbeda dari koda tergantung SNR dan jarak record itu.

    Taruhan bervarians paling tinggi di folder ini: ukuran sampel efektif cuma ~905 EVENT
    (bukan 10.505 record), dan transformer biasanya kurang pada data sekecil itu."""
    def __init__(s, n_scalar, w=64, h=160, nl=3):
        super().__init__()
        s.body=nn.Sequential(Blk(9,w,k=9,pool=4), Blk(w,w*2,k=7,pool=4))   # 1000 -> 62
        s.proj=nn.Linear(w*2,h)
        s.pos=nn.Parameter(torch.randn(1,64,h)*0.02)
        enc=nn.TransformerEncoderLayer(h,8,h*3,dropout=0.1,batch_first=True,
                                       norm_first=True,activation="gelu")
        s.tr=nn.TransformerEncoder(enc,nl)
        s.trunk=nn.Sequential(nn.Linear(2*h+n_scalar,256), nn.SiLU(), nn.Dropout(0.25),
                              nn.Linear(256,96), nn.SiLU())
        s.mag=nn.Linear(96,1); s.dep=nn.Linear(96,1)
    def forward(s,x,sc_):
        h=s.body(x).transpose(1,2)
        h=s.proj(h)+s.pos[:,:h.shape[1]]
        h=s.tr(h)
        h=torch.cat([h.mean(1),h.amax(1),sc_],dim=1); h=s.trunk(h)
        return s.mag(h).squeeze(-1), s.dep(h).squeeze(-1)
''', "Net6", dict(epochs=90, lr=1.5e-3, avg_last=12), "~2-3 jam")


def arch_notebook(key, judul, deskripsi, catatan_arsitektur):
    src, cls, kw, waktu = ARCH_SRC[key]
    cells = prelude_cells(
        judul, deskripsi,
        "\n**Perkiraan waktu di GPU Kaggle (T4): %s.** Notebook mencetak sisa waktu "
        "setiap fold selesai, jadi progresnya kelihatan sejak fold pertama.\n" % waktu)
    cells.append(md("---\n## 1. Arsitektur yang diuji\n\n" + catatan_arsitektur))
    cells.append(co(src))
    cells.append(md(
        "---\n## 2. Training\n\n15 fold total (3 seed x 5 GroupKFold berbasis event). "
        "**GroupKFold wajib**: `KFold` biasa memberi optimisme palsu **0,031** karena "
        "record gempa yang sama bocor antar-fold lewat `depth_km` yang identik."))
    cells.append(co(
        'sw = make_sw(power=0.5)\n'
        't0 = time.time()\n'
        'oof, pte = run(Wtr, Str, Wte, Ste, sw, seeds=(0,1,2), %s, arch=%s)\n'
        'simpan("%s", oof, pte)\n'
        'print("\\n%s selesai dalam %%.0f menit"%%((time.time()-t0)/60))\n'
        'print("  lb_real  %%.4f"%%lb_real(oof))\n'
        'print("  dec %%.4f   rnd %%.4f   bias_rnd %%+.3f"\n'
        '      %%(part_real(oof,True), part_real(oof,False), bias_rnd(oof)))\n'
        'print("\\npembanding model TUNGGAL (makin kecil makin baik):")\n'
        'print("  cnn3_avg 0,2074 | cnn3_dir 0,2116 | LightGBM terbaik 0,2030")\n'
        'if REF is not None:\n'
        '    print()\n'
        '    for n in CAND:\n'
        '        print("  korelasi vs %%-10s %%.3f"%%(n, np.corrcoef(oof, REF[n+"__oof"])[0,1]))\n'
        '    print("\\nKorelasi RENDAH lebih berharga daripada skor tunggal yang bagus:")\n'
        '    print("CNN v3 KALAH dari LightGBM terbaik sebagai model tunggal (0,2074 vs")\n'
        '    print("0,2030), tapi dapat bobot blend 0,404 -- kandidat tunggal terbesar --")\n'
        '    print("semata karena korelasinya cuma 0,878.")\n'
        % (", ".join("%s=%r" % (k, v) for k, v in kw.items()), cls, key, cls)))
    cells.append(md(
        "---\n## 3. Blend + verdikt target\n\nBobot dicari di separuh event dan diukur di "
        "separuh **lain**, 12 belahan; bobot final = rata-rata lintas belahan, bukan "
        "argmin di data penuh. Optimisme seleksi ikut **diukur**, tidak diasumsikan nol."))
    cells.append(co(
        'if REF is None:\n'
        '    print("nb8_ref.npz tidak ditemukan -- verdikt blend dilewati.")\n'
        '    print("Upload belum_run/ref/ sebagai Kaggle Dataset lalu jalankan ulang sel ini.")\n'
        'else:\n'
        '    Oref, Eref = ref_stack()\n'
        '    ref_oof = post_tr(REF["__w__"] @ Oref)\n'
        '    print("acuan notebook_8: lb_real=%%.4f   [LB aktual 0,1849, peringkat 2]"%%sc(ref_oof))\n'
        '    names = CAND + ["%s"]\n'
        '    Otr = np.vstack([Oref, oof[None,:]]); Ote = np.vstack([Eref, pte[None,:]])\n'
        '    res = blend_search(names, Otr, Ote, ref_oof)\n'
        '    print("\\nbobot:", dict(zip(names, np.round(res["w"],3))))\n'
        '    print("bobot model baru: %%.3f\\n"%%res["w"][-1])\n'
        '    est = verdikt(res, "notebook_8 + %s")\n'
        '    simpan("blend_%s", res["oof"], res["pte"], res)\n' % (key, cls, key)))
    cells.append(md("---\n## 4. Bungkus hasil jadi satu zip"))
    cells.append(co('bundel("hasil_%s")\n' % key))
    return nb(cells)


# ---------------------------------------------------------------- set-transformer
def set_src():
    s = (_path.ROOT/"lab"/"lab_set.py").read_text(encoding="utf-8")
    s = s.split('DEV = "cuda" if torch.cuda.is_available() else "cpu"', 1)[1]
    s = s.replace("C.", "")
    s = s.replace("Ftr, Fte = get_feats()", "pass")
    s = s.replace("def run(", "def run_set(")
    return s.strip() + "\n"


def set_notebook():
    cells = prelude_cells(
        "kaggle 01 — Set-Transformer atas grup depth",
        "Satu-satunya ide sesudah `notebook_8` yang **gain-nya sudah terukur di lokal**: "
        "−0,0021 `lb_real`, menang **11/12** belahan. Sisanya di folder ini masih hipotesis.\n\n"
        "Tapi separuh gain itu ternyata **pergeseran rata-rata sisi depth-bulat** (+0,042), "
        "bukan koreksi per-record — dan itu persis prior katalog train yang membuat "
        "`notebook_2` dan `notebook_5` rugi di LB. Versi di notebook ini dilatih dengan "
        "**target yang sudah di-demean per subset**, sehingga model tidak punya cara untuk "
        "mempelajari prior itu sama sekali. Versi demean menahan −0,0011 dengan `bias_rnd` "
        "tidak bergerak sedikit pun.",
        "\n**Perkiraan waktu di GPU Kaggle (T4): ~30–45 menit.** Jalankan ini duluan — "
        "paling murah dan satu-satunya yang sudah terbukti.\n")
    cells.append(md("""---
## 1. Kenapa sisi depth-bulat yang disasar

| | `lb_real` sekarang | oracle grouping | headroom |
|---|---|---|---|
| sisi desimal | 0,1437 | ~0,1488 | habis |
| **sisi bulat** | **0,2074** | **0,1596** | **0,048** |

Hampir **seluruh** headroom yang tersisa ada di sisi depth-bulat, dan sebabnya jelas.
Record depth-desimal di-smooth ke median grupnya, dan grup di sana ≈ event nyata. Untuk
`depth = 10.0`, satu grup mencampur **1.633 record dari 21 gempa berbeda** — median grupnya
derau, jadi sisi itu tidak di-smooth sama sekali dan tertinggal jauh.

Dua usaha memulihkan grouping sudah **gagal**:

| usaha | hasil |
|---|---|
| classifier pasangan co-membership (nb7), AUC 0,79 | cuma memanen 0,3–1,0% headroom |
| sidik derau pre-P sebagai identitas stasiun | AUC 0,56; smoothing tetangga **memperburuk** |

Yang kedua gagal karena sinyalnya terlalu lemah. Yang pertama gagal karena classifier-nya
**hanya yakin untuk pasangan yang prediksinya sudah mirip** — jadi tidak menambah
informasi apa pun.

Set-transformer menyerang dari sudut lain: bukan pairwise lalu smoothing berbasis
probabilitas, melainkan **set-level dan dilatih end-to-end** pada metrik yang benar.
Attention yang memutuskan record mana saling co-belong."""))
    cells.append(md("""### Dua hal yang membuat evaluasinya jujur

**Set dibentuk hanya dari record yang tersedia di himpunan yang sedang dinilai** — untuk
OOF berarti di dalam fold validasi, untuk test di dalam test. Itu meniru kondisi test-time
persis. Kalau set dibentuk dari seluruh data train, model dapat konteks yang tidak akan
pernah ia punya saat inferensi, dan skornya jadi bohong.

**Target di-demean per subset.** Tanpa itu model belajar bahwa depth bulat rata-rata
M 5,45 vs desimal 5,19 — artefak katalog, bukan fisika — lalu mendorong `bias_rnd` dari
+0,031 ke +0,044. Proporsi depth-bulat **32% di train tapi 51% di test**, jadi prior itu
selalu merugi di LB."""))
    cells.append(co(set_src()))
    cells.append(md(
        "---\n## 2. Training\n\nInput model = prediksi blend `notebook_8` + fitur per-record. "
        "Yang dipelajari adalah **koreksi** terhadap blend itu, bukan magnitudo dari nol."))
    cells.append(co(
        'if REF is None:\n'
        '    raise SystemExit(\n'
        '        "BERHENTI: nb8_ref.npz belum terpasang.\\n"\n'
        '        "Notebook ini tidak melatih model berdiri sendiri -- ia mempelajari KOREKSI\\n"\n'
        '        "terhadap blend notebook_8, jadi prediksi 8 kandidat itu wajib ada.\\n"\n'
        '        "Langkah pemasangannya sudah dicetak di output sel Setup di atas.\\n"\n'
        '        "Notebook 02-05 TIDAK butuh file ini untuk melatih -- kalau mau langsung\\n"\n'
        '        "pakai GPU-nya sekarang, jalankan salah satu dari itu dulu.")\n'
        'Oref, Eref = ref_stack()\n'
        'btr = REF["__w__"] @ Oref; bte = REF["__w__"] @ Eref\n'
        'base = post_tr(btr); baset = post_te(bte)\n'
        'print("acuan notebook_8: lb_real=%.4f  rnd=%.4f  bias=%+.3f   [LB aktual 0,1849]"\n'
        '      %(sc(base), part_real(base,False), bias_rnd(base)))\n'
        't0=time.time()\n'
        'corr, cte = run_set(btr, bte, seeds=(0,1,2), epochs=60)\n'
        'print("selesai %.0f menit | koreksi sd=%.4f  mean di MR=%+.4f"\n'
        '      %((time.time()-t0)/60, corr.std(), corr[MR].mean()))\n'
        'np.savez(catat(OUT/"set2.npz"), corr=corr, cte=cte)\n'))
    cells.append(md(
        "---\n## 3. Seleksi `lam` yang jujur + verdikt\n\n`lam` dipilih di separuh event dan "
        "diukur di separuh **lain**. Hasil lokal sebagai pembanding: versi tanpa demean "
        "memberi gain −0,0021 (menang 11/12); versi demean −0,0011 dengan `bias_rnd` tetap "
        "+0,031."))
    cells.append(co(
        'grid=[0.0,0.1,0.15,0.2,0.25,0.3,0.4,0.5,0.6,0.75]\n'
        'Q=np.stack([post_tr(btr+l*corr) for l in grid])\n'
        'for l,q in zip(grid,Q):\n'
        '    print("  lam=%.2f  lb_real=%.4f  dec=%.4f  rnd=%.4f  bias=%+.3f"\n'
        '          %(l, sc(q), part_real(q,True), part_real(q,False), bias_rnd(q)))\n'
        'uev=np.unique(ev); gains=[]; sel=[]\n'
        'for rep in range(6):\n'
        '    r=np.random.RandomState(100+rep); perm=r.permutation(uev)\n'
        '    h1=np.isin(ev,perm[:len(perm)//2])\n'
        '    for keep in (h1,~h1):\n'
        '        ss=Scorer(EVR,keep); sh=Scorer(EVR,~keep)\n'
        '        v=np.array([ss(q) for q in Q]); i=v.argmin()\n'
        '        gains.append(sh(Q[i])-sh(base)); sel.append(grid[i])\n'
        'lam=float(np.median(sel))\n'
        'print("\\ngain holdout jujur %+.5f (menang %d/12) | lam median %.2f"\n'
        '      %(np.mean(gains), sum(g<0 for g in gains), lam))\n'
        'oof_f = post_tr(btr+lam*corr); pte_f = post_te(bte+lam*cte)\n'
        'res = dict(w=np.array([lam]), oof=oof_f, pte=pte_f, lb_real=float(sc(oof_f)),\n'
        '           jujur=float(sc(oof_f)), optimisme=0.0, gain=float(np.mean(gains)),\n'
        '           menang=int(sum(g<0 for g in gains)), bias=bias_rnd(oof_f),\n'
        '           dec=part_real(oof_f,True), rnd=part_real(oof_f,False),\n'
        '           mean_rnd_te=float(pte_f[MT].mean()), sd_rnd_te=float(pte_f[rnd_te].std()))\n'
        'est = verdikt(res, "notebook_8 + koreksi set-transformer (lam=%.2f)"%lam)\n'
        'simpan("blend_set2", oof_f, pte_f, res)\n'))
    cells.append(md("---\n## 4. Bungkus hasil jadi satu zip"))
    cells.append(co('bundel("hasil_set_transformer")\n'))
    return nb(cells)


# ---------------------------------------------------------------- tulis
files = {
    "01_set_transformer.ipynb": set_notebook(),
    "02_cnn8_inception.ipynb": arch_notebook(
        "cnn8", "kaggle 02 — CNN Inception 1D (multi-skala)",
        "Diversitas arsitektur adalah pengali terbesar di blend ini. CNN v3 **kalah** dari "
        "LightGBM terbaik sebagai model tunggal (0,2074 vs 0,2030) tapi dapat bobot blend "
        "**0,404** — kandidat tunggal terbesar — semata karena korelasinya cuma 0,878.\n\n"
        "Jadi yang dikejar di sini bukan skor tunggal terbaik, melainkan **korelasi rendah "
        "dengan skor yang setara**.",
        "Net3 memakai satu ukuran kernel per tingkat (7, 7, 7, 5, 3). Net8 memakai **empat "
        "kernel paralel di setiap blok** — 3/9/21/41 sampel, yaitu 15/45/105/205 ms pada "
        "200 Hz.\n\n"
        "Alasannya fisik: kandungan frekuensi gelombang P berbeda tajam antar magnitudo — "
        "`tauc` dan `taup` adalah fitur EEW klasik justru karena itu — dan gempa besar "
        "melepas energi pada skala waktu yang jauh lebih panjang. Melihat empat skala "
        "sekaligus di tiap tingkat adalah bias induktif yang tepat untuk sifat itu."),
    "03_cnn7_tcn_dilatasi.ipynb": arch_notebook(
        "cnn7", "kaggle 03 — TCN dilatasi (tanpa pooling)",
        "Varian termurah di folder ini, dan sumbu diversitasnya paling bersih: **tidak ada "
        "MaxPool sama sekali**.",
        "Net3 dan Net5 membuang resolusi waktu lewat MaxPool bertingkat (4, 4, 4, 2, 2 = "
        "faktor 256). Net7 memakai konvolusi **dilatasi** (1, 2, 4, 8, 16, 32, 64) untuk "
        "mendapat reseptif yang sama lebarnya **tanpa membuang resolusi**: satu stride-2 di "
        "depan, lalu resolusi bertahan penuh sampai kepala.\n\n"
        "Kalau detail waktu halus memang penting untuk magnitudo — dan onset P adalah "
        "kejadian berskala milidetik — model ini akan melihat sesuatu yang Net3 buang."),
    "04_cnn5_konvolusi_dalam.ipynb": arch_notebook(
        "cnn5", "kaggle 04 — CNN v3 diperlebar & diperdalam",
        "Taruhan paling langsung: **v3 memang kurang dilatih, bukan datanya yang habis**.\n\n"
        "Itu pelajaran terbesar `notebook_8`. Sekitar 25 keluarga ide berturut-turut memberi "
        "≤ 0,001, dan kesimpulan \"informasi dataset ini sudah habis\" terasa makin masuk "
        "akal — lalu satu perubahan memberi −0,0070 dengan menang 12/12. Notebook ini "
        "menanyakan apakah sumur yang sama masih ada isinya.",
        "Dua perubahan terhadap v3: **lebih lebar** (w = 64 → 80, 5 → 6 blok) dan yang lebih "
        "penting, **blok pertama memampatkan 2× bukan 4×**.\n\n"
        "Yang kedua itulah biayanya — blok pertama mengerjakan 80 kanal pada panjang penuh "
        "1000 sampel, kira-kira **4× biaya v3 keseluruhan**. Kalau kuota GPU Kaggle "
        "terbatas, **jalankan notebook 01–03 dulu**: ketiganya lebih murah, dan 01 sudah "
        "terbukti."),
    "05_cnn6_transformer.ipynb": arch_notebook(
        "cnn6", "kaggle 05 — Frontend konvolusi + Transformer",
        "Bias induktif paling jauh dari Net3 di antara semua varian di folder ini — kalau ia "
        "jalan, korelasinya rendah dan bobot blend-nya besar.\n\n"
        "Juga **taruhan bervarians paling tinggi**, dan itu harus dikatakan terus terang: "
        "ukuran sampel efektif di sini cuma **~905 event**, bukan 10.505 record, dan "
        "transformer biasanya kurang pada data sekecil itu. Jalankan paling akhir.",
        "Konvolusi pendek memampatkan 1000 sampel jadi 62 token, lalu 3 lapis transformer "
        "encoder (8 head, d = 160) bekerja di atas token waktu itu.\n\n"
        "Bedanya dengan Net3 bukan sekadar kapasitas. Net3 mengagregasi lewat mean/max "
        "global atas seluruh waktu, sedangkan attention bisa **memilih jendela waktu mana "
        "yang penting per-record** — misalnya menimbang onset P berbeda dari koda, "
        "tergantung SNR dan jarak record itu sendiri."),
}

for nama, obj in files.items():
    (OUT/nama).write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")
    print("tulis %-32s (%d sel)" % (nama, len(obj["cells"])))
