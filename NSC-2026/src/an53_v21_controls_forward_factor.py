"""Session 27, Tahap B: the three controls rebuilt on the repaired harness, one de-shrink
factor estimated forward instead of by interpolation, and the calibration diagnostics that
section 187's breakdown could not support.

**Why the controls are rebuilt rather than carried over.** Section 190 changed two things about
what a fold sees -- which meta rows it may fit on, and where its exogenous record stops. Both
apply identically to every configuration, but both move the numbers, so a session-27 candidate
compared against session 26's 5.514359 would be reading a harness difference as a mechanism
difference. Everything below is scored in `outputs/audit_v21_s27/`, against controls rebuilt
there.

**The one new variant.** `fp.fit_increments(deshrink=True)` estimates the dispersion factor
with `np.array_split` into three contiguous chunks and trains on both sides of the held-out one.
Nothing there touches an outer label, so it is not a leak; it is an interpolation, and the
quantity it produces is then used to widen a FORECAST. A model that can see both endpoints of
the gap it is predicting across shrinks less than one that cannot, so the interpolated factor is
plausibly too small -- or too large, if the two-sided fit is simply better. `forward_factor`
answers the question the reconciliation actually asks: train on the past only, purge both
endpoints of every training pair out of the validation window, and measure the shrinkage that a
genuinely forward increment model exhibits. Clip and strength stay at the shipped [1, 1.5] and
0.5; this varies the estimator, not the knob.

**What the diagnostics are for.** Section 187 reported bias by ACTUAL RH tercile and by cooling
phase. Selecting a group on the realised target guarantees a conditional-mean model looks
biased inside it, because the noise that put a row in the group is part of the residual, and
the cooling aggregate does not separate phase from hour of day. Neither is a rule anyone can
apply at inference. These are computed on inner calibration rows only, binned on quantities
available before the label: the prediction itself, and hour crossed with predicted phase.

    .venv/Scripts/python.exe src/an53_v21_controls_forward_factor.py
"""
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import lightgbm as lgb

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'src'))
import final_pipeline as fp
import an47_v21_forward_benchmark as a47

OUT = a47.OUT_S27
FWD_FOLDS = 3            # same count as DESHRINK_FOLDS, so only the direction differs
MIN_FWD_TRAIN = 800      # rows a forward split must have behind it to be worth fitting


def forward_factor(X, tgt, rows, h, seed=fp.INC_SEED, folds=FWD_FOLDS):
    """Dispersion factor from forward out-of-fold increment predictions.

    `rows` are the training rows in time order. The last `folds` contiguous chunks are held out
    one at a time; each is predicted by a model fitted only on rows whose LATER endpoint is at
    least h steps before the chunk starts, so neither endpoint of a training pair lies inside
    the window being predicted. The factor is sd(truth)/sd(prediction) over the union of the
    held-out chunks, clipped exactly as the shipped estimator is.

    Returns (factor, provenance). A split with too little history behind it is skipped and
    named; if none survive the factor is 1.0, which is the identity, and the caller logs the
    fallback rather than quietly widening nothing."""
    rows = pd.DatetimeIndex(rows).sort_values()
    chunks = np.array_split(np.arange(len(rows)), folds + 1)[1:]
    oof, used, skipped = pd.Series(np.nan, index=rows), 0, []
    for c in chunks:
        va = rows[c]
        cut = va.min() - pd.Timedelta(minutes=30 * h)
        trn = rows[rows < cut]
        if len(trn) < MIN_FWD_TRAIN:
            skipped.append(dict(start=str(va.min()), train_rows=len(trn)))
            continue
        m = lgb.LGBMRegressor(random_state=seed, **fp.INC_KW).fit(X.loc[trn], tgt.loc[trn])
        oof.loc[va] = m.predict(X.loc[va])
        used += len(va)
    ok = oof.notna()
    if not ok.any() or float(oof[ok].std()) <= 0:
        return 1.0, dict(h=h, factor=1.0, raw=None, oof_rows=0, splits_used=0,
                         fallback='no forward split had %d training rows' % MIN_FWD_TRAIN,
                         skipped=skipped)
    raw = float(tgt.loc[oof.index[ok]].std() / oof[ok].std())
    return float(np.clip(raw, *fp.DESHRINK_CLIP)), dict(
        h=h, factor=float(np.clip(raw, *fp.DESHRINK_CLIP)), raw=raw, oof_rows=int(ok.sum()),
        splits_used=len(chunks) - len(skipped), fallback='', skipped=skipped)


