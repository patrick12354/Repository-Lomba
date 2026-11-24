"""Session 30, P2: a level correction built from the SLOW part of member disagreement.

Section 215 measured that 40-42% of v21's remaining MSE is a per-calendar-day bias, and that
reconciliation almost entirely attacks the within-day part. Sections 158 and 163 tried to reach
that bias with a smoothed-level term and with daily Ridge models on exogenous aggregates, and
both failed. This is a different source of information, and the difference is the whole
hypothesis.

**Correction, section 225.** This docstring originally justified the target by saying `D 1 = 0`
leaves the increment terms unable to speak about a constant, and treated the whole 40% as out of
their reach. That is too strong. What an increment cannot move is the mean per CONNECTED
COMPONENT of the difference graph, and every holdout here has exactly one component -- 2.44% of
SSE on the 15-day blocks, not 40%. Slow modes are heavily damped rather than unreachable: at
eigenvalue 0.085 the solver passes 7.83% of a proposed increment path but 92.17% of a change in
the level. The conclusion that a LEVEL correction has the more direct route survives; the
arithmetic offered for it did not.

**Hypothesis.** When the thermal-linear members and the tree members disagree about the LEVEL and
keep disagreeing for hours, that persistent disagreement may carry the sign of the error rather
than merely its uncertainty. Fast disagreement is noise between two fits; slow disagreement is
two models reading the regime differently. The model has to earn this: predicting sign and
magnitude of the residual is the claim, and disagreement on its own is not evidence.

**Construction, frozen before fitting.**

1. Five contrasts `m_j - level` from the OOF member predictions -- hbt, cat, ridge, enet,
   ridge_e. `l2` is excluded on this round because section 98 measured its residual correlation
   with `hbt` at 0.950; it is nearly a duplicate direction, and it is not re-chosen from outer.
2. Each contrast is smoothed with a centred 49-point rolling mean, 24 hours, reindexed onto a
   complete 30-minute grid and computed INSIDE its own forecast window with `min_periods=1`.
   It never crosses an origin and never reads a label. Member predictions for a forecast window
   are available at inference, so this is computable when it matters.
3. `u_j = A^-1 b_j` with the same operator the v21 reconciliation uses, so the correction is
   `z_new = z_v21 + U beta` exactly, before clipping.
4. Ridge without intercept on the OOF residual `y - z_v21`, standardised without centring so the
   correction stays a pure `U beta`. Alpha grid frozen at {10, 100, 1000}; **beta = 0 is a
   candidate in the same selection and wins ties**, so a family with no forward signal returns
   the incumbent rather than a shrunken version of itself.
5. Every origin's coefficients use only labels and OOF predictions whose entire construction
   precedes that origin, one calibration prediction per timestamp, latest eligible forecast.
6. Forward selection runs one split per calibration FORECAST, in origin order: split k trains on
   what was available at forecast k's origin and validates on forecast k's own rows -- see
   `eligible_at` and `origin_splits`. Below that, beta = 0 and a recorded fallback. A fallback is
   a limit of the available design, not a measurement of the predictor, and is reported
   separately so pooled numbers cannot hide it.

   Session 31 replaced an earlier rule here that split calibration TIMESTAMPS into three
   chronological chunks. That ordered the targets and said nothing about availability; section
   224 measured the consequence. The verdict below is unchanged under the repair.

Training uses pre-clip `z` so the linear identity is exact; scoring clips exactly as production
does.

    .venv/Scripts/python.exe src/an70_v21_slow_member_correction.py
"""
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.sparse import identity
from scipy.sparse.linalg import factorized
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
import final_pipeline as fp
import an47_v21_forward_benchmark as a47
import an59_v21_candidate_contract as c

OUT = ROOT / 'outputs' / 'audit_v21_s30'
CONTRASTS = ('hbt', 'cat', 'ridge', 'enet', 'ridge_e')   # l2 excluded: 0.950 corr with hbt
SMOOTH_POINTS = 49                                       # 24 h, centred
ALPHAS = (10.0, 100.0, 1000.0)
MIN_CHUNKS, MIN_TIMESTAMPS = 3, 96
SELECTION_MARGIN = 0.01      # a non-zero alpha must beat zero by 1% of its forward SSE
ANCHOR = 'v21'


