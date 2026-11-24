"""Session 35, Task 1: RH anchors transported from historical episodes with similar sensors.

**The identity.** For a query `i` and a labelled training row `j`,

    q_ij = y_j * es(T_j) / es(T_i)

is the relative humidity the query would have if its vapour pressure equalled the anchor's. The
conversion is exact -- `RH = 100 e / es(T)`, so holding `e` fixed and changing `T` gives exactly
this ratio. **The physics is not the hypothesis.** The hypothesis is that two moments whose
temperature, ventilation and pressure dynamics look alike also carry similar vapour pressure, and
that is what the falsification gate in `an81` exists to test before anything is benchmarked.

**How this differs from the KNN that already failed.** `exp07` scored KNN25 at 8.257970 and KNN60
at 8.269191 by taking Euclidean distance over the whole standardised no-soil feature block and
averaging the neighbours' RH directly. That is not this:

* distance is over four small, named state groups, each averaged separately, so no single block of
  correlated columns dominates;
* at most one anchor per episode-day and five episodes total, because twenty-five rows from one
  afternoon are one piece of evidence, not twenty-five;
* the anchor's RH is TRANSPORTED through the temperature ratio rather than used raw -- and the raw
  version is kept as the control arm, so the transport can be isolated;
* a query with no support ABSTAINS instead of being given the nearest bad match.

**What is frozen here and not searched.** Five episodes, the `exp(-d^2/2)` weight, the 48-hour
separation, the `a = 0.25` anchor strength, and the four descriptor groups. The one quantity read
from data is the distance threshold, and it is the q90 of the distance-to-fifth-neighbour measured
on inner calibration queries whose labels all precede the outer origin.

**What may be read.** Descriptors come from a feature frame built at the forecast's own horizon
end, so nothing after it is visible. Anchors must be labelled training rows at or before the
origin and at least 48 hours before the query, so no anchor can be a near-duplicate of its own
query. RH after the origin never enters -- `tests/test_v21_episode_anchors.py` mutates it and
requires every output to be unchanged.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
import final_pipeline as fp

# Four state groups. Every name is asserted against `fp.make_features` output before use; a
# guessed column that silently became NaN would turn the distance into noise without failing.
GROUPS = {
    'thermal': ('T', 'T_min48', 'T_rng48', 'air_temperature_a24h'),
    'ventilation': ('co2_c24h', 'co2_a24h', 'co2_slope'),
    'pressure_dynamics': ('pressure_a24h', 'pressure_slope'),
    'diurnal': ('sin1', 'cos1'),
}
CYCLIC = ('sin1', 'cos1')          # already on a natural [-1, 1] scale; not rescaled
N_EPISODES = 5                     # anchors kept per query, one per episode-day
MIN_SEPARATION = pd.Timedelta(hours=48)
ANCHOR_STRENGTH = 0.25             # `a_i` for a supported query; frozen, not swept
THRESHOLD_QUANTILE = 0.90          # of distance-to-fifth-neighbour on inner calibration queries
SCALE_FLOOR = 1e-6
EPISODE_HOURS = 24

REASONS = ('ok', 'too_few_episodes', 'missing_descriptor', 'above_threshold', 'no_threshold')


def descriptor_columns():
    out = []
    for g in GROUPS:
        out.extend(GROUPS[g])
    return out


def assert_columns(F):
    missing = [c for c in descriptor_columns() if c not in F.columns]
    assert not missing, 'descriptor columns absent from the feature frame: %r' % (missing,)


class DescriptorScaler:
    """Median/IQR per non-cyclic descriptor, fitted on training rows only.

    The cyclic pair is left alone: `sin1` and `cos1` already share one scale, and standardising
    them separately would stretch whichever happens to have the smaller spread in the prefix.
    """

    def __init__(self):
        self.center_ = None
        self.scale_ = None
        self.columns_ = None

    def fit(self, F, train_idx):
        assert_columns(F)
        cols = descriptor_columns()
        sub = F.loc[pd.DatetimeIndex(train_idx), cols]
        med = sub.median()
        iqr = sub.quantile(0.75) - sub.quantile(0.25)
        scale = iqr.where(np.isfinite(iqr) & (iqr > SCALE_FLOOR), 1.0)
        for c in CYCLIC:
            med[c], scale[c] = 0.0, 1.0
        self.center_, self.scale_, self.columns_ = med, scale, cols
        return self

    def transform(self, F, idx):
        idx = pd.DatetimeIndex(idx)
        sub = F.loc[idx, self.columns_]
        return (sub - self.center_) / self.scale_


def episode_id(idx, grid_start):
    """Calendar-independent episode label: which 24-hour slab of the record a row falls in."""
    idx = pd.DatetimeIndex(idx)
    delta = (idx - pd.Timestamp(grid_start)).total_seconds() / 3600.0
    return np.floor(delta / EPISODE_HOURS).astype(np.int64)


def group_distances(Zq, Za):
    """Mean over groups of the mean squared descriptor difference inside each group.

    Averaging within a group and then across groups means a four-column group and a two-column
    group carry the same weight, so `thermal` cannot dominate by having more columns.
    """
    total = np.zeros((len(Zq), len(Za)))
    for cols in GROUPS.values():
        q = Zq[list(cols)].to_numpy(float)
        a = Za[list(cols)].to_numpy(float)
        d = np.zeros((len(q), len(a)))
        for k in range(q.shape[1]):
            diff = q[:, k][:, None] - a[:, k][None, :]
            d += diff ** 2
        total += d / q.shape[1]
    return total / len(GROUPS)


def build_anchor_table(F, y, query_idx, anchor_idx, scaler, grid_start, threshold=None,
                       n_episodes=N_EPISODES, strength=ANCHOR_STRENGTH):
    """Per-query anchors, transported values and the abstention reason.

    Returns `(summary, detail)`. `summary` has one row per query with `q_transport`, `q_raw`,
    `a`, `distance5`, `n_episodes` and `reason`; `detail` has one row per kept anchor with its
    timestamp, episode, distance, weight and transport ratio, so any correction can be traced
    back to the training labels that produced it.
    """
    assert_columns(F)
    query_idx = pd.DatetimeIndex(query_idx)
    anchor_idx = pd.DatetimeIndex(anchor_idx)
    assert anchor_idx.is_monotonic_increasing and not anchor_idx.has_duplicates
    Zq = scaler.transform(F, query_idx)
    Za = scaler.transform(F, anchor_idx)
    q_ok = Zq.notna().all(axis=1).to_numpy()
    a_ok = Za.notna().all(axis=1).to_numpy()
    Za, anchor_idx = Za.loc[a_ok], anchor_idx[a_ok]

    ya = y.reindex(anchor_idx).to_numpy(float)
    Ta = F.loc[anchor_idx, 'T'].to_numpy(float)
    Tq = F.loc[query_idx, 'T'].to_numpy(float)
    esa, esq = fp.es(Ta), fp.es(Tq)
    ep_a = episode_id(anchor_idx, grid_start)
    a_time = anchor_idx.to_numpy()

    D = group_distances(Zq, Za) if len(anchor_idx) else np.zeros((len(query_idx), 0))
    rows, detail = [], []
    for i, ts in enumerate(query_idx):
        if not q_ok[i]:
            rows.append(dict(datetime=ts, q_transport=np.nan, q_raw=np.nan, a=0.0,
                             distance5=np.nan, n_episodes=0, reason='missing_descriptor'))
            continue
        # eligible anchors: strictly at least MIN_SEPARATION earlier, so an anchor can never be a
        # near-copy of its own query -- the failure a naive KNN on a 30-minute grid walks into.
        elig = np.flatnonzero(a_time <= (ts - MIN_SEPARATION).to_datetime64())
        if len(elig) == 0:
            rows.append(dict(datetime=ts, q_transport=np.nan, q_raw=np.nan, a=0.0,
                             distance5=np.nan, n_episodes=0, reason='too_few_episodes'))
            continue
        d = D[i, elig]
        # one anchor per episode: sort by (distance, timestamp) and keep the first of each episode
        order = np.lexsort((a_time[elig], d))
        seen, keep = set(), []
        for pos in order:
            e = ep_a[elig[pos]]
            if e in seen:
                continue
            seen.add(e)
            keep.append(pos)
            if len(keep) == n_episodes:
                break
        keep = np.asarray(keep, int)
        picked = elig[keep]
        dist = d[keep]
        if len(keep) < n_episodes:
            rows.append(dict(datetime=ts, q_transport=np.nan, q_raw=np.nan, a=0.0,
                             distance5=float(dist[-1]) if len(dist) else np.nan,
                             n_episodes=len(keep), reason='too_few_episodes'))
            continue
        d5 = float(dist[-1])
        w = np.exp(-dist / 2.0)
        s = w.sum()
        w = w / s if s > 0 else np.full(len(w), 1.0 / len(w))
        ratio = esa[picked] / esq[i]
        qt = float(np.sum(w * ya[picked] * ratio))
        qr = float(np.sum(w * ya[picked]))
        over = threshold is not None and d5 > threshold
        rows.append(dict(datetime=ts, q_transport=qt, q_raw=qr,
                         a=0.0 if over else strength, distance5=d5,
                         n_episodes=len(keep), reason='above_threshold' if over else 'ok'))
        for k in range(len(picked)):
            detail.append(dict(datetime=ts, anchor=anchor_idx[picked[k]],
                               episode=int(ep_a[picked[k]]), distance=float(dist[k]),
                               weight=float(w[k]), y_anchor=float(ya[picked[k]]),
                               ratio=float(ratio[k]),
                               q_ij=float(ya[picked[k]] * ratio[k])))
    S = pd.DataFrame(rows)
    Dt = pd.DataFrame(detail, columns=['datetime', 'anchor', 'episode', 'distance', 'weight',
                                       'y_anchor', 'ratio', 'q_ij'])
    return S, Dt


def choose_threshold(distance5, quantile=THRESHOLD_QUANTILE):
    """The q90 of distance-to-fifth-neighbour over inner calibration queries.

    Session 36. This returned `inf` when no calibration query had a finite distance, which is a
    threshold that admits everything -- the opposite of the intended behaviour. A calibration that
    produced nothing cannot license unlimited support, so it now returns `None` and the caller is
    required to treat that as abstention.
    """
    v = np.asarray(distance5, float)
    v = v[np.isfinite(v)]
    if len(v) == 0:
        return None
    return float(np.quantile(v, quantile))


def abstain_all(query_idx, reason):
    """A summary frame in which every query abstains, for a window that cannot be calibrated."""
    assert reason in REASONS, reason
    idx = pd.DatetimeIndex(query_idx)
    return (pd.DataFrame(dict(datetime=idx, q_transport=np.nan, q_raw=np.nan, a=0.0,
                              distance5=np.nan, n_episodes=0, reason=reason)),
            pd.DataFrame(columns=['datetime', 'anchor', 'episode', 'distance', 'weight',
                                  'y_anchor', 'ratio', 'q_ij']))


def global_best_day_guard(y, base, cand, when):
    """Drop the single largest-gain DAY across the whole population, then recompute SSE/n.

    Session 36. `an81` dropped one day per window and then averaged the per-window results
    weighted by each window's row count, which is neither "drop the best day globally" nor a
    pooled statistic -- it reported 5.057280 where the global supported figure is 4.083291. The
    guard exists to ask whether a gain survives without its single best day, so the day has to be
    chosen and removed once, over the pooled rows.
    """
    y = np.asarray(y, float)
    b = (np.asarray(base, float) - y) ** 2
    c = (np.asarray(cand, float) - y) ** 2
    t = pd.DataFrame(dict(day=pd.DatetimeIndex(when).normalize(), b=b, c=c))
    gs = t.groupby('day').sum()
    worst = (gs.c - gs.b).idxmin()
    keep = t.loc[t.day != worst]
    return dict(guard=float((keep.c.sum() - keep.b.sum()) / len(keep)),
                dropped_day=str(worst.date()), n_kept=int(len(keep)), n_days=int(len(gs)))


def coverage(summary):
    n = len(summary)
    ok = int((summary.reason == 'ok').sum())
    return dict(n=n, supported=ok, coverage=(ok / n) if n else 0.0,
                **{r: int((summary.reason == r).sum()) for r in REASONS})


def solve_with_anchors(level, idx, terms, a=None, q=None):
    """`a47.solve` with an absolute anchor term added to the same quadratic problem.

        min_z ||z - p||^2 + sum_h lam_h ||D_h z - d_h||^2 + sum_i a_i (z_i - q_i)^2
        (A + diag(a)) z = p + sum_h lam_h D_h^T d_h + a * q

    This is the only structural change to the objective the solver has carried since session 21.
    Every difference term has zero row sum, so the increments cannot move a component's mean --
    the anchor term can, which is the whole point of using absolute level information. With
    `a = 0` it reproduces `a47.solve` exactly, and `tests/test_v21_anchor_solver.py` pins that.

    `q` is ignored wherever `a` is zero, so an abstaining row contributes nothing and a NaN there
    cannot leak into the solve.
    """
    from scipy.sparse import diags, identity
    from scipy.sparse.linalg import spsolve
    level = np.asarray(level, float)
    n = len(level)
    A = identity(n, format='csc')
    rhs = level.copy()
    for M, t, lam in terms:
        if M is None:
            continue
        A = (A + lam * (M.T @ M)).tocsc()
        rhs = rhs + lam * (M.T @ t)
    if a is not None:
        a = np.asarray(a, float)
        assert a.shape == (n,) and np.isfinite(a).all() and (a >= 0).all()
        qq = np.where(a > 0, np.nan_to_num(np.asarray(q, float), nan=0.0), 0.0)
        A = (A + diags(a)).tocsc()
        rhs = rhs + a * qq
    z = spsolve(A, rhs)
    assert np.max(np.abs(A @ z - rhs)) < 1e-7 and np.isfinite(z).all()
    return np.clip(z, 5, 100)
