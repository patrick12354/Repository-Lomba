"""Cari hyperparameter ULANG di bawah metrik terkoreksi — semua kesimpulan HP lama
diambil dengan metrik yang cacat, jadi peringkatnya belum tentu berlaku."""
import _path  # noqa: F401  -- menaruh Case 1/ di sys.path
import numpy as np
import lab_common as C, lab_models as M
Ftr,Fte=C.get_feats(); Gtr=C.add_group_feats(Ftr,C.train); Gte=C.add_group_feats(Fte,C.test)
dh=np.load(C.CACHE/"dhat.npy")
def add_depth_feats(F,dep,dhat,dist):
    G=F.copy(); d=np.clip(10**dhat-1,1,700)
    G["dep_hat"]=d.astype(np.float32); G["dep_hat_diff"]=(dhat-np.log10(dep+1)).astype(np.float32)
    G["loghypo_hat"]=np.log10(np.sqrt(dist**2+d**2)+1).astype(np.float32)
    for c in ["Pd_2","Pv_2","Pa_4","Pd_4"]: G[f"H{c}"]=(F[c].values+G["loghypo_hat"].values).astype(np.float32)
    return G.astype(np.float32)
F2=add_depth_feats(Ftr,C.d_tr,dh[:len(Ftr)],C.train.distance_km.values.astype(np.float32))
F2e=add_depth_feats(Fte,C.d_te,dh[len(Ftr):],C.test.distance_km.values.astype(np.float32))
G2=C.add_group_feats(F2,C.train); G2e=C.add_group_feats(F2e,C.test)
CFG={
 "hp_lf15": dict(num_leaves=15,min_child_samples=80,learning_rate=0.015),
 "hp_lf63": dict(num_leaves=63,min_child_samples=30,learning_rate=0.02),
 "hp_cs04": dict(colsample_bytree=0.4),
 "hp_l2_10": dict(reg_lambda=10.0),
 "hp_mcs150": dict(min_child_samples=150,num_leaves=31),
 "hp_lr005": dict(learning_rate=0.005,num_leaves=31),
 "hp_huber": dict(objective="huber",alpha=0.4),
 "hp_sub05": dict(subsample=0.5,colsample_bytree=0.5,num_leaves=63),
}
print(f"{'config':>11}{'cv_real':>9}{'dec':>8}{'rnd':>8}{'lb_real':>9}{'bias':>8}")
print(f"{'resB_dep':>11}{0.2019:9.4f}{0.1776:8.4f}{0.2275:8.4f}{0.2031:9.4f}{0.064:+8.3f}  <- baseline")
for n,p in CFG.items():
    o,_=M.cached("B_"+n, lambda p=p: M.cv_lgb(G2,G2e,resid=True,Ftr=Ftr,Fte=Fte,params=p))
    print(f"{n:>11}{C.cv_real(o):9.4f}{C.part_real(o,True):8.4f}{C.part_real(o,False):8.4f}"
          f"{C.lb_real(o):9.4f}{C.bias_rnd(o):+8.3f}",flush=True)
