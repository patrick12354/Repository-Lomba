"""Session 26, Tahap 0 of the v21 re-evaluation: one forward harness that every candidate is
scored on, with the provenance needed to tell two runs apart.

What this fixes about the way session 22-25 measured things.

1. **A primary metric that is defined.** `pooled` is now `sqrt(sum SSE / sum n)` over the two
   NON-OVERLAPPING blocks B1 and B2. Section 176 reported the MEAN of block RMSEs under the
   same word, and `an36_increment_production.py` pooled B3 in as though it were a third
   independent fortnight when it is a 7-day shift that overlaps both. B3 is still computed and
   still reported -- as a sensitivity, never as an extra 720 rows of evidence.

2. **Seed counts that match what ships.** `an36` called `fit_increments` with no `seeds`
   argument, so the cached "production" scores were built from ONE increment seed while the
   shipped file averages five and `an41` used five. Every control and every candidate in this
   session uses `SEEDS_INC` (five), so a seed-count difference can never masquerade as a
   mechanism difference.

3. **A calibration set that exists.** Nothing before this session had a forward window on which
   a meta parameter could be fitted without touching the scored rows. The inner rolling origins
   that train the level stack are reused: for inner fold i the stack is refitted on folds < i
   only and applied to fold i, which makes each fold a genuine forward level prediction. The
   fold windows are 8 days at a 2-day step and therefore overlap, so SSE is accumulated only on
   each fold's last two days -- `score` in the cache marks those rows. The union is a
   non-overlapping stretch of forward days ending exactly at the outer origin, and no label at
   or after the origin is used to produce any of it.

**Feature-horizon policy.** One feature matrix per block, built from the grid truncated at the
END of that block's horizon. This is production's shape, not a relaxation of it: in production
the grid ends at the last test row and training rows near the boundary legitimately see
test-period EXOGENOUS sensors, which is all `make_features` reads. Building training features
from a grid stopped at the origin would be a different -- stricter -- policy than the one that
ships; `--train-features-at-origin` runs it as an ablation rather than as the default.

**What this harness does NOT establish.** B1, B2 and B3 sit in the same calendar as every
experiment in this log, they are not new days, and a candidate that wins here has won on data
that has been looked at many times. The bar in section 180 exists because of that, not despite
it.

---------------------------------------------------------------------------------------------
**Session 27.** Four repairs, all to the measurement, none to the model. See section 190.

1. **The inner calibration set was not label-isolated.** Meta rows were selected as
   `O.fold.isin(fids[:k])` -- by fold NUMBER. Folds are 8-day windows at a 2-day step, so fold
   k-1's labels run six days past fold k's origin, and the first scored fold was additionally
   scored on its whole window instead of its 2-day tail. 864 of 2304 calibration rows were
   scored under parameters fitted from their own labels, 60% of them on B2. `meta_prior` now
   selects on the label timestamp AND on whether the producing fold was itself fitted before
   this origin; the whole-window exception is gone. An origin left with less than
   MIN_META_ROWS/MIN_META_DAYS of legitimate history takes `stack_fallback` and is not scored.
2. **An inner fold read exogenous data from after its own horizon.** One feature matrix was
   built per block and reused for every fold in it, so a fold ending 2023-07-31 saw sensors
   through 2023-08-29. `frame_at` gives each simulated forecast a matrix truncated at its own
   horizon end. Joint train+test exogenous INSIDE a horizon is the shipped policy and is
   unchanged; this only removes what was after it.
3. **`--train-features-at-origin` did not do what it says.** `an36.member_preds` takes one
   frame and uses it to fit and to predict, so the flag changed the inner member fits and left
   the outer ones reading the block matrix. `member_preds` here takes both frames.
4. **The cache was loaded without checking the manifest.** `load_cache` refuses a pickle whose
   code, input or config hashes have moved, naming the field.

The session-26 cache and every artifact scored from it stay where they are, under
`outputs/audit_v21/`; the rebuild writes to `outputs/audit_v21_s27/`. Numbers from the two
namespaces are NOT comparable -- repairs 1 and 2 both change what a fold sees -- so every
session-27 candidate is compared against controls rebuilt in the same namespace.

    .venv/Scripts/python.exe src/an47_v21_forward_benchmark.py --rebuild --controls
"""
import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.sparse import identity
from scipy.sparse.linalg import spsolve

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'src'))
import final_pipeline as fp
import an36_increment_production as a36

