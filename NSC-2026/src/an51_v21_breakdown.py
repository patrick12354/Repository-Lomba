"""Session 26, the section-3 breakdown redone on five-seed predictions for every control.

Section 146's breakdown was hour-of-day and per-day mean on a one-seed cache, and section 181
showed the seed count alone is worth 0.023 of pooled RMSE -- more than most of the deltas those
sections were adjudicating. This redoes it on the Tahap 1 predictions, adds the slices the audit
asked for, and reports the number of DAYS behind every row count, because 360 rows over 30 days
and 360 rows over 3 days are not the same evidence.

The slices, all cut at thresholds taken from the TRAINING side of each origin so nothing here is
defined by the window being described:

  hour band x phase        warming or cooling, from the sign of the 2-hour temperature change
  |dT| quantile            terciles of the absolute 2-hour temperature change
  lead time                0-6h, 6-24h, 1-3d, 3-7d, 7-15d from the origin
  repaired sensors         rows where a fast sensor was missing or Hampel-flagged, and the
                           distance in hours to the nearest such row
  actual RH band           DIAGNOSTIC ONLY -- terciles of the true humidity and of its 2-hour
                           change. These read the label and can never become inference features;
                           they are here to say whether the error concentrates in wet or dry air.

Every slice carries bias, RMSE, share of SSE, and the day-level/within-day split of its own MSE.

    .venv/Scripts/python.exe src/an51_v21_breakdown.py
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'src'))
import final_pipeline as fp
import an47_v21_forward_benchmark as a47

OUT = ROOT / 'outputs' / 'audit_v21'
LEADS = [(0, 6, '0-6h'), (6, 24, '6-24h'), (24, 72, '1-3d'), (72, 168, '3-7d'),
         (168, 360, '7-15d')]


def repaired_rows(g):
    """Rows where any fast sensor was absent from the grid or removed by the Hampel filter --
    the places `clean_exog` had to invent a value."""
    bad = pd.Series(False, index=g.index)
    for c in fp.FAST:
        raw = g[c]
        bad |= raw.isna() | (fp.hampel(raw).isna() & raw.notna())
    return bad


def slice_stats(d, e, name, value):
    if not len(d):
        return None
    dm = pd.Series(e, index=d.index).groupby(d.day).transform('mean').to_numpy()
    return dict(dimension=name, slice=str(value), n=int(len(d)),
                days=int(d.day.nunique()), rmse=float(np.sqrt(np.mean(e ** 2))),
                bias=float(e.mean()), sse=float((e ** 2).sum()),
                day_level_share=float(np.mean(dm ** 2) / np.mean(e ** 2)),
                within_day_share=float(np.mean((e - dm) ** 2) / np.mean(e ** 2)))


def breakdown(P, g, F, label):
    P = P.loc[P.score].copy()
    idx = pd.DatetimeIndex(P.datetime)
    P.index = range(len(P))
    P['day'] = idx.normalize()
    P['hour'] = idx.hour
    P['lead'] = (idx - pd.DatetimeIndex(P.origin)).total_seconds() / 3600.0
    dT = F['T'].diff(4).reindex(idx).to_numpy()
    P['phase'] = np.where(dT >= 0, 'warming', 'cooling')
    P['band'] = pd.cut(P.hour, [-1, 5, 11, 17, 23],
                       labels=['00-05', '06-11', '12-17', '18-23'])
    bad = repaired_rows(g)
    P['repaired'] = bad.reindex(idx).fillna(False).to_numpy()
    pos = pd.Series(np.arange(len(g)), index=g.index)
    badpos = pos[bad.to_numpy()].to_numpy()
    here = pos.reindex(idx).to_numpy()
    P['gap_hours'] = (np.abs(here[:, None] - badpos[None, :]).min(axis=1) / 2.0
                      if len(badpos) else np.inf)

    e = (P.recon - P.y).to_numpy()
    total = float((e ** 2).sum())
    rows = [slice_stats(P, e, 'all', 'all')]

    # Thresholds from the training side of each block's origin, not from the scored rows.
    tq, rq, dq = {}, {}, {}
    for b, d in P.groupby('block'):
        o = pd.Timestamp(d.origin.iloc[0])
        tr = F.index[(F.index <= o) & (g.is_test == 0).reindex(F.index).fillna(False)]
        tq[b] = np.nanquantile(F['T'].diff(4).reindex(tr).abs(), [1 / 3, 2 / 3])
        yy = g[fp.TARGET].reindex(tr)
        rq[b] = np.nanquantile(yy, [1 / 3, 2 / 3])
        dq[b] = np.nanquantile(yy.diff(4).abs(), [1 / 3, 2 / 3])
    P['absdT_q'] = [np.searchsorted(tq[b], v) for b, v in zip(P.block, np.abs(dT))]
    dRH = np.abs(P.y.to_numpy() - pd.Series(P.y.to_numpy(), index=idx)
                 .reindex(idx - pd.Timedelta(hours=2)).to_numpy())
    P['rh_q'] = [np.searchsorted(rq[b], v) for b, v in zip(P.block, P.y)]
    P['dRH_q'] = [np.searchsorted(dq[b], v) if np.isfinite(v) else -1
                  for b, v in zip(P.block, dRH)]

    for col, dim in (('block', 'block'), ('band', 'hour band'), ('phase', 'phase'),
                     ('absdT_q', '|dT| tercile'), ('repaired', 'repaired sensors'),
                     ('rh_q', 'actual RH tercile (diagnostic)'),
                     ('dRH_q', '|dRH| tercile (diagnostic)')):
        for v, d in P.groupby(col, observed=True):
            rows.append(slice_stats(d, e[d.index.to_numpy()], dim, v))
    for a, b_, nm in LEADS:
        m = (P.lead >= a) & (P.lead < b_)
        rows.append(slice_stats(P.loc[m], e[m.to_numpy()], 'lead time', nm))
    for lo, hi, nm in ((0, 6, '<=6h from a repair'), (6, 24, '6-24h'), (24, 1e9, '>24h')):
        m = (P.gap_hours >= lo) & (P.gap_hours < hi)
        rows.append(slice_stats(P.loc[m], e[m.to_numpy()], 'distance to repair', nm))
    for b, d in P.groupby('band', observed=True):
        for ph, dd in d.groupby('phase'):
            rows.append(slice_stats(dd, e[dd.index.to_numpy()], 'hour band x phase',
                                    '%s %s' % (b, ph)))

    R = pd.DataFrame([r for r in rows if r])
    R['sse_share'] = R.sse / total
    R['candidate'] = label
    day_sse = pd.Series(e ** 2).groupby(P.day.to_numpy()).sum().sort_values(ascending=False)
    worst = [dict(day=str(pd.Timestamp(d).date()), sse=float(v), share=float(v / total))
             for d, v in day_sse.head(3).items()]
    return R, worst


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    cache = pd.read_pickle(a47.CACHE)
    g = fp.load_grid()
    y = g[fp.TARGET]
    F = fp.make_features(g)

    specs = [('v21_increment', dict(physics=False, deshrink=0.0)),
             ('v21_physics_deshrink_half', dict(physics=True, deshrink=fp.INC_DESHRINK))]
    tables, worst = [], {}
    for label, kw in specs:
        P = a47.score_config(g, y, cache, **kw)
        P = P.loc[P.block.isin(a47.PRIMARY_BLOCKS)]
        R, w = breakdown(P, g, F, label)
        tables.append(R)
        worst[label] = w
        print('\n=== %s ===' % label)
        print(R[['dimension', 'slice', 'n', 'days', 'rmse', 'bias', 'sse_share',
                 'day_level_share']].to_string(index=False,
                                               float_format=lambda v: '%.4f' % v))
        print('worst days: ' + '  '.join('%s %.1f%%' % (d['day'], 100 * d['share'])
                                         for d in w))
    T = pd.concat(tables, ignore_index=True)
    T.to_csv(OUT / 'breakdown.csv', index=False)

    a, b = [t.set_index(['dimension', 'slice']) for t in tables]
    delta = (b.rmse - a.rmse).dropna().sort_values()
    print('\nWHERE THE ADOPTED CANDIDATE ACTUALLY MOVES THE ERROR (negative = better)')
    print(pd.DataFrame({'incumbent': a.rmse, 'phys_dsh': b.rmse, 'delta': delta,
                        'n': a.n, 'days': a.days}).dropna()
          .sort_values('delta').to_string(float_format=lambda v: '%.4f' % v))
    (OUT / 'breakdown.json').write_text(json.dumps(
        dict(worst_days=worst, rows=int(len(T))), indent=2))


if __name__ == '__main__':
    main()
