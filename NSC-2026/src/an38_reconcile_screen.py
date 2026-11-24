"""Session 22 screen: the increment reconciliation cannot touch a third of the error, and
this asks whether a low-frequency term can.

Every row of `D_h` sums to zero, so the shipped reconciliation preserves the mean of the
level prediction exactly (section 150). It corrects within-day shape and nothing else.
Section 146 measured **36.31 % of MSE sitting in the per-day mean** -- an error component the
current flag is structurally incapable of reaching.

The natural companion is a model of the SMOOTHED humidity, `mean(RH over +/-w/2)`, entered as
a third quadratic term:

    min_z ||z-p||^2 + sum_h lam_h ||D_h z - d_h||^2 + lam_s ||S z - s||^2

`S` is a centered moving average, so unlike `D` its rows do not sum to zero and this term CAN
move the level. That is the point and also the risk: sections 6, 35 and 46 each tried a global
offset correction and each failed. This is not a global offset -- it is a per-window level
driven by a fitted model -- but the screen has to be read with those three failures in mind.

A daily model fitted on daily rows was rejected before writing this: the training calendar has
about 61 days, so a per-day design has 61 samples. Predicting a smoothed target at every
half-hour keeps all 2933 training rows and asks the same question.

PRE-REGISTERED, so that section 38's prune-by-CV trap is not re-entered:

  candidates   incumbent {1,4}; lambda scaled x0.5 and x2; {1,2,4}; {1,4,8};
               incumbent + s24 at lambda 0.25 / 1 / 4; incumbent + s12 at 1; s24 alone
  evaluations  three production holdouts (an36 protocol, truncated feature horizons,
               chronological meta) and the twelve chronological cache folds
  adoption     beat the incumbent on pooled RMSE in BOTH evaluations, AND on at least two of
               the three holdout blocks, AND on at least eight of the twelve cache folds
  seeds        one seed while screening; the winner is re-confirmed at five

Screening uses cached stack predictions as the level p, so only the component models are
refitted. Nothing here writes a submission.

    .venv/Scripts/python.exe src/an38_reconcile_screen.py
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import lightgbm as lgb
from scipy.sparse import csc_matrix, identity
from scipy.sparse.linalg import spsolve

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import final_pipeline as fp

OUT = ROOT / 'outputs' / 'audit_v20'
BACKBONE = 'v16'
HOLD_DAYS = 15

# component -> (kind, parameter). Difference components reuse the shipped operator.
COMPONENTS = {'d1': ('diff', 1), 'd2': ('diff', 2), 'd4': ('diff', 4), 'd8': ('diff', 8),
              's12': ('smooth', 25), 's24': ('smooth', 49)}

INCUMBENT = {'d1': 4.0, 'd4': 1.0}
CANDIDATES = {
    'incumbent_d1_d4': INCUMBENT,
    'lambda_half': {'d1': 2.0, 'd4': 0.5},
    'lambda_double': {'d1': 8.0, 'd4': 2.0},
    'add_d2': {'d1': 4.0, 'd2': 2.0, 'd4': 1.0},
    'add_d8': {'d1': 4.0, 'd4': 1.0, 'd8': 0.5},
    'add_s24_w025': {'d1': 4.0, 'd4': 1.0, 's24': 0.25},
    'add_s24_w1': {'d1': 4.0, 'd4': 1.0, 's24': 1.0},
    'add_s24_w4': {'d1': 4.0, 'd4': 1.0, 's24': 4.0},
    'add_s12_w1': {'d1': 4.0, 'd4': 1.0, 's12': 1.0},
    's24_alone_w1': {'s24': 1.0},
}


# ------------------------------------------------------------------ operators
def smooth_operator(idx, w):
    """Centered moving-average operator. One row per position whose complete w-point window
    is present in `idx`, so a block edge or a hole produces no row rather than an average
    over a shorter, differently-biased window."""
    idx = pd.DatetimeIndex(idx)
    pos = pd.Series(np.arange(len(idx)), index=idx)
    half = w // 2
    offs = [pd.Timedelta(minutes=30 * k) for k in range(-half, half + 1)]
    cols, keep = [], np.ones(len(idx), bool)
    for o in offs:
        p = pos.reindex(idx + o).to_numpy()
        keep &= ~np.isnan(p)
        cols.append(p)
    i = np.flatnonzero(keep)
    if len(i) == 0:
        return None, idx[:0]
    rows = np.repeat(np.arange(len(i)), w)
    col = np.concatenate([c[i][:, None] for c in cols], axis=1).ravel().astype(int)
    S = csc_matrix((np.full(len(rows), 1.0 / w), (rows, col)), shape=(len(i), len(idx)))
    return S, idx[i]


def smooth_design(F, w):
    c = [x for x in fp.INC_COLS if x in F.columns]
    m = F[c].rolling(w, center=True, min_periods=w).mean().add_suffix('_sm%d' % w)
    return pd.concat([F, m], axis=1)


def fit_component(name, F, y, train_mask, seeds):
    """One model per component. `train_mask` marks labelled training rows; every label the
    component's target consumes must lie inside it."""
    kind, par = COMPONENTS[name]
    if kind == 'diff':
        X = fp.inc_design(F, par)
        tgt = (y - y.shift(par)).reindex(X.index)
        m = train_mask.reindex(X.index, fill_value=False)
        m = m & tgt.notna() & m.shift(par, fill_value=False)
    else:
        X = smooth_design(F, par)
        tgt = y.reindex(X.index).rolling(par, center=True, min_periods=par).mean()
        full = (train_mask.reindex(X.index, fill_value=False).astype(float)
                .rolling(par, center=True, min_periods=par).sum() == par)
        m = full.fillna(False) & tgt.notna()
    assert m.sum() > 400, (name, int(m.sum()))
    return [lgb.LGBMRegressor(random_state=s, **fp.INC_KW).fit(X.loc[m], tgt.loc[m])
            for s in seeds]


