"""Session 30, P0: the section-29 relative design with the physical feature put back on the
endpoint the production design uses.

At constant vapour pressure the RH change over h steps has two exact forms, with
`ratio = es(T[t-h]) / es(T[t])`:

    dRH = RH[t-h] * (ratio - 1) = RH[t] * (1 - 1/ratio)

`final_pipeline.inc_design` computes the first. `an65.rel_design` kept the `(ratio - 1)`
multiplier but moved the proxy to time t, producing `RH[t] * (ratio - 1)` -- a mixture of the two
forms that is off by a factor of `ratio` and, on a plausible five-point fixture, wrong by more
than a full %RH. Nothing about it is leakage and nothing about it touches the target; it is
causal and target-blind either way. What it is not is the parent's physical feature, which is
what section 210's arm claimed to be holding fixed while it changed the sensor columns.

So this is a methodology control, not a submission candidate: **one column changes**, and
`tests/test_v21_relative_endpoint.py` asserts that exactly one column changes. The session-29
artefact is left alone rather than quietly corrected, so the old number keeps describing the old
run.

Its purpose is to answer a narrow question before P1 spends any compute on sensor ablation: was
section 210's B2 collapse partly this, or is it entirely the sensor columns? A control that
cannot move the result is worth knowing about too.

    .venv/Scripts/python.exe src/an68_v21_relative_endpoint.py
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
import an65_v21_relative_dynamics as a65

OUT = ROOT / 'outputs' / 'audit_v21_s30'
ANCHOR = 'v21'


def rel_design_prev_endpoint(F, h):
    """`a65.rel_design` with `dRH_const_e` on the previous endpoint, as production has it.

    Built by calling the session-29 function and replacing the one column, so the two designs
    cannot drift apart in any other respect."""
    X = a65.rel_design(F, h)
    ratio = F['esT'].shift(h) / F['esT']
    X['dRH_const_e'] = F['rh_tmin48'].shift(h) * (ratio - 1.0)
    return X


def fit_prev_endpoint(F, y, mask, seeds):
    out = {'relative': True, 'endpoint': 'previous'}
    for h, _ in fp.INC_SPEC:
        X = rel_design_prev_endpoint(F, h)
        tgt = (y - y.shift(h)).reindex(X.index)
        m = mask.reindex(X.index, fill_value=False)
        m = m & tgt.notna() & m.shift(h, fill_value=False)
        out[h] = [lgb.LGBMRegressor(random_state=s, **fp.INC_KW).fit(X.loc[m], tgt.loc[m])
                  for s in seeds]
        out[('n', h)] = int(m.sum())
    return out


def prev_endpoint_terms(F, idx, inc):
    out = []
    for h, lam in fp.INC_SPEC:
        D, st = fp.diff_operator(idx, h)
        if D is None:
            out.append((None, None, lam))
            continue
        X = rel_design_prev_endpoint(F, h).loc[st]
        out.append((D, np.mean([m.predict(X) for m in inc[h]], axis=0), lam))
    return out


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    g = fp.load_grid()
    y = g[fp.TARGET]
    cache = a47.load_cache(a47.CACHE_S27, a47.MANIFEST_S27)
    seeds, feats = a47.SEEDS_INC, {}

    print('control  : v21 increment')
    base = a47.score_config(g, y, cache, physics=False, deshrink=0.0, seeds=seeds,
                            scopes=('outer',), feature_cache=feats)
    frozen = pd.read_pickle(a47.OUT_S27 / 'preds_v21_increment.pkl')
    j = c.join_predictions(frozen.loc[frozen.scope == 'outer'], base)
    np.testing.assert_allclose(j.recon, j.recon_q, atol=1e-9, rtol=0)
    ref = a47.report(base, ANCHOR)
    print('  pooled %.6f  [reproduces the frozen v21 predictions exactly]' % ref['pooled'])

    # Reproduce the session-29 arm before reading the new delta, exactly as the plan requires.
    print('reproduce: session-29 relative dynamics (current-endpoint physical feature)')
    old = a47.score_config(g, y, cache, physics=False, deshrink=0.0, seeds=seeds,
                           scopes=('outer',), inc_builder=a65.fit_relative,
                           term_builder=a65.relative_terms, feature_cache=feats)
    stored = ROOT / 'outputs' / 'audit_v21_s29' / 'preds_relative_dynamics.pkl'
    jo = c.join_predictions(pd.read_pickle(stored), old)
    np.testing.assert_allclose(jo.recon, jo.recon_q, atol=1e-9, rtol=0)
    r_old = a47.report(old, 'relative_dynamics_s29', ref)
    print('  pooled %.6f  [reproduces preds_relative_dynamics.pkl exactly]' % r_old['pooled'])

    print('candidate: same design, physical feature on the previous endpoint')
    t = time.time()
    P = a47.score_config(g, y, cache, physics=False, deshrink=0.0, seeds=seeds,
                         scopes=('outer',), inc_builder=fit_prev_endpoint,
                         term_builder=prev_endpoint_terms, feature_cache=feats)
    r = a47.report(P, 'relative_prev_endpoint', ref)
    r_vs_old = a47.report(P, 'relative_prev_endpoint', r_old)
    r['d_pooled_vs_s29_arm'] = r_vs_old['d_pooled']
    print('  pooled %.6f  (%.0f s)' % (r['pooled'], time.time() - t), flush=True)

    b = a47.bootstrap_pair(base, P)
    r['boot3_lo'], r['boot3_hi'] = b['b3d']['lo'], b['b3d']['hi']
    diag = []
    for label, ctrl in (('v21', base), ('relative_dynamics_s29', old)):
        jj = c.join_predictions(ctrl, P)
        for bl, d in jj.groupby('block'):
            diag.append(dict(arm='relative_prev_endpoint', vs=label, block=bl,
                             **c.direction(d.y, d.recon, d.recon_q)))

    R = pd.DataFrame([ref, r_old, r])
    D = pd.DataFrame(diag)
    print('\n' + R.to_string(index=False))
    print('\ndirection\n' + D.to_string(index=False))

    R.to_csv(OUT / 'relative_endpoint.csv', index=False)
    D.to_csv(OUT / 'relative_endpoint_direction.csv', index=False)
    P.to_pickle(OUT / 'preds_relative_prev_endpoint.pkl')
    c.write_json(OUT / 'relative_endpoint.json', dict(
        anchor=ANCHOR, seeds=list(seeds), changed_columns=['dRH_const_e'],
        results=json.loads(R.to_json(orient='records')),
        direction=json.loads(D.to_json(orient='records')), bootstrap=b,
        code={'src/an68_v21_relative_endpoint.py': a47.md5(Path(__file__)),
              'src/an65_v21_relative_dynamics.py': a47.md5(ROOT / 'src'
                                                           / 'an65_v21_relative_dynamics.py')},
        level_cache_md5=a47.md5(a47.CACHE_S27),
        note='methodology control; one column differs from the session-29 arm'))
    print('\nwrote relative_endpoint.csv to %s' % OUT)


if __name__ == '__main__':
    main()
