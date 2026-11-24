"""Session 28, Tahap 4: re-score the winning arm through the code that actually ships.

`an60` fitted the lag arm with its own helper, and that helper's training mask is not the
shipped one. `fp.fit_increments` shifts the mask AFTER intersecting it with `tgt.notna()`, so it
additionally requires a label at t-2h; `an60.fit_extra` shifts the raw mask. The difference is a
handful of rows near label gaps and it is not a leak in either direction -- but it means the
number in section 202's ablation was produced by a function that is not `final_pipeline`. A
candidate is promoted on the strength of a number, and that number has to come from the artifact
that will generate the submission.

So this refits both arms through `fp.fit_increments` and `fp.reconcile`'s own design selector,
on the frozen session-27 level cache, and reports:

* the control, which must reproduce the frozen `preds_v21_physics_deshrink_half` exactly -- the
  same assertion `an60` makes, repeated here because the design selector in `an47` changed;
* the production lag arm, against the section-180 bar;
* the paired direction decomposition, so the gain is attributed to alignment or to movement
  rather than assumed.

    .venv/Scripts/python.exe src/an62_v21_production_rescore.py
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

OUT = ROOT / 'outputs' / 'audit_v21_s28'
ARMS = {
    'control': dict(physics=True, deshrink=True, lags=False),
    'lgb_lags_production': dict(physics=True, deshrink=True, lags=True),
}


def builder(**kw):
    def build(F, yh, mask, seeds):
        return fp.fit_increments(F, yh, mask, seeds, **kw)
    return build


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    g = fp.load_grid()
    y = g[fp.TARGET]
    cache = a47.load_cache(a47.CACHE_S27, a47.MANIFEST_S27)
    seeds, feats = a47.SEEDS_INC, {}

    preds = {}
    for arm, kw in ARMS.items():
        t = time.time()
        P = a47.score_config(g, y, cache, physics=kw['physics'],
                             deshrink=fp.INC_DESHRINK if kw['deshrink'] else 0.0,
                             seeds=seeds, scopes=('outer',),
                             inc_builder=builder(**kw), feature_cache=feats)
        preds[arm] = P
        print('  %-22s pooled %.6f  (%.0f s)'
              % (arm, a47.report(P, arm)['pooled'], time.time() - t), flush=True)

    # The control must still be the frozen session-27 artifact, bit for bit.
    frozen = pd.read_pickle(a47.OUT_S27 / 'preds_v21_physics_deshrink_half.pkl')
    frozen = frozen.loc[frozen.scope == 'outer']
    j = c.join_predictions(frozen, preds['control'])
    np.testing.assert_allclose(j.recon, j.recon_q, atol=1e-9, rtol=0)
    print('  control reproduces the frozen session-27 predictions exactly (%d rows)' % len(j))

    ref = a47.report(preds['control'], 'control')
    public = pd.read_pickle(a47.OUT_S27 / 'preds_v21_increment.pkl')
    rp = a47.report(public.loc[public.scope == 'outer'], 'v21_public_configuration')

    rows, boots, diag = [ref], {}, []
    for arm in ARMS:
        if arm == 'control':
            continue
        r = a47.report(preds[arm], arm, ref)
        r['delta_vs_v21'] = r['pooled'] - rp['pooled']
        rows.append(r)
        boots[arm] = a47.bootstrap_pair(preds['control'], preds[arm])
        jj = c.join_predictions(preds['control'], preds[arm])
        for b, d in jj.groupby('block'):
            diag.append(dict(candidate=arm, block=b, **c.direction(d.y, d.recon, d.recon_q)))

    R = pd.DataFrame(rows)
    D = pd.DataFrame(diag)
    print('\n' + R.to_string(index=False))
    print('\ndirection decomposition (alignment = 2*mean(e*u), movement = mean(u^2))')
    print(D.to_string(index=False))
    for arm, b in boots.items():
        print('\nbootstrap %s: 3d %+.4f [%+.4f, %+.4f] over %d blocks | 7d %+.4f [%+.4f, %+.4f]'
              ' | %d/%d days improved'
              % (arm, b['b3d']['mean'], b['b3d']['lo'], b['b3d']['hi'], b['b3d']['blocks'],
                 b['b7d']['mean'], b['b7d']['lo'], b['b7d']['hi'],
                 b['worst_day']['days_improved'], b['worst_day']['days']))

    passing = [r['candidate'] for r in rows if r.get('promotable')]
    print('\nPASSES THE SECTION-180 BAR: %s' % (', '.join(passing) if passing else 'none'))

    R.to_csv(OUT / 'production_rescore.csv', index=False)
    D.to_csv(OUT / 'production_rescore_direction.csv', index=False)
    for arm, P in preds.items():
        P.to_pickle(OUT / ('preds_production_%s.pkl' % arm))
    c.write_json(OUT / 'production_rescore.json',
                 dict(arms={k: {kk: bool(vv) if isinstance(vv, bool) else vv
                                for kk, vv in v.items()} for k, v in ARMS.items()},
                      seeds=list(seeds), results=json.loads(R.to_json(orient='records')),
                      direction=json.loads(D.to_json(orient='records')),
                      bootstrap=boots, passing=passing,
                      code={'final_pipeline.py': a47.md5(ROOT / 'final_pipeline.py')}))
    print('\nwrote production_rescore.csv and the predictions to %s' % OUT)


if __name__ == '__main__':
    main()
