"""Rank the CV folds by how far their validation window has drifted from their own training
set (adversarial AUC, features only), then re-score every adopted change on the most-shifted
folds.  The private slice is the most-shifted window there is, so this is the closest CV can
get to it."""
import numpy as np, pandas as pd, pickle, sys
sys.path.insert(0,'.'); import final_pipeline as fp
import lightgbm as lgb
from sklearn.model_selection import cross_val_predict, StratifiedKFold
from sklearn.metrics import roc_auc_score
from scipy.optimize import nnls
B=fp.MODELS; S=(0,1,2)
cache=pickle.load(open('outputs/h7_oof.pkl','rb'))
g=fp.load_grid(); F=fp.make_features(g); y=g[fp.TARGET]; IDX=g.index
is_tr=(g.is_test==0).values & y.notna().values; idx=IDX[is_tr]; end=idx.max()
def famdef(n,vd,sd,mtd=30):
    out=[]
    for i in range(n):
        cut=end-pd.Timedelta(days=sd*i); vs=cut-pd.Timedelta(days=vd)
        if (vs-idx.min()).days<mtd: break
        out.append((vs,cut))
    return out[::-1]
FAMS={'P':famdef(9,15,2),'Q':famdef(6,15,3,36),'R':famdef(5,21,3,28)}
def adv_auc(a_idx,b_idx):
    X=pd.concat([F.loc[a_idx],F.loc[b_idx]]); lab=np.r_[np.zeros(len(a_idx)),np.ones(len(b_idx))]
    clf=lgb.LGBMClassifier(n_estimators=200,learning_rate=0.05,num_leaves=15,min_child_samples=30,
                           subsample=0.8,subsample_freq=1,colsample_bytree=0.7,verbose=-1,random_state=0)
    p=cross_val_predict(clf,X,lab,cv=StratifiedKFold(4,shuffle=True,random_state=0),method='predict_proba')[:,1]
    return roc_auc_score(lab,p)
rows=[]
for fam,folds in FAMS.items():
    for fi,(vs,ve) in enumerate(folds):
        v=is_tr&(IDX>vs)&(IDX<=ve)
        if v.sum()<50 or (fam,fi,B[0],'',S) not in cache: continue
        d=pd.DataFrame({m:cache[(fam,fi,m,'',S)] for m in B})
        d['y']=y[v].values; d['tod']=IDX[v].hour+IDX[v].minute/60; d['fam']=fam; d['fold']=fi
        rows.append(d)
A=pd.concat(rows,ignore_index=True)
def fit_w(O):
    w,_=nnls(O[B].values,O.y.values); w=w/w.sum() if w.sum()>0 else np.ones(5)/5
    return (1-fp.BLEND_SHRINK)*w+fp.BLEND_SHRINK*np.ones(5)/5
def dz(t):
    t=2*np.pi*np.asarray(t)/24; return np.column_stack([np.sin(t),np.cos(t)])
res=[]
for fam,folds in FAMS.items():
    Af=A[A.fam==fam]
    for fi,(vs,ve) in enumerate(folds):
        if fi not in Af.fold.values: continue
        vi=IDX[is_tr&(IDX>vs)&(IDX<=ve)]; ti=IDX[is_tr&(IDX<=vs)]
        auc=adv_auc(ti,vi)
        tr_=Af[Af.fold!=fi].copy(); va=Af[Af.fold==fi]
        w=fit_w(tr_); e,W=fp.tod_blend_weights(tr_,w)
        tr_['pred']=np.clip(fp.apply_tod_blend(tr_[B].values,tr_.tod.values,e,W),5,100)
        b=np.linalg.lstsq(np.c_[np.ones(len(tr_)),dz(tr_.tod.values)],(tr_.pred-tr_.y).values,rcond=None)[0][1:]
        bt=np.array([ (tr_.pred-tr_.y)[np.digitize(tr_.tod.values,np.quantile(tr_.tod.values,[1/3,2/3]))==i].mean() for i in range(3)])
        bt=bt-(tr_.pred-tr_.y).mean()
        g8 =np.clip(va[B].values@w,5,100)
        g10=np.clip(fp.apply_tod_blend(va[B].values,va.tod.values,e,W),5,100)
        g11=np.clip(g10-0.5*bt[np.digitize(va.tod.values,np.quantile(tr_.tod.values,[1/3,2/3]))],5,100)
        g12=np.clip(g10-0.5*(dz(va.tod.values)@b),5,100)
        res.append(dict(fam=fam,fold=fi,auc=auc,n=len(va),
            v8=fp.rmse(va.y,g8),v10=fp.rmse(va.y,g10),v11=fp.rmse(va.y,g11),v12=fp.rmse(va.y,g12)))
        print("  %s%d auc %.3f"%(fam,fi,auc),flush=True)
R=pd.DataFrame(res).sort_values('auc'); R.to_csv('outputs/exp_shiftfolds.csv',index=False)
print("\nfolds sorted by train->validation adversarial AUC (higher = more shifted):")
print(R[['fam','fold','auc','v8','v10','v11','v12']].round(4).to_string(index=False))
print("\n(for scale: train -> public slice and train -> private slice both score AUC 1.000,")
print(" i.e. the real test window is more shifted than ANY cross-validation fold.)")
for nm,sub in (('least-shifted half',R.head(len(R)//2)),('MOST-shifted half',R.tail(len(R)//2)),('all',R)):
    print("\n%s (AUC %.3f-%.3f):"%(nm,sub.auc.min(),sub.auc.max()))
    for c in ['v10','v11','v12']:
        print("   %s vs v8: %+.4f (%d/%d)   vs v10: %+.4f (%d/%d)"%(c,
            (sub[c]-sub.v8).mean(),(sub[c]<sub.v8).sum(),len(sub),
            (sub[c]-sub.v10).mean(),(sub[c]<sub.v10).sum(),len(sub)))
print("\ncorr(fold shift AUC, gain of v12 over v8) = %+.3f"%R.auc.corr(R.v12-R.v8))
print("corr(fold shift AUC, gain of v12 over v10) = %+.3f"%R.auc.corr(R.v12-R.v10))
