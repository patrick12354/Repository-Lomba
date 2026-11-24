"""Session 47: the blend's forward level bias, and where it comes from.

**The observation.** On the scored rows of the forward cache the six members carry these mean
signed errors (prediction minus truth), pooled over the three 15-day outer blocks:

    hbt +0.578   cat -2.892   ridge +0.114   enet +0.046   ridge_e -0.382   l2 +0.732

Five of the six sit inside +-0.8 %RH. `cat` sits at -2.9 on the outer rows and -4.5 on the inner
ones, and it holds roughly a quarter of the blend weight, so the stack inherits a level bias of
about -1.0 %RH that no component of the pipeline can remove: NNLS weights are non-negative and
normalised, so the blend cannot produce an intercept, and both `tod_bias` and `harm_bias` fit an
intercept and then deliberately throw it away (progress.md 69, 73).

`cat`'s in-sample bias is -0.006. This is a forward property of `Huber:delta=4` on a target with
standard deviation 18 %RH, not a fitting artefact -- every residual past 4 %RH contributes a
constant gradient, so the member tracks something close to a conditional median and lands low when
it is asked to predict past its training window.

**The arm.** One scalar per member, measured on that block's own past-only inner frame `O` and
subtracted from the member on both `O` and the outer rows before the stack is fitted. Nothing else
moves: same members, same weights machinery, same increment terms, same solver.

Two controls, both registered before the numbers were read:

* `wrong_sign` -- add the measured offset instead of subtracting it. If the gain were "the blend
  likes being shifted up", this would lose by about as much as the candidate wins.
* `debias_enet` -- the same machinery pointed at the member whose measured bias is +0.05. It has
  nothing to remove, so it must do nothing.

    .venv/Scripts/python.exe src/an100_v21_member_bias_arm.py
"""
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
import final_pipeline as fp
import an36_increment_production as a36
import an47_v21_forward_benchmark as a47
import an76_v21_level_shape as a76
import an96_v21_increment_bundle_split as a96

OUT = ROOT / 'outputs' / 'audit_v21_s47'
M = list(fp.MODELS_L2)
MR = [m for m in M if m != 'ridge']
BLOCKS = ['B1_last15d', 'B2_prev15d', 'B3_shift7d', 'H1_last7d', 'H2_last14d', 'H3_last21d']
PRIMARY = ('B1_last15d', 'B2_prev15d')
SEVEN = ('H1_last7d', 'H2_last14d', 'H3_last21d')

# (label, member, strength). Strength multiplies the measured offset; a negative one adds it.
ARMS = [('control', None, 0.0),
        ('debias_cat_25', 'cat', 0.25),
        ('debias_cat_50', 'cat', 0.50),
        ('debias_cat_75', 'cat', 0.75),
        ('debias_cat_100', 'cat', 1.00),
        ('wrong_sign', 'cat', -0.50),
        ('debias_enet', 'enet', 0.50)]


def shifted(O, V, member, strength):
    """`O` and `V` with one member's past-only mean error removed at the given strength."""
    if member is None or strength == 0.0:
        return O, V, 0.0
    b = strength * float((O[member] - O.y).mean())
    O2, V2 = O.copy(), V.copy()
    O2[member] = np.clip(O[member] - b, 5, 100)
    V2[member] = np.clip(V[member] - b, 5, 100)
    return O2, V2, b


def run(reconcile=True):
    OUT.mkdir(parents=True, exist_ok=True)
    g = fp.load_grid()
    y = g[fp.TARGET]
    c15 = a47.load_cache(a76.CACHE_15, a76.MANIFEST_15)
    c7 = a76.load_validated(a76.CACHE_7, a76.MANIFEST_7, '7-day forward')
    oof7 = a76.load_validated(a76.OOF7, a76.OOF7_MANIFEST, 'rebuilt 7-day OOF')
    feats, res = {}, {a[0]: [] for a in ARMS}
    offsets = {}

    for name in BLOCKS:
        t0 = time.time()
        O, V = a96.block_frames(g, y, name, c15, c7, oof7)
        idx = pd.DatetimeIndex(V.datetime)
        terms = None
        if reconcile:
            gh, F = a47.frame_at(g, V.horizon_end.iloc[0], feats)
            mask = a47.train_mask_before(g, gh, y, pd.Timestamp(V.origin.iloc[0]))
            inc = fp.fit_increments(F, y.reindex(gh.index), mask, a47.SEEDS_INC)
            terms = a47.increment_terms(F, idx, inc, None, 0.0)
        for label, member, strength in ARMS:
            O2, V2, b = shifted(O, V, member, strength)
            level = a36.stack(O2, V2, MR, fp.BLEND_SHRINK)
            z = a47.solve(level, idx, terms) if reconcile else level
            res[label].append((name, V.y.to_numpy(), z))
            offsets.setdefault(label, {})[name] = b
        print('  %-12s [%3.0f s]  %s' % (name, time.time() - t0,
                                         '  '.join('%s %.5f' % (l, fp.rmse(res[l][-1][1],
                                                                           res[l][-1][2]))
                                                   for l, _, _ in ARMS)), flush=True)

    def pooled(label, sel):
        yy = np.concatenate([b for n, b, _ in res[label] if n in sel])
        zz = np.concatenate([c for n, _, c in res[label] if n in sel])
        return float(np.sqrt(np.mean((yy - zz) ** 2)))

    summary = {}
    print('\n%-15s %11s %11s %11s %11s' % ('arm', 'd_primary', 'd_7d', 'worst_H', 'd_B3'))
    for label, _, _ in ARMS:
        per = {n: fp.rmse(b, c) - fp.rmse(b2, c2)
               for (n, b, c), (_n, b2, c2) in zip(res[label], res['control'])}
        summary[label] = dict(
            d_primary=pooled(label, PRIMARY) - pooled('control', PRIMARY),
            d_pooled7=pooled(label, SEVEN) - pooled('control', SEVEN),
            worst_h=max(per[n] for n in SEVEN), d_b3=per['B3_shift7d'],
            per_block=per, offsets=offsets[label],
            blocks_improved=int(sum(v < 0 for v in per.values())))
        s = summary[label]
        print('%-15s %+11.6f %+11.6f %+11.6f %+11.6f   %d/6 blocks better'
              % (label, s['d_primary'], s['d_pooled7'], s['worst_h'], s['d_b3'],
                 s['blocks_improved']))
        print('   per block: %s' % {k[:2]: round(v, 5) for k, v in per.items()})
    tag = 'member_bias_arms' + ('' if reconcile else '_level')
    (OUT / (tag + '.json')).write_text(json.dumps(summary, indent=2, default=str))
    pd.to_pickle(res, OUT / ('preds_' + tag + '.pkl'))
    return summary


if __name__ == '__main__':
    run(reconcile='--level-only' not in sys.argv)
