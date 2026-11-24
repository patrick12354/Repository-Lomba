"""Session 27, Tahap C, mechanism 1: how much each blend member should contribute to the LEVEL,
judged after the reconciliation instead of before it.

Every experiment in sections 180-189 froze the level prediction `p` and changed the increment
side -- different learners, different gains, a spline, an anchor. None of them asked whether `p`
itself is the right combination for the loss that is actually reported, which is measured on `z`,
not on `p`.

The reconciliation is linear in the level. With `A = I + sum_h lam_h D_h' D_h` and
`b = sum_h lam_h D_h' d_h`,

    z = A^-1 (p + b),

so replacing the incumbent `p0` by `p_theta = (1 - sum theta_j) p0 + sum_j theta_j p_j` moves the
answer along fixed directions that can be computed once per origin:

    u_j = A^-1 (p_j - p0),      z(theta) = z0 + sum_j theta_j u_j     (before the final clip).

The blend weights inside `p0` were chosen by NNLS against the LEVEL, before `A^-1` was applied.
`A^-1` is a smoother: it damps the high-frequency part of a member's disagreement with the blend
and passes the low-frequency part. A member that loses on raw level RMSE can still carry a
component that survives that operator usefully, and nothing in this log has tested it.

**Protocol, frozen before the run.**

* Two directions only, one per family: the L2-loss tree `l2`, and whichever of the three
  linear/vapour members has the steepest inner descent direction. Chosen on inner rows.
* `theta_j >= 0` and `sum theta_j <= 0.25`, the constraint frozen rather than swept. `p0` keeps
  at least three quarters of the weight and all of its time-of-day and harmonic structure.
* Fitted per block on that block's own inner calibration rows, which under the section-190
  contract are the only rows before that block's origin that are legitimately forward.
* A chronological transfer gate first: fit on the earlier inner origins, score on the later
  ones. If theta does not transfer across episodes, it is set to zero and the mechanism is
  closed without looking at an outer row.
* The fitted vector then ships at half strength, the same 0.5 this log applies to every
  correction it does not fully trust.

**The result to expect before running it.** Under the repaired contract B2 has one usable inner
origin and 96 calibration rows, so it cannot fit anything and takes theta = 0 by rule. The
section-180 bar needs BOTH primary blocks to improve. Any mechanism whose parameters are fitted
on inner calibration data is therefore structurally unable to clear that bar on this calendar --
which is a fact about the calendar, not about this mechanism, and is worth stating once here
rather than rediscovering it per candidate.

    .venv/Scripts/python.exe src/an54_v21_level_contributions.py
"""
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.sparse import identity
from scipy.sparse.linalg import factorized

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'src'))
import final_pipeline as fp
import an47_v21_forward_benchmark as a47

OUT = a47.OUT_S27
TREE_DIR = 'l2'                        # the L2-loss tree, the one member fitted to the metric
LINEAR_POOL = ('ridge', 'enet', 'ridge_e')
THETA_CAP = 0.25                       # frozen, not swept
SHIP_STRENGTH = 0.5                    # the log's standing half-strength convention
MIN_CAL_ROWS = 192                     # 4 days; below this a block does not fit theta at all
MIN_TRANSFER_ORIGINS = 4               # need at least 2 fit and 2 score origins to gate on


def basis(level, members, idx, terms):
    """`z0` and one column `u_j = A^-1 (p_j - p0)` per member, all from one factorisation.

    Returns the UNCLIPPED `z0`; the clip is applied by `apply_theta` after the directions are
    combined, because `clip(z0) + theta u` is not `clip(z0 + theta u)` and the second is what
    the solver would produce."""
    A = identity(len(level), format='csc')
    rhs = np.asarray(level, float).copy()
    for M, t, lam in terms:
        if M is None:
            continue
        A = (A + lam * (M.T @ M)).tocsc()
        rhs = rhs + lam * (M.T @ t)
    lu = factorized(A.tocsc())
    z0 = lu(rhs)
    U = np.column_stack([lu(np.asarray(members[m], float) - np.asarray(level, float))
                         for m in members])
    return z0, U, list(members)


def apply_theta(z0, U, theta):
    return np.clip(z0 + U @ np.asarray(theta, float), 5, 100)


