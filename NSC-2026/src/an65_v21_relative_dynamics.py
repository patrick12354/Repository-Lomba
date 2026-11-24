"""Session 29, arm B: an increment model whose inputs are CHANGES, not sensor levels.

The shift the audit measured is in pressure. Test forecast rows average 1013.20 hPa against a
1008.94 training mean; 14.99% sit outside the training 1st-99th percentile and **6.27% outside
the training min-max altogether**. Temperature is colder but stays inside the observed range, and
CO2 barely moves. A gradient-boosted tree cannot extrapolate: every split on absolute pressure
sends those 6.27% of rows down whichever branch the largest training value happened to take.

The incumbent increment design hands the model all 118 columns of `F` -- absolute pressure,
absolute CO2, their rolling means and their lags -- plus, since section 202, seven more absolute
pressure and CO2 lags. Those columns can identify WHICH EPISODE a row belongs to as easily as
they describe its dynamics, and when the test episode sits outside the training range the
identification is worthless while the dynamics are still there.

So this arm changes the inductive bias rather than the capacity. It keeps the v21 level
prediction untouched -- `p` is not re-fitted, and pressure information is still in the level
members exactly as it always was -- and replaces only the CHANGE model's design with one built
from differences:

* absolute where thermodynamics needs it: T, es(T), log es(T), the endpoint ratio es(T_{t-h})/es(T_t),
  the closed-form `dRH_const_e` from section 170, the diurnal harmonics, and the dewpoint-proxy
  RH level that sets the scale a fractional change acts on;
* relative everywhere else: dT over 1/2/4/8/16/24/48 steps, the same differences for pressure and
  CO2, causal rolling range and standard deviation over 2/8/24 hours, and the RH proxy's lags
  expressed as changes against its current value.

Nothing about absolute pressure or absolute CO2 survives, which is a testable property, not a
claim: adding any constant to the entire pressure history must leave every column and every
prediction bit-identical. `tests/test_v21_relative_dynamics.py` checks that, and checks it does
NOT hold for temperature, because temperature is deliberately absolute.

De-shrink is OFF. Section 206 found most of the package's B3 loss appears at the expansion step
and that lag columns partly undid it on test, so mixing expansion into a new representation would
make the result unattributable in exactly the way the public comparison already is.

    .venv/Scripts/python.exe src/an65_v21_relative_dynamics.py
"""
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import lightgbm as lgb

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
import final_pipeline as fp
import an47_v21_forward_benchmark as a47
import an59_v21_candidate_contract as c

OUT = ROOT / 'outputs' / 'audit_v21_s29'
DIFF_LAGS = (1, 2, 4, 8, 16, 24, 48)      # half-hour steps: 30 min to 24 h
ROLL_WINS = (4, 16, 48)                   # causal windows: 2 h, 8 h, 24 h
REL_COLS = ('pressure', 'co2')            # made invariant to an additive sensor offset
ANCHOR = 'v21'


def rel_design(F, h):
    """Compact change-based design for the h-step increment. No absolute pressure or CO2."""
    out = {}
    # --- absolute, and deliberately so: thermodynamics is not translation invariant ---
    out['T'] = F['T']
    out['esT'] = F['esT']
    out['log_esT'] = F['log_esT']
    ratio = F['esT'].shift(h) / F['esT']
    out['es_ratio'] = ratio
    out['dRH_const_e'] = F['rh_tmin48'] * (ratio - 1.0)
    out['rh_tmin48'] = F['rh_tmin48']            # the scale a fractional change acts on
    for col in ('sin1', 'cos1', 'sin2', 'cos2', 'tod'):
        if col in F.columns:
            out[col] = F[col]
    # --- relative: differences, ranges and spreads only ---
    #
    # Every column below is translation invariant in exact arithmetic, but not in float64 if it
    # is computed on the raw series. Pressure sits near 1009 hPa, and `rolling().std()` uses a
    # running-sums formula, so subtracting two nearly-equal large numbers loses about eight
    # digits: a +25 hPa offset moves `pressure_sd4` by 7e-9 and a +1e6 offset by 3e-6, growing
    # WITH the offset, which is the signature of cancellation rather than of retained level.
    # Re-centring each series on its own first observation -- a constant over the whole column,
    # so every difference, range and spread is mathematically unchanged -- keeps the arithmetic
    # in a well-conditioned range and makes the invariance exact to rounding.
    cen = {c: F[c] - F[c].iloc[0] for c in ('T', 'rh_tmin48') + REL_COLS if c in F.columns}
    for k in DIFF_LAGS:
        out['dT_%d' % k] = cen['T'] - cen['T'].shift(k)
        out['drh_%d' % k] = cen['rh_tmin48'] - cen['rh_tmin48'].shift(k)
        for col in REL_COLS:
            if col in cen:
                out['d%s_%d' % (col, k)] = cen[col] - cen[col].shift(k)
    for w in ROLL_WINS:
        for col in ('T',) + REL_COLS:
            if col not in cen:
                continue
            r = cen[col].rolling(w, min_periods=w)        # causal: no centre, no partial window
            out['%s_rng%d' % (col, w)] = r.max() - r.min()
            out['%s_sd%d' % (col, w)] = r.std()
    return pd.DataFrame(out, index=F.index)


