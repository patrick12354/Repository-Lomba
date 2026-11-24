"""A target-free difficulty estimator that should extrapolate: how much the five blend
members disagree with each other. Where they disagree, the blend is wrong. Calibrate the
relationship on CV chunks, then read it off on the public and private test slices.
"""
import numpy as np, pandas as pd, pickle, sys
sys.path.insert(0, '.')
import final_pipeline as FP
from scipy.optimize import nnls

BASE = ['hbt', 'cat', 'ridge', 'enet', 'ridge_e']; S = (0, 1, 2)
cache = pickle.load(open('outputs/h7_oof.pkl', 'rb'))
g = FP.load_grid(); y = g[FP.TARGET]; IDX = g.index
is_tr = (g.is_test == 0).values & y.notna().values
idx = IDX[is_tr]; end = idx.max()
def famdef(n, vd, sd, mtd=30):
    out = []
    for i in range(n):
        cut = end - pd.Timedelta(days=sd * i); vs = cut - pd.Timedelta(days=vd)
        if (vs - idx.min()).days < mtd: break
        out.append((vs, cut))
    return out[::-1]
FAMS = {'P': famdef(9, 15, 2), 'Q': famdef(6, 15, 3, 36), 'R': famdef(5, 21, 3, 28)}

rows = []
for fam, folds in FAMS.items():
    for fi, (vs, ve) in enumerate(folds):
        v = is_tr & (IDX > vs) & (IDX <= ve)
        if v.sum() < 50 or (fam, fi, BASE[0], '', S) not in cache: continue
        d = pd.DataFrame({m: cache[(fam, fi, m, '', S)] for m in BASE})
        d['y'] = y[v].values; d['dt'] = IDX[v]; d['fam'] = fam; d['fold'] = fi
        rows.append(d)
A = pd.concat(rows, ignore_index=True)
w, _ = nnls(A[BASE].values, A.y.values); w = w / w.sum(); w = 0.75 * w + 0.25 * np.ones(5) / 5
A['pred'] = np.clip(A[BASE].values @ w, 5, 100)
# disagreement: weighted sd of the members around the blend, per row
Wv = w / w.sum()
A['spread'] = np.sqrt((Wv * (A[BASE].values - A.pred.values[:, None]) ** 2).sum(1))
# and the two-tree disagreement, which is the part that actually carries the blend
A['spread_ht'] = (A.hbt - A.cat).abs()

print('per-row: corr(|error|, spread) = %+.3f    corr(|error|, |hbt-cat|) = %+.3f'
      % (np.corrcoef((A.pred - A.y).abs(), A.spread)[0, 1],
         np.corrcoef((A.pred - A.y).abs(), A.spread_ht)[0, 1]))

A['chunk'] = A.dt.dt.floor('2D')
recs = []
for (fam, fo, ch), d in A.groupby(['fam', 'fold', 'chunk']):
    if len(d) < 60: continue
    recs.append(dict(fam=fam, chunk=ch, rmse=float(np.sqrt(((d.pred - d.y) ** 2).mean())),
                     spread=d.spread.mean(), spread_ht=d.spread_ht.mean()))
C = pd.DataFrame(recs)
print('chunk level (n=%d): corr(RMSE, spread) = %+.3f   corr(RMSE, |hbt-cat|) = %+.3f'
      % (len(C), C.rmse.corr(C.spread), C.rmse.corr(C.spread_ht)))

import numpy.linalg as la
X = np.c_[np.ones(len(C)), C.spread]
b, *_ = la.lstsq(X, C.rmse.values, rcond=None)
r2 = 1 - ((C.rmse - X @ b) ** 2).sum() / ((C.rmse - C.rmse.mean()) ** 2).sum()
print('RMSE = %.3f + %.3f * spread     R2 = %.3f' % (b[0], b[1], r2))
print('CV chunk spread range: %.3f - %.3f' % (C.spread.min(), C.spread.max()))

# ---------- now compute the same spread on the TEST rows, from the real fit ----------
print('\nrefitting the five members on all train rows to get test-row member spread...')
F = FP.make_features(g)
esT = pd.Series(FP.es(F['T'].values), index=IDX)
E = y * esT / 100.0
tr_i = IDX[is_tr]; te_i = IDX[(g.is_test == 1).values]
P = {}
for m in BASE:
    P[m] = np.clip(FP.predict(m, F.loc[tr_i], y[tr_i], F.loc[te_i], esT[te_i].values,
                              E[tr_i], FP.SEEDS_FIT), 5, 100)
    print('  %s done' % m)
Pt = pd.DataFrame(P, index=te_i)
blend = np.clip(Pt[BASE].values @ w, 5, 100)
sp = np.sqrt((Wv * (Pt[BASE].values - blend[:, None]) ** 2).sum(1))
sub = pd.read_csv('outputs/submissions/v8_qblock.csv').air_humidity.values
print('  refit blend vs shipped submission: max|diff| = %.4f  rmse %.4f'
      % (np.abs(blend - sub).max(), np.sqrt(((blend - sub) ** 2).mean())))

K = 220
print('\n=== member disagreement on the test slices ===')
print('%-24s %8s %10s %14s' % ('slice', 'spread', 'pred_std', 'implied RMSE'))
for nm, sl in [('public 30% (near)', slice(0, K)), ('private 70% (far)', slice(K, None)),
               ('full test', slice(None))]:
    s = sp[sl].mean()
    print('%-24s %8.3f %10.2f %14.3f' % (nm, s, blend[sl].std(), b[0] + b[1] * s))
print('\nCV pooled RMSE %.3f at mean spread %.3f' % (np.sqrt(((A.pred - A.y) ** 2).mean()),
                                                     A.spread.mean()))
print('ratio private/public implied by spread: %.3f'
      % ((b[0] + b[1] * sp[K:].mean()) / (b[0] + b[1] * sp[:K].mean())))
np.save('outputs/test_member_spread.npy', sp)
Pt.to_csv('outputs/test_member_preds.csv')
