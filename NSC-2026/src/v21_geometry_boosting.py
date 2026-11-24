"""Session 34, Task 2: train the two increment learners against the solver's geometry.

`fp.fit_increments` fits one LightGBM per horizon against squared error on that horizon's own
rows. The two learners never see each other, and neither sees how its errors will be propagated.
This module keeps everything else identical -- same features, same mask, same targets, same
`INC_KW`, same five seeds, same 500 trees -- and changes only the gradient.

**Three modes.**

    l2_control   grad = r, hess = 1. The same schedule and the same plumbing as the geometry
                 arms, but the incumbent's objective. It is a CONTROL, not a candidate: if it
                 does not reproduce `fit_increments`, the difference between the geometry arms
                 and the incumbent is plumbing rather than objective.
    separate     Q_sep -- each horizon's error propagated through its own operator only.
    coupled      Q_full -- both horizons through the joint operator, so an error in the
                 30-minute model can be answered by the 2-hour model.

**The alternating schedule.** One booster per horizon per seed, never one model over stacked
rows. Each round updates h=1, refreshes its training error, then updates h=4 against the refreshed
error, then refreshes that. Exactly `N_ROUNDS` updates per horizon; a round that happens to grow
an empty tree is counted and kept, because stopping early would make the tree count depend on the
data in a way the incumbent's does not.

**Raw score and the mean offset.** `LGBMRegressor` with the built-in L2 objective starts boosting
from the label mean. A custom objective disables that, so the booster would start from zero and
spend its first trees rediscovering the mean. Each Dataset therefore carries an explicit
`init_score` of the training-target mean, and `predict` adds the same offset back. `l2_control`
exists to expose that convention rather than assume it away.

**Why `l2_control` is NOT bit-identical to `fp.fit_increments`, and what was done about it.**

The plan expected the two L2 paths to agree to 1e-5, treating any gap as round-off. They do not,
and the cause is not round-off. With `colsample_bytree = 0.8` LightGBM draws a different per-tree
FEATURE SUBSET on the custom-objective path than on the built-in one, and the divergence survives
pinning `feature_fraction_seed`, `bagging_seed`, `data_random_seed`, `extra_seed` and
`objective_seed`: tree 0 already uses different columns. At `feature_fraction = 1.0` the two paths
agree exactly -- 0.0 after one round, 8.8e-9 after five -- which is what identifies the cause.

Measured on B1 rather than argued: `l2_control` differs from `fit_increments` by at most 0.409
(h=1) and 0.633 (h=4) in increment prediction and moves the reconciled RMSE from 4.232249 to
4.227263, while `fit_increments` under a DIFFERENT seed set differs by 0.459 and 0.812 and moves
it to 4.234493. The plumbing gap is smaller than ordinary seed noise, so `l2_control` is an L2
model with a different random feature draw, not a broken one.

The consequence for the round, decided before any candidate was trained: `colsample_bytree` stays
at the shipped 0.8, and there are TWO controls. `C1` shares the plumbing and the RNG path with
G1/G2, so `G - C1` isolates the objective; `C0` is what actually ships, so `G - C0` is the
promotion gate. Both are reported, and `C1` is run under several seed sets so the size of the
plumbing noise is on the table and cannot be mistaken for a gain.
"""
import hashlib
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import lightgbm as lgb

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
import final_pipeline as fp
import v21_increment_geometry as ig

N_ROUNDS = fp.INC_KW['n_estimators']         # 500, taken from the incumbent, not chosen here
MODES = ig.MODES

# `INC_KW` is written for the sklearn wrapper. The native Booster takes the canonical names, and
# `n_estimators` is not a parameter there at all -- it is the number of `update()` calls. Mapping
# it explicitly, rather than passing the dict through and hoping the aliases resolve, is what
# `tests/test_v21_geometry_boosting.py::ParameterMapping` checks.
_ALIAS = {'learning_rate': 'learning_rate', 'num_leaves': 'num_leaves',
          'min_child_samples': 'min_data_in_leaf', 'reg_lambda': 'lambda_l2',
          'colsample_bytree': 'feature_fraction', 'verbose': 'verbosity'}


def native_params(seed, kw=None):
    kw = dict(kw or fp.INC_KW)
    kw.pop('n_estimators', None)
    kw.pop('objective', None)
    out = {}
    for k, v in kw.items():
        if k not in _ALIAS:
            raise KeyError('no native mapping for INC_KW[%r]; add it deliberately' % k)
        out[_ALIAS[k]] = v
    out.update(objective=None, seed=seed, deterministic=True, num_threads=0,
               feature_pre_filter=False)
    return out


class _SeedModel:
    """One horizon of one seed, exposing `.predict` so `a47.increment_terms` needs no change."""

    def __init__(self, booster, offset, columns):
        self.booster = booster
        self.offset = float(offset)
        self.columns = list(columns)

    def predict(self, X):
        X = X[self.columns] if hasattr(X, 'columns') else X
        return self.booster.predict(X, raw_score=True) + self.offset

    def to_dict(self):
        return dict(model=self.booster.model_to_string(), offset=self.offset,
                    columns=self.columns)

    @classmethod
    def from_dict(cls, d):
        return cls(lgb.Booster(model_str=d['model']), d['offset'], d['columns'])