OUT = ROOT / 'outputs' / 'audit_v21'
CACHE = OUT / 'forward_predictions.pkl'
MANIFEST = OUT / 'manifest.json'
# Session 27 rebuilds into its own namespace so the session-26 artifacts that sections 183-187
# were written from stay byte-identical and still load under their own manifest.
OUT_S27 = ROOT / 'outputs' / 'audit_v21_s27'
CACHE_S27 = OUT_S27 / 'forward_predictions.pkl'
MANIFEST_S27 = OUT_S27 / 'manifest.json'
HOLD_DAYS = 15
BACKBONE = 'v16'                 # MODELS_L2 + BLEND_SHRINK, the shipped stack
SEEDS_INC = tuple(fp.INC_SEED + i for i in range(fp.INC_SEEDS))
PRIMARY_BLOCKS = ('B1_last15d', 'B2_prev15d')
SCORE_TAIL_DAYS = 2              # the non-overlapping slice of each inner fold window
# Session 27. The meta rows an inner fold is allowed to learn from are now the ones whose LABEL
# timestamp is at or before that fold's own origin, not the ones carrying a smaller fold number
# -- see section 190. Folds left with less than this much history do not get to fit anything:
# they take the frozen fallback below and are excluded from calibration rather than scored on
# parameters fitted from two days. Both numbers are frozen here, before the rebuild.
MIN_META_ROWS = 192              # 4 days at 48 rows/day
MIN_META_DAYS = 4

# The promotion bar, frozen here before any candidate is run. It is an engineering rule for
# spending submission slots, not a significance test and not a leaderboard prediction.
BAR = dict(pooled_gain=0.02, require_both_blocks=True, b3_tolerance=0.05)


def md5(path):
    return hashlib.md5(Path(path).read_bytes()).hexdigest()


def pooled(y, p, n=None):
    """sqrt(sum SSE / sum n). Given arrays it is just RMSE; given per-block RMSEs and counts
    it is the SSE-weighted combination, which is the thing section 176 did not compute."""
    if n is None:
        e = np.asarray(y, float) - np.asarray(p, float)
        return float(np.sqrt(np.mean(e ** 2)))
    y, n = np.asarray(y, float), np.asarray(n, float)
    return float(np.sqrt(np.sum(y ** 2 * n) / n.sum()))


def blocks_of(g):
    boundary = g.index[(g.is_test == 0).to_numpy()].max()
    day = pd.Timedelta(days=HOLD_DAYS)
    return [('B1_last15d', boundary - day, boundary),
            ('B2_prev15d', boundary - 2 * day, boundary - day),
            ('B3_shift7d', boundary - day - pd.Timedelta(days=7),
             boundary - pd.Timedelta(days=7))]


def member_preds(F_train, F_pred, y, t_idx, v_idx, models, seeds):
    """`an36.member_preds` with the matrix the members are FITTED on separated from the matrix
    they PREDICT from.

    `an36` takes a single frame and uses it for both, which is why `--train-features-at-origin`
    never did what its name says: it changed the inner member fits and left the outer ones
    reading the block-wide matrix. Keeping the two arguments apart makes the ablation a
    property of the call rather than of which variable happened to be in scope. Passing the
    same frame twice reproduces `an36.member_preds` exactly; `tests/test_v21_inner_contract.py`
    pins that."""
    esT_t = pd.Series(fp.es(F_train.loc[t_idx, 'T'].values), index=t_idx)
    E_t = y.loc[t_idx] * esT_t / 100.0
    esv = fp.es(F_pred.loc[v_idx, 'T'].values)
    out = {}
    for m in models:
        sd = seeds if fp.base_model(m) in ('hbt', 'cat') else (0,)
        out[m] = np.clip(fp.predict(fp.base_model(m), F_train.loc[t_idx], y.loc[t_idx],
                                    F_pred.loc[v_idx], esv, E_t, sd), 5, 100)
    return pd.DataFrame(out, index=v_idx)


def stack_on(O_train, V, models=None, shrink=fp.BLEND_SHRINK):
    """`an36.stack` with the training frame separated from the frame being predicted, so the
    same code can serve the outer holdout and an inner fold."""
    return a36.stack(O_train, V, models or fp.MODELS_L2, shrink)


def stack_fallback(V, models=None):
    """The frozen no-calibration stack: equal member weights, no time-of-day bands, no
    harmonic correction. Used when an inner origin has too little legitimate history behind it
    to fit anything -- section 190's rule is that such a fold does not get to learn parameters,
    not that it gets to learn them from six days of future labels."""
    models = models or fp.MODELS_L2
    return np.clip(V[list(models)].to_numpy().mean(axis=1), 5, 100)