def slow_contrasts(idx, level, members, points=SMOOTH_POINTS):
    """Centred 24-hour means of `m_j - level`, computed on a complete 30-minute grid spanning
    THIS forecast window only. Never crosses an origin; never touches a label."""
    idx = pd.DatetimeIndex(idx)
    full = pd.date_range(idx.min(), idx.max(), freq='30min')
    cols = []
    for m in CONTRASTS:
        raw = pd.Series(np.asarray(members[m], float) - np.asarray(level, float), index=idx)
        sm = raw.reindex(full).rolling(points, center=True, min_periods=1).mean()
        cols.append(sm.reindex(idx).to_numpy())
    return np.column_stack(cols)


def pieces(g, y, d, seeds, feats):
    """Everything one forecast window contributes: the v21 operator, its pre-clip solution, the
    slow contrast basis and its image under A^-1."""
    d = d.sort_values('datetime')
    idx = pd.DatetimeIndex(d.datetime)
    gh, F = a47.frame_at(g, d.horizon_end.iloc[0], feats)
    origin = pd.Timestamp(d.origin.iloc[0])
    mask = a47.train_mask_before(g, gh, y, origin)
    inc = fp.fit_increments(F, y.reindex(gh.index), mask, seeds, physics=False, deshrink=False)
    terms = a47.increment_terms(F, idx, inc, None, 0.0)

    level = d.level.to_numpy()
    A = identity(len(level), format='csc')
    rhs = level.astype(float).copy()
    for M, t, lam in terms:
        if M is None:
            continue
        A = (A + lam * (M.T @ M)).tocsc()
        rhs = rhs + lam * (M.T @ t)
    lu = factorized(A.tocsc())
    z_pre = lu(rhs)
    B = slow_contrasts(idx, level, {m: d['m_' + m].to_numpy() for m in CONTRASTS})
    U = np.column_stack([lu(B[:, j]) for j in range(B.shape[1])])
    return dict(idx=idx, y=d.y.to_numpy(), level=level, z_pre=z_pre,
                z=np.clip(z_pre, 5, 100), U=U, origin=origin, block=d.block.iloc[0])


def fit_beta(U, resid, alpha):
    model = make_pipeline(StandardScaler(with_mean=False),
                          Ridge(alpha=alpha, fit_intercept=False))
    return model.fit(U, resid)


def select_alpha(chunks):
    """Forward chronological selection inside the calibration set. Zero is a competitor and must
    be BEATEN BY A MARGIN, not merely tied.

    Three alphas racing a zero candidate on one forward sum will beat it by chance a fair share
    of the time: on pure Gaussian noise the best alpha won by 0.056% of the zero SSE, while a
    planted direction won by 99.75%. Three orders of magnitude separate them, so a 1% relative
    margin rejects the first and admits the second with room to spare. The threshold was chosen
    on synthetic data before this arm was ever run on a real fold, and it only ever makes the
    rule more conservative -- a correction that cannot clear 1% forward is one this log has no
    business shipping."""
    table = []
    for alpha in (None,) + ALPHAS:
        sse = 0.0
        for sp in chunks:
            # Each split carries its OWN training side, assembled from what was available at
            # that split's origin. Nothing is accumulated across splits here, because "the
            # earlier chunks" is exactly the notion of availability that was wrong before.
            if alpha is None:
                pred = np.zeros(len(sp['val_r']))
            else:
                pred = fit_beta(sp['train_U'], sp['train_r'], alpha).predict(sp['val_U'])
            sse += float(np.sum((sp['val_r'] - pred) ** 2))
        table.append(dict(alpha=alpha, sse=sse))
    zero = [t['sse'] for t in table if t['alpha'] is None][0]
    best = min((t for t in table if t['alpha'] is not None), key=lambda x: x['sse'])
    gain = (zero - best['sse']) / zero if zero > 0 else 0.0
    for t in table:
        t['relative_gain_vs_zero'] = ((zero - t['sse']) / zero) if zero > 0 else 0.0
    return (best['alpha'] if gain >= SELECTION_MARGIN else None), table


