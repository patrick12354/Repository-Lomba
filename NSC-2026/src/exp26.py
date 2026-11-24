"""The v8 blend is under-dispersed (OLS slope 1.08, diurnal swing 89.5% of actual).
Two ways to fix it, both fitted strictly on earlier folds and scored on the held-out one:

  1. post-hoc expansion about some centre, expansion factor fitted on past folds
  2. an unconstrained stack -- NNLS forces weights onto the simplex, which *causes*
     shrinkage; letting the stack scale freely should fix calibration at the source

Run on all three fold families. Uses the stored OOF only, so nothing is refitted.
"""
import warnings; warnings.filterwarnings('ignore')
import sys, json, pickle, numpy as np, pandas as pd
sys.path.insert(0, 'src')
from common import *
from scipy.optimize import nnls
from sklearn.linear_model import Ridge

MS = ['hbt', 'cat', 'ridge', 'enet', 'ridge_e']
OOF = pickle.load(open('outputs/v8_oof.pkl', 'rb'))
FAMS = ['P', 'Q', 'R']


def base_nested(O, shrink=0.25):
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


def fit_scale(past, centre):
    """Expansion factor that minimises MSE on the past folds, in closed form."""
    c = centre(past)
    num = ((past.y - c) * (past.p - c)).sum()
    den = ((past.p - c) ** 2).sum()
    return float(num / den) if den > 0 else 1.0


CENTRES = {
    'global':  lambda d: d.p.mean(),
    'daily':   lambda d: d.groupby('day').p.transform('mean'),
    'hourly':  lambda d: d.hr.map(d.groupby('hr').p.mean()),
}


def evaluate(name, fn):
    row = {}
    for fam in FAMS:
        L = base_nested(OOF[('v8', fam)])
        L['err'] = L.p - L.y; L['hr'] = L.dt.dt.hour; L['day'] = L.dt.dt.date
        per_base, per_adj, wins = [], [], 0
        for k in sorted(L.fold.unique()):
            past, cur = L[L.fold < k], L[L.fold == k].copy()
            if len(past) < 400: continue
            cur['adj'] = fn(past, cur, OOF[('v8', fam)])
            b, a = rmse(cur.y, cur.p), rmse(cur.y, cur.adj)
            per_base.append(b); per_adj.append(a); wins += (a < b)
        row[fam] = (float(np.mean(per_base)), float(np.mean(per_adj)), wins, len(per_adj))
    avg_b = np.mean([row[f][0] for f in FAMS]); avg_a = np.mean([row[f][1] for f in FAMS])
    tw = sum(row[f][2] for f in FAMS); tn = sum(row[f][3] for f in FAMS)
    print(f'  {name:34s} ' + ' '.join(f'{f} {row[f][1]:6.3f}' for f in FAMS) +
          f'  avg {avg_a:6.3f} (base {avg_b:6.3f}, {avg_a-avg_b:+.4f})  folds {tw}/{tn}', flush=True)
    return dict(name=name, avg=avg_a, base=avg_b, delta=avg_a - avg_b, folds_won=tw, n=tn,
                per_family={f: row[f][1] for f in FAMS})


R = []
R.append(evaluate('no correction', lambda p, c, O: c.p))

for cn, cf in CENTRES.items():
    def f(past, cur, O, cf=cf):
        s = fit_scale(past, cf)
        return cf(cur) + s * (cur.p - cf(cur))
    R.append(evaluate(f'expand about {cn} (fitted s)', f))
    def fh(past, cur, O, cf=cf):
        s = 1.0 + 0.5 * (fit_scale(past, cf) - 1.0)
        return cf(cur) + s * (cur.p - cf(cur))
    R.append(evaluate(f'expand about {cn} (half s)', fh))

for s0 in (1.03, 1.05, 1.08, 1.12):
    R.append(evaluate(f'expand about global, fixed s={s0}',
                      lambda p, c, O, s0=s0: c.p.mean() + s0 * (c.p - c.p.mean())))


def unconstrained_stack(past, cur, O, alpha=1.0, positive=False):
    m = Ridge(alpha=alpha, fit_intercept=True, positive=positive)
    m.fit(past[MS].values, past.y.values)
    return m.predict(cur[MS].values)


for al in (0.1, 1.0, 10.0):
    R.append(evaluate(f'ridge stack (alpha={al}, free)',
                      lambda p, c, O, al=al: unconstrained_stack(p, c, O, al)))
R.append(evaluate('ridge stack (alpha=1, positive)',
                  lambda p, c, O: unconstrained_stack(p, c, O, 1.0, True)))


def nnls_free(past, cur, O):
    """NNLS without renormalising to the simplex, plus an intercept column."""
    A = np.hstack([past[MS].values, np.ones((len(past), 1))])
    B = np.hstack([cur[MS].values, np.ones((len(cur), 1))])
    w, _ = nnls(A, past.y.values)
    return B @ w


R.append(evaluate('NNLS free scale + intercept', nnls_free))

json.dump(R, open('outputs/exp26_res.json', 'w'), indent=1, default=float)
print('\n=== RANKING ===', flush=True)
for r in sorted(R, key=lambda r: r['avg']):
    print(f"  {r['name']:36s} avg {r['avg']:6.3f}  {r['delta']:+.4f}  folds {r['folds_won']}/{r['n']}",
          flush=True)
