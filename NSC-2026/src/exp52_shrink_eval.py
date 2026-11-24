"""Full adjudication of the blend-shrinkage change: fold-level bootstrap, weight
stability across folds, exposure to the section-78 shifted features, dispersion guard."""
import pickle, sys, json
import numpy as np, pandas as pd
from scipy.optimize import nnls
sys.path[:0] = ['.', 'src']
import final_pipeline as fp
from robust_eval import paired_summary

A = pickle.load(open('outputs/robust_core_scored.pkl', 'rb'))
frame = A['frame'].copy()
M = list(fp.MODELS_L2)

def run(lam):
    out, ws = [], []
    for family, fold in frame[['family','fold']].drop_duplicates().itertuples(index=False, name=None):
        vm = (frame.family == family) & (frame.fold == fold)
        meta, valid = frame.loc[~vm].copy(), frame.loc[vm].copy()
        u = np.ones(len(M))/len(M)
        w, _ = nnls(meta[M].values, meta.y.values)
        w = w/w.sum() if w.sum() else u.copy()
        w = (1-lam)*w + lam*u
        ws.append(w)
        work = meta.copy()
        work['blend'] = np.clip(work[M].values @ w, 5, 100)
        edges, bw = fp.tod_blend_weights(work, w, models=M)
        work['blend'] = np.clip(fp.apply_tod_blend(work[M].values, work.tod.values, edges, bw), 5, 100)
        pr = np.clip(fp.apply_tod_blend(valid[M].values, valid.tod.values, edges, bw), 5, 100)
        valid['pred'] = np.clip(fp.apply_harm_bias(pr, valid.tod.values, fp.harm_bias(work)), 5, 100)
        out.append(valid)
    return pd.concat(out, ignore_index=True), np.array(ws)

ref, wref = run(fp.BLEND_SHRINK)
rng = np.random.default_rng(20260905)
res = {}
print("global NNLS weights across the 18 outer folds\n")
for lam in (0.00, 0.10, 0.15, 0.25):
    s, ws = run(lam)
    ps = paired_summary(ref, s)
    boot = np.array([rng.choice(ps.delta.values, len(ps), True).mean() for _ in range(20000)])
    fam = ps.groupby('family').delta.agg(['mean', lambda x: int((x<0).sum()), 'size'])
    def amp(d, col):
        t = (d.datetime.dt.hour + d.datetime.dt.minute/60).round(0)
        m = d.groupby(t)[col].mean(); return m.max()-m.min()
    print("lambda %.2f  mean %.4f  delta %+.5f  folds %2d/18  CI [%+.5f,%+.5f]  P(>=0) %.4f"
          % (lam, ps.candidate.mean(), ps.delta.mean(), (ps.delta<0).sum(),
             np.percentile(boot,2.5), np.percentile(boot,97.5), (boot>=0).mean()))
    print("   families  P %+.4f (%d/9)  Q %+.4f (%d/4)  R %+.4f (%d/5)   worst fold %.4f -> %.4f"
          % (fam.loc['P','mean'], fam.loc['P','<lambda_0>'], fam.loc['Q','mean'], fam.loc['Q','<lambda_0>'],
             fam.loc['R','mean'], fam.loc['R','<lambda_0>'], ps.base.max(), ps.candidate.max()))
    print("   dispersion ratio %.4f (reference %.4f)"
          % (amp(s,'pred')/amp(s,'y'), amp(ref,'pred')/amp(ref,'y')))
    print("   mean weight  " + "  ".join("%s %.3f" % (m, v) for m, v in zip(M, ws.mean(0))))
    print("   sd   weight  " + "  ".join("%s %.3f" % (m, v) for m, v in zip(M, ws.std(0))))
    print("   linear share (ridge+enet+ridge_e) %.3f  min across folds %.3f  max %.3f\n"
          % (ws[:, [1,2,3,4][1:]].sum(1).mean() if False else ws[:, [M.index('ridge'),M.index('enet'),M.index('ridge_e')]].sum(1).mean(),
             ws[:, [M.index('ridge'),M.index('enet'),M.index('ridge_e')]].sum(1).min(),
             ws[:, [M.index('ridge'),M.index('enet'),M.index('ridge_e')]].sum(1).max()))
    res["%.2f" % lam] = dict(mean=float(ps.candidate.mean()), delta=float(ps.delta.mean()),
        won=int((ps.delta<0).sum()), ci=[float(np.percentile(boot,2.5)), float(np.percentile(boot,97.5))],
        p_ge0=float((boot>=0).mean()), worst=float(ps.candidate.max()),
        families={k: [float(fam.loc[k,'mean']), int(fam.loc[k,'<lambda_0>']), int(fam.loc[k,'size'])] for k in 'PQR'},
        weights_mean=dict(zip(M, map(float, ws.mean(0)))), weights_sd=dict(zip(M, map(float, ws.std(0)))))
json.dump(res, open('outputs/shrink_eval.json','w'), indent=2)
