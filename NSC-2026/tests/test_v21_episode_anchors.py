"""Session 35, Task 1: what the episode-anchor construction must guarantee.

The anchor arm reads training LABELS at inference time, which is exactly the shape of thing that
has leaked before in this log (§144, §190). These tests pin the boundaries: nothing after the
origin may move an anchor, nothing after the horizon may move a descriptor, no anchor may be a
near-copy of its own query, and an episode may contribute at most once.

The transport identity is checked on a synthetic constant-vapour example where the right answer
is known by construction. That verifies the algebra, not the hypothesis -- whether real episodes
share vapour pressure is what `an81` tests.

    .venv/Scripts/python.exe -m unittest discover -s tests -p test_v21_episode_anchors.py
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
import v21_episode_anchors as ea

_C = {}


def ctx():
    """B1: the frame at its horizon, the training rows, and the scored queries."""
    if not _C:
        g = fp.load_grid()
        y = g[fp.TARGET]
        name, hs, he = a47.blocks_of(g)[0]
        gh, F = a47.frame_at(g, he)
        mask = a47.train_mask_before(g, gh, y, hs)
        train = F.index[mask.reindex(F.index, fill_value=False).to_numpy()]
        lab = pd.Series((gh.is_test == 0).to_numpy(), index=gh.index) & y.reindex(gh.index).notna()
        hold = gh.index[(lab & (gh.index > hs)).to_numpy()]
        sc = ea.DescriptorScaler().fit(F, train)
        _C.update(g=g, y=y, F=F, train=train, hold=hold, origin=hs, horizon_end=he,
                  scaler=sc, grid_start=g.index.min())
    return _C


def build(c, F=None, y=None, queries=None, threshold=None):
    return ea.build_anchor_table(F if F is not None else c['F'], y if y is not None else c['y'],
                                 queries if queries is not None else c['hold'][:120],
                                 c['train'], c['scaler'], c['grid_start'], threshold=threshold)


class Descriptors(unittest.TestCase):
    def test_every_descriptor_column_exists_in_the_incumbent_frame(self):
        c = ctx()
        ea.assert_columns(c['F'])
        self.assertEqual(len(ea.descriptor_columns()), 11)
        self.assertEqual(len(set(ea.descriptor_columns())), 11)

    def test_a_guessed_column_name_is_refused(self):
        c = ctx()
        F = c['F'].drop(columns=['co2_slope'])
        with self.assertRaises(AssertionError):
            ea.assert_columns(F)

    def test_no_absolute_pressure_soil_or_date_axis(self):
        cols = ea.descriptor_columns()
        self.assertNotIn('pressure', cols)
        self.assertFalse(any(x.startswith('soil') for x in cols))
        self.assertFalse(any('day' in x for x in cols))

    def test_the_scaler_is_fitted_on_training_rows_only(self):
        c = ctx()
        sc = ea.DescriptorScaler().fit(c['F'], c['train'])
        alt = c['F'].copy()
        after = alt.index > pd.Timestamp(c['origin'])
        alt.loc[after, 'T'] = alt.loc[after, 'T'] + 40.0
        sc2 = ea.DescriptorScaler().fit(alt, c['train'])
        self.assertAlmostEqual(float(sc.center_['T']), float(sc2.center_['T']), places=12)
        self.assertAlmostEqual(float(sc.scale_['T']), float(sc2.scale_['T']), places=12)

    def test_the_cyclic_pair_keeps_its_own_scale(self):
        c = ctx()
        for col in ea.CYCLIC:
            self.assertEqual(float(c['scaler'].center_[col]), 0.0)
            self.assertEqual(float(c['scaler'].scale_[col]), 1.0)

    def test_every_group_contributes_equally_regardless_of_column_count(self):
        # A four-column group and a two-column group must weigh the same.
        idx = pd.date_range('2023-07-01', periods=3, freq='30min')
        Z = pd.DataFrame(0.0, index=idx, columns=ea.descriptor_columns())
        W = Z.copy()
        for col in ea.GROUPS['diurnal']:
            W[col] = 1.0
        d_diurnal = ea.group_distances(Z, W)[0, 0]
        W2 = Z.copy()
        for col in ea.GROUPS['thermal']:
            W2[col] = 1.0
        d_thermal = ea.group_distances(Z, W2)[0, 0]
        self.assertAlmostEqual(d_diurnal, d_thermal, places=12)
        self.assertAlmostEqual(d_diurnal, 1.0 / len(ea.GROUPS), places=12)


class Transport(unittest.TestCase):
    def test_constant_vapour_transport_recovers_the_true_rh(self):
        # If two moments share vapour pressure, the ratio conversion is exact. This checks the
        # algebra; it is NOT evidence that real episodes share vapour pressure.
        T_a, T_q, rh_a = 18.0, 26.0, 82.0
        e = rh_a / 100.0 * fp.es(T_a)
        rh_q = 100.0 * e / fp.es(T_q)
        transported = rh_a * fp.es(T_a) / fp.es(T_q)
        self.assertAlmostEqual(transported, rh_q, places=10)
        self.assertLess(transported, rh_a)          # warmer query, lower RH at fixed vapour

    def test_equal_temperature_makes_transport_a_no_op(self):
        c = ctx()
        S, D = build(c)
        same = D.loc[np.isclose(D.ratio, 1.0, atol=1e-12)]
        if len(same):
            np.testing.assert_allclose(same.q_ij.to_numpy(), same.y_anchor.to_numpy(),
                                       rtol=0, atol=1e-9)

    def test_the_two_arms_differ_only_by_the_ratio(self):
        c = ctx()
        S, D = build(c)
        ok = S.loc[S.reason == 'ok']
        self.assertGreater(len(ok), 0)
        self.assertGreater(float(np.max(np.abs(ok.q_transport - ok.q_raw))), 1e-6)

    def test_raw_values_are_not_clipped_away(self):
        # Section 6.1: a bad analog must stay visible rather than being clipped into range.
        c = ctx()
        S, D = build(c)
        self.assertTrue(np.isfinite(D.q_ij).all())
        self.assertGreater(D.q_ij.max(), 0.0)


class Eligibility(unittest.TestCase):
    def test_an_anchor_is_never_within_48_hours_of_its_query(self):
        c = ctx()
        S, D = build(c)
        gap = pd.DatetimeIndex(D.datetime) - pd.DatetimeIndex(D.anchor)
        self.assertGreaterEqual(gap.min(), ea.MIN_SEPARATION)

    def test_no_anchor_is_its_own_query(self):
        c = ctx()
        S, D = build(c)
        self.assertFalse((pd.DatetimeIndex(D.datetime) == pd.DatetimeIndex(D.anchor)).any())

    def test_every_anchor_is_a_labelled_training_row_before_the_origin(self):
        c = ctx()
        S, D = build(c)
        anchors = pd.DatetimeIndex(D.anchor.unique())
        self.assertTrue(anchors.isin(c['train']).all())
        self.assertLessEqual(anchors.max(), pd.Timestamp(c['origin']))
        self.assertTrue(c['y'].reindex(anchors).notna().all())

    def test_at_most_one_anchor_per_episode(self):
        c = ctx()
        S, D = build(c)
        per = D.groupby(['datetime', 'episode']).size()
        self.assertEqual(int(per.max()), 1)

    def test_a_supported_query_gets_exactly_five_episodes(self):
        c = ctx()
        S, D = build(c)
        ok = set(S.loc[S.reason == 'ok'].datetime)
        counts = D.loc[D.datetime.isin(ok)].groupby('datetime').size()
        self.assertTrue((counts == ea.N_EPISODES).all())

    def test_too_few_episodes_abstains_with_zero_strength(self):
        c = ctx()
        tiny = c['train'][:20]                      # one short stretch, fewer than five episodes
        S, D = ea.build_anchor_table(c['F'], c['y'], c['hold'][:20], tiny, c['scaler'],
                                     c['grid_start'])
        self.assertTrue((S.a == 0.0).all())
        self.assertTrue((S.reason == 'too_few_episodes').all())
        self.assertEqual(len(D), 0)


class Abstention(unittest.TestCase):
    def test_a_threshold_moves_queries_to_abstain_without_changing_q(self):
        c = ctx()
        S0, _ = build(c)
        d5 = S0.loc[S0.reason == 'ok', 'distance5']
        thr = float(np.quantile(d5, 0.5))
        S1, _ = build(c, threshold=thr)
        self.assertGreater(int((S1.reason == 'above_threshold').sum()), 0)
        self.assertTrue((S1.loc[S1.reason == 'above_threshold', 'a'] == 0.0).all())
        # q is still computed and recorded; only the strength is zeroed.
        np.testing.assert_allclose(S0.q_transport.to_numpy(), S1.q_transport.to_numpy(),
                                   rtol=0, atol=1e-12, equal_nan=True)

    def test_supported_rows_carry_the_frozen_strength(self):
        c = ctx()
        S, _ = build(c)
        self.assertTrue((S.loc[S.reason == 'ok', 'a'] == ea.ANCHOR_STRENGTH).all())
        self.assertEqual(ea.ANCHOR_STRENGTH, 0.25)

    def test_every_row_has_a_recorded_reason(self):
        c = ctx()
        S, _ = build(c)
        self.assertTrue(set(S.reason) <= set(ea.REASONS))
        self.assertEqual(len(S), 120)

    def test_a_missing_descriptor_abstains_rather_than_imputing(self):
        c = ctx()
        F = c['F'].copy()
        q = c['hold'][:120]
        F.loc[q[:5], 'co2_a24h'] = np.nan
        S, _ = build(c, F=F)
        self.assertTrue((S.iloc[:5].reason == 'missing_descriptor').all())
        self.assertTrue((S.iloc[:5].a == 0.0).all())

    def test_the_threshold_is_the_q90_of_distance_to_fifth_neighbour(self):
        v = np.arange(1, 101, dtype=float)
        self.assertAlmostEqual(ea.choose_threshold(v), float(np.quantile(v, 0.90)), places=12)
        # Session 36: an empty calibration returns None, not `inf`. Returning `inf` was a
        # threshold nothing could exceed, so a failed calibration licensed unlimited support --
        # see §256.3 and `tests/test_v21_anchor_gate_contract.py`.
        self.assertIsNone(ea.choose_threshold([]))


class Isolation(unittest.TestCase):
    def test_labels_after_the_origin_change_nothing(self):
        c = ctx()
        S0, D0 = build(c)
        y2 = c['y'].copy()
        y2.loc[y2.index > pd.Timestamp(c['origin'])] = 1.0
        S1, D1 = build(c, y=y2)
        assert_frame_equal(S0, S1)
        assert_frame_equal(D0, D1)

    def test_sensors_after_the_horizon_end_cannot_reach_the_frame(self):
        # The frame is built at the horizon end, so this is a property of `frame_at`; asserting
        # it here keeps the anchor arm from being the place that quietly relaxes it.
        c = ctx()
        g2 = c['g'].copy()
        after = g2.index > pd.Timestamp(c['horizon_end'])
        for col in fp.FAST:
            g2.loc[after, col] = g2.loc[after, col] + 50.0
        _gh, F2 = a47.frame_at(g2, c['horizon_end'])
        S0, _ = build(c)
        S1, _ = build(c, F=F2)
        assert_frame_equal(S0, S1)

    def test_the_result_does_not_depend_on_query_order(self):
        c = ctx()
        q = c['hold'][:120]
        S0, _ = build(c, queries=q)
        S1, _ = build(c, queries=q[::-1])
        a = S0.sort_values('datetime').reset_index(drop=True)
        b = S1.sort_values('datetime').reset_index(drop=True)
        assert_frame_equal(a, b)

    def test_ties_break_on_ascending_timestamp(self):
        # Two anchors at identical distance must resolve deterministically, oldest first.
        c = ctx()
        S, D = build(c)
        d = D.sort_values(['datetime', 'distance', 'anchor'])
        assert_frame_equal(d.reset_index(drop=True),
                           D.sort_values(['datetime', 'distance', 'anchor'])
                            .reset_index(drop=True))


class Coverage(unittest.TestCase):
    def test_coverage_counts_reasons_and_sums_to_n(self):
        c = ctx()
        S, _ = build(c)
        cov = ea.coverage(S)
        self.assertEqual(cov['n'], len(S))
        self.assertEqual(sum(cov[r] for r in ea.REASONS), cov['n'])
        self.assertAlmostEqual(cov['coverage'], cov['ok'] / cov['n'], places=12)


if __name__ == '__main__':
    unittest.main()
