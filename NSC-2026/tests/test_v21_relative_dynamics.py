"""Checks for the session-29 relative-dynamics increment design.

The design exists to answer one measured problem: 6.27% of test rows carry a pressure a boosted
tree has never seen, so every split on absolute pressure sends them down whichever branch the
largest training value happened to take. The fix is only real if the columns are genuinely free
of absolute pressure and CO2, and that is a property you can test rather than assert -- add a
constant to the whole sensor history and nothing may move.

The converse matters just as much. Temperature is deliberately absolute, because es(T) is a
thermodynamic function of the actual temperature and not of a difference. A design that were
invariant to a temperature offset would have thrown away the physics that section 170 adopted, so
the non-invariance is asserted too.

    .venv/Scripts/python.exe -m unittest discover -s tests -p test_v21_relative_dynamics.py
"""
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
import final_pipeline as fp
import an65_v21_relative_dynamics as a65

_G = {}


def grid():
    if not _G:
        g = fp.load_grid()
        _G['g'], _G['y'], _G['F'] = g, g[fp.TARGET], fp.make_features(g)
    return _G['g'], _G['y'], _G['F']


class OffsetInvariance(unittest.TestCase):
    """The property the arm is built for."""

    def shifted(self, col, amount):
        g, _, _ = grid()
        g2 = g.copy()
        g2[col] = g2[col] + amount
        return fp.make_features(g2)

    # Exact bit-equality is not achievable and asking for it would be a misunderstanding: the
    # offset itself is not exactly representable, so `x + 25.0` already differs from `x` by more
    # than a rescaled copy in its last bits before any design column is computed. 1e-9 %RH-per-
    # hPa is roughly seven orders of magnitude below the smallest change these columns describe.
    ATOL = 1e-9

    def test_a_pressure_offset_moves_nothing(self):
        _, _, F = grid()
        F2 = self.shifted('pressure', 25.0)
        for h, _lam in fp.INC_SPEC:
            a, b = a65.rel_design(F, h), a65.rel_design(F2, h)
            self.assertEqual(list(a.columns), list(b.columns))
            np.testing.assert_allclose(a.to_numpy(), b.to_numpy(), equal_nan=True,
                                       atol=self.ATOL, rtol=0)

    def test_a_co2_offset_moves_nothing(self):
        _, _, F = grid()
        F2 = self.shifted('co2', -60.0)
        for h, _lam in fp.INC_SPEC:
            np.testing.assert_allclose(a65.rel_design(F, h).to_numpy(),
                                       a65.rel_design(F2, h).to_numpy(),
                                       equal_nan=True, atol=self.ATOL, rtol=0)

    def test_the_residual_deviation_is_rounding_and_not_retained_level(self):
        """The distinguishing test. A column that still carried absolute pressure would move
        roughly IN PROPORTION to the offset; rounding noise stays microscopic. A 40000x larger
        offset must not produce a 40000x larger deviation in any meaningful sense -- and must
        stay far below anything that could steer a split."""
        _, _, F = grid()
        base = a65.rel_design(F, 1).to_numpy()
        dev = []
        for amount in (25.0, 1e6):
            b = a65.rel_design(self.shifted('pressure', amount), 1).to_numpy()
            d = np.abs(base - b)
            dev.append(float(np.nanmax(d)))
        self.assertLess(dev[0], self.ATOL)
        self.assertLess(dev[1], 1e-6)
        # A column still carrying absolute pressure would grow by the full offset ratio,
        # 1e6/25 = 40000x. Rounding grows far more slowly; require it to be at most 5% of
        # proportional, which is ~200x here against the 40000x a real dependency would give.
        offset_ratio = 1e6 / 25.0
        self.assertLess(dev[1] / max(dev[0], 1e-18), 0.05 * offset_ratio)

    def test_a_pressure_offset_DOES_move_the_incumbent_design(self):
        """The control that makes the two tests above mean something: the design this replaces
        is not offset invariant, which is the whole reason for the arm."""
        _, _, F = grid()
        F2 = self.shifted('pressure', 25.0)
        a = fp.increment_design(F, 1, fp.INC_PHYS_COLS, True, True)
        b = fp.increment_design(F2, 1, fp.INC_PHYS_COLS, True, True)
        self.assertFalse(np.allclose(a.to_numpy(), b.to_numpy(), equal_nan=True))

    def test_a_temperature_offset_DOES_move_the_relative_design(self):
        """Deliberate: es(T) is a function of the actual temperature."""
        _, _, F = grid()
        F2 = self.shifted('air_temperature', 3.0)
        a, b = a65.rel_design(F, 1), a65.rel_design(F2, 1)
        self.assertFalse(np.allclose(a.to_numpy(), b.to_numpy(), equal_nan=True))
        # ...but its DIFFERENCE columns are still invariant, which is what they are for.
        for k in a65.DIFF_LAGS:
            np.testing.assert_allclose(a['dT_%d' % k].to_numpy(), b['dT_%d' % k].to_numpy(),
                                       equal_nan=True, atol=1e-9)

    def test_no_absolute_pressure_or_co2_column_survives_by_name(self):
        _, _, F = grid()
        for h, _lam in fp.INC_SPEC:
            for col in a65.rel_design(F, h).columns:
                self.assertNotIn(col, ('pressure', 'co2'))
                self.assertFalse(str(col).startswith('pressure_lag'), col)
                self.assertFalse(str(col).startswith('co2_lag'), col)

    def test_every_pressure_and_co2_column_is_a_difference_range_or_spread(self):
        _, _, F = grid()
        X = a65.rel_design(F, 4)
        touched = [c for c in X.columns if 'pressure' in str(c) or 'co2' in str(c)]
        self.assertGreater(len(touched), 10)
        for c in touched:
            self.assertTrue(str(c).startswith('d') or '_rng' in str(c) or '_sd' in str(c), c)


