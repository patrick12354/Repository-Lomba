"""Session 33, Task 1: how much of A2's result was the broken internal replay?

`an72` chose the sequence Ridge penalty on internal folds whose features were built at the OUTER
horizon and normalised by a scaler fitted on the whole outer training set (see
`v21_sequence_replay`). This script selects the penalty again with each fold rebuilt at its own
horizon, refits A2 under both choices, and reports the difference.

**This is a methodology control, not a candidate.** It is scored so that the size of the defect
is a measured number rather than an adjective; it is not a fourth arm and nothing here can
promote the sequence family. The plan freezes that before the run, and section 3.1's oracle
result -- that no fixed weight clears the gate even with hindsight -- is unaffected by which
penalty A2 picks.

Two controls run before any delta is read:

* the frozen v21 reconciliation must reproduce to 1e-9 from the cache, and
* the legacy selection must reproduce the alphas session 31 actually recorded, per block and per
  seed. Without that second check a "repair delta" could just be a reimplementation difference.

Only the penalty changes. The final model is fitted on the full outer training set from the
outer frame in both arms, which is that forecast's own horizon and legitimate; the blend weight
stays at the frozen 0.25 and the increment terms are v21's.

    .venv/Scripts/python.exe src/an75_v21_sequence_replay_audit.py
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
import an72_v21_sequence_benchmark as a72
import v21_sequence_design as sd
import v21_temporal_models as tm
import v21_sequence_replay as replay

OUT = ROOT / 'outputs' / 'audit_v21_s33'
S31 = ROOT / 'outputs' / 'audit_v21_s31'
TOL = 1e-9


def legacy_expected():
    """The alphas session 31 recorded for A2, per block, in seed order."""
    d = pd.read_csv(S31 / 'sequence_random-conv_provenance.csv')
    d = d.loc[d.arm == 'A2']
    return {r.block: [float(x) for x in json.loads(r.alphas)] for r in d.itertuples()}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    g = fp.load_grid()
    y = g[fp.TARGET]
    cache = a47.load_cache(a47.CACHE_S27, a47.MANIFEST_S27)
    frozen = pd.read_pickle(ROOT / 'outputs' / 'audit_v21_s27' / 'preds_v21_increment.pkl')
    expected = legacy_expected()
    feats = {}
    rows, folds_rows = [], []

    for name, blk in cache.loc[cache.scope == 'outer'].groupby('block', sort=False):
        d = blk.sort_values('datetime')
        idx, gh, F, origin, terms = a72.v21_terms(g, y, d, a47.SEEDS_INC, feats)
        level = d.level.to_numpy()
        z_base = a47.solve(level, idx, terms)
        ref = frozen.loc[(frozen.block == name) & (frozen.scope == 'outer')] \
            .sort_values('datetime')
        e = float(np.max(np.abs(z_base - ref.recon.to_numpy())))
        assert e < TOL, '%s: control does not reproduce the frozen v21 recon (%.3g)' % (name, e)

        train = sd.training_rows(g, F, y, origin)
        folds = tm.forward_folds(train)
        cols = sd.scalar_columns(F)
        scaler_outer = sd.ChannelScaler().fit(F, train)
        r_train = sd.residual_target(y, F).loc[train].to_numpy()
        S_train = sd.scalar_matrix(F, train, cols)
        S_out = sd.scalar_matrix(F, idx, cols)
        W_train = sd.build_windows(F, train, scaler_outer)
        W_out = sd.build_windows(F, idx, scaler_outer)
        print('\n%s  origin %s  train %d  folds %d' % (name, origin.date(), len(train),
                                                       len(folds)), flush=True)

        qs = {'legacy': [], 'replayed': []}
        alphas = {'legacy': [], 'replayed': []}
        for si, seed in enumerate(tm.SEEDS):
            t0 = time.time()
            bank = tm.kernel_bank(seed)
            a_old, _ = replay.legacy_alpha(F, scaler_outer, g, y, train, folds, bank)
            a_new, _tab, prov = replay.replay_alpha(g, y, train, folds, bank,
                                                   feature_cache=feats)
            assert a_old == expected[name][si], \
                ('%s seed %d: the legacy path reproduces %g, session 31 recorded %g -- the '
                 'comparison is not measuring the repair' % (name, si, a_old,
                                                             expected[name][si]))
            Xtr = np.hstack([S_train, tm.apply_bank(W_train, bank)])
            Xou = np.hstack([S_out, tm.apply_bank(W_out, bank)])
            for tag, alpha in (('legacy', a_old), ('replayed', a_new)):
                m = tm.make_ridge(alpha).fit(Xtr, r_train)
                qs[tag].append(sd.invert_residual(m.predict(Xou), F, idx))
                alphas[tag].append(alpha)
            for rec in prov:
                folds_rows.append(dict(block=name, seed=seed, **rec,
                                       alpha_legacy=a_old, alpha_replayed=a_new))
            print('  seed %d  alpha legacy %g -> replayed %g  (%.0f s)'
                  % (si, a_old, a_new, time.time() - t0), flush=True)

        for tag in ('legacy', 'replayed'):
            q = np.mean(qs[tag], axis=0)
            z = a47.solve(sd.blend_level(level, q), idx, terms)
            rows.append(dict(block=name, arm=tag, origin=str(origin),
                             horizon_end=str(d.horizon_end.iloc[0]), n=len(d),
                             n_train=len(train), alphas=json.dumps(alphas[tag]),
                             q_rmse=fp.rmse(d.y, q), level_rmse=fp.rmse(d.y, level),
                             recon_rmse=fp.rmse(d.y, z), base_rmse=fp.rmse(d.y, z_base)))
            print('  %-9s q %.5f  recon %.6f  (v21 base %.6f)'
                  % (tag, rows[-1]['q_rmse'], rows[-1]['recon_rmse'], rows[-1]['base_rmse']),
                  flush=True)

    R = pd.DataFrame(rows)
    wide = R.pivot(index='block', columns='arm',
                   values=['alphas', 'q_rmse', 'recon_rmse', 'base_rmse', 'n_train'])
    R.to_csv(OUT / 'replay_delta.csv', index=False)
    pd.DataFrame(folds_rows).to_csv(OUT / 'replay_folds.csv', index=False)
    c.write_json(OUT / 'replay_delta.json', dict(
        created=pd.Timestamp.now().isoformat(timespec='seconds'),
        note=('methodology control only; the repaired replay is not a candidate and cannot '
              'promote the sequence family'),
        seeds=list(tm.SEEDS), alpha_grid=list(tm.ALPHAS), n_kernels=tm.N_KERNELS,
        blend_weight=0.25, rows=R.to_dict('records'),
        helper_code={p: a47.md5(ROOT / p) for p in
                     ('src/v21_sequence_replay.py',
                      'src/an75_v21_sequence_replay_audit.py')}))
    print('\n' + R.to_string(index=False))
    print('\n' + wide.to_string())
    print('\nwrote %s' % (OUT / 'replay_delta.csv'))


if __name__ == '__main__':
    main()
