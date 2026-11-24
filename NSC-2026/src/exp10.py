"""E1: vapour-pressure reparameterisation with an EXACT RH-equivalent loss.

RH = 100 * e / es(T).  Given the concurrent (and despiked) T, that map is LINEAR in e,
so weighted L2 on e with w = (100/es(T))^2 is *identically* L2 on RH -- unlike the Td
target (progress sec 4.4), which lost precisely because dRH/dTd is not constant.
The point: e is an air-mass property (smooth, no diurnal cycle), so the tree spends its
capacity on the slow component that sec 4.2 shows carries 55% of the MSE.
"""
import warnings; warnings.filterwarnings('ignore')
import sys, time, json, numpy as np, pandas as pd
sys.path.insert(0,'src')
from common import *
from screen import origins
import lightgbm as lgb
from sklearn.linear_model import Ridge, ElasticNet
from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from scipy.optimize import nnls

g,_,_=load_grid()
is_tr=pd.Series((g.is_test==0).values,index=g.index); y=g[TARGET]
c=clean_exog(g,k=6.0); F=build_features(c); F=F[feature_set(F,'nosoil')]
T=c['air_temperature']; ESt=pd.Series(es(T.values),index=g.index)
E=y*ESt/100.0                       # actual vapour pressure, hPa
tr=is_tr&y.notna(); IDX=F.index
folds=origins(IDX[tr],n=9,val_days=15,step_days=2)
print(f'feats {F.shape[1]}  folds {len(folds)}',flush=True)
print(f'RH  std {y[tr].std():.2f}   e std {E[tr].std():.3f}  e/mean {E[tr].std()/E[tr].mean():.3f}',flush=True)

def HBT(s=0,obj='huber',a=4.0): return lgb.LGBMRegressor(objective=obj,alpha=a,n_estimators=900,
    learning_rate=0.03,num_leaves=31,min_child_samples=25,subsample=0.8,subsample_freq=1,
    colsample_bytree=1.0,reg_lambda=3.,random_state=s,verbose=-1)
def RID(): return make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),Ridge(alpha=20.))
def ENE(): return make_pipeline(SimpleImputer(strategy='median'),StandardScaler(),ElasticNet(alpha=0.05,l1_ratio=0.5,max_iter=8000))

def run(tag, space, weighted, model='lgbm', obj='huber', alpha=4.0):
    """space: 'rh' or 'e'.  weighted: use w=(100/es(T))^2 when fitting in e-space."""
    rows=[]
    for fi,(vs,ve) in enumerate(folds):
        v=tr&(IDX>vs)&(IDX<=ve); t=tr&(IDX<=vs)
        if space=='rh': ytr=y[t]
        else:
            ytr=E[t]
            if not weighted: pass
        sw=None
        if space=='e' and weighted: sw=(100.0/ESt[t].values)**2
        if model=='lgbm':  m=HBT(0,obj,alpha)
        elif model=='ridge': m=RID()
        else: m=ENE()
        if sw is not None and model=='lgbm': m.fit(F[t],ytr,sample_weight=sw)
        elif sw is not None: m.fit(F[t],ytr,**{m.steps[-1][0]+'__sample_weight':sw})
        else: m.fit(F[t],ytr)
        p=np.asarray(m.predict(F[v])).ravel()
        if space=='e': p=100.0*p/ESt[v].values
        rows.append(pd.DataFrame(dict(fold=fi,dt=IDX[v],y=y[v].values,p=np.clip(p,5,100))))
    L=pd.concat(rows,ignore_index=True)
    pf=L.groupby('fold').apply(lambda d: rmse(d.y,d.p))
    print(f'{tag:34s} mean {pf.mean():6.3f}  worst {pf.max():6.3f}  pooled {rmse(L.y,L.p):6.3f}  {[round(x,2) for x in pf.values]}',flush=True)
    return L, float(pf.mean())

t0=time.time()
res={}
res['A_rh_huber']       = run('A rh-space huber  (v5 model)','rh',False)
res['B_e_plain']        = run('B e-space  plain L2','e',False,obj='regression')
res['C_e_weighted']     = run('C e-space  weighted L2 (=RH L2)','e',True,obj='regression')
res['D_e_w_huber']      = run('D e-space  weighted huber a=0.5','e',True,obj='huber',alpha=0.5)
res['E_e_w_huber1']     = run('E e-space  weighted huber a=1.0','e',True,obj='huber',alpha=1.0)
res['F_rh_l2']          = run('F rh-space plain L2','rh',False,obj='regression')
res['G_ridge_rh']       = run('G ridge rh-space','rh',False,model='ridge')
res['H_ridge_e']        = run('H ridge e-space weighted','e',True,model='ridge')
print(f'\n{time.time()-t0:.0f}s',flush=True)
import pickle; pickle.dump({k:v[0] for k,v in res.items()},open('outputs/exp10_preds.pkl','wb'))
