"""Checks for the session-30 sensor ablation.

The point of the arms is that they remove absolute LEVEL information about one sensor and keep
everything else, so the tests are mostly about what SURVIVES. An ablation that quietly took the
thermal block with it would repeat section 210's confound, which is the thing this experiment
exists to avoid.

    .venv/Scripts/python.exe -m unittest discover -s tests -p test_v21_sensor_ablation.py
"""
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
import final_pipeline as fp
import an69_v21_sensor_ablation as a69

_G = {}


def grid():
    if not _G:
        g = fp.load_grid()
        _G['g'], _G['y'], _G['F'] = g, g[fp.TARGET], fp.make_features(g)
        _G['drops'] = a69.freeze_whitelist(g)
    return _G['g'], _G['y'], _G['F'], _G['drops']


def offset(g, sensor, amount):
    g2 = g.copy()
    g2[sensor] = g2[sensor] + amount
    return fp.make_features(g2)


class Whitelist(unittest.TestCase):
    def test_the_drop_lists_are_a_small_minority_of_the_design(self):
        _, _, F, drops = grid()
        for h, _lam in fp.INC_SPEC:
            n = fp.inc_design(F, h, fp.INC_COLS, False).shape[1]
            self.assertLess(len(drops[h]['drop_both_abs']), n / 3, h)
            self.assertGreater(len(drops[h]['drop_pressure_abs']), 0)
            self.assertGreater(len(drops[h]['drop_co2_abs']), 0)

    def test_no_column_is_lost_to_both_sensors_at_once(self):
        """Reported rather than assumed: if a CO2xT interaction ever enters the design this
        fails, and the ablation stops being separable."""
        _, _, _, drops = grid()
        for h, _lam in fp.INC_SPEC:
            self.assertEqual(drops[h]['mixed'], [], h)

    def test_the_drop_list_is_stable_on_a_truncated_prefix(self):
        """It is frozen once on the full grid and applied to every fold, so it must not depend
        on where the grid happens to end."""
        g, _, _, drops = grid()
        end = g.index[(g.is_test == 0).to_numpy()].max() - pd.Timedelta(days=20)
        sub = a69.sensitive_columns(g.loc[g.index <= end], 'pressure', a69.PRESSURE_OFFSET)
        for h, _lam in fp.INC_SPEC:
            self.assertEqual(sorted(sub[h]), drops[h]['drop_pressure_abs'], h)


class WhatSurvives(unittest.TestCase):
    def test_the_pressure_arm_keeps_every_co2_column(self):
        _, _, F, drops = grid()
        for h, _lam in fp.INC_SPEC:
            X = a69.ablated_design(F, h, drops[h]['drop_pressure_abs'])
            base = fp.inc_design(F, h, fp.INC_COLS, False)
            for col in base.columns:
                if 'co2' in str(col):
                    self.assertIn(col, X.columns, col)

    def test_the_co2_arm_keeps_every_pressure_column(self):
        _, _, F, drops = grid()
        for h, _lam in fp.INC_SPEC:
            X = a69.ablated_design(F, h, drops[h]['drop_co2_abs'])
            base = fp.inc_design(F, h, fp.INC_COLS, False)
            for col in base.columns:
                if 'pressure' in str(col):
                    self.assertIn(col, X.columns, col)

    def test_every_thermal_and_time_column_survives_all_three_arms(self):
        """Section 210's confound, asserted away: nothing about temperature, soil, water or
        the diurnal clock may be removed by a pressure or CO2 ablation."""
        _, _, F, drops = grid()
        base = fp.inc_design(F, 4, fp.INC_COLS, False)
        protected = [c for c in base.columns
                     if not any(s in str(c) for s in ('pressure', 'co2'))]
        # 80 of the parent's 132 columns mention neither sensor. Of the 52 that do, only 31 are
        # offset-sensitive; the other 21 are dynamics and survive too (see the test below).
        self.assertEqual(len(protected), 80)
        for arm in a69.ARMS:
            X = a69.ablated_design(F, 4, drops[4][arm])
            for col in protected:
                self.assertIn(col, X.columns, (arm, col))
            pd.testing.assert_series_equal(X[protected[0]], base[protected[0]])

    def test_the_invariant_sensor_dynamics_survive(self):
        """The arms remove level, not dynamics. These columns are differences, slopes, ranges
        and spreads, and every one of them is kept."""
        _, _, F, drops = grid()
        X = a69.ablated_design(F, 4, drops[4]['drop_both_abs'])
        for col in ('pressure_change', 'pressure_slope', 'pressure_sd6h', 'pressure_a1h',
                    'co2_change', 'co2_slope', 'co2_rng48', 'co2_sd6h', 'co2_tend24h'):
            self.assertIn(col, X.columns, col)

    def test_the_absolute_level_columns_are_gone(self):
        _, _, F, drops = grid()
        X = a69.ablated_design(F, 4, drops[4]['drop_both_abs'])
        self.assertNotIn('pressure', X.columns)
        self.assertNotIn('co2', X.columns)
        self.assertNotIn('pressure_prev', X.columns)
        self.assertNotIn('co2_prev', X.columns)


