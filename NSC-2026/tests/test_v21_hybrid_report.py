"""Session 36, Task 3: the hybrid report's populations and its control logic.

The decision rule here has a trap the shape round did not: there are TWO references. `C0` is the
promotion gate, and `L0` is the control that says whether a win came from smooth nonlinearity or
merely from having a two-stage structure. An arm that beats C0 but loses to L0 has not supported
the hypothesis, and L0 must not be promoted in its place -- it was the control.

    .venv/Scripts/python.exe -m unittest discover -s tests -p test_v21_hybrid_report.py
"""
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
import an59_v21_candidate_contract as c
import an77_v21_shape_report as rep
import an85_v21_level_hybrid_report as hr

PREDS = ROOT / 'outputs' / 'audit_v21_s36' / 'hybrid' / 'preds_hybrid.pkl'
_P = {}


def preds():
    if not _P:
        _P['P'] = pd.read_pickle(PREDS)
    return _P['P']


def row(arm, pooled, promotable=True, **kw):
    r = dict(arm=arm, pooled_cand=pooled, promotable=promotable, breakthrough=False,
             d_B1_last15d=-0.05, d_B2_prev15d=-0.05, d_H1_last7d=0.0)
    r.update(kw)
    return r


class Populations(unittest.TestCase):
    def test_the_primary_frame_is_1440_unique_timestamps(self):
        k = hr.joined(preds(), 'S1')
        p = hr.primary(k)
        self.assertEqual(len(p), 1440)
        self.assertFalse(p.datetime.duplicated().any())
        self.assertEqual(sorted(p.block.unique()), list(hr.PRIMARY))

    def test_b3_is_not_in_the_primary_population(self):
        p = hr.primary(hr.joined(preds(), 'S1'))
        self.assertNotIn('B3_shift7d', set(p.block))

    def test_the_control_pooled_rmse_is_the_frozen_value(self):
        r = hr.evaluate(preds(), 'S1')
        self.assertAlmostEqual(r['pooled_base'], hr.C0_POOLED, places=6)

    def test_direction_reconstructs_the_pooled_delta_exactly(self):
        for arm in ('L0', 'S1', 'S2'):
            r = hr.evaluate(preds(), arm)
            self.assertAlmostEqual(r['direction_d_mse'], r['d_mse_pooled'], places=12, msg=arm)

    def test_the_matched_calendar_is_1008_rows(self):
        self.assertEqual(hr.evaluate(preds(), 'S1')['matched_n'], 1008)

    def test_a_mismatched_arm_is_refused(self):
        P = preds()
        broken = P.loc[~((P.arm == 'S1') & (P.block == 'B1_last15d'))]
        with self.assertRaises(AssertionError):
            hr.joined(broken, 'S1')


class BestDayGuard(unittest.TestCase):
    def test_the_guard_uses_the_global_single_day_definition(self):
        import v21_episode_anchors as ea
        k = hr.joined(preds(), 'S1')
        p = hr.primary(k)
        g = ea.global_best_day_guard(p.y, p.z_new, p.z_new_q, p.datetime)
        self.assertEqual(hr.evaluate(preds(), 'S1')['d_mse_excluding_best_day'], g['guard'])
        self.assertEqual(g['n_days'] - 1, len(set(pd.DatetimeIndex(p.datetime).normalize())) - 1)


class ControlLogic(unittest.TestCase):
    """The L0 control decides whether a win is about splines."""

    def test_a_spline_beating_c0_but_losing_to_l0_does_not_promote(self):
        rows = [row('L0', 5.40), row('S1', 5.45), row('S2', 5.46)]
        verdict, chosen, why = hr.choose(rows)
        self.assertEqual(verdict, 'keep_v21')
        self.assertIsNone(chosen)
        self.assertIn('do not beat the L0 control', why)

    def test_l0_is_never_promoted_even_when_it_alone_passes(self):
        rows = [row('L0', 5.40), row('S1', 5.60, promotable=False),
                row('S2', 5.61, promotable=False)]
        verdict, chosen, why = hr.choose(rows)
        self.assertEqual(verdict, 'keep_v21')
        self.assertIsNone(chosen)
        self.assertIn('L0 control DOES clear it', why)

    def test_a_spline_that_beats_both_is_selected(self):
        rows = [row('L0', 5.45), row('S1', 5.40), row('S2', 5.60, promotable=False)]
        verdict, chosen, _why = hr.choose(rows)
        self.assertEqual(chosen['arm'], 'S1')
        self.assertEqual(verdict, 'production_check_candidate')

    def test_s2_must_beat_s1_by_the_margin_to_replace_it(self):
        rows = [row('L0', 5.50), row('S1', 5.40), row('S2', 5.395)]
        _v, chosen, _w = hr.choose(rows)
        self.assertEqual(chosen['arm'], 'S1')
        rows = [row('L0', 5.50), row('S1', 5.40), row('S2', 5.38)]
        _v, chosen, _w = hr.choose(rows)
        self.assertEqual(chosen['arm'], 'S2')

    def test_s2_is_refused_when_it_hurts_a_primary_block_against_s1(self):
        rows = [row('L0', 5.50), row('S1', 5.40, d_B1_last15d=-0.20),
                row('S2', 5.38, d_B1_last15d=-0.05)]
        _v, chosen, _w = hr.choose(rows)
        self.assertEqual(chosen['arm'], 'S1')

    def test_breakthrough_needs_the_extra_mse_fraction(self):
        rows = [row('L0', 5.50), row('S1', 5.40, breakthrough=True)]
        verdict, chosen, _w = hr.choose(rows)
        self.assertEqual(verdict, 'breakthrough_candidate')
        self.assertEqual(hr.BAR['breakthrough_mse_fraction'], 0.05)

    def test_nothing_passing_keeps_v21(self):
        rows = [row('L0', 5.6, promotable=False), row('S1', 5.6, promotable=False)]
        verdict, chosen, _w = hr.choose(rows)
        self.assertEqual(verdict, 'keep_v21')
        self.assertIsNone(chosen)


class ActualVerdict(unittest.TestCase):
    def test_no_arm_clears_the_bar_on_the_real_predictions(self):
        rows = [hr.evaluate(preds(), a) for a in ('L0', 'S1', 'S2')]
        for r in rows:
            self.assertFalse(r['promotable'], r['arm'])
            self.assertGreater(r['d_pooled'], 0.0, r['arm'])
        verdict, chosen, _w = hr.choose(rows)
        self.assertEqual(verdict, 'keep_v21')
        self.assertIsNone(chosen)

    def test_the_spline_arms_also_lose_to_the_linear_control(self):
        l0 = hr.evaluate(preds(), 'L0')
        for arm in ('S1', 'S2'):
            self.assertGreater(hr.evaluate(preds(), arm)['pooled_cand'], l0['pooled_cand'], arm)


if __name__ == '__main__':
    unittest.main()
