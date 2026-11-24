"""Read-only model audit: cached predictions, chronological meta fitting, no submission.

Run from repo root: .venv/Scripts/python.exe src/an30_v20_audit.py
The strict cache audit is a diagnostic, not a new untouched model-selection holdout.
"""
import json
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import nnls, minimize

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import final_pipeline as fp

OUT = ROOT / 'outputs' / 'audit_v20'
OUT.mkdir(exist_ok=True)


def fit_weights(d, models, lam, simplex=False):
    x, y = d[models].to_numpy(), d.y.to_numpy()
    w, _ = nnls(x, y)
    raw_sum = w.sum()
    w = w / raw_sum if raw_sum else np.ones(len(models)) / len(models)
    if simplex:
        opt = minimize(lambda a: np.mean((x @ a-y)**2), w,
                       jac=lambda a: 2*x.T@(x@a-y)/len(y), method='SLSQP',
                       bounds=[(0, 1)]*len(w),
                       constraints={'type': 'eq', 'fun': lambda a: a.sum()-1,
                                    'jac': lambda a: np.ones(len(a))},
                       options={'ftol': 1e-10, 'maxiter': 500})
        assert opt.success, opt.message
        w = opt.x
    return (1-lam)*w + lam/len(w), raw_sum


def stack(meta, valid, models, lam, simplex=False, harmonic=True, bands=True):
    w, raw_sum = fit_weights(meta, models, lam, simplex)
    work = meta.copy()
    if bands:
        edges = np.quantile(meta.tod, np.linspace(0, 1, 4))
        edges[0], edges[-1] = -np.inf, np.inf
        band = np.digitize(meta.tod, edges[1:-1])
        bw = {}
        for k in range(3):
            part = meta.loc[band == k]
            wi = fit_weights(part, models, lam, simplex)[0] if len(part) >= 150 else w
            bw[k] = .5*wi + .5*w
        work['blend'] = np.clip(fp.apply_tod_blend(meta[models].values, meta.tod, edges, bw), 5, 100)
        pred = np.clip(fp.apply_tod_blend(valid[models].values, valid.tod, edges, bw), 5, 100)
    else:
        work['blend'] = np.clip(meta[models].values@w, 5, 100)
        pred = np.clip(valid[models].values@w, 5, 100)
    if harmonic:
        pred = np.clip(fp.apply_harm_bias(pred, valid.tod, fp.harm_bias(work)), 5, 100)
    return pred, raw_sum


