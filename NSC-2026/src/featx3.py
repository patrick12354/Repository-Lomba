"""Fast-component blocks. The v8 residual splits 40% slow / 60% fast, so the
within-day error is now the larger target -- the reverse of the v5 diagnosis that
motivated the tmin block."""
import sys, os, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
from common import *


def farlag_block(c, cols=('air_temperature', 'co2', 'pressure'), lags=(6, 12)):
    """v8 stops at +/-2 h. Ventilation and cloud episodes last longer than that, so the
    model cannot currently see the shoulders of an event it is sitting inside."""
    d = {}
    for col in cols:
        s = c[col]
        for L in lags:
            d[f'{col}_f{L}'] = s.shift(L)
            d[f'{col}_b{L}'] = s.shift(-L)
            d[f'{col}_d{L}'] = s.shift(-L) - s.shift(L)
    return pd.DataFrame(d, index=c.index)


def accel_block(c, cols=('air_temperature', 'co2')):
    """Curvature of the sensor trace: a ventilation event is a kink, not a ramp."""
    d = {}
    for col in cols:
        s = c[col]
        for w in (2, 4, 8):
            d[f'{col}_acc{w}'] = s.shift(-w) + s.shift(w) - 2 * s
    return pd.DataFrame(d, index=c.index)


def phase_block(c, wins=(24, 48)):
    """Where the current moment sits inside the local thermal cycle, expressed without
    reference to clock time. Percentile rank is invariant to the day's level and
    amplitude, so it transfers across the regime shift better than raw temperature."""
    T = c['air_temperature']
    idx = c.index
    d = {}
    for hrs in wins:
        w = int(hrs * 2) + 1
        r = T.rolling(w, center=True, min_periods=6)
        lo = r.min(); rng = (r.max() - lo).replace(0, np.nan)
        d[f'T_pos{hrs}'] = (T - lo) / rng
        d[f'T_rank{hrs}'] = T.rolling(w, center=True, min_periods=6).apply(
            lambda a: (a < a[len(a) // 2]).mean(), raw=True)
    # hours since the coldest point of the surrounding 24 h
    w = 49
    argmin = T.rolling(w, center=True, min_periods=6).apply(lambda a: float(np.argmin(a)), raw=True)
    d['hrs_since_tmin'] = (w // 2 - argmin) / 2.0
    return pd.DataFrame(d, index=idx)


def fastphys_block(c, wins=(6, 12)):
    """The dewpoint-proxy idea applied at short range: es(T_q05_6h)/es(T) says how close
    the air is to saturating given only the last few hours."""
    T = c['air_temperature']
    d = {}
    for hrs in wins:
        w = int(hrs * 2) + 1
        lo = T.rolling(w, center=True, min_periods=4).quantile(0.05)
        d[f'rh_fast{hrs}'] = 100 * es(lo.values) / es(T.values)
        d[f'T_minus_fast{hrs}'] = T - lo
    return pd.DataFrame(d, index=c.index)
