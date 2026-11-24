"""Session 26, Tahap 2: fit the increment vector to the loss that is actually scored, and
give each horizon the learner that is good at it.

Section 174 is the reason both of these exist. The three-learner average had the LOWEST
increment RMSE ever measured at both horizons and the WORST reconciled result of any candidate
-- so the intermediate objective the increment models are trained on is not the objective the
submission is graded on. Section 176 took one step from that observation (rescale `d` to the
dispersion the target has). This takes the other two.

**A. Two gains fitted on the final loss.** Instead of matching the dispersion of `d_h` to the
dispersion of the true change, choose `a_h` to minimise the SSE of `z` AFTER the solve:

    d'_h = mean(d_h) + a_h (d_h - mean(d_h)),   z = argmin ||z-p||^2 + sum_h lam_h ||D_h z - d'_h||^2

Two parameters, bounded to [0.80, 1.20], penalised toward 1, and fitted on forward inner folds
that end before the outer origin. This is not section 176 with a different constant: the
de-shrink factor is `sd(target)/sd(oof prediction)` measured on TRAINING pairs and knows nothing
about the solve, while `a_h` is the number that minimises the reconciled error and can come out
below 1 if the solve wants less amplitude, which the clipped de-shrink factor structurally
cannot. The penalty strength is chosen on an inner split of the inner folds, never on B1/B2/B3.

**B. One learner per horizon.** Section 174's own table has CatBoost beating LightGBM on the
30-minute increment on 3/3 blocks and losing at two hours; it was rejected because it was used
at BOTH horizons. The pairing was never tried. Same solve, same weights, only the estimator of
`d_1` changes.

PRE-REGISTERED, before any outer number is looked at:

  baseline    whatever Tahap 1 leaves standing, at five increment seeds
  candidates  gains; hybrid; hybrid+gains -- three, inside the four-configuration budget
  primary     pooled RMSE over B1+B2, sqrt(sum SSE / sum n), paired on identical rows
  secondary   per-block RMSE, B3, the 3-day paired calendar bootstrap of the pooled MSE
  bar         section 180: pooled better by >= 0.02, B1 AND B2 both better, B3 worse by <= 0.05

    .venv/Scripts/python.exe src/an48_v21_solver_loss.py
"""
import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import lightgbm as lgb
import catboost as cb
from scipy.sparse import identity
from scipy.sparse.linalg import splu

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'src'))
import final_pipeline as fp
import an47_v21_forward_benchmark as a47

OUT = ROOT / 'outputs' / 'audit_v21'
CAT_KW = dict(iterations=800, learning_rate=0.03, depth=6, l2_leaf_reg=6.0,
              loss_function='RMSE', verbose=0, allow_writing_files=False)
GAIN_GRID = np.round(np.arange(0.80, 1.2001, 0.02), 4)
PENALTIES = (0.0, 0.5, 2.0, 8.0, 32.0)     # MSE units per unit^2 of (a-1)
HYBRID = {1: 'cat', 4: 'lgb'}


def fit_one(name, X, tgt, seed):
    if name == 'lgb':
        return lgb.LGBMRegressor(random_state=seed, **fp.INC_KW).fit(X, tgt)
    if name == 'cat':
        return cb.CatBoostRegressor(random_seed=seed, **CAT_KW).fit(X, tgt)
    raise ValueError(name)


def build_increments(F, y, mask, seeds, physics=True, deshrink=False, learners=None):
    """`fp.fit_increments` with a per-horizon learner. Identical to the shipped function when
    `learners` is None or all-LightGBM -- checked in tests/test_v21_evaluation.py."""
    if learners is None:
        return fp.fit_increments(F, y, mask, seeds, physics=physics, deshrink=deshrink)
    cols = fp.INC_PHYS_COLS if physics else fp.INC_COLS
    out = {'physics': physics, 'cols': cols}
    for h, _ in fp.INC_SPEC:
        X = fp.inc_design(F, h, cols, physics)
        tgt = (y - y.shift(h)).reindex(X.index)
        m = mask.reindex(X.index, fill_value=False)
        m = m & tgt.notna() & m.shift(h, fill_value=False)
        name = learners.get(h, 'lgb')
        out[h] = [fit_one(name, X.loc[m], tgt.loc[m], s) for s in seeds]
        if deshrink:
            rows = X.index[m]
            oof = pd.Series(np.nan, index=rows)
            for cut in np.array_split(np.arange(len(rows)), fp.DESHRINK_FOLDS):
                va, trn = rows[cut], rows.difference(rows[cut])
                oof.loc[va] = np.asarray(fit_one(name, X.loc[trn], tgt.loc[trn],
                                                 fp.INC_SEED).predict(X.loc[va])).ravel()
            out[('f', h)] = float(np.clip(tgt.loc[rows].std() / oof.std(),
                                          *fp.DESHRINK_CLIP))
    return out


