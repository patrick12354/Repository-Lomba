"""Session 33, Task 2: what the 72 local-shape features must mean.

These tests exist to keep a mistake in the feature definition from being read as a result about
the weather. Two kinds of check:

* **Mechanism.** Feed a trajectory whose shape is known by construction -- a ramp, a zigzag, a
  delayed copy of another channel -- and require the statistic to report the value the
  definition implies. A test that merely re-ran the implementation and compared would pass on a
  wrong definition, which is the failure mode section 181 met.
* **Isolation.** RH may not move any feature. Exogenous recorded after the horizon may not move
  any feature. A translated pressure or CO2 channel may not move the shape block at all.

    .venv/Scripts/python.exe -m unittest discover -s tests -p test_v21_local_shape.py
"""
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
import final_pipeline as fp
import v21_local_shape as ls

N_SLOTS = 480                       # 10 days: long enough for a full past24h and future24h
MID = N_SLOTS // 2


# `fp.hampel` takes its scale from the rolling 75th percentile of |x - median(x)|, and the
# median of seven consecutive points of a MONOTONE stretch is exactly the middle point. On a
# noiseless sine that makes the deviation zero everywhere except at the turning points, the
# scale collapses toward zero, and the filter then rejects the sine's own peaks -- 66 of 480
# slots. Real sensors carry enough noise for the deviation to be nonzero everywhere, so the
# fixtures below carry some too. Without it these tests would be measuring an artefact of
# synthetic data rather than the feature definitions.
NOISE = dict(air_temperature=0.30, co2=1.20, pressure=0.05)


def _noise(name, n, seed):
    return np.random.default_rng(seed).standard_normal(n) * NOISE[name]


def synthetic(T=None, co2=None, pressure=None, n=N_SLOTS):
    """A grid with the columns `clean_exog` touches and nothing that could be mistaken for RH.

    Defaults are deliberately boring: constant soil and daily blocks, a monotone counter for the
    cumulative columns. Only the three channels the shape block reads are ever varied, and a
    channel passed in explicitly is used verbatim -- a test that needs an exact trajectory gets
    one.
    """
    idx = pd.date_range('2023-07-01', periods=n, freq='30min')
    d = {}
    d['air_temperature'] = np.asarray(T, float) if T is not None else \
        20.0 + 5.0 * np.sin(2 * np.pi * np.arange(n) / 48.0) + _noise('air_temperature', n, 11)
    d['co2'] = np.asarray(co2, float) if co2 is not None else \
        400.0 + 20.0 * np.cos(2 * np.pi * np.arange(n) / 48.0) + _noise('co2', n, 12)
    d['pressure'] = np.asarray(pressure, float) if pressure is not None else \
        1010.0 + np.linspace(0, 2, n) + _noise('pressure', n, 13)
    for c in fp.SOIL:
        d[c] = np.full(n, 15.0)
    for c in fp.DAILY:
        d[c] = np.full(n, 12.0)
    for c in fp.CUMUL:
        d[c] = np.arange(n, dtype=float)
    d[fp.TARGET] = 60.0 + 5.0 * np.cos(2 * np.pi * np.arange(n) / 48.0)
    d['is_test'] = np.zeros(n)
    return pd.DataFrame(d, index=idx)


def build(g, end=None):
    return ls.build_local_shape(g, end if end is not None else g.index.max())


class Contract(unittest.TestCase):
    def test_the_block_is_60_shape_and_12_quality_columns_in_a_frozen_order(self):
        F = build(synthetic())
        self.assertEqual(sum(c.startswith('shape_') for c in F.columns), 60)
        self.assertEqual(sum(c.startswith('quality_') for c in F.columns), 12)
        self.assertEqual(list(F.columns), ls.all_columns())
        self.assertEqual(len(set(F.columns)), 72)

    def test_the_index_is_the_grid_truncated_at_the_horizon(self):
        g = synthetic()
        end = g.index[300]
        F = build(g, end)
        self.assertTrue(F.index.equals(g.index[:301]))

    def test_nothing_is_infinite(self):
        F = build(synthetic())
        self.assertFalse(np.isinf(F.to_numpy(float)).any())


