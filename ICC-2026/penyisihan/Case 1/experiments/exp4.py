import _path  # noqa: F401  -- menaruh Case 1/ di sys.path
import numpy as np, pandas as pd
import lab_common as C, lab_models as M
Ftr,Fte=C.get_feats(); Gtr=C.add_group_feats(Ftr,C.train); Gte=C.add_group_feats(Fte,C.test)
print("sensitivitas chunk:")
for ch in [5,8,12]:
    C.EVR=[C.make_ev_real(s,ch) for s in range(6)]
    o,_=M.cached("regA",None); print(f"  chunk={ch}: rnd_real(regA)={C.part_real(o,False):.4f}")
C.EVR=[C.make_ev_real(s,8) for s in range(8)]

cands={"cnt(base)":C.make_sw(), "cap30":C.make_sw(30), "cap15":C.make_sw(15),
       "cap8":C.make_sw(8), "cap5":C.make_sw(5), "sqrt":C.make_sw(power=0.5),
       "flat":C.mag_weight(C.y).astype(float)}
print(f"\n{'SW':>10}{'massRnd':>9}  {'A:cvR':>7}{'decR':>7}{'rndR':>7}{'lbR':>7}{'bias':>7}   {'B:cvR':>7}{'lbR':>7}{'bias':>7}")
res={}
for nm,sw in cands.items():
    oA,pA=M.cached(f"swA_{nm}", lambda sw=sw: M.cv_lgb(Ftr,Fte,sw=sw))
    oB,pB=M.cached(f"swB_{nm}", lambda sw=sw: M.cv_lgb(Gtr,Gte,sw=sw))
    res[nm]=(oA,pA,oB,pB)
    mr=sw[C.rnd_tr].sum()/sw.sum()
    print(f"{nm:>10}{mr:9.3f}  {C.cv_real(oA):7.4f}{C.part_real(oA,True):7.4f}{C.part_real(oA,False):7.4f}"
          f"{C.lb_real(oA):7.4f}{C.bias_rnd(oA):+7.3f}   {C.cv_real(oB):7.4f}{C.lb_real(oB):7.4f}{C.bias_rnd(oB):+7.3f}")
np.save(C.CACHE/"_done_exp4.npy",[1])
