"""Session 28: three fixed arms, five seeds, paired final-path loss.

Arm 1 changes only the feature representation of the physics LightGBM; its factor
uses the same blocked-OOF estimator on that new representation. Arms 2/3 use an
identical fixed alpha=100, w=.25 Ridge/LGB vector and differ only in the factor.
No alpha/blend selection and no new outer-guided sweep. Outputs never overwrite s27.
"""
import sys
import time
from pathlib import Path
import numpy as np
import pandas as pd
import lightgbm as lgb

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
import final_pipeline as fp
import an47_v21_forward_benchmark as a47
import an56_v21_distributed_lag as a56
import an59_v21_candidate_contract as c

ALPHA, BLEND = 100., .25
MIN_FORWARD_TRAIN = 800
ARMS = ('lgb_lags', 'fixed_old', 'fixed_matched')


def extra_design(F, h):
    base = fp.inc_design(F, h, fp.INC_PHYS_COLS, True)
    X = base.copy()
    for name, column in a56.lag_design(F).items():
        if name in X or any(column.equals(X[k]) for k in X.columns):
            continue
        X[name] = column
    return X


def fit_extra(F, y, mask, seeds):
    result = {'extra': {}, 'extra_factor': {}, 'extra_columns': {}}
    for h, _ in fp.INC_SPEC:
        X = extra_design(F, h)
        target = y - y.shift(h)
        m = mask & mask.shift(h, fill_value=False) & target.notna()
        rows = X.index[m]
        result['extra'][h] = [lgb.LGBMRegressor(random_state=s, **fp.INC_KW).fit(
            X.loc[rows], target.loc[rows]) for s in seeds]
        oof = pd.Series(np.nan, index=rows)
        for cut in np.array_split(np.arange(len(rows)), fp.DESHRINK_FOLDS):
            va = rows[cut]; tr = rows.difference(va)
            model = lgb.LGBMRegressor(random_state=fp.INC_SEED, **fp.INC_KW).fit(
                X.loc[tr], target.loc[tr])
            oof.loc[va] = model.predict(X.loc[va])
        result['extra_factor'][h] = float(np.clip(target.loc[rows].std()/oof.std(),
                                                  *fp.DESHRINK_CLIP))
        result['extra_columns'][h] = list(X.columns)
    return result


def fixed_bundle(F, y, mask, incumbent):
    X, T = a56.lag_design(F), a56.lag_targets(y)
    m = a56.lag_mask(mask, F.index) & T.notna().all(axis=1)
    rows = F.index[m]
    ridge = a56.fit_lag_model(X, T, rows, ALPHA)
    return dict(incumbent=incumbent, ridge=ridge, ridge_rows=rows)


def bundle_terms(F, idx, bundle, arm, blend=BLEND):
    """Return exact inference terms plus raw/adjusted increment vectors for diagnostics."""
    inc = bundle['incumbent']
    terms, vectors = [], []
    ridge = bundle['ridge'].predict(a56.lag_design(F).loc[idx]) if arm != 'lgb_lags' and blend else None
    lookup = pd.Series(np.arange(len(idx)), index=idx)
    for j, (h, lam) in enumerate(fp.INC_SPEC):
        D, stamps = fp.diff_operator(idx, h)
        if D is None:
            continue
        if arm == 'lgb_lags':
            X = extra_design(F, h)[bundle['extra_columns'][h]].loc[stamps]
            t = np.mean([m.predict(X) for m in bundle['extra'][h]], axis=0)
            factor = bundle['extra_factor'][h]
        else:
            X = fp.inc_design(F, h, inc['cols'], True).loc[stamps]
            t = np.mean([m.predict(X) for m in inc[h]], axis=0)
            if blend:
                t = (1-blend)*t + blend*ridge[lookup.loc[stamps].to_numpy(), j]
            factor = bundle['matched_factor'][h] if arm == 'fixed_matched' else inc[('f', h)]
        adjusted = t.mean() + (t-t.mean())*(1+fp.INC_DESHRINK*(factor-1))
        terms.append((D, adjusted, lam))
        vectors.append(pd.DataFrame(dict(datetime=stamps, h=h, raw=t,
                                          adjusted=adjusted, factor=factor)))
    return terms, pd.concat(vectors, ignore_index=True)


