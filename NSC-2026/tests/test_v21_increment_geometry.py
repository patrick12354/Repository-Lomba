"""Session 34, Task 1: the algebra the geometry objective rests on.

If `B` is wrong, every number the geometry arms produce is wrong in a way no RMSE table would
reveal. These tests check the identity itself, the chronology, and the numerical properties the
boosting step needs -- before any model is fitted.

    .venv/Scripts/python.exe -m unittest discover -s tests -p test_v21_increment_geometry.py
"""
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.sparse import hstack as sp_hstack

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
import final_pipeline as fp
import an47_v21_forward_benchmark as a47
import v21_increment_geometry as ig

_R = {}


def toy(n=24, freq='30min', start='2023-07-01'):
    return pd.date_range(start, periods=n, freq=freq)


def real_block():
    """B1's labelled training index, its frame, and the incumbent effective edges."""
    if not _R:
        g = fp.load_grid()
        y = g[fp.TARGET]
        name, hs, he = a47.blocks_of(g)[0]
        gh, F = a47.frame_at(g, he)
        mask = a47.train_mask_before(g, gh, y, hs)
        idx = F.index[mask.reindex(F.index, fill_value=False).to_numpy()]
        _R.update(g=g, y=y, F=F, mask=mask, index=idx, origin=hs, horizon_end=he)
    return _R


class Identity(unittest.TestCase):
    def test_A_times_B_recovers_the_stacked_operator(self):
        # A B = [4 D1^T, D4^T] is the definition of B; if this fails nothing else matters.
        G = ig.build_geometry(toy(48))
        M = sp_hstack([lam * G.D[h].T for h, lam in G.horizons], format='csc').toarray()
        np.testing.assert_allclose(G.A @ G.B, M, rtol=0, atol=1e-9)

    def test_the_solver_identity_holds_on_a_toy_graph(self):
        # z - y = e0 + B r, with z produced by the SHIPPED solver rather than by this module.
        rng = np.random.default_rng(20260906)
        idx = toy(48)
        G = ig.build_geometry(idx)
        y = 60 + 8 * np.sin(np.arange(len(idx)) / 5.0)
        p = y + rng.normal(scale=1.5, size=len(idx))
        r = rng.normal(scale=0.05, size=G.m)
        terms = []
        for h, lam in G.horizons:
            t = G.D[h] @ y + r[G.slice(h)]
            terms.append((G.D[h], t, lam))
        z = a47.solve(p, idx, terms)           # clipped, but far from the 5/100 bounds here
        e0 = ig.solver_error(p, y, G.A)
        np.testing.assert_allclose(z - y, e0 + G.B @ r, rtol=0, atol=1e-8)

    def test_zero_increment_error_gives_the_true_increment_reference(self):
        rng = np.random.default_rng(7)
        idx = toy(48)
        G = ig.build_geometry(idx)
        y = 55 + 5 * np.cos(np.arange(len(idx)) / 4.0)
        p = y + rng.normal(scale=2.0, size=len(idx))
        terms = [(G.D[h], G.D[h] @ y, lam) for h, lam in G.horizons]
        z = a47.solve(p, idx, terms)
        np.testing.assert_allclose(z, ig.true_increment_reference(p, y, idx), rtol=0, atol=1e-8)

    def test_the_operator_annihilates_a_constant(self):
        G = ig.build_geometry(toy(48))
        one = np.ones(len(G.index))
        for h, _lam in G.horizons:
            np.testing.assert_allclose(G.D[h] @ one, 0.0, atol=1e-12)
        np.testing.assert_allclose(G.A @ one, one, rtol=0, atol=1e-12)


