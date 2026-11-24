"""Session 34, Task 2: control parity before any geometry candidate is trained.

Two questions, answered in order, and no candidate is fitted until both have an answer.

1. **Does C0 reproduce the shipped v21?** `fp.fit_increments` at the v21 configuration, run
   through the same solver and the same cached level, must land on the frozen predictions to
   1e-9. If it does not, the harness has moved and nothing measured against it means anything.

2. **How far is C1 from C0, and is that distance meaningful?** C1 is the same L2 objective driven
   through the native two-booster plumbing the geometry arms use. The plan expected the two to
   agree to 1e-5. They do not, and the cause is identified in `v21_geometry_boosting`: with
   `colsample_bytree = 0.8` LightGBM draws different per-tree feature subsets on the
   custom-objective path. Rather than assert that this is harmless, the run measures it against
   the only reference that makes it interpretable -- the spread of C0 under DIFFERENT SEED SETS.
   If the plumbing gap sits inside the seed band, C1 is an L2 model with a different random draw,
   and `G - C1` is a fair reading of what the objective did.

Nothing here is a candidate. `an79` trains G1/G2 and is not run until this reports.

    .venv/Scripts/python.exe src/an78_v21_geometry_controls.py
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
import v21_increment_geometry as ig
import v21_geometry_boosting as gb

OUT = ROOT / 'outputs' / 'audit_v21_s34' / 'geometry'
FROZEN = ROOT / 'outputs' / 'audit_v21_s27' / 'preds_v21_increment.pkl'
TOL = 1e-9
SEED_SHIFTS = (0, 100, 200)      # alternate seed sets used to size the noise band


def blocks(which):
    """(name, rows) for every holdout, from the validated caches."""
    out = []
    if '15d' in which:
        cache = a47.load_cache(a47.CACHE_S27, a47.MANIFEST_S27)
        for name, blk in cache.loc[cache.scope == 'outer'].groupby('block', sort=False):
            out.append((name, '15d', blk.sort_values('datetime')))
    if '7d' in which:
        cache7 = a76.load_validated(a76.CACHE_7, a76.MANIFEST_7, '7-day forward')
        for name, blk in cache7.loc[cache7.scope == 'outer'].groupby('block', sort=False):
            out.append((name, '7d', blk.sort_values('datetime')))
    return out


def context(g, y, d, feats):
    idx = pd.DatetimeIndex(d.datetime)
    he, hs = pd.Timestamp(d.horizon_end.iloc[0]), pd.Timestamp(d.origin.iloc[0])
    gh, F = a47.frame_at(g, he, feats)
    mask = a47.train_mask_before(g, gh, y, hs)
    return dict(idx=idx, origin=hs, horizon_end=he, F=F, mask=mask,
                yh=y.reindex(gh.index), level=d.level.to_numpy(), y=d.y.to_numpy())


def reconcile(ctx, inc):
    return a47.solve(ctx['level'], ctx['idx'],
                     a47.increment_terms(ctx['F'], ctx['idx'], inc, None, 0.0))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--blocks', nargs='+', default=['15d', '7d'], choices=['15d', '7d'])
    ap.add_argument('--rounds', type=int, default=gb.N_ROUNDS)
    ap.add_argument('--noise-blocks', nargs='+', default=['B1_last15d', 'B2_prev15d'],
                    help='blocks on which the seed-noise band is measured')
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)

    g = fp.load_grid()
    y = g[fp.TARGET]
    frozen = pd.read_pickle(FROZEN)
    feats = {}
    seeds = a47.SEEDS_INC
    rows, prov = [], []

    for name, family, d in blocks(a.blocks):
        ctx = context(g, y, d, feats)
        print('\n%s (%s)  origin %s  n=%d' % (name, family, ctx['origin'].date(), len(d)),
              flush=True)

        # ---- C0: the incumbent, and the reproduction gate ----------------------------------
        t0 = time.time()
        c0 = gb.incumbent_increments(ctx['F'], ctx['yh'], ctx['mask'], seeds)
        z0 = reconcile(ctx, c0)
        sec0 = time.time() - t0
        if family == '15d':
            ref = frozen.loc[(frozen.block == name) & (frozen.scope == 'outer')] \
                .sort_values('datetime')
            err = float(np.max(np.abs(z0 - ref.recon.to_numpy())))
            assert err < TOL, ('%s: C0 does not reproduce the frozen v21 recon (max %.3g). Stop; '
                               'the harness has moved.' % (name, err))
            print('  C0 reproduces the frozen v21 recon (max %.2g)' % err, flush=True)
        rmse0 = fp.rmse(ctx['y'], z0)

        # ---- geometry, built once per origin and shared by the arms ------------------------
        t0 = time.time()
        edges = ig.effective_edges(ctx['F'], ctx['yh'], ctx['mask'])
        G = ig.build_geometry(ctx['mask'].index[ctx['mask'].to_numpy()], edges=edges)
        secG = time.time() - t0
        print('  geometry n=%d m=%d  %.1f s  %s' % (len(G.index), G.m, secG,
              {k: round(v, 1) for k, v in G.memory_mb().items()}), flush=True)

        # ---- C1: same objective, the geometry arms' plumbing --------------------------------
        t0 = time.time()
        c1 = gb.fit_geometry_increments(ctx['F'], ctx['yh'], ctx['mask'], seeds, 'l2_control',
                                        geometry=G, rounds=a.rounds)
        z1 = reconcile(ctx, c1)
        sec1 = time.time() - t0
        gap = gb.compare_predictions(c0, c1, ctx['F'], ctx['idx'])
        rmse1 = fp.rmse(ctx['y'], z1)
        print('  C0 %.6f | C1 %.6f  (d %+.6f)  max|dd| h1 %.4f h4 %.4f  [%.0f s / %.0f s]'
              % (rmse0, rmse1, rmse1 - rmse0, gap[1], gap[4], sec0, sec1), flush=True)
        rows.append(dict(block=name, family=family, arm='C0', rmse=rmse0, d_vs_c0=0.0,
                         seconds=round(sec0, 1), n=len(d)))
        rows.append(dict(block=name, family=family, arm='C1', rmse=rmse1, d_vs_c0=rmse1 - rmse0,
                         max_dd_h1=gap[1], max_dd_h4=gap[4], seconds=round(sec1, 1), n=len(d)))

        # ---- the seed band: how much C0 moves when only the seeds change --------------------
        if name in a.noise_blocks:
            for shift in SEED_SHIFTS[1:]:
                alt = tuple(s + shift for s in seeds)
                ca = gb.incumbent_increments(ctx['F'], ctx['yh'], ctx['mask'], alt)
                za = reconcile(ctx, ca)
                ga = gb.compare_predictions(c0, ca, ctx['F'], ctx['idx'])
                rows.append(dict(block=name, family=family, arm='C0_seed+%d' % shift,
                                 rmse=fp.rmse(ctx['y'], za), d_vs_c0=fp.rmse(ctx['y'], za) - rmse0,
                                 max_dd_h1=ga[1], max_dd_h4=ga[4], n=len(d)))
                print('    C0 seeds+%d  %.6f (d %+.6f)  max|dd| h1 %.4f h4 %.4f'
                      % (shift, rows[-1]['rmse'], rows[-1]['d_vs_c0'], ga[1], ga[4]), flush=True)

        prov.append(dict(block=name, family=family, origin=str(ctx['origin']),
                         horizon_end=str(ctx['horizon_end']), n_rows=len(d),
                         n_train=len(G.index), m_edges=G.m,
                         edges_h1=len(G.edges[1]), edges_h4=len(G.edges[4]),
                         geometry_digest=G.digest(), design_digest=c1['design_digest'],
                         eps=G.eps, c=G.c, scale=G.scale, rounds=a.rounds))
        del G

    R = pd.DataFrame(rows)
    R.to_csv(OUT / 'controls.csv', index=False)
    pd.DataFrame(prov).to_csv(OUT / 'controls_provenance.csv', index=False)

    band = R.loc[R.arm.str.startswith('C0_seed')]
    c1r = R.loc[R.arm == 'C1']
    verdict = dict(
        c0_reproduces_frozen_v21=True,
        c1_vs_c0_max_abs_rmse=float(c1r.d_vs_c0.abs().max()),
        seed_band_max_abs_rmse=float(band.d_vs_c0.abs().max()) if len(band) else None,
        c1_within_seed_band=(bool(c1r.d_vs_c0.abs().max() <= band.d_vs_c0.abs().max())
                             if len(band) else None),
        note=('C1 is not bit-identical to C0: with colsample_bytree=0.8 LightGBM draws different '
              'per-tree feature subsets on the custom-objective path. The comparison that '
              'isolates the objective is G - C1; the promotion gate is G - C0.'))
    c.write_json(OUT / 'controls.json', dict(
        created=pd.Timestamp.now().isoformat(timespec='seconds'),
        seeds=list(seeds), seed_shifts=list(SEED_SHIFTS), rounds=a.rounds, eps=ig.EPS,
        inc_kw=fp.INC_KW, native_params=gb.native_params(seeds[0]),
        inputs=a47.input_hashes(), code=a47.code_hashes(),
        helper_code={p: a47.md5(ROOT / p) for p in
                     ('src/v21_increment_geometry.py', 'src/v21_geometry_boosting.py',
                      'src/an78_v21_geometry_controls.py')},
        verdict=verdict, rows=rows, provenance=prov))
    print('\n' + R.to_string(index=False))
    print('\nC1 vs C0 max |dRMSE| %.6f ; seed band max |dRMSE| %s'
          % (verdict['c1_vs_c0_max_abs_rmse'], verdict['seed_band_max_abs_rmse']))
    print('C1 inside the seed band: %s' % verdict['c1_within_seed_band'])
    print('wrote %s' % OUT)


if __name__ == '__main__':
    main()
