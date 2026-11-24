"""Checks for the two session-27 mechanisms, before either is allowed to report a number.

`an54` searches over member contributions through a precomputed basis instead of re-solving the
sparse system for every candidate theta, and `an55` reweights the increment training rows by a
calendar-block bootstrap. Both are only worth reading if the shortcut is exact and the resample
is a resample: a basis that drifts from the solver optimises something other than the reported
metric, and five "bags" that draw the same rows are five seeds wearing a new name.

    .venv/Scripts/python.exe -m unittest discover -s tests -p test_v21_mechanisms.py
"""
import hashlib
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'src'))
import final_pipeline as fp
import an47_v21_forward_benchmark as a47
import an54_v21_level_contributions as a54
import an55_v21_block_bagging as a55


def toy_terms(idx, seed=5):
    rng = np.random.default_rng(seed)
    terms = []
    for h, lam in fp.INC_SPEC:
        D, st = fp.diff_operator(idx, h)
        terms.append((D, rng.standard_normal(D.shape[0]) * 2, lam))
    return terms


class LevelContributionBasis(unittest.TestCase):
    def setUp(self):
        self.idx = pd.date_range('2023-08-01', periods=192, freq='30min')
        rng = np.random.default_rng(11)
        self.terms = toy_terms(self.idx)
        self.level = 58 + 5 * rng.standard_normal(len(self.idx))
        self.members = {m: self.level + rng.standard_normal(len(self.idx)) * (1 + i)
                        for i, m in enumerate(['l2', 'ridge', 'enet'])}

    def test_theta_zero_is_exactly_the_shipped_solve(self):
        z0, U, cols = a54.basis(self.level, self.members, self.idx, self.terms)
        np.testing.assert_allclose(a54.apply_theta(z0, U, np.zeros(len(cols))),
                                   a47.solve(self.level, self.idx, self.terms), atol=1e-9)

    def test_nonzero_theta_matches_solving_the_blended_level_directly(self):
        """The whole point of the basis. If these ever disagree the search is optimising a
        linearisation of the metric rather than the metric."""
        z0, U, cols = a54.basis(self.level, self.members, self.idx, self.terms)
        for th in ([0.25, 0.0, 0.0], [0.0, 0.15, 0.10], [0.10, 0.05, 0.05], [0.2, 0.03, 0.02]):
            th = np.array(th)
            blended = (1 - th.sum()) * self.level + sum(
                t * np.asarray(self.members[c]) for t, c in zip(th, cols))
            np.testing.assert_allclose(a54.apply_theta(z0, U, th),
                                       a47.solve(blended, self.idx, self.terms), atol=1e-9)

    def test_the_clip_is_applied_after_the_directions_are_combined(self):
        """`clip(z0) + theta u` and `clip(z0 + theta u)` differ wherever the path leaves the
        physical range, and only the second is what the solver returns."""
        members = {m: np.full(len(self.idx), 300.0) for m in ['l2', 'ridge']}
        z0, U, cols = a54.basis(self.level, members, self.idx, self.terms)
        th = np.array([0.25, 0.0])
        got = a54.apply_theta(z0, U, th)
        self.assertLessEqual(got.max(), 100.0)
        blended = (1 - th.sum()) * self.level + th[0] * members['l2']
        np.testing.assert_allclose(got, a47.solve(blended, self.idx, self.terms), atol=1e-9)

    def test_fit_theta_respects_the_frozen_constraint(self):
        """Fitting against a target the directions can chase all the way must still stop at the
        cap, or `p0` is no longer the thing carrying the time-of-day structure."""
        z0, U, cols = a54.basis(self.level, self.members, self.idx, self.terms)
        target = a54.apply_theta(z0, U, np.array([1.0, 0.0, 0.0]))
        fold = dict(z0=z0, U=U, cols=cols, y=target)
        th, info = a54.fit_theta([fold], cols)
        self.assertTrue((th >= -1e-12).all())
        self.assertLessEqual(th.sum(), a54.THETA_CAP + 1e-9)
        self.assertLess(info['sse'], info['sse0'])

    def test_fit_theta_returns_zero_when_the_directions_only_hurt(self):
        z0, U, cols = a54.basis(self.level, self.members, self.idx, self.terms)
        target = a54.apply_theta(z0, U, np.array([-1.0, -1.0, -1.0]))
        th, _ = a54.fit_theta([dict(z0=z0, U=U, cols=cols, y=target)], cols)
        np.testing.assert_allclose(th, 0.0, atol=1e-6)


