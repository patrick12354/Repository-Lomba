"""Session 7 analysis: why improving a blend member made the blend worse.

Step 6 produced the sharpest negative in this log. CatBoost with plain MAE scores 0.918
better than the shipped Huber member on family P, 7/9 folds, and the same swap costs the
blend +0.106. Something is being paid for that is not accuracy.

The hypothesis is that the shipped `cat` earns its weight by being WRONG DIFFERENTLY from
`hbt`, and that fixing its loss moves it toward `hbt`'s behaviour, spending the diversity
to buy accuracy the blend already had. This scores every cached model on three axes --
solo RMSE, residual correlation with `hbt`, and what it does to the blend when added --
and checks which of the first two predicts the third.
"""
import pickle
import numpy as np, pandas as pd
from scipy.optimize import nnls
import h7

CACHE = pickle.load(open(h7.CACHE, 'rb'))
SEEDS = (0, 1, 2)
LOADED = h7.load()


def frame(models, fam):
    F, y, is_tr, g = LOADED
    IDX, tr = F.index, is_tr.values
    rows = []
    for fi, (vs, ve) in enumerate(h7.families(IDX[tr])[fam]):
        v = tr & (IDX > vs) & (IDX <= ve)
        t = tr & (IDX <= vs)
        if t.sum() < 300 or v.sum() < 50:
            continue
        keys = [(fam, fi, m, '', SEEDS) for m in models]
        if any(k not in CACHE for k in keys):
            return None
        d = pd.DataFrame(dict(fold=fi, dt=IDX[v], y=y[v].values))
        for m, k in zip(models, keys):
            d[m] = CACHE[k]
        rows.append(d)
    return pd.concat(rows, ignore_index=True)


def nested_avg(models):
    means, folds = {}, []
    for fam in ('P', 'Q', 'R'):
        D = frame(models, fam)
        if D is None:
            return None
        per = []
        for k in sorted(D.fold.unique()):
            prev, cur = D[D.fold < k], D[D.fold == k]
            if len(prev) == 0:
                continue
            w, _ = nnls(prev[models].values, prev.y.values)
            w = w / w.sum() if w.sum() > 0 else np.ones(len(models)) / len(models)
            w = 0.75 * w + 0.25 * np.ones(len(models)) / len(models)
            per.append(h7.rmse(cur.y, cur[models].values @ w))
        means[fam] = float(np.mean(per))
        folds += [float(x) for x in per]
    return dict(avg=float(np.mean(list(means.values()))), means=means, folds=folds)


base = nested_avg(h7.BASE)
P = frame(h7.BASE, 'P')
rh = P['hbt'].values - P.y.values

models = sorted({k[2] for k in CACHE} - set(h7.BASE))
rows = []
for m in models:
    D = frame(['hbt', m], 'P')
    if D is None:
        continue
    solo = float(np.mean([h7.rmse(d.y, d[m]) for _, d in D.groupby('fold')]))
    corr = float(np.corrcoef(D[m].values - D.y.values, D['hbt'].values - D.y.values)[0, 1])
    add = nested_avg(h7.BASE + [m])
    swap = nested_avg([x for x in h7.BASE if x != 'cat'] + [m])
    rows.append(dict(model=m, solo_P=solo, corr_hbt=corr,
                     d_add=add['avg'] - base['avg'] if add else np.nan,
                     d_swap_cat=swap['avg'] - base['avg'] if swap else np.nan))

# the shipped members, for reference on the same axes
for m in h7.BASE:
    D = frame(['hbt', m], 'P') if m != 'hbt' else P
    solo = float(np.mean([h7.rmse(d.y, d[m]) for _, d in D.groupby('fold')]))
    corr = 1.0 if m == 'hbt' else float(
        np.corrcoef(D[m].values - D.y.values, D['hbt'].values - D.y.values)[0, 1])
    drop = nested_avg([x for x in h7.BASE if x != m])
    rows.append(dict(model=f'[{m}]', solo_P=solo, corr_hbt=corr, d_add=np.nan,
                     d_swap_cat=np.nan, d_drop=drop['avg'] - base['avg']))

T = pd.DataFrame(rows).sort_values('d_add')
print(f'baseline blend avg {base["avg"]:.4f}\n')
print('every cached model on three axes (family P for solo/corr, all three for the deltas):')
print(T.to_string(index=False, float_format=lambda x: f'{x:+.4f}'))

V = T[T.d_add.notna()]
print(f'\nacross {len(V)} candidates:')
print(f'  corr(solo RMSE, blend delta)      = {np.corrcoef(V.solo_P, V.d_add)[0,1]:+.3f}')
print(f'  corr(residual corr, blend delta)  = {np.corrcoef(V.corr_hbt, V.d_add)[0,1]:+.3f}')
sane = V[V.solo_P < 9]
print(f'  the same, excluding the 4 broken models (solo > 9): n={len(sane)}')
print(f'  corr(solo RMSE, blend delta)      = {np.corrcoef(sane.solo_P, sane.d_add)[0,1]:+.3f}')
print(f'  corr(residual corr, blend delta)  = {np.corrcoef(sane.corr_hbt, sane.d_add)[0,1]:+.3f}')
T.to_csv('outputs/an06_axes.csv', index=False)
