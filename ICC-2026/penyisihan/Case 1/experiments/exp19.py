"""depth=10.0 adalah default katalog. Kalau kedalaman asli bisa ditaksir dari waveform,
jarak hiposenter (dan semua fitur terkoreksi jarak) bisa diperbaiki untuk 32% test itu."""
import _path  # noqa: F401  -- menaruh Case 1/ di sys.path
import numpy as np, pandas as pd, lightgbm as lgb
from sklearn.model_selection import GroupKFold
import lab_common as C, lab_models as M
Ftr,Fte=C.get_feats()
# fitur yang TIDAK boleh dipakai untuk menaksir depth (mengandung depth)
BAD=[c for c in Ftr.columns if c.startswith(("C",)) or c in
     ("depth_km","logdep","hypo","loghypo")]
FEAT=[c for c in Ftr.columns if c not in BAD]
print(f"{len(FEAT)} fitur untuk taksiran depth (buang {len(BAD)})")
dec=~C.rnd_tr; ytr=np.log10(C.d_tr+1)
Xd=Ftr[FEAT]; Xd_te=Fte[FEAT]
oof=np.full(len(C.y),np.nan); pte=np.zeros(len(Fte))
sub=np.where(dec)[0]
for ti,vi in GroupKFold(5).split(sub,None,C.ev[sub]):
    tr,va=sub[ti],sub[vi]
    m=lgb.LGBMRegressor(n_estimators=1500,learning_rate=0.03,num_leaves=31,
                        min_child_samples=40,colsample_bytree=0.7,subsample=0.8,
                        subsample_freq=1,verbose=-1,n_jobs=-1)
    m.fit(Xd.iloc[tr],ytr[tr],eval_set=[(Xd.iloc[va],ytr[va])],
          callbacks=[lgb.early_stopping(150,verbose=False)])
    oof[va]=m.predict(Xd.iloc[va]); pte+=m.predict(Xd_te)/5
# model penuh utk record depth-bulat
mfull=lgb.LGBMRegressor(n_estimators=800,learning_rate=0.03,num_leaves=31,min_child_samples=40,
                        colsample_bytree=0.7,subsample=0.8,subsample_freq=1,verbose=-1,n_jobs=-1)
mfull.fit(Xd.iloc[sub],ytr[sub]); oof[C.rnd_tr]=mfull.predict(Xd[C.rnd_tr])
r=np.corrcoef(oof[dec],ytr[dec])[0,1]
print(f"taksiran depth di holdout desimal: korelasi={r:.3f} R2={r**2:.3f} "
      f"MAE(log10 depth)={np.abs(oof[dec]-ytr[dec]).mean():.3f}")
print(f"  depth asli median={10**np.median(ytr[dec])-1:.1f} km, taksiran median={10**np.median(oof[dec])-1:.1f} km")
print(f"  untuk record depth-bulat 10.0: taksiran median={10**np.median(oof[np.isclose(C.d_tr,10)])-1:.1f} km")

def add_depth_feats(F, dep, dhat, dist):
    G=F.copy()
    dh=np.clip(10**dhat-1, 1, 700)
    G["dep_hat"]=dh.astype(np.float32)
    G["dep_hat_diff"]=(dhat-np.log10(dep+1)).astype(np.float32)
    hh=np.sqrt(dist**2+dh**2); G["loghypo_hat"]=np.log10(hh+1).astype(np.float32)
    for c in ["Pd_2","Pv_2","Pa_4","Pd_4"]:
        G[f"H{c}"]=(F[c].values+G["loghypo_hat"].values).astype(np.float32)
    return G.astype(np.float32)
Ftr2=add_depth_feats(Ftr,C.d_tr,oof,C.train.distance_km.values.astype(np.float32))
Fte2=add_depth_feats(Fte,C.d_te,pte,C.test.distance_km.values.astype(np.float32))
Gtr2=C.add_group_feats(Ftr2,C.train); Gte2=C.add_group_feats(Fte2,C.test)
SQ=C.make_sw(power=0.5)
print(f"\n{'model':>12}{'cv_real':>9}{'dec':>8}{'rnd':>8}{'lb_real':>9}{'bias':>8}")
for n,(Xt,Xe,sw) in {"resA_dep":(Ftr2,Fte2,SQ),"resB_dep":(Gtr2,Gte2,C.SW)}.items():
    o,_=M.cached(n, lambda Xt=Xt,Xe=Xe,sw=sw: M.cv_lgb(Xt,Xe,resid=True,sw=sw,Ftr=Ftr,Fte=Fte))
    print(f"{n:>12}{C.cv_real(o):9.4f}{C.part_real(o,True):8.4f}{C.part_real(o,False):8.4f}"
          f"{C.lb_real(o):9.4f}{C.bias_rnd(o):+8.3f}",flush=True)
print("pembanding: resA_sqrt 0.2101 (+0.015) | resB 0.2036 (+0.067)")
np.save(C.CACHE/"dhat.npy",np.r_[oof,pte])
