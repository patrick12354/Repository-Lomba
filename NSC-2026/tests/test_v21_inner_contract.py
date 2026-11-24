"""Checks for the session-27 inner calibration contract.

Session 26's harness picked the meta rows an inner fold learned from by FOLD NUMBER. Folds are
8-day windows at a 2-day step, so fold k-1's labels run six days past fold k's origin and every
inner origin fitted its stack partly on its own future; the first scored fold was then scored on
its whole window rather than its tail, so 864 of 2304 calibration rows were scored under
parameters fitted from their own labels. `src/an52_v21_inner_contract.py` counts it. These tests
pin the fix, and the first one fails against the old rule on purpose.

The expensive checks run the real chain -- members, stack, time-of-day blend, harmonic bias,
increment models, de-shrink factor and the sparse solve -- on a two-member backbone and one
seed. That is not the shipped ensemble, but it is the shipped code path, which is what a leak
would have to travel through.

    .venv/Scripts/python.exe -m unittest discover -s tests -p test_v21_inner_contract.py
"""
import json
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'src'))
import final_pipeline as fp
import an36_increment_production as a36
import an47_v21_forward_benchmark as a47
import an52_v21_inner_contract as a52

CHEAP = dict(models=['ridge', 'enet'], seeds_oof=(0,), seeds_fit=(0,))
_GRID = {}


def grid():
    if 'g' not in _GRID:
        g = fp.load_grid()
        _GRID['g'] = g
        _GRID['y'] = g[fp.TARGET]
    return _GRID['g'], _GRID['y']


def smallest_block():
    """B2: three inner folds, so the chain runs three times instead of eight."""
    g, _ = grid()
    return a47.blocks_of(g)[1]


class MetaSelection(unittest.TestCase):
    """The rule itself, on the fold geometry, with no model behind it."""

    def setUp(self):
        g, y = grid()
        self.plan = a52.inner_plan(g, y)

    def test_the_fold_number_rule_reproduces_the_audits_overlap(self):
        """A regression test for the bug, not for the fix: if this stops reproducing 864 of
        2304 then the geometry changed and section 190's numbers no longer describe it."""
        old = a52.session26_overlap(self.plan)
        self.assertEqual(int(old.scored.sum()), 2304)
        self.assertEqual(int(old.overlapping.sum()), 864)
        per = old.groupby('block').overlapping.sum()
        self.assertEqual(int(per['B1_last15d']), 288)
        self.assertEqual(int(per['B2_prev15d']), 288)
        self.assertEqual(int(per['B3_shift7d']), 288)
        # And every origin, not only the three that were scored on their whole window, fitted
        # its stack partly on labels from after itself.
        self.assertTrue((old.meta_rows_after_origin > 0).all())

    def test_every_meta_label_is_at_or_before_its_own_origin(self):
        for name, (hs, he, spans) in self.plan.items():
            for fi in sorted(spans):
                vs = spans[fi][0]
                prior = pd.DatetimeIndex([])
                for f, (vs2, _, v2) in spans.items():
                    if f != fi and vs2 <= vs:
                        prior = prior.append(v2[v2 <= vs])
                if len(prior):
                    self.assertLessEqual(prior.max(), vs, (name, fi))

    def test_meta_prior_drops_rows_by_timestamp_not_by_fold_number(self):
        """The direct unit check on the selector: a later fold's window contains rows on both
        sides of an earlier origin, and only the earlier ones may come through."""
        idx = pd.date_range('2023-07-18 15:00', periods=8 * 48, freq='30min')
        O = pd.DataFrame({'dt': idx.append(idx + pd.Timedelta(days=2)),
                          'fold': [0] * len(idx) + [1] * len(idx)})
        spans = {0: (idx[0], idx[-1]), 1: (idx[0] + pd.Timedelta(days=2),
                                           idx[-1] + pd.Timedelta(days=2))}
        origin = idx[0] + pd.Timedelta(days=1)
        got = a47.meta_prior(O, spans, origin)
        self.assertTrue((pd.DatetimeIndex(got.dt) <= origin).all())
        self.assertEqual(len(got), 49)           # one day of fold 0 inclusive, not its whole window
        # Fold 1 was fitted at an origin two days after this one, so none of its rows are
        # admissible even where their own timestamps would be early enough.
        self.assertEqual(set(got.fold), {0})
        # Same frame, a later origin: fold 1 becomes admissible, and only up to that origin.
        later = a47.meta_prior(O, spans, idx[0] + pd.Timedelta(days=3))
        self.assertEqual(set(later.fold), {0, 1})
        self.assertLessEqual(pd.DatetimeIndex(later.dt).max(), idx[0] + pd.Timedelta(days=3))

    def test_a_fold_without_enough_history_falls_back_instead_of_borrowing(self):
        new = a52.session27_contract(self.plan)
        thin = new.loc[new.meta_rows < a47.MIN_META_ROWS]
        self.assertGreater(len(thin), 0)
        self.assertTrue(thin.fallback.all())
        self.assertTrue((thin.scored == 0).all())
        self.assertTrue((new.loc[~new.fallback].meta_rows >= a47.MIN_META_ROWS).all())
        self.assertTrue((new.loc[~new.fallback].meta_days >= a47.MIN_META_DAYS).all())

    def test_no_scored_row_overlaps_the_meta_labels_behind_it(self):
        new = a52.session27_contract(self.plan)
        self.assertEqual(int(new.overlapping.sum()), 0)
        self.assertGreater(int(new.loc[~new.fallback].scored.sum()), 0)


