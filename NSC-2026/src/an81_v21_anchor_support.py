"""Session 35, Task 2: falsify the analog hypothesis on inner windows before spending an outer run.

The hypothesis is that two moments whose temperature, ventilation and pressure dynamics look alike
carry similar vapour pressure, so a historical episode's RH can be transported to a query through
`es(T_anchor)/es(T_query)`. It is a hypothesis, and `exp07`'s KNN25 at 8.257970 says analogs on
this data are not free. So the cheap, decisive test runs first, entirely inside the training
prefix, and the outer benchmark is not run unless it passes.

**Three gates, frozen before the run** (section 7 of the plan):

1. coverage >= 30% and at least 96 SUPPORTED queries per window -- a condition for the test to
   have any power, not an effect estimate;
2. transport beats the raw-RH analog in pooled MSE and does not lose on both windows -- the
   control that isolates the transport from the neighbour search;
3. the anchor term, put through the solver, lowers pooled MSE against C0, and the gain does not
   come from a single day.

**Everything is inside the prefix.** For each window the frame stops at that window's own
endpoint, anchors are labelled rows at or before its origin, and the distance threshold is the q90
of distance-to-fifth-neighbour measured on a SEPARATE calibration stretch that ends at the origin.
No outer label, and no label from the window itself, sets any parameter.

Failure is a real outcome and is written as `reject_analog_hypothesis`. It does not license
retuning the metric, k, the strength or the sensor subset in the same round.

    .venv/Scripts/python.exe src/an81_v21_anchor_support.py
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
import v21_episode_anchors as ea

OUT = ROOT / 'outputs' / 'audit_v21_s35'
PRIMARY = ('B1_last15d', 'B2_prev15d')
CAL_DAYS = 7                 # calibration stretch used only to set the distance threshold
MIN_SUPPORTED = 96
MIN_COVERAGE = 0.30
SEEDS_INC = a47.SEEDS_INC


def pick_windows(cache, block, n=2):
    """The two most recent non-overlapping inner folds of a block, newest first.

    The inner harness builds 8-day windows at a 2-day step, so consecutive folds overlap by six
    days. Walking back and keeping a fold only when its window clears the previously kept one
    gives two genuinely disjoint stretches; taking adjacent folds would count the same six days
    twice, which is the mistake section 176 made with B3.
    """
    inner = cache.loc[(cache.block == block) & (cache.scope == 'inner')]
    spans = (inner.groupby('fold')
             .agg(origin=('origin', 'first'), horizon_end=('horizon_end', 'first'), n=('y', 'size'))
             .sort_values('horizon_end', ascending=False))
    kept = []
    for fold, r in spans.iterrows():
        if any(pd.Timestamp(r.horizon_end) > pd.Timestamp(k['origin']) for k in kept):
            continue
        kept.append(dict(fold=int(fold), origin=pd.Timestamp(r.origin),
                         horizon_end=pd.Timestamp(r.horizon_end), n=int(r.n)))
        if len(kept) == n:
            break
    return kept


def labelled(g, y, end):
    gh = g.loc[g.index <= pd.Timestamp(end)]
    lab = pd.Series((gh.is_test == 0).to_numpy(), index=gh.index) & y.reindex(gh.index).notna()
    return gh.index[lab.to_numpy()]


def window_threshold(g, y, F, origin, scaler, grid_start):
    """q90 of distance-to-fifth-neighbour on a calibration stretch ending at the origin.

    The calibration queries are the last `CAL_DAYS` of labelled rows before the origin and their
    anchors stop before that stretch begins, so nothing the window is scored on has touched the
    threshold.
    """
    origin = pd.Timestamp(origin)
    cal_start = origin - pd.Timedelta(days=CAL_DAYS)
    idx = labelled(g, y, origin)
    cal_q = idx[(idx > cal_start) & (idx <= origin)]
    cal_a = idx[idx <= cal_start]
    if len(cal_q) < 48 or len(cal_a) < 240:
        return None, dict(cal_queries=len(cal_q), cal_anchors=len(cal_a))
    S, _ = ea.build_anchor_table(F, y, cal_q, cal_a, scaler, grid_start, threshold=None)
    thr = ea.choose_threshold(S.distance5)
    return thr, dict(cal_queries=len(cal_q), cal_anchors=len(cal_a))


def run_window(g, y, cache, block, w, grid_start):
    """One inner window: anchors, both analog arms, and the solved comparison against C0."""
    origin, he = w['origin'], w['horizon_end']
    gh, F = a47.frame_at(g, he)
    idx_all = labelled(g, y, he)
    anchors = idx_all[idx_all <= origin]
    rows = cache.loc[(cache.block == block) & (cache.scope == 'inner') &
                     (cache.fold == w['fold'])].sort_values('datetime')
    queries = pd.DatetimeIndex(rows.datetime)
    scaler = ea.DescriptorScaler().fit(F, anchors)
    thr, cal = window_threshold(g, y, F, origin, scaler, grid_start)
    if thr is None:
        # Session 36. Passing `threshold=None` through means NO threshold, i.e. every query is
        # supported however far its analogs are -- the opposite of what a failed calibration
        # should produce. A window that cannot be calibrated abstains entirely.
        S, D = ea.abstain_all(queries, 'no_threshold')
    else:
        S, D = ea.build_anchor_table(F, y, queries, anchors, scaler, grid_start, threshold=thr)

    cov = ea.coverage(S)
    yv = rows.y.to_numpy(float)
    level = rows.level.to_numpy(float)
    sup = (S.reason == 'ok').to_numpy()

    # C0 for this window: the shipped increments at this fold's own origin and frame.
    mask = a47.train_mask_before(g, gh, y, origin)
    inc = fp.fit_increments(F, y.reindex(gh.index), mask, SEEDS_INC,
                            physics=False, deshrink=False)
    terms = a47.increment_terms(F, queries, inc, None, 0.0)
    z0 = ea.solve_with_anchors(level, queries, terms)
    ref = a47.solve(level, queries, terms)
    assert np.max(np.abs(z0 - ref)) < 1e-12, 'the anchor solver must reproduce a47.solve at a=0'

    # `cov` carries its own `n`; drop it rather than let it silently shadow the query count.
    cov_fields = {k: v for k, v in cov.items() if k != 'n'}
    out = dict(block=block, fold=w['fold'], origin=str(origin), horizon_end=str(he),
               n=len(queries), n_anchors=len(anchors), threshold=thr, **cal, **cov_fields)
    if sup.sum() == 0:
        out.update(status='no_support')
        return out, S.assign(block=block, fold=w['fold']), D, None

    a = S.a.to_numpy(float)
    for tag, col in (('transport', 'q_transport'), ('raw', 'q_raw')):
        q = S[col].to_numpy(float)
        out['mse_q_' + tag] = float(np.mean((q[sup] - yv[sup]) ** 2))
        z = ea.solve_with_anchors(level, queries, terms, a, q)
        out['mse_z_' + tag] = float(np.mean((z[sup] - yv[sup]) ** 2))
        out['rmse_z_' + tag] = float(np.sqrt(np.mean((z - yv) ** 2)))
        S['z_' + tag] = z
    out['mse_z_c0'] = float(np.mean((z0[sup] - yv[sup]) ** 2))
    out['rmse_z_c0'] = float(np.sqrt(np.mean((z0 - yv) ** 2)))
    out['d_mse_transport'] = out['mse_z_transport'] - out['mse_z_c0']
    out['d_mse_raw'] = out['mse_z_raw'] - out['mse_z_c0']
    out['q_transport_beats_raw'] = bool(out['mse_q_transport'] < out['mse_q_raw'])
    # Session 36. `build_anchor_table` records detail rows for queries that later abstain, so
    # counting over all of `D` describes pairs the solver never used. Both are kept, and the
    # supported count is the one that means anything.
    sup_ts = set(S.datetime[sup])
    Ds = D.loc[D.datetime.isin(sup_ts)] if len(D) else D
    out['pairs_all'] = int(len(D))
    out['pairs_supported'] = int(len(Ds))
    out['out_of_range_q_all'] = int(((D.q_ij < 5) | (D.q_ij > 100)).sum()) if len(D) else 0
    out['out_of_range_q'] = int(((Ds.q_ij < 5) | (Ds.q_ij > 100)).sum()) if len(Ds) else 0
    out['status'] = 'scored'
    S = S.assign(block=block, fold=w['fold'], y=yv, level=level, z_c0=z0, supported=sup)
    return out, S, D.assign(block=block, fold=w['fold']), None


def near_far_table(S):
    """Does a closer analog actually predict better? Diagnosis, and it gates nothing."""
    d = S.loc[S.supported].copy()
    if len(d) < 8:
        return pd.DataFrame()
    d['bucket'] = pd.qcut(d.distance5, min(4, d.distance5.nunique()), duplicates='drop')
    out = []
    for b, gd in d.groupby('bucket', observed=True):
        out.append(dict(bucket=str(b), n=len(gd), mean_distance5=float(gd.distance5.mean()),
                        mse_q_transport=float(np.mean((gd.q_transport - gd.y) ** 2)),
                        mse_q_raw=float(np.mean((gd.q_raw - gd.y) ** 2)),
                        mse_z_c0=float(np.mean((gd.z_c0 - gd.y) ** 2)),
                        mse_z_transport=float(np.mean((gd.z_transport - gd.y) ** 2))))
    return pd.DataFrame(out)


def pooled_delta(S, col, supported_only=True):
    """Pooled ΔMSE against C0 over the whole population, not a weighted mean of per-window means."""
    d = S.loc[S.supported] if supported_only else S
    if not len(d):
        return float('nan')
    return float(((d[col] - d.y) ** 2).mean() - ((d.z_c0 - d.y) ** 2).mean())


def best_day_guard(S, col='z_transport', supported_only=True):
    """The global guard: one day dropped once, over the pooled rows. See `ea.global_best_day_guard`."""
    d = S.loc[S.supported] if supported_only else S
    if not len(d):
        return dict(guard=float('nan'), dropped_day=None, n_kept=0, n_days=0)
    return ea.global_best_day_guard(d.y, d.z_c0, d[col], d.datetime)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--blocks', nargs='+', default=list(PRIMARY))
    ap.add_argument('--out', default=str(OUT))
    a = ap.parse_args()
    out_dir = Path(a.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    t0 = time.time()

    g = fp.load_grid()
    y = g[fp.TARGET]
    grid_start = g.index.min()
    cache = a47.load_cache(a47.CACHE_S27, a47.MANIFEST_S27)

    rows, summaries, details = [], [], []
    for block in a.blocks:
        wins = pick_windows(cache, block)
        print('\n%s: %d non-overlapping inner windows' % (block, len(wins)), flush=True)
        if len(wins) < 2:
            rows.append(dict(block=block, status='insufficient_windows', n=0))
            print('  insufficient evidence: fewer than two disjoint inner windows', flush=True)
            continue
        for w in wins:
            r, S, D, _ = run_window(g, y, cache, block, w, grid_start)
            rows.append(r)
            summaries.append(S)
            details.append(D)
            print('  fold %d  %s -> %s  n=%d  coverage %.3f (%d supported)'
                  % (w['fold'], w['origin'].date(), w['horizon_end'].date(), r['n'],
                     r['coverage'], r['supported']), flush=True)
            if r['status'] == 'scored':
                print('    q MSE transport %.4f vs raw %.4f | z MSE C0 %.4f -> transport %.4f '
                      '(%+.4f), raw %.4f (%+.4f)'
                      % (r['mse_q_transport'], r['mse_q_raw'], r['mse_z_c0'],
                         r['mse_z_transport'], r['d_mse_transport'],
                         r['mse_z_raw'], r['d_mse_raw']), flush=True)

    R = pd.DataFrame(rows)
    S = pd.concat(summaries, ignore_index=True) if summaries else pd.DataFrame()
    D = pd.concat(details, ignore_index=True) if details else pd.DataFrame()
    R.to_csv(out_dir / 'anchor_support.csv', index=False)
    if len(S):
        S.to_pickle(out_dir / 'anchor_inner_predictions.pkl')
        near_far_table(S).to_csv(out_dir / 'anchor_near_far.csv', index=False)
    if len(D):
        D.to_pickle(out_dir / 'anchor_detail.pkl')

    scored = R.loc[R.get('status', pd.Series(dtype=object)) == 'scored'] if len(R) else R
    # Session 36. A block that could not be evidenced is a block that did not pass. The previous
    # version filtered those rows out before deciding, so a single passing block could have
    # written `proceed_to_outer` while another had no evidence at all.
    mandatory = list(a.blocks)
    evidenced = {b for b in mandatory
                 if len(scored.loc[scored.block == b]) >= 2} if len(scored) else set()
    missing = [b for b in mandatory if b not in evidenced]
    gates, verdict, why = {}, 'reject_analog_hypothesis', ''
    if not len(scored) or len(scored) < 2:
        why = 'insufficient evidence: fewer than two scored inner windows'
        gates = dict(gate1_support=False, gate2_transport_beats_raw=False, gate3_solver=False,
                     gate0_all_blocks_evidenced=False, blocks_missing_evidence=missing)
    else:
        sup = S.loc[S.supported] if len(S) else S
        g0 = bool(not missing)
        g1 = bool((scored.coverage >= MIN_COVERAGE).all() and
                  (scored.supported >= MIN_SUPPORTED).all())
        loses_both = bool((~scored.q_transport_beats_raw).all())
        # Pooled over the rows themselves, not a weighted mean of per-window means.
        pooled_q_t = float(((sup.q_transport - sup.y) ** 2).mean())
        pooled_q_r = float(((sup.q_raw - sup.y) ** 2).mean())
        g2 = bool(pooled_q_t < pooled_q_r and not loses_both)
        pooled_d = pooled_delta(S, 'z_transport')
        guard = best_day_guard(S, 'z_transport')
        g3 = bool(pooled_d < 0 and guard['guard'] < 0)
        gates = dict(gate0_all_blocks_evidenced=g0, gate1_support=g1,
                     gate2_transport_beats_raw=g2, gate3_solver=g3,
                     blocks_missing_evidence=missing,
                     pooled_mse_q_transport=pooled_q_t, pooled_mse_q_raw=pooled_q_r,
                     pooled_d_mse_solver=pooled_d,
                     pooled_d_mse_solver_all_query=pooled_delta(S, 'z_transport', False),
                     d_mse_excluding_best_day=guard['guard'],
                     best_day_dropped=guard['dropped_day'],
                     control_raw_pooled_d_mse=pooled_delta(S, 'z_raw'),
                     control_raw_pooled_d_mse_all_query=pooled_delta(S, 'z_raw', False),
                     control_raw_guard=best_day_guard(S, 'z_raw')['guard'],
                     min_coverage=float(scored.coverage.min()),
                     min_supported=int(scored.supported.min()))
        names = ('gate0_all_blocks_evidenced', 'gate1_support', 'gate2_transport_beats_raw',
                 'gate3_solver')
        if all(gates[k] for k in names):
            verdict = 'proceed_to_outer'
            why = 'all gates pass on every mandatory block'
        else:
            why = 'failed %s' % ', '.join(k for k in names if not gates[k])
            if missing:
                why += ' (no evidence for %s)' % ', '.join(missing)

    c.write_json(out_dir / 'anchor_support.json', dict(
        created=pd.Timestamp.now().isoformat(timespec='seconds'),
        seconds=round(time.time() - t0, 1), verdict=verdict, reason=why, gates=gates,
        config=dict(groups={k: list(v) for k, v in ea.GROUPS.items()},
                    n_episodes=ea.N_EPISODES, strength=ea.ANCHOR_STRENGTH,
                    min_separation_hours=ea.MIN_SEPARATION / pd.Timedelta(hours=1),
                    threshold_quantile=ea.THRESHOLD_QUANTILE, cal_days=CAL_DAYS,
                    window_source='existing 8-day inner folds (an47), NOT the 7-day windows the plan described; recorded rather than varied silently',
                    min_coverage=MIN_COVERAGE, min_supported=MIN_SUPPORTED),
        inputs=a47.input_hashes(), code=a47.code_hashes(),
        helper_code={p: a47.md5(ROOT / p) for p in
                     ('src/v21_episode_anchors.py', 'src/an81_v21_anchor_support.py')},
        windows=rows))
    print('\n' + R.to_string(index=False))
    print('\ngates: %s' % gates)
    print('verdict: %s (%s)' % (verdict, why))
    print('wrote %s' % out_dir)


if __name__ == '__main__':
    main()
