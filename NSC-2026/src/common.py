"""Shared data loading, cleaning and feature engineering for the NSC 2026 air-humidity task."""
import numpy as np, pandas as pd, json, os, datetime as _dt

D = 'Dataset/'
OUT = 'outputs/'
TARGET = 'air_humidity'

# columns that are cumulative counters -> level is useless / extrapolates in test
CUMUL = ['gdd', 'water_volume_line1', 'water_volume_line2', 'water_volume_line3']
DROP_RAW = ['env_id', 'env_battery']
FAST = ['air_temperature', 'co2', 'pressure']
SOIL = ['soil_ec_line1', 'soil_humidity_line1', 'soil_temp_line1',
        'soil_ec_line2', 'soil_humidity_line2', 'soil_temp_line2',
        'soil_ec_line3', 'soil_humidity_line3', 'soil_temp_line3']
DAILY = ['standard_day_degree', 'daily_mean_temperature', 'daily_max_above_Tbase',
         'daily_max', 'daily_max_reduction', 'ontario_units']


# ---------------------------------------------------------------- physics
def es(t):
    """Saturation vapour pressure (hPa), Magnus/Bolton."""
    return 6.112 * np.exp(17.67 * t / (t + 243.5))


def rh_to_td(rh, t):
    e = np.clip(rh, 1e-3, None) / 100.0 * es(t)
    l = np.log(np.clip(e, 1e-6, None) / 6.112)
    return 243.5 * l / (17.67 - l)


def td_to_rh(td, t):
    return 100.0 * es(td) / es(t)


# ---------------------------------------------------------------- loading
def load_grid():
    """Train+test on one continuous 30-min DatetimeIndex. Exogenous are fully observed
    across the test window (concurrent sensors), so joint cleaning is legitimate."""
    tr = pd.read_csv(D + 'train.csv', parse_dates=['datetime'])
    te = pd.read_csv(D + 'test.csv', parse_dates=['datetime'])
    tr['is_test'] = 0
    te['is_test'] = 1
    te[TARGET] = np.nan
    al = pd.concat([tr, te], ignore_index=True).sort_values('datetime')
    g = al.set_index('datetime').asfreq('30min')
    g['is_test'] = g['is_test'].fillna(-1)          # -1 = slot missing from both files
    return g, tr.datetime.values, te.datetime.values


# ---------------------------------------------------------------- cleaning
def hampel(s, w=7, k=6.0, scale_win=289, min_scale=0.0):
    """Centered Hampel filter. Scale from a long rolling window so a locally quiet
    stretch does not make every wiggle an outlier."""
    med = s.rolling(w, center=True, min_periods=3).median()
    dev = (s - med).abs()
    scale = dev.rolling(scale_win, center=True, min_periods=48).quantile(0.75) * 2.5
    scale = scale.clip(lower=min_scale)
    bad = dev > (k * scale).clip(lower=1e-9)
    return s.mask(bad), bad.fillna(False)


def clean_exog(g, k=6.0, verbose=False):
    """Despike + interpolate every exogenous sensor. Returns cleaned frame."""
    c = g.copy()
    rep = {}
    for col in FAST + SOIL + DAILY:
        s = c[col]
        cl, bad = hampel(s, w=7, k=k)
        rep[col] = int(bad.sum())
        c[col] = cl.interpolate('time', limit_direction='both')
    for col in CUMUL:
        s = c[col]
        # cumulative: kill non-monotone dips as well as spikes
        cl, bad = hampel(s, w=9, k=k)
        cl = cl.interpolate('time', limit_direction='both')
        cm = cl.cummax()
        c[col] = cm
        c[col + '_rate'] = cm.diff().clip(lower=0).rolling(48, min_periods=1).sum()
        rep[col] = int(bad.sum())
    if verbose:
        print('despiked:', {k_: v for k_, v in rep.items() if v})
    return c


