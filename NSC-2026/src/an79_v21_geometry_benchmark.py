"""Session 34, Task 3: the two geometry candidates, scored through the unchanged v21 solver.

    C0   `fp.fit_increments` -- the shipped incumbent, and the promotion gate
    C1   the same L2 objective through the two-booster plumbing -- isolates the objective
    G1   `separate`: each horizon's error propagated through its own operator
    G2   `coupled`: both horizons through the joint operator

Only the training gradient differs. The level `p` is the cached incumbent one, the meta
parameters are untouched, the solver, its weights and the clip are the shipped ones, and the
features, mask, targets, seeds and tree count are `fit_increments`' own. Inference uses the
predicted increments and nothing about `Q` -- the geometry exists only to train.

**Reported for every arm and every block**, so a gain can be attributed rather than admired:

* increment RMSE per horizon, the statistic the incumbent optimises;
* `||B r||^2 / n` on the HOLDOUT operator, the statistic the surrogate optimises;
* the decomposition `||e0||^2/n + 2 e0^T B r/n + ||B r||^2/n`, which must sum to the pre-clip
  final MSE -- if `||B r||` falls while final RH worsens, the cross-term is where it went;
* `d4 - sum of four d1` disagreement, as a diagnosis of the cancellation `coupled` is allowed to
  learn and `separate` is not. It is not a penalty and nothing is tuned on it.

Holdout targets are never shown to a model. They are read here only to score what was already
produced.

    .venv/Scripts/python.exe src/an79_v21_geometry_benchmark.py --arms G1 G2 \
        --blocks B1 B2 B3 H1 H2 H3
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
import an78_v21_geometry_controls as a78
import v21_increment_geometry as ig
import v21_geometry_boosting as gb

OUT = ROOT / 'outputs' / 'audit_v21_s34' / 'geometry'
FROZEN = ROOT / 'outputs' / 'audit_v21_s27' / 'preds_v21_increment.pkl'
TOL = 1e-9
ARM_MODE = {'C0': None, 'C1': 'l2_control', 'G1': 'separate', 'G2': 'coupled'}
SHORT = {'B1': 'B1_last15d', 'B2': 'B2_prev15d', 'B3': 'B3_shift7d',
         'H1': 'H1_last7d', 'H2': 'H2_last14d', 'H3': 'H3_last21d'}


def holdout_geometry(idx):
    """The operator on the SCORED index. `||B r||` on a holdout is measured with the holdout's
    own geometry -- scoring it with the training `Q` would be a different quantity wearing the
    same name."""
    return ig.build_geometry(pd.DatetimeIndex(idx))


def edge_errors(F, idx, inc, y_true, Gh):
    """Predicted minus true increment, on the holdout edges, stacked in `Gh`'s order."""
    r = np.empty(Gh.m)
    per = {}
    yv = np.asarray(y_true, float)
    for h, _lam in fp.INC_SPEC:
        X = fp.increment_design(F, h, inc.get('cols', fp.INC_COLS),
                                inc.get('physics', False), inc.get('lags', False))
        stamps = Gh.edges[h]
        pred = np.mean([m.predict(X.loc[stamps]) for m in inc[h]], axis=0)
        true = Gh.D[h] @ yv
        r[Gh.slice(h)] = pred - true
        per[h] = dict(rmse=float(np.sqrt(np.mean((pred - true) ** 2))), n=len(stamps),
                      pred=pred, true=true)
    return r, per


def decompose(Gh, p, y, r):
    """`||e0||^2/n + 2 e0^T B r/n + ||B r||^2/n`, which is the pre-clip final MSE."""
    e0 = ig.solver_error(p, y, Gh.A)
    Br = Gh.B @ r
    n = len(y)
    return dict(e0_mse=float(e0 @ e0 / n), cross=float(2 * e0 @ Br / n),
                Br_mse=float(Br @ Br / n), pre_clip_mse=float((e0 + Br) @ (e0 + Br) / n))


