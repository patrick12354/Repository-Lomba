"""Session 47: contracts for the member level de-bias (progress.md section 310).

The change is one scalar per member, so almost everything that could go wrong with it is a
contract rather than a number: the offset must come from the member's own out-of-fold rows, it
must be subtracted rather than added, it must be inert when the flag is off, and the file it
writes must not collide with the one that scored 2.84953.

    .venv/Scripts/python.exe -m unittest discover -s tests -p test_v21_member_bias.py
"""
import inspect
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
import final_pipeline as fp
import an100_v21_member_bias_arm as arm


def frame(cat_bias=-3.0, n=400, seed=0):
    """An out-of-fold frame where `cat` is offset by a known amount and nothing else is."""
    r = np.random.default_rng(seed)
    y = 50 + 15 * r.standard_normal(n)
    O = pd.DataFrame({'y': y, 'tod': r.uniform(0, 24, n)})
    for m in fp.MODELS_L2:
        O[m] = np.clip(y + r.standard_normal(n), 5, 100)
    O['cat'] = np.clip(O['cat'] + cat_bias, 5, 100)
    return O


class TheOffsetIsTheMeasuredForwardError(unittest.TestCase):
    def test_it_recovers_the_injected_offset_at_full_strength(self):
        O = frame(cat_bias=-3.0)
        b = fp.member_bias(O, fp.MODELS_L2, shrink=1.0)
        self.assertAlmostEqual(b['cat'], float((O['cat'] - O.y).mean()), places=12)
        self.assertLess(abs(b['cat'] + 3.0), 0.25)

    def test_shrink_scales_it_linearly_and_0_disables_it(self):
        O = frame()
        full = fp.member_bias(O, fp.MODELS_L2, shrink=1.0)['cat']
        self.assertAlmostEqual(fp.member_bias(O, fp.MODELS_L2, shrink=0.5)['cat'],
                               0.5 * full, places=12)
        self.assertEqual(fp.member_bias(O, fp.MODELS_L2, shrink=0.0)['cat'], 0.0)

    def test_only_the_named_members_are_touched(self):
        b = fp.member_bias(frame(), fp.MODELS_L2)
        self.assertEqual(set(b), set(fp.DEBIAS_MEMBERS))

    def test_a_member_not_in_the_blend_is_skipped(self):
        """`--drop-ridge` removes a member; the de-bias must not resurrect its name."""
        models = [m for m in fp.MODELS_L2 if m != 'cat']
        self.assertEqual(fp.member_bias(frame(), models), {})

    def test_the_shipped_strength_is_the_files_standing_half(self):
        self.assertEqual(fp.CATDB_SHRINK, 0.50)
        self.assertEqual(fp.CATDB_SHRINK, fp.TODB_SHRINK)


class TheArmSubtractsRatherThanAdds(unittest.TestCase):
    def setUp(self):
        self.O = frame(cat_bias=-3.0)
        self.V = frame(cat_bias=-3.0, seed=1)

    def test_a_positive_strength_moves_cat_up(self):
        O2, V2, b = arm.shifted(self.O, self.V, 'cat', 1.0)
        self.assertLess(b, 0)
        self.assertGreater(V2['cat'].mean(), self.V['cat'].mean())

    def test_the_wrong_sign_control_moves_it_the_other_way(self):
        _, V_up, _ = arm.shifted(self.O, self.V, 'cat', 0.5)
        _, V_dn, _ = arm.shifted(self.O, self.V, 'cat', -0.5)
        self.assertGreater(V_up['cat'].mean(), self.V['cat'].mean())
        self.assertLess(V_dn['cat'].mean(), self.V['cat'].mean())

    def test_the_offset_is_measured_on_O_and_applied_to_both(self):
        """A shift fitted on V would be fitting the rows it is scored on."""
        O2, V2, b = arm.shifted(self.O, self.V, 'cat', 1.0)
        self.assertAlmostEqual(b, float((self.O['cat'] - self.O.y).mean()), places=12)
        self.assertAlmostEqual(float((self.O['cat'] - O2['cat']).mean()), b, places=6)
        self.assertAlmostEqual(float((self.V['cat'] - V2['cat']).mean()), b, places=6)

    def test_the_control_arm_shifts_nothing(self):
        O2, V2, b = arm.shifted(self.O, self.V, None, 0.0)
        self.assertEqual(b, 0.0)
        self.assertTrue(O2['cat'].equals(self.O['cat']))
        self.assertTrue(V2['cat'].equals(self.V['cat']))

    def test_the_registered_arms_include_both_controls(self):
        labels = [a[0] for a in arm.ARMS]
        self.assertIn('wrong_sign', labels)
        self.assertIn('debias_enet', labels)
        self.assertEqual(labels[0], 'control')
        self.assertEqual(dict((a[0], a[2]) for a in arm.ARMS)['wrong_sign'], -0.50)


class TheFlagIsInertAndNamed(unittest.TestCase):
    def base(self, **kw):
        d = dict(l2_member=True, blend_shrink=fp.BLEND_SHRINK, drop_ridge=True,
                 bag_nopress=False, robust_core=False, smooth_level=False,
                 vapour_increment=False, inc_physics=False, inc_deshrink=False,
                 inc_lags=False, inc_lambda_scale=1.0, tod_bias_on=True, harm_bias_on=False)
        d.update(kw)
        return fp.increment_tag(**d)

    def test_the_scored_filename_is_unchanged_with_the_flag_off(self):
        self.assertEqual(self.base(), 'v16_noridge_todbias')

    def test_the_candidate_gets_its_own_filename(self):
        self.assertNotEqual(self.base(cat_debias=True), self.base())
        self.assertIn('catdb', self.base(cat_debias=True))

    def test_a_non_default_strength_is_in_the_name(self):
        """Section 179's rule: a constant moved for an experiment belongs in the file name."""
        self.assertNotEqual(self.base(cat_debias=True, cat_debias_shrink=0.75),
                            self.base(cat_debias=True))

    def test_main_defaults_to_off(self):
        p = inspect.signature(fp.main).parameters
        self.assertIs(p['cat_debias'].default, False)
        self.assertEqual(p['cat_debias_shrink'].default, fp.CATDB_SHRINK)


if __name__ == '__main__':
    unittest.main()