def meta_prior(O, spans, origin):
    """The meta rows an inner origin is allowed to see. Two conditions, both enforced:

    1. the row's own LABEL timestamp is at or before the origin, and
    2. the fold that produced it was fitted on data ending at or before the origin, so the
       prediction in the row is itself a forward one from where this origin stands.

    The bug this replaces selected by fold NUMBER and checked neither. Inner folds are 8-day
    windows at a 2-day step, so fold k-1's window ends six days AFTER fold k's origin, and
    every fold inherited six days of labels from its own future. Fold number orders the fits;
    it does not order the labels."""
    origin = pd.Timestamp(origin)
    ok = [f for f, (vs, _) in spans.items() if vs <= origin]
    return O.loc[O.fold.isin(ok) & (pd.DatetimeIndex(O.dt) <= origin)]


def build_block(g, y, name, hs, he, train_feats_at_origin=False, models=None,
                seeds_oof=None, seeds_fit=None, feature_cache=None):
    """Level predictions for one block: the outer holdout plus every inner calibration fold.

    Each inner fold is a self-contained simulated forecast. Its features come from a grid
    truncated at ITS OWN horizon end, not the block's -- an inner fold ending 2023-07-31 has no
    business reading exogenous sensors from 2023-08-29 through a centered rolling window. Its
    members are fitted before its origin, and its stack is fitted on meta rows whose labels are
    also before its origin."""
    models = list(models or fp.MODELS_L2)
    seeds_oof = seeds_oof if seeds_oof is not None else tuple(range(len(fp.SEEDS_OOF)))
    seeds_fit = seeds_fit if seeds_fit is not None else tuple(range(len(fp.SEEDS_FIT)))
    feats = feature_cache if feature_cache is not None else {}

    def frame(end):
        end = pd.Timestamp(end)
        if end not in feats:
            feats[end] = fp.make_features(g.loc[g.index <= end])
        return feats[end]

    F = frame(he)
    labelled = pd.Series((g.loc[g.index <= he].is_test == 0).values, index=F.index) \
        & y.reindex(F.index).notna()
    lab_idx = F.index[labelled.to_numpy()]
    pre = lab_idx[lab_idx <= hs]
    hold = lab_idx[(lab_idx > hs) & (lab_idx <= he)]
    assert len(hold) > 400 and len(pre) > 900, (len(pre), len(hold))
    assert pre.max() <= hs < hold.min()

    origins = a36.inner_origins(pre)
    oof, spans = [], {}
    for fi, (vs, ve) in enumerate(origins):
        v = pre[(pre > vs) & (pre <= ve)]
        t = pre[pre <= vs]
        if len(t) < 300 or len(v) < 50:
            continue
        Fi = frame(ve)                       # exogenous stops at THIS fold's horizon end
        Ftr = frame(vs) if train_feats_at_origin else Fi
        d = member_preds(Ftr, Fi, y, t, v, models, seeds_oof)
        d['y'] = y.loc[v].to_numpy()
        d['tod'] = Fi.loc[v, 'tod'].to_numpy()
        d['fold'] = fi
        spans[fi] = (vs, ve)
        oof.append(d.reset_index(names='dt'))
        print('    inner fold %d  %s -> %s  n=%d' % (fi, vs.date(), ve.date(), len(v)),
              flush=True)
    O = pd.concat(oof, ignore_index=True)
    assert O.dt.max() <= hs, 'meta training reaches past the origin'

    # ---- outer holdout: members refitted on everything before the origin, five seeds -------
    F_out_train = frame(hs) if train_feats_at_origin else F
    V = member_preds(F_out_train, F, y, pre, hold, models, seeds_fit)
    V['y'] = y.loc[hold].to_numpy()
    V['tod'] = F.loc[hold, 'tod'].to_numpy()
    # The member columns ride along under an `m_` prefix. Section 191 needs `p_j - p_0` for
    # every member at every scored row, and refitting six members at nine origins to recover
    # something the build already computed would be twenty minutes spent on arithmetic.
    rows = [pd.DataFrame({'block': name, 'scope': 'outer', 'fold': -1,
                          'datetime': hold, 'y': V.y.to_numpy(),
                          'level': stack_on(O, V, models), 'score': True,
                          'origin': hs, 'horizon_end': he,
                          'meta_rows': len(O), 'meta_days': _days(O.dt),
                          'meta_fallback': False,
                          **{'m_' + m: V[m].to_numpy() for m in models}})]

    # ---- inner folds: stack fitted on meta rows labelled at or before this fold's origin ---
    for fi in sorted(spans):
        cur = O.loc[O.fold == fi].sort_values('dt')
        vs, ve = spans[fi]
        prior = meta_prior(O.loc[O.fold != fi], {f: s for f, s in spans.items() if f != fi}, vs)
        enough = len(prior) >= MIN_META_ROWS and _days(prior.dt) >= MIN_META_DAYS
        p = stack_on(prior, cur, models) if enough else stack_fallback(cur, models)
        cut = ve - pd.Timedelta(days=SCORE_TAIL_DAYS)
        rows.append(pd.DataFrame({'block': name, 'scope': 'inner', 'fold': fi,
                                  'datetime': pd.DatetimeIndex(cur.dt), 'y': cur.y.to_numpy(),
                                  'level': p,
                                  'score': (cur.dt > cut).to_numpy() & enough,
                                  'origin': vs, 'horizon_end': ve,
                                  'meta_rows': len(prior), 'meta_days': _days(prior.dt),
                                  'meta_fallback': not enough,
                                  **{'m_' + m: cur[m].to_numpy() for m in models}}))
    out = pd.concat(rows, ignore_index=True)
    inner = out.loc[out.scope == 'inner']
    used = inner.loc[inner.score]
    print('  outer n=%d level RMSE %.5f | inner folds %d (%d fell back), calibration rows %d '
          'over %d days'
          % (len(hold), fp.rmse(V.y, out.loc[out.scope == 'outer', 'level']),
             inner.fold.nunique(),
             int(inner.groupby('fold').meta_fallback.first().sum()),
             len(used), _days(used.datetime)), flush=True)
    return out


