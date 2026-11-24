"""Read-only model audit after user-reported public 2.93028. No test labels or tuning.

Writes diagnostic files only. Random-subset experiments are conditional simulations
on labelled holdouts, not estimates of Kaggle's actual split or private performance.
"""
import sys
import json
from pathlib import Path
import numpy as np
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT/'src')]
import final_pipeline as fp
import an47_v21_forward_benchmark as a47

OUT = ROOT/'outputs/audit_v21_public_regression'
SCORES = dict(v21=2.86595, full=2.93028)


def run():
    OUT.mkdir(parents=True, exist_ok=True)
    paths = dict(v21='v21_increment_v16', physics='v21_increment_v16_phys',
                 dsh='v21_increment_v16_phys_dsh', full='v21_increment_v16_phys_dsh_lags')
    frames = {k:pd.read_csv(ROOT/'outputs/submissions'/f'{v}.csv',parse_dates=['datetime'])
              for k,v in paths.items()}
    idx = pd.DatetimeIndex(frames['v21'].datetime)
    for f in frames.values():
        assert pd.DatetimeIndex(f.datetime).equals(idx)
        assert np.isfinite(f[fp.TARGET]).all() and len(f)==734
    moves, move_slices = [], []
    for before, after in [('v21','physics'),('physics','dsh'),('dsh','full'),('v21','full')]:
        p,q=frames[before][fp.TARGET].to_numpy(),frames[after][fp.TARGET].to_numpy()
        u=q-p
        moves.append(dict(before=before,after=after,rms=float(np.sqrt(np.mean(u*u))),
            mean=float(u.mean()),max_abs=float(abs(u).max()),sd_before=float(p.std()),
            sd_after=float(q.std()),rows_gt1=int((abs(u)>1).sum())))
        d=pd.DataFrame(dict(datetime=idx,move=u,day=idx.normalize(),hour=idx.hour))
        for key, grp in [('hour',pd.cut(d.hour,[-1,5,11,17,23]).astype(str)),('day',d.day.astype(str))]:
            for value, t in d.groupby(grp):
                move_slices.append(dict(before=before,after=after,dimension=key,slice=value,
                    n=len(t),mean=t.move.mean(),rms=np.sqrt(np.mean(t.move**2))))
    pd.DataFrame(moves).to_csv(OUT/'submission_moves.csv',index=False)
    pd.DataFrame(move_slices).to_csv(OUT/'submission_move_slices.csv',index=False)
    stages=dict(v21=a47.OUT_S27/'preds_v21_increment.pkl',
                physics=a47.OUT_S27/'preds_v21_physics.pkl',
                dsh=a47.OUT_S27/'preds_v21_physics_deshrink_half.pkl',
                full=ROOT/'outputs/audit_v21_s28/preds_production_lgb_lags_production.pkl')
    combined=None
    for k,p in stages.items():
        d=pd.read_pickle(p)
        if 'scope' in d: d=d.loc[d.scope=='outer']
        d=d.loc[d.score,['block','datetime','y','recon']].rename(columns={'recon':k})
        if combined is None: combined=d
        else: combined=combined.merge(d.drop(columns='y'),on=['block','datetime'],validate='one_to_one')
    rows, daily, sims=[],[],[]
    rng=np.random.default_rng(20260906)
    for before,after in [('v21','physics'),('physics','dsh'),('dsh','full'),('v21','full')]:
        for b,d in combined.groupby('block'):
            p,q,y=d[before].to_numpy(),d[after].to_numpy(),d.y.to_numpy()
            a,e=(p-y)**2,(q-y)**2
            rows.append(dict(before=before,after=after,block=b,base=fp.rmse(y,p),
                candidate=fp.rmse(y,q),delta=fp.rmse(y,q)-fp.rmse(y,p)))
            work=d.assign(dmse=e-a,day=pd.to_datetime(d.datetime).dt.normalize())
            for day,t in work.groupby('day'):
                daily.append(dict(before=before,after=after,block=b,day=day,n=len(t),dmse=t.dmse.mean()))
            if (before,after)==('v21','full'):
                draws=[]
                for _ in range(20000):
                    take=rng.choice(len(d),220,replace=False)
                    draws.append(float(np.sqrt(e[take].mean())-np.sqrt(a[take].mean())))
                sims.append(dict(block=b,scenario='220 random rows of this 720-row holdout',
                    p_worse=float(np.mean(np.array(draws)>0)),
                    p_ge_observed=float(np.mean(np.array(draws)>=SCORES['full']-SCORES['v21'])),
                    q025=float(np.quantile(draws,.025)),q50=float(np.median(draws)),q975=float(np.quantile(draws,.975))))
    pd.DataFrame(rows).to_csv(OUT/'stage_holdouts.csv',index=False)
    pd.DataFrame(daily).to_csv(OUT/'stage_daily.csv',index=False)
    # Exogenous support on each forecast's own feature horizon, with train-only cutoffs.
    g=fp.load_grid(); support=[]
    spans=list(a47.blocks_of(g))+[('test',g.index[g.is_test.eq(0)].max(),g.index.max())]
    for b,origin,end in spans:
        gh=g.loc[g.index<=end];F=fp.make_features(gh)
        tr=gh.index[(gh.index<=origin)&gh[fp.TARGET].notna()&gh.is_test.eq(0)]
        va=gh.index[(gh.index>origin)&(gh.is_test.eq(1) if b=='test' else gh[fp.TARGET].notna())]
        for col in ['T','co2','pressure','rh_tmin48']:
            for lag in [0,4,16,48]:
                v=F[col].shift(lag);t=v.loc[tr].dropna();q=v.loc[va].dropna()
                lo,hi=t.quantile([.01,.99]);outside=((q<lo)|(q>hi)).mean()
                support.append(dict(block=b,feature=col,lag=lag,train_mean=t.mean(),
                    forecast_mean=q.mean(),outside_p01_p99=outside,
                    outside_minmax=((q<t.min())|(q>t.max())).mean()))
    pd.DataFrame(support).to_csv(OUT/'feature_support.csv',index=False)
    report=dict(scores_reported_by_user=SCORES,public_delta=SCORES['full']-SCORES['v21'],
        public_mse_delta=SCORES['full']**2-SCORES['v21']**2,
        public_mse_relative=SCORES['full']**2/SCORES['v21']**2-1,
        submission_hashes={k:a47.md5(ROOT/'outputs/submissions'/f'{v}.csv') for k,v in paths.items()},
        simulation=sims,moves=moves,
        caveat='No test targets read. Subset simulations condition on old, repeatedly-used holdouts; not private odds.')
    (OUT/'public_audit.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2));print(pd.DataFrame(rows).to_string(index=False))
    print(pd.DataFrame(support).query("lag==0").to_string(index=False))


if __name__=='__main__':
    run()
