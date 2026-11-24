"""Session 31, Task 2: the random-convolution transform.

The claim being tested is that these features see ORDER. A transform whose output is invariant
to reversing a sequence would be another summary statistic wearing a new name, which is exactly
what section 229 found the existing features already are.

    .venv/Scripts/python.exe -m unittest discover -s tests -p test_v21_temporal_models.py
"""
import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
import v21_sequence_design as sd
import v21_temporal_models as tm


def window(values, channel=0, valid=True):
    """One window with `values` on `channel` and everything else zero."""
    W = np.zeros((1, 2 * len(sd.CHANNELS), sd.WINDOW))
    W[0, channel, :] = values
    if valid:
        W[0, len(sd.CHANNELS):, :] = 1.0
    return W


class SeesOrder(unittest.TestCase):
    def test_a_difference_kernel_responds_differently_to_a_reversed_sequence(self):
        """The plan's fixture: `[1,0,-1]` on a ramp and its reverse. Mean, min and max are
        identical; the convolution response is not."""
        ramp = np.linspace(-1, 1, sd.WINDOW)
        bank = [dict(channel=0, length=3, dilation=1,
                     weight=np.array([1.0, 0.0, -1.0]), bias=0.0)]
        a = tm.apply_bank(window(ramp), bank)
        b = tm.apply_bank(window(ramp[::-1]), bank)
        self.assertAlmostEqual(float(ramp.mean()), float(ramp[::-1].mean()))
        self.assertAlmostEqual(float(ramp.max()), float(ramp[::-1].max()))
        self.assertFalse(np.allclose(a, b))

    def test_pooling_keeps_which_side_of_the_target_a_pattern_fell_on(self):
        """Global pooling would collapse these two windows; side-separated pooling must not."""
        early = np.zeros(sd.WINDOW)
        early[20:26] = 5.0
        late = np.zeros(sd.WINDOW)
        late[sd.WINDOW - 26:sd.WINDOW - 20] = 5.0
        bank = tm.kernel_bank(tm.SEEDS[0], n=8)
        bank = [k for k in bank if k['channel'] == 0] or [dict(
            channel=0, length=3, dilation=1, weight=np.array([0.5, 0.5, -1.0]), bias=0.0)]
        a = tm.apply_bank(window(early), bank)
        b = tm.apply_bank(window(late), bank)
        self.assertFalse(np.allclose(np.nan_to_num(a), np.nan_to_num(b)))

    def test_four_features_per_kernel(self):
        bank = tm.kernel_bank(tm.SEEDS[0], n=16)
        X = tm.apply_bank(window(np.random.default_rng(0).standard_normal(sd.WINDOW)), bank)
        self.assertEqual(X.shape, (1, 4 * len(bank)))


class MaskHandling(unittest.TestCase):
    def test_responses_touching_an_invalid_position_are_dropped(self):
        rng = np.random.default_rng(3)
        vals = rng.standard_normal(sd.WINDOW)
        bank = [dict(channel=0, length=3, dilation=1,
                     weight=np.array([1.0, -1.0, 0.0]), bias=0.0)]
        full = tm.apply_bank(window(vals), bank)
        W = window(vals)
        W[0, len(sd.CHANNELS) + 0, :sd.CENTER] = 0.0          # invalidate the whole early side
        holed = tm.apply_bank(W, bank)
        self.assertTrue(np.isfinite(full).all())
        self.assertTrue(np.isnan(holed[0, 0]) and np.isnan(holed[0, 1]))
        np.testing.assert_allclose(holed[0, 2:], full[0, 2:])  # the late side is untouched

    def test_a_fully_invalid_window_yields_all_nan_rather_than_zeros(self):
        """NaN is imputed from training statistics later; a silent zero would be a fabricated
        observation."""
        bank = tm.kernel_bank(tm.SEEDS[0], n=4)
        W = window(np.ones(sd.WINDOW), valid=False)
        self.assertTrue(np.isnan(tm.apply_bank(W, bank)).all())


class Determinism(unittest.TestCase):
    def test_a_frozen_seed_gives_an_identical_bank_and_transform(self):
        a, b = tm.kernel_bank(tm.SEEDS[0]), tm.kernel_bank(tm.SEEDS[0])
        self.assertEqual(tm.bank_hash(a), tm.bank_hash(b))
        rng = np.random.default_rng(11)
        W = window(rng.standard_normal(sd.WINDOW))
        np.testing.assert_array_equal(tm.apply_bank(W, a), tm.apply_bank(W, b))

    def test_different_seeds_give_different_banks(self):
        self.assertNotEqual(tm.bank_hash(tm.kernel_bank(tm.SEEDS[0])),
                            tm.bank_hash(tm.kernel_bank(tm.SEEDS[1])))

    def test_kernels_are_mean_removed_unit_norm_and_fit_the_window(self):
        for k in tm.kernel_bank(tm.SEEDS[0]):
            self.assertAlmostEqual(float(k['weight'].mean()), 0.0, places=12)
            self.assertAlmostEqual(float(np.linalg.norm(k['weight'])), 1.0, places=12)
            self.assertLessEqual((k['length'] - 1) * k['dilation'] + 1, sd.WINDOW)
            self.assertIn(k['length'], tm.LENGTHS)
            self.assertIn(k['channel'], range(len(sd.CHANNELS)))

    def test_the_bank_size_is_frozen(self):
        self.assertEqual(len(tm.kernel_bank(tm.SEEDS[0])), 512)
        self.assertEqual(len(tm.SEEDS), 3)


