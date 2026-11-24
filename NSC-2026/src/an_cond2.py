"""Stress-test the conditional-blend result.

s38's phantom gain came from a cheap scan whose winner did not survive a change of
protocol. So: four different conditioning variables, two nesting schemes, fixed vs quantile
bin edges, and a check that the test window actually occupies the same bins as CV.
"""
import numpy as np, pandas as pd, pickle, sys
sys.path.insert(0,'.')
import final_pipeline as FP
from scipy.optimize import nnls
BASE=['hbt','cat','ridge','enet','ridge_e']; S=(0,1,2); SH=0.25
cache=pickle.load(open('outputs/h7_oof.pkl','rb'))
g=FP.load_grid(); y=g[FP.TARGET]; IDX=g.index
FEAT=FP.make_features(g)
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
def wfit(D,shrink=SH,minn=150):
    if len(D)<minn: return None
    w,_=nnls(D[BASE].values,D.y.values); w=w/w.sum() if w.sum()>0 else np.ones(5)/5
    return (1-shrink)*w+shrink*np.ones(5)/5

COND={'T_clean':FEAT['T'], 'tod':FEAT['tod'], 'rh_tmin48':FEAT['rh_tmin48'],
      'esT':FEAT['esT'], 'co2':FEAT['co2']}
rows=[]
for fam,folds in FAMS.items():
    for fi,(vs,ve) in enumerate(folds):
        v=is_tr&(IDX>vs)&(IDX<=ve)
        if v.sum()<50 or any((fam,fi,m,'',S) not in cache for m in BASE): continue
        d=pd.DataFrame({m:cache[(fam,fi,m,'',S)] for m in BASE})
        d['y']=y[v].values; d['fam']=fam; d['fold']=fi
        for k2,s in COND.items(): d[k2]=s[v].values
        rows.append(d)
A=pd.concat(rows,ignore_index=True)
A['selfpred']=np.nan

def run(nb,bg,cv,loo=False):
    per=[]
    for fam in FAMS:
        D=A[A.fam==fam]; ks=sorted(D.fold.unique())
        for k in ks:
            prev = D[D.fold!=k] if loo else D[D.fold<k]
            cur=D[D.fold==k]
            if len(prev)<200: continue
            wg=wfit(prev)
            if nb==1: p=cur[BASE].values@wg
            else:
                e=np.nanquantile(prev[cv],np.linspace(0,1,nb+1)); e[0]=-1e18; e[-1]=1e18
                bp=np.digitize(prev[cv],e[1:-1]); bc=np.digitize(cur[cv],e[1:-1])
                p=np.empty(len(cur))
                for b in range(nb):
                    wb=wfit(prev[bp==b]); wb=wg if wb is None else (1-bg)*wb+bg*wg
                    m=bc==b
                    if m.any(): p[m]=cur[BASE].values[m]@wb
            per.append(rmse(np.clip(p,5,100),cur.y))
    return per

def famsplit(per,ref):
    out={};i=0
    for fam in FAMS:
        n=sum(1 for k in sorted(A[A.fam==fam].fold.unique()) if len(A[(A.fam==fam)&(A.fold<k)])>=200)
        out[fam]=np.mean(per[i:i+n])-np.mean(ref[i:i+n]); i+=n
    return out

for loo in (False,True):
    ref=run(1,0,'T_clean',loo)
    print('\n===== nesting: %s   reference %.4f ====='%('leave-one-fold-out' if loo else 'expanding window (shipped protocol)',np.mean(ref)))
    print('%-26s %8s %9s %9s %s'%('conditioning variable','mean','delta','won','per family'))
    for cv in COND:
        for nb,bg in [(4,0.5),(5,0.5)]:
            per=run(nb,bg,cv,loo); fs=famsplit(per,ref)
            ok='OK' if all(x<0 for x in fs.values()) and sum(a<b for a,b in zip(ref,per))>len(ref)/2 else ''
            print('%-26s %8.4f %+9.4f %4d/%-4d %s %s'%('%s, %d bins, shrink %.1f'%(cv,nb,bg),
                  np.mean(per),np.mean(per)-np.mean(ref),sum(a<b for a,b in zip(ref,per)),len(ref),
                  {k:round(v,4) for k,v in fs.items()},ok))

# ---- s46 guard: does the test window occupy the same bins as CV? ----
print('\n===== s46 guard: bin occupancy, train vs test =====')
is_te=(g.is_test==1).values
for cv in ['T_clean','tod','rh_tmin48']:
    tr_v=FEAT.loc[is_tr,cv]; te_v=FEAT.loc[is_te,cv]
    for nb in (4,5):
        e=np.nanquantile(tr_v,np.linspace(0,1,nb+1)); e[0]=-1e18; e[-1]=1e18
        ctr=np.bincount(np.digitize(tr_v,e[1:-1]),minlength=nb)/len(tr_v)
        cte=np.bincount(np.digitize(te_v,e[1:-1]),minlength=nb)/len(te_v)
        print('  %-10s %d bins  train %s   test %s'%(cv,nb,np.round(ctr,3),np.round(cte,3)))
