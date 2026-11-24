"""Session 34, Task 1: the solver's geometry, as a training objective for the increment models.

**The identity this is built on.** `a47.solve` minimises `||z - p||^2 + sum_h lam_h ||D_h z - t_h||^2`,
whose normal equations are `A z = p + sum_h lam_h D_h^T t_h` with

    A = I + 4 D1^T D1 + D4^T D4                (lam_1 = 4, lam_4 = 1, frozen since session 21)

If the increment models were exactly right, `t_h = D_h y`, and because `4 D1^T D1 + D4^T D4 = A - I`
the solution collapses to `z_true = y + A^{-1}(p - y)`. Writing `r = t - D y` for the increment
error stacked over both horizons,

    e0 = A^{-1}(p - y)                          the level error the solver cannot remove
    B  = A^{-1} [4 D1^T , D4^T]                 how increment error reaches the answer
    z - y = e0 + B r

**Why this is worth training against.** `fit_increments` minimises `||r||^2` -- the size of each
element of `r` on its own. The solver is moved by `B r`, which depends on WHERE the errors sit,
how they correlate across time, and whether the 30-minute and 2-hour errors reinforce or cancel.
Two error vectors with identical RMSE can produce very different RH. Sections 174-195 swapped the
increment learner six times and tuned two gain scalars after fitting; none of them changed the
gradient that trains `d_h(X_h)`. That is the gap this module fills.

**The limit, stated before any result.** The objective here is `||B r||^2`, not the final RH loss
`||e0 + B r||^2`. It drops the cross-term `2 e0^T B r`. Computing that term during training would
need `p` on the training rows, where `p` is in-sample and optimistically small, so the cross-term
would be fitted against a level error that the holdout will not have. This is a surrogate with a
known omission, not end-to-end training, and final RH remains the only thing that decides.

**The quadratic form.** With `m` training edges over both horizons:

    c       = trace(B^T B) / m                  scale from the timestamp geometry alone
    Q_full  = B^T B / c + eps I                 both horizons coupled
    Q_sep   = blockdiag(B1^T B1, B4^T B4) / c + eps I

`eps = 0.10` is set here, not searched. Without it the objective is blind to any error in the
nullspace of `B` -- and `B` has one, since there are more edges than timestamps -- which would let
the two horizons drift to large values that happen to cancel. `c` is computed from the operator,
never from labels or from a score.

**The Hessian.** LightGBM takes a per-row Hessian vector, and `Q` is not diagonal. The diagonal
majorizer `H_i = sum_j |Q_ij|` gives `diag(H) - Q` positive semidefinite by Gershgorin, so each
boosting step solves an upper bound on the true quadratic -- a majorise-minimise step, not a claim
that LightGBM supports a full Hessian. The same `H` bounds `Q_sep` as well, because zeroing the
cross-blocks only shrinks `|Q_ij|` elementwise. Both arms therefore use one `H` and one `scale`,
so a difference between them cannot be a difference in step size.
"""
import hashlib
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.sparse import csc_matrix, identity
from scipy.sparse.linalg import splu

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
import final_pipeline as fp

EPS = 0.10                  # frozen regularisation; not a searched hyperparameter
MODES = ('l2_control', 'separate', 'coupled')
ROW_BLOCK = 512             # rows of B^T B materialised at once when accumulating H


def effective_edges(F, y, train_mask, horizons=fp.INC_SPEC):
    """The later endpoints `fit_increments` actually trains on, per horizon.

    Reproduces its mask exactly: the later endpoint is a labelled training row, the target
    exists, and the earlier endpoint is a labelled training row too. Returned so the geometry can
    be checked against it rather than quietly deriving its own -- replacing the objective and
    silently repairing the legacy mask at the same time would make the comparison meaningless.
    """
    out = {}
    for h, _lam in horizons:
        X = fp.increment_design(F, h, fp.INC_COLS, False, False)
        tgt = (y - y.shift(h)).reindex(X.index)
        m = train_mask.reindex(X.index, fill_value=False)
        m = m & tgt.notna() & m.shift(h, fill_value=False)
        out[h] = X.index[m.to_numpy()]
    return out


