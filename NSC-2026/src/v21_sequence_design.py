"""Session 31, Task 1: the shared window builder for every sequence arm.

Every feature this log has tried summarises the past — minima, quantiles, means, ranges, a
handful of lags. Two trajectories can share a Tmin, a range and a quantile set and still differ
in how long the cooling lasted, in what order the plateaus came, and in how T and CO2 moved
relative to one another over a day. The hypothesis for session 31 is that this shape carries RH
information the summaries drop. It is a hypothesis; nothing here assumes it.

**The target is a residual against a deterministic physical anchor, not against a fitted model.**

    residual[t] = (RH[t] - rh_tmin48[t]) / 10
    q[t]        = rh_tmin48[t] + 10 * f(window[t], scalar[t])

`rh_tmin48` is section 19's parameter-free dewpoint proxy, built from temperature alone. Because
it is deterministic, a residual label exists for every legitimate training row before the origin
— unlike a residual against the fitted stack, which exists only where an OOF prediction does and
left section 220 with one usable window on B2. `f = 0` returns the anchor exactly, which is the
zero-correction control and is asserted in the tests.

**What the window is.** 193 points at offsets -96..+96 half-hours, so ±48 hours with the target
at index 96. Four value channels (T, CO2, pressure, and the `rh_tmin48` proxy trajectory) and
four validity channels, shape `(n, 8, 193)`.

**What may and may not be read.** Future EXOGENOUS is available in this task — the sensors for
the whole forecast window are known — so a centred window is legitimate. Future RH is not, and
never enters: no channel is the target or a lag of it. The frame is always built by
`a47.frame_at` at the forecast's own horizon end, so nothing beyond that horizon is visible
either; past that edge the builder pads and flags the mask, rather than reaching into a matrix
that was constructed to the end of the dataset and then sliced.

**Normalisation is fitted on training rows only** and is shared by every window in a fold, so the
absolute temperature a window sits at is preserved. Per-window standardisation would delete
exactly the level information the anchor needs. Padding is zero in normalised space — the
training median — and the mask says so, so the model can tell a padded edge from a real reading
at the median.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
import final_pipeline as fp

HALF_WINDOW = 96                      # 48 h either side
OFFSETS = tuple(range(-HALF_WINDOW, HALF_WINDOW + 1))
CENTER = HALF_WINDOW                  # index of the target inside the window
WINDOW = len(OFFSETS)                 # 193
CHANNELS = ('T', 'co2', 'pressure', 'rh_tmin48')
ANCHOR_COL = 'rh_tmin48'
RESIDUAL_SCALE = 10.0                 # keeps the target near unit scale; exact and invertible


def residual_target(y, F):
    """(RH - anchor) / scale, aligned on F's index. NaN wherever RH is unlabelled."""
    return (y.reindex(F.index) - F[ANCHOR_COL]) / RESIDUAL_SCALE


def invert_residual(pred, F, idx):
    """anchor + scale * f. With f = 0 this is the anchor itself."""
    return F[ANCHOR_COL].reindex(pd.DatetimeIndex(idx)).to_numpy() \
        + RESIDUAL_SCALE * np.asarray(pred, float)


class ChannelScaler:
    """Median/scale per channel, fitted on training rows only.

    Uses the median and a std computed about it. A channel with no spread gets scale 1 rather
    than dividing by zero, and is reported so a silently constant channel cannot pass unnoticed.
    """

    def __init__(self):
        self.median_ = None
        self.scale_ = None
        self.degenerate_ = []

    def fit(self, F, train_idx):
        sub = F.loc[pd.DatetimeIndex(train_idx), list(CHANNELS)]
        self.median_ = sub.median().to_numpy(float)
        scale = sub.std().to_numpy(float)
        self.degenerate_ = [CHANNELS[i] for i in range(len(CHANNELS))
                            if not np.isfinite(scale[i]) or scale[i] <= 0]
        scale = np.where(np.isfinite(scale) & (scale > 0), scale, 1.0)
        self.scale_ = scale
        return self

    def transform(self, values):
        return (values - self.median_[None, :, None]) / self.scale_[None, :, None]


def build_windows(F, idx, scaler):
    """Value and validity channels for every timestamp in `idx`.

    Alignment is by CLOCK TIME on a complete 30-minute grid spanning F, so offset 48 is always
    24 hours and never "48 surviving rows" -- the failure mode section 181 met in another guise.
    A position outside the frame, or holding a missing reading, is padded to the training median
    and flagged invalid.
    """
    idx = pd.DatetimeIndex(idx)
    full = pd.date_range(F.index.min(), F.index.max(), freq='30min')
    V = F.reindex(full)[list(CHANNELS)].to_numpy(float)          # (T, C)
    present = np.isfinite(V)
    pos = full.get_indexer(idx)
    assert (pos >= 0).all(), 'every target timestamp must lie on the feature grid'

    n, ch = len(idx), len(CHANNELS)
    values = np.zeros((n, ch, WINDOW), float)
    mask = np.zeros((n, ch, WINDOW), float)
    for k, off in enumerate(OFFSETS):
        src = pos + off
        inside = (src >= 0) & (src < len(full))
        take = np.where(inside, src, 0)
        v = V[take]                                              # (n, C)
        ok = present[take] & inside[:, None]
        values[:, :, k] = np.where(ok, v, 0.0)
        mask[:, :, k] = ok.astype(float)

    values = scaler.transform(values)
    values = np.where(mask > 0, values, 0.0)                     # pad = median in normalised space
    return np.concatenate([values, mask], axis=1)                # (n, 2C, WINDOW)


def scalar_matrix(F, idx, columns):
    """The parent scalar block, frozen column order, no sensor dropped."""
    return F.reindex(pd.DatetimeIndex(idx))[list(columns)].to_numpy(float)


def scalar_columns(F):
    """Every finite-typed parent feature, in F's own order, frozen for the round."""
    return [c for c in F.columns if pd.api.types.is_numeric_dtype(F[c])]


def training_rows(g, F, y, origin):
    """Labelled training rows at or before the origin, on the frame's own index."""
    lab = pd.Series((g.loc[F.index, 'is_test'] == 0).to_numpy(), index=F.index) \
        & y.reindex(F.index).notna()
    return F.index[(lab & (F.index <= pd.Timestamp(origin))).to_numpy()]


def window_metadata(idx, origin, horizon_end, F):
    idx = pd.DatetimeIndex(idx)
    return pd.DataFrame(dict(
        target_timestamp=idx, origin=pd.Timestamp(origin),
        horizon_end=pd.Timestamp(horizon_end),
        feature_start=idx - pd.Timedelta(minutes=30 * HALF_WINDOW),
        feature_end=idx + pd.Timedelta(minutes=30 * HALF_WINDOW),
        grid_end=F.index.max()))


def blend_level(level, q, weight=0.25):
    """The frozen contribution weight. Not swept, not chosen from outer."""
    return (1.0 - weight) * np.asarray(level, float) + weight * np.asarray(q, float)