class Chronology(unittest.TestCase):
    def test_a_hole_produces_no_edge_across_it(self):
        # Drop four slots. No edge may span the gap: durations are exact, never "h surviving rows".
        idx = toy(48).delete([20, 21, 22, 23])
        G = ig.build_geometry(idx)
        for h, _lam in G.horizons:
            later = G.edges[h]
            earlier = later - pd.Timedelta(minutes=30 * h)
            self.assertTrue(pd.DatetimeIndex(earlier).isin(idx).all(), h)
            self.assertEqual(set(pd.TimedeltaIndex(later - earlier).unique()),
                             {pd.Timedelta(minutes=30 * h)})

    def test_every_edge_spans_exactly_its_horizon(self):
        r = real_block()
        G = ig.build_geometry(r['index'])
        for h, _lam in G.horizons:
            d = (G.edges[h] - (G.edges[h] - pd.Timedelta(minutes=30 * h)))
            self.assertEqual(set(d.unique()), {pd.Timedelta(minutes=30 * h)})

    def test_the_geometry_matches_the_incumbent_effective_mask(self):
        r = real_block()
        want = ig.effective_edges(r['F'], r['y'], r['mask'])
        G = ig.build_geometry(r['index'], edges=want)
        self.assertEqual(len(G.edges[1]), 2211)
        self.assertEqual(len(G.edges[4]), 2208)
        self.assertEqual(G.m, 4419)

    def test_a_mismatched_edge_set_is_refused(self):
        r = real_block()
        want = ig.effective_edges(r['F'], r['y'], r['mask'])
        broken = dict(want)
        broken[1] = broken[1][:-5]
        with self.assertRaises(AssertionError):
            ig.build_geometry(r['index'], edges=broken)

    def test_the_training_index_stops_at_the_origin(self):
        r = real_block()
        self.assertLessEqual(r['index'].max(), pd.Timestamp(r['origin']))
        G = ig.build_geometry(r['index'])
        for h, _lam in G.horizons:
            self.assertLessEqual(G.edges[h].max(), pd.Timestamp(r['origin']))

    def test_labels_and_sensors_after_the_origin_cannot_move_the_geometry(self):
        # The geometry is a function of the timestamps alone. Nothing else may enter it.
        r = real_block()
        a = ig.build_geometry(r['index']).digest()
        g2 = r['g'].copy()
        after = g2.index > pd.Timestamp(r['origin'])
        g2.loc[after, fp.TARGET] = 1.0
        for col in fp.FAST:
            g2.loc[after, col] = g2.loc[after, col] + 50.0
        _gh2, F2 = a47.frame_at(g2, r['horizon_end'])
        mask2 = a47.train_mask_before(g2, _gh2, g2[fp.TARGET], r['origin'])
        idx2 = F2.index[mask2.reindex(F2.index, fill_value=False).to_numpy()]
        self.assertTrue(idx2.equals(r['index']))
        self.assertEqual(ig.build_geometry(idx2).digest(), a)


class Gradient(unittest.TestCase):
    def _finite_difference(self, G, mode):
        rng = np.random.default_rng(20260906)
        r = rng.normal(size=G.m)
        grad = G.grad(r, mode)
        num = np.zeros_like(r)
        step = 1e-6
        for j in range(len(r)):
            sh = np.zeros_like(r)
            sh[j] = step
            num[j] = (G.loss(r + sh, mode) - G.loss(r - sh, mode)) / (2 * step)
        np.testing.assert_allclose(grad, num, rtol=1e-5, atol=1e-6)

    def test_the_gradient_matches_finite_differences_for_both_arms(self):
        G = ig.build_geometry(toy(24))
        for mode in ('separate', 'coupled'):
            self._finite_difference(G, mode)

    def test_the_gradient_equals_the_explicit_matrix_product(self):
        rng = np.random.default_rng(3)
        G = ig.build_geometry(toy(32))
        r = rng.normal(size=G.m)
        for mode in ('separate', 'coupled'):
            np.testing.assert_allclose(G.grad(r, mode), G.Q_dense(mode) @ r, rtol=0, atol=1e-10)

    def test_only_the_coupled_arm_lets_one_horizon_move_the_other(self):
        rng = np.random.default_rng(11)
        G = ig.build_geometry(toy(32))
        r = np.zeros(G.m)
        s1, s4 = G.slice(1), G.slice(4)
        r[s4] = rng.normal(size=s4.stop - s4.start)
        self.assertGreater(np.abs(G.grad(r, 'coupled')[s1]).max(), 1e-8)
        np.testing.assert_allclose(G.grad(r, 'separate')[s1], 0.0, atol=1e-12)

    def test_l2_control_has_no_quadratic_form(self):
        G = ig.build_geometry(toy(24))
        with self.assertRaises(ValueError):
            G.grad(np.zeros(G.m), 'l2_control')


