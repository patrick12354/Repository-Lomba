import _path  # noqa: F401  -- menaruh Case 1/ di sys.path
import numpy as np
import lab_common as C, lab_models as M
Ftr,Fte=C.get_feats(); Gtr=C.add_group_feats(Ftr,C.train); Gte=C.add_group_feats(Fte,C.test)
SQ=C.make_sw(power=0.5); C30=C.make_sw(30)
jobs={
 "resA_sqrt": lambda: M.cv_lgb(Ftr,Fte,resid=True,sw=SQ,Ftr=Ftr,Fte=Fte),
 "resB_sqrt": lambda: M.cv_lgb(Gtr,Gte,resid=True,sw=SQ,Ftr=Ftr,Fte=Fte),
 "resB_c30":  lambda: M.cv_lgb(Gtr,Gte,resid=True,sw=C30,Ftr=Ftr,Fte=Fte),
 "resA_c30":  lambda: M.cv_lgb(Ftr,Fte,resid=True,sw=C30,Ftr=Ftr,Fte=Fte),
 # variasi struktural: leaves lebih kecil (event efektif cuma ~900)
 "resB_lf":   lambda: M.cv_lgb(Gtr,Gte,resid=True,Ftr=Ftr,Fte=Fte,
                               params=dict(num_leaves=15,min_child_samples=80,learning_rate=0.015)),
 "swA_sqrt_lf": lambda: M.cv_lgb(Ftr,Fte,sw=SQ,params=dict(num_leaves=63,colsample_bytree=0.5)),
}
for n,f in jobs.items():
    o,p=M.cached(n,f)
    print(f"{n:>14} cv_real={C.cv_real(o):.4f} dec={C.part_real(o,True):.4f} rnd={C.part_real(o,False):.4f} lb_real={C.lb_real(o):.4f} bias={C.bias_rnd(o):+.3f}", flush=True)
