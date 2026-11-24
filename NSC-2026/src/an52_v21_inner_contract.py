"""Session 27, Tahap A: what the session-26 inner calibration set actually contained, and what
the fixed contract leaves behind.

The audit that opened this session found one concrete defect in `an47.build_block`. The meta
rows an inner fold fitted its stack on were chosen by FOLD NUMBER:

    prior = O.loc[O.fold.isin(fids[:k])]

Inner folds are 8-day windows at a 2-day step, so fold k-1's window ends six days AFTER fold
k's origin. A smaller fold number does not mean earlier labels. On top of that the first scored
fold was scored on its whole 8-day window rather than its 2-day tail, so those six days were
not merely available to the stack -- they were also being scored.

This script trains nothing. It reads the frozen session-26 cache, reconstructs which meta rows
each origin was handed, and counts the overlap in timestamps. It then reports what the session-27
rule leaves: how many calibration rows and days survive per origin once meta rows are selected by
label timestamp, once folds whose producing model was fitted after the origin are excluded, and
once every fold is scored on its tail only.

The point of the count is the second half. The plan's own instruction is that the audit must not
become an excuse to relax the rule until the row count looks respectable, so the surviving
numbers are printed per origin, including the ones that fall below the frozen minimum and are
therefore dropped rather than shrunk into.

    .venv/Scripts/python.exe src/an52_v21_inner_contract.py
"""
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'src'))
import final_pipeline as fp
import an36_increment_production as a36
import an47_v21_forward_benchmark as a47

OUT = a47.OUT_S27
VAL_DAYS, STEP_DAYS = 8, 2


def inner_plan(g, y):
    """The inner fold windows each block would generate, without fitting anything. Same
    `a36.inner_origins` call `build_block` makes, over the same labelled pre-origin index."""
    plan = {}
    for name, hs, he in a47.blocks_of(g):
        gh = g.loc[g.index <= he]
        lab = pd.Series((gh.is_test == 0).values, index=gh.index) & y.reindex(gh.index).notna()
        pre = gh.index[lab.to_numpy()]
        pre = pre[pre <= hs]
        spans = {}
        for fi, (vs, ve) in enumerate(a36.inner_origins(pre)):
            v = pre[(pre > vs) & (pre <= ve)]
            if len(pre[pre <= vs]) < 300 or len(v) < 50:
                continue
            spans[fi] = (vs, ve, v)
        plan[name] = (hs, he, spans)
    return plan


def session26_overlap(plan):
    """Rows the session-26 rule scored that its own stack had already seen the label of.

    For scored fold k the prior was folds 0..k-1, whose label union runs to the end of fold
    k-1's window. Everything scored at or before that timestamp is a row whose label helped fit
    the parameters it is being scored under."""
    rows = []
    for name, (hs, he, spans) in plan.items():
        fids = sorted(spans)
        for k, fi in enumerate(fids):
            if k == 0:
                continue
            vs, ve, v = spans[fi]
            prior_end = max(spans[f][1] for f in fids[:k])
            prior = pd.DatetimeIndex([])
            for f in fids[:k]:
                prior = prior.append(spans[f][2])
            cut = vs if k == 1 else ve - pd.Timedelta(days=a47.SCORE_TAIL_DAYS)
            scored = v[v > cut]
            rows.append(dict(block=name, fold=int(fi), origin=vs, horizon_end=ve,
                             prior_label_end=prior_end,
                             prior_ends_days_after_origin=(prior_end - vs).days,
                             # The headline overlap: rows scored under parameters fitted from
                             # their own label.
                             scored=len(scored),
                             overlapping=int((scored <= prior_end).sum()),
                             # The quieter half. Even where the scored tail clears the prior
                             # label window, the stack applied to it was fitted with labels
                             # from after this origin, so the parameters are not forward.
                             meta_rows=len(prior),
                             meta_rows_after_origin=int((prior > vs).sum()),
                             whole_window_exception=bool(k == 1)))
    R = pd.DataFrame(rows)
    R['overlap_pct'] = 100.0 * R.overlapping / R.scored
    return R


