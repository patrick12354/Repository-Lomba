"""Session 39: score the sequence prediction as a seventh BLEND MEMBER.

Sections 229, 233 and 234 all spent `q` the same way -- as a scalar weight on the finished level
-- and all three failed at the weight. This arm never chooses a weight. `q` becomes a column in
the inner out-of-fold frame, and the weight comes from the blend estimator `final_pipeline` has
run for eighteen nested folds: NNLS over the whole frame, shrunk toward equal weighting, refitted
per time-of-day band and shrunk again toward the global vector.

**How the incumbent members are held fixed.** `member_preds_seq` delegates every non-`seq` member
to `an47.member_preds` unchanged, so the five incumbents are bit-identical by construction rather
than by inspection. `tests/test_v21_seq_member.py` pins that.

**The pre-registered readings, written before the arm was run.** Both are informative, which is
the point of registering them:

* NNLS weight on `seq` below 0.02 -- the member is redundant at blend level. The family then
  closes on a mechanism DIFFERENT from section 234's (redundancy, not weight mis-selection).
* Weight in 0.05-0.20 with pooled improving and B1 worsening past +0.10 -- section 233's bound
  reappears at member level, and the family closes on a second independent measurement.

**The gate for this arm**, frozen before execution and not to be moved afterwards: pooled
<= -0.02, `d_B3` <= 0, `d_matched` <= 0, `d_pooled7` <= 0, and `d_B1` <= +0.10. The last is a
deliberate loosening of the standing "no primary block may worsen" rule, and its size is taken
from section 233's oracle sweep -- B1 costs about 0.119 at the oracle's best uniform weight of
0.15 -- not from anything this arm produced.
"""
import sys
from pathlib import Path

import pickle

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
import final_pipeline as fp
import an47_v21_forward_benchmark as a47
import v21_sequence_design as sd
import v21_seq_member as sm

SEQ = 'seq'


def member_preds_seq(F_train, F_pred, y, t_idx, v_idx, models, seeds, seq_kw=None):
    """`an47.member_preds` plus a `seq` column, in `models` order.

    Every member other than `seq` is produced by the original function, on the original
    arguments, so this cannot move an incumbent. `seq` is clipped to the same [5, 100] the other
    members are.
    """
    base = [m for m in models if m != SEQ]
    out = a47.member_preds(F_train, F_pred, y, t_idx, v_idx, base, seeds)
    if SEQ in models:
        if F_train is not F_pred:
            raise ValueError('seq needs one frame for the windows it fits and predicts on; '
                             'an47 was called with train_feats_at_origin')
        q = sm.seq_predict(F_train, y, t_idx, v_idx, **(seq_kw or {}))
        out[SEQ] = np.clip(q, 5, 100)
    return out[list(models)]


# --------------------------------------------------------------------------- the arm
# The session-27 cache already stores every member's prediction at every inner and outer row
# (`m_hbt` ... `m_l2`), and re-stacking those columns reproduces the banked level EXACTLY --
# max |rebuilt - cached| is 0.0 on all three blocks. So the arm does not refit the incumbent
# stack: it fits only `seq`, adds the column, and re-runs the same blend. That makes the
# control identical by construction rather than to a tolerance, and it removes six member
# refits per fold from the cost.

def frames_from_cache(block_rows, models):
    """`O` (inner meta frame) and `V` (outer member matrix) as `build_block` assembled them."""
    def prep(d):
        d = d.rename(columns={'m_' + m: m for m in models}).copy()
        ts = pd.DatetimeIndex(d.datetime)
        d['tod'] = ts.hour + ts.minute / 60.0
        d['dt'] = ts
        return d
    return (prep(block_rows[block_rows.scope == 'inner']),
            prep(block_rows[block_rows.scope == 'outer']))


def nnls_weights(O, models, shrink):
    """The global weight vector `a36.stack` fits, reported so the pre-registered reading on the
    `seq` weight can be made before any score is looked at."""
    from scipy.optimize import nnls
    w, _ = nnls(O[list(models)].to_numpy(), O.y.to_numpy())
    w = w / w.sum() if w.sum() > 0 else np.ones(len(models)) / len(models)
    w = (1 - shrink) * w + shrink * np.ones(len(models)) / len(models)
    return dict(zip(models, (float(x) for x in w)))


