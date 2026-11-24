"""Every member decision, re-adjudicated under the corrected shrinkage.

With the uniform floor gone, a member only earns weight if NNLS gives it weight. That
re-opens three verdicts taken under the floor: section 98's L2 member, exp44's robust
core, and exp49's two null members.
"""
import pickle, sys, json
import numpy as np, pandas as pd
from scipy.optimize import nnls
sys.path[:0] = ['.', 'src']
import final_pipeline as fp
from robust_eval import paired_summary

A = pickle.load(open('outputs/robust_core_scored.pkl', 'rb'))
frame = A['frame'].copy()
dup = pickle.load(open('outputs/dilution_control_oof.pkl', 'rb'))
frame['dup_hbt'] = np.nan
for (fam, fold), v in dup.items():
    m = (frame.family == fam) & (frame.fold == fold)
    frame.loc[m, 'dup_hbt'] = v.reindex(pd.DatetimeIndex(frame.loc[m, 'datetime'])).values
rs = np.random.default_rng(4242)
frame['noise_hbt'] = frame['hbt'] + rs.normal(0, frame['hbt'].std() * 0.02, len(frame))

def run(models, glam, blam):
    U = np.ones(len(models)) / len(models)
    out, gw, bws = [], [], []
    for family, fold in frame[['family','fold']].drop_duplicates().itertuples(index=False, name=None):
        vm = (frame.family == family) & (frame.fold == fold)
        meta, valid = frame.loc[~vm].copy(), frame.loc[vm].copy()
        w, _ = nnls(meta[models].values, meta.y.values)
        w = w / w.sum() if w.sum() else U.copy()
        w = (1 - glam) * w + glam * U
        gw.append(w)
        work = meta.copy()
        work['blend'] = np.clip(work[models].values @ w, 5, 100)
        edges = np.quantile(work.tod.values, np.linspace(0, 1, fp.TOD_BINS + 1))
        edges[0], edges[-1] = -np.inf, np.inf
        b = np.digitize(work.tod.values, edges[1:-1]); W = {}
        for i in range(fp.TOD_BINS):
            d = work[b == i]
            if len(d) < 150: W[i] = w; continue
            wi, _ = nnls(d[models].values, d.y.values)
            wi = wi / wi.sum() if wi.sum() > 0 else U.copy()
            wi = (1 - blam) * wi + blam * U
            W[i] = (1 - fp.TOD_SHRINK) * wi + fp.TOD_SHRINK * w
        bws.append(np.array([W[i] for i in sorted(W)]))
        work['blend'] = np.clip(fp.apply_tod_blend(work[models].values, work.tod.values, edges, W), 5, 100)
        pr = np.clip(fp.apply_tod_blend(valid[models].values, valid.tod.values, edges, W), 5, 100)
        valid['pred'] = np.clip(fp.apply_harm_bias(pr, valid.tod.values, fp.harm_bias(work)), 5, 100)
        out.append(valid)
    return pd.concat(out, ignore_index=True), np.array(gw), np.array(bws)

def amp(d, col):
    t = (d.datetime.dt.hour + d.datetime.dt.minute / 60).round(0)
    m = d.groupby(t)[col].mean(); return m.max() - m.min()

M5, M6 = list(fp.MODELS), list(fp.MODELS_L2)
SETS = {'v12 5-member': M5, 'v16 6-member': M6,
        '6 + robust_core': M6 + ['robust_hbt'],
        '6 + dup_hbt (null)': M6 + ['dup_hbt'],
        '6 + noise_hbt (null)': M6 + ['noise_hbt']}
rng = np.random.default_rng(7)
res = {}
for glam, blam in ((0.25, 0.25), (0.05, 0.05), (0.00, 0.00)):
    print("\n=== shrinkage global %.2f / band %.2f ===" % (glam, blam))
    ref = None
    for name, models in SETS.items():
        s, gw, bw = run(models, glam, blam)
        folds = s.groupby(['family','fold']).apply(lambda d: fp.rmse(d.y, d.pred), include_groups=False)
        if name == 'v16 6-member': ref = s
        line = "  %-21s mean %.4f  disp %.4f  w:" % (name, folds.mean(), amp(s,'pred')/amp(s,'y'))
        line += " ".join("%s=%.3f" % (m, v) for m, v in zip(models, gw.mean(0)))
        print(line)
        res["%.2f|%s" % (glam, name)] = dict(mean=float(folds.mean()),
            weights=dict(zip(models, map(float, gw.mean(0)))))
    for name, models in SETS.items():
        if name == 'v16 6-member': continue
        s, _, _ = run(models, glam, blam)
        ps = paired_summary(ref, s)
        fam = ps.groupby('family').delta.agg(['mean', lambda x: int((x<0).sum()), 'size'])
        boot = np.array([rng.choice(ps.delta.values, len(ps), True).mean() for _ in range(10000)])
        print("     %-21s vs 6-member: %+.5f  %2d/18  CI [%+.5f,%+.5f]  P %+.4f Q %+.4f R %+.4f"
              % (name, ps.delta.mean(), (ps.delta<0).sum(), np.percentile(boot,2.5),
                 np.percentile(boot,97.5), fam.loc['P','mean'], fam.loc['Q','mean'], fam.loc['R','mean']))
json.dump(res, open('outputs/members_reeval.json','w'), indent=2)
