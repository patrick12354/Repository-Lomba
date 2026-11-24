import warnings; warnings.filterwarnings('ignore')
import sys, numpy as np, pandas as pd
sys.path.insert(0,'src')
from common import *
from screen import *

g,_,_ = load_grid()
is_tr = pd.Series((g.is_test==0).values, index=g.index); y = g[TARGET]

c_clean = clean_exog(g)
c_raw = g.copy()
for col in FAST+SOIL+DAILY:
    c_raw[col] = c_raw[col].interpolate('time', limit_direction='both')
for col in CUMUL:
    s = c_raw[col].interpolate('time', limit_direction='both')
    c_raw[col]=s; c_raw[col+'_rate']=s.diff().clip(lower=0).rolling(48,min_periods=1).sum()

Fc = build_features(c_clean); Fr = build_features(c_raw)
Tc = c_clean['air_temperature']; Tr = c_raw['air_temperature']
folds = origins(g.index[is_tr & y.notna()], n=9, val_days=15, step_days=2)
print('folds:'); [print('  ',str(a)[:10],'->',str(b)[:10]) for a,b in folds]
print()

S={}
screen('B0_raw',       Fr, y, Tr, is_tr, folds=folds, store=S)
screen('B1_clean',     Fc, y, Tc, is_tr, folds=folds, store=S)
screen('B2_clean_sm3', Fc, y, Tc, is_tr, folds=folds, smooth=3, store=S)
screen('B3_clean_sm5', Fc, y, Tc, is_tr, folds=folds, smooth=5, store=S)
screen('B4_clean_sm7', Fc, y, Tc, is_tr, folds=folds, smooth=7, store=S)
screen('B5_clean_td',  Fc, y, Tc, is_tr, folds=folds, target='td', store=S)
import pickle; pickle.dump({k:(v[0]) for k,v in S.items()}, open('outputs/screen_B.pkl','wb'))