class FeatureMatrices(unittest.TestCase):
    def test_the_split_call_reproduces_an36_when_both_frames_are_the_same(self):
        g, y = grid()
        _, hs, he = smallest_block()
        F = fp.make_features(g.loc[g.index <= he])
        lab = pd.Series((g.loc[g.index <= he].is_test == 0).values, index=F.index) \
            & y.reindex(F.index).notna()
        pre = F.index[lab.to_numpy() & (F.index <= hs)]
        t, v = pre[:-96], pre[-96:]
        a = a36.member_preds(F, y, t, v, ['ridge', 'enet'], (0,))
        b = a47.member_preds(F, F, y, t, v, ['ridge', 'enet'], (0,))
        pd.testing.assert_frame_equal(a, b)

    def test_frame_at_stops_where_it_is_told(self):
        g, _ = grid()
        end = g.index[(g.is_test == 0).to_numpy()].max() - pd.Timedelta(days=20)
        gh, F = a47.frame_at(g, end)
        self.assertEqual(gh.index.max(), end)
        self.assertEqual(F.index.max(), end)

    def test_exogenous_after_the_horizon_cannot_reach_the_features(self):
        """The property `--train-features-at-origin` was named for and did not have. Sensors
        recorded after a fold's horizon must not move a single feature value inside it; sensors
        recorded INSIDE the horizon are joint-window exogenous and are allowed to."""
        g, _ = grid()
        end = g.index[(g.is_test == 0).to_numpy()].max() - pd.Timedelta(days=20)
        _, base = a47.frame_at(g, end)
        rng = np.random.default_rng(19)

        g2 = g.copy()
        after = g2.index > end
        g2.loc[after, 'air_temperature'] += 15.0 * rng.random(int(after.sum()))
        _, moved = a47.frame_at(g2, end)
        pd.testing.assert_frame_equal(base, moved)

        g3 = g.copy()
        inside = (g3.index > end - pd.Timedelta(days=1)) & (g3.index <= end)
        g3.loc[inside, 'air_temperature'] += 15.0
        _, near = a47.frame_at(g3, end)
        self.assertFalse(near.equals(base))

    def test_an_inner_fold_is_built_from_its_own_horizon_not_the_blocks(self):
        g, y = grid()
        name, hs, he = smallest_block()
        out = a47.build_block(g, y, name, hs, he, **CHEAP)
        inner = out.loc[out.scope == 'inner']
        self.assertGreater(inner.horizon_end.nunique(), 1)
        self.assertTrue((pd.DatetimeIndex(inner.horizon_end) < he).all())
        self.assertEqual(pd.Timestamp(out.loc[out.scope == 'outer'].horizon_end.iloc[0]), he)


