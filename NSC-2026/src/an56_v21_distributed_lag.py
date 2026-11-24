"""Session 27, Tahap D: a distributed-lag linear baseline for the change target, before anyone
builds a sequence model.

Sections 174, 184 and 185 replaced the increment LEARNER -- HistGB, CatBoost, a ridge, an
extra-trees, a physical spline, several averages of those -- and every one of them read the same
summary of the past: the drivers at `t`, the drivers at `t-h`, and their difference. That is two
points on a trajectory. The audit's remaining open question is whether the trajectory itself
carries anything, and the honest way to ask it is not to add a temporal convolution to two months
of data and see what happens.

So: causal lags of T, CO2, pressure and the dewpoint-proxy RH at 0, 1, 2, 4, 8, 16, 24 and 48
half-hour steps -- 30 minutes to a full day back -- plus rectified warming and cooling terms and
the diurnal harmonics the rest of the pipeline already uses, and one regularised Ridge predicting
BOTH horizons' changes at once. Compared with the spline of section 185, the model sees several
points that are all far from `t` rather than one summary and one horizon difference. Compared
with a TCN, it has a closed-form fit, no capacity to speak of, and nothing to tune except the
penalty.

**Rules it has to obey, all of which have bitten this log before.**

* The grid is a complete 30-minute index, so `shift(4)` is exactly two hours. It is asserted,
  not assumed, because `dropna` before shifting would silently make h=4 mean "four surviving
  rows" -- section 181's date-pairing bug in another costume.
* No actual RH lag is ever read at inference. The RH that enters the design is `rh_tmin48`, the
  parameter-free dewpoint proxy built from temperature, which is what the increment models
  already use.
* A training row needs BOTH endpoints of BOTH horizons to be labelled training rows, so a pair
  can never straddle the origin.
* The imputer and the scaler are fitted inside the training split, and the penalty and the blend
  strength are chosen on a forward validation window carved out of the pre-origin rows -- never
  on the window being scored.
* It is judged as a CORRECTION to the incumbent increment, not as a replacement, and on the
  final reconciled RMSE rather than on increment error. Zero blend is kept as the control and is
  what ships if the selection does not choose otherwise.

    .venv/Scripts/python.exe src/an56_v21_distributed_lag.py
"""
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'src'))
import final_pipeline as fp
import an47_v21_forward_benchmark as a47

OUT = a47.OUT_S27
LAGS = (0, 1, 2, 4, 8, 16, 24, 48)          # half-hour steps: 0 min to 24 h
LAG_COLS = ('T', 'co2', 'pressure', 'rh_tmin48')
ALPHAS = (10.0, 100.0, 1000.0, 10000.0)
BLENDS = (0.0, 0.1, 0.2, 0.3, 0.5)
VAL_FRACTION = 0.25                          # trailing share of the pre-origin rows
HORIZONS = tuple(h for h, _ in fp.INC_SPEC)


def lag_design(F, cols=LAG_COLS, lags=LAGS):
    """Causal lags of the exogenous drivers, rectified two-hour temperature change, and the
    diurnal harmonics. Everything here is known at `t` looking backwards only."""
    assert (pd.DatetimeIndex(F.index).to_series().diff().dropna()
            == pd.Timedelta(minutes=30)).all(), \
        'lag_design needs a complete 30-minute grid; shift(k) would not mean k half-hours'
    have = [c for c in cols if c in F.columns]
    parts = [F[have].shift(k).add_suffix('_lag%d' % k) for k in lags]
    dT = F['T'] - F['T'].shift(4)
    parts.append(pd.DataFrame({'warm2h': dT.clip(lower=0), 'cool2h': (-dT).clip(lower=0),
                               'sin1': F['sin1'], 'cos1': F['cos1'],
                               'sin2': F['sin2'], 'cos2': F['cos2']}, index=F.index))
    return pd.concat(parts, axis=1)


