"""s7 dropped the soil block on test-coverage grounds. The residual is unpredictable from the
118 columns that remain -- but the soil columns are not among them, so that result says
nothing about them.  Two questions: is there signal there, and can it be used at test time?"""
import numpy as np, pandas as pd, pickle, sys
sys.path.insert(0,'.'); import final_pipeline as fp
import lightgbm as lgb
from scipy.optimize import nnls
B=fp.MODELS
res=pickle.load(open('outputs/dropblend_oof.pkl','rb'))
g=fp.load_grid(); y=g[fp.TARGET]; IDX=g.index
c=fp.clean_exog(g); base=fp.build_features(c)          # BEFORE drop_soil
FULL=pd.concat([base, fp.tmin_block(c), fp.tend_block(c),
                fp.ordstat_block(c,'co2',fp.CO2_WINS),
                fp.qblock(c,fp.TMIN_WINS), fp.qblock(c,fp.CO2_WINS,col='co2',rh=False)],
               axis=1).replace([np.inf,-np.inf],np.nan)
KEPT=set(fp.make_features(g).columns)
SOIL=[cc for cc in FULL.columns if cc not in KEPT]
print("columns dropped by drop_soil: %d"%len(SOIL))
is_tr=(g.is_test==0).values; te=IDX[(g.is_test==1).values]
lo,hi=FULL[is_tr].quantile(.01),FULL[is_tr].quantile(.99)
cov=(((FULL.loc[te]>=lo)&(FULL.loc[te]<=hi))|FULL.loc[te].isna()).mean()
covp=(((FULL.loc[te[220:]]>=lo)&(FULL.loc[te[220:]]<=hi))|FULL.loc[te[220:]].isna()).mean()
print("\ntest support of the dropped columns (s19.2 bar 0.916):")
d=pd.DataFrame({'test':cov[SOIL],'private':covp[SOIL]}).sort_values('test')
print(d.round(3).to_string())
print("  above the 0.916 bar: %d of %d"%((d.test>=0.916).sum(),len(d)))
USABLE=[cc for cc in SOIL if cov[cc]>=0.916]
print("  usable columns: %s"%USABLE)
# rebuild the nested OOF prediction
folds=sorted({(k[0],k[1]) for k in res if (k[0],k[1],'base') in res})
def dz(t):
    t=2*np.pi*np.asarray(t)/24; return np.column_stack([np.sin(t),np.cos(t)])
A=[]
for fam,fi in folds:
    dd=res[(fam,fi,'base')].copy(); dd['y']=y.reindex(dd.index).values
    dd['tod']=dd.index.hour+dd.index.minute/60; dd['fam']=fam; dd['fold']=fi; dd['dt']=dd.index
    A.append(dd.reset_index(drop=True))
A=pd.concat(A,ignore_index=True)
def fit_w(O):
    w,_=nnls(O[B].values,O.y.values); w=w/w.sum() if w.sum()>0 else np.ones(5)/5
    return (1-fp.BLEND_SHRINK)*w+fp.BLEND_SHRINK*np.ones(5)/5
P=[]
for fam,fi in folds:
    tr_=A[~((A.fam==fam)&(A.fold==fi))].copy(); va=A[(A.fam==fam)&(A.fold==fi)]
    w=fit_w(tr_); e,W=fp.tod_blend_weights(tr_,w)
    tr_['pred']=np.clip(fp.apply_tod_blend(tr_[B].values,tr_.tod.values,e,W),5,100)
    b=np.linalg.lstsq(np.c_[np.ones(len(tr_)),dz(tr_.tod.values)],(tr_.pred-tr_.y).values,rcond=None)[0][1:]
    p=np.clip(fp.apply_tod_blend(va[B].values,va.tod.values,e,W),5,100)
    P.append(pd.Series(np.clip(p-0.5*(dz(va.tod.values)@b),5,100),index=va.index))
A['pred']=pd.concat(P).sort_index(); A['dt']=pd.DatetimeIndex(A.dt)
U=A.groupby('dt').agg(pred=('pred','mean'),y=('y','first')).sort_index(); U['r']=U.pred-U.y
KW=dict(objective='huber',alpha=2.0,n_estimators=400,learning_rate=0.03,num_leaves=15,
        min_child_samples=40,subsample=0.8,subsample_freq=1,colsample_bytree=0.7,reg_lambda=5.0,verbose=-1)
end=U.index.max()
for nm,cols in (('ALL dropped soil columns',SOIL),('only the usable ones',USABLE)):
    if not cols: continue
    X=FULL.loc[U.index,cols]; out=[]
    for i in range(8):
        cut=end-pd.Timedelta(days=2*i); vs=cut-pd.Timedelta(days=15)
        vm=(U.index>vs)&(U.index<=cut); tm=U.index<=vs
        if tm.sum()<300 or vm.sum()<80: continue
        gp=lgb.LGBMRegressor(random_state=0,**KW).fit(X[tm],U.r[tm]).predict(X[vm])
        rec=dict(base=fp.rmse(U.y[vm],U.pred[vm]))
        for s in (0.25,0.5,1.0): rec[f's{s}']=fp.rmse(U.y[vm],np.clip(U.pred[vm]-s*gp,5,100))
        out.append(rec)
    R=pd.DataFrame(out)
    print("\nstage-2 on the residual using %s (%d cols, %d time-blocked folds):"%(nm,len(cols),len(R)))
    for s in (0.25,0.5,1.0):
        dd=R[f's{s}']-R.base
        print("   x%.2f: %+.4f  (%d/%d folds)"%(s,dd.mean(),(dd<0).sum(),len(R)))
