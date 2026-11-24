"""Session 29, arm set A: finish the lag/de-shrink 2x2 so the public loss can be attributed.

The package that scored 2.93028 changed THREE things against the configuration that scored
2.86595 -- physics, half de-shrink, and lags -- and only the endpoints have public scores. The
local table has the same hole: `physics+lags` was never run as its own arm, so every statement
about what the lag columns are worth is a statement about what they are worth AFTER expansion.

|                | no lags                     | lags                                  |
|----------------|-----------------------------|---------------------------------------|
| no de-shrink   | `physics` (have)            | **`physics_lags` (missing)**          |
| half de-shrink | `physics_dsh` (have)        | `physics_dsh_lags` -> public 2.93028  |

Two new arms, no strength grid, nothing else varied:

* `physics_lags`   -- physics + lags, de-shrink OFF. Fills the empty cell.
* `v21_lags`       -- lags on the bare v21 increment: no physics, no de-shrink. Asks whether
                      trajectory information stands on its own, against the one configuration
                      in this log with an externally validated score.

Everything is refitted through `fp.fit_increments` and `fp.reconcile`, the functions that
generate submissions, and the three arms that already have frozen session-27 predictions must
reproduce them to 1e-9 before any new number is read. Section 206's rule applies to the output:
after an external loss, clearing the engineering bar is not by itself a reason to displace v21.

    .venv/Scripts/python.exe src/an64_v21_lag_without_expansion.py
"""
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
import final_pipeline as fp
import an47_v21_forward_benchmark as a47
import an59_v21_candidate_contract as c

OUT = ROOT / 'outputs' / 'audit_v21_s29'
ANCHOR = 'v21'                      # the only configuration here with a public score

# arm -> (fit flags, parent arm, frozen session-27/28 pickle that must be reproduced)
ARMS = {
    'v21':               (dict(physics=False, deshrink=False, lags=False), None,
                          a47.OUT_S27 / 'preds_v21_increment.pkl'),
    'physics':           (dict(physics=True, deshrink=False, lags=False), 'v21',
                          a47.OUT_S27 / 'preds_v21_physics.pkl'),
    'physics_dsh':       (dict(physics=True, deshrink=True, lags=False), 'physics',
                          a47.OUT_S27 / 'preds_v21_physics_deshrink_half.pkl'),
    'physics_dsh_lags':  (dict(physics=True, deshrink=True, lags=True), 'physics_dsh',
                          ROOT / 'outputs' / 'audit_v21_s28'
                          / 'preds_production_lgb_lags_production.pkl'),
    'physics_lags':      (dict(physics=True, deshrink=False, lags=True), 'physics', None),
    'v21_lags':          (dict(physics=False, deshrink=False, lags=True), 'v21', None),
}


def builder(**kw):
    def build(F, yh, mask, seeds):
        return fp.fit_increments(F, yh, mask, seeds, **kw)
    return build