class BlockBagging(unittest.TestCase):
    def setUp(self):
        self.rows = pd.date_range('2023-07-01', '2023-08-10', freq='30min')

    def test_blocks_are_three_calendar_days_and_contiguous(self):
        b = a55.block_ids(self.rows)
        self.assertTrue((np.diff(b) >= 0).all())
        for i in np.unique(b):
            span = self.rows[b == i]
            self.assertLessEqual((span.max().normalize() - span.min().normalize()).days,
                                 a55.BLOCK_DAYS - 1)

    def test_the_five_bags_are_five_different_draws(self):
        self.assertEqual(a55.check_bags(self.rows), a55.BAGS)

    def test_a_bag_is_reproducible_from_its_seed(self):
        a, _ = a55.bag_weights(self.rows, 2)
        b, _ = a55.bag_weights(self.rows, 2)
        np.testing.assert_array_equal(a, b)
        c, _ = a55.bag_weights(self.rows, 3)
        self.assertFalse(np.array_equal(a, c))

    def test_a_bag_actually_drops_episodes(self):
        """Sampling blocks with replacement has to leave some out, or the 'bootstrap' is the
        identity and the whole comparison is five seeds against five seeds."""
        for bag in range(a55.BAGS):
            w, prov = a55.bag_weights(self.rows, bag)
            self.assertGreater(prov['zero_fraction'], 0.0)
            self.assertGreater(prov['max_block_weight'], 1.0)
            self.assertEqual(len(w), len(self.rows))

    def test_weights_are_constant_within_a_block(self):
        """A pair must be wholly in or wholly out of a bag; a block boundary may not split one."""
        w, _ = a55.bag_weights(self.rows, 1)
        b = a55.block_ids(self.rows)
        for i in np.unique(b):
            self.assertEqual(len(np.unique(w[b == i])), 1)

    def test_the_weight_vector_hash_identifies_the_draw(self):
        w, prov = a55.bag_weights(self.rows, 4)
        self.assertEqual(prov['weight_md5'], hashlib.md5(w.tobytes()).hexdigest())
        self.assertEqual(prov['rows'], len(self.rows))

    def test_bagging_never_weights_a_row_after_the_origin(self):
        """The weights are indexed by the training rows they are handed, so the guard is that
        the caller's row set is already pre-origin -- and that the weight vector adds nothing
        outside it."""
        origin = self.rows.max()
        w, prov = a55.bag_weights(self.rows, 0)
        self.assertEqual(prov['nonzero_rows'], int((w > 0).sum()))
        self.assertLessEqual(pd.DatetimeIndex(self.rows)[w > 0].max(), origin)


