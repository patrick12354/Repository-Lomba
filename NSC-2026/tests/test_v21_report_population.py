"""Session 34, Task 0: the reporter must say which population each number describes.

Four numbers in the session-33 report described a population other than the one the decision is
made on. None changed the verdict, but the failure mode is section 181's and section 223's: a
statistic computed on rows that are not the rows being decided about. These tests pin each
repair, and each one is written so the OLD logic fails it -- a test only the new code is run
through does not show it discriminates.

    .venv/Scripts/python.exe -m unittest discover -s tests -p test_v21_report_population.py
"""
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
import final_pipeline as fp
import an59_v21_candidate_contract as c
import an77_v21_shape_report as rep

PREDS = ROOT / 'outputs' / 'audit_v21_s33' / 'preds_level_shape.pkl'

# Pinned in section 4 of the session-34 audit, recomputed here from the frozen prediction file.
EXPECTED = {
    'E1': dict(d_pooled=+0.048620, d_matched=+0.073714, align=+0.489902, movement=+0.050778,
               guard=+0.595980),
    'E2': dict(d_pooled=+0.033600, d_matched=+0.051139, align=+0.311644, movement=+0.061502,
               guard=+0.430731),
}

_P = {}


def preds():
    if not _P:
        _P['P'] = pd.read_pickle(PREDS)
    return _P['P']


class Fixture(unittest.TestCase):
    def test_the_prediction_file_is_the_one_the_audit_read(self):
        P = preds()
        self.assertEqual(len(P), 9504)
        self.assertFalse(P.duplicated(['arm', 'block', 'datetime']).any())
        self.assertEqual(sorted(P.arm.unique()), ['C0', 'E1', 'E2'])


class MatchedPopulation(unittest.TestCase):
    """B3 is a 7-day shift that shares timestamps with both primary blocks."""

    def test_the_primary_frame_is_unique_and_excludes_b3(self):
        k = rep.joined(preds(), 'E1')
        prim = rep.primary_rows(k)
        self.assertEqual(len(prim), 1440)
        self.assertFalse(prim.datetime.duplicated().any())
        self.assertEqual(sorted(prim.block.unique()), list(rep.PRIMARY))

    def test_matched_selection_returns_1008_rows_not_1680(self):
        for arm, want in EXPECTED.items():
            k = rep.joined(preds(), arm)
            prim = rep.primary_rows(k)
            want_ts = pd.DatetimeIndex(k.loc[k.family == '7d'].datetime).unique()
            m = prim.loc[prim.datetime.isin(want_ts).to_numpy()]
            self.assertEqual(len(m), 1008, arm)
            got = fp.rmse(m.y, m.z_new_q) - fp.rmse(m.y, m.z_new)
            self.assertAlmostEqual(got, want['d_matched'], places=6, msg=arm)

    def test_the_old_selection_expanded_the_population(self):
        # The discriminating half. Selecting the same timestamps from a frame that still holds B3
        # returns 1680 rows, because `.loc` on a non-unique index expands.
        k = rep.joined(preds(), 'E1')
        k15 = k.loc[k.family == '15d']
        prim = rep.primary_rows(k)
        idx = pd.DatetimeIndex(k.loc[k.family == '7d'].datetime).unique() \
            .intersection(pd.DatetimeIndex(prim.datetime))
        old = k15.set_index('datetime').loc[idx]
        self.assertEqual(len(old), 1680)
        self.assertIn('B3_shift7d', set(old.block))


