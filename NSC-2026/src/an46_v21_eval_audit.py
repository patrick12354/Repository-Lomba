"""Session 26, Tahap 0: re-derive every number the last four sessions decided on, from the
artifacts those sessions left behind, and print the ones that do not survive.

Nothing here trains a model. It reads `outputs/audit_v20/*` and recomputes, so a claim that
disagrees with this script is a claim about arithmetic, not about a modelling choice.

Four audits:

1. **Date pairing in the daily-correction diagnostic.** `an40_error_anatomy.py` applied the
   leave-one-day-out daily prediction with `np.repeat(pred, group_sizes)`, which assumes the
   prediction frame is in the same order as the row frame. It is not: the cache is stacked B1
   then B2 while `groupby('day')` starts at B2's earlier dates, so every row got another day's
   correction. Both versions are recomputed here.

2. **What "pooled" meant.** `an36` summed B1, B2 AND B3 into one RMSE even though B3 is a
   7-day shift overlapping both; `an41` printed the MEAN of block RMSEs under the same name.
   Neither is `sqrt(sum SSE / sum n)` over the non-overlapping blocks.

3. **Seed counts.** `an36` calls `fit_increments(F, y, mask)` with no `seeds` argument, so the
   cached "production" numbers are one-seed while the shipped file and `an41` are five-seed.
   The default is read out of the signature rather than asserted from memory.

4. **Where the error is.** Hour-of-day slices, the worst days, and the day-level/within-day
   split, on the 1440 non-overlapping rows -- with the day counts that section 146 left out.

    .venv/Scripts/python.exe src/an46_v21_eval_audit.py
"""
import hashlib
import inspect
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

V20 = ROOT / 'outputs' / 'audit_v20'
OUT = ROOT / 'outputs' / 'audit_v21'
SUBS = ROOT / 'outputs' / 'submissions'
BACKBONE = 'v16'
PRIMARY = ('B1_last15d', 'B2_prev15d')
DAILY_FEATURES = ['T', 'co2', 'pressure', 'rh_tmin48', 'T_rng48', 'T_min48', 'p_tend24h',
                  'co2_tend24h', 'esT', 'daily_mean_temperature', 'T_minus_min48', 'p_sd24h']
TRACKED = ['v21_increment_v16.csv', 'v21_increment_v16_phys.csv',
           'v21_increment_v16_phys_dsh.csv']


def md5(p):
    return hashlib.md5(Path(p).read_bytes()).hexdigest()


def sse_pooled(rmses, counts):
    r, n = np.asarray(rmses, float), np.asarray(counts, float)
    return float(np.sqrt(np.sum(r ** 2 * n) / n.sum()))


def audit_date_pairing(Q, F):
    """Section 163's daily correction, computed both ways from the same estimates."""
    e = (Q.increment - Q.y).to_numpy()
    day_err = Q.groupby('day').apply(lambda d: (d.increment - d.y).mean())
    D = F.loc[pd.DatetimeIndex(Q.datetime).unique(), DAILY_FEATURES].copy()
    D['day'] = pd.DatetimeIndex(D.index).normalize()
    agg = D.groupby('day').agg(['mean', 'std'])
    agg.columns = ['_'.join(c) for c in agg.columns]
    agg = agg.loc[day_err.index].dropna(axis=1)
    X = ((agg - agg.mean()) / agg.std()).to_numpy()
    yv = day_err.to_numpy()
    pred = cross_val_predict(RidgeCV(alphas=np.logspace(-2, 4, 40)), X, yv, cv=LeaveOneOut())
    r2 = float(1 - ((yv - pred) ** 2).sum() / ((yv - yv.mean()) ** 2).sum())

    wrong = e - np.repeat(pred, Q.groupby('day').size().to_numpy())
    right = e - Q['day'].map(pd.Series(pred, index=day_err.index)).to_numpy()
    mism = int((np.repeat(pred, Q.groupby('day').size().to_numpy())
                != Q['day'].map(pd.Series(pred, index=day_err.index)).to_numpy()).sum())
    res = dict(days=int(len(agg)), loo_r2=r2, rows=int(len(Q)), mispaired_rows=mism,
               baseline=float(np.sqrt((e ** 2).mean())),
               as_reported_section163=float(np.sqrt((wrong ** 2).mean())),
               correctly_paired=float(np.sqrt((right ** 2).mean())))
    res['claimed_gain'] = res['as_reported_section163'] - res['baseline']
    res['actual_effect'] = res['correctly_paired'] - res['baseline']
    print('\n1. DATE PAIRING IN THE DAILY CORRECTION (%d rows, %d days)'
          % (res['rows'], res['days']))
    print('   rows given another day\'s correction: %d of %d' % (mism, len(Q)))
    print('   leave-one-day-out R2 %+.4f  (unchanged by the pairing fix)' % r2)
    print('   increment baseline            %.8f' % res['baseline'])
    print('   as reported in section 163    %.8f  (%+.5f, the withdrawn gain)'
          % (res['as_reported_section163'], res['claimed_gain']))
    print('   correctly paired by date      %.8f  (%+.5f, it HURTS)'
          % (res['correctly_paired'], res['actual_effect']))
    return res


