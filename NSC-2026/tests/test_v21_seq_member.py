"""Session 39: the sequence model as a blend member.

Section 229 built `q` -- a Ridge over random convolutions of exogenous windows -- and blended
it into the finished level at a frozen 0.25. Section 234 then chose that weight per outer
origin from 384-864 calibration rows and it picked 0.45 on B1 where the truth is 0.00.

This module puts the same prediction somewhere else: as a column in the out-of-fold frame the
NNLS blend already fits on. The weight then comes from the whole OOF frame, is constrained
non-negative, and is shrunk twice -- toward equal weighting and, per time-of-day band, toward
the global vector. None of that machinery was available to section 234's bespoke search.

The tests here are about the CONTRACT, not the score: the member must never read a label from
the window it predicts, must be reproducible, and must leave every earlier submission
byte-identical when the flag is off.

    .venv/Scripts/python.exe -m unittest discover -s tests -p test_v21_seq_member.py
"""
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
import final_pipeline as fp
import v21_seq_member as sm


# A deliberately small configuration: enough kernels for the ridge to be non-degenerate, few
# enough that the whole file runs in a normal test session.
FAST = dict(n_kernels=24, seeds=(20260906,), alphas=(1000.0,))

_CACHE = {}


def frame():
    """The real grid, one 30-day training stretch and the 3 days immediately after it."""
    if 'f' not in _CACHE:
        g = fp.load_grid()
        F = fp.make_features(g)
        y = g[fp.TARGET]
        lab = F.index[(g.is_test == 0).values & y.notna().values]
        t0 = lab[0]
        train = lab[(lab > t0 + pd.Timedelta(days=14)) & (lab <= t0 + pd.Timedelta(days=44))]
        pred = lab[(lab > t0 + pd.Timedelta(days=44)) & (lab <= t0 + pd.Timedelta(days=47))]
        _CACHE['f'] = (F, y, train, pred)
    return _CACHE['f']


class Leakage(unittest.TestCase):
    def test_prediction_ignores_labels_inside_the_prediction_window(self):
        """The one guard the whole log is built on: destroying the labels the member is asked
        to predict must not move the prediction by a single bit.

        This discriminates. A version that fitted on train+pred, or that let the anchor read
        RH, would move here -- the replacement below is not a small perturbation, it is a
        different humidity series.
        """
        F, y, train, pred = frame()
        a = sm.seq_predict(F, y, train, pred, **FAST)

        poisoned = y.copy()
        poisoned.loc[pred] = 100.0 - poisoned.loc[pred]
        b = sm.seq_predict(F, poisoned, train, pred, **FAST)

        self.assertTrue(np.array_equal(a, b),
                        'the sequence member read a label from its prediction window')


class MemberFrame(unittest.TestCase):
    """`member_preds_seq` adds a column and changes nothing else.

    The arm is only interpretable if the five incumbent members are the SAME numbers they would
    have been without it -- otherwise a delta could come from anywhere. Delegation makes that
    true by construction, and this test is what proves the delegation is real.
    """

    def test_incumbent_members_are_bit_identical_and_seq_is_appended(self):
        import an47_v21_forward_benchmark as a47
        import an91_v21_seq_member_arm as arm

        F, y, train, pred = frame()
        models = ['hbt', arm.SEQ]

        base = a47.member_preds(F, F, y, train, pred, ['hbt'], (0,))
        both = arm.member_preds_seq(F, F, y, train, pred, models, (0,), seq_kw=FAST)

        self.assertEqual(list(both.columns), models, 'column order must follow `models`')
        self.assertTrue(np.array_equal(base['hbt'].to_numpy(), both['hbt'].to_numpy()),
                        'adding the sequence member moved an incumbent member')
        self.assertTrue(np.isfinite(both[arm.SEQ].to_numpy()).all())


class CachedControl(unittest.TestCase):
    """The arm skips refitting the incumbent stack and re-stacks the session-27 cache's stored
    member columns instead. That is only legitimate if it reproduces the banked level EXACTLY.

    This pins an invariant that was measured before the shortcut was taken, not one the design
    assumed: max |rebuilt - cached| is 0.0 on all three blocks. If a member list, a shrinkage
    constant or the stack function ever moves, the arm's control stops being the incumbent and
    this fails.
    """

    def test_restacking_cached_members_reproduces_the_banked_level_bit_for_bit(self):
        import pickle
        import an36_increment_production as a36
        import an91_v21_seq_member_arm as arm

        with open(ROOT / 'outputs/audit_v21_s27/forward_predictions.pkl', 'rb') as fh:
            cache = pickle.load(fh)
        models = list(fp.MODELS_L2)
        seen = 0
        for name, blk in cache.groupby('block'):
            O, V = arm.frames_from_cache(blk, models)
            rebuilt = a36.stack(O, V, models, fp.BLEND_SHRINK)
            self.assertEqual(float(np.max(np.abs(rebuilt - V.level.to_numpy()))), 0.0,
                             '%s: the cached control is not the banked level' % name)
            seen += 1
        self.assertEqual(seen, 3, 'expected the three 15-day blocks')


def synthetic(deltas, arm='seq'):
    """A prediction frame whose per-block RMSE delta is exactly `deltas[block]`.

    `y` is zero, the control errs by a constant 1.0 and the candidate by a constant
    `1 + delta`, so each block's RMSE delta is the number asked for and the gate is being
    tested rather than the arithmetic that feeds it.
    """
    out = []
    for block, d in deltas.items():
        n = 720
        out.append(pd.DataFrame(dict(
            block=block, arm=arm, datetime=pd.date_range('2023-08-01', periods=n, freq='30min'),
            y=np.zeros(n), z_ctrl=np.ones(n), z_cand=np.full(n, 1.0 + d))))
    return pd.concat(out, ignore_index=True)


class Gate(unittest.TestCase):
    """The bar was frozen in `an91`'s docstring before the arm ran. These pin it in code so it
    cannot drift once a number is on the screen."""

    def setUp(self):
        import an91_v21_seq_member_arm as arm
        self.gate = arm.gate

    def test_a_population_this_run_cannot_measure_fails_closed(self):
        """`d_pooled7` needs the 7-day H blocks, which the session-27 cache does not carry.

        A gate that silently treats an absent condition as satisfied is the defect section 264
        found in `an87.choose`. Missing must mean not promotable, and the reason must say so.
        """
        r = self.gate(synthetic({'B1_last15d': -0.05, 'B2_prev15d': -0.05, 'B3_shift7d': -0.05}))
        self.assertFalse(r['promotable'])
        self.assertIn('pooled7', ' '.join(r['unevaluated']))

    def test_b1_may_worsen_to_the_registered_tolerance_but_not_past_it(self):
        inside = self.gate(synthetic({'B1_last15d': +0.09, 'B2_prev15d': -0.10,
                                      'B3_shift7d': -0.10}))
        outside = self.gate(synthetic({'B1_last15d': +0.11, 'B2_prev15d': -0.10,
                                       'B3_shift7d': -0.10}))
        self.assertTrue(inside['bar_b1'])
        self.assertFalse(outside['bar_b1'])

    def test_b2_was_not_loosened(self):
        """Only B1's tolerance was registered. B2 keeps the standing rule."""
        r = self.gate(synthetic({'B1_last15d': -0.10, 'B2_prev15d': +0.01,
                                 'B3_shift7d': -0.10}))
        self.assertFalse(r['bar_b2'])


if __name__ == '__main__':
    unittest.main()
