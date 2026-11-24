"""Session 37, Task 1: hide a few real sensor readings, then rebuild everything downstream.

**The question.** Every model in this log has learned from ONE deterministic cleaning of the
sensors. About a tenth of the raw grid is missing and is filled by `clean_exog`'s Hampel-plus-
interpolate, so a good part of what `hbt` sees at any moment is a reconstruction. If the model has
come to depend on the particular shape of that reconstruction, then hiding a few more genuine
readings and re-cleaning should move its predictions more than the weather warrants -- and
training on both views should teach it not to.

That is a hypothesis about ROBUSTNESS, not capacity. Nothing here makes the model bigger: same
learner, same features, same hyperparameters, same inference. It can easily fail by simply
destroying useful readings, and section 5 of the plan says so.

**What is masked.** Bernoulli p = 0.05 over cells that are genuinely observed -- raw finite AND
not rejected by the incumbent Hampel filter -- on `air_temperature`, `co2` and `pressure` only, at
timestamps inside the requested window and on official train rows. Grid holes and spikes are
already absent from the model's view; re-hiding them would teach nothing.

**Why the whole frame is rebuilt.** Masking columns of `F` directly would leave `esT`, the rolling
means, the quantile block and the lag columns describing a sensor history that no longer matches
the readings. The mask is applied to the RAW grid and `clean_exog` and `make_features` are then
run again, so every derived column is consistent with the observations that survived -- including
the interpolation filling the new hole.

**Determinism.** The draw comes from a stable hash of `(seed, sensor, timestamp)`, never from row
position, so the same cell is chosen whatever order the frame arrives in and whatever else is in
it. `tests/test_v21_sensor_masking.py` pins that.
"""
import hashlib
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
import final_pipeline as fp

SENSORS = ('air_temperature', 'co2', 'pressure')
P_MASK = 0.05                                  # one strength, frozen; there is no p grid
TRAIN_SEEDS = (2026090701, 2026090702, 2026090703, 2026090704, 2026090705)
STRESS_SEEDS = (2026090791, 2026090792, 2026090793)


def _uniform(seed, sensor, stamps):
    """A stable uniform draw per (seed, sensor, timestamp), independent of row order.

    Hashing the timestamp itself rather than its position is the whole point: a cell's fate must
    not depend on how many rows precede it, or the mask would change with the horizon.
    """
    out = np.empty(len(stamps))
    key = ('%d|%s|' % (int(seed), sensor)).encode()
    for i, t in enumerate(np.asarray(stamps, dtype='datetime64[ns]').astype('int64')):
        h = hashlib.blake2b(key + str(int(t)).encode(), digest_size=8).digest()
        out[i] = int.from_bytes(h, 'big') / 2.0 ** 64
    return out


def observed_mask(g, sensor):
    """Cells the model actually sees as observations: raw finite and not Hampel-rejected."""
    s = g[sensor]
    finite = s.notna().to_numpy()
    kept = fp.hampel(s).notna().to_numpy()
    return finite & kept


def eligible_mask(g, sensor, lo=None, hi=None):
    """Observed cells inside the window that belong to official training rows."""
    idx = g.index
    ok = observed_mask(g, sensor) & (g['is_test'] == 0).to_numpy()
    if lo is not None:
        ok &= np.asarray(idx > pd.Timestamp(lo))
    if hi is not None:
        ok &= np.asarray(idx <= pd.Timestamp(hi))
    return ok


def masked_frame(g, seed, lo=None, hi=None, sensors=SENSORS, p=P_MASK):
    """A copy of the raw grid with `p` of the eligible cells hidden, plus a per-cell audit.

    Only the three sensor columns are touched. The index, `is_test`, the target and every other
    column are returned unchanged, so the augmented view differs from the original in exactly the
    readings that were hidden and in whatever the cleaner then does about them.
    """
    out = g.copy()
    rows = []
    for sensor in sensors:
        assert sensor in out.columns, 'unknown sensor %r' % sensor
        elig = eligible_mask(g, sensor, lo, hi)
        u = _uniform(seed, sensor, g.index.to_numpy())
        hit = elig & (u < p)
        if hit.any():
            out.loc[out.index[hit], sensor] = np.nan
        rows.append(pd.DataFrame(dict(timestamp=g.index, sensor=sensor,
                                      eligible=elig, masked=hit, draw=u)))
    return out, pd.concat(rows, ignore_index=True)


def mask_report(audit):
    """Counts per sensor, for the manifest. The realised rate is not forced to equal `p`."""
    out = []
    for sensor, d in audit.groupby('sensor'):
        e, m = int(d.eligible.sum()), int(d.masked.sum())
        out.append(dict(sensor=sensor, eligible=e, masked=m,
                        rate=(m / e) if e else float('nan'), rows=int(len(d))))
    return pd.DataFrame(out)


def build_views(g, horizon_end, origin, seed, p=P_MASK):
    """`(F_original, F_masked, audit)` for one origin, both built to the same endpoint.

    The mask is confined to timestamps at or before the origin, so the augmented copy differs from
    the original only in training territory. Rows after the origin still change slightly, because
    the cleaner's centred windows reach across the boundary -- those rows are never used for
    prediction, and `an86` takes its query features from the ORIGINAL frame.
    """
    he = pd.Timestamp(horizon_end)
    gh = g.loc[g.index <= he]
    gm, audit = masked_frame(gh, seed, lo=None, hi=pd.Timestamp(origin), p=p)
    return fp.make_features(gh), fp.make_features(gm), audit


def stress_frame(g, horizon_end, origin, seed, p=P_MASK):
    """The diagnostic view: readings hidden only inside the SCORED horizon.

    Used after a model is frozen, to ask how much its prediction moves when the sensor record it
    is asked about is slightly different. A model that barely moves is not thereby good -- a
    constant predictor does not move at all -- so this is reported beside the natural score and
    never instead of it.
    """
    he = pd.Timestamp(horizon_end)
    gh = g.loc[g.index <= he]
    gm, audit = masked_frame(gh, seed, lo=pd.Timestamp(origin), hi=he, p=p)
    return fp.make_features(gm), audit


def audit_digest(audit):
    h = hashlib.md5()
    d = audit.loc[audit.masked].sort_values(['sensor', 'timestamp'])
    for sensor, ts in zip(d.sensor, np.asarray(d.timestamp, dtype='datetime64[ns]').astype('int64')):
        h.update(('%s|%d|' % (sensor, int(ts))).encode())
    return h.hexdigest()
