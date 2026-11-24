"""Session 31, Task 2/3: score the sequence arms through the v21 solver.

Each arm predicts the physical residual, is inverted to a level `q`, blended into the banked v21
level at the frozen weight 0.25, and reconciled with the SAME increment terms v21 ships. The
control must reproduce the frozen v21 predictions to 1e-9 before any candidate number is read.

    .venv/Scripts/python.exe src/an72_v21_sequence_benchmark.py --family random-conv
"""
import argparse
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
import v21_sequence_design as sd
import v21_temporal_models as tm

OUT = ROOT / 'outputs' / 'audit_v21_s31'
ANCHOR = 'v21'


def v21_terms(g, y, d, seeds, feats):
    """The banked increment terms: no physics, no de-shrink, no lags."""
    idx = pd.DatetimeIndex(d.datetime)
    gh, F = a47.frame_at(g, d.horizon_end.iloc[0], feats)
    origin = pd.Timestamp(d.origin.iloc[0])
    mask = a47.train_mask_before(g, gh, y, origin)
    inc = fp.fit_increments(F, y.reindex(gh.index), mask, seeds, physics=False, deshrink=False)
    return idx, gh, F, origin, a47.increment_terms(F, idx, inc, None, 0.0)


def features_for(arm, W, S, bank=None):
    if arm == 'A0':
        return S
    if arm == 'A1':
        return np.hstack([S, tm.trajectory_features(W)])
    if arm == 'A2':
        return np.hstack([S, tm.apply_bank(W, bank)])
    raise ValueError(arm)


