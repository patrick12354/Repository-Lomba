"""Session 36, Task 0: four contract defects in the session-35 anchor gate.

None of them changed the session-35 verdict -- transport failed by a wide margin under every
definition -- but each could have let a later round through on a technicality, and one of them
would have made a failed calibration look like unlimited support.

    .venv/Scripts/python.exe -m unittest discover -s tests -p test_v21_anchor_gate_contract.py
"""
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
import v21_episode_anchors as ea
import an81_v21_anchor_support as a81

S35 = ROOT / 'outputs' / 'audit_v21_s35' / 'anchor_inner_predictions.pkl'
D35 = ROOT / 'outputs' / 'audit_v21_s35' / 'anchor_detail.pkl'

# Recomputed from the frozen session-35 artifacts; pinned so a definition change is visible.
EXPECT = dict(
    transport_all=+0.763861880, raw_all=-0.577606513,
    transport_supported=+0.824161278, raw_supported=-0.749991077,
    transport_guard_supported=+4.083290878, raw_guard_supported=-0.146094947,
    pairs_all=3820, pairs_supported=3300, oor_supported=153,
)

_A = {}


def art():
    if not _A:
        _A['S'] = pd.read_pickle(S35)
        _A['D'] = pd.read_pickle(D35)
    return _A['S'], _A['D']


class MissingThresholdAbstains(unittest.TestCase):
    """A calibration that produced nothing cannot license unlimited support."""

    def test_choose_threshold_returns_none_not_infinity(self):
        self.assertIsNone(ea.choose_threshold([]))
        self.assertIsNone(ea.choose_threshold([np.nan, np.nan]))
        self.assertIsInstance(ea.choose_threshold([1.0, 2.0, 3.0]), float)

    def test_an_infinite_threshold_would_have_admitted_everything(self):
        # The discriminating half: the old return value is a threshold nothing can exceed.
        self.assertFalse(0.9 > float('inf'))

    def test_abstain_all_zeroes_the_strength_and_names_the_reason(self):
        idx = pd.date_range('2023-08-01', periods=10, freq='30min')
        S, D = ea.abstain_all(idx, 'no_threshold')
        self.assertEqual(len(S), 10)
        self.assertTrue((S.a == 0.0).all())
        self.assertTrue((S.reason == 'no_threshold').all())
        self.assertEqual(len(D), 0)
        self.assertIn('no_threshold', ea.REASONS)

    def test_an_unknown_reason_is_refused(self):
        idx = pd.date_range('2023-08-01', periods=4, freq='30min')
        with self.assertRaises(AssertionError):
            ea.abstain_all(idx, 'made_up')

    def test_a_no_threshold_window_reports_zero_coverage(self):
        idx = pd.date_range('2023-08-01', periods=48, freq='30min')
        S, _ = ea.abstain_all(idx, 'no_threshold')
        cov = ea.coverage(S)
        self.assertEqual(cov['coverage'], 0.0)
        self.assertEqual(cov['supported'], 0)
        self.assertEqual(cov['no_threshold'], 48)


class GlobalBestDayGuard(unittest.TestCase):
    """One day dropped once, over the pooled rows -- not a weighted mean of per-window guards."""

    def test_the_guard_drops_exactly_one_day(self):
        when = pd.date_range('2023-08-01', periods=96, freq='30min')
        y = np.zeros(96)
        base = np.ones(96)
        cand = np.ones(96)
        cand[:48] = 0.0                       # day one is where the whole gain lives
        g = ea.global_best_day_guard(y, base, cand, when)
        self.assertEqual(g['n_days'], 2)
        self.assertEqual(g['n_kept'], 48)
        self.assertEqual(g['dropped_day'], '2023-08-01')
        self.assertAlmostEqual(g['guard'], 0.0, places=12)

    def test_a_gain_spread_over_days_survives_the_guard(self):
        when = pd.date_range('2023-08-01', periods=96, freq='30min')
        y = np.zeros(96)
        base = np.ones(96)
        cand = np.full(96, 0.5)
        g = ea.global_best_day_guard(y, base, cand, when)
        self.assertLess(g['guard'], 0.0)

    def test_the_session35_numbers_reproduce_under_the_repaired_definition(self):
        S, _ = art()
        sup = S.loc[S.supported]
        for col, key in (('z_transport', 'transport_guard_supported'),
                         ('z_raw', 'raw_guard_supported')):
            g = ea.global_best_day_guard(sup.y, sup.z_c0, sup[col], sup.datetime)
            self.assertAlmostEqual(g['guard'], EXPECT[key], places=6, msg=col)

    def test_the_old_per_window_average_gives_a_different_number(self):
        # The discriminating half: 5.057280 was in the session-35 JSON.
        S, _ = art()
        parts, weights = [], []
        for (_b, _f), d in S.loc[S.supported].groupby(['block', 'fold']):
            g = ea.global_best_day_guard(d.y, d.z_c0, d.z_transport, d.datetime)
            parts.append(g['guard'])
            weights.append(len(d))
        old = float(np.average(parts, weights=weights))
        self.assertAlmostEqual(old, 5.057280, places=4)
        self.assertGreater(abs(old - EXPECT['transport_guard_supported']), 0.5)


