"""Session 33, Task 1: build each internal fold's features from that fold's own horizon.

**The defect this repairs.** `an72.run_family` picks the sequence Ridge penalty like this:

1. build `F` from the grid truncated at the OUTER horizon end;
2. fit a `ChannelScaler` on the whole outer training set and build every window from `F`;
3. cut the resulting matrices into two internal folds with `tm.forward_folds`;
4. refit only the Ridge pipeline's imputer and standardiser inside each fold.

Steps 1 and 2 happen once, before the fold boundary exists. So the internal validation window of
fold 0 -- 31 July to 7 August on B1 -- is scored with features built from a grid running to 29
August, and normalised by a scaler fitted on training rows that include the fold's own validation
period and three weeks past it. Measured on B1, the outer scaler's medians differ from fold 0's
by [-0.43, -5.92, -0.03, -0.7356] on T/CO2/pressure/`rh_tmin48`, so this is not a rewrite that
happens to produce the same arithmetic.

**What this is and is not.** It is a violation of the replay contract -- a simulated forecast
must see only what a real one at that origin would have -- and of train-only preprocessing on the
internal validation rows. It is NOT reading outer or test labels: the A2 verdict in section 231
still describes predictions that were genuinely produced, and repairing it does not retract that
verdict. Future exogenous INSIDE a horizon stays legitimate and is unchanged here; only what lies
after the horizon is removed.

Whether the repair moves RMSE at all is an open question with no expected direction, which is why
`an75` reports it as a methodology delta and not as a candidate.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
import final_pipeline as fp
import an47_v21_forward_benchmark as a47
import v21_sequence_design as sd
import v21_temporal_models as tm


def fold_context(g, y, train_idx, trn, val, feature_cache=None):
    """Frame, scaler and row slices for one internal fold, all built at ITS horizon.

    `trn` and `val` are integer positions into `train_idx`, which is how `tm.forward_folds`
    reports them. The frame stops at the last validation timestamp -- the fold's own horizon end
    -- and the channel scaler sees the fold's training rows and nothing later.
    """
    train_idx = pd.DatetimeIndex(train_idx)
    t_idx, v_idx = train_idx[trn], train_idx[val]
    assert t_idx.max() < v_idx.min(), 'an internal fold must train strictly before it validates'
    val_end = v_idx.max()
    _, F = a47.frame_at(g, val_end, feature_cache)
    assert F.index.max() <= val_end
    scaler = sd.ChannelScaler().fit(F, t_idx)
    return dict(F=F, scaler=scaler, t_idx=t_idx, v_idx=v_idx,
                feature_frame_end=F.index.max(), scaler_fit_end=t_idx.max(),
                validation_horizon_end=val_end, n_train=len(t_idx), n_val=len(v_idx))


def fold_matrices(ctx, y, bank=None, columns=None):
    """Design matrices and residual targets for one fold, from that fold's own frame.

    With `bank` the A2 representation is rebuilt here rather than sliced out of a matrix that was
    convolved once at the outer horizon -- the windows themselves depend on the frame and on the
    scaler, so slicing cannot be made equivalent.
    """
    F, sc = ctx['F'], ctx['scaler']
    cols = list(columns) if columns is not None else sd.scalar_columns(F)
    r = sd.residual_target(y, F)
    out = {}
    for tag, idx in (('train', ctx['t_idx']), ('val', ctx['v_idx'])):
        S = sd.scalar_matrix(F, idx, cols)
        if bank is None:
            out['X_' + tag] = S
        else:
            out['X_' + tag] = np.hstack([S, tm.apply_bank(sd.build_windows(F, idx, sc), bank)])
        out['r_' + tag] = r.loc[idx].to_numpy()
    out['columns'] = cols
    return out


def replay_alpha(g, y, train_idx, folds, bank=None, alphas=tm.ALPHAS, feature_cache=None):
    """`tm.forward_alpha` with every fold's features and scaler rebuilt at its own horizon.

    Same grid, same two forward windows, same three penalties: the search is not widened here.
    Widening it would confound "the replay was wrong" with "the grid was too small", and section
    3.2 is explicit that those are separate questions.
    """
    ctxs = [fold_context(g, y, train_idx, trn, val, feature_cache) for trn, val in folds]
    mats = [fold_matrices(ctx, y, bank) for ctx in ctxs]
    table = []
    for alpha in alphas:
        sse, n = 0.0, 0
        for m in mats:
            fit = tm.make_ridge(alpha).fit(m['X_train'], m['r_train'])
            sse += float(np.sum((m['r_val'] - fit.predict(m['X_val'])) ** 2))
            n += len(m['r_val'])
        table.append(dict(alpha=alpha, sse=sse, n=n))
    best = min(table, key=lambda t: t['sse'])
    prov = [dict(fold=i, alpha_grid=list(alphas), **{k: ctx[k] for k in (
        'feature_frame_end', 'scaler_fit_end', 'validation_horizon_end', 'n_train', 'n_val')})
        for i, ctx in enumerate(ctxs)]
    return best['alpha'], table, prov


def legacy_alpha(F_outer, scaler_outer, g, y, train_idx, folds, bank=None, alphas=tm.ALPHAS):
    """What `an72` actually did, kept so the delta can be measured instead of asserted.

    One frame at the outer horizon, one scaler fitted on the whole outer training set, then the
    matrices sliced by fold. This exists to be compared against and to be failed by
    `tests/test_v21_sequence_replay.py`; it is not a code path anything new should use.
    """
    train_idx = pd.DatetimeIndex(train_idx)
    cols = sd.scalar_columns(F_outer)
    S = sd.scalar_matrix(F_outer, train_idx, cols)
    X = S if bank is None else np.hstack(
        [S, tm.apply_bank(sd.build_windows(F_outer, train_idx, scaler_outer), bank)])
    r = sd.residual_target(y, F_outer).loc[train_idx].to_numpy()
    alpha, table = tm.forward_alpha(X, r, folds)
    return alpha, table


def early_stop_frame_end(train_idx, es_val):
    """The horizon an early-stopped epoch choice is allowed to see.

    `es_val` is a vector of integer POSITIONS into `train_idx`, not timestamps -- reading it as
    timestamps is how a contract like this gets written down correctly and implemented wrongly.
    The epoch is selected on a window ending here, so the frame that produces the features for
    that selection must end here too. The production refit afterwards uses the outer frame,
    which is its own horizon and therefore legitimate.
    """
    train_idx = pd.DatetimeIndex(train_idx)
    pos = np.asarray(es_val)
    assert pos.ndim == 1 and len(pos) > 0, 'es_val must be a nonempty vector of positions'
    assert np.issubdtype(pos.dtype, np.integer), 'es_val holds positions, not timestamps'
    assert pos.min() >= 0 and pos.max() < len(train_idx), 'es_val positions leave train_idx'
    return train_idx[pos].max()
