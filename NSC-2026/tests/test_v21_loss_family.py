"""Session 45: the loss of the dominant member, never swept in forty-four sessions.

`hbt` carries the largest NNLS weight in every block and it is fitted with `huber, alpha=2.0` on a
target whose standard deviation is 18 %RH. Huber is linear beyond alpha, so every residual past
2 %RH contributes a *constant* gradient. §300 measured where the error now lives: the wettest
tercile has bias −3.498 and carries **46.4 %** of SSE. Those are precisely the rows the loss refuses
to take a full gradient from.

§98 noticed the shape of this — "every tree in the blend uses a huber loss ... both deliberately
under-weight large residuals, which is exactly where §35's under-dispersion lives" — and responded
by adding ONE plain-L2 member, which NNLS then pinned to the 0.042 floor because its residuals
correlate 0.950 with `hbt`. The dominant member's own loss was left at 2.0 and has never been
re-swept, on any harness, in any session.

Family L sweeps it. `L05` is plain L2, the extreme point, and it needs `alpha` removed rather than
ignored — `fp.predict('l2', ...)` pops it for exactly this reason.

    .venv/Scripts/python.exe -m unittest discover -s tests -p test_v21_loss_family.py
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
import final_pipeline as fp
import v21_campaign_registry as reg


class Family(unittest.TestCase):
    def test_the_sweep_brackets_the_incumbent_on_both_sides(self):
        T = reg.wave4_trials()
        self.assertEqual([t['id'] for t in T], ['L01', 'L02', 'L03', 'L04', 'L05'])
        alphas = [t['params'].get('alpha') for t in T[:4]]
        self.assertEqual(alphas, [1.0, 3.0, 4.0, 6.0])
        self.assertLess(min(a for a in alphas), fp.LGB_KW['alpha'])
        self.assertGreater(max(a for a in alphas), fp.LGB_KW['alpha'])

    def test_the_extreme_point_is_plain_l2(self):
        L05 = reg.by_id(reg.wave4_trials())['L05']
        self.assertEqual(L05['params'], {'objective': 'regression'})
        self.assertEqual(L05['kind'], 'control')

    def test_family_l_resolves_through_the_runner(self):
        self.assertTrue({'L01', 'L05'} <= set(reg.by_id(reg.all_trials())))


class AlphaIsRemovedForL2(unittest.TestCase):
    """`alpha` is a huber parameter. Leaving it set while the objective is `regression` ships a
    parameter the loss does not use, and `fp.predict('l2', ...)` pops it for that reason. If
    `hbt_params` does not do the same, `L05` is not the L2 control it claims to be."""

    def test_switching_the_objective_drops_the_huber_parameter(self):
        kw = reg.hbt_params({'objective': 'regression'})
        self.assertEqual(kw['objective'], 'regression')
        self.assertNotIn('alpha', kw)

    def test_the_incumbent_keeps_its_alpha(self):
        kw = reg.hbt_params(None)
        self.assertEqual(kw['objective'], 'huber')
        self.assertEqual(kw['alpha'], fp.LGB_KW['alpha'])

    def test_a_plain_alpha_override_is_untouched(self):
        kw = reg.hbt_params({'alpha': 4.0})
        self.assertEqual(kw['objective'], 'huber')
        self.assertEqual(kw['alpha'], 4.0)


if __name__ == '__main__':
    unittest.main()