def lag_targets(y, horizons=HORIZONS):
    return pd.DataFrame({h: y - y.shift(h) for h in horizons})


def lag_mask(mask, index, horizons=HORIZONS):
    """A usable row: itself a labelled training row, and so is the earlier endpoint of every
    horizon this model predicts."""
    base = mask.reindex(index, fill_value=False)
    m = base.copy()
    for h in horizons:
        m = m & base.shift(h, fill_value=False)
    return m


def fit_lag_model(X, T, rows, alpha):
    """Imputer and scaler fitted inside the training rows, one multi-output Ridge on top."""
    p = make_pipeline(SimpleImputer(strategy='median'), StandardScaler(), Ridge(alpha=alpha))
    return p.fit(X.loc[rows], T.loc[rows])


def select_alpha_and_blend(X, T, rows, lgb_oof, val_fraction=VAL_FRACTION):
    """Forward selection inside the pre-origin rows.

    The trailing `val_fraction` of the training rows is held out, both learners are refitted on
    what comes before it, and the (alpha, blend) pair with the lowest validation MSE over the two
    change targets wins. `lgb_oof` is the incumbent's prediction on the same validation rows,
    produced by the same forward split, so the blend is chosen against a like-for-like control
    rather than against an in-sample increment."""
    rows = pd.DatetimeIndex(rows).sort_values()
    k = int(len(rows) * (1 - val_fraction))
    trn, val = rows[:k], rows[k:]
    if len(val) < 200 or len(trn) < 500:
        return ALPHAS[1], 0.0, dict(fallback='validation window too small: %d/%d'
                                    % (len(trn), len(val)))
    truth = T.loc[val].to_numpy()
    best, table = None, []
    for a in ALPHAS:
        pred = fit_lag_model(X, T, trn, a).predict(X.loc[val])
        for w in BLENDS:
            mix = (1 - w) * lgb_oof + w * pred
            mse = float(np.mean((mix - truth) ** 2))
            table.append(dict(alpha=a, blend=w, mse=mse))
            if best is None or mse < best[2]:
                best = (a, w, mse)
    zero = min(r['mse'] for r in table if r['blend'] == 0.0)
    return best[0], best[1], dict(val_rows=len(val), train_rows=len(trn),
                                  best_mse=best[2], zero_blend_mse=zero,
                                  gain=zero - best[2], table=table)


def make_builder(log, force_blend=None):
    """`inc_builder` for `a47.score_config`: shipped increments, plus the lag model and the
    blend strength selected at this origin."""
    def build(F, yh, mask, seeds):
        inc = fp.fit_increments(F, yh, mask, seeds, physics=True, deshrink=True)
        X = lag_design(F)
        T = lag_targets(yh)
        m = lag_mask(mask, F.index) & T.notna().all(axis=1)
        rows = F.index[m.to_numpy()]

        # The incumbent's forward prediction on the same validation window, so the blend is
        # chosen against the control rather than against an in-sample number.
        k = int(len(rows) * (1 - VAL_FRACTION))
        trn, val = rows[:k], rows[k:]
        if len(val) >= 200 and len(trn) >= 500:
            import lightgbm as lgb
            oof = np.column_stack([
                lgb.LGBMRegressor(random_state=fp.INC_SEED, **fp.INC_KW)
                .fit(fp.inc_design(F, h, inc['cols'], True).loc[trn], T[h].loc[trn])
                .predict(fp.inc_design(F, h, inc['cols'], True).loc[val])
                for h in HORIZONS])
        else:
            oof = np.zeros((len(val), len(HORIZONS)))
        alpha, blend, info = select_alpha_and_blend(X, T, rows, oof)
        if force_blend is not None:
            blend = force_blend
        inc['lag_model'] = fit_lag_model(X, T, rows, alpha)
        inc['lag_blend'] = blend
        inc['lag_alpha'] = alpha
        log.append(dict(origin=str(rows.max()), alpha=alpha, blend=blend, rows=len(rows),
                        **{k2: v for k2, v in info.items() if k2 != 'table'}))
        return inc
    return build