def make_forward_builder(log):
    """An `inc_builder` for `a47.score_config`: the shipped physics increments, with the
    de-shrink factor replaced by the forward estimate. Everything else -- horizons, weights,
    seeds, LightGBM settings -- is untouched."""
    def build(F, yh, mask, seeds):
        inc = fp.fit_increments(F, yh, mask, seeds, physics=True, deshrink=False)
        for h, _ in fp.INC_SPEC:
            X = fp.inc_design(F, h, inc['cols'], True)
            tgt = (yh - yh.shift(h)).reindex(X.index)
            m = mask.reindex(X.index, fill_value=False)
            m = m & tgt.notna() & m.shift(h, fill_value=False)
            rows = X.index[m]
            f, prov = forward_factor(X, tgt, rows, h)
            prov['train_end'] = str(rows.max())
            inc[('f', h)] = f
            log.append(prov)
        return inc
    return build


def interpolated_factors(g, y, cache, seeds):
    """The shipped factor at every origin, for the side-by-side table. Cheap: the increments
    are refitted anyway, and this reads the scalar off them."""
    rows, feats = [], {}
    for name, blk in cache.groupby('block', sort=False):
        for scope, fold in sorted(set(zip(blk.scope, blk.fold))):
            if scope != 'outer':
                continue                     # one refit per block, not per inner fold
            d = blk.loc[(blk.scope == scope) & (blk.fold == fold)]
            gh, F = a47.frame_at(g, d.horizon_end.iloc[0], feats)
            origin = pd.Timestamp(d.origin.iloc[0])
            mask = a47.train_mask_before(g, gh, y, origin)
            inc = fp.fit_increments(F, y.reindex(gh.index), mask, seeds, physics=True,
                                    deshrink=True)
            for h, _ in fp.INC_SPEC:
                rows.append(dict(block=name, scope=scope, fold=int(fold), origin=origin,
                                 h=h, interpolated=inc[('f', h)]))
    return pd.DataFrame(rows)


# ------------------------------------------------------------------------- diagnostics

def calibration_by_prediction_bin(P, nbins=10):
    """E[y - pred | pred_bin] on inner calibration rows.

    This is the version of section 187's tercile table that an inference rule could actually
    use. Binning on the ACTUAL target guarantees a slope: the noise that pushed a row into the
    top tercile is in its residual too, so even a perfectly calibrated conditional mean
    under-predicts there. Binning on the prediction has no such artefact."""
    d = P.loc[P.score].copy()
    out = []
    for b, blk in d.groupby('block'):
        q = pd.qcut(blk.recon, nbins, labels=False, duplicates='drop')
        for i, part in blk.groupby(q):
            out.append(dict(block=b, bin=int(i), n=len(part),
                            pred_lo=float(part.recon.min()), pred_hi=float(part.recon.max()),
                            mean_pred=float(part.recon.mean()), mean_y=float(part.y.mean()),
                            bias=float((part.y - part.recon).mean()),
                            rmse=fp.rmse(part.y, part.recon)))
    return pd.DataFrame(out)


