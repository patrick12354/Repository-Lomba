"""(a) koreksi covariate shift lewat density ratio train-vs-test
   (b) uji ulang eksponen tail w(M)^p DI BAWAH metrik terkoreksi"""
import _path  # noqa: F401  -- menaruh Case 1/ di sys.path
import numpy as np, pandas as pd, lightgbm as lgb
from sklearn.model_selection import GroupKFold
from sklearn.metrics import roc_auc_score
import lab_common as C, lab_models as M
Ftr,Fte=C.get_feats(); Gtr=C.add_group_feats(Ftr,C.train); Gte=C.add_group_feats(Fte,C.test)

# --- (a) seberapa besar covariate shift-nya? ---
X=pd.concat([Ftr,Fte],ignore_index=True); t=np.r_[np.zeros(len(Ftr)),np.ones(len(Fte))]
grp=np.r_[C.ev, C.ev.max()+1+np.arange(len(Fte))]
dr=np.zeros(len(X)); aucs=[]
for ti,vi in GroupKFold(4).split(X,t,grp):
    m=lgb.LGBMClassifier(n_estimators=400,learning_rate=0.05,num_leaves=31,
                         min_child_samples=60,colsample_bytree=0.7,verbose=-1,n_jobs=-1)
    m.fit(X.iloc[ti],t[ti]); p=m.predict_proba(X.iloc[vi])[:,1]
    dr[vi]=p; aucs.append(roc_auc_score(t[vi],p))
print(f"AUC train-vs-test = {np.mean(aucs):.4f}  (0,5 = tidak ada shift)")
r=dr[:len(Ftr)]; ratio=np.clip(r/(1-r+1e-9),0.1,10)
ratio*= len(Ftr)/ratio.sum()*1.0
print("density ratio: median=%.2f  p90=%.2f  rata2 di rnd=%.2f di dec=%.2f"%(
    np.median(ratio),np.percentile(ratio,90),ratio[C.rnd_tr].mean(),ratio[~C.rnd_tr].mean()))
np.save(C.CACHE/"dratio.npy",ratio)

SQ=C.make_sw(power=0.5)
jobs={"resA_dr": (Ftr,Fte,True, SQ*ratio),
      "resB_dr": (Gtr,Gte,True, C.SW*ratio),
      "resA_p05":(Ftr,Fte,True, C.mag_weight(C.y)**0.5/np.sqrt(C.cnt)),
      "resA_p15":(Ftr,Fte,True, C.mag_weight(C.y)**1.5/np.sqrt(C.cnt)),
      "resB_p05":(Gtr,Gte,True, C.mag_weight(C.y)**0.5/C.cnt),
      "resB_p15":(Gtr,Gte,True, C.mag_weight(C.y)**1.5/C.cnt)}
print(f"\n{'model':>10}{'cv_real':>9}{'dec':>8}{'rnd':>8}{'lb_real':>9}{'bias':>8}")
for n,(Xt,Xe,rs,sw) in jobs.items():
    o,_=M.cached(n, lambda Xt=Xt,Xe=Xe,rs=rs,sw=sw: M.cv_lgb(Xt,Xe,resid=rs,sw=sw,Ftr=Ftr,Fte=Fte))
    print(f"{n:>10}{C.cv_real(o):9.4f}{C.part_real(o,True):8.4f}{C.part_real(o,False):8.4f}"
          f"{C.lb_real(o):9.4f}{C.bias_rnd(o):+8.3f}",flush=True)
print("\npembanding: resA_sqrt lb_real=0.2101 bias=+0.015 | resB lb_real=0.2036 bias=+0.067 | resB_c30 0.2047 +0.041")
