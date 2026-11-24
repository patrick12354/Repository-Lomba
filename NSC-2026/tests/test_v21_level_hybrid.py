"""Session 36, Task 1: the two-stage level estimator must compose correctly and read only the prefix.

The dangerous failure here is silent: a backbone that double-counts its own offset, or a residual
stage that sees a label it should not, would still produce plausible RMSE. These tests pin the
composition arithmetic, the label boundary, and the determinism of the basis.

    .venv/Scripts/python.exe -m unittest discover -s tests -p test_v21_level_hybrid.py
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
import an47_v21_forward_benchmark as a47
import v21_level_hybrid as lh

warnings.filterwarnings('ignore')
_C = {}


def ctx():
    """B1's frame at its horizon, a short training prefix and a small query set."""
    if not _C:
        g = fp.load_grid()
        y = g[fp.TARGET]
        name, hs, he = a47.blocks_of(g)[0]
        gh, F = a47.frame_at(g, he)
        mask = a47.train_mask_before(g, gh, y, hs)
        train = F.index[mask.reindex(F.index, fill_value=False).to_numpy()]
        lab = pd.Series((gh.is_test == 0).to_numpy(), index=gh.index) & y.reindex(gh.index).notna()
        hold = gh.index[(lab & (gh.index > hs)).to_numpy()]
        _C.update(g=g, y=y, F=F, train=train, hold=hold, origin=hs, horizon_end=he)
    return _C


def small(c, n_train=700, n_query=120):
    return c['train'][-n_train:], c['hold'][:n_query]


class Contract(unittest.TestCase):
    def test_only_the_three_named_kinds_are_accepted(self):
        for k in lh.KINDS:
            lh.LevelHybrid(k)
        for bad in ('spline', 'gam', '', None):
            with self.assertRaises(AssertionError):
                lh.LevelHybrid(bad)

    def test_the_driver_and_harmonic_columns_are_the_frozen_ones(self):
        self.assertEqual(len(lh.DRIVERS), 8)
        self.assertEqual(len(lh.HARMONICS), 4)
        self.assertEqual(lh.INTERACTIONS, (('T', 'T_min48'), ('T', 'co2_c24h')))
        lh.assert_columns(ctx()['F'])

    def test_no_soil_pressure_level_or_time_index_enters(self):
        cols = lh.required_columns()
        self.assertNotIn('pressure', cols)
        self.assertFalse(any(x.startswith('soil') for x in cols))
        self.assertFalse(any('day' in x for x in cols))

    def test_a_missing_column_is_refused(self):
        with self.assertRaises(AssertionError):
            lh.assert_columns(ctx()['F'].drop(columns=['co2_slope']))

    def test_the_ridge_penalty_scales_with_the_training_count(self):
        self.assertAlmostEqual(lh._ridge_alpha(1000), 10.0, places=12)
        self.assertEqual(lh.RIDGE_LAMBDA, 0.01)


class Composition(unittest.TestCase):
    """q = g + h, once. Not 2g + h, not h alone."""

    def test_a_stubbed_backbone_and_residual_add_exactly_once(self):
        # The plan's explicit case: g = 10 and h = 2 must give 12, never 22 or 2.
        c = ctx()
        tr, q = small(c, 400, 40)
        m = lh.LevelHybrid('linear').fit(c['F'], c['y'], tr)
        m.ridge_.coef_ = np.zeros_like(m.ridge_.coef_)
        m.ridge_.intercept_ = 10.0
        m.resid_train_ = np.full(len(tr), 2.0)
        got, g, h = m.predict(c['F'], q)
        np.testing.assert_allclose(g, 10.0, atol=1e-9)
        np.testing.assert_allclose(h, 2.0, atol=1e-6)
        np.testing.assert_allclose(got, 12.0, atol=1e-6)

    def test_predict_returns_the_parts_it_summed(self):
        c = ctx()
        tr, q = small(c, 500, 60)
        m = lh.LevelHybrid('additive').fit(c['F'], c['y'], tr)
        total, g, h = m.predict(c['F'], q)
        np.testing.assert_allclose(total, np.clip(g + h, *lh.CLIP), rtol=0, atol=1e-12)

    def test_the_backbone_is_never_a_feature_of_the_tree(self):
        # `g` is an additive offset. If it were also a column the tree would see it twice.
        c = ctx()
        tr, _q = small(c, 400, 20)
        m = lh.LevelHybrid('additive').fit(c['F'], c['y'], tr)
        self.assertEqual(list(m.F_train_.columns), list(c['F'].columns))
        self.assertNotIn('g', m.F_train_.columns)

    def test_only_the_total_is_clipped(self):
        c = ctx()
        tr, q = small(c, 400, 40)
        m = lh.LevelHybrid('linear').fit(c['F'], c['y'], tr)
        m.ridge_.intercept_ = 500.0
        total, g, _h = m.predict(c['F'], q)
        self.assertGreater(float(np.max(g)), lh.CLIP[1])       # g itself is not clipped
        self.assertLessEqual(float(np.max(total)), lh.CLIP[1])