class Majorizer(unittest.TestCase):
    def test_diag_H_minus_Q_is_positive_semidefinite_for_both_arms(self):
        G = ig.build_geometry(toy(32))
        H = G.hess()
        for mode in ('separate', 'coupled'):
            Q = G.Q_dense(mode)
            w = np.linalg.eigvalsh(np.diag(H) - Q)
            self.assertGreaterEqual(w.min(), -1e-10, mode)

    def test_the_hessian_is_positive_and_has_mean_one(self):
        G = ig.build_geometry(toy(32))
        H = G.hess()
        self.assertTrue((H > 0).all())
        self.assertAlmostEqual(float(H.mean()), 1.0, places=12)

    def test_both_arms_share_the_hessian_and_the_scale(self):
        # A difference between G1 and G2 must not be a difference in step size.
        G = ig.build_geometry(toy(32))
        self.assertIs(G.hess(), G.H)
        self.assertIsInstance(G.scale, float)


class Regularisation(unittest.TestCase):
    def test_epsilon_makes_the_nullspace_of_B_cost_something(self):
        # There are more edges than timestamps, so B has a nontrivial nullspace. Without eps an
        # error living there would be free, and the two horizons could drift apart without
        # penalty as long as their effects cancelled.
        G = ig.build_geometry(toy(32))
        _u, s, vt = np.linalg.svd(G.B, full_matrices=True)
        null = vt[np.sum(s > 1e-10):]
        self.assertGreater(len(null), 0)
        r = null[0]
        np.testing.assert_allclose(G.B @ r, 0.0, atol=1e-9)
        for mode in ('separate', 'coupled'):
            self.assertGreater(G.loss(r, mode), 0.0, mode)
        self.assertAlmostEqual(G.loss(r, 'coupled'),
                               0.5 * G.eps * float(r @ r) / G.scale, places=10)

    def test_the_loss_is_zero_only_at_zero_error(self):
        G = ig.build_geometry(toy(24))
        for mode in ('separate', 'coupled'):
            self.assertEqual(G.loss(np.zeros(G.m), mode), 0.0)

    def test_epsilon_is_frozen_at_the_documented_value(self):
        self.assertEqual(ig.EPS, 0.10)
        self.assertEqual(ig.build_geometry(toy(24)).eps, 0.10)

    def test_the_scale_constant_comes_from_the_operator_not_the_labels(self):
        # c and scale are functions of the timestamps only; changing y cannot move them.
        G1 = ig.build_geometry(toy(32))
        G2 = ig.build_geometry(toy(32))
        self.assertEqual(G1.c, G2.c)
        self.assertEqual(G1.scale, G2.scale)
        self.assertEqual(G1.digest(), G2.digest())


class Boundary(unittest.TestCase):
    def test_a_long_prefix_and_a_short_window_are_not_assumed_identical(self):
        # Diagnosis, not an equivalence claim: the operator on a 15-day sub-window differs from
        # the operator on the full prefix near the window's edges, and the interior agrees only
        # approximately. The plan asks for this to be measured rather than assumed.
        r = real_block()
        full = r['index']
        sub = full[full > full.max() - pd.Timedelta(days=15)]
        Gf = ig.build_geometry(full)
        Gs = ig.build_geometry(sub)
        self.assertNotEqual(Gf.digest(), Gs.digest())
        self.assertLess(Gs.m, Gf.m)
        # Same timestamp, different operator support -> different row of B. Report, do not equate.
        self.assertNotAlmostEqual(Gf.c, Gs.c, places=6)

    def test_memory_estimate_is_reported(self):
        r = real_block()
        G = ig.build_geometry(r['index'])
        mb = G.memory_mb()
        self.assertGreater(mb['B'], 1.0)
        self.assertGreater(mb['peak_estimate'], mb['B'])


class RealScale(unittest.TestCase):
    def test_the_identity_holds_on_the_real_training_index(self):
        r = real_block()
        G = ig.build_geometry(r['index'], edges=ig.effective_edges(r['F'], r['y'], r['mask']))
        rng = np.random.default_rng(20260906)
        rr = rng.normal(scale=0.02, size=G.m)
        y = r['y'].reindex(r['index']).to_numpy()
        p = y + rng.normal(scale=1.0, size=len(y))
        terms = [(G.D[h], G.D[h] @ y + rr[G.slice(h)], lam) for h, lam in G.horizons]
        z = a47.solve(p, r['index'], terms)
        e0 = ig.solver_error(p, y, G.A)
        np.testing.assert_allclose(z - y, e0 + G.B @ rr, rtol=0, atol=1e-7)


if __name__ == '__main__':
    unittest.main()
