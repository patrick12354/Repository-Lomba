"""Session 30, P0: the constant-vapour identity, and which endpoint each design uses.

`final_pipeline.inc_design` builds `dRH_const_e` as `RH[t-h] * (ratio - 1)` with
`ratio = es(T[t-h]) / es(T[t])`. `an65.rel_design` kept the same multiplier but swapped the
proxy to time t, giving `RH[t] * (ratio - 1)`. At constant vapour pressure the two exact forms
are

    dRH = RH[t-h] * (ratio - 1) = RH[t] * (1 - 1/ratio)

and the mixture `RH[t] * (ratio - 1)` is neither. This is not leakage and not a target error --
every column is still target-blind and causal -- but section 210's arm did not preserve the
parent's physical feature the way its docstring claimed, so the comparison carried an extra
uncontrolled change.

These tests pin the identity itself first, on numbers with no model behind them, then check
which form each design in the repo actually computes.

    .venv/Scripts/python.exe -m unittest discover -s tests -p test_v21_relative_endpoint.py
"""
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
import final_pipeline as fp
import an65_v21_relative_dynamics as a65
import an68_v21_relative_endpoint as a68

_G = {}


def grid():
    if not _G:
        g = fp.load_grid()
        _G['g'], _G['y'], _G['F'] = g, g[fp.TARGET], fp.make_features(g)
    return _G['g'], _G['y'], _G['F']


class Identity(unittest.TestCase):
    """The plan's fixture, verbatim in intent: a closed system at constant vapour pressure."""

    def test_constant_vapour_endpoints(self):
        es = np.array([20., 25., 30., 24., 22.])
        rh = 1200. / es                      # e = RH*es/100 constant by construction
        ratio = es[:-1] / es[1:]             # es(T[t-h]) / es(T[t]) for h = 1
        actual = np.diff(rh)
        np.testing.assert_allclose(rh[:-1] * (ratio - 1), actual)
        np.testing.assert_allclose(rh[1:] * (1 - 1 / ratio), actual)
        self.assertFalse(np.allclose(rh[1:] * (ratio - 1), actual))

    def test_the_mixed_form_is_wrong_by_a_factor_of_ratio(self):
        """Naming the size of the error, so nobody has to rediscover whether it is small."""
        es = np.array([20., 25., 30., 24., 22.])
        rh = 1200. / es
        ratio = es[:-1] / es[1:]
        exact = rh[:-1] * (ratio - 1)
        mixed = rh[1:] * (ratio - 1)
        # RH[t-h] = RH[t] / ratio at constant vapour pressure, so the mixed form overstates the
        # change by exactly `ratio` -- it is the right shape scaled wrong, not noise.
        np.testing.assert_allclose(mixed / ratio, exact)
        self.assertGreater(np.max(np.abs(mixed - exact)), 1.0)


class WhichEndpointEachDesignUses(unittest.TestCase):
    def test_the_production_design_uses_the_previous_endpoint(self):
        _, _, F = grid()
        for h, _lam in fp.INC_SPEC:
            X = fp.inc_design(F, h, fp.INC_PHYS_COLS, True)
            ratio = F['esT'].shift(h) / F['esT']
            np.testing.assert_allclose(X['dRH_const_e'].to_numpy(),
                                       (F['rh_tmin48'].shift(h) * (ratio - 1.0)).to_numpy(),
                                       equal_nan=True)

    def test_the_session_29_relative_design_uses_the_current_endpoint(self):
        """Documenting the artefact as it is, not editing it after the fact."""
        _, _, F = grid()
        X = a65.rel_design(F, 4)
        ratio = F['esT'].shift(4) / F['esT']
        np.testing.assert_allclose(X['dRH_const_e'].to_numpy(),
                                   (F['rh_tmin48'] * (ratio - 1.0)).to_numpy(), equal_nan=True)

    def test_the_new_arm_matches_the_production_form(self):
        _, _, F = grid()
        for h, _lam in fp.INC_SPEC:
            X = a68.rel_design_prev_endpoint(F, h)
            ratio = F['esT'].shift(h) / F['esT']
            np.testing.assert_allclose(X['dRH_const_e'].to_numpy(),
                                       (F['rh_tmin48'].shift(h) * (ratio - 1.0)).to_numpy(),
                                       equal_nan=True)

    def test_only_that_one_column_differs_from_the_session_29_design(self):
        """The arm is a one-column control. If anything else moved it would not be one."""
        _, _, F = grid()
        for h, _lam in fp.INC_SPEC:
            a, b = a65.rel_design(F, h), a68.rel_design_prev_endpoint(F, h)
            self.assertEqual(list(a.columns), list(b.columns))
            differing = [c for c in a.columns
                         if not np.allclose(a[c].to_numpy(), b[c].to_numpy(), equal_nan=True)]
            self.assertEqual(differing, ['dRH_const_e'], h)