def _days(s):
    return int(pd.DatetimeIndex(s).normalize().nunique()) if len(s) else 0


# ------------------------------------------------------------------ reconciliation helpers

def frame_at(g, horizon_end, feature_cache=None):
    """The grid and feature matrix for one simulated forecast: everything up to ITS horizon
    end, and nothing after.

    Session 27. `block_frame` below was called once per block and its matrix reused for every
    inner fold in that block, which handed a fold ending 2023-07-31 the exogenous record
    through 2023-08-29 -- eight days of sensors that had not been recorded at the fold's own
    horizon. Joint train+test exogenous inside a forecast horizon is the shipped policy and
    stays; exogenous from AFTER the horizon is not the same thing. Every horizon now gets its
    own matrix. `make_features` costs about 0.2 s, so the cache is convenience, not necessity."""
    he = pd.Timestamp(horizon_end)
    gh = g.loc[g.index <= he]
    if feature_cache is None:
        return gh, fp.make_features(gh)
    if he not in feature_cache:
        feature_cache[he] = fp.make_features(gh)
    return gh, feature_cache[he]


def block_frame(g, block_rows):
    """`frame_at` keyed off the first row's horizon end. Kept for the session-26 scripts
    (`an48`-`an51`) that call it with a whole block and only ever score outer rows."""
    return frame_at(g, block_rows.horizon_end.iloc[0])


def train_mask_before(g, gh, y, origin):
    return (pd.Series((gh.is_test == 0).to_numpy(), index=gh.index)
            & y.reindex(gh.index).notna() & (gh.index <= origin))


def solve(level, idx, terms):
    """min ||z - level||^2 + sum lam ||M z - t||^2 for pre-computed (M, t, lam) triples."""
    A = identity(len(level), format='csc')
    rhs = np.asarray(level, float).copy()
    for M, t, lam in terms:
        if M is None:
            continue
        A = (A + lam * (M.T @ M)).tocsc()
        rhs = rhs + lam * (M.T @ t)
    z = spsolve(A, rhs)
    assert np.max(np.abs(A @ z - rhs)) < 1e-7 and np.isfinite(z).all()
    return np.clip(z, 5, 100)


def increment_terms(F, idx, inc, gains=None, deshrink=0.0):
    """The two frozen difference terms, with the predicted change optionally rescaled about
    its own mean. `gains` is the session-26 calibration knob (one multiplier per horizon,
    fitted on inner folds); `deshrink` is section 176's factor at the given strength. They are
    different mechanisms and are reported separately even though they act on the same vector."""
    cols, phys = inc.get('cols', fp.INC_COLS), inc.get('physics', False)
    lags = inc.get('lags', False)     # session 28; absent on every pre-s28 inc dict, so False
    out = []
    for h, lam in fp.INC_SPEC:
        D, st = fp.diff_operator(idx, h)
        if D is None:
            out.append((None, None, lam))
            continue
        X = fp.increment_design(F, h, cols, phys, lags).loc[st]
        t = np.mean([m.predict(X) for m in inc[h]], axis=0)
        f = 1.0
        if deshrink and ('f', h) in inc:
            f *= 1.0 + deshrink * (inc[('f', h)] - 1.0)
        if gains:
            f *= float(gains.get(h, 1.0))
        if f != 1.0:
            t = t.mean() + (t - t.mean()) * f
        out.append((D, t, lam))
    return out


