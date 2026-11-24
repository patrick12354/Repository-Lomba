"""Extend the fixed increment hypothesis to every chronological-cache fold.
Diagnostic only; no public/private labels or submission output.
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import lightgbm as lgb
from scipy.sparse import eye,diags
from scipy.sparse.linalg import spsolve
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import final_pipeline as fp


def main():
    out=ROOT/'outputs/audit_v20';g=fp.load_grid();F=fp.make_features(g);y=g[fp.TARGET]
    cache=pd.read_pickle(out/'predictions.pkl')
    cache=cache.loc[(cache['mode']=='past_only')&cache.model.isin(['v12','v16','v20'])]
    records=[];predictions=[]
    cols=['T','co2','pressure','rh_tmin48','T_rng48','sin1','cos1']
    Xs={h:pd.concat([F,F[cols].shift(h).add_suffix('_prev'),F[cols].diff(h).add_suffix('_change')],axis=1) for h in (1,4,12)}
    for (fam,k),group in cache.groupby(['family','fold']):
        base=group.loc[group.model=='v20'].sort_values('datetime');vi=pd.DatetimeIndex(base.datetime)
        cut=vi.min()-pd.Timedelta(minutes=30);n=len(base)
        tr=(g.is_test==0)&y.notna()&(g.index<=cut)
        A=eye(n,format='csc');offset=np.zeros(n);parts={}
        for h,lam in [(1,4.),(4,1.),(12,1.)]:
            target=y-y.shift(h);tm=tr&target.notna()&tr.shift(h,fill_value=False)
            assert g.index[tm].max()<=cut
            model=lgb.LGBMRegressor(objective='regression',n_estimators=500,learning_rate=.03,
                        num_leaves=15,min_child_samples=30,reg_lambda=5,colsample_bytree=.8,
                        random_state=20260905,verbosity=-1,n_jobs=2).fit(Xs[h].loc[tm],target.loc[tm])
            inc=model.predict(Xs[h].loc[vi[h:]])
            D=diags([-np.ones(n-h),np.ones(n-h)],[0,h],shape=(n-h,n),format='csc')
            parts[h]=(lam*(D.T@D),lam*(D.T@inc))
            A=A+parts[h][0];offset+=parts[h][1]
        for name in ['v12','v16','v20']:
            b=group.loc[group.model==name].sort_values('datetime')
            assert np.array_equal(b.datetime.values,base.datetime.values)
            rhs=b.pred.to_numpy()+offset;p=spsolve(A,rhs)
            assert np.max(np.abs(A@p-rhs))<1e-7
            p=np.clip(p,5,100);assert np.isfinite(p).all()
            rec=dict(family=fam,fold=k,model=name,n=n,
                     base_rmse=fp.rmse(b.y,b.pred),increment_rmse=fp.rmse(b.y,p))
            d=b[['family','fold','datetime','origin','model','y','pred']].copy();d['increment']=p
            # Mechanism ablations added after the original all-scale screen.
            for label,hs in [('inc_30min',[1]),('inc_2h',[4]),('inc_6h',[12]),('inc_30min_2h',[1,4])]:
                Ah=eye(n,format='csc');rh=b.pred.to_numpy().copy()
                for h in hs:Ah=Ah+parts[h][0];rh+=parts[h][1]
                ph=spsolve(Ah,rh)
                assert np.max(np.abs(Ah@ph-rh))<1e-7
                ph=np.clip(ph,5,100);d[label]=ph;rec[label]=fp.rmse(b.y,ph)
            records.append(rec)
            predictions.append(d)
        pd.DataFrame(records).to_csv(out/'increment_validation_scores.csv',index=False)
        pd.concat(predictions).to_pickle(out/'increment_validation_predictions.pkl')
        print(fam,k,'finished',flush=True)
    r=pd.DataFrame(records);r['delta']=r.increment_rmse-r.base_rmse
    print(r.groupby('model').agg(base=('base_rmse','mean'),increment=('increment_rmse','mean'),delta=('delta','mean'),wins=('delta',lambda x:int((x<0).sum()))).to_string())


if __name__=='__main__':main()