def raw_terms(g, y, cache, physics, deshrink, seeds, learners, scopes):
    """Every fold's solve inputs, with `d_h` NOT yet rescaled, so a gain can be applied later
    without refitting anything. Also carries the h=1/h=4 inconsistency diagnostic."""
    folds, diag = [], []
    for name, rows in cache.groupby('block', sort=False):
        gh, F = a47.block_frame(g, rows)
        yh = y.reindex(gh.index)
        for scope, fid in sorted(set(zip(rows.scope, rows.fold))):
            if scope not in scopes:
                continue
            d = rows.loc[(rows.scope == scope) & (rows.fold == fid)].sort_values('datetime')
            idx = pd.DatetimeIndex(d.datetime)
            origin = pd.Timestamp(d.origin.iloc[0])
            mask = a47.train_mask_before(g, gh, y, origin)
            inc = build_increments(F, yh, mask, seeds, physics, deshrink, learners)
            terms, preds = [], {}
            for h, lam in fp.INC_SPEC:
                D, st = fp.diff_operator(idx, h)
                if D is None:
                    continue
                X = fp.inc_design(F, h, inc['cols'], inc['physics']).loc[st]
                t = np.mean([np.asarray(m.predict(X)).ravel() for m in inc[h]], axis=0)
                if deshrink and ('f', h) in inc:
                    f = 1.0 + fp.INC_DESHRINK * (inc[('f', h)] - 1.0)
                    t = t.mean() + (t - t.mean()) * f
                terms.append((h, D, t, lam))
                preds[h] = pd.Series(t, index=st)
            f = dict(block=name, scope=scope, fold=fid, idx=idx,
                     level=d.level.to_numpy(), y=d.y.to_numpy(),
                     score=d.score.to_numpy(), terms=terms, origin=origin)
            f['basis'] = gain_basis(f)
            folds.append(f)
            if 1 in preds and 4 in preds:
                # d4 should equal the sum of the four 30-minute changes inside it. It does
                # not, and the size of the gap is how much the two horizons disagree about
                # the same interval -- the thing the single solve has to arbitrate.
                roll = preds[1].rolling(4).sum()
                j = preds[4].index.intersection(roll.dropna().index)
                if len(j):
                    diag.append(dict(block=name, scope=scope, fold=fid, n=len(j),
                                     inconsistency_rms=float(np.sqrt(
                                         np.mean((preds[4][j] - roll[j]) ** 2))),
                                     d4_sd=float(preds[4][j].std())))
    return folds, pd.DataFrame(diag)


def apply_gains(fold, gains):
    out = []
    for h, D, t, lam in fold['terms']:
        a = float(gains.get(h, 1.0))
        out.append((D, t if a == 1.0 else t.mean() + (t - t.mean()) * a, lam))
    return out


def gain_basis(fold):
    """`z` is affine in the gains, so the whole grid search costs three sparse solves.

    Rescaling `d_h` about its own mean makes the right-hand side `rhs0 + sum_h a_h r_h`, and
    `A` does not depend on `a` at all, so `z(a) = z0 + sum_h a_h u_h` with `u_h = A^-1 r_h`.
    Only the final clip is nonlinear, and it is applied afterwards exactly as the solver does.
    Checked against the general solver in tests/test_v21_evaluation.py."""
    level, terms = fold['level'].astype(float), fold['terms']
    A = identity(len(level), format='csc')
    for _, D, _, lam in terms:
        A = (A + lam * (D.T @ D)).tocsc()
    lu = splu(A)
    rhs0 = level.copy()
    for _, D, t, lam in terms:
        rhs0 = rhs0 + lam * (D.T @ np.full(len(t), float(t.mean())))
    return lu.solve(rhs0), {h: lu.solve(lam * (D.T @ (t - t.mean())))
                            for h, D, t, lam in terms}


def fold_z(fold, gains):
    z0, U = fold['basis']
    z = z0 + sum(float(gains.get(h, 1.0)) * u for h, u in U.items())
    return np.clip(z, 5, 100)


def fold_sse(fold, gains):
    m = fold['score']
    e = fold_z(fold, gains)[m] - fold['y'][m]
    return float((e ** 2).sum()), int(m.sum())


def fit_gains(folds, penalty):
    """Grid search over the two gains. The grid is coarse on purpose: with about a fortnight
    of forward inner rows per block there is no resolution to justify a finer one, and a
    continuous optimiser here would only be more confident, not more right."""
    n = sum(int(f['score'].sum()) for f in folds)
    best, arg = None, (1.0, 1.0)
    for a1 in GAIN_GRID:
        for a4 in GAIN_GRID:
            gains = {1: a1, 4: a4}
            sse = sum(fold_sse(f, gains)[0] for f in folds)
            obj = sse / n + penalty * ((a1 - 1) ** 2 + (a4 - 1) ** 2)
            if best is None or obj < best:
                best, arg = obj, (float(a1), float(a4))
    return {1: arg[0], 4: arg[1]}, best