def audit_pooled(P):
    """Every "pooled" figure the log carries, recomputed under one definition."""
    rows = []
    Q = P.loc[P.block.isin(PRIMARY)]
    for col, label in (('base', 'cache level v16'), ('increment', 'cache increment, 1 seed')):
        per = [(fp.rmse(d.y, d[col]), len(d)) for _, d in Q.groupby('block')]
        rows.append(dict(source=label, pooled_b1b2=sse_pooled(*zip(*per)),
                         mean_block_rmse=float(np.mean([r for r, _ in per])),
                         with_b3=fp.rmse(P.y, P[col]), n=int(sum(n for _, n in per))))

    disp = V20 / 'increment_dispersion.csv'
    if disp.exists():
        R = pd.read_csv(disp)
        for cand, label in (('incumbent', 'physics screen, 1 seed'),
                            ('deshrink_half', 'physics + half deshrink screen, 1 seed'),
                            ('deshrink', 'physics + full deshrink screen, 1 seed')):
            c = R.loc[R.candidate == cand].set_index('block')
            if not len(c):
                continue
            prim = [b for b in c.index if b in PRIMARY]
            rows.append(dict(source=label,
                             pooled_b1b2=sse_pooled(c.loc[prim, 'reconciled'],
                                                    [720] * len(prim)),
                             mean_block_rmse=float(c.reconciled.mean()),
                             with_b3=float('nan'), n=720 * len(prim)))

    orc = V20 / 'increment_oracle.csv'
    if orc.exists():
        T = pd.read_csv(orc, index_col=0)
        cols = [c for c in T.columns if c.startswith('B')]
        for var, label in (('shipped increment models', 'oracle script, 5 seeds'),
                           ('ORACLE increments', 'oracle script, true increments')):
            if var not in T.index:
                continue
            rows.append(dict(source=label,
                             pooled_b1b2=sse_pooled(T.loc[var, cols], [720] * len(cols)),
                             mean_block_rmse=float(T.loc[var, cols].mean()),
                             with_b3=float('nan'), n=720 * len(cols)))
    R = pd.DataFrame(rows)
    print('\n2. WHAT "POOLED" MEANT  (pooled_b1b2 = sqrt(sum SSE / sum n), B1+B2 only)')
    print(R.to_string(index=False, float_format=lambda v: '%.6f' % v))
    return R


def audit_seeds():
    sig = inspect.signature(fp.fit_increments)
    default = sig.parameters['seeds'].default
    src = (ROOT / 'src' / 'an36_increment_production.py').read_text(encoding='utf-8')
    a36_call = [l.strip() for l in src.splitlines() if 'fit_increments(' in l]
    res = dict(fit_increments_default_seeds=len(default), shipped_inc_seeds=fp.INC_SEEDS,
               an36_call=a36_call, an36_seeds_used=len(default),
               an41_seeds_used=fp.INC_SEEDS)
    print('\n3. SEED COUNTS')
    print('   fit_increments default          %d seed(s)  %s' % (len(default), default))
    print('   an36 production cache call      %s' % (a36_call[0] if a36_call else '?'))
    print('   -> the cached "production" scores are %d-seed; the shipped file and an41 are %d'
          % (len(default), fp.INC_SEEDS))
    return res