def score_config(g, y, cache, physics, deshrink, seeds=SEEDS_INC, gains=None,
                 scopes=('outer',), inc_builder=None, term_builder=None, feature_cache=None):
    """Reconcile every cached block under one configuration and return per-row predictions.

    One feature matrix per (block, scope, fold), truncated at that group's own horizon end --
    see `frame_at`. Increments are refitted at each origin, so an inner fold's dynamics are
    learned from its own past and applied inside its own horizon."""
    feats = {} if feature_cache is None else feature_cache
    res = []
    for name, rows in cache.groupby('block', sort=False):
        for scope, fold in sorted(set(zip(rows.scope, rows.fold))):
            if scope not in scopes:
                continue
            d = rows.loc[(rows.scope == scope) & (rows.fold == fold)].sort_values('datetime')
            gh, F = frame_at(g, d.horizon_end.iloc[0], feats)
            yh = y.reindex(gh.index)
            idx = pd.DatetimeIndex(d.datetime)
            origin = pd.Timestamp(d.origin.iloc[0])
            mask = train_mask_before(g, gh, y, origin)
            inc = (inc_builder(F, yh, mask, seeds) if inc_builder else
                   fp.fit_increments(F, yh, mask, seeds, physics=physics,
                                     deshrink=deshrink > 0))
            terms = (term_builder(F, idx, inc) if term_builder else
                     increment_terms(F, idx, inc, gains, deshrink))
            z = solve(d.level.to_numpy(), idx, terms)
            res.append(d.assign(recon=z))
    return pd.concat(res, ignore_index=True)


def report(P, label, ref=None):
    """Per-block RMSE plus the SSE-weighted pooled number over B1+B2 only."""
    P = P.loc[P.score]
    per = {b: (fp.rmse(d.y, d.recon), len(d)) for b, d in P.groupby('block')}
    prim = [b for b in PRIMARY_BLOCKS if b in per]
    pool = pooled([per[b][0] for b in prim], None, [per[b][1] for b in prim])
    row = dict(candidate=label, pooled=pool,
               **{b: per[b][0] for b in sorted(per)},
               n=int(sum(per[b][1] for b in prim)))
    if ref is not None:
        row['d_pooled'] = pool - ref['pooled']
        row['d_mse'] = pool ** 2 - ref['pooled'] ** 2
        for b in per:
            row['d_' + b] = per[b][0] - ref[b]
        row['promotable'] = bool(
            row['d_pooled'] <= -BAR['pooled_gain']
            and all(row.get('d_' + b, 0) < 0 for b in PRIMARY_BLOCKS if b in per)
            and row.get('d_B3_shift7d', 0) <= BAR['b3_tolerance'])
    return row


def bootstrap(P, Q, days=3, n=2000, seed=20260906):
    """Paired calendar-block bootstrap of the pooled MSE difference over B1+B2. Conditional on
    a search that has already happened many times on this calendar; it is a spread, not a
    selection-bias correction."""
    P, Q = P.loc[P.score], Q.loc[Q.score]
    k = P.merge(Q[['block', 'datetime', 'recon']], on=['block', 'datetime'],
                suffixes=('', '_q'))
    k = k.loc[k.block.isin(PRIMARY_BLOCKS)]
    key = (k.block.astype(str) + '|' +
           (pd.DatetimeIndex(k.datetime).normalize().astype('int64') //
            (days * 86400 * 10 ** 9)).astype(str))
    groups = [g.index.to_numpy() for _, g in k.groupby(key)]
    a = (k.recon - k.y).to_numpy() ** 2
    b = (k.recon_q - k.y).to_numpy() ** 2
    rng = np.random.default_rng(seed)
    draws = np.empty(n)
    for i in range(n):
        pick = np.concatenate([groups[j] for j in rng.integers(0, len(groups), len(groups))])
        draws[i] = b[pick].mean() - a[pick].mean()
    return dict(blocks=len(groups), mean=float(draws.mean()),
                lo=float(np.quantile(draws, 0.025)), hi=float(np.quantile(draws, 0.975)),
                p_worse=float((draws > 0).mean()))


