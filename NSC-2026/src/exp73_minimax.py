"""A blend fitted for the worst regime instead of the average one.

NNLS minimises pooled squared error across the folds, which is the right thing if the test
window is drawn from the same mixture the folds are. Section 77 says it is not: the test
window is a regime cross-validation never contains. The criterion that matches that situation
is distributionally robust -- minimise the WORST fold's RMSE rather than the mean -- and
section 4.2 already argued the worst fold is what matters when errors are bursty. This log
has never tried it.

Nested throughout: the weights for fold k are fitted on the other folds only.
"""
import pickle, sys, json
import numpy as np, pandas as pd
from scipy.optimize import nnls, minimize
sys.path[:0] = ['.', 'src']
import final_pipeline as fp
from robust_eval import paired_summary

frame = pickle.load(open('outputs/robust_core_scored.pkl','rb'))['frame'].copy()
stress = pickle.load(open('outputs/stress_members.pkl','rb'))
M = list(fp.MODELS_L2)

def fold_rmses(d, models, w):
    p = np.clip(d[models].values @ w, 5, 100)
    return d.assign(se=(p-d.y.values)**2).groupby(['family','fold']).se.mean().pow(.5).values

def w_nnls(meta, models, lam):
    U = np.ones(len(models))/len(models)
    w,_ = nnls(meta[models].values, meta.y.values); w = w/w.sum() if w.sum() else U.copy()
    return (1-lam)*w + lam*U

def w_minimax(meta, models, tau):
    """Softmax-weighted worst case: tau -> 0 is the mean, tau large is the true minimax.
    Optimising the smooth surrogate keeps the problem differentiable and well conditioned."""
    U = np.ones(len(models))/len(models)
    def obj(z):
        w = np.exp(z - z.max()); w = w/w.sum()
        r = fold_rmses(meta, models, w)
        return np.log(np.sum(np.exp(tau*(r - r.max()))))/tau + r.max()
    best, bz = None, None
    for start in (np.log(U), np.log(np.clip(w_nnls(meta, models, 0.0), 1e-3, None))):
        res = minimize(obj, start, method='Nelder-Mead',
                       options=dict(maxiter=4000, xatol=1e-4, fatol=1e-6))
        if best is None or res.fun < best: best, bz = res.fun, res.x
    w = np.exp(bz - bz.max()); return w/w.sum()

def run(kind, param):
    out = []
    for family, fold in frame[['family','fold']].drop_duplicates().itertuples(index=False,name=None):
        vm = (frame.family==family)&(frame.fold==fold)
        meta, valid = frame.loc[~vm].copy(), frame.loc[vm].copy()
        w = w_nnls(meta, M, param) if kind=='nnls' else w_minimax(meta, M, param)
        work = meta.copy(); work['blend'] = np.clip(work[M].values @ w,5,100)
        e, W = fp.tod_blend_weights(work, w, models=M, blend_shrink=(param if kind=='nnls' else 0.0))
        work['blend'] = np.clip(fp.apply_tod_blend(work[M].values, work.tod.values, e, W),5,100)
        pr = np.clip(fp.apply_tod_blend(valid[M].values, valid.tod.values, e, W),5,100)
        valid['pred'] = np.clip(fp.apply_harm_bias(pr, valid.tod.values, fp.harm_bias(work)),5,100)
        valid['_w'] = 0; out.append((valid, w))
    S = pd.concat([o[0] for o in out], ignore_index=True)
    return S, np.array([o[1] for o in out])

def stress_score(kind, param):
    se, per = [], []
    for sid in sorted(stress):
        P = stress[sid]
        meta = frame[frame.datetime <= P.index.min()-pd.Timedelta(hours=96)].copy()
        w = w_nnls(meta, M, param) if kind=='nnls' else w_minimax(meta, M, param)
        work = meta.copy(); work['blend'] = np.clip(work[M].values @ w,5,100)
        e, W = fp.tod_blend_weights(work, w, models=M, blend_shrink=(param if kind=='nnls' else 0.0))
        work['blend'] = np.clip(fp.apply_tod_blend(work[M].values, work.tod.values, e, W),5,100)
        pr = np.clip(fp.apply_tod_blend(P[M].values, P.tod.values, e, W),5,100)
        pr = np.clip(fp.apply_harm_bias(pr, P.tod.values, fp.harm_bias(work)),5,100)
        q = (pr-P.y.values)**2; se.append(q); per.append(float(np.sqrt(q.mean())))
    return float(np.sqrt(np.concatenate(se).mean())), float(np.max(per))

ref, wref = run('nnls', 0.25)
r0 = ref.groupby(['family','fold']).apply(lambda d: fp.rmse(d.y,d.pred), include_groups=False)
s0 = stress_score('nnls', 0.25)
print("v16 reference (NNLS, floor 0.25): nested %.4f  worst %.4f  stress %.4f / %.4f\n"
      % (r0.mean(), r0.max(), s0[0], s0[1]))
res = {}
for kind, param, label in (('nnls', 0.00, 'v20  NNLS, no floor'),
                           ('minimax', 2.0,  'minimax, tau 2'),
                           ('minimax', 6.0,  'minimax, tau 6'),
                           ('minimax', 20.0, 'minimax, tau 20')):
    S, wl = run(kind, param); ps = paired_summary(ref, S)
    fam = ps.groupby('family').delta.agg(['mean', lambda x: int((x<0).sum())])
    sp, sw = stress_score(kind, param)
    print("%-22s nested %.4f  delta %+.4f  %2d/18  worst %.4f  P %+.4f Q %+.4f R %+.4f  stress %.4f / %.4f"
          % (label, ps.candidate.mean(), ps.delta.mean(), (ps.delta<0).sum(), ps.candidate.max(),
             fam.loc['P','mean'], fam.loc['Q','mean'], fam.loc['R','mean'], sp, sw))
    print("     mean weights " + " ".join("%s=%.3f"%(m,x) for m,x in zip(M, wl.mean(0))))
    res[label] = dict(nested=float(ps.candidate.mean()), delta=float(ps.delta.mean()),
        won=int((ps.delta<0).sum()), worst=float(ps.candidate.max()), stress=sp, stress_worst=sw,
        families={k: float(fam.loc[k,'mean']) for k in 'PQR'},
        weights=dict(zip(M, map(float, wl.mean(0)))))
json.dump(res, open('outputs/minimax.json','w'), indent=2)
