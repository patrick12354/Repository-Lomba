"""Predeclared diagnostic screen, not a submission generator.

Hypothesis: increments can transfer more reliably than absolute RH levels.
Fit RH increments at 0.5/2/6h using past train labels only; reconcile them with
the unmodified chronological v20 prediction. Compare zero-increment smoothing
as a control, and 21/30-day hbt replacements as the temporal-bagging audit.
No strength selection, leaderboard input, or test predictions.
"""
import json
import pickle
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import lightgbm as lgb
from scipy.sparse import diags, eye
from scipy.sparse.linalg import spsolve

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'src')]
import final_pipeline as fp
from an30_v20_audit import stack

OUT=ROOT/'outputs/audit_v20'


def main():
    g=fp.load_grid();F=fp.make_features(g);y=g[fp.TARGET]
    frame=pickle.load(open(ROOT/'outputs/robust_baseline.pkl','rb'))['frame']
    audit=pd.read_pickle(OUT/'predictions.pkl')
    # Fixed spread of origins, screen only. These validation windows overlap.
    selected=[('P',3),('P',5),('P',8),('R',4)]
    records=[];saved=[];diagnostics=[]
    for fam,k in selected:
        va=frame.loc[(frame.family==fam)&(frame.fold==k)].copy()
        vi=pd.DatetimeIndex(va.datetime);cut=vi.min()-pd.Timedelta(minutes=30)
        tr=(g.is_test==0)&y.notna()&(g.index<=cut)
        base=audit.loc[(audit['mode']=='past_only')&(audit.model=='v20')&(audit.family==fam)&(audit.fold==k)].sort_values('datetime')
        assert len(base)==len(va) and np.array_equal(base.datetime.values,va.datetime.values)
        p=base.pred.to_numpy();n=len(p)
        A=eye(n,format='csc');rhs=p.copy();smoothrhs=p.copy()
        for h,lam in [(1,4.0),(4,1.0),(12,1.0)]:
            target=y-y.shift(h)
            cols=['T','co2','pressure','rh_tmin48','T_rng48','sin1','cos1']
            X=pd.concat([F,F[cols].shift(h).add_suffix('_prev'),F[cols].diff(h).add_suffix('_change')],axis=1)
            tm=tr&target.notna()&tr.shift(h,fill_value=False)
            assert g.index[tm].max()<=cut
            kw=dict(objective='regression',n_estimators=500,learning_rate=.03,
                    num_leaves=15,min_child_samples=30,reg_lambda=5,
                    colsample_bytree=.8,random_state=20260905,verbosity=-1,n_jobs=4)
            model=lgb.LGBMRegressor(**kw).fit(X.loc[tm],target.loc[tm])
            inc=model.predict(X.loc[vi[h:]])
            D=diags([-np.ones(n-h),np.ones(n-h)],[0,h],shape=(n-h,n),format='csc')
            A=A+lam*(D.T@D);rhs=rhs+lam*(D.T@inc)
            truth=va.y.to_numpy()[h:]-va.y.to_numpy()[:-h]
            diagnostics.append(dict(family=fam,fold=k,steps=h,
                                    model_increment_rmse=fp.rmse(truth,inc),
                                    baseline_increment_rmse=fp.rmse(truth,D@p),
                                    zero_increment_rmse=fp.rmse(truth,np.zeros(len(truth)))))
        preds={'v20':p,'increment_reconcile':np.clip(spsolve(A,rhs),5,100),
               'zero_increment_control':np.clip(spsolve(A,smoothrhs),5,100)}
        meta=frame.loc[frame.datetime<=cut].copy()
        origins=frame.groupby(['family','fold']).datetime.min()-pd.Timedelta(minutes=30)
        meta['origin']=[origins.loc[(f,j)] for f,j in zip(meta.family,meta.fold)]
        meta=meta.sort_values(['origin','family','fold']).drop_duplicates('datetime',keep='last')
        for days in (21,30):
            # Refit each meta forecast using the same window; don't train weights against
            # the legacy full-history hbt and silently swap it only at validation time.
            work=meta.copy()
            for origin,part in work.groupby('origin'):
                mask=(g.is_test==0)&y.notna()&(g.index<=origin)&(g.index>origin-pd.Timedelta(days=days))
                kw=dict(fp.LGB_KW,n_jobs=4)
                pp=np.mean([lgb.LGBMRegressor(random_state=s,**kw).fit(F.loc[mask],y.loc[mask]).predict(F.loc[pd.DatetimeIndex(part.datetime)]) for s in fp.SEEDS_OOF],axis=0)
                work.loc[part.index,'hbt']=np.clip(pp,5,100)
            tm=tr&(g.index>cut-pd.Timedelta(days=days))
            vnew=va.copy()
            vnew['hbt']=np.clip(np.mean([lgb.LGBMRegressor(random_state=s,**dict(fp.LGB_KW,n_jobs=4)).fit(F.loc[tm],y.loc[tm]).predict(F.loc[vi]) for s in fp.SEEDS_OOF],axis=0),5,100)
            preds[f'hbt_recent{days}']=stack(work,vnew,fp.MODELS_L2,0.)[0]
        for name,pr in preds.items():
            records.append(dict(family=fam,fold=k,model=name,n=n,rmse=fp.rmse(va.y,pr)))
            saved.append(pd.DataFrame({'family':fam,'fold':k,'datetime':vi,'model':name,'y':va.y.values,'pred':pr}))
        print(fam,k,pd.DataFrame(records).tail(len(preds)).to_string(index=False),flush=True)
        pd.DataFrame(records).to_csv(OUT/'dynamics_scores.csv',index=False)
        pd.DataFrame(diagnostics).to_csv(OUT/'increment_diagnostics.csv',index=False)
        pd.concat(saved).to_pickle(OUT/'dynamics_predictions.pkl')
    r=pd.DataFrame(records)
    print(r.groupby('model').rmse.mean().to_string())


if __name__=='__main__':main()