def bootstrap_pair(P, Q, n=2000, seed=20260906):
    """The same paired bootstrap at both block lengths section 191's decision rule asks for.

    Three-day blocks give more groups and a narrower interval; seven-day blocks respect the
    longer weather episodes and give fewer. Reporting only the narrower one would be choosing
    the answer. `p_worse` is the share of resamples in which the candidate loses -- a property
    of THESE 30 days resampled, not a probability that the candidate loses on unseen data, and
    it is conditional on a search that has already run dozens of candidates over this calendar.
    Also reports the worst single calendar day, because a pooled gain carried by one day is a
    different object from one spread across the window."""
    out = {}
    for days in (3, 7):
        out['b%dd' % days] = bootstrap(P, Q, days=days, n=n, seed=seed)
    k = P.loc[P.score].merge(Q.loc[Q.score][['block', 'datetime', 'recon']],
                             on=['block', 'datetime'], suffixes=('', '_q'))
    k = k.loc[k.block.isin(PRIMARY_BLOCKS)]
    day = pd.DatetimeIndex(k.datetime).normalize()
    d = (((k.recon_q - k.y) ** 2) - ((k.recon - k.y) ** 2)).groupby(day).mean()
    out['worst_day'] = dict(date=str(d.idxmax().date()), d_mse=float(d.max()),
                            days_improved=int((d < 0).sum()), days=int(len(d)),
                            # drop the day the CANDIDATE wins hardest: if the pooled gain only
                            # survives with that day in, it is one day, not a mechanism
                            d_mse_excluding_best_day=float(d.drop(d.idxmin()).mean()))
    return out


# --------------------------------------------------------------------------------- driver

def manifest_config(train_feats_at_origin=False):
    """Everything that changes what the cache MEANS, in one dict. `load_cache` refuses a
    pickle whose manifest does not reproduce this exactly, so a run cannot silently score
    yesterday's cache under today's constants."""
    return dict(backbone=BACKBONE, models=list(fp.MODELS_L2),
                blend_shrink=fp.BLEND_SHRINK, seeds_oof=list(fp.SEEDS_OOF),
                seeds_fit=list(fp.SEEDS_FIT), seeds_inc=list(SEEDS_INC),
                inc_spec=[list(x) for x in fp.INC_SPEC],
                inc_deshrink=fp.INC_DESHRINK, deshrink_clip=list(fp.DESHRINK_CLIP),
                deshrink_folds=fp.DESHRINK_FOLDS,
                tod_bins=fp.TOD_BINS, tod_shrink=fp.TOD_SHRINK,
                harm_shrink=fp.HARM_SHRINK,
                inner=dict(val_days=8, step_days=2, score_tail_days=SCORE_TAIL_DAYS,
                           min_meta_rows=MIN_META_ROWS, min_meta_days=MIN_META_DAYS),
                train_features_at_origin=bool(train_feats_at_origin))


def code_hashes():
    return {'final_pipeline.py': md5(ROOT / 'final_pipeline.py'),
            'src/an36_increment_production.py': md5(ROOT / 'src' /
                                                    'an36_increment_production.py'),
            'src/an47_v21_forward_benchmark.py': md5(Path(__file__))}


# Session 28. A whole-file hash cannot tell "the level cache means something different now" from
# "a reporting helper was renamed", and both of those happened in session 27 -- once costing a
# 16-minute rebuild to prove a byte-identical result. The functions below are the ones the level
# cache is actually built out of. Their source is fingerprinted separately and checked strictly;
# the file hashes stay in the manifest but become informational, because a file can change for
# reasons the cache does not care about. Adding a function here is a deliberate act: if it can
# change a cached level, it belongs in the list.
BUILD_PATH = (
    ('fp', ('es', 'load_grid', 'hampel', 'clean_exog', 'build_features', 'make_features',
            'tmin_block', 'tend_block', 'ordstat_block', 'qblock', 'low_support',
            'no_pressure', 'stable_core', 'drop_soil', 'base_model', 'predict', '_pipe',
            'tod_blend_weights', 'apply_tod_blend', 'harm_bias', 'apply_harm_bias')),
    ('a36', ('member_preds', 'stack', 'inner_origins')),
    ('a47', ('member_preds', 'stack_on', 'stack_fallback', 'meta_prior', 'frame_at',
             'blocks_of', 'build_block', '_days')),
)


