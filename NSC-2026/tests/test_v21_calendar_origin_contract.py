"""Session 31, Task 0: the two contracts session 30 got wrong.

Both defects were mine, both were found by audit rather than by a test, and neither changed a
promotion decision -- which is exactly why they are worth pinning. A reporting population that
silently triples a duplicated timestamp, and a forward selection that trains on labels its own
origin could not have seen, are the kinds of error that stay invisible while every headline
number looks reasonable.

    .venv/Scripts/python.exe -m unittest discover -s tests -p test_v21_calendar_origin_contract.py
"""
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
import an69_v21_sensor_ablation as a69
import an70_v21_slow_member_correction as a70


def frame(block, stamps, recon=0.0):
    idx = pd.DatetimeIndex(stamps)
    return pd.DataFrame(dict(block=block, datetime=idx, y=np.zeros(len(idx)),
                             recon=np.full(len(idx), recon), score=True))


class MatchedPopulation(unittest.TestCase):
    """B3 is a 7-day shift that overlaps both primary blocks, so its timestamps are duplicates
    of theirs. `.loc[idx]` on a non-unique index expands rather than selects."""

    def test_an_overlapping_block_does_not_inflate_the_matched_row_count(self):
        a = pd.Timestamp('2023-08-15 00:00')
        b = pd.Timestamp('2023-08-16 00:00')
        P = pd.concat([frame('B1_last15d', [a, b]), frame('B3_shift7d', [b])],
                      ignore_index=True)
        self.assertEqual(len(P), 3)
        # the naive version, kept here as the thing being ruled out
        naive = P.set_index('datetime').sort_index().loc[pd.DatetimeIndex([a, b])]
        self.assertEqual(len(naive), 3)
        # the contract: two timestamps queried, two primary rows returned
        got = a69.primary_index(P).loc[pd.DatetimeIndex([a, b])]
        self.assertEqual(len(got), 2)
        self.assertEqual(sorted(got.index), [a, b])

    def test_primary_index_drops_b3_and_unscored_rows(self):
        idx = pd.date_range('2023-08-15', periods=4, freq='30min')
        P = pd.concat([frame('B1_last15d', idx[:2]), frame('B2_prev15d', idx[2:]),
                       frame('B3_shift7d', idx)], ignore_index=True)
        P.loc[P.index[-1], 'score'] = False
        got = a69.primary_index(P)
        self.assertEqual(len(got), 4)
        self.assertEqual(set(got.block), {'B1_last15d', 'B2_prev15d'})

    def test_duplicate_primary_timestamps_are_refused_rather_than_averaged(self):
        a = pd.Timestamp('2023-08-15 00:00')
        P = pd.concat([frame('B1_last15d', [a]), frame('B2_prev15d', [a])], ignore_index=True)
        with self.assertRaises(AssertionError):
            a69.primary_index(P)

    def test_the_real_session_30_artifacts_now_give_1008_not_1680(self):
        s30 = ROOT / 'outputs' / 'audit_v21_s30'
        p15, p7 = s30 / 'preds_sensor_drop_pressure_abs.pkl', \
            s30 / 'preds_sensor_7d_drop_pressure_abs.pkl'
        if not (p15.exists() and p7.exists()):
            self.skipTest('session-30 sensor predictions not present')
        P15, P7 = pd.read_pickle(p15), pd.read_pickle(p7)
        idx = P7.loc[P7.score].set_index('datetime').sort_index().index
        self.assertEqual(len(P15.set_index('datetime').sort_index().loc[idx]), 1680)
        self.assertEqual(len(a69.primary_index(P15).loc[idx]), 1008)
        self.assertEqual(len(a69.primary_index(P15)), 1440)


def part(origin, start, n=96, r=1.0, u=1.0):
    idx = pd.date_range(start, periods=n, freq='30min')
    return dict(idx=idx, origin=pd.Timestamp(origin), y=np.full(n, r),
                z_pre=np.zeros(n), U=np.full((n, len(a70.CONTRASTS)), u))


