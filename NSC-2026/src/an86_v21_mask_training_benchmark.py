"""Session 37, Task 2: train `hbt` on two sensor views, and separate that from mere duplication.

    C0   F original, weight 1 per row              the incumbent
    D0   concat(F, F), weight 0.5                  the duplication control
    M1   concat(F, F_masked), weight 0.5           the candidate

`D0` exists because concatenating a frame with itself is not a no-op for a tree: it changes the
histogram bin populations, the bagging draw and the leaf-size and Hessian minimums even when the
total weight is unchanged. Without it, any M1 effect would be confounded with that. **M1 - D0
isolates the change of VIEW; M1 - C0 decides whether the incumbent can be replaced.** D0 is a
control and is not promoted if it happens to win.

Everything else is the incumbent's, through `an76`'s frozen-meta contract: the other five members
come from the validated cache, `O_base` is identical across arms, the increment terms are the
shipped v21 ones fitted from the ORIGINAL frame, and prediction always reads the original frame.
Augmented rows never reach the meta stack or the increment models.

**Stress diagnostic.** After the models are frozen, the same 5% mask is applied inside the SCORED
horizon instead, the frame is rebuilt, and the frozen models predict again. No refitting. It
measures how much a prediction moves when the sensor record moves; it is reported beside the
natural score, never instead of it, because a model that never moves is not thereby good.

    .venv/Scripts/python.exe src/an86_v21_mask_training_benchmark.py
"""
import argparse
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
import an76_v21_level_shape as a76
import v21_sensor_masking as sm

OUT = ROOT / 'outputs' / 'audit_v21_s37'
FROZEN = ROOT / 'outputs' / 'audit_v21_s27' / 'preds_v21_increment.pkl'
ARMS = ('C0', 'D0', 'M1')
TOL = 1e-9
CLIP = (5.0, 100.0)


def fit_models(X, y, seeds, weight=None):
    """`fp.predict('hbt', ...)` split into fit and predict, so a frozen model can be reused.

    With `weight=None` this is exactly what `fp.predict` does internally, which is what lets C0
    reproduce the cached member; the stress pass then predicts from the same objects instead of
    refitting five boosters per call.
    """
    return [lgb.LGBMRegressor(random_state=s, **fp.LGB_KW).fit(X, y, sample_weight=weight)
            for s in seeds]


def predict_models(models, X):
    return np.mean([m.predict(X) for m in models], axis=0)


