import pandas as pd, numpy as np
pd.set_option('display.width',250); pd.set_option('display.max_columns',60)
D='Dataset/'
tr=pd.read_csv(D+'train.csv',parse_dates=['datetime'])
te=pd.read_csv(D+'test.csv',parse_dates=['datetime'])
tr['is_tr']=1; te['is_tr']=0
al=pd.concat([tr,te],ignore_index=True).sort_values('datetime').reset_index(drop=True)
EX=[c for c in te.columns if c not in ('datetime','env_id','is_tr')]

print("=== env_id vs time ===")
al['idx']=np.arange(len(al))
print(al[['env_id','idx']].corr().round(6))
d=al.env_id.diff()
print('env_id diff describe:'); print(d.describe().round(2))
print('env_id vs 30min-slot linear fit:')
t=(al.datetime-al.datetime.min()).dt.total_seconds()/1800
import numpy.polynomial as P
co=np.polyfit(t,al.env_id,1); print(' slope',round(co[0],3),'intercept',round(co[1],2),'resid std',round(np.std(al.env_id-np.polyval(co,t)),3))

print("\n=== TARGET: hour-of-day profile (train) ===")
tr['hour']=tr.datetime.dt.hour
print(tr.groupby('hour').air_humidity.agg(['mean','std','count']).round(2).T)

print("\n=== TARGET autocorrelation (train, contiguous) ===")
s=tr.set_index('datetime').air_humidity.asfreq('30min')
for l in [1,2,4,8,12,24,48,96,336,720,734]:
    print(f'  lag{l:4d} ({l/2:6.1f}h): {s.autocorr(l):.4f}')

print("\n=== corr of exogenous w/ air_humidity (train, pearson & spearman) ===")
cc=[]
for c in EX:
    x=tr[c]
    if x.notna().sum()<50: continue
    cc.append((c, tr.air_humidity.corr(x), tr.air_humidity.corr(x,method='spearman')))
cc=pd.DataFrame(cc,columns=['col','pearson','spearman']).sort_values('spearman',key=abs,ascending=False)
print(cc.round(3).to_string(index=False))

print("\n=== outlier sniff: |z| of point vs neighbor-median (all cols, train+test) ===")
for c in ['air_humidity','air_temperature','pressure','co2','soil_temp_line1','soil_ec_line1','water_volume_line1','gdd']:
    v=al.set_index('datetime')[c].asfreq('30min')
    med=v.rolling(9,center=True,min_periods=4).median()
    dev=(v-med).abs()
    mad=dev.rolling(97,center=True,min_periods=20).median()
    r=(dev/(mad+1e-9))
    print(f'  {c:24s} n={v.notna().sum():5d} frac dev>6*mad: {(r>6).mean():.4f}  max dev {dev.max():.1f}')