def fit_theta(folds, cols, cap=THETA_CAP):
    """Least squares in theta over the pooled scored rows of `folds`, subject to theta >= 0 and
    sum theta <= cap. Two parameters, so SLSQP from zero is exact enough and the clip is carried
    inside the objective rather than linearised away."""
    z0 = np.concatenate([f['z0'] for f in folds])
    U = np.vstack([f['U'][:, [f['cols'].index(c) for c in cols]] for f in folds])
    y = np.concatenate([f['y'] for f in folds])

    def sse(th):
        return float(np.sum((apply_theta(z0, U, th) - y) ** 2)) / len(y)

    r = minimize(sse, np.zeros(len(cols)), method='SLSQP',
                 bounds=[(0.0, cap)] * len(cols),
                 constraints=[{'type': 'ineq', 'fun': lambda t: cap - t.sum()}],
                 options=dict(maxiter=200, ftol=1e-10))
    th = np.clip(r.x, 0.0, cap)
    if th.sum() > cap:
        th = th * cap / th.sum()
    return th, dict(sse0=sse(np.zeros(len(cols))), sse=sse(th), success=bool(r.success))


def pick_linear(folds):
    """Steepest inner descent direction among the linear/vapour members at theta = 0.

    d/dtheta_j of the inner SSE at zero is 2 * sum (z0 - y) . u_j, so the most negative value is
    the direction the inner rows most want to move in. Inner only, and it selects one of three
    rather than searching a space."""
    grads = {}
    for m in LINEAR_POOL:
        gr = 0.0
        for f in folds:
            j = f['cols'].index(m)
            gr += 2.0 * float((f['z0'] - f['y']) @ f['U'][:, j])
        grads[m] = gr
    return min(grads, key=grads.get), grads


def build_folds(g, y, cache, seeds, scopes=('outer', 'inner')):
    """One record per (block, scope, fold) carrying the basis, the labels and the scored mask."""
    feats, out = {}, []
    for name, blk in cache.groupby('block', sort=False):
        members = [c[2:] for c in cache.columns if c.startswith('m_')]
        for scope, fold in sorted(set(zip(blk.scope, blk.fold))):
            if scope not in scopes:
                continue
            d = blk.loc[(blk.scope == scope) & (blk.fold == fold)].sort_values('datetime')
            if scope == 'inner' and not d.score.any():
                continue
            gh, F = a47.frame_at(g, d.horizon_end.iloc[0], feats)
            idx = pd.DatetimeIndex(d.datetime)
            origin = pd.Timestamp(d.origin.iloc[0])
            mask = a47.train_mask_before(g, gh, y, origin)
            inc = fp.fit_increments(F, y.reindex(gh.index), mask, seeds, physics=True,
                                    deshrink=True)
            terms = a47.increment_terms(F, idx, inc, None, fp.INC_DESHRINK)
            z0, U, cols = basis(d.level.to_numpy(),
                                {m: d['m_' + m].to_numpy() for m in members}, idx, terms)
            s = d.score.to_numpy()
            out.append(dict(block=name, scope=scope, fold=int(fold), origin=origin,
                            datetime=idx[s], z0=z0[s], U=U[s], cols=cols,
                            y=d.y.to_numpy()[s], level=d.level.to_numpy()[s],
                            n=int(s.sum())))
            print('  %-11s %-5s fold %2d  n=%4d  origin %s' % (name, scope, fold, int(s.sum()),
                                                               origin.date()), flush=True)
    return out


