"""Checks for the session-30 slow-member level correction.

The correction is only interpretable if `z + A^-1 B beta` really is what re-solving with the
extra right-hand side would give, and only honest if the smoothing never reaches across an
origin and the coefficients never see a heldout label. Those are the tests.

    .venv/Scripts/python.exe -m unittest discover -s tests -p test_v21_slow_member_correction.py
"""
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.sparse import identity
from scipy.sparse.linalg import spsolve

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
import final_pipeline as fp
import an47_v21_forward_benchmark as a47
import an70_v21_slow_member_correction as a70


def toy(n=192, seed=9):
    rng = np.random.default_rng(seed)
    idx = pd.date_range('2023-08-01', periods=n, freq='30min')
    level = 58 + 5 * rng.standard_normal(n)
    terms = []
    for h, lam in fp.INC_SPEC:
        D, _st = fp.diff_operator(idx, h)
        terms.append((D, rng.standard_normal(D.shape[0]) * 2, lam))
    A = identity(n, format='csc')
    rhs = level.copy()
    for M, t, lam in terms:
        A = (A + lam * (M.T @ M)).tocsc()
        rhs = rhs + lam * (M.T @ t)
    members = {m: level + rng.standard_normal(n) * (1 + i)
               for i, m in enumerate(a70.CONTRASTS)}
    return idx, level, members, A.tocsc(), rhs, terms


class Algebra(unittest.TestCase):
    def test_the_correction_equals_re_solving_with_the_extra_right_hand_side(self):
        """`z + A^-1 B beta` must be `A^-1 (rhs + B beta)`, or the fitted beta is optimising
        something the scorer never computes."""
        idx, level, members, A, rhs, _t = toy()
        B = a70.slow_contrasts(idx, level, members)
        z = spsolve(A, rhs)
        U = np.column_stack([spsolve(A, B[:, j]) for j in range(B.shape[1])])
        rng = np.random.default_rng(4)
        for _ in range(5):
            beta = rng.standard_normal(B.shape[1]) * 0.3
            np.testing.assert_allclose(z + U @ beta, spsolve(A, rhs + B @ beta), atol=1e-9)

    def test_zero_beta_reproduces_the_incumbent_exactly(self):
        idx, level, members, A, rhs, _t = toy()
        B = a70.slow_contrasts(idx, level, members)
        z = spsolve(A, rhs)
        U = np.column_stack([spsolve(A, B[:, j]) for j in range(B.shape[1])])
        np.testing.assert_array_equal(z + U @ np.zeros(B.shape[1]), z)
        np.testing.assert_allclose(np.clip(z, 5, 100),
                                   a47.solve(level, idx, _t), atol=1e-9)


class Smoothing(unittest.TestCase):
    def test_the_window_is_centred_twenty_four_hours_and_never_leaves_it(self):
        idx = pd.date_range('2023-08-01', periods=200, freq='30min')
        level = np.zeros(200)
        members = {m: np.zeros(200) for m in a70.CONTRASTS}
        members['hbt'] = np.where(np.arange(200) == 100, 100.0, 0.0)
        B = a70.slow_contrasts(idx, level, members)
        col = B[:, a70.CONTRASTS.index('hbt')]
        half = a70.SMOOTH_POINTS // 2
        self.assertTrue(np.all(col[:100 - half] == 0))
        self.assertTrue(np.all(col[100 + half + 1:] == 0))
        self.assertGreater(col[100], 0)
        # a centred mean puts the spike symmetrically around its own position
        np.testing.assert_allclose(col[100 - half], col[100 + half], atol=1e-12)

    def test_smoothing_never_crosses_an_origin(self):
        """Two windows scored separately must not leak into one another: the function is only
        ever handed one forecast's timestamps."""
        idx = pd.date_range('2023-08-01', periods=100, freq='30min')
        later = pd.date_range('2023-09-01', periods=100, freq='30min')
        lvl = np.zeros(100)
        a = {m: np.zeros(100) for m in a70.CONTRASTS}
        b = {m: np.zeros(100) for m in a70.CONTRASTS}
        b['hbt'] = np.full(100, 50.0)
        first = a70.slow_contrasts(idx, lvl, a)
        np.testing.assert_array_equal(first, np.zeros_like(first))
        second = a70.slow_contrasts(later, lvl, b)
        self.assertGreater(second[:, a70.CONTRASTS.index('hbt')].min(), 0)

    def test_a_gap_in_the_index_is_bridged_by_the_grid_not_by_row_position(self):
        """The window is 24 hours of clock time. Dropping rows must not silently make it 24
        hours of surviving observations."""
        full = pd.date_range('2023-08-01', periods=200, freq='30min')
        idx = full.delete(slice(60, 90))
        level = np.zeros(len(idx))
        members = {m: np.zeros(len(idx)) for m in a70.CONTRASTS}
        B = a70.slow_contrasts(idx, level, members)
        self.assertEqual(B.shape, (len(idx), len(a70.CONTRASTS)))
        self.assertTrue(np.isfinite(B).all())

    def test_a_constant_contrast_smooths_to_itself(self):
        idx = pd.date_range('2023-08-01', periods=120, freq='30min')
        level = np.zeros(120)
        members = {m: np.full(120, 3.0) for m in a70.CONTRASTS}
        B = a70.slow_contrasts(idx, level, members)
        np.testing.assert_allclose(B, np.full_like(B, 3.0), atol=1e-12)


