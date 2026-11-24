"""Is the model biased low when the validation window is cooler/moister than its training
data? That is exactly the test set's situation, and it is the one systematic error that a
post-hoc step could in principle fix -- so it needs measuring, not assuming.
"""
import numpy as np, pandas as pd, pickle, sys
sys.path.insert(0,'.')
import final_pipeline as FP
from scipy.optimize import nnls
BASE=['hbt','cat','ridge','enet','ridge_e']; S=(0,1,2)
cache=pickle.load(open('outputs/h7_oof.pkl','rb'))
g=FP.load_grid(); y=g[FP.TARGET]; IDX=g.index
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
T=g.air_temperature
rows=[]
for fam,folds in FAMS.items():
    for fi,(vs,ve) in enumerate(folds):
        v=is_tr&(IDX>vs)&(IDX<=ve); t=is_tr&(IDX<=vs)
        if v.sum()<50 or (fam,fi,BASE[0],'',S) not in cache: continue
        d=pd.DataFrame({m:cache[(fam,fi,m,'',S)] for m in BASE})
        d['y']=y[v].values; d['dt']=IDX[v]; d['fam']=fam; d['fold']=fi
        d['trT']=T[t].mean(); d['trY']=y[t].mean()
        rows.append(d)
A=pd.concat(rows,ignore_index=True)
w,_=nnls(A[BASE].values,A.y.values); w=w/w.sum(); w=0.75*w+0.25*np.ones(5)/5
A['pred']=np.clip(A[BASE].values@w,5,100); A['e']=A.pred-A.y
A['Tm']=T.reindex(A.dt).values

print('=== fold-level: bias vs how much cooler the window is than its own training data ===')
print('%3s %5s %8s %8s %8s %8s %8s'%('fam','fold','trainT','valT','dT','bias','rmse'))
recs=[]
for (fam,fi),d in A.groupby(['fam','fold']):
    dT=d.Tm.mean()-d.trT.iloc[0]
    recs.append(dict(fam=fam,fold=fi,dT=dT,bias=d.e.mean(),
                     rmse=float(np.sqrt((d.e**2).mean())),
                     dispersion=d.pred.std()/d.y.std()))
    print('%3s %5d %8.2f %8.2f %8.2f %+8.3f %8.3f'%(fam,fi,d.trT.iloc[0],d.Tm.mean(),dT,d.e.mean(),recs[-1]['rmse']))
R=pd.DataFrame(recs)
print('\ncorr(bias, dT) = %+.3f    slope = %+.4f RH per degC'
      %(R.bias.corr(R.dT), np.polyfit(R.dT,R.bias,1)[0]))
print('corr(dispersion, dT) = %+.3f'%R.dispersion.corr(R.dT))

# chunk level, more points
A['chunk']=A.dt.dt.floor('2D')
CK=A.groupby(['fam','fold','chunk']).agg(n=('y','size'),bias=('e','mean'),
     rmse=('e',lambda s: float(np.sqrt((s**2).mean()))),Tm=('Tm','mean'),trT=('trT','first')).reset_index()
CK=CK[CK.n>=60]; CK['dT']=CK.Tm-CK.trT
print('\n=== chunk level (n=%d) ==='%len(CK))
CK['bin']=pd.cut(CK.dT,[-99,-5,-3,-1,1,99],labels=['<-5','-5..-3','-3..-1','-1..1','>1'])
print(CK.groupby('bin',observed=True).agg(n=('bias','size'),mean_dT=('dT','mean'),
     mean_bias=('bias','mean'),mean_rmse=('rmse','mean')).round(3).to_string())
print('corr(bias, dT) = %+.3f'%CK.bias.corr(CK.dT))

# the real test situation
sub=pd.read_csv('outputs/submissions/v8_qblock.csv'); sub['dt']=pd.to_datetime(sub.datetime)
Tt=T.reindex(sub.dt).values; K=220
trT_full=T[is_tr].mean()
print('\n=== the real fit ===')
print('train mean T = %.2f'%trT_full)
for nm,sl in [('public',slice(0,K)),('private',slice(K,None)),('full',slice(None))]:
    dT=np.nanmean(Tt[sl])-trT_full
    print('  %-8s valT %.2f  dT %+.2f  -> fold-level bias extrapolation %+.3f RH'
          %(nm,np.nanmean(Tt[sl]),dT,np.polyval(np.polyfit(R.dT,R.bias,1),dT)))
print('  CV dT range: %.2f to %.2f'%(R.dT.min(),R.dT.max()))
print('\nv8 predicted mean: public %.2f private %.2f full %.2f | train y mean %.2f'
      %(sub.air_humidity[:K].mean(),sub.air_humidity[K:].mean(),sub.air_humidity.mean(),y[is_tr].mean()))
