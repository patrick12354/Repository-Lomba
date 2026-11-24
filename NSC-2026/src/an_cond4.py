"""Final verification of time-of-day-conditional blend weights before recommending it.

Winner from an_cond3: tod, 3 bins, shrink-to-global 0.5. What the weights actually are,
whether the per-fold deltas are distinguishable from zero, and what it does to the test
predictions.
"""
import numpy as np, pandas as pd, pickle, sys
sys.path.insert(0,'.')
import final_pipeline as FP
from scipy.optimize import nnls
BASE=['hbt','cat','ridge','enet','ridge_e']; S=(0,1,2); SH=0.25; NB=3; BG=0.5
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
rows=[]
for fam,folds in FAMS.items():
    for fi,(vs,ve) in enumerate(folds):
        v=is_tr&(IDX>vs)&(IDX<=ve)
        if v.sum()<50 or any((fam,fi,m,'',S) not in cache for m in BASE): continue
        d=pd.DataFrame({m:cache[(fam,fi,m,'',S)] for m in BASE})
        d['y']=y[v].values; d['fam']=fam; d['fold']=fi; d['tod']=FEAT['tod'][v].values
        rows.append(d)
A=pd.concat(rows,ignore_index=True)

def run(cond,loo=False):
    per=[]
    for fam in FAMS:
        D=A[A.fam==fam]
        for k in sorted(D.fold.unique()):
            prev=D[D.fold!=k] if loo else D[D.fold<k]; cur=D[D.fold==k]
            if len(prev)<200: continue
            wg=wfit(prev)
            if not cond: p=cur[BASE].values@wg
            else:
                e=np.quantile(prev.tod,np.linspace(0,1,NB+1)); e[0]=-1e18; e[-1]=1e18
                bp=np.digitize(prev.tod,e[1:-1]); bc=np.digitize(cur.tod,e[1:-1])
                p=np.empty(len(cur))
                for b in range(NB):
                    wb=wfit(prev[bp==b]); wb=wg if wb is None else (1-BG)*wb+BG*wg
                    m=bc==b
                    if m.any(): p[m]=cur[BASE].values[m]@wb
            per.append(rmse(np.clip(p,5,100),cur.y))
    return np.array(per)

for loo in (False,True):
    a,b=run(False,loo),run(True,loo)
    d=b-a
    rng=np.random.default_rng(0)
    bs=[rng.choice(d,len(d),replace=True).mean() for _ in range(20000)]
    print('%s: global %.4f -> conditional %.4f   delta %+.4f  95%% CI [%+.4f, %+.4f]  won %d/%d'
          %('expanding' if not loo else 'LOO   ',a.mean(),b.mean(),d.mean(),
            np.percentile(bs,2.5),np.percentile(bs,97.5),(d<0).sum(),len(d)))

# ---- the weights themselves, fitted on all OOF as the pipeline would ----
wg=wfit(A)
e=np.quantile(A.tod,np.linspace(0,1,NB+1)); e[0]=-1e18; e[-1]=1e18
print('\ntime-of-day bin edges: %s h'%np.round(e[1:-1],2))
print('%-22s %s'%('global (shipped)',{m:round(float(x),3) for m,x in zip(BASE,wg)}))
bp=np.digitize(A.tod,e[1:-1])
WB={}
for b in range(NB):
    wb=wfit(A[bp==b]); WB[b]=(1-BG)*wb+BG*wg
    lo=e[b] if b else 0; hi=e[b+1] if b<NB-1 else 24
    print('%-22s %s   n=%d'%('bin %d (%.1f-%.1fh)'%(b,lo,hi),
          {m:round(float(x),3) for m,x in zip(BASE,WB[b])},(bp==b).sum()))

# ---- what it does to the actual test predictions ----
print('\nrefitting the five members on all training rows...')
esT=pd.Series(FP.es(FEAT['T'].values),index=IDX); E=y*esT/100.0
tr_i,te_i=IDX[is_tr],IDX[is_te]
P={m:np.clip(FP.predict(m,FEAT.loc[tr_i],y[tr_i],FEAT.loc[te_i],esT[te_i].values,E[tr_i],
                        FP.SEEDS_FIT),5,100) for m in BASE}
Pt=pd.DataFrame(P,index=te_i)
tod_te=FEAT['tod'][is_te].values
bc=np.digitize(tod_te,e[1:-1])
p_glob=np.clip(Pt[BASE].values@wg,5,100)
p_cond=np.empty(len(Pt))
for b in range(NB):
    m=bc==b; p_cond[m]=Pt[BASE].values[m]@WB[b]
p_cond=np.clip(p_cond,5,100)
sub=pd.read_csv('outputs/submissions/v8_qblock.csv')
v8=sub.air_humidity.values
print('global-weight refit vs shipped v8:  rmse %.4f  max %.4f'%(rmse(p_glob,v8),np.abs(p_glob-v8).max()))
print('conditional        vs shipped v8:  rmse %.4f  max %.4f'%(rmse(p_cond,v8),np.abs(p_cond-v8).max()))
K=220
print('conditional vs v8, public slice %.4f   private slice %.4f'
      %(rmse(p_cond[:K],v8[:K]),rmse(p_cond[K:],v8[K:])))
print('pred std: v8 %.3f  conditional %.3f   mean: v8 %.3f  conditional %.3f'
      %(v8.std(),p_cond.std(),v8.mean(),p_cond.mean()))
print('\ns46 dispersion guard: CV fold pred std range vs test')
sds=[]
for fam in FAMS:
    D=A[A.fam==fam]
    for k in sorted(D.fold.unique()):
        cur=D[D.fold==k]; sds.append((cur[BASE].values@wg).std())
print('  CV %.2f-%.2f   test global %.2f   test conditional %.2f'
      %(min(sds),max(sds),p_glob.std(),p_cond.std()))
np.save('outputs/pred_cond_tod.npy',p_cond)
