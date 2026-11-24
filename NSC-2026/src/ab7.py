"""A/B harness pinned to the v7 model configuration, with paired day-level bootstrap."""
import warnings; warnings.filterwarnings('ignore')
import sys, os, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
from common import *
import lightgbm as lgb

V7KW = dict(objective='huber', alpha=4.0, n_estimators=900, learning_rate=0.03, num_leaves=15,
            min_child_samples=25, subsample=0.8, subsample_freq=1, colsample_bytree=0.7,
            reg_lambda=3.0, verbose=-1)


def families(idx):
    def fam(n, val_days, step_days, min_train_days=30):
        d0, end, out = idx.min(), idx.max(), []
        for i in range(n):
            cut = end - pd.Timedelta(days=step_days * i)
            vs = cut - pd.Timedelta(days=val_days)
            if (vs - d0).days < min_train_days:
                break
            out.append((vs, cut))
        return out[::-1]
    return {'P': fam(9, 15, 2), 'Q': fam(6, 15, 3, 36), 'R': fam(5, 21, 3, 28)}


def run(F, y, is_tr, folds, seeds=(0, 1, 2), kw=None):
    kw = kw or V7KW
    tr = is_tr & y.notna()
    IDX = F.index
    out = []
    for fi, (vs, ve) in enumerate(folds):
        v = tr & (IDX > vs) & (IDX <= ve)
        t = tr & (IDX <= vs)
        p = np.mean([lgb.LGBMRegressor(random_state=s, **kw).fit(F[t], y[t]).predict(F[v])
                     for s in seeds], 0)
        out.append(pd.DataFrame(dict(fold=fi, dt=IDX[v], y=y[v].values, p=np.clip(p, 5, 100))))
    D = pd.concat(out, ignore_index=True)
    D['se'] = (D.p - D.y) ** 2
    return D


def report(name, Ds, refs=None, nboot=4000):
    means = {}
    line = f"{name:26s}"
    for fam, D in Ds.items():
        pf = D.groupby('fold').apply(lambda d: rmse(d.y, d.p))
        means[fam] = float(pf.mean())
        line += f" {fam} {pf.mean():6.3f}/{pf.max():6.3f}"
    avg = float(np.mean(list(means.values())))
    line += f"  avg {avg:6.3f}"
    res = dict(name=name, means=means, avg=avg)
    if refs is not None:
        D, R = Ds['P'], refs['P']
        m = R[['fold', 'dt', 'se']].rename(columns={'se': 'se_r'}).merge(
            D[['fold', 'dt', 'se']], on=['fold', 'dt'])
        m['day'] = m.dt.dt.date
        dd = m.groupby(['fold', 'day']).agg(se_r=('se_r', 'mean'), se=('se', 'mean')).reset_index()
        a, b = dd.se.values, dd.se_r.values
        rng = np.random.default_rng(0)
        n = len(dd)
        diffs = np.empty(nboot)
        for i in range(nboot):
            s = rng.integers(0, n, n)
            diffs[i] = np.sqrt(a[s].mean()) - np.sqrt(b[s].mean())
        pf = D.groupby('fold').apply(lambda d: rmse(d.y, d.p))
        pr = R.groupby('fold').apply(lambda d: rmse(d.y, d.p))
        res.update(delta=float(np.sqrt(a.mean()) - np.sqrt(b.mean())),
                   folds_won=int((pf.values < pr.values).sum()), n_folds=len(pf),
                   ci=[float(np.percentile(diffs, 2.5)), float(np.percentile(diffs, 97.5))],
                   p_better=float((diffs < 0).mean()))
        line += (f" | d {res['delta']:+.3f} CI[{res['ci'][0]:+.3f},{res['ci'][1]:+.3f}]"
                 f" {res['folds_won']}/{res['n_folds']} P{res['p_better'] * 100:.0f}%")
    print(line, flush=True)
    return res
