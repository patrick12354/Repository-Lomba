"""Row-level value of the CHU-recovered day minimum, against the blocks already shipped."""
import numpy as np, pandas as pd, sys
sys.path[:0] = ['.', 'src']
import final_pipeline as fp

g = fp.load_grid(); c = fp.clean_exog(g)
F = fp.make_features(g)
y = g['air_humidity']
istr = y.notna()

def chu_block(c):
    k = (c.index - pd.Timedelta(hours=22)).normalize()
    b = c.groupby(k)[['daily_max','ontario_units','daily_mean_temperature']].median()
    x = b.daily_max - 10.0
    b['Tmin_chu'] = (2*b.ontario_units - (3.33*x - 0.084*x**2))/1.8 + 4.4
    m = b.reindex(k)
    m.index = c.index
    T = c['air_temperature']
    d = {}
    d['chu_Tmin']   = m.Tmin_chu
    d['chu_Tmax']   = m.daily_max
    d['chu_rng']    = m.daily_max - m.Tmin_chu
    d['chu_rh']     = 100*fp.es(m.Tmin_chu.values)/fp.es(T.values)
    d['chu_T_minus_min'] = T - m.Tmin_chu
    d['chu_frac']   = (T - m.Tmin_chu) / (m.daily_max - m.Tmin_chu).replace(0, np.nan)
    return pd.DataFrame(d, index=c.index)

C = chu_block(c)
print("row-level |corr| with air_humidity (train rows):")
cand = {**{k: C[k] for k in C}, 
        'rh_tmin18': F['rh_tmin18'], 'rh_tmin48': F['rh_tmin48'], 'rh_q18': F['rh_q18'],
        'T_min18': F['T_min18'], 'T_min48': F['T_min48'], 'T': F['T'],
        'T_rng48': F['T_rng48'], 'daily_max': F['daily_max'], 'ontario_units': F['ontario_units']}
rows=[]
for k,v in cand.items():
    m = istr & v.notna()
    rows.append((k, np.corrcoef(v[m], y[m])[0,1]))
for k,r in sorted(rows, key=lambda t:-abs(t[1])): print("  %-18s %+.4f" % (k,r))

print("\ncorrelation of chu_Tmin with the existing minima:")
for k in ['T_min18','T_min48','T_min96','air_temperature_q18','air_temperature_q48']:
    m = C.chu_Tmin.notna() & F[k].notna()
    print("  chu_Tmin vs %-22s %+.4f" % (k, np.corrcoef(C.chu_Tmin[m], F[k][m])[0,1]))

# does chu_Tmin add to a regression that already has the shipped minima?
from sklearn.linear_model import LinearRegression
base = F[['T_min18','T_min48','T_min96','air_temperature_q18','air_temperature_q48','T']]
m = istr & base.notna().all(1) & C.chu_Tmin.notna()
r = y[m] - LinearRegression().fit(base[m], y[m]).predict(base[m])
print("\npartial corr( chu_Tmin , RH | shipped minima+T ) = %+.4f"
      % np.corrcoef(C.chu_Tmin[m] - LinearRegression().fit(base[m], C.chu_Tmin[m]).predict(base[m]), r)[0,1])
print("partial corr( chu_rh   , RH | shipped minima+T ) = %+.4f"
      % np.corrcoef(C.chu_rh[m] - LinearRegression().fit(base[m], C.chu_rh[m]).predict(base[m]), r)[0,1])

# support audit, section 19.2 bar
te = ~istr
lo, hi = C[istr].quantile(.01), C[istr].quantile(.99)
def cov(S): return (((S>=lo)&(S<=hi))|S.isna()).mean()
d = pd.DataFrame({'all_test': cov(C[te]), 'public': cov(C[te].iloc[:220]), 'private': cov(C[te].iloc[220:])})
print("\nsection 19.2 support audit of the new block (bar 0.916):")
print(d.round(3).to_string())
