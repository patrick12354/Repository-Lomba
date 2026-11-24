"""Every leaderboard number this project has is measured on the SAME 220 public rows.
If those rows are an easy stretch, the CV->LB ratio of 0.652 is a property of that stretch
and not of the test window. This asks what predicts a window's difficulty, using only
things observable WITHOUT the target, then applies it to the two test slices.
"""
import numpy as np, pandas as pd, pickle, sys
sys.path.insert(0, '.')
import final_pipeline as FP
from scipy.optimize import nnls

BASE = ['hbt', 'cat', 'ridge', 'enet', 'ridge_e']; S = (0, 1, 2)
cache = pickle.load(open('outputs/h7_oof.pkl', 'rb'))
g = FP.load_grid(); y = g[FP.TARGET]; IDX = g.index
is_tr = (g.is_test == 0).values & y.notna().values
is_te = (g.is_test == 1).values
idx = IDX[is_tr]; end = idx.max()


def famdef(n, vd, sd, mtd=30):
    out = []
    for i in range(n):
        cut = end - pd.Timedelta(days=sd * i); vs = cut - pd.Timedelta(days=vd)
        if (vs - idx.min()).days < mtd: break
        out.append((vs, cut))
    return out[::-1]


FAMS = {'P': famdef(9, 15, 2), 'Q': famdef(6, 15, 3, 36), 'R': famdef(5, 21, 3, 28)}
T = g.air_temperature

rows = []
for fam, folds in FAMS.items():
    for fi, (vs, ve) in enumerate(folds):
        v = is_tr & (IDX > vs) & (IDX <= ve)
        if v.sum() < 50: continue
        k = (fam, fi, BASE[0], '', S)
        if k not in cache: continue
        d = pd.DataFrame({m: cache[(fam, fi, m, '', S)] for m in BASE})
        d['y'] = y[v].values; d['dt'] = IDX[v]; d['fam'] = fam; d['fold'] = fi
        rows.append(d)
A = pd.concat(rows, ignore_index=True)
w, _ = nnls(A[BASE].values, A.y.values); w = w / w.sum(); w = 0.75 * w + 0.25 * np.ones(5) / 5
A['pred'] = np.clip(A[BASE].values @ w, 5, 100)

# ---- chop into 2-day chunks and describe each chunk without using y ----
A['chunk'] = A.dt.dt.floor('2D')
recs = []
for (fam, fo, ch), d in A.groupby(['fam', 'fold', 'chunk']):
    if len(d) < 60: continue
    Td = T.reindex(d.dt)
    amp = Td.groupby(Td.index.floor('D')).agg(lambda s: s.max() - s.min()).mean()
    recs.append(dict(fam=fam, fold=fo, chunk=ch, n=len(d),
                     rmse=float(np.sqrt(((d.pred - d.y) ** 2).mean())),
                     pred_std=d.pred.std(), y_std=d.y.std(),
                     T_std=Td.std(), T_amp=amp, T_mean=Td.mean(),
                     pred_mean=d.pred.mean()))
C = pd.DataFrame(recs).drop_duplicates(subset=['chunk', 'fam', 'fold'])
print('%d two-day chunks across 3 fold families' % len(C))
print('\ncorrelation of chunk RMSE with target-free descriptors:')
for c in ['pred_std', 'T_std', 'T_amp', 'T_mean', 'pred_mean']:
    print('  %-10s r = %+.3f' % (c, C.rmse.corr(C[c])))
print('  (y_std, needs the target)  r = %+.3f' % C.rmse.corr(C.y_std))

# ---- simple regression on the two best target-free descriptors ----
import numpy.linalg as la
X = np.c_[np.ones(len(C)), C.pred_std, C.T_amp]
beta, *_ = la.lstsq(X, C.rmse.values, rcond=None)
pred = X @ beta
r2 = 1 - ((C.rmse - pred) ** 2).sum() / ((C.rmse - C.rmse.mean()) ** 2).sum()
print('\nRMSE ~ 1 + pred_std + T_amp    R2 = %.3f   beta = %s' % (r2, np.round(beta, 4)))

# ---- apply to the two test slices ----
sub = pd.read_csv('outputs/submissions/v8_qblock.csv')
sub['dt'] = pd.to_datetime(sub.datetime)
K = 220
Tt = T.reindex(sub.dt)
out = []
for name, sl in [('test NEAR (public 30%)', slice(0, K)), ('test FAR (private 70%)', slice(K, None)),
                 ('test FULL', slice(None))]:
    p = sub.air_humidity.values[sl]; tt = Tt.iloc[sl]
    amp = tt.groupby(tt.index.floor('D')).agg(lambda s: s.max() - s.min()).mean()
    est = beta[0] + beta[1] * p.std() + beta[2] * amp
    out.append((name, len(p), p.std(), amp, est))
    print('%-24s n=%3d pred_std=%5.2f T_amp=%5.2f  -> CV-scale RMSE est %5.2f  (x0.652 = %.2f)'
          % (name, len(p), p.std(), amp, est, 0.652 * est))
print('\nfor reference, CV chunk descriptors:  pred_std %.2f-%.2f   T_amp %.2f-%.2f'
      % (C.pred_std.min(), C.pred_std.max(), C.T_amp.min(), C.T_amp.max()))
print('the observed public LB is 3.04904; the ratio implied by the NEAR estimate is %.3f'
      % (3.04904 / out[0][4]))

# ---- how noisy is a 220-row RMSE anyway? moving-block bootstrap on fold residuals ----
print('\n=== how much does a slice RMSE move by luck alone? ===')
rng = np.random.default_rng(0)
P = A[A.fam == 'P']
res = (P.pred - P.y).values
for n, lab in [(220, 'public 220 rows'), (514, 'private 514 rows'), (734, 'full 734')]:
    outs = []
    for _ in range(4000):
        # moving blocks of 48 (one day) to respect the autocorrelation of the residuals
        nb = int(np.ceil(n / 48))
        st = rng.integers(0, len(res) - 48, nb)
        r = np.concatenate([res[s:s + 48] for s in st])[:n]
        outs.append(np.sqrt((r ** 2).mean()))
    q = np.percentile(outs, [5, 25, 50, 75, 95])
    print('  %-18s median %.3f   90%% band [%.3f, %.3f]  (relative spread +-%.1f%%)'
          % (lab, q[2], q[0], q[4], 100 * (q[4] - q[0]) / 2 / q[2]))

# ------------------------------------------------------------------ appendix
print('\n\n=== chunk table, family P only, in calendar order ===')
Q = C[C.fam == 'P'].sort_values('chunk')
print(Q[['fold', 'chunk', 'n', 'rmse', 'T_mean', 'T_amp', 'pred_std', 'y_std']].round(2).to_string(index=False))
print('\nfamily-P-only correlations: rmse~T_mean %+.3f   rmse~T_amp %+.3f'
      % (Q.rmse.corr(Q.T_mean), Q.rmse.corr(Q.T_amp)))
u = Q.drop_duplicates('chunk')
print('unique calendar chunks: %d   rmse~T_mean %+.3f' % (len(u), u.rmse.corr(u.T_mean)))
print('\ntest slice T_mean:')
sub2 = pd.read_csv('outputs/submissions/v8_qblock.csv'); sub2['dt'] = pd.to_datetime(sub2.datetime)
tt = T.reindex(sub2.dt)
print('  near %.2f   far %.2f   full %.2f' % (tt[:220].mean(), tt[220:].mean(), tt.mean()))
print('  train chunk T_mean range %.2f - %.2f' % (u.T_mean.min(), u.T_mean.max()))
