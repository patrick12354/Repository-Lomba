"""Regression checks for session-28 experiments; no outer tuning in these tests."""
import importlib
import sys
import unittest
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
import an56_v21_distributed_lag as a56
import an47_v21_forward_benchmark as a47


class MethodContract(unittest.TestCase):
    def module(self):
        name = 'an59_v21_candidate_contract'
        self.assertIsNotNone(importlib.util.find_spec(name), 'candidate contract not implemented')
        return importlib.import_module(name)

    def test_mask_requires_only_actual_target_endpoints(self):
        idx = pd.date_range('2023-01-01', periods=20, freq='30min')
        mask = pd.Series(True, index=idx)
        mask.iloc[8] = False
        expected = mask & mask.shift(1, fill_value=False) & mask.shift(4, fill_value=False)
        pd.testing.assert_series_equal(a56.lag_mask(mask, idx), expected)

    def test_selector_uses_final_solve_even_when_raw_increment_order_reverses(self):
        c = self.module()
        idx = pd.date_range('2023-01-01', periods=2, freq='30min')
        import final_pipeline as fp
        D, _ = fp.diff_operator(idx, 1)
        y, level = np.array([40., 60.]), np.array([50., 50.])
        choices = {'raw_best': 20., 'final_best': 22.5}
        def evaluate(v):
            z = a47.solve(level, idx, [(D, np.array([v]), 4.)])
            return float(np.mean((z-y)**2))
        label, table = c.select_final(choices, evaluate)
        self.assertEqual(label, 'final_best')
        self.assertLess(table['final_best'], table['raw_best'])

    def test_provenance_rejects_selection_and_inference_seed_mismatch(self):
        c = self.module()
        with self.assertRaisesRegex(ValueError, 'seeds'):
            c.require_matching_config({'seeds': [1]}, {'seeds': [1, 2]})

    def test_provenance_rejects_factor_kind_mismatch(self):
        c = self.module()
        with self.assertRaisesRegex(ValueError, 'factor'):
            c.require_matching_config({'factor': 'mixed'}, {'factor': 'lgb'})

    def test_direction_decomposition_matches_direct_mse(self):
        c = self.module()
        y, p, q = np.array([1., 2., 3.]), np.array([3., 3., 4.]), np.array([2., 4., 3.])
        d = c.direction(y, p, q)
        self.assertAlmostEqual(d['d_mse'], np.mean((q-y)**2)-np.mean((p-y)**2))
        self.assertAlmostEqual(d['d_mse'], d['alignment']+d['movement_mse'])

    def test_lead_is_distance_from_origin_not_scored_window_width(self):
        c = self.module()
        origin = pd.Timestamp('2023-01-01')
        idx = pd.date_range(origin + pd.Timedelta(hours=144.5), periods=96, freq='30min')
        h = c.lead_hours(idx, origin)
        self.assertEqual((h.min(), h.max()), (144.5, 192.))

    def test_training_provenance_rejects_future_rows(self):
        c = self.module()
        rows = pd.date_range('2023-01-01', periods=3, freq='30min')
        with self.assertRaisesRegex(ValueError, 'origin'):
            c.training_record(rows, rows[1], rows[-1], {'seeds': [1]})


class LagFactorContract(unittest.TestCase):
    def module(self):
        name = 'an60_v21_lag_factor_ablation'
        self.assertIsNotNone(importlib.util.find_spec(name), 'lag ablation not implemented')
        return importlib.import_module(name)

    def frame(self, n=200):
        import final_pipeline as fp
        idx = pd.date_range('2023-01-01', periods=n, freq='30min')
        t = np.arange(n)/48*2*np.pi
        F = pd.DataFrame({'T': 25+4*np.sin(t), 'co2': 400+np.cos(t),
                          'pressure': 1000+np.sin(t/3), 'esT': fp.es(25+4*np.sin(t)),
                          'rh_tmin48': 60+5*np.cos(t), 'sin1': np.sin(t),
                          'cos1': np.cos(t), 'sin2': np.sin(2*t), 'cos2': np.cos(2*t)}, index=idx)
        return F

    def test_lgb_lag_design_retains_baseline_columns_without_duplicate_values(self):
        a = self.module()
        import final_pipeline as fp
        F = self.frame()
        base = fp.inc_design(F, 1, fp.INC_PHYS_COLS, True)
        X = a.extra_design(F, 1)
        self.assertTrue(set(base.columns) <= set(X.columns))
        self.assertNotIn('T_lag0', X)
        self.assertIn('T_lag48', X)
        self.assertEqual(len(X.columns), len(set(X.columns)))

    def test_zero_blend_reproduces_base_increment_terms(self):
        a = self.module()
        import final_pipeline as fp
        from unittest.mock import patch
        F = self.frame()
        y = pd.Series(60-10*F.sin1, index=F.index)
        mask = pd.Series(F.index < F.index[-40], index=F.index)
        with patch.dict(fp.INC_KW, {'n_estimators': 5, 'n_jobs': 1}):
            inc = fp.fit_increments(F, y, mask, seeds=(7,), physics=True, deshrink=True)
            bundle = a.fixed_bundle(F, y, mask, inc)
        idx = F.index[-40:]
        old = a47.increment_terms(F, idx, inc, deshrink=.5)
        new, _ = a.bundle_terms(F, idx, bundle, 'fixed_old', blend=0.)
        for x, z in zip(old, new):
            np.testing.assert_allclose(x[1], z[1], atol=1e-12)

    def test_fixed_candidate_is_blind_to_labels_after_origin(self):
        a = self.module()
        import final_pipeline as fp
        from unittest.mock import patch
        F = self.frame()
        y = pd.Series(60-10*F.sin1, index=F.index)
        mask = pd.Series(F.index < F.index[-40], index=F.index)
        bad = y.copy(); bad.loc[~mask] += 999
        with patch.dict(fp.INC_KW, {'n_estimators': 5, 'n_jobs': 1}):
            ia = fp.fit_increments(F, y, mask, seeds=(7,), physics=True, deshrink=True)
            ib = fp.fit_increments(F, bad, mask, seeds=(7,), physics=True, deshrink=True)
            ba, bb = a.fixed_bundle(F, y, mask, ia), a.fixed_bundle(F, bad, mask, ib)
        ta, _ = a.bundle_terms(F, F.index[-40:], ba, 'fixed_old')
        tb, _ = a.bundle_terms(F, F.index[-40:], bb, 'fixed_old')
        for x, z in zip(ta, tb):
            np.testing.assert_array_equal(x[1], z[1])


if __name__ == '__main__':
    unittest.main()