def endpoint_provenance(g, y, cache, kw, seeds):
    """What each arm actually trained on, per origin: row counts, endpoint masks, the factor if
    it is on, and the design width. Recorded so a later session never has to guess whether an
    arm had expansion enabled."""
    rows, feats = [], {}
    for name, blk in cache.loc[cache.scope == 'outer'].groupby('block', sort=False):
        d = blk.sort_values('datetime')
        gh, F = a47.frame_at(g, d.horizon_end.iloc[0], feats)
        origin = pd.Timestamp(d.origin.iloc[0])
        mask = a47.train_mask_before(g, gh, y, origin)
        yh = y.reindex(gh.index)
        cols = fp.INC_PHYS_COLS if kw['physics'] else fp.INC_COLS
        inc = fp.fit_increments(F, yh, mask, seeds, **kw)
        for h, _ in fp.INC_SPEC:
            X = fp.increment_design(F, h, cols, kw['physics'], kw['lags'])
            tgt = (yh - yh.shift(h)).reindex(X.index)
            m = mask.reindex(X.index, fill_value=False)
            m = m & tgt.notna() & m.shift(h, fill_value=False)
            used = X.index[m]
            rows.append(dict(block=name, h=h, origin=str(origin), design_columns=X.shape[1],
                             train_rows=int(m.sum()), first_endpoint=str(used.min()),
                             last_endpoint=str(used.max()),
                             earlier_endpoint_max=str((used - pd.Timedelta(
                                 minutes=30 * h)).max()),
                             deshrink_enabled=bool(kw['deshrink']),
                             factor=float(inc[('f', h)]) if ('f', h) in inc else None,
                             training_rows_hash=c.digest(used.astype(str).tolist())))
    return rows


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    g = fp.load_grid()
    y = g[fp.TARGET]
    cache = a47.load_cache(a47.CACHE_S27, a47.MANIFEST_S27)
    seeds, feats = a47.SEEDS_INC, {}

    preds, prov = {}, []
    for arm, (kw, parent, frozen) in ARMS.items():
        t = time.time()
        P = a47.score_config(g, y, cache, physics=kw['physics'],
                             deshrink=fp.INC_DESHRINK if kw['deshrink'] else 0.0,
                             seeds=seeds, scopes=('outer',), inc_builder=builder(**kw),
                             feature_cache=feats)
        preds[arm] = P
        note = ''
        if frozen is not None and Path(frozen).exists():
            f = pd.read_pickle(frozen)
            j = c.join_predictions(f.loc[f.scope == 'outer'] if 'scope' in f else f, P)
            np.testing.assert_allclose(j.recon, j.recon_q, atol=1e-9, rtol=0)
            note = '  [reproduces %s exactly]' % Path(frozen).name
        elif frozen is not None:
            note = '  [WARNING: frozen file %s missing, not verified]' % Path(frozen).name
        print('  %-18s pooled %.6f  (%.0f s)%s'
              % (arm, a47.report(P, arm)['pooled'], time.time() - t, note), flush=True)

    for arm, (kw, _p, _f) in ARMS.items():
        prov += [dict(arm=arm, **r) for r in endpoint_provenance(g, y, cache, kw, seeds)]

    anchor = a47.report(preds[ANCHOR], ANCHOR)
    rows, boots, diag = [], {}, []
    for arm, (kw, parent, _f) in ARMS.items():
        r = a47.report(preds[arm], arm, anchor)
        r['parent'] = parent or ''
        r['physics'], r['deshrink'], r['lags'] = kw['physics'], kw['deshrink'], kw['lags']
        if parent:
            pr = a47.report(preds[arm], arm, a47.report(preds[parent], parent))
            r['d_pooled_vs_parent'] = pr['d_pooled']
            for b in ('B1_last15d', 'B2_prev15d', 'B3_shift7d'):
                r['d_%s_vs_parent' % b] = pr.get('d_' + b)
            b = a47.bootstrap_pair(preds[parent], preds[arm])
            boots['%s_vs_%s' % (arm, parent)] = b
            r['boot3_lo_vs_parent'], r['boot3_hi_vs_parent'] = b['b3d']['lo'], b['b3d']['hi']
        if arm != ANCHOR:
            b = a47.bootstrap_pair(preds[ANCHOR], preds[arm])
            boots['%s_vs_%s' % (arm, ANCHOR)] = b
            r['boot3_lo_vs_v21'], r['boot3_hi_vs_v21'] = b['b3d']['lo'], b['b3d']['hi']
            r['boot7_lo_vs_v21'], r['boot7_hi_vs_v21'] = b['b7d']['lo'], b['b7d']['hi']
            r['days_improved_vs_v21'] = b['worst_day']['days_improved']
            jj = c.join_predictions(preds[ANCHOR], preds[arm])
            for bl, dd in jj.groupby('block'):
                diag.append(dict(arm=arm, vs=ANCHOR, block=bl,
                                 **c.direction(dd.y, dd.recon, dd.recon_q)))
        rows.append(r)

    R = pd.DataFrame(rows)
    D = pd.DataFrame(diag)
    show = ['candidate', 'physics', 'deshrink', 'lags', 'pooled', 'B1_last15d', 'B2_prev15d',
            'B3_shift7d', 'd_pooled', 'd_pooled_vs_parent', 'promotable']
    print('\nall arms, delta columns are against %s (the scored anchor)\n' % ANCHOR)
    print(R[[x for x in show if x in R.columns]].to_string(index=False))
    print('\ndirection vs %s (alignment = 2*mean(e*u), movement = mean(u^2))' % ANCHOR)
    print(D.to_string(index=False))
    print('\npaired bootstrap of pooled dMSE, 3-day blocks')
    for k, b in boots.items():
        print('  %-34s %+.4f [%+.4f, %+.4f]  %d/%d days improved'
              % (k, b['b3d']['mean'], b['b3d']['lo'], b['b3d']['hi'],
                 b['worst_day']['days_improved'], b['worst_day']['days']))

    R.to_csv(OUT / 'lag_without_expansion.csv', index=False)
    D.to_csv(OUT / 'lag_without_expansion_direction.csv', index=False)
    pd.DataFrame(prov).to_csv(OUT / 'lag_without_expansion_provenance.csv', index=False)
    for arm, P in preds.items():
        P.to_pickle(OUT / ('preds_%s.pkl' % arm))
    c.write_json(OUT / 'lag_without_expansion.json', dict(
        anchor=ANCHOR, arms={k: v[0] for k, v in ARMS.items()},
        parents={k: v[1] for k, v in ARMS.items()}, seeds=list(seeds),
        results=json.loads(R.to_json(orient='records')),
        direction=json.loads(D.to_json(orient='records')), bootstrap=boots,
        code={'final_pipeline.py': a47.md5(ROOT / 'final_pipeline.py'),
              'src/an64_v21_lag_without_expansion.py': a47.md5(Path(__file__))},
        level_cache_md5=a47.md5(a47.CACHE_S27)))
    print('\nwrote lag_without_expansion.csv and the predictions to %s' % OUT)


if __name__ == '__main__':
    main()
