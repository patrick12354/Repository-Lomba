"""Session 33, Tasks 0 and 3: does the trajectory-shape block make the LEVEL member better?

Three arms, and only one thing differs between them:

    C0   the incumbent, `hbt` fitted on the incumbent feature matrix F
    E1   `hbt` fitted on F plus the 60 trajectory-shape features
    E2   `hbt` fitted on F plus those 60 and the 12 observation-quality features

Everything else is held fixed by construction, not by intention. The other five members are the
cached incumbent predictions, byte for byte. The meta parameters -- NNLS weights, the
time-of-day bands, the harmonic bias -- are fitted on `O_base`, the incumbent out-of-fold frame,
which is IDENTICAL across the three arms: a candidate is never allowed to refit the blend on its
own out-of-fold predictions, because that is a different method and it has not been evaluated.
The increment terms are the shipped v21 ones (no physics, no de-shrink, no lags, five seeds),
fitted from F alone at each origin and shared across the arms.

So the only channel through which E1 or E2 can move the final number is the `hbt` column of the
holdout member matrix. That is the isolation the round is for.

**Why `hbt` and why the level.** Section 225 put 44.16% of the primary SSE in slow non-constant
modes that reach the solver only through the increment terms and arrive heavily attenuated, and
2.44% in the solver's constant nullspace. Pushing harder on the increments cannot reach either;
a better LEVEL can. `hbt` was chosen before any score was read: it is the strongest existing
level member and it is a tree ensemble, so it can use an interaction between shape and state
without being told which one. No other member is touched this round.

**What would make this fail honestly.** A member that improves on its own can still make the
ensemble worse -- section 53 measured exactly that -- so the arm is judged on `z_new`, the
reconciled prediction after stacking and solving, never on solo `hbt` RMSE. Both outcomes are
recorded.

Task 0 runs first and unconditionally. It reproduces the frozen session-27 control from its
components and refuses to score a candidate unless the reproduction is exact to 1e-9. That check
has caught a real problem before (section 227) and it is cheap.

    .venv/Scripts/python.exe src/an76_v21_level_shape.py --arms C0 E1 E2
"""
import argparse
import hashlib
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
import v21_local_shape as ls

OUT = ROOT / 'outputs' / 'audit_v21_s33'
CACHE_15 = ROOT / 'outputs' / 'audit_v21_s27' / 'forward_predictions.pkl'
MANIFEST_15 = ROOT / 'outputs' / 'audit_v21_s27' / 'manifest.json'
CACHE_7 = ROOT / 'outputs' / 'audit_v21_s29' / 'forward_7d.pkl'
MANIFEST_7 = ROOT / 'outputs' / 'audit_v21_s29' / 'forward_7d_manifest.json'
OOF7 = OUT / 'oof_base_7d.pkl'
OOF7_MANIFEST = OUT / 'oof_base_7d_manifest.json'
FROZEN_C0 = ROOT / 'outputs' / 'audit_v21_s27' / 'preds_v21_increment.pkl'

ARMS = ('C0', 'E1', 'E2')
FEATURES = {'C0': (), 'E1': ('shape_',), 'E2': ('shape_', 'quality_')}
SEEDS_INC = a47.SEEDS_INC
TOL = 1e-9

# Section 227's expected control, at full precision, written down before this session ran
# anything. If the numbers below stop reproducing, the difference is in the pipeline and it gets
# found before a candidate is scored -- the baseline does not get moved to match.
EXPECTED_C0 = {'B1_last15d': 4.2322485291, 'B2_prev15d': 6.5863733772,
               'B3_shift7d': 4.6901306270}
EXPECTED_C0_POOLED = 5.535893869794081


def shape_block(g, horizon_end, prefixes, cache):
    """The extra columns for one horizon, or an empty frame for the control."""
    if not prefixes:
        return None
    he = pd.Timestamp(horizon_end)
    if he not in cache:
        cache[he] = ls.build_local_shape(g, he)
    S = cache[he]
    return S[[col for col in S.columns if col.startswith(prefixes)]]


def design(F, extra):
    """F, or F with the extra block joined on the index. Column order is frozen and asserted."""
    if extra is None:
        return F
    assert F.index.equals(extra.index), 'the shape block must share the feature frame index'
    X = pd.concat([F, extra], axis=1)
    assert len(X.columns) == len(set(X.columns)), 'the shape block must not shadow an F column'
    return X


