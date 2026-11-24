"""Session 7, step 8: the blend composition and its shrinkage, re-scored from cache.

Step 7's drop-one ablation says the blend is carried by `hbt` (+0.369 when removed) and
`cat` (+0.109), while dropping `ridge` (-0.007) or `ridge_e` (-0.013) makes it slightly
BETTER. Meanwhile `BLEND_SHRINK = 0.25` pulls the NNLS weights a quarter of the way to
equal weighting, which forces 5 % of the blend onto each member whether it earns it or not.
That was tuned in section 22 on the v7 model set and never revisited.

Everything here re-scores predictions already in the cache, so it is seconds rather than
hours -- but that cheapness is also the danger. Scanning many subsets against the same
folds is exactly the selection-overfitting that section 38 caught, so the bar for adopting
anything is agreement across all three families plus a clear fold majority, not the best
average in the table.
"""
import itertools, json, pickle, sys
import numpy as np, pandas as pd
from scipy.optimize import nnls
import h7

CACHE = pickle.load(open(h7.CACHE, 'rb'))
SEEDS = (0, 1, 2)


def available():
    return sorted({k[2] for k in CACHE})


def frame(models, fam):
    """Assemble a family frame from cached predictions only."""
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


def score(models, shrink):
    """Nested NNLS at a given shrink. Returns (avg, per-family means, all fold scores)."""
    means, allf = {}, []
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
            w = (1 - shrink) * w + shrink * np.ones(len(models)) / len(models)
            per.append(h7.rmse(cur.y, cur[models].values @ w))
        means[fam] = float(np.mean(per))
        allf += [float(x) for x in per]
    return dict(avg=float(np.mean(list(means.values()))), means=means, folds=allf)


if __name__ == '__main__':
    LOADED = h7.load()
    print('cached models:', ' '.join(available()))

    base = score(h7.BASE, 0.25)
    print(f'\nreference: v8 blend, shrink 0.25 -> avg {base["avg"]:.4f}  '
          f'P {base["means"]["P"]:.3f} Q {base["means"]["Q"]:.3f} R {base["means"]["R"]:.3f}')

    print('\n-- shrink sweep, v8 model set unchanged:')
    for s in (0.0, 0.1, 0.25, 0.4, 0.6, 1.0):
        r = score(h7.BASE, s)
        won = sum(int(a < b) for a, b in zip(r['folds'], base['folds']))
        print(f'  shrink {s:4.2f}  avg {r["avg"]:.4f}  P {r["means"]["P"]:6.3f} '
              f'Q {r["means"]["Q"]:6.3f} R {r["means"]["R"]:6.3f}  '
              f'd {r["avg"]-base["avg"]:+.4f}  {won}/{len(r["folds"])}')

    print('\n-- subset x shrink, every subset that contains hbt:')
    pool = [m for m in h7.BASE]
    extra = [m for m in ('enet_a02', 'cat_rmse', 'lin') if m in available()]
    pool += extra
    print(f'   (pool = {" ".join(pool)})')
    rows = []
    for n in range(2, len(pool) + 1):
        for sub in itertools.combinations(pool, n):
            if 'hbt' not in sub:
                continue
            if 'enet' in sub and 'enet_a02' in sub:
                continue
            for s in (0.0, 0.1, 0.25):
                r = score(list(sub), s)
                if r is None:
                    continue
                won = sum(int(a < b) for a, b in zip(r['folds'], base['folds']))
                rows.append(dict(models=' '.join(sub), shrink=s, avg=r['avg'],
                                 **{f'{k}_mean': v for k, v in r['means'].items()},
                                 won=won, n=len(r['folds']),
                                 all_fams=int(all(r['means'][f] < base['means'][f]
                                                  for f in ('P', 'Q', 'R')))))
    T = pd.DataFrame(rows).sort_values('avg')
    print(f'\n   {len(T)} combinations scored. Top 15 by average:')
    print(T.head(15).to_string(index=False, float_format=lambda x: f'{x:.4f}'))
    print('\n   Top 10 among those that beat the reference in ALL THREE families:')
    S = T[T.all_fams == 1]
    print(S.head(10).to_string(index=False, float_format=lambda x: f'{x:.4f}')
          if len(S) else '   (none)')

    T.to_csv('outputs/exp41_grid.csv', index=False)
    json.dump(dict(base=base, best=T.iloc[0].to_dict()),
              open('outputs/exp41_res.json', 'w'), indent=1, default=float)
