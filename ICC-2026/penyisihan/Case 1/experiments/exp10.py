"""Uji ulang co-membership DI SISI DEPTH-DESIMAL, di mana event-nya asli.
Uji lama memakai label dari pseudo-event depth-bulat yang melebur sampai 401 record,
jadi pasangan 'positif'-nya sebagian besar bukan gempa yang sama -> AUC 0,57 tak berarti."""
import _path  # noqa: F401  -- menaruh Case 1/ di sys.path
import numpy as np, pandas as pd, lightgbm as lgb
from sklearn.model_selection import GroupKFold
from sklearn.metrics import roc_auc_score
import lab_common as C

Ftr,_=C.get_feats()
dec = ~C.rnd_tr
idx = np.where(dec)[0]
dep = C.d_tr[idx]; evd = C.ev[idx]
z=np.load(C.CACHE/"resA_sqrt.npz"); pred=z["oof"]

# pool: pasangan dalam pita kedalaman sempit (meniru "semua record di depth 10.0")
band = np.floor(dep/12).astype(int)
rng=np.random.RandomState(0)
PAIR_F=["Cd_2","Cv_2","Ca_4","logE","cent_a","cent_d","fdom_a","lhr_a","tauc","taup_2",
        "tE50","E_slope","kurt","rectilin","planarity","gd_0.5_4","gv_1_2","hv_d",
        "bdra_1_3","bdra_10_20","bdrd_1_3","bdrd_10_20","rmsd_2","PdH_2","PdV_2"]
Fv = Ftr.iloc[idx][PAIR_F].values.astype(np.float32)
logd = Ftr.iloc[idx]["logdist"].values; snr=Ftr.iloc[idx]["snr_db"].values
pv = pred[idx]

rows_i=[];rows_j=[];lab=[];grp=[]
for b in np.unique(band):
    w=np.where(band==b)[0]
    if len(w)<40: continue
    e=evd[w]
    for _ in range(len(w)*12):
        a,c = rng.randint(len(w)), rng.randint(len(w))
        if a==c: continue
        rows_i.append(w[a]); rows_j.append(w[c])
        lab.append(int(e[a]==e[c])); grp.append(min(e[a],e[c]))
I=np.array(rows_i);J=np.array(rows_j);lab=np.array(lab);grp=np.array(grp)
print(f"pasangan={len(I)}  positif={lab.mean():.3f}  n_band={len(np.unique(band))}")

X = np.column_stack([np.abs(Fv[I]-Fv[J]),
                     np.abs(pv[I]-pv[J]), np.minimum(pv[I],pv[J]), np.maximum(pv[I],pv[J]),
                     np.abs(logd[I]-logd[J]), np.minimum(logd[I],logd[J]),
                     np.abs(snr[I]-snr[J])])
names=[f"d_{c}" for c in PAIR_F]+["d_pred","pred_min","pred_max","d_logd","logd_min","d_snr"]
def auc_of(cols,tag):
    Xs=X[:,cols]; aucs=[]
    for ti,vi in GroupKFold(3).split(Xs,lab,grp):
        m=lgb.LGBMClassifier(n_estimators=400,learning_rate=0.05,num_leaves=31,verbose=-1)
        m.fit(Xs[ti],lab[ti])
        aucs.append(roc_auc_score(lab[vi],m.predict_proba(Xs[vi])[:,1]))
    print(f"  {tag:28s} AUC={np.mean(aucs):.4f}")
    return np.mean(aucs)
allc=list(range(X.shape[1]))
noamp=[k for k,n in enumerate(names) if n not in ("d_pred","pred_min","pred_max","d_Cd_2","d_Cv_2","d_Ca_4","d_logE","d_rmsd_2","d_PdH_2","d_PdV_2")]
auc_of([names.index("d_pred")],"hanya |delta prediksi|")
auc_of(noamp,"tanpa proxy amplitudo")
auc_of(allc,"semua fitur")
