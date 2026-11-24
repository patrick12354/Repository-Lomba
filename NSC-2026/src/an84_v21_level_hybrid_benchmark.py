"""Session 36, Task 2: score C0/L0/S1/S2 by replacing only the `hbt` slot of the level stack.

    C0   the incumbent member, `hbt` fitted on RH directly
    L0   ridge on eight drivers plus four harmonics, then `hbt` on its residual
    S1   cubic spline additive backbone plus harmonics, then `hbt` on its residual
    S2   S1 plus two named tensor interactions

`L0` is the control that separates "two stages help" from "smooth nonlinearity helps". If only
`L0` wins, the spline hypothesis is not supported and `L0` is not promoted on that basis -- it was
not the candidate.

Everything but the `hbt` column is the incumbent's, reusing `an76`'s frozen-meta contract: the
other five members come from the validated cache byte for byte, `O_base` is the incumbent
out-of-fold frame and is identical across arms, and the increment terms are the shipped v21 ones
fitted from the incumbent feature frame at each origin. The meta parameters are never refitted on
a candidate's own out-of-fold predictions -- that is a different method and it has not been
evaluated.

C0 is reproduced against the frozen artifacts before any candidate number is read.

    .venv/Scripts/python.exe src/an84_v21_level_hybrid_benchmark.py
"""
import argparse
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
import an76_v21_level_shape as a76
import v21_level_hybrid as lh

