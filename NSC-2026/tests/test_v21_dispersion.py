"""Session 48: contracts for the dispersion arm and for the `--calibrate` naming defect.

`--calibrate` was in no version of `increment_tag`, so `--increment --calibrate` and `--increment`
wrote the same path. That is progress.md section 296's defect for the third time, and it is the one
that would have destroyed a scored file rather than merely confused a comparison.

    .venv/Scripts/python.exe -m unittest discover -s tests -p test_v21_dispersion.py
"""
import inspect
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
import final_pipeline as fp
import an105_v21_dispersion_arm as disp


class TheSlopeIsTruthOnPrediction(unittest.TestCase):
    def test_a_compressed_prediction_gives_a_slope_above_one(self):
        r = np.random.default_rng(0)
        y = 50 + 18 * r.standard_normal(2000)
        p = y.mean() + 0.9 * (y - y.mean())          # the model under-disperses by 10 %
        self.assertAlmostEqual(disp.fitted_slope(p, y), 1 / 0.9, places=6)

    def test_an_expanded_prediction_gives_a_slope_below_one(self):
        r = np.random.default_rng(1)
        y = 50 + 18 * r.standard_normal(2000)
        p = y.mean() + 1.2 * (y - y.mean())
        self.assertLess(disp.fitted_slope(p, y), 1.0)

    def test_a_perfect_prediction_gives_exactly_one(self):
        y = np.linspace(20, 90, 500)
        self.assertAlmostEqual(disp.fitted_slope(y, y), 1.0, places=10)


class TheOperatorChangesSpreadAndNotLevel(unittest.TestCase):
    def setUp(self):
        # Deliberately well inside [5, 100] so the physical clip cannot fire and turn a
        # scaling test into a clipping test; the clip itself is checked separately below.
        r = np.random.default_rng(2)
        self.p = np.clip(50 + 8 * r.standard_normal(1000), 5, 100)

    def test_scaling_leaves_the_mean_alone(self):
        for s in (0.9, 1.0, 1.05, 1.2):
            out = disp.apply_slope(self.p, s)
            self.assertAlmostEqual(out.mean(), self.p.mean(), places=6)

    def test_scaling_moves_the_spread_by_the_factor(self):
        out = disp.apply_slope(self.p, 1.10)
        self.assertAlmostEqual(out.std() / self.p.std(), 1.10, places=6)

    def test_slope_one_is_the_identity(self):
        """The `null_recentre` arm exists to prove the harness is measuring the SCALING and not
        the act of touching the vector; that only holds if s=1 is a no-op."""
        np.testing.assert_allclose(disp.apply_slope(self.p, 1.0), self.p, atol=1e-12)

    def test_the_result_stays_inside_the_physical_clip(self):
        wide = np.array([6.0, 20.0, 60.0, 98.0])
        out = disp.apply_slope(wide, 3.0)
        self.assertGreaterEqual(out.min(), 5.0)
        self.assertLessEqual(out.max(), 100.0)


class TheRegisteredArms(unittest.TestCase):
    def test_the_direction_control_is_the_negative_of_a_candidate(self):
        d = dict((a, s) for a, s in disp.ARMS)
        self.assertEqual(d['wrong_sign'], -0.50)
        self.assertEqual(d['disp_50'], 0.50)

    def test_the_null_arm_carries_zero_strength_and_is_named_apart(self):
        d = dict((a, s) for a, s in disp.ARMS)
        self.assertEqual(d['null_recentre'], 0.0)
        self.assertIn('null_recentre', d)


class CalibrateIsInTheFilename(unittest.TestCase):
    def base(self, **kw):
        d = dict(l2_member=True, blend_shrink=fp.BLEND_SHRINK, drop_ridge=True,
                 bag_nopress=False, robust_core=False, smooth_level=False,
                 vapour_increment=False, inc_physics=False, inc_deshrink=False,
                 inc_lags=False, inc_lambda_scale=1.0, tod_bias_on=True, harm_bias_on=False)
        d.update(kw)
        return fp.increment_tag(**d)

    def test_the_defect_calibrate_and_no_calibrate_shared_one_path(self):
        self.assertNotEqual(self.base(calibrate=True), self.base())

    def test_the_strength_is_in_the_name_too(self):
        self.assertNotEqual(self.base(calibrate=True, cal_shrink=0.5),
                            self.base(calibrate=True, cal_shrink=0.7))

    def test_every_previously_scored_filename_is_unchanged(self):
        self.assertEqual(self.base(), 'v16_noridge_todbias')
        self.assertEqual(self.base(tod_bias_on=False, harm_bias_on=True), 'v16_noridge')

    def test_calibrate_and_cat_debias_do_not_collide(self):
        names = {self.base(cat_debias=True), self.base(calibrate=True, cal_shrink=0.5),
                 self.base(cat_debias=True, calibrate=True, cal_shrink=0.5), self.base()}
        self.assertEqual(len(names), 4)

    def test_main_exposes_the_strength_and_defaults_to_the_session_6_value(self):
        self.assertEqual(inspect.signature(fp.main).parameters['cal_shrink'].default,
                         fp.CAL_SHRINK)
        self.assertEqual(fp.CAL_SHRINK, 0.70)


if __name__ == '__main__':
    unittest.main()