def matched_forward_factor(g, origin, seeds, min_train=MIN_FORWARD_TRAIN):
    """Estimate the fixed blend's factor from five-seed forward predictions.

    Every fold rebuilds features through its own validation horizon. Both targets'
    train endpoints precede the fold origin. Factor labels never reach the outer holdout.
    The same rows partition both horizons so covariance/dispersion diagnostics are paired.
    """
    gp = g.loc[g.index <= origin]
    yp = gp[fp.TARGET]
    mp = yp.notna() & gp.is_test.eq(0)
    rows = gp.index[a56.lag_mask(mp, gp.index) & a56.lag_targets(yp).notna().all(axis=1)]
    records, predictions = [], []
    for fi, cut in enumerate(np.array_split(np.arange(len(rows)), 4)[1:]):
        va = rows[cut]
        fold_origin = va.min() - pd.Timedelta(hours=2, minutes=30)
        train = rows[rows <= fold_origin]
        if len(train) < min_train:
            records.append(dict(fold=fi, origin=str(fold_origin), horizon_end=str(va.max()),
                                n_train=len(train), skipped=True, reason='insufficient forward history'))
            continue
        gh, F = a47.frame_at(gp, va.max())
        yh = gh[fp.TARGET]
        mask = yh.notna() & gh.is_test.eq(0) & (gh.index <= fold_origin)
        X, T = a56.lag_design(F), a56.lag_targets(yh)
        tr = F.index[a56.lag_mask(mask, F.index) & T.notna().all(axis=1)]
        ridge = a56.fit_lag_model(X, T, tr, ALPHA)
        pr = ridge.predict(X.loc[va])
        cfg = dict(seeds=list(seeds), alpha=ALPHA, blend=BLEND, factor='forward_fixed_mixture')
        rec = c.training_record(tr, fold_origin, va.max(), cfg)
        rec.update(fold=fi, skipped=False, prediction_timestamps=va.astype(str).tolist())
        records.append(rec)
        for j, (h, _) in enumerate(fp.INC_SPEC):
            design = fp.inc_design(F, h, fp.INC_PHYS_COLS, True)
            # Use the incumbent's individual-horizon mask, exactly as its final fit.
            mh = mask & mask.shift(h, fill_value=False) & T[h].notna()
            models = [lgb.LGBMRegressor(random_state=s, **fp.INC_KW).fit(
                design.loc[mh], T[h].loc[mh]) for s in seeds]
            pl = np.mean([m.predict(design.loc[va]) for m in models], axis=0)
            mix = (1-BLEND)*pl + BLEND*pr[:, j]
            predictions.append(pd.DataFrame(dict(fold=fi, datetime=va, h=h,
                truth=T[h].loc[va].to_numpy(), prediction=mix, lgb=pl, ridge=pr[:, j])))
    P = pd.concat(predictions, ignore_index=True) if predictions else pd.DataFrame()
    factors = {}
    for h, _ in fp.INC_SPEC:
        d = P.loc[P.h == h] if len(P) else P
        std = float(d.prediction.std()) if len(d) > 1 else 0.
        factors[h] = float(np.clip(d.truth.std()/std, *fp.DESHRINK_CLIP)) if std > 0 else 1.
    return factors, records, P


