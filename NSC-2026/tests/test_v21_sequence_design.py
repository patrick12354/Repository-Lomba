"""Session 31, Task 1: the window contract.

A centred window is only legitimate here because future EXOGENOUS is genuinely available for a
forecast horizon. That makes the boundary between "allowed" and "leakage" narrow and worth
testing precisely: future sensors may move a window, future RH may not move anything, and
nothing beyond the forecast's own horizon end may be visible at all.

    .venv/Scripts/python.exe -m unittest discover -s tests -p test_v21_sequence_design.py
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

_G = {}


def grid():
    if not _G:
        g = fp.load_grid()
        _G['g'], _G['y'], _G['F'] = g, g[fp.TARGET], fp.make_features(g)
    return _G['g'], _G['y'], _G['F']


def fitted_scaler(F, idx):
    return sd.ChannelScaler().fit(F, idx)


class Geometry(unittest.TestCase):
    def test_the_window_is_193_points_centred_on_the_target(self):
        self.assertEqual(sd.WINDOW, 193)
        self.assertEqual(sd.CENTER, 96)
        self.assertEqual(sd.OFFSETS[sd.CENTER], 0)
        self.assertEqual(sd.OFFSETS[0], -96)
        self.assertEqual(sd.OFFSETS[-1], 96)
        self.assertEqual(len(sd.OFFSETS), sd.WINDOW)

    def test_the_cnn_receptive_field_fits_inside_the_window(self):
        """1 + 4*(1+3+9+27) = 161 points, 80 hours, inside the 96-hour span."""
        field = 1 + 4 * (1 + 3 + 9 + 27)
        self.assertEqual(field, 161)
        self.assertLessEqual(field, sd.WINDOW)

    def test_the_centre_channel_value_is_the_target_timestamps_own_reading(self):
        _, _, F = grid()
        idx = F.index[500:520]
        sc = fitted_scaler(F, F.index[:2000])
        W = sd.build_windows(F, idx, sc)
        for c, name in enumerate(sd.CHANNELS):
            want = (F.loc[idx, name].to_numpy() - sc.median_[c]) / sc.scale_[c]
            np.testing.assert_allclose(W[:, c, sd.CENTER], want, atol=1e-12)

    def test_offset_k_is_exactly_k_half_hours_of_clock_time(self):
        _, _, F = grid()
        idx = F.index[600:604]
        sc = fitted_scaler(F, F.index[:2000])
        W = sd.build_windows(F, idx, sc)
        for k in (0, 4, 48, 96, 192):
            off = sd.OFFSETS[k]
            want_t = idx + pd.Timedelta(minutes=30 * off)
            want = (F.loc[want_t, 'T'].to_numpy() - sc.median_[0]) / sc.scale_[0]
            np.testing.assert_allclose(W[:, 0, k], want, atol=1e-12)

    def test_a_hole_in_the_frame_shifts_nothing_and_is_flagged(self):
        """Dropping a row must produce an invalid slot at that CLOCK time, not slide every
        later reading one position earlier."""
        _, _, F = grid()
        idx = F.index[600:602]
        sc = fitted_scaler(F, F.index[:2000])
        base = sd.build_windows(F, idx, sc)
        gone = idx[0] - pd.Timedelta(minutes=30 * 10)
        holed = F.drop(gone)
        got = sd.build_windows(holed, idx, sc)
        k = sd.OFFSETS.index(-10)
        self.assertEqual(base[0, 0, k] == 0.0, False)
        self.assertEqual(got[0, 0, k], 0.0)                      # padded
        self.assertEqual(got[0, len(sd.CHANNELS), k], 0.0)       # and masked invalid
        others = [j for j in range(sd.WINDOW) if j != k]
        np.testing.assert_allclose(got[0, 0, others], base[0, 0, others], atol=1e-12)


class WhatMayBeRead(unittest.TestCase):
    def test_future_humidity_cannot_move_a_window(self):
        """No channel is the target or a lag of it, so corrupting every future RH label must
        leave the windows bit-identical."""
        g, y, F = grid()
        boundary = g.index[(g.is_test == 0).to_numpy()].max()
        origin = boundary - pd.Timedelta(days=15)
        rng = np.random.default_rng(31)
        g2 = g.copy()
        after = g2.index > origin
        g2.loc[after, fp.TARGET] = 40.0 + 30.0 * rng.random(int(after.sum()))
        F2 = fp.make_features(g2)
        idx = F.index[(F.index > origin)][:200]
        sc = fitted_scaler(F, F.index[F.index <= origin])
        np.testing.assert_array_equal(sd.build_windows(F, idx, sc),
                                      sd.build_windows(F2, idx, sc))

    def test_future_exogenous_beyond_the_horizon_is_invisible(self):
        """The frame is built at the forecast's own horizon end, so a sensor recorded after it
        cannot enter -- and the edge is padded and masked rather than reaching further."""
        g, _, _ = grid()
        end = g.index[(g.is_test == 0).to_numpy()].max() - pd.Timedelta(days=20)
        _, Fh = a47.frame_at(g, end)
        g2 = g.copy()
        g2.loc[g2.index > end, 'air_temperature'] += 20.0
        _, Fh2 = a47.frame_at(g2, end)
        idx = Fh.index[-6:]
        sc = fitted_scaler(Fh, Fh.index[:1500])
        np.testing.assert_array_equal(sd.build_windows(Fh, idx, sc),
                                      sd.build_windows(Fh2, idx, sc))

    def test_the_horizon_edge_is_padded_and_masked_not_borrowed(self):
        g, _, _ = grid()
        end = g.index[(g.is_test == 0).to_numpy()].max() - pd.Timedelta(days=20)
        _, Fh = a47.frame_at(g, end)
        sc = fitted_scaler(Fh, Fh.index[:1500])
        W = sd.build_windows(Fh, Fh.index[-1:], sc)
        nch = len(sd.CHANNELS)
        # everything strictly after the last grid point is invalid
        self.assertTrue(np.all(W[0, nch:, sd.CENTER + 1:] == 0.0))
        self.assertTrue(np.all(W[0, :nch, sd.CENTER + 1:] == 0.0))
        self.assertEqual(W[0, nch, sd.CENTER], 1.0)              # the target itself is valid

    def test_future_exogenous_inside_the_horizon_DOES_move_a_window(self):
        """The control that makes the previous two meaningful: a centred window is supposed to
        see the sensors around its target."""
        g, _, F = grid()
        idx = F.index[800:802]
        sc = fitted_scaler(F, F.index[:2000])
        base = sd.build_windows(F, idx, sc)
        g2 = g.copy()
        later = (g2.index > idx[-1]) & (g2.index <= idx[-1] + pd.Timedelta(hours=12))
        g2.loc[later, 'air_temperature'] += 5.0
        F2 = fp.make_features(g2)
        self.assertFalse(np.array_equal(base, sd.build_windows(F2, idx, sc)))


class AnchorAndTarget(unittest.TestCase):
    def test_zero_prediction_returns_the_physical_anchor_exactly(self):
        _, _, F = grid()
        idx = F.index[400:500]
        np.testing.assert_allclose(sd.invert_residual(np.zeros(len(idx)), F, idx),
                                   F.loc[idx, sd.ANCHOR_COL].to_numpy(), atol=0)

    def test_the_residual_transform_round_trips(self):
        _, y, F = grid()
        idx = F.index[(y.reindex(F.index).notna()).to_numpy()][:300]
        r = sd.residual_target(y, F).loc[idx].to_numpy()
        np.testing.assert_allclose(sd.invert_residual(r, F, idx), y.loc[idx].to_numpy(),
                                   atol=1e-9)

    def test_the_anchor_is_available_for_every_labelled_training_row(self):
        """The reason for using a deterministic anchor rather than the fitted stack: section
        220 had one usable calibration window on B2, this has every labelled row."""
        g, y, F = grid()
        boundary = g.index[(g.is_test == 0).to_numpy()].max()
        origin = boundary - pd.Timedelta(days=15)
        rows = sd.training_rows(g, F, y, origin)
        self.assertGreater(len(rows), 2000)
        r = sd.residual_target(y, F).loc[rows]
        self.assertTrue(r.notna().all())


class Normalisation(unittest.TestCase):
    def test_statistics_come_from_training_rows_only(self):
        _, _, F = grid()
        train = F.index[:1500]
        sc = fitted_scaler(F, train)
        np.testing.assert_allclose(sc.median_,
                                   F.loc[train, list(sd.CHANNELS)].median().to_numpy())
        # a later change must not move the fitted statistics
        F2 = F.copy()
        F2.loc[F2.index[2000:], 'T'] += 50.0
        sc2 = fitted_scaler(F2, train)
        np.testing.assert_allclose(sc.median_, sc2.median_)
        np.testing.assert_allclose(sc.scale_, sc2.scale_)

    def test_absolute_temperature_survives_normalisation(self):
        """A per-window standardisation would delete the level the anchor depends on. Two
        windows at different absolute temperatures must stay different."""
        _, _, F = grid()
        sc = fitted_scaler(F, F.index[:2000])
        W = sd.build_windows(F, F.index[[300, 1200, 2500]], sc)
        centres = W[:, 0, sd.CENTER]
        self.assertGreater(float(np.ptp(centres)), 0.1)

    def test_a_constant_channel_is_reported_rather_than_dividing_by_zero(self):
        _, _, F = grid()
        F2 = F.copy()
        F2['pressure'] = 1000.0
        sc = sd.ChannelScaler().fit(F2, F2.index[:1500])
        self.assertIn('pressure', sc.degenerate_)
        self.assertTrue(np.isfinite(sd.build_windows(F2, F2.index[500:505], sc)).all())

    def test_windows_are_finite_and_correctly_shaped(self):
        _, _, F = grid()
        idx = F.index[700:760]
        W = sd.build_windows(F, idx, fitted_scaler(F, F.index[:2000]))
        self.assertEqual(W.shape, (len(idx), 2 * len(sd.CHANNELS), sd.WINDOW))
        self.assertTrue(np.isfinite(W).all())
        self.assertTrue(set(np.unique(W[:, len(sd.CHANNELS):, :])) <= {0.0, 1.0})


class Blend(unittest.TestCase):
    def test_the_blend_weight_is_frozen_and_reduces_to_the_level(self):
        level = np.array([50.0, 60.0])
        q = np.array([70.0, 40.0])
        np.testing.assert_allclose(sd.blend_level(level, q),
                                   0.75 * level + 0.25 * q)
        np.testing.assert_allclose(sd.blend_level(level, level), level)


if __name__ == '__main__':
    unittest.main()