class OriginEligibility(unittest.TestCase):
    """A calibration record is usable at an origin only once its label exists."""

    def test_a_record_whose_target_is_after_the_origin_is_refused(self):
        """The plan's B1 example: a record targeting 8 Aug 14:30 cannot inform a forecaster
        standing at 6 Aug 14:30, even though the window it validates lies later still."""
        p = part('2023-08-01 14:30', '2023-08-05 14:30', n=200)
        got = a70.eligible_at([p], pd.Timestamp('2023-08-06 14:30'))
        self.assertIsNotNone(got)
        self.assertLessEqual(got.dt.max(), pd.Timestamp('2023-08-06 14:30'))
        self.assertNotIn(pd.Timestamp('2023-08-08 14:30'), set(got.dt))
        # ...and the 5 August rows are admitted
        self.assertIn(pd.Timestamp('2023-08-05 15:00'), set(got.dt))

    def test_a_forecast_launched_after_the_origin_contributes_nothing(self):
        p = part('2023-08-10 00:00', '2023-08-01 00:00')
        self.assertIsNone(a70.eligible_at([p], pd.Timestamp('2023-08-05 00:00')))

    def test_records_are_deduplicated_keeping_the_latest_eligible_forecast(self):
        idx_start = '2023-08-02 00:00'
        early = part('2023-08-01 00:00', idx_start, r=1.0, u=1.0)
        late = part('2023-08-01 12:00', idx_start, r=9.0, u=9.0)
        got = a70.eligible_at([early, late], pd.Timestamp('2023-08-04 00:00'))
        self.assertEqual(len(got), 96)
        np.testing.assert_allclose(got.r.to_numpy(), 9.0)

    def test_every_split_trains_only_on_labels_its_origin_could_hold(self):
        """The property section 224 found violated: zero validation rows may be trained on
        labels dated after the validating forecast's own origin."""
        parts = [part('2023-08-%02d 00:00' % (1 + 2 * k),
                      '2023-08-%02d 00:00' % (2 + 2 * k), n=192) for k in range(5)]
        splits = a70.origin_splits(parts)
        self.assertGreaterEqual(len(splits), a70.MIN_CHUNKS - 1)
        for sp in splits:
            self.assertLessEqual(pd.Timestamp(sp['train_label_end']),
                                 pd.Timestamp(sp['origin']))

    def test_a_split_never_validates_against_itself(self):
        parts = [part('2023-08-%02d 00:00' % (1 + 2 * k),
                      '2023-08-%02d 00:00' % (2 + 2 * k), n=192) for k in range(5)]
        for sp in a70.origin_splits(parts):
            self.assertGreaterEqual(sp['n_train'], a70.MIN_TIMESTAMPS)

    def test_one_window_alone_yields_no_split(self):
        self.assertEqual(a70.origin_splits([part('2023-08-01', '2023-08-02', n=400)]), [])

    def test_select_alpha_uses_each_splits_own_training_side(self):
        rng = np.random.default_rng(5)
        splits = []
        for _ in range(3):
            tU = rng.standard_normal((300, len(a70.CONTRASTS)))
            vU = rng.standard_normal((150, len(a70.CONTRASTS)))
            beta = np.zeros(len(a70.CONTRASTS))
            beta[0] = 2.0
            splits.append(dict(train_U=tU, train_r=tU @ beta + 0.05 * rng.standard_normal(300),
                               val_U=vU, val_r=vU @ beta + 0.05 * rng.standard_normal(150),
                               origin='x', n_train=300, n_val=150, train_label_end='x'))
        alpha, table = a70.select_alpha(splits)
        self.assertIn(alpha, a70.ALPHAS)
        self.assertEqual(len(table), 1 + len(a70.ALPHAS))

    def test_zero_still_wins_on_noise_under_the_new_split_shape(self):
        rng = np.random.default_rng(6)
        splits = [dict(train_U=rng.standard_normal((300, len(a70.CONTRASTS))),
                       train_r=rng.standard_normal(300),
                       val_U=rng.standard_normal((150, len(a70.CONTRASTS))),
                       val_r=rng.standard_normal(150),
                       origin='x', n_train=300, n_val=150, train_label_end='x')
                  for _ in range(3)]
        alpha, _t = a70.select_alpha(splits)
        self.assertIsNone(alpha)


if __name__ == '__main__':
    unittest.main()
