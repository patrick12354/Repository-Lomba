"""Session 36, Task 1: a smooth level backbone with the incumbent tree fitted on its residual.

    g = backbone(X_small, y)          low-dimensional, smooth, fitted on the prefix
    r = y - g(X_small)                residual on the SAME training rows
    h = mean_s hbt_s(F, r)            the incumbent member, five incumbent seeds
    q = g(X_small) + h(F)             one estimator, two stages

**Why this and not another feature block.** Sessions 33-35 added information (shape features),
changed how increment error is penalised (geometry loss), and tried to import level information
from historical episodes (analog transport). All three failed. What none of them changed is the
SHAPE of the level estimator: `hbt` must approximate a smooth global response to temperature and
ventilation through axis-aligned splits, spending capacity on a curve rather than on structure.
Giving it an explicit smooth offset divides that work. It is a hypothesis about estimator
structure, not a diagnosis of a measured error.

**Why this is not the residual fitting that already failed.** `an_residstruct2` and the slow-member
work fitted a second model to the residual of an out-of-fold PREDICTION -- a meta model on
validation residuals, which is scarce and leaks easily. Here the residual is in-sample on the
training rows of one estimator, exactly as boosting fits stage two on stage one's residual, and
both stages are refitted from scratch at every origin. `an49`'s spline was on the INCREMENT with a
constant-vapour offset; this one is on the RH level directly with no physical equation imposed.

**What is frozen before any score is read.** Eight drivers plus four harmonics, four knots, cubic
degree, quantile knots, constant extrapolation, ridge penalty 0.01, two named tensor interactions,
`fp.LGB_KW` untouched, five incumbent seeds. There is no grid over any of these. The backbone is
an additive offset only -- it is never handed to the tree as a feature -- and neither `g` nor the
residual is clipped; only the final `q` is clipped, on the same bounds as the control member.
"""
import hashlib
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.preprocessing import SplineTransformer

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
import final_pipeline as fp

KINDS = ('linear', 'additive', 'pairwise')
DRIVERS = ('T', 'T_min48', 'T_rng48', 'air_temperature_a24h',
           'co2_c24h', 'co2_a24h', 'co2_slope', 'pressure_a24h')
HARMONICS = ('sin1', 'cos1', 'sin2', 'cos2')
INTERACTIONS = (('T', 'T_min48'), ('T', 'co2_c24h'))
N_KNOTS = 4
DEGREE = 3
RIDGE_LAMBDA = 0.01          # penalty on mean squared error; see `_ridge_alpha`
MIN_UNIQUE = 4               # fewer distinct finite values than this -> linear term, recorded
DROP_SD = 1e-8
CLIP = (5.0, 100.0)


def required_columns():
    return list(DRIVERS) + list(HARMONICS)


def assert_columns(F):
    missing = [c for c in required_columns() if c not in F.columns]
    assert not missing, 'backbone columns absent from the feature frame: %r' % (missing,)


def _ridge_alpha(n):
    """`mean(resid^2) + RIDGE_LAMBDA * sum(beta^2)` is sklearn's `sum(resid^2) + alpha*sum(beta^2)`
    with `alpha = RIDGE_LAMBDA * n`."""
    return RIDGE_LAMBDA * n


