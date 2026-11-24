"""Frozen feature builder for the v6 line: v5's 68 non-soil columns + the tmin[18,48]
air-mass block + pressure/co2 tendency.  Kept in one place so every downstream script
sees exactly the columns that were validated in exp16."""
import sys, os, numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(__file__))
from common import *

TMIN_WINS = (18, 48)

def tmin_block(c, wins=TMIN_WINS):
    """Daily-minimum temperature is a dewpoint proxy: moist air cools until it reaches
    its dewpoint and stalls, so es(Tmin)/es(T) is a parameter-free RH estimate.  The
    diurnal range is the complementary signal -- clear dry days swing wide, humid days
    do not.  Centered windows are legitimate here because the exogenous sensors are
    fully observed across the test window."""
    T = c['air_temperature']; idx = c.index; d = {}
    for hrs in wins:
        w = int(hrs * 2) + 1
        mn = T.rolling(w, center=True, min_periods=6).min()
        mx = T.rolling(w, center=True, min_periods=6).max()
        d[f'T_min{hrs}'] = mn
        d[f'T_max{hrs}'] = mx
        d[f'T_minus_min{hrs}'] = T - mn
        d[f'T_rng{hrs}'] = mx - mn
        d[f'rh_tmin{hrs}'] = pd.Series(100 * es(mn.values) / es(T.values), index=idx)
    return pd.DataFrame(d, index=idx)

def tend_block(c):
    """Synoptic tendency: falling pressure precedes moist advection; the co2 trend tracks
    the ventilation regime."""
    idx = c.index; p = c['pressure']
    pm = p.rolling(49, center=True, min_periods=8).mean()
    return pd.DataFrame({'p_tend24h': pm.diff(48), 'p_tend48h': pm.diff(96),
                         'p_sd24h': p.rolling(49, center=True, min_periods=8).std(),
                         'co2_tend24h': c['co2'].rolling(49, center=True, min_periods=8).mean().diff(48)},
                        index=idx)

def build_v6(c):
    F = build_features(c)
    F = F[feature_set(F, 'nosoil')]
    F = pd.concat([F, tmin_block(c), tend_block(c)], axis=1)
    return F.replace([np.inf, -np.inf], np.nan)


# ---- v7: 96h window added (exp21) + co2 order statistics (exp20) -----------------
TMIN_WINS_V7 = (18, 48, 96)
CO2_WINS_V7 = (18, 48)

def ordstat_block(c, col, wins):
    """Windowed min/max/range. Only used for co2: the same block on pressure LOST
    (exp20, 5.918 vs 5.614), which is the negative control showing the Tmin gain is the
    specific dewpoint physics and not just 'more rolling statistics'."""
    s = c[col]; idx = c.index; d = {}
    for hrs in wins:
        w = int(hrs * 2) + 1
        mn = s.rolling(w, center=True, min_periods=6).min()
        mx = s.rolling(w, center=True, min_periods=6).max()
        d[f'{col}_min{hrs}'] = mn; d[f'{col}_max{hrs}'] = mx
        d[f'{col}_rng{hrs}'] = mx - mn; d[f'{col}_minus_min{hrs}'] = s - mn
    return pd.DataFrame(d, index=idx)

def build_v7(c):
    F = build_features(c)
    F = F[feature_set(F, 'nosoil')]
    F = pd.concat([F, tmin_block(c, TMIN_WINS_V7), tend_block(c),
                   ordstat_block(c, 'co2', CO2_WINS_V7)], axis=1)
    return F.replace([np.inf, -np.inf], np.nan)