def eligible_at(parts, origin):
    """Calibration records a forecaster standing at `origin` could actually hold.

    A record is admissible only if its TARGET timestamp is at or before the origin -- that is
    when its label exists -- and the forecast that produced it was itself launched at or before
    the origin. Records are then de-duplicated per timestamp, keeping the most recent eligible
    forecast.

    This replaces a timestamp-slice split that ordered targets correctly but not availability.
    Section 224 measured the gap it left: on B1 split 2 the validation predictions came from an
    origin of 6 August 14:30 while the calibrator had already read labels through 8 August
    14:30 -- 288 of 288 validation rows trained on labels from their own future. No outer or
    test label was ever read, so this is an availability mismatch rather than target leakage,
    but a forward selection that cannot be executed at the origin it claims is not a forward
    selection."""
    origin = pd.Timestamp(origin)
    frames = []
    for p in parts:
        keep = pd.DatetimeIndex(p['idx']) <= origin
        if not keep.any() or pd.Timestamp(p['origin']) > origin:
            continue
        frames.append(pd.DataFrame(dict(dt=pd.DatetimeIndex(p['idx'])[keep],
                                        origin=p['origin'],
                                        r=(p['y'] - p['z_pre'])[keep],
                                        **{'u%d' % j: p['U'][keep, j]
                                           for j in range(p['U'].shape[1])})))
    if not frames:
        return None
    D = pd.concat(frames, ignore_index=True).sort_values(['dt', 'origin'])
    return D.drop_duplicates(subset='dt', keep='last').sort_values('dt').reset_index(drop=True)


