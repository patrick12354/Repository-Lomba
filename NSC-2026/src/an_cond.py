"""Temperature-conditional blend weights.

Members are not equally good everywhere: across temperature quintiles cat runs 4.07 -> 11.10
while hbt runs 3.63 -> 7.01, so the NNLS optimum is not one vector. The shipped blend uses a
single global one. This fits a weight vector per bin, nested (weights from folds < k, scored
on fold k), and gates on the s38 bar: it must agree across all three fold families AND win a
majority of folds, or it does not get adopted.
"""
import numpy as np, pandas as pd, pickle, sys
sys.path.insert(0,'.')
import final_pipeline as FP
from scipy.optimize import nnls
BASE=['hbt','cat','ridge','enet','ridge_e']; S=(0,1,2); SH=0.25
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
def wfit(D,shrink=SH):
    if len(D)<150: return None
    w,_=nnls(D[BASE].values,D.y.values)
    w=w/w.sum() if w.sum()>0 else np.ones(5)/5
    return (1-shrink)*w+shrink*np.ones(5)/5

rows=[]
for fam,folds in FAMS.items():
    for fi,(vs,ve) in enumerate(folds):
        v=is_tr&(IDX>vs)&(IDX<=ve)
        if v.sum()<50 or any((fam,fi,m,'',S) not in cache for m in BASE): continue
        d=pd.DataFrame({m:cache[(fam,fi,m,'',S)] for m in BASE})
        d['y']=y[v].values; d['dt']=IDX[v]; d['fam']=fam; d['fold']=fi; d['T']=T[v].values
        rows.append(d)
A=pd.concat(rows,ignore_index=True)

def run(nbins, blend_global=0.0):
    """nbins=1 reproduces the shipped global blend. blend_global mixes the conditional
    weights back toward the global ones (0 = fully conditional, 1 = shipped)."""
    per=[]
    for fam in FAMS:
        D=A[A.fam==fam]
        for k in sorted(D.fold.unique()):
            prev,cur=D[D.fold<k],D[D.fold==k]
            if len(prev)<200: continue
            wg=wfit(prev)
            if nbins==1:
                p=cur[BASE].values@wg
            else:
                edges=np.quantile(prev['T'],np.linspace(0,1,nbins+1)); edges[0]=-1e9; edges[-1]=1e9
                bp=np.digitize(prev['T'],edges[1:-1]); bc=np.digitize(cur['T'],edges[1:-1])
                p=np.empty(len(cur))
                for b in range(nbins):
                    wb=wfit(prev[bp==b])
                    wb=wg if wb is None else (1-blend_global)*wb+blend_global*wg
                    m=bc==b
                    if m.any(): p[m]=cur[BASE].values[m]@wb
            per.append(rmse(np.clip(p,5,100),cur.y))
    return per

ref=run(1)
print('%-42s %8s %9s %11s'%('config','mean','delta','folds won'))
print('%-42s %8.4f %9s %11s'%('v8 shipped: one global weight vector',np.mean(ref),'--','--'))
best=None
for nb in (2,3,4,5):
    for bg in (0.0,0.3,0.5,0.7):
        per=run(nb,bg)
        won=sum(a<b for a,b in zip(per,ref)); d=np.mean(per)-np.mean(ref)
        fams=[]
        i=0
        for fam in FAMS:
            n=sum(1 for k in sorted(A[A.fam==fam].fold.unique())
                  if len(A[(A.fam==fam)&(A.fold<k)])>=200)
            fams.append(np.mean(per[i:i+n])-np.mean(ref[i:i+n])); i+=n
        allfam = all(x<0 for x in fams)
        print('%-42s %8.4f %+9.4f %5d/%-5d  per-family %s %s'
              %('%d T-bins, shrink-to-global %.1f'%(nb,bg),np.mean(per),d,won,len(ref),
                np.round(fams,4), 'ALL FAMILIES AGREE' if allfam else ''))
