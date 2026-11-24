"""Session 32, step 1: is the sequence level COMPLEMENTARY to the stack, or a worse copy of it?

Section 231 left A2 at −0.018 pooled against a 0.02 bar, with the loss concentrated entirely on
B1 and the gain on B2/B3. Before spending compute on an honest per-origin blend weight, the
question worth answering is cheaper and more basic: do `q` and the v21 level make DIFFERENT
mistakes? A blend only helps when they do. If `q` is simply a noisier estimate of the same thing,
no weight rescues it and the family closes.

**The sweep is free, because the solver is affine in the level.** With `z = A^-1(p + b)`,

    z(w) = A^-1((1-w) p0 + w q + b) = (1-w) A^-1(p0 + b) + w A^-1(q + b)

before clipping, so two solves give every weight exactly. The tests assert that identity rather
than assuming it.

**Everything here that uses an outer label is a DIAGNOSTIC and is labelled as one.** The oracle
weight is computed to answer "is there a weight that would have worked", which bounds the family
from above. It is not a candidate, it is not a selection rule, and section 231's warning applies:
after sections 220 and 227 this log knows exactly how easy it is to turn a diagnostic into an
accidental fit.

    .venv/Scripts/python.exe src/an73_v21_sequence_complementarity.py
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.sparse import identity
from scipy.sparse.linalg import factorized

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
import final_pipeline as fp
import an47_v21_forward_benchmark as a47
import an59_v21_candidate_contract as c
import an72_v21_sequence_benchmark as a72

OUT = ROOT / 'outputs' / 'audit_v21_s32'
WEIGHTS = np.round(np.arange(0.0, 1.0001, 0.05), 3)


def solve_pair(level, q, idx, terms):
    """Pre-clip solutions at w = 0 and w = 1. Every other weight is their interpolation."""
    A = identity(len(level), format='csc')
    b = np.zeros(len(level), float)
    for M, t, lam in terms:
        if M is None:
            continue
        A = (A + lam * (M.T @ M)).tocsc()
        b = b + lam * (M.T @ t)
    lu = factorized(A.tocsc())
    return lu(np.asarray(level, float) + b), lu(np.asarray(q, float) + b)


def z_at(z0_pre, z1_pre, w):
    return np.clip((1.0 - w) * z0_pre + w * z1_pre, 5, 100)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    g = fp.load_grid()
    y = g[fp.TARGET]
    cache = a47.load_cache(a47.CACHE_S27, a47.MANIFEST_S27)
    A2 = pd.read_pickle(ROOT / 'outputs' / 'audit_v21_s31' / 'preds_seq_A2.pkl')
    feats = {}

    rows, sweep, pieces = [], [], {}
    for name, blk in cache.loc[cache.scope == 'outer'].groupby('block', sort=False):
        d = blk.sort_values('datetime')
        idx, _gh, F, origin, terms = a72.v21_terms(g, y, d, a47.SEEDS_INC, feats)
        a = A2.loc[A2.block == name].sort_values('datetime')
        assert np.array_equal(pd.DatetimeIndex(a.datetime), idx)
        level, q, yy = d.level.to_numpy(), a.q.to_numpy(), d.y.to_numpy()
        z0, z1 = solve_pair(level, q, idx, terms)
        pieces[name] = dict(z0=z0, z1=z1, y=yy, idx=idx)

        e_lvl, e_q = level - yy, q - yy
        rows.append(dict(block=name, n=len(yy),
                         level_rmse=fp.rmse(yy, level), q_rmse=fp.rmse(yy, q),
                         err_corr=float(np.corrcoef(e_lvl, e_q)[0, 1]),
                         q_bias=float(e_q.mean()), level_bias=float(e_lvl.mean()),
                         # least-squares optimal weight ON THE LEVEL, closed form
                         w_star_level=float(np.dot(e_lvl, e_lvl - e_q)
                                            / max(np.dot(e_lvl - e_q, e_lvl - e_q), 1e-12))))
        for w in WEIGHTS:
            z = z_at(z0, z1, w)
            sweep.append(dict(block=name, w=float(w), rmse=fp.rmse(yy, z)))

    R = pd.DataFrame(rows)
    S = pd.DataFrame(sweep)

    # pooled over the two primary blocks at each weight
    prim = [b for b in a47.PRIMARY_BLOCKS]
    pooled = []
    for w in WEIGHTS:
        per = S.loc[(S.w == w) & S.block.isin(prim)]
        n = [int(R.loc[R.block == b, 'n'].iloc[0]) for b in per.block]
        pooled.append(dict(w=float(w), pooled=a47.pooled(per.rmse.tolist(), None, n),
                           **{b: float(S.loc[(S.w == w) & (S.block == b), 'rmse'].iloc[0])
                              for b in R.block}))
    P = pd.DataFrame(pooled)
    base = float(P.loc[P.w == 0.0, 'pooled'].iloc[0])
    P['d_pooled'] = P.pooled - base
    best = P.loc[P.pooled.idxmin()]

    print('per-block error structure (level vs sequence q)\n')
    print(R.to_string(index=False))
    print('\npooled B1+B2 by blend weight (ORACLE sweep, diagnostic only)\n')
    print(P[['w', 'pooled', 'd_pooled'] + list(R.block)].to_string(index=False))
    print('\nbest weight on this sweep: w=%.2f pooled %.6f (%+.6f vs w=0)'
          % (best.w, best.pooled, best.d_pooled))
    print('the frozen weight used in section 229 was 0.25: %+.6f'
          % float(P.loc[P.w == 0.25, 'd_pooled'].iloc[0]))
    print('\nper-block oracle weights: ' + ', '.join(
        '%s %.2f' % (b, S.loc[S.block == b].set_index('w').rmse.idxmin()) for b in R.block))

    R.to_csv(OUT / 'complementarity.csv', index=False)
    S.to_csv(OUT / 'complementarity_sweep.csv', index=False)
    P.to_csv(OUT / 'complementarity_pooled.csv', index=False)
    c.write_json(OUT / 'complementarity.json', dict(
        weights=[float(w) for w in WEIGHTS],
        per_block=json.loads(R.to_json(orient='records')),
        pooled=json.loads(P.to_json(orient='records')),
        best_weight=float(best.w), best_pooled=float(best.pooled),
        frozen_weight_delta=float(P.loc[P.w == 0.25, 'd_pooled'].iloc[0]),
        note='oracle sweep uses outer labels; diagnostic bound, not a candidate or a rule'))
    print('\nwrote complementarity.csv to %s' % OUT)


if __name__ == '__main__':
    main()
