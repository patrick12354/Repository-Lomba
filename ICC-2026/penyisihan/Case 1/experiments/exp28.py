"""Stacking: meta-model di atas prediksi OOF base + beberapa fitur konteks.
Blend linear memberi bobot yang sama di seluruh ruang fitur; stacker boleh
mempercayai model berbeda di rezim berbeda (mis. CNN saat SNR tinggi)."""
import _path  # noqa: F401  -- menaruh Case 1/ di sys.path
import numpy as np, pandas as pd, lightgbm as lgb
from sklearn.model_selection import GroupKFold
from sklearn.linear_model import Ridge
import lab_common as C
from fastscore import Scorer, Post
BASE=["regA","swA_sqrt","resA_dep","resB","resB_dep","resB_c30","resB_p05","cnn_sqrt","cnnres"]
O=np.stack([np.load(C.CACHE/f"{n}.npz")["oof"] for n in BASE]).T
T=np.stack([np.load(C.CACHE/f"{n}.npz")["pte"] for n in BASE]).T
F,Fe=C.get_feats()
CTX=["logdist","snr_db","is_clipped","depth_km","Pd_2","logE","cent_a"]
def mk(P,Fx,dep):
    D=pd.DataFrame(P,columns=BASE)
    D["p_mean"]=P.mean(1); D["p_sd"]=P.std(1); D["p_rng"]=P.max(1)-P.min(1)
    for c in CTX: D[c]=Fx[c].values
    D["is_rnd"]=np.isclose(dep,np.round(dep)).astype(np.int8)
    return D.astype(np.float32)
Xs, Xs_te = mk(O,F,C.d_tr), mk(T,Fe,C.d_te)
po=Post(C.d_tr,0.95,0.5,150,1.15,1.05); sc=Scorer(C.EVR,np.ones(len(C.y),bool))
w=np.load(C.CACHE/"w7_mean.npy")
OLD=["regA","swA_sqrt","resA_sqrt","resB","resB_sqrt","resB_c30","cnn_sqrt"]
lin=po(w@np.stack([np.load(C.CACHE/f"{n}.npz")["oof"] for n in OLD]))
print(f"blend linear (nb6)  lb_real={sc(lin):.4f} bias={C.bias_rnd(lin):+.3f}")

for tag,params in [("kecil",dict(num_leaves=7,min_child_samples=200,learning_rate=0.02,n_estimators=600,
                                 colsample_bytree=0.6,subsample=0.8,subsample_freq=1)),
                   ("sedang",dict(num_leaves=15,min_child_samples=100,learning_rate=0.02,n_estimators=900,
                                  colsample_bytree=0.6,subsample=0.8,subsample_freq=1)),
                   ("ridge",None)]:
    oof=np.zeros(len(C.y))
    for seed in (0,1,2):
        o=np.zeros(len(C.y))
        for ti,vi in GroupKFold(5).split(Xs,C.y,C.ev):
            if params is None:
                m=Ridge(alpha=3.0).fit(Xs.iloc[ti],C.y[ti],sample_weight=C.SW[ti])
                o[vi]=m.predict(Xs.iloc[vi])
            else:
                m=lgb.LGBMRegressor(objective="mae",verbose=-1,n_jobs=-1,random_state=seed,**params)
                m.fit(Xs.iloc[ti],C.y[ti],sample_weight=C.SW[ti])
                o[vi]=m.predict(Xs.iloc[vi])
        oof+=o/3
        if params is None: break
    q=po(oof)
    print(f"stacker {tag:7s} lb_real={sc(q):.4f} bias={C.bias_rnd(q):+.3f} (mentah {C.lb_real(oof):.4f})",flush=True)
