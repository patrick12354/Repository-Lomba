import numpy as np, pandas as pd, sys
sys.path.insert(0,'.'); import final_pipeline as fp
from sklearn.linear_model import Ridge
g=fp.load_grid(); F=fp.make_features(g); y=g[fp.TARGET]; IDX=F.index
tr=IDX[(g.is_test==0).values & y.notna().values]; te=IDX[(g.is_test==1).values]
Xtr,ytr=F.loc[tr],y.loc[tr]
pipe=fp._pipe(Ridge(alpha=20.0)).fit(Xtr,ytr)
imp,sc,rid=pipe[0],pipe[1],pipe[2]
Z=lambda D: sc.transform(imp.transform(D))
Ztr,Zte=Z(Xtr),Z(F.loc[te])
contrib=Zte*rid.coef_                      # per-row, per-feature contribution to the prediction
C=pd.DataFrame(contrib,index=te,columns=F.columns)
pub,pri=C.iloc[:220],C.iloc[220:]
d=pd.DataFrame({'pub':pub.mean(),'pri':pri.mean()}); d['shift']=d.pri-d.pub
print("ridge prediction shift public->private, decomposed by feature (top 16 each way):")
print(d.sort_values('shift',ascending=False).head(16).round(3).to_string())
print("...")
print(d.sort_values('shift').head(10).round(3).to_string())
print("\ntotal ridge shift pub->pri: %.3f  (sum of parts %.3f)"%(pri.sum(1).mean()-pub.sum(1).mean(), d['shift'].sum()))

# how much of the shift comes from rows OUTSIDE the training support?
lo,hi=Xtr.quantile(.01),Xtr.quantile(.99)
Xte=F.loc[te]
Xclip=Xte.clip(lo,hi,axis=1)
Zc=Z(Xclip); Cc=pd.DataFrame(Zc*rid.coef_,index=te,columns=F.columns)
print("\nridge mean prediction:")
print("  raw   : public %.2f  private %.2f  (shift %+.2f)"%(pipe.predict(Xte)[:220].mean(),pipe.predict(Xte)[220:].mean(),
      pipe.predict(Xte)[220:].mean()-pipe.predict(Xte)[:220].mean()))
print("  clipped: public %.2f  private %.2f  (shift %+.2f)"%(pipe.predict(Xclip)[:220].mean(),pipe.predict(Xclip)[220:].mean(),
      pipe.predict(Xclip)[220:].mean()-pipe.predict(Xclip)[:220].mean()))
ds=(d['shift']-(Cc.iloc[220:].mean()-Cc.iloc[:220].mean()))
print("\nfeatures whose shift is REMOVED by clipping to the train 1-99%% band (top 12):")
print(ds.sort_values(ascending=False).head(12).round(3).to_string())