def fit_relative(F, y, mask, seeds):
    """One LightGBM per frozen horizon on the relative design. Same estimator, same
    hyperparameters, same seeds, same horizons as the incumbent -- only the columns differ."""
    out = {'relative': True}
    for h, _ in fp.INC_SPEC:
        X = rel_design(F, h)
        tgt = (y - y.shift(h)).reindex(X.index)
        m = mask.reindex(X.index, fill_value=False)
        m = m & tgt.notna() & m.shift(h, fill_value=False)
        out[h] = [lgb.LGBMRegressor(random_state=s, **fp.INC_KW).fit(X.loc[m], tgt.loc[m])
                  for s in seeds]
        out[('n', h)] = int(m.sum())
        out[('cols', h)] = list(X.columns)
    return out


def relative_terms(F, idx, inc):
    """`a47.increment_terms` on the relative design, de-shrink deliberately absent."""
    out = []
    for h, lam in fp.INC_SPEC:
        D, st = fp.diff_operator(idx, h)
        if D is None:
            out.append((None, None, lam))
            continue
        X = rel_design(F, h).loc[st]
        out.append((D, np.mean([m.predict(X) for m in inc[h]], axis=0), lam))
    return out


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    g = fp.load_grid()
    y = g[fp.TARGET]
    cache = a47.load_cache(a47.CACHE_S27, a47.MANIFEST_S27)
    seeds, feats = a47.SEEDS_INC, {}

    print('control : v21 increment (no physics, no de-shrink, no lags)')
    t = time.time()
    base = a47.score_config(g, y, cache, physics=False, deshrink=0.0, seeds=seeds,
                            scopes=('outer',), feature_cache=feats)
    frozen = pd.read_pickle(a47.OUT_S27 / 'preds_v21_increment.pkl')
    j = c.join_predictions(frozen.loc[frozen.scope == 'outer'], base)
    np.testing.assert_allclose(j.recon, j.recon_q, atol=1e-9, rtol=0)
    ref = a47.report(base, ANCHOR)
    print('  pooled %.6f  (%.0f s)  [reproduces the frozen v21 predictions exactly]'
          % (ref['pooled'], time.time() - t), flush=True)

    print('candidate: relative-dynamics increments, de-shrink off, level stack untouched')
    t = time.time()
    P = a47.score_config(g, y, cache, physics=False, deshrink=0.0, seeds=seeds,
                         scopes=('outer',), inc_builder=fit_relative,
                         term_builder=relative_terms, feature_cache=feats)
    r = a47.report(P, 'relative_dynamics', ref)
    print('  pooled %.6f  (%.0f s)' % (r['pooled'], time.time() - t), flush=True)

    b = a47.bootstrap_pair(base, P)
    r['boot3_lo'], r['boot3_hi'] = b['b3d']['lo'], b['b3d']['hi']
    r['boot7_lo'], r['boot7_hi'] = b['b7d']['lo'], b['b7d']['hi']
    r['days_improved'] = b['worst_day']['days_improved']
    diag = []
    jj = c.join_predictions(base, P)
    for bl, d in jj.groupby('block'):
        diag.append(dict(arm='relative_dynamics', vs=ANCHOR, block=bl,
                         **c.direction(d.y, d.recon, d.recon_q)))

    # Design width and offset invariance, recorded rather than asserted in prose.
    gh, F = a47.frame_at(g, cache.horizon_end.max(), feats)
    widths = {h: rel_design(F, h).shape[1] for h, _ in fp.INC_SPEC}
    g2 = g.copy()
    g2['pressure'] = g2['pressure'] + 25.0
    _, F2 = a47.frame_at(g2, cache.horizon_end.max())
    same = {h: bool(np.allclose(rel_design(F, h).to_numpy(),
                                rel_design(F2, h).to_numpy(), equal_nan=True))
            for h, _ in fp.INC_SPEC}

    R = pd.DataFrame([ref, r])
    D = pd.DataFrame(diag)
    print('\n' + R.to_string(index=False))
    print('\ndirection vs %s\n' % ANCHOR + D.to_string(index=False))
    print('\nbootstrap vs %s: 3d %+.4f [%+.4f, %+.4f] | 7d %+.4f [%+.4f, %+.4f] | %d/%d days'
          % (ANCHOR, b['b3d']['mean'], b['b3d']['lo'], b['b3d']['hi'],
             b['b7d']['mean'], b['b7d']['lo'], b['b7d']['hi'],
             b['worst_day']['days_improved'], b['worst_day']['days']))
    print('design columns %s  (incumbent physics design is 138, with lags 158)' % widths)
    print('pressure +25 hPa leaves the design identical: %s' % same)

    R.to_csv(OUT / 'relative_dynamics.csv', index=False)
    D.to_csv(OUT / 'relative_dynamics_direction.csv', index=False)
    P.to_pickle(OUT / 'preds_relative_dynamics.pkl')
    c.write_json(OUT / 'relative_dynamics.json', dict(
        anchor=ANCHOR, diff_lags=list(DIFF_LAGS), roll_wins=list(ROLL_WINS),
        rel_cols=list(REL_COLS), deshrink=False, seeds=list(seeds),
        design_columns={str(k): v for k, v in widths.items()},
        pressure_offset_invariant={str(k): v for k, v in same.items()},
        results=json.loads(R.to_json(orient='records')),
        direction=json.loads(D.to_json(orient='records')), bootstrap=b,
        code={'src/an65_v21_relative_dynamics.py': a47.md5(Path(__file__)),
              'final_pipeline.py': a47.md5(ROOT / 'final_pipeline.py')},
        level_cache_md5=a47.md5(a47.CACHE_S27)))
    print('\nwrote relative_dynamics.csv and the predictions to %s' % OUT)


if __name__ == '__main__':
    main()