def component_parts(name, idx, F, models):
    kind, par = COMPONENTS[name]
    if kind == 'diff':
        M, stamps = fp.diff_operator(idx, par)
        X = fp.inc_design(F, par)
    else:
        M, stamps = smooth_operator(idx, par)
        X = smooth_design(F, par)
    if M is None:
        return None, None
    t = np.mean([m.predict(X.loc[stamps]) for m in models], axis=0)
    return M, t


def solve(p, parts, weights):
    A = identity(len(p), format='csc')
    rhs = np.asarray(p, float).copy()
    for name, lam in weights.items():
        M, t = parts[name]
        if M is None:
            continue
        A = (A + lam * (M.T @ M)).tocsc()
        rhs = rhs + lam * (M.T @ t)
    z = spsolve(A, rhs)
    assert np.max(np.abs(A @ z - rhs)) < 1e-7
    return np.clip(z, 5, 100)


# ----------------------------------------------------------------- evaluation
def evaluate(blocks, label, seeds):
    """`blocks` is a list of (name, F, y, train_mask_at_origin, index, truth, base)."""
    rows = []
    for name, F, y, mask, idx, truth, base in blocks:
        models = {c: fit_component(c, F, y, mask, seeds) for c in COMPONENTS}
        parts = {c: component_parts(c, idx, F, models[c]) for c in COMPONENTS}
        rec = dict(evaluation=label, block=name, n=len(idx), base=fp.rmse(truth, base))
        for cand, weights in CANDIDATES.items():
            rec[cand] = fp.rmse(truth, solve(base, parts, weights))
        rows.append(rec)
        print('  %-12s base %.5f  ' % (name, rec['base'])
              + '  '.join('%s %+.4f' % (k, rec[k] - rec['base']) for k in CANDIDATES),
              flush=True)
    return pd.DataFrame(rows)


