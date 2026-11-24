"""10-fold: tiap model fold melihat 90% data (bukan 80%). Dengan hanya ~905 event efektif,
itu perbedaan nyata untuk prediksi test."""
import _path  # noqa: F401  -- menaruh Case 1/ di sys.path
import numpy as np
import lab_common as C, lab_models as M
Ftr,Fte=C.get_feats()
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
Gtr=C.add_group_feats(Ftr,C.train); Gte=C.add_group_feats(Fte,C.test)
SQ=C.make_sw(power=0.5); C30=C.make_sw(30); P05=C.mag_weight(C.y)**0.5/C.cnt
jobs={"f10_swA_sqrt":(Ftr,Fte,False,SQ),
      "f10_resA_dep":(F2,F2e,True,SQ),
      "f10_resB_dep":(G2,G2e,True,C.SW),
      "f10_resB_c30":(Gtr,Gte,True,C30),
      "f10_resB_p05":(Gtr,Gte,True,P05)}
print(f"{'model':>14}{'cv_real':>9}{'dec':>8}{'rnd':>8}{'lb_real':>9}{'bias':>8}   (5-fold)")
ref={"f10_swA_sqrt":0.2142,"f10_resA_dep":0.2088,"f10_resB_dep":0.2031,"f10_resB_c30":0.2047,"f10_resB_p05":0.2030}
for n,(Xt,Xe,rs,sw) in jobs.items():
    o,_=M.cached(n, lambda Xt=Xt,Xe=Xe,rs=rs,sw=sw: M.cv_lgb(Xt,Xe,resid=rs,sw=sw,Ftr=Ftr,Fte=Fte,nfold=10))
    print(f"{n:>14}{C.cv_real(o):9.4f}{C.part_real(o,True):8.4f}{C.part_real(o,False):8.4f}"
          f"{C.lb_real(o):9.4f}{C.bias_rnd(o):+8.3f}   ({ref[n]:.4f})",flush=True)
