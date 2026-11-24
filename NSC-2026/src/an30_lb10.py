"""Post-mortem with TEN scored files -- v20_shrinkonly (3.05372) is the new one.

Same exact arithmetic as an23: the error Gram on the public slice is fully determined by
the scores and the prediction vectors, with no unknown. Diagnosis only -- nothing here is
used to select or construct a submission (section 43.3).
"""
import sys, itertools
import numpy as np, pandas as pd
sys.path[:0] = ['.', 'src']

LB = {
    'v8_qblock':      3.04904,
    'v10_todblend':   3.02942,
    'v11_seed5':      3.00589,
    'v12_harmbias':   3.02286,
    'v14_rngbias':    3.31777,
    'v15_rngonly':    3.14901,
    'v16_l2member':   3.02586,
    'v18_nopress':    3.14173,
    'v19_noridge':    3.13071,
    'v20_shrinkonly': 3.05372,
}
P = pd.DataFrame({k: pd.read_csv('outputs/submissions/%s.csv' % k).air_humidity.values
                  for k in LB})
names = list(LB); n = len(names)
mse = np.array([LB[k]**2 for k in names])
idx = {k: i for i, k in enumerate(names)}

def gram(S):
    Q = P.iloc[S].values
    M = Q.T @ Q / len(S)
    d = np.diag(M)
    return M - 0.5*(d[:, None] + d[None, :]) + 0.5*(mse[:, None] + mse[None, :])

N = len(P)
slices = {'first220': np.arange(220), 'last220': np.arange(N-220, N),
          'strat': np.arange(N)[::N//220][:220], 'all734': np.arange(N)}
rng = np.random.default_rng(0)
for r in range(5):
    slices['rand%d' % r] = np.sort(rng.choice(N, 220, replace=False))

print("=== integrity: Gram PSD over candidate slices ===")
for lab, S in slices.items():
    G = gram(S); ev = np.linalg.eigvalsh(G)
    print("  %-9s min eig %+9.5f" % (lab, ev.min()))

# alpha* : optimal step length for change base -> cand on slice S.
# d = p_cand - p_base ;  alpha* = mean[d(y-p_base)] / mean[d^2]
# mean[d(y-p_base)] = (MSE_base - MSE_cand + mean[d^2]) / 2   (exact)
def alpha(base, cand, S):
    d = P[cand].values[S] - P[base].values[S]
    md2 = float(np.mean(d*d))
    num = (LB[base]**2 - LB[cand]**2 + md2) / 2.0
    return num/md2, md2, LB[cand]**2 - LB[base]**2

CH = [('v8_qblock','v10_todblend','per-band weights'),
      ('v10_todblend','v11_seed5','band bias'),
      ('v11_seed5','v12_harmbias','harmonic bias'),
      ('v12_harmbias','v16_l2member','L2 member'),
      ('v12_harmbias','v15_rngonly','wide-range bet (falsified)'),
      ('v16_l2member','v18_nopress','robust core + nopress + shrink0'),
      ('v16_l2member','v19_noridge','   ... + drop ridge'),
      ('v16_l2member','v20_shrinkonly','*** SHRINK FLOOR REMOVED ONLY ***'),
      ('v20_shrinkonly','v19_noridge','shrink0 -> + nopress/core/noridge'),
      ('v11_seed5','v16_l2member','v11 -> v16'),
      ('v11_seed5','v20_shrinkonly','v11 -> v20')]
print("\n=== alpha* (public=first220) ===")
print("%-46s %8s %9s %9s" % ("change", "rms|d|", "alpha*", "dMSE"))
for b,c,lab in CH:
    a, md2, dm = alpha(b,c,slices['first220'])
    print("%-46s %8.3f %9.3f %+9.4f" % (lab, md2**0.5, a, dm))

print("\n=== alpha* robustness across assumed slices ===")
print("%-46s %s" % ("change", "  ".join("%8s"%s for s in slices)))
for b,c,lab in CH[-4:] + [CH[5], CH[3]]:
    row = [alpha(b,c,S)[0] for S in slices.values()]
    print("%-46s %s" % (lab, "  ".join("%8.2f"%v for v in row)))

# --- ceiling diagnosis: how good is the best convex mix of what we already have? ---
from scipy.optimize import nnls
S = slices['first220']; G = gram(S)
print("\n=== DIAGNOSIS ONLY: frontier of the ten existing files on the public slice ===")
print("(reported to price how far 2.7 is; NOT used to build a submission)")
# min w'Gw s.t. sum w = 1  -- errors combine as e_mix = sum w_i e_i when sum w = 1
A = np.vstack([G, np.ones(n)*1e3]); b = np.zeros(n+1); b[-1] = 1e3
w, _ = nnls(A, b)
w = w/w.sum()
print("  best nonneg convex mix RMSE %.5f   (best single %.5f)" % (np.sqrt(w@G@w), np.sqrt(mse.min())))
for k,v in sorted(zip(names,w), key=lambda z:-z[1]):
    if v > 1e-4: print("     %-16s %.3f" % (k,v))
sd = np.sqrt(np.diag(G)); C = G/np.outer(sd,sd)
print("\n  error correlation on public, min off-diagonal pair:")
c2 = C.copy(); np.fill_diagonal(c2, 9)
i,j = np.unravel_index(np.argmin(c2), c2.shape)
print("     %s vs %s : %.4f" % (names[i], names[j], C[i,j]))
print("  mean off-diagonal error corr %.4f" % C[~np.eye(n,dtype=bool)].mean())
