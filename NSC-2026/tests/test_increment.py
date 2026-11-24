"""Checks for the session-21 increment reconciliation.

These cover the three things that would silently ruin the candidate: a difference that
straddles a hole in the index, a training pair whose earlier endpoint sits after the
forecast origin, and a design matrix that has picked up the target. The reconciliation
algebra is checked against a dense solve rather than against itself.
"""
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import final_pipeline as fp


class Operator(unittest.TestCase):
    def test_contiguous_block_differences_by_h(self):
        idx = pd.date_range('2023-08-01', periods=20, freq='30min')
        for h in (1, 4, 12):
            D, stamps = fp.diff_operator(idx, h)
            self.assertEqual(D.shape, (20 - h, 20))
            self.assertTrue((stamps == idx[h:]).all())
            z = np.arange(20, dtype=float)
            np.testing.assert_allclose(D @ z, np.full(20 - h, float(h)))

    def test_hole_produces_no_row_instead_of_a_wrong_one(self):
        full = pd.date_range('2023-08-01', periods=10, freq='30min')
        idx = full.delete(4)                       # one missing half hour
        D, stamps = fp.diff_operator(idx, 1)
        # Eight remaining timestamps could be the later end of a one-step pair; the two
        # that neighbour the hole cannot.
        self.assertEqual(D.shape[0], 7)
        self.assertNotIn(full[5], set(stamps))
        z = (idx - idx[0]).total_seconds().to_numpy() / 1800.0
        np.testing.assert_allclose(D @ z, np.ones(7))

    def test_no_pairs_at_all_is_survivable(self):
        idx = pd.DatetimeIndex(['2023-08-01 00:00', '2023-08-02 00:00'])
        D, stamps = fp.diff_operator(idx, 1)
        self.assertIsNone(D)
        self.assertEqual(len(stamps), 0)


class Solve(unittest.TestCase):
    """`reconcile` is a least-squares problem with a closed form; check the sparse solve
    against a dense one built independently from the definition."""

    def setUp(self):
        rng = np.random.default_rng(0)
        self.idx = pd.date_range('2023-08-01', periods=48, freq='30min')
        self.p = 50 + 10 * rng.standard_normal(48)
        self.d = {h: rng.standard_normal(48 - h) for h, _ in fp.INC_SPEC}

    def _dense(self):
        n = len(self.p)
        A = np.eye(n)
        b = self.p.copy()
        for h, lam in fp.INC_SPEC:
            D = np.zeros((n - h, n))
            for k in range(n - h):
                D[k, k], D[k, k + h] = -1.0, 1.0
            A += lam * D.T @ D
            b += lam * D.T @ self.d[h]
        return np.linalg.solve(A, b)

    def test_matches_a_dense_least_squares_solve(self):
        class Fixed:
            def __init__(self, v):
                self.v = v

            def predict(self, X):
                return self.v

        inc = {h: [Fixed(self.d[h])] for h, _ in fp.INC_SPEC}
        F = pd.DataFrame({c: 0.0 for c in fp.INC_COLS}, index=self.idx)
        got = fp.reconcile(self.p, self.idx, F, inc)
        np.testing.assert_allclose(got, np.clip(self._dense(), 5, 100), atol=1e-8)

    def test_the_solve_cannot_change_the_overall_level(self):
        """Every row of D sums to zero, so 1'D' = 0 and 1'(I + sum lam D'D) = 1'. The mean
        of the reconciled path therefore equals the mean of the level prediction exactly.
        That matters: sections 6, 35 and 46 all tried and rejected a global offset, and this
        change is guaranteed to be a shape correction rather than another attempt at one."""
        class Noisy:
            def __init__(self, n):
                self.rng = np.random.default_rng(7)
                self.n = n

            def predict(self, X):
                return 5 * self.rng.standard_normal(len(X))

        inc = {h: [Noisy(len(self.p))] for h, _ in fp.INC_SPEC}
        F = pd.DataFrame({c: 0.0 for c in fp.INC_COLS}, index=self.idx)
        z = fp.reconcile(self.p, self.idx, F, inc)
        self.assertGreater(np.abs(z - self.p).max(), 0.5)     # it did move the path
        self.assertAlmostEqual(z.mean(), self.p.mean(), places=10)

    def test_zero_increments_pull_the_path_flat_not_toward_the_level(self):
        """The control from progress.md s147: feeding zeros is smoothing, and it must be a
        different answer from the level itself, otherwise the solve is doing nothing."""
        class Zero:
            def predict(self, X):
                return np.zeros(len(X))

        inc = {h: [Zero()] for h, _ in fp.INC_SPEC}
        F = pd.DataFrame({c: 0.0 for c in fp.INC_COLS}, index=self.idx)
        flat = fp.reconcile(self.p, self.idx, F, inc)
        self.assertGreater(np.abs(flat - self.p).max(), 1.0)
        self.assertLess(flat.std(), self.p.std())


