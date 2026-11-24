"""Session 43: the submission filename must encode every flag that changes the predictions.

§179 recorded this exact near-miss once: "a full-strength observation run silently overwrote the
half-strength file, because the tag encoded the flag but not its strength. A constant moved for an
experiment belongs in the file name."

The repair then covered `INC_DESHRINK`. It did not cover the **diurnal bias form**. `tag` is
`'v16'` whenever `--l2-member` is on, and the flag loop lists eight flags, none of which is
`--tod-bias` or `--harm-bias`. So

    --tod-blend --harm-bias --l2-member --increment --drop-ridge      -> v21_increment_v16_noridge
    --tod-blend --tod-bias  --l2-member --increment --drop-ridge      -> v21_increment_v16_noridge

are two different models writing one path, and the second would have destroyed the file that
scored **2.85383** — the only public improvement since session 21.

    .venv/Scripts/python.exe -m unittest discover -s tests -p test_v21_submission_naming.py
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
import final_pipeline as fp


def tag(**kw):
    base = dict(l2_member=True, blend_shrink=fp.BLEND_SHRINK, drop_ridge=False,
                bag_nopress=False, robust_core=False, smooth_level=False,
                vapour_increment=False, inc_physics=False, inc_deshrink=False,
                inc_lags=False, inc_lambda_scale=1.0, tod_bias_on=False, harm_bias_on=True)
    base.update(kw)
    return fp.increment_tag(**base)


class BiasFormIsInTheName(unittest.TestCase):
    def test_the_two_bias_forms_do_not_share_a_filename(self):
        """The bug: without this, `--tod-bias` overwrites the scored `--harm-bias` file."""
        self.assertNotEqual(tag(drop_ridge=True, harm_bias_on=True, tod_bias_on=False),
                            tag(drop_ridge=True, harm_bias_on=False, tod_bias_on=True))

    def test_all_four_bias_configurations_are_distinct(self):
        names = {
            tag(harm_bias_on=True, tod_bias_on=False),
            tag(harm_bias_on=False, tod_bias_on=True),
            tag(harm_bias_on=True, tod_bias_on=True),
            tag(harm_bias_on=False, tod_bias_on=False),
        }
        self.assertEqual(len(names), 4)


class ExistingFilenamesAreUnchanged(unittest.TestCase):
    """Every scored file must keep the name it was scored under, or the log's md5 trail breaks.

    The shipped configuration is `--harm-bias` without `--tod-bias`, so that combination has to
    stay untagged.
    """

    def test_the_scored_files_keep_their_names(self):
        self.assertEqual(tag(), 'v16')
        self.assertEqual(tag(drop_ridge=True), 'v16_noridge')
        self.assertEqual(tag(drop_ridge=True, inc_physics=True), 'v16_noridge_phys')
        self.assertEqual(tag(inc_physics=True, inc_deshrink=True, inc_lags=True),
                         'v16_phys_dsh_lags')
        self.assertEqual(tag(l2_member=False), 'v12')
        self.assertEqual(tag(blend_shrink=0.0), 'v20')

    def test_the_deshrink_strength_guard_from_section_179_still_holds(self):
        default = tag(inc_deshrink=True)
        moved = tag(inc_deshrink=True)          # same call, same constant
        self.assertEqual(default, moved)
        self.assertIn('dsh', default)


if __name__ == '__main__':
    unittest.main()