class OffsetInvariance(unittest.TestCase):
    def test_the_pressure_arm_is_invariant_to_a_pressure_offset(self):
        g, _, F, drops = grid()
        F2 = offset(g, 'pressure', a69.PRESSURE_OFFSET)
        for h, _lam in fp.INC_SPEC:
            a = a69.ablated_design(F, h, drops[h]['drop_pressure_abs'])
            b = a69.ablated_design(F2, h, drops[h]['drop_pressure_abs'])
            self.assertEqual(list(a.columns), list(b.columns))
            np.testing.assert_allclose(a.to_numpy(), b.to_numpy(), **a69.TOL)

    def test_the_co2_arm_is_invariant_to_a_co2_offset(self):
        g, _, F, drops = grid()
        F2 = offset(g, 'co2', a69.CO2_OFFSET)
        for h, _lam in fp.INC_SPEC:
            a = a69.ablated_design(F, h, drops[h]['drop_co2_abs'])
            b = a69.ablated_design(F2, h, drops[h]['drop_co2_abs'])
            np.testing.assert_allclose(a.to_numpy(), b.to_numpy(), **a69.TOL)

    def test_the_parent_is_NOT_invariant(self):
        """The control that makes the two above meaningful."""
        g, _, F, _ = grid()
        F2 = offset(g, 'pressure', a69.PRESSURE_OFFSET)
        a = fp.inc_design(F, 4, fp.INC_COLS, False)
        b = fp.inc_design(F2, 4, fp.INC_COLS, False)
        self.assertFalse(np.allclose(a.to_numpy(), b.to_numpy(), **a69.TOL))

    def test_the_pressure_arm_is_still_moved_by_a_co2_offset(self):
        """Each arm removes one sensor's level, not both. Otherwise the three arms would not
        be distinguishable."""
        g, _, F, drops = grid()
        F2 = offset(g, 'co2', a69.CO2_OFFSET)
        a = a69.ablated_design(F, 4, drops[4]['drop_pressure_abs'])
        b = a69.ablated_design(F2, 4, drops[4]['drop_pressure_abs'])
        self.assertFalse(np.allclose(a.to_numpy(), b.to_numpy(), **a69.TOL))


class LabelIsolation(unittest.TestCase):
    def setUp(self):
        self.g, self.y, self.F, self.drops = grid()
        boundary = self.g.index[(self.g.is_test == 0).to_numpy()].max()
        self.origin = boundary - pd.Timedelta(days=15)
        self.mask = (pd.Series((self.g.is_test == 0).to_numpy(), index=self.g.index)
                     & self.y.notna() & (self.g.index <= self.origin))
        self.idx = self.g.index[(self.g.index > self.origin) & (self.g.index <= boundary)][:200]

    def test_no_target_or_target_lag_is_in_any_arm(self):
        for arm in a69.ARMS:
            X = a69.ablated_design(self.F, 4, self.drops[4][arm])
            lab = self.y.notna()
            for col in X.columns:
                self.assertNotIn(fp.TARGET, str(col))
                s = X[col].reindex(self.F.index)
                ok = s.notna() & lab
                if int(ok.sum()) > 100 and float(s[ok].std()) > 0:
                    self.assertLess(abs(float(np.corrcoef(s[ok], self.y[ok])[0, 1])), 0.999,
                                    (arm, col))

    def test_labels_after_the_origin_change_no_prediction(self):
        rng = np.random.default_rng(73)
        y2 = self.y.copy()
        after = y2.index > self.origin
        y2[after] = 45.0 + 25.0 * rng.random(int(after.sum()))
        build = a69.make_builder(self.drops, 'drop_both_abs')
        a = build(self.F, self.y, self.mask, (fp.INC_SEED,))
        b = build(self.F, y2, self.mask, (fp.INC_SEED,))
        for h, _lam in fp.INC_SPEC:
            X = a69.ablated_design(self.F, h, self.drops[h]['drop_both_abs']).loc[self.idx]
            np.testing.assert_array_equal(a[h][0].predict(X), b[h][0].predict(X))

    def test_the_null_arm_reproduces_the_incumbent_design(self):
        """`arm=None` must be the parent exactly, or the control is not a control."""
        for h, _lam in fp.INC_SPEC:
            pd.testing.assert_frame_equal(a69.ablated_design(self.F, h, []),
                                          fp.inc_design(self.F, h, fp.INC_COLS, False))


if __name__ == '__main__':
    unittest.main()