def fit_hbt(X, y, train_idx, pred_idx):
    """`hbt` exactly as `a47.member_preds` fits it, on whatever design matrix it is handed.

    Same learner, same `fp.LGB_KW`, same five seed positions, same clip. Nothing about the
    fitting procedure is a variable this round: only the columns of `X` change.
    """
    seeds = tuple(range(len(fp.SEEDS_FIT)))
    esT_t = pd.Series(fp.es(X.loc[train_idx, 'T'].values), index=train_idx)
    E_t = y.loc[train_idx] * esT_t / 100.0
    esv = fp.es(X.loc[pred_idx, 'T'].values)
    return np.clip(fp.predict('hbt', X.loc[train_idx], y.loc[train_idx], X.loc[pred_idx],
                              esv, E_t, seeds), 5, 100)


def tod_of(idx):
    """`fp.build_features`' time-of-day column, recomputed from the timestamp.

    The forward caches keep the member predictions but not `tod`, and the stack needs it for the
    time-of-day bands and the harmonic bias. It is a pure function of the index -- `idx.hour +
    idx.minute / 60` -- so recomputing it is exact rather than approximate; `control` asserts the
    recomputed column reproduces the frame's own to 1e-12 before it is used.
    """
    idx = pd.DatetimeIndex(idx)
    return idx.hour + idx.minute / 60.0


def base_frames(cache, name, models):
    """`O_base` (inner out-of-fold) and `V_base` (outer members) for one 15-day block.

    The row order matters: `build_block` concatenated the inner folds in fold order, each
    sorted by timestamp, and the NNLS and least-squares fits inside the stack are reproduced
    bit for bit only if the frame is rebuilt the same way.
    """
    blk = cache.loc[cache.block == name]
    inner = blk.loc[blk.scope == 'inner'].sort_values(['fold', 'datetime'])
    outer = blk.loc[blk.scope == 'outer'].sort_values('datetime')
    O = pd.DataFrame({m: inner['m_' + m].to_numpy() for m in models})
    O['y'] = inner.y.to_numpy()
    O['tod'] = tod_of(inner.datetime).to_numpy()
    O['fold'] = inner.fold.to_numpy()
    O['dt'] = pd.DatetimeIndex(inner.datetime)
    assert O.notna().to_numpy().all(), '%s: the rebuilt meta frame has holes' % name
    V = pd.DataFrame({m: outer['m_' + m].to_numpy() for m in models},
                     index=pd.DatetimeIndex(outer.datetime))
    V['y'] = outer.y.to_numpy()
    return O, V, outer


def rebuild_oof_7d(g, y, cache7, models, feats):
    """`an66.build_one`'s inner out-of-fold frame, which the 7-day cache did not keep.

    The 7-day build stored only the outer rows and the level it had already stacked, so the meta
    parameters cannot be refitted from it. This reruns the same inner folds under the same
    recipe. It is not trusted on faith: `control` below requires the rebuilt `O_base` to
    reproduce each cached `level` to 1e-9, which it cannot do unless the folds, the seeds and
    the frames all match.
    """
    out = {}
    for name, blk in cache7.loc[cache7.scope == 'outer'].groupby('block', sort=False):
        d = blk.sort_values('datetime')
        hs, he = pd.Timestamp(d.origin.iloc[0]), pd.Timestamp(d.horizon_end.iloc[0])
        _, F = a47.frame_at(g, he, feats)
        lab = pd.Series((g.loc[F.index, 'is_test'] == 0).to_numpy(), index=F.index) \
            & y.reindex(F.index).notna()
        idx = F.index[lab.to_numpy()]
        pre = idx[idx <= hs]
        oof = []
        for fi, (vs, ve) in enumerate(a36.inner_origins(pre)):
            v, t = pre[(pre > vs) & (pre <= ve)], pre[pre <= vs]
            if len(t) < 300 or len(v) < 50:
                continue
            _, Fi = a47.frame_at(g, ve, feats)
            r = a47.member_preds(Fi, Fi, y, t, v, models, tuple(range(len(fp.SEEDS_OOF))))
            r['y'] = y.loc[v].to_numpy()
            r['tod'] = Fi.loc[v, 'tod'].to_numpy()
            r['fold'] = fi
            oof.append(r.reset_index(names='dt'))
            print('    %s inner fold %d %s -> %s n=%d'
                  % (name, fi, vs.date(), ve.date(), len(v)), flush=True)
        O = pd.concat(oof, ignore_index=True)
        assert O.dt.max() <= hs, 'meta training reaches past the origin'
        out[name] = O
    return out


