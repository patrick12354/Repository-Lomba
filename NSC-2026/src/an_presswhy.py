"""Why does removing ten collinear pressure columns improve ridge by 0.69?"""
import numpy as np, pandas as pd, sys
sys.path.insert(0,'.'); import final_pipeline as fp
from sklearn.linear_model import Ridge
g=fp.load_grid(); F=fp.make_features(g); y=g[fp.TARGET]; IDX=g.index
is_tr=(g.is_test==0).values & y.notna().values; idx=IDX[is_tr]; end=idx.max()
d85=set(np.load('outputs/drop_85.npy',allow_pickle=True))
PRESS=[c for c in d85 if c.startswith('pressure')]
print("pressure-level columns: %d"%len(PRESS))
C=F.loc[idx,PRESS].corr().values
print("mean |pairwise correlation| among them: %.3f  (min %.3f)"%(
    np.abs(C[np.triu_indices(len(PRESS),1)]).mean(),np.abs(C[np.triu_indices(len(PRESS),1)]).min()))
cut=end-pd.Timedelta(days=15); v=idx[idx>cut]; t=idx[idx<=cut]
for nm,drop in (('with pressure levels',set()),('without',d85)):
    cols=[c for c in F.columns if c not in drop]
    pipe=fp._pipe(Ridge(alpha=20.0)).fit(F.loc[t,cols],y.loc[t])
    p=np.clip(pipe.predict(F.loc[v,cols]),5,100)
    co=pd.Series(pipe[-1].coef_,index=cols)
    Z=pipe[1].transform(pipe[0].transform(F.loc[v,cols]))
    contrib=Z*co.values
    pc=[i for i,c in enumerate(cols) if c.startswith('pressure')]
    print("\n%s: fold RMSE %.4f   sum|coef| %.1f"%(nm,fp.rmse(y.loc[v],p),co.abs().sum()))
    print("   |coef| on pressure columns: %.2f   sd of their TOTAL contribution across rows: %.2f"%(
        co.iloc[pc].abs().sum(), contrib[:,pc].sum(1).std()))
    print("   sd of the whole prediction: %.2f"%p.std())
    top=co.abs().sort_values(ascending=False).head(6)
    print("   top coefficients: %s"%", ".join("%s %.2f"%(k,v_) for k,v_ in top.items()))