def choose_penalty(folds):
    """The penalty is a hyper-parameter, so it gets its own split: leave one inner fold out,
    fit the gains on the rest, score the held-out fold, and take the penalty with the lowest
    total. Leave-one-out rather than early/late halves because B2 and B3 have only two or
    three usable inner folds -- their origins sit 15 and 7 days further back, so there is less
    history in front of them to roll an origin through."""
    rows = []
    for pen in PENALTIES:
        sse, n = 0, 0
        for i in range(len(folds)):
            rest = folds[:i] + folds[i + 1:]
            gains, _ = fit_gains(rest or folds, pen)
            s, k = fold_sse(folds[i], gains)
            sse, n = sse + s, n + k
        rows.append(dict(penalty=pen, holdout_mse=sse / n))
    R = pd.DataFrame(rows)
    return float(R.loc[R.holdout_mse.idxmin(), 'penalty']), R


def score_folds(folds, gains, label):
    """`gains` is None for unit gains, or a {block: {h: a}} map fitted on that block's own
    inner folds."""
    P = []
    for f in folds:
        gv = (gains or {}).get(f['block'], {1: 1.0, 4: 1.0})
        z = fold_z(f, gv)
        P.append(pd.DataFrame({'block': f['block'], 'datetime': f['idx'], 'y': f['y'],
                               'recon': z, 'score': f['score']}))
    return pd.concat(P, ignore_index=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--physics', type=int, default=1)
    ap.add_argument('--deshrink', type=int, default=1,
                    help='1 = section 176 half de-shrink under the candidate as well')
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    cache = pd.read_pickle(a47.CACHE)
    g = fp.load_grid()
    y = g[fp.TARGET]
    phys, dsh = bool(a.physics), bool(a.deshrink)
    seeds = a47.SEEDS_INC
    print('base configuration: physics=%s  half-deshrink=%s  seeds=%d'
          % (phys, dsh, len(seeds)))

    results, rows, ref, gain_log = {}, [], None, []
    for label, learners in (('base', None), ('hybrid', HYBRID)):
        t = time.time()
        inner, _ = raw_terms(g, y, cache, phys, dsh, seeds, learners, ('inner',))
        outer, diag = raw_terms(g, y, cache, phys, dsh, seeds, learners, ('outer',))
        # Gains are fitted PER BLOCK on that block's own inner folds. Pooling them across
        # blocks would be a leak, not an efficiency: B1's inner folds run to 2023-08-14, which
        # is the whole of B2's scored horizon.
        gains = {}
        for b in sorted({f['block'] for f in inner}):
            own = [f for f in inner if f['block'] == b]
            pen, tbl = choose_penalty(own)
            gains[b], _ = fit_gains(own, pen)
            gain_log.append(dict(candidate=label, block=b, folds=len(own),
                                 rows=int(sum(f['score'].sum() for f in own)),
                                 penalty=pen, a1=gains[b][1], a4=gains[b][4],
                                 **{'mse_pen%g' % r.penalty: r.holdout_mse
                                    for r in tbl.itertuples()}))
            print('  %-11s %d inner folds, %4d rows -> penalty %-4g  a1=%.3f a4=%.3f'
                  % (b, len(own), gain_log[-1]['rows'], pen, gains[b][1], gains[b][4]))
        print('  [%s fitted in %.0f s]' % (label, time.time() - t))
        if len(diag):
            print('  d4 vs four d1 inconsistency, outer: %s'
                  % '  '.join('%s %.3f (d4 sd %.3f)' % (r.block, r.inconsistency_rms, r.d4_sd)
                              for r in diag.itertuples()))
        for tag, per_block in (('', None), ('_gains', gains)):
            name = label + tag
            P = score_folds(outer, per_block, name)
            results[name] = P
            r = a47.report(P, name, ref)
            if per_block:
                for b, gv in per_block.items():
                    r['a1_' + b[:2]], r['a4_' + b[:2]] = gv[1], gv[4]
            if ref is None:
                ref = r                      # 'base' with unit gains is the incumbent
            rows.append(r)
            print('  %-14s pooled %.5f%s' % (name, r['pooled'],
                                             '' if 'd_pooled' not in r
                                             else '  (%+.5f)' % r['d_pooled']))
        if len(diag):
            diag.to_csv(OUT / ('solver_loss_inconsistency_%s.csv' % label), index=False)
    pd.DataFrame(gain_log).to_csv(OUT / 'solver_loss_gains.csv', index=False)

    for name in ('base_gains', 'hybrid', 'hybrid_gains'):
        bs = a47.bootstrap(results['base'], results[name])
        for k, v in bs.items():
            rows[[r['candidate'] for r in rows].index(name)]['boot_' + k] = v
        print('bootstrap %-13s dMSE %+.4f  [%+.4f, %+.4f]  worse in %.0f%% of draws'
              % (name, bs['mean'], bs['lo'], bs['hi'], 100 * bs['p_worse']))

    R = pd.DataFrame(rows)
    R.to_csv(OUT / 'solver_loss.csv', index=False)
    (OUT / 'solver_loss.json').write_text(R.to_json(orient='records', indent=2))
    print('\n' + R.to_string(index=False))
    win = R.loc[R.get('promotable', False) == True, 'candidate'].tolist()
    print('\nPASSES THE SECTION-180 BAR:', win or 'none')


if __name__ == '__main__':
    main()