def audit_breakdown(Q):
    e = (Q.increment - Q.y).to_numpy()
    sse = float((e ** 2).sum())
    hour = pd.DatetimeIndex(Q.datetime).hour
    rows = []
    for lo in (0, 6, 12, 18):
        m = (hour >= lo) & (hour < lo + 6)
        rows.append(dict(slice='%02d-%02d' % (lo, lo + 5), n=int(m.sum()),
                         days=int(pd.DatetimeIndex(Q.datetime[m]).normalize().nunique()),
                         rmse=float(np.sqrt((e[m] ** 2).mean())),
                         sse_share=float((e[m] ** 2).sum() / sse)))
    H = pd.DataFrame(rows)
    day_sse = pd.Series(e ** 2).groupby(Q.day.to_numpy()).sum().sort_values(ascending=False)
    dm = Q.assign(e=e).groupby('day').e.transform('mean').to_numpy()
    res = dict(rows=int(len(Q)), days=int(Q.day.nunique()), sse=sse,
               hours=H.to_dict('records'),
               worst_days=[dict(day=str(pd.Timestamp(d).date()), sse=float(v),
                                share=float(v / sse)) for d, v in day_sse.head(3).items()],
               worst3_share=float(day_sse.head(3).sum() / sse),
               day_level_share=float(np.mean(dm ** 2) / np.mean(e ** 2)),
               within_day_share=float(np.mean((e - dm) ** 2) / np.mean(e ** 2)),
               per_block={b: dict(rmse=fp.rmse(d.y, d.increment), n=int(len(d)))
                          for b, d in Q.groupby('block')})
    print('\n4. WHERE THE ERROR IS  (%d rows, %d days, total SSE %.3f)'
          % (res['rows'], res['days'], sse))
    print(H.to_string(index=False, float_format=lambda v: '%.4f' % v))
    for d in res['worst_days']:
        print('   worst day %s  SSE %.1f (%.2f%%)' % (d['day'], d['sse'], 100 * d['share']))
    print('   three worst days carry %.2f%% of SSE' % (100 * res['worst3_share']))
    print('   day-level %.2f%% / within-day %.2f%% of MSE -- both large'
          % (100 * res['day_level_share'], 100 * res['within_day_share']))
    for b, v in res['per_block'].items():
        print('   %-11s RMSE %.5f on %d rows' % (b, v['rmse'], v['n']))
    return res


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    g = fp.load_grid()
    F = fp.make_features(g)
    P = pd.read_pickle(V20 / 'increment_production_predictions.pkl')
    P = P.loc[P.model == BACKBONE].copy()
    P['day'] = pd.DatetimeIndex(P.datetime).normalize()
    Q = P.loc[P.block.isin(PRIMARY)].copy()
    assert len(Q) == 1440 and Q.datetime.is_unique

    rep = dict(cache_rows=int(len(P)), primary_rows=int(len(Q)),
               artifacts={f: md5(SUBS / f) for f in TRACKED if (SUBS / f).exists()})
    print('SUBMISSION ARTIFACTS ON DISK')
    for f, h in rep['artifacts'].items():
        print('   %-34s %s' % (f, h))

    rep['date_pairing'] = audit_date_pairing(Q, F)
    pooled = audit_pooled(P)
    rep['pooled'] = pooled.to_dict('records')
    rep['seeds'] = audit_seeds()
    rep['breakdown'] = audit_breakdown(Q)

    pooled.to_csv(OUT / 'eval_audit_pooled.csv', index=False)
    (OUT / 'eval_audit.json').write_text(json.dumps(rep, indent=2, default=str))
    print('\nwrote outputs/audit_v21/eval_audit.json')


if __name__ == '__main__':
    main()