def build_fingerprint():
    """md5 of the source of every function the level build calls, plus the constants it reads."""
    import inspect
    mods = {'fp': fp, 'a36': a36, 'a47': sys.modules[__name__]}
    out = {}
    for tag, names in BUILD_PATH:
        for n in names:
            fn = getattr(mods[tag], n, None)
            if fn is None:
                out['%s.%s' % (tag, n)] = 'MISSING'
                continue
            out['%s.%s' % (tag, n)] = hashlib.md5(
                inspect.getsource(fn).encode('utf-8')).hexdigest()
    out['constants'] = hashlib.md5(json.dumps(
        dict(models=list(fp.MODELS_L2), blend_shrink=fp.BLEND_SHRINK,
             seeds_oof=list(fp.SEEDS_OOF), seeds_fit=list(fp.SEEDS_FIT),
             tod_bins=fp.TOD_BINS, tod_shrink=fp.TOD_SHRINK, harm_shrink=fp.HARM_SHRINK,
             tmin_wins=list(fp.TMIN_WINS), support_bar=fp.SUPPORT_BAR,
             fast=list(fp.FAST), soil=list(fp.SOIL), daily=list(fp.DAILY),
             cumul=list(fp.CUMUL), target=fp.TARGET,
             min_meta_rows=MIN_META_ROWS, min_meta_days=MIN_META_DAYS,
             score_tail_days=SCORE_TAIL_DAYS, hold_days=HOLD_DAYS),
        sort_keys=True).encode('utf-8')).hexdigest()
    return out


def input_hashes():
    return {f: md5(ROOT / 'Dataset' / f)
            for f in ('train.csv', 'test.csv', 'sample_submission.csv')}


def load_cache(cache_path=None, manifest_path=None, train_feats_at_origin=False, strict=True):
    """Load a forward cache only if its manifest still describes the code, the inputs and the
    constants in force right now.

    Session 26's loader read whatever pickle was on disk and printed its md5. That is a receipt,
    not a check: `--train-features-at-origin` without `--rebuild` quietly scored the joint-feature
    cache under the strict label, and any edit to `final_pipeline.py` silently changed the
    meaning of every cached level. The mismatch is now an error naming the field that moved."""
    cache_path = Path(cache_path or CACHE)
    manifest_path = Path(manifest_path or MANIFEST)
    if not cache_path.exists():
        raise FileNotFoundError('%s does not exist; run with --rebuild' % cache_path)
    if not manifest_path.exists():
        raise FileNotFoundError('%s has no manifest beside it; run with --rebuild' % cache_path)
    man = json.loads(manifest_path.read_text())
    bad, soft = [], []
    if man.get('cache_md5') != md5(cache_path):
        bad.append('cache_md5: the pickle is not the one this manifest was written for')
    # Build path: strict. These functions decide what a cached level MEANS.
    stored_build = man.get('build_code')
    if stored_build is None:
        soft.append('build_code: manifest predates the session-28 fingerprint; only the file '
                    'hashes below were checked')
    else:
        for k, v in build_fingerprint().items():
            if stored_build.get(k) != v:
                bad.append('build_code[%s]: %s on disk, %s in manifest'
                           % (k, v[:8], str(stored_build.get(k))[:8]))
    # Whole files: informational once the build path is pinned, because a file changes for
    # reasons the cache does not care about -- a new flag, a renamed reporting helper.
    for k, v in code_hashes().items():
        if man.get('code', {}).get(k) != v:
            msg = ('code[%s]: %s on disk, %s in manifest'
                   % (k, v[:8], str(man.get('code', {}).get(k))[:8]))
            (soft if stored_build is not None else bad).append(msg)
    for k, v in input_hashes().items():
        if man.get('inputs', {}).get(k) != v:
            bad.append('inputs[%s]: %s on disk, %s in manifest'
                       % (k, v[:8], str(man.get('inputs', {}).get(k))[:8]))
    want = manifest_config(train_feats_at_origin)
    have = man.get('config', {})
    for k, v in want.items():
        if have.get(k) != v:
            bad.append('config[%s]: %r requested, %r cached' % (k, v, have.get(k)))
    if bad and strict:
        raise ValueError('cache %s does not match the current run:\n  %s\nRebuild it, or point '
                         '--namespace at a different folder.' % (cache_path, '\n  '.join(bad)))
    if bad:
        print('WARNING: manifest mismatch on %s:\n  %s' % (cache_path, '\n  '.join(bad)))
    for s in soft:
        print('  note: %s' % s)
    cache = pd.read_pickle(cache_path)
    print('loaded %s: %d rows, md5 %s, build path verified' % (cache_path.name, len(cache),
                                                               md5(cache_path)))
    return cache


