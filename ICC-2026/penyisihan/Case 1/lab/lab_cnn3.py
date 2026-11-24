"""CNN v3: multi-task (magnitudo + kedalaman), augmentasi derau realistis dari jendela pre-P,
target residual anchor, jaringan lebih lebar & jadwal lebih panjang."""
import numpy as np, torch, torch.nn as nn, time
from sklearn.model_selection import GroupKFold
from sklearn.linear_model import Ridge
import lab_common as C, lab_models as M

DEV = "cuda" if torch.cuda.is_available() else "cpu"

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
    def __init__(s, n_scalar, w=64):
        super().__init__()
        s.body=nn.Sequential(Blk(9,w),Blk(w,w*2),Blk(w*2,w*3),Blk(w*3,w*4,k=5,pool=2),
                             Blk(w*4,w*4,k=3,pool=2))
        s.trunk=nn.Sequential(nn.Linear(w*8+n_scalar,256), nn.SiLU(), nn.Dropout(0.25),
                              nn.Linear(256,96), nn.SiLU())
        s.mag=nn.Linear(96,1); s.dep=nn.Linear(96,1)
    def forward(s,x,sc):
        h=s.body(x); h=torch.cat([h.mean(-1),h.amax(-1),sc],dim=1); h=s.trunk(h)
        return s.mag(h).squeeze(-1), s.dep(h).squeeze(-1)

def run(Wtr,Str,Wte,Ste, sw, seeds=(0,1,2), epochs=80, bs=128, lr=2.5e-3, avg_last=10, resid=True, arch=None):
    y,ev=C.y,C.ev
    Ftr,Fte=C.get_feats()
    Xa=Ftr[M.A_BASE].values.astype(np.float64); Xa_te=Fte[M.A_BASE].values.astype(np.float64)
    dep_t=np.log10(C.d_tr+1).astype(np.float32); dep_ok=(~C.rnd_tr).astype(np.float32)
    noise=Wtr[:,:,:200].copy()                       # jendela pre-P utk augmentasi
    oof=np.zeros(len(y)); pte=np.zeros(len(Wte))
    Xte_t=torch.tensor(Wte).to(DEV); Ste_t=torch.tensor(Ste).to(DEV)
    _fold=0; _t0=time.time()
    for seed in seeds:
        torch.manual_seed(seed); np.random.seed(seed)
        for ti,vi in GroupKFold(5).split(Wtr,y,ev):
            if resid:
                rg=Ridge(alpha=1.0).fit(Xa[ti],y[ti],sample_weight=sw[ti])
                tgt=(y-rg.predict(Xa)).astype(np.float32); off_v=rg.predict(Xa[vi]); off_t=rg.predict(Xa_te)
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
                        e,n_=xb[:,k].clone(),xb[:,k+1].clone()
                        xb[:,k]=cs[:,None]*e-sn[:,None]*n_; xb[:,k+1]=sn[:,None]*e+cs[:,None]*n_
                    if torch.rand(1).item()<0.5:
                        for k in (2,5,8): xb[:,k]*=-1
                    # tempel derau pre-P dari record lain (augmentasi fisik, bukan sintetis)
                    if torch.rand(1).item()<0.5:
                        j=torch.randint(0,len(ti),(len(b),))
                        amp=(torch.rand(len(b),1,1)*0.6)
                        seg=Nz[j]                      # (B,9,200)
                        rep=seg.repeat(1,1,5)[:,:,:xb.shape[2]]
                        xb=xb+amp*rep
                    xb=xb.to(DEV)
                    pm,pdep=net(xb,sb)
                    lm=(wt[b].to(DEV)*(pm-tt[b].to(DEV)).abs()).sum()/wt[b].sum().to(DEV)
                    dkb=dk[b].to(DEV)
                    ld=((pdep-dt[b].to(DEV)).abs()*dkb).sum()/(dkb.sum()+1e-6)
                    loss=lm+0.15*ld
                    opt.zero_grad(); loss.backward(); opt.step(); sch.step()
                if ep>=epochs-avg_last:
                    net.eval()
                    with torch.no_grad():
                        av+=net(Xv,Sv)[0].cpu().numpy()
                        at+=np.concatenate([net(Xte_t[i:i+512],Ste_t[i:i+512])[0].cpu().numpy()
                                            for i in range(0,len(Wte),512)])
            oof[vi]+=(av/avg_last+off_v)/len(seeds)
            pte+=(at/avg_last+off_t)/(5*len(seeds))
            _fold+=1
            print("    seed %d fold %d/5 selesai (%.0fs)"%(seed,_fold%5 or 5,time.time()-_t0),flush=True)
    return oof,pte