class BaggedIncrementsAreLabelBlind(unittest.TestCase):
    """One end-to-end pass: the bagged builder must be as blind to post-origin labels as the
    shipped one, or the mechanism buys its gain with a leak."""

    def test_labels_after_the_origin_do_not_move_a_bagged_prediction(self):
        g = fp.load_grid()
        y = g[fp.TARGET]
        F = fp.make_features(g)
        boundary = g.index[(g.is_test == 0).to_numpy()].max()
        origin = boundary - pd.Timedelta(days=15)
        mask = (pd.Series((g.is_test == 0).to_numpy(), index=g.index)
                & y.notna() & (g.index <= origin))
        idx = g.index[(g.index > origin) & (g.index <= boundary)][:240]

        rng = np.random.default_rng(41)
        y2 = y.copy()
        after = y2.index > origin
        y2[after] = 45.0 + 25.0 * rng.random(int(after.sum()))

        build = a55.make_bagged_builder([], bags=2)
        a = build(F, y, mask, (fp.INC_SEED,))
        b = build(F, y2, mask, (fp.INC_SEED,))
        for h, _ in fp.INC_SPEC:
            X = fp.inc_design(F, h, a['cols'], True).loc[idx]
            for m1, m2 in zip(a[h], b[h]):
                np.testing.assert_array_equal(m1.predict(X), m2.predict(X))
            self.assertEqual(a[('f', h)], b[('f', h)])

    def test_the_bagged_ensemble_is_the_same_size_as_the_control(self):
        self.assertEqual(a55.BAGS, fp.INC_SEEDS)
        self.assertEqual(len(a47.SEEDS_INC), fp.INC_SEEDS)


class DistributedLag(unittest.TestCase):
    """Lag alignment is where a trajectory model quietly goes wrong: `shift(4)` means two hours
    only on a complete grid, and a target endpoint that happens to sit inside the scored window
    is not a target endpoint you may train on."""

    def setUp(self):
        import an56_v21_distributed_lag as a56
        self.a56 = a56
        self.g = fp.load_grid()
        self.y = self.g[fp.TARGET]

    def test_the_grid_is_complete_so_a_lag_is_a_duration(self):
        d = pd.DatetimeIndex(self.g.index).to_series().diff().dropna()
        self.assertTrue((d == pd.Timedelta(minutes=30)).all())

    def test_lag_k_is_exactly_k_half_hours_back(self):
        F = fp.make_features(self.g)
        X = self.a56.lag_design(F)
        for k in self.a56.LAGS:
            got = X['T_lag%d' % k]
            want = F['T'].shift(k)
            pd.testing.assert_series_equal(got, want, check_names=False)
        # and h=4 is two hours, not four surviving rows
        i = F.index[500]
        self.assertEqual(X.loc[i, 'T_lag4'], F.loc[i - pd.Timedelta(hours=2), 'T'])

    def test_the_design_refuses_a_grid_with_a_hole(self):
        F = fp.make_features(self.g)
        holed = F.drop(F.index[300])
        with self.assertRaises(AssertionError):
            self.a56.lag_design(holed)

    def test_no_actual_humidity_lag_reaches_the_design(self):
        F = fp.make_features(self.g)
        X = self.a56.lag_design(F)
        lab = self.y.notna()
        for c in X.columns:
            self.assertNotIn(fp.TARGET, str(c))
            s = X[c].reindex(F.index)
            ok = s.notna() & lab
            if int(ok.sum()) > 100 and float(s[ok].std()) > 0:
                self.assertLess(abs(float(np.corrcoef(s[ok], self.y[ok])[0, 1])), 0.999, c)

    def test_a_training_pair_never_straddles_the_origin(self):
        F = fp.make_features(self.g)
        boundary = self.g.index[(self.g.is_test == 0).to_numpy()].max()
        origin = boundary - pd.Timedelta(days=15)
        mask = (pd.Series((self.g.is_test == 0).to_numpy(), index=self.g.index)
                & self.y.notna() & (self.g.index <= origin))
        m = self.a56.lag_mask(mask, F.index)
        used = F.index[m.to_numpy()]
        self.assertGreater(len(used), 500)
        for h in self.a56.HORIZONS:
            earlier = used - pd.Timedelta(minutes=30 * h)
            self.assertLessEqual(earlier.max(), origin)
            self.assertTrue(self.y.reindex(earlier).notna().all())

    def test_inference_needs_no_target_history_at_all(self):
        """Predicting at rows whose own RH and whose lagged RH are both missing must still
        work, because nothing in the design reads the target."""
        F = fp.make_features(self.g)
        X = self.a56.lag_design(F)
        T = self.a56.lag_targets(self.y)
        boundary = self.g.index[(self.g.is_test == 0).to_numpy()].max()
        origin = boundary - pd.Timedelta(days=15)
        mask = (pd.Series((self.g.is_test == 0).to_numpy(), index=self.g.index)
                & self.y.notna() & (self.g.index <= origin))
        rows = F.index[(self.a56.lag_mask(mask, F.index) & T.notna().all(axis=1)).to_numpy()]
        model = self.a56.fit_lag_model(X, T, rows, 100.0)
        test_rows = self.g.index[(self.g.is_test == 1).to_numpy()][:200]
        self.assertTrue(self.y.reindex(test_rows).isna().all())
        p = model.predict(X.loc[test_rows])
        self.assertEqual(p.shape, (len(test_rows), len(self.a56.HORIZONS)))
        self.assertTrue(np.isfinite(p).all())

    def test_zero_blend_reproduces_the_shipped_reconciliation_exactly(self):
        """The control has to be the incumbent, or the comparison measures two changes."""
        F = fp.make_features(self.g)
        boundary = self.g.index[(self.g.is_test == 0).to_numpy()].max()
        origin = boundary - pd.Timedelta(days=15)
        mask = (pd.Series((self.g.is_test == 0).to_numpy(), index=self.g.index)
                & self.y.notna() & (self.g.index <= origin))
        idx = self.g.index[(self.g.index > origin) & (self.g.index <= boundary)][:240]
        inc = fp.fit_increments(F, self.y, mask, (fp.INC_SEED,), physics=True, deshrink=True)
        inc['lag_blend'] = 0.0
        inc['lag_model'] = None
        p = np.full(len(idx), 60.0) + np.arange(len(idx)) * 0.01
        np.testing.assert_allclose(a47.solve(p, idx, self.a56.lag_terms(F, idx, inc)),
                                   fp.reconcile(p, idx, F, inc), atol=1e-9)


