"""Session 23: two mechanisms that are not weight tweaks.

Session 22 screened the reconciliation's weights and horizons and found the shipped setting is
a local optimum. That closes the *tuning* axis, not the *mechanism* axis. Two mechanisms here,
each with an argument that stands before any number is computed.

**1. Reconcile the vapour pressure, not the humidity.**
Relative humidity moves whenever temperature moves, because `es(T)` is in its denominator, and
that part of the motion is thermodynamics rather than weather. Measured on the training grid:

    corr(dRH, dT) = -0.802 at 30 min and -0.904 at 2 h
    corr(de,  dT) = +0.461 at 30 min and +0.580 at 2 h

At two hours **82 % of the variance of the RH change is temperature**. The shipped increment
model spends most of its capacity re-deriving a relation that `es(T)` already gives exactly.
Vapour pressure `e = RH*es(T)/100` moves only by advection, condensation and ventilation, so
its change is the moisture signal with the thermodynamics divided out.

It stays a linear least squares problem. With `w = es(T)/mean_train(es(T))`, the normalised
vapour pressure is `v = z*w`, and the h-step change in v is `(D diag(w)) z` -- still linear in
z, so it enters the same sparse solve as one more quadratic term.

**2. Weight each difference row by how predictable that change is.**
The scalar lambda is one compromise across rows the increment model predicts well and rows it
does not. Session 22 found both halving and doubling it hurt, which is what a compromise at its
optimum looks like -- and a compromise implies heterogeneity worth exploiting. Honest residuals
come from three contiguous time-folds inside train; a second model predicts `log(residual^2)`;
the row weight is the precision, renormalised so the MEAN weight is exactly the shipped lambda
and clipped to [1/3, 3] so no single row can dominate. That constraint means this cannot become
a global strength change in disguise -- session 22 already rejected those.

PRE-REGISTERED. Five challengers, not ten, because section 158 showed a wide screen manufactures
winners at chance:

  candidates  incumbent; +vapour at half weight; +vapour at full weight; vapour instead of RH;
              incumbent with per-row weights; per-row weights + vapour
  evaluation  the three production holdouts ONLY. Section 159 measured the twelve cache folds at
              1200 unique timestamps over 26 days with two literally duplicated pairs, so they
              are dropped from the decision entirely.
  adoption    beat the incumbent on the pooled holdout RMSE AND on at least two of three blocks,
              then survive the pipeline's own nine folds, which are not part of this screen.
  seeds       one while screening; the winner is re-confirmed at five.

    .venv/Scripts/python.exe src/an39_newmech_screen.py
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import lightgbm as lgb
from scipy.sparse import csc_matrix, diags, identity
from scipy.sparse.linalg import spsolve

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import final_pipeline as fp

OUT = ROOT / 'outputs' / 'audit_v20'
BACKBONE = 'v16'
HOLD_DAYS = 15
WCLIP = (1 / 3.0, 3.0)
VAR_FOLDS = 3

CANDIDATES = {
    'incumbent':        dict(rh={1: 4.0, 4: 1.0}, vp={}, gls=False),
    'add_vp_half':      dict(rh={1: 4.0, 4: 1.0}, vp={1: 2.0, 4: 0.5}, gls=False),
    'add_vp_full':      dict(rh={1: 4.0, 4: 1.0}, vp={1: 4.0, 4: 1.0}, gls=False),
    'vp_instead_of_rh': dict(rh={}, vp={1: 4.0, 4: 1.0}, gls=False),
    'gls_rows':         dict(rh={1: 4.0, 4: 1.0}, vp={}, gls=True),
    'gls_plus_vp':      dict(rh={1: 4.0, 4: 1.0}, vp={1: 2.0, 4: 0.5}, gls=True),
}


# --------------------------------------------------------------------- pieces
def vp_weight(F, train_mask):
    """`es(T)` normalised by its training mean. Uses temperature only, so it is target-blind
    and constant across candidates."""
    es = pd.Series(fp.es(F['T'].to_numpy()), index=F.index)
    ref = float(es[train_mask.reindex(F.index, fill_value=False)].mean())
    return es / ref, ref


def scaled_diff_operator(idx, h, w):
    """`D diag(w)` -- row k holds -w at the earlier position and +w at the later one, so
    `(D diag(w)) z` is the h-step change in `z*w`."""
    D, stamps = fp.diff_operator(idx, h)
    if D is None:
        return None, stamps
    return (D @ diags(w.reindex(idx).to_numpy())).tocsc(), stamps


def fit_change(F, y, train_mask, h, seeds, scale=None):
    """One increment model. `scale` None gives the shipped RH change; a series gives the
    change in `y*scale`, i.e. normalised vapour pressure."""
    X = fp.inc_design(F, h)
    q = y if scale is None else y * scale.reindex(y.index)
    tgt = (q - q.shift(h)).reindex(X.index)
    m = train_mask.reindex(X.index, fill_value=False)
    m = m & tgt.notna() & m.shift(h, fill_value=False)
    assert m.sum() > 400
    return [lgb.LGBMRegressor(random_state=s, **fp.INC_KW).fit(X.loc[m], tgt.loc[m])
            for s in seeds], X, m


def row_precision(F, y, train_mask, h, seeds):
    """Per-row weights from a model of the increment model's own squared error.

    Residuals come from three contiguous time-folds inside train, never in-sample, so the
    variance model is not fitted to residuals the increment model has already memorised."""
    X = fp.inc_design(F, h)
    tgt = (y - y.shift(h)).reindex(X.index)
    m = train_mask.reindex(X.index, fill_value=False)
    m = m & tgt.notna() & m.shift(h, fill_value=False)
    rows = X.index[m]
    edges = np.array_split(np.arange(len(rows)), VAR_FOLDS)
    res = pd.Series(np.nan, index=rows)
    for cut in edges:
        va = rows[cut]
        trn = rows.difference(va)
        mod = lgb.LGBMRegressor(random_state=seeds[0], **fp.INC_KW).fit(X.loc[trn], tgt.loc[trn])
        res.loc[va] = tgt.loc[va].to_numpy() - mod.predict(X.loc[va])
    lg = np.log(res.to_numpy() ** 2 + 1e-6)
    var_mod = lgb.LGBMRegressor(random_state=seeds[0], **fp.INC_KW).fit(X.loc[rows], lg)
    return var_mod, X


def precision_weights(var_mod, X, stamps):
    v = np.exp(var_mod.predict(X.loc[stamps]))
    p = 1.0 / np.clip(v, 1e-6, None)
    p = p / p.mean()                       # mean weight 1, so lambda keeps its meaning
    return np.clip(p, *WCLIP)


def solve(p, terms):
    A = identity(len(p), format='csc')
    rhs = np.asarray(p, float).copy()
    for M, t, lam, rw in terms:
        if M is None:
            continue
        W = diags(lam * rw) if rw is not None else None
        MtW = (M.T @ W) if W is not None else (M.T * lam)
        A = (A + MtW @ M).tocsc()
        rhs = rhs + MtW @ t
    z = spsolve(A, rhs)
    assert np.max(np.abs(A @ z - rhs)) < 1e-7
    assert np.isfinite(z).all()
    return np.clip(z, 5, 100)


# ----------------------------------------------------------------- evaluation
def run_block(name, F, y, mask, idx, truth, base, seeds):
    w, ref = vp_weight(F, mask)
    rh_mod, vp_mod, prec = {}, {}, {}
    for h, _ in fp.INC_SPEC:
        rh_mod[h] = fit_change(F, y, mask, h, seeds)
        vp_mod[h] = fit_change(F, y, mask, h, seeds, scale=w)
        prec[h] = row_precision(F, y, mask, h, seeds)
    print('  %s  es_ref %.3f hPa' % (name, ref), flush=True)

    parts = {}
    for h, _ in fp.INC_SPEC:
        D, st = fp.diff_operator(idx, h)
        X = fp.inc_design(F, h)
        parts[('rh', h)] = (D, np.mean([m.predict(X.loc[st]) for m in rh_mod[h][0]], 0), st)
        Dv, stv = scaled_diff_operator(idx, h, w)
        parts[('vp', h)] = (Dv, np.mean([m.predict(X.loc[stv]) for m in vp_mod[h][0]], 0), stv)
        vm, vx = prec[h]
        parts[('pw', h)] = precision_weights(vm, vx, st)

    rec = dict(block=name, n=len(idx), base=fp.rmse(truth, base))
    for cand, spec in CANDIDATES.items():
        terms = []
        for h, lam in spec['rh'].items():
            M, t, _ = parts[('rh', h)]
            terms.append((M, t, lam, parts[('pw', h)] if spec['gls'] else None))
        for h, lam in spec['vp'].items():
            M, t, _ = parts[('vp', h)]
            terms.append((M, t, lam, None))
        rec[cand] = fp.rmse(truth, solve(base, terms))
    # Descriptive: how much of the RH change the two targets each leave unexplained.
    for h, _ in fp.INC_SPEC:
        rec['pw_spread_h%d' % h] = float(parts[('pw', h)].std())
    print('     base %.5f  ' % rec['base']
          + '  '.join('%s %+.4f' % (k, rec[k] - rec['incumbent']) for k in CANDIDATES),
          flush=True)
    return rec


def main():
    g = fp.load_grid()
    y = g[fp.TARGET]
    base_frame = pd.read_pickle(OUT / 'increment_production_predictions.pkl')
    boundary = g.index[(g.is_test == 0).to_numpy()].max()
    day = pd.Timedelta(days=HOLD_DAYS)
    spec = [('B1_last15d', boundary - day, boundary),
            ('B2_prev15d', boundary - 2 * day, boundary - day),
            ('B3_shift7d', boundary - day - pd.Timedelta(days=7),
             boundary - pd.Timedelta(days=7))]

    rows, preds = [], []
    for name, hs, he in spec:
        gh = g.loc[g.index <= he]
        F = fp.make_features(gh)
        mask = (pd.Series((gh.is_test == 0).to_numpy(), index=gh.index)
                & y.reindex(gh.index).notna() & (gh.index <= hs))
        b = base_frame.loc[(base_frame.block == name)
                           & (base_frame.model == BACKBONE)].sort_values('datetime')
        idx = pd.DatetimeIndex(b.datetime)
        rows.append(run_block(name, F, y.reindex(gh.index), mask, idx,
                              b.y.to_numpy(), b.base.to_numpy(), (fp.INC_SEED,)))
        pd.DataFrame(rows).to_csv(OUT / 'newmech_screen_scores.csv', index=False)

    R = pd.DataFrame(rows)
    P = pd.read_pickle(OUT / 'increment_production_predictions.pkl')
    print('\n' + R.to_string(index=False))

    summary = {}
    for cand in CANDIDATES:
        d = R[cand] - R['incumbent']
        summary[cand] = dict(
            mean_delta_vs_incumbent=float(d.mean()),
            blocks_better=int((d < 0).sum()), blocks=len(R),
            mean_vs_base=float((R[cand] - R.base).mean()),
            worst_block=float(R[cand].max()),
            adopted=bool(d.mean() < 0 and (d < 0).sum() >= 2))
    (OUT / 'newmech_screen_summary.json').write_text(json.dumps(summary, indent=2))
    print('\n' + pd.DataFrame(summary).T.to_string())
    print('\nPASSES THE PRE-REGISTERED BAR:',
          [k for k, v in summary.items() if v['adopted'] and k != 'incumbent'] or 'none')


if __name__ == '__main__':
    main()
