import pandas as pd, numpy as np
pd.set_option('display.width',250); pd.set_option('display.max_columns',60)
D='Dataset/'
tr=pd.read_csv(D+'train.csv',parse_dates=['datetime'])
te=pd.read_csv(D+'test.csv',parse_dates=['datetime'])
tr['is_tr']=1; te['is_tr']=0
al=pd.concat([tr,te],ignore_index=True).sort_values('datetime').reset_index(drop=True)
g=al.set_index('datetime').asfreq('30min')

def flag(s,w=7,k=5.0):
    med=s.rolling(w,center=True,min_periods=3).median()
    dev=s-med
    mad=dev.abs().rolling(193,center=True,min_periods=30).median()*1.4826
    return dev.abs()>k*(mad+1e-9), dev, med

print("=== per-column outlier rate (k=5, w=7) and spike magnitude ===")
cols=[c for c in g.columns if c not in ('env_id','is_tr','env_battery')]
rows=[]
for c in cols:
    s=g[c]
    f,dev,med=flag(s)
    n=s.notna().sum()
    rows.append(dict(col=c,n=n,miss=round(1-n/len(g),4),outl=round(f.sum()/max(n,1),4),
                     dev_med=round(dev[f].abs().median(),2) if f.sum() else 0,
                     spike_min=round(s[f].min(),2) if f.sum() else 0, spike_max=round(s[f].max(),2) if f.sum() else 0,
                     clean_min=round(s[~f].min(),2), clean_max=round(s[~f].max(),2)))
print(pd.DataFrame(rows).to_string(index=False))

print("\n=== is corruption correlated across columns? (train rows) ===")
F=pd.DataFrame({c:flag(g[c])[0] for c in cols})
M=g[cols].isna()
print('mean pairwise corr of outlier-flags:',round(np.nanmean(F.corr().values[np.triu_indices(len(cols),1)]),4))
print('mean pairwise corr of missing-masks:',round(np.nanmean(M.corr().values[np.triu_indices(len(cols),1)]),4))
print('rows with >=1 outlier flag:',round(F.any(axis=1).mean(),3),'| rows all-clean:',round((~F.any(axis=1)&~M.any(axis=1)).mean(),3))

print("\n=== TARGET air_humidity spike analysis ===")
s=g.air_humidity; f,dev,med=flag(s,7,5.0)
print('flagged',f.sum(),'of',s.notna().sum(),'=',round(f.sum()/s.notna().sum(),4))
print('flagged values describe:'); print(s[f].describe().round(2))
print('their deviation from local median:'); print(dev[f].describe().round(2))
print('\nsample of flagged target rows:')
tmp=pd.DataFrame({'val':s[f],'localmed':med[f],'dev':dev[f]}).head(20)
print(tmp.round(2).to_string())

print("\n=== per-day target stats (find the anomaly) ===")
day=al.assign(d=al.datetime.dt.date).groupby('d').agg(hmean=('air_humidity','mean'),hstd=('air_humidity','std'),
    tmean=('air_temperature','median'),co2=('co2','median'),n=('air_humidity','size'))
print(day.round(2).to_string())