class LevelHybrid:
    """`fit(F, y, train_idx)` then `predict(F, idx)`. One object per origin; nothing is shared."""

    def __init__(self, kind):
        assert kind in KINDS, 'unknown backbone kind %r; expected one of %r' % (kind, KINDS)
        self.kind = kind
        self.fitted_ = False

    # ------------------------------------------------------------------ backbone basis
    def _fit_basis(self, X):
        """One spline transformer per driver, or a centered linear term where support is thin."""
        self.medians_ = X.median()
        self.spline_, self.fallback_ = {}, []
        if self.kind == 'linear':
            return
        Xi = X.fillna(self.medians_)
        for d in DRIVERS:
            v = Xi[d].to_numpy(float)
            if len(np.unique(v[np.isfinite(v)])) < MIN_UNIQUE:
                self.fallback_.append(d)
                continue
            st = SplineTransformer(n_knots=N_KNOTS, degree=DEGREE, knots='quantile',
                                   include_bias=False, extrapolation='constant')
            st.fit(v.reshape(-1, 1))
            self.spline_[d] = st

    def _basis(self, X):
        """The design matrix before standardisation, with a stable column order."""
        Xi = X.fillna(self.medians_)
        parts, names = [], []
        for d in DRIVERS:
            if self.kind == 'linear' or d in self.fallback_:
                parts.append(Xi[[d]].to_numpy(float) - float(self.medians_[d]))
                names.append('lin_%s' % d)
            else:
                B = self.spline_[d].transform(Xi[[d]].to_numpy(float))
                parts.append(B)
                names.extend('sp_%s_%d' % (d, k) for k in range(B.shape[1]))
        for h in HARMONICS:
            parts.append(Xi[[h]].to_numpy(float))
            names.append('h_%s' % h)
        if self.kind == 'pairwise':
            for a, b in INTERACTIONS:
                Ba = self._driver_basis(Xi, a)
                Bb = self._driver_basis(Xi, b)
                T = (Ba[:, :, None] * Bb[:, None, :]).reshape(len(Xi), -1)
                parts.append(T)
                names.extend('tx_%s_%s_%d' % (a, b, k) for k in range(T.shape[1]))
        M = np.hstack(parts)
        assert M.shape[1] == len(names)
        return M, names

    def _driver_basis(self, Xi, d):
        if d in self.spline_:
            return self.spline_[d].transform(Xi[[d]].to_numpy(float))
        return Xi[[d]].to_numpy(float) - float(self.medians_[d])

    # ------------------------------------------------------------------ fit / predict
    def fit(self, F, y, train_idx):
        """Both stages, on the training rows only. `y` is read at `train_idx` and nowhere else."""
        assert_columns(F)
        train_idx = pd.DatetimeIndex(train_idx)
        X = F.loc[train_idx, required_columns()]
        yt = np.asarray(y.reindex(train_idx), float)
        assert np.isfinite(yt).all(), 'the backbone needs a label on every training row'

        self._fit_basis(X)
        M, names = self._basis(X)
        self.mean_ = M.mean(axis=0)
        sd = M.std(axis=0)
        self.keep_ = sd > DROP_SD
        assert self.keep_.any(), 'every basis column is constant on the training rows'
        self.sd_ = np.where(self.keep_, sd, 1.0)
        self.names_ = [n for n, k in zip(names, self.keep_) if k]
        Z = ((M - self.mean_) / self.sd_)[:, self.keep_]

        self.ridge_ = Ridge(alpha=_ridge_alpha(len(train_idx)), fit_intercept=True).fit(Z, yt)
        self.g_train_ = self.ridge_.predict(Z)
        resid = yt - self.g_train_

        # Stage two: the incumbent member, on the incumbent frame, at the incumbent seeds.
        seeds = tuple(range(len(fp.SEEDS_FIT)))
        self.h_train_ = fp.predict('hbt', F.loc[train_idx], pd.Series(resid, index=train_idx),
                                   F.loc[train_idx], np.ones(len(train_idx)),
                                   pd.Series(resid, index=train_idx), seeds)
        self.train_idx_ = train_idx
        self.F_train_ = F.loc[train_idx]
        self.resid_train_ = resid
        self.y_train_ = yt
        self.fitted_ = True
        return self

    def backbone(self, F, idx):
        """`g` alone, unclipped. Diagnostic; never submitted on its own."""
        assert self.fitted_
        idx = pd.DatetimeIndex(idx)
        M, _names = self._basis(F.loc[idx, required_columns()])
        Z = ((M - self.mean_) / self.sd_)[:, self.keep_]
        return self.ridge_.predict(Z)

    def predict(self, F, idx):
        """`q = g + h`, clipped once on the control member's bounds."""
        assert self.fitted_
        idx = pd.DatetimeIndex(idx)
        g = self.backbone(F, idx)
        seeds = tuple(range(len(fp.SEEDS_FIT)))
        r = pd.Series(self.resid_train_, index=self.train_idx_)
        h = fp.predict('hbt', self.F_train_, r, F.loc[idx], np.ones(len(idx)), r, seeds)
        return np.clip(g + h, *CLIP), g, h

    # ------------------------------------------------------------------ provenance
    def digest(self):
        h = hashlib.md5()
        h.update(self.kind.encode())
        h.update('|'.join(self.names_).encode())
        h.update(np.ascontiguousarray(self.mean_, np.float64).tobytes())
        h.update(np.ascontiguousarray(self.sd_, np.float64).tobytes())
        h.update(np.ascontiguousarray(self.ridge_.coef_, np.float64).tobytes())
        h.update(np.asarray([self.ridge_.intercept_], np.float64).tobytes())
        return h.hexdigest()

    def info(self):
        return dict(kind=self.kind, n_basis=int(self.keep_.sum()),
                    n_dropped=int((~self.keep_).sum()), fallback=list(self.fallback_),
                    n_train=int(len(self.train_idx_)),
                    ridge_alpha=float(_ridge_alpha(len(self.train_idx_))),
                    rmse_g_train=float(np.sqrt(np.mean((self.y_train_ - self.g_train_) ** 2))),
                    rmse_q_train=float(np.sqrt(np.mean(
                        (self.y_train_ - self.g_train_ - self.h_train_) ** 2))),
                    digest=self.digest())


def control_hbt(F, y, train_idx, pred_idx):
    """`a76.fit_hbt` in this module's terms: the C0 member, for the `g = 0` equivalence test."""
    train_idx, pred_idx = pd.DatetimeIndex(train_idx), pd.DatetimeIndex(pred_idx)
    seeds = tuple(range(len(fp.SEEDS_FIT)))
    yt = y.reindex(train_idx)
    return np.clip(fp.predict('hbt', F.loc[train_idx], yt, F.loc[pred_idx],
                              np.ones(len(pred_idx)), yt, seeds), *CLIP)
