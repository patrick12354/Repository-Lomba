"""Checks for the session-28 production integration: the lag increment design and the split
between build-path and reporting fingerprints.

Two things have to be true before `--inc-lags` may generate a submission. The design that ships
must be the design that was scored -- column for column, value for value, and in the same ORDER,
because LightGBM breaks equal-gain splits by feature index and a reordering is a different model.
And the manifest guard has to keep refusing a cache whose meaning moved while tolerating a file
that changed for a reason the cache cannot see; otherwise the honest response to a renamed helper
is a sixteen-minute rebuild, which is what happened twice in session 27.

    .venv/Scripts/python.exe -m unittest discover -s tests -p test_v21_production_lags.py
"""
import json
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
import final_pipeline as fp
import an47_v21_forward_benchmark as a47
import an60_v21_lag_factor_ablation as a60

_G = {}


def grid():
    if not _G:
        g = fp.load_grid()
        _G['g'], _G['y'], _G['F'] = g, g[fp.TARGET], fp.make_features(g)
    return _G['g'], _G['y'], _G['F']


class ProductionDesignIsTheScoredDesign(unittest.TestCase):
    def test_the_shipped_design_equals_the_ablation_design_exactly(self):
        """The contract that lets section 202's number describe the submission."""
        _, _, F = grid()
        for h, _lam in fp.INC_SPEC:
            a = a60.extra_design(F, h)
            b = fp.inc_lag_design(F, h, fp.INC_PHYS_COLS, True)
            self.assertEqual(list(a.columns), list(b.columns), h)
            pd.testing.assert_frame_equal(a, b)

    def test_lags_off_is_byte_for_byte_the_incumbent_design(self):
        _, _, F = grid()
        for h, _lam in fp.INC_SPEC:
            pd.testing.assert_frame_equal(
                fp.increment_design(F, h, fp.INC_PHYS_COLS, True, False),
                fp.inc_design(F, h, fp.INC_PHYS_COLS, True))

    def test_the_design_adds_columns_and_keeps_the_incumbent_block_in_front(self):
        _, _, F = grid()
        for h, _lam in fp.INC_SPEC:
            base = fp.inc_design(F, h, fp.INC_PHYS_COLS, True)
            got = fp.inc_lag_design(F, h, fp.INC_PHYS_COLS, True)
            self.assertGreater(got.shape[1], base.shape[1])
            self.assertEqual(list(got.columns)[:base.shape[1]], list(base.columns))

    def test_the_lag_block_adds_no_duplicate_of_anything_already_present(self):
        """Scoped to what this change is responsible for.

        `inc_design` already ships four value-duplicate pairs of its own -- `T` IS
        `air_temperature`, and the `_prev` block reproduces `air_temperature_s1`, `co2_s1` and
        `pressure_s1`. Those are the incumbent's, they are in the model that scored 2.86595, and
        removing them is a different experiment. What this test pins is that the lag block does
        not ADD any, by name or by value."""
        _, _, F = grid()
        for h, _lam in fp.INC_SPEC:
            base = fp.inc_design(F, h, fp.INC_PHYS_COLS, True)
            X = fp.inc_lag_design(F, h, fp.INC_PHYS_COLS, True)
            self.assertEqual(len(set(X.columns)), X.shape[1], h)
            added = [c for c in X.columns if c not in base.columns]
            self.assertGreater(len(added), 0)
            for i, c in enumerate(added):
                self.assertFalse(any(X[c].equals(base[b]) for b in base.columns),
                                 '%s duplicates an incumbent column at h=%d' % (c, h))
                for d in added[i + 1:]:
                    self.assertFalse(X[c].equals(X[d]),
                                     '%s duplicates %s at h=%d' % (c, d, h))

    def test_lag_k_is_exactly_k_half_hours(self):
        _, _, F = grid()
        X = fp.inc_lag_design(F, 4, fp.INC_PHYS_COLS, True)
        i = F.index[600]
        for k in fp.INC_LAGS:
            col = 'T_lag%d' % k
            if col in X.columns:
                self.assertEqual(X.loc[i, col], F.loc[i - pd.Timedelta(minutes=30 * k), 'T'])

    def test_the_design_refuses_an_incomplete_grid(self):
        _, _, F = grid()
        with self.assertRaises(AssertionError):
            fp.inc_lag_design(F.drop(F.index[400]), 1, fp.INC_PHYS_COLS, True)

    def test_the_design_never_contains_the_target(self):
        _, y, F = grid()
        X = fp.inc_lag_design(F, 4, fp.INC_PHYS_COLS, True)
        lab = y.notna()
        for c in X.columns:
            self.assertNotIn(fp.TARGET, str(c))
            s = X[c].reindex(F.index)
            ok = s.notna() & lab
            if int(ok.sum()) > 100 and float(s[ok].std()) > 0:
                self.assertLess(abs(float(np.corrcoef(s[ok], y[ok])[0, 1])), 0.999, c)


