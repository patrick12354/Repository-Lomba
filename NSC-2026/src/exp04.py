import warnings; warnings.filterwarnings('ignore')
import sys, json, numpy as np, pandas as pd, pickle
sys.path.insert(0,'src')
from common import *
from screen import *

g,_,_ = load_grid()
is_tr = pd.Series((g.is_test==0).values, index=g.index); y = g[TARGET]

def interp_only(g):
    c=g.copy()
    for col in FAST+SOIL+DAILY: c[col]=c[col].interpolate('time',limit_direction='both')
    for col in CUMUL:
        s=c[col].interpolate('time',limit_direction='both'); c[col]=s
        c[col+'_rate']=s.diff().clip(lower=0).rolling(48,min_periods=1).sum()
    return c

variants = {
  'raw'      : interp_only(g),
  'clean_k6' : clean_exog(g, k=6.0),
  'clean_k4' : clean_exog(g, k=4.0),
  'clean_k9' : clean_exog(g, k=9.0),
}
folds = origins(g.index[is_tr & y.notna()], n=9, val_days=15, step_days=2)
print('folds:', [(str(a)[:10],str(b)[:10]) for a,b in folds], flush=True)

RES=[]; RAW={}
for vn, c in variants.items():
    F = build_features(c); T = c['air_temperature']
    L, M = raw_oof(F, y, T, is_tr, target='rh', folds=folds)
    RAW[vn]=(L,M)
    for sm in (0,3,5,7,9):
        RES.append(evaluate(f'{vn}|sm{sm}', L, M, smooth=sm))
    print(flush=True)

# dewpoint target on the best-cleaned variant
c = variants['clean_k6']; F=build_features(c); T=c['air_temperature']
Ltd, M = raw_oof(F, y, T, is_tr, target='td', folds=folds)
RAW['clean_k6_td']=(Ltd,M)
for sm in (0,5):
    RES.append(evaluate(f'clean_k6_td|sm{sm}', Ltd, M, smooth=sm))

# cross-space blend: RH-space models + Td-space models together
Lrh,_ = RAW['clean_k6']
J = Lrh.merge(Ltd.rename(columns={m:m+'_td' for m in M}), on=['fold','dt','y'])
RES.append(evaluate('clean_k6_rh+td', J, M+[m+'_td' for m in M], smooth=0))
RES.append(evaluate('clean_k6_rh+td|sm5', J, M+[m+'_td' for m in M], smooth=5))

pickle.dump(RAW, open('outputs/raw_oof_exp04.pkl','wb'))
json.dump(RES, open('outputs/exp04_res.json','w'), indent=1, default=float)
print('\n=== RANKING ===', flush=True)
for r in sorted(RES, key=lambda r:r['mean']):
    print(f"  {r['name']:26s} mean {r['mean']:6.3f} med {r['med']:6.3f} worst {r['worst']:6.3f}", flush=True)
