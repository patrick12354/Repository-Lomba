"""Both shrinkage layers, separated.

`tod_blend_weights` hard-codes BLEND_SHRINK for the per-band NNLS as well, so exp52 only
moved the global layer. Separate them and report the per-band weight vectors, because
section 61 adopted per-band weights on the strength of `ridge_e` rising to 0.17 mid-day --
if that only happens because of the uniform floor, section 61's mechanism needs restating.
"""
import pickle, sys, json, itertools
import numpy as np, pandas as pd
from scipy.optimize import nnls
sys.path[:0] = ['.', 'src']
import final_pipeline as fp
from robust_eval import paired_summary

A = pickle.load(open('outputs/robust_core_scored.pkl', 'rb'))
frame = A['frame'].copy()
M = list(fp.MODELS_L2)
U = np.ones(len(M)) / len(M)

def band_weights(O, w_global, band_lam, nbins=fp.TOD_BINS, shrink=fp.TOD_SHRINK):
    edges = np.quantile(O.tod.values, np.linspace(0, 1, nbins + 1))
    edges[0], edges[-1] = -np.inf, np.inf
    b = np.digitize(O.tod.values, edges[1:-1])
    W = {}
    for i in range(nbins):
        d = O[b == i]
        if len(d) < 150:
            W[i] = w_global; continue
        wi, _ = nnls(d[M].values, d.y.values)
        wi = wi / wi.sum() if wi.sum() > 0 else U.copy()
        wi = (1 - band_lam) * wi + band_lam * U
        W[i] = (1 - shrink) * wi + shrink * w_global
    return edges, W

def run(glam, blam):
    out, gw, bw_all = [], [], []
    for family, fold in frame[['family','fold']].drop_duplicates().itertuples(index=False, name=None):
        vm = (frame.family == family) & (frame.fold == fold)
        meta, valid = frame.loc[~vm].copy(), frame.loc[vm].copy()
        w, _ = nnls(meta[M].values, meta.y.values)
        w = w / w.sum() if w.sum() else U.copy()
        w = (1 - glam) * w + glam * U
        gw.append(w)
        work = meta.copy()
        work['blend'] = np.clip(work[M].values @ w, 5, 100)
        edges, W = band_weights(work, w, blam)
        bw_all.append(np.array([W[i] for i in sorted(W)]))
        work['blend'] = np.clip(fp.apply_tod_blend(work[M].values, work.tod.values, edges, W), 5, 100)
        pr = np.clip(fp.apply_tod_blend(valid[M].values, valid.tod.values, edges, W), 5, 100)
        valid['pred'] = np.clip(fp.apply_harm_bias(pr, valid.tod.values, fp.harm_bias(work)), 5, 100)
        out.append(valid)
    return pd.concat(out, ignore_index=True), np.array(gw), np.array(bw_all)

ref, _, bref = run(0.25, 0.25)
rng = np.random.default_rng(20260905)
print("reference: global 0.25 / band 0.25 (shipped), nested mean %.4f\n"
      % ref.groupby(['family','fold']).apply(lambda d: fp.rmse(d.y,d.pred), include_groups=False).mean())
print("shipped band weight vectors (mean over folds), bands are night / day / evening:")
for i in range(bref.shape[1]):
    print("   band %d  " % i + "  ".join("%s %.3f" % (m, v) for m, v in zip(M, bref[:, i, :].mean(0))))
res = {}
for glam, blam in [(0.25,0.25),(0.00,0.25),(0.25,0.00),(0.00,0.00),(0.10,0.10),(0.05,0.05)]:
    s, gw, bw = run(glam, blam)
    ps = paired_summary(ref, s)
    boot = np.array([rng.choice(ps.delta.values, len(ps), True).mean() for _ in range(20000)])
    fam = ps.groupby('family').delta.agg(['mean', lambda x: int((x<0).sum()), 'size'])
    print("\nglobal %.2f / band %.2f   mean %.4f  delta %+.5f  folds %2d/18  CI [%+.5f,%+.5f]"
          % (glam, blam, ps.candidate.mean(), ps.delta.mean(), (ps.delta<0).sum(),
             np.percentile(boot,2.5), np.percentile(boot,97.5)))
    print("   P %+.4f (%d/9)  Q %+.4f (%d/4)  R %+.4f (%d/5)   worst %.4f -> %.4f"
          % (fam.loc['P','mean'],fam.loc['P','<lambda_0>'],fam.loc['Q','mean'],fam.loc['Q','<lambda_0>'],
             fam.loc['R','mean'],fam.loc['R','<lambda_0>'], ps.base.max(), ps.candidate.max()))
    for i in range(bw.shape[1]):
        print("   band %d  " % i + "  ".join("%s %.3f" % (m, v) for m, v in zip(M, bw[:, i, :].mean(0))))
    res["g%.2f_b%.2f" % (glam, blam)] = dict(mean=float(ps.candidate.mean()), delta=float(ps.delta.mean()),
        won=int((ps.delta<0).sum()), ci=[float(np.percentile(boot,2.5)),float(np.percentile(boot,97.5))],
        worst=float(ps.candidate.max()),
        families={k:[float(fam.loc[k,'mean']),int(fam.loc[k,'<lambda_0>'])] for k in 'PQR'})
json.dump(res, open('outputs/shrink_both.json','w'), indent=2)
