"""Session 38: the campaign's own contracts — registry, selection rule, and fail-closed gates.

A campaign of 27 configurations fails differently from a single frozen recipe: a label whose
payload has drifted, a selection rule applied after seeing the answer, or a parameter silently
dropped so two "different" trials are the same run. These tests pin each.

    .venv/Scripts/python.exe -m unittest discover -s tests -p test_v21_campaign_contract.py
"""
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
import final_pipeline as fp
import v21_campaign_registry as reg
import v21_campaign_models as cm
import v21_sensor_masking as sm
import an87_v21_mask_training_report as mr


class Registry(unittest.TestCase):
    def test_the_core_wave_is_27_configurations_in_six_families(self):
        m = reg.registry_manifest()
        self.assertEqual(m['n_core'], 27)
        self.assertEqual(m['counts'], dict(A=4, B=8, C=4, D=6, E=3, F=2))

    def test_every_trial_carries_its_full_parameter_payload(self):
        for t in reg.core_trials():
            self.assertTrue(t['params'], t['id'])
            self.assertIn(t['component'], ('hbt_view', 'hbt_params', 'history', 'inc_params',
                                           'joint_level', 'inference_avg'))

    def test_identity_is_the_payload_not_the_label(self):
        a = dict(id='X', family='B', component='hbt_params', params={'num_leaves': 7})
        b = dict(a, params={'num_leaves': 31})
        self.assertNotEqual(reg.config_digest(a), reg.config_digest(b))
        self.assertEqual(reg.config_digest(a), reg.config_digest(dict(a)))

    def test_the_three_masking_strengths_are_actually_different(self):
        p = {t['id']: t['params']['p'] for t in reg.core_trials() if t['family'] == 'A'}
        self.assertEqual(sorted({p['A01'], p['A02'], p['A03']}), [0.025, 0.05, 0.10])

    def test_retest_families_are_labelled_as_retests(self):
        kinds = {t['id']: t['kind'] for t in reg.core_trials()}
        self.assertTrue(all(kinds[i] == 'retest' for i in kinds if i[0] in ('B', 'D')))
        self.assertTrue(all(kinds[i] == 'novel' for i in kinds if i[0] in ('A', 'C', 'E', 'F')))

    def test_the_seed_families_are_fresh_and_frozen(self):
        self.assertEqual(reg.AUG_SEEDS[0], 2026090801)
        self.assertEqual(len(reg.AUG_SEEDS), len(fp.SEEDS_FIT))
        self.assertEqual(len(reg.VIEW_SEEDS), 9)
        self.assertEqual(reg.SCREEN_HBT_SEEDS, (0, 1))
        self.assertNotEqual(set(reg.AUG_SEEDS), set(sm.TRAIN_SEEDS))


class MaskingStrength(unittest.TestCase):
    """The bug this catches was real: `p` was dropped and A01/A02/A03 masked identically."""

    def test_the_strength_reaches_the_mask(self):
        g = fp.load_grid()
        end = g.index[(g.is_test == 0).to_numpy()].max()
        counts = []
        for p in (0.025, 0.05, 0.10):
            _o, a = sm.masked_frame(g.loc[g.index <= end], 2026090801, hi=end, p=p)
            counts.append(int(a.masked.sum()))
        self.assertTrue(counts[0] < counts[1] < counts[2], counts)

    def test_build_views_and_stress_frame_both_take_p(self):
        import inspect
        self.assertIn('p', inspect.signature(sm.build_views).parameters)
        self.assertIn('p', inspect.signature(sm.stress_frame).parameters)
        src = inspect.getsource(cm.view_frame)
        self.assertIn('p=p', src)