def holdout_blocks(g, y, base_frame):
    boundary = g.index[(g.is_test == 0).to_numpy()].max()
    day = pd.Timedelta(days=HOLD_DAYS)
    spec = [('B1_last15d', boundary - day, boundary),
            ('B2_prev15d', boundary - 2 * day, boundary - day),
            ('B3_shift7d', boundary - day - pd.Timedelta(days=7),
             boundary - pd.Timedelta(days=7))]
    out = []
    for name, hs, he in spec:
        gh = g.loc[g.index <= he]
        F = fp.make_features(gh)
        mask = pd.Series((gh.is_test == 0).to_numpy(), index=gh.index) & y.reindex(gh.index).notna()
        b = base_frame.loc[(base_frame.block == name) & (base_frame.model == BACKBONE)]
        b = b.sort_values('datetime')
        idx = pd.DatetimeIndex(b.datetime)
        assert idx.min() > hs and idx.max() <= he
        out.append((name, F, y.reindex(gh.index), mask & (gh.index <= hs), idx,
                    b.y.to_numpy(), b.base.to_numpy()))
    return out


def cache_blocks(g, y, F):
    cache = pd.read_pickle(OUT / 'predictions.pkl')
    cache = cache.loc[(cache['mode'] == 'past_only') & (cache.model == BACKBONE)]
    tr = pd.Series((g.is_test == 0).to_numpy(), index=g.index) & y.notna()
    out = []
    for (fam, k), b in cache.groupby(['family', 'fold']):
        b = b.sort_values('datetime')
        idx = pd.DatetimeIndex(b.datetime)
        cut = idx.min() - pd.Timedelta(minutes=30)
        out.append(('%s%d' % (fam, k), F, y, tr & (g.index <= cut), idx,
                    b.y.to_numpy(), b.pred.to_numpy()))
    return out


def main():
    g = fp.load_grid()
    y = g[fp.TARGET]
    F_full = fp.make_features(g)
    base_frame = pd.read_pickle(OUT / 'increment_production_predictions.pkl')

    print('PRODUCTION HOLDOUTS (truncated feature horizons)', flush=True)
    H = evaluate(holdout_blocks(g, y, base_frame), 'holdout', (fp.INC_SEED,))
    print('\nCHRONOLOGICAL CACHE FOLDS', flush=True)
    C = evaluate(cache_blocks(g, y, F_full), 'cache', (fp.INC_SEED,))

    R = pd.concat([H, C], ignore_index=True)
    R.to_csv(OUT / 'reconcile_screen_scores.csv', index=False)

    inc = 'incumbent_d1_d4'
    summary = {}
    for cand in CANDIDATES:
        h, c = R[R.evaluation == 'holdout'], R[R.evaluation == 'cache']
        e = dict(
            holdout_mean_delta=float((h[cand] - h[inc]).mean()),
            holdout_blocks_better=int((h[cand] < h[inc]).sum()), holdout_blocks=len(h),
            cache_mean_delta=float((c[cand] - c[inc]).mean()),
            cache_folds_better=int((c[cand] < c[inc]).sum()), cache_folds=len(c),
            holdout_vs_base=float((h[cand] - h.base).mean()),
            cache_vs_base=float((c[cand] - c.base).mean()))
        e['adopted'] = bool(e['holdout_mean_delta'] < 0 and e['cache_mean_delta'] < 0
                            and e['holdout_blocks_better'] >= 2
                            and e['cache_folds_better'] >= 8)
        summary[cand] = e
    (OUT / 'reconcile_screen_summary.json').write_text(json.dumps(summary, indent=2))

    print('\nAGAINST THE INCUMBENT (negative = better than the shipped {1,4} config)')
    t = pd.DataFrame(summary).T[['holdout_mean_delta', 'holdout_blocks_better',
                                 'cache_mean_delta', 'cache_folds_better', 'adopted']]
    print(t.to_string())
    winners = [k for k, v in summary.items() if v['adopted'] and k != inc]
    print('\nPASSES THE PRE-REGISTERED BAR:', winners or 'none')


if __name__ == '__main__':
    main()
