"""Simulate the public/private split inside CV, where the truth is known.
Each 15/21-day fold window is cut 30/70 by time (temporal) and also 30/70 at random.
Blend weights are fitted leave-one-fold-out, so every score is honest."""
import numpy as np, pandas as pd, pickle, sys
sys.path.insert(0,'.'); import final_pipeline as fp
from scipy.optimize import nnls
B=fp.MODELS; S=(0,1,2)
cache=pickle.load(open('outputs/h7_oof.pkl','rb'))
g=fp.load_grid(); y=g[fp.TARGET]; IDX=g.index
is_tr=(g.is_test==0).values & y.notna().values
idx=IDX[is_tr]; end=idx.max()
def famdef(n,vd,sd,mtd=30):
    out=[]
    for i in range(n):
        cut=end-pd.Timedelta(days=sd*i); vs=cut-pd.Timedelta(days=vd)
        if (vs-idx.min()).days<mtd: break
        out.append((vs,cut))
    return out[::-1]
FAMS={'P':famdef(9,15,2),'Q':famdef(6,15,3,36),'R':famdef(5,21,3,28)}
rows=[]
for fam,folds in FAMS.items():
    for fi,(vs,ve) in enumerate(folds):
        v=is_tr&(IDX>vs)&(IDX<=ve)
        if v.sum()<50 or (fam,fi,B[0],'',S) not in cache: continue
        d=pd.DataFrame({m:cache[(fam,fi,m,'',S)] for m in B})
        d['y']=y[v].values; d['dt']=IDX[v]; d['tod']=IDX[v].hour+IDX[v].minute/60
        d['fam']=fam; d['fold']=fi
        rows.append(d)
A=pd.concat(rows,ignore_index=True)
print("folds:",A.groupby('fam').fold.nunique().to_dict()," rows:",len(A))

def fit_w(O):
    w,_=nnls(O[B].values,O.y.values); w=w/w.sum() if w.sum()>0 else np.ones(5)/5
    return (1-fp.BLEND_SHRINK)*w+fp.BLEND_SHRINK*np.ones(5)/5

rng=np.random.default_rng(0)
res=[]
for fam in FAMS:
    Af=A[A.fam==fam]
    for fo in sorted(Af.fold.unique()):
        tr_=Af[Af.fold!=fo]; va=Af[Af.fold==fo].sort_values('dt').reset_index(drop=True)
        w=fit_w(tr_)
        edges,W=fp.tod_blend_weights(tr_.assign(tod=tr_.tod), w)
        pv8 =np.clip(va[B].values@w,5,100)
        pv10=np.clip(fp.apply_tod_blend(va[B].values,va.tod.values,edges,W),5,100)
        n=len(va); k=int(round(0.30*n))
        masks={'temporal':(np.arange(n)<k),'random':np.isin(np.arange(n),rng.choice(n,k,replace=False))}
        for sp,mk in masks.items():
            res.append(dict(fam=fam,fold=fo,split=sp,
                pub_v8=fp.rmse(va.y[mk],pv8[mk]),   pri_v8=fp.rmse(va.y[~mk],pv8[~mk]),
                pub_v10=fp.rmse(va.y[mk],pv10[mk]), pri_v10=fp.rmse(va.y[~mk],pv10[~mk]),
                all_v8=fp.rmse(va.y,pv8), all_v10=fp.rmse(va.y,pv10)))
R=pd.DataFrame(res)
R['gap_v8']=R.pri_v8-R.pub_v8; R['gap_v10']=R.pri_v10-R.pub_v10
pd.set_option('display.width',250)
print("\n=== private minus public RMSE, by split type ===")
print(R.groupby('split')[['gap_v8','gap_v10']].agg(['mean','std','min','max']).round(3).to_string())
print("\ncorr(public, private) across folds:")
for sp in ['temporal','random']:
    d=R[R.split==sp]; print(f"  {sp:9s} v8 {d.pub_v8.corr(d.pri_v8):+.3f}   v10 {d.pub_v10.corr(d.pri_v10):+.3f}")
print("\n=== does v10 beat v8?  measured on public vs on private ===")
for sp in ['temporal','random']:
    d=R[R.split==sp]
    dp=(d.pub_v10-d.pub_v8); dq=(d.pri_v10-d.pri_v8); da=(d.all_v10-d.all_v8)
    print(f"  {sp:9s}  public d {dp.mean():+.4f} ({(dp<0).sum()}/{len(dp)} folds better)"
          f"   private d {dq.mean():+.4f} ({(dq<0).sum()}/{len(dq)})"
          f"   whole d {da.mean():+.4f} ({(da<0).sum()}/{len(da)})")
    print(f"             agreement public/private on the sign of the v10-v8 delta: "
          f"{(np.sign(dp)==np.sign(dq)).mean():.2f}")
R.to_csv('outputs/exp_pubpriv_sim.csv',index=False)
print("\nper-fold (temporal split):")
print(R[R.split=='temporal'][['fam','fold','pub_v8','pri_v8','gap_v8','pub_v10','pri_v10','gap_v10']].round(3).to_string(index=False))