def build(train_feats_at_origin=False, out=None):
    out = Path(out or OUT)
    cache_path, manifest_path = out / 'forward_predictions.pkl', out / 'manifest.json'
    out.mkdir(parents=True, exist_ok=True)
    g = fp.load_grid()
    y = g[fp.TARGET]
    t0 = time.time()
    parts, feats = [], {}
    for name, hs, he in blocks_of(g):
        print('\n%s  origin %s  horizon ends %s' % (name, hs, he), flush=True)
        parts.append(build_block(g, y, name, hs, he, train_feats_at_origin,
                                 feature_cache=feats))
    cache = pd.concat(parts, ignore_index=True)
    cache.to_pickle(cache_path)

    F = fp.make_features(g)
    man = dict(
        created=pd.Timestamp.now().isoformat(timespec='seconds'),
        seconds=round(time.time() - t0, 1),
        inputs=input_hashes(),
        code=code_hashes(),
        build_code=build_fingerprint(),
        blocks=[dict(name=n, origin=str(a), horizon_end=str(b)) for n, a, b in blocks_of(g)],
        primary_blocks=list(PRIMARY_BLOCKS), bar=BAR,
        config=manifest_config(train_feats_at_origin),
        feature_columns=list(F.columns),
        rows=dict(total=int(len(cache)),
                  outer=int((cache.scope == 'outer').sum()),
                  inner_scored=int(((cache.scope == 'inner') & cache.score).sum()),
                  inner_fallback_folds=int(cache.loc[cache.scope == 'inner']
                                           .groupby(['block', 'fold']).meta_fallback
                                           .first().sum()),
                  calibration_days=_days(cache.loc[(cache.scope == 'inner') & cache.score,
                                                   'datetime'])),
        cache_md5=md5(cache_path))
    manifest_path.write_text(json.dumps(man, indent=2))
    print('\nwrote %s (%d rows) and %s' % (cache_path, len(cache), manifest_path.name))
    return cache


def controls(g, y, cache):
    """Tahap 1: the three shipped configurations, all at five increment seeds."""
    specs = [('v21_increment', dict(physics=False, deshrink=0.0)),
             ('v21_physics', dict(physics=True, deshrink=0.0)),
             ('v21_physics_deshrink_half', dict(physics=True, deshrink=fp.INC_DESHRINK)),
             ('v21_physics_deshrink_full', dict(physics=True, deshrink=1.0))]
    preds, rows, ref = {}, [], None
    base = cache.loc[cache.scope == 'outer'].assign(recon=lambda d: d.level)
    rows.append(report(base, 'level_only'))
    for label, kw in specs:
        t = time.time()
        P = score_config(g, y, cache, **kw)
        preds[label] = P
        r = report(P, label, ref)
        if ref is None:
            ref = r
        rows.append(r)
        print('  %-26s pooled %.5f  (%.0f s)' % (label, r['pooled'], time.time() - t),
              flush=True)
    R = pd.DataFrame(rows)
    for label in ('v21_physics', 'v21_physics_deshrink_half'):
        bs = bootstrap(preds['v21_increment'], preds[label])
        print('  bootstrap %s vs v21_increment: dMSE %+.4f [%+.4f, %+.4f] over %d blocks'
              % (label, bs['mean'], bs['lo'], bs['hi'], bs['blocks']))
        R.loc[R.candidate == label, 'boot_dmse'] = bs['mean']
        R.loc[R.candidate == label, 'boot_lo'] = bs['lo']
        R.loc[R.candidate == label, 'boot_hi'] = bs['hi']
    return R, preds


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--rebuild', action='store_true', help='refit the level cache')
    ap.add_argument('--train-features-at-origin', action='store_true',
                    help='ablation: build training features from a grid stopped at the origin')
    ap.add_argument('--controls', action='store_true', help='run the Tahap 1 control scoring')
    ap.add_argument('--namespace', default='s27', choices=('s26', 's27'),
                    help='output folder: s26 is the frozen session-26 cache, s27 the rebuild')
    a = ap.parse_args()

    out = OUT if a.namespace == 's26' else OUT_S27
    cache_path, manifest_path = out / 'forward_predictions.pkl', out / 'manifest.json'
    if a.rebuild or not cache_path.exists():
        cache = build(a.train_features_at_origin, out)
    else:
        cache = load_cache(cache_path, manifest_path, a.train_features_at_origin)

    if a.controls:
        g = fp.load_grid()
        R, _ = controls(g, g[fp.TARGET], cache)
        R.to_csv(out / 'controls.csv', index=False)
        print('\n' + R.to_string(index=False))
        (out / 'controls.json').write_text(R.to_json(orient='records', indent=2))


if __name__ == '__main__':
    main()