def cancellation(per):
    """`d4 - sum of the four d1 steps that span it`, where both are available. Diagnosis only."""
    # d4 ending at t should equal the four 30-minute steps ending at t, t-1, t-2, t-3.
    s1 = pd.Series(per[1]['pred'], index=pd.DatetimeIndex(per[1]['stamps']))
    s4 = pd.Series(per[4]['pred'], index=pd.DatetimeIndex(per[4]['stamps']))
    tot = sum(s1.reindex(s4.index - pd.Timedelta(minutes=30 * k)).to_numpy() for k in range(4))
    ok = np.isfinite(tot)
    if not ok.any():
        return dict(n=0, rmse=float('nan'), mean=float('nan'))
    diff = s4.to_numpy()[ok] - tot[ok]
    return dict(n=int(ok.sum()), rmse=float(np.sqrt(np.mean(diff ** 2))),
                mean=float(np.mean(diff)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--arms', nargs='+', default=['C0', 'C1', 'G1', 'G2'],
                    choices=list(ARM_MODE))
    ap.add_argument('--blocks', nargs='+', default=list(SHORT), choices=list(SHORT))
    ap.add_argument('--rounds', type=int, default=gb.N_ROUNDS)
    a = ap.parse_args()
    assert 'C0' in a.arms, 'the incumbent control is not optional'
    OUT.mkdir(parents=True, exist_ok=True)
    want = {SHORT[b] for b in a.blocks}

    g = fp.load_grid()
    y = g[fp.TARGET]
    frozen = pd.read_pickle(FROZEN)
    feats = {}
    seeds = a47.SEEDS_INC
    rows, per_row, prov, edge_rows = [], [], [], []

    families = ['15d'] if not any(b.startswith('H') for b in a.blocks) else ['15d', '7d']
    for name, family, d in a78.blocks(families):
        if name not in want:
            continue
        ctx = a78.context(g, y, d, feats)
        idx = ctx['idx']
        print('\n%s (%s)  origin %s  n=%d' % (name, family, ctx['origin'].date(), len(d)),
              flush=True)

        edges = ig.effective_edges(ctx['F'], ctx['yh'], ctx['mask'])
        G = ig.build_geometry(ctx['mask'].index[ctx['mask'].to_numpy()], edges=edges)
        Gh = holdout_geometry(idx)
        print('  train geometry m=%d | holdout geometry m=%d' % (G.m, Gh.m), flush=True)

        base_z = None
        for arm in a.arms:
            t0 = time.time()
            mode = ARM_MODE[arm]
            if mode is None:
                inc = gb.incumbent_increments(ctx['F'], ctx['yh'], ctx['mask'], seeds)
            else:
                inc = gb.fit_geometry_increments(ctx['F'], ctx['yh'], ctx['mask'], seeds, mode,
                                                 geometry=G, rounds=a.rounds)
            terms = a47.increment_terms(ctx['F'], idx, inc, None, 0.0)
            z = a47.solve(ctx['level'], idx, terms)
            if arm == 'C0':
                base_z = z
                if family == '15d':
                    ref = frozen.loc[(frozen.block == name) & (frozen.scope == 'outer')] \
                        .sort_values('datetime')
                    e = float(np.max(np.abs(z - ref.recon.to_numpy())))
                    assert e < TOL, '%s: C0 does not reproduce the frozen v21 recon (%.3g)' \
                        % (name, e)

            r, per = edge_errors(ctx['F'], idx, inc, ctx['y'], Gh)
            for h, _lam in fp.INC_SPEC:
                per[h]['stamps'] = Gh.edges[h]
            dec = decompose(Gh, ctx['level'], ctx['y'], r)
            can = cancellation(per)
            rmse = fp.rmse(ctx['y'], z)
            rows.append(dict(
                arm=arm, block=name, family=family, n=len(d), rmse=rmse,
                d_vs_c0=rmse - fp.rmse(ctx['y'], base_z),
                inc_rmse_h1=per[1]['rmse'], inc_rmse_h4=per[4]['rmse'],
                **dec, cancel_rmse=can['rmse'], cancel_mean=can['mean'], cancel_n=can['n'],
                rounds=a.rounds, seconds=round(time.time() - t0, 1)))
            per_row.append(pd.DataFrame(dict(
                arm=arm, block=name, family=family, datetime=idx, y=ctx['y'],
                level=ctx['level'], z=z, z_c0=base_z, origin=ctx['origin'],
                horizon_end=ctx['horizon_end'], score=d.score.to_numpy())))
            for h, _lam in fp.INC_SPEC:
                edge_rows.append(pd.DataFrame(dict(
                    arm=arm, block=name, horizon=h, datetime=per[h]['stamps'],
                    pred=per[h]['pred'], true=per[h]['true'])))
            print('    %-3s RMSE %.6f (%+.6f)  inc h1 %.5f h4 %.5f  |Br|2/n %.5f  cross %+.5f'
                  ' [%.0f s]'
                  % (arm, rmse, rows[-1]['d_vs_c0'], per[1]['rmse'], per[4]['rmse'],
                     dec['Br_mse'], dec['cross'], rows[-1]['seconds']), flush=True)
            if mode is not None:
                prov.append(dict(block=name, arm=arm, mode=mode,
                                 design_digest=inc['design_digest'],
                                 geometry_digest=G.digest(), eps=G.eps, c=G.c, scale=G.scale,
                                 records=inc['records']))
        del G, Gh

    R = pd.DataFrame(rows)
    P = pd.concat(per_row, ignore_index=True)
    R.to_csv(OUT / 'geometry_arms.csv', index=False)
    P.to_pickle(OUT / 'preds_geometry.pkl')
    pd.concat(edge_rows, ignore_index=True).to_pickle(OUT / 'edges_geometry.pkl')
    c.write_json(OUT / 'geometry_manifest.json', dict(
        created=pd.Timestamp.now().isoformat(timespec='seconds'),
        arms=list(a.arms), blocks=sorted(want), rounds=a.rounds, eps=ig.EPS,
        seeds=list(seeds), inc_kw=fp.INC_KW, inc_spec=[list(x) for x in fp.INC_SPEC],
        native_params=gb.native_params(seeds[0]),
        inputs=a47.input_hashes(), code=a47.code_hashes(),
        helper_code={p: a47.md5(ROOT / p) for p in
                     ('src/v21_increment_geometry.py', 'src/v21_geometry_boosting.py',
                      'src/an79_v21_geometry_benchmark.py')},
        controls=dict(gate='C0', objective_isolating='C1'),
        provenance=prov))
    print('\n' + R[['arm', 'block', 'rmse', 'd_vs_c0', 'inc_rmse_h1', 'inc_rmse_h4', 'Br_mse',
                    'cross', 'pre_clip_mse']].to_string(index=False))
    print('\nwrote %s' % OUT)


if __name__ == '__main__':
    main()
