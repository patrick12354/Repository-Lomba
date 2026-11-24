"""Invert the Ontario crop-heat-unit block. If the identities hold, the daily columns
carry a SECOND thermometer's Tmax and Tmin -- and Tmin is a dewpoint proxy."""
import numpy as np, pandas as pd

tr = pd.read_csv('Dataset/train.csv', parse_dates=['datetime'])
te = pd.read_csv('Dataset/test.csv',  parse_dates=['datetime'])
D = ['gdd','standard_day_degree','daily_mean_temperature','daily_max_above_Tbase',
     'daily_max','daily_max_reduction','ontario_units']
for f, nm in ((tr,'train'), (te,'test')):
    f['d'] = f.datetime.dt.date
d = tr.groupby('d')[D].median().dropna()
print("days:", len(d), "\n", d.head(4).round(3).to_string(), "\n")

# candidate identities
print("daily_max - daily_max_above_Tbase   :", (d.daily_max - d.daily_max_above_Tbase).describe()[['mean','std','min','max']].round(4).to_dict())
print("daily_max_above_Tbase * 3.33        vs ?")
x = d.daily_max_above_Tbase
print("  daily_max_reduction / x^2         :", (d.daily_max_reduction / x**2).describe()[['mean','std']].round(5).to_dict())
print("  daily_max_reduction / (3.33x - Ymax_guess)")
# Ontario: Ymax = 3.33*(Tmax-10) - 0.084*(Tmax-10)^2
Ymax = 3.33*x - 0.084*x**2
print("  Ymax from formula, corr with ontario_units:", np.corrcoef(Ymax, d.ontario_units)[0,1].round(4))
print("  3.33x - daily_max_reduction, mean/sd:", (3.33*x - d.daily_max_reduction).describe()[['mean','std']].round(3).to_dict())
print("  corr(daily_max_reduction, 0.084x^2) :", np.corrcoef(d.daily_max_reduction, 0.084*x**2)[0,1].round(5))
print("  ratio daily_max_reduction/(0.084x^2):", (d.daily_max_reduction/(0.084*x**2)).describe()[['mean','std']].round(4).to_dict())

# solve Ymin = 2*CHU - Ymax  ->  Tmin = Ymin/1.8 + 4.4
Ymin = 2*d.ontario_units - Ymax
Tmin_ref = Ymin/1.8 + 4.4
print("\nrecovered reference Tmin: ", Tmin_ref.describe().round(3).to_dict())

obs = tr.groupby('d').agg(Tmin=('air_temperature','min'), Tmax=('air_temperature','max'),
                          Tmean=('air_temperature','mean'), RHmean=('air_humidity','mean'),
                          RHmin=('air_humidity','min'), n=('air_temperature','size'))
J = d.join(obs)
J = J[J.n>=40]
print("\ncorr(recovered Tmin_ref, local Tmin) :", np.corrcoef(Tmin_ref[J.index], J.Tmin)[0,1].round(4))
print("corr(daily_max, local Tmax)          :", np.corrcoef(J.daily_max, J.Tmax)[0,1].round(4))
print("corr(daily_mean_temperature, local Tmean):", np.corrcoef(J.daily_mean_temperature, J.Tmean)[0,1].round(4))
print("corr(standard_day_degree, daily_mean_temperature):", np.corrcoef(J.standard_day_degree, J.daily_mean_temperature)[0,1].round(5))
print("diff standard_day_degree - daily_mean_temperature:", (J.standard_day_degree-J.daily_mean_temperature).describe()[['mean','std']].round(4).to_dict())

# the payoff test: a parameter-free RH from the recovered reference Tmin
def es(t): return 6.112*np.exp(17.67*t/(t+243.5))
tref = Tmin_ref[J.index]
print("\ncorr(es(Tmin_ref)/es(local Tmean)*100, RHmean):",
      np.corrcoef(100*es(tref)/es(J.Tmean), J.RHmean)[0,1].round(4))
print("corr(es(local Tmin)/es(local Tmean)*100, RHmean):",
      np.corrcoef(100*es(J.Tmin)/es(J.Tmean), J.RHmean)[0,1].round(4))
print("corr(Tmin_ref, RHmean) %+.4f   corr(local Tmin, RHmean) %+.4f"
      % (np.corrcoef(tref, J.RHmean)[0,1], np.corrcoef(J.Tmin, J.RHmean)[0,1]))
