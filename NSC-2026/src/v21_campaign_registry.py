"""Session 38: the campaign registry -- every configuration, written down before anything runs.

Sessions 33-37 each froze one recipe, watched it lose, and moved to another family. That kept the
evaluation honest but it mapped almost nothing: a recipe failing was repeatedly read as a family
failing, and with one point per mechanism there was no way to tell "this direction is wrong" from
"this strength is wrong".

This registry holds **27 core configurations across six families**, each a single named change
against the incumbent, plus the follow-up slots the plan allows. Every entry carries its full
parameter payload, so a trial can never be identified by a label whose meaning has drifted.

    A  masking without duplication      4   does a masked VIEW help once row duplication is gone?
    B  hbt capacity                     8   retest, in the v21 context, on the current harness
    C  history length                   4   does a shorter label prefix transfer better?
    D  increment capacity               6   the same question for the dynamics models
    E  one level predictor, joint loss  3   level and change supervised through ONE function
    F  reconstruction averaging         2   marginalise the interpolation at inference

**B and D are retests, not novelties.** Members of these families have been tried before, on older
harnesses and older stacks. What is new is the context -- final `z` after the v21 stack and solver,
on the repaired populations -- and they are labelled `retest` so nobody reads a win as a discovery.

**What the registry does not do.** It is not a Cartesian grid: each entry changes one thing.
Follow-up slots (G/H/I) exist but are filled only from written rules after the confirmation stage,
never from a screen result and never from anything public.
"""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
import final_pipeline as fp

FAMILIES = ('A', 'B', 'C', 'D', 'E', 'F')
# Fresh seed families, fixed here so no run can pick the ones that scored well.
AUG_SEEDS = (2026090801, 2026090802, 2026090803, 2026090804, 2026090805)
VIEW_SEEDS = tuple(range(2026090891, 2026090900))       # nine, F02 uses all, F01 the first five
SCREEN_HBT_SEEDS = (0, 1)
CONFIRM_HBT_SEEDS = tuple(range(len(fp.SEEDS_FIT)))     # 0..4
STABILITY_HBT_SEEDS = (100, 101, 102, 103, 104)         # the second seed block for the final check
SCREEN_BLOCKS = ('B1_last15d', 'B2_prev15d')


def _t(tid, family, component, params, note, kind='novel'):
    return dict(id=tid, family=family, component=component, params=dict(params),
                note=note, kind=kind)


def core_trials():
    """The 27. Order is the execution order: A-D and F before E, which needs its own contract."""
    T = []

    # ---- A: one training view, n_train rows, weight 1. No concatenation. -------------------
    for tid, p in (('A01', 0.025), ('A02', 0.05), ('A03', 0.10)):
        T.append(_t(tid, 'A', 'hbt_view', dict(p=p, mode='all'),
                    'train hbt entirely on a masked reconstruction at p=%.3f' % p))
    T.append(_t('A04', 'A', 'hbt_view', dict(p=0.05, mode='episode', episode_hours=24),
                'per 24h episode, take the original or the masked feature rows with prob 0.5'))

    # ---- B: hbt capacity, one parameter each ------------------------------------------------
    for tid, k, v in (('B01', 'num_leaves', 7), ('B02', 'num_leaves', 31),
                      ('B03', 'n_estimators', 500), ('B04', 'n_estimators', 1400),
                      ('B05', 'reg_lambda', 10.0), ('B06', 'reg_lambda', 30.0),
                      ('B07', 'min_child_samples', 50), ('B08', 'colsample_bytree', 1.0)):
        T.append(_t(tid, 'B', 'hbt_params', {k: v},
                    'hbt %s=%r, everything else incumbent' % (k, v), kind='retest'))

    # ---- C: history length, label prefix only ------------------------------------------------
    for tid, tgt, days in (('C01', 'hbt', 21), ('C02', 'hbt', 28),
                           ('C03', 'inc', 21), ('C04', 'inc', 28)):
        T.append(_t(tid, 'C', 'history', dict(target=tgt, days=days),
                    'fit %s on the last %d days of labels only; raw context unchanged'
                    % (tgt, days)))

    # ---- D: increment capacity ----------------------------------------------------------------
    for tid, k, v in (('D01', 'num_leaves', 7), ('D02', 'num_leaves', 31),
                      ('D03', 'n_estimators', 250), ('D04', 'n_estimators', 900),
                      ('D05', 'min_child_samples', 60), ('D06', 'reg_lambda', 15.0)):
        T.append(_t(tid, 'D', 'inc_params', {k: v},
                    'both increment horizons %s=%r' % (k, v), kind='retest'))

    # ---- E: one predictor, level and change from the same function ---------------------------
    for tid, beta in (('E00', 0.0), ('E01', 0.25), ('E02', 1.0)):
        T.append(_t(tid, 'E', 'joint_level', dict(beta=beta),
                    'level loss with change penalty beta=%.2f (E00 is the L2 plumbing control)'
                    % beta))

    # ---- F: averaging the reconstruction at inference ----------------------------------------
    for tid, n in (('F01', 5), ('F02', 9)):
        T.append(_t(tid, 'F', 'inference_avg', dict(p=0.05, n_views=n, weight=0.5),
                    'q = 0.5*original + 0.5*mean of %d masked-horizon views' % n))
    return T