def residual_phase_after_harmonics(P, F_by_block):
    """Cooling/warming bias with the diurnal harmonic removed first.

    Section 187 reported cooling -1.36 and warming +0.03 and stopped there. Split by hour, the
    00-05 cell reverses -- warming is the more under-predicted side overnight -- and two of the
    extreme cells hold 14 and 20 rows. Cooling is not independent of hour, so the aggregate is
    partly a restatement of the diurnal bias the harmonic correction already targets. Here the
    residual is regressed on sin/cos of hour first and the phase means are taken on what is
    left. A phase effect that survives is a candidate; one that does not is the hour bias
    wearing a different label."""
    rows = []
    for b, blk in P.loc[P.score].groupby('block'):
        F = F_by_block[b]
        idx = pd.DatetimeIndex(blk.datetime)
        dT = F['T'].reindex(idx).to_numpy() - F['T'].shift(4).reindex(idx).to_numpy()
        r = (blk.y - blk.recon).to_numpy()
        hour = idx.hour + idx.minute / 60.0
        t = 2 * np.pi * hour / 24.0
        A = np.column_stack([np.ones(len(t)), np.sin(t), np.cos(t), np.sin(2 * t), np.cos(2 * t)])
        ok = np.isfinite(dT) & np.isfinite(r)
        resid = r.copy()
        resid[ok] = r[ok] - A[ok] @ np.linalg.lstsq(A[ok], r[ok], rcond=None)[0]
        for name, sel in (('cooling', ok & (dT < -0.5)), ('warming', ok & (dT > 0.5)),
                          ('flat', ok & (np.abs(dT) <= 0.5))):
            if sel.sum() == 0:
                continue
            rows.append(dict(block=b, phase=name, n=int(sel.sum()),
                             raw_bias=float(r[sel].mean()),
                             bias_after_harmonics=float(resid[sel].mean()),
                             sd=float(resid[sel].std())))
        for lo, hi in ((0, 6), (6, 12), (12, 18), (18, 24)):
            hsel = ok & (idx.hour >= lo) & (idx.hour < hi)
            for name, ph in (('cooling', dT < -0.5), ('warming', dT > 0.5)):
                sel = hsel & ph
                if sel.sum() == 0:
                    continue
                rows.append(dict(block=b, phase='%s_%02d-%02d' % (name, lo, hi),
                                 n=int(sel.sum()), raw_bias=float(r[sel].mean()),
                                 bias_after_harmonics=float(resid[sel].mean()),
                                 sd=float(resid[sel].std())))
    return pd.DataFrame(rows)