def transfer_gate(inner, cols):
    """Fit theta on the earlier half of a block's inner origins, score it on the later half.

    A theta that only fits the episodes it was fitted on is a theta that will not survive the
    move to the outer window either. The gate is per block; a block with too few origins to
    split does not get a verdict and does not get a theta."""
    rows = []
    for b in sorted({f['block'] for f in inner}):
        fs = sorted([f for f in inner if f['block'] == b], key=lambda f: f['origin'])
        if len(fs) < MIN_TRANSFER_ORIGINS:
            rows.append(dict(block=b, origins=len(fs), verdict='too few origins to gate',
                             theta=None, d_sse=np.nan))
            continue
        k = len(fs) // 2
        th, _ = fit_theta(fs[:k], cols)
        z0 = np.concatenate([f['z0'] for f in fs[k:]])
        U = np.vstack([f['U'][:, [f['cols'].index(c) for c in cols]] for f in fs[k:]])
        yv = np.concatenate([f['y'] for f in fs[k:]])
        base = float(np.sum((np.clip(z0, 5, 100) - yv) ** 2))
        got = float(np.sum((apply_theta(z0, U, th) - yv) ** 2))
        rows.append(dict(block=b, origins=len(fs), fit_origins=k, score_rows=len(yv),
                         theta=[float(x) for x in th],
                         rmse_zero=float(np.sqrt(base / len(yv))),
                         rmse_theta=float(np.sqrt(got / len(yv))),
                         d_sse=got - base,
                         verdict='transfers' if got < base else 'does not transfer'))
    return pd.DataFrame(rows)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    g = fp.load_grid()
    y = g[fp.TARGET]
    cache = a47.load_cache(a47.CACHE_S27, a47.MANIFEST_S27)
    seeds = a47.SEEDS_INC

    t0 = time.time()
    folds = build_folds(g, y, cache, seeds)
    inner = [f for f in folds if f['scope'] == 'inner']
    outer = [f for f in folds if f['scope'] == 'outer']
    print('  [%d folds, basis built in %.0f s]' % (len(folds), time.time() - t0), flush=True)

    lin, grads = pick_linear(inner)
    cols = [TREE_DIR, lin]
    print('\ndirections: %s (frozen) and %s (steepest inner descent among %s)'
          % (TREE_DIR, lin, ', '.join(LINEAR_POOL)))
    print('  inner gradients at theta=0: ' +
          '  '.join('%s %+.1f' % (k, v) for k, v in sorted(grads.items(), key=lambda x: x[1])))

    gate = transfer_gate(inner, cols)
    print('\nchronological transfer gate on inner origins\n' + gate.to_string(index=False))

    verdicts = set(gate.verdict)
    passed = gate.loc[gate.verdict == 'transfers']
    rows, per_block = [], {}
    for b in sorted({f['block'] for f in outer}):
        cal = [f for f in inner if f['block'] == b]
        n = sum(f['n'] for f in cal)
        g_row = gate.loc[gate.block == b]
        ok = (n >= MIN_CAL_ROWS and len(g_row) and g_row.verdict.iloc[0] == 'transfers')
        if not ok:
            per_block[b] = dict(theta=[0.0] * len(cols), reason=(
                'calibration rows %d < %d' % (n, MIN_CAL_ROWS) if n < MIN_CAL_ROWS else
                'gate: %s' % (g_row.verdict.iloc[0] if len(g_row) else 'no gate')))
            continue
        th, info = fit_theta(cal, cols)
        per_block[b] = dict(theta=[float(x) for x in th * SHIP_STRENGTH],
                            theta_unshrunk=[float(x) for x in th],
                            calibration_rows=n, reason='fitted', **info)

    print('\nper-block theta after the gate and the half-strength shrink')
    for b, v in per_block.items():
        print('  %-11s theta %s  (%s)' % (b, np.round(v['theta'], 4), v['reason']))

    # ---- score: incumbent vs the theta the protocol actually authorises ------------------
    for label, use in (('incumbent_theta0', False), ('level_contributions', True)):
        parts = []
        for f in outer:
            th = np.array(per_block[f['block']]['theta']) if use else np.zeros(len(cols))
            U = f['U'][:, [f['cols'].index(c) for c in cols]]
            parts.append(pd.DataFrame(dict(block=f['block'], datetime=f['datetime'],
                                           y=f['y'], score=True,
                                           recon=apply_theta(f['z0'], U, th))))
        P = pd.concat(parts, ignore_index=True)
        r = a47.report(P, label, rows[0] if rows else None)
        rows.append(r)
        if label == 'incumbent_theta0':
            base_P = P
        else:
            cand_P = P
        print('  %-22s pooled %.5f' % (label, r['pooled']))

    R = pd.DataFrame(rows)
    if not np.allclose([sum(v['theta']) for v in per_block.values()], 0):
        bs = a47.bootstrap(base_P, cand_P)
        print('  bootstrap dMSE %+.4f [%+.4f, %+.4f] over %d blocks'
              % (bs['mean'], bs['lo'], bs['hi'], bs['blocks']))
        for k in ('mean', 'lo', 'hi', 'p_worse'):
            R.loc[R.candidate == 'level_contributions', 'boot_' + k] = bs[k]
    else:
        print('  every block took theta = 0; the candidate IS the incumbent, nothing to test')

    base_P.to_pickle(OUT / 'preds_theta0.pkl')
    cand_P.to_pickle(OUT / 'preds_level_contributions.pkl')
    R.to_csv(OUT / 'level_contributions.csv', index=False)
    gate.to_csv(OUT / 'level_contributions_gate.csv', index=False)
    (OUT / 'level_contributions.json').write_text(json.dumps(dict(
        directions=cols, inner_gradients=grads, theta_cap=THETA_CAP,
        ship_strength=SHIP_STRENGTH, min_calibration_rows=MIN_CAL_ROWS,
        per_block=per_block, gate=json.loads(gate.to_json(orient='records')),
        results=json.loads(R.to_json(orient='records'))), indent=2, default=str))
    print('\n' + R.to_string(index=False))


if __name__ == '__main__':
    main()
