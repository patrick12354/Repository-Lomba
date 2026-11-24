"""Session 33, Task 3: what must be true of the level-shape arms before a number is believed.

The claim `an76` makes is narrow and mechanical: E1 and E2 differ from C0 in the columns handed
to `hbt` and in nothing else. These tests hold that claim to its parts.

* **Zero intervention.** Feed the arm the control's own `hbt` and the final reconciled prediction
  must be identical -- not close. That exercises the clip, the NNLS weights, the time-of-day
  bands, the harmonic bias and the sparse solve in one assertion.
* **Frozen meta.** The stack parameters come from `O_base`, the incumbent out-of-fold frame. A
  candidate that refits the blend on its own out-of-fold predictions is a different method and
  is not what this round evaluated.
* **The control reproduces.** `fit_hbt` on the incumbent matrix must land on the cached member
  column. If it does not, the training rows or the seeds are not the incumbent's and no
  comparison downstream means anything.
* **Increment isolation.** The new columns must never reach `fit_increments`, which pulls the
  whole feature frame into its design.

    .venv/Scripts/python.exe -m unittest discover -s tests -p test_v21_level_shape_contract.py
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
import an76_v21_level_shape as a76
import v21_local_shape as ls

_C = {}


def block():
    """B1: the cache rows, the incumbent meta frame and the block's own context."""
    if not _C:
        g = fp.load_grid()
        y = g[fp.TARGET]
        cache = a47.load_cache(a47.CACHE_S27, a47.MANIFEST_S27)
        name = 'B1_last15d'
        d = cache.loc[(cache.block == name) & (cache.scope == 'outer')].sort_values('datetime')
        O, V, _ = a76.base_frames(cache, name, list(fp.MODELS_L2))
        feats = {}
        ctx = a76.block_context(g, y, name, d, feats)
        V = V.copy()
        V['tod'] = ctx['F'].loc[ctx['idx'], 'tod'].to_numpy()
        _C.update(g=g, y=y, cache=cache, name=name, d=d, O=O, V=V, ctx=ctx,
                  models=list(fp.MODELS_L2))
    return _C


class MetaFrame(unittest.TestCase):
    def test_the_rebuilt_meta_frame_reproduces_the_cached_level_exactly(self):
        b = block()
        level = a47.stack_on(b['O'], b['V'], b['models'])
        np.testing.assert_allclose(level, b['d'].level.to_numpy(), rtol=0, atol=1e-9)

    def test_the_meta_frame_has_no_holes_and_stops_at_the_origin(self):
        b = block()
        self.assertTrue(b['O'].notna().to_numpy().all())
        self.assertLessEqual(b['O'].dt.max(), pd.Timestamp(b['ctx']['origin']))

    def test_time_of_day_recomputed_from_the_timestamp_matches_the_frame(self):
        b = block()
        got = a76.tod_of(b['ctx']['idx']).to_numpy()
        want = b['ctx']['F'].loc[b['ctx']['idx'], 'tod'].to_numpy()
        np.testing.assert_allclose(got, want, rtol=0, atol=1e-12)


class ZeroIntervention(unittest.TestCase):
    def test_substituting_the_control_member_changes_nothing(self):
        b = block()
        terms, idx = b['ctx']['terms'], b['ctx']['idx']
        level = a47.stack_on(b['O'], b['V'], b['models'])
        z0 = a47.solve(level, idx, terms)
        V2 = b['V'].copy()
        V2['hbt'] = np.clip(b['V']['hbt'].to_numpy(), 5, 100)
        z1 = a47.solve(a47.stack_on(b['O'], V2, b['models']), idx, terms)
        np.testing.assert_allclose(z1, z0, rtol=0, atol=1e-12)

    def test_moving_the_member_does_move_the_result(self):
        # The discriminating half: the test above would also pass if the substitution path were
        # dead code that never reached the solve.
        b = block()
        V2 = b['V'].copy()
        V2['hbt'] = np.clip(V2['hbt'].to_numpy() + 1.0, 5, 100)
        z0 = a47.solve(a47.stack_on(b['O'], b['V'], b['models']), b['ctx']['idx'],
                       b['ctx']['terms'])
        z1 = a47.solve(a47.stack_on(b['O'], V2, b['models']), b['ctx']['idx'],
                       b['ctx']['terms'])
        self.assertGreater(float(np.max(np.abs(z1 - z0))), 1e-3)


class ControlReproduction(unittest.TestCase):
    def test_the_refitted_control_hbt_is_the_cached_member(self):
        b = block()
        hbt = a76.fit_hbt(b['ctx']['F'], b['y'], b['ctx']['train'], b['ctx']['idx'])
        np.testing.assert_allclose(hbt, b['V']['hbt'].to_numpy(), rtol=0, atol=1e-9)

    def test_the_control_reproduces_the_frozen_v21_reconciliation(self):
        b = block()
        z = a47.solve(a47.stack_on(b['O'], b['V'], b['models']), b['ctx']['idx'],
                      b['ctx']['terms'])
        frozen = pd.read_pickle(ROOT / 'outputs/audit_v21_s27/preds_v21_increment.pkl')
        ref = frozen.loc[(frozen.block == b['name']) & (frozen.scope == 'outer')] \
            .sort_values('datetime')
        np.testing.assert_allclose(z, ref.recon.to_numpy(), rtol=0, atol=1e-9)

    def test_the_training_rows_stop_at_the_origin(self):
        b = block()
        train = b['ctx']['train']
        self.assertLessEqual(train.max(), pd.Timestamp(b['ctx']['origin']))
        self.assertTrue(b['y'].reindex(train).notna().all())
        self.assertGreater(len(train), 900)


