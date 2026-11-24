"""Adoption test for conditional blend weights.

Bar, set before looking: negative in ALL THREE fold families under BOTH nesting schemes,
a fold majority in both, and it must beat a random-conditioner negative control that has
exactly the same number of free parameters. The control is the point -- 5 weights per bin
is extra capacity, and capacity alone can lower a nested score.
"""
import numpy as np, pandas as pd, pickle, sys
sys.path.insert(0,'.')
import final_pipeline as FP
from scipy.optimize import nnls
BASE=['hbt','cat','ridge','enet','ridge_e']; S=(0,1,2); SH=0.25
cache=pickle.load(open('outputs/h7_oof.pkl','rb'))
g=FP.load_grid(); y=g[FP.TARGET]; IDX=g.index; FEAT=FP.make_features(g)
is_tr=(g.is_test==0).values & y.notna().values; is_te=(g.is_test==1).values
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
rng=np.random.default_rng(7)
CONDS={'T':FEAT['T'],'tod':FEAT['tod'],'rh_tmin48':FEAT['rh_tmin48']}
for j in range(3):
    CONDS['rand%d'%j]=pd.Series(rng.normal(size=len(FEAT)),index=FEAT.index)
rows=[]
for fam,folds in FAMS.items():
    for fi,(vs,ve) in enumerate(folds):
        v=is_tr&(IDX>vs)&(IDX<=ve)
        if v.sum()<50 or any((fam,fi,m,'',S) not in cache for m in BASE): continue
        d=pd.DataFrame({m:cache[(fam,fi,m,'',S)] for m in BASE})
        d['y']=y[v].values; d['fam']=fam; d['fold']=fi
        for k2,s in CONDS.items(): d[k2]=s[v].values
        rows.append(d)
A=pd.concat(rows,ignore_index=True)
FOLDN={fam:[k for k in sorted(A[A.fam==fam].fold.unique())] for fam in FAMS}

def run(nb,bg,cv,loo):
    per,tags=[],[]
    for fam in FAMS:
        D=A[A.fam==fam]
        for k in FOLDN[fam]:
            prev=D[D.fold!=k] if loo else D[D.fold<k]
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
            per.append(rmse(np.clip(p,5,100),cur.y)); tags.append(fam)
    return np.array(per),np.array(tags)

for loo in (False,True):
    ref,tags=run(1,0,'T',loo)
    print('\n===== %s   reference %.4f over %d folds ====='
          %('leave-one-fold-out' if loo else 'expanding window (shipped protocol)',ref.mean(),len(ref)))
    print('%-30s %8s %9s %8s   %s'%('config','mean','delta','won','per family'))
    for cv in CONDS:
        for nb,bg in [(3,0.5),(4,0.5),(5,0.5),(4,0.3)]:
            per,_=run(nb,bg,cv,loo)
            fs={f:round(float(per[tags==f].mean()-ref[tags==f].mean()),4) for f in FAMS}
            won=int((per<ref).sum())
            ok='PASS' if all(v<0 for v in fs.values()) and won>len(ref)/2 else ''
            print('%-30s %8.4f %+9.4f %4d/%-3d %s %s'
                  %('%s %db shrink%.1f'%(cv,nb,bg),per.mean(),per.mean()-ref.mean(),won,len(ref),fs,ok))

print('\n===== s46 guard: do the test rows land in the same bins as the training rows? =====')
for cv in ['T','tod','rh_tmin48']:
    tr_v=FEAT.loc[is_tr,cv].values; te_v=FEAT.loc[is_te,cv].values
    for nb in (4,):
        e=np.nanquantile(tr_v,np.linspace(0,1,nb+1)); e[0]=-1e18; e[-1]=1e18
        ctr=np.bincount(np.digitize(tr_v,e[1:-1]),minlength=nb)/len(tr_v)
        cte=np.bincount(np.digitize(te_v,e[1:-1]),minlength=nb)/len(te_v)
        print('  %-10s %d bins  edges %s'%(cv,nb,np.round(e[1:-1],2)))
        print('             train occupancy %s'%np.round(ctr,3))
        print('             test  occupancy %s   max shift %+.3f'%(np.round(cte,3),(cte-ctr)[np.argmax(abs(cte-ctr))]))
