"""Session 32, step 2: a blend weight fitted per origin from data that origin could hold.

Section 233 established the shape of the problem. The per-block optimal weights are 0.00, 0.37
and 0.50 — an enormous spread — so no single frozen weight can serve all three, and the oracle
best uniform weight still costs B1 0.119 and therefore still fails the gate. The only route left
for this family is a weight that ADAPTS, chosen at each origin from data available there.

**The contract is section 227's, not section 220's.** A calibration record is admissible at an
origin only when its target timestamp is at or before that origin AND the forecast that produced
it was launched at or before it. Every inner fold's `q` is produced by an A2 model trained solely
on rows before that fold's own origin, with its own channel scaler and its own alpha selection —
the full pipeline replayed, not a shortcut.

**The weight grid is frozen** at 0.00 to 0.50 in steps of 0.05, and **w = 0 competes in the same
selection and wins ties**, so an origin with no usable evidence returns the banked prediction
rather than a shrunken guess. The same 1% relative margin as section 220 applies: a non-zero
weight must beat zero by 1% of its forward SSE. With three alphas and eleven weights racing zero,
chance wins are otherwise routine.

**This cannot beat the oracle of section 233.** If it fails, the family is closed on a bound
rather than on a single disappointing run — which is a stronger reason to stop than any this log
has had for a family that showed real signal.

    .venv/Scripts/python.exe src/an74_v21_sequence_weight.py
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
import an73_v21_sequence_complementarity as a73
import v21_sequence_design as sd
import v21_temporal_models as tm

OUT = ROOT / 'outputs' / 'audit_v21_s32'
WEIGHTS = tuple(np.round(np.arange(0.0, 0.5001, 0.05), 3))
MARGIN = 0.01                 # same as section 220: beat zero by 1% of its SSE, not merely tie
MIN_ROWS, MIN_ORIGINS = 288, 2
ANCHOR = 'v21'


def fit_q(g, y, d, seeds_inc, feats):
    """Replay the whole A2 pipeline for one forecast window: its own training rows, its own
    channel scaler, its own alpha, three seeds averaged."""
    idx, _gh, F, origin, terms = a72.v21_terms(g, y, d, seeds_inc, feats)
    train = sd.training_rows(g, F, y, origin)
    if len(train) < 600:
        return None
    scaler = sd.ChannelScaler().fit(F, train)
    cols = sd.scalar_columns(F)
    r_train = sd.residual_target(y, F).loc[train].to_numpy()
    W_train, S_train = sd.build_windows(F, train, scaler), sd.scalar_matrix(F, train, cols)
    W_out, S_out = sd.build_windows(F, idx, scaler), sd.scalar_matrix(F, idx, cols)
    folds = tm.forward_folds(train)
    if not folds:
        return None
    qs = []
    for seed in tm.SEEDS:
        bank = tm.kernel_bank(seed)
        Xtr = np.hstack([S_train, tm.apply_bank(W_train, bank)])
        Xou = np.hstack([S_out, tm.apply_bank(W_out, bank)])
        alpha, _t = tm.forward_alpha(Xtr, r_train, folds)
        qs.append(sd.invert_residual(tm.make_ridge(alpha).fit(Xtr, r_train).predict(Xou),
                                     F, idx))
    q = np.mean(qs, axis=0)
    z0, z1 = a73.solve_pair(d.level.to_numpy(), q, idx, terms)
    return dict(idx=idx, y=d.y.to_numpy(), q=q, level=d.level.to_numpy(),
                z0=z0, z1=z1, origin=origin, block=d.block.iloc[0])


def eligible(parts, origin):
    """Section 227's rule, applied to sequence calibration records."""
    origin = pd.Timestamp(origin)
    frames = []
    for p in parts:
        keep = pd.DatetimeIndex(p['idx']) <= origin
        if not keep.any() or pd.Timestamp(p['origin']) > origin:
            continue
        frames.append(pd.DataFrame(dict(dt=pd.DatetimeIndex(p['idx'])[keep],
                                        origin=p['origin'], y=p['y'][keep],
                                        z0=p['z0'][keep], z1=p['z1'][keep])))
    if not frames:
        return None
    D = pd.concat(frames, ignore_index=True).sort_values(['dt', 'origin'])
    return D.drop_duplicates(subset='dt', keep='last').sort_values('dt').reset_index(drop=True)


