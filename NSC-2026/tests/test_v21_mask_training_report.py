"""Session 37, Task 3: populations, the duplication control, and keeping stress out of the score.

Two traps specific to this round. First, `D0` is a control that could plausibly win on its own,
and promoting it would be a claim about row duplication dressed up as a claim about masking.
Second, the stress pass produces plausible-looking RMSEs on a synthetic corruption; folding those
into the primary population would be inventing a holdout.

    .venv/Scripts/python.exe -m unittest discover -s tests -p test_v21_mask_training_report.py
"""
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
import an87_v21_mask_training_report as mr

PREDS = ROOT / 'outputs' / 'audit_v21_s37' / 'preds_mask.pkl'
STRESS = ROOT / 'outputs' / 'audit_v21_s37' / 'mask_stress.csv'
_P = {}


def preds():
    if not _P:
        _P['P'] = pd.read_pickle(PREDS)
    return _P['P']


def row(arm, promotable=True, d_pooled=-0.05, **kw):
    r = dict(arm=arm, promotable=promotable, breakthrough=False, d_pooled=d_pooled)
    r.update(kw)
    return r


class Populations(unittest.TestCase):
    def test_the_primary_frame_is_1440_unique_timestamps(self):
        p = mr.primary(mr.joined(preds(), 'M1'))
        self.assertEqual(len(p), 1440)
        self.assertFalse(p.datetime.duplicated().any())
        self.assertEqual(sorted(p.block.unique()), list(mr.PRIMARY))

    def test_b3_is_excluded_from_primary(self):
        self.assertNotIn('B3_shift7d', set(mr.primary(mr.joined(preds(), 'M1')).block))

    def test_the_control_pooled_rmse_is_the_frozen_value(self):
        self.assertAlmostEqual(mr.evaluate(preds(), 'M1')['pooled_base'], mr.C0_POOLED, places=6)

    def test_direction_reconstructs_the_pooled_delta(self):
        for arm in ('D0', 'M1'):
            r = mr.evaluate(preds(), arm)
            self.assertAlmostEqual(r['direction_d_mse'], r['d_mse_pooled'], places=12, msg=arm)

    def test_matched_is_1008_rows(self):
        self.assertEqual(mr.evaluate(preds(), 'M1')['matched_n'], 1008)

    def test_a_missing_arm_row_is_refused(self):
        P = preds()
        broken = P.loc[~((P.arm == 'M1') & (P.block == 'B1_last15d'))]
        with self.assertRaises(AssertionError):
            mr.joined(broken, 'M1')


class DuplicationControl(unittest.TestCase):
    def test_m1_beating_c0_but_not_d0_does_not_promote(self):
        vs_c0 = [row('D0', promotable=False), row('M1', promotable=True)]
        vs_d0 = [row('M1', d_pooled=+0.01)]
        verdict, chosen, why = mr.choose(vs_c0, vs_d0)
        self.assertEqual(verdict, 'keep_v21')
        self.assertIsNone(chosen)
        self.assertIn('does not beat the D0 duplication control', why)

    def test_m1_beating_both_is_promoted(self):
        vs_c0 = [row('D0', promotable=False), row('M1', promotable=True)]
        vs_d0 = [row('M1', d_pooled=-0.03)]
        verdict, chosen, _w = mr.choose(vs_c0, vs_d0)
        self.assertEqual(chosen['arm'], 'M1')
        self.assertEqual(verdict, 'production_check_candidate')

    def test_d0_is_never_promoted_even_if_it_alone_passes(self):
        vs_c0 = [row('D0', promotable=True), row('M1', promotable=False)]
        verdict, chosen, why = mr.choose(vs_c0, [row('M1', d_pooled=+0.2)])
        self.assertEqual(verdict, 'keep_v21')
        self.assertIsNone(chosen)
        self.assertIn('D0 was the control', why)

    def test_breakthrough_needs_the_extra_fraction(self):
        vs_c0 = [row('M1', promotable=True, breakthrough=True)]
        verdict, chosen, _w = mr.choose(vs_c0, [row('M1', d_pooled=-0.03)])
        self.assertEqual(verdict, 'breakthrough_candidate')
        self.assertEqual(mr.BAR['breakthrough_mse_fraction'], 0.05)


class StressIsolation(unittest.TestCase):
    def test_stress_rows_are_reported_per_seed_and_not_pooled(self):
        S = pd.read_csv(STRESS)
        T = mr.stress_table(S)
        self.assertGreater(len(T), 0)
        self.assertEqual(sorted(T.stress_seed.unique().tolist()),
                         [2026090791, 2026090792, 2026090793])
        self.assertTrue((T.population == 'primary').all())

    def test_the_stress_table_covers_every_arm(self):
        T = mr.stress_table(pd.read_csv(STRESS))
        self.assertEqual(sorted(T.arm.unique().tolist()), ['C0', 'D0', 'M1'])

    def test_stress_never_enters_the_primary_metric(self):
        # The scored population is the natural one; nothing from the stress file reaches it.
        import inspect
        src = inspect.getsource(mr.evaluate)
        self.assertNotIn('stress', src)
        r = mr.evaluate(preds(), 'M1')
        self.assertEqual(r['n_primary'], 1440)

    def test_stress_only_covers_the_primary_blocks(self):
        T = mr.stress_table(pd.read_csv(STRESS))
        self.assertTrue((T.n_blocks <= len(mr.PRIMARY)).all())


class ActualVerdict(unittest.TestCase):
    def test_the_arms_are_scored_and_the_decision_is_recorded(self):
        vs_c0 = [mr.evaluate(preds(), a) for a in ('D0', 'M1')]
        vs_d0 = [mr.evaluate(preds(), 'M1', mr.CONTROL)]
        verdict, chosen, _w = mr.choose(vs_c0, vs_d0)
        self.assertIn(verdict, ('keep_v21', 'production_check_candidate',
                                'breakthrough_candidate'))
        for r in vs_c0:
            self.assertEqual(r['n_primary'], 1440)

    def test_duplication_alone_moves_the_result(self):
        # D0 is not a no-op: if it were, the control would be pointless and this would fail.
        d0 = mr.evaluate(preds(), 'D0')
        self.assertGreater(abs(d0['d_pooled']), 1e-6)


if __name__ == '__main__':
    unittest.main()