def seq_columns(g, y, block_rows, feats, seq_kw=None):
    """`seq` at every inner and outer row of one block.

    Each inner fold is fitted at its OWN origin on a frame truncated at its OWN horizon end, so
    a fold ending in July never sees August sensors through a centred window -- the same rule
    `build_block` applies to the members it refits.
    """
    out = {}
    for (origin, he), part in block_rows.groupby(['origin', 'horizon_end'], sort=False):
        gh, F = a47.frame_at(g, he, feats)
        train = sd_training_rows(gh, F, y, origin)
        idx = pd.DatetimeIndex(part.datetime)
        q = np.clip(sm.seq_predict(F, y, train, idx, **(seq_kw or {})), 5, 100)
        print('    seq  origin %s  horizon %s  train %d  rows %d'
              % (pd.Timestamp(origin).date(), pd.Timestamp(he).date(), len(train), len(idx)),
              flush=True)
        out.update(dict(zip(idx, q)))
    return out


def sd_training_rows(gh, F, y, origin):
    import v21_sequence_design as sd
    return sd.training_rows(gh, F, y, origin)


# The bar, frozen in this module's docstring before the arm ran. `PRIMARY` is the pooled
# population the campaign calls `n_primary`: B1 and B2 together.
PRIMARY = ('B1_last15d', 'B2_prev15d')
BAR = dict(pooled=-0.02, b1_tolerance=0.10, b2=0.0, b3=0.0)
# Conditions the session-27 cache cannot measure. `pooled7` needs the three 7-day H blocks and
# `matched` needs the matched-calendar index, both of which live in the session-38 campaign
# harness. They are named here rather than quietly omitted: section 264 caught `an87.choose`
# skipping a comparison when its input was missing, and the repair was to fail closed.
NEEDS_OTHER_HARNESS = ('pooled7', 'matched')


def gate(P, arm='seq'):
    """Evaluate the frozen bar on one arm. Returns the deltas, each condition, and the
    conditions this harness cannot measure.

    `promotable` is False whenever anything is unevaluated, so a screen can never be mistaken
    for a promotion decision.
    """
    d = P[P.arm == arm] if 'arm' in P.columns else P

    def delta(sub):
        return float(fp.rmse(sub.y, sub.z_cand) - fp.rmse(sub.y, sub.z_ctrl))

    per = {b: delta(x) for b, x in d.groupby('block')}
    pooled = delta(d[d.block.isin(PRIMARY)])
    r = dict(arm=arm, d_pooled=pooled, per_block=per,
             unevaluated=list(NEEDS_OTHER_HARNESS))
    r['bar_pooled'] = bool(pooled <= BAR['pooled'])
    r['bar_b1'] = bool(per.get('B1_last15d', 0.0) <= BAR['b1_tolerance'])
    r['bar_b2'] = bool(per.get('B2_prev15d', 0.0) < BAR['b2'])
    r['bar_b3'] = bool(per.get('B3_shift7d', 0.0) <= BAR['b3'])
    r['promotable'] = bool(r['bar_pooled'] and r['bar_b1'] and r['bar_b2'] and r['bar_b3']
                           and not r['unevaluated'])
    return r


def v21_terms(g, y, d, seeds, feats):
    """The banked increment terms: no physics, no de-shrink, no lags -- exactly what v21 ships
    and exactly what `an72` reconciled the section-229 arms with."""
    idx = pd.DatetimeIndex(d.datetime)
    gh, F = a47.frame_at(g, d.horizon_end.iloc[0], feats)
    origin = pd.Timestamp(d.origin.iloc[0])
    mask = a47.train_mask_before(g, gh, y, origin)
    inc = fp.fit_increments(F, y.reindex(gh.index), mask, seeds, physics=False, deshrink=False)
    return idx, a47.increment_terms(F, idx, inc, None, 0.0)


