"""Session 46: the random-convolution representation, pointed at the CHANGE instead of the level.

**Why here and not at the level.** §229 showed a Ridge over 512 random convolutions of exogenous
windows reaches B3 4.8226 against the whole six-member stack's 4.8109, from sensors alone. That is
the only thing in this log that ever found dynamics the summary columns drop. Three attempts to
spend it have failed — a frozen 0.25 blend (§229), a per-origin weight (§234), and a seventh NNLS
member (§268) — and **all three failed at the same step: choosing a scalar weight on a LEVEL.**

The increment terms do not have that step. They enter the solver as constraints at weights `lam`
frozen since §147, and the solver reconciles rather than blends. So the representation can be spent
in a place where the failure mode that killed it three times does not exist.

**Why the change is the right target for it.** §307 measured the deficit: the shipped stack
reproduces only **0.45-0.49** of the real vapour-pressure curvature and 0.62-0.67 of the RH
curvature. The path is too flat, and it is worst in the quantity that carries the weather. The
increment models are LightGBM on a two-point design — the drivers at `t`, at `t-h`, and their
difference — and §202's `--inc-lags` showed that widening that design to a causal lag trajectory
was worth −0.0250 pooled, the last increment change this log adopted. Random convolutions over a
193-point window are the same move, much further.

**What is held fixed.** The horizons and their reconciliation weights (§147), the level stack, the
solver, and the alpha grid and kernel bank of §229. Only the function producing `d_h` changes.

The target is the h-step change of the label, exactly as `fp.fit_increments` defines it, and both
endpoints must be labelled training rows — so no RH from the scored window ever enters.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
import final_pipeline as fp
import v21_sequence_design as sd
import v21_seq_member as sm
import v21_temporal_models as tm


def _design(F, idx, scaler, cols, bank):
    """Scalar block plus the random-convolution responses of the centred window."""
    W = sd.build_windows(F, idx, scaler)
    S = sd.scalar_matrix(F, idx, cols)
    return np.hstack([S, tm.apply_bank(W, bank)])


def fit_seq_increments(F, y, train_mask, h, seeds=sm.SEEDS, alphas=sm.ALPHAS,
                       n_kernels=tm.N_KERNELS):
    """One Ridge per seed for the h-step change, on the same rows `fp.fit_increments` uses.

    `train_mask` selects rows usable as the LATER endpoint; the shift below additionally requires
    the EARLIER endpoint to be a labelled training row, so a difference can never straddle the
    forecast origin.
    """
    tgt = (y - y.shift(h)).reindex(F.index)
    m = train_mask.reindex(F.index, fill_value=False)
    m = m & tgt.notna() & m.shift(h, fill_value=False)
    rows = F.index[m.to_numpy()]
    assert len(rows) > 300, 'only %d usable difference rows at h=%d' % (len(rows), h)

    scaler = sd.ChannelScaler().fit(F, rows)
    cols = sd.scalar_columns(F)
    r = tgt.loc[rows].to_numpy()
    folds = tm.forward_folds(rows)
    out = []
    for seed in seeds:
        bank = tm.kernel_bank(seed, n=n_kernels)
        X = _design(F, rows, scaler, cols, bank)
        alpha = sm._alpha(X, r, folds, alphas) if folds else alphas[-1]
        out.append((tm.make_ridge(alpha).fit(X, r), bank))
    return dict(models=out, scaler=scaler, cols=cols, h=h)


def predict_seq_increments(fit, F, stamps):
    """The predicted h-step change at `stamps`, averaged over the seed bank."""
    stamps = pd.DatetimeIndex(stamps)
    return np.mean([m.predict(_design(F, stamps, fit['scaler'], fit['cols'], bank))
                    for m, bank in fit['models']], axis=0)


def seq_terms(F, idx, y, train_mask, spec=fp.INC_SPEC, **kw):
    """`(operator, target, weight)` triples for the solver, one per frozen horizon.

    Same shape `an47.increment_terms` returns, so the same `an47.solve` consumes it and the two
    families can be compared, added or swapped without touching the solver.
    """
    out = []
    for h, lam in spec:
        D, stamps = fp.diff_operator(idx, h)
        if D is None:
            out.append((None, None, lam))
            continue
        fit = fit_seq_increments(F, y, train_mask, h, **kw)
        out.append((D, predict_seq_increments(fit, F, stamps), lam))
    return out
