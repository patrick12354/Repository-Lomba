"""Summarize fixed-screen and post-screen ablations; calendar-block uncertainty."""
from pathlib import Path
import json
import numpy as np
import pandas as pd

OUT=Path(__file__).resolve().parents[1]/'outputs/audit_v20'


def main():
    r=pd.read_pickle(OUT/'increment_validation_predictions.pkl')
    candidates=['increment','inc_30min','inc_2h','inc_6h','inc_30min_2h']
    results=[]
    for name,g in r.groupby('model'):
        u=g.sort_values(['origin','family','fold']).drop_duplicates('datetime',keep='last').sort_values('datetime').copy()
        for cand in candidates:
            se=(g.pred-g.y)**2;ce=(g[cand]-g.y)**2
            delta=g.assign(sb=se,sc=ce).groupby(['family','fold']).agg(sb=('sb','mean'),sc=('sc','mean'))
            delta['delta']=np.sqrt(delta.sc)-np.sqrt(delta.sb)
            u['sb']=(u.pred-u.y)**2;u['sc']=(u[cand]-u.y)**2
            daily=u.groupby(u.datetime.dt.normalize()).agg(sb=('sb','sum'),sc=('sc','sum'),n=('sb','size'))
            cis={}
            for length in [1,3,7]:
                rng=np.random.default_rng(20260905)
                starts=rng.integers(0,len(daily),size=(4000,int(np.ceil(len(daily)/length))))
                ix=((starts[:,:,None]+np.arange(length))%len(daily)).reshape(4000,-1)[:,:len(daily)]
                z=daily.to_numpy()[ix].sum(axis=1)
                bd=np.sqrt(z[:,1]/z[:,2])-np.sqrt(z[:,0]/z[:,2])
                cis[str(length)]=np.quantile(bd,[.025,.975]).tolist()
            results.append(dict(model=name,candidate=cand,folds=len(delta),wins=int((delta.delta<0).sum()),
                                mean_delta=float(delta.delta.mean()),base_pooled=float(np.sqrt(se.mean())),
                                candidate_pooled=float(np.sqrt(ce.mean())),
                                unique_base=float(np.sqrt(u.sb.mean())),unique_candidate=float(np.sqrt(u.sc.mean())),
                                families=delta.groupby('family').delta.mean().to_dict(),
                                bootstrap_ci=cis))
    (OUT/'ablation_summary.json').write_text(json.dumps(results,indent=2))
    print(pd.DataFrame(results).drop(columns=['families','bootstrap_ci']).to_string(index=False))
    for row in results:
        if row['candidate']=='inc_30min_2h':print(json.dumps(row,indent=2))
    s=pd.read_csv(OUT/'increment_validation_scores.csv')
    print('LAST 15D FOLD\n',s[(s.family=='P')&(s.fold==8)].to_string(index=False))


if __name__=='__main__':main()
