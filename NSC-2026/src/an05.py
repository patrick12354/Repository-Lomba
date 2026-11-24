"""Why did the dispersion calibration lose on the leaderboard after winning 13/13 folds?

Hypothesis: the amount of under-dispersion is regime-dependent. It is measured on folds
inside the hot, variable July-August training period; the test window is cooler and
calmer. In a low-variance window an averaged ensemble is less compressed, so a slope
fitted elsewhere overshoots.

Test: per fold, compute the slope that WOULD have been optimal, and see what it tracks.
"""
import warnings; warnings.filterwarnings('ignore')
import sys, pickle, numpy as np, pandas as pd
sys.path.insert(0, 'src')
from common import *
from scipy.optimize import nnls
pd.set_option('display.width', 220)

MS = ['hbt', 'cat', 'ridge', 'enet', 'ridge_e']
OOF = pickle.load(open('outputs/v8_oof.pkl', 'rb'))
g, _, _ = load_grid()
c = clean_exog(g, k=6.0)
T = c['air_temperature']


def nested(O, shrink=0.25):
    out = []
    for k in sorted(O.fold.unique()):
        prev, cur = O[O.fold < k], O[O.fold == k].copy()
        if len(prev) < 200: continue
        w, _ = nnls(prev[MS].values, prev.y.values)
        w = w / w.sum() if w.sum() > 0 else np.ones(len(MS)) / len(MS)
        w = (1 - shrink) * w + shrink * np.ones(len(MS)) / len(MS)
        cur['p'] = cur[MS].values @ w
        out.append(cur)
    return pd.concat(out, ignore_index=True)


L = nested(OOF[('v8', 'P')])
print('=== per-fold optimal expansion slope vs what the window looks like ===')
rows = []
for k, d in L.groupby('fold'):
    m = d.p.mean()
    num = ((d.y - m) * (d.p - m)).sum()
    den = ((d.p - m) ** 2).sum()
    s_opt = float(num / den)
    Tw = T.reindex(d.dt)
    gain = rmse(d.y, d.p) - rmse(d.y, m + s_opt * (d.p - m))
    at105 = rmse(d.y, np.clip(m + 1.058 * (d.p - m), 5, 100)) - rmse(d.y, d.p)
    rows.append(dict(fold=k, start=str(d.dt.min())[:10], y_std=d.y.std(), p_std=d.p.std(),
                     ratio=d.p.std() / d.y.std(), s_opt=s_opt, T_med=float(Tw.median()),
                     T_std=float(Tw.std()), rmse=rmse(d.y, d.p),
                     gain_at_opt=gain, delta_at_1058=at105))
R = pd.DataFrame(rows)
print(R.round(3).to_string(index=False))

print('\n=== what does the optimal slope correlate with? ===')
for col in ['y_std', 'p_std', 'ratio', 'T_med', 'T_std', 'rmse']:
    print(f'  s_opt vs {col:8s}: {R.s_opt.corr(R[col]):+.3f}')

print('\n=== the key question: what does the TEST window look like? ===')
is_te = (g.is_test == 1).values
Tt = T[is_te]
print(f'  test window   : T median {Tt.median():.2f}  T std {Tt.std():.2f}')
print(f'  CV folds range: T median {R.T_med.min():.2f}-{R.T_med.max():.2f}  '
      f'T std {R.T_std.min():.2f}-{R.T_std.max():.2f}')
sub8 = pd.read_csv('outputs/submissions/v8_qblock.csv')
print(f'  v8 test prediction std {sub8.air_humidity.std():.2f}   '
      f'CV fold prediction std {R.p_std.min():.2f}-{R.p_std.max():.2f}')

print('\n=== if the test window behaves like the calmest folds, what happens at s=1.058? ===')
calm = R.nsmallest(3, 'T_std')
print(calm[['fold', 'start', 'T_std', 's_opt', 'delta_at_1058']].round(3).to_string(index=False))
hot = R.nlargest(3, 'T_std')
print(hot[['fold', 'start', 'T_std', 's_opt', 'delta_at_1058']].round(3).to_string(index=False))

print('\n=== arithmetic check: does the LB regression match an over-expansion? ===')
lb8, lbf = 3.04904, 3.28564
print(f'  v8 LB {lb8}  -> MSE {lb8**2:.4f}')
print(f'  final LB {lbf} -> MSE {lbf**2:.4f}   difference {lbf**2-lb8**2:+.4f}')
s = 1.0580
var_p = float(sub8.air_humidity.var())
print(f'  v8 prediction variance {var_p:.1f}')
print(f'  pure over-expansion cost (s-1)^2 * Var(pred) = {(s-1)**2*var_p:.4f} MSE')
print('  (equal to the observed gap only if the model was already well dispersed on test;')
print('   a positive residual-prediction covariance would add the rest)')