class Design(unittest.TestCase):
    def test_the_arms_add_exactly_the_columns_they_claim(self):
        b = block()
        shapes = {}
        F = b['ctx']['F']
        e1 = a76.shape_block(b['g'], b['ctx']['horizon_end'], a76.FEATURES['E1'], shapes)
        e2 = a76.shape_block(b['g'], b['ctx']['horizon_end'], a76.FEATURES['E2'], shapes)
        self.assertIsNone(a76.shape_block(b['g'], b['ctx']['horizon_end'],
                                          a76.FEATURES['C0'], shapes))
        self.assertEqual(list(e1.columns), ls.shape_columns())
        self.assertEqual(list(e2.columns), ls.all_columns())
        self.assertEqual(a76.design(F, None).shape[1], F.shape[1])
        self.assertEqual(a76.design(F, e1).shape[1], F.shape[1] + 60)
        self.assertEqual(a76.design(F, e2).shape[1], F.shape[1] + 72)

    def test_the_new_columns_do_not_shadow_an_incumbent_one(self):
        b = block()
        F = b['ctx']['F']
        self.assertFalse(set(F.columns) & set(ls.all_columns()))

    def test_the_design_keeps_the_incumbent_columns_untouched(self):
        b = block()
        F = b['ctx']['F']
        e1 = a76.shape_block(b['g'], b['ctx']['horizon_end'], a76.FEATURES['E1'], {})
        X = a76.design(F, e1)
        pd.testing.assert_frame_equal(X[list(F.columns)], F)


class IncrementIsolation(unittest.TestCase):
    def test_the_increment_design_never_sees_a_shape_column(self):
        # `fp.increment_design` pulls whatever it is given through `INC_COLS`, and the terms are
        # built from F alone in `block_context`. This pins that the shape block cannot arrive
        # there by accident.
        b = block()
        F = b['ctx']['F']
        X = fp.increment_design(F, 1, fp.INC_COLS, False, False)
        self.assertFalse(any(c.startswith(('shape_', 'quality_')) for c in X.columns))

    def test_a_wide_frame_would_contaminate_the_increment_design(self):
        # `inc_design` builds `parts = [F, ...]` -- it carries the WHOLE feature frame, not just
        # `INC_COLS`. So the hazard the plan names is real: if the wide matrix ever reached
        # `fit_increments`, all 60 shape columns would land in the increment model and the arm
        # would no longer be isolated to `hbt`. This test exists to keep that fact visible, and
        # to fail loudly if someone later "simplifies" `block_context` to pass the design matrix.
        b = block()
        e1 = a76.shape_block(b['g'], b['ctx']['horizon_end'], a76.FEATURES['E1'], {})
        wide = a76.design(b['ctx']['F'], e1)
        narrow_cols = fp.increment_design(b['ctx']['F'], 4, fp.INC_COLS, False, False).columns
        wide_cols = fp.increment_design(wide, 4, fp.INC_COLS, False, False).columns
        self.assertEqual(len(wide_cols) - len(narrow_cols), 60)
        self.assertTrue(any(c.startswith('shape_') for c in wide_cols))
        self.assertFalse(any(c.startswith('shape_') for c in narrow_cols))

    def test_the_runner_builds_its_terms_from_the_incumbent_frame(self):
        # The guard that matters: `block_context` must hand `fit_increments` and
        # `increment_terms` the narrow frame. Reproducing its terms from F alone proves it.
        b = block()
        ctx = b['ctx']
        gh = b['g'].loc[b['g'].index <= ctx['horizon_end']]
        inc = fp.fit_increments(ctx['F'], b['y'].reindex(gh.index),
                                a47.train_mask_before(b['g'], gh, b['y'], ctx['origin']),
                                a76.SEEDS_INC, physics=False, deshrink=False)
        terms = a47.increment_terms(ctx['F'], ctx['idx'], inc, None, 0.0)
        self.assertEqual(a76.terms_digest(terms), a76.terms_digest(ctx['terms']))


class ArmConfiguration(unittest.TestCase):
    def test_the_seeds_and_learner_settings_are_the_incumbent_ones(self):
        self.assertEqual(a76.SEEDS_INC, a47.SEEDS_INC)
        self.assertEqual(len(fp.SEEDS_FIT), 5)
        self.assertEqual(fp.LGB_KW['objective'], 'huber')

    def test_the_increment_configuration_is_v21_not_an_extension(self):
        import inspect
        src = inspect.getsource(a76.block_context)
        self.assertIn('physics=False', src)
        self.assertIn('deshrink=False', src)
        self.assertNotIn('lags=True', src)

    def test_the_arm_table_is_the_frozen_three(self):
        self.assertEqual(a76.ARMS, ('C0', 'E1', 'E2'))
        self.assertEqual(a76.FEATURES['C0'], ())
        self.assertEqual(a76.FEATURES['E1'], ('shape_',))
        self.assertEqual(a76.FEATURES['E2'], ('shape_', 'quality_'))


class LabelIsolation(unittest.TestCase):
    def test_the_shape_block_handed_to_hbt_is_target_blind(self):
        b = block()
        e = a76.shape_block(b['g'], b['ctx']['horizon_end'], a76.FEATURES['E2'], {})
        blind = b['g'].copy()
        blind[fp.TARGET] = np.nan
        e2 = a76.shape_block(blind, b['ctx']['horizon_end'], a76.FEATURES['E2'], {})
        pd.testing.assert_frame_equal(e, e2)

    def test_the_shape_block_stops_at_the_block_horizon(self):
        b = block()
        he = pd.Timestamp(b['ctx']['horizon_end'])
        e = a76.shape_block(b['g'], he, a76.FEATURES['E2'], {})
        self.assertLessEqual(e.index.max(), he)
        self.assertTrue(e.index.equals(b['ctx']['F'].index))


if __name__ == '__main__':
    unittest.main()
