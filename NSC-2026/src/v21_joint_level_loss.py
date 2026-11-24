"""Session 38, family E: one predictor supervised on both the level and its own changes.

G1/G2 (session 34) trained TWO increment models with a geometry-derived penalty, and the coupled
arm learned large errors that cancelled each other -- `d4 - sum of four d1` blew out from about
1.9 to 11. That is possible only because the two horizons are separate functions. Here there is
one function `f(X)` predicting the RH level, and the change penalty is applied to the changes OF
THAT SAME FUNCTION, so every implied increment is a difference of one potential and cannot drift
against a sibling model.

    r        = f(X_train) - y_train
    Q_beta   = I + beta * D1^T D1 + (beta/4) * D4^T D4
    L        = 0.5 * r^T Q_beta r
    grad     = Q_beta r

`beta = 0` is plain L2 and is the plumbing control `E00`: whatever the custom-objective path costs
relative to the built-in one, all three arms pay it equally, so `E01 - E00` and `E02 - E00` isolate
the change penalty. Session 34 established that this path is not bit-identical to the built-in
objective when `feature_fraction < 1` -- LightGBM draws different per-tree column subsets -- which
is exactly why E00 exists rather than comparing E01 against the incumbent directly.

**The Hessian.** LightGBM takes a per-row Hessian vector and `Q_beta` is not diagonal. The
majorizer `H_i = sum_j |Q_1[i,j]|` is computed once at `beta = 1` and shared by all three arms, so
a difference between arms is never a difference in step size. `|Q_beta| <= |Q_1|` elementwise for
`beta` in [0, 1], so `diag(H) - Q_beta` is positive semidefinite by Gershgorin for every arm here.

**Edges.** `D_h` has one row per pair of training timestamps exactly `h` half-hours apart, so no
difference is ever taken across a hole, and both endpoints are labelled training rows. Nothing
after the origin enters the operator, the offset or the fit.
"""
import hashlib
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import lightgbm as lgb
from scipy.sparse import identity

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
import final_pipeline as fp

HORIZON_WEIGHT = {1: 1.0, 4: 0.25}      # beta and beta/4, from section 5 of the plan
BETAS = (0.0, 0.25, 1.0)


def build_Q(index, beta, horizons=HORIZON_WEIGHT):
    """`I + beta*D1'D1 + (beta/4)*D4'D4` on the labelled training index."""
    index = pd.DatetimeIndex(index)
    assert index.is_monotonic_increasing and not index.has_duplicates
    Q = identity(len(index), format='csc')
    ops = {}
    for h, w in horizons.items():
        D, _stamps = fp.diff_operator(index, h)
        if D is None:
            continue
        ops[h] = D
        if beta:
            Q = (Q + (beta * w) * (D.T @ D)).tocsc()
    return Q.tocsr(), ops


def majorizer(index, horizons=HORIZON_WEIGHT):
    """`H_i = sum_j |Q_1[i,j]|` -- computed at beta=1 and shared by every arm."""
    Q1, _ops = build_Q(index, 1.0, horizons)
    H = np.asarray(np.abs(Q1).sum(axis=1)).ravel()
    assert (H > 0).all() and np.isfinite(H).all()
    return H


class JointLevelModel:
    """Fit once, predict many. Holds the boosters and the explicit mean offset."""

    def __init__(self, beta, seeds, params=None, rounds=None):
        assert beta in BETAS or beta >= 0.0, beta
        self.beta = float(beta)
        self.seeds = tuple(seeds)
        kw = dict(params or fp.LGB_KW)
        kw.pop('alpha', None)              # the Huber delta has no meaning under a custom loss
        self.rounds = int(rounds if rounds is not None else kw.pop('n_estimators', 900))
        kw.pop('n_estimators', None)
        kw.pop('objective', None)
        self.kw = kw
        self.boosters_ = None
        self.offset_ = None
        self.log_ = []

    def _native(self, seed):
        alias = {'learning_rate': 'learning_rate', 'num_leaves': 'num_leaves',
                 'min_child_samples': 'min_data_in_leaf', 'reg_lambda': 'lambda_l2',
                 'colsample_bytree': 'feature_fraction', 'subsample': 'bagging_fraction',
                 'subsample_freq': 'bagging_freq', 'verbose': 'verbosity'}
        out = {}
        for k, v in self.kw.items():
            if k not in alias:
                raise KeyError('no native mapping for %r; add it deliberately' % k)
            out[alias[k]] = v
        out.update(objective=None, seed=seed, num_threads=0, feature_pre_filter=False)
        return out

    def fit(self, X, y, index, log_every=50):
        index = pd.DatetimeIndex(index)
        yv = np.asarray(y, float)
        assert np.isfinite(yv).all() and len(yv) == len(X) == len(index)
        Q, ops = build_Q(index, self.beta)
        H = majorizer(index)
        scale = float(H.mean())
        Hs = H / scale
        self.offset_ = float(yv.mean())
        self.scale_ = scale
        self.n_edges_ = {h: int(D.shape[0]) for h, D in ops.items()}

        self.boosters_ = []
        for seed in self.seeds:
            ds = lgb.Dataset(X, label=yv, init_score=np.full(len(yv), self.offset_),
                             free_raw_data=False).construct()
            b = lgb.Booster(params=self._native(seed), train_set=ds)
            state = {'i': 0}

            def fobj(preds, _d, _st=state, _Q=Q, _H=Hs, _s=scale, _y=yv, _seed=seed):
                r = np.asarray(preds, float) - _y
                grad = np.asarray(_Q @ r).ravel() / _s
                assert np.isfinite(grad).all()
                _st['i'] += 1
                if _st['i'] % log_every == 0 or _st['i'] == 1:
                    self.log_.append(dict(seed=_seed, round=_st['i'],
                                          level_loss=float(0.5 * r @ r),
                                          change_loss=float(0.5 * (r @ (_Q @ r) - r @ r)),
                                          objective=float(0.5 * r @ (_Q @ r))))
                return grad, _H
            for _ in range(self.rounds):
                b.update(fobj=fobj)
            self.boosters_.append(b)
        return self

    def predict(self, X):
        assert self.boosters_ is not None, 'fit first'
        return np.mean([b.predict(X, raw_score=True) + self.offset_
                        for b in self.boosters_], axis=0)

    def digest(self):
        h = hashlib.md5()
        h.update(('beta=%.6f|rounds=%d|offset=%.12f|scale=%.12f'
                  % (self.beta, self.rounds, self.offset_, self.scale_)).encode())
        for b in self.boosters_ or []:
            h.update(b.model_to_string().encode())
        return h.hexdigest()

    def info(self):
        return dict(beta=self.beta, rounds=self.rounds, seeds=list(self.seeds),
                    offset=self.offset_, scale=self.scale_, n_edges=self.n_edges_,
                    trees=[b.num_trees() for b in self.boosters_ or []],
                    digest=self.digest())


def loss_and_grad(r, Q):
    r = np.asarray(r, float)
    grad = np.asarray(Q @ r).ravel()
    return float(0.5 * r @ grad), grad
