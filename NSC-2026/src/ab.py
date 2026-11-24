"""A/B harness with paired per-day bootstrap - sensitive enough to rank small changes."""
import warnings; warnings.filterwarnings('ignore')
import sys, os, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
from common import *
from screen import origins
import lightgbm as lgb

def HBT(s=0, **kw):
    d = dict(objective='huber', alpha=4.0, n_estimators=2500, learning_rate=0.01,
             num_leaves=31, min_child_samples=25, subsample=0.8, subsample_freq=1,
             colsample_bytree=1.0, reg_lambda=3., random_state=s, verbose=-1)
    d.update(kw); return lgb.LGBMRegressor(**d)

def run(F, y, is_tr, folds, mk=HBT, seeds=(0,)):
    tr = is_tr & y.notna(); IDX = F.index; out = []
    for fi, (vs, ve) in enumerate(folds):
        v = tr & (IDX > vs) & (IDX <= ve); t = tr & (IDX <= vs)
        ps = [np.asarray(mk(sd).fit(F[t], y[t]).predict(F[v])).ravel() for sd in seeds]
        out.append(pd.DataFrame(dict(fold=fi, dt=IDX[v], y=y[v].values,
                                     p=np.clip(np.mean(ps, axis=0), 5, 100))))
    D = pd.concat(out, ignore_index=True); D['se'] = (D.p - D.y) ** 2
    return D

def summarize(name, D, ref=None, nboot=4000):
    pf = D.groupby('fold').apply(lambda d: rmse(d.y, d.p))
    line = f"{name:30s} mean {pf.mean():6.3f} pooled {np.sqrt(D.se.mean()):6.3f} worst {pf.max():6.3f}"
    res = dict(name=name, mean=float(pf.mean()), pooled=float(np.sqrt(D.se.mean())),
               worst=float(pf.max()), folds=[round(x, 3) for x in pf.values])
    if ref is not None:
        m = ref[['fold','dt','se']].rename(columns={'se':'se_r'}).merge(
            D[['fold','dt','se']], on=['fold','dt'])
        m['day'] = m.dt.dt.date
        dd = m.groupby(['fold','day']).agg(se_r=('se_r','mean'), se=('se','mean')).reset_index()
        rng = np.random.default_rng(0); n = len(dd); diffs = np.empty(nboot)
        a, b = dd.se.values, dd.se_r.values
        for i in range(nboot):
            s = rng.integers(0, n, n)
            diffs[i] = np.sqrt(a[s].mean()) - np.sqrt(b[s].mean())
        pfr = ref.groupby('fold').apply(lambda d: rmse(d.y, d.p))
        res.update(delta=float(np.sqrt(a.mean()) - np.sqrt(b.mean())),
                   folds_won=int((pf.values < pfr.values).sum()), n_folds=len(pf),
                   days_won=float((a < b).mean()),
                   ci=[float(np.percentile(diffs,2.5)), float(np.percentile(diffs,97.5))],
                   p_better=float((diffs < 0).mean()))
        line += (f" | d {res['delta']:+.3f} CI[{res['ci'][0]:+.3f},{res['ci'][1]:+.3f}]"
                 f" folds {res['folds_won']}/{res['n_folds']} P {res['p_better']*100:.0f}%")
    print(line, flush=True)
    return res
