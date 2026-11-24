import _path  # noqa: F401  -- menaruh Case 1/ di sys.path
import numpy as np, pandas as pd
import lab_common as C, lab_models as M
Ftr,Fte = C.get_feats()
Gtr = C.add_group_feats(Ftr, C.train); Gte = C.add_group_feats(Fte, C.test)
np.save(C.CACHE/"cols_G.npy", np.array(Gtr.columns))

oofA,pteA = M.cached("regA", lambda: M.cv_lgb(Ftr,Fte))
oofB,pteB = M.cached("regB", lambda: M.cv_lgb(Gtr,Gte))
oofRA,pteRA = M.cached("resA", lambda: M.cv_lgb(Ftr,Fte,resid=True,Ftr=Ftr,Fte=Fte))
oofRB,pteRB = M.cached("resB", lambda: M.cv_lgb(Gtr,Gte,resid=True,Ftr=Ftr,Fte=Fte))
for n,o in [("regA",oofA),("regB",oofB),("resA",oofRA),("resB",oofRB)]:
    print(f"{n}: raw CV={C.eb_twmae(C.y,o,C.ev):.4f} dec={C.part_score(o,True):.4f} rnd={C.part_score(o,False):.4f} lb_est={C.lb_estimate(o):.4f}")

# --- baseline nb3 ---
W=0.35
bo=(1-W)*oofA+W*oofB; bp=(1-W)*pteA+W*pteB
so=C.smooth_gen(bo,C.d_tr,0.95,0.0); sp=C.smooth_gen(bp,C.d_te,0.95,0.0)
print("\n=== SWEEP alpha terpisah dec vs rnd (base nb3 blend) ===")
print(f"{'a_dec':>6}{'a_rnd':>7}{'CV':>9}{'dec':>9}{'rnd':>9}{'lb_est':>9}{'bias':>8}{'sd_rnd_te':>11}")
for ad in [1.00,1.10,1.15,1.25]:
    for ar in [0.85,0.90,0.95,1.00,1.05,1.15]:
        o=C.expand_subset(so,C.d_tr,ad,ar); p=C.expand_subset(sp,C.d_te,ad,ar)
        print(f"{ad:6.2f}{ar:7.2f}{C.eb_twmae(C.y,o,C.ev):9.4f}{C.part_score(o,True):9.4f}"
              f"{C.part_score(o,False):9.4f}{C.lb_estimate(o):9.4f}{C.bias_rnd(o):+8.3f}{p[C.rnd_te].std():11.4f}")
