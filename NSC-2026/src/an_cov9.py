import numpy as np, pandas as pd, sys
sys.path.insert(0,'.'); import final_pipeline as fp
g=fp.load_grid(); F=fp.make_features(g)
trm=(g.is_test==0).values; tem=(g.is_test==1).values
Ftr=F[trm]; Fte=F[tem]
lo=Ftr.quantile(0.01); hi=Ftr.quantile(0.99)
pub=Fte.iloc[:220]; pri=Fte.iloc[220:]
def cov(D): return (((D>=lo)&(D<=hi))|D.isna()).mean()
d=pd.DataFrame({'cov_pub':cov(pub),'cov_pri':cov(pri)})
d['drop']=d.cov_pub-d.cov_pri
d['cov_test']=cov(Fte)
print("features with the worst private-slice coverage:")
print(d.sort_values('cov_pri').head(22).round(3).to_string())
print("\nfeatures that degrade most from public -> private:")
print(d.sort_values('drop',ascending=False).head(15).round(3).to_string())

# how time-index-like is each feature?  corr with row number over the joint grid
rn=pd.Series(np.arange(len(F)),index=F.index)
tt=F.assign(_rn=rn).corr(numeric_only=True)['_rn'].drop('_rn').abs().sort_values(ascending=False)
print("\nmost time-index-like features (|corr| with absolute row number, joint grid):")
print(tt.head(18).round(3).to_string())
DAILYF=[c for c in F.columns if c in fp.DAILY]
print("\ndaily block present in model:",DAILYF)
print("\nlevels (train vs test):")
for c in DAILYF+['T_min96','rh_tmin96']:
    print(f"  {c:26s} train [{Ftr[c].quantile(.01):8.2f},{Ftr[c].quantile(.99):8.2f}]  "
          f"pub [{pub[c].min():8.2f},{pub[c].max():8.2f}]  pri [{pri[c].min():8.2f},{pri[c].max():8.2f}]  "
          f"cov_pub {cov(pub)[c]:.2f} cov_pri {cov(pri)[c]:.2f}")