class Mechanism(unittest.TestCase):
    """Trajectories whose four statistics are known before the code runs."""

    def test_a_linear_ramp_reports_its_slope_per_hour_and_nothing_else(self):
        # +0.25 C per slot is +0.5 C per hour. A straight line has no residual, never reverses,
        # and is one single run.
        T = 20.0 + 0.25 * np.arange(N_SLOTS)
        F = build(synthetic(T=T))
        r = F.iloc[MID]
        for region in ('past6h', 'past24h', 'future6h', 'future24h'):
            self.assertAlmostEqual(r[f'shape_T_{region}_slope'], 0.5, places=9, msg=region)
            self.assertAlmostEqual(r[f'shape_T_{region}_rms'], 0.0, places=9, msg=region)
            self.assertAlmostEqual(r[f'shape_T_{region}_turn'], 0.0, places=12, msg=region)
            self.assertAlmostEqual(r[f'shape_T_{region}_run'], 1.0, places=12, msg=region)

    def test_a_zigzag_separates_order_from_amplitude(self):
        # Same amplitude as a ramp step, opposite ordering: every difference reverses the last.
        T = 20.0 + 0.25 * (np.arange(N_SLOTS) % 2)
        F = build(synthetic(T=T))
        r = F.iloc[MID]
        for region in ('past24h', 'future24h'):
            self.assertLess(abs(r[f'shape_T_{region}_slope']), 0.02, region)
            self.assertAlmostEqual(r[f'shape_T_{region}_turn'], 1.0, places=12, msg=region)
            self.assertLess(r[f'shape_T_{region}_run'], 0.1, region)
            self.assertGreater(r[f'shape_T_{region}_rms'], 0.05, region)

    def test_a_ramp_and_a_zigzag_of_equal_range_differ_only_in_order(self):
        # The point of the block: a summary feature that sees min, max and range cannot tell
        # these apart, and `turn`/`run` must.
        n = N_SLOTS
        ramp = np.concatenate([np.linspace(20, 25, n // 2), np.linspace(25, 20, n - n // 2)])
        zig = ramp.copy()
        zig[1::2] += 0.4
        zig[0::2] -= 0.4
        a = build(synthetic(T=ramp)).iloc[MID]
        b = build(synthetic(T=zig)).iloc[MID]
        self.assertAlmostEqual(a['shape_T_past24h_turn'], 0.0, places=12)
        self.assertAlmostEqual(b['shape_T_past24h_turn'], 1.0, places=12)
        self.assertGreater(a['shape_T_past24h_run'], 0.9)
        self.assertLess(b['shape_T_past24h_run'], 0.1)

    def test_a_plateau_ends_a_run_without_counting_as_a_reversal(self):
        # Rise, hold exactly flat, rise again. The rises carry noise well below the step so
        # every nonzero difference is still positive; the plateau's differences are exact zeros.
        # Those zeros must end the run without being counted as reversals.
        rise = 0.1 * np.arange(200) + _noise('air_temperature', 200, 21) * 0.05
        tail = np.arange(N_SLOTS - 280)
        T = np.concatenate([rise, np.full(80, rise[-1]),
                            rise[-1] + 0.1 * tail + _noise('air_temperature', len(tail), 22) * 0.05])
        F = build(synthetic(T=T))
        r = F.iloc[240]                      # centred inside the plateau
        self.assertAlmostEqual(r['shape_T_past24h_turn'], 0.0, places=12)
        self.assertLess(r['shape_T_past24h_run'], 1.0)
        self.assertGreater(r['shape_T_past24h_run'], 0.0)

    def test_slope_is_per_hour_not_per_slot(self):
        T = 20.0 + 1.0 * np.arange(N_SLOTS)           # +1 per slot = +2 per hour
        r = build(synthetic(T=T)).iloc[MID]
        self.assertAlmostEqual(r['shape_T_past6h_slope'], 2.0, places=9)


class LagConvention(unittest.TestCase):
    def test_lag_sign_convention(self):
        # co2 repeats the temperature trace four slots LATER. The feature correlates dT at k
        # with dCO2 at k - lag, so the copy shows up at lag -4 and nowhere else.
        rng = np.random.default_rng(0)
        walk = np.cumsum(rng.standard_normal(N_SLOTS)) * 0.2 + 20.0
        co2 = np.concatenate([np.full(4, walk[0]), walk[:-4]]) * 10.0
        F = build(synthetic(T=walk, co2=co2))
        r = F.iloc[MID]
        self.assertGreater(r['shape_corr_T_co2_lagm4_past24h'], 0.98)
        self.assertLess(abs(r['shape_corr_T_co2_lag0_past24h']), 0.5)
        self.assertLess(abs(r['shape_corr_T_co2_lagp4_past24h']), 0.5)

    def test_no_lag_is_searched_over(self):
        # All three lags are emitted for both pairs and both regions; none is selected.
        cols = [c for c in ls.shape_columns() if c.startswith('shape_corr_')]
        self.assertEqual(len(cols), 12)
        for tag in ('lagm4', 'lag0', 'lagp4'):
            self.assertEqual(sum(tag in c for c in cols), 4)

    def test_a_constant_channel_correlates_zero_not_nan(self):
        F = build(synthetic(pressure=np.full(N_SLOTS, 1010.0)))
        r = F.iloc[MID]
        self.assertEqual(r['shape_corr_T_pressure_lag0_past24h'], 0.0)

    def test_a_channel_interpolated_across_a_gap_correlates_zero_not_rounding_noise(self):
        # `clean_exog` fills a hole with a straight line, whose first differences agree only to
        # about 1e-13 rather than exactly. Correlating that residue against a real signal used
        # to return an arbitrary sign that moved when the channel was shifted by a constant.
        # A straight line has no shape, so the answer is zero.
        # The hole has to be longer than the 48-slot window, or the row still sees real motion
        # at one end and the correlation it reports is a genuine one.
        g = synthetic()
        g.iloc[100:201, g.columns.get_loc('pressure')] = np.nan
        F = build(g)
        col = 'shape_corr_T_pressure_lag0_past24h'
        self.assertEqual(F.iloc[160][col], 0.0)
        h = g.copy()
        h['pressure'] = h['pressure'] + 100.0
        self.assertEqual(build(h).iloc[160][col], 0.0)
        # The same window's own shape statistics still report the straight line honestly.
        self.assertAlmostEqual(F.iloc[160]['shape_pressure_past24h_rms'], 0.0, places=9)


class Invariance(unittest.TestCase):
    def test_translating_pressure_and_co2_leaves_every_shape_feature_alone(self):
        # An additive offset changes the incumbent F -- levels are features there -- but slope,
        # detrended RMS, turning rate, run fraction and correlation are all translation
        # invariant, so the shape block must not move. This is a claim about THIS block only.
        g = synthetic()
        h = g.copy()
        h['pressure'] = h['pressure'] + 100.0
        h['co2'] = h['co2'] + 100.0
        a, b = build(g), build(h)
        cols = ls.shape_columns()
        np.testing.assert_allclose(a[cols].to_numpy(float), b[cols].to_numpy(float),
                                   rtol=0, atol=1e-9)

    def test_scaling_a_channel_leaves_the_order_statistics_alone(self):
        g = synthetic()
        h = g.copy()
        h['co2'] = h['co2'] * 3.0
        a, b = build(g), build(h)
        order = [c for c in ls.shape_columns()
                 if c.startswith('shape_co2_') and c.endswith(('_turn', '_run'))]
        self.assertTrue(order)
        np.testing.assert_allclose(a[order].to_numpy(float), b[order].to_numpy(float),
                                   rtol=0, atol=1e-9)


class Isolation(unittest.TestCase):
    def test_the_block_is_target_blind(self):
        g = synthetic()
        before = build(g)
        altered = g.copy()
        altered[fp.TARGET] = np.nan
        after = build(altered)
        assert_frame_equal(before, after)

    def test_a_different_target_trajectory_changes_nothing(self):
        g = synthetic()
        altered = g.copy()
        altered[fp.TARGET] = np.linspace(5, 95, len(g))
        assert_frame_equal(build(g), build(altered))

    def test_exogenous_after_the_horizon_changes_nothing(self):
        g = synthetic()
        end = g.index[300]
        before = build(g, end)
        altered = g.copy()
        altered.iloc[301:, altered.columns.get_loc('air_temperature')] += 50.0
        altered.iloc[301:, altered.columns.get_loc('co2')] *= 4.0
        after = build(altered, end)
        assert_frame_equal(before, after)

    def test_truncating_first_gives_the_same_answer_as_passing_the_horizon(self):
        g = synthetic()
        end = g.index[300]
        assert_frame_equal(build(g, end), build(g.loc[:end], end))


class Boundaries(unittest.TestCase):
    def test_a_window_without_support_is_nan_not_a_short_window(self):
        F = build(synthetic())
        # First row: no past at all. Last row: no future at all.
        self.assertTrue(np.isnan(F.iloc[0]['shape_T_past24h_slope']))
        self.assertTrue(np.isnan(F.iloc[0]['shape_T_past6h_slope']))
        self.assertTrue(np.isnan(F.iloc[-1]['shape_T_future24h_slope']))
        self.assertTrue(np.isnan(F.iloc[-1]['shape_T_future6h_slope']))

    def test_the_support_floor_is_six_points(self):
        F = build(synthetic())
        # past6h spans offsets -12..-1, so row 5 sees 5 points and row 6 sees 6.
        self.assertTrue(np.isnan(F.iloc[5]['shape_T_past6h_slope']))
        self.assertTrue(np.isfinite(F.iloc[6]['shape_T_past6h_slope']))

    def test_the_future_window_stops_at_the_horizon_and_does_not_wrap(self):
        g = synthetic()
        end = g.index[300]
        F = build(g, end)
        # The row at the horizon has no future; the row 48 slots before it is the last one
        # with a complete future24h.
        self.assertTrue(np.isnan(F.iloc[300]['shape_T_future24h_slope']))
        self.assertTrue(np.isfinite(F.iloc[300 - 48]['shape_T_future24h_slope']))

    def test_a_constant_channel_reports_zero_motion_not_missing(self):
        F = build(synthetic(pressure=np.full(N_SLOTS, 1010.0)))
        r = F.iloc[MID]
        self.assertAlmostEqual(r['shape_pressure_past24h_slope'], 0.0, places=12)
        self.assertAlmostEqual(r['shape_pressure_past24h_rms'], 0.0, places=12)
        self.assertEqual(r['shape_pressure_past24h_turn'], 0.0)
        self.assertEqual(r['shape_pressure_past24h_run'], 0.0)

    def test_a_hole_of_thirteen_slots_is_interpolated_by_the_incumbent_cleaner(self):
        # Section 187: repaired rows are not worse in aggregate, so the shape statistics keep
        # the cleaned values. What must NOT happen is a NaN leaking into the shape block from a
        # gap the cleaner already filled.
        T = 20.0 + 5.0 * np.sin(2 * np.pi * np.arange(N_SLOTS) / 48.0)
        g = synthetic(T=T)
        g.iloc[MID - 6:MID + 7, g.columns.get_loc('air_temperature')] = np.nan
        F = build(g)
        self.assertTrue(np.isfinite(F.iloc[MID]['shape_T_past24h_slope']))
        self.assertTrue(np.isfinite(F.iloc[MID]['shape_T_past24h_rms']))


class Quality(unittest.TestCase):
    def test_quality_separates_an_observation_from_a_reconstruction(self):
        g = synthetic()
        g.iloc[MID - 6:MID + 7, g.columns.get_loc('air_temperature')] = np.nan
        F = build(g)
        self.assertEqual(F.iloc[MID]['quality_T_observed_now'], 0.0)
        self.assertEqual(F.iloc[MID - 20]['quality_T_observed_now'], 1.0)
        # 13 reconstructed slots inside a 97-slot neighbourhood.
        self.assertAlmostEqual(F.iloc[MID]['quality_T_repaired_fraction_24h'], 13 / 97, places=9)
        # The nearest surviving readings are seven slots either side of the centre.
        self.assertAlmostEqual(F.iloc[MID]['quality_T_gap_past_hours'], 3.5, places=9)
        self.assertAlmostEqual(F.iloc[MID]['quality_T_gap_future_hours'], 3.5, places=9)

    def test_a_hampel_rejected_spike_counts_as_reconstructed_not_observed(self):
        g = synthetic()
        g.iloc[MID, g.columns.get_loc('air_temperature')] = 500.0
        F = build(g)
        self.assertEqual(F.iloc[MID]['quality_T_observed_now'], 0.0)
        self.assertGreater(F.iloc[MID]['quality_T_repaired_fraction_24h'], 0.0)

    def test_a_fully_observed_channel_reports_no_gap_and_no_repair(self):
        F = build(synthetic())
        r = F.iloc[MID]
        for ch in ('T', 'co2', 'pressure'):
            self.assertEqual(r[f'quality_{ch}_observed_now'], 1.0)
            self.assertEqual(r[f'quality_{ch}_gap_past_hours'], 0.0)
            self.assertEqual(r[f'quality_{ch}_gap_future_hours'], 0.0)
            self.assertEqual(r[f'quality_{ch}_repaired_fraction_24h'], 0.0)

    def test_gaps_are_capped_at_forty_eight_hours(self):
        g = synthetic()
        col = g.columns.get_loc('co2')
        g.iloc[10:400, col] = np.nan
        F = build(g)
        self.assertEqual(F.iloc[300]['quality_co2_gap_past_hours'], 48.0)
        self.assertEqual(F.iloc[100]['quality_co2_gap_future_hours'], 48.0)

    def test_quality_never_reads_the_target(self):
        g = synthetic()
        altered = g.copy()
        altered[fp.TARGET] = np.nan
        cols = ls.quality_columns()
        np.testing.assert_array_equal(build(g)[cols].to_numpy(float),
                                      build(altered)[cols].to_numpy(float))


class RealGrid(unittest.TestCase):
    """One pass over the competition grid: the block must survive real missingness."""

    def test_the_block_builds_on_the_real_frame_and_reports_real_repair(self):
        g = fp.load_grid()
        end = g.index[(g.is_test == 0).to_numpy()].max()
        F = ls.build_local_shape(g, end)
        self.assertEqual(F.shape[1], 72)
        self.assertFalse(np.isinf(F.to_numpy(float)).any())
        interior = F.iloc[96:-96]
        for c in ls.shape_columns():
            self.assertTrue(np.isfinite(interior[c].to_numpy(float)).all(), c)
        # The raw grid really is about a tenth missing; if this ever reads 0 the provenance
        # mask has silently started looking at cleaned values instead of raw ones.
        self.assertGreater(F['quality_T_repaired_fraction_24h'].mean(), 0.01)
        self.assertLess(F['quality_T_repaired_fraction_24h'].mean(), 0.5)

    def test_translation_invariance_holds_on_the_real_frame(self):
        # The synthetic version of this check runs on data the incumbent cleaner treats
        # differently from real readings. This is the claim that matters: on the actual sensor
        # record, moving pressure and CO2 by a constant leaves all 60 shape features alone.
        g = fp.load_grid()
        end = g.index[(g.is_test == 0).to_numpy()].max()
        h = g.copy()
        h['pressure'] = h['pressure'] + 100.0
        h['co2'] = h['co2'] + 100.0
        cols = ls.shape_columns()
        a = ls.build_local_shape(g, end)[cols].to_numpy(float)
        b = ls.build_local_shape(h, end)[cols].to_numpy(float)
        np.testing.assert_allclose(a, b, rtol=0, atol=1e-8)


if __name__ == '__main__':
    unittest.main()
