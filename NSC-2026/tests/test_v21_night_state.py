"""Night-state boundaries, chronology, exogenous isolation and solve checks."""
import sys
import unittest
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
import final_pipeline as fp
import an47_v21_forward_benchmark as a47
try:
    import an61_v21_night_state as night
except ImportError:
    night = None


class NightStateTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(night, 'night-state implementation is missing')
        self.idx = pd.date_range('2023-07-01 12:00', periods=96, freq='30min')
        self.F = pd.DataFrame({'T': 20., 'co2': 400., 'pressure': 1000.}, index=self.idx)
        self.y = pd.Series(60., index=self.idx)
        self.labels = pd.Series(True, index=self.idx)

    def test_midnight_belongs_to_previous_evening(self):
        groups = night.complete_nights(self.idx)
        self.assertEqual(len(groups), 2)
        self.assertEqual(groups[0][0], pd.Timestamp('2023-07-01 18:00'))
        self.assertEqual(len(groups[0][1]), 24)
        self.assertIn(pd.Timestamp('2023-07-02 00:00'), groups[0][1])
        self.assertNotIn(pd.Timestamp('2023-07-02 06:00'), groups[0][1])

    def test_incomplete_nights_and_unlabelled_targets_excluded(self):
        cut = self.idx.delete(self.idx.get_loc('2023-07-02 01:00'))
        self.assertEqual(len(night.complete_nights(cut)), 1)
        labels = self.labels.copy()
        labels.loc['2023-07-02 01:00'] = False
        tab = night.training_nights(self.F, self.y, labels, self.idx.max())
        self.assertEqual(len(tab), 1)

    def test_origin_excludes_unfinished_night_and_future_targets(self):
        origin = pd.Timestamp('2023-07-03 05:30')
        a = night.training_nights(self.F, self.y, self.labels, origin)
        y = self.y.copy()
        y.loc[y.index > pd.Timestamp('2023-07-02 06:00')] = 999.
        b = night.training_nights(self.F, y, self.labels, origin)
        pd.testing.assert_frame_equal(a, b)
        self.assertEqual(len(a), 1)
        self.assertAlmostEqual(a.target.iloc[0], .6 * fp.es(20.))

    def test_normalized_sparse_night_solve_matches_dense(self):
        nights = night.night_features(self.F)
        pred = pd.Series(.6 * fp.es(20.), index=nights.index)
        M, target, mu = night.night_term(self.F, self.idx, pred)
        np.testing.assert_allclose(np.asarray(M.multiply(M).sum(axis=1)).ravel(), 1.)
        level = np.full(len(self.idx), 65.)
        dense = M.toarray()
        expected = np.linalg.solve(np.eye(len(level)) + mu * dense.T @ dense,
                                   level + mu * dense.T @ target)
        np.testing.assert_allclose(a47.solve(level, self.idx, [(M, target, mu)]), expected)

    def test_features_cannot_read_after_simulated_horizon(self):
        g = fp.load_grid().iloc[:480].copy()
        end = g.index[335]
        a = night.features_at(g, end)
        for col in fp.FAST + fp.SOIL + fp.DAILY + fp.CUMUL:
            g.loc[g.index > end, col] = 1e8
        b = night.features_at(g, end)
        pd.testing.assert_frame_equal(a, b)

    def test_gate_requires_both_baselines_and_two_chunks(self):
        rows = pd.DataFrame({'chunk': [0, 1, 2], 'target': [0., 0., 0.],
                             'ridge': [.1, .1, 3.], 'proxy': [1., 1., 1.],
                             'mean': [2., 2., 2.]})
        self.assertFalse(night.gate_decision(rows)['passed'])
        rows['ridge'] = .1
        self.assertTrue(night.gate_decision(rows)['passed'])

    def test_gate_rejects_two_winning_chunks_without_third_validation_chunk(self):
        rows = pd.DataFrame({'chunk': [0, 1], 'target': [0., 0.],
                             'ridge': [.1, .1], 'proxy': [1., 1.],
                             'mean': [2., 2.]})
        self.assertFalse(night.gate_decision(rows)['passed'])

    def test_gate_is_blind_to_outer_targets_and_future_exogenous(self):
        g = fp.load_grid().iloc[:2000].copy()
        origin = g.index[1700]
        first, rows = night.gate_origin(g, g[fp.TARGET], origin)
        g.loc[g.index > origin, fp.TARGET] = -999.
        for col in fp.FAST + fp.SOIL + fp.DAILY + fp.CUMUL:
            g.loc[g.index > origin, col] = 1e8
        second, changed = night.gate_origin(g, g[fp.TARGET], origin)
        self.assertEqual(first, second)
        pd.testing.assert_frame_equal(rows, changed)
        self.assertEqual(first['chunks'], 3)
        for fold in first['folds']:
            self.assertGreaterEqual(fold['train_nights'], 10)
            self.assertLessEqual(pd.Timestamp(fold['max_training_night_end']),
                                 pd.Timestamp(fold['origin']))
            self.assertLess(pd.Timestamp(fold['horizon_end']), origin)


if __name__ == '__main__':
    unittest.main()