class DirectionPopulation(unittest.TestCase):
    def test_direction_reconstructs_the_primary_delta_mse_exactly(self):
        for arm, want in EXPECTED.items():
            k = rep.joined(preds(), arm)
            prim = rep.primary_rows(k)
            d = c.direction(prim.y.to_numpy(), prim.z_new.to_numpy(), prim.z_new_q.to_numpy())
            self.assertAlmostEqual(d['alignment'], want['align'], places=6, msg=arm)
            self.assertAlmostEqual(d['movement_mse'], want['movement'], places=6, msg=arm)
            actual = float(((prim.z_new_q - prim.y) ** 2).mean() -
                           ((prim.z_new - prim.y) ** 2).mean())
            self.assertAlmostEqual(d['d_mse'], actual, places=12, msg=arm)

    def test_the_three_block_population_does_not_reconstruct_it(self):
        # Why the identity assertion in `evaluate` is worth having.
        k = rep.joined(preds(), 'E1')
        k15 = k.loc[k.family == '15d']
        prim = rep.primary_rows(k)
        d_all = c.direction(k15.y.to_numpy(), k15.z_new.to_numpy(), k15.z_new_q.to_numpy())
        actual = float(((prim.z_new_q - prim.y) ** 2).mean() -
                       ((prim.z_new - prim.y) ** 2).mean())
        self.assertGreater(abs(d_all['d_mse'] - actual), 1e-3)

    def test_evaluate_asserts_the_identity(self):
        P = preds()
        res, _k, _prim, _day = rep.evaluate(P, 'E1', fp.load_grid(), {})
        self.assertAlmostEqual(res['direction_d_mse'], res['d_mse_pooled'], places=12)
        self.assertEqual(res['n_primary'], 1440)
        self.assertEqual(res['matched_n'], 1008)


class QualityJoin(unittest.TestCase):
    def test_quality_values_follow_the_row_not_the_groupby_order(self):
        import v21_local_shape as ls
        g = fp.load_grid()
        k = rep.joined(preds(), 'E1')
        prim = rep.primary_rows(k)
        Q = rep.quality_slice(g, prim, {})
        self.assertEqual(int(Q.n.sum()), 1440)
        # Section 4.3's corrected quartiles, low repaired fraction to high.
        np.testing.assert_allclose(Q.n.to_numpy(), [451, 299, 356, 334])
        np.testing.assert_allclose(Q.d_mse.to_numpy(),
                                   [0.5250, 0.7025, 0.8968, 0.0374], atol=5e-4)

    def test_the_concatenate_pairing_attached_the_wrong_block(self):
        # The discriminating half. Session 33 sliced the primary rows out of a frame sorted by
        # (block, datetime), so B1 came first; `groupby('horizon_end')` yields B2 first because
        # its horizon ends earlier. Concatenating the groups onto that frame swaps the two
        # blocks' columns wholesale -- 1364 of 1440 values land on the wrong row.
        import v21_local_shape as ls
        g = fp.load_grid()
        k = rep.joined(preds(), 'E1')
        d = k.loc[k.block.isin(rep.PRIMARY)].sort_values(['block', 'datetime']) \
            .reset_index(drop=True)
        parts, correct = [], np.empty(len(d))
        for he, gd in d.groupby('horizon_end'):
            S = ls.build_local_shape(g, pd.Timestamp(he))
            v = S.loc[pd.DatetimeIndex(gd.datetime), 'quality_T_repaired_fraction_24h'].to_numpy()
            parts.append(v)
            correct[d.index.get_indexer(gd.index)] = v
        self.assertEqual(int((np.concatenate(parts) != correct).sum()), 1364)

    def test_reversing_the_block_order_does_not_change_the_answer(self):
        g = fp.load_grid()
        k = rep.joined(preds(), 'E1')
        prim = rep.primary_rows(k)
        cache = {}
        a = rep.quality_slice(g, prim, cache)
        b = rep.quality_slice(g, prim.iloc[::-1], cache)
        np.testing.assert_allclose(a.d_mse.to_numpy(), b.d_mse.to_numpy(), atol=1e-12)
        np.testing.assert_allclose(a.n.to_numpy(), b.n.to_numpy())


class BestDayGuard(unittest.TestCase):
    def test_partial_days_exist_so_the_weighting_matters(self):
        k = rep.joined(preds(), 'E1')
        day = rep.daily(rep.primary_rows(k))
        self.assertLess(int(day.n.min()), 48)
        self.assertEqual(int(day.n.max()), 48)

    def test_the_guard_pools_sse_over_n(self):
        for arm, want in EXPECTED.items():
            k = rep.joined(preds(), arm)
            prim = rep.primary_rows(k)
            got, best, n = rep.guard_excluding_best_day(prim, rep.daily(prim))
            self.assertAlmostEqual(got, want['guard'], places=6, msg=arm)
            self.assertEqual(best, '2023-08-01', arm)
            self.assertLess(n, len(prim))

    def test_averaging_daily_means_gives_a_different_number(self):
        k = rep.joined(preds(), 'E1')
        prim = rep.primary_rows(k)
        day = rep.daily(prim)
        old = float(day.d_mse.drop(day.d_mse.idxmin()).mean())
        new, _b, _n = rep.guard_excluding_best_day(prim, day)
        self.assertAlmostEqual(old, 0.657287, places=5)
        self.assertGreater(abs(old - new), 1e-3)