def by_id(trials=None):
    return {t['id']: t for t in (trials or core_trials())}


def family_of(tid):
    return tid[0]


def config_digest(trial):
    """Identity of a trial is its payload, never its label."""
    return hashlib.md5(json.dumps(
        {k: trial[k] for k in ('id', 'family', 'component', 'params')},
        sort_keys=True, default=str).encode()).hexdigest()


def hbt_params(overrides=None):
    """`fp.LGB_KW` with overrides applied.

    `alpha` is a huber parameter. Switching the objective away from huber drops it, the same way
    `fp.predict('l2', ...)` pops it -- otherwise family L's plain-L2 control would ship a
    parameter its loss does not use and would not be the control it claims to be.
    """
    kw = dict(fp.LGB_KW)
    kw.update(overrides or {})
    if kw.get('objective') != 'huber':
        kw.pop('alpha', None)
    return kw


def inc_params(overrides=None):
    kw = dict(fp.INC_KW)
    kw.update(overrides or {})
    return kw


def registry_manifest():
    trials = core_trials()
    assert len(trials) == 27, 'the core wave is 27 configurations, got %d' % len(trials)
    counts = {f: sum(1 for t in trials if t['family'] == f) for f in FAMILIES}
    assert counts == dict(A=4, B=8, C=4, D=6, E=3, F=2), counts
    assert len({t['id'] for t in trials}) == 27, 'trial ids must be unique'
    return dict(n_core=len(trials), counts=counts,
                aug_seeds=list(AUG_SEEDS), view_seeds=list(VIEW_SEEDS),
                screen_hbt_seeds=list(SCREEN_HBT_SEEDS),
                confirm_hbt_seeds=list(CONFIRM_HBT_SEEDS),
                stability_hbt_seeds=list(STABILITY_HBT_SEEDS),
                screen_blocks=list(SCREEN_BLOCKS),
                lgb_kw=fp.LGB_KW, inc_kw=fp.INC_KW,
                trials=[dict(t, digest=config_digest(t)) for t in trials])


# ---------------------------------------------------------------- screen -> confirm selection
MAX_CONFIRM_PER_FAMILY = 2
WORST_BLOCK_TOLERANCE = 0.10
POOLED_REJECT = 0.03