class Manifest(unittest.TestCase):
    def setUp(self):
        self.tmp = ROOT / 'outputs' / 'audit_v21_s27' / '_test_manifest'
        self.tmp.mkdir(parents=True, exist_ok=True)
        self.cache = self.tmp / 'forward_predictions.pkl'
        self.man = self.tmp / 'manifest.json'
        pd.DataFrame({'block': ['B1_last15d'], 'scope': ['outer'], 'fold': [-1],
                      'datetime': [pd.Timestamp('2023-08-15')], 'y': [50.0],
                      'level': [50.0], 'score': [True],
                      'origin': [pd.Timestamp('2023-08-14 14:30')],
                      'horizon_end': [pd.Timestamp('2023-08-29 14:30')],
                      'meta_rows': [100], 'meta_days': [3],
                      'meta_fallback': [False]}).to_pickle(self.cache)
        self.base = dict(inputs=a47.input_hashes(), code=a47.code_hashes(),
                         config=a47.manifest_config(False), cache_md5=a47.md5(self.cache))
        self.man.write_text(json.dumps(self.base, indent=2))

    def tearDown(self):
        for p in (self.cache, self.man):
            if p.exists():
                p.unlink()
        if self.tmp.exists():
            self.tmp.rmdir()

    def test_a_matching_manifest_loads(self):
        C = a47.load_cache(self.cache, self.man)
        self.assertEqual(len(C), 1)

    def test_a_config_mismatch_is_refused_by_name(self):
        """The `--train-features-at-origin`-without-`--rebuild` case: the cache on disk is the
        joint one and the run asked for the strict one."""
        with self.assertRaises(ValueError) as e:
            a47.load_cache(self.cache, self.man, train_feats_at_origin=True)
        self.assertIn('train_features_at_origin', str(e.exception))

    def test_a_code_change_is_refused(self):
        man = dict(self.base)
        man['code'] = dict(man['code'], **{'final_pipeline.py': '0' * 32})
        self.man.write_text(json.dumps(man))
        with self.assertRaises(ValueError) as e:
            a47.load_cache(self.cache, self.man)
        self.assertIn('final_pipeline.py', str(e.exception))

    def test_a_constant_change_is_refused(self):
        man = dict(self.base)
        man['config'] = dict(man['config'], harm_shrink=0.123)
        self.man.write_text(json.dumps(man))
        with self.assertRaises(ValueError) as e:
            a47.load_cache(self.cache, self.man)
        self.assertIn('harm_shrink', str(e.exception))

    def test_a_swapped_pickle_is_refused(self):
        pd.read_pickle(self.cache).head(0).to_pickle(self.cache)
        with self.assertRaises(ValueError) as e:
            a47.load_cache(self.cache, self.man)
        self.assertIn('cache_md5', str(e.exception))

    def test_a_missing_manifest_is_refused(self):
        self.man.unlink()
        with self.assertRaises(FileNotFoundError):
            a47.load_cache(self.cache, self.man)


