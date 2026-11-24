"""Session 40: the OOD stress gate for the `hbt` capacity curve.

Section 110 is the reason this exists. Four shrinkage changes with nested-CV deltas of −0.011 to
−0.041 passed the fold gate, the family gate, the bootstrap AND the random-conditioner control,
and every one of them transferred four to six times worse on the stress blocks. Section 114 turned
that into a standing rule: run the OOD stress evaluation on every candidate, not only on new
members. Family J is a hyper-parameter change of exactly the kind section 110 caught, so it does
not get recommended without this.

Section 109 also fixed the statistic: the mean of per-block RMSEs re-weights toward easy blocks
and reverses verdicts. The competition pools squared error over all rows, so **pooled** is the
number that decides, and these tests pin that too.

    .venv/Scripts/python.exe -m unittest discover -s tests -p test_v21_capacity_stress.py
"""
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
import final_pipeline as fp
import an92_v21_capacity_stress as cs


class Arms(unittest.TestCase):
    def test_the_control_is_the_shipped_hyper_parameters_exactly(self):
        """If the control drifts from `fp.LGB_KW`, the delta is measuring two changes at once."""
        self.assertEqual(cs.ARMS['control'], dict(fp.LGB_KW))

    def test_every_candidate_differs_from_the_control_in_n_estimators_alone(self):
        base = dict(fp.LGB_KW)
        for name, kw in cs.ARMS.items():
            if name == 'control':
                continue
            differing = {k for k in set(base) | set(kw) if base.get(k) != kw.get(k)}
            self.assertEqual(differing, {'n_estimators'},
                             '%s changes %s, so a stress delta would not isolate capacity'
                             % (name, sorted(differing)))

    def test_the_curve_under_test_is_the_one_the_registry_froze(self):
        """The stress arms must be the family-J tree counts, not a fresh grid invented here."""
        import v21_campaign_registry as reg
        registered = {t['params']['n_estimators'] for t in reg.wave2_trials()
                      if set(t['params']) == {'n_estimators'}}
        tested = {kw['n_estimators'] for n, kw in cs.ARMS.items() if n != 'control'}
        self.assertEqual(tested, registered)


class PooledIsTheStatistic(unittest.TestCase):
    """Section 109: a block at RMSE 6.5 carries fourteen times the weight of one at 1.75, so the
    mean of per-block RMSEs is not the competition's metric and must not be the verdict."""

    def test_pooled_weights_blocks_by_row_count_and_squared_error(self):
        # two blocks: one large and hard, one small and easy.
        blocks = [(np.zeros(900), np.full(900, 6.0)), (np.zeros(100), np.full(100, 1.0))]
        pooled = cs.pooled_rmse(blocks)
        mean_of_rmse = float(np.mean([fp.rmse(y, p) for y, p in blocks]))
        self.assertAlmostEqual(pooled, float(np.sqrt((900 * 36 + 100 * 1) / 1000)), places=9)
        self.assertGreater(pooled, mean_of_rmse,
                           'pooled must be dominated by the hard block, unlike the mean')

    def test_pooled_of_one_block_is_that_blocks_rmse(self):
        y, p = np.array([1.0, 2.0, 3.0]), np.array([1.5, 2.5, 2.0])
        self.assertAlmostEqual(cs.pooled_rmse([(y, p)]), fp.rmse(y, p), places=12)


class ShippedParametersResolve(unittest.TestCase):
    """`None` means "the shipped hyper-parameters" for every member, `hbt` included.

    `an92` only ever called `_fit('hbt', ...)` with an explicit arm payload, so the `None` path
    was never exercised and it raised `TypeError` the first time `an93` asked for a plain
    control stack. A helper whose contract is "None = default" has to honour that for the one
    member that also accepts overrides.
    """

    def test_hbt_with_no_overrides_matches_an_explicit_shipped_payload(self):
        g = fp.load_grid()
        F = fp.make_features(g)
        y = g[fp.TARGET]
        lab = F.index[(g.is_test == 0).to_numpy() & y.notna().to_numpy()]
        tr, va = lab[:900], lab[900:1000]

        a = cs._fit('hbt', None, F, y, tr, va)
        b = cs._fit('hbt', dict(fp.LGB_KW), F, y, tr, va)

        self.assertTrue(np.array_equal(a, b))
        self.assertTrue(np.isfinite(a).all())


if __name__ == '__main__':
    unittest.main()
