"""Whole-day temperature statistics recovered from the agronomic daily block.

The seven `daily_*` / `ontario_units` columns are not per-row measurements. They are
constant over a day that runs 22:00 -> 22:00, with roughly 0.08 C of jitter added on
top, and they are reported on EVERY row of that day -- so at 02:00 the file already
states what that day's maximum will be. Two of them are exact affine copies of others:

    daily_max - daily_max_above_Tbase   = 10.00 (sd 0.03)
    daily_mean_temperature - standard_day_degree = 10.00 (sd 0.02)

`ontario_units` is the Ontario crop-heat-unit index, which is built from the day's
maximum and minimum:

    Ymax = 3.33*(Tmax-10) - 0.084*(Tmax-10)^2
    Ymin = 1.8*(Tmin-4.4)
    CHU  = (Ymax + Ymin)/2

Tmax is `daily_max`, so Tmin drops out by algebra. Against the pipeline's own cleaned
temperature the recovered minimum lands at corr +0.987, error sd 0.45 C -- and it is the
clean minimum: on days where an injected spike drags the observed maximum to 51.5 or
59.8 C, `daily_max` still reports 35.4 and 29.5.

That matters because the overnight minimum is the dewpoint proxy the whole `tmin_block`
is built on. This gives a second, day-anchored, spike-immune estimate of it, and it is
better supported on the private slice (1.000) than the rolling-range block it sits
beside (0.818).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

DAY_ANCHOR_HOURS = 22


def day_key(index: pd.DatetimeIndex) -> pd.DatetimeIndex:
    return (index - pd.Timedelta(hours=DAY_ANCHOR_HOURS)).normalize()


def chu_daily(c: pd.DataFrame) -> pd.DataFrame:
    """One row per 22:00-anchored day: de-jittered Tmax, Tmean and the recovered Tmin."""
    k = day_key(c.index)
    b = c.groupby(k)[['daily_max', 'ontario_units', 'daily_mean_temperature']].median()
    x = b.daily_max - 10.0
    ymax = 3.33 * x - 0.084 * x ** 2
    b['Tmin'] = (2 * b.ontario_units - ymax) / 1.8 + 4.4
    return b.rename(columns={'daily_max': 'Tmax', 'daily_mean_temperature': 'Tmean'})


def chu_block(c: pd.DataFrame, es) -> pd.DataFrame:
    """Row-level features. `chu_rng` is deliberately absent: its private-slice support is
    0.818, the same failure the section 78 audit found in the T_rng block."""
    b = chu_daily(c)
    m = b.reindex(day_key(c.index))
    m.index = c.index
    T = c['air_temperature']
    return pd.DataFrame({
        'chu_Tmin': m.Tmin,
        'chu_Tmax': m.Tmax,
        'chu_Tmean': m.Tmean,
        # parameter-free RH from the dewpoint approximation Td ~ day minimum
        'chu_rh': 100.0 * es(m.Tmin.values) / es(T.values),
        'chu_T_minus_min': T - m.Tmin,
        # where in today's range this reading sits: 0 at the night minimum, 1 at the peak
        'chu_frac': (T - m.Tmin) / (m.Tmax - m.Tmin).replace(0, np.nan),
    }, index=c.index)


def dejitter_daily(c: pd.DataFrame, columns) -> pd.DataFrame:
    """Replace each day-constant column with its own 22:00-day median.

    `clean_exog` runs these through a Hampel filter and `interpolate('time')`, which is the
    wrong treatment for a step function: inside a day it smears the jitter around instead of
    cancelling it, and across a boundary with missing rows it ramps linearly between two
    plateaus that should meet at a step. The median over the day does both jobs at once --
    it removes the jitter and it fills the 10-18 % of rows where the column is absent with
    the value that day actually had.
    """
    out = c.copy()
    k = day_key(c.index)
    for col in columns:
        if col in out:
            out[col] = out.groupby(k)[col].transform('median')
    return out
