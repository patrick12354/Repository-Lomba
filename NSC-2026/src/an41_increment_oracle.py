"""Session 24: how much is left in the mechanism that actually worked.

Section 162 measured the oracle ceiling for correcting the per-day LEVEL at -1.2357 and
section 163 showed it is unreachable -- leave-one-day-out R2 is negative from the sensors, and
the level error does not persist across the origin. That closed the biggest-looking route and
left the question of whether anything was left at all.

This asks the same oracle question about the mechanism that did work. The reconciliation takes
the increment models' predictions `d_h` as given. What if they were better? Substituting the
TRUE changes -- available on a holdout because both endpoints are labelled -- gives the ceiling
for improving the increment models, and substituting a blend of true and predicted gives the
conversion rate along the way.

The interpolation is `d = d_true + frac*(d_model - d_true)`, so `frac = 0.5` is an increment
model with exactly half the current error and the same bias structure. Nothing here is a
result that can be shipped; it prices a direction.

    .venv/Scripts/python.exe src/an41_increment_oracle.py
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.sparse import identity
from scipy.sparse.linalg import spsolve

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import final_pipeline as fp

OUT = ROOT / 'outputs' / 'audit_v20'
BACKBONE = 'v16'
FRACTIONS = [('shipped increment models', 1.0), ('three quarters of its error', 0.75),
             ('half its error', 0.5), ('a quarter of its error', 0.25),
             ('ORACLE increments', 0.0)]


def main():
    g = fp.load_grid()
    y = g[fp.TARGET]
    P = pd.read_pickle(OUT / 'increment_production_predictions.pkl')
    # B3 overlaps B1 and B2 and is excluded from anything meant as a measurement.
    P = P.loc[(P.model == BACKBONE) & (P.block != 'B3_shift7d')]
    seeds = tuple(fp.INC_SEED + i for i in range(fp.INC_SEEDS))

    rows = []
    for b, d in P.groupby('block'):
        d = d.sort_values('datetime')
        idx = pd.DatetimeIndex(d.datetime)
        hs, he = idx.min() - pd.Timedelta(minutes=30), idx.max()
        gh = g.loc[g.index <= he]
        F = fp.make_features(gh)
        yh = y.reindex(gh.index)
        mask = (pd.Series((gh.is_test == 0).to_numpy(), index=gh.index)
                & yh.notna() & (gh.index <= hs))
        inc = fp.fit_increments(F, yh, mask, seeds)
        truth, base = d.y.to_numpy(), d.base.to_numpy()
        ytrue = pd.Series(truth, index=idx)
        rows.append(dict(block=b, variant='no reconciliation', frac=None, n=len(idx),
                         rmse=fp.rmse(truth, base)))
        for label, frac in FRACTIONS:
            A = identity(len(idx), format='csc')
            rhs = base.astype(float).copy()
            for h, lam in fp.INC_SPEC:
                D, st = fp.diff_operator(idx, h)
                X = fp.inc_design(F, h).loc[st]
                dm = np.mean([m.predict(X) for m in inc[h]], axis=0)
                dt = (ytrue.reindex(st).to_numpy()
                      - ytrue.reindex(st - pd.Timedelta(minutes=30 * h)).to_numpy())
                dd = dt + frac * (dm - dt)
                A = (A + lam * (D.T @ D)).tocsc()
                rhs = rhs + lam * (D.T @ dd)
            rows.append(dict(block=b, variant=label, frac=frac, n=len(idx),
                             rmse=fp.rmse(truth, np.clip(spsolve(A, rhs), 5, 100))))
        print(b, 'done', flush=True)

    R = pd.DataFrame(rows)
    T = R.pivot(index='variant', columns='block', values='rmse')
    # Session 26. This column used to be named `pooled` while holding the MEAN of the
    # block RMSEs. Both are reported now, under names that say which is which: `pooled`
    # is sqrt(sum SSE / sum n), the primary metric of the session-26 contract.
    N = R.pivot(index='variant', columns='block', values='n').reindex(T.index)
    blocks = [c for c in T.columns if str(c).startswith('B')]
    T['mean_block_rmse'] = T[blocks].mean(axis=1)
    T['pooled'] = np.sqrt(sum((T[c] ** 2) * N[c] for c in blocks) / N[blocks].sum(axis=1))
    order = ['no reconciliation'] + [n for n, _ in FRACTIONS]
    T = T.reindex(order)
    T.to_csv(OUT / 'increment_oracle.csv')
    print('\n' + T.round(4).to_string())

    ship = float(T.loc['shipped increment models', 'pooled'])
    print('\n`pooled` is SSE-weighted over B1+B2; `mean_block_rmse` is what sections'
          ' 169 and 174 called pooled.')
    print('headroom from a better increment model: %+.4f to the oracle'
          % (float(T.loc['ORACLE increments', 'pooled']) - ship))
    print('halving the increment error already collects %+.4f of it'
          % (float(T.loc['half its error', 'pooled']) - ship))
    (OUT / 'increment_oracle.json').write_text(json.dumps(
        {'pooled': T.pooled.to_dict(), 'mean_block_rmse': T.mean_block_rmse.to_dict(),
         'headroom_to_oracle': float(T.loc['ORACLE increments', 'pooled']) - ship,
         'gain_if_error_halved': float(T.loc['half its error', 'pooled']) - ship},
        indent=2))


if __name__ == '__main__':
    main()