# ---------------------------------------------------------------- features
def build_features(c, use_day=False):
    """All features are computable for the test window because every exogenous sensor
    is observed there. Centered windows are therefore NOT leakage."""
    f = pd.DataFrame(index=c.index)
    idx = c.index

    T = c['air_temperature']
    f['T'] = T
    f['esT'] = es(T)
    f['log_esT'] = np.log(es(T))

    # time of day (3 harmonics) -- the diurnal cycle is the dominant structure
    tod = idx.hour + idx.minute / 60.0
    for h in (1, 2, 3):
        f[f'sin{h}'] = np.sin(2 * np.pi * h * tod / 24)
        f[f'cos{h}'] = np.cos(2 * np.pi * h * tod / 24)
    f['tod'] = tod

    key = FAST + SOIL
    for col in key:
        s = c[col]
        f[col] = s
        for w, nm in ((3, '1h'), (13, '6h'), (49, '24h')):
            m = s.rolling(w, center=True, min_periods=2).mean()
            f[f'{col}_c{nm}'] = m
            f[f'{col}_a{nm}'] = s - m
        f[f'{col}_sd6h'] = s.rolling(13, center=True, min_periods=3).std()

    # short leads/lags for the fast, physically-coupled sensors
    for col in FAST:
        s = c[col]
        for l in (-4, -2, -1, 1, 2, 4):
            f[f'{col}_s{l}'] = s.shift(l)
        f[f'{col}_slope'] = (s.shift(-2) - s.shift(2)) / 4.0

    for col in DAILY:
        f[col] = c[col]
    for col in CUMUL:
        f[col + '_rate'] = c[col + '_rate']

    # cross terms with strong physical grounding
    f['T_minus_soilT1'] = c['air_temperature'] - c['soil_temp_line1']
    f['T_minus_soilT2'] = c['air_temperature'] - c['soil_temp_line2']
    f['T_minus_soilT3'] = c['air_temperature'] - c['soil_temp_line3']
    f['T_minus_dailymean'] = c['air_temperature'] - c['daily_mean_temperature']
    f['T_over_dailymax'] = c['air_temperature'] / c['daily_max'].replace(0, np.nan)
    f['co2_x_T'] = c['co2'] * c['air_temperature']
    f['esT_ratio_daily'] = es(T) / es(c['daily_mean_temperature'])

    if use_day:
        f['day_idx'] = (idx - idx[0]).total_seconds() / 86400.0

    return f.replace([np.inf, -np.inf], np.nan)


# ---------------------------------------------------------------- bookkeeping
def log_experiment(rec, path=OUT + 'experiments.jsonl'):
    rec = dict(rec)
    rec.setdefault('ts', _dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    with open(path, 'a', encoding='utf-8') as fh:
        fh.write(json.dumps(rec, ensure_ascii=False, default=float) + '\n')


def rmse(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    m = np.isfinite(a) & np.isfinite(b)
    return float(np.sqrt(np.mean((a[m] - b[m]) ** 2)))


# ---------------------------------------------------------------- feature sets
def feature_set(F, name='nosoil'):
    """Named column subsets. `nosoil` drops every soil probe column and the cumulative
    rate columns: the soil probes stop fluctuating in the test window (irrigation halts),
    so their rolling stats have almost no training support there."""
    cols = list(F.columns)
    if name == 'full':
        return cols
    if name == 'nosoil':
        return [c for c in cols if not c.startswith('soil_') and not c.endswith('_rate')]
    if name == 'nosoil_keepcross':
        return [c for c in cols if not c.startswith('soil_') and not c.endswith('_rate')]
    if name == 'nosoil_nocross':
        return [c for c in cols if not c.startswith('soil_') and not c.endswith('_rate')
                and not c.startswith('T_minus_soilT')]
    raise ValueError(name)


# ---------------------------------------------------------------- cleaning v2
def _rscale(v):
    v = np.asarray(v, float); v = v[np.isfinite(v)]
    if len(v) < 8: return np.nan
    return 1.4826 * np.median(np.abs(v - np.median(v))) + 1e-9


def curvature_flag(s, k=5.0, passes=2):
    """Flag isolated spikes via c_t = x_t - (x_{t-1}+x_{t+1})/2.

    A linear ramp gives c = 0, so genuine fast transitions survive; only single-point
    excursions light up. Iterated: once the worst spikes are removed the scale estimate
    tightens and smaller ones become visible."""
    work = s.copy()
    bad = pd.Series(False, index=s.index)
    for _ in range(passes):
        c = work - (work.shift(1) + work.shift(-1)) / 2
        sg = _rscale(c.values)
        if not np.isfinite(sg): break
        new = (c.abs() > k * sg).fillna(False) & ~bad
        if not new.any(): break
        bad |= new
        work = work.mask(bad)
    return bad


def clean_exog2(g, k=5.0, passes=2, method='time', detector='curv', hampel_k=6.0):
    """Despike + impute every exogenous sensor over the joint train+test grid."""
    c = g.copy()
    report = {}
    for col in FAST + SOIL + DAILY:
        s = c[col]
        if detector == 'curv':
            bad = curvature_flag(s, k=k, passes=passes)
        elif detector == 'hampel_mad':
            med = s.rolling(7, center=True, min_periods=3).median()
            dev = s - med
            bad = (dev.abs() > k * _rscale(dev.values)).fillna(False)
        else:
            _, bad = hampel(s, w=7, k=hampel_k)
        report[col] = int(bad.sum())
        cl = s.mask(bad)
        if method == 'pchip':
            cl = cl.interpolate('pchip', limit_direction='both')
        else:
            cl = cl.interpolate('time', limit_direction='both')
        c[col] = cl.ffill().bfill()
    for col in CUMUL:
        s = c[col]
        bad = curvature_flag(s, k=max(k, 6.0), passes=1)
        cl = s.mask(bad).interpolate('time', limit_direction='both').ffill().bfill().cummax()
        c[col] = cl
        c[col + '_rate'] = cl.diff().clip(lower=0).rolling(48, min_periods=1).sum()
    c.attrs['despike_report'] = report
    return c