OUT = ROOT / 'outputs' / 'audit_v21_s36' / 'hybrid'
FROZEN = ROOT / 'outputs' / 'audit_v21_s27' / 'preds_v21_increment.pkl'
ARMS = ('C0', 'L0', 'S1', 'S2')
KIND = {'C0': None, 'L0': 'linear', 'S1': 'additive', 'S2': 'pairwise'}
TOL = 1e-9


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--arms', nargs='+', default=list(ARMS), choices=list(ARMS))
    ap.add_argument('--blocks', nargs='+', default=['15d', '7d'], choices=['15d', '7d'])
    a = ap.parse_args()
    assert 'C0' in a.arms, 'the incumbent control is not optional'
    OUT.mkdir(parents=True, exist_ok=True)

    models = list(fp.MODELS_L2)
    g = fp.load_grid()
    y = g[fp.TARGET]
    feats = {}
    cache15 = a47.load_cache(a76.CACHE_15, a76.MANIFEST_15)
    cache7 = a76.load_validated(a76.CACHE_7, a76.MANIFEST_7, '7-day forward')
    frozen = pd.read_pickle(FROZEN)

    oof7 = {}
    if '7d' in a.blocks:
        assert a76.OOF7.exists() and a76.OOF7_MANIFEST.exists(), \
            'the rebuilt 7-day OOF is missing; run an76 once to produce it'
        oof7 = a76.load_validated(a76.OOF7, a76.OOF7_MANIFEST, 'rebuilt 7-day OOF')

    plans = []
    if '15d' in a.blocks:
        for name, blk in cache15.loc[cache15.scope == 'outer'].groupby('block', sort=False):
            O, V, _outer = a76.base_frames(cache15, name, models)
            plans.append((name, '15d', blk.sort_values('datetime'), O, V))
    if '7d' in a.blocks:
        for name, blk in cache7.loc[cache7.scope == 'outer'].groupby('block', sort=False):
            d = blk.sort_values('datetime')
            V = pd.DataFrame({m: d['m_' + m].to_numpy() for m in models},
                             index=pd.DatetimeIndex(d.datetime))
            V['y'] = d.y.to_numpy()
            plans.append((name, '7d', d, oof7[name], V))

    rows, per_row, prov = [], [], []
    for name, family, d, O, V in plans:
        ctx = a76.block_context(g, y, name, d, feats)
        idx, F = ctx['idx'], ctx['F']
        V = V.copy()
        V['tod'] = F.loc[idx, 'tod'].to_numpy()
        level_base = a47.stack_on(O, V, models)
        err = float(np.max(np.abs(level_base - d.level.to_numpy())))
        assert err < TOL, '%s: O_base does not reproduce the cached level (%.3g)' % (name, err)
        z_base = a47.solve(level_base, idx, ctx['terms'])
        if family == '15d':
            ref = frozen.loc[(frozen.block == name) & (frozen.scope == 'outer')] \
                .sort_values('datetime')
            e = float(np.max(np.abs(z_base - ref.recon.to_numpy())))
            assert e < TOL, '%s: C0 does not reproduce the frozen v21 recon (%.3g)' % (name, e)
        hbt_base = a76.fit_hbt(F, y, ctx['train'], idx)
        drift = float(np.max(np.abs(hbt_base - V['hbt'].to_numpy())))
        assert drift < TOL, '%s: the refitted control hbt does not match the cache (%.3g)' \
            % (name, drift)
        print('\n%s (%s)  origin %s  n=%d  control reproduced'
              % (name, family, ctx['origin'].date(), len(d)), flush=True)

        yv = d.y.to_numpy(float)
        for arm in a.arms:
            t0 = time.time()
            if arm == 'C0':
                q, gpred, info = hbt_base, np.full(len(idx), np.nan), {}
            else:
                m = lh.LevelHybrid(KIND[arm]).fit(F, y, ctx['train'])
                q, gpred, _h = m.predict(F, idx)
                info = m.info()
            V_new = V.copy()
            V_new['hbt'] = np.clip(q, *lh.CLIP)
            level_new = a47.stack_on(O, V_new, models)
            z_new = a47.solve(level_new, idx, ctx['terms'])
            if arm == 'C0':
                assert np.max(np.abs(z_new - z_base)) < TOL, 'zero intervention moved the result'
            rows.append(dict(arm=arm, block=name, family=family, n=len(d),
                             rmse_member=fp.rmse(yv, q), rmse_level=fp.rmse(yv, level_new),
                             rmse_z=fp.rmse(yv, z_new),
                             rmse_g=fp.rmse(yv, gpred) if np.isfinite(gpred).all() else np.nan,
                             d_vs_c0=fp.rmse(yv, z_new) - fp.rmse(yv, z_base),
                             seconds=round(time.time() - t0, 1), **info))
            per_row.append(pd.DataFrame(dict(
                arm=arm, block=name, family=family, datetime=idx, y=yv,
                g=gpred, q=np.clip(q, *lh.CLIP), hbt_c0=hbt_base,
                level=level_new, z=z_new, z_c0=z_base, origin=ctx['origin'],
                horizon_end=ctx['horizon_end'], score=d.score.to_numpy())))
            print('    %-3s member %.5f  level %.5f  z %.5f (%+.6f)  g %s  [%.0f s]'
                  % (arm, rows[-1]['rmse_member'], rows[-1]['rmse_level'], rows[-1]['rmse_z'],
                     rows[-1]['d_vs_c0'],
                     '%.5f' % rows[-1]['rmse_g'] if np.isfinite(rows[-1]['rmse_g']) else '-',
                     rows[-1]['seconds']), flush=True)
            if info:
                prov.append(dict(arm=arm, block=name, **info))

    R = pd.DataFrame(rows)
    P = pd.concat(per_row, ignore_index=True)
    R.to_csv(OUT / 'hybrid_arms.csv', index=False)
    P.to_pickle(OUT / 'preds_hybrid.pkl')
    pd.DataFrame(prov).to_csv(OUT / 'hybrid_provenance.csv', index=False)
    c.write_json(OUT / 'hybrid_manifest.json', dict(
        created=pd.Timestamp.now().isoformat(timespec='seconds'),
        arms=list(a.arms), kinds=KIND, blocks=list(a.blocks),
        drivers=list(lh.DRIVERS), harmonics=list(lh.HARMONICS),
        interactions=[list(x) for x in lh.INTERACTIONS],
        n_knots=lh.N_KNOTS, degree=lh.DEGREE, ridge_lambda=lh.RIDGE_LAMBDA,
        clip=list(lh.CLIP), lgb_kw=fp.LGB_KW, seeds_fit=list(fp.SEEDS_FIT),
        models=models, blend_shrink=fp.BLEND_SHRINK,
        increment=dict(physics=False, deshrink=False, lags=False),
        inputs=a47.input_hashes(), code=a47.code_hashes(),
        helper_code={p: a47.md5(ROOT / p) for p in
                     ('src/v21_level_hybrid.py', 'src/an84_v21_level_hybrid_benchmark.py')},
        incumbent_submission_md5=a47.md5(ROOT / 'outputs' / 'submissions' /
                                         'v21_increment_v16.csv'),
        provenance=prov))
    print('\n' + R[['arm', 'block', 'rmse_member', 'rmse_g', 'rmse_z', 'd_vs_c0']]
          .to_string(index=False))
    print('\nwrote %s' % OUT)


if __name__ == '__main__':
    main()
