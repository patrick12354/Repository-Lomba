import pandas as pd, numpy as np
pd.set_option('display.width',250)
D='Dataset/'
tr=pd.read_csv(D+'train.csv',parse_dates=['datetime'])
te=pd.read_csv(D+'test.csv',parse_dates=['datetime'])
al=pd.concat([tr,te],ignore_index=True).sort_values('datetime')
g=al.set_index('datetime').asfreq('30min')

def curv(s):
    # deviation from linear interp of neighbours (robust to trend & slope)
    return s - (s.shift(1)+s.shift(-1))/2

print("=== curvature distribution (|x - mid(neighbours)|) quantiles ===")
for c in ['air_humidity','air_temperature','co2','pressure','soil_temp_line1','soil_ec_line1','soil_humidity_line2','gdd','daily_max']:
    v=curv(g[c]).abs().dropna()
    q=v.quantile([.5,.75,.9,.95,.97,.99,1.0]).round(3)
    print(f'{c:22s} n={len(v):5d} ' + ' '.join(f'{k*100:g}%={x:9.3f}' for k,x in q.items()))

print("\n=== air_humidity: does the series look spiked? consecutive-diff acf ===")
s=g.air_humidity.dropna()
d=s.diff().dropna()
print('diff autocorr lag1 (spiky noise -> strongly negative):',round(d.autocorr(1),4))
print('raw autocorr lag1:',round(s.autocorr(1),4))
for c in ['air_temperature','co2','pressure','soil_temp_line1','soil_ec_line3','water_volume_line1','gdd']:
    x=g[c].dropna(); dd=x.diff().dropna()
    print(f'  {c:22s} raw_acf1={x.autocorr(1):.4f}  diff_acf1={dd.autocorr(1):.4f}')

print("\n=== implied 'clean' vs 'spike' split via robust local quadratic residual ===")
def robust_resid(s,w=9):
    idx=np.arange(len(s)); out=np.full(len(s),np.nan)
    v=s.values
    for i in range(len(s)):
        lo,hi=max(0,i-w//2),min(len(s),i+w//2+1)
        seg=v[lo:hi].copy(); j=i-lo
        seg[j]=np.nan
        if np.isfinite(seg).sum()>=4: out[i]=v[i]-np.nanmedian(seg)
    return pd.Series(out,index=s.index)
for c in ['air_humidity','air_temperature','co2','pressure']:
    r=robust_resid(g[c])
    a=r.abs().dropna()
    print(f'{c:20s} resid |q50|={a.quantile(.5):.2f} q90={a.quantile(.9):.2f} q95={a.quantile(.95):.2f} q99={a.quantile(.99):.2f} max={a.max():.2f}')
    # bimodality: fraction beyond 4x q75
    thr=4*a.quantile(.75); print(f'      frac beyond 4*q75({thr:.2f}) = {(a>thr).mean():.4f}')

print("\n=== TEST vs TRAIN distribution shift on key drivers ===")
for c in ['air_temperature','co2','pressure','soil_temp_line1','soil_humidity_line1','gdd','ontario_units']:
    print(f'{c:22s} train med={tr[c].median():9.2f} test med={te[c].median():9.2f} | train q10-q90 {tr[c].quantile(.1):.1f}-{tr[c].quantile(.9):.1f} | test {te[c].quantile(.1):.1f}-{te[c].quantile(.9):.1f}')