def origin_splits(parts):
    """One forward split per calibration forecast, in origin order.

    Split k trains on everything available at forecast k's origin and validates on forecast k's
    own rows. A split is usable only if the training side reaches MIN_TIMESTAMPS unique
    timestamps drawn from at least two distinct earlier forecasts, so a single window can never
    validate against itself."""
    ucols = ['u%d' % j for j in range(len(CONTRASTS))]
    out = []
    for p in sorted(parts, key=lambda q: pd.Timestamp(q['origin'])):
        train = eligible_at([q for q in parts if pd.Timestamp(q['origin'])
                             < pd.Timestamp(p['origin'])], p['origin'])
        if train is None or train.dt.nunique() < MIN_TIMESTAMPS or train.origin.nunique() < 2:
            continue
        out.append(dict(train_U=train[ucols].to_numpy(), train_r=train.r.to_numpy(),
                        val_U=p['U'], val_r=p['y'] - p['z_pre'],
                        origin=str(p['origin']), n_train=len(train),
                        n_val=len(p['y']), train_label_end=str(train.dt.max())))
    return out if len(out) >= MIN_CHUNKS - 1 else []


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    g = fp.load_grid()
    y = g[fp.TARGET]
    cache = a47.load_cache(a47.CACHE_S27, a47.MANIFEST_S27)
    seeds, feats = a47.SEEDS_INC, {}

    inner_parts, outer_parts = {}, {}
    t0 = time.time()
    for name, blk in cache.groupby('block', sort=False):
        inner_parts[name] = []
        for scope, fold in sorted(set(zip(blk.scope, blk.fold))):
            d = blk.loc[(blk.scope == scope) & (blk.fold == fold)]
            if scope == 'inner' and bool(d.meta_fallback.iloc[0]):
                continue                      # its level came from the frozen fallback stack
            p = pieces(g, y, d, seeds, feats)
            (outer_parts.setdefault(name, p) if scope == 'outer'
             else inner_parts[name].append(p))
        print('  %-11s calibration windows %d  (%.0f s)'
              % (name, len(inner_parts[name]), time.time() - t0), flush=True)

    rows, preds, prov = [], [], []
    for name, op in outer_parts.items():
        chunks = origin_splits(inner_parts[name])
        final = eligible_at(inner_parts[name], op['origin'])
        if not chunks or final is None:
            beta, alpha, reason = np.zeros(len(CONTRASTS)), None, 'insufficient calibration'
            table = []
        else:
            alpha, table = select_alpha(chunks)
            if alpha is None:
                beta, reason = np.zeros(len(CONTRASTS)), 'zero won the forward selection'
            else:
                # The shipped coefficients use everything available at the OUTER origin, which
                # is strictly more than any single split saw -- and still nothing after it.
                ucols = ['u%d' % j for j in range(len(CONTRASTS))]
                model = fit_beta(final[ucols].to_numpy(), final.r.to_numpy(), alpha)
                beta = model.predict(np.eye(len(CONTRASTS)))
                reason = 'fitted'
        corr = op['U'] @ beta if np.any(beta) else np.zeros(len(op['y']))
        znew = np.clip(op['z_pre'] + corr, 5, 100)
        preds.append(pd.DataFrame(dict(block=name, datetime=op['idx'], y=op['y'],
                                       score=True, recon=znew)))
        prov.append(dict(block=name, alpha=alpha, reason=reason,
                         chunks=len(chunks), beta=[float(b) for b in beta],
                         contrasts=list(CONTRASTS),
                         calibration=[{k: ch[k] for k in
                                       ('origin', 'n_train', 'n_val', 'train_label_end')}
                                      for ch in (chunks or [])],
                         selection=[{'alpha': t['alpha'], 'sse': t['sse'],
                    'relative_gain_vs_zero': t['relative_gain_vs_zero']} for t in table],
                         correction_rms=float(np.sqrt(np.mean(corr ** 2))),
                         base_rmse=fp.rmse(op['y'], op['z']),
                         new_rmse=fp.rmse(op['y'], znew)))
        print('  %-11s alpha %-6s %-28s correction RMS %.4f  %.6f -> %.6f'
              % (name, alpha, reason, prov[-1]['correction_rms'],
                 prov[-1]['base_rmse'], prov[-1]['new_rmse']), flush=True)

    base = pd.concat([pd.DataFrame(dict(block=n, datetime=p['idx'], y=p['y'], score=True,
                                        recon=p['z'])) for n, p in outer_parts.items()],
                     ignore_index=True)
    frozen = pd.read_pickle(a47.OUT_S27 / 'preds_v21_increment.pkl')
    j = c.join_predictions(frozen.loc[frozen.scope == 'outer'], base)
    np.testing.assert_allclose(j.recon, j.recon_q, atol=1e-9, rtol=0)
    print('\n  control reproduces the frozen v21 predictions exactly (%d rows)' % len(j))

    P = pd.concat(preds, ignore_index=True)
    ref = a47.report(base, ANCHOR)
    r = a47.report(P, 'slow_member_correction', ref)
    b = a47.bootstrap_pair(base, P)
    r['boot3_lo'], r['boot3_hi'] = b['b3d']['lo'], b['b3d']['hi']

    # Did it move the part of the error it targets, and at what cost to the rest?
    energy = []
    for label, Q in (('v21', base), ('slow_member_correction', P)):
        e = Q.recon - Q.y
        daily = e.groupby([Q.block, pd.DatetimeIndex(Q.datetime).floor('D')]).transform('mean')
        energy.append(dict(prediction=label, mse=float(np.mean(e ** 2)),
                           daily_bias_mse=float(np.mean(daily ** 2)),
                           within_day_mse=float(np.mean((e - daily) ** 2))))

    R = pd.DataFrame([ref, r])
    E = pd.DataFrame(energy)
    print('\n' + R.to_string(index=False))
    print('\nresidual energy decomposition\n' + E.to_string(index=False))

    R.to_csv(OUT / 'slow_member.csv', index=False)
    E.to_csv(OUT / 'slow_member_energy.csv', index=False)
    P.to_pickle(OUT / 'preds_slow_member.pkl')
    c.write_json(OUT / 'slow_member.json', dict(
        contrasts=list(CONTRASTS), smooth_points=SMOOTH_POINTS, alphas=list(ALPHAS),
        min_chunks=MIN_CHUNKS, min_timestamps=MIN_TIMESTAMPS, seeds=list(seeds),
        per_block=prov, results=json.loads(R.to_json(orient='records')),
        energy=json.loads(E.to_json(orient='records')), bootstrap=b,
        code={'src/an70_v21_slow_member_correction.py': a47.md5(Path(__file__))},
        level_cache_md5=a47.md5(a47.CACHE_S27)))
    print('\nwrote slow_member.csv to %s' % OUT)


if __name__ == '__main__':
    main()