def lag_terms(F, idx, inc):
    """`a47.increment_terms` with the change vector blended toward the lag model's prediction
    before the de-shrink factor is applied. The factor stays the incumbent estimator: this
    screen varies the change model, nothing else."""
    X = lag_design(F)
    out, w = [], inc.get('lag_blend', 0.0)
    ridge = inc['lag_model'].predict(X.loc[idx]) if w else None
    for j, (h, lam) in enumerate(fp.INC_SPEC):
        D, st = fp.diff_operator(idx, h)
        if D is None:
            out.append((None, None, lam))
            continue
        t = np.mean([m.predict(fp.inc_design(F, h, inc['cols'], True).loc[st])
                     for m in inc[h]], axis=0)
        if w:
            pos = pd.Series(np.arange(len(idx)), index=pd.DatetimeIndex(idx)).loc[st].to_numpy()
            t = (1 - w) * t + w * ridge[pos, j]
        f = 1.0 + fp.INC_DESHRINK * (inc[('f', h)] - 1.0)
        t = t.mean() + (t - t.mean()) * f
        out.append((D, t, lam))
    return out


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    g = fp.load_grid()
    y = g[fp.TARGET]
    cache = a47.load_cache(a47.CACHE_S27, a47.MANIFEST_S27)
    seeds, feats = a47.SEEDS_INC, {}

    print('control : v21 physics + half de-shrink (blend forced to zero)')
    t = time.time()
    log0 = []
    base = a47.score_config(g, y, cache, physics=True, deshrink=fp.INC_DESHRINK, seeds=seeds,
                            scopes=('outer',), inc_builder=make_builder(log0, force_blend=0.0),
                            term_builder=lag_terms, feature_cache=feats)
    ref = a47.report(base, 'incumbent_blend0')
    print('  pooled %.5f  (%.0f s)' % (ref['pooled'], time.time() - t), flush=True)

    print('candidate: distributed-lag Ridge blended in at the strength chosen per origin')
    t = time.time()
    log = []
    P = a47.score_config(g, y, cache, physics=True, deshrink=fp.INC_DESHRINK, seeds=seeds,
                         scopes=('outer',), inc_builder=make_builder(log),
                         term_builder=lag_terms, feature_cache=feats)
    r = a47.report(P, 'distributed_lag_blend', ref)
    print('  pooled %.5f  (%.0f s)' % (r['pooled'], time.time() - t), flush=True)

    S = pd.DataFrame(log)
    print('\nper-origin selection\n' + S.to_string(index=False))

    if S.blend.max() > 0:
        bs = a47.bootstrap(base, P)
        print('  bootstrap dMSE %+.4f [%+.4f, %+.4f] over %d blocks, worse in %.0f%% of draws'
              % (bs['mean'], bs['lo'], bs['hi'], bs['blocks'], 100 * bs['p_worse']))
        for k in ('mean', 'lo', 'hi', 'p_worse'):
            r['boot_' + k] = bs[k]
    else:
        bs = None
        print('  every origin selected zero blend; the candidate IS the control')

    R = pd.DataFrame([ref, r])
    P.to_pickle(OUT / 'preds_distributed_lag.pkl')
    R.to_csv(OUT / 'distributed_lag.csv', index=False)
    S.to_csv(OUT / 'distributed_lag_selection.csv', index=False)
    (OUT / 'distributed_lag.json').write_text(json.dumps(dict(
        lags=list(LAGS), lag_cols=list(LAG_COLS), alphas=list(ALPHAS), blends=list(BLENDS),
        val_fraction=VAL_FRACTION, selection=json.loads(S.to_json(orient='records')),
        results=json.loads(R.to_json(orient='records')), bootstrap=bs), indent=2, default=str))
    print('\n' + R.to_string(index=False))


if __name__ == '__main__':
    main()