def choose_weight(cal):
    """Forward weight selection on eligible calibration rows, zero competing and winning ties."""
    table = []
    for w in WEIGHTS:
        z = np.clip((1.0 - w) * cal.z0.to_numpy() + w * cal.z1.to_numpy(), 5, 100)
        table.append(dict(w=float(w), sse=float(np.sum((cal.y.to_numpy() - z) ** 2))))
    zero = [t['sse'] for t in table if t['w'] == 0.0][0]
    for t in table:
        t['relative_gain_vs_zero'] = (zero - t['sse']) / zero if zero > 0 else 0.0
    best = min((t for t in table if t['w'] > 0), key=lambda t: t['sse'])
    gain = (zero - best['sse']) / zero if zero > 0 else 0.0
    return (best['w'] if gain >= MARGIN else 0.0), table


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    g = fp.load_grid()
    y = g[fp.TARGET]
    cache = a47.load_cache(a47.CACHE_S27, a47.MANIFEST_S27)
    seeds, feats = a47.SEEDS_INC, {}

    inner, outer = {}, {}
    t0 = time.time()
    for name, blk in cache.groupby('block', sort=False):
        inner[name] = []
        for scope, fold in sorted(set(zip(blk.scope, blk.fold))):
            d = blk.loc[(blk.scope == scope) & (blk.fold == fold)]
            if scope == 'inner' and bool(d.meta_fallback.iloc[0]):
                continue
            p = fit_q(g, y, d.sort_values('datetime'), seeds, feats)
            if p is None:
                continue
            (outer.__setitem__(name, p) if scope == 'outer' else inner[name].append(p))
        print('  %-11s calibration windows %d  (%.0f s)'
              % (name, len(inner[name]), time.time() - t0), flush=True)

    rows, prov, preds = [], [], []
    for name, op in outer.items():
        cal = eligible(inner[name], op['origin'])
        if cal is None or len(cal) < MIN_ROWS or cal.origin.nunique() < MIN_ORIGINS:
            w, table, reason = 0.0, [], 'insufficient calibration'
        else:
            w, table = choose_weight(cal)
            reason = 'fitted' if w > 0 else 'zero won the forward selection'
        z = a73.z_at(op['z0'], op['z1'], w)
        preds.append(pd.DataFrame(dict(block=name, datetime=op['idx'], y=op['y'],
                                       score=True, recon=z)))
        prov.append(dict(block=name, weight=w, reason=reason,
                         calibration_rows=0 if cal is None else len(cal),
                         calibration_origins=0 if cal is None else int(cal.origin.nunique()),
                         calibration_end=None if cal is None else str(cal.dt.max()),
                         origin=str(op['origin']),
                         base_rmse=fp.rmse(op['y'], a73.z_at(op['z0'], op['z1'], 0.0)),
                         new_rmse=fp.rmse(op['y'], z),
                         selection=table))
        print('  %-11s w=%.2f  %-28s cal rows %s  %.6f -> %.6f'
              % (name, w, reason, prov[-1]['calibration_rows'],
                 prov[-1]['base_rmse'], prov[-1]['new_rmse']), flush=True)

    base = pd.concat([pd.DataFrame(dict(block=n, datetime=p['idx'], y=p['y'], score=True,
                                        recon=a73.z_at(p['z0'], p['z1'], 0.0)))
                      for n, p in outer.items()], ignore_index=True)
    frozen = pd.read_pickle(a47.OUT_S27 / 'preds_v21_increment.pkl')
    j = c.join_predictions(frozen.loc[frozen.scope == 'outer'], base)
    np.testing.assert_allclose(j.recon, j.recon_q, atol=1e-9, rtol=0)
    print('\n  control reproduces the frozen v21 predictions exactly (%d rows)' % len(j))

    P = pd.concat(preds, ignore_index=True)
    ref = a47.report(base, ANCHOR)
    r = a47.report(P, 'sequence_honest_weight', ref)
    b = a47.bootstrap_pair(base, P)
    r['boot3_lo'], r['boot3_hi'] = b['b3d']['lo'], b['b3d']['hi']
    R = pd.DataFrame([ref, r])
    print('\n' + R.to_string(index=False))

    R.to_csv(OUT / 'sequence_weight.csv', index=False)
    pd.DataFrame([{k: v for k, v in p.items() if k != 'selection'}
                  for p in prov]).to_csv(OUT / 'sequence_weight_provenance.csv', index=False)
    P.to_pickle(OUT / 'preds_sequence_honest_weight.pkl')
    c.write_json(OUT / 'sequence_weight.json', dict(
        weights=[float(w) for w in WEIGHTS], margin=MARGIN, min_rows=MIN_ROWS,
        min_origins=MIN_ORIGINS, per_block=prov,
        results=json.loads(R.to_json(orient='records')), bootstrap=b,
        code={'src/an74_v21_sequence_weight.py': a47.md5(Path(__file__))},
        level_cache_md5=a47.md5(a47.CACHE_S27)))
    print('\nwrote sequence_weight.csv to %s' % OUT)


if __name__ == '__main__':
    main()