class Net4(nn.Module):
    """Frontend konvolusi -> BiGRU -> attention pooling. Bias induktif berbeda dari Net3
    (yang murni konvolusi + pooling global), jadi errornya lebih terdekorelasi."""
    def __init__(s, n_scalar, w=48, h=112):
        super().__init__()
        s.body=nn.Sequential(Blk(9,w),Blk(w,w*2),Blk(w*2,w*3,k=5,pool=2))   # 1000 -> 31 token
        s.gru=nn.GRU(w*3,h,num_layers=2,batch_first=True,bidirectional=True,dropout=0.1)
        s.att=nn.Sequential(nn.Linear(2*h,64), nn.Tanh(), nn.Linear(64,1))
        s.trunk=nn.Sequential(nn.Linear(4*h+n_scalar,224), nn.SiLU(), nn.Dropout(0.25),
                              nn.Linear(224,96), nn.SiLU())
        s.mag=nn.Linear(96,1); s.dep=nn.Linear(96,1)
    def forward(s,x,sc):
        h=s.body(x).transpose(1,2)
        h,_=s.gru(h)
        a=torch.softmax(s.att(h),dim=1)
        h=torch.cat([(a*h).sum(1), h.mean(1), sc],dim=1)
        h=s.trunk(h)
        return s.mag(h).squeeze(-1), s.dep(h).squeeze(-1)


class Net5(nn.Module):
    """v3 diperlebar + dilepas satu tingkat pooling di awal supaya resolusi waktu lebih
    lama bertahan. Kepala ketiga: prediksi log10(hypo) sebagai regularizer geometri."""
    def __init__(s, n_scalar, w=80):
        super().__init__()
        s.body=nn.Sequential(Blk(9,w,k=9,pool=2), Blk(w,w*2,k=7,pool=4),
                             Blk(w*2,w*3,k=7,pool=2), Blk(w*3,w*3,k=5,pool=2),
                             Blk(w*3,w*4,k=5,pool=2), Blk(w*4,w*4,k=3,pool=2))
        s.trunk=nn.Sequential(nn.Linear(w*8+n_scalar,320), nn.SiLU(), nn.Dropout(0.3),
                              nn.Linear(320,128), nn.SiLU())
        s.mag=nn.Linear(128,1); s.dep=nn.Linear(128,1)
    def forward(s,x,sc):
        h=s.body(x); h=torch.cat([h.mean(-1),h.amax(-1),sc],dim=1); h=s.trunk(h)
        return s.mag(h).squeeze(-1), s.dep(h).squeeze(-1)


class Net6(nn.Module):
    """Frontend konvolusi pendek -> transformer encoder atas token waktu. Bias induktif
    paling jauh dari Net3 (konvolusi murni) di antara semua varian yang sudah dicoba."""
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
    def forward(s,x,sc):
        h=s.body(x).transpose(1,2)
        h=s.proj(h)+s.pos[:,:h.shape[1]]
        h=s.tr(h)
        h=torch.cat([h.mean(1),h.amax(1),sc],dim=1); h=s.trunk(h)
        return s.mag(h).squeeze(-1), s.dep(h).squeeze(-1)


