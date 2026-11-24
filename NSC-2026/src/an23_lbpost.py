"""Post-mortem on nine scored submissions.

For any two scored files, on the public slice S,

    MSE_i - MSE_j = mean_S[p_i^2] - mean_S[p_j^2] - 2*mean_S[(p_i - p_j) y]

so mean_S[(p_i - p_j) y] is EXACTLY determined by two leaderboard numbers and the two
prediction vectors. Substituting, the full error Gram matrix

    G_ij = mean_S[e_i e_j] = mean_S[p_i p_j] - (mean_S[p_i^2] + mean_S[p_j^2])/2
                             + (MSE_i + MSE_j)/2

is exactly determined too, with no unknown at all -- mean_S[y^2] cancels. G must be positive
semi-definite with diagonal MSE_i, which makes it a TEST of the assumed public slice S as
well as a description of what happened.

This is post-mortem arithmetic on scores already obtained from genuine model submissions,
which is what section 95 did. It is NOT used to choose or construct anything: the implied
step lengths below are read as diagnosis and nothing is fitted to them. Doing otherwise
would be section 43.3's leaderboard probing by the back door.
"""
import sys, json, itertools
import numpy as np, pandas as pd
sys.path[:0] = ['.', 'src']

LB = {  # file -> public score, all from the competition leaderboard
    'v8_qblock':    3.04904,
    'v10_todblend': 3.02942,
    'v11_seed5':    3.00589,
    'v12_harmbias': 3.02286,
    'v14_rngbias':  3.31777,
    'v15_rngonly':  3.14901,
    'v16_l2member': 3.02586,
    'v18_nopress':  3.14173,
    'v19_noridge':  3.13071,
}
P = pd.DataFrame({k: pd.read_csv('outputs/submissions/%s.csv' % k).air_humidity.values
                  for k in LB})
names = list(LB)
mse = np.array([LB[k]**2 for k in names])

def gram(S):
    Q = P.iloc[S].values                       # rows x models
    M = Q.T @ Q / len(S)                       # mean[p_i p_j]
    d = np.diag(M)
    G = M - 0.5*(d[:, None] + d[None, :]) + 0.5*(mse[:, None] + mse[None, :])
    return G

def report(label, S):
    G = gram(S)
    ev = np.linalg.eigvalsh(G)
    sd = np.sqrt(np.clip(np.diag(G), 1e-12, None))
    C = G / np.outer(sd, sd)
    offdiag = C[~np.eye(len(C), dtype=bool)]
    print("%-26s n=%3d  min eig %+9.4f  max |corr| %6.3f  diag ok %s  n_corr>1 %d"
          % (label, len(S), ev.min(), np.abs(offdiag).max(),
             np.allclose(np.diag(G), mse, atol=1e-9), int((np.abs(offdiag) > 1.0).sum())))
    return G, C

print("Is the public slice the first 220 rows? The error Gram matrix must be PSD.\n")
n = len(P)
cands = {'first 220 (assumed)': list(range(220)),
         'last 220':            list(range(n-220, n)),
         'first 514':           list(range(514)),
         'all 734':             list(range(n))}
rng = np.random.default_rng(0)
for i in range(3):
    cands['random 220 #%d' % i] = sorted(rng.choice(n, 220, replace=False))
G = None
for label, S in cands.items():
    g, c = report(label, S)
    if label.startswith('first 220'):
        G, C = g, c

print("\n--- taking the first-220 slice as the public one ---\n")
print("error correlation on the public slice (exact):")
print(pd.DataFrame(C, index=names, columns=names).round(3).to_string())

print("\nstep-length diagnosis. For d = p_cand - p_base, the step that would have been")
print("optimal on the public slice is alpha* = mean[d(y - p_base)] / mean[d^2]; the change")
print("actually taken is alpha = 1. alpha* < 0 means the DIRECTION is wrong.\n")
S = list(range(220))
Q = P.iloc[S]
idx = {k: i for i, k in enumerate(names)}
def step(base, cand):
    d = (Q[cand] - Q[base]).values
    # mean[d (y - p_base)] = -( mean[e_cand e_base] - mean[e_base^2] )  with e = p - y
    num = -(G[idx[cand], idx[base]] - G[idx[base], idx[base]])
    dd = float(np.mean(d**2))
    return num/dd, dd, num
print("%-38s %8s %9s %9s %9s" % ("change", "|d|rms", "alpha*", "d MSE", "best d MSE"))
PAIRS = [('v16_l2member','v18_nopress'), ('v18_nopress','v19_noridge'),
         ('v16_l2member','v19_noridge'), ('v12_harmbias','v16_l2member'),
         ('v11_seed5','v12_harmbias'), ('v10_todblend','v11_seed5'),
         ('v8_qblock','v10_todblend'), ('v12_harmbias','v15_rngonly'),
         ('v12_harmbias','v18_nopress')]
out = {}
for b, c in PAIRS:
    a, dd, num = step(b, c)
    actual = LB[c]**2 - LB[b]**2
    best = -num**2/dd
    print("%-38s %8.4f %9.3f %+9.4f %+9.4f"
          % ("%s -> %s" % (b, c), np.sqrt(dd), a, actual, best))
    out["%s->%s" % (b, c)] = dict(alpha_star=float(a), d_rms=float(np.sqrt(dd)),
                                  delta_mse=float(actual), best_delta_mse=float(best))
json.dump({'gram': G.tolist(), 'names': names, 'steps': out},
          open('outputs/lbpost.json','w'), indent=2)