def run_family(family, seeds_inc):
    OUT.mkdir(parents=True, exist_ok=True)
    g = fp.load_grid()
    y = g[fp.TARGET]
    cache = a47.load_cache(a47.CACHE_S27, a47.MANIFEST_S27)
    feats = {}
    arms = ('A0', 'A1', 'A2') if family == 'random-conv' else ('B0', 'B1')
    preds = {a: [] for a in arms}
    base_rows, prov = [], []

    for name, blk in cache.loc[cache.scope == 'outer'].groupby('block', sort=False):
        d = blk.sort_values('datetime')
        idx, gh, F, origin, terms = v21_terms(g, y, d, seeds_inc, feats)
        level = d.level.to_numpy()
        z_base = a47.solve(level, idx, terms)
        base_rows.append(d.assign(recon=z_base))

        train = sd.training_rows(g, F, y, origin)
        scaler = sd.ChannelScaler().fit(F, train)
        cols = sd.scalar_columns(F)
        r_train = sd.residual_target(y, F).loc[train].to_numpy()
        W_train = sd.build_windows(F, train, scaler)
        S_train = sd.scalar_matrix(F, train, cols)
        W_out = sd.build_windows(F, idx, scaler)
        S_out = sd.scalar_matrix(F, idx, cols)
        folds = tm.forward_folds(train)
        print('  %-11s train %d  scalars %d  forward folds %d  degenerate %s'
              % (name, len(train), len(cols), len(folds), scaler.degenerate_), flush=True)

        # Scalar path for the neural arms: imputer and scaler fitted on training rows only.
        from sklearn.impute import SimpleImputer
        from sklearn.preprocessing import StandardScaler
        from sklearn.pipeline import make_pipeline as _mp
        sprep = _mp(SimpleImputer(strategy='median'), StandardScaler()).fit(S_train)
        Sn_train, Sn_out = sprep.transform(S_train), sprep.transform(S_out)
        # Early stopping window: the last 7 days of training, all strictly before the origin.
        cut = pd.DatetimeIndex(train).max() - pd.Timedelta(days=7)
        es_val = np.flatnonzero(pd.DatetimeIndex(train) > cut)
        es_trn = np.flatnonzero(pd.DatetimeIndex(train) <= cut)

        for arm in arms:
            t = time.time()
            if arm in ('B0', 'B1'):
                builder = tm.ScalarNet if arm == 'B0' else tm.ThermalWindowNet
                qs, epochs, params = [], [], None
                for seed in tm.SEEDS:
                    # preprocessing for the early-stop fold is refitted on ITS training part
                    sp2 = _mp(SimpleImputer(strategy='median'),
                              StandardScaler()).fit(S_train[es_trn])
                    sc2 = sd.ChannelScaler().fit(F, pd.DatetimeIndex(train)[es_trn])
                    W2 = sd.build_windows(F, pd.DatetimeIndex(train), sc2)
                    _m, best_epoch, _b = tm.train_net(
                        builder, W2[es_trn], sp2.transform(S_train[es_trn]), r_train[es_trn],
                        (W2[es_val], sp2.transform(S_train[es_val]), r_train[es_val]), seed)
                    best_epoch = max(1, best_epoch)
                    model, _e, _b2 = tm.train_net(builder, W_train, Sn_train, r_train,
                                                  None, seed, epochs=best_epoch)
                    qs.append(sd.invert_residual(tm.predict_net(model, W_out, Sn_out), F, idx))
                    epochs.append(best_epoch)
                    params = tm.count_parameters(model)
                q = np.mean(qs, axis=0)
                info = dict(alphas=[], epochs=epochs, parameters=params,
                            n_features=int(Sn_train.shape[1]), constant_features=0)
            elif arm == 'A2':
                qs, alphas, banks = [], [], []
                for seed in tm.SEEDS:
                    bank = tm.kernel_bank(seed)
                    Xtr = features_for(arm, W_train, S_train, bank)
                    Xou = features_for(arm, W_out, S_out, bank)
                    alpha, _tab = tm.forward_alpha(Xtr, r_train, folds)
                    m = tm.make_ridge(alpha).fit(Xtr, r_train)
                    qs.append(sd.invert_residual(m.predict(Xou), F, idx))
                    alphas.append(alpha)
                    banks.append(tm.bank_hash(bank))
                q = np.mean(qs, axis=0)
                info = dict(alphas=alphas, bank_hashes=banks,
                            valid_share=tm.valid_response_share(W_out[:8],
                                                                tm.kernel_bank(tm.SEEDS[0])),
                            n_features=int(Xtr.shape[1]),
                            constant_features=int((np.nanstd(Xtr, axis=0) == 0).sum()))
            else:
                Xtr = features_for(arm, W_train, S_train)
                Xou = features_for(arm, W_out, S_out)
                alpha, _tab = tm.forward_alpha(Xtr, r_train, folds)
                m = tm.make_ridge(alpha).fit(Xtr, r_train)
                q = sd.invert_residual(m.predict(Xou), F, idx)
                info = dict(alphas=[alpha], n_features=int(Xtr.shape[1]),
                            constant_features=int((np.nanstd(Xtr, axis=0) == 0).sum()))

            p_new = sd.blend_level(level, q)
            z_new = a47.solve(p_new, idx, terms)
            preds[arm].append(d.assign(recon=z_new, q=q, level_blend=p_new))
            prov.append(dict(block=name, arm=arm, origin=str(origin), seconds=round(
                time.time() - t, 1), q_rmse=fp.rmse(d.y, q),
                anchor_rmse=fp.rmse(d.y, F.loc[idx, sd.ANCHOR_COL].to_numpy()),
                level_rmse=fp.rmse(d.y, level), recon_rmse=fp.rmse(d.y, z_new),
                base_rmse=fp.rmse(d.y, z_base), **info))
            print('     %-3s q %.4f (anchor %.4f, level %.4f)  recon %.6f vs %.6f'
                  % (arm, prov[-1]['q_rmse'], prov[-1]['anchor_rmse'], prov[-1]['level_rmse'],
                     prov[-1]['recon_rmse'], prov[-1]['base_rmse']), flush=True)

    base = pd.concat(base_rows, ignore_index=True)
    frozen = pd.read_pickle(a47.OUT_S27 / 'preds_v21_increment.pkl')
    j = c.join_predictions(frozen.loc[frozen.scope == 'outer'], base)
    np.testing.assert_allclose(j.recon, j.recon_q, atol=1e-9, rtol=0)
    print('\n  control reproduces the frozen v21 predictions exactly (%d rows)' % len(j))

    ref = a47.report(base, ANCHOR)
    rows, diag = [ref], []
    for arm in arms:
        P = pd.concat(preds[arm], ignore_index=True)
        r = a47.report(P, arm, ref)
        b = a47.bootstrap_pair(base, P)
        r['boot3_lo'], r['boot3_hi'] = b['b3d']['lo'], b['b3d']['hi']
        r['days_improved'] = b['worst_day']['days_improved']
        rows.append(r)
        jj = c.join_predictions(base, P)
        for bl, dd in jj.groupby('block'):
            diag.append(dict(arm=arm, block=bl, **c.direction(dd.y, dd.recon, dd.recon_q)))
        P.to_pickle(OUT / ('preds_seq_%s.pkl' % arm))

    R, D, V = pd.DataFrame(rows), pd.DataFrame(diag), pd.DataFrame(prov)
    print('\n' + R.to_string(index=False))
    print('\ndirection vs v21\n' + D.to_string(index=False))
    R.to_csv(OUT / ('sequence_%s.csv' % family), index=False)
    D.to_csv(OUT / ('sequence_%s_direction.csv' % family), index=False)
    V.to_csv(OUT / ('sequence_%s_provenance.csv' % family), index=False)
    base.to_pickle(OUT / 'preds_seq_v21_control.pkl')
    c.write_json(OUT / ('sequence_%s.json' % family), dict(
        family=family, arms=list(arms), blend_weight=0.25, alphas=list(tm.ALPHAS),
        seeds=list(tm.SEEDS), n_kernels=tm.N_KERNELS, window=sd.WINDOW,
        channels=list(sd.CHANNELS), results=json.loads(R.to_json(orient='records')),
        direction=json.loads(D.to_json(orient='records')),
        provenance=json.loads(V.to_json(orient='records')),
        code={'src/v21_sequence_design.py': a47.md5(ROOT / 'src/v21_sequence_design.py'),
              'src/v21_temporal_models.py': a47.md5(ROOT / 'src/v21_temporal_models.py'),
              'src/an72_v21_sequence_benchmark.py': a47.md5(Path(__file__))},
        level_cache_md5=a47.md5(a47.CACHE_S27)))
    print('\nwrote sequence_%s.csv to %s' % (family, OUT))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--family', default='random-conv',
                    choices=('random-conv', 'learned-conv'))
    a = ap.parse_args()
    run_family(a.family, a47.SEEDS_INC)


if __name__ == '__main__':
    main()
