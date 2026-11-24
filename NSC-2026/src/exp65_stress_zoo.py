"""Fit the two surviving candidates on the five OOD stress splits so they can be gated."""
import os, pickle, sys, time
import numpy as np, pandas as pd
sys.path[:0] = ['.', 'src']
import final_pipeline as fp
import lightgbm as lgb
from robust_eval import (block_descriptors, feature_groups, make_stress_splits,
                         score_blocks_against_reference, support_fraction)

g = fp.load_grid(); F = fp.make_features(g); y = g[fp.TARGET]; idx = g.index
is_tr = (g.is_test == 0).values & y.notna().values
is_te = (g.is_test == 1).values
cov = support_fraction(F.loc[is_tr], F.loc[is_te])
G = feature_groups(F.columns, cov)

trF = F.loc[is_tr]
desc = block_descriptors(trF, block_days=3)
priv = F.loc[is_te].iloc[220:]
ref = pd.Series({'pressure': priv.pressure.median(), 'temp_range': priv.T_rng48.median(),
                 'missing': priv.isna().mean().mean(),
                 'season': (priv.index.min()-trF.index.min()).total_seconds()/86400.0})
desc['stress_score'] = score_blocks_against_reference(desc, ref)
splits = make_stress_splits(trF.index, desc, n=5, embargo_hours=96, min_train_rows=1000)

cache = pickle.load(open('outputs/stress_members.pkl','rb'))
t0 = time.time()
for sid, (ti, vi) in enumerate(splits):
    P = cache[sid]
    assert P.index.equals(pd.DatetimeIndex(vi)), sid
    trm = idx.isin(ti) & is_tr; vam = idx.isin(vi) & is_tr
    etr = y[trm].values * fp.es(F.loc[trm,'T'].values) / 100.0
    if 'bag_nopress' not in P:
        P['bag_nopress'] = np.clip(fp.predict('hbt', F.loc[trm, G['no_pressure']], y[trm].values,
                          F.loc[vam, G['no_pressure']], fp.es(F.loc[vam,'T'].values), etr,
                          fp.SEEDS_OOF), 5, 100)
    if 'lin' not in P:
        kw = dict(fp.LGB_KW); kw.update(linear_tree=True, num_leaves=7, reg_lambda=30.0,
                                        linear_lambda=10.0, n_estimators=600, learning_rate=0.04)
        P['lin'] = np.clip(np.mean([lgb.LGBMRegressor(random_state=s, **kw)
                   .fit(F.loc[trm], y[trm].values).predict(F.loc[vam]) for s in fp.SEEDS_OOF], 0), 5, 100)
    # keep column order stable: members first, then tod/y
    cols = [c for c in P.columns if c not in ('tod','y')] + ['tod','y']
    cache[sid] = P[cols]
    pickle.dump(cache, open('outputs/stress_members.pkl','wb'))
    print("split %d done (%.0fs)" % (sid, time.time()-t0), flush=True)
print("columns now:", list(cache[0].columns))