def main():
    c.OUT.mkdir(parents=True, exist_ok=True)
    g = fp.load_grid()
    cache = a47.load_cache(a47.CACHE_S27, a47.MANIFEST_S27)
    seeds = a47.SEEDS_INC
    cfg = dict(seeds=list(seeds), alpha=ALPHA, blend=BLEND, strength=fp.INC_DESHRINK,
               clip=list(fp.DESHRINK_CLIP), inc_spec=list(fp.INC_SPEC),
               arms=ARMS, selection='fixed designs; no outer or inner alpha/blend search')
    hashes = {str(p.relative_to(ROOT)): a47.md5(p) for p in
              [Path(__file__), ROOT/'src/an59_v21_candidate_contract.py',
               ROOT/'src/an56_v21_distributed_lag.py', ROOT/'final_pipeline.py']}
    c.write_json(c.OUT/'lag_factor_manifest.json', dict(config=cfg, code=hashes,
        inputs=a47.input_hashes(), level_cache_md5=a47.md5(a47.CACHE_S27), state='running'))
    preds = {arm: [] for arm in ('control',)+ARMS}
    provenance, vector_rows, factor_rows, oof_rows = [], [], [], []
    frozen = pd.read_pickle(a47.OUT_S27/'preds_v21_physics_deshrink_half.pkl')
    frozen = frozen.loc[frozen.scope == 'outer']
    for name, d in cache.loc[cache.scope == 'outer'].groupby('block', sort=False):
        start = time.time()
        d = d.sort_values('datetime'); idx = pd.DatetimeIndex(d.datetime)
        origin, end = pd.Timestamp(d.origin.iloc[0]), pd.Timestamp(d.horizon_end.iloc[0])
        gh, F = a47.frame_at(g, end)
        y = gh[fp.TARGET]
        mask = a47.train_mask_before(g, gh, y, origin)
        print(name, 'fit control + lag designs', flush=True)
        inc = fp.fit_increments(F, y, mask, seeds, physics=True, deshrink=True)
        base_terms = a47.increment_terms(F, idx, inc, deshrink=fp.INC_DESHRINK)
        base = d.assign(recon=a47.solve(d.level.to_numpy(), idx, base_terms))
        compare = c.join_predictions(frozen.loc[frozen.block==name], base)
        np.testing.assert_allclose(compare.recon, compare.recon_q, atol=1e-9, rtol=0)
        preds['control'].append(base)
        bundle = fixed_bundle(F, y, mask, inc)
        bundle.update(fit_extra(F, y, mask, seeds))
        print(name, 'fit five-seed forward mixture factors', flush=True)
        factors, recs, oof = matched_forward_factor(g, origin, seeds)
        bundle['matched_factor'] = factors
        provenance.append(dict(block=name, outer=c.training_record(F.index[mask], origin, end, cfg),
                               factor_splits=recs, extra_columns=bundle['extra_columns']))
        if len(oof):
            oof_rows.append(oof.assign(block=name))
        for h, _ in fp.INC_SPEC:
            factor_rows.append(dict(block=name, h=h, old=inc[('f', h)],
                                    extra=bundle['extra_factor'][h], matched=factors[h]))
        for arm in ARMS:
            terms, vectors = bundle_terms(F, idx, bundle, arm)
            p = d.assign(recon=a47.solve(d.level.to_numpy(), idx, terms))
            preds[arm].append(p)
            vectors['truth'] = [float(y.loc[t]-y.loc[t-pd.Timedelta(minutes=30*int(h))])
                                for t, h in zip(vectors.datetime, vectors.h)]
            vector_rows.append(vectors.assign(block=name, candidate=arm))
            print(' ', arm, 'RMSE', round(fp.rmse(p.y, p.recon), 6), flush=True)
        for arm, parts in preds.items():
            pd.concat(parts, ignore_index=True).to_pickle(c.OUT/('preds_'+arm+'.pkl'))
        pd.DataFrame(factor_rows).to_csv(c.OUT/'lag_factor_factors.csv', index=False)
        pd.concat(vector_rows).to_csv(c.OUT/'lag_factor_vectors.csv', index=False)
        if oof_rows:
            pd.concat(oof_rows).to_csv(c.OUT/'lag_factor_oof.csv', index=False)
        c.write_json(c.OUT/'lag_factor_provenance.json', provenance)
        print(name, 'completed seconds', round(time.time()-start, 1), flush=True)
    results = {k: pd.concat(v, ignore_index=True) for k, v in preds.items()}
    reference = a47.report(results['control'], 'control')
    reports = [reference]; boots, diagnostics = {}, []
    public = pd.read_pickle(a47.OUT_S27/'preds_v21_increment.pkl')
    public = public.loc[public.scope=='outer']
    rp = a47.report(public, 'v21_public_configuration')
    for arm in ARMS:
        report = a47.report(results[arm], arm, reference)
        report['delta_vs_v21'] = report['pooled'] - rp['pooled']
        reports.append(report)
        boots[arm] = a47.bootstrap_pair(results['control'], results[arm])
        joined = c.join_predictions(results['control'], results[arm])
        for name, d in joined.groupby('block'):
            diagnostics.append(dict(candidate=arm, block=name, **c.direction(d.y, d.recon, d.recon_q)))
    pd.DataFrame(reports).to_csv(c.OUT/'lag_factor_scores.csv', index=False)
    pd.DataFrame(diagnostics).to_csv(c.OUT/'lag_factor_direction.csv', index=False)
    c.write_json(c.OUT/'lag_factor_bootstrap.json', boots)
    c.write_json(c.OUT/'lag_factor_manifest.json', dict(config=cfg, code=hashes,
        inputs=a47.input_hashes(), level_cache_md5=a47.md5(a47.CACHE_S27), state='complete',
        outputs={p.name:a47.md5(p) for p in c.OUT.glob('lag_factor_*.csv')}))
    print(pd.DataFrame(reports).to_string(index=False), flush=True)


if __name__ == '__main__':
    main()