def run(blocks=None, seq_kw=None, out_dir=None):
    import json
    import an36_increment_production as a36

    g = fp.load_grid()
    y = g[fp.TARGET]
    with open(ROOT / 'outputs/audit_v21_s27/forward_predictions.pkl', 'rb') as fh:
        cache = pickle.load(fh)
    M = list(fp.MODELS_L2)
    MS = M + [SEQ]
    feats, rows, weights = {}, [], {}

    for name, blk in cache.groupby('block', sort=False):
        if blocks and name not in blocks:
            continue
        print('  %s' % name, flush=True)
        O, V = frames_from_cache(blk, M)

        # ---- control: re-stack the cached members. Must be bit-identical to the banked level.
        ctrl_level = a36.stack(O, V, M, fp.BLEND_SHRINK)
        gap = float(np.max(np.abs(ctrl_level - V.level.to_numpy())))
        assert gap == 0.0, '%s: control did not reproduce the banked level (%g)' % (name, gap)
        print('    control reproduces the banked level exactly', flush=True)

        # ---- the extra column, one per arm.
        #
        # `dup` and `noise` are section 105's dilution controls and they are the reason this
        # arm is interpretable. A seventh member changes the shrinkage target for EVERY member
        # (1/6 -> 1/7), so some of any delta is a re-weighting artefact rather than information.
        # Section 105 measured that floor at -0.013 nested using exactly these two members: a
        # literal duplicate, and `hbt` plus Gaussian noise. `seq` has to beat what they do here.
        q = seq_columns(g, y, blk, feats, seq_kw)
        rng = np.random.default_rng(20260907)
        extra = {
            SEQ: (pd.DatetimeIndex(O.datetime).map(q).to_numpy(float),
                  pd.DatetimeIndex(V.datetime).map(q).to_numpy(float)),
            'dup': (O['hbt'].to_numpy(), V['hbt'].to_numpy()),
        }
        sigma = float(O['hbt'].std()) * 0.0633      # section 105's corr(member, hbt) = 0.998
        extra['noise'] = (O['hbt'].to_numpy() + rng.normal(0, sigma, len(O)),
                          V['hbt'].to_numpy() + rng.normal(0, sigma, len(V)))

        idx, terms = v21_terms(g, y, V, a47.SEEDS_INC, feats)
        z_ctrl = a47.solve(ctrl_level, idx, terms)
        base = dict(block=name, datetime=idx, y=V.y.to_numpy(), origin=V.origin.to_numpy(),
                    horizon_end=V.horizon_end.to_numpy(),
                    level_ctrl=ctrl_level, z_ctrl=z_ctrl)

        for arm, (o_col, v_col) in extra.items():
            Oa, Va = O.copy(), V.copy()
            Oa[arm], Va[arm] = o_col, v_col
            assert np.isfinite(Oa[arm]).all() and np.isfinite(Va[arm]).all()
            ms = M + [arm]
            w = nnls_weights(Oa, ms, fp.BLEND_SHRINK)
            weights.setdefault(name, {})[arm] = w
            lvl = a36.stack(Oa, Va, ms, fp.BLEND_SHRINK)
            z = a47.solve(lvl, idx, terms)
            rows.append(pd.DataFrame(dict(base, arm=arm, level_cand=lvl, q=v_col, z_cand=z)))
            print('    %-5s weight %.4f (floor %.4f) | level %.5f -> %.5f | recon %.5f -> %.5f'
                  ' (%+.5f)'
                  % (arm, w[arm], fp.BLEND_SHRINK / len(ms),
                     fp.rmse(V.y, ctrl_level), fp.rmse(V.y, lvl),
                     fp.rmse(V.y, z_ctrl), fp.rmse(V.y, z),
                     fp.rmse(V.y, z) - fp.rmse(V.y, z_ctrl)), flush=True)

    P = pd.concat(rows, ignore_index=True)
    out_dir = Path(out_dir or (ROOT / 'outputs' / 'audit_v21_s39'))
    out_dir.mkdir(parents=True, exist_ok=True)
    P.to_pickle(out_dir / 'preds_seq_member.pkl')
    (out_dir / 'weights.json').write_text(json.dumps(weights, indent=2))
    return P, weights


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--blocks', nargs='*', default=None)
    ap.add_argument('--kernels', type=int, default=None)
    a = ap.parse_args()
    kw = dict(n_kernels=a.kernels) if a.kernels else None
    P, w = run(a.blocks, kw)
    print('\n%-6s %10s %10s %10s   per block' % ('arm', 'pooled', 'ctrl', 'delta'))
    for arm, d in P.groupby('arm'):
        per = '  '.join('%s %+.5f' % (b[:2], fp.rmse(x.y, x.z_cand) - fp.rmse(x.y, x.z_ctrl))
                        for b, x in d.groupby('block'))
        print('%-6s %10.6f %10.6f %+10.6f   %s'
              % (arm, fp.rmse(d.y, d.z_cand), fp.rmse(d.y, d.z_ctrl),
                 fp.rmse(d.y, d.z_cand) - fp.rmse(d.y, d.z_ctrl), per))
    print('\nseq is only evidence to the extent it beats `dup` and `noise` (section 105).')


if __name__ == '__main__':
    main()