class ArmContract(unittest.TestCase):
    def setUp(self):
        self.g, self.y, self.F = grid()
        boundary = self.g.index[(self.g.is_test == 0).to_numpy()].max()
        self.origin = boundary - pd.Timedelta(days=15)
        self.mask = (pd.Series((self.g.is_test == 0).to_numpy(), index=self.g.index)
                     & self.y.notna() & (self.g.index <= self.origin))
        self.idx = self.g.index[(self.g.index > self.origin) & (self.g.index <= boundary)][:200]

    def test_the_arm_keeps_the_offset_invariance_it_inherited(self):
        g2 = self.g.copy()
        g2['pressure'] = g2['pressure'] + 25.0
        F2 = fp.make_features(g2)
        for h, _lam in fp.INC_SPEC:
            np.testing.assert_allclose(a68.rel_design_prev_endpoint(self.F, h).to_numpy(),
                                       a68.rel_design_prev_endpoint(F2, h).to_numpy(),
                                       equal_nan=True, atol=1e-9, rtol=0)

    def test_the_target_never_enters_the_design(self):
        X = a68.rel_design_prev_endpoint(self.F, 4)
        lab = self.y.notna()
        for c in X.columns:
            self.assertNotIn(fp.TARGET, str(c))
            s = X[c].reindex(self.F.index)
            ok = s.notna() & lab
            if int(ok.sum()) > 100 and float(s[ok].std()) > 0:
                self.assertLess(abs(float(np.corrcoef(s[ok], self.y[ok])[0, 1])), 0.999, c)

    def test_labels_after_the_origin_change_no_prediction(self):
        rng = np.random.default_rng(71)
        y2 = self.y.copy()
        after = y2.index > self.origin
        y2[after] = 45.0 + 25.0 * rng.random(int(after.sum()))
        a = a68.fit_prev_endpoint(self.F, self.y, self.mask, (fp.INC_SEED,))
        b = a68.fit_prev_endpoint(self.F, y2, self.mask, (fp.INC_SEED,))
        for h, _lam in fp.INC_SPEC:
            X = a68.rel_design_prev_endpoint(self.F, h).loc[self.idx]
            np.testing.assert_array_equal(a[h][0].predict(X), b[h][0].predict(X))

    def test_no_training_pair_straddles_the_origin(self):
        for h, _lam in fp.INC_SPEC:
            X = a68.rel_design_prev_endpoint(self.F, h)
            tgt = (self.y - self.y.shift(h)).reindex(X.index)
            m = self.mask.reindex(X.index, fill_value=False)
            m = m & tgt.notna() & m.shift(h, fill_value=False)
            used = X.index[m]
            self.assertGreater(len(used), 500)
            self.assertLessEqual(used.max(), self.origin)
            self.assertLessEqual((used - pd.Timedelta(minutes=30 * h)).max(), self.origin)


if __name__ == '__main__':
    unittest.main()
