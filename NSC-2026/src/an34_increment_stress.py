"""Fixed 30min+2h increment candidate on existing embargoed stress blocks."""
import sys,pickle,json
from pathlib import Path
import numpy as np
import pandas as pd
import lightgbm as lgb
from scipy.sparse import eye,diags
from scipy.sparse.linalg import spsolve
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'src')]
import final_pipeline as fp
from an30_v20_audit import stack


def main():
    out=ROOT/'outputs/audit_v20';g=fp.load_grid();F=fp.make_features(g);y=g[fp.TARGET]
    S=pickle.load(open(ROOT/'outputs/stress_members.pkl','rb'))
    frame=pickle.load(open(ROOT/'outputs/robust_baseline.pkl','rb'))['frame']
    origins=frame.groupby(['family','fold']).datetime.min()-pd.Timedelta(minutes=30)
    frame['origin']=[origins.loc[(f,k)] for f,k in zip(frame.family,frame.fold)]
    rows=[];preds=[];cols=['T','co2','pressure','rh_tmin48','T_rng48','sin1','cos1']
    for k,v in S.items():
        vi=v.index;cut=vi.min()-pd.Timedelta(hours=96);n=len(v)
        tr=(g.is_test==0)&y.notna()&(g.index<=cut)
        m=frame.loc[frame.datetime<=cut].sort_values(['origin','family','fold']).drop_duplicates('datetime',keep='last')
        assert len(m)>=300 and not m.datetime.isin(vi).any()
        A=eye(n,format='csc');off=np.zeros(n)
        for h,lam in [(1,4.),(4,1.)]:
            target=y-y.shift(h);tm=tr&target.notna()&tr.shift(h,fill_value=False)
            X=pd.concat([F,F[cols].shift(h).add_suffix('_prev'),F[cols].diff(h).add_suffix('_change')],axis=1)
            mod=lgb.LGBMRegressor(objective='regression',n_estimators=500,learning_rate=.03,num_leaves=15,
                                 min_child_samples=30,reg_lambda=5,colsample_bytree=.8,random_state=20260905,
                                 verbosity=-1,n_jobs=4).fit(X.loc[tm],target.loc[tm])
            inc=mod.predict(X.loc[vi[h:]])
            D=diags([-np.ones(n-h),np.ones(n-h)],[0,h],shape=(n-h,n),format='csc')
            A+=lam*(D.T@D);off+=lam*(D.T@inc)
        for name,models,lam in [('v12',fp.MODELS,.25),('v16',fp.MODELS_L2,.25),('v20',fp.MODELS_L2,0.)]:
            p=stack(m,v,models,lam)[0];q=spsolve(A,p+off)
            assert np.max(abs(A@q-(p+off)))<1e-7
            q=np.clip(q,5,100)
            rows.append(dict(block=k,model=name,meta_unique=len(m),base=fp.rmse(v.y,p),increment=fp.rmse(v.y,q)))
            preds.append(pd.DataFrame({'block':k,'model':name,'datetime':vi,'y':v.y.values,'pred':p,'increment':q}))
        print('stress',k,'done',flush=True)
    r=pd.DataFrame(rows);r['delta']=r.increment-r.base;r.to_csv(out/'increment_stress_scores.csv',index=False)
    P=pd.concat(preds);P.to_pickle(out/'increment_stress_predictions.pkl')
    summary={name:dict(base_pooled=fp.rmse(d.y,d.pred),candidate_pooled=fp.rmse(d.y,d.increment),
                      base_worst=float(r.loc[r.model==name,'base'].max()),candidate_worst=float(r.loc[r.model==name,'increment'].max())) for name,d in P.groupby('model')}
    (out/'increment_stress_summary.json').write_text(json.dumps(summary,indent=2))
    print(r.to_string(index=False));print(json.dumps(summary,indent=2))


if __name__=='__main__':main()
