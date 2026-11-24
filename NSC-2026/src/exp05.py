import warnings; warnings.filterwarnings('ignore')
import sys, json, numpy as np, pandas as pd
sys.path.insert(0,'src')
from common import *
from screen import *

g,_,_=load_grid(); is_tr=pd.Series((g.is_test==0).values,index=g.index)
is_te=(g.is_test==1).values; y=g[TARGET]
c=clean_exog(g); F=build_features(c); T=c['air_temperature']
folds=origins(g.index[is_tr & y.notna()], n=9, val_days=15, step_days=2)
M4=('lgbm','lgbm_hub','ridge','enet')

# support coverage: fraction of test values inside the train 1-99 pct range
cov={}
for col in F.columns:
    a=F[col].values
    lo,hi=np.nanquantile(a[is_tr.values],[.01,.99])
    cov[col]=float(np.nanmean((a[is_te]>=lo)&(a[is_te]<=hi)))
cov=pd.Series(cov).sort_values()
print('lowest-coverage features:'); print(cov.head(12).round(3).to_string(), flush=True)

SD6=[cl for cl in F.columns if cl.endswith('_sd6h')]
WR =[cl for cl in F.columns if cl.endswith('_rate')]
SOIL_ALL=[cl for cl in F.columns if cl.startswith('soil_')]
SOIL_EH =[cl for cl in F.columns if cl.startswith('soil_ec') or cl.startswith('soil_humidity')]
LOWCOV=list(cov[cov<0.55].index)
print('\nlow-coverage(<0.55) drop list:',LOWCOV, flush=True)

sets={
 'C0_full'          : list(F.columns),
 'C1_drop_lowcov'   : [cl for cl in F.columns if cl not in LOWCOV],
 'C2_drop_sd6h_rate': [cl for cl in F.columns if cl not in set(SD6)|set(WR)],
 'C3_drop_soil_ec_h': [cl for cl in F.columns if cl not in set(SOIL_EH)|set(WR)],
 'C4_drop_all_soil' : [cl for cl in F.columns if cl not in set(SOIL_ALL)|set(WR)],
 'C5_core'          : [cl for cl in F.columns if cl.startswith(('T','es','log_es','sin','cos','tod',
                        'air_temperature','co2','pressure','daily_','standard_','ontario_'))],
}
RES=[]
for nm,cols in sets.items():
    L,Mn=raw_oof(F[cols],y,T,is_tr,models=M4,folds=folds)
    r=evaluate(f'{nm}({len(cols)})',L,Mn); r['cols']=len(cols); RES.append(r)
json.dump(RES,open('outputs/exp05_res.json','w'),indent=1,default=float)
print('\n=== RANKING ===',flush=True)
for r in sorted(RES,key=lambda r:r['mean']): print(f"  {r['name']:26s} mean {r['mean']:6.3f} worst {r['worst']:6.3f}",flush=True)