class DesignContract(unittest.TestCase):
    def test_the_design_is_much_smaller_than_the_incumbent(self):
        _, _, F = grid()
        for h, _lam in fp.INC_SPEC:
            rel = a65.rel_design(F, h).shape[1]
            inc = fp.increment_design(F, h, fp.INC_PHYS_COLS, True, True).shape[1]
            self.assertLess(rel, inc / 2, (h, rel, inc))

    def test_the_target_never_enters_the_design(self):
        _, y, F = grid()
        X = a65.rel_design(F, 4)
        lab = y.notna()
        for c in X.columns:
            self.assertNotIn(fp.TARGET, str(c))
            s = X[c].reindex(F.index)
            ok = s.notna() & lab
            if int(ok.sum()) > 100 and float(s[ok].std()) > 0:
                self.assertLess(abs(float(np.corrcoef(s[ok], y[ok])[0, 1])), 0.999, c)

    def test_lag_k_is_exactly_k_half_hours_not_k_surviving_rows(self):
        _, _, F = grid()
        X = a65.rel_design(F, 1)
        i = F.index[900]
        for k in a65.DIFF_LAGS:
            self.assertAlmostEqual(
                X.loc[i, 'dT_%d' % k],
                F.loc[i, 'T'] - F.loc[i - pd.Timedelta(minutes=30 * k), 'T'], places=12)

    def test_the_rolling_windows_are_causal_and_never_partial(self):
        """A centred window would read the future; a partial one would be a differently-biased
        statistic wearing the same column name."""
        _, _, F = grid()
        X = a65.rel_design(F, 1)
        for w in a65.ROLL_WINS:
            col = 'pressure_rng%d' % w
            self.assertTrue(X[col].iloc[:w - 1].isna().all(), col)
            i = F.index[1000]
            window = F['pressure'].loc[i - pd.Timedelta(minutes=30 * (w - 1)):i]
            self.assertEqual(len(window), w)
            self.assertAlmostEqual(X.loc[i, col], window.max() - window.min(), places=10)

    def test_the_es_ratio_is_the_endpoint_ratio_for_this_horizon(self):
        _, _, F = grid()
        for h, _lam in fp.INC_SPEC:
            X = a65.rel_design(F, h)
            i = F.index[800]
            self.assertAlmostEqual(
                X.loc[i, 'es_ratio'],
                F.loc[i - pd.Timedelta(minutes=30 * h), 'esT'] / F.loc[i, 'esT'], places=12)


class LabelIsolation(unittest.TestCase):
    def setUp(self):
        self.g, self.y, self.F = grid()
        boundary = self.g.index[(self.g.is_test == 0).to_numpy()].max()
        self.origin = boundary - pd.Timedelta(days=15)
        self.mask = (pd.Series((self.g.is_test == 0).to_numpy(), index=self.g.index)
                     & self.y.notna() & (self.g.index <= self.origin))
        self.idx = self.g.index[(self.g.index > self.origin) & (self.g.index <= boundary)][:200]

    def test_no_training_pair_straddles_the_origin(self):
        for h, _lam in fp.INC_SPEC:
            X = a65.rel_design(self.F, h)
            tgt = (self.y - self.y.shift(h)).reindex(X.index)
            m = self.mask.reindex(X.index, fill_value=False)
            m = m & tgt.notna() & m.shift(h, fill_value=False)
            used = X.index[m]
            self.assertGreater(len(used), 500)
            self.assertLessEqual(used.max(), self.origin)
            self.assertLessEqual((used - pd.Timedelta(minutes=30 * h)).max(), self.origin)

    def test_labels_after_the_origin_change_no_prediction(self):
        rng = np.random.default_rng(67)
        y2 = self.y.copy()
        after = y2.index > self.origin
        y2[after] = 45.0 + 25.0 * rng.random(int(after.sum()))
        a = a65.fit_relative(self.F, self.y, self.mask, (fp.INC_SEED,))
        b = a65.fit_relative(self.F, y2, self.mask, (fp.INC_SEED,))
        for h, _lam in fp.INC_SPEC:
            X = a65.rel_design(self.F, h).loc[self.idx]
            np.testing.assert_array_equal(a[h][0].predict(X), b[h][0].predict(X))

    def test_the_terms_carry_no_deshrink_factor(self):
        """De-shrink is off by construction in this arm; if a factor ever appears the arm has
        silently become two changes."""
        inc = a65.fit_relative(self.F, self.y, self.mask, (fp.INC_SEED,))
        self.assertFalse(any(isinstance(k, tuple) and k[0] == 'f' for k in inc))
        terms = a65.relative_terms(self.F, self.idx, inc)
        self.assertEqual(len(terms), len(fp.INC_SPEC))
        for D, t, lam in terms:
            self.assertIsNotNone(D)
            self.assertTrue(np.isfinite(t).all())


if __name__ == '__main__':
    unittest.main()
