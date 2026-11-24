"""Session-3 candidate blocks, layered on top of featx.build_v7.

Everything here is a *feature*, never a target transform or a hard anchor (see the
standing decisions in progress.md). Centered windows stay legitimate because the
exogenous sensors are fully observed across the test window.
"""
import sys, os, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
from common import *
from featx import build_v7, tmin_block, tend_block, ordstat_block, TMIN_WINS_V7, CO2_WINS_V7


def nightmin_block(c, night=(0, 6), lags=(0, 1, 2)):
    """Minimum temperature over the night hours of a calendar day, rather than a
    centered rolling minimum that can straddle two different nights.

    The dewpoint-stalling argument is specifically about overnight cooling, so a
    night-scoped minimum is the literal form of that physics. Lagged copies let the
    model see whether the air mass is drying or moistening between successive nights --
    a centered minimum averages that direction away.
    """
    T = c['air_temperature']
    idx = c.index
    hr = idx.hour + idx.minute / 60.0
    is_night = (hr >= night[0]) & (hr < night[1])
    day = pd.Series(idx.normalize(), index=idx)
    per_day = T.where(is_night).groupby(day).min()
    d = {}
    for L in lags:
        v = per_day.shift(L).reindex(day.values).values
        d[f'nmin_L{L}'] = v
        d[f'rh_nmin_L{L}'] = 100 * es(v) / es(T.values)
    d['nmin_trend'] = d['nmin_L0'] - d['nmin_L2']
    d['T_minus_nmin'] = T.values - d['nmin_L0']
    return pd.DataFrame(d, index=idx)


def nextmin_block(c, wins=(48, 96)):
    """Split each centered window into its trailing and leading halves. The centered
    minimum gives the air-mass level; the gap between halves gives its direction."""
    T = c['air_temperature']
    idx = c.index
    d = {}
    for hrs in wins:
        w = int(hrs * 2)
        past = T.rolling(w, min_periods=6).min()
        fut = T.iloc[::-1].rolling(w, min_periods=6).min().iloc[::-1]
        d[f'T_minpast{hrs}'] = past
        d[f'T_minfut{hrs}'] = fut
        d[f'T_mindir{hrs}'] = fut - past
    return pd.DataFrame(d, index=idx)


def qstat_block(c, wins=TMIN_WINS_V7, q=0.05):
    """Low/high quantiles instead of hard min/max: same information, less sensitive to
    a single surviving glitch."""
    T = c['air_temperature']
    idx = c.index
    d = {}
    for hrs in wins:
        w = int(hrs * 2) + 1
        lo = T.rolling(w, center=True, min_periods=6).quantile(q)
        hi = T.rolling(w, center=True, min_periods=6).quantile(1 - q)
        d[f'T_q{int(q * 100)}_{hrs}'] = lo
        d[f'T_qrng{hrs}'] = hi - lo
        d[f'rh_q{hrs}'] = 100 * es(lo.values) / es(T.values)
    return pd.DataFrame(d, index=idx)


def build(c, blocks=()):
    F = build_v7(c)
    add = []
    if 'night' in blocks: add.append(nightmin_block(c))
    if 'dir' in blocks:   add.append(nextmin_block(c))
    if 'q' in blocks:     add.append(qstat_block(c))
    if add:
        F = pd.concat([F] + add, axis=1)
    return F.replace([np.inf, -np.inf], np.nan)
