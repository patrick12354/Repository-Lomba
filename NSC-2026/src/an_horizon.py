"""Horizon decomposition of the v8 blend: near 30% vs far 70% of each validation window.

If the public/private leaderboard split is temporal, public = first 4.56 days of the
734-row test window and private = the remaining 10.69 days. This scores every CV fold
the same way, from the h7 cache, so it costs nothing to run.
"""
import numpy as np, pandas as pd, pickle, sys
sys.path.insert(0, '.')
import final_pipeline as FP
from scipy.optimize import nnls

CACHE = 'outputs/h7_oof.pkl'
BASE = ['hbt', 'cat', 'ridge', 'enet', 'ridge_e']
SEEDS = (0, 1, 2)
SHRINK = FP.BLEND_SHRINK

cache = pickle.load(open(CACHE, 'rb'))
g = FP.load_grid()
y = g[FP.TARGET]
IDX = g.index
is_tr = (g.is_test == 0).values & y.notna().values


def fam(n, val_days, step_days, min_train_days=30):
    idx = IDX[is_tr]
    d0, end, out = idx.min(), idx.max(), []
    for i in range(n):
        cut = end - pd.Timedelta(days=step_days * i)
        vs = cut - pd.Timedelta(days=val_days)
        if (vs - d0).days < min_train_days:
            break
        out.append((vs, cut))
    return out[::-1]


FAMS = {'P': fam(9, 15, 2), 'Q': fam(6, 15, 3, 36), 'R': fam(5, 21, 3, 28)}


def rmse(a, b):
    return float(np.sqrt(np.mean((np.asarray(a) - np.asarray(b)) ** 2)))


def collect(famname):
    rows = []
    for fi, (vs, ve) in enumerate(FAMS[famname]):
        v = is_tr & (IDX > vs) & (IDX <= ve)
        t = is_tr & (IDX <= vs)
        if t.sum() < 300 or v.sum() < 50:
            continue
        d = pd.DataFrame(dict(fold=fi, dt=IDX[v], y=y[v].values))
        ok = True
        for m in BASE:
            k = (famname, fi, m, '', SEEDS)
            if k not in cache:
                ok = False
                break
            d[m] = cache[k]
        if not ok:
            continue
        d['h'] = (d.dt - d.dt.min()).dt.total_seconds() / 86400.0
        rows.append(d)
    return pd.concat(rows, ignore_index=True)


# --- blend weights exactly as the pipeline does: NNLS on all OOF, shrunk to equal ---
def blend_of(D):
    w, _ = nnls(D[BASE].values, D.y.values)
    w = w / w.sum() if w.sum() > 0 else np.ones(len(BASE)) / len(BASE)
    w = (1 - SHRINK) * w + SHRINK * np.ones(len(BASE)) / len(BASE)
    return w


P = collect('P')
w = blend_of(P)
print('blend weights (family P OOF):', {m: round(float(x), 4) for m, x in zip(BASE, w)})
for D in (P,):
    D['blend'] = np.clip(D[BASE].values @ w, 5, 100)

# test window geometry
TEST_DAYS = 15.27
CUT_D = 0.30 * TEST_DAYS      # 4.58 days -> the public/private boundary if temporal

print('\n=== family P: RMSE by horizon segment within each 15-day window ===')
print('%5s %8s %8s %8s %8s %8s %8s' % ('fold', 'n_near', 'RMSE_all', 'RMSE_nr', 'RMSE_far', 'y_std_nr', 'y_std_far'))
tot = []
for fi, d in P.groupby('fold'):
    nr = d.h <= CUT_D
    fr = ~nr
    tot.append((fi, rmse(d.blend, d.y), rmse(d.blend[nr], d.y[nr]), rmse(d.blend[fr], d.y[fr])))
    print('%5d %8d %8.3f %8.3f %8.3f %8.2f %8.2f' % (
        fi, nr.sum(), tot[-1][1], tot[-1][2], tot[-1][3], d.y[nr].std(), d.y[fr].std()))
T = pd.DataFrame(tot, columns=['fold', 'all', 'near', 'far'])
print('%5s %8s %8.3f %8.3f %8.3f' % ('MEAN', '', T['all'].mean(), T['near'].mean(), T['far'].mean()))
print('pooled: all=%.3f near=%.3f far=%.3f' % (
    rmse(P.blend, P.y), rmse(P.blend[P.h <= CUT_D], P.y[P.h <= CUT_D]),
    rmse(P.blend[P.h > CUT_D], P.y[P.h > CUT_D])))
print('far/near ratio (pooled) = %.3f' % (
    rmse(P.blend[P.h > CUT_D], P.y[P.h > CUT_D]) / rmse(P.blend[P.h <= CUT_D], P.y[P.h <= CUT_D])))

print('\n=== RMSE vs horizon, in 2-day buckets (pooled over folds) ===')
P['bucket'] = (P.h // 2).astype(int) * 2
for b, d in P.groupby('bucket'):
    print('  days %2d-%2d  n=%4d  RMSE=%6.3f  bias=%+6.3f  pred_std=%6.2f  y_std=%6.2f'
          % (b, b + 2, len(d), rmse(d.blend, d.y), (d.blend - d.y).mean(),
             d.blend.std(), d.y.std()))

# --- dispersion by segment ---
print('\n=== dispersion (pred std / y std) by segment, per fold ===')
for fi, d in P.groupby('fold'):
    nr = d.h <= CUT_D
    print('  fold %d  near %.3f   far %.3f' % (
        fi, d.blend[nr].std() / d.y[nr].std(), d.blend[~nr].std() / d.y[~nr].std()))

# --- per-model, by segment: does the blend's member ranking change with horizon? ---
print('\n=== per-model pooled RMSE by segment ===')
print('%-9s %8s %8s %8s' % ('model', 'all', 'near', 'far'))
for m in BASE + ['blend']:
    print('%-9s %8.3f %8.3f %8.3f' % (m, rmse(P[m], P.y),
                                      rmse(P[m][P.h <= CUT_D], P.y[P.h <= CUT_D]),
                                      rmse(P[m][P.h > CUT_D], P.y[P.h > CUT_D])))

# --- what would NNLS weights be if fitted only on far rows? ---
wf = blend_of(P[P.h > CUT_D])
wn = blend_of(P[P.h <= CUT_D])
print('\nweights fitted on NEAR rows only:', {m: round(float(x), 4) for m, x in zip(BASE, wn)})
print('weights fitted on FAR  rows only:', {m: round(float(x), 4) for m, x in zip(BASE, wf)})
bf = np.clip(P[BASE].values @ wf, 5, 100)
print('far-fitted blend, scored on far rows: %.3f  (shipped weights: %.3f)'
      % (rmse(bf[(P.h > CUT_D).values], P.y[P.h > CUT_D]),
         rmse(P.blend[P.h > CUT_D], P.y[P.h > CUT_D])))