class Geometry:
    """`D`, `A`, `B`, the edge map and the quadratic form for one origin.

    Holds one dense `B` of shape (n_timestamps, n_edges). At the largest origin in this project
    that is about 2200 x 4400 float64, roughly 78 MB; `B^T B` is never held whole, only the row
    blocks needed to accumulate `H`. Build one origin at a time and drop it before the next.
    """

    def __init__(self, index, D, edges, A, B, c, H, scale, eps, horizons):
        self.index = index
        self.D = D
        self.edges = edges
        self.A = A
        self.B = B
        self.c = c
        self.H = H
        self.scale = scale
        self.eps = eps
        self.horizons = horizons
        self.offsets = {}
        k = 0
        for h, _lam in horizons:
            self.offsets[h] = (k, k + len(edges[h]))
            k += len(edges[h])
        self.m = k

    # ---------------------------------------------------------------- pieces
    def slice(self, h):
        a, b = self.offsets[h]
        return slice(a, b)

    def block(self, h):
        """`B` restricted to one horizon's edges."""
        return self.B[:, self.slice(h)]

    # ---------------------------------------------------------------- objective
    def _Qr(self, r, mode):
        """`Q r` before the `scale` division. Computed through `B`, never by forming `Q`."""
        r = np.asarray(r, float)
        if mode == 'coupled':
            out = self.B.T @ (self.B @ r) / self.c
        elif mode == 'separate':
            out = np.empty_like(r)
            for h, _lam in self.horizons:
                s = self.slice(h)
                Bh = self.B[:, s]
                out[s] = Bh.T @ (Bh @ r[s]) / self.c
        else:
            raise ValueError('mode %r has no quadratic form; l2_control bypasses it' % mode)
        return out + self.eps * r

    def grad(self, r, mode):
        """Gradient of `0.5 r^T Q r`, on the same scale as `H`."""
        return self._Qr(r, mode) / self.scale

    def loss(self, r, mode):
        r = np.asarray(r, float)
        return float(0.5 * r @ self.grad(r, mode))

    def hess(self):
        """The diagonal majorizer. One vector, shared by both arms."""
        return self.H

    def Q_dense(self, mode):
        """The explicit matrix. For tests and small graphs only -- O(m^2) memory."""
        if mode == 'coupled':
            Q = (self.B.T @ self.B) / self.c
        elif mode == 'separate':
            Q = np.zeros((self.m, self.m))
            for h, _lam in self.horizons:
                s = self.slice(h)
                Bh = self.B[:, s]
                Q[s, s] = (Bh.T @ Bh) / self.c
        else:
            raise ValueError(mode)
        Q[np.diag_indices_from(Q)] += self.eps
        return Q / self.scale

    # ---------------------------------------------------------------- provenance
    def digest(self):
        h = hashlib.md5()
        h.update(np.asarray(self.index.astype('int64')).tobytes())
        for hz, lam in self.horizons:
            h.update(np.asarray([hz, lam], float).tobytes())
            h.update(np.asarray(self.edges[hz].astype('int64')).tobytes())
        h.update(np.asarray([self.c, self.scale, self.eps], float).tobytes())
        h.update(np.ascontiguousarray(self.H, np.float64).tobytes())
        return h.hexdigest()

    def memory_mb(self):
        return dict(B=self.B.nbytes / 2 ** 20, H=self.H.nbytes / 2 ** 20,
                    peak_estimate=(self.B.nbytes + ROW_BLOCK * self.m * 8) / 2 ** 20)


def build_geometry(index, edges=None, eps=EPS, horizons=fp.INC_SPEC):
    """`Geometry` for one origin, from the labelled training index alone.

    `index` must be the labelled training timestamps -- nothing at or after the origin, and no
    test rows. `fp.diff_operator` emits one row per pair of timestamps EXACTLY `h` half-hours
    apart within that index, so a hole produces no row rather than a difference silently taken
    across it, and the derived edges coincide with `fit_increments`' effective mask. When `edges`
    is supplied the two are asserted equal; a mismatch stops the run rather than being repaired.
    """
    index = pd.DatetimeIndex(index)
    assert index.is_monotonic_increasing and not index.has_duplicates, \
        'the training index must be sorted and unique'
    n = len(index)

    D, got, cols = {}, {}, []
    for h, lam in horizons:
        Dh, stamps = fp.diff_operator(index, h)
        assert Dh is not None and Dh.shape[0] > 0, 'horizon %d has no training edge' % h
        D[h] = Dh
        got[h] = pd.DatetimeIndex(stamps)
        cols.append(lam * Dh.T)
        if edges is not None:
            want = pd.DatetimeIndex(edges[h])
            assert got[h].equals(want), (
                'horizon %d: the geometry derives %d edges and the incumbent mask has %d; the '
                'objective may not change the training pairs' % (h, len(got[h]), len(want)))

    A = identity(n, format='csc')
    for h, lam in horizons:
        A = (A + lam * (D[h].T @ D[h])).tocsc()
    M = csc_matrix(np.hstack([c.toarray() for c in cols])) if n <= 8 else None
    if M is None:
        from scipy.sparse import hstack as sp_hstack
        M = sp_hstack(cols, format='csc')

    # B = A^{-1} M, by factorising A once and solving for every edge column. Never inv(A).
    lu = splu(A.tocsc())
    B = np.asfortranarray(lu.solve(np.asarray(M.todense(), float)))

    m = B.shape[1]
    c_norm = float(np.sum(B * B) / m)              # trace(B^T B)/m, from geometry alone
    assert c_norm > 0, 'the operator has no response at all'

    # H_i = sum_j |Q_ij|, accumulated in row blocks so B^T B is never held whole.
    H = np.empty(m)
    for a in range(0, m, ROW_BLOCK):
        b = min(a + ROW_BLOCK, m)
        G = B[:, a:b].T @ B                        # (block, m)
        H[a:b] = np.abs(G).sum(axis=1) / c_norm
        del G
    H += eps
    scale = float(H.mean())
    assert scale > 0 and np.isfinite(H).all()
    H = H / scale

    return Geometry(index, D, got, A, B, c_norm, H, scale, eps, tuple(horizons))


def solver_error(p, y, A):
    """`e0 = A^{-1}(p - y)`: the part of the final error increments cannot touch."""
    return splu(A.tocsc()).solve(np.asarray(p, float) - np.asarray(y, float))


def true_increment_reference(p, y, index, horizons=fp.INC_SPEC):
    """`z = y + A^{-1}(p - y)`: what the solver returns if the increments were exact.

    A diagnostic ceiling for a FIXED level `p`, computed without fitting anything. It is not an
    absolute bound: a biased `p` can be partly cancelled by increments that differ from the truth,
    so a real model could in principle beat it. Pre-clip.
    """
    index = pd.DatetimeIndex(index)
    A = identity(len(index), format='csc')
    for h, lam in horizons:
        Dh, _ = fp.diff_operator(index, h)
        if Dh is not None:
            A = (A + lam * (Dh.T @ Dh)).tocsc()
    return np.asarray(y, float) + solver_error(p, y, A)
