"""Checks for the session-26 evaluation contract.

Sessions 22-25 decided things on numbers that turned out to depend on row order, on which of
three definitions of "pooled" was in force, and on a seed count nobody had read off the
signature. These tests pin the parts of that contract that can be checked without training a
production model: the metric, the row bookkeeping, the label isolation of the increment
training mask, and the fact that changing a label inside the scored window changes nothing
about the prediction.

    .venv/Scripts/python.exe -m unittest discover -s tests -p test_v21_evaluation.py
"""
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

CACHE = a47.CACHE


def toy_frame(n_per_block=40, seed=0):
    """Two blocks of scored rows shaped like the cache, with no model behind them."""
    rng = np.random.default_rng(seed)
    parts = []
    for i, b in enumerate(a47.PRIMARY_BLOCKS):
        idx = pd.date_range('2023-08-%02d' % (1 + 5 * i), periods=n_per_block, freq='30min')
        y = 60 + 8 * rng.standard_normal(n_per_block)
        parts.append(pd.DataFrame({'block': b, 'scope': 'outer', 'fold': -1, 'datetime': idx,
                                   'y': y, 'recon': y + rng.standard_normal(n_per_block),
                                   'score': True, 'origin': idx[0],
                                   'horizon_end': idx[-1]}))
    return pd.concat(parts, ignore_index=True)


class Metric(unittest.TestCase):
    def test_pooled_equals_the_direct_sse_computation(self):
        P = toy_frame()
        r = a47.report(P, 'toy')
        e = (P.recon - P.y).to_numpy()
        self.assertAlmostEqual(r['pooled'], float(np.sqrt(np.mean(e ** 2))), places=12)

    def test_pooled_is_sse_weighted_not_the_mean_of_block_rmses(self):
        """The bug in section 176: two blocks with different error sizes make the two
        definitions disagree, and only one of them is the RMSE of the union."""
        P = toy_frame()
        big = P.block == a47.PRIMARY_BLOCKS[1]
        P.loc[big, 'recon'] = P.loc[big, 'y'] + 6.0
        P.loc[~big, 'recon'] = P.loc[~big, 'y'] + 1.0
        r = a47.report(P, 'toy')
        self.assertAlmostEqual(r['pooled'], float(np.sqrt((36 + 1) / 2)), places=12)
        self.assertNotAlmostEqual(r['pooled'], 3.5, places=3)

    def test_b3_is_reported_but_never_pooled(self):
        P = toy_frame()
        b3 = P.loc[P.block == a47.PRIMARY_BLOCKS[0]].copy()
        b3['block'] = 'B3_shift7d'
        b3['recon'] = b3.y + 20.0
        both = a47.report(pd.concat([P, b3], ignore_index=True), 'toy')
        self.assertAlmostEqual(both['pooled'], a47.report(P, 'toy')['pooled'], places=12)
        self.assertGreater(both['B3_shift7d'], 19.0)
        self.assertEqual(both['n'], len(P))

    def test_metric_is_invariant_to_row_and_block_order(self):
        P = toy_frame()
        a = a47.report(P, 'toy')
        for seed in (1, 2, 3):
            shuffled = P.sample(frac=1.0, random_state=seed).reset_index(drop=True)
            b = a47.report(shuffled, 'toy')
            for k in a:
                if isinstance(a[k], float):
                    self.assertAlmostEqual(a[k], b[k], places=12, msg=k)

    def test_unscored_rows_do_not_enter_the_metric(self):
        P = toy_frame()
        clean = a47.report(P, 'toy')
        P.loc[len(P)] = dict(P.iloc[0], score=False, recon=999.0,
                             datetime=P.datetime.iloc[0] + pd.Timedelta(days=9))
        self.assertAlmostEqual(a47.report(P, 'toy')['pooled'], clean['pooled'], places=12)

    def test_promotion_bar_needs_both_blocks_and_the_full_margin(self):
        ref = a47.report(toy_frame(), 'ref')
        one_block = dict(ref)
        # A candidate that wins big on B2 and loses on B1 must not be promotable, however
        # good the pooled number looks.
        P = toy_frame()
        b1 = P.block == a47.PRIMARY_BLOCKS[0]
        P.loc[b1, 'recon'] = P.loc[b1, 'y'] + 3.0
        P.loc[~b1, 'recon'] = P.loc[~b1, 'y']
        r = a47.report(P, 'lopsided', one_block)
        self.assertFalse(r['promotable'])


