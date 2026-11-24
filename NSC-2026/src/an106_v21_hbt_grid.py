"""Session 48: the `hbt` hyper-parameters, swept on the repaired forward harness for the first time.

`hbt` holds 0.489 of the shipped global blend weight. Its parameters were last tuned in **session 9**
(progress.md 30), on a 118-column feature set, before the increment machinery, before `--drop-ridge`,
and on the meta-validation harness the session-27 audit found to be sharing labels across folds.
`n_estimators` is the only one anything has moved since, and §274 found the response monotone over
900/1100/1400/1800/2400 with J04 proving the axis is `n_estimators x learning_rate` -- the total
shrinkage budget -- rather than the number of steps. **The incumbent is under-fitted and the other
five knobs have never been looked at on this harness.**

Only `hbt` varies. Every other member comes from the session-27 forward cache, so no arm can differ
by a `cat` fit, and each block's blend is refitted from its own past-only inner frame with the §310
de-bias applied. The screen runs on the three 15-day B blocks; anything that survives goes to all
six with the increments.

The grid is registered here before any number is read, and K12 is the control: `1800 x 0.015` holds
the budget at the incumbent's 27, so a gain there would mean steps rather than budget and would
contradict §274.

    .venv/Scripts/python.exe src/an106_v21_hbt_grid.py [--confirm id1,id2] [--blocks all]
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
import lightgbm as lgb
import final_pipeline as fp
import an36_increment_production as a36
import an47_v21_forward_benchmark as a47
import an76_v21_level_shape as a76
import an96_v21_increment_bundle_split as a96
import an100_v21_member_bias_arm as bias_arm

OUT = ROOT / 'outputs' / 'audit_v21_s48'
M = list(fp.MODELS_L2)
MR = [m for m in M if m != 'ridge']
B_BLOCKS = ['B1_last15d', 'B2_prev15d', 'B3_shift7d']
ALL_BLOCKS = B_BLOCKS + ['H1_last7d', 'H2_last14d', 'H3_last21d']
PRIMARY = ('B1_last15d', 'B2_prev15d')
SEVEN = ('H1_last7d', 'H2_last14d', 'H3_last21d')
SEEDS = tuple(fp.SEEDS_OOF)      # raised to five for the confirm stage; see --seeds

GRID = {
    'control': {},
    'K01_trees2400': dict(n_estimators=2400),
    'K02_leaves31': dict(num_leaves=31),
    'K03_leaves31_t1800': dict(num_leaves=31, n_estimators=1800),
    'K04_leaves7_t2400': dict(num_leaves=7, n_estimators=2400),
    'K05_mcs10': dict(min_child_samples=10),
    'K06_mcs50': dict(min_child_samples=50),
    'K07_colsample40': dict(colsample_bytree=0.4),
    'K08_colsample100': dict(colsample_bytree=1.0),
    'K09_lambda03': dict(reg_lambda=0.3),
    'K10_lambda30': dict(reg_lambda=30.0),
    'K11_subsample60': dict(subsample=0.6),
    'K12_budget_control': dict(n_estimators=1800, learning_rate=0.015),
    # Registered AFTER the screen and BEFORE the confirm, with the reasoning written down so it
    # can be graded: the screen orders the arms by STRUCTURAL capacity per tree and nothing else.
    # K05 (min_child_samples 10, the most capacity) is the worst arm at +0.042; K02/K03
    # (num_leaves 31) are next worst; K04 (num_leaves 7), K11 (subsample 0.6) and K06
    # (min_child_samples 50) are the three best. K10 (reg_lambda 30) is worse, so it is not
    # shrinkage in general -- only the amount of structure each tree is allowed to fit. C1 is the
    # two strongest points on that one axis put together, at the tree count the axis needs.
    'C1_leaves7_sub60_t2400': dict(num_leaves=7, subsample=0.6, n_estimators=2400),
    'C2_leaves7_sub60_mcs50_t2400': dict(num_leaves=7, subsample=0.6, min_child_samples=50,
                                          n_estimators=2400),
}


def kw_for(arm):
    kw = dict(fp.LGB_KW)
    kw.update(GRID[arm])
    return kw


def block_folds(g, y, cache7, oof7, c15, name):
    """(train index, predict index, horizon_end) for every inner fold and the outer window."""
    if name.startswith('B'):
        blk = c15[c15.block == name]
        out = []
        for (scope, fold), d in blk.groupby(['scope', 'fold'], sort=False):
            d = d.sort_values('datetime')
            out.append((scope, fold, pd.Timestamp(d.origin.iloc[0]),
                        pd.DatetimeIndex(d.datetime), pd.Timestamp(d.horizon_end.iloc[0])))
        return out
    d = cache7[(cache7.block == name) & (cache7.scope == 'outer')].sort_values('datetime')
    out = [('outer', -1, pd.Timestamp(d.origin.iloc[0]), pd.DatetimeIndex(d.datetime),
            pd.Timestamp(d.horizon_end.iloc[0]))]
    o = oof7[name]
    for fold, dd in o.groupby('fold', sort=False):
        idx = pd.DatetimeIndex(dd.dt if 'dt' in dd else dd.index)
        out.append(('inner', int(fold), idx.min() - pd.Timedelta(minutes=30), idx,
                    pd.Timestamp(d.horizon_end.iloc[0])))
    return out


def hbt_on(g, y, kw, folds, feats):
    """`hbt` refitted at these parameters on every fold of one block."""
    got = {}
    for scope, fold, origin, idx, he in folds:
        gh, F = a47.frame_at(g, he, feats)
        lab = pd.Series((gh.is_test == 0).to_numpy(), index=gh.index) & y.reindex(gh.index).notna()
        tr = gh.index[lab.to_numpy() & (gh.index <= origin)]
        p = np.mean([lgb.LGBMRegressor(random_state=s, **kw)
                     .fit(F.loc[tr], y.loc[tr]).predict(F.loc[idx]) for s in SEEDS], 0)
        got[(scope, fold)] = pd.Series(np.clip(p, 5, 100), index=idx)
    return got


def run(arms, blocks, reconcile):
    OUT.mkdir(parents=True, exist_ok=True)
    g = fp.load_grid()
    y = g[fp.TARGET]
    c15 = a47.load_cache(a76.CACHE_15, a76.MANIFEST_15)
    c7 = a76.load_validated(a76.CACHE_7, a76.MANIFEST_7, '7-day forward')
    oof7 = a76.load_validated(a76.OOF7, a76.OOF7_MANIFEST, 'rebuilt 7-day OOF')
    feats, res = {}, {a: [] for a in arms}

    for name in blocks:
        t0 = time.time()
        O, V = a96.block_frames(g, y, name, c15, c7, oof7)
        folds = block_folds(g, y, c7, oof7, c15, name)
        idx = pd.DatetimeIndex(V.datetime)
        terms = None
        if reconcile:
            gh, F = a47.frame_at(g, V.horizon_end.iloc[0], feats)
            mask = a47.train_mask_before(g, gh, y, pd.Timestamp(V.origin.iloc[0]))
            inc = fp.fit_increments(F, y.reindex(gh.index), mask, a47.SEEDS_INC)
            terms = a47.increment_terms(F, idx, inc, None, 0.0)
        line = []
        for arm in arms:
            got = hbt_on(g, y, kw_for(arm), folds, feats)
            O2, V2 = O.copy(), V.copy()
            oi = pd.DatetimeIndex(O.dt if 'dt' in O else O.datetime)
            allo = pd.concat([s for (sc, f), s in got.items() if sc == 'inner'])
            O2['hbt'] = allo.reindex(oi).to_numpy()
            V2['hbt'] = got[('outer', -1)].reindex(idx).to_numpy()
            keep = np.isfinite(O2['hbt'].to_numpy())
            O2 = O2.loc[keep]
            O2, V2, _ = bias_arm.shifted(O2, V2, 'cat', fp.CATDB_SHRINK)
            level = a36.stack(O2, V2, MR, fp.BLEND_SHRINK)
            z = a47.solve(level, idx, terms) if reconcile else level
            res[arm].append((name, V.y.to_numpy(), z))
            line.append('%s %.5f' % (arm.split('_')[0], fp.rmse(res[arm][-1][1], z)))
        print('  %-12s [%4.0f s]  %s' % (name, time.time() - t0, '  '.join(line)), flush=True)

    def pooled(arm, sel):
        yy = np.concatenate([b for n, b, _ in res[arm] if n in sel])
        zz = np.concatenate([c for n, _, c in res[arm] if n in sel])
        return float(np.sqrt(np.mean((yy - zz) ** 2)))

    summary = {}
    print('\n%-20s %11s  per block' % ('arm', 'd_primary'))
    for arm in arms:
        per = {n: fp.rmse(b, c) - fp.rmse(b2, c2)
               for (n, b, c), (_n, b2, c2) in zip(res[arm], res['control'])}
        has7 = all(b in per for b in SEVEN)
        summary[arm] = dict(d_primary=pooled(arm, PRIMARY) - pooled('control', PRIMARY),
                            d_pooled7=(pooled(arm, SEVEN) - pooled('control', SEVEN)) if has7 else None,
                            worst_h=(max(per[b] for b in SEVEN)) if has7 else None,
                            d_b3=per.get('B3_shift7d'), per_block=per, kw=GRID[arm],
                            blocks_improved=int(sum(v < 0 for v in per.values())))
        s7 = summary[arm]
        print('%-30s %+11.6f  %s  %s  %s  %d/%d better'
              % (arm, s7['d_primary'],
                 ('d7 %+.6f' % s7['d_pooled7']) if has7 else '',
                 ('worstH %+.6f' % s7['worst_h']) if has7 else '',
                 {k[:2]: round(v, 5) for k, v in per.items()},
                 s7['blocks_improved'], len(per)))
    tag = 'hbt_grid_%s%s' % ('all' if len(blocks) > 3 else 'screen',
                             '' if reconcile else '_level')
    (OUT / (tag + '.json')).write_text(json.dumps(summary, indent=2, default=str))
    pd.to_pickle(res, OUT / ('preds_' + tag + '.pkl'))
    return summary


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--confirm', default=None, help='comma-separated arm ids to re-run')
    ap.add_argument('--blocks', default='b', choices=['b', 'all'])
    ap.add_argument('--level-only', action='store_true')
    ap.add_argument('--seeds', type=int, default=len(fp.SEEDS_OOF))
    a = ap.parse_args()
    SEEDS = tuple(range(a.seeds))
    ids = ['control'] + [x for x in (a.confirm.split(',') if a.confirm else [])
                         if x != 'control'] if a.confirm else list(GRID)
    run(ids, B_BLOCKS if a.blocks == 'b' else ALL_BLOCKS, not a.level_only)
