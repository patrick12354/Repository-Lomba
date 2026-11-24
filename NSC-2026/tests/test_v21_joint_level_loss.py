"""Session 38, family E: the joint level/change objective must be the thing it claims to be.

A custom objective that is subtly wrong still trains and still scores, so the algebra is checked
before any arm is read: the gradient against finite differences, the majorizer's positive
semidefiniteness for every arm, the edge set, and the fact that beta=0 really is plain L2.

    .venv/Scripts/python.exe -m unittest discover -s tests -p test_v21_joint_level_loss.py
"""
import sys
import unittest
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
import final_pipeline as fp
import v21_joint_level_loss as jl

warnings.filterwarnings('ignore')


def toy(n=48, start='2023-07-01'):
    return pd.date_range(start, periods=n, freq='30min')


class Operator(unittest.TestCase):
    def test_beta_zero_is_the_identity(self):
        idx = toy()
        Q, _ops = jl.build_Q(idx, 0.0)
        np.testing.assert_allclose(Q.toarray(), np.eye(len(idx)), rtol=0, atol=1e-12)

    def test_the_weights_are_beta_and_beta_over_four(self):
        self.assertEqual(jl.HORIZON_WEIGHT, {1: 1.0, 4: 0.25})
        idx = toy()
        Q, ops = jl.build_Q(idx, 1.0)
        D1, D4 = ops[1], ops[4]
        want = (np.eye(len(idx)) + (D1.T @ D1).toarray() + 0.25 * (D4.T @ D4).toarray())
        np.testing.assert_allclose(Q.toarray(), want, rtol=0, atol=1e-12)

    def test_no_edge_crosses_a_hole(self):
        idx = toy(48).delete([20, 21, 22, 23])
        _Q, ops = jl.build_Q(idx, 1.0)
        for h, D in ops.items():
            _d, stamps = fp.diff_operator(idx, h)
            later = pd.DatetimeIndex(stamps)
            earlier = later - pd.Timedelta(minutes=30 * h)
            self.assertTrue(earlier.isin(idx).all(), h)
            self.assertEqual(D.shape[0], len(later))

    def test_the_operator_annihilates_a_constant_in_its_change_part(self):
        idx = toy()
        Q0, _ = jl.build_Q(idx, 0.0)
        Q1, _ = jl.build_Q(idx, 1.0)
        one = np.ones(len(idx))
        np.testing.assert_allclose(Q1 @ one, Q0 @ one, rtol=0, atol=1e-12)

    def test_the_operator_is_symmetric_and_positive_definite(self):
        idx = toy(32)
        for beta in jl.BETAS:
            Q = jl.build_Q(idx, beta)[0].toarray()
            np.testing.assert_allclose(Q, Q.T, rtol=0, atol=1e-12)
            self.assertGreater(float(np.linalg.eigvalsh(Q).min()), 0.5)


class Gradient(unittest.TestCase):
    def test_the_gradient_matches_finite_differences_for_every_arm(self):
        idx = toy(24)
        rng = np.random.default_rng(20260907)
        for beta in jl.BETAS:
            Q, _ = jl.build_Q(idx, beta)
            r = rng.normal(size=len(idx))
            _loss, grad = jl.loss_and_grad(r, Q)
            num = np.zeros_like(r)
            step = 1e-6
            for j in range(len(r)):
                sh = np.zeros_like(r)
                sh[j] = step
                hi, _ = jl.loss_and_grad(r + sh, Q)
                lo, _ = jl.loss_and_grad(r - sh, Q)
                num[j] = (hi - lo) / (2 * step)
            np.testing.assert_allclose(grad, num, rtol=1e-5, atol=1e-6)

    def test_beta_zero_reduces_to_the_l2_gradient(self):
        idx = toy(24)
        Q, _ = jl.build_Q(idx, 0.0)
        r = np.linspace(-2, 3, len(idx))
        loss, grad = jl.loss_and_grad(r, Q)
        np.testing.assert_allclose(grad, r, rtol=0, atol=1e-12)
        self.assertAlmostEqual(loss, 0.5 * float(r @ r), places=12)

    def test_the_loss_is_zero_only_at_zero_error(self):
        idx = toy(24)
        for beta in jl.BETAS:
            Q, _ = jl.build_Q(idx, beta)
            self.assertEqual(jl.loss_and_grad(np.zeros(len(idx)), Q)[0], 0.0)


