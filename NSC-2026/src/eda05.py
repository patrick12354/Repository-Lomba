import pandas as pd, numpy as np
pd.set_option('display.width',250)
D='Dataset/'
tr=pd.read_csv(D+'train.csv',parse_dates=['datetime'])
te=pd.read_csv(D+'test.csv',parse_dates=['datetime'])
al=pd.concat([tr,te],ignore_index=True).sort_values('datetime')
g=al.set_index('datetime').asfreq('30min')

def despike(s,k=6.0,w=7):
    med=s.rolling(w,center=True,min_periods=3).median()
    dev=(s-med).abs()
    scale=dev.rolling(289,center=True,min_periods=48).quantile(.75)*2.5
    bad=dev>np.maximum(k*scale,1e-9)
    return s.mask(bad), bad

T,badT=despike(g.air_temperature)
print('air_temperature despiked:',badT.sum(),'pts =',round(badT.sum()/g.air_temperature.notna().sum(),4))
print('T clean range',round(T.min(),2),round(T.max(),2))

RH=g.air_humidity
def es(t): return 6.112*np.exp(17.67*t/(t+243.5))
Ti=T.interpolate('time',limit=6).ffill().bfill()
e=RH/100*es(Ti)
Td=243.5*np.log(e/6.112)/(17.67-np.log(e/6.112))
Td=Td.where(RH.notna())
print('\n=== dewpoint (from clean T + RH) ===')
print(Td.describe().round(2))
print('Td autocorr: lag1',round(Td.autocorr(1),4),' lag2',round(Td.autocorr(2),4),' lag48',round(Td.autocorr(48),4))
print('Td std',round(Td.std(),3),' vs RH std',round(RH.std(),3),' vs T std',round(Ti.std(),3))
print('Td curvature q50/q95/q99:',Td.pipe(lambda s:(s-(s.shift(1)+s.shift(-1))/2).abs()).quantile([.5,.95,.99]).round(3).tolist())
print('Td hour-of-day amplitude:')
h=Td.groupby(Td.index.hour).mean()
print(h.round(2).to_string())
print('Td daily-mean range over season:', Td.resample('D').mean().min().round(2),'->',Td.resample('D').mean().max().round(2))

print("\n=== how well does RH = f(T, Td_slow) reconstruct? ===")
for win in [1,3,6,12,24,48]:
    Tds=Td.rolling(win,center=True,min_periods=1).mean()
    rec=100*es(Tds)/es(Ti)
    err=(RH-rec).dropna()
    print(f'  Td smoothed over {win:3d} steps ({win/2:5.1f}h): RMSE={np.sqrt((err**2).mean()):.3f}')
# persistence-style: Td from previous day same hour
Tds=Td.shift(48)
rec=100*es(Tds)/es(Ti); err=(RH-rec).dropna()
print(f'  Td from 24h earlier             : RMSE={np.sqrt((err**2).mean()):.3f}')
Tds=Td.rolling(48,min_periods=6).mean().shift(1)
rec=100*es(Tds)/es(Ti); err=(RH-rec).dropna()
print(f'  Td = trailing 24h mean (shift 1): RMSE={np.sqrt((err**2).mean()):.3f}')
print("\n baseline for scale: predict RH by hour-of-day mean ->",
      round(np.sqrt(((RH-RH.groupby(RH.index.hour).transform('mean'))**2).mean()),3))
print(" predict RH by global mean ->",round(RH.std(),3))
