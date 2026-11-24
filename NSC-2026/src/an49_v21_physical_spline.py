"""Session 26, Tahap 2B: a smooth additive model for the change, fitted to what the
constant-vapour identity does NOT already explain.

Every increment learner tried so far has been a gradient-boosted tree (sections 147, 170, 174)
plus one plain ridge that lost badly at two hours. Trees are piecewise constant and ridge on raw
columns is a plane; neither can bend. `dRH_const_e` is the clearest case -- it is a product of a
level proxy and a temperature ratio, and section 174 noted piecewise-linear leaves helped at 30
minutes for exactly that reason before losing at two hours. A spline basis is the representation
that fits between those two, and it has never been run here.

Two design choices that are not cosmetic:

**The target is the residual to the constant-vapour prediction.** At constant vapour pressure
RH(t) = RH(t-h) es(T(t-h))/es(T(t)), so the change thermodynamics alone produce is
`RH_proxy(t-h) * (es(T(t-h))/es(T(t)) - 1)` -- the `dRH_const_e` column session 24 added. Fitting
`tgt - dRH_const_e` forces a coefficient of exactly 1 on that term instead of letting the
penalty shrink it, which is the whole content of using it as a physical prior rather than as one
more feature. `RH_proxy` is section 19's parameter-free dewpoint proxy `rh_tmin48`, built from
temperature only, so nothing here reads the target at inference.

**The basis is cheap and the penalty is chosen forward.** Cubic B-splines with six knots on ten
physical drivers, the two diurnal harmonics linear, and one interaction -- the h-step temperature
change split by warming/cooling phase, which is where hysteresis would show if it exists. Ridge,
with alpha chosen by a five-fold TimeSeriesSplit over the TRAINING rows of each origin. No
selection touches a scored row.

PRE-REGISTERED: primary is pooled RMSE over B1+B2 after the solve, against the Tahap 1
incumbent, on identical rows; the bar is section 180's. The spline's increment RMSE is reported
as a diagnostic only -- section 174 is why it cannot be the criterion.

    .venv/Scripts/python.exe src/an49_v21_physical_spline.py
"""
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import RidgeCV
from sklearn.model_selection import TimeSeriesSplit
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import SplineTransformer, StandardScaler

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'src'))
import final_pipeline as fp
import an47_v21_forward_benchmark as a47
import an48_v21_solver_loss as a48

OUT = ROOT / 'outputs' / 'audit_v21'
# Smooth drivers. Everything is a temperature, a gas concentration, a pressure or a window
# statistic of one of those -- no target history, at any lag.
SPLINE_COLS = ['T', 'esT', 'co2', 'pressure', 'rh_tmin48', 'T_rng48', 'T_min48',
               'T_minus_min48', 'p_tend24h', 'co2_tend24h']
LINEAR_COLS = ['sin1', 'cos1', 'sin2', 'cos2']
N_KNOTS, DEGREE = 6, 3
ALPHAS = np.logspace(-2, 5, 36)


def design(F, h):
    """Spline inputs at t, the h-step change of the three fast drivers, and the change split
    by warming/cooling phase -- the interaction that would carry hysteresis."""
    cols = [c for c in SPLINE_COLS if c in F.columns]
    X = F[cols].copy()
    for c in ('T', 'co2', 'pressure'):
        X[c + '_d'] = F[c].diff(h)
    dT = X['T_d']
    X['dT_warm'] = dT.clip(lower=0)
    X['dT_cool'] = dT.clip(upper=0)
    X['dT_x_esT'] = dT * F['esT']
    for c in LINEAR_COLS:
        if c in F.columns:
            X[c] = F[c]
    return X


def spline_model(X):
    smooth = [c for c in X.columns if c in SPLINE_COLS or c.endswith('_d')
              or c.startswith('dT_')]
    plain = [c for c in X.columns if c not in smooth]
    pre = ColumnTransformer(
        [('spl', make_pipeline(StandardScaler(),
                               SplineTransformer(n_knots=N_KNOTS, degree=DEGREE,
                                                 include_bias=False)), smooth),
         ('lin', StandardScaler(), plain)])
    return make_pipeline(pre, RidgeCV(alphas=ALPHAS, cv=TimeSeriesSplit(5)))


def physical_offset(F, h):
    """The constant-vapour change, from temperature and the dewpoint proxy only."""
    ratio = F['esT'].shift(h) / F['esT']
    return (F['rh_tmin48'].shift(h) * (ratio - 1.0)).rename('const_e')


def build_spline_increments(F, y, mask, seeds, blend_lgb=0.0, physics=True, deshrink=False):
    """Same contract as `fp.fit_increments`: a dict the reconciler can predict from. `seeds`
    is accepted and ignored for the spline, which is deterministic; when `blend_lgb` > 0 the
    LightGBM members are fitted too and averaged in at that weight."""
    out = {'physics': physics, 'cols': fp.INC_PHYS_COLS if physics else fp.INC_COLS,
           'spline': True, 'blend_lgb': blend_lgb, 'alphas': {}}
    for h, _ in fp.INC_SPEC:
        X = design(F, h)
        off = physical_offset(F, h)
        tgt = (y - y.shift(h)).reindex(X.index)
        m = mask.reindex(X.index, fill_value=False)
        m = m & tgt.notna() & m.shift(h, fill_value=False) & off.notna() & X.notna().all(axis=1)
        mod = spline_model(X).fit(X.loc[m], (tgt - off).loc[m])
        out[('spl', h)] = mod
        out['alphas'][h] = float(mod[-1].alpha_)
        if blend_lgb > 0:
            Xl = fp.inc_design(F, h, out['cols'], physics)
            ml = mask.reindex(Xl.index, fill_value=False)
            ml = ml & tgt.reindex(Xl.index).notna() & ml.shift(h, fill_value=False)
            out[h] = [fp.lgb.LGBMRegressor(random_state=s, **fp.INC_KW).fit(
                Xl.loc[ml], tgt.reindex(Xl.index).loc[ml]) for s in seeds]
    return out


