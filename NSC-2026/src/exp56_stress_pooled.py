"""Re-aggregate the stress blocks the way the competition metric does.

`passes_gate` compares the MEAN of per-block RMSEs. The leaderboard computes ONE RMSE over
all 734 test rows, which pools squared errors -- so hard blocks carry more weight than an
unweighted mean of RMSEs gives them. Recompute both, from the same stored predictions.
"""
import pickle, sys, json
import numpy as np, pandas as pd
from scipy.optimize import nnls
sys.path[:0] = ['.', 'src']
import final_pipeline as fp

cache = pickle.load(open('outputs/stress_members.pkl', 'rb'))
frame = pickle.load(open('outputs/robust_core_scored.pkl', 'rb'))['frame']
M6 = list(fp.MODELS_L2)

def predict_stack(meta, valid, models, glam, blam):
    U = np.ones(len(models))/len(models)
    w, _ = nnls(meta[models].values, meta.y.values)
    w = w/w.sum() if w.sum() else U.copy(); w = (1-glam)*w + glam*U
    work = meta.copy(); work['blend'] = np.clip(work[models].values @ w, 5, 100)
    edges = np.quantile(work.tod.values, np.linspace(0,1,fp.TOD_BINS+1)); edges[0],edges[-1]=-np.inf,np.inf
    b = np.digitize(work.tod.values, edges[1:-1]); W={}
    for i in range(fp.TOD_BINS):
        d = work[b==i]
        if len(d)<150: W[i]=w; continue
        wi,_ = nnls(d[models].values, d.y.values); wi = wi/wi.sum() if wi.sum()>0 else U.copy()
        wi = (1-blam)*wi + blam*U
        W[i] = (1-fp.TOD_SHRINK)*wi + fp.TOD_SHRINK*w
    work['blend'] = np.clip(fp.apply_tod_blend(work[models].values, work.tod.values, edges, W),5,100)
    pr = np.clip(fp.apply_tod_blend(valid[models].values, valid.tod.values, edges, W),5,100)
    return np.clip(fp.apply_harm_bias(pr, valid.tod.values, fp.harm_bias(work)),5,100)

ARMS = [('v16  0.25/0.25 (shipped)', M6, .25, .25), ('v16  0.05/0.05', M6, .05, .05),
        ('v16  0.00/0.00', M6, .00, .00),
        ('v16+core 0.25/0.25', M6+['robust_hbt'], .25, .25),
        ('v16+core 0.05/0.05', M6+['robust_hbt'], .05, .05),
        ('v16+core 0.00/0.00', M6+['robust_hbt'], .00, .00)]
out = {}
for name, models, gl, bl in ARMS:
    se, per = [], []
    for sid in sorted(cache):
        P = cache[sid]
        meta = frame[frame.datetime <= P.index.min() - pd.Timedelta(hours=96)].copy()
        pr = predict_stack(meta, P, models, gl, bl)
        e = (pr - P.y.values) ** 2
        se.append(e); per.append(float(np.sqrt(e.mean())))
    pooled = float(np.sqrt(np.concatenate(se).mean()))
    out[name] = dict(pooled=pooled, mean_of_rmse=float(np.mean(per)),
                     worst=float(np.max(per)), per_block=per)
    print("%-26s pooled RMSE %.4f   mean-of-RMSE %.4f   worst block %.4f"
          % (name, pooled, np.mean(per), np.max(per)))
b = out['v16  0.25/0.25 (shipped)']
print("\ndeltas against the shipped configuration:")
for k, v in out.items():
    print("  %-26s pooled %+.4f   mean-of-RMSE %+.4f   worst %+.4f"
          % (k, v['pooled']-b['pooled'], v['mean_of_rmse']-b['mean_of_rmse'], v['worst']-b['worst']))

# same question for the 18 nested CV folds
A = pickle.load(open('outputs/robust_core_scored.pkl','rb'))
print("\nnested CV, both aggregations:")
for name, models, gl, bl in ARMS:
    rows = []
    for family, fold in frame[['family','fold']].drop_duplicates().itertuples(index=False, name=None):
        vm = (frame.family==family)&(frame.fold==fold)
        meta, valid = frame.loc[~vm].copy(), frame.loc[vm].copy()
        pr = predict_stack(meta, valid, models, gl, bl)
        rows.append(pd.DataFrame({'family':family,'fold':fold,'se':(pr-valid.y.values)**2}))
    R = pd.concat(rows)
    f = R.groupby(['family','fold']).se.mean().pow(.5)
    print("  %-26s mean-of-RMSE %.4f   pooled %.4f   worst %.4f"
          % (name, f.mean(), np.sqrt(R.se.mean()), f.max()))
json.dump(out, open('outputs/stress_pooled.json','w'), indent=2)
