"""s19.2's extrapolation audit, run against the PRIVATE slice instead of the whole test set.
s7 dropped the soil block on exactly this criterion and it was one of the biggest wins in
the log.  Note this is NOT s38's trap: s38 pruned by CV score (a selection leak), this prunes
by training-support coverage, which is a target-free property of the data."""
import numpy as np, pandas as pd, sys
sys.path.insert(0,'.'); import final_pipeline as fp
g=fp.load_grid(); F=fp.make_features(g)
trm=(g.is_test==0).values; tem=(g.is_test==1).values
Ftr,Fte=F[trm],F[tem]; lo,hi=Ftr.quantile(0.01),Ftr.quantile(0.99)
def cov(D): return (((D>=lo)&(D<=hi))|D.isna()).mean()
d=pd.DataFrame({'all_test':cov(Fte),'public':cov(Fte.iloc[:220]),'private':cov(Fte.iloc[220:])})
d=d.sort_values('private')
BAR=0.916    # s19.2's own minimum-support bar
print("features below s19.2's 0.916 support bar ON THE PRIVATE SLICE:")
print(d[d.private<BAR].round(3).to_string())
print("\ncount below 0.916: private %d, public %d, whole test %d  (of %d)"%(
    (d.private<BAR).sum(),(d.public<BAR).sum(),(d.all_test<BAR).sum(),len(d)))
for nm,thr in (('DROP_916',0.916),('DROP_85',0.85),('DROP_PRESSLEVEL',None)):
    if thr is None:
        cols=[c for c in F.columns if c.startswith('pressure') and not c.endswith(('_a1h','_a6h','_a24h','_sd6h'))]
    else:
        cols=list(d[d.private<thr].index)
    print("\n%s (%d features):\n  %s"%(nm,len(cols),cols))
np.save('outputs/drop_916.npy',np.array(list(d[d.private<0.916].index),dtype=object),allow_pickle=True)
np.save('outputs/drop_85.npy',np.array(list(d[d.private<0.85].index),dtype=object),allow_pickle=True)