class ControlEquivalence(unittest.TestCase):
    def test_a_zero_backbone_reproduces_the_control_member(self):
        # With g == 0 the residual IS y, so the two-stage estimator must return the C0 member
        # bit for bit -- same learner, same seeds, same frame.
        c = ctx()
        tr, q = small(c, 800, 100)
        m = lh.LevelHybrid('linear').fit(c['F'], c['y'], tr)
        m.ridge_.coef_ = np.zeros_like(m.ridge_.coef_)
        m.ridge_.intercept_ = 0.0
        m.resid_train_ = np.asarray(c['y'].reindex(tr), float)
        got, _g, _h = m.predict(c['F'], q)
        want = lh.control_hbt(c['F'], c['y'], tr, q)
        np.testing.assert_allclose(got, want, rtol=0, atol=1e-9)

    def test_the_stage_two_learner_is_the_incumbent(self):
        self.assertEqual(fp.LGB_KW['objective'], 'huber')
        self.assertEqual(len(fp.SEEDS_FIT), 5)
        self.assertEqual(lh.CLIP, (5.0, 100.0))


class LabelIsolation(unittest.TestCase):
    def test_labels_after_the_training_prefix_change_nothing(self):
        c = ctx()
        tr, q = small(c, 600, 80)
        a = lh.LevelHybrid('additive').fit(c['F'], c['y'], tr)
        y2 = c['y'].copy()
        y2.loc[y2.index > tr.max()] = 1.0
        b = lh.LevelHybrid('additive').fit(c['F'], y2, tr)
        self.assertEqual(a.digest(), b.digest())
        np.testing.assert_allclose(a.predict(c['F'], q)[0], b.predict(c['F'], q)[0],
                                   rtol=0, atol=1e-12)

    def test_the_basis_is_fitted_on_the_prefix_only(self):
        c = ctx()
        tr, _q = small(c, 600, 40)
        a = lh.LevelHybrid('additive').fit(c['F'], c['y'], tr)
        F2 = c['F'].copy()
        after = F2.index > tr.max()
        for d in lh.DRIVERS:
            F2.loc[after, d] = F2.loc[after, d] + 100.0
        b = lh.LevelHybrid('additive').fit(F2, c['y'], tr)
        self.assertEqual(a.digest(), b.digest())

    def test_fit_refuses_a_training_row_without_a_label(self):
        c = ctx()
        tr, _q = small(c, 300, 20)
        y2 = c['y'].copy()
        y2.loc[tr[5]] = np.nan
        with self.assertRaises(AssertionError):
            lh.LevelHybrid('linear').fit(c['F'], y2, tr)


