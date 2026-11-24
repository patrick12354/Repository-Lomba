"""Session 29, diagnostic: 7-day holdouts with training histories close to the final fit.

Every candidate in this log was chosen on 15-day holdouts whose origins leave 31 to 46 days of
training history behind them. The model that generates the submission is fitted on about 61 days.
Section 207 lists that gap as an unexamined reason a local winner might not transfer: bias and
variance estimated from a model with two thirds of the history are not automatically the bias and
variance of the shipped one.

So this builds a SECOND harness -- shorter horizon, longer history -- and scores the same
candidates on it. Non-overlapping 7-day holdouts walking back from the label boundary, each with
its own horizon-truncated feature matrix, its own meta rows restricted to labels at or before its
origin, and the same section-190 fallback rule.

**This is a diagnostic and is reported as one.** It reuses the same calendar the primary blocks
already cover, so it is not new evidence and it does not replace pooled B1+B2; the horizon is 7
days rather than 15, so it is not the forecast the competition asks for either. What it can do is
tell a candidate whose gain survives a longer training history from one whose does not, and after
section 206 that distinction is worth having.

The orchestration is deliberately separate from `an47.build_block` rather than a parameter added
to it: `build_block` is inside the level cache's build fingerprint, and widening it to admit
336-row holdouts would invalidate a cache that three independent builds have shown to be stable.
The primitives -- `member_preds`, `stack_on`, `meta_prior`, `frame_at` -- are the shared ones.

    .venv/Scripts/python.exe src/an66_v21_transfer_report.py
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
import an36_increment_production as a36
import an47_v21_forward_benchmark as a47
import an59_v21_candidate_contract as c
import an65_v21_relative_dynamics as a65

OUT = ROOT / 'outputs' / 'audit_v21_s29'
CACHE = OUT / 'forward_7d.pkl'
MANIFEST = OUT / 'forward_7d_manifest.json'
HOLD_DAYS = 7
N_HOLDOUTS = 3          # frozen before the run; walking back from the boundary
ANCHOR = 'v21'

ARMS = {
    'v21':              dict(physics=False, deshrink=False, lags=False),
    'physics_dsh':      dict(physics=True, deshrink=True, lags=False),
    'physics_dsh_lags': dict(physics=True, deshrink=True, lags=True),
    'physics_lags':     dict(physics=True, deshrink=False, lags=True),
    'v21_lags':         dict(physics=False, deshrink=False, lags=True),
}


def holdouts(g):
    b = g.index[(g.is_test == 0).to_numpy()].max()
    d = pd.Timedelta(days=HOLD_DAYS)
    return [('H%d_last%dd' % (i + 1, HOLD_DAYS * (i + 1)), b - d * (i + 1), b - d * i)
            for i in range(N_HOLDOUTS)]


def build_one(g, y, name, hs, he, feats):
    """One 7-day holdout: inner forward folds for the stack, then the outer members."""
    _, F = a47.frame_at(g, he, feats)
    lab = pd.Series((g.loc[g.index <= he].is_test == 0).to_numpy(), index=F.index) \
        & y.reindex(F.index).notna()
    idx = F.index[lab.to_numpy()]
    pre, hold = idx[idx <= hs], idx[(idx > hs) & (idx <= he)]
    assert len(hold) > 300 and len(pre) > 900, (name, len(pre), len(hold))

    oof, spans = [], {}
    for fi, (vs, ve) in enumerate(a36.inner_origins(pre)):
        v = pre[(pre > vs) & (pre <= ve)]
        t = pre[pre <= vs]
        if len(t) < 300 or len(v) < 50:
            continue
        _, Fi = a47.frame_at(g, ve, feats)
        d = a47.member_preds(Fi, Fi, y, t, v, fp.MODELS_L2, tuple(range(len(fp.SEEDS_OOF))))
        d['y'] = y.loc[v].to_numpy()
        d['tod'] = Fi.loc[v, 'tod'].to_numpy()
        d['fold'] = fi
        spans[fi] = (vs, ve)
        oof.append(d.reset_index(names='dt'))
    O = pd.concat(oof, ignore_index=True)
    assert O.dt.max() <= hs

    V = a47.member_preds(F, F, y, pre, hold, fp.MODELS_L2, tuple(range(len(fp.SEEDS_FIT))))
    V['y'] = y.loc[hold].to_numpy()
    V['tod'] = F.loc[hold, 'tod'].to_numpy()
    level = a47.stack_on(O, V, fp.MODELS_L2)
    hist = (hs - pre.min()).days
    print('  %-14s origin %s  history %d d  hold %d  level RMSE %.5f'
          % (name, hs.date(), hist, len(hold), fp.rmse(V.y, level)), flush=True)
    return pd.DataFrame({'block': name, 'scope': 'outer', 'fold': -1, 'datetime': hold,
                         'y': V.y.to_numpy(), 'level': level, 'score': True,
                         'origin': hs, 'horizon_end': he, 'history_days': hist,
                         'meta_rows': len(O), 'meta_days': a47._days(O.dt),
                         'meta_fallback': False,
                         **{'m_' + m: V[m].to_numpy() for m in fp.MODELS_L2}})


def build(g, y):
    feats, parts = {}, []
    t0 = time.time()
    for name, hs, he in holdouts(g):
        parts.append(build_one(g, y, name, hs, he, feats))
    cache = pd.concat(parts, ignore_index=True)
    cache.to_pickle(CACHE)
    c.write_json(MANIFEST, dict(
        created=pd.Timestamp.now().isoformat(timespec='seconds'),
        seconds=round(time.time() - t0, 1), hold_days=HOLD_DAYS, n_holdouts=N_HOLDOUTS,
        holdouts=[dict(name=n, origin=str(a), horizon_end=str(b)) for n, a, b in holdouts(g)],
        history_days={n: int(d.history_days.iloc[0]) for n, d in cache.groupby('block')},
        rows=int(len(cache)), cache_md5=a47.md5(CACHE),
        inputs=a47.input_hashes(), build_code=a47.build_fingerprint(),
        code={'src/an66_v21_transfer_report.py': a47.md5(Path(__file__)),
              'final_pipeline.py': a47.md5(ROOT / 'final_pipeline.py')}))
    return cache


def pooled_report(P, label, ref=None):
    P = P.loc[P.score]
    per = {b: (fp.rmse(d.y, d.recon), len(d)) for b, d in P.groupby('block')}
    pool = a47.pooled([per[b][0] for b in per], None, [per[b][1] for b in per])
    row = dict(candidate=label, pooled_7d=pool, **{b: per[b][0] for b in sorted(per)},
               n=int(sum(v[1] for v in per.values())))
    if ref is not None:
        row['d_pooled_7d'] = pool - ref['pooled_7d']
        for b in per:
            row['d_' + b] = per[b][0] - ref[b]
    return row


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    g = fp.load_grid()
    y = g[fp.TARGET]
    if CACHE.exists():
        # Session 30. This used to load whatever pickle was on disk. The hash happened to match,
        # so no number here was ever wrong -- but a receipt is not a check, and the session-27
        # guard exists because the difference matters later rather than at the moment you skip
        # it. Fail closed on the cache bytes, the inputs and the build-path fingerprint.
        man = json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {}
        bad = []
        if not MANIFEST.exists():
            bad.append('manifest missing beside %s' % CACHE.name)
        if man.get('cache_md5') != a47.md5(CACHE):
            bad.append('cache_md5: the pickle is not the one this manifest was written for')
        for k, v in a47.input_hashes().items():
            if man.get('inputs', {}).get(k) != v:
                bad.append('inputs[%s] moved' % k)
        for k, v in a47.build_fingerprint().items():
            if man.get('build_code', {}).get(k) != v:
                bad.append('build_code[%s] moved' % k)
        if bad:
            raise ValueError('7-day cache does not match the current run:\n  %s\nDelete %s to '
                             'rebuild it.' % ('\n  '.join(bad), CACHE))
        cache = pd.read_pickle(CACHE)
        print('loaded %s (%d rows), manifest and build path verified' % (CACHE.name, len(cache)))
    else:
        print('building %d non-overlapping %d-day holdouts' % (N_HOLDOUTS, HOLD_DAYS))
        cache = build(g, y)

    hist = {n: int(d.history_days.iloc[0]) for n, d in cache.groupby('block')}
    print('training history per origin (final fit is ~61 d): %s' % hist)

    seeds, feats = a47.SEEDS_INC, {}
    preds, rows, ref = {}, [], None
    for arm, kw in ARMS.items():
        t = time.time()

        def bld(F, yh, mask, sd, kw=kw):
            return fp.fit_increments(F, yh, mask, sd, **kw)
        P = a47.score_config(g, y, cache, physics=kw['physics'],
                             deshrink=fp.INC_DESHRINK if kw['deshrink'] else 0.0,
                             seeds=seeds, scopes=('outer',), inc_builder=bld,
                             feature_cache=feats)
        preds[arm] = P
        r = pooled_report(P, arm, ref)
        if ref is None:
            ref = r
        rows.append(r)
        print('  %-18s pooled_7d %.6f  (%.0f s)' % (arm, r['pooled_7d'], time.time() - t),
              flush=True)

    t = time.time()
    P = a47.score_config(g, y, cache, physics=False, deshrink=0.0, seeds=seeds,
                         scopes=('outer',), inc_builder=a65.fit_relative,
                         term_builder=a65.relative_terms, feature_cache=feats)
    preds['relative_dynamics'] = P
    rows.append(pooled_report(P, 'relative_dynamics', ref))
    print('  %-18s pooled_7d %.6f  (%.0f s)' % ('relative_dynamics', rows[-1]['pooled_7d'],
                                                time.time() - t), flush=True)

    R = pd.DataFrame(rows)
    diag = []
    for arm, P in preds.items():
        if arm == ANCHOR:
            continue
        jj = c.join_predictions(preds[ANCHOR], P)
        for b, d in jj.groupby('block'):
            diag.append(dict(arm=arm, block=b, **c.direction(d.y, d.recon, d.recon_q)))
    D = pd.DataFrame(diag)

    print('\n7-day holdout diagnostic (NOT the primary metric; same calendar, shorter horizon)\n')
    print(R.to_string(index=False))
    print('\ndirection vs %s on the 7-day holdouts\n' % ANCHOR + D.to_string(index=False))

    R.to_csv(OUT / 'transfer_report.csv', index=False)
    D.to_csv(OUT / 'transfer_report_direction.csv', index=False)
    for arm, P in preds.items():
        P.to_pickle(OUT / ('preds_7d_%s.pkl' % arm))
    c.write_json(OUT / 'transfer_report.json', dict(
        hold_days=HOLD_DAYS, n_holdouts=N_HOLDOUTS, history_days=hist, anchor=ANCHOR,
        arms={k: v for k, v in ARMS.items()}, seeds=list(seeds),
        results=json.loads(R.to_json(orient='records')),
        direction=json.loads(D.to_json(orient='records')),
        note='diagnostic only; reuses the primary calendar and a 7-day horizon'))
    print('\nwrote transfer_report.csv to %s' % OUT)


if __name__ == '__main__':
    main()
