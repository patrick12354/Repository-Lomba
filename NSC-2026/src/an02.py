"""Extrapolation audit of the new tmin block: test values must have training support.
Sec 7 killed the soil block for exactly this reason -- do not import the same bug."""
import warnings; warnings.filterwarnings('ignore')
import sys, numpy as np, pandas as pd
sys.path.insert(0,'src'); from common import *
g,_,_=load_grid(); c=clean_exog(g,k=6.0); T=c['air_temperature']
tr=(g.is_test==0).values; te=(g.is_test==1).values
mn24=T.rolling(49,center=True,min_periods=8).min(); mx24=T.rolling(49,center=True,min_periods=8).max()
mn48=T.rolling(97,center=True,min_periods=8).min(); mx48=T.rolling(97,center=True,min_periods=8).max()
cand={'T_min24h':mn24,'T_max24h':mx24,'T_rng24h':mx24-mn24,'T_minus_min24h':T-mn24,
      'rh_from_tmin24h':pd.Series(100*es(mn24.values)/es(T.values),index=g.index),
      'T_min48h':mn48,'T_rng48h':mx48-mn48,
      'rh_from_tmin48h':pd.Series(100*es(mn48.values)/es(T.values),index=g.index),
      '[ref] air_temperature':T,'[ref] T_c24h':T.rolling(49,center=True,min_periods=2).mean()}
print(f'{"feature":22s} {"tr p1":>7s} {"tr p99":>7s} {"te med":>7s} {"te min":>7s} {"te max":>7s} {"in-range":>9s} {"n_tr<te_p10":>12s}')
for k,s in cand.items():
    a,b=np.nanpercentile(s[tr],[1,99]); t=s[te].dropna()
    inr=float(((t>=a)&(t<=b)).mean()); p10=np.nanpercentile(t,10)
    print(f'{k:22s} {a:7.2f} {b:7.2f} {t.median():7.2f} {t.min():7.2f} {t.max():7.2f} {inr:9.3f} {int((s[tr]<p10).sum()):12d}')