class Bookkeeping(unittest.TestCase):
    def test_blocks_are_the_frozen_calendar_and_b1b2_do_not_overlap(self):
        g = fp.load_grid()
        bl = a47.blocks_of(g)
        self.assertEqual([n for n, _, _ in bl],
                         ['B1_last15d', 'B2_prev15d', 'B3_shift7d'])
        (_, b1s, b1e), (_, b2s, b2e), (_, b3s, b3e) = bl
        self.assertEqual(b1s, b2e)                       # touching, not overlapping
        self.assertLess(b3s, b1s)
        self.assertGreater(b3e, b1s)                     # B3 straddles the B1/B2 seam
        self.assertEqual(list(a47.PRIMARY_BLOCKS), ['B1_last15d', 'B2_prev15d'])

    @unittest.skipUnless(CACHE.exists(), 'forward cache not built')
    def test_cache_timestamps_are_unique_within_each_fold(self):
        C = pd.read_pickle(CACHE)
        for key, d in C.groupby(['block', 'scope', 'fold']):
            self.assertTrue(pd.DatetimeIndex(d.datetime).is_unique, key)

    @unittest.skipUnless(CACHE.exists(), 'forward cache not built')
    def test_every_scored_row_lies_after_its_own_origin(self):
        C = pd.read_pickle(CACHE)
        self.assertTrue((pd.DatetimeIndex(C.datetime) > pd.DatetimeIndex(C.origin)).all())
        self.assertTrue((pd.DatetimeIndex(C.datetime)
                         <= pd.DatetimeIndex(C.horizon_end)).all())

    @unittest.skipUnless(CACHE.exists(), 'forward cache not built')
    def test_inner_scored_windows_do_not_overlap_within_a_block(self):
        """The inner folds themselves overlap by design; the SCORED slices must not, or the
        calibration set double-counts days."""
        C = pd.read_pickle(CACHE)
        inner = C.loc[(C.scope == 'inner') & C.score]
        for b, d in inner.groupby('block'):
            self.assertTrue(pd.DatetimeIndex(d.datetime).is_unique, b)

    @unittest.skipUnless(CACHE.exists(), 'forward cache not built')
    def test_the_calibration_set_ends_before_the_outer_origin(self):
        C = pd.read_pickle(CACHE)
        for b, d in C.groupby('block'):
            outer = d.loc[d.scope == 'outer']
            inner = d.loc[d.scope == 'inner']
            self.assertLessEqual(pd.DatetimeIndex(inner.datetime).max(),
                                 pd.Timestamp(outer.origin.iloc[0]), b)


class LabelIsolation(unittest.TestCase):
    """The increment models are the only place a label can enter, so the mask is where the
    leak would be."""

    def setUp(self):
        self.g = fp.load_grid()
        self.y = self.g[fp.TARGET]
        self.F = fp.make_features(self.g)
        boundary = self.g.index[(self.g.is_test == 0).to_numpy()].max()
        self.origin = boundary - pd.Timedelta(days=15)
        self.mask = (pd.Series((self.g.is_test == 0).to_numpy(), index=self.g.index)
                     & self.y.notna() & (self.g.index <= self.origin))

    def test_no_training_pair_straddles_the_origin(self):
        for h, _ in fp.INC_SPEC:
            X = fp.inc_design(self.F, h, fp.INC_PHYS_COLS, True)
            tgt = (self.y - self.y.shift(h)).reindex(X.index)
            m = self.mask.reindex(X.index, fill_value=False)
            m = m & tgt.notna() & m.shift(h, fill_value=False)
            used = X.index[m]
            self.assertGreater(len(used), 500)
            self.assertLessEqual(used.max(), self.origin)
            earlier = used - pd.Timedelta(minutes=30 * h)
            self.assertLessEqual(earlier.max(), self.origin)
            self.assertTrue(self.y.reindex(earlier).notna().all())

    def test_changing_a_label_after_the_origin_changes_nothing(self):
        """The strongest available leak check: corrupt every label in the scored window and
        confirm the fitted increments are bit-identical."""
        rng = np.random.default_rng(7)
        y2 = self.y.copy()
        after = y2.index > self.origin
        y2[after] = 50.0 + 20.0 * rng.random(int(after.sum()))
        idx = self.g.index[after][:200]
        a = fp.fit_increments(self.F, self.y, self.mask, (fp.INC_SEED,), physics=True)
        b = fp.fit_increments(self.F, y2, self.mask, (fp.INC_SEED,), physics=True)
        for h, _ in fp.INC_SPEC:
            X = fp.inc_design(self.F, h, fp.INC_PHYS_COLS, True).loc[idx]
            np.testing.assert_array_equal(a[h][0].predict(X), b[h][0].predict(X))

    def test_the_deshrink_factor_is_also_blind_to_the_scored_window(self):
        rng = np.random.default_rng(11)
        y2 = self.y.copy()
        after = y2.index > self.origin
        y2[after] = 50.0 + 20.0 * rng.random(int(after.sum()))
        a = fp.fit_increments(self.F, self.y, self.mask, (fp.INC_SEED,), physics=True,
                              deshrink=True)
        b = fp.fit_increments(self.F, y2, self.mask, (fp.INC_SEED,), physics=True,
                              deshrink=True)
        for h, _ in fp.INC_SPEC:
            self.assertEqual(a[('f', h)], b[('f', h)])
            self.assertGreaterEqual(a[('f', h)], fp.DESHRINK_CLIP[0])

    def test_increment_design_never_contains_the_target(self):
        X = fp.inc_design(self.F, 4, fp.INC_PHYS_COLS, True)
        lab = self.y.notna()
        for c in X.columns:
            self.assertNotIn(fp.TARGET, str(c))
            s = X[c].reindex(self.F.index)
            ok = s.notna() & lab
            if int(ok.sum()) > 100 and float(s[ok].std()) > 0:
                r = abs(float(np.corrcoef(s[ok], self.y[ok])[0, 1]))
                self.assertLess(r, 0.999, c)


