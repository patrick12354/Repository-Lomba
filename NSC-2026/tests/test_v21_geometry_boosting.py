"""Session 34, Task 2: the two-booster plumbing must change the objective and nothing else.

The geometry arms are only interpretable if everything except the gradient is the incumbent's:
the same rows, the same feature matrix in the same order, the same targets, the same learner
parameters, the same seeds, the same number of trees. These tests pin each of those, plus the
numerical guards the custom objective needs.

    .venv/Scripts/python.exe -m unittest discover -s tests -p test_v21_geometry_boosting.py
"""
import sys
import unittest
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import lightgbm as lgb

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
import final_pipeline as fp
import an47_v21_forward_benchmark as a47
import v21_increment_geometry as ig
import v21_geometry_boosting as gb

warnings.filterwarnings('ignore')
_C = {}


def ctx():
    """B1's frame, mask and increment training parts."""
    if not _C:
        g = fp.load_grid()
        y = g[fp.TARGET]
        name, hs, he = a47.blocks_of(g)[0]
        gh, F = a47.frame_at(g, he)
        mask = a47.train_mask_before(g, gh, y, hs)
        _C.update(g=g, y=y, F=F, mask=mask, origin=hs, horizon_end=he, name=name,
                  parts=gb.increment_targets(F, y, mask),
                  index=F.index[mask.reindex(F.index, fill_value=False).to_numpy()])
    return _C


def small_geometry():
    c = ctx()
    return ig.build_geometry(c['index'], edges={h: c['parts'][h]['rows'] for h, _ in fp.INC_SPEC})


class ParameterMapping(unittest.TestCase):
    def test_n_estimators_becomes_a_round_count_not_a_parameter(self):
        p = gb.native_params(1)
        self.assertNotIn('n_estimators', p)
        self.assertEqual(gb.N_ROUNDS, fp.INC_KW['n_estimators'])
        self.assertEqual(gb.N_ROUNDS, 500)

    def test_every_incumbent_parameter_is_mapped_deliberately(self):
        p = gb.native_params(7)
        self.assertEqual(p['learning_rate'], fp.INC_KW['learning_rate'])
        self.assertEqual(p['num_leaves'], fp.INC_KW['num_leaves'])
        self.assertEqual(p['min_data_in_leaf'], fp.INC_KW['min_child_samples'])
        self.assertEqual(p['lambda_l2'], fp.INC_KW['reg_lambda'])
        self.assertEqual(p['feature_fraction'], fp.INC_KW['colsample_bytree'])
        self.assertEqual(p['seed'], 7)

    def test_an_unknown_incumbent_parameter_is_refused_rather_than_dropped(self):
        with self.assertRaises(KeyError):
            gb.native_params(1, dict(fp.INC_KW, some_new_knob=3))


class TrainingSetParity(unittest.TestCase):
    """The rows, columns and targets must be `fit_increments`' own."""

    def test_the_edges_match_the_incumbent_mask_exactly(self):
        c = ctx()
        want = ig.effective_edges(c['F'], c['y'], c['mask'])
        for h, _lam in fp.INC_SPEC:
            self.assertTrue(c['parts'][h]['rows'].equals(want[h]), h)

    def test_the_feature_matrix_is_the_incumbent_design_in_order(self):
        c = ctx()
        for h, _lam in fp.INC_SPEC:
            X = fp.increment_design(c['F'], h, fp.INC_COLS, False, False)
            got = c['parts'][h]['X']
            self.assertEqual(list(got.columns), list(X.columns))
            pd.testing.assert_frame_equal(got, X.loc[got.index])
            self.assertFalse(any(str(col).startswith(('shape_', 'quality_'))
                                 for col in got.columns))

    def test_the_target_is_the_h_step_difference(self):
        c = ctx()
        for h, _lam in fp.INC_SPEC:
            rows = c['parts'][h]['rows']
            want = (c['y'] - c['y'].shift(h)).reindex(rows).to_numpy()
            np.testing.assert_allclose(c['parts'][h]['t'], want, rtol=0, atol=0)

    def test_the_target_equals_the_operator_applied_to_the_labels(self):
        c = ctx()
        G = small_geometry()
        yv = c['y'].reindex(c['index']).to_numpy()
        for h, _lam in fp.INC_SPEC:
            np.testing.assert_allclose(G.D[h] @ yv, c['parts'][h]['t'], rtol=0, atol=1e-12)

    def test_the_design_digest_moves_when_a_row_is_dropped(self):
        c = ctx()
        a = gb.design_digest(c['parts'])
        cut = {h: dict(d, t=d['t'][:-1], rows=d['rows'][:-1], X=d['X'].iloc[:-1])
               for h, d in c['parts'].items()}
        self.assertNotEqual(a, gb.design_digest(cut))


class Schedule(unittest.TestCase):
    def test_every_horizon_gets_exactly_the_requested_number_of_trees(self):
        c = ctx()
        out = gb.fit_geometry_increments(c['F'], c['y'], c['mask'], (11,), 'l2_control',
                                         rounds=12)
        for h, _lam in fp.INC_SPEC:
            self.assertEqual(out[h][0].booster.num_trees(), 12, h)
        for rec in out['records']:
            self.assertEqual(rec['rounds'], 12)
            self.assertEqual(rec['trees'], 12)

    def test_one_model_per_seed_per_horizon(self):
        c = ctx()
        seeds = (3, 4)
        out = gb.fit_geometry_increments(c['F'], c['y'], c['mask'], seeds, 'l2_control', rounds=4)
        for h, _lam in fp.INC_SPEC:
            self.assertEqual(len(out[h]), len(seeds))
        self.assertEqual(len(out['records']), len(seeds) * len(fp.INC_SPEC))

    def test_the_result_has_the_shape_increment_terms_reads(self):
        c = ctx()
        out = gb.fit_geometry_increments(c['F'], c['y'], c['mask'], (5,), 'l2_control', rounds=3)
        self.assertEqual(out.get('cols'), fp.INC_COLS)
        self.assertFalse(out.get('physics'))
        self.assertFalse(out.get('lags'))
        idx = pd.DatetimeIndex(c['index'][-200:])
        terms = a47.increment_terms(c['F'], idx, out, None, 0.0)
        self.assertEqual(len(terms), len(fp.INC_SPEC))

    def test_a_geometry_whose_edges_disagree_with_the_rows_is_refused(self):
        c = ctx()
        bad = ig.build_geometry(c['index'][:-50])
        with self.assertRaises(AssertionError):
            gb.fit_geometry_increments(c['F'], c['y'], c['mask'], (1,), 'coupled',
                                       geometry=bad, rounds=2)


