"""Section 21's rule applied to the two shrinkages that were NOT changed.

TOD_SHRINK (band weights toward global) and HARM_SHRINK were both tuned while
BLEND_SHRINK was 0.25. That constant is now 0.0, so their optima have to be re-measured
rather than assumed. Predeclared grid, 18 nested folds, 7-member stack; a candidate needs a
negative mean in P, Q and R plus a fold majority, and a plateau rather than a lone cell.
"""
import pickle, sys, json, itertools
import numpy as np, pandas as pd
from scipy.optimize import nnls
sys.path[:0] = ['.', 'src']
import final_pipeline as fp
from robust_eval import paired_summary

frame = pickle.load(open('outputs/robust_core_scored.pkl', 'rb'))['frame'].copy()
M = list(fp.MODELS_L2) + ['robust_hbt']
U = np.ones(len(M)) / len(M)

def run(tod_shrink, harm_shrink, nbins=fp.TOD_BINS):
    out = []
    for family, fold in frame[['family','fold']].drop_duplicates().itertuples(index=False, name=None):
        vm = (frame.family == family) & (frame.fold == fold)
        meta, valid = frame.loc[~vm].copy(), frame.loc[vm].copy()
        w, _ = nnls(meta[M].values, meta.y.values)
        w = w / w.sum() if w.sum() else U.copy()
        work = meta.copy(); work['blend'] = np.clip(work[M].values @ w, 5, 100)
        edges = np.quantile(work.tod.values, np.linspace(0, 1, nbins + 1))
        edges[0], edges[-1] = -np.inf, np.inf
        b = np.digitize(work.tod.values, edges[1:-1]); W = {}
        for i in range(nbins):
            d = work[b == i]
            if len(d) < 150: W[i] = w; continue
            wi, _ = nnls(d[M].values, d.y.values)
            wi = wi / wi.sum() if wi.sum() > 0 else U.copy()
            W[i] = (1 - tod_shrink) * wi + tod_shrink * w
        work['blend'] = np.clip(fp.apply_tod_blend(work[M].values, work.tod.values, edges, W), 5, 100)
        pr = np.clip(fp.apply_tod_blend(valid[M].values, valid.tod.values, edges, W), 5, 100)
        valid['pred'] = np.clip(fp.apply_harm_bias(pr, valid.tod.values,
                                                   fp.harm_bias(work, shrink=harm_shrink)), 5, 100)
        out.append(valid)
    return pd.concat(out, ignore_index=True)

ref = run(fp.TOD_SHRINK, fp.HARM_SHRINK)
r0 = ref.groupby(['family','fold']).apply(lambda d: fp.rmse(d.y, d.pred), include_groups=False)
print("reference (tod 0.50 / harm 0.50, blend shrink 0): nested %.4f  pooled %.4f  worst %.4f\n"
      % (r0.mean(), np.sqrt(((ref.pred-ref.y)**2).mean()), r0.max()))
res = {}
print("%-22s %8s %9s %6s %8s %8s %8s %8s" % ("config","nested","delta","folds","P","Q","R","pooled"))
for ts, hs in itertools.product((0.00, 0.25, 0.50, 0.75), (0.35, 0.50, 0.65)):
    s = run(ts, hs)
    ps = paired_summary(ref, s)
    fam = ps.groupby('family').delta.mean()
    print("tod %.2f / harm %.2f   %8.4f %+9.4f %4d/18 %+8.4f %+8.4f %+8.4f %8.4f"
          % (ts, hs, ps.candidate.mean(), ps.delta.mean(), (ps.delta<0).sum(),
             fam['P'], fam['Q'], fam['R'], np.sqrt(((s.pred-s.y)**2).mean())))
    res["t%.2f_h%.2f" % (ts, hs)] = dict(nested=float(ps.candidate.mean()),
        delta=float(ps.delta.mean()), won=int((ps.delta<0).sum()),
        families={k: float(v) for k, v in fam.items()},
        pooled=float(np.sqrt(((s.pred-s.y)**2).mean())), worst=float(ps.candidate.max()))
print("\nband count at tod 0.50 / harm 0.50:")
for nb in (2, 3, 4, 6):
    s = run(0.50, 0.50, nbins=nb)
    ps = paired_summary(ref, s)
    print("  %d bands  nested %.4f  delta %+.4f  folds %2d/18" % (nb, ps.candidate.mean(), ps.delta.mean(), (ps.delta<0).sum()))
    res["bins%d" % nb] = dict(nested=float(ps.candidate.mean()), delta=float(ps.delta.mean()), won=int((ps.delta<0).sum()))
json.dump(res, open('outputs/retune_after.json','w'), indent=2)
