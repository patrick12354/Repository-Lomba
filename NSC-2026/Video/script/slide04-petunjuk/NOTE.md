# NOTE — slide 4

`assets/tmin.js` dibuat dari root repo dengan:

```python
import pandas as pd, json
d = pd.concat([pd.read_csv('Dataset/train.csv', parse_dates=['datetime']), pd.read_csv('Dataset/test.csv', parse_dates=['datetime'])])
d['day'] = d.datetime.dt.date
g = d.groupby('day')[['daily_mean_temperature', 'daily_max', 'ontario_units']].median().dropna()
tmax = g.daily_max
t1 = 2 * g.daily_mean_temperature - tmax                      # jalur 1
ymax = 3.33 * (tmax - 10) - 0.084 * (tmax - 10) ** 2
t2 = (2 * g.ontario_units - ymax) / 1.8 + 4.4                 # jalur 2 (Ontario CHU)
```

SD selisih versi median harian ini 0,049 °C; layar memakai 0,047 °C dari laporan.
