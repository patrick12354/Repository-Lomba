"""Latih model yang kurang untuk merekonstruksi nb1/nb2/nb5, lalu KALIBRASI metrik ke 5 titik LB."""
import _path  # noqa: F401  -- menaruh Case 1/ di sys.path
import numpy as np, pandas as pd
import lab_common as C, lab_models as M
Ftr,Fte=C.get_feats(); Gtr=C.add_group_feats(Ftr,C.train); Gte=C.add_group_feats(Fte,C.test)
RATIO=(C.rnd_te.mean()/C.rnd_tr.mean())/((1-C.rnd_te.mean())/(1-C.rnd_tr.mean()))
SW_IW=C.SW*np.where(C.rnd_tr,RATIO,1.0)
def mask_grp(G, dep):
    Gm=G.copy(); r=np.isclose(dep,np.round(dep))
    cols=[c for c in G.columns if c.startswith(("gm_","gd_","gs_","gx_","gr_")) or c=="grp_size"]
    Gm.loc[r,cols]=np.nan
    return Gm
GtrM=mask_grp(Gtr,C.d_tr); GteM=mask_grp(Gte,C.d_te)
for n,f in [("resB_iw", lambda: M.cv_lgb(Gtr,Gte,resid=True,sw=SW_IW,Ftr=Ftr,Fte=Fte)),
            ("resA_iw", lambda: M.cv_lgb(Ftr,Fte,resid=True,sw=SW_IW,Ftr=Ftr,Fte=Fte)),
            ("regB_mask", lambda: M.cv_lgb(GtrM,GteM))]:
    o,_=M.cached(n,f); print(f"{n}: cv_lama={C.eb_twmae(C.y,o,C.ev):.4f}",flush=True)
