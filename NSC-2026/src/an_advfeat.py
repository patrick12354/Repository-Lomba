"""Per-feature adversarial separability.  A feature that alone separates training rows from
test rows is one a tree can use to route every test row into a leaf built from
unrepresentative training data -- s2.3's time-proxy hazard, measured feature by feature."""
import numpy as np, pandas as pd, sys
sys.path.insert(0,'.'); import final_pipeline as fp
from sklearn.metrics import roc_auc_score
g=fp.load_grid(); F=fp.make_features(g); y=g[fp.TARGET]; IDX=g.index
is_tr=(g.is_test==0).values & y.notna().values; idx=IDX[is_tr]
te=IDX[(g.is_test==1).values]; pub,pri=te[:220],te[220:]
def auc1(col,tgt):
    a=F.loc[idx,col].values; b=F.loc[tgt,col].values
    m1,m2=np.isfinite(a),np.isfinite(b)
    if m1.sum()<50 or m2.sum()<20: return np.nan
    v=np.r_[a[m1],b[m2]]; lab=np.r_[np.zeros(m1.sum()),np.ones(m2.sum())]
    return max(roc_auc_score(lab,v),1-roc_auc_score(lab,v))
rows=[]
for c in F.columns:
    rows.append(dict(feat=c,auc_pub=auc1(c,pub),auc_pri=auc1(c,pri)))
D=pd.DataFrame(rows).set_index('feat')
lo,hi=F.loc[idx].quantile(.01),F.loc[idx].quantile(.99)
D['cov_pri']=(((F.loc[pri]>=lo)&(F.loc[pri]<=hi))|F.loc[pri].isna()).mean()
D['delta']=D.auc_pri-D.auc_pub
D=D.sort_values('auc_pri',ascending=False)
pd.set_option('display.width',200)
print("features that most separate TRAIN from the PRIVATE slice, on their own:")
print(D.head(28).round(3).to_string())
print("\ncount with single-feature AUC > 0.95:  private %d, public %d  (of %d)"%(
    (D.auc_pri>0.95).sum(),(D.auc_pub>0.95).sum(),len(D)))
print("count with AUC > 0.90:                private %d, public %d"%(
    (D.auc_pri>0.90).sum(),(D.auc_pub>0.90).sum()))
D.to_csv('outputs/adv_perfeature.csv')
sus=D[(D.auc_pri>0.95)].index.tolist()
np.save('outputs/drop_auc95.npy',np.array(sus,dtype=object),allow_pickle=True)
print("\nDROP_AUC95 (%d features):\n  %s"%(len(sus),sus))
d916=set(np.load('outputs/drop_916.npy',allow_pickle=True))
print("\noverlap with the coverage list (DROP_916): %d of %d"%(len(set(sus)&d916),len(sus)))
print("union of the two lists: %d features"%len(set(sus)|d916))
np.save('outputs/drop_union.npy',np.array(sorted(set(sus)|d916),dtype=object),allow_pickle=True)
