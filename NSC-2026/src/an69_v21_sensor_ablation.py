"""Session 30, P1: drop only the columns an absolute sensor offset can move.

Section 210 tested the pressure hypothesis by replacing the whole 132-column increment design
with a 57-column one. That arm lost, but it cannot isolate pressure: it also deleted most of the
thermal context, the multi-scale statistics and the soil block, and `colsample_bytree=0.8` was
sampling a different number and mix of columns. A family losing under that much simultaneous
change says nothing about the family.

This is the narrow version. Offset the raw sensor and rebuild the ENTIRE feature pipeline from
the grid -- not the derived columns after the fact -- and a column either moves or it does not:

    invariant  <=>  np.allclose(a, b, rtol=1e-9, atol=1e-6, equal_nan=True)

On the parent design (v21: no physics, no de-shrink, no lags) that marks **11 of 132** columns as
pressure-sensitive and **20** as CO2-sensitive, with **no mixed columns** -- nothing here is a
CO2xT interaction, so no column is lost to two sensors at once. Everything else stays, including
the invariant dynamics the parent already had: `pressure_change`, `pressure_slope`,
`pressure_a1h/a6h/a24h`, `pressure_sd6h`, and the whole `co2_rng/qrng/minus_min` family. The
arms remove absolute LEVEL information about a sensor while keeping its dynamics.

Three arms, frozen before fitting and listed in `sensor_columns.json`:

* `drop_pressure_abs`  132 -> 121 columns
* `drop_co2_abs`       132 -> 112 columns
* `drop_both_abs`      132 -> 101 columns

The offsets (+25 hPa, +60 ppm) are diagnostic probes used once to build the whitelist. They are
not augmentation, they never touch a target, and no arm is fitted on offset data.

    .venv/Scripts/python.exe src/an69_v21_sensor_ablation.py
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

OUT = ROOT / 'outputs' / 'audit_v21_s30'
PRESSURE_OFFSET, CO2_OFFSET = 25.0, 60.0
TOL = dict(rtol=1e-9, atol=1e-6, equal_nan=True)
ANCHOR = 'v21'
ARMS = ('drop_pressure_abs', 'drop_co2_abs', 'drop_both_abs')


def sensitive_columns(g, sensor, offset):
    """Columns of the parent design that move when `sensor` is offset and every feature is
    rebuilt from the grid. Returned per horizon; the union is what an arm drops."""
    F = fp.make_features(g)
    g2 = g.copy()
    g2[sensor] = g2[sensor] + offset
    F2 = fp.make_features(g2)
    out = {}
    for h, _ in fp.INC_SPEC:
        X, X2 = fp.inc_design(F, h, fp.INC_COLS, False), fp.inc_design(F2, h, fp.INC_COLS, False)
        assert list(X.columns) == list(X2.columns)
        out[h] = [col for col in X.columns
                  if not np.allclose(X[col].to_numpy(), X2[col].to_numpy(), **TOL)]
    return out


def freeze_whitelist(g):
    """Compute the drop lists once, write them out, and never recompute them per fold."""
    p = sensitive_columns(g, 'pressure', PRESSURE_OFFSET)
    q = sensitive_columns(g, 'co2', CO2_OFFSET)
    drops = {}
    for h, _ in fp.INC_SPEC:
        both = sorted(set(p[h]) & set(q[h]))
        drops[h] = dict(drop_pressure_abs=sorted(p[h]), drop_co2_abs=sorted(q[h]),
                        drop_both_abs=sorted(set(p[h]) | set(q[h])), mixed=both)
    return drops


def ablated_design(F, h, drop):
    X = fp.inc_design(F, h, fp.INC_COLS, False)
    keep = [col for col in X.columns if col not in drop]
    return X[keep]


def make_builder(drops, arm, colsample=None):
    kw = dict(fp.INC_KW)
    if colsample is not None:
        kw['colsample_bytree'] = colsample

    def build(F, y, mask, seeds):
        out = {'ablation': arm, 'drops': drops}
        for h, _ in fp.INC_SPEC:
            X = ablated_design(F, h, drops[h][arm] if arm else [])
            tgt = (y - y.shift(h)).reindex(X.index)
            m = mask.reindex(X.index, fill_value=False)
            m = m & tgt.notna() & m.shift(h, fill_value=False)
            out[h] = [lgb.LGBMRegressor(random_state=s, **kw).fit(X.loc[m], tgt.loc[m])
                      for s in seeds]
            out[('cols', h)] = list(X.columns)
        return out
    return build


def make_terms(drops, arm):
    def terms(F, idx, inc):
        out = []
        for h, lam in fp.INC_SPEC:
            D, st = fp.diff_operator(idx, h)
            if D is None:
                out.append((None, None, lam))
                continue
            X = ablated_design(F, h, drops[h][arm] if arm else []).loc[st]
            out.append((D, np.mean([m.predict(X) for m in inc[h]], axis=0), lam))
        return out
    return terms


def score_all(g, y, cache_15, cache_7, drops, arm, seeds, feats, colsample=None):
    kw = dict(inc_builder=make_builder(drops, arm, colsample),
              term_builder=make_terms(drops, arm)) if arm else {}
    if colsample is not None and not arm:
        kw = dict(inc_builder=make_builder(drops, None, colsample),
                  term_builder=make_terms(drops, None))
    P15 = a47.score_config(g, y, cache_15, physics=False, deshrink=0.0, seeds=seeds,
                           scopes=('outer',), feature_cache=feats, **kw)
    P7 = a47.score_config(g, y, cache_7, physics=False, deshrink=0.0, seeds=seeds,
                          scopes=('outer',), feature_cache=feats, **kw)
    return P15, P7


def primary_index(P):
    """Primary rows only (B1/B2), indexed by timestamp, with uniqueness asserted.

    Session 31 found the bug this replaces. `matched` used to call
    `P15.set_index('datetime').loc[idx]` on a frame that still contained B3. B3 is a 7-day shift
    that overlaps both primary blocks, so its timestamps are duplicates, and `.loc` on a
    non-unique index EXPANDS: asking for 1008 timestamps returned **1680 rows**. The `15d_all`
    column had the same defect from the other direction, pooling 2160 rows where the primary
    metric uses 1440. The promotion decisions were unaffected -- `a47.report` was always correct
    and no arm came close to the bar -- but every matched-calendar number in section 219 was
    computed on a population that does not exist."""
    Q = P.loc[P.score & P.block.str.startswith(('B1_', 'B2_'))].copy()
    assert not Q.datetime.duplicated().any(), 'primary blocks must not share a timestamp'
    return Q.set_index('datetime').sort_index()


def matched(P15, P7, ref15, ref7):
    """The section-214 standardisation: same 1008 timestamps, three populations."""
    a = primary_index(P15)
    b = P7.loc[P7.score].set_index('datetime').sort_index()
    r15 = primary_index(ref15)
    r7 = ref7.loc[ref7.score].set_index('datetime').sort_index()
    assert not b.index.duplicated().any(), 'the 7-day holdouts must not share a timestamp'
    idx = b.index
    out = {}
    for label, d, ref in (('15d_all', a, r15), ('15d_matched', a.loc[idx], r15.loc[idx]),
                          ('7d_matched', b, r7)):
        e = (d.recon - d.y).to_numpy() ** 2
        f = (ref.recon - ref.y).to_numpy() ** 2
        out[label + '_d_rmse'] = float(np.sqrt(e.mean()) - np.sqrt(f.mean()))
        out[label + '_d_mse'] = float(e.mean() - f.mean())
    return out


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    g = fp.load_grid()
    y = g[fp.TARGET]
    cache_15 = a47.load_cache(a47.CACHE_S27, a47.MANIFEST_S27)
    cache_7 = pd.read_pickle(ROOT / 'outputs' / 'audit_v21_s29' / 'forward_7d.pkl')
    seeds, feats = a47.SEEDS_INC, {}

    drops = freeze_whitelist(g)
    c.write_json(OUT / 'sensor_columns.json', dict(
        pressure_offset=PRESSURE_OFFSET, co2_offset=CO2_OFFSET, tolerance=TOL,
        parent='v21 increment design (no physics, no de-shrink, no lags)',
        parent_columns={str(h): fp.inc_design(fp.make_features(g), h, fp.INC_COLS,
                                              False).shape[1] for h, _ in fp.INC_SPEC},
        drops={str(h): v for h, v in drops.items()}))
    for h, _ in fp.INC_SPEC:
        print('h=%d  pressure-sensitive %d  co2-sensitive %d  mixed %d'
              % (h, len(drops[h]['drop_pressure_abs']), len(drops[h]['drop_co2_abs']),
                 len(drops[h]['mixed'])))
    print('frozen drop lists written to sensor_columns.json before any fitting\n')

    preds15, preds7, rows = {}, {}, []
    P15, P7 = score_all(g, y, cache_15, cache_7, drops, None, seeds, feats)
    frozen = pd.read_pickle(a47.OUT_S27 / 'preds_v21_increment.pkl')
    j = c.join_predictions(frozen.loc[frozen.scope == 'outer'], P15)
    np.testing.assert_allclose(j.recon, j.recon_q, atol=1e-9, rtol=0)
    preds15[ANCHOR], preds7[ANCHOR] = P15, P7
    ref15 = a47.report(P15, ANCHOR)
    print('  %-20s pooled15 %.6f  [reproduces the frozen v21 predictions exactly]'
          % (ANCHOR, ref15['pooled']))

    for arm in ARMS:
        t = time.time()
        P15, P7 = score_all(g, y, cache_15, cache_7, drops, arm, seeds, feats)
        preds15[arm], preds7[arm] = P15, P7
        r = a47.report(P15, arm, ref15)
        r['columns'] = len(fp.inc_design(fp.make_features(g), 1, fp.INC_COLS, False).columns) \
            - len(drops[1][arm])
        r.update(matched(P15, P7, preds15[ANCHOR], preds7[ANCHOR]))
        for hb, d in P7.loc[P7.score].groupby('block'):
            ref = preds7[ANCHOR]
            ref = ref.loc[ref.score]
            ref = ref.loc[ref.block == hb]
            r['d_' + hb] = fp.rmse(d.y, d.recon) - fp.rmse(ref.y, ref.recon)
        b = a47.bootstrap_pair(preds15[ANCHOR], P15)
        r['boot3_lo'], r['boot3_hi'] = b['b3d']['lo'], b['b3d']['hi']
        r['boot3_days'] = b['worst_day']['days_improved']
        rows.append(r)
        print('  %-20s pooled15 %.6f  (%.0f s)' % (arm, r['pooled'], time.time() - t),
              flush=True)

    R = pd.DataFrame([ref15] + rows)
    diag = []
    for arm in ARMS:
        jj = c.join_predictions(preds15[ANCHOR], preds15[arm])
        for bl, d in jj.groupby('block'):
            diag.append(dict(arm=arm, block=bl, **c.direction(d.y, d.recon, d.recon_q)))
    D = pd.DataFrame(diag)

    keep = ['candidate', 'columns', 'pooled', 'B1_last15d', 'B2_prev15d', 'B3_shift7d',
            'd_pooled', '15d_matched_d_rmse', '7d_matched_d_rmse',
            'd_H1_last7d', 'd_H2_last14d', 'd_H3_last21d', 'promotable']
    print('\n' + R[[k for k in keep if k in R.columns]].to_string(index=False))
    print('\ndirection vs v21\n' + D.to_string(index=False))

    R.to_csv(OUT / 'sensor_ablation.csv', index=False)
    D.to_csv(OUT / 'sensor_ablation_direction.csv', index=False)
    for arm, P in preds15.items():
        P.to_pickle(OUT / ('preds_sensor_%s.pkl' % arm))
    for arm, P in preds7.items():
        P.to_pickle(OUT / ('preds_sensor_7d_%s.pkl' % arm))
    c.write_json(OUT / 'sensor_ablation.json', dict(
        anchor=ANCHOR, arms=list(ARMS), seeds=list(seeds),
        results=json.loads(R.to_json(orient='records')),
        direction=json.loads(D.to_json(orient='records')),
        code={'src/an69_v21_sensor_ablation.py': a47.md5(Path(__file__)),
              'final_pipeline.py': a47.md5(ROOT / 'final_pipeline.py')},
        level_cache_md5=a47.md5(a47.CACHE_S27)))
    print('\nwrote sensor_ablation.csv to %s' % OUT)


if __name__ == '__main__':
    main()