def main():
    with (ROOT/'outputs/robust_baseline.pkl').open('rb') as f:
        frame = pickle.load(f)['frame'].copy()
    frame['datetime'] = pd.to_datetime(frame.datetime)
    assert not frame.duplicated(['family', 'fold', 'datetime']).any()
    origins = frame.groupby(['family', 'fold']).datetime.min()-pd.Timedelta(minutes=30)
    frame['origin'] = [origins.loc[(f, k)] for f, k in zip(frame.family, frame.fold)]
    assert (frame.origin < frame.datetime).all()
    specs = {
        'v12': (fp.MODELS, .25, False, True, True),
        'v16': (fp.MODELS_L2, .25, False, True, True),
        'v20': (fp.MODELS_L2, 0., False, True, True),
        'simplex_v20': (fp.MODELS_L2, 0., True, True, True),
        'v20_noharm': (fp.MODELS_L2, 0., False, False, True),
        'v20_global': (fp.MODELS_L2, 0., False, False, False),
    }
    rows, predictions, overlaps = [], [], []
    for (family, fold), valid in frame.groupby(['family', 'fold']):
        other = frame.loc[~((frame.family == family)&(frame.fold == fold))]
        overlaps.append(dict(family=family, fold=int(fold), n=len(valid),
                             labels_shared=int(valid.datetime.isin(other.datetime).sum()),
                             origin=str(valid.origin.iloc[0])))
        for mode in ('legacy_loo', 'past_repeated', 'past_only', 'past_only_48h'):
            if mode == 'legacy_loo':
                meta = other
            else:
                cutoff = valid.origin.iloc[0] - pd.Timedelta(hours=48 if mode.endswith('48h') else 0)
                meta = other.loc[other.datetime <= cutoff]
                # Preserve individual OOF forecasts but give each label one total vote:
                # choose its latest available forecast rather than averaging predictions.
                if mode != 'past_repeated':
                    meta = meta.sort_values(['origin', 'family', 'fold']).drop_duplicates('datetime', keep='last')
                assert not valid.datetime.isin(meta.datetime).any()
                if len(meta):
                    assert meta.datetime.max() <= cutoff
                    assert meta.origin.max() < valid.origin.iloc[0]
            if len(meta) < 300:
                continue
            for name, args in specs.items():
                pred, raw_sum = stack(meta, valid, *args)
                rows.append(dict(mode=mode, family=family, fold=int(fold), model=name,
                                 n=len(valid), meta_rows=len(meta), meta_unique=meta.datetime.nunique(),
                                 rmse=fp.rmse(valid.y, pred), nnls_raw_sum=raw_sum))
                d=valid[['family','fold','datetime','origin','y','tod']].copy()
                d['mode'],d['model'],d['pred']=mode,name,pred
                predictions.append(d)
    scores=pd.DataFrame(rows)
    preds=pd.concat(predictions,ignore_index=True)
    scores.to_csv(OUT/'scores.csv',index=False)
    preds.to_pickle(OUT/'predictions.pkl')
    pd.DataFrame(overlaps).to_csv(OUT/'overlap.csv',index=False)
    print('OVERLAP', json.dumps(overlaps))
    print('ROWS', len(frame), 'UNIQUE', frame.datetime.nunique())
    print(scores.groupby(['mode','model']).agg(mean_rmse=('rmse','mean'),folds=('rmse','size')).to_string())
    # Compare all modes on the same folds, avoiding a changed evaluation population.
    common=scores.loc[scores['mode']=='past_only_48h',['family','fold']].drop_duplicates()
    matched=scores.merge(common,on=['family','fold'])
    print('MATCHED FOLDS\n',matched.groupby(['mode','model']).rmse.mean().to_string())
    # One forecast per timestamp, latest eligible origin, for descriptive error accounting.
    u=preds.loc[(preds['mode']=='past_only')&(preds.model=='v20')].sort_values(['origin','family','fold']).drop_duplicates('datetime',keep='last').sort_values('datetime').set_index('datetime')
    g=fp.load_grid(); F=fp.make_features(g)
    u['error']=u.pred-u.y;u['se']=u.error**2
    u['T']=F.loc[u.index,'T'];u['pressure']=F.loc[u.index,'pressure'];u['T_rng48']=F.loc[u.index,'T_rng48']
    u['T_missing']=g.loc[u.index,'air_temperature'].isna()
    u['T_repaired']=g.loc[u.index,'air_temperature'].notna() & (abs(g.loc[u.index,'air_temperature']-u['T'])>1e-8)
    u['abs_dT']=F['T'].diff().abs().reindex(u.index)
    u['hour_band']=pd.cut(u.tod,[0,6,12,18,24],right=False,include_lowest=True)
    u['dT_band']=pd.cut(u.abs_dT,[-np.inf,.5,1,2,np.inf])
    daily=u.groupby(u.index.normalize()).agg(n=('se','size'),mse=('se','mean'),bias=('error','mean'))
    daily['rmse']=np.sqrt(daily.mse)
    daily.to_csv(OUT/'daily.csv')
    print('WORST DAYS\n',daily.sort_values('mse',ascending=False).head(10).to_string())
    breakdown=[]
    for col in ['hour_band','dT_band','T_missing','T_repaired']:
        tab=u.groupby(col,observed=True).agg(n=('se','size'),mse=('se','mean'),bias=('error','mean'),sse=('se','sum'))
        tab['rmse']=np.sqrt(tab.mse);tab['error_share']=tab.sse/u.se.sum()
        print(col,'\n',tab.to_string())
        for key,r in tab.iterrows():breakdown.append(dict(axis=col,group=str(key),**r.to_dict()))
    pd.DataFrame(breakdown).to_csv(OUT/'breakdown.csv',index=False)
    day_bias=u.groupby(u.index.normalize()).error.transform('mean')
    summary=dict(n=len(u),rmse=float(np.sqrt(u.se.mean())),bias=float(u.error.mean()),
                 day_level_mse_share=float(np.mean(day_bias**2)/u.se.mean()),
                 within_day_rmse=float(np.sqrt(np.mean((u.error-day_bias)**2))),
                 worst10pct_sse_share=float(u.se.nlargest(int(np.ceil(.1*len(u)))).sum()/u.se.sum()),
                 lag1=float(u.error.autocorr()),
                 dataset=dict(train=int((g.is_test==0).sum()),test=int((g.is_test==1).sum()),features=len(F.columns)))
    # Last-45d bagging cannot act on <=45d folds.
    counts=[]
    for (fam,k),origin in origins.items():
        tr=g.loc[(g.is_test==0)&g[fp.TARGET].notna()&(g.index<=origin)]
        counts.append(dict(family=fam,fold=int(k),train_rows=len(tr),removed_by_recent45=int((tr.index<=origin-pd.Timedelta(days=45)).sum())))
    pd.DataFrame(counts).to_csv(OUT/'recent45_exposure.csv',index=False)
    summary['recent45_folds_unchanged']=sum(r['removed_by_recent45']==0 for r in counts)
    summary['recent45_folds_total']=len(counts)
    # Negative control: a scored label must not influence its own prediction.
    v=frame.loc[(frame.family=='P')&(frame.fold==8)]
    m=frame.loc[~((frame.family=='P')&(frame.fold==8))].copy()
    changed=m.copy();changed.loc[changed.datetime.isin(v.datetime),'y']+=10
    old=stack(m,v,fp.MODELS_L2,0.)[0]
    altered=stack(changed,v,fp.MODELS_L2,0.)[0]
    cut=v.origin.iloc[0]
    strict=stack(m.loc[m.datetime<=cut],v,fp.MODELS_L2,0.)[0]
    strict_altered=stack(changed.loc[changed.datetime<=cut],v,fp.MODELS_L2,0.)[0]
    invariance=dict(legacy_prediction_change_when_scored_labels_changed=float(np.max(abs(old-altered))),
                    chronological_prediction_change=float(np.max(abs(strict-strict_altered))),
                    shared_label_rows_in_meta=int(m.datetime.isin(v.datetime).sum()))
    assert invariance['legacy_prediction_change_when_scored_labels_changed']>.01
    assert invariance['chronological_prediction_change']==0
    (OUT/'label_invariance.json').write_text(json.dumps(invariance,indent=2))
    (OUT/'summary.json').write_text(json.dumps(summary,indent=2))
    print('SUMMARY',json.dumps(summary,indent=2))
    u.to_csv(OUT/'unique_errors.csv')


if __name__=='__main__':main()