def select_for_confirmation(screen_rows):
    """Section 4.2's rule, applied to screen results and written down before confirmation runs.

    1. configurations improving BOTH screen blocks come first;
    2. then smallest pooled ΔRMSE whose worst block is within +0.10;
    3. anything losing on both blocks with pooled > +0.03 is not confirmed;
    4. a family with no qualifier is skipped -- the campaign continues with the others.

    `screen_rows` is one dict per trial with `id`, `family`, `d_pooled` and `d_worst_block`.
    """
    chosen, skipped = [], {}
    for fam in FAMILIES:
        rows = [r for r in screen_rows if r['family'] == fam]
        if not rows:
            skipped[fam] = 'no screen results'
            continue
        both = [r for r in rows if r.get('improves_both')]
        rest = [r for r in rows
                if r not in both
                and r['d_worst_block'] <= WORST_BLOCK_TOLERANCE
                and not (r['d_pooled'] > POOLED_REJECT and not r.get('improves_any'))]
        ranked = (sorted(both, key=lambda r: r['d_pooled'])
                  + sorted(rest, key=lambda r: r['d_pooled']))
        take = ranked[:MAX_CONFIRM_PER_FAMILY]
        if not take:
            skipped[fam] = 'no configuration met the confirmation rule'
            continue
        chosen.extend(take)
    return chosen, skipped


# ---------------------------------------------------------------- family I: refinement
# Section 6's rules, and only those. Each point is an interpolation between two configurations
# that both moved pooled in the same direction; no point is invented after seeing a winner, and
# unused slots are simply left unused.
REFINE_RULES = (
    ('I01', 'B', 'hbt_params', {'n_estimators': 1100},
     'B03 500 lost and B04 1400 won, so interpolate the 900->1400 direction'),
    ('I02', 'B', 'hbt_params', {'num_leaves': 11},
     'B01 leaves 7 beat both the incumbent 15 and B02 31, so interpolate to 11'),
    ('I03', 'D', 'inc_params', {'num_leaves': 11},
     'D01 leaves 7 beat the incumbent 15 on pooled, so interpolate to 11'),
)


# ------------------------------------------------------------------- session-40 wave (family J)
# `outputs/campaign_v21_s38/next_wave.md`, question 1, written before any of this was run:
# "Where does the tree-count curve stop? Register 1400/1800/2400 and a learning-rate pairing
# before running. If the gain is monotone to 2400 the mechanism is underfitting."
#
# Session 38 found `hbt` n_estimators monotone over 900 -> 1100 -> 1400 (I01 -0.0051, B04 -0.0107)
# with 1400 the largest value in that registry. The campaign rules forbid inventing a bigger point
# after seeing the biggest one win, so the bigger points are registered here, before the run, and
# the grid may not grow again afterwards.
#
# J01 re-runs 1400 inside this wave so the curve has an anchor at the same seeds; it is a retest.
# J04 is the control that separates "more trees" from "more total capacity": it holds
# n_estimators * learning_rate at the incumbent's 27 while tripling the number of trees. If J04
# lands on the incumbent, the session-38 gain was capacity; if it lands on the tree-count curve,
# it was step size. Without it, a monotone curve cannot distinguish the two.
WAVE2_RULES = (
    ('J01', {'n_estimators': 1400}, 'retest',
     'B04 re-run inside this wave, so the curve has a common-seed anchor'),
    ('J02', {'n_estimators': 1800}, 'novel',
     'next_wave.md question 1: the first point past the session-38 registry'),
    ('J03', {'n_estimators': 2400}, 'novel',
     'next_wave.md question 1: if the response is still monotone here, the mechanism is '
     'underfitting rather than a tuned optimum'),
    ('J04', {'n_estimators': 2700, 'learning_rate': 0.01}, 'control',
     'the learning-rate pairing: three times the trees at the incumbent total shrinkage '
     '(2700 * 0.01 == 900 * 0.03), so trees and capacity are separated'),
)


def wave2_trials():
    """The four session-40 points, in execution order. Frozen; see WAVE2_RULES."""
    return [_t(tid, 'J', 'hbt_params', params, note, kind=kind)
            for tid, params, kind, note in WAVE2_RULES]


