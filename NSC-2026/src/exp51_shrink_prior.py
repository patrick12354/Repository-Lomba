"""If a duplicate member helps, the shrinkage PRIOR is wrong, not the member list.

exp49: a seventh member that is `hbt` refit on other seeds (residual corr 0.998) is worth
-0.0128 on 14/18 folds, and pure noise added to `hbt` is worth -0.0132 on 15/18. Neither
carries information. The mechanism is `BLEND_SHRINK`: the weights are pulled toward the
UNIFORM vector, which hands 1/6 to members NNLS wants at zero. Duplicating `hbt` moves the
uniform target toward `hbt` and recovers part of what the shrinkage gave away.

So test the prior directly instead of smuggling it in as a member. Predeclared grid, all
18 folds, three families; judged on a plateau plus a family-wise sign, not on the best cell.
"""
import pickle, sys, json, itertools
import numpy as np, pandas as pd
from scipy.optimize import nnls
sys.path[:0] = ['.', 'src']
import final_pipeline as fp
from robust_eval import paired_summary

A = pickle.load(open('outputs/robust_core_scored.pkl', 'rb'))
frame = A['frame'].copy()
M5, M6 = list(fp.MODELS), list(fp.MODELS_L2)

def prior_vec(meta, models, kind):
    if kind == 'uniform':
        return np.ones(len(models)) / len(models)
    # inverse mean-squared-error of each member, fitted on the same nested meta rows
    mse = np.array([np.mean((meta[m].values - meta.y.values) ** 2) for m in models])
    w = 1.0 / mse
    return w / w.sum()

def score(models, lam, kind):
    out = []
    for family, fold in frame[['family', 'fold']].drop_duplicates().itertuples(index=False, name=None):
        vm = (frame.family == family) & (frame.fold == fold)
        meta, valid = frame.loc[~vm].copy(), frame.loc[vm].copy()
        p0 = prior_vec(meta, models, kind)
        w, _ = nnls(meta[models].values, meta.y.values)
        w = w / w.sum() if w.sum() else p0.copy()
        w = (1 - lam) * w + lam * p0
        work = meta.copy()
        work['blend'] = np.clip(work[models].values @ w, 5, 100)
        edges, bw = fp.tod_blend_weights(work, w, models=models)
        work['blend'] = np.clip(fp.apply_tod_blend(work[models].values, work.tod.values, edges, bw), 5, 100)
        pr = np.clip(fp.apply_tod_blend(valid[models].values, valid.tod.values, edges, bw), 5, 100)
        h = fp.harm_bias(work)
        valid['pred'] = np.clip(fp.apply_harm_bias(pr, valid.tod.values, h), 5, 100)
        out.append(valid)
    return pd.concat(out, ignore_index=True)

LAMS = [0.00, 0.10, 0.15, 0.25, 0.40]
KINDS = ['uniform', 'inv_mse']
ref = None
rows = []
for models, tag in ((M6, 'v16(6)'), (M5, 'v12(5)')):
    for kind, lam in itertools.product(KINDS, LAMS):
        s = score(models, lam, kind)
        if ref is None and tag == 'v16(6)' and kind == 'uniform' and lam == 0.25:
            ref = s
        rows.append((tag, kind, lam, s))
print("reference = v16, uniform prior, lambda 0.25 (shipped)\n")
res = {}
for tag, kind, lam, s in rows:
    ps = paired_summary(ref, s)
    fam = ps.groupby('family').delta.agg(['mean', lambda x: int((x < 0).sum()), 'size'])
    mean_rmse = ps.candidate.mean()
    flag = ' <-- shipped' if (tag, kind, lam) == ('v16(6)', 'uniform', 0.25) else ''
    print("%-8s %-8s lam %.2f  mean %.4f  delta %+.4f  folds %2d/18  P %+.4f Q %+.4f R %+.4f%s"
          % (tag, kind, lam, mean_rmse, ps.delta.mean(), (ps.delta < 0).sum(),
             fam.loc['P', 'mean'], fam.loc['Q', 'mean'], fam.loc['R', 'mean'], flag))
    res["%s|%s|%.2f" % (tag, kind, lam)] = dict(
        mean=float(mean_rmse), delta=float(ps.delta.mean()),
        won=int((ps.delta < 0).sum()),
        families={k: float(v) for k, v in fam['mean'].items()},
        fam_won={k: int(v) for k, v in fam['<lambda_0>'].items()})
json.dump(res, open('outputs/shrink_prior.json', 'w'), indent=2)