class ChainLabelIsolation(unittest.TestCase):
    """The whole chain, not one link of it.

    `tests/test_v21_evaluation.py` perturbs labels and checks `fit_increments` and the de-shrink
    factor. Neither is where session 26's defect was: the stack was. These run members, blend,
    time-of-day weights, harmonic bias, increments, factor and solve end to end, and compare the
    reconciled numbers."""

    @classmethod
    def setUpClass(cls):
        cls.g, cls.y = grid()
        cls.name, cls.hs, cls.he = smallest_block()

    def chain(self, y, scopes=('inner',)):
        feats = {}
        out = a47.build_block(self.g, y, self.name, self.hs, self.he,
                              feature_cache=feats, **CHEAP)
        P = a47.score_config(self.g, y, out, physics=True, deshrink=fp.INC_DESHRINK,
                             seeds=(fp.INC_SEED,), scopes=scopes, feature_cache=feats)
        return P.sort_values(['scope', 'fold', 'datetime']).reset_index(drop=True)

    def perturbed(self, after):
        rng = np.random.default_rng(23)
        y2 = self.y.copy()
        m = y2.index > after
        y2[m] = 40.0 + 30.0 * rng.random(int(m.sum()))
        return y2

    def test_labels_after_the_outer_origin_change_nothing_anywhere(self):
        a = self.chain(self.y, scopes=('inner', 'outer'))
        b = self.chain(self.perturbed(self.hs), scopes=('inner', 'outer'))
        np.testing.assert_array_equal(a.level.to_numpy(), b.level.to_numpy())
        np.testing.assert_array_equal(a.recon.to_numpy(), b.recon.to_numpy())

    def test_labels_after_the_last_inner_origin_change_no_inner_prediction(self):
        """The check that fails under the fold-number rule. Every inner origin here sits at or
        before the perturbation, so every inner stack, every inner increment fit and every
        inner solve must be blind to it -- under the old rule the last fold's stack was fitted
        on labels running six days past its origin, which is inside the perturbed range."""
        a = self.chain(self.y)
        last = pd.DatetimeIndex(a.origin).max()
        b = self.chain(self.perturbed(last))
        np.testing.assert_array_equal(a.level.to_numpy(), b.level.to_numpy())
        np.testing.assert_array_equal(a.recon.to_numpy(), b.recon.to_numpy())

    def test_the_perturbation_is_strong_enough_to_be_detected(self):
        """A no-op control for the two tests above: the same perturbation applied where the
        chain IS allowed to look must move the answer, or they prove nothing."""
        a = self.chain(self.y)
        early = pd.DatetimeIndex(a.origin).min() - pd.Timedelta(days=3)
        b = self.chain(self.perturbed(early))
        self.assertFalse(np.array_equal(a.recon.to_numpy(), b.recon.to_numpy()))


class Fallback(unittest.TestCase):
    def test_the_fallback_stack_is_the_equal_weighted_mean_and_nothing_else(self):
        rng = np.random.default_rng(31)
        V = pd.DataFrame({'ridge': 50 + rng.standard_normal(64),
                          'enet': 60 + rng.standard_normal(64),
                          'tod': rng.uniform(0, 24, 64)})
        np.testing.assert_allclose(a47.stack_fallback(V, ['ridge', 'enet']),
                                   V[['ridge', 'enet']].mean(axis=1).to_numpy())

    def test_fallback_folds_are_marked_and_not_scored(self):
        g, y = grid()
        name, hs, he = smallest_block()
        out = a47.build_block(g, y, name, hs, he, **CHEAP)
        inner = out.loc[out.scope == 'inner']
        fb = inner.groupby('fold').meta_fallback.first()
        self.assertTrue(fb.any(), 'B2 is the block that runs out of history; expected a fallback')
        for fold, is_fb in fb.items():
            d = inner.loc[inner.fold == fold]
            if is_fb:
                self.assertEqual(int(d.score.sum()), 0, fold)
            else:
                self.assertEqual(int(d.score.sum()), 96, fold)

    def test_scored_rows_are_the_two_day_tail_with_no_first_fold_exception(self):
        g, y = grid()
        name, hs, he = smallest_block()
        out = a47.build_block(g, y, name, hs, he, **CHEAP)
        inner = out.loc[(out.scope == 'inner') & out.score]
        for fold, d in inner.groupby('fold'):
            ve = pd.Timestamp(d.horizon_end.iloc[0])
            self.assertGreater(pd.DatetimeIndex(d.datetime).min(),
                               ve - pd.Timedelta(days=a47.SCORE_TAIL_DAYS))
            self.assertEqual(len(d), 96, fold)


if __name__ == '__main__':
    unittest.main()