# ------------------------------------------------------- session-41 wave (family K, the soil block)
# `drop_soil` has removed 76 columns from every member since session 2, and BOTH of its
# justifications have been withdrawn: §7's support claim (§97 measured it again and it is false for
# 70 of the 76) and §97's fallback appeal to §96 (whose headline is withdrawn in the banner and in
# §229, and whose soil evidence is a residual-stage test on a session-14 blend, not a feature test
# on the v21 stack).
#
# Re-measured on the private slice, 68 of 76 sit at support 1.000 and the six that collapse are all
# `_sd6h` DISPERSION columns. §7's mechanism is real and narrow: when irrigation halts the probes
# stop fluctuating, which destroys a rolling standard deviation and leaves a level alone.
#
# K03 is the control that makes this a measurement rather than a restoration. If support is the
# mechanism, adding ONLY the six broken columns should be the harmful arm; if K03 is harmless the
# support story is wrong and K01's result needs another explanation.
WAVE3_RULES = (
    ('K01', {'columns': 'supported'}, 'novel',
     'restore the 70 soil/rate columns that hold support on the private slice'),
    ('K02', {'columns': 'all_soil'}, 'novel',
     'restore all 76, including the six that collapse: what "drop none" is worth'),
    ('K03', {'columns': 'dispersion_only'}, 'control',
     'restore ONLY the six collapsing _sd6h columns, to test whether support is the mechanism'),
)


def wave3_trials():
    """The three session-41 soil arms. Frozen; see WAVE3_RULES."""
    return [_t(tid, 'K', 'hbt_features', params, note, kind=kind)
            for tid, params, kind, note in WAVE3_RULES]


# ---------------------------------------------------- session-45 wave (family L, the hbt loss)
# `hbt` holds the largest NNLS weight in every block and has been fitted with `huber, alpha=2.0`
# since session 8, on a target with standard deviation 18 %RH. Huber is linear past alpha, so every
# residual beyond 2 %RH contributes a constant gradient -- and §300 measured the wettest tercile at
# bias -3.498 carrying 46.4% of SSE. Those are the rows the loss declines to fully fit.
#
# §98 saw the shape of this and added one plain-L2 MEMBER, which NNLS pinned to the 0.042 floor
# because its residuals correlate 0.950 with `hbt`. The dominant member's own loss was never
# re-swept. Forty-four sessions, zero mentions of an alpha sweep.
#
# L05 is the extreme point and the control: plain L2, with `alpha` removed rather than ignored.
WAVE4_RULES = (
    ('L01', {'alpha': 1.0}, 'novel', 'harsher clipping than the incumbent, the other direction'),
    ('L02', {'alpha': 3.0}, 'novel', 'one step toward L2'),
    ('L03', {'alpha': 4.0}, 'novel', "cat's delta, and the alpha the v5 model used"),
    ('L04', {'alpha': 6.0}, 'novel', 'a third of the target standard deviation'),
    ('L05', {'objective': 'regression'}, 'control',
     'plain L2: the limit of the sweep, and the loss the metric actually is'),
)


def wave4_trials():
    """The five session-45 loss points. Frozen; see WAVE4_RULES."""
    return [_t(tid, 'L', 'hbt_params', params, note, kind=kind)
            for tid, params, kind, note in WAVE4_RULES]


def all_trials():
    """Every registered trial the runner may be asked for, across waves.

    `an89` resolves `--ids` against this. A wave that is registered but missing here is
    registered and unrunnable, which is a silent failure rather than a loud one.
    """
    return (core_trials() + refine_trials() + wave2_trials() + wave3_trials()
            + wave4_trials())


def refine_trials(families=('B', 'D')):
    """At most two families and two points each, from REFINE_RULES alone."""
    out, per = [], {}
    for tid, fam, comp, params, note in REFINE_RULES:
        if fam not in families or per.get(fam, 0) >= 2:
            continue
        per[fam] = per.get(fam, 0) + 1
        out.append(_t(tid, fam, comp, params, note, kind='refine'))
    return out
