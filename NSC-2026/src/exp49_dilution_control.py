"""Capacity-floor control for a seventh blend member (section 61's rule, applied to
members instead of conditioners).

`robust_hbt` and `l2` both land on the NNLS floor, and adding a seventh member also moves
the uniform vector the shrinkage pulls toward from 1/6 to 1/7. So part of any gain is
dilution, not information. Measure that part directly: put a member in the seventh slot
that carries no new information at all -- `hbt` refit on a disjoint seed set, residual
correlation with `hbt` near 1 -- and see what the blend does with it.
"""
import pickle, sys, time, json
import numpy as np, pandas as pd
sys.path[:0] = ['.', 'src']
import final_pipeline as fp
from exp43_robust_baseline import score_stack
from robust_eval import paired_summary

CACHE = 'outputs/dilution_control_oof.pkl'
ARMS = {'dup_hbt': ('hbt', (7, 8, 9)),      # same model, different seeds -> no new info
        'noise_hbt': ('hbt', (0, 1, 2))}     # identical, then perturbed with pure noise

g = fp.load_grid(); F = fp.make_features(g)
y = g[fp.TARGET]; idx = g.index
is_tr = (g.is_test == 0).values & y.notna().values

A = pickle.load(open('outputs/robust_core_scored.pkl', 'rb'))
frame = A['frame'].copy()
cache = pickle.load(open(CACHE, 'rb')) if __import__('os').path.exists(CACHE) else {}

t0 = time.time()
for family, fold in frame[['family', 'fold']].drop_duplicates().itertuples(index=False, name=None):
    key = (family, int(fold))
    vi = pd.DatetimeIndex(frame.loc[(frame.family == family) & (frame.fold == fold), 'datetime'])
    if key in cache and cache[key].index.equals(vi):
        continue
    cut = vi.min() - pd.Timedelta(minutes=30)
    trm = is_tr & (idx <= cut); vam = idx.isin(vi)
    p = fp.predict('hbt', F.loc[trm], y[trm].values, F.loc[vam],
                   fp.es(F.loc[vam, 'T'].values),
                   y[trm].values * fp.es(F.loc[trm, 'T'].values) / 100.0, (7, 8, 9))
    cache[key] = pd.Series(np.clip(p, 5, 100), index=idx[vam])
    pickle.dump(cache, open(CACHE, 'wb'))
    print("fit %s%s (%.0fs)" % (family, fold, time.time() - t0), flush=True)

frame['dup_hbt'] = np.nan
for (family, fold), v in cache.items():
    m = (frame.family == family) & (frame.fold == fold)
    frame.loc[m, 'dup_hbt'] = v.reindex(pd.DatetimeIndex(frame.loc[m, 'datetime'])).values
assert frame.dup_hbt.notna().all()

rs = np.random.default_rng(4242)
frame['noise_hbt'] = frame['hbt'] + rs.normal(0, frame['hbt'].std() * 0.02, len(frame))

M = list(fp.MODELS_L2)
res = {}
sb, fb = score_stack(frame, M)
for nm in ('robust_hbt', 'dup_hbt', 'noise_hbt'):
    sc, fc = score_stack(frame, M + [nm])
    ps = paired_summary(sb, sc)
    fam = ps.groupby('family').delta.agg(['mean', lambda s: int((s < 0).sum()), 'size'])
    fam.columns = ['delta', 'won', 'n']
    rho = np.corrcoef(frame[nm] - frame.y, frame['hbt'] - frame.y)[0, 1]
    res[nm] = dict(delta=float(ps.delta.mean()), won=int((ps.delta < 0).sum()),
                   n=len(ps), resid_corr_with_hbt=float(rho),
                   families={k: dict(delta=float(r.delta), won=int(r.won), n=int(r.n))
                             for k, r in fam.iterrows()})
    print("\n%-11s delta %+.5f  folds %d/%d  resid corr with hbt %.4f"
          % (nm, ps.delta.mean(), (ps.delta < 0).sum(), len(ps), rho))
    print(fam.round(4).to_string())

res['base_mean'] = float(fb.rmse.mean())
json.dump(res, open('outputs/dilution_control.json', 'w'), indent=2)