class SolveAlgebra(unittest.TestCase):
    def test_sparse_solve_matches_a_dense_normal_equation(self):
        rng = np.random.default_rng(3)
        idx = pd.date_range('2023-08-01', periods=64, freq='30min')
        p = 55 + 6 * rng.standard_normal(64)
        terms, A, rhs = [], np.eye(64), p.copy()
        for h, lam in fp.INC_SPEC:
            D, st = fp.diff_operator(idx, h)
            t = rng.standard_normal(D.shape[0])
            terms.append((D, t, lam))
            Dd = D.toarray()
            A = A + lam * Dd.T @ Dd
            rhs = rhs + lam * Dd.T @ t
        np.testing.assert_allclose(a47.solve(p, idx, terms),
                                   np.clip(np.linalg.solve(A, rhs), 5, 100), atol=1e-9)

    def test_a_unit_gain_is_exactly_the_shipped_reconciliation(self):
        """The calibration knob must reduce to the incumbent at a=1, or every comparison
        against the incumbent is measuring two changes at once."""
        g = fp.load_grid()
        y = g[fp.TARGET]
        F = fp.make_features(g)
        boundary = g.index[(g.is_test == 0).to_numpy()].max()
        origin = boundary - pd.Timedelta(days=15)
        mask = (pd.Series((g.is_test == 0).to_numpy(), index=g.index)
                & y.notna() & (g.index <= origin))
        idx = g.index[(g.index > origin) & (g.index <= boundary)][:240]
        inc = fp.fit_increments(F, y, mask, (fp.INC_SEED,), physics=True)
        p = np.full(len(idx), 60.0) + np.arange(len(idx)) * 0.01
        ship = fp.reconcile(p, idx, F, inc)
        mine = a47.solve(p, idx, a47.increment_terms(F, idx, inc, gains={1: 1.0, 4: 1.0}))
        np.testing.assert_allclose(ship, mine, atol=1e-9)


class GainBasis(unittest.TestCase):
    """`an48` searches the gain grid through an affine basis instead of re-solving. If the
    two ever disagree the search is optimising something other than the reported metric."""

    def test_basis_reproduces_the_general_solver_on_the_whole_grid(self):
        import an48_v21_solver_loss as a48
        rng = np.random.default_rng(5)
        idx = pd.date_range('2023-08-01', periods=96, freq='30min')
        terms = []
        for h, lam in fp.INC_SPEC:
            D, st = fp.diff_operator(idx, h)
            terms.append((h, D, rng.standard_normal(D.shape[0]) * 2, lam))
        fold = dict(idx=idx, level=58 + 5 * rng.standard_normal(96), terms=terms,
                    y=58 + 5 * rng.standard_normal(96), score=np.ones(96, bool))
        fold['basis'] = a48.gain_basis(fold)
        for a1 in (0.80, 0.94, 1.0, 1.14, 1.20):
            for a4 in (0.80, 1.0, 1.20):
                gains = {1: a1, 4: a4}
                slow = a47.solve(fold['level'], idx, a48.apply_gains(fold, gains))
                np.testing.assert_allclose(a48.fold_z(fold, gains), slow, atol=1e-9)


if __name__ == '__main__':
    unittest.main()