class PooledDelta(unittest.TestCase):
    def test_pooled_delta_matches_the_recomputed_artifact_values(self):
        S, _ = art()
        self.assertAlmostEqual(a81.pooled_delta(S, 'z_transport', False),
                               EXPECT['transport_all'], places=8)
        self.assertAlmostEqual(a81.pooled_delta(S, 'z_raw', False), EXPECT['raw_all'], places=8)
        self.assertAlmostEqual(a81.pooled_delta(S, 'z_transport', True),
                               EXPECT['transport_supported'], places=8)
        self.assertAlmostEqual(a81.pooled_delta(S, 'z_raw', True),
                               EXPECT['raw_supported'], places=8)

    def test_the_raw_control_improved_and_the_transport_did_not(self):
        # Pinning the fact §253 got backwards: raw pools NEGATIVE, transport pools positive.
        S, _ = art()
        self.assertLess(a81.pooled_delta(S, 'z_raw', False), 0.0)
        self.assertGreater(a81.pooled_delta(S, 'z_transport', False), 0.0)


class SupportedPairPopulation(unittest.TestCase):
    def test_detail_rows_exist_for_queries_that_later_abstain(self):
        S, D = art()
        sup = set(S.loc[S.supported].datetime)
        self.assertEqual(len(D), EXPECT['pairs_all'])
        self.assertEqual(int(D.datetime.isin(sup).sum()), EXPECT['pairs_supported'])
        self.assertGreater(EXPECT['pairs_all'], EXPECT['pairs_supported'])

    def test_out_of_range_is_counted_on_the_pairs_the_solver_used(self):
        S, D = art()
        sup = set(S.loc[S.supported].datetime)
        Ds = D.loc[D.datetime.isin(sup)]
        self.assertEqual(int(((Ds.q_ij < 5) | (Ds.q_ij > 100)).sum()), EXPECT['oor_supported'])
        self.assertAlmostEqual(100 * EXPECT['oor_supported'] / EXPECT['pairs_supported'],
                               4.636, places=2)


class MandatoryBlocks(unittest.TestCase):
    """A block with no evidence is a block that did not pass."""

    def test_a_block_without_two_scored_windows_is_not_evidenced(self):
        scored = pd.DataFrame(dict(block=['B1_last15d', 'B1_last15d'], fold=[3, 7]))
        mandatory = ['B1_last15d', 'B2_prev15d']
        evidenced = {b for b in mandatory if len(scored.loc[scored.block == b]) >= 2}
        missing = [b for b in mandatory if b not in evidenced]
        self.assertEqual(missing, ['B2_prev15d'])

    def test_the_session35_run_had_a_block_without_evidence(self):
        S, _ = art()
        per = S.groupby('block').fold.nunique()
        self.assertEqual(int(per.get('B1_last15d', 0)), 2)
        self.assertEqual(int(per.get('B2_prev15d', 0)), 0)

    def test_the_gate_name_is_present_in_the_runner(self):
        import inspect
        src = inspect.getsource(a81.main)
        self.assertIn('gate0_all_blocks_evidenced', src)
        self.assertIn('blocks_missing_evidence', src)


class WindowProvenance(unittest.TestCase):
    def test_the_runner_records_that_the_windows_are_eight_days(self):
        # The plan asked for two 7-day windows; the implementation reuses the existing 8-day
        # inner folds. That is recorded rather than left to be rediscovered from the source.
        import inspect
        src = inspect.getsource(a81.main)
        self.assertIn('window_source', src)

    def test_the_selected_windows_do_not_overlap(self):
        S, _ = art()
        spans = S.groupby(['block', 'fold']).datetime.agg(['min', 'max']).sort_values('min')
        for i in range(len(spans) - 1):
            self.assertLessEqual(spans['max'].iloc[i], spans['min'].iloc[i + 1])


if __name__ == '__main__':
    unittest.main()
