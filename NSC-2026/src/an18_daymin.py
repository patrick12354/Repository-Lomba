"""The daily block is constant over a 22:00-anchored day plus jitter. Ontario CHU uses
Tmax and Tmin; we have CHU and Tmax, so Tmin falls out. Does it match the observed
daily minimum -- and is it the CLEAN minimum or the spiked one?"""
import numpy as np, pandas as pd

DAILY = ['standard_day_degree','daily_mean_temperature','daily_max_above_Tbase',
         'daily_max','daily_max_reduction','ontario_units']

def load(p):
    f = pd.read_csv(p, parse_dates=['datetime']).set_index('datetime').sort_index()
    return f

tr, te = load('Dataset/train.csv'), load('Dataset/test.csv')
allf = pd.concat([tr.drop(columns=['air_humidity']), te])
# 22:00-anchored day label
def daykey(idx): return (idx - pd.Timedelta(hours=22)).normalize()

for nm, f in (('train', tr), ('test', te)):
    k = daykey(f.index)
    n = f.groupby(k)[DAILY].nunique().mean()
    sd = f.groupby(k)[DAILY].std().mean()
    print(f"[{nm}] within-22h-day sd of each daily column:")
    print("   " + sd.round(4).to_dict().__str__())

k = daykey(tr.index)
blk = tr.groupby(k)[DAILY].median()
obs = tr.groupby(k).agg(Tmin=('air_temperature','min'), Tmax=('air_temperature','max'),
                        Tmean=('air_temperature','mean'), n=('air_temperature','size'),
                        nn=('air_temperature','count'),
                        RHmean=('air_humidity','mean'))
J = blk.join(obs)
J = J[J.n >= 44]
print("\ncomplete 22h-days:", len(J))

Tmax = J.daily_max
x = Tmax - 10.0
Ymax = 3.33*x - 0.084*x**2
Tmin_chu = (2*J.ontario_units - Ymax)/1.8 + 4.4
J['Tmin_chu'] = Tmin_chu

print("\n  corr(daily_max, observed day Tmax)   : %+.4f   mean diff %+.3f sd %.3f"
      % (np.corrcoef(J.daily_max, J.Tmax)[0,1], (J.daily_max-J.Tmax).mean(), (J.daily_max-J.Tmax).std()))
print("  corr(daily_mean, observed day Tmean) : %+.4f   mean diff %+.3f sd %.3f"
      % (np.corrcoef(J.daily_mean_temperature, J.Tmean)[0,1],
         (J.daily_mean_temperature-J.Tmean).mean(), (J.daily_mean_temperature-J.Tmean).std()))
print("  corr(Tmin_chu, observed day Tmin)    : %+.4f   mean diff %+.3f sd %.3f"
      % (np.corrcoef(J.Tmin_chu, J.Tmin)[0,1], (J.Tmin_chu-J.Tmin).mean(), (J.Tmin_chu-J.Tmin).std()))
print("\n  corr(daily_max_reduction, 0.084*x^2) : %+.4f" % np.corrcoef(J.daily_max_reduction, 0.084*x**2)[0,1])
print("  corr(daily_max_reduction, Tmin_chu)  : %+.4f" % np.corrcoef(J.daily_max_reduction, J.Tmin_chu)[0,1])
print("  corr(daily_max_reduction, obs Tmin)  : %+.4f" % np.corrcoef(J.daily_max_reduction, J.Tmin)[0,1])
print("  daily_max - daily_max_reduction vs Tmin: corr %+.4f  mean diff %+.3f"
      % (np.corrcoef(J.daily_max-J.daily_max_reduction, J.Tmin)[0,1],
         (J.daily_max-J.daily_max_reduction-J.Tmin).mean()))

def es(t): return 6.112*np.exp(17.67*t/(t+243.5))
print("\n  dewpoint-proxy RH from day Tmin, corr with day-mean RH:")
print("    from CHU-recovered Tmin : %+.4f" % np.corrcoef(100*es(J.Tmin_chu)/es(J.Tmean), J.RHmean)[0,1])
print("    from observed  day Tmin : %+.4f" % np.corrcoef(100*es(J.Tmin)/es(J.Tmean), J.RHmean)[0,1])
print(J[['daily_max','Tmax','Tmin_chu','Tmin','daily_max_reduction','ontario_units']].head(12).round(2).to_string())
