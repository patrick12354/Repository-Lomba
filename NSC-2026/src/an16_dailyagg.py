"""Can any daily-aggregate column be explained by temperature alone? If not, what is
the residual made of -- and does it know about humidity?"""
import numpy as np, pandas as pd
from sklearn.linear_model import LinearRegression

tr = pd.read_csv('Dataset/train.csv', parse_dates=['datetime'])
te = pd.read_csv('Dataset/test.csv',  parse_dates=['datetime'])
tr['d'] = tr.datetime.dt.date; te['d'] = te.datetime.dt.date

DAILY = ['gdd','standard_day_degree','daily_mean_temperature','daily_max_above_Tbase',
         'daily_max','daily_max_reduction','ontario_units']

# how constant is each within a day?
print("within-day spread (train), std of column within a calendar day, mean over days:")
for c in DAILY:
    g = tr.groupby('d')[c]
    print("  %-26s within-day sd %.4f   overall sd %.3f  n_missing %d"
          % (c, g.std().mean(), tr[c].std(), tr[c].isna().sum()))

# daily table: one row per day, daily aggregates + observed daily temp/RH stats
dt = tr.groupby('d').agg(**{c: (c,'median') for c in DAILY})
obs = tr.groupby('d').agg(Tmin=('air_temperature','min'), Tmax=('air_temperature','max'),
                          Tmean=('air_temperature','mean'),
                          RHmin=('air_humidity','min'), RHmax=('air_humidity','max'),
                          RHmean=('air_humidity','mean'), n=('air_temperature','size'))
D = dt.join(obs)
D = D[D.n >= 40].dropna(subset=['Tmax','RHmean'])
print("\ncomplete days:", len(D))

print("\ncorrelation of each daily aggregate with observed daily RH stats:")
print(D[DAILY].corrwith(D.RHmean).rename('r_RHmean').to_frame()
      .join(D[DAILY].corrwith(D.RHmin).rename('r_RHmin'))
      .join(D[DAILY].corrwith(D.Tmax).rename('r_Tmax')).round(3).to_string())

# key test: regress each aggregate on temperature-only daily stats; does the residual
# correlate with RH?  If an aggregate uses humidity, the residual will.
Xt = D[['Tmin','Tmax','Tmean']].values
print("\nresidual after regressing on (Tmin,Tmax,Tmean):")
for c in DAILY:
    y = D[c].values
    m = np.isfinite(y)
    if m.sum() < 20: continue
    f = LinearRegression().fit(Xt[m], y[m])
    r = y[m] - f.predict(Xt[m])
    R2 = 1 - r.var()/y[m].var()
    rc = np.corrcoef(r, D.RHmean.values[m])[0,1]
    rc2 = np.corrcoef(r, D.RHmin.values[m])[0,1]
    print("  %-26s R2_T=%.4f  resid_sd=%.4f  corr(resid,RHmean)=%+.3f  corr(resid,RHmin)=%+.3f"
          % (c, R2, r.std(), rc, rc2))
