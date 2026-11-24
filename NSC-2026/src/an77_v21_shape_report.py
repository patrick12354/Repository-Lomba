"""Session 33 Task 4, repaired in session 34: read `an76`'s predictions once and decide from them.

Every number here comes from `outputs/audit_v21_s33/preds_level_shape.pkl` and nothing else.
Section 181's lesson was that a table assembled from a file whose name resembled the right one
was larger than the effect it was reporting, so the arms are joined `one_to_one` on
(block, datetime) and a mismatch is an error rather than a silent reindex.

**Session-34 repairs.** The session-33 version of this file reported four numbers that described
populations other than the one the decision is made on. None of them changed the verdict -- every
correction makes the rejection larger -- but a report whose populations drift is not a report.

1. **Matched calendar re-admitted B3.** `a69.primary_index` was called correctly and then thrown
   away: the selection ran `k15.set_index('datetime').loc[matched_idx]` on a frame that still
   held B3, whose 7-day shift shares timestamps with both primary blocks, so asking for 1008
   timestamps returned **1680 rows**. This is section 223's bug in a new place. Selecting from
   the unique primary frame gives ΔRMSE +0.073714 (E1) and +0.051139 (E2), against the +0.046130
   and +0.033249 that were reported.
2. **Direction and solo `hbt` used B1+B2+B3 while pooled used B1+B2.** The quoted alignment
   therefore did not reconstruct the primary ΔMSE. On the primary population the identity holds
   exactly: alignment +0.489902 plus movement +0.050778 equals ΔMSE +0.540679 for E1.
3. **The quality slice re-paired blocks by groupby order.** Quality arrays were gathered per
   `horizon_end` and `np.concatenate`d onto a frame ordered by block. B2's horizon ends first, so
   the two blocks' quality columns were swapped: **1364 of 1440** values were attached to the
   wrong row. Values are now joined on (block, datetime).
4. **The best-day guard averaged daily means.** Days at the edge of a block carry as few as 18
   rows against a full day's 48, and weighting those equally is not the pooled statistic the rest
   of the report uses. Dropping the day by summed SSE gain and recomputing SSE/n gives +0.595980
   (E1) and +0.430731 (E2), not +0.657287 and +0.478712.

Also repaired: the E2 tie-break compared E2 against the control where the rule says E2 against
E1, and the bootstrap indexed by DataFrame label rather than by position.

**What is reported**

* pooled RMSE as `sqrt(sum SSE / sum n)` over B1+B2 only -- B3 is a 7-day shift that overlaps
  both and is a sensitivity, never 720 more rows of evidence;
* the matched calendar, selected from the unique primary frame;
* `delta_MSE = 2*mean((z0-y)*(z1-z0)) + mean((z1-z0)^2)` via `c.direction`, on the primary rows,
  which separates "the correction points the right way" from "the prediction moved a lot";
* the solver's own spectrum, using an71's operator, so a gain can be attributed to a band;
* a paired calendar bootstrap at 3 and 7 days, on the SAME resampled calendar for both arms.

Every table carries the `population` it was computed on and its `n`.

**What the bootstrap is not.** It is a spread conditional on a calendar that has been searched
over for many sessions. It is not the probability that an arm wins on the test set.

    .venv/Scripts/python.exe src/an77_v21_shape_report.py --out outputs/audit_v21_s34/repaired_s33
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import connected_components

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
import final_pipeline as fp
import an47_v21_forward_benchmark as a47
import an59_v21_candidate_contract as c
import an69_v21_sensor_ablation as a69
import v21_local_shape as ls

PREDS = ROOT / 'outputs' / 'audit_v21_s33' / 'preds_level_shape.pkl'
DEFAULT_OUT = ROOT / 'outputs' / 'audit_v21_s34' / 'repaired_s33'
PRIMARY = ('B1_last15d', 'B2_prev15d')
CONTROL = 'C0'
BOOT_SEED = 20260906
BOOT_N = 2000

# The bar, frozen before the session-33 run and unchanged by these repairs.
BAR = dict(pooled_gain=0.02, b3_tolerance=0.05, worst_h_tolerance=0.02, h1_tolerance=0.0,
           e2_over_e1=0.01)


def scored(P, arm):
    d = P.loc[(P.arm == arm) & P.score].copy()
    assert len(d), 'no scored rows for %s' % arm
    return d.sort_values(['block', 'datetime']).reset_index(drop=True)


def joined(P, arm):
    """Control and arm on identical scored timestamps, or an error."""
    a, b = scored(P, CONTROL), scored(P, arm)
    k = a.merge(b[['block', 'datetime', 'z_new', 'hbt_new', 'level_new']],
                on=['block', 'datetime'], suffixes=('', '_q'), how='outer',
                validate='one_to_one', indicator=True)
    assert k['_merge'].eq('both').all(), '%s and the control differ in scored rows' % arm
    return k.drop(columns='_merge').sort_values(['block', 'datetime']).reset_index(drop=True)


def primary_rows(k):
    """The one primary population every primary statistic in this file is computed on.

    `a69.primary_index` asserts the primary timestamps are unique before indexing, which is the
    check the session-33 matched calendar skipped. Returning the FRAME rather than just its index
    is the repair: callers cannot then go back to a frame that still contains B3. `datetime` is
    handed back as a column and the rows are ordered by it, so every downstream statistic sees
    one canonical ordering.
    """
    q = a69.primary_index(k.loc[k.family == '15d'].assign(score=True, recon=lambda d: d.z_new))
    out = q.reset_index().sort_values('datetime').reset_index(drop=True)
    assert not out.datetime.duplicated().any() and set(out.block) <= set(PRIMARY)
    return out


def pooled_rmse(d, base=True):
    col = 'z_new' if base else 'z_new_q'
    e = d[col].to_numpy() - d.y.to_numpy()
    return float(np.sqrt(np.mean(e ** 2)))


def bootstrap(d, days, n=BOOT_N, seed=BOOT_SEED):
    """Paired calendar-block bootstrap of the pooled MSE difference, same draw for both arms.

    Indexed by POSITION, after canonical sorting. The session-33 version collected
    `g.index.to_numpy()` from a groupby on a frame whose index was not guaranteed contiguous, then
    used those labels to index numpy arrays -- correct only by accident of the frame having been
    reset. Sorting here as well means the answer depends on the rows, not on the order they
    happened to arrive in.
    """
    d = d.sort_values(['block', 'datetime']).reset_index(drop=True)
    key = (d.block.astype(str) + '|' +
           (pd.DatetimeIndex(d.datetime).normalize().astype('int64') //
            (days * 86400 * 10 ** 9)).astype(str))
    groups = [np.flatnonzero((key == k_).to_numpy()) for k_ in key.unique()]
    a = (d.z_new.to_numpy() - d.y.to_numpy()) ** 2
    b = (d.z_new_q.to_numpy() - d.y.to_numpy()) ** 2
    rng = np.random.default_rng(seed)
    draws = np.empty(n)
    for i in range(n):
        pick = np.concatenate([groups[j] for j in rng.integers(0, len(groups), len(groups))])
        draws[i] = b[pick].mean() - a[pick].mean()
    return dict(blocks=len(groups), mean=float(draws.mean()),
                lo=float(np.quantile(draws, 0.025)), hi=float(np.quantile(draws, 0.975)),
                p_worse=float((draws > 0).mean()))


def daily(d):
    """Per-day summed SSE and row count, so the guard can pool instead of averaging means."""
    day = pd.DatetimeIndex(d.datetime).normalize()
    t = pd.DataFrame(dict(day=day,
                          sse_base=(d.z_new.to_numpy() - d.y.to_numpy()) ** 2,
                          sse_cand=(d.z_new_q.to_numpy() - d.y.to_numpy()) ** 2))
    out = t.groupby('day').agg(sse_base=('sse_base', 'sum'), sse_cand=('sse_cand', 'sum'),
                               n=('sse_base', 'size'))
    out['d_sse'] = out.sse_cand - out.sse_base
    out['d_mse'] = out.d_sse / out.n
    return out


def guard_excluding_best_day(d, day_table):
    """Drop the day contributing the largest SSE gain, then recompute ΔMSE as SSE/n."""
    best = day_table.d_sse.idxmin()
    day = pd.DatetimeIndex(d.datetime).normalize()
    keep = d.loc[np.asarray(day != best)]
    sse_b = float((((keep.z_new - keep.y) ** 2)).sum())
    sse_c = float((((keep.z_new_q - keep.y) ** 2)).sum())
    return (sse_c - sse_b) / len(keep), str(best.date()), len(keep)


def spectrum(k):
    """an71's operator: where in the solver's own spectrum the change lands."""
    out = []
    for block, d in k.loc[k.block.isin(PRIMARY)].groupby('block'):
        d = d.sort_values('datetime')
        idx = pd.DatetimeIndex(d.datetime)
        n = len(idx)
        L = np.zeros((n, n))
        for h, lam in fp.INC_SPEC:
            D, _ = fp.diff_operator(idx, h)
            if D is not None:
                L += lam * (D.T @ D).toarray()
        assert np.max(np.abs(L @ np.ones(n))) < 1e-10
        nc, _lab = connected_components(csr_matrix(L), directed=False)
        vals, vecs = np.linalg.eigh(L)
        bands = {'null': vals < 1e-9,
                 'low_0_to_0.085': (vals >= 1e-9) & (vals <= .085),
                 'mid_0.085_to_0.337': (vals > .085) & (vals <= .337),
                 'high_above_0.337': vals > .337}
        for tag, col in (('base', 'z_new'), ('cand', 'z_new_q')):
            e = d[col].to_numpy() - d.y.to_numpy()
            mass = (vecs.T @ e) ** 2
            assert np.isclose(mass.sum(), e @ e, atol=1e-7)
            for band, m in bands.items():
                out.append(dict(population='primary', block=block, arm=tag, band=band,
                                components=nc, n=n, modes=int(m.sum()),
                                sse=float(mass[m].sum())))
    return pd.DataFrame(out)


def lead_bands(k, population, blocks=None):
    """ΔMSE by forecast lead. Reported per block as well as pooled: section 4.5 of the session-34
    audit showed the pooled version hides that the loss is not monotone in lead on B2."""
    d = k if blocks is None else k.loc[k.block.isin(blocks)]
    lead = (pd.DatetimeIndex(d.datetime) - pd.DatetimeIndex(d.origin)).total_seconds() / 86400.0
    d = d.assign(lead_band=pd.cut(lead, [0, 3, 7, 11, 15],
                                  labels=['0-3d', '3-7d', '7-11d', '11-15d']))
    out = []
    for keys, gd in d.groupby(['block', 'lead_band'], observed=True):
        out.append(dict(population=population, block=keys[0], lead_band=str(keys[1]), n=len(gd),
                        base=fp.rmse(gd.y, gd.z_new), cand=fp.rmse(gd.y, gd.z_new_q),
                        d_mse=float(((gd.z_new_q - gd.y) ** 2 - (gd.z_new - gd.y) ** 2).mean())))
    for band, gd in d.groupby('lead_band', observed=True):
        out.append(dict(population=population, block='POOLED', lead_band=str(band), n=len(gd),
                        base=fp.rmse(gd.y, gd.z_new), cand=fp.rmse(gd.y, gd.z_new_q),
                        d_mse=float(((gd.z_new_q - gd.y) ** 2 - (gd.z_new - gd.y) ** 2).mean())))
    return pd.DataFrame(out)


def quality_slice(g_grid, d, shape_cache):
    """Does the change land where the sensors were reconstructed? Diagnosis only.

    Quality values are joined on (block, datetime). The session-33 version gathered them per
    `horizon_end` and concatenated onto a frame ordered by block, which swapped B1's and B2's
    columns wholesale.

    This is not allowed to gate anything: slicing an outcome by a variable chosen after seeing
    the outcome is how section 181's phantom gains were produced.
    """
    keys = d[['block', 'datetime', 'horizon_end']].copy()
    vals = []
    for he, gd in keys.groupby('horizon_end'):
        he = pd.Timestamp(he)
        if he not in shape_cache:
            shape_cache[he] = ls.build_local_shape(g_grid, he)
        S = shape_cache[he]
        vals.append(gd.assign(repaired=S.loc[pd.DatetimeIndex(gd.datetime),
                                             'quality_T_repaired_fraction_24h'].to_numpy()))
    q = pd.concat(vals)[['block', 'datetime', 'repaired']]
    m = d.merge(q, on=['block', 'datetime'], how='left', validate='one_to_one')
    assert m.repaired.notna().all(), 'a scored row got no quality value'
    m['bucket'] = pd.qcut(m.repaired, 4, duplicates='drop')
    out = []
    for b, gd in m.groupby('bucket', observed=True):
        out.append(dict(population='primary', bucket=str(b), n=len(gd),
                        mean_repaired=float(gd.repaired.mean()),
                        base=fp.rmse(gd.y, gd.z_new), cand=fp.rmse(gd.y, gd.z_new_q),
                        d_mse=float(((gd.z_new_q - gd.y) ** 2 - (gd.z_new - gd.y) ** 2).mean())))
    return pd.DataFrame(out)


def evaluate(P, arm, g_grid, shape_cache):
    k = joined(P, arm)
    prim = primary_rows(k)                      # B1+B2, unique timestamps -- THE population
    k7 = k.loc[k.family == '7d']
    per15 = {b: (fp.rmse(d.y, d.z_new), fp.rmse(d.y, d.z_new_q))
             for b, d in k.loc[k.family == '15d'].groupby('block')}
    per7 = {b: (fp.rmse(d.y, d.z_new), fp.rmse(d.y, d.z_new_q)) for b, d in k7.groupby('block')}

    want = pd.DatetimeIndex(k7.datetime).unique()
    m = prim.loc[prim.datetime.isin(want).to_numpy()]
    day = daily(prim)
    guard_val, best_day, guard_n = guard_excluding_best_day(prim, day)
    direction = c.direction(prim.y.to_numpy(), prim.z_new.to_numpy(), prim.z_new_q.to_numpy())

    res = dict(
        arm=arm, population='primary_B1_B2', n_primary=len(prim),
        pooled_base=pooled_rmse(prim, True), pooled_cand=pooled_rmse(prim, False),
        matched_n=len(m), matched_base=fp.rmse(m.y, m.z_new),
        matched_cand=fp.rmse(m.y, m.z_new_q),
        pooled7_base=fp.rmse(k7.y, k7.z_new), pooled7_cand=fp.rmse(k7.y, k7.z_new_q),
        n_pooled7=len(k7),
        rmse_hbt_base=fp.rmse(prim.y, prim.hbt_new), rmse_hbt_cand=fp.rmse(prim.y, prim.hbt_new_q),
        best_day=best_day, guard_n=guard_n, d_mse_excluding_best_day=guard_val,
        days=int(len(day)), days_improved=int((day.d_sse < 0).sum()),
        **{'d_' + b: v[1] - v[0] for b, v in {**per15, **per7}.items()},
        **{'direction_' + kk: v for kk, v in direction.items()})
    res['d_pooled'] = res['pooled_cand'] - res['pooled_base']
    res['d_mse_pooled'] = res['pooled_cand'] ** 2 - res['pooled_base'] ** 2
    res['d_matched'] = res['matched_cand'] - res['matched_base']
    res['d_pooled7'] = res['pooled7_cand'] - res['pooled7_base']
    # The direction identity must reconstruct the primary ΔMSE exactly. It did not in session 33
    # because the two used different populations; asserting it here means it cannot drift again.
    assert abs(res['direction_d_mse'] - res['d_mse_pooled']) < 1e-9, \
        'direction and pooled disagree: the populations have drifted apart again'
    for days in (3, 7):
        for kk, v in bootstrap(prim, days).items():
            res['boot%dd_%s' % (days, kk)] = v

    worst_h = max(res['d_' + b] for b in per7)
    res['worst_h'] = worst_h
    res['bar_pooled'] = bool(res['d_pooled'] <= -BAR['pooled_gain'])
    res['bar_primary_blocks'] = bool(all(res['d_' + b] < 0 for b in PRIMARY))
    res['bar_b3'] = bool(res.get('d_B3_shift7d', 0.0) <= BAR['b3_tolerance'])
    res['bar_matched'] = bool(res['d_matched'] <= 0)
    res['bar_pooled7'] = bool(res['d_pooled7'] <= 0)
    res['bar_worst_h'] = bool(worst_h <= BAR['worst_h_tolerance'])
    res['guard_h1'] = bool(res.get('d_H1_last7d', 0.0) <= BAR['h1_tolerance'])
    res['guard_best_day'] = bool(res['d_mse_excluding_best_day'] < 0)
    res['promotable'] = bool(res['bar_pooled'] and res['bar_primary_blocks'] and res['bar_b3']
                             and res['bar_matched'] and res['bar_pooled7']
                             and res['bar_worst_h'])
    res['strong'] = bool(res['promotable'] and res['guard_h1'] and res['guard_best_day']
                         and res['boot3d_hi'] < 0 and res['boot7d_hi'] < 0)
    return res, k, prim, day


def choose(rows):
    """The frozen decision rule. E1 is the default; E2 must beat E1, not merely beat the control.

    The session-33 expression was `e2['d_' + b] <= e1['d_' + b] or e2['d_' + b] < 0`, whose second
    clause lets E2 through on being better than the CONTROL on a block where it is worse than E1.
    The rule says E2 must not hurt E1 on B1/B2/H1, so the comparison is E2 against E1 throughout.
    """
    passing = [r for r in rows if r['promotable']]
    strong = [r for r in rows if r['strong']]
    if not passing:
        return 'keep_v21', None, ('no arm clears the engineering bar; the shape block does not '
                                  'replace the incumbent this round')
    e1 = next((r for r in passing if r['arm'] == 'E1'), None)
    e2 = next((r for r in passing if r['arm'] == 'E2'), None)
    if e1 is not None and e2 is not None:
        better = (e1['pooled_cand'] - e2['pooled_cand']) >= BAR['e2_over_e1']
        safe = all(e2['d_' + b] <= e1['d_' + b] for b in list(PRIMARY) + ['H1_last7d']
                   if ('d_' + b) in e2 and ('d_' + b) in e1)
        chosen = e2 if (better and safe) else e1
        why = ('E2 beats E1 by >= %.2f pooled without hurting E1 on B1/B2/H1' % BAR['e2_over_e1']
               if chosen is e2 else
               'E1 is the simpler arm and E2 does not buy its extra columns')
    else:
        chosen = passing[0]
        why = 'the only arm clearing the bar'
    verdict = 'candidate_for_production_check' if chosen in strong else 'weak_candidate'
    if chosen not in strong:
        why += ('; the bootstrap interval crosses zero or a stress guard disagrees, so it is not '
                'a strong recommendation')
    return verdict, chosen, why


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=str(DEFAULT_OUT),
                    help='output directory; the session-33 folder is never written to')
    ap.add_argument('--preds', default=str(PREDS))
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    P = pd.read_pickle(a.preds)
    arms = [x for x in P.arm.unique() if x != CONTROL]
    assert arms, 'nothing to report: only the control is present'
    g_grid = fp.load_grid()
    shape_cache = {}

    rows, days, specs, leads, quals = [], [], [], [], []
    for arm in arms:
        res, k, prim, day = evaluate(P, arm, g_grid, shape_cache)
        rows.append(res)
        days.append(day.assign(arm=arm, population='primary').reset_index())
        specs.append(spectrum(k).assign(candidate=arm))
        leads.append(pd.concat([lead_bands(prim, 'primary'),
                                lead_bands(k.loc[k.family == '7d'], 'holdout_7d')])
                     .assign(candidate=arm))
        quals.append(quality_slice(g_grid, prim, shape_cache).assign(candidate=arm))
        print('  %s  pooled %.6f -> %.6f (%+.6f)  matched n=%d %+.6f  7d %+.6f  worst H %+.6f'
              % (arm, res['pooled_base'], res['pooled_cand'], res['d_pooled'],
                 res['matched_n'], res['d_matched'], res['d_pooled7'], res['worst_h']),
              flush=True)

    R = pd.DataFrame(rows)
    R.to_csv(out / 'metrics.csv', index=False)
    pd.concat(days, ignore_index=True).to_csv(out / 'daily.csv', index=False)
    pd.concat(specs, ignore_index=True).to_csv(out / 'spectrum.csv', index=False)
    pd.concat(leads, ignore_index=True).to_csv(out / 'lead_bands.csv', index=False)
    pd.concat(quals, ignore_index=True).to_csv(out / 'quality_slice.csv', index=False)
    R[['arm', 'population', 'n_primary'] +
      [x for x in R.columns if x.startswith('direction_')]].to_csv(out / 'direction.csv',
                                                                   index=False)

    verdict, chosen, why = choose(rows)
    c.write_json(out / 'decision.json', dict(
        created=pd.Timestamp.now().isoformat(timespec='seconds'),
        verdict=verdict, chosen=None if chosen is None else chosen['arm'], reason=why,
        bar=BAR, control=CONTROL, populations=dict(primary='B1+B2 unique timestamps',
                                                   sensitivity_15d='B3', holdout_7d='H1+H2+H3'),
        arms=rows, source=str(Path(a.preds)), source_md5=a47.md5(a.preds),
        repairs=['matched calendar selected from the unique primary frame',
                 'direction and solo hbt on the primary population',
                 'quality values joined on (block, datetime)',
                 'best-day guard pooled as SSE/n',
                 'E2 tie-break compares against E1',
                 'bootstrap indexes by position']))
    print('\n' + R[['arm', 'pooled_base', 'pooled_cand', 'd_pooled', 'matched_n', 'd_matched',
                    'd_pooled7', 'worst_h', 'promotable', 'strong']].to_string(index=False))
    print('\nverdict: %s (%s)\n  %s' % (verdict, chosen and chosen['arm'], why))
    print('wrote %s' % out)


if __name__ == '__main__':
    main()
