"""Is the blend as diurnally compressed on the TEST window as it is in CV?
Referee = a parameter-free physical RH estimate, 100*es(T_q05_48h)/es(T). It needs no
target, so it can be read on the test rows directly. What matters is the RATIO
pred_amplitude / referee_amplitude, compared between CV folds and the test window."""
import numpy as np, pandas as pd, pickle, sys
sys.path.insert(0,'.'); import final_pipeline as fp
from scipy.optimize import nnls
B=fp.MODELS; S=(0,1,2)
cache=pickle.load(open('outputs/h7_oof.pkl','rb'))
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
REF=['rh_q48','rh_tmin48']
rows=[]
for fam,folds in FAMS.items():
    for fi,(vs,ve) in enumerate(folds):
        v=is_tr&(IDX>vs)&(IDX<=ve)
        if v.sum()<50 or (fam,fi,B[0],'',S) not in cache: continue
        d=pd.DataFrame({m:cache[(fam,fi,m,'',S)] for m in B})
        d['y']=y[v].values; d['tod']=IDX[v].hour+IDX[v].minute/60; d['fam']=fam; d['fold']=fi
        for c in REF: d[c]=F.loc[IDX[v],c].values
        rows.append(d)
A=pd.concat(rows,ignore_index=True)
w,_=nnls(A[B].values,A.y.values); w=w/w.sum(); w=0.75*w+0.25*np.ones(5)/5
A['pred']=np.clip(A[B].values@w,5,100)
ed=np.quantile(A.tod.values,np.linspace(0,1,4)); ed[0],ed[-1]=-np.inf,np.inf
A['band']=np.digitize(A.tod.values,ed[1:-1])
def amp(p,b):
    m=pd.Series(np.asarray(p,float)).groupby(np.asarray(b)).mean(); return m.max()-m.min()
recs=[]
for (fa,fo),d in A.groupby(['fam','fold']):
    r=dict(fam=fa,fold=fo,pred=amp(d.pred,d.band),true=amp(d.y,d.band))
    for c in REF: r[c]=amp(d[c],d.band)
    r['p_over_true']=r['pred']/r['true']
    r['p_over_ref']=r['pred']/np.mean([r[c] for c in REF])
    r['true_over_ref']=r['true']/np.mean([r[c] for c in REF])
    recs.append(r)
C=pd.DataFrame(recs)
print(C.round(3).to_string(index=False))
print("\nCV: pred/true      %.3f - %.3f  (mean %.3f)"%(C.p_over_true.min(),C.p_over_true.max(),C.p_over_true.mean()))
print("CV: pred/referee   %.3f - %.3f  (mean %.3f)"%(C.p_over_ref.min(),C.p_over_ref.max(),C.p_over_ref.mean()))
print("CV: true/referee   %.3f - %.3f  (mean %.3f)"%(C.true_over_ref.min(),C.true_over_ref.max(),C.true_over_ref.mean()))
te=IDX[(g.is_test==1).values]; todte=te.hour+te.minute/60; bte=np.digitize(todte,ed[1:-1])
ref_te=np.mean([amp(F.loc[te,c].values,bte) for c in REF])
print("\ntest window referee amplitude: %.3f"%ref_te)
for nm in ['v8_qblock','v10_todblend','v11_seed5','v12_harmbias']:
    p=pd.read_csv(f'outputs/submissions/{nm}.csv',parse_dates=['datetime']).set_index('datetime')['air_humidity'].reindex(te).values
    a=amp(p,bte); print("  %-13s amplitude %.3f   pred/referee %.3f"%(nm,a,a/ref_te))
print("\nimplied true test amplitude if the model compresses as it does in CV: %.2f"%(
    amp(pd.read_csv('outputs/submissions/v10_todblend.csv',parse_dates=['datetime']).set_index('datetime')['air_humidity'].reindex(te).values,bte)/C.p_over_true.mean()))