def run_grp(Wtr,Str,Wte,Ste, sw, seeds=(0,1,2), epochs=80, n_ev=20, lr=2.5e-3,
            avg_last=10, beta=0.5, arch=None):
    """Sama seperti run(), tapi batch disusun dari EVENT UTUH dan loss punya suku kedua
    di tingkat agregat.

    Alasannya: metrik mentah = rata-rata |y - p_i| per event, dan itu memang yang
    dioptimalkan `sw`. Tapi yang benar-benar disubmit untuk record depth-DESIMAL adalah
    **median grup** (lam_dec = 0,95). Meminimalkan mean|y - p_i| tidak sama dengan
    meminimalkan |y - median_i(p_i)| -- yang kedua toleran terhadap sebaran asal
    median-nya tepat. Suku `beta` melatih besaran yang sebenarnya dipakai.

    Suku agregat hanya untuk event depth-desimal, karena hanya di sana smoothing berlaku.
    """
    import numpy as _np
    y,ev=C.y,C.ev
    Ftr,Fte=C.get_feats()
    Xa=Ftr[M.A_BASE].values.astype(_np.float64); Xa_te=Fte[M.A_BASE].values.astype(_np.float64)
    dep_t=_np.log10(C.d_tr+1).astype(_np.float32); dep_ok=(~C.rnd_tr).astype(_np.float32)
    is_dec=(~C.rnd_tr)
    noise=Wtr[:,:,:200].copy()
    oof=_np.zeros(len(y)); pte=_np.zeros(len(Wte))
    Xte_t=torch.tensor(Wte).to(DEV); Ste_t=torch.tensor(Ste).to(DEV)
    for seed in seeds:
        torch.manual_seed(seed); _np.random.seed(seed)
        for ti,vi in GroupKFold(5).split(Wtr,y,ev):
            rg=Ridge(alpha=1.0).fit(Xa[ti],y[ti],sample_weight=sw[ti])
            tgt=(y-rg.predict(Xa)).astype(_np.float32)
            off_v=rg.predict(Xa[vi]); off_t=rg.predict(Xa_te)
            ev_ti=ev[ti]; uev=_np.unique(ev_ti)
            by_ev={e: _np.where(ev_ti==e)[0] for e in uev}
            net=(arch or Net3)(Str.shape[1]).to(DEV)
            opt=torch.optim.AdamW(net.parameters(),lr=lr,weight_decay=2e-2)
            steps=epochs*max(1,len(uev)//n_ev)
            sch=torch.optim.lr_scheduler.OneCycleLR(opt,max_lr=lr,total_steps=steps+10,pct_start=0.2)
            Xt=torch.tensor(Wtr[ti]); St=torch.tensor(Str[ti]); Nz=torch.tensor(noise[ti])
            tt=torch.tensor(tgt[ti]); wt=torch.tensor(sw[ti],dtype=torch.float32)
            dt=torch.tensor(dep_t[ti]); dk=torch.tensor(dep_ok[ti])
            yt=torch.tensor(y[ti].astype(_np.float32))
            offt=torch.tensor(rg.predict(Xa[ti]).astype(_np.float32))
            mw=torch.tensor(C.mag_weight(y[ti]).astype(_np.float32))
            decm=torch.tensor(is_dec[ti].astype(_np.float32))
            Xv=torch.tensor(Wtr[vi]).to(DEV); Sv=torch.tensor(Str[vi]).to(DEV)
            av=_np.zeros(len(vi)); at=_np.zeros(len(Wte))
            rng=_np.random.RandomState(seed)
            for ep in range(epochs):
                net.train(); order=rng.permutation(uev)
                for k in range(0,len(order)-n_ev+1,n_ev):
                    evb=order[k:k+n_ev]
                    idx=_np.concatenate([by_ev[e] for e in evb])
                    seg=_np.concatenate([[j]*len(by_ev[e]) for j,e in enumerate(evb)])
                    if len(idx)>320:
                        sel=rng.choice(len(idx),320,replace=False); idx=idx[sel]; seg=seg[sel]
                    b=torch.tensor(idx); xb=Xt[b].clone(); sb=St[b].to(DEV)
                    th=torch.rand(len(b))*2*_np.pi; cs,sn=torch.cos(th),torch.sin(th)
                    for kk in (0,3,6):
                        e_,n_=xb[:,kk].clone(),xb[:,kk+1].clone()
                        xb[:,kk]=cs[:,None]*e_-sn[:,None]*n_; xb[:,kk+1]=sn[:,None]*e_+cs[:,None]*n_
                    if torch.rand(1).item()<0.5:
                        for kk in (2,5,8): xb[:,kk]*=-1
                    if torch.rand(1).item()<0.5:
                        j=torch.randint(0,len(ti),(len(b),))
                        amp=(torch.rand(len(b),1,1)*0.6)
                        xb=xb+amp*Nz[j].repeat(1,1,5)[:,:,:xb.shape[2]]
                    xb=xb.to(DEV)
                    pm,pdep=net(xb,sb)
                    wb=wt[b].to(DEV)
                    lm=(wb*(pm-tt[b].to(DEV)).abs()).sum()/wb.sum()
                    dkb=dk[b].to(DEV)
                    ld=((pdep-dt[b].to(DEV)).abs()*dkb).sum()/(dkb.sum()+1e-6)
                    # ---- suku agregat: median prediksi per event, hanya event desimal
                    pabs=pm+offt[b].to(DEV)
                    segt=torch.tensor(seg).to(DEV)
                    lagg=torch.zeros((),device=DEV); wsum=torch.zeros((),device=DEV)
                    for j in range(len(evb)):
                        m=segt==j
                        if m.sum()<2: continue
                        if decm[b].to(DEV)[m].mean()<0.5: continue
                        med=pabs[m].median()
                        ww=mw[b].to(DEV)[m][0]
                        lagg=lagg+ww*(med-yt[b].to(DEV)[m][0]).abs(); wsum=wsum+ww
                    if wsum>0: lagg=lagg/wsum
                    loss=lm+0.15*ld+beta*lagg
                    opt.zero_grad(); loss.backward(); opt.step()
                    if sch.last_epoch<steps: sch.step()
                if ep>=epochs-avg_last:
                    net.eval()
                    with torch.no_grad():
                        av+=net(Xv,Sv)[0].cpu().numpy()
                        at+=_np.concatenate([net(Xte_t[i:i+512],Ste_t[i:i+512])[0].cpu().numpy()
                                             for i in range(0,len(Wte),512)])
            oof[vi]+=(av/avg_last+off_v)/len(seeds)
            pte+=(at/avg_last+off_t)/(5*len(seeds))
    return oof,pte


class Net7(nn.Module):
    """TCN dilatasi: reseptif lebar tanpa pooling, jadi resolusi waktu penuh dipertahankan
    sampai akhir. Sumbu diversitas berbeda dari Net3/Net5 (yang membuang resolusi lewat
    MaxPool bertingkat) maupun Net6 (yang menukar waktu jadi token)."""
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
    def forward(s,x,sc):
        h=s.inp(x)
        for b in s.blocks: h=s.act(h+b(h))
        h=s.head(h)
        h=torch.cat([h.mean(-1),h.amax(-1),sc],dim=1); h=s.trunk(h)
        return s.mag(h).squeeze(-1), s.dep(h).squeeze(-1)


class _Inc(nn.Module):
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
    """Inception 1D: tiap blok melihat empat skala waktu sekaligus (3/9/21/41 sampel =
    15/45/105/205 ms). Kandungan frekuensi gelombang P sangat berbeda antar magnitudo,
    jadi kernel multi-skala paralel adalah bias induktif yang tepat -- dan berbeda dari
    Net3 yang memakai satu ukuran kernel per tingkat."""
    def __init__(s, n_scalar, w=64):
        super().__init__()
        s.body=nn.Sequential(_Inc(9,w),_Inc(w,w*2),_Inc(w*2,w*3),_Inc(w*3,w*4,pool=2),
                             _Inc(w*4,w*4,pool=2))
        s.trunk=nn.Sequential(nn.Linear(w*8+n_scalar,288), nn.SiLU(), nn.Dropout(0.25),
                              nn.Linear(288,96), nn.SiLU())
        s.mag=nn.Linear(96,1); s.dep=nn.Linear(96,1)
    def forward(s,x,sc):
        h=s.body(x); h=torch.cat([h.mean(-1),h.amax(-1),sc],dim=1); h=s.trunk(h)
        return s.mag(h).squeeze(-1), s.dep(h).squeeze(-1)
