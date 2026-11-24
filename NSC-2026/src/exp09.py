import warnings; warnings.filterwarnings('ignore')
import sys, json, numpy as np, pandas as pd
sys.path.insert(0,'src')
from common import *
from screen import origins
from ab import run, summarize, HBT

g,_,_=load_grid(); is_tr=pd.Series((g.is_test==0).values,index=g.index); y=g[TARGET]
folds=origins(g.index[is_tr & y.notna()],n=9,val_days=15,step_days=2)

def prep(c):
    F=build_features(c); return F[feature_set(F,'nosoil')]

VAR={
 'S0_ref_hampel_k6' : clean_exog(g,k=6.0),
 'S1_curv_k3'       : clean_exog2(g,k=3.0),
 'S2_curv_k4'       : clean_exog2(g,k=4.0),
 'S3_curv_k5'       : clean_exog2(g,k=5.0),
 'S4_curv_k6'       : clean_exog2(g,k=6.0),
 'S5_curv_k8'       : clean_exog2(g,k=8.0),
 'S6_curv_k4_p4'    : clean_exog2(g,k=4.0,passes=4),
 'S7_curv_k4_pchip' : clean_exog2(g,k=4.0,method='pchip'),
 'S8_hampelMAD_k6'  : clean_exog2(g,detector='hampel_mad',k=6.0),
}
for n,c in VAR.items():
    r=c.attrs.get('despike_report',{})
    print(f'{n:20s} despiked total {sum(r.values()):5d}  air_temp {r.get("air_temperature",0):3d} co2 {r.get("co2",0):3d} press {r.get("pressure",0):3d}',flush=True)
print(flush=True)

REF=None; RES=[]
for n,c in VAR.items():
    D=run(prep(c),y,is_tr,folds)
    if REF is None:
        RES.append(summarize(n,D)); REF=D
    else:
        RES.append(summarize(n,D,ref=REF))
json.dump(RES,open('outputs/exp09_res.json','w'),indent=1,default=float)
print('\n=== RANKING ===',flush=True)
for r in sorted(RES,key=lambda r:r['mean']): print(f"  {r['name']:22s} mean {r['mean']:6.3f} worst {r['worst']:6.3f}",flush=True)
