"""Set-transformer sebagai pengganti smoothing tangan.

Smoothing sekarang: median seluruh grup depth, bobot lam tetap. Untuk depth=10.0 grup itu
mencampur 1.633 record dari 21 gempa berbeda -- median-nya derau. Ide: biarkan attention
yang memutuskan record mana yang saling co-belong, alih-alih median buta.

Beda dari classifier co-membership nb7 (yang gagal): itu pairwise + smoothing berbasis
probabilitas. Ini set-level, dilatih end-to-end pada metrik yang benar.
"""
import _path
import numpy as np, torch, torch.nn as nn, time
from sklearn.model_selection import GroupKFold
import lab_common as C
from fastscore import Scorer, Post

DEV="cuda" if torch.cuda.is_available() else "cpu"
sc=Scorer(C.EVR, np.ones(len(C.y),bool))
post=Post(C.d_tr,0.95,0.5,150,1.15,1.05)
CAND=["swA_sqrt","resA_dep","resB_dep","resB_c30","resB_p05","cnnres","cnn3_avg","cnn3_dir"]
def ld(n):
    z=np.load(C.CACHE/f"{n}.npz"); return z["oof"],z["pte"]
Otr=np.stack([ld(n)[0] for n in CAND]); Ote=np.stack([ld(n)[1] for n in CAND])
w=np.load(C.CACHE/"w_nb9.npy")
blend_tr = w@Otr; blend_te = w@Ote
base_tr = post(blend_tr)
print("baseline nb8: lb_real=%.4f rnd=%.4f"%(sc(base_tr),C.part_real(base_tr,False)))

# fitur per-record untuk set model: prediksi mentah + sinyal yang membedakan event
Ftr,Fte=C.get_feats()
FCOL=["Cd_2","Cv_2","Ca_4","logdist","loghypo","logE","snr_db","tauc","cent_a",
      "lhr_a","tE50","rectilin","Pd_4","Pv_4","Pa_4","gd_0.5_4","depth_km"]
def mk(F, blend, dep):
    Z=F[FCOL].values.astype(np.float32)
    Z=(Z-Z.mean(0))/(Z.std(0)+1e-6)
    return np.concatenate([blend[:,None].astype(np.float32), Z],1)
Xtr=mk(Ftr,blend_tr,C.d_tr); Xte=mk(Fte,blend_te,C.d_te)
NF=Xtr.shape[1]

class SetNet(nn.Module):
    def __init__(s, nf, h=96, nl=2):
        super().__init__()
        s.emb=nn.Sequential(nn.Linear(nf,h),nn.SiLU(),nn.Linear(h,h))
        enc=nn.TransformerEncoderLayer(h,4,h*2,dropout=0.1,batch_first=True,norm_first=True)
        s.tr=nn.TransformerEncoder(enc,nl)
        s.out=nn.Sequential(nn.LayerNorm(h),nn.Linear(h,64),nn.SiLU(),nn.Linear(64,1))
    def forward(s,x,mask):
        h=s.emb(x); h=s.tr(h,src_key_padding_mask=~mask)
        return s.out(h).squeeze(-1)   # koreksi terhadap blend

def build_sets(idx, dep, maxn=40, rng=None, reps=1):
    """Bangun set record yang berbagi depth key, HANYA dari idx yang diberikan.
    Ini meniru test-time: grup dibentuk di dalam himpunan yang tersedia."""
    out=[]
    for _ in range(reps):
        for d in np.unique(dep[idx]):
            g=idx[dep[idx]==d]
            if rng is not None and len(g)>maxn:
                g=rng.permutation(g)
                for k in range(0,len(g),maxn):
                    if len(g[k:k+maxn])>=2: out.append(g[k:k+maxn])
            else:
                for k in range(0,len(g),maxn):
                    out.append(g[k:k+maxn])
    return out

def pad(sets, X, maxn=40):
    B=len(sets)
    xb=np.zeros((B,maxn,X.shape[1]),np.float32); mk_=np.zeros((B,maxn),bool)
    ids=np.full((B,maxn),-1,np.int64)
    for i,s in enumerate(sets):
        n=len(s); xb[i,:n]=X[s]; mk_[i,:n]=True; ids[i,:n]=s
    return xb,mk_,ids

def run(epochs=60, lr=2e-3, seeds=(0,1,2), maxn=40, lam=1.0):
    corr=np.zeros(len(C.y)); ncorr=np.zeros(len(C.y))
    cte=np.zeros(len(C.d_te)); 
    sw=C.SW
    for seed in seeds:
        torch.manual_seed(seed); rng=np.random.RandomState(seed)
        for ti,vi in GroupKFold(5).split(Xtr,C.y,C.ev):
            net=SetNet(NF).to(DEV)
            opt=torch.optim.AdamW(net.parameters(),lr=lr,weight_decay=1e-2)
            nstep=epochs*max(1,len(build_sets(ti,C.d_tr,maxn,rng))//8)
            sch=torch.optim.lr_scheduler.OneCycleLR(opt,max_lr=lr,total_steps=nstep+10,pct_start=0.25)
            tgt=torch.tensor((C.y-blend_tr).astype(np.float32)).to(DEV)
            yt=torch.tensor(C.y.astype(np.float32)).to(DEV)
            swt=torch.tensor(sw.astype(np.float32)).to(DEV)
            for ep in range(epochs):
                net.train()
                sets=build_sets(ti,C.d_tr,maxn,rng)
                rng.shuffle(sets)
                for k in range(0,len(sets),8):
                    bs_=sets[k:k+8]
                    xb,mkb,ids=pad(bs_,Xtr,maxn)
                    xb=torch.tensor(xb).to(DEV); mkb_t=torch.tensor(mkb).to(DEV)
                    idt=torch.tensor(np.maximum(ids,0)).to(DEV)
                    pc=net(xb,mkb_t)
                    m=torch.tensor(mkb).to(DEV)
                    tg=tgt[idt]; ww=swt[idt]*m
                    loss=((pc-tg).abs()*ww).sum()/(ww.sum()+1e-8)
                    opt.zero_grad(); loss.backward()
                    nn.utils.clip_grad_norm_(net.parameters(),1.0)
                    opt.step()
                    if sch.last_epoch<nstep: sch.step()
            # inferensi: set dibentuk DI DALAM fold validasi (meniru test)
            net.eval()
            with torch.no_grad():
                for reps in range(4):
                    r2=np.random.RandomState(1000+reps)
                    sets=build_sets(vi,C.d_tr,maxn,r2)
                    for k in range(0,len(sets),16):
                        bs_=sets[k:k+16]
                        xb,mkb,ids=pad(bs_,Xtr,maxn)
                        pc=net(torch.tensor(xb).to(DEV),torch.tensor(mkb).to(DEV)).cpu().numpy()
                        for i,s in enumerate(bs_):
                            corr[s]+=pc[i,:len(s)]; ncorr[s]+=1
    corr=corr/np.maximum(ncorr,1)
    return corr

t0=time.time()
corr=run()
print("waktu %.0fs"%(time.time()-t0))
for lam in [0.0,0.15,0.3,0.5,0.75,1.0]:
    p=blend_tr+lam*corr
    q=post(p)
    print("  lam=%.2f  lb_real=%.4f  dec=%.4f  rnd=%.4f  bias=%+.3f"
          %(lam,sc(q),C.part_real(q,True),C.part_real(q,False),C.bias_rnd(q)))
np.save(C.CACHE/"set_corr.npy",corr)
