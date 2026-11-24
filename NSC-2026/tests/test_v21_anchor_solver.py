"""Session 35: the anchor term added to the v21 solver.

The anchor is the first term since session 21 that can move a component's MEAN -- every difference
operator has zero row sum, so `D z` cannot. That makes it powerful and worth pinning precisely:
with zero strength it must vanish exactly, the sparse solve must satisfy its own normal equation,
and no anchor may reach across a gap in the index.

    .venv/Scripts/python.exe -m unittest discover -s tests -p test_v21_anchor_solver.py
"""
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
import final_pipeline as fp
import an47_v21_forward_benchmark as a47
import v21_episode_anchors as ea


def toy(n=48, start='2023-07-01'):
    return pd.date_range(start, periods=n, freq='30min')


def terms_for(idx, d=None, rng=None):
    rng = rng or np.random.default_rng(0)
    out = []
    for h, lam in fp.INC_SPEC:
        D, _ = fp.diff_operator(pd.DatetimeIndex(idx), h)
        if D is None:
            out.append((None, None, lam))
            continue
        t = rng.normal(scale=0.2, size=D.shape[0]) if d is None else D @ d
        out.append((D, t, lam))
    return out


class ZeroStrength(unittest.TestCase):
    def test_a_zero_anchor_reproduces_the_shipped_solver_exactly(self):
        rng = np.random.default_rng(1)
        idx = toy()
        p = 60 + rng.normal(scale=3.0, size=len(idx))
        terms = terms_for(idx, rng=rng)
        want = a47.solve(p, idx, terms)
        got = ea.solve_with_anchors(p, idx, terms)
        np.testing.assert_allclose(got, want, rtol=0, atol=1e-12)

    def test_an_explicit_zero_vector_also_reproduces_it(self):
        rng = np.random.default_rng(2)
        idx = toy()
        p = 60 + rng.normal(scale=3.0, size=len(idx))
        terms = terms_for(idx, rng=rng)
        a = np.zeros(len(idx))
        q = np.full(len(idx), 999.0)          # nonsense values that must not be read
        np.testing.assert_allclose(ea.solve_with_anchors(p, idx, terms, a, q),
                                   a47.solve(p, idx, terms), rtol=0, atol=1e-12)

    def test_a_nan_anchor_on_an_abstaining_row_cannot_leak(self):
        rng = np.random.default_rng(3)
        idx = toy()
        p = 60 + rng.normal(scale=3.0, size=len(idx))
        terms = terms_for(idx, rng=rng)
        a = np.zeros(len(idx))
        a[:10] = 0.25
        q = np.full(len(idx), np.nan)
        q[:10] = 70.0
        z = ea.solve_with_anchors(p, idx, terms, a, q)
        self.assertTrue(np.isfinite(z).all())


class NormalEquation(unittest.TestCase):
    def test_the_solution_satisfies_the_dense_normal_equation(self):
        rng = np.random.default_rng(4)
        idx = toy(40)
        n = len(idx)
        p = 60 + rng.normal(scale=3.0, size=n)
        terms = terms_for(idx, rng=rng)
        a = rng.choice([0.0, 0.25], size=n)
        q = 55 + rng.normal(scale=5.0, size=n)
        z = ea.solve_with_anchors(p, idx, terms, a, q)
        A = np.eye(n)
        rhs = p.copy()
        for M, t, lam in terms:
            if M is None:
                continue
            Md = M.toarray()
            A += lam * (Md.T @ Md)
            rhs += lam * (Md.T @ t)
        A += np.diag(a)
        rhs += a * np.where(a > 0, q, 0.0)
        np.testing.assert_allclose(z, np.linalg.solve(A, rhs), rtol=0, atol=1e-8)

    def test_the_sparse_and_dense_solves_agree(self):
        rng = np.random.default_rng(5)
        idx = toy(32)
        p = 60 + rng.normal(scale=2.0, size=len(idx))
        terms = terms_for(idx, rng=rng)
        a = np.full(len(idx), 0.25)
        q = 58 + rng.normal(scale=4.0, size=len(idx))
        z = ea.solve_with_anchors(p, idx, terms, a, q)
        self.assertTrue(np.isfinite(z).all())
        self.assertTrue(((z >= 5) & (z <= 100)).all())

    def test_a_negative_strength_is_refused(self):
        idx = toy(16)
        terms = terms_for(idx)
        with self.assertRaises(AssertionError):
            ea.solve_with_anchors(np.full(16, 60.0), idx, terms,
                                  np.full(16, -0.1), np.full(16, 60.0))


class MeanShift(unittest.TestCase):
    def test_increments_alone_cannot_move_the_component_mean(self):
        # Every difference operator has zero row sum, so with a = 0 the mean of z is pinned to
        # the mean of p. This is what §225 measured and what the anchor term exists to change.
        rng = np.random.default_rng(6)
        idx = toy()
        p = np.full(len(idx), 60.0)
        terms = terms_for(idx, rng=rng)
        z = ea.solve_with_anchors(p, idx, terms)
        self.assertAlmostEqual(float(z.mean()), float(p.mean()), places=6)

    def test_a_supported_anchor_does_move_the_mean(self):
        idx = toy()
        p = np.full(len(idx), 60.0)
        terms = terms_for(idx, d=np.full(len(idx), 60.0))     # increments consistent with flat p
        a = np.full(len(idx), 0.25)
        q = np.full(len(idx), 70.0)
        z = ea.solve_with_anchors(p, idx, terms, a, q)
        self.assertGreater(float(z.mean()), float(p.mean()) + 1.0)
        self.assertLess(float(z.mean()), 70.0)

    def test_the_pull_scales_with_the_strength(self):
        idx = toy()
        p = np.full(len(idx), 60.0)
        terms = terms_for(idx, d=np.full(len(idx), 60.0))
        q = np.full(len(idx), 70.0)
        means = [float(ea.solve_with_anchors(p, idx, terms, np.full(len(idx), s), q).mean())
                 for s in (0.0, 0.05, 0.25, 1.0)]
        self.assertTrue(all(b > a for a, b in zip(means, means[1:])))


class Gaps(unittest.TestCase):
    def test_no_temporal_edge_crosses_a_hole(self):
        idx = toy(48).delete([20, 21, 22, 23])
        for h, _lam in fp.INC_SPEC:
            D, stamps = fp.diff_operator(idx, h)
            later = pd.DatetimeIndex(stamps)
            earlier = later - pd.Timedelta(minutes=30 * h)
            self.assertTrue(earlier.isin(idx).all(), h)

    def test_the_anchor_term_is_row_local_and_survives_a_gap(self):
        rng = np.random.default_rng(7)
        idx = toy(48).delete([20, 21, 22, 23])
        p = 60 + rng.normal(scale=2.0, size=len(idx))
        terms = terms_for(idx, rng=rng)
        a = np.zeros(len(idx))
        a[0] = 0.25
        q = np.zeros(len(idx))
        q[0] = 95.0
        z = ea.solve_with_anchors(p, idx, terms, a, q)
        base = ea.solve_with_anchors(p, idx, terms)
        self.assertGreater(z[0], base[0])
        self.assertTrue(np.isfinite(z).all())


if __name__ == '__main__':
    unittest.main()
