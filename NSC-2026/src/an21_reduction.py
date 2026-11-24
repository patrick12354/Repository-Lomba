"""What is daily_max_reduction? Scan every day-anchored statistic of every raw column."""
import numpy as np, pandas as pd, sys
sys.path[:0] = ['.','src']
import final_pipeline as fp
from sklearn.linear_model import LinearRegression

g = fp.load_grid(); c = fp.clean_exog(g)
raw = pd.read_csv('Dataset/train.csv', parse_dates=['datetime']).set_index('datetime').sort_index()
k = (c.index - pd.Timedelta(hours=22)).normalize()
blk = c.groupby(k)[['daily_max','ontario_units','daily_mean_temperature','daily_max_reduction',
                    'daily_max_above_Tbase','standard_day_degree']].median()
x = blk.daily_max - 10.0
blk['Tmin_chu'] = (2*blk.ontario_units - (3.33*x - 0.084*x**2))/1.8 + 4.4
n = c.groupby(k).size()
blk = blk[n >= 46]

# every day-anchored stat of every numeric exogenous column, plus RH where known
src = c.drop(columns=[cc for cc in c.columns if cc in
      ('daily_max','ontario_units','daily_mean_temperature','daily_max_reduction',
       'daily_max_above_Tbase','standard_day_degree','gdd')]).select_dtypes('number')
src = src.drop(columns=["air_humidity"], errors="ignore").join(raw[["air_humidity"]], how="left")
kk = (src.index - pd.Timedelta(hours=22)).normalize()
stats = {}
for col in src.columns:
    gg = src.groupby(kk)[col]
    for nm, s in (('min', gg.min()), ('max', gg.max()), ('mean', gg.mean()),
                  ('rng', gg.max()-gg.min())):
        stats[f'{col}_{nm}'] = s
S = pd.DataFrame(stats).reindex(blk.index)

y = blk.daily_max_reduction
rows = []
for col in S.columns:
    v = S[col]; m = v.notna() & y.notna()
    if m.sum() < 30 or v[m].std() == 0: continue
    rows.append((col, np.corrcoef(v[m], y[m])[0,1], m.sum()))
rows.sort(key=lambda t: -abs(t[1]))
print("top |corr| with daily_max_reduction (22h-day level, n=%d days):" % len(blk))
for cn, r, nm in rows[:18]: print("  %-34s %+.4f  (n=%d)" % (cn, r, nm))

# partial: after temperature triple
base = blk[['daily_max','Tmin_chu','daily_mean_temperature']]
mb = base.notna().all(1) & y.notna()
res_y = y[mb] - LinearRegression().fit(base[mb], y[mb]).predict(base[mb])
print("\npartial corr with daily_max_reduction | (daily_max, Tmin_chu, daily_mean):")
out=[]
for col in S.columns:
    v = S[col]; m = mb & v.notna()
    if m.sum() < 30 or v[m].std()==0: continue
    rv = v[m] - LinearRegression().fit(base[m], v[m]).predict(base[m])
    ry = y[m] - LinearRegression().fit(base[m], y[m]).predict(base[m])
    if rv.std()==0: continue
    out.append((col, np.corrcoef(rv, ry)[0,1], m.sum()))
out.sort(key=lambda t:-abs(t[1]))
for cn, r, nm in out[:15]: print("  %-34s %+.4f  (n=%d)" % (cn, r, nm))
