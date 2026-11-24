import warnings; warnings.filterwarnings('ignore')
import sys, os, numpy as np, pandas as pd
sys.path.insert(0,'src')
from common import *
from runner import *

g, dtr, dte = load_grid()
c = clean_exog(g)
F = build_features(c)
is_tr = (g.is_test == 0).values
is_te = (g.is_test == 1).values
is_tr = pd.Series(is_tr, index=g.index); is_te = pd.Series(is_te, index=g.index)
y = g[TARGET]
T = c['air_temperature']

folds = make_folds(g.index[is_tr & y.notna()], n_folds=5, val_days=15, step_days=5)
print('FOLDS:'); [print(f'  F{i}: {str(a)[:16]} -> {str(b)[:16]}') for i,(a,b) in enumerate(folds)]

MODELS = ('lgbm','lgbm_huber','lgbm_shallow','xgb','cat','et','ridge','enet')
res=[]
for nm, tgt in [('R1_rh_clean','rh'), ('R2_td_clean','td')]:
    rec,O,bl,fid,w = run_cv(nm, F, y, T, is_tr, models=MODELS, target=tgt, folds=folds,
                            notes='cleaned exog, 144 feats, no day-trend features')
    res.append(rec); print(fmt(rec))
    print('   per-model:', {k: round(v,3) for k,v in rec['per_model'].items()})

# oracle ceiling: how good could we be if Td were known at various smoothings?
print('\n=== ORACLE ceilings on the same fold rows ===')