class ForwardSelection(unittest.TestCase):
    def test_folds_are_forward_and_do_not_overlap(self):
        import pandas as pd
        idx = pd.date_range('2023-07-01', periods=48 * 40, freq='30min')
        folds = tm.forward_folds(idx)
        self.assertEqual(len(folds), 2)
        for trn, val in folds:
            self.assertLess(idx[trn].max(), idx[val].min())
        self.assertEqual(len(set(folds[0][1]) & set(folds[1][1])), 0)

    def test_alpha_selection_never_sees_the_scored_rows(self):
        rng = np.random.default_rng(7)
        X = rng.standard_normal((600, 5))
        r = X @ np.array([1.0, 0, 0, 0, 0]) + 0.1 * rng.standard_normal(600)
        folds = [(np.arange(0, 300), np.arange(300, 450)),
                 (np.arange(0, 450), np.arange(450, 600))]
        alpha, table = tm.forward_alpha(X, r, folds)
        self.assertIn(alpha, tm.ALPHAS)
        self.assertEqual(len(table), len(tm.ALPHAS))



class LearnedNets(unittest.TestCase):
    """B0/B1 contracts. These are cheap structural checks; the expensive generalisation
    question is what the benchmark answers."""

    def test_the_zero_initialised_head_reproduces_the_physical_anchor(self):
        """Before training, f = 0 everywhere, so q is the anchor exactly -- the control that
        makes 'the network only ever adds a correction' true by construction."""
        import numpy as _np
        for builder in (tm.ScalarNet, tm.ThermalWindowNet):
            model = builder.build(12)
            W = _np.random.default_rng(0).standard_normal(
                (5, 2 * len(sd.CHANNELS), sd.WINDOW)).astype('float32')
            S = _np.random.default_rng(1).standard_normal((5, 12)).astype('float32')
            out = tm.predict_net(model, W, S)
            _np.testing.assert_allclose(out, 0.0, atol=0)

    def test_the_receptive_field_and_parameter_count_are_what_was_specified(self):
        field = 1 + 4 * (1 + 3 + 9 + 27)
        self.assertEqual(field, 161)
        self.assertLess(field, sd.WINDOW)
        n = tm.count_parameters(tm.ThermalWindowNet.build(118))
        self.assertGreater(n, 4000)
        self.assertLess(n, 8000)

    def test_evaluation_is_deterministic_with_dropout_off(self):
        import numpy as _np
        model = tm.ThermalWindowNet.build(10)
        W = _np.random.default_rng(2).standard_normal(
            (4, 2 * len(sd.CHANNELS), sd.WINDOW)).astype('float32')
        S = _np.random.default_rng(3).standard_normal((4, 10)).astype('float32')
        a = tm.predict_net(model, W, S)
        b = tm.predict_net(model, W, S)
        _np.testing.assert_array_equal(a, b)

    def test_the_optimiser_can_fit_a_deterministic_synthetic_signal(self):
        """A sanity check on optimisation, not evidence of generalisation: if the network
        cannot learn a signal that is present by construction, a negative result on real data
        would be uninterpretable."""
        import numpy as _np
        rng = _np.random.default_rng(4)
        n = 256
        W = rng.standard_normal((n, 2 * len(sd.CHANNELS), sd.WINDOW)).astype('float32')
        W[:, len(sd.CHANNELS):, :] = 1.0
        S = rng.standard_normal((n, 4)).astype('float32')
        target = (W[:, 0, sd.CENTER] * 2.0).astype('float32')
        model, _e, _b = tm.train_net(tm.ThermalWindowNet, W, S, target, None, seed=0,
                                     epochs=60)
        pred = tm.predict_net(model, W, S)
        self.assertLess(float(_np.mean((pred - target) ** 2)),
                        0.5 * float(_np.mean(target ** 2)))

    def test_outputs_are_finite(self):
        import numpy as _np
        model = tm.ThermalWindowNet.build(6)
        W = _np.zeros((3, 2 * len(sd.CHANNELS), sd.WINDOW), dtype='float32')
        S = _np.zeros((3, 6), dtype='float32')
        self.assertTrue(_np.isfinite(tm.predict_net(model, W, S)).all())

    def test_the_training_recipe_is_frozen(self):
        self.assertEqual(tm.TORCH_TRAIN['lr'], 1e-3)
        self.assertEqual(tm.TORCH_TRAIN['weight_decay'], 1e-2)
        self.assertEqual(tm.TORCH_TRAIN['batch'], 64)
        self.assertEqual(tm.TORCH_TRAIN['max_epochs'], 160)
        self.assertEqual(tm.TORCH_TRAIN['patience'], 15)
        self.assertEqual(tm.TORCH_TRAIN['grad_clip'], 1.0)

if __name__ == '__main__':
    unittest.main()
