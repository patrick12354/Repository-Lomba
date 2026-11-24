"""Error analysis on the v5 OOF: where does the remaining MSE live?"""
import warnings; warnings.filterwarnings('ignore')
import sys, numpy as np, pandas as pd
sys.path.insert(0,'src'); from common import *

O=pd.read_csv('outputs/oof_long_v5_final.csv',parse_dates=['dt'])
w={'hbt':0.6579,'cat':0.2113,'ridge':0.0625,'enet':0.0683}
O['p']=sum(O[m]*v for m,v in w.items())
O['e']=O.p-O.y; O['se']=O.e**2

print('=== overall ==='); print(f'pooled RMSE {np.sqrt(O.se.mean()):.4f}  bias {O.e.mean():+.3f}  n {len(O)}')

print('\n=== MSE concentration (pooled) ===')
s=O.se.sort_values(ascending=False).values; tot=s.sum()
for q in (0.01,0.02,0.05,0.10,0.20,0.50):
    k=int(len(s)*q); print(f'  worst {q*100:5.1f}% of rows carry {s[:k].sum()/tot*100:5.1f}% of MSE')

print('\n=== by hour of day ===')
O['h']=O.dt.dt.hour
h=O.groupby('h').agg(rmse=('se',lambda x: np.sqrt(x.mean())),bias=('e','mean'),n=('e','size'))
print(h.round(2).to_string())

print('\n=== by true-RH decile ===')
O['dec']=pd.qcut(O.y,10,labels=False)
d=O.groupby('dec').agg(y=('y','mean'),p=('p','mean'),rmse=('se',lambda x:np.sqrt(x.mean())),bias=('e','mean'))
print(d.round(2).to_string())

print('\n=== per fold, per validation day (worst days) ===')
O['day']=O.dt.dt.date
dd=O.groupby(['fold','day']).agg(rmse=('se',lambda x:np.sqrt(x.mean())),bias=('e','mean'),n=('e','size'))
print(dd.sort_values('rmse',ascending=False).head(15).round(2).to_string())
print('\n  day-RMSE distribution:', dd.rmse.describe([.25,.5,.75,.9,.95]).round(2).to_dict())

print('\n=== error vs horizon (days into the validation window) ===')
O['hz']=O.groupby('fold').dt.transform(lambda s:(s-s.min()).dt.total_seconds()/86400)
O['hzb']=(O.hz//2).astype(int)
print(O.groupby('hzb').agg(rmse=('se',lambda x:np.sqrt(x.mean())),bias=('e','mean'),n=('e','size')).round(2).to_string())

print('\n=== decomposition: slow (24h mean) vs fast error ===')
for f,g in O.groupby('fold'):
    g=g.sort_values('dt')
    es=g.e.rolling(48,center=True,min_periods=12).mean()
    print(f'  fold {f}: total {np.sqrt((g.e**2).mean()):5.2f}  slow-part {np.sqrt((es**2).mean()):5.2f}  fast-part {np.sqrt(((g.e-es)**2).mean()):5.2f}')
gg=O.sort_values(['fold','dt']); es=gg.groupby('fold').e.transform(lambda s:s.rolling(48,center=True,min_periods=12).mean())
print(f'  POOLED: total {np.sqrt((gg.e**2).mean()):.3f}  slow {np.sqrt((es**2).mean()):.3f}  fast {np.sqrt(((gg.e-es)**2).mean()):.3f}')
print('  -> slow^2 share of MSE: %.1f%%'%(100*(es**2).mean()/(gg.e**2).mean()))