def block_context(g, y, name, d, feats):
    """Everything one holdout needs that does not depend on the arm."""
    idx = pd.DatetimeIndex(d.datetime)
    he, hs = pd.Timestamp(d.horizon_end.iloc[0]), pd.Timestamp(d.origin.iloc[0])
    gh, F = a47.frame_at(g, he, feats)
    lab = pd.Series((gh.is_test == 0).to_numpy(), index=gh.index) & y.reindex(gh.index).notna()
    train = gh.index[(lab & (gh.index <= hs)).to_numpy()]
    inc = fp.fit_increments(F, y.reindex(gh.index), a47.train_mask_before(g, gh, y, hs),
                            SEEDS_INC, physics=False, deshrink=False)
    terms = a47.increment_terms(F, idx, inc, None, 0.0)
    return dict(name=name, idx=idx, origin=hs, horizon_end=he, F=F, train=train, terms=terms)


def terms_digest(terms):
    """A checksum of the increment terms, so "the arms shared them" is provable.

    Session 34. The first version hashed only the target vector and lambda, leaving the sparse
    difference operator `M` out entirely -- so two runs whose edge sets differed but whose
    targets happened to match would produce the same digest. The operator decides WHICH pairs of
    timestamps the term constrains, which is exactly the thing a boundary or mask change moves.
    Its shape and its three CSR arrays go in.
    """
    h = hashlib.md5()
    for M, t, lam in terms:
        h.update(np.asarray([lam], float).tobytes())
        h.update(b'none' if t is None else np.asarray(t, float).tobytes())
        if M is None:
            h.update(b'no-operator')
            continue
        C = M.tocsr()
        h.update(np.asarray(C.shape, np.int64).tobytes())
        h.update(np.ascontiguousarray(C.indptr, np.int64).tobytes())
        h.update(np.ascontiguousarray(C.indices, np.int64).tobytes())
        h.update(np.ascontiguousarray(C.data, np.float64).tobytes())
    return h.hexdigest()


def load_validated(path, manifest_path, kind):
    """Read a cached pickle only after its manifest still describes it and the inputs.

    Session 34. `an76` read the 7-day cache and the rebuilt OOF with a bare `pd.read_pickle`,
    which is a receipt rather than a check -- exactly what `a47.load_cache` exists to stop. The
    7-day manifest carries the pickle's own md5 and the dataset hashes, and both are verified.
    This is a provenance repair, not evidence that the cached artifacts were wrong.
    """
    path, manifest_path = Path(path), Path(manifest_path)
    if not path.exists():
        raise FileNotFoundError('%s does not exist' % path)
    if not manifest_path.exists():
        raise FileNotFoundError('%s has no manifest beside it (%s)' % (path, manifest_path))
    man = json.loads(manifest_path.read_text())
    bad = []
    if man.get('cache_md5') != a47.md5(path):
        bad.append('cache_md5: the pickle is not the one this manifest was written for')
    for k, v in a47.input_hashes().items():
        if man.get('inputs', {}).get(k) != v:
            bad.append('inputs[%s]: %s on disk, %s in manifest'
                       % (k, v[:8], str(man.get('inputs', {}).get(k))[:8]))
    if bad:
        raise ValueError('%s cache %s does not match this run:\n  %s'
                         % (kind, path, '\n  '.join(bad)))
    print('  validated %s (%s, md5 %s)' % (kind, path.name, a47.md5(path)[:8]), flush=True)
    return pd.read_pickle(path)


def meta_digest(O, models):
    h = hashlib.md5()
    h.update(np.ascontiguousarray(O[list(models)].to_numpy(float)).tobytes())
    h.update(np.ascontiguousarray(O.y.to_numpy(float)).tobytes())
    h.update(np.ascontiguousarray(O.tod.to_numpy(float)).tobytes())
    return h.hexdigest()


