"""Does the linear-leaf member earn its keep specifically where the model has to
extrapolate? Constant-leaf boosting cannot predict outside the range of its training
leaves; linear leaves can. The test window sits 3 degC below the training mean, further out
than any CV fold reaches, so if `lin` has a mechanism this is where it should show.
"""
import numpy as np, pandas as pd, pickle, sys
sys.path.insert(0,'.')
import final_pipeline as FP
from scipy.optimize import nnls
BASE=['hbt','cat','ridge','enet','ridge_e']; M6=BASE+['lin']; S=(0,1,2); SH=0.25
cache=pickle.load(open('outputs/h7_oof.pkl','rb'))
g=FP.load_grid(); y=g[FP.TARGET]; IDX=g.index; T=FP.make_features(g)['T']  # cleaned, despiked temperature
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
def rmse(a,b): return float(np.sqrt(np.mean((np.asarray(a)-np.asarray(b))**2)))
def wfit(D,models):
    w,_=nnls(D[models].values,D.y.values); w=w/w.sum() if w.sum()>0 else np.ones(len(models))/len(models)
    return (1-SH)*w+SH*np.ones(len(models))/len(models)

rows=[]
for fam,folds in FAMS.items():
    for fi,(vs,ve) in enumerate(folds):
        v=is_tr&(IDX>vs)&(IDX<=ve); t=is_tr&(IDX<=vs)
        if v.sum()<50 or any((fam,fi,m,'',S) not in cache for m in M6): continue
        d=pd.DataFrame({m:cache[(fam,fi,m,'',S)] for m in M6})
        d['y']=y[v].values; d['dt']=IDX[v]; d['fam']=fam; d['fold']=fi
        d['Tm']=T[v].values
        # how far below its own training range this row's temperature sits
        d['trT']=T[t].mean(); d['trTq05']=np.nanquantile(T[t],0.05)
        rows.append(d)
A=pd.concat(rows,ignore_index=True)

print('=== nested: 5-member vs 6-member, and where the difference lives ===')
per5,per6,meta=[],[],[]
for fam in FAMS:
    D=A[A.fam==fam]
    for k in sorted(D.fold.unique()):
        prev,cur=D[D.fold<k],D[D.fold==k]
        if len(prev)<200: continue
        p5=np.clip(cur[BASE].values@wfit(prev,BASE),5,100)
        p6=np.clip(cur[M6].values@wfit(prev,M6),5,100)
        per5.append(rmse(p5,cur.y)); per6.append(rmse(p6,cur.y))
        meta.append(dict(fam=fam,fold=k,dT=cur.Tm.mean()-cur.trT.iloc[0],
                         coldfrac=float((cur.Tm<cur.trTq05.iloc[0]).mean()),
                         d=per6[-1]-per5[-1]))
Mt=pd.DataFrame(meta)
Mt['r5']=per5; Mt['r6']=per6
print(Mt.round(4).to_string(index=False))
print('\nmean 5-member %.4f   6-member %.4f   delta %+.4f   folds won %d/%d'
      %(np.mean(per5),np.mean(per6),np.mean(per6)-np.mean(per5),
        sum(b<a for a,b in zip(per5,per6)),len(per5)))
print('per family:')
for fam in FAMS:
    s=Mt[Mt.fam==fam]
    print('  %s  5=%.4f 6=%.4f  d=%+.4f  won %d/%d'%(fam,s.r5.mean(),s.r6.mean(),
          s.r6.mean()-s.r5.mean(),(s.d<0).sum(),len(s)))
print('\ncorr(delta, window dT) = %+.3f  (negative => lin helps more on COLD windows)'
      %Mt.d.corr(Mt.dT))
print('corr(delta, frac rows below train 5th pct T) = %+.3f'%Mt.d.corr(Mt.coldfrac))

# row-level: solo accuracy of hbt vs lin by how far the row is outside its training range
print('\n=== solo RMSE by row temperature vs the fold\'s own training distribution ===')
A['below']=A.trT-A.Tm
A['bin']=pd.qcut(A.below,5,labels=['warmest','warm','mid','cool','coldest'])
r=A.groupby('bin',observed=True).apply(lambda d: pd.Series({
    'n':len(d),'meanT':d.Tm.mean(),
    'hbt':rmse(d.hbt,d.y),'lin':rmse(d.lin,d.y),'cat':rmse(d.cat,d.y),
    'enet':rmse(d.enet,d.y)}))
print(r.round(3).to_string())
print('\nthe test window sits at trT - Tm = %.2f (train mean T %.2f, test mean T %.2f)'
      %(T[is_tr].mean()-T[(g.is_test==1).values].mean(), T[is_tr].mean(),
        T[(g.is_test==1).values].mean()))
print('CV row range of trT - Tm: %.2f to %.2f, mean %.2f'%(A.below.min(),A.below.max(),A.below.mean()))