class Leakage(unittest.TestCase):
    """The slow ones: they build the real grid once and share it."""

    @classmethod
    def setUpClass(cls):
        cls.g = fp.load_grid()
        cls.F = fp.make_features(cls.g)
        cls.y = cls.g[fp.TARGET]
        cls.idx = cls.F.index
        cls.tr = pd.Series((cls.g.is_test == 0).values & cls.y.notna().values,
                           index=cls.idx)

    def test_design_carries_no_target_column(self):
        for h, _ in fp.INC_SPEC:
            cols = list(fp.inc_design(self.F, h).columns)
            self.assertNotIn(fp.TARGET, cols)
            self.assertEqual(len(cols), len(set(cols)))

    def test_design_is_identical_when_the_target_is_wiped(self):
        g2 = self.g.copy()
        g2[fp.TARGET] = np.nan
        Fb = fp.make_features(g2)[self.F.columns]
        for h, _ in fp.INC_SPEC:
            a, b = fp.inc_design(self.F, h), fp.inc_design(Fb, h)
            self.assertEqual(list(a.columns), list(b.columns))
            for c in a.columns:
                self.assertTrue(np.array_equal(a[c].values, b[c].values, equal_nan=True), c)

    def test_both_endpoints_of_every_training_difference_precede_the_origin(self):
        origin = pd.Timestamp('2023-08-01 00:00')
        mask = self.tr & (self.idx <= origin)
        for h, _ in fp.INC_SPEC:
            X = fp.inc_design(self.F, h)
            tgt = (self.y - self.y.shift(h)).reindex(X.index)
            m = mask.reindex(X.index, fill_value=False)
            m = m & tgt.notna() & m.shift(h, fill_value=False)
            used = X.index[m]
            self.assertGreater(len(used), 500)
            self.assertLessEqual(used.max(), origin)
            earlier = used - pd.Timedelta(minutes=30 * h)
            self.assertLessEqual(earlier.max(), origin)
            self.assertTrue(mask.reindex(earlier).all())

    def test_fitted_models_never_see_a_label_after_the_origin(self):
        """A stronger form of the check above: change every label after the origin and the
        fitted increment predictions must not move at all."""
        origin = pd.Timestamp('2023-08-01 00:00')
        mask = self.tr & (self.idx <= origin)
        later = self.idx[self.idx > origin]
        y2 = self.y.copy()
        y2.loc[later] += 10.0
        a = fp.fit_increments(self.F, self.y, mask)
        b = fp.fit_increments(self.F, y2, mask)
        block = self.idx[(self.idx > origin)][:200]
        for h, _ in fp.INC_SPEC:
            X = fp.inc_design(self.F, h).loc[block]
            np.testing.assert_array_equal(a[h][0].predict(X), b[h][0].predict(X))


if __name__ == '__main__':
    unittest.main(verbosity=2)
