"""The metric is RMSE and the blend contains no L2-matched tree: `hbt` is huber alpha=2 and
`cat` is Huber delta=4.  Both deliberately under-weight large residuals, which is where s35's
under-dispersion comes from.  Test a plain-L2 LightGBM as a sixth member."""
import numpy as np, pandas as pd, pickle, sys, time, os
sys.path.insert(0,'.'); import final_pipeline as fp
import lightgbm as lgb
from scipy.optimize import nnls
B=fp.MODELS
res=pickle.load(open('outputs/dropblend_oof.pkl','rb'))
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
L2_KW=dict(fp.LGB_KW); L2_KW.pop('alpha'); L2_KW['objective']='regression'
CACHE='outputs/l2_member.pkl'
extra=pickle.load(open(CACHE,'rb')) if os.path.exists(CACHE) else {}
t0=time.time()
for fam,folds in FAMS.items():
    for fi,(vs,ve) in enumerate(folds):
        vm=is_tr&(IDX>vs)&(IDX<=ve); tm=is_tr&(IDX<=vs)
        if vm.sum()<50 or tm.sum()<300 or (fam,fi,'base') not in res: continue
        if (fam,fi) in extra: continue
        p=np.mean([lgb.LGBMRegressor(random_state=s,**L2_KW).fit(F[tm],y[tm]).predict(F[vm]) for s in (0,1,2)],0)
        extra[(fam,fi)]=pd.Series(np.clip(p,5,100),index=IDX[vm])
        pickle.dump(extra,open(CACHE,'wb')); print("  %s%d (%ds)"%(fam,fi,time.time()-t0),flush=True)
folds=sorted({(k[0],k[1]) for k in res if (k[0],k[1],'base') in res and (k[0],k[1]) in extra})
def dz(t):
    t=2*np.pi*np.asarray(t)/24; return np.column_stack([np.sin(t),np.cos(t)])
A=[]
for fam,fi in folds:
    d=res[(fam,fi,'base')].copy(); d['l2']=extra[(fam,fi)].reindex(d.index).values
    d['y']=y.reindex(d.index).values; d['tod']=d.index.hour+d.index.minute/60
    d['fam']=fam; d['fold']=fi
    A.append(d.reset_index(drop=True))
A=pd.concat(A,ignore_index=True)
print("\nsolo RMSE: hbt %.4f  l2 %.4f   residual corr(hbt,l2) %.3f"%(
    fp.rmse(A.y,A.hbt),fp.rmse(A.y,A.l2),np.corrcoef(A.hbt-A.y,A.l2-A.y)[0,1]))
def run(cols):
    out=[]
    for fam,fi in folds:
        tr_=A[~((A.fam==fam)&(A.fold==fi))].copy(); va=A[(A.fam==fam)&(A.fold==fi)]
        w,_=nnls(tr_[cols].values,tr_.y.values); w=w/w.sum() if w.sum()>0 else np.ones(len(cols))/len(cols)
        w=(1-fp.BLEND_SHRINK)*w+fp.BLEND_SHRINK*np.ones(len(cols))/len(cols)
        O=tr_.copy(); O['blend']=np.clip(O[cols].values@w,5,100)
        ed=np.quantile(O.tod.values,np.linspace(0,1,4)); ed[0],ed[-1]=-np.inf,np.inf
        bb=np.digitize(O.tod.values,ed[1:-1]); W={}
        for i in range(3):
            dsub=O[bb==i]
            wi,_=nnls(dsub[cols].values,dsub.y.values); wi=wi/wi.sum() if wi.sum()>0 else w
            wi=(1-fp.BLEND_SHRINK)*wi+fp.BLEND_SHRINK*np.ones(len(cols))/len(cols)
            W[i]=0.5*wi+0.5*w
        bv=np.digitize(va.tod.values,ed[1:-1])
        po=np.array([O[cols].values[j]@W[bb[j]] for j in range(len(O))])
        pv=np.array([va[cols].values[j]@W[bv[j]] for j in range(len(va))])
        po=np.clip(po,5,100); pv=np.clip(pv,5,100)
        hb=np.linalg.lstsq(np.c_[np.ones(len(O)),dz(O.tod.values)],po-O.y.values,rcond=None)[0][1:]
        out.append(dict(fam=fam,fold=fi,r=fp.rmse(va.y,np.clip(pv-0.5*(dz(va.tod.values)@hb),5,100)),
                        w=dict(zip(cols,np.round(w,3)))))
    return pd.DataFrame(out)
R5=run(B); R6=run(B+['l2'])
d=R6.r-R5.r
print("\nfull v12 stack, nested LOO (%d folds):"%len(R5))
print("  5 members: %.4f"%R5.r.mean())
print("  6 members: %.4f   delta %+.4f  (%d/%d folds)"%(R6.r.mean(),d.mean(),(d<0).sum(),len(d)))
for fam in ('P','Q','R'):
    s5=R5[R5.fam==fam]; s6=R6[R6.fam==fam]
    print("    family %s: %+.4f (%d/%d)"%(fam,s6.r.mean()-s5.r.mean(),(s6.r.values<s5.r.values).sum(),len(s5)))
rng=np.random.default_rng(2); bs=[rng.choice(d.values,len(d),replace=True).mean() for _ in range(20000)]
print("  bootstrap 95%% CI [%.4f, %.4f]"%(np.percentile(bs,2.5),np.percentile(bs,97.5)))
print("\npooled 6-member weights:", R6.w.iloc[-1])
