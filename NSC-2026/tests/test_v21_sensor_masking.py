"""Session 37, Task 1: what the sensor mask must and must not touch.

The mask changes the training distribution, so it sits exactly where a leak would be invisible:
a frame that quietly saw a post-origin label, or derived columns inconsistent with the readings
they claim to summarise, would still train and still score.

    .venv/Scripts/python.exe -m unittest discover -s tests -p test_v21_sensor_masking.py
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
import an47_v21_forward_benchmark as a47
import v21_sensor_masking as sm

_C = {}


def ctx():
    if not _C:
        g = fp.load_grid()
        name, hs, he = a47.blocks_of(g)[0]
        _C.update(g=g, origin=hs, horizon_end=he, name=name,
                  gh=g.loc[g.index <= he])
    return _C


class Eligibility(unittest.TestCase):
    def test_only_the_three_named_sensors_are_touched(self):
        c = ctx()
        out, _a = sm.masked_frame(c['gh'], 1, hi=c['origin'])
        changed = [col for col in c['gh'].columns
                   if not c['gh'][col].equals(out[col])]
        self.assertTrue(set(changed) <= set(sm.SENSORS), changed)
        self.assertEqual(sm.SENSORS, ('air_temperature', 'co2', 'pressure'))

    def test_the_index_target_and_is_test_are_untouched(self):
        c = ctx()
        out, _a = sm.masked_frame(c['gh'], 2, hi=c['origin'])
        self.assertTrue(out.index.equals(c['gh'].index))
        pd.testing.assert_series_equal(out[fp.TARGET], c['gh'][fp.TARGET])
        pd.testing.assert_series_equal(out['is_test'], c['gh']['is_test'])

    def test_an_already_missing_cell_is_not_eligible(self):
        c = ctx()
        elig = sm.eligible_mask(c['gh'], 'co2', hi=c['origin'])
        raw_missing = c['gh']['co2'].isna().to_numpy()
        self.assertFalse((elig & raw_missing).any())

    def test_a_hampel_rejected_spike_is_not_eligible(self):
        c = ctx()
        g2 = c['gh'].copy()
        pos = np.flatnonzero(np.asarray(g2.index <= pd.Timestamp(c['origin'])))[500]
        g2.iloc[pos, g2.columns.get_loc('air_temperature')] = 900.0
        elig = sm.eligible_mask(g2, 'air_temperature', hi=c['origin'])
        self.assertFalse(bool(elig[pos]))

    def test_test_rows_and_grid_holes_are_not_eligible(self):
        c = ctx()
        for s in sm.SENSORS:
            elig = sm.eligible_mask(c['gh'], s)
            self.assertFalse((elig & (c['gh']['is_test'] != 0).to_numpy()).any(), s)

    def test_nothing_after_the_origin_is_masked_for_training(self):
        c = ctx()
        _out, a = sm.masked_frame(c['gh'], 3, hi=c['origin'])
        hit = a.loc[a.masked]
        self.assertGreater(len(hit), 0)
        self.assertLessEqual(pd.DatetimeIndex(hit.timestamp).max(), pd.Timestamp(c['origin']))

    def test_the_stress_window_masks_only_inside_the_horizon(self):
        c = ctx()
        _out, a = sm.masked_frame(c['gh'], 4, lo=c['origin'], hi=c['horizon_end'])
        hit = a.loc[a.masked]
        self.assertGreater(len(hit), 0)
        self.assertGreater(pd.DatetimeIndex(hit.timestamp).min(), pd.Timestamp(c['origin']))
        self.assertLessEqual(pd.DatetimeIndex(hit.timestamp).max(), pd.Timestamp(c['horizon_end']))


class Strength(unittest.TestCase):
    def test_p_zero_is_the_identity(self):
        c = ctx()
        out, a = sm.masked_frame(c['gh'], 5, hi=c['origin'], p=0.0)
        assert_frame_equal(out, c['gh'])
        self.assertEqual(int(a.masked.sum()), 0)

    def test_p_one_masks_every_eligible_cell_and_nothing_else(self):
        c = ctx()
        out, a = sm.masked_frame(c['gh'], 6, hi=c['origin'], p=1.0)
        for s in sm.SENSORS:
            elig = sm.eligible_mask(c['gh'], s, hi=c['origin'])
            still = out[s].notna().to_numpy()
            self.assertFalse((elig & still).any(), s)
        self.assertEqual(int(a.masked.sum()), int(a.eligible.sum()))

    def test_the_realised_rate_is_near_the_requested_one(self):
        c = ctx()
        _out, a = sm.masked_frame(c['gh'], 7, hi=c['origin'])
        rep = sm.mask_report(a)
        self.assertTrue(((rep.rate > 0.03) & (rep.rate < 0.07)).all(), rep.to_dict())
        self.assertEqual(sm.P_MASK, 0.05)

    def test_the_frozen_seeds_are_the_documented_ones(self):
        self.assertEqual(sm.TRAIN_SEEDS,
                         (2026090701, 2026090702, 2026090703, 2026090704, 2026090705))
        self.assertEqual(sm.STRESS_SEEDS, (2026090791, 2026090792, 2026090793))
        self.assertEqual(len(sm.TRAIN_SEEDS), len(fp.SEEDS_FIT))


class Determinism(unittest.TestCase):
    def test_the_draw_does_not_depend_on_row_order_or_frame_extent(self):
        c = ctx()
        _o1, a1 = sm.masked_frame(c['gh'], 8, hi=c['origin'])
        short = c['gh'].loc[c['gh'].index <= pd.Timestamp(c['origin'])]
        _o2, a2 = sm.masked_frame(short, 8, hi=c['origin'])
        h1 = set(map(tuple, a1.loc[a1.masked, ['sensor', 'timestamp']].to_numpy()))
        h2 = set(map(tuple, a2.loc[a2.masked, ['sensor', 'timestamp']].to_numpy()))
        self.assertTrue(h2 <= h1)
        self.assertGreater(len(h2), 0)

    def test_two_calls_give_the_same_cells(self):
        c = ctx()
        _o1, a1 = sm.masked_frame(c['gh'], 9, hi=c['origin'])
        _o2, a2 = sm.masked_frame(c['gh'], 9, hi=c['origin'])
        self.assertEqual(sm.audit_digest(a1), sm.audit_digest(a2))

    def test_different_seeds_give_different_cells(self):
        c = ctx()
        _o1, a1 = sm.masked_frame(c['gh'], 10, hi=c['origin'])
        _o2, a2 = sm.masked_frame(c['gh'], 11, hi=c['origin'])
        self.assertNotEqual(sm.audit_digest(a1), sm.audit_digest(a2))

    def test_each_sensor_draws_independently(self):
        c = ctx()
        _o, a = sm.masked_frame(c['gh'], 12, hi=c['origin'])
        per = {s: set(d.loc[d.masked].timestamp) for s, d in a.groupby('sensor')}
        t, co2 = per['air_temperature'], per['co2']
        self.assertLess(len(t & co2), 0.5 * min(len(t), len(co2)))


class DerivedConsistency(unittest.TestCase):
    """Derived columns must describe the readings that survived, not the ones that were hidden."""

    def test_the_whole_feature_frame_is_rebuilt_from_the_masked_raw(self):
        c = ctx()
        F0, F1, a = sm.build_views(c['g'], c['horizon_end'], c['origin'], 13)
        self.assertTrue(F0.index.equals(F1.index))
        self.assertEqual(list(F0.columns), list(F1.columns))
        moved = [col for col in F0.columns
                 if not np.allclose(F0[col].to_numpy(float), F1[col].to_numpy(float),
                                    rtol=0, atol=1e-12, equal_nan=True)]
        # A masked temperature must move T AND everything derived from it.
        for col in ('T', 'esT', 'air_temperature_c24h', 'T_min48'):
            self.assertIn(col, moved)

    def test_masking_a_column_of_f_directly_would_not_do_this(self):
        # The discriminating half: hiding F['T'] leaves esT and the rolling block describing a
        # history that no longer exists. Rebuilding from raw is what keeps them consistent.
        c = ctx()
        F0, F1, _a = sm.build_views(c['g'], c['horizon_end'], c['origin'], 14)
        d_T = np.abs(F0['T'].to_numpy() - F1['T'].to_numpy())
        d_es = np.abs(F0['esT'].to_numpy() - F1['esT'].to_numpy())
        self.assertGreater(d_T.max(), 0.0)
        self.assertGreater(d_es.max(), 0.0)
        self.assertGreater(float(np.corrcoef(d_T, d_es)[0, 1]), 0.5)

    def test_the_cleaner_refills_the_hole_so_the_frame_stays_finite(self):
        c = ctx()
        _F0, F1, _a = sm.build_views(c['g'], c['horizon_end'], c['origin'], 15)
        for col in ('T', 'esT', 'co2', 'pressure'):
            self.assertTrue(np.isfinite(F1[col].to_numpy(float)).all(), col)


class Isolation(unittest.TestCase):
    def test_labels_after_the_origin_cannot_change_the_mask(self):
        c = ctx()
        g2 = c['gh'].copy()
        g2.loc[g2.index > pd.Timestamp(c['origin']), fp.TARGET] = 1.0
        _o1, a1 = sm.masked_frame(c['gh'], 16, hi=c['origin'])
        _o2, a2 = sm.masked_frame(g2, 16, hi=c['origin'])
        self.assertEqual(sm.audit_digest(a1), sm.audit_digest(a2))

    def test_the_target_is_never_read_when_choosing_cells(self):
        c = ctx()
        g2 = c['gh'].copy()
        g2[fp.TARGET] = np.nan
        _o1, a1 = sm.masked_frame(c['gh'], 17, hi=c['origin'])
        _o2, a2 = sm.masked_frame(g2, 17, hi=c['origin'])
        self.assertEqual(sm.audit_digest(a1), sm.audit_digest(a2))

    def test_sensors_after_the_endpoint_do_not_reach_the_frame(self):
        c = ctx()
        g2 = c['g'].copy()
        after = g2.index > pd.Timestamp(c['horizon_end'])
        for s in sm.SENSORS:
            g2.loc[after, s] = g2.loc[after, s] + 60.0
        F0a, F1a, _ = sm.build_views(c['g'], c['horizon_end'], c['origin'], 18)
        F0b, F1b, _ = sm.build_views(g2, c['horizon_end'], c['origin'], 18)
        assert_frame_equal(F0a, F0b)
        assert_frame_equal(F1a, F1b)

    def test_the_original_view_is_the_incumbent_frame(self):
        c = ctx()
        F0, _F1, _a = sm.build_views(c['g'], c['horizon_end'], c['origin'], 19)
        _gh, F_ref = a47.frame_at(c['g'], c['horizon_end'])
        assert_frame_equal(F0, F_ref)


if __name__ == '__main__':
    unittest.main()
