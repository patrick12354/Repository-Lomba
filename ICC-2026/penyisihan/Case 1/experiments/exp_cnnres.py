"""CNN dengan target residual anchor ridge (trik yang menolong LightGBM di nb5)."""
import _path  # noqa: F401  -- menaruh Case 1/ di sys.path
import numpy as np, torch, time
from sklearn.model_selection import GroupKFold
from sklearn.linear_model import Ridge
import lab_common as C, lab_cnn as N, lab_models as M
z=np.load(C.CACHE/"cnn_input.npz"); Wtr,Str,Wte,Ste=z["Wtr"],z["Str"],z["Wte"],z["Ste"]
Ftr,Fte=C.get_feats()
Xa=Ftr[M.A_BASE].values.astype(np.float64); Xa_te=Fte[M.A_BASE].values.astype(np.float64)
sw=C.make_sw(power=0.5)
DEV=N.DEV
oof=np.zeros(len(C.y)); pte=np.zeros(len(Wte)); t0=time.time()
SEEDS=(0,1,2); EP=55; BS=128; LR=2e-3; AVG=8
Xte_t=torch.tensor(Wte).to(DEV); Ste_t=torch.tensor(Ste).to(DEV)
for seed in SEEDS:
    torch.manual_seed(seed); np.random.seed(seed)
    for ti,vi in GroupKFold(5).split(Wtr,C.y,C.ev):
        rg=Ridge(alpha=1.0).fit(Xa[ti],C.y[ti],sample_weight=sw[ti])
        tgt=(C.y-rg.predict(Xa)).astype(np.float32)
        net=N.Net(Str.shape[1]).to(DEV)
        opt=torch.optim.AdamW(net.parameters(),lr=LR,weight_decay=1e-2)
        sch=torch.optim.lr_scheduler.OneCycleLR(opt,max_lr=LR,total_steps=EP*max(1,len(ti)//BS),pct_start=0.25)
        Xt=torch.tensor(Wtr[ti]); St=torch.tensor(Str[ti])
        tt=torch.tensor(tgt[ti]); wt=torch.tensor(sw[ti],dtype=torch.float32)
        Xv=torch.tensor(Wtr[vi]).to(DEV); Sv=torch.tensor(Str[vi]).to(DEV)
        av=np.zeros(len(vi)); at=np.zeros(len(Wte))
        for ep in range(EP):
            net.train(); perm=torch.randperm(len(ti))
            for i in range(0,len(ti)-BS+1,BS):
                b=perm[i:i+BS]; xb=Xt[b].clone(); sb=St[b].to(DEV)
                th=torch.rand(len(b))*2*np.pi; cs,sn=torch.cos(th),torch.sin(th)
                for k in (0,3,6):
                    e,n_=xb[:,k].clone(),xb[:,k+1].clone()
                    xb[:,k]=cs[:,None]*e-sn[:,None]*n_; xb[:,k+1]=sn[:,None]*e+cs[:,None]*n_
                xb=xb.to(DEV)
                loss=(wt[b].to(DEV)*(net(xb,sb)-tt[b].to(DEV)).abs()).sum()/wt[b].sum().to(DEV)
                opt.zero_grad(); loss.backward(); opt.step(); sch.step()
            if ep>=EP-AVG:
                net.eval()
                with torch.no_grad():
                    av+=net(Xv,Sv).cpu().numpy()
                    pp=[net(Xte_t[i:i+512],Ste_t[i:i+512]).cpu().numpy() for i in range(0,len(Wte),512)]
                    at+=np.concatenate(pp)
        oof[vi]+=(av/AVG+rg.predict(Xa[vi]))/len(SEEDS)
        pte+=(at/AVG+rg.predict(Xa_te))/(5*len(SEEDS))
np.savez(C.CACHE/"cnnres.npz",oof=oof,pte=pte)
print(f"CNNres {time.time()-t0:.0f}s cv_lama={C.eb_twmae(C.y,oof,C.ev):.4f} lb_real={C.lb_real(oof):.4f} bias={C.bias_rnd(oof):+.3f}")
print("korelasi vs cnn_sqrt:",np.corrcoef(oof,np.load(C.CACHE/"cnn_sqrt.npz")["oof"])[0,1].round(3))
