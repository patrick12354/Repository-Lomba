import warnings; warnings.filterwarnings('ignore')
import sys, numpy as np, pandas as pd
sys.path.insert(0,'src')
from common import *
from runner import *

g, dtr, dte = load_grid()
is_tr = pd.Series((g.is_test==0).values, index=g.index)
is_te = pd.Series((g.is_test==1).values, index=g.index)
y = g[TARGET]

# --- cleaned vs raw exogenous, same feature recipe ---
c_clean = clean_exog(g)
c_raw = g.copy()
for col in FAST+SOIL+DAILY:
    c_raw[col] = c_raw[col].interpolate('time', limit_direction='both')   # fill only, no despike
for col in CUMUL:
    s = c_raw[col].interpolate('time', limit_direction='both')
    c_raw[col] = s
    c_raw[col+'_rate'] = s.diff().clip(lower=0).rolling(48,min_periods=1).sum()

F_clean = build_features(c_clean)
F_raw   = build_features(c_raw)
T_clean = c_clean['air_temperature']
T_raw   = c_raw['air_temperature']

folds = make_folds(g.index[is_tr & y.notna()], n_folds=5, val_days=15, step_days=5)
M = ('lgbm','lgbm_huber','cat','et','ridge','enet')

runs = [
    ('A1_raw_rh',    F_raw,   T_raw,   'rh', 'no despike, interp-only'),
    ('A2_clean_rh',  F_clean, T_clean, 'rh', 'despiked'),
    ('A3_raw_td',    F_raw,   T_raw,   'td', 'no despike, dewpoint target'),
    ('A4_clean_td',  F_clean, T_clean, 'td', 'despiked, dewpoint target'),
]
out=[]
for nm,F,T,tgt,note in runs:
    rec,O,bl,fid,w = run_cv(nm, F, y, T, is_tr, models=M, target=tgt, folds=folds, notes=note)
    out.append(rec); print(fmt(rec), flush=True)
    print('    per-model:', {k:round(v,3) for k,v in rec['per_model'].items()}, flush=True)

print('\n=== ORACLE ceiling on the union of validation rows ===', flush=True)
_,_,_,fid,_ = run_cv('tmp_oracle', F_clean, y, T_clean, is_tr, models=('ridge',), target='rh',
                     folds=folds, save_oof=False, log=False)[:5]
Td = pd.Series(rh_to_td(y.values, T_clean.values), index=g.index)
val = fid.notna() & y.notna()
for w_ in [1,3,6,13,25,49]:
    Tds = Td.rolling(w_, center=True, min_periods=1).mean()
    rec_ = td_to_rh(Tds, T_clean)
    print(f'   Td smoothed {w_:3d} steps ({w_/2:5.1f}h) -> RMSE {rmse(y[val], rec_[val]):.3f}', flush=True)
