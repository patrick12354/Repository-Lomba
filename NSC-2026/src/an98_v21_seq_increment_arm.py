"""Session 46: score the random-convolution increments through the v21 solver.

Three arms on the shipped backbone (`MODELS_L2` without `ridge`, `--tod-bias`):

* `control`  — the shipped LightGBM increments. Must reproduce the frozen v21 recon on B1/B2/B3.
* `seq`      — the same horizons and weights, `d_h` from a Ridge over random convolutions instead.
* `both`     — both families, each at HALF the frozen weight, so the total pull toward the dynamics
               is unchanged and the arm tests composition rather than strength. Without that the
               comparison would confound "two views" with "twice the constraint".

Everything else is held: horizons and weights (§147), the level stack, the solver, and §229's
kernel bank and alpha grid.

    .venv/Scripts/python.exe src/an98_v21_seq_increment_arm.py
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
import an76_v21_level_shape as a76
import an91_v21_seq_member_arm as arm
import an96_v21_increment_bundle_split as a96
import v21_seq_increment as si

OUT = ROOT / 'outputs' / 'audit_v21_s46'
M = list(fp.MODELS_L2)
MR = [m for m in M if m != 'ridge']
BLOCKS = ['B1_last15d', 'B2_prev15d', 'B3_shift7d', 'H1_last7d', 'H2_last14d', 'H3_last21d']
PRIMARY = ('B1_last15d', 'B2_prev15d')
SEVEN = ('H1_last7d', 'H2_last14d', 'H3_last21d')


def halve(terms):
    return [(D, t, lam / 2.0) for D, t, lam in terms]


def run():
    OUT.mkdir(parents=True, exist_ok=True)
    g = fp.load_grid()
    y = g[fp.TARGET]
    c15 = a47.load_cache(a76.CACHE_15, a76.MANIFEST_15)
    c7 = a76.load_validated(a76.CACHE_7, a76.MANIFEST_7, '7-day forward')
    oof7 = a76.load_validated(a76.OOF7, a76.OOF7_MANIFEST, 'rebuilt 7-day OOF')
    feats, res = {}, {a: [] for a in ('control', 'seq', 'both')}

    for name in BLOCKS:
        t0 = time.time()
        O, V = a96.block_frames(g, y, name, c15, c7, oof7)
        level = a36.stack(O, V, MR, fp.BLEND_SHRINK)
        idx = pd.DatetimeIndex(V.datetime)
        gh, F = a47.frame_at(g, V.horizon_end.iloc[0], feats)
        mask = a47.train_mask_before(g, gh, y, pd.Timestamp(V.origin.iloc[0]))
        yh = y.reindex(gh.index)

        inc = fp.fit_increments(F, yh, mask, a47.SEEDS_INC)
        lgb_terms = a47.increment_terms(F, idx, inc, None, 0.0)
        seq_t = si.seq_terms(F, idx, yh, mask)

        for label, terms in (('control', lgb_terms), ('seq', seq_t),
                             ('both', halve(lgb_terms) + halve(seq_t))):
            res[label].append((name, V.y.to_numpy(), a47.solve(level, idx, terms)))
        print('  %-12s [%.0f s]  %s' % (name, time.time() - t0,
                                        '  '.join('%s %.5f' % (l, fp.rmse(res[l][-1][1],
                                                                          res[l][-1][2]))
                                                  for l in res)), flush=True)

    def pooled(label, sel):
        yy = np.concatenate([b for n, b, _ in res[label] if n in sel])
        zz = np.concatenate([c for n, _, c in res[label] if n in sel])
        return float(np.sqrt(np.mean((yy - zz) ** 2)))

    summary = {}
    print('\n%-9s %11s %11s %11s' % ('arm', 'd_primary', 'd_7d', 'worst_H'))
    for label in res:
        per = {n: fp.rmse(b, c) - fp.rmse(b2, c2)
               for (n, b, c), (_n, b2, c2) in zip(res[label], res['control'])}
        summary[label] = dict(d_primary=pooled(label, PRIMARY) - pooled('control', PRIMARY),
                              d_pooled7=pooled(label, SEVEN) - pooled('control', SEVEN),
                              worst_h=max(per[n] for n in SEVEN), per_block=per)
        print('%-9s %+11.6f %+11.6f %+11.6f' % (label, summary[label]['d_primary'],
                                                summary[label]['d_pooled7'],
                                                summary[label]['worst_h']))
        print('   per block: %s' % {k[:2]: round(v, 5) for k, v in per.items()})
    (OUT / 'seq_increment_arms.json').write_text(json.dumps(summary, indent=2, default=str))
    pd.to_pickle(res, OUT / 'preds_seq_increment.pkl')
    return summary


if __name__ == '__main__':
    run()
