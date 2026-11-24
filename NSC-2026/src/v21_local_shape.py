"""Session 33, Task 2: 60 trajectory-shape features and 12 observation-quality features.

Every scalar feature this pipeline feeds the level members is a SUMMARY of a sensor window --
a mean, a minimum, a quantile, a range, a handful of fixed lags. Two 24-hour temperature
trajectories can agree on all of those and still differ in whether the cooling arrived as one
long slide or as six reversals, and in whether CO2 turned before or after the temperature did.
Section 229 found that shape carries level information the summaries drop: a random-convolution
transform of the same raw window beat the physical anchor on all three blocks. What sections
231-234 then failed at was PLACING that information -- every route went through a standalone
sequence prediction whose weight had to be chosen from a calibration window that does not
resemble the outer one.

This module takes the other route. It computes a small, deterministic, fixed description of the
local trajectory and hands it straight to `hbt`, the LightGBM level member that already learns
from every training label. There is no new prediction to weight and no new hyperparameter to
select: the feature definitions below are frozen, and `an76` changes nothing else about the
ensemble.

**What is read.** The cleaned T, CO2 and pressure channels, from a grid truncated at the
forecast's own `horizon_end`. Future exogenous INSIDE the horizon is the shipped policy -- the
sensors for the forecast window are given -- so the forward regions are legitimate. RH is never
read, by this module or by anything it calls, and `tests/test_v21_local_shape.py` pins that by
blanking the target and requiring a byte-identical frame.

**The four regions** are past6h, past24h, future6h and future24h, expressed as offsets on the
30-minute grid and resolved by CLOCK TIME, never by row count. Each channel x region gets four
statistics:

    slope   least-squares slope against time, in units per HOUR
    rms     root-mean-square residual after that line is removed -- how much of the motion is
            not the trend
    turn    proportion of adjacent first-difference pairs that change sign
    run     longest same-sign run of first differences, over the number of first differences

`slope` and `rms` say how far and how smoothly the sensor moved; `turn` and `run` say in what
ORDER, and are invariant to the sensor's unit and offset. A monotone ramp has turn 0 and run 1
whatever its steepness; a zigzag of the same amplitude has turn 1 and run near 0. That contrast
is the whole point of the block, and it is what a min/max/quantile summary cannot express.

3 channels x 4 regions x 4 statistics = 48, plus 12 cross-sensor lagged difference correlations
(section "correlations" below) = **60 shape features**.

**Support rule.** A region needs at least `MIN_POINTS` finite readings or all four of its
statistics are NaN. That happens at the two frame edges only -- a row near the start of the
record has no past24h, one near `horizon_end` has no future24h -- and NaN is the honest answer
there. The builder never reaches past the horizon and never wraps around to fill a short window.
LightGBM handles NaN natively; infinities are refused outright.

The 6-point floor is written into `MIN_POINTS` once and applied to all four statistics, not just
to slope and rms. A turning rate computed from two differences is noise with a number attached,
and treating the four statistics of a region as one supported-or-not unit keeps the missingness
pattern of the block simple enough to reason about.

**The 12 quality features** describe where a raw reading actually came from. `clean_exog`
despikes and interpolates, so by the time a channel reaches the shape statistics above there is
no missingness left to see -- on the frame to 29 August the raw grid is 9.7-10.8% missing for
T/CO2/pressure and 0% after cleaning. Section 187 already established that repaired rows are not
worse in aggregate, so this is NOT a claim that interpolation causes error. The open question is
narrower: whether the PROPORTION of reconstructed points inside a trajectory makes the shape
statistics above describe a shape that was drawn by the interpolator rather than by the weather.
E2 exists to answer that and nothing more.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
import final_pipeline as fp

# ---------------------------------------------------------------- frozen definitions
SLOT = pd.Timedelta(minutes=30)
CHANNELS = (('T', 'air_temperature'), ('co2', 'co2'), ('pressure', 'pressure'))
REGIONS = (('past6h', tuple(range(-12, 0))),
           ('past24h', tuple(range(-48, 0))),
           ('future6h', tuple(range(1, 13))),
           ('future24h', tuple(range(1, 49))))
STATS = ('slope', 'rms', 'turn', 'run')
MIN_POINTS = 6                      # finite readings a region needs before it reports anything
MIN_PAIRS = 6                       # difference pairs a correlation needs
CORR_PAIRS = (('T', 'co2'), ('T', 'pressure'))
CORR_LAGS = ((-4, 'm4'), (0, '0'), (4, 'p4'))
CORR_REGIONS = ('past24h', 'future24h')
QUALITY_STATS = ('observed_now', 'repaired_fraction_24h', 'gap_past_hours', 'gap_future_hours')
QUALITY_HALF = 48                   # +/- 24 h, in slots, for repaired_fraction_24h
GAP_CAP_HOURS = 48.0                # a gap longer than this, or no observation at all, reports 48
N_SHAPE = len(CHANNELS) * len(REGIONS) * len(STATS) + \
    len(CORR_PAIRS) * len(CORR_LAGS) * len(CORR_REGIONS)      # 48 + 12 = 60
N_QUALITY = len(CHANNELS) * len(QUALITY_STATS)                # 12


def shape_columns():
    """The 60 `shape_` names, in the order `build_local_shape` emits them."""
    out = [f'shape_{ch}_{rg}_{st}'
           for ch, _ in CHANNELS for rg, _ in REGIONS for st in STATS]
    out += [f'shape_corr_{a}_{b}_lag{tag}_{rg}'
            for a, b in CORR_PAIRS for _, tag in CORR_LAGS for rg in CORR_REGIONS]
    return out


def quality_columns():
    return [f'quality_{ch}_{st}' for ch, _ in CHANNELS for st in QUALITY_STATS]


def all_columns():
    return shape_columns() + quality_columns()


# ---------------------------------------------------------------- window gathering

def _gather(values, offsets):
    """`(n, len(offsets))` of `values[i + off]`, NaN wherever the offset leaves the grid.

    Offsets are positions on a grid asserted complete at 30 minutes, so offset 48 is 24 hours
    for every row and cannot silently become "48 surviving readings" the way a `.shift` on a
    frame with holes would.
    """
    values = np.asarray(values, float)
    n = len(values)
    pos = np.arange(n)[:, None] + np.asarray(offsets, int)[None, :]
    inside = (pos >= 0) & (pos < n)
    return np.where(inside, values[np.clip(pos, 0, max(n - 1, 0))], np.nan)


def _slope_rms(X, offsets):
    """Least-squares slope per hour and the RMS residual about that line."""
    t = np.asarray(offsets, float) * (SLOT / pd.Timedelta(hours=1))
    ok = np.isfinite(X)
    cnt = ok.sum(axis=1)
    supported = cnt >= MIN_POINTS
    den = np.maximum(cnt, 1).astype(float)

    Xz = np.where(ok, X, 0.0)
    Tz = np.where(ok, np.broadcast_to(t, X.shape), 0.0)
    dt = np.where(ok, Tz - (Tz.sum(1) / den)[:, None], 0.0)
    dx = np.where(ok, Xz - (Xz.sum(1) / den)[:, None], 0.0)
    stt = (dt * dt).sum(1)
    slope = np.divide((dt * dx).sum(1), stt, out=np.zeros(len(X)), where=stt > 0)
    resid = dx - slope[:, None] * dt
    rms = np.sqrt(np.where(ok, resid ** 2, 0.0).sum(1) / den)
    return (np.where(supported, slope, np.nan), np.where(supported, rms, np.nan))


def _diffs(X):
    """First differences between ADJACENT grid slots inside the region."""
    d = X[:, 1:] - X[:, :-1]
    return np.where(np.isfinite(X[:, 1:]) & np.isfinite(X[:, :-1]), d, np.nan)


def _order_stats(D, supported):
    """Turning rate and longest-run fraction of a difference sequence.

    An exactly zero difference is neither an up-step nor a down-step: it ends the current run
    and it is excluded from the turning-rate denominator rather than counted as a reversal. On
    real sensor data zeros are quantisation plateaus, and calling a plateau a turn would make
    `turn` a resolution statistic instead of a shape one.
    """
    ok = np.isfinite(D)
    s = np.where(ok, np.sign(D), 0.0)
    a, b = s[:, :-1], s[:, 1:]
    both = (a != 0) & (b != 0)
    den = both.sum(1)
    turn = np.divide((both & (a != b)).sum(1).astype(float), den.astype(float),
                     out=np.zeros(len(D)), where=den > 0)

    cur = np.zeros(len(D))
    best = np.zeros(len(D))
    prev = np.zeros(len(D))
    for j in range(s.shape[1]):
        sj = s[:, j]
        cur = np.where(sj == 0, 0.0, np.where(sj == prev, cur + 1.0, 1.0))
        best = np.maximum(best, cur)
        prev = sj
    n_diff = ok.sum(1)
    run = np.divide(best, n_diff.astype(float), out=np.zeros(len(D)), where=n_diff > 0)
    return (np.where(supported, turn, np.nan), np.where(supported, run, np.nan))


CONST_TOL = 1e-9        # a side whose spread is this small relative to its own size is constant


def _corr(U, V):
    """Row-wise Pearson correlation over the columns where both are finite.

    Zero -- not NaN -- when one side is constant: a flat sensor and a moving one are genuinely
    uncorrelated, and NaN there would be read as missing support. NaN is reserved for windows
    that do not have `MIN_PAIRS` usable pairs.

    "Constant" is judged against the size of the vector rather than against exact equality,
    because the constant case that actually occurs here is not exact. `clean_exog` interpolates
    across gaps, and a straight line through a 13-slot hole has first differences that agree to
    about 1e-13 rather than to the last bit. Dividing that residue by itself produces a
    correlation of arbitrary sign that is pure rounding -- and it is not stable, so the same
    window reports a different number after the channel is shifted by a constant. An exact
    `> 0` guard misses this entirely; the relative floor catches it and leaves genuine motion,
    which is fifteen orders of magnitude larger, untouched.
    """
    ok = np.isfinite(U) & np.isfinite(V)
    cnt = ok.sum(1)
    den = np.maximum(cnt, 1).astype(float)
    Uz, Vz = np.where(ok, U, 0.0), np.where(ok, V, 0.0)
    du = np.where(ok, Uz - (Uz.sum(1) / den)[:, None], 0.0)
    dv = np.where(ok, Vz - (Vz.sum(1) / den)[:, None], 0.0)
    su, sv = np.sqrt((du * du).sum(1)), np.sqrt((dv * dv).sum(1))
    moves = ((su > CONST_TOL * (1.0 + np.sqrt((Uz * Uz).sum(1)))) &
             (sv > CONST_TOL * (1.0 + np.sqrt((Vz * Vz).sum(1)))))
    scale = su * sv
    r = np.divide((du * dv).sum(1), scale, out=np.zeros(len(U)), where=moves & (scale > 0))
    return np.where(cnt >= MIN_PAIRS, np.clip(r, -1.0, 1.0), np.nan)


# ---------------------------------------------------------------- quality provenance

def _valid_raw(series):
    """A reading that was recorded AND survived the incumbent Hampel filter.

    `fp.hampel` is the exact filter `clean_exog` runs before interpolating, so `~valid` is
    precisely the set of slots whose cleaned value was reconstructed rather than observed.
    """
    return fp.hampel(series).notna().to_numpy()


def _gap_hours(valid, forward):
    """Hours to the nearest valid observation at or before (or at or after) each slot."""
    n = len(valid)
    pos = np.arange(n)
    idx = np.where(valid, pos, -1 if not forward else n)
    if forward:
        nearest = np.minimum.accumulate(idx[::-1])[::-1]
        gap = np.where(nearest < n, (nearest - pos), np.inf)
    else:
        nearest = np.maximum.accumulate(idx)
        gap = np.where(nearest >= 0, (pos - nearest), np.inf)
    hours = gap.astype(float) * (SLOT / pd.Timedelta(hours=1))
    return np.minimum(hours, GAP_CAP_HOURS)


def _repaired_fraction(valid):
    """Share of the +/-24 h neighbourhood that was reconstructed.

    The denominator counts only slots that exist inside this frame, so a row near an edge
    reports the fraction of what it can see rather than being penalised for the horizon.
    """
    n = len(valid)
    csum = np.concatenate([[0.0], np.cumsum(valid.astype(float))])
    pos = np.arange(n)
    lo = np.maximum(pos - QUALITY_HALF, 0)
    hi = np.minimum(pos + QUALITY_HALF + 1, n)
    span = (hi - lo).astype(float)
    return 1.0 - (csum[hi] - csum[lo]) / span


# ---------------------------------------------------------------- public builder

def build_local_shape(g, horizon_end):
    """The 72 features for every slot of the grid truncated at `horizon_end`.

    Truncation happens FIRST and cleaning runs on the truncated grid, so no statistic can be
    shaped by a sensor reading recorded after the forecast horizon -- including through the
    centred rolling windows inside `fp.hampel`. Passing an already-truncated grid gives the
    same answer as passing the full one with the same `horizon_end`.
    """
    horizon_end = pd.Timestamp(horizon_end)
    gh = g.loc[g.index <= horizon_end]
    idx = gh.index
    assert isinstance(idx, pd.DatetimeIndex) and len(idx) > 0, 'empty frame'
    if len(idx) > 1:
        step = np.unique(np.diff(idx.to_numpy()))
        assert len(step) == 1 and step[0] == SLOT.to_timedelta64(), \
            'offsets are only clock time on a complete 30-minute grid; got %r' % (step,)

    cleaned = fp.clean_exog(gh)
    raw_valid = {tag: _valid_raw(gh[col]) for tag, col in CHANNELS}

    out = {}
    diffs = {}                                   # (channel, region) -> region first differences
    for tag, col in CHANNELS:
        values = cleaned[col].to_numpy(float)
        for rg, offsets in REGIONS:
            X = _gather(values, offsets)
            supported = np.isfinite(X).sum(axis=1) >= MIN_POINTS
            slope, rms = _slope_rms(X, offsets)
            D = _diffs(X)
            turn, run = _order_stats(D, supported)
            diffs[(tag, rg)] = D
            for st, v in zip(STATS, (slope, rms, turn, run)):
                out[f'shape_{tag}_{rg}_{st}'] = v

    # ---- cross-sensor lagged difference correlation -----------------------------------------
    # `lag` is in slots and is applied to the SECOND sensor: the feature correlates dA at
    # endpoint k with dB at endpoint k - lag. A B that repeats A four slots later therefore
    # correlates at lag -4, which `tests/test_v21_local_shape.py::test_lag_sign_convention`
    # pins. No lag is searched over; all three are computed and handed to the learner.
    for a, b in CORR_PAIRS:
        for lag, tag in CORR_LAGS:
            for rg in CORR_REGIONS:
                DA, DB = diffs[(a, rg)], diffs[(b, rg)]
                m = DA.shape[1]
                j = np.arange(m)
                keep = (j - lag >= 0) & (j - lag < m)
                if keep.any():
                    r = _corr(DA[:, j[keep]], DB[:, j[keep] - lag])
                else:
                    r = np.full(len(DA), np.nan)
                out[f'shape_corr_{a}_{b}_lag{tag}_{rg}'] = r

    # ---- observation provenance --------------------------------------------------------------
    for tag, _ in CHANNELS:
        valid = raw_valid[tag]
        out[f'quality_{tag}_observed_now'] = valid.astype(float)
        out[f'quality_{tag}_repaired_fraction_24h'] = _repaired_fraction(valid)
        out[f'quality_{tag}_gap_past_hours'] = _gap_hours(valid, forward=False)
        out[f'quality_{tag}_gap_future_hours'] = _gap_hours(valid, forward=True)

    F = pd.DataFrame({c: out[c] for c in all_columns()}, index=idx)
    assert list(F.columns) == all_columns() and F.shape[1] == N_SHAPE + N_QUALITY
    assert not np.isinf(F.to_numpy(float)).any(), 'shape features must be finite or NaN'
    return F
