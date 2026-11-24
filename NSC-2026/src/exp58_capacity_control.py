"""Section 61's random-conditioner control, applied to the follow-on knobs.

exp57 says loosening TOD_SHRINK and using six bands both help. Both add effective free
parameters, and section 61's standing rule is that a change adding capacity must be scored
against a RANDOM conditioner with the same parameter count. Here the conditioner is replaced
by a random variable drawn once per fold-row, banded identically -- everything else is held.
"""
import pickle, sys, json
import numpy as np, pandas as pd
from scipy.optimize import nnls
sys.path[:0] = ['.', 'src']
import final_pipeline as fp
from robust_eval import paired_summary

frame = pickle.load(open('outputs/robust_core_scored.pkl', 'rb'))['frame'].copy()
M = list(fp.MODELS_L2) + ['robust_hbt']
U = np.ones(len(M)) / len(M)

def run(tod_shrink, nbins, harm_shrink=fp.HARM_SHRINK, cond='tod', seed=0):
    rng = np.random.default_rng(seed)
    frame['_rand'] = rng.uniform(0, 24, len(frame))
    key = 'tod' if cond == 'tod' else '_rand'
    out = []
    for family, fold in frame[['family','fold']].drop_duplicates().itertuples(index=False, name=None):
        vm = (frame.family == family) & (frame.fold == fold)
        meta, valid = frame.loc[~vm].copy(), frame.loc[vm].copy()
        w, _ = nnls(meta[M].values, meta.y.values); w = w / w.sum() if w.sum() else U.copy()
        work = meta.copy(); work['blend'] = np.clip(work[M].values @ w, 5, 100)
        edges = np.quantile(work[key].values, np.linspace(0, 1, nbins + 1)); edges[0], edges[-1] = -np.inf, np.inf
        b = np.digitize(work[key].values, edges[1:-1]); W = {}
        for i in range(nbins):
            d = work[b == i]
            if len(d) < 150: W[i] = w; continue
            wi, _ = nnls(d[M].values, d.y.values); wi = wi / wi.sum() if wi.sum() > 0 else U.copy()
            W[i] = (1 - tod_shrink) * wi + tod_shrink * w
        work['blend'] = np.clip(fp.apply_tod_blend(work[M].values, work[key].values, edges, W), 5, 100)
        pr = np.clip(fp.apply_tod_blend(valid[M].values, valid[key].values, edges, W), 5, 100)
        # the harmonic correction always uses the true hour of day
        work2 = work.copy()
        valid['pred'] = np.clip(fp.apply_harm_bias(pr, valid.tod.values,
                                                   fp.harm_bias(work2, shrink=harm_shrink)), 5, 100)
        out.append(valid)
    return pd.concat(out, ignore_index=True)

ref = run(fp.TOD_SHRINK, fp.TOD_BINS)
print("reference tod-shrink 0.50 / 3 bands: %.4f\n"
      % ref.groupby(['family','fold']).apply(lambda d: fp.rmse(d.y, d.pred), include_groups=False).mean())
res = {}
for label, ts, nb in (('tod-shrink 0.25, 3 bands', 0.25, 3),
                      ('tod-shrink 0.00, 3 bands', 0.00, 3),
                      ('tod-shrink 0.50, 6 bands', 0.50, 6)):
    s = run(ts, nb)
    ps = paired_summary(ref, s)
    fam = ps.groupby('family').delta.mean()
    real = ps.delta.mean()
    # random-conditioner control, five draws
    ctrl = []
    for sd in range(5):
        sc = run(ts, nb, cond='rand', seed=sd)
        ctrl.append(paired_summary(ref, sc).delta.mean())
    print("%-26s real %+.4f (%2d/18)  P %+.4f Q %+.4f R %+.4f   random control %+.4f (%s)"
          % (label, real, (ps.delta<0).sum(), fam['P'], fam['Q'], fam['R'],
             float(np.mean(ctrl)), " ".join("%+.4f" % c for c in ctrl)))
    print("   %s: real gain beyond capacity = %+.4f"
          % ("ADOPTABLE" if real < np.mean(ctrl) - 0.005 else "INSIDE THE CAPACITY FLOOR",
             real - float(np.mean(ctrl))))
    res[label] = dict(real=float(real), control=float(np.mean(ctrl)), controls=list(map(float, ctrl)),
                      won=int((ps.delta<0).sum()), families={k: float(v) for k, v in fam.items()})

print("\nharmonic shrink, extended -- this strengthens a POST-HOC correction, see section 46")
for hs in (0.50, 0.65, 0.80, 1.00):
    s = run(fp.TOD_SHRINK, fp.TOD_BINS, harm_shrink=hs)
    ps = paired_summary(ref, s)
    fam = ps.groupby('family').delta.mean()
    # amplitude of the correction actually applied, against section 69.1's guard
    print("  harm %.2f  nested %.4f  delta %+.4f  %2d/18  P %+.4f Q %+.4f R %+.4f"
          % (hs, ps.candidate.mean(), ps.delta.mean(), (ps.delta<0).sum(), fam['P'], fam['Q'], fam['R']))
    res['harm %.2f' % hs] = dict(delta=float(ps.delta.mean()), won=int((ps.delta<0).sum()),
                                 families={k: float(v) for k, v in fam.items()})
json.dump(res, open('outputs/capacity_control.json','w'), indent=2)