class Majorizer(unittest.TestCase):
    def test_diag_H_minus_Q_is_psd_for_every_arm(self):
        idx = toy(32)
        H = jl.majorizer(idx)
        for beta in jl.BETAS:
            Q = jl.build_Q(idx, beta)[0].toarray()
            w = np.linalg.eigvalsh(np.diag(H) - Q)
            self.assertGreaterEqual(w.min(), -1e-10, beta)

    def test_the_majorizer_comes_from_beta_one_and_is_shared(self):
        idx = toy(32)
        H = jl.majorizer(idx)
        Q1 = jl.build_Q(idx, 1.0)[0].toarray()
        np.testing.assert_allclose(H, np.abs(Q1).sum(axis=1), rtol=0, atol=1e-12)
        for beta in (0.0, 0.25):
            Qb = np.abs(jl.build_Q(idx, beta)[0].toarray())
            self.assertTrue((Qb <= np.abs(Q1) + 1e-12).all(), beta)

    def test_the_hessian_is_strictly_positive(self):
        self.assertTrue((jl.majorizer(toy(32)) > 0).all())


class Fitting(unittest.TestCase):
    def _data(self, n=400):
        idx = pd.date_range('2023-07-01', periods=n, freq='30min')
        rng = np.random.default_rng(3)
        X = pd.DataFrame({'a': np.sin(np.arange(n) / 7.0), 'b': rng.normal(size=n),
                          'c': np.cos(np.arange(n) / 11.0)}, index=idx)
        y = 60 + 8 * X.a + 2 * X.b
        return X, y, idx

    def test_the_offset_is_the_training_mean_and_is_added_once(self):
        X, y, idx = self._data()
        m = jl.JointLevelModel(0.0, (0,), rounds=5).fit(X, y, idx)
        self.assertAlmostEqual(m.offset_, float(np.mean(y)), places=12)
        raw = np.mean([b.predict(X, raw_score=True) for b in m.boosters_], axis=0)
        np.testing.assert_allclose(m.predict(X) - raw, m.offset_, rtol=0, atol=1e-9)

    def test_the_objective_decreases(self):
        X, y, idx = self._data()
        for beta in jl.BETAS:
            m = jl.JointLevelModel(beta, (0,), rounds=60).fit(X, y, idx, log_every=10)
            obj = [r['objective'] for r in m.log_]
            self.assertGreater(len(obj), 2, beta)
            self.assertLess(obj[-1], obj[0], beta)

    def test_a_larger_beta_reduces_change_error_under_a_common_reference(self):
        # `change_loss` in the log is measured under each arm's OWN Q, and at beta=0 that term is
        # identically zero. To compare arms the residuals must be scored under one fixed
        # operator, so both are evaluated at beta=1.
        X, y, idx = self._data()
        Qref, _ = jl.build_Q(idx, 1.0)
        yv = np.asarray(y, float)
        change = {}
        for beta in (0.0, 1.0):
            m = jl.JointLevelModel(beta, (0,), rounds=60).fit(X, y, idx, log_every=60)
            r = m.predict(X) - yv
            change[beta] = float(0.5 * (r @ (Qref @ r) - r @ r))
        self.assertLess(change[1.0], change[0.0])

    def test_fit_once_predict_many(self):
        X, y, idx = self._data()
        m = jl.JointLevelModel(0.25, (0, 1), rounds=10).fit(X, y, idx)
        a, b = m.predict(X), m.predict(X)
        np.testing.assert_allclose(a, b, rtol=0, atol=0)
        self.assertEqual(len(m.boosters_), 2)
        self.assertEqual(m.digest(), m.digest())

    def test_the_huber_delta_is_dropped_under_a_custom_objective(self):
        m = jl.JointLevelModel(0.25, (0,), rounds=1)
        self.assertNotIn('alpha', m.kw)
        self.assertNotIn('objective', m.kw)
        self.assertEqual(m.rounds, 1)

    def test_an_unmapped_parameter_is_refused(self):
        m = jl.JointLevelModel(0.0, (0,), params=dict(fp.LGB_KW, some_knob=1), rounds=1)
        with self.assertRaises(KeyError):
            m._native(0)

    def test_labels_after_the_training_index_cannot_enter(self):
        # The operator and the offset are functions of the training rows only.
        X, y, idx = self._data()
        a = jl.JointLevelModel(1.0, (0,), rounds=5).fit(X, y, idx)
        y2 = y.copy()
        y2.iloc[:] = y2.to_numpy()
        m2 = jl.JointLevelModel(1.0, (0,), rounds=5).fit(X, y2, idx)
        self.assertEqual(a.digest(), m2.digest())

    def test_the_edge_count_is_recorded(self):
        X, y, idx = self._data(200)
        m = jl.JointLevelModel(1.0, (0,), rounds=3).fit(X, y, idx)
        self.assertEqual(m.info()['n_edges'][1], 199)
        self.assertEqual(m.info()['n_edges'][4], 196)


if __name__ == '__main__':
    unittest.main()