def increment_targets(F, y, train_mask, horizons=fp.INC_SPEC):
    """Design matrices, targets and edge rows per horizon, exactly as `fit_increments` selects."""
    out = {}
    for h, _lam in horizons:
        X = fp.increment_design(F, h, fp.INC_COLS, False, False)
        tgt = (y - y.shift(h)).reindex(X.index)
        m = train_mask.reindex(X.index, fill_value=False)
        m = m & tgt.notna() & m.shift(h, fill_value=False)
        rows = X.index[m.to_numpy()]
        out[h] = dict(X=X.loc[rows], t=tgt.loc[rows].to_numpy(float), rows=rows)
    return out


def design_digest(parts):
    h = hashlib.md5()
    for hz in sorted(parts):
        d = parts[hz]
        h.update(str(hz).encode())
        h.update('|'.join(map(str, d['X'].columns)).encode())
        h.update(np.asarray(d['rows'].astype('int64')).tobytes())
        h.update(np.ascontiguousarray(d['t'], np.float64).tobytes())
    return h.hexdigest()


def fit_geometry_increments(F, y, train_mask, seeds, mode, geometry=None, rounds=N_ROUNDS,
                            horizons=fp.INC_SPEC, log=None):
    """The drop-in replacement for `fp.fit_increments`, with the objective as a parameter.

    Returns the same dict shape `a47.increment_terms` reads: `cols`, `physics`, `lags`, and a
    list of per-seed models under each horizon key. The solver path downstream is untouched.
    """
    assert mode in MODES, mode
    parts = increment_targets(F, y, train_mask, horizons)
    if mode != 'l2_control':
        if geometry is None:
            geometry = ig.build_geometry(
                train_mask.index[train_mask.to_numpy()],
                edges={h: parts[h]['rows'] for h, _ in horizons})
        for h, _lam in horizons:
            assert geometry.edges[h].equals(parts[h]['rows']), \
                'horizon %d: geometry edges and training rows are in different orders' % h

    out = {'cols': fp.INC_COLS, 'physics': False, 'lags': False,
           'mode': mode, 'rounds': rounds, 'design_digest': design_digest(parts)}
    records = []
    for h, _lam in horizons:
        out[h] = []
    for seed in seeds:
        boosters, offsets, datasets, r = {}, {}, {}, {}
        for h, _lam in horizons:
            d = parts[h]
            offsets[h] = float(np.mean(d['t']))
            ds = lgb.Dataset(d['X'], label=d['t'],
                             init_score=np.full(len(d['t']), offsets[h]),
                             free_raw_data=False).construct()
            datasets[h] = ds
            boosters[h] = lgb.Booster(params=native_params(seed), train_set=ds)
            r[h] = np.full(len(d['t']), 0.0)          # raw = offset at round 0 -> r = offset - t
            r[h] = offsets[h] - d['t']

        def make_fobj(h_cur):
            def fobj(preds, _ds):
                cur = np.asarray(preds, float) - parts[h_cur]['t']
                r[h_cur] = cur
                if mode == 'l2_control':
                    g = cur
                    hess = np.ones_like(cur)
                else:
                    full = np.concatenate([r[hz] for hz, _l in horizons])
                    g = geometry.grad(full, mode)[geometry.slice(h_cur)]
                    hess = geometry.hess()[geometry.slice(h_cur)]
                assert np.isfinite(g).all() and (hess > 0).all(), \
                    'non-finite gradient or non-positive hessian at horizon %d' % h_cur
                return g, hess
            return fobj

        fobjs = {h: make_fobj(h) for h, _lam in horizons}
        empty = {h: 0 for h, _lam in horizons}
        for it in range(rounds):
            for h, _lam in horizons:
                done = boosters[h].update(fobj=fobjs[h])
                if done:
                    empty[h] += 1
                # refresh this horizon's error so the next horizon sees the current one
                r[h] = boosters[h].predict(parts[h]['X'], raw_score=True) + offsets[h] \
                    - parts[h]['t']
        for h, _lam in horizons:
            out[h].append(_SeedModel(boosters[h], offsets[h], parts[h]['X'].columns))
            rec = dict(seed=seed, horizon=h, mode=mode, rounds=rounds,
                       trees=boosters[h].num_trees(), empty_rounds=empty[h],
                       offset=offsets[h], n_edges=len(parts[h]['t']),
                       rmse=float(np.sqrt(np.mean(r[h] ** 2))))
            if mode != 'l2_control':
                full = np.concatenate([r[hz] for hz, _l in horizons])
                rec['geometry_loss'] = geometry.loss(full, mode)
                rec['Br_mse'] = float(np.mean((geometry.B @ full) ** 2))
            records.append(rec)
            if log is not None:
                log.append(rec)
    out['records'] = records
    return out


def incumbent_increments(F, y, train_mask, seeds):
    """`fp.fit_increments` at the v21 configuration, for the C0 control."""
    return fp.fit_increments(F, y, train_mask, tuple(seeds),
                             physics=False, deshrink=False, lags=False)


def compare_predictions(inc_a, inc_b, F, idx, horizons=fp.INC_SPEC):
    """Max absolute difference between two increment dicts' seed-averaged targets."""
    out = {}
    for h, _lam in horizons:
        D, st = fp.diff_operator(pd.DatetimeIndex(idx), h)
        if D is None:
            continue
        X = fp.increment_design(F, h, fp.INC_COLS, False, False).loc[st]
        a = np.mean([m.predict(X) for m in inc_a[h]], axis=0)
        b = np.mean([m.predict(X) for m in inc_b[h]], axis=0)
        out[h] = float(np.max(np.abs(a - b)))
    return out
