"""CNN waveform gaya MagNet: bentuk gelombang ternormalisasi + skala amplitudo
disuntikkan balik sebagai skalar. Ini yang membedakannya dari CNN v1/v2 sebelumnya
(yang memberi makan waveform mentah dengan rentang 5 orde magnitudo)."""
import numpy as np, pandas as pd, time, torch, torch.nn as nn
from scipy import signal
from sklearn.model_selection import GroupKFold
import lab_common as C

FS, P_IDX = 200, 200
DEV = "cuda" if torch.cuda.is_available() else "cpu"

def _hp(a,f=0.075,order=2):
    b,aa=signal.butter(order,f/(FS/2),btype="high")
    return signal.filtfilt(b,aa,a,axis=1).astype(np.float32)

def build_input(X, meta):
    """-> W (N,9,1000) bentuk ternormalisasi, S (N,n_scalar)"""
    A=X.astype(np.float32); V=np.cumsum(_hp(A),axis=1)/FS; D=np.cumsum(_hp(V),axis=1)/FS
    chans=[]; scales=[]
    for W in (A,V,D):
        mx=np.abs(W).max(axis=(1,2),keepdims=True)+1e-20
        chans.append((W/mx).transpose(0,2,1))          # (N,3,1000)
        scales.append(np.log10(mx[:,0,0]))
    Wn=np.concatenate(chans,axis=1).astype(np.float32)
    dist=meta.distance_km.values.astype(np.float32); dep=meta.depth_km.values.astype(np.float32)
    S=np.stack([*scales,
                np.log10(dist+1), np.log10(dep+1),
                np.log10(np.sqrt(dist**2+dep**2)+1),
                meta.snr_db.values.astype(np.float32)/40.0,
                meta.is_clipped.values.astype(np.float32)],axis=1).astype(np.float32)
    return Wn, S