class ForwardFactor(unittest.TestCase):
    def test_the_forward_estimator_never_trains_across_its_own_validation_window(self):
        import an53_v21_controls_forward_factor as a53
        rng = np.random.default_rng(3)
        rows = pd.date_range('2023-07-01', periods=4000, freq='30min')
        X = pd.DataFrame({'a': rng.standard_normal(len(rows))}, index=rows)
        tgt = pd.Series(rng.standard_normal(len(rows)) * 2, index=rows)
        seen = []

        class Spy(a53.lgb.LGBMRegressor):
            def fit(self, Xf, yf, **kw):
                seen.append((Xf.index.min(), Xf.index.max()))
                return super().fit(Xf, yf, **kw)

        real = a53.lgb.LGBMRegressor
        a53.lgb.LGBMRegressor = Spy
        try:
            f, prov = a53.forward_factor(X, tgt, rows, h=4)
        finally:
            a53.lgb.LGBMRegressor = real
        self.assertGreater(len(seen), 0)
        chunks = np.array_split(np.arange(len(rows)), a53.FWD_FOLDS + 1)[1:]
        starts = sorted(rows[c].min() for c in chunks)
        for (_, tr_end), va_start in zip(seen, starts[-len(seen):]):
            # both endpoints of every training pair sit strictly before the window predicted
            self.assertLess(tr_end + pd.Timedelta(minutes=30 * 4), va_start)
        self.assertGreaterEqual(f, fp.DESHRINK_CLIP[0])
        self.assertLessEqual(f, fp.DESHRINK_CLIP[1])

    def test_a_hopeless_history_falls_back_to_one_rather_than_widening_blindly(self):
        import an53_v21_controls_forward_factor as a53
        rows = pd.date_range('2023-07-01', periods=60, freq='30min')
        X = pd.DataFrame({'a': np.arange(60.0)}, index=rows)
        tgt = pd.Series(np.arange(60.0), index=rows)
        f, prov = a53.forward_factor(X, tgt, rows, h=1)
        self.assertEqual(f, 1.0)
        self.assertTrue(prov['fallback'])
        self.assertEqual(prov['splits_used'], 0)


if __name__ == '__main__':
    unittest.main()