class OffsetSemantics(unittest.TestCase):
    def test_the_offset_is_the_training_target_mean(self):
        c = ctx()
        out = gb.fit_geometry_increments(c['F'], c['y'], c['mask'], (2,), 'l2_control', rounds=2)
        for h, _lam in fp.INC_SPEC:
            self.assertAlmostEqual(out[h][0].offset, float(np.mean(c['parts'][h]['t'])),
                                   places=12)

    def test_dropping_the_offset_changes_the_prediction(self):
        # If the offset were silently zero the model would spend its first trees relearning the
        # mean, and nothing else in the pipeline would notice.
        c = ctx()
        out = gb.fit_geometry_increments(c['F'], c['y'], c['mask'], (2,), 'l2_control', rounds=2)
        m = out[1][0]
        X = c['parts'][1]['X'].iloc[:50]
        raw = m.booster.predict(X, raw_score=True)
        np.testing.assert_allclose(m.predict(X) - raw, m.offset, rtol=0, atol=1e-12)
        self.assertNotAlmostEqual(m.offset, 0.0, places=6)

    def test_serialisation_round_trip_keeps_the_offset_and_the_prediction(self):
        c = ctx()
        out = gb.fit_geometry_increments(c['F'], c['y'], c['mask'], (2,), 'l2_control', rounds=3)
        X = c['parts'][4]['X'].iloc[:100]
        m = out[4][0]
        back = gb._SeedModel.from_dict(m.to_dict())
        self.assertEqual(back.offset, m.offset)
        self.assertEqual(back.columns, m.columns)
        np.testing.assert_allclose(back.predict(X), m.predict(X), rtol=0, atol=1e-12)


class Numerics(unittest.TestCase):
    def test_the_geometry_arms_train_with_finite_gradients_and_positive_hessians(self):
        c = ctx()
        G = small_geometry()
        for mode in ('separate', 'coupled'):
            out = gb.fit_geometry_increments(c['F'], c['y'], c['mask'], (1,), mode,
                                             geometry=G, rounds=4)
            for rec in out['records']:
                self.assertTrue(np.isfinite(rec['rmse']))
                self.assertTrue(np.isfinite(rec['geometry_loss']))
                self.assertGreaterEqual(rec['geometry_loss'], 0.0)
                self.assertTrue(np.isfinite(rec['Br_mse']))

    def test_the_hessian_is_strictly_positive_everywhere(self):
        self.assertTrue((small_geometry().hess() > 0).all())

    def test_the_two_arms_produce_different_models(self):
        c = ctx()
        G = small_geometry()
        a = gb.fit_geometry_increments(c['F'], c['y'], c['mask'], (1,), 'separate',
                                       geometry=G, rounds=6)
        b = gb.fit_geometry_increments(c['F'], c['y'], c['mask'], (1,), 'coupled',
                                       geometry=G, rounds=6)
        X = c['parts'][1]['X'].iloc[:200]
        self.assertGreater(float(np.max(np.abs(a[1][0].predict(X) - b[1][0].predict(X)))), 1e-9)

    def test_an_unknown_mode_is_refused(self):
        c = ctx()
        with self.assertRaises(AssertionError):
            gb.fit_geometry_increments(c['F'], c['y'], c['mask'], (1,), 'nonsense', rounds=1)


class L2PlumbingGap(unittest.TestCase):
    """The identified, measured gap between the two L2 paths -- see the module docstring."""

    def test_feature_fraction_is_what_separates_the_two_l2_paths(self):
        # At feature_fraction 1.0 the custom-objective path reproduces the built-in one exactly.
        # This is the evidence that the gap is a different feature draw, not a wrong gradient.
        c = ctx()
        d = c['parts'][1]
        X, t = d['X'], d['t']
        seed = 20260905
        outs = []
        for use_fobj in (True, False):
            prm = dict(gb.native_params(seed))
            prm['feature_fraction'] = 1.0
            if not use_fobj:
                prm['objective'] = 'regression'
                prm['boost_from_average'] = False
            ds = lgb.Dataset(X, label=t, free_raw_data=False).construct()
            b = lgb.Booster(params=prm, train_set=ds)
            for _ in range(3):
                if use_fobj:
                    b.update(fobj=lambda pr, _dd: (np.asarray(pr, float) - t, np.ones(len(t))))
                else:
                    b.update()
            outs.append(b.predict(X, raw_score=True))
        self.assertLess(float(np.max(np.abs(outs[0] - outs[1]))), 1e-7)

    def test_the_shipped_feature_fraction_is_still_zero_point_eight(self):
        # The repair for the gap was NOT to change the incumbent's parameter.
        self.assertEqual(fp.INC_KW['colsample_bytree'], 0.8)
        self.assertEqual(gb.native_params(1)['feature_fraction'], 0.8)


if __name__ == '__main__':
    unittest.main()
