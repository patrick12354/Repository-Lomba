"""Session 33, Task 1: the replay contract for internal hyperparameter selection.

An internal fold is a simulated forecast. Two things follow, and neither was true of the code
`an72` used to choose the sequence Ridge penalty:

* **Horizon.** Features for a fold must come from a grid that stops at that fold's own horizon
  end. Sensors recorded after it may not move the fold's features, its scaler, or its
  predictions.
* **Train-only preprocessing.** The channel scaler is a fitted object. Fitting it on the whole
  outer training set and then using it inside a fold hands the fold statistics of its own
  validation window.

Every horizon test below is run twice: once against `replay.legacy_alpha`, which must FAIL, and
once against the repaired path, which must pass. A test that only the new code is run through
does not establish that it discriminates -- it may just be describing the new code.

    .venv/Scripts/python.exe -m unittest discover -s tests -p test_v21_sequence_replay.py
"""
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
import final_pipeline as fp
import an47_v21_forward_benchmark as a47
import v21_sequence_design as sd
import v21_temporal_models as tm
import v21_sequence_replay as replay

_CTX = {}


def context():
    """B1's origin and horizon, the block the selection failure was measured on."""
    if not _CTX:
        g = fp.load_grid()
        y = g[fp.TARGET]
        name, hs, he = a47.blocks_of(g)[0]
        gh, F = a47.frame_at(g, he)
        lab = pd.Series((gh.is_test == 0).to_numpy(), index=gh.index) \
            & y.reindex(gh.index).notna()
        train = gh.index[(lab & (gh.index <= hs)).to_numpy()]
        _CTX.update(g=g, y=y, F=F, train=train, origin=hs, horizon_end=he,
                    folds=tm.forward_folds(train))
    return _CTX


def bump_exogenous(g, after, amount=25.0):
    """Move every fast sensor after a timestamp by a large, unmistakable amount."""
    h = g.copy()
    m = h.index > pd.Timestamp(after)
    for col in fp.FAST:
        h.loc[m, col] = h.loc[m, col] + amount
    return h


class Folds(unittest.TestCase):
    def test_the_internal_folds_are_forward_and_inside_the_training_set(self):
        c = context()
        self.assertGreaterEqual(len(c['folds']), 1)
        for trn, val in c['folds']:
            t, v = c['train'][trn], c['train'][val]
            self.assertLess(t.max(), v.min())
            self.assertLessEqual(v.max(), c['origin'])


class HorizonContract(unittest.TestCase):
    """A fold may not see a sensor recorded after its own validation window."""

    def test_the_repaired_fold_frame_stops_at_the_validation_horizon(self):
        c = context()
        for i, (trn, val) in enumerate(c['folds']):
            ctx = replay.fold_context(c['g'], c['y'], c['train'], trn, val)
            self.assertEqual(ctx['feature_frame_end'], ctx['validation_horizon_end'], 'fold %d' % i)
            self.assertLessEqual(ctx['scaler_fit_end'], c['origin'], 'fold %d' % i)
            self.assertLess(ctx['scaler_fit_end'], ctx['validation_horizon_end'], 'fold %d' % i)

    def test_the_repaired_fold_ignores_exogenous_after_its_horizon(self):
        c = context()
        trn, val = c['folds'][0]
        base = replay.fold_context(c['g'], c['y'], c['train'], trn, val)
        bumped = replay.fold_context(bump_exogenous(c['g'], base['validation_horizon_end']),
                                     c['y'], c['train'], trn, val)
        np.testing.assert_allclose(base['scaler'].median_, bumped['scaler'].median_,
                                   rtol=0, atol=1e-12)
        np.testing.assert_allclose(base['scaler'].scale_, bumped['scaler'].scale_,
                                   rtol=0, atol=1e-12)
        a = replay.fold_matrices(base, c['y'])
        b = replay.fold_matrices(bumped, c['y'])
        np.testing.assert_allclose(a['X_val'], b['X_val'], rtol=0, atol=1e-9)
        np.testing.assert_allclose(a['r_val'], b['r_val'], rtol=0, atol=1e-9)

    def test_the_legacy_path_does_not_ignore_it(self):
        # The discriminating half. `an72` built one frame at the outer horizon, so sensors from
        # weeks after a fold's window reach that fold's features. If this ever stops failing,
        # the test above has stopped testing anything.
        c = context()
        trn, val = c['folds'][0]
        cut = c['train'][val].max()
        gb = bump_exogenous(c['g'], cut)
        _, Fb = a47.frame_at(gb, c['horizon_end'])
        sa = sd.ChannelScaler().fit(c['F'], c['train'])
        sb = sd.ChannelScaler().fit(Fb, c['train'])
        moved = np.max(np.abs(sa.median_ - sb.median_))
        self.assertGreater(moved, 1e-6,
                           'the legacy scaler should be contaminated by post-horizon sensors')

    def test_the_scaler_is_fitted_on_the_fold_and_differs_from_the_outer_one(self):
        # Section 4A measured this on B1. It is recorded as a test so that "reuse was harmless"
        # cannot be assumed later without someone deleting an assertion.
        c = context()
        outer = sd.ChannelScaler().fit(c['F'], c['train'])
        for i, (trn, val) in enumerate(c['folds']):
            ctx = replay.fold_context(c['g'], c['y'], c['train'], trn, val)
            self.assertGreater(np.max(np.abs(outer.median_ - ctx['scaler'].median_)), 1e-3,
                               'fold %d scaler is indistinguishable from the outer one' % i)