def run(arms, blocks, seed_note):
    OUT.mkdir(parents=True, exist_ok=True)
    models = list(fp.MODELS_L2)
    g = fp.load_grid()
    y = g[fp.TARGET]
    feats, shapes = {}, {}

    cache15 = a47.load_cache(CACHE_15, MANIFEST_15)
    cache7 = load_validated(CACHE_7, MANIFEST_7, '7-day forward')
    frozen = pd.read_pickle(FROZEN_C0)

    # ---- Task 0: the control, before any candidate number exists ---------------------------
    print('\n== Task 0: control reproduction ==', flush=True)
    oof7 = {}
    if '7d' in blocks:
        if OOF7.exists() and OOF7_MANIFEST.exists():
            oof7 = load_validated(OOF7, OOF7_MANIFEST, 'rebuilt 7-day OOF')
        else:
            print('  rebuilding the 7-day inner OOF (not kept by the s29 build)', flush=True)
            oof7 = rebuild_oof_7d(g, y, cache7, models, feats)
            pd.to_pickle(oof7, OOF7)
            c.write_json(OOF7_MANIFEST, dict(
                created=pd.Timestamp.now().isoformat(timespec='seconds'),
                source=str(CACHE_7.relative_to(ROOT)), source_md5=a47.md5(CACHE_7),
                blocks=sorted(oof7), models=models,
                seeds_oof=list(fp.SEEDS_OOF), inputs=a47.input_hashes(),
                code=a47.code_hashes(), cache_md5=a47.md5(OOF7)))

    plans = []
    if '15d' in blocks:
        for name, blk in cache15.loc[cache15.scope == 'outer'].groupby('block', sort=False):
            O, V, outer = base_frames(cache15, name, models)
            plans.append((name, blk.sort_values('datetime'), O, V, outer, '15d'))
    if '7d' in blocks:
        for name, blk in cache7.loc[cache7.scope == 'outer'].groupby('block', sort=False):
            d = blk.sort_values('datetime')
            V = pd.DataFrame({m: d['m_' + m].to_numpy() for m in models},
                             index=pd.DatetimeIndex(d.datetime))
            V['y'] = d.y.to_numpy()
            plans.append((name, d, oof7[name], V, d, '7d'))

    rows, prov, per_row = [], [], []
    for name, d, O, V, outer, family in plans:
        ctx = block_context(g, y, name, d, feats)
        V = V.copy()
        V['tod'] = ctx['F'].loc[ctx['idx'], 'tod'].to_numpy()
        assert np.max(np.abs(V['tod'].to_numpy() - tod_of(ctx['idx']).to_numpy())) < 1e-12, \
            '%s: recomputing tod from the timestamp does not match the feature frame' % name

        level_base = a47.stack_on(O, V, models)
        cached_level = d.level.to_numpy()
        err = float(np.max(np.abs(level_base - cached_level)))
        assert err < TOL, ('%s: O_base does not reproduce the cached level (max %.3g). The meta '
                           'frame is wrong; do not score a candidate against it.' % (name, err))
        z_base = a47.solve(level_base, ctx['idx'], ctx['terms'])
        if family == '15d':
            ref = frozen.loc[(frozen.block == name) & (frozen.scope == 'outer')] \
                .sort_values('datetime')
            e = float(np.max(np.abs(z_base - ref.recon.to_numpy())))
            assert e < TOL, '%s: control does not reproduce the frozen v21 recon (max %.3g)' \
                % (name, e)
        print('  %-12s control reproduced (level %.2g, n=%d)' % (name, err, len(d)), flush=True)

        # Refit C0's own hbt from scratch. It must land on the cached member column, which is
        # what proves the training rows, the seeds and the frame are the incumbent's -- and
        # therefore that E1/E2 differ from C0 in the columns and in nothing else.
        hbt_base = fit_hbt(ctx['F'], y, ctx['train'], ctx['idx'])
        drift = float(np.max(np.abs(hbt_base - V['hbt'].to_numpy())))
        assert drift < TOL, ('%s: the refitted control hbt does not reproduce the cached one '
                             '(max %.3g)' % (name, drift))

        md = meta_digest(O, models)
        td = terms_digest(ctx['terms'])
        for arm in arms:
            t0 = time.time()
            if arm == 'C0':
                hbt_new = hbt_base
            else:
                extra = shape_block(g, ctx['horizon_end'], FEATURES[arm], shapes)
                hbt_new = fit_hbt(design(ctx['F'], extra), y, ctx['train'], ctx['idx'])
            V_new = V.copy()
            V_new['hbt'] = np.clip(hbt_new, 5, 100)
            level_new = a47.stack_on(O, V_new, models)
            z_new = a47.solve(level_new, ctx['idx'], ctx['terms'])
            if arm == 'C0':
                # The substitution control: an unchanged member must give an unchanged answer
                # through clipping, the time-of-day bands, the harmonic bias and the solve.
                assert np.max(np.abs(z_new - z_base)) < TOL, 'zero intervention moved the result'

            yv = d.y.to_numpy()
            per_row.append(pd.DataFrame(dict(
                arm=arm, family=family, block=name, scope='outer',
                origin=ctx['origin'], horizon_end=ctx['horizon_end'],
                datetime=ctx['idx'], score=d.score.to_numpy(), y=yv,
                hbt_base=hbt_base, hbt_new=np.clip(hbt_new, 5, 100),
                level_base=level_base, level_new=level_new, z_base=z_base, z_new=z_new)))
            rows.append(dict(arm=arm, family=family, block=name, n=len(d),
                             rmse_hbt=fp.rmse(yv, hbt_new), rmse_level=fp.rmse(yv, level_new),
                             rmse_z=fp.rmse(yv, z_new), rmse_z_base=fp.rmse(yv, z_base),
                             meta_digest=md, terms_digest=td, seconds=round(time.time() - t0, 1)))
            print('    %-3s hbt %.5f  level %.5f  z %.5f  (%.0f s)'
                  % (arm, rows[-1]['rmse_hbt'], rows[-1]['rmse_level'], rows[-1]['rmse_z'],
                     rows[-1]['seconds']), flush=True)
        prov.append(dict(block=name, family=family, origin=str(ctx['origin']),
                         horizon_end=str(ctx['horizon_end']), n_train=len(ctx['train']),
                         train_end=str(ctx['train'].max()), n_rows=len(d),
                         meta_rows=len(O), meta_digest=md, terms_digest=td))

    P = pd.concat(per_row, ignore_index=True)
    R = pd.DataFrame(rows)
    P.to_pickle(OUT / 'preds_level_shape.pkl')
    R.to_csv(OUT / 'level_shape_arms.csv', index=False)
    pd.DataFrame(prov).to_csv(OUT / 'level_shape_provenance.csv', index=False)

    # One meta frame and one set of increment terms per block, shared by every arm. If these
    # digests ever differ within a block, the arms were not comparable and the table is void.
    for name, sub in R.groupby('block'):
        assert sub.meta_digest.nunique() == 1 and sub.terms_digest.nunique() == 1, \
            '%s: the arms did not share the meta frame and increment terms' % name

    c.write_json(OUT / 'level_shape_manifest.json', dict(
        created=pd.Timestamp.now().isoformat(timespec='seconds'),
        arms=list(arms), blocks=list(blocks), features=FEATURES,
        shape_columns=ls.shape_columns(), quality_columns=ls.quality_columns(),
        seeds_fit=list(fp.SEEDS_FIT), seeds_oof=list(fp.SEEDS_OOF), seeds_inc=list(SEEDS_INC),
        lgb_kw=fp.LGB_KW, models=models, blend_shrink=fp.BLEND_SHRINK,
        increment=dict(physics=False, deshrink=False, lags=False,
                       spec=[list(x) for x in fp.INC_SPEC]),
        expected_control=EXPECTED_C0, expected_control_pooled=EXPECTED_C0_POOLED,
        inputs=a47.input_hashes(), code=a47.code_hashes(),
        helper_code={p: a47.md5(ROOT / p) for p in
                     ('src/v21_local_shape.py', 'src/an76_v21_level_shape.py')},
        incumbent_submission_md5=a47.md5(ROOT / 'outputs' / 'submissions' /
                                         'v21_increment_v16.csv'),
        provenance=prov, note=seed_note))
    print('\n' + R.to_string(index=False))
    print('\nwrote %s' % (OUT / 'level_shape_arms.csv'))
    return P, R


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--arms', nargs='+', default=list(ARMS), choices=list(ARMS))
    ap.add_argument('--blocks', nargs='+', default=['15d', '7d'], choices=['15d', '7d'])
    a = ap.parse_args()
    assert 'C0' in a.arms, 'the control is not optional'
    run(tuple(a.arms), tuple(a.blocks),
        'hbt is the only member refitted; meta and increments come from the control')


if __name__ == '__main__':
    main()