def split(train_U, train_r, val_U, val_r):
    return dict(train_U=train_U, train_r=train_r, val_U=val_U, val_r=val_r,
                origin='x', n_train=len(train_r), n_val=len(val_r), train_label_end='x')


def part(origin, start, n=192, r=0.0, u=0.0):
    idx = pd.date_range(start, periods=n, freq='30min')
    return dict(idx=idx, origin=pd.Timestamp(origin), y=np.full(n, float(r)),
                z_pre=np.zeros(n), U=np.full((n, len(a70.CONTRASTS)), float(u)))


class Selection(unittest.TestCase):
    """Session 31 replaced the timestamp-chunk split with an origin replay; these assert the
    same behaviours against the new shape."""

    def test_zero_wins_when_the_basis_carries_no_signal(self):
        rng = np.random.default_rng(12)
        splits = [split(rng.standard_normal((200, 5)), rng.standard_normal(200),
                        rng.standard_normal((150, 5)), rng.standard_normal(150))
                  for _ in range(3)]
        alpha, table = a70.select_alpha(splits)
        self.assertIsNone(alpha)
        self.assertEqual(len(table), 1 + len(a70.ALPHAS))
        best = max(t['relative_gain_vs_zero'] for t in table if t['alpha'] is not None)
        self.assertLess(best, a70.SELECTION_MARGIN)

    def test_a_real_direction_beats_zero(self):
        rng = np.random.default_rng(13)
        beta = np.array([1.5, 0., 0., 0., 0.])
        splits = []
        for _ in range(3):
            tU, vU = rng.standard_normal((250, 5)), rng.standard_normal((150, 5))
            splits.append(split(tU, tU @ beta + 0.05 * rng.standard_normal(250),
                                vU, vU @ beta + 0.05 * rng.standard_normal(150)))
        alpha, t = a70.select_alpha(splits)
        self.assertIn(alpha, a70.ALPHAS)
        best = max(x['relative_gain_vs_zero'] for x in t if x['alpha'] is not None)
        self.assertGreater(best, 0.5)

    def test_too_little_calibration_yields_no_splits(self):
        self.assertEqual(a70.origin_splits([part('2023-07-31', '2023-08-01', n=50)]), [])

    def test_one_calibration_row_per_timestamp_keeping_the_latest_forecast(self):
        """Staggered windows, as the real inner folds are. Every timestamp survives once and
        the later origin wins where two windows cover it."""
        parts = [part('2023-08-%02d 00:00' % (1 + 2 * k),
                      '2023-08-%02d 00:00' % (2 + 2 * k), n=192, r=float(k), u=float(k))
                 for k in range(4)]
        got = a70.eligible_at(parts, pd.Timestamp('2023-09-01'))
        union = len(pd.DatetimeIndex(np.concatenate([q['idx'] for q in parts])).unique())
        self.assertEqual(len(got), union)
        self.assertEqual(got.dt.nunique(), union)
        self.assertAlmostEqual(float(got.r.max()), 3.0)

    def test_fully_overlapping_windows_collapse_to_one_origin_and_are_refused(self):
        """The B2 case: three windows on identical timestamps leave one window's worth of
        information after de-duplication."""
        parts = [part('2023-07-2%d 00:00' % k, '2023-08-01 00:00', n=400, r=float(k),
                      u=float(k)) for k in (0, 3, 5)]
        self.assertEqual(a70.origin_splits(parts), [])


class LabelIsolation(unittest.TestCase):
    def test_changing_a_heldout_label_changes_no_coefficient(self):
        """The calibration residual is built only from pre-origin rows, so perturbing the
        scored window must leave both beta and the selection untouched."""
        rng = np.random.default_rng(21)
        splits = []
        for _ in range(3):
            tU, vU = rng.standard_normal((250, 5)), rng.standard_normal((150, 5))
            b = np.array([0.8, 0, 0, 0, 0])
            splits.append(split(tU, tU @ b + 0.1 * rng.standard_normal(250),
                                vU, vU @ b + 0.1 * rng.standard_normal(150)))
        a_alpha, _ = a70.select_alpha(splits)
        U = np.vstack([sp['train_U'] for sp in splits])
        r = np.concatenate([sp['train_r'] for sp in splits])
        beta_a = a70.fit_beta(U, r, a_alpha).predict(np.eye(5))
        # a heldout window is simply not part of U or r; recomputing must be identical
        b_alpha, _ = a70.select_alpha(splits)
        beta_b = a70.fit_beta(U, r, b_alpha).predict(np.eye(5))
        self.assertEqual(a_alpha, b_alpha)
        np.testing.assert_array_equal(beta_a, beta_b)

    def test_the_ridge_has_no_intercept_so_zero_input_gives_zero_correction(self):
        rng = np.random.default_rng(22)
        U = rng.standard_normal((300, 5))
        model = a70.fit_beta(U, U @ np.array([1., 0, 0, 0, 0]) + 5.0, 100.0)
        np.testing.assert_allclose(model.predict(np.zeros((1, 5))), [0.0], atol=1e-12)


if __name__ == '__main__':
    unittest.main()


if __name__ == '__main__':
    unittest.main()