class FitAndReconcileHonourTheFlag(unittest.TestCase):
    def setUp(self):
        self.g, self.y, self.F = grid()
        boundary = self.g.index[(self.g.is_test == 0).to_numpy()].max()
        self.origin = boundary - pd.Timedelta(days=15)
        self.mask = (pd.Series((self.g.is_test == 0).to_numpy(), index=self.g.index)
                     & self.y.notna() & (self.g.index <= self.origin))
        self.idx = self.g.index[(self.g.index > self.origin) & (self.g.index <= boundary)][:240]

    def test_the_flag_is_recorded_and_changes_the_fitted_models(self):
        off = fp.fit_increments(self.F, self.y, self.mask, (fp.INC_SEED,), physics=True)
        on = fp.fit_increments(self.F, self.y, self.mask, (fp.INC_SEED,), physics=True, lags=True)
        self.assertFalse(off['lags'])
        self.assertTrue(on['lags'])
        self.assertEqual(off[1][0].n_features_, fp.inc_design(
            self.F, 1, fp.INC_PHYS_COLS, True).shape[1])
        self.assertEqual(on[1][0].n_features_, fp.inc_lag_design(
            self.F, 1, fp.INC_PHYS_COLS, True).shape[1])

    def test_reconcile_feeds_the_matching_design_back_in(self):
        """A model fitted on 158 columns and scored on 138 would raise, or worse, silently
        mis-align; this proves the solve round-trips."""
        inc = fp.fit_increments(self.F, self.y, self.mask, (fp.INC_SEED,), physics=True,
                                deshrink=True, lags=True)
        p = np.full(len(self.idx), 60.0) + np.arange(len(self.idx)) * 0.01
        z = fp.reconcile(p, self.idx, self.F, inc)
        self.assertEqual(len(z), len(self.idx))
        self.assertTrue(np.isfinite(z).all())
        self.assertFalse(np.allclose(z, fp.reconcile(p, self.idx, self.F, fp.fit_increments(
            self.F, self.y, self.mask, (fp.INC_SEED,), physics=True, deshrink=True))))

    def test_an_inc_dict_without_the_key_still_means_no_lags(self):
        """Every increment bundle written before session 28 lacks `lags`; they must keep
        reconciling exactly as they did."""
        inc = fp.fit_increments(self.F, self.y, self.mask, (fp.INC_SEED,), physics=True,
                                deshrink=True)
        legacy = {k: v for k, v in inc.items() if k != 'lags'}
        p = np.full(len(self.idx), 60.0) + np.arange(len(self.idx)) * 0.01
        np.testing.assert_allclose(fp.reconcile(p, self.idx, self.F, legacy),
                                   fp.reconcile(p, self.idx, self.F, inc), atol=0)

    def test_labels_after_the_origin_do_not_move_a_lag_increment(self):
        rng = np.random.default_rng(53)
        y2 = self.y.copy()
        after = y2.index > self.origin
        y2[after] = 45.0 + 25.0 * rng.random(int(after.sum()))
        a = fp.fit_increments(self.F, self.y, self.mask, (fp.INC_SEED,), physics=True,
                              deshrink=True, lags=True)
        b = fp.fit_increments(self.F, y2, self.mask, (fp.INC_SEED,), physics=True,
                              deshrink=True, lags=True)
        for h, _lam in fp.INC_SPEC:
            X = fp.inc_lag_design(self.F, h, fp.INC_PHYS_COLS, True).loc[self.idx]
            np.testing.assert_array_equal(a[h][0].predict(X), b[h][0].predict(X))
            self.assertEqual(a[('f', h)], b[('f', h)])

    def test_no_training_pair_straddles_the_origin_under_lags(self):
        for h, _lam in fp.INC_SPEC:
            X = fp.inc_lag_design(self.F, h, fp.INC_PHYS_COLS, True)
            tgt = (self.y - self.y.shift(h)).reindex(X.index)
            m = self.mask.reindex(X.index, fill_value=False)
            m = m & tgt.notna() & m.shift(h, fill_value=False)
            used = X.index[m]
            self.assertGreater(len(used), 500)
            self.assertLessEqual(used.max(), self.origin)
            self.assertLessEqual((used - pd.Timedelta(minutes=30 * h)).max(), self.origin)