class Bootstrap(unittest.TestCase):
    def test_the_bootstrap_is_invariant_to_input_row_order(self):
        k = rep.joined(preds(), 'E1')
        prim = rep.primary_rows(k)
        # Shuffled and NOT pre-sorted: the bootstrap canonicalises its own input.
        a = rep.bootstrap(prim, 3)
        b = rep.bootstrap(prim.sample(frac=1.0, random_state=7), 3)
        self.assertAlmostEqual(a['mean'], b['mean'], places=12)
        self.assertEqual(a['blocks'], b['blocks'])

    def test_a_noncontiguous_index_does_not_change_the_result(self):
        k = rep.joined(preds(), 'E1')
        prim = rep.primary_rows(k)
        shifted = prim.copy()
        shifted.index = shifted.index  # datetime index, deliberately not 0..n-1
        self.assertAlmostEqual(rep.bootstrap(prim, 7)['mean'],
                               rep.bootstrap(shifted, 7)['mean'], places=12)


class TieBreak(unittest.TestCase):
    """E2 must beat E1, not merely beat the control."""

    def _row(self, arm, pooled, **d):
        r = dict(arm=arm, pooled_cand=pooled, promotable=True, strong=True,
                 d_B1_last15d=0.0, d_B2_prev15d=0.0, d_H1_last7d=0.0)
        r.update(d)
        return r

    def test_e2_is_refused_when_it_is_worse_than_e1_on_a_primary_block(self):
        # E2 is better than the control on B1 (negative) but worse than E1 there. The session-33
        # expression let this through on the `or delta < 0` clause.
        e1 = self._row('E1', 5.40, d_B1_last15d=-0.20)
        e2 = self._row('E2', 5.30, d_B1_last15d=-0.05)
        verdict, chosen, _why = rep.choose([e1, e2])
        self.assertEqual(chosen['arm'], 'E1')

    def test_e2_is_taken_when_it_beats_e1_everywhere_the_rule_names(self):
        e1 = self._row('E1', 5.40, d_B1_last15d=-0.20)
        e2 = self._row('E2', 5.30, d_B1_last15d=-0.25)
        verdict, chosen, _why = rep.choose([e1, e2])
        self.assertEqual(chosen['arm'], 'E2')

    def test_e2_is_refused_when_the_pooled_margin_is_too_small(self):
        e1 = self._row('E1', 5.40, d_B1_last15d=-0.20)
        e2 = self._row('E2', 5.395, d_B1_last15d=-0.30)
        verdict, chosen, _why = rep.choose([e1, e2])
        self.assertEqual(chosen['arm'], 'E1')

    def test_nothing_passing_keeps_v21(self):
        verdict, chosen, _why = rep.choose([self._row('E1', 5.6, promotable=False, strong=False)])
        self.assertEqual(verdict, 'keep_v21')
        self.assertIsNone(chosen)


class Verdict(unittest.TestCase):
    def test_the_repaired_report_still_rejects_both_arms(self):
        P = preds()
        g = fp.load_grid()
        cache, rows = {}, []
        for arm in ('E1', 'E2'):
            res, _k, _p, _d = rep.evaluate(P, arm, g, cache)
            rows.append(res)
            self.assertAlmostEqual(res['d_pooled'], EXPECTED[arm]['d_pooled'], places=6)
            self.assertAlmostEqual(res['d_matched'], EXPECTED[arm]['d_matched'], places=6)
            self.assertFalse(res['promotable'], arm)
        verdict, chosen, _why = rep.choose(rows)
        self.assertEqual(verdict, 'keep_v21')
        self.assertIsNone(chosen)


if __name__ == '__main__':
    unittest.main()