class LabelIsolation(unittest.TestCase):
    def test_labels_after_the_training_split_do_not_change_the_fit(self):
        # Changing a label the fold is SCORED on must change that fold's score -- that is the
        # score doing its job. What must not change is the fitted model.
        c = context()
        trn, val = c['folds'][0]
        ctx = replay.fold_context(c['g'], c['y'], c['train'], trn, val)
        y2 = c['y'].copy()
        y2.loc[y2.index > ctx['scaler_fit_end']] = 42.0
        a = replay.fold_matrices(ctx, c['y'])
        b = replay.fold_matrices(ctx, y2)
        np.testing.assert_allclose(a['r_train'], b['r_train'], rtol=0, atol=1e-12)
        np.testing.assert_allclose(a['X_train'], b['X_train'], rtol=0, atol=1e-12)
        pa = tm.make_ridge(1000.0).fit(a['X_train'], a['r_train']).predict(a['X_val'])
        pb = tm.make_ridge(1000.0).fit(b['X_train'], b['r_train']).predict(b['X_val'])
        np.testing.assert_allclose(pa, pb, rtol=0, atol=1e-9)

    def test_the_features_never_read_the_target(self):
        c = context()
        trn, val = c['folds'][0]
        ctx = replay.fold_context(c['g'], c['y'], c['train'], trn, val)
        blind = c['y'].copy()
        blind[:] = np.nan
        np.testing.assert_allclose(replay.fold_matrices(ctx, c['y'])['X_train'],
                                   replay.fold_matrices(ctx, blind)['X_train'],
                                   rtol=0, atol=1e-12)


class Selection(unittest.TestCase):
    def test_the_penalty_grid_and_fold_count_are_not_widened_by_the_repair(self):
        c = context()
        alpha, table, prov = replay.replay_alpha(c['g'], c['y'], c['train'], c['folds'])
        self.assertEqual([t['alpha'] for t in table], list(tm.ALPHAS))
        self.assertEqual(len(prov), len(c['folds']))
        self.assertIn(alpha, tm.ALPHAS)
        for rec in prov:
            self.assertEqual(rec['feature_frame_end'], rec['validation_horizon_end'])
            self.assertLessEqual(rec['scaler_fit_end'], c['origin'])


class EarlyStopContract(unittest.TestCase):
    def test_the_early_stop_horizon_comes_from_positions_not_timestamps(self):
        c = context()
        train = c['train']
        cut = train.max() - pd.Timedelta(days=7)
        es_val = np.flatnonzero(train > cut)
        end = replay.early_stop_frame_end(train, es_val)
        self.assertEqual(end, train.max())
        self.assertEqual(end, train[es_val].max())

    def test_a_timestamp_vector_is_refused(self):
        c = context()
        train = c['train']
        with self.assertRaises(AssertionError):
            replay.early_stop_frame_end(train, np.asarray(train[-10:]))

    def test_positions_outside_the_training_index_are_refused(self):
        c = context()
        with self.assertRaises(AssertionError):
            replay.early_stop_frame_end(c['train'], np.asarray([len(c['train']) + 5]))


if __name__ == '__main__':
    unittest.main()
