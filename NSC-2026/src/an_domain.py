"""Domain-matched blend weights.

The test window's member disagreement averages 2.02, against a CV mean of 2.99 -- the test
rows sit at the coherent, easy end of the range the weights were fitted on. If the optimal
weight vector moves with disagreement, fitting on test-like rows should transfer better.
Nested throughout: weights come from folds < k, scored on fold k, exactly the s22/s30
protocol, so this cannot buy itself a phantom gain the way s38 did.
"""
import numpy as np, pandas as pd, pickle, sys
sys.path.insert(0,'.')
import final_pipeline as FP
from scipy.optimize import nnls
BASE=['hbt','cat','ridge','enet','ridge_e']; S=(0,1,2); SH=0.25
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

def frame(fam,models):
    rows=[]
    for fi,(vs,ve) in enumerate(FAMS[fam]):
        v=is_tr&(IDX>vs)&(IDX<=ve)
        if v.sum()<50 or any((fam,fi,m,'',S) not in cache for m in models): continue
        d=pd.DataFrame({m:cache[(fam,fi,m,'',S)] for m in models})
        d['y']=y[v].values; d['fold']=fi
        rows.append(d)
    return pd.concat(rows,ignore_index=True)

def wfit(D,models,shrink=SH):
    w,_=nnls(D[models].values,D.y.values)
    w=w/w.sum() if w.sum()>0 else np.ones(len(models))/len(models)
    return (1-shrink)*w+shrink*np.ones(len(models))/len(models)

def rmse(a,b): return float(np.sqrt(np.mean((np.asarray(a)-np.asarray(b))**2)))

def spread_of(D,models,w):
    p=D[models].values@w; wv=w/w.sum()
    return np.sqrt((wv*(D[models].values-p[:,None])**2).sum(1))

def run(models,mode,q=None):
    """mode: 'all' = shipped. 'low' = fit only on prior-fold rows whose member spread is
    below the q-quantile of prior-fold spread."""
    per=[]
    for fam in FAMS:
        D=frame(fam,models)
        if D.empty: continue
        for k in sorted(D.fold.unique()):
            prev=D[D.fold<k]; cur=D[D.fold==k]
            if len(prev)<200: continue
            w0=wfit(prev,models)                     # provisional, to measure spread
            if mode=='low':
                sp=spread_of(prev,models,w0)
                sel=prev[sp<=np.quantile(sp,q)]
                if len(sel)<200: sel=prev
                w=wfit(sel,models)
            else:
                w=w0
            per.append(rmse(np.clip(cur[models].values@w,5,100),cur.y))
    return np.mean(per),per

ref_m,ref=run(BASE,'all')
print('%-38s %8s %8s %8s'%('config','mean','delta','folds won'))
print('%-38s %8.4f %8s %8s'%('v8 shipped (weights on all rows)',ref_m,'--','--'))
for q in (0.75,0.5,0.33):
    m,per=run(BASE,'low',q)
    won=sum(a<b for a,b in zip(per,ref))
    print('%-38s %8.4f %+8.4f %5d/%d'%('weights on lowest-spread %d%% rows'%(q*100),m,m-ref_m,won,len(ref)))

print()
M6=BASE+['lin']
m6,per6=run(M6,'all'); won=sum(a<b for a,b in zip(per6,ref))
print('%-38s %8.4f %+8.4f %5d/%d'%('+ lin as a 6th member',m6,m6-ref_m,won,len(ref)))
for q in (0.5,):
    m,per=run(M6,'low',q); won=sum(a<b for a,b in zip(per,ref))
    print('%-38s %8.4f %+8.4f %5d/%d'%('+ lin, weights on lowest-spread 50%%',m,m-ref_m,won,len(ref)))

# does the optimal weight vector actually move with spread? direct look.
D=pd.concat([frame(f,BASE) for f in FAMS],ignore_index=True)
w0=wfit(D,BASE); sp=spread_of(D,BASE,w0)
print('\noptimal weights by member-disagreement tercile (unshrunk NNLS):')
for lab,sel in [('low  (test-like)',sp<=np.quantile(sp,1/3)),
                ('mid ',(sp>np.quantile(sp,1/3))&(sp<=np.quantile(sp,2/3))),
                ('high',sp>np.quantile(sp,2/3))]:
    w,_=nnls(D[sel][BASE].values,D[sel].y.values); w=w/w.sum()
    print('  %-16s %s   mean spread %.2f'%(lab,{m:round(float(x),3) for m,x in zip(BASE,w)},sp[sel].mean()))
print('  test window mean spread 2.018')