class Determinism(unittest.TestCase):
    def test_prediction_does_not_depend_on_query_order_or_batch_size(self):
        c = ctx()
        tr, q = small(c, 500, 90)
        m = lh.LevelHybrid('pairwise').fit(c['F'], c['y'], tr)
        full, _g, _h = m.predict(c['F'], q)
        rev, _g2, _h2 = m.predict(c['F'], q[::-1])
        np.testing.assert_allclose(full, rev[::-1], rtol=0, atol=1e-9)
        first, _, _ = m.predict(c['F'], q[:30])
        np.testing.assert_allclose(full[:30], first, rtol=0, atol=1e-9)

    def test_two_fits_on_the_same_rows_agree(self):
        c = ctx()
        tr, q = small(c, 500, 50)
        a = lh.LevelHybrid('additive').fit(c['F'], c['y'], tr)
        b = lh.LevelHybrid('additive').fit(c['F'], c['y'], tr)
        self.assertEqual(a.digest(), b.digest())
        np.testing.assert_allclose(a.predict(c['F'], q)[0], b.predict(c['F'], q)[0],
                                   rtol=0, atol=1e-12)

    def test_the_column_order_is_stable_and_named(self):
        c = ctx()
        tr, _q = small(c, 500, 20)
        m = lh.LevelHybrid('pairwise').fit(c['F'], c['y'], tr)
        self.assertEqual(len(m.names_), int(m.keep_.sum()))
        self.assertTrue(any(n.startswith('tx_T_T_min48_') for n in m.names_))
        self.assertTrue(any(n.startswith('tx_T_co2_c24h_') for n in m.names_))
        self.assertTrue(any(n.startswith('h_sin1') for n in m.names_))


class Degeneracy(unittest.TestCase):
    def test_a_constant_driver_falls_back_to_a_linear_term_without_nan(self):
        c = ctx()
        tr, q = small(c, 400, 40)
        F2 = c['F'].copy()
        F2['co2_slope'] = 0.0
        m = lh.LevelHybrid('additive').fit(F2, c['y'], tr)
        self.assertIn('co2_slope', m.fallback_)
        out, g, _h = m.predict(F2, q)
        self.assertTrue(np.isfinite(out).all())
        self.assertTrue(np.isfinite(g).all())

    def test_constant_basis_columns_are_dropped_not_divided_by_zero(self):
        c = ctx()
        tr, q = small(c, 400, 40)
        F2 = c['F'].copy()
        F2['pressure_a24h'] = 3.0
        m = lh.LevelHybrid('additive').fit(F2, c['y'], tr)
        self.assertGreaterEqual(int((~m.keep_).sum()), 1)
        self.assertTrue(np.isfinite(m.predict(F2, q)[0]).all())

    def test_a_nan_driver_is_median_imputed_rather_than_propagated(self):
        c = ctx()
        tr, q = small(c, 400, 40)
        F2 = c['F'].copy()
        F2.loc[q[:5], 'T_rng48'] = np.nan
        m = lh.LevelHybrid('additive').fit(c['F'], c['y'], tr)
        self.assertTrue(np.isfinite(m.predict(F2, q)[0]).all())


class Diagnostics(unittest.TestCase):
    def test_info_reports_the_backbone_shape_and_training_fit(self):
        c = ctx()
        tr, _q = small(c, 600, 20)
        for kind in lh.KINDS:
            i = lh.LevelHybrid(kind).fit(c['F'], c['y'], tr).info()
            self.assertEqual(i['kind'], kind)
            self.assertGreater(i['n_basis'], 0)
            self.assertGreater(i['rmse_g_train'], 0.0)
            self.assertLess(i['rmse_q_train'], i['rmse_g_train'])

    def test_the_pairwise_basis_is_larger_than_the_additive_one(self):
        c = ctx()
        tr, _q = small(c, 600, 20)
        a = lh.LevelHybrid('additive').fit(c['F'], c['y'], tr)
        p = lh.LevelHybrid('pairwise').fit(c['F'], c['y'], tr)
        l = lh.LevelHybrid('linear').fit(c['F'], c['y'], tr)
        self.assertLess(int(l.keep_.sum()), int(a.keep_.sum()))
        self.assertLess(int(a.keep_.sum()), int(p.keep_.sum()))


if __name__ == '__main__':
    unittest.main()
