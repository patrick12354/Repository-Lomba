"""Session 23: where the error that is LEFT actually lives, and what each remaining route
could be worth even if it worked perfectly.

Sessions 22 and 23 screened variants and mechanisms and mostly found noise. This asks the
prior question instead -- what is still broken, and is it the kind of thing that any model
could fix -- so the next mechanism is chosen from a measurement rather than from a hunch.

Three things, all on the two non-overlapping production holdouts (1440 rows over 31 days,
truncated feature horizons, chronological meta), scoring the shipped v16 + increment:

1. **Decomposition.** Per-day mean error and the deviation from it are orthogonal, so their
   mean squares add to 100% of MSE exactly.
2. **Oracle ceilings.** What would remain if an ORACLE removed each day's mean error, or each
   hour-of-day's, or one global offset. These are upper bounds no model can beat, so a route
   whose ceiling is small is closed regardless of how it is implemented.
3. **Reachability.** Whether the day-level error can be predicted at all -- from daily
   aggregates of the exogenous sensors, scored leave-one-day-out; and from the level error
   observed just before the origin, which is the only information source the exogenous
   features do not already contain.

    .venv/Scripts/python.exe src/an40_error_anatomy.py
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import RidgeCV
from sklearn.model_selection import LeaveOneOut, cross_val_predict

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import final_pipeline as fp

OUT = ROOT / 'outputs' / 'audit_v20'
BACKBONE = 'v16'
DAILY_FEATURES = ['T', 'co2', 'pressure', 'rh_tmin48', 'T_rng48', 'T_min48', 'p_tend24h',
                  'co2_tend24h', 'esT', 'daily_mean_temperature', 'T_minus_min48', 'p_sd24h']


def decompose(P, col):
    e = (P[col] - P.y).to_numpy()
    se = e ** 2
    dm = P.assign(e=e).groupby('day').e.transform('mean').to_numpy()
    return dict(rmse=float(np.sqrt(se.mean())), bias=float(e.mean()),
                day_level_share=float(np.mean(dm ** 2) / se.mean()),
                within_day_share=float(np.mean((e - dm) ** 2) / se.mean()),
                worst10pct_sse_share=float(np.sort(se)[-int(.1 * len(se)):].sum() / se.sum()),
                lag1=float(pd.Series(e).autocorr()))


def main():
    g = fp.load_grid()
    F = fp.make_features(g)
    P = pd.read_pickle(OUT / 'increment_production_predictions.pkl')
    P = P.loc[P.model == BACKBONE].copy()
    dt = pd.DatetimeIndex(P.datetime)
    P['day'], P['tod'] = dt.normalize(), dt.hour + dt.minute / 60.0
    # B3 overlaps B1 and B2, so it is excluded from every number that is meant to be a
    # measurement rather than a replicate.
    Q = P.loc[P.block != 'B3_shift7d'].copy()
    report = {'rows': int(len(Q)), 'days': int(Q.day.nunique())}

    print('DECOMPOSITION on %d rows over %d days' % (len(Q), Q.day.nunique()))
    for col in ('base', 'increment'):
        report[col] = decompose(Q, col)
        d = report[col]
        print('  %-10s RMSE %.4f  bias %+.4f | day-level %.2f%%  within-day %.2f%%'
              ' | worst 10%% carry %.2f%% | lag1 %.4f'
              % (col, d['rmse'], d['bias'], 100 * d['day_level_share'],
                 100 * d['within_day_share'], 100 * d['worst10pct_sse_share'], d['lag1']))
    print('  the increment is mean-preserving, so it can only move the within-day part')

    e = (Q.increment - Q.y).to_numpy()
    r0 = float(np.sqrt((e ** 2).mean()))
    print('\nORACLE CEILINGS -- upper bounds, not achievable results')
    ceil = {'current': r0}
    for name, key in (('per_day', 'day'), ('per_hour_of_day', 'tod'), ('per_block', 'block')):
        adj = e - Q.assign(e=e).groupby(key).e.transform('mean').to_numpy()
        ceil[name] = float(np.sqrt((adj ** 2).mean()))
        print('  remove each %-18s mean error  %.4f  (%+.4f)'
              % (name, ceil[name], ceil[name] - r0))
    ceil['global'] = float(np.sqrt(((e - e.mean()) ** 2).mean()))
    print('  remove one %-19s offset      %.4f  (%+.4f)'
          % ('global', ceil['global'], ceil['global'] - r0))
    report['oracle'] = ceil
    print('  -> per-day level holds %.1f%% of the MSE and within-day %.1f%%; neither is'
          ' small, so "all the headroom is daily" was wrong'
          % (100 * report['increment']['day_level_share'],
             100 * report['increment']['within_day_share']))

    # ---- is the day level reachable from the sensors? ----
    day_err = Q.groupby('day').apply(lambda d: (d.increment - d.y).mean())
    D = F.loc[pd.DatetimeIndex(Q.datetime).unique(), DAILY_FEATURES].copy()
    D['day'] = pd.DatetimeIndex(D.index).normalize()
    agg = D.groupby('day').agg(['mean', 'std'])
    agg.columns = ['_'.join(c) for c in agg.columns]
    agg = agg.loc[day_err.index].dropna(axis=1)
    corr = agg.apply(lambda s: float(np.corrcoef(s, day_err)[0, 1])).sort_values(
        key=lambda v: v.abs(), ascending=False)
    X = ((agg - agg.mean()) / agg.std()).to_numpy()
    yv = day_err.to_numpy()
    pred = cross_val_predict(RidgeCV(alphas=np.logspace(-2, 4, 40)), X, yv, cv=LeaveOneOut())
    r2 = float(1 - ((yv - pred) ** 2).sum() / ((yv - yv.mean()) ** 2).sum())
    # Session 26. `np.repeat` assumed Q was sorted by day; it is not -- the cache is stacked
    # B1 then B2 while `day_err.index` starts at B2, so every one of the 1440 rows got the
    # WRONG day's correction. Map by date instead. See progress.md section 181.
    pred_day = pd.Series(pred, index=day_err.index)
    adj = e - Q['day'].map(pred_day).to_numpy()
    assert np.isfinite(adj).all()
    honest = float(np.sqrt((adj ** 2).mean()))
    print('\nIS THE DAY LEVEL PREDICTABLE FROM THE SENSORS?')
    print('  %d days, %d daily features, day-error sd %.4f' % (len(agg), agg.shape[1], yv.std()))
    print('  strongest |corr|:', ', '.join('%s %+.3f' % (k, v) for k, v in corr.head(4).items()))
    print('  leave-one-day-out R2 %+.4f' % r2)
    print('  applying that honest prediction: %.4f -> %.4f (%+.4f), against %+.4f for a'
          ' global offset' % (r0, honest, honest - r0, ceil['global'] - r0))
    report['day_level_predictability'] = dict(
        days=int(len(agg)), features=int(agg.shape[1]), day_error_sd=float(yv.std()),
        loo_r2=r2, honest_rmse=honest, honest_gain=honest - r0,
        top_correlations={k: float(v) for k, v in corr.head(6).items()})

    # ---- does the level error persist across the origin? ----
    print('\nDOES THE DAY-LEVEL ERROR PERSIST DAY TO DAY?')
    persist = {}
    for b, d in P.groupby('block'):
        s = d.groupby('day').apply(lambda t: (t.increment - t.y).mean())
        eb = (d.increment - d.y).to_numpy()
        anchor = float(s.iloc[0])
        row = dict(days=int(len(s)), sd=float(s.std()),
                   lag1=float(s.autocorr(1)), lag2=float(s.autocorr(2)))
        for k in (1, 3, 15):
            m = d.day.isin(s.index[:k]).to_numpy()
            before = float(np.sqrt((eb[m] ** 2).mean()))
            after = float(np.sqrt(((eb[m] - anchor) ** 2).mean()))
            row['anchor_first%dd' % k] = after - before
        persist[b] = row
        print('  %-11s n=%2d sd %.3f lag1 %+.3f lag2 %+.3f | oracle day-1 anchor applied to'
              ' first 1/3/15 days: %+.3f %+.3f %+.3f'
              % (b, row['days'], row['sd'], row['lag1'], row['lag2'],
                 row['anchor_first1d'], row['anchor_first3d'], row['anchor_first15d']))
    report['day_level_persistence'] = persist
    print('  -> an anchor helps day one and hurts from day two; the horizon is fifteen days')

    (OUT / 'error_anatomy.json').write_text(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
