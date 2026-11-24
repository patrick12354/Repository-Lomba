"""Session 41: the soil block, whose exclusion has outlived both of its justifications.

`drop_soil` removes 76 columns from every member and has done since session 2. Its stated reasons,
in order:

* **§7**: "only 7-12 % of test values have training support". **§97 withdrew this** -- on the
  current cleaning 70 of the 76 have full support.
* **§97's fallback**: "the decision survives on other grounds -- §96 shows the block carries no
  residual signal at all". §96's headline (the information ceiling) is itself **withdrawn** in the
  file banner and in §229; what survives of it for soil is one residual-stage test on a
  session-14 blend, which is not a test of the columns as FEATURES in the v21 stack.

Re-measuring the support directly splits the two claims apart. On the private slice 68 of 76
columns sit at support 1.000, and the six that collapse are all `_sd6h` **dispersion** columns --
`soil_humidity_line3_sd6h` at 0.0000, `soil_humidity_line2_sd6h` at 0.0000. That is §7's mechanism
("the probes stop fluctuating when irrigation halts": test std is 0.16-0.23x train std) applying to
six columns rather than to seventy-six.

So the audited decision is "drop six", not "drop seventy-six", and this module builds the frames
that test it.

    .venv/Scripts/python.exe -m unittest discover -s tests -p test_v21_soil_features.py
"""
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
import final_pipeline as fp
import v21_soil_features as sf

_C = {}


def frames():
    if 'f' not in _C:
        g = fp.load_grid()
        _C['f'] = (g, fp.make_features(g), sf.augmented_features(g))
    return _C['f']


class Additive(unittest.TestCase):
    """The arm must be the incumbent frame PLUS columns. If restoring soil also perturbs a kept
    column, a delta cannot be attributed to the soil block."""

    def test_every_incumbent_column_survives_with_identical_values(self):
        _g, F, A = frames()
        self.assertTrue(set(F.columns) <= set(A.columns))
        for c in F.columns:
            self.assertTrue(np.array_equal(F[c].to_numpy(), A[c].to_numpy(), equal_nan=True),
                            '%s changed when the soil block was restored' % c)

    def test_the_restored_columns_are_exactly_what_drop_soil_removes(self):
        _g, F, A = frames()
        restored = [c for c in A.columns if c not in set(F.columns)]
        self.assertEqual(len(restored), 76)
        self.assertTrue(all(c.startswith('soil_') or c.endswith('_rate') for c in restored))


class SupportSplit(unittest.TestCase):
    """The audit finding, pinned so a later change cannot quietly restore the broken columns."""

    def test_the_collapsing_columns_are_the_six_dispersion_ones(self):
        g, _F, A = frames()
        bad = sf.low_support_soil(g, A)
        self.assertEqual(len(bad), 6)
        self.assertTrue(all(c.endswith('_sd6h') for c in bad),
                        'the columns that lose support should be the dispersion ones: %s' % bad)

    def test_the_supported_set_excludes_them_and_keeps_the_rest(self):
        g, F, A = frames()
        cols = sf.column_set(g, A, 'supported')
        bad = set(sf.low_support_soil(g, A))
        self.assertEqual(len(cols), A.shape[1] - 6)
        self.assertFalse(bad & set(cols))
        self.assertTrue(set(F.columns) <= set(cols), 'the incumbent columns must all be kept')

    def test_the_dispersion_only_arm_is_the_incumbent_plus_exactly_those_six(self):
        """K04 is the negative control: if support is the mechanism, this arm should be the bad
        one. It only isolates that if it adds the six and nothing else."""
        g, F, A = frames()
        cols = sf.column_set(g, A, 'dispersion_only')
        self.assertEqual(set(cols) - set(F.columns), set(sf.low_support_soil(g, A)))

    def test_an_unknown_column_set_is_refused_rather_than_silently_defaulted(self):
        g, _F, A = frames()
        with self.assertRaises(ValueError):
            sf.column_set(g, A, 'whatever')


class Registered(unittest.TestCase):
    def test_family_k_is_the_three_arms_including_the_dispersion_control(self):
        import v21_campaign_registry as reg
        T = reg.wave3_trials()
        self.assertEqual([t['id'] for t in T], ['K01', 'K02', 'K03'])
        self.assertEqual([t['params']['columns'] for t in T],
                         ['supported', 'all_soil', 'dispersion_only'])
        self.assertEqual(reg.by_id(T)['K03']['kind'], 'control')
        self.assertTrue(all(t['component'] == 'hbt_features' for t in T))

    def test_the_runner_can_resolve_family_k(self):
        import v21_campaign_registry as reg
        self.assertTrue({'K01', 'K02', 'K03'} <= set(reg.by_id(reg.all_trials())))

    def test_the_arms_are_three_genuinely_different_column_sets(self):
        """K01 and K02 differ by exactly the six broken columns; a wave where two arms are the
        same set would report one finding under two labels, which is the defect §265 caught in
        family A."""
        g, _F, A = frames()
        sets = {n: set(sf.column_set(g, A, n))
                for n in ('incumbent', 'supported', 'all_soil', 'dispersion_only')}
        self.assertEqual(len({frozenset(v) for v in sets.values()}), 4)
        self.assertEqual(sets['all_soil'] - sets['supported'],
                         set(sf.low_support_soil(g, A)))


if __name__ == '__main__':
    unittest.main()