def stacked(F_a, F_b, y, train_idx):
    """Two views of the same training rows, copy-major, with weights summing to `n_train`."""
    a = F_a.loc[train_idx]
    b = F_b.loc[train_idx]
    assert list(a.columns) == list(b.columns), 'the two views must share the column order'
    assert a.index.equals(b.index), 'the two views must share the training rows'
    X = pd.concat([a, b], axis=0)
    yy = pd.concat([y.reindex(train_idx), y.reindex(train_idx)], axis=0)
    w = np.full(len(X), 0.5)
    assert abs(w.sum() - len(train_idx)) < 1e-9, 'total sample weight must be n_train'
    return X, yy, w


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--arms', nargs='+', default=list(ARMS), choices=list(ARMS))
    ap.add_argument('--blocks', nargs='+', default=['15d', '7d'], choices=['15d', '7d'])
    ap.add_argument('--out', default=str(OUT))
    a = ap.parse_args()
    assert 'C0' in a.arms, 'the incumbent control is not optional'
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    models_l2 = list(fp.MODELS_L2)
    g = fp.load_grid()
    y = g[fp.TARGET]
    feats = {}
    cache15 = a47.load_cache(a76.CACHE_15, a76.MANIFEST_15)
    cache7 = a76.load_validated(a76.CACHE_7, a76.MANIFEST_7, '7-day forward')
    frozen = pd.read_pickle(FROZEN)
    oof7 = {}
    if '7d' in a.blocks:
        oof7 = a76.load_validated(a76.OOF7, a76.OOF7_MANIFEST, 'rebuilt 7-day OOF')

    plans = []
    if '15d' in a.blocks:
        for name, blk in cache15.loc[cache15.scope == 'outer'].groupby('block', sort=False):
            O, V, _o = a76.base_frames(cache15, name, models_l2)
            plans.append((name, '15d', blk.sort_values('datetime'), O, V))
    if '7d' in a.blocks:
        for name, blk in cache7.loc[cache7.scope == 'outer'].groupby('block', sort=False):
            d = blk.sort_values('datetime')
            V = pd.DataFrame({m: d['m_' + m].to_numpy() for m in models_l2},
                             index=pd.DatetimeIndex(d.datetime))
            V['y'] = d.y.to_numpy()
            plans.append((name, '7d', d, oof7[name], V))

    seeds = tuple(range(len(fp.SEEDS_FIT)))
    rows, per_row, prov, stress_rows = [], [], [], []
    for name, family, d, O, V in plans:
        ctx = a76.block_context(g, y, name, d, feats)
        idx, F = ctx['idx'], ctx['F']
        train = ctx['train']
        V = V.copy()
        V['tod'] = F.loc[idx, 'tod'].to_numpy()
        level_base = a47.stack_on(O, V, models_l2)
        assert np.max(np.abs(level_base - d.level.to_numpy())) < TOL, \
            '%s: O_base does not reproduce the cached level' % name
        z_base = a47.solve(level_base, idx, ctx['terms'])
        if family == '15d':
            ref = frozen.loc[(frozen.block == name) & (frozen.scope == 'outer')] \
                .sort_values('datetime')
            assert np.max(np.abs(z_base - ref.recon.to_numpy())) < TOL, \
                '%s: C0 does not reproduce the frozen v21 recon' % name
        print('\n%s (%s)  origin %s  n=%d  train=%d  control reproduced'
              % (name, family, ctx['origin'].date(), len(d), len(train)), flush=True)

        # One masked view per hbt seed, built once and reused by the arm and the manifest.
        views, audits = {}, {}
        if 'M1' in a.arms:
            t0 = time.time()
            for i, aseed in enumerate(sm.TRAIN_SEEDS):
                _F0, Fm, au = sm.build_views(g, ctx['horizon_end'], ctx['origin'], aseed)
                views[i] = Fm
                audits[i] = au
            print('  built %d masked views (%.0f s)' % (len(views), time.time() - t0), flush=True)

        yv = d.y.to_numpy(float)
        fitted, natural = {}, {}
        for arm in a.arms:
            t0 = time.time()
            if arm == 'C0':
                mdl = fit_models(F.loc[train], y.reindex(train), seeds)
                q = np.clip(predict_models(mdl, F.loc[idx]), *CLIP)
                assert np.max(np.abs(q - V['hbt'].to_numpy())) < TOL, \
                    '%s: the refitted control hbt does not match the cache' % name
                fitted[arm] = [mdl]
            elif arm == 'D0':
                X, yy, w = stacked(F, F, y, train)
                mdl = fit_models(X, yy, seeds, w)
                q = np.clip(predict_models(mdl, F.loc[idx]), *CLIP)
                fitted[arm] = [mdl]
            else:
                preds, per_seed = [], []
                for i, s in enumerate(seeds):
                    X, yy, w = stacked(F, views[i], y, train)
                    m = lgb.LGBMRegressor(random_state=s, **fp.LGB_KW).fit(X, yy, sample_weight=w)
                    per_seed.append(m)
                    preds.append(m.predict(F.loc[idx]))
                q = np.clip(np.mean(preds, axis=0), *CLIP)
                fitted[arm] = [per_seed]
            V_new = V.copy()
            V_new['hbt'] = q
            level_new = a47.stack_on(O, V_new, models_l2)
            z_new = a47.solve(level_new, idx, ctx['terms'])
            if arm == 'C0':
                assert np.max(np.abs(z_new - z_base)) < TOL, 'zero intervention moved the result'
            natural[arm] = dict(q=q, z=z_new)
            rows.append(dict(arm=arm, block=name, family=family, n=len(d), n_train=len(train),
                             rmse_member=fp.rmse(yv, q), rmse_level=fp.rmse(yv, level_new),
                             rmse_z=fp.rmse(yv, z_new),
                             d_vs_c0=fp.rmse(yv, z_new) - fp.rmse(yv, z_base),
                             seconds=round(time.time() - t0, 1)))
            per_row.append(pd.DataFrame(dict(
                arm=arm, block=name, family=family, datetime=idx, y=yv, q=q,
                level=level_new, z=z_new, z_c0=z_base, origin=ctx['origin'],
                horizon_end=ctx['horizon_end'], score=d.score.to_numpy())))
            print('    %-3s member %.5f  level %.5f  z %.5f (%+.6f)  [%.0f s]'
                  % (arm, rows[-1]['rmse_member'], rows[-1]['rmse_level'], rows[-1]['rmse_z'],
                     rows[-1]['d_vs_c0'], rows[-1]['seconds']), flush=True)

        if 'M1' in a.arms:
            for i, au in audits.items():
                rep = sm.mask_report(au)
                prov.append(dict(block=name, seed_index=i, aug_seed=sm.TRAIN_SEEDS[i],
                                 digest=sm.audit_digest(au),
                                 **{('%s_%s' % (r.sensor, k)): getattr(r, k)
                                    for r in rep.itertuples() for k in ('eligible', 'masked')}))

        # ---- stress: frozen models, sensors hidden inside the scored horizon -----------------
        for sseed in sm.STRESS_SEEDS:
            Fs, _au = sm.stress_frame(g, ctx['horizon_end'], ctx['origin'], sseed)
            for arm in a.arms:
                mdl = fitted[arm][0]
                if arm == 'M1':
                    qs = np.clip(np.mean([m.predict(Fs.loc[idx]) for m in mdl], axis=0), *CLIP)
                else:
                    qs = np.clip(predict_models(mdl, Fs.loc[idx]), *CLIP)
                base_q, base_z = natural[arm]['q'], natural[arm]['z']
                V_s = V.copy()
                V_s['hbt'] = qs
                z_s = a47.solve(a47.stack_on(O, V_s, models_l2), idx, ctx['terms'])
                # Each arm is compared with ITS OWN natural prediction: the question is how far
                # this model moves when the sensor record moves, not how it stands against C0.
                stress_rows.append(dict(arm=arm, block=name, family=family, stress_seed=sseed,
                                        rms_dq=float(np.sqrt(np.mean((qs - base_q) ** 2))),
                                        rms_dz=float(np.sqrt(np.mean((z_s - base_z) ** 2))),
                                        rmse_z_natural=fp.rmse(yv, base_z),
                                        rmse_z_stress=fp.rmse(yv, z_s),
                                        d_mse_vs_natural=float(np.mean((z_s - yv) ** 2) -
                                                               np.mean((base_z - yv) ** 2))))
        print('    stress: %s' % ', '.join(
            '%s rms_dq %.4f' % (r['arm'], r['rms_dq'])
            for r in stress_rows[-len(a.arms):]), flush=True)

    R = pd.DataFrame(rows)
    P = pd.concat(per_row, ignore_index=True)
    S = pd.DataFrame(stress_rows)
    R.to_csv(out / 'mask_arms.csv', index=False)
    P.to_pickle(out / 'preds_mask.pkl')
    S.to_csv(out / 'mask_stress.csv', index=False)
    pd.DataFrame(prov).to_csv(out / 'mask_provenance.csv', index=False)
    c.write_json(out / 'mask_manifest.json', dict(
        created=pd.Timestamp.now().isoformat(timespec='seconds'),
        arms=list(a.arms), blocks=list(a.blocks), sensors=list(sm.SENSORS), p_mask=sm.P_MASK,
        train_seeds=list(sm.TRAIN_SEEDS), stress_seeds=list(sm.STRESS_SEEDS),
        hbt_seed_positions=list(seeds), lgb_kw=fp.LGB_KW, clip=list(CLIP),
        models=models_l2, blend_shrink=fp.BLEND_SHRINK,
        increment=dict(physics=False, deshrink=False, lags=False),
        weights='0.5 per copy; total equals n_train',
        inputs=a47.input_hashes(), code=a47.code_hashes(),
        helper_code={p: a47.md5(ROOT / p) for p in
                     ('src/v21_sensor_masking.py',
                      'src/an86_v21_mask_training_benchmark.py')},
        incumbent_submission_md5=a47.md5(ROOT / 'outputs' / 'submissions' /
                                         'v21_increment_v16.csv')))
    print('\n' + R[['arm', 'block', 'rmse_member', 'rmse_z', 'd_vs_c0']].to_string(index=False))
    print('\nwrote %s' % out)


if __name__ == '__main__':
    main()
