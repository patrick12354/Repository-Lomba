"""Session 46: contracts for the random-convolution increment models.

The mechanism is new but the hazard is the oldest one in this log: an increment target is a
DIFFERENCE OF TWO LABELS, so a design that is sloppy about which endpoints are training rows can
read the scored window without looking like it does. `fp.fit_increments` guards that with a shifted
mask, and this module has to guard it the same way.

    .venv/Scripts/python.exe -m unittest discover -s tests -p test_v21_seq_increment.py
"""
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
import final_pipeline as fp
import v21_seq_increment as si

FAST = dict(n_kernels=24, seeds=(20260906,), alphas=(1000.0,))
_C = {}


def setup():
    if 'f' not in _C:
        g = fp.load_grid()
        F = fp.make_features(g)
        y = g[fp.TARGET]
        lab = F.index[(g.is_test == 0).to_numpy() & y.notna().to_numpy()]
        origin = lab[0] + pd.Timedelta(days=40)
        mask = pd.Series(False, index=F.index)
        mask.loc[lab[lab <= origin]] = True
        scored = lab[(lab > origin) & (lab <= origin + pd.Timedelta(days=3))]
        _C['f'] = (F, y, mask, scored, origin)
    return _C['f']


class Leakage(unittest.TestCase):
    def test_no_label_at_or_after_the_origin_reaches_the_fit(self):
        """Destroying every label from the origin onward must not move the prediction.

        This discriminates: a fit that used the unshifted mask, or that took `tgt` before masking,
        would pick up differences whose earlier endpoint sits after the origin.
        """
        F, y, mask, scored, origin = setup()
        fit = si.fit_seq_increments(F, y, mask, 4, **FAST)
        a = si.predict_seq_increments(fit, F, scored)

        # strictly AFTER the origin: the label AT the origin is a past observation the fit is
        # entitled to use, and poisoning it made the first version of this test fail on a
        # legitimate read rather than on a leak.
        after = y.index > origin
        poisoned = y.copy()
        poisoned.loc[after] = 100.0 - poisoned.loc[after]
        fit2 = si.fit_seq_increments(F, poisoned, mask, 4, **FAST)
        b = si.predict_seq_increments(fit2, F, scored)

        self.assertTrue(np.array_equal(a, b),
                        'the sequence increment read a label at or after the origin')

    def test_a_difference_may_not_straddle_a_hole_in_the_mask(self):
        """What the shifted mask actually guards.

        With a contiguous prefix mask every `t - h` is inside it automatically, so the origin
        gives the guard nothing to do — the first version of this test asserted a property that
        held trivially. The guard earns its place at GAPS: if a stretch of labels is missing, a
        difference spanning it pairs two endpoints that are not h steps apart in reality.
        """
        F, y, mask, _s, origin = setup()
        h = 4
        holed = mask.copy()
        rows_in = F.index[mask.to_numpy()]
        hole = rows_in[(rows_in > origin - pd.Timedelta(days=6))
                       & (rows_in <= origin - pd.Timedelta(days=6) + pd.Timedelta(hours=4))]
        self.assertGreater(len(hole), 0)
        holed.loc[hole] = False

        tgt = (y - y.shift(h)).reindex(F.index)
        m = holed.reindex(F.index, fill_value=False)
        kept = F.index[(m & tgt.notna() & m.shift(h, fill_value=False)).to_numpy()]

        for t in kept:
            self.assertTrue(holed.get(t, False))
            self.assertTrue(holed.get(t - pd.Timedelta(minutes=30 * h), False),
                            '%s pairs an endpoint inside the hole' % t)
        self.assertTrue(set(hole).isdisjoint(set(kept)))


class SolverContract(unittest.TestCase):
    def test_terms_match_the_shape_the_solver_consumes(self):
        """`seq_terms` must be drop-in for `an47.increment_terms`, or the arms are not comparable."""
        import an47_v21_forward_benchmark as a47
        F, y, mask, scored, _o = setup()
        terms = si.seq_terms(F, scored, y, mask, **FAST)
        self.assertEqual(len(terms), len(fp.INC_SPEC))
        for (D, t, lam), (h, lam_ref) in zip(terms, fp.INC_SPEC):
            self.assertEqual(lam, lam_ref, 'the frozen reconciliation weights must not change')
            if D is not None:
                self.assertEqual(D.shape[1], len(scored))
                self.assertEqual(len(t), D.shape[0])
        z = a47.solve(np.full(len(scored), 60.0), scored, terms)
        self.assertEqual(len(z), len(scored))
        self.assertTrue(np.isfinite(z).all())


if __name__ == '__main__':
    unittest.main()
