"""Harness bersama untuk eksperimen Case 1. Cache fitur supaya iterasi cepat."""
import numpy as np, pandas as pd, time, os, warnings
warnings.filterwarnings("ignore")
from pathlib import Path
from scipy import signal, stats

# Semua path diikat ke folder Case 1/ (lokasi file ini), bukan ke cwd, supaya
# skrip di experiments/ dan tools/ tetap menemukan data dari mana pun dijalankan.
ROOT = Path(__file__).resolve().parent.parent   # lab/ -> Case 1/
DATA = ROOT/"seismic-dataset"; CACHE = ROOT/"cache"; CACHE.mkdir(exist_ok=True)
SUB_DIR = ROOT/"submission"; SUB_DIR.mkdir(exist_ok=True)
FS, P_IDX, EPS = 200, 200, 1e-15

train = (pd.read_csv(DATA/"train"/"train_meta.csv")
           .merge(pd.read_csv(DATA/"train"/"train_labels.csv"), on="sample_id"))
test  = pd.read_csv(DATA/"test"/"test_meta.csv")
y  = train.magnitude.values.astype(np.float64)
ev = train.groupby(["depth_km","magnitude"]).ngroup().values
cnt = pd.Series(ev).map(pd.Series(ev).value_counts()).values

def mag_weight(m):
    m=np.asarray(m); return np.where(m<5.5,1.0,np.where(m<6.0,1.5,np.where(m<6.5,2.0,2.5)))
def eb_twmae(yt,yp,e):
    df=pd.DataFrame({"y":yt,"p":yp,"e":e}); df["err"]=np.abs(df.y-df.p)
    g=df.groupby("e").agg(mae=("err","mean"),m=("y","first"))
    w=mag_weight(g.m.values); return float((w*g.mae.values).sum()/w.sum())

SW  = mag_weight(y)/cnt
d_tr = train.depth_km.values; d_te = test.depth_km.values
rnd_tr = np.isclose(d_tr, np.round(d_tr)); rnd_te = np.isclose(d_te, np.round(d_te))
MR = rnd_tr & (d_tr < 100); MT = rnd_te & (d_te < 100)
FD = 0.49   # proporsi event depth-desimal di test (perkiraan komposisi)

def bias_rnd(p): return float(p[MR].mean()-y[MR].mean())
def part_score(p, dec):
    m = (~rnd_tr) if dec else rnd_tr
    return eb_twmae(y[m], p[m], ev[m])
def lb_estimate(p): return FD*part_score(p,True)+(1-FD)*part_score(p,False)

# ---------- fitur ----------
def _hp(a,f=0.075,order=2):
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
    print("  extract %.1fs -> %d fitur"%(time.time()-t0,F.shape[1]))
    return F.astype(np.float32)

AGG_SRC=["Pd_1","Pd_2","Pd_4","Pv_2","Pv_4","Pa_4","Cd_2","Cd_4","Cv_2","Ca_4",
         "logE","rmsd_2","lhr_a","cent_a","tauc","logdist","loghypo","snr_db",
         "gd_0.5_4","gv_1_2","PdH_2","PdV_2"]
def add_group_feats(F, meta):
    G=F.copy(); key=meta.depth_km.values; k=pd.Series(key)
    G["grp_size"]=k.map(k.value_counts()).values.astype(np.float32)
    for c in AGG_SRC:
        s=pd.Series(F[c].values)
        gm=s.groupby(key).transform("mean").values
        gx=s.groupby(key).transform("max").values
        gn=s.groupby(key).transform("min").values
        G[f"gm_{c}"]=gm.astype(np.float32)
        G[f"gd_{c}"]=(F[c].values-gm).astype(np.float32)
        G[f"gs_{c}"]=s.groupby(key).transform("std").fillna(0).values.astype(np.float32)
        G[f"gx_{c}"]=gx.astype(np.float32)
        G[f"gr_{c}"]=(gx-gn).astype(np.float32)
    return G.astype(np.float32)

def get_feats():
    ftr, fte = CACHE/"Ftr.parquet", CACHE/"Fte.parquet"
    if ftr.exists() and fte.exists():
        Ftr=pd.read_parquet(ftr); Fte=pd.read_parquet(fte)
    else:
        print("TRAIN"); Ftr=extract(np.load(DATA/"train"/"train_waveforms.npy"), train)
        print("TEST ");  Fte=extract(np.load(DATA/"test"/"test_waveforms.npy"), test)
        Ftr.to_parquet(ftr); Fte.to_parquet(fte)
    return Ftr, Fte

# ---------- post-processing ----------
def smooth_gen(p, dep, lam_dec=0.95, lam_deep=0.0, T_deep=100):
    r=np.isclose(dep,np.round(dep))
    gm=pd.Series(p).groupby(pd.Series(dep)).transform("median").values
    lam=np.where(~r, lam_dec, np.where(dep>=T_deep, lam_deep, 0.0))
    return (1-lam)*p + lam*gm
def expand_subset(p, dep, a_dec=1.15, a_rnd=None):
    if a_rnd is None: a_rnd=a_dec
    r=np.isclose(dep,np.round(dep)); q=p.copy()
    for m,a in ((r,a_rnd),(~r,a_dec)):
        mu=p[m].mean(); q[m]=mu+a*(p[m]-mu)
    return q

# ---------- evaluasi REALISTIS ----------
# Pseudo-event sisi depth-bulat menggabung banyak gempa nyata (max 401 record dalam satu
# grup). Akibatnya metrik CV menimbang tiap kombinasi (depth, M) sama rata dan
# over-weight ekor ~3x. Pecah grup besar jadi chunk seukuran event nyata di test (~8).
depth_arr = d_tr
def make_ev_real(seed, chunk=8):
    rng=np.random.RandomState(seed); e2=ev.copy(); nxt=ev.max()+1
    split_me = rnd_tr & (depth_arr < 100)     # >=100 km: grup 67-100% murni, jangan dipecah
    for eid in np.unique(ev[split_me]):
        idx=np.where(ev==eid)[0]
        if len(idx) <= chunk*1.5: continue
        rng.shuffle(idx)
        k=max(2,int(round(len(idx)/chunk)))
        for j,part in enumerate(np.array_split(idx,k)):
            if j>0: e2[part]=nxt; nxt+=1
    return e2
EVR = [make_ev_real(s) for s in range(8)]
def part_real(p, dec):
    m=(~rnd_tr) if dec else rnd_tr
    return float(np.mean([eb_twmae(y[m],p[m],e[m]) for e in EVR]))
def cv_real(p):  return float(np.mean([eb_twmae(y,p,e) for e in EVR]))
def lb_real(p):  return FD*part_real(p,True)+(1-FD)*part_real(p,False)

# ---------- sample weight ----------
def make_sw(cap=None, power=1.0):
    c = cnt.astype(float)
    if cap is not None: c = np.minimum(c, cap)
    return mag_weight(y)/(c**power)