def spline_predict(F, inc, h, stamps):
    X = design(F, h).loc[stamps]
    p = np.asarray(inc[('spl', h)].predict(X)).ravel() + physical_offset(F, h).loc[stamps].to_numpy()
    w = inc.get('blend_lgb', 0.0)
    if w > 0 and h in inc:
        Xl = fp.inc_design(F, h, inc['cols'], inc['physics']).loc[stamps]
        q = np.mean([np.asarray(m.predict(Xl)).ravel() for m in inc[h]], axis=0)
        p = (1 - w) * p + w * q
    return p


def spline_terms(F, idx, inc, deshrink_factors=None):
    out = []
    for h, lam in fp.INC_SPEC:
        D, st = fp.diff_operator(idx, h)
        if D is None:
            continue
        t = spline_predict(F, inc, h, st)
        if deshrink_factors and h in deshrink_factors:
            f = 1.0 + fp.INC_DESHRINK * (deshrink_factors[h] - 1.0)
            t = t.mean() + (t - t.mean()) * f
        out.append((D, t, lam))
    return out


def run(g, y, cache, blend_lgb, deshrink, label):
    """Score one spline configuration on the outer blocks, with increment diagnostics."""
    rows, diag = [], []
    for name, blk in cache.groupby('block', sort=False):
        gh, F = a47.block_frame(g, blk)
        yh = y.reindex(gh.index)
        d = blk.loc[blk.scope == 'outer'].sort_values('datetime')
        idx = pd.DatetimeIndex(d.datetime)
        origin = pd.Timestamp(d.origin.iloc[0])
        mask = a47.train_mask_before(g, gh, y, origin)
        inc = build_spline_increments(F, yh, mask, a47.SEEDS_INC, blend_lgb)
        fac = {}
        if deshrink:
            for h, _ in fp.INC_SPEC:
                X, off = design(F, h), physical_offset(F, h)
                tgt = (yh - yh.shift(h)).reindex(X.index)
                m = mask.reindex(X.index, fill_value=False)
                m = (m & tgt.notna() & m.shift(h, fill_value=False) & off.notna()
                     & X.notna().all(axis=1))
                r = X.index[m]
                oof = pd.Series(np.nan, index=r)
                for cut in np.array_split(np.arange(len(r)), fp.DESHRINK_FOLDS):
                    va, trn = r[cut], r.difference(r[cut])
                    oof.loc[va] = (np.asarray(spline_model(X).fit(
                        X.loc[trn], (tgt - off).loc[trn]).predict(X.loc[va])).ravel()
                        + off.loc[va].to_numpy())
                fac[h] = float(np.clip(tgt.loc[r].std() / oof.std(), *fp.DESHRINK_CLIP))
        z = a47.solve(d.level.to_numpy(), idx, spline_terms(F, idx, inc, fac or None))
        rows.append(d.assign(recon=z))
        ytrue = pd.Series(d.y.to_numpy(), index=idx)
        for h, _ in fp.INC_SPEC:
            D, st = fp.diff_operator(idx, h)
            act = (ytrue.reindex(st).to_numpy()
                   - ytrue.reindex(st - pd.Timedelta(minutes=30 * h)).to_numpy())
            pr = spline_predict(F, inc, h, st)
            diag.append(dict(block=name, candidate=label, steps=h,
                             inc_rmse=fp.rmse(act, pr),
                             disp=float(pr.std() / act.std()),
                             alpha=inc['alphas'][h],
                             deshrink_factor=fac.get(h, float('nan'))))
    return pd.concat(rows, ignore_index=True), pd.DataFrame(diag)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    cache = pd.read_pickle(a47.CACHE)
    g = fp.load_grid()
    y = g[fp.TARGET]

    # The incumbent, rebuilt here so the comparison is on identical rows and identical seeds.
    base = a47.score_config(g, y, cache, physics=True, deshrink=fp.INC_DESHRINK)
    ref = a47.report(base, 'incumbent_physics_dsh')
    rows, diags, preds = [ref], [], {}
    print('incumbent pooled %.5f' % ref['pooled'])

    for label, kw in (('spline', dict(blend_lgb=0.0, deshrink=True)),
                      ('spline_lgb_half', dict(blend_lgb=0.5, deshrink=True))):
        t = time.time()
        P, D = run(g, y, cache, kw['blend_lgb'], kw['deshrink'], label)
        preds[label] = P
        r = a47.report(P, label, ref)
        rows.append(r)
        diags.append(D)
        print('  %-16s pooled %.5f  (%+.5f)  [%.0f s]' % (label, r['pooled'],
                                                          r['d_pooled'], time.time() - t))
        print(D.to_string(index=False, float_format=lambda v: '%.4f' % v))
        bs = a47.bootstrap(base, P)
        rows[-1].update({'boot_' + k: v for k, v in bs.items()})
        print('  bootstrap dMSE %+.4f [%+.4f, %+.4f]' % (bs['mean'], bs['lo'], bs['hi']))

    R = pd.DataFrame(rows)
    R.to_csv(OUT / 'physical_spline.csv', index=False)
    pd.concat(diags).to_csv(OUT / 'physical_spline_increments.csv', index=False)
    (OUT / 'physical_spline.json').write_text(R.to_json(orient='records', indent=2))
    print('\n' + R.to_string(index=False))
    win = R.loc[R.get('promotable', False) == True, 'candidate'].tolist()
    print('\nPASSES THE SECTION-180 BAR:', win or 'none')


if __name__ == '__main__':
    main()
