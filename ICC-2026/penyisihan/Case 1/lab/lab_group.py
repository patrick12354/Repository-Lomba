"""Soft event grouping: classifier pasangan -> bobot co-membership -> smoothing lunak."""
import numpy as np, lightgbm as lgb
import lab_common as C

PAIR_F=["Cd_2","Cv_2","Ca_4","logE","cent_a","cent_d","fdom_a","lhr_a","tauc","taup_2",
        "tE50","E_slope","kurt","rectilin","planarity","gd_0.5_4","gv_1_2","hv_d",
        "bdra_1_3","bdra_10_20","bdrd_1_3","bdrd_10_20","rmsd_2","PdH_2","PdV_2"]

class PairFeat:
    def __init__(self, F, pred):
        self.V=F[PAIR_F].values.astype(np.float32)
        self.logd=F["logdist"].values.astype(np.float32)
        self.snr=F["snr_db"].values.astype(np.float32)
        self.p=pred.astype(np.float32)
    def __call__(self, I, J):
        V,p,logd,snr=self.V,self.p,self.logd,self.snr
        return np.column_stack([np.abs(V[I]-V[J]),
            np.abs(p[I]-p[J]), np.minimum(p[I],p[J]), np.maximum(p[I],p[J]),
            np.abs(logd[I]-logd[J]), np.minimum(logd[I],logd[J]),
            np.abs(snr[I]-snr[J])]).astype(np.float32)

def sample_pairs(pool_idx, ev, rng, mult=12):
    I=[];J=[];lab=[]
    for w in pool_idx:
        if len(w)<20: continue
        e=ev[w]
        a=rng.randint(0,len(w),len(w)*mult); c=rng.randint(0,len(w),len(w)*mult)
        m=a!=c; a,c=a[m],c[m]
        I.append(w[a]); J.append(w[c]); lab.append((e[a]==e[c]).astype(int))
    return np.concatenate(I),np.concatenate(J),np.concatenate(lab)

def train_pair_clf(PF, I, J, lab, seed=0):
    X=PF(I,J)
    m=lgb.LGBMClassifier(n_estimators=500,learning_rate=0.05,num_leaves=31,
                         min_child_samples=60,subsample=0.8,subsample_freq=1,
                         colsample_bytree=0.7,verbose=-1,random_state=seed,n_jobs=-1)
    m.fit(X,lab); return m

def soft_smooth(p, PF, clf, pools, lam=0.6, gamma=2.0, topk=None, chunk=400):
    """p -> prediksi dihaluskan memakai bobot co-membership dalam tiap pool."""
    out=p.copy()
    for w in pools:
        n=len(w)
        if n<3: continue
        Pm=np.empty((n,n),dtype=np.float32)
        for s in range(0,n,chunk):
            e=min(s+chunk,n)
            I=np.repeat(w[s:e],n); J=np.tile(w,e-s)
            Pm[s:e]=clf.predict_proba(PF(I,J))[:,1].reshape(e-s,n)
        Pm=(Pm+Pm.T)/2
        np.fill_diagonal(Pm,1.0)
        W=Pm**gamma
        if topk is not None and topk<n:
            th=np.partition(W,n-topk,axis=1)[:,n-topk][:,None]
            W=np.where(W>=th,W,0.0)
        sm=(W@p[w])/W.sum(1)
        out[w]=(1-lam)*p[w]+lam*sm
    return out
