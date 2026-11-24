"""Does the disagreement estimator break on cool windows? The test window is cooler than
anything in training, and cool CV chunks are by far the hardest ones. If the members agree
with each other while all being wrong there, the estimator is blind exactly where it matters.
"""
import numpy as np, pandas as pd, pickle, sys
sys.path.insert(0, '.')
import final_pipeline as FP
from scipy.optimize import nnls
BASE = ['hbt', 'cat', 'ridge', 'enet', 'ridge_e']; S = (0, 1, 2)
cache = pickle.load(open('outputs/h7_oof.pkl', 'rb'))
g = FP.load_grid(); y = g[FP.TARGET]; IDX = g.index
is_tr = (g.is_test == 0).values & y.notna().values
idx = IDX[is_tr]; end = idx.max()
def famdef(n, vd, sd, mtd=30):
    out = []
    for i in range(n):
        cut = end - pd.Timedelta(days=sd*i); vs = cut - pd.Timedelta(days=vd)
        if (vs-idx.min()).days < mtd: break
        out.append((vs, cut))
    return out[::-1]
FAMS = {'P': famdef(9,15,2), 'Q': famdef(6,15,3,36), 'R': famdef(5,21,3,28)}
rows=[]
for fam, folds in FAMS.items():
    for fi,(vs,ve) in enumerate(folds):
        v = is_tr & (IDX>vs) & (IDX<=ve)
        if v.sum()<50 or (fam,fi,BASE[0],'',S) not in cache: continue
        d = pd.DataFrame({m: cache[(fam,fi,m,'',S)] for m in BASE})
        d['y']=y[v].values; d['dt']=IDX[v]; d['fam']=fam; d['fold']=fi
        rows.append(d)
A = pd.concat(rows, ignore_index=True)
w,_ = nnls(A[BASE].values, A.y.values); w=w/w.sum(); w=0.75*w+0.25*np.ones(5)/5
Wv = w/w.sum()
A['pred']=np.clip(A[BASE].values@w,5,100)
A['spread']=np.sqrt((Wv*(A[BASE].values-A.pred.values[:,None])**2).sum(1))
T = g.air_temperature
A['Tm'] = T.reindex(A.dt).values
A['chunk']=A.dt.dt.floor('2D')
C = A.groupby(['fam','fold','chunk']).agg(n=('y','size'), rmse=('y', lambda s: np.nan),
                                          spread=('spread','mean'), Tm=('Tm','mean')).reset_index()
C['rmse'] = A.groupby(['fam','fold','chunk']).apply(
    lambda d: float(np.sqrt(((d.pred-d.y)**2).mean()))).values
C = C[C.n>=60]
import numpy.linalg as la
X=np.c_[np.ones(len(C)), C.spread]; b,*_=la.lstsq(X, C.rmse.values, rcond=None)
C['resid'] = C.rmse - X@b
print('estimator residual (actual RMSE - predicted from spread), by chunk temperature:')
C['Tbin']=pd.cut(C.Tm,[0,24,26,28,30,99],labels=['<24','24-26','26-28','28-30','>30'])
print(C.groupby('Tbin',observed=True).agg(n=('resid','size'), mean_rmse=('rmse','mean'),
      mean_spread=('spread','mean'), mean_resid=('resid','mean')).round(3).to_string())
print('\ncorr(resid, T_mean) = %+.3f' % C.resid.corr(C.Tm))

print('\n=== the coolest CV chunks, in detail ===')
print(C.nsmallest(12,'Tm')[['fam','fold','chunk','n','Tm','spread','rmse','resid']].round(2).to_string(index=False))

# two-variable estimator
X2=np.c_[np.ones(len(C)), C.spread, C.Tm]; b2,*_=la.lstsq(X2, C.rmse.values, rcond=None)
r2a=1-((C.rmse-X@b)**2).sum()/((C.rmse-C.rmse.mean())**2).sum()
r2b=1-((C.rmse-X2@b2)**2).sum()/((C.rmse-C.rmse.mean())**2).sum()
print('\nR2  spread only %.3f   spread+T_mean %.3f   beta=%s'%(r2a,r2b,np.round(b2,3)))
sp=np.load('outputs/test_member_spread.npy')
sub=pd.read_csv('outputs/submissions/v8_qblock.csv'); sub['dt']=pd.to_datetime(sub.datetime)
Tt=T.reindex(sub.dt).values; K=220
for nm,sl in [('public',slice(0,K)),('private',slice(K,None)),('full',slice(None))]:
    print('  %-8s spread %.3f  T_mean %.2f -> RMSE est (spread only) %.3f   (+T_mean) %.3f'
          %(nm, sp[sl].mean(), np.nanmean(Tt[sl]),
            b[0]+b[1]*sp[sl].mean(), b2[0]+b2[1]*sp[sl].mean()+b2[2]*np.nanmean(Tt[sl])))