class Blk(nn.Module):
    def __init__(s, ci, co, k=7, pool=4):
        super().__init__()
        s.c1=nn.Conv1d(ci,co,k,padding=k//2); s.b1=nn.BatchNorm1d(co)
        s.c2=nn.Conv1d(co,co,k,padding=k//2); s.b2=nn.BatchNorm1d(co)
        s.sk=nn.Conv1d(ci,co,1) if ci!=co else nn.Identity()
        s.act=nn.SiLU(); s.pool=nn.MaxPool1d(pool)
    def forward(s,x):
        h=s.act(s.b1(s.c1(x))); h=s.b2(s.c2(h))
        return s.pool(s.act(h+s.sk(x)))

class Net(nn.Module):
    def __init__(s, n_scalar, w=48):
        super().__init__()
        s.body=nn.Sequential(Blk(9,w),Blk(w,w*2),Blk(w*2,w*4),Blk(w*4,w*4,k=5,pool=2))
        s.head=nn.Sequential(nn.Linear(w*8+n_scalar,192), nn.SiLU(), nn.Dropout(0.2),
                             nn.Linear(192,64), nn.SiLU(), nn.Linear(64,1))
    def forward(s,x,sc):
        h=s.body(x)
        h=torch.cat([h.mean(-1), h.amax(-1), sc],dim=1)
        return s.head(h).squeeze(-1)

def run_cnn(Wtr,Str,Wte,Ste, target, sw, seeds=(0,1), epochs=55, bs=128, lr=2e-3, avg_last=8):
    y=C.y; ev=C.ev
    oof=np.zeros(len(y)); pte=np.zeros(len(Wte))
    Xte_t=torch.tensor(Wte).to(DEV); Ste_t=torch.tensor(Ste).to(DEV)
    for seed in seeds:
        torch.manual_seed(seed); np.random.seed(seed)
        for ti,vi in GroupKFold(n_splits=5).split(Wtr,y,ev):
            net=Net(Str.shape[1]).to(DEV)
            opt=torch.optim.AdamW(net.parameters(),lr=lr,weight_decay=1e-2)
            sch=torch.optim.lr_scheduler.OneCycleLR(opt,max_lr=lr,
                    total_steps=epochs*max(1,len(ti)//bs), pct_start=0.25)
            Xt=torch.tensor(Wtr[ti]); St=torch.tensor(Str[ti])
            tt=torch.tensor(target[ti],dtype=torch.float32); wt=torch.tensor(sw[ti],dtype=torch.float32)
            Xv=torch.tensor(Wtr[vi]).to(DEV); Sv=torch.tensor(Str[vi]).to(DEV)
            accum_v=np.zeros(len(vi)); accum_t=np.zeros(len(Wte)); nacc=0
            for ep in range(epochs):
                net.train(); perm=torch.randperm(len(ti))
                for i in range(0,len(ti)-bs+1,bs):
                    b=perm[i:i+bs]
                    xb=Xt[b].clone(); sb=St[b].to(DEV)
                    # augmentasi: rotasi horizontal (kanal 0,1 tiap grup a/v/d) + flip tanda
                    th=torch.rand(len(b))*2*np.pi; cs,sn=torch.cos(th),torch.sin(th)
                    for k in (0,3,6):
                        e,n=xb[:,k].clone(),xb[:,k+1].clone()
                        xb[:,k]=cs[:,None]*e-sn[:,None]*n; xb[:,k+1]=sn[:,None]*e+cs[:,None]*n
                    if torch.rand(1).item()<0.5:
                        for k in (2,5,8): xb[:,k]*=-1
                    xb=xb.to(DEV)
                    pred=net(xb,sb)
                    loss=(wt[b].to(DEV)*(pred-tt[b].to(DEV)).abs()).sum()/wt[b].sum().to(DEV)
                    opt.zero_grad(); loss.backward(); opt.step(); sch.step()
                if ep>=epochs-avg_last:
                    net.eval()
                    with torch.no_grad():
                        accum_v+=net(Xv,Sv).cpu().numpy()
                        pt=[]
                        for i in range(0,len(Wte),512): pt.append(net(Xte_t[i:i+512],Ste_t[i:i+512]).cpu().numpy())
                        accum_t+=np.concatenate(pt)
                    nacc+=1
            oof[vi]+=accum_v/(avg_last)/len(seeds)
            pte+=accum_t/(avg_last)/(5*len(seeds))
    return oof,pte

# ---------------- model kedua: 2D CNN di spektrogram ----------------
def build_spec(X, meta, nper=64, hop=16):
    """log-spektrogram 3 komponen -> (N,3,F,T), dinormalisasi; skala tetap disuntik skalar."""
    from scipy import signal as sg
    A=X.astype(np.float32)
    f,t,S = sg.stft(A, fs=FS, nperseg=nper, noverlap=nper-hop, axis=1)
    P = np.abs(S)**2                      # (N,F,3,T)
    P = np.transpose(P,(0,2,1,3))         # (N,3,F,T)
    L = np.log10(P+1e-20).astype(np.float32)
    mx = L.max(axis=(1,2,3),keepdims=True)
    L = (L-mx)/6.0                        # bentuk relatif, rentang ~[-1,0]
    _,S2 = build_input(X,meta)
    return np.ascontiguousarray(L), S2

class SpecNet(nn.Module):
    def __init__(s, n_scalar, w=32):
        super().__init__()
        def blk(ci,co,pool):
            return nn.Sequential(nn.Conv2d(ci,co,3,padding=1), nn.BatchNorm2d(co), nn.SiLU(),
                                 nn.Conv2d(co,co,3,padding=1), nn.BatchNorm2d(co), nn.SiLU(),
                                 nn.MaxPool2d(pool))
        s.body=nn.Sequential(blk(3,w,2), blk(w,w*2,2), blk(w*2,w*4,2), blk(w*4,w*4,2))
        s.head=nn.Sequential(nn.Linear(w*8+n_scalar,192), nn.SiLU(), nn.Dropout(0.2),
                             nn.Linear(192,64), nn.SiLU(), nn.Linear(64,1))
    def forward(s,x,sc):
        h=s.body(x); h=h.flatten(2)
        return s.head(torch.cat([h.mean(-1),h.amax(-1),sc],dim=1)).squeeze(-1)

def run_spec(Wtr,Str,Wte,Ste, target, sw, seeds=(0,1), epochs=45, bs=96, lr=2e-3, avg_last=8):
    y=C.y; ev=C.ev
    oof=np.zeros(len(y)); pte=np.zeros(len(Wte))
    Xte_t=torch.tensor(Wte).to(DEV); Ste_t=torch.tensor(Ste).to(DEV)
    for seed in seeds:
        torch.manual_seed(seed); np.random.seed(seed)
        for ti,vi in GroupKFold(n_splits=5).split(Wtr,y,ev):
            net=SpecNet(Str.shape[1]).to(DEV)
            opt=torch.optim.AdamW(net.parameters(),lr=lr,weight_decay=1e-2)
            sch=torch.optim.lr_scheduler.OneCycleLR(opt,max_lr=lr,
                    total_steps=epochs*max(1,len(ti)//bs), pct_start=0.25)
            Xt=torch.tensor(Wtr[ti]); St=torch.tensor(Str[ti])
            tt=torch.tensor(target[ti],dtype=torch.float32); wt=torch.tensor(sw[ti],dtype=torch.float32)
            Xv=torch.tensor(Wtr[vi]).to(DEV); Sv=torch.tensor(Str[vi]).to(DEV)
            av=np.zeros(len(vi)); at=np.zeros(len(Wte)); nacc=0
            for ep in range(epochs):
                net.train(); perm=torch.randperm(len(ti))
                for i in range(0,len(ti)-bs+1,bs):
                    b=perm[i:i+bs]
                    xb=Xt[b].to(DEV); sb=St[b].to(DEV)
                    if torch.rand(1).item()<0.5:            # tukar kanal horizontal E<->N
                        xb=xb[:,[1,0,2]]
                    loss=(wt[b].to(DEV)*(net(xb,sb)-tt[b].to(DEV)).abs()).sum()/wt[b].sum().to(DEV)
                    opt.zero_grad(); loss.backward(); opt.step(); sch.step()
                if ep>=epochs-avg_last:
                    net.eval()
                    with torch.no_grad():
                        av+=net(Xv,Sv).cpu().numpy()
                        pt=[]
                        for i in range(0,len(Wte),256): pt.append(net(Xte_t[i:i+256],Ste_t[i:i+256]).cpu().numpy())
                        at+=np.concatenate(pt)
                    nacc+=1
            oof[vi]+=av/avg_last/len(seeds); pte+=at/avg_last/(5*len(seeds))
    return oof,pte
