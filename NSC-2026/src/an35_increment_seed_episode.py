"""Session 21, step 4 of the session-20 recommendation: is the increment candidate stable
across seeds and across weather episodes, or did one lucky draw carry it?

The 6-hour horizon failed on the same screen the 30-minute and 2-hour ones passed, which
is a reminder that a dynamics model has a scale beyond which it stops helping. That is a
reason to ask whether the two surviving scales are themselves fragile.

This calls `final_pipeline.fit_increments` and `final_pipeline.reconcile` directly, so it
audits the code that will ship rather than a second copy of the same idea.

    .venv/Scripts/python.exe src/an35_increment_seed_episode.py
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import final_pipeline as fp

OUT = ROOT / 'outputs' / 'audit_v20'
SEEDS = [fp.INC_SEED + i for i in range(5)]


def main():
    g = fp.load_grid()
    F = fp.make_features(g)
    y = g[fp.TARGET]
    tr = pd.Series((g.is_test == 0).values & y.notna().values, index=g.index)

    cache = pd.read_pickle(OUT / 'predictions.pkl')
    cache = cache.loc[(cache['mode'] == 'past_only')
                      & cache.model.isin(['v12', 'v16', 'v20'])]

    rows, preds = [], []
    for (fam, k), group in cache.groupby(['family', 'fold']):
        base = group.loc[group.model == 'v20'].sort_values('datetime')
        vi = pd.DatetimeIndex(base.datetime)
        cut = vi.min() - pd.Timedelta(minutes=30)
        mask = tr & (g.index <= cut)

        # One fit per seed, reused across the three backbones: the increment models do not
        # depend on which level model they are reconciled against.
        single = {s: fp.fit_increments(F, y, mask, (s,)) for s in SEEDS}
        pooled = {h: [single[s][h][0] for s in SEEDS] for h, _ in fp.INC_SPEC}

        for name in ('v12', 'v16', 'v20'):
            b = group.loc[group.model == name].sort_values('datetime')
            assert np.array_equal(b.datetime.values, base.datetime.values)
            p = b.pred.to_numpy()
            per_seed = {s: fp.reconcile(p, vi, F, single[s]) for s in SEEDS}
            avg = fp.reconcile(p, vi, F, pooled)
            rec = dict(family=fam, fold=int(k), model=name, n=len(p),
                       base=fp.rmse(b.y, p), seed_avg5=fp.rmse(b.y, avg))
            for s in SEEDS:
                rec['seed_%d' % s] = fp.rmse(b.y, per_seed[s])
            # How far apart do the five reconciled paths sit from each other?
            stack = np.array([per_seed[s] for s in SEEDS])
            rec['path_sd_mean'] = float(stack.std(0, ddof=1).mean())
            rec['path_sd_max'] = float(stack.std(0, ddof=1).max())
            rows.append(rec)
            d = b[['family', 'fold', 'datetime', 'origin', 'model', 'y']].copy()
            d['base'], d['increment'] = p, per_seed[fp.INC_SEED]
            d['increment_avg5'] = avg
            preds.append(d)
        print(fam, k, 'done', flush=True)

    r = pd.DataFrame(rows)
    seed_cols = ['seed_%d' % s for s in SEEDS]
    for c in seed_cols + ['seed_avg5']:
        r['d_' + c] = r[c] - r.base
    r.to_csv(OUT / 'increment_seed_scores.csv', index=False)
    P = pd.concat(preds, ignore_index=True)
    P.to_pickle(OUT / 'increment_seed_predictions.pkl')

    print('\nMEAN DELTA BY SEED (negative is better)')
    print(r.groupby('model')[['d_' + c for c in seed_cols + ['seed_avg5']]].mean().to_string())
    print('\nFOLDS IMPROVED, out of %d' % r.fold.nunique())
    print(r.groupby('model')[['d_' + c for c in seed_cols + ['seed_avg5']]]
          .apply(lambda d: (d < 0).sum()).to_string())

    summary = {}
    for name, d in r.groupby('model'):
        deltas = d[['d_' + c for c in seed_cols]].to_numpy()
        summary[name] = dict(
            base_mean=float(d.base.mean()),
            delta_mean_across_seeds=float(deltas.mean()),
            delta_best_seed=float(deltas.mean(0).min()),
            delta_worst_seed=float(deltas.mean(0).max()),
            delta_seed_sd=float(deltas.mean(0).std(ddof=1)),
            delta_avg5=float(d.d_seed_avg5.mean()),
            fold_seed_cells_improved=int((deltas < 0).sum()),
            fold_seed_cells=int(deltas.size),
            path_sd_mean=float(d.path_sd_mean.mean()),
            path_sd_max=float(d.path_sd_max.max()),
        )

    # Episode stability: one forecast per timestamp, latest eligible origin, then per day.
    print('\nPER-DAY DELTA, one forecast per timestamp')
    episodes = {}
    for name, d in P.groupby('model'):
        u = (d.sort_values(['origin', 'family', 'fold'])
             .drop_duplicates('datetime', keep='last').sort_values('datetime'))
        day = pd.DatetimeIndex(u.datetime).normalize()
        tab = u.assign(day=day).groupby('day').apply(
            lambda t: pd.Series(dict(n=len(t), base=fp.rmse(t.y, t.base),
                                     increment=fp.rmse(t.y, t.increment))))
        tab['delta'] = tab.increment - tab.base
        if name == 'v12':
            print(tab.to_string())
        episodes[name] = dict(
            unique_rows=int(len(u)),
            unique_base=fp.rmse(u.y, u.base),
            unique_increment=fp.rmse(u.y, u.increment),
            unique_increment_avg5=fp.rmse(u.y, u.increment_avg5),
            days=int(len(tab)), days_improved=int((tab.delta < 0).sum()),
            worst_day_delta=float(tab.delta.max()),
            best_day_delta=float(tab.delta.min()))
        tab.to_csv(OUT / ('increment_days_%s.csv' % name))
    for name in episodes:
        summary[name].update(episodes[name])
    (OUT / 'increment_seed_summary.json').write_text(json.dumps(summary, indent=2))
    print('\n' + json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