def session27_contract(plan):
    """What each origin gets under the fixed rule, before any model is fitted.

    Meta rows are the union of the OTHER folds' windows restricted to labels at or before this
    origin, and restricted to folds whose own fit ended at or before this origin. Scoring is the
    2-day tail, always. A fold below the frozen minimum keeps the fallback stack and is not
    scored at all."""
    rows = []
    for name, (hs, he, spans) in plan.items():
        for fi in sorted(spans):
            vs, ve, v = spans[fi]
            prior = pd.DatetimeIndex([])
            for f, (vs2, ve2, v2) in spans.items():
                if f == fi or vs2 > vs:
                    continue
                prior = prior.append(v2[v2 <= vs])
            scored = v[v > ve - pd.Timedelta(days=a47.SCORE_TAIL_DAYS)]
            days = int(prior.normalize().nunique()) if len(prior) else 0
            enough = len(prior) >= a47.MIN_META_ROWS and days >= a47.MIN_META_DAYS
            rows.append(dict(block=name, fold=int(fi), origin=vs, horizon_end=ve,
                             meta_rows=len(prior), meta_days=days,
                             meta_label_end=prior.max() if len(prior) else pd.NaT,
                             fallback=not enough,
                             scored=len(scored) if enough else 0,
                             scored_days=int(scored.normalize().nunique()) if enough else 0,
                             overlapping=int((scored <= prior.max()).sum()) if len(prior) else 0,
                             fallback_reason=('' if enough else
                                              'meta_rows=%d<%d or meta_days=%d<%d'
                                              % (len(prior), a47.MIN_META_ROWS, days,
                                                 a47.MIN_META_DAYS))))
    return pd.DataFrame(rows)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    g = fp.load_grid()
    y = g[fp.TARGET]
    plan = inner_plan(g, y)

    old = session26_overlap(plan)
    print('--- session 26, meta rows chosen by fold number ---')
    print(old.to_string(index=False))
    per_block = old.groupby('block')[['scored', 'overlapping']].sum()
    per_block['pct'] = 100.0 * per_block.overlapping / per_block.scored
    print('\n' + per_block.to_string())
    print('total scored %d, overlapping %d (%.2f%%)'
          % (old.scored.sum(), old.overlapping.sum(),
             100.0 * old.overlapping.sum() / old.scored.sum()))
    print('meta rows fitted from labels after their own origin: %d of %d (%.2f%%), '
          'and every one of the %d origins has some'
          % (old.meta_rows_after_origin.sum(), old.meta_rows.sum(),
             100.0 * old.meta_rows_after_origin.sum() / old.meta_rows.sum(),
             int((old.meta_rows_after_origin > 0).sum())))

    new = session27_contract(plan)
    print('\n--- session 27, meta rows chosen by label timestamp, tail-only scoring ---')
    print(new.to_string(index=False))
    keep = new.loc[~new.fallback]
    print('\ncalibration rows %d over %d origins and %d days; %d origins fall back'
          % (keep.scored.sum(), len(keep), keep.scored_days.sum(), int(new.fallback.sum())))
    print('timestamp violations: %d' % int(new.overlapping.sum()))
    assert new.overlapping.sum() == 0, 'the fixed rule still overlaps its own meta labels'

    old.to_csv(OUT / 'inner_contract_session26.csv', index=False)
    new.to_csv(OUT / 'inner_contract_session27.csv', index=False)
    (OUT / 'inner_contract.json').write_text(json.dumps(dict(
        session26=dict(scored=int(old.scored.sum()), overlapping=int(old.overlapping.sum()),
                       pct=float(100.0 * old.overlapping.sum() / old.scored.sum()),
                       meta_rows=int(old.meta_rows.sum()),
                       meta_rows_after_origin=int(old.meta_rows_after_origin.sum()),
                       origins_with_future_meta=int((old.meta_rows_after_origin > 0).sum()),
                       per_block={b: dict(scored=int(r.scored), overlapping=int(r.overlapping),
                                          pct=float(r.pct))
                                  for b, r in per_block.iterrows()}),
        session27=dict(min_meta_rows=a47.MIN_META_ROWS, min_meta_days=a47.MIN_META_DAYS,
                       origins=int(len(new)), fallback_origins=int(new.fallback.sum()),
                       calibration_rows=int(keep.scored.sum()),
                       calibration_days=int(keep.scored_days.sum()),
                       overlapping=int(new.overlapping.sum()),
                       per_block={b: dict(rows=int(d.scored.sum()),
                                          origins=int((~d.fallback).sum()))
                                  for b, d in new.groupby('block')})), indent=2))
    print('\nwrote %s' % (OUT / 'inner_contract.json'))


if __name__ == '__main__':
    main()