class SelectionRule(unittest.TestCase):
    def _row(self, tid, fam, d_pooled, worst, both=False, any_=None):
        return dict(id=tid, family=fam, d_pooled=d_pooled, d_worst_block=worst,
                    improves_both=both, improves_any=(both if any_ is None else any_))

    def test_configurations_improving_both_blocks_come_first(self):
        rows = [self._row('B01', 'B', -0.01, +0.05, both=False, any_=True),
                self._row('B02', 'B', -0.005, -0.001, both=True)]
        chosen, _sk = reg.select_for_confirmation(rows)
        self.assertEqual(chosen[0]['id'], 'B02')

    def test_at_most_two_per_family(self):
        rows = [self._row('B0%d' % i, 'B', -0.01 * i, -0.001, both=True) for i in range(1, 6)]
        chosen, _sk = reg.select_for_confirmation(rows)
        self.assertEqual(len(chosen), 2)

    def test_a_configuration_losing_both_blocks_badly_is_not_confirmed(self):
        rows = [self._row('B01', 'B', +0.5, +0.6, both=False, any_=False)]
        chosen, skipped = reg.select_for_confirmation(rows)
        self.assertEqual(chosen, [])
        self.assertIn('B', skipped)

    def test_a_worst_block_beyond_the_tolerance_is_excluded(self):
        rows = [self._row('C01', 'C', -0.01, +0.5, both=False, any_=True)]
        chosen, skipped = reg.select_for_confirmation(rows)
        self.assertEqual(chosen, [])
        self.assertEqual(reg.WORST_BLOCK_TOLERANCE, 0.10)

    def test_an_empty_family_does_not_stop_the_campaign(self):
        rows = [self._row('A01', 'A', -0.02, -0.01, both=True)]
        chosen, skipped = reg.select_for_confirmation(rows)
        self.assertEqual([r['id'] for r in chosen], ['A01'])
        self.assertEqual(set(skipped), set(reg.FAMILIES) - {'A'})


class FailClosed(unittest.TestCase):
    def test_the_mask_report_refuses_to_promote_without_its_control(self):
        # Session 38 repair: a missing D0 reference used to skip the check and promote.
        m = dict(arm='M1', promotable=True, breakthrough=False)
        verdict, chosen, why = mr.choose([m], [])
        self.assertEqual(verdict, 'keep_v21')
        self.assertIsNone(chosen)
        self.assertIn('missing', why)

    def test_with_the_control_present_the_decision_is_made_normally(self):
        m = dict(arm='M1', promotable=True, breakthrough=False)
        verdict, chosen, _w = mr.choose([m], [dict(arm='M1', d_pooled=-0.03)])
        self.assertEqual(chosen['arm'], 'M1')


class Adapters(unittest.TestCase):
    def test_the_increment_refit_matches_the_incumbent_selection(self):
        import an47_v21_forward_benchmark as a47
        g = fp.load_grid()
        y = g[fp.TARGET]
        name, hs, he = a47.blocks_of(g)[0]
        gh, F = a47.frame_at(g, he)
        mask = a47.train_mask_before(g, gh, y, hs)
        inc = cm.fit_increments_kw(F, y.reindex(gh.index), mask, a47.SEEDS_INC[:1])
        self.assertEqual(inc[('n_edges', 1)], 2211)
        self.assertEqual(inc[('n_edges', 4)], 2208)
        self.assertEqual(inc['cols'], fp.INC_COLS)
        self.assertFalse(inc['physics'])
        self.assertFalse(inc['lags'])

    def test_truncating_the_mask_restricts_both_endpoints(self):
        import an47_v21_forward_benchmark as a47
        g = fp.load_grid()
        y = g[fp.TARGET]
        name, hs, he = a47.blocks_of(g)[0]
        gh, F = a47.frame_at(g, he)
        mask = a47.train_mask_before(g, gh, y, hs)
        m2 = cm.truncate_mask(mask, hs, 21)
        inc = cm.fit_increments_kw(F, y.reindex(gh.index), m2, a47.SEEDS_INC[:1])
        self.assertLess(inc[('n_edges', 1)], 2211)
        self.assertGreater(inc[('n_edges', 1)], 200)

    def test_the_episode_choice_is_constant_within_an_episode(self):
        idx = pd.date_range('2023-07-01', periods=200, freq='30min')
        take = cm.episode_choice(idx, idx[0], 2026090801, hours=24)
        ep = np.floor((idx - idx[0]).total_seconds() / 3600.0 / 24).astype(int)
        for e in np.unique(ep):
            self.assertEqual(len(set(take[ep == e])), 1, e)

    def test_the_episode_choice_is_order_independent(self):
        idx = pd.date_range('2023-07-01', periods=200, freq='30min')
        a = cm.episode_choice(idx, idx[0], 7)
        b = cm.episode_choice(idx[::-1], idx[0], 7)
        np.testing.assert_array_equal(a, b[::-1])


if __name__ == '__main__':
    unittest.main()