class FingerprintSplit(unittest.TestCase):
    """Session 27 rebuilt a 16-minute cache to prove a renamed reporting helper had changed
    nothing. The build path is now fingerprinted on its own."""

    def test_every_declared_build_path_function_resolves(self):
        bf = a47.build_fingerprint()
        self.assertEqual([k for k, v in bf.items() if v == 'MISSING'], [])
        self.assertIn('constants', bf)
        self.assertIn('fp.make_features', bf)
        self.assertIn('a47.build_block', bf)

    def test_the_fingerprint_moves_when_a_build_function_moves(self):
        before = a47.build_fingerprint()
        real = fp.make_features
        try:
            fp.make_features = lambda grid: None      # a different function body
            after = a47.build_fingerprint()
        finally:
            fp.make_features = real
        self.assertNotEqual(before['fp.make_features'], after['fp.make_features'])
        self.assertEqual(before['a47.build_block'], after['a47.build_block'])

    def test_a_reporting_only_change_is_not_a_build_change(self):
        """`bootstrap_pair` and `report` are reporting; neither is in the build path."""
        for name in ('bootstrap_pair', 'report', 'bootstrap', 'score_config'):
            self.assertNotIn('a47.' + name, a47.build_fingerprint())

    def test_a_constant_the_build_reads_moves_the_fingerprint(self):
        before = a47.build_fingerprint()['constants']
        real = fp.HARM_SHRINK
        try:
            fp.HARM_SHRINK = 0.123
            self.assertNotEqual(before, a47.build_fingerprint()['constants'])
        finally:
            fp.HARM_SHRINK = real
        self.assertEqual(before, a47.build_fingerprint()['constants'])


class ManifestGuard(unittest.TestCase):
    def setUp(self):
        self.tmp = ROOT / 'outputs' / 'audit_v21_s28' / '_test_guard'
        self.tmp.mkdir(parents=True, exist_ok=True)
        self.cache = self.tmp / 'forward_predictions.pkl'
        self.man = self.tmp / 'manifest.json'
        pd.DataFrame({'block': ['B1_last15d'], 'scope': ['outer'], 'fold': [-1],
                      'datetime': [pd.Timestamp('2023-08-15')], 'y': [50.0], 'level': [50.0],
                      'score': [True], 'origin': [pd.Timestamp('2023-08-14 14:30')],
                      'horizon_end': [pd.Timestamp('2023-08-29 14:30')], 'meta_rows': [100],
                      'meta_days': [3], 'meta_fallback': [False]}).to_pickle(self.cache)
        self.base = dict(inputs=a47.input_hashes(), code=a47.code_hashes(),
                         build_code=a47.build_fingerprint(),
                         config=a47.manifest_config(False), cache_md5=a47.md5(self.cache))
        self.man.write_text(json.dumps(self.base, indent=2))

    def tearDown(self):
        for p in (self.cache, self.man):
            if p.exists():
                p.unlink()
        if self.tmp.exists():
            self.tmp.rmdir()

    def test_a_matching_manifest_loads(self):
        self.assertEqual(len(a47.load_cache(self.cache, self.man)), 1)

    def test_a_build_path_change_is_still_refused(self):
        man = dict(self.base)
        man['build_code'] = dict(man['build_code'], **{'fp.make_features': '0' * 32})
        self.man.write_text(json.dumps(man))
        with self.assertRaises(ValueError) as e:
            a47.load_cache(self.cache, self.man)
        self.assertIn('build_code[fp.make_features]', str(e.exception))

    def test_a_whole_file_change_alone_is_tolerated_once_the_build_path_matches(self):
        """The session-28 case: `final_pipeline.py` gained `--inc-lags`, which cannot reach a
        cached level."""
        man = dict(self.base)
        man['code'] = dict(man['code'], **{'final_pipeline.py': '0' * 32})
        self.man.write_text(json.dumps(man))
        self.assertEqual(len(a47.load_cache(self.cache, self.man)), 1)

    def test_a_manifest_without_the_fingerprint_still_checks_whole_files(self):
        man = {k: v for k, v in self.base.items() if k != 'build_code'}
        man['code'] = dict(man['code'], **{'final_pipeline.py': '0' * 32})
        self.man.write_text(json.dumps(man))
        with self.assertRaises(ValueError) as e:
            a47.load_cache(self.cache, self.man)
        self.assertIn('final_pipeline.py', str(e.exception))

    def test_a_swapped_pickle_is_still_refused(self):
        pd.read_pickle(self.cache).head(0).to_pickle(self.cache)
        with self.assertRaises(ValueError) as e:
            a47.load_cache(self.cache, self.man)
        self.assertIn('cache_md5', str(e.exception))


if __name__ == '__main__':
    unittest.main()
