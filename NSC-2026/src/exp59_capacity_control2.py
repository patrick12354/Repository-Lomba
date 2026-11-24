"""Corrected control. exp58 compared a loosened real conditioner against a random one at a
DIFFERENT shrink, which measures the value of banding on hour-of-day rather than the cost of
the loosening. What is needed is the same loosening applied to both conditioners:

    real gain    = real(0.25) - real(0.50)
    capacity gain = random(0.25) - random(0.50)

If the second explains the first, loosening is buying free parameters, not signal.
"""
import pickle, sys, json
import numpy as np, pandas as pd
from scipy.optimize import nnls
sys.path[:0] = ['.', 'src']
import final_pipeline as fp

frame = pickle.load(open('outputs/robust_core_scored.pkl', 'rb'))['frame'].copy()
M = list(fp.MODELS_L2) + ['robust_hbt']
U = np.ones(len(M)) / len(M)

def run(tod_shrink, nbins, cond='tod', seed=0):
    rng = np.random.default_rng(seed)
    frame['_rand'] = rng.uniform(0, 24, len(frame))
    key = 'tod' if cond == 'tod' else '_rand'
    out = []
    for family, fold in frame[['family','fold']].drop_duplicates().itertuples(index=False, name=None):
        vm = (frame.family == family) & (frame.fold == fold)
        meta, valid = frame.loc[~vm].copy(), frame.loc[vm].copy()
        w, _ = nnls(meta[M].values, meta.y.values); w = w/w.sum() if w.sum() else U.copy()
        work = meta.copy(); work['blend'] = np.clip(work[M].values @ w, 5, 100)
        edges = np.quantile(work[key].values, np.linspace(0,1,nbins+1)); edges[0],edges[-1]=-np.inf,np.inf
        b = np.digitize(work[key].values, edges[1:-1]); W={}
        for i in range(nbins):
            d = work[b==i]
            if len(d)<150: W[i]=w; continue
            wi,_ = nnls(d[M].values, d.y.values); wi = wi/wi.sum() if wi.sum()>0 else U.copy()
            W[i] = (1-tod_shrink)*wi + tod_shrink*w
        work['blend'] = np.clip(fp.apply_tod_blend(work[M].values, work[key].values, edges, W),5,100)
        pr = np.clip(fp.apply_tod_blend(valid[M].values, valid[key].values, edges, W),5,100)
        valid['pred'] = np.clip(fp.apply_harm_bias(pr, valid.tod.values, fp.harm_bias(work)),5,100)
        out.append(valid)
    s = pd.concat(out, ignore_index=True)
    f = s.groupby(['family','fold']).apply(lambda d: fp.rmse(d.y, d.pred), include_groups=False)
    return float(f.mean()), s

CFG = [('tod-shrink 0.50, 3 bands', 0.50, 3), ('tod-shrink 0.25, 3 bands', 0.25, 3),
       ('tod-shrink 0.00, 3 bands', 0.00, 3), ('tod-shrink 0.50, 6 bands', 0.50, 6),
       ('tod-shrink 0.25, 6 bands', 0.25, 6)]
real, rand = {}, {}
for label, ts, nb in CFG:
    real[label] = run(ts, nb)[0]
    rand[label] = float(np.mean([run(ts, nb, cond='rand', seed=sd)[0] for sd in range(3)]))
    print("%-26s real %.4f   random-conditioner %.4f" % (label, real[label], rand[label]))
base = 'tod-shrink 0.50, 3 bands'
print("\nchange from the shipped setting, both conditioners:")
print("%-26s %10s %10s %12s" % ("config", "real", "capacity", "signal"))
out = {}
for label, _, _ in CFG:
    r, c = real[label]-real[base], rand[label]-rand[base]
    print("%-26s %+10.4f %+10.4f %+12.4f" % (label, r, c, r-c))
    out[label] = dict(real_delta=r, capacity_delta=c, signal=r-c)
json.dump(out, open('outputs/capacity_control2.json','w'), indent=2)
