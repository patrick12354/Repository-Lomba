"""Session 39: the section-229 sequence prediction, packaged as a blend member.

`q` is a Ridge over random convolutions of exogenous windows. Section 229 measured it standalone
at 6.7852 / 7.2243 / 4.8226 on B1/B2/B3 against the six-member level stack's 4.2932 / 6.7782 /
4.8109 -- on B3 within 0.012 of the whole ensemble, from sensors alone, with no RH history of any
kind as input. Its error correlation with the stack is 0.583-0.797 (section 233), so it is partly
a different view and partly the same mistakes made worse.

Two attempts to spend it have failed, and both failed at the same place: choosing a scalar weight.
Section 229 froze the weight at 0.25 and blended `q` into the FINISHED level. Section 233 then
showed no uniform weight can pass the gate -- B1 worsens at every positive weight, even with the
outer labels in hand. Section 234 chose the weight per outer origin from 384-864 calibration rows
and it picked 0.45 on B1 where the true optimum is 0.00.

This module does not choose a weight. It exposes `q` as a column so the weight comes from the
blend machinery `final_pipeline` already ships and has validated over eighteen nested folds:
non-negative least squares over the WHOLE out-of-fold frame, shrunk toward equal weighting, then
re-fitted per time-of-day band and shrunk again toward the global vector. Section 98 is the
precedent -- an L2 member whose residuals correlate 0.950 with `hbt` was given weight 0.042 and
was worth -0.0128 nested with a bootstrap interval excluding zero.

That is a different estimator from section 234's, not a second try at the same one. It may still
fail, and section 233's bound says how: a global NNLS weight IS a uniform weight, so if NNLS
lands anywhere above about 0.05 the B1 damage section 233 measured should appear here too.

**The alpha grid is section 229's, and one attempt to widen it was reverted.** Every fold recorded
in `replay_folds.csv` chose 10000, the top of `(100, 1000, 10000)`, which looks like a grid pinned
at its edge. Extending it to `(..., 30000, 100000)` was tried and is WORSE: B1 unchanged at
6.7852, B2 7.2243 -> 7.1136, B3 4.8226 -> 5.0823, net +0.149 over the three blocks. The edge was
not a defect, and the grid stays as section 229 froze it.

`seq_predict` reproduces section 229's A2 exactly on all three blocks -- 6.7852 / 7.2243 / 4.8226,
to four decimals, against `an72_v21_sequence_benchmark.py`'s independent implementation. That
equality is the correctness proof this module rests on; anything that breaks it is a regression.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.exceptions import ConvergenceWarning  # noqa: F401  (kept for parity with tm)

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
import v21_sequence_design as sd
import v21_temporal_models as tm

# Section 229's grid was (100, 1000, 10000) and every recorded fold chose 10000, its maximum.
ALPHAS = (100.0, 1000.0, 10000.0)
SEEDS = tm.SEEDS


def _alpha(X, r, folds, alphas):
    """Alpha on forward windows inside the training set. `tm.forward_alpha` hard-codes its own
    grid; this is the same selection over a grid the caller owns."""
    best, best_sse = alphas[0], np.inf
    for alpha in alphas:
        sse = 0.0
        for trn, val in folds:
            m = tm.make_ridge(alpha).fit(X[trn], r[trn])
            sse += float(np.sum((r[val] - m.predict(X[val])) ** 2))
        if sse < best_sse:
            best, best_sse = alpha, sse
    return best


def seq_predict(F, y, train_idx, pred_idx, seeds=SEEDS, alphas=ALPHAS,
                n_kernels=tm.N_KERNELS):
    """Level prediction on `pred_idx`, fitted on `train_idx`.

    `y` is read at `train_idx` and nowhere else. The channel scaler, the alpha and the ridge are
    all fitted on `train_idx` only, so nothing from the prediction window enters the model. The
    target is section 229's physical residual `(RH - rh_tmin48)/10`, inverted back to a level, so
    a ridge that predicts zero returns the parameter-free dewpoint proxy exactly.
    """
    train_idx = pd.DatetimeIndex(train_idx)
    pred_idx = pd.DatetimeIndex(pred_idx)

    scaler = sd.ChannelScaler().fit(F, train_idx)
    cols = sd.scalar_columns(F)
    r_train = sd.residual_target(y, F).reindex(train_idx).to_numpy()

    W_tr = sd.build_windows(F, train_idx, scaler)
    S_tr = sd.scalar_matrix(F, train_idx, cols)
    W_pr = sd.build_windows(F, pred_idx, scaler)
    S_pr = sd.scalar_matrix(F, pred_idx, cols)
    folds = tm.forward_folds(train_idx)

    out = []
    for seed in seeds:
        bank = tm.kernel_bank(seed, n=n_kernels)
        Xtr = np.hstack([S_tr, tm.apply_bank(W_tr, bank)])
        Xpr = np.hstack([S_pr, tm.apply_bank(W_pr, bank)])
        alpha = _alpha(Xtr, r_train, folds, alphas) if folds else alphas[-1]
        m = tm.make_ridge(alpha).fit(Xtr, r_train)
        out.append(sd.invert_residual(m.predict(Xpr), F, pred_idx))
    return np.mean(out, axis=0)