def day_night_shares(P):
    """How much of the squared error is a per-day offset, stated with the slice named.

    Section 187's "87.6% day-level share at 00-05" is the share of the mean error computed
    INSIDE that six-hour slice, which is not the share of a constant 24-hour offset. Both are
    reported here with the window each is computed over, because the two support different
    conclusions and only one of them was ever measured."""
    rows = []
    for b, blk in P.loc[P.score].groupby('block'):
        idx = pd.DatetimeIndex(blk.datetime)
        e = (blk.recon - blk.y).to_numpy()
        day = idx.normalize()
        full = pd.Series(e).groupby(day.to_numpy()).transform('mean').to_numpy()
        rows.append(dict(block=b, slice='full_day', n=len(e), sse=float((e ** 2).sum()),
                         day_level_share=float((full ** 2).sum() / (e ** 2).sum())))
        for lo, hi in ((0, 6), (6, 12), (12, 18), (18, 24)):
            m = (idx.hour >= lo) & (idx.hour < hi)
            if m.sum() < 24:
                continue
            es, ds = e[m], day[m]
            within = pd.Series(es).groupby(ds.to_numpy()).transform('mean').to_numpy()
            outside = full[m]
            rows.append(dict(block=b, slice='%02d-%02d' % (lo, hi), n=int(m.sum()),
                             sse=float((es ** 2).sum()),
                             # the section-187 number: mean recomputed inside the slice
                             day_level_share=float((within ** 2).sum() / (es ** 2).sum()),
                             # what a constant 24-hour offset would actually explain here
                             full_day_offset_share=float((outside ** 2).sum() /
                                                         (es ** 2).sum())))
    return pd.DataFrame(rows)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    g = fp.load_grid()
    y = g[fp.TARGET]
    cache = a47.load_cache(a47.CACHE_S27, a47.MANIFEST_S27)
    seeds = a47.SEEDS_INC
    scopes = ('outer', 'inner')
    feats = {}

    log = []
    specs = [('v21_increment', dict(physics=False, deshrink=0.0)),
             ('v21_physics', dict(physics=True, deshrink=0.0)),
             ('v21_physics_deshrink_half', dict(physics=True, deshrink=fp.INC_DESHRINK)),
             ('v21_physics_forward_factor',
              dict(physics=True, deshrink=fp.INC_DESHRINK,
                   inc_builder=make_forward_builder(log)))]

    preds, rows, ref = {}, [], None
    base = cache.loc[cache.scope == 'outer'].assign(recon=lambda d: d.level)
    rows.append(a47.report(base, 'level_only'))
    for label, kw in specs:
        t = time.time()
        P = a47.score_config(g, y, cache, scopes=scopes, seeds=seeds, feature_cache=feats, **kw)
        preds[label] = P
        r = a47.report(P.loc[P.scope == 'outer'], label, ref)
        r['inner_rmse'] = (fp.rmse(P.loc[P.score & (P.scope == 'inner'), 'y'],
                                   P.loc[P.score & (P.scope == 'inner'), 'recon'])
                           if int((P.score & (P.scope == 'inner')).sum()) else np.nan)
        r['inner_n'] = int((P.score & (P.scope == 'inner')).sum())
        if ref is None:
            ref = r
        rows.append(r)
        print('  %-28s outer pooled %.5f  inner %.5f (n=%d)  (%.0f s)'
              % (label, r['pooled'], r['inner_rmse'], r['inner_n'], time.time() - t), flush=True)

    R = pd.DataFrame(rows)
    for label in ('v21_physics', 'v21_physics_deshrink_half', 'v21_physics_forward_factor'):
        bs = a47.bootstrap(preds['v21_increment'].loc[preds['v21_increment'].scope == 'outer'],
                           preds[label].loc[preds[label].scope == 'outer'])
        print('  bootstrap %-28s vs v21_increment: dMSE %+.4f [%+.4f, %+.4f] over %d blocks'
              % (label, bs['mean'], bs['lo'], bs['hi'], bs['blocks']))
        for k, v in (('boot_dmse', bs['mean']), ('boot_lo', bs['lo']), ('boot_hi', bs['hi']),
                     ('boot_p_worse', bs['p_worse'])):
            R.loc[R.candidate == label, k] = v
    # The half-de-shrink control is the local incumbent, so the forward factor is also judged
    # against it directly rather than only against v21_increment.
    bs = a47.bootstrap(
        preds['v21_physics_deshrink_half'].loc[preds['v21_physics_deshrink_half'].scope == 'outer'],
        preds['v21_physics_forward_factor'].loc[preds['v21_physics_forward_factor'].scope == 'outer'])
    print('  bootstrap forward_factor vs deshrink_half: dMSE %+.4f [%+.4f, %+.4f]'
          % (bs['mean'], bs['lo'], bs['hi']))

    R.to_csv(OUT / 'controls.csv', index=False)
    print('\n' + R.to_string(index=False))

    fac = pd.DataFrame(log).drop_duplicates(subset=['h', 'train_end'])
    inter = interpolated_factors(g, y, cache, seeds)
    fac.to_csv(OUT / 'factor_forward.csv', index=False)
    inter.to_csv(OUT / 'factor_interpolated.csv', index=False)
    print('\nforward factors, one row per origin per horizon\n'
          + fac.drop(columns=['skipped']).to_string(index=False))
    print('\ninterpolated factors, by horizon\n' +
          inter.groupby('h').interpolated.describe()[['count', 'mean', 'min', 'max']]
          .to_string())

    P = preds['v21_physics_deshrink_half']
    F_by_block = {b: a47.frame_at(g, d.loc[d.scope == 'outer'].horizon_end.iloc[0], feats)[1]
                  for b, d in P.groupby('block')}
    inner = P.loc[P.scope == 'inner']
    outer = P.loc[P.scope == 'outer']
    cb = calibration_by_prediction_bin(inner)
    ph = residual_phase_after_harmonics(inner, F_by_block)
    dn = day_night_shares(outer)
    cb.to_csv(OUT / 'calibration_bins.csv', index=False)
    ph.to_csv(OUT / 'phase_after_harmonics.csv', index=False)
    dn.to_csv(OUT / 'day_night_shares.csv', index=False)
    print('\ncalibration by prediction bin, inner rows\n' + cb.to_string(index=False))
    print('\nphase bias after removing the diurnal harmonics, inner rows\n'
          + ph.to_string(index=False))
    print('\nday-level share by slice, outer rows\n' + dn.to_string(index=False))

    (OUT / 'controls_and_factor.json').write_text(json.dumps(dict(
        controls=json.loads(R.to_json(orient='records')),
        forward_factor=json.loads(fac.to_json(orient='records')),
        interpolated_factor={str(h): dict(mean=float(d.interpolated.mean()),
                                          min=float(d.interpolated.min()),
                                          max=float(d.interpolated.max()))
                             for h, d in inter.groupby('h')},
        forward_vs_half=bs), indent=2, default=str))
    for label, P in preds.items():
        P.to_pickle(OUT / ('preds_%s.pkl' % label))
    print('\nwrote controls.csv, factor_*.csv, the diagnostics and per-row predictions to %s'
          % OUT)


if __name__ == '__main__':
    main()
