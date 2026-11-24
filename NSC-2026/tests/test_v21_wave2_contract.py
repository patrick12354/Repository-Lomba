"""Session 40: the wave the session-38 campaign registered before it saw its own answer.

`outputs/campaign_v21_s38/next_wave.md` says: "Where does the tree-count curve stop? Register
1400/1800/2400 and a learning-rate pairing before running." It also says what NOT to do -- do not
add tree counts beyond the registry once a result is in, and do not lower the bar so B04 fits
under it.

These tests pin the wave to that written text. The point of a pre-registered wave is that the
grid cannot grow after the answer arrives, so the grid has to be checkable.

    .venv/Scripts/python.exe -m unittest discover -s tests -p test_v21_wave2_contract.py
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
import final_pipeline as fp
import v21_campaign_registry as reg


class Wave2(unittest.TestCase):
    def test_the_wave_is_the_three_registered_tree_counts_plus_one_pairing(self):
        T = reg.wave2_trials()
        self.assertEqual([t['id'] for t in T], ['J01', 'J02', 'J03', 'J04'])
        self.assertEqual([t['params'].get('n_estimators') for t in T],
                         [1400, 1800, 2400, 2700])
        self.assertTrue(all(t['family'] == 'J' and t['component'] == 'hbt_params' for t in T))

    def test_the_anchor_is_labelled_a_retest_not_a_discovery(self):
        """J01 is B04's 1400 re-run inside this wave so the curve has a common-seed anchor. It
        is not a new finding and must not be labelled as one -- the same rule family B carried
        in session 38."""
        j01 = reg.by_id(reg.wave2_trials())['J01']
        self.assertEqual(j01['kind'], 'retest')
        self.assertEqual(j01['params'], {'n_estimators': 1400})

    def test_the_learning_rate_pairing_holds_capacity_at_the_incumbent(self):
        """J04 is the control that separates "more trees" from "more capacity".

        Its `n_estimators x learning_rate` must equal the incumbent's, so it has three times the
        trees at the SAME total shrinkage. If J04 lands on the incumbent the gain is capacity; if
        it lands on the tree-count curve the gain is step size. A pairing that does not match
        capacity answers neither question, so the equality is pinned here rather than trusted.
        """
        j04 = reg.by_id(reg.wave2_trials())['J04']
        incumbent = fp.LGB_KW['n_estimators'] * fp.LGB_KW['learning_rate']
        paired = j04['params']['n_estimators'] * j04['params']['learning_rate']
        self.assertAlmostEqual(paired, incumbent, places=9)
        self.assertGreater(j04['params']['n_estimators'], fp.LGB_KW['n_estimators'])

    def test_wave2_ids_do_not_collide_with_the_core_wave_or_the_refinements(self):
        earlier = set(reg.by_id(reg.core_trials() + reg.refine_trials()))
        self.assertFalse(earlier & {t['id'] for t in reg.wave2_trials()})

    def test_identity_is_the_payload_so_a_relabelled_point_is_the_same_trial(self):
        T = reg.by_id(reg.wave2_trials())
        clone = dict(T['J02'], id='J99')
        self.assertNotEqual(reg.config_digest(T['J02']), reg.config_digest(clone),
                            'the digest must include the id, or resume cannot detect a swap')
        same = dict(T['J02'])
        self.assertEqual(reg.config_digest(T['J02']), reg.config_digest(same))

    def test_the_core_wave_is_untouched(self):
        """Adding a wave must not disturb the 27 the session-38 manifest describes."""
        self.assertEqual(reg.registry_manifest()['n_core'], 27)


class RunnerCanResolveTheWave(unittest.TestCase):
    """`an89` looks every requested id up in one table and refuses ids it cannot find. If the
    wave is registered but not in that table, `--ids J02` fails at the lookup rather than
    running -- so the table, not just the registry, is what has to contain family J."""

    def test_all_trials_is_the_union_the_runner_resolves_against(self):
        ids = set(reg.by_id(reg.all_trials()))
        self.assertTrue({'J01', 'J02', 'J03', 'J04'} <= ids)
        self.assertTrue({'B04', 'I01'} <= ids, 'the earlier waves must still resolve')

    def test_the_runner_resolves_against_all_trials(self):
        source = (ROOT / 'src' / 'an89_v21_campaign_run.py').read_text(encoding='utf-8')
        self.assertTrue('reg.all_trials()' in source,
                        'an89 must build its lookup from reg.all_trials(), or family J is '
                        'registered but unrunnable')


if __name__ == '__main__':
    unittest.main()
