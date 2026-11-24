"""Precision check of the CHU inversion against the pipeline's own cleaned temperature,
and coverage of the new columns on train / public / private."""
import numpy as np, pandas as pd, sys
sys.path[:0] = ['.', 'src']
import final_pipeline as fp

g = fp.load_grid()
c = fp.clean_exog(g)
tr = pd.read_csv('Dataset/train.csv', parse_dates=['datetime']).set_index('datetime').sort_index()

k = (c.index - pd.Timedelta(hours=22)).normalize()
blk = c.groupby(k)[['daily_max','ontario_units','daily_mean_temperature','daily_max_reduction']].median()
x = blk.daily_max - 10.0
Ymax = 3.33*x - 0.084*x**2
blk['Tmin_chu'] = (2*blk.ontario_units - Ymax)/1.8 + 4.4

obs = c.groupby(k).agg(Tmin=('air_temperature','min'), Tmax=('air_temperature','max'),
                       Tmean=('air_temperature','mean'), n=('air_temperature','size'))
J = blk.join(obs)
full = J[J.n >= 46]
istr = full.index <= tr.index.max()
print("full 22h-days: %d  (train %d, test %d)" % (len(full), istr.sum(), (~istr).sum()))

for nm, S in (('all', full), ('train-side', full[istr]), ('test-side', full[~istr])):
    d1 = S.Tmin_chu - S.Tmin; d2 = S.daily_max - S.Tmax; d3 = S.daily_mean_temperature - S.Tmean
    print("\n[%s]  n=%d" % (nm, len(S)))
    print("  Tmin_chu  - cleaned day Tmin : mean %+.3f  sd %.3f  |q95| %.3f  corr %+.5f"
          % (d1.mean(), d1.std(), d1.abs().quantile(.95), np.corrcoef(S.Tmin_chu,S.Tmin)[0,1]))
    print("  daily_max - cleaned day Tmax : mean %+.3f  sd %.3f  |q95| %.3f  corr %+.5f"
          % (d2.mean(), d2.std(), d2.abs().quantile(.95), np.corrcoef(S.daily_max,S.Tmax)[0,1]))
    print("  dailymean - cleaned day Tmean: mean %+.3f  sd %.3f  |q95| %.3f  corr %+.5f"
          % (d3.mean(), d3.std(), d3.abs().quantile(.95), np.corrcoef(S.daily_mean_temperature,S.Tmean)[0,1]))

# where does the residual live?  worst days
w = (full.Tmin_chu - full.Tmin).abs().sort_values(ascending=False).head(6)
print("\nworst |Tmin_chu - Tmin| days:")
print(full.loc[w.index, ['daily_max','Tmax','Tmin_chu','Tmin','n']].round(2).to_string())

# what is daily_max_reduction?
from sklearn.linear_model import LinearRegression
Z = full[['daily_max','Tmin_chu','daily_mean_temperature']].values
y = full.daily_max_reduction.values
print("\ndaily_max_reduction ~ (daily_max, Tmin_chu, daily_mean): R2 = %.4f"
      % LinearRegression().fit(Z,y).score(Z,y))
print("  corr with day index (drift): %+.3f" % np.corrcoef(np.arange(len(full)), y)[0,1])
