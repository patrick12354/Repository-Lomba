"""Session 31, Task 2: the three non-neural arms, A0/A1/A2.

All three predict the same physical residual against the same anchor and differ only in what
they are allowed to look at, so a gain can be attributed to the representation rather than to a
new learner or a new target:

* **A0** scalar control -- the parent `F` block only. Establishes what the target and the Ridge
  are worth without any trajectory access at all. Not a candidate; a control.
* **A1** linear trajectory control -- A0 plus raw channel values at eleven offsets and their
  masks. Separates "access to context" from "nonlinear shape", so a negative A2 cannot be read
  as "sequences do not help" when the linear version was never run.
* **A2** random convolution screen -- ROCKET-INSPIRED, not an implementation of ROCKET. Dempster
  et al. (arXiv:1910.13051) evaluate random convolutional kernels for time-series
  CLASSIFICATION; using them with a Ridge regressor on RH is an adaptation whose transfer is
  exactly what is being tested.

**Where this deliberately departs from ROCKET.** Global max and proportion-positive pooling
discard where in the window a response occurred, and position relative to the target is the
whole point here. So each filter pools separately over responses centred BEFORE and AFTER the
target, giving four features per filter and keeping a coarse sense of "this pattern happened
before the target, not after".

Responses whose footprint touches an invalid mask position are dropped, so a padded horizon edge
never masquerades as a flat signal. If a side has no valid response the feature is NaN and is
imputed from training statistics -- never from the validation labels, and never with a quantile
fitted on them.
"""
import hashlib
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
import v21_sequence_design as sd

ALPHAS = (100.0, 1000.0, 10000.0)
SEEDS = (20260906, 20260907, 20260908)
N_KERNELS = 512
LENGTHS = (7, 9, 11)
DILATIONS = (1, 2, 4, 8)
A1_OFFSETS = (-96, -48, -24, -12, -4, 0, 4, 12, 24, 48, 96)
N_CHAN = len(sd.CHANNELS)


# ------------------------------------------------------------------ A1: linear trajectory

def trajectory_features(W):
    """Raw values and masks at the frozen offsets, flattened."""
    cols = [sd.OFFSETS.index(o) for o in A1_OFFSETS]
    return W[:, :, cols].reshape(len(W), -1)


# ------------------------------------------------------------------ A2: random convolution

def kernel_bank(seed, n=N_KERNELS):
    """Deterministic filters. Each picks one value channel, a length and a dilation; weights are
    Gaussian, mean-removed and unit-norm; bias is uniform on the normalised scale."""
    rng = np.random.default_rng(seed)
    bank = []
    for _ in range(n):
        length = int(rng.choice(LENGTHS))
        dil = int(rng.choice(DILATIONS))
        if (length - 1) * dil + 1 > sd.WINDOW:
            dil = 1
        w = rng.standard_normal(length)
        w = w - w.mean()
        nrm = np.linalg.norm(w)
        w = w / (nrm if nrm > 0 else 1.0)
        bank.append(dict(channel=int(rng.integers(0, N_CHAN)), length=length,
                         dilation=dil, weight=w, bias=float(rng.uniform(-1.0, 1.0))))
    return bank


def bank_hash(bank):
    h = hashlib.md5()
    for k in bank:
        h.update(np.asarray([k['channel'], k['length'], k['dilation']], dtype=np.int64).tobytes())
        h.update(np.asarray(k['weight'], dtype=np.float64).tobytes())
        h.update(np.asarray([k['bias']], dtype=np.float64).tobytes())
    return h.hexdigest()


def apply_bank(W, bank):
    """Four features per kernel: max and proportion-positive, separately for responses centred
    before and after the target."""
    n = len(W)
    out = np.full((n, 4 * len(bank)), np.nan)
    for i, k in enumerate(bank):
        span = (k['length'] - 1) * k['dilation'] + 1
        half = span // 2
        taps = np.arange(k['length']) * k['dilation']
        starts = np.arange(0, sd.WINDOW - span + 1)
        if len(starts) == 0:
            continue
        cols = starts[:, None] + taps[None, :]                     # (P, L)
        vals = W[:, k['channel'], :][:, cols]                      # (n, P, L)
        good = W[:, N_CHAN + k['channel'], :][:, cols].min(axis=2) > 0
        resp = (vals * k['weight'][None, None, :]).sum(axis=2) + k['bias']
        centres = starts + half
        for s, side in enumerate((centres < sd.CENTER, centres > sd.CENTER)):
            if not side.any():
                continue
            r = resp[:, side]
            ok = good[:, side]
            any_ok = ok.any(axis=1)
            masked = np.where(ok, r, -np.inf)
            mx = masked.max(axis=1)
            pp = np.where(ok, (r > 0).astype(float), 0.0).sum(axis=1)
            cnt = ok.sum(axis=1)
            out[any_ok, 4 * i + 2 * s] = mx[any_ok]
            out[any_ok, 4 * i + 2 * s + 1] = pp[any_ok] / np.maximum(cnt[any_ok], 1)
    return out


def valid_response_share(W, bank):
    """Diagnostic: what fraction of pooled features exist rather than being imputed."""
    X = apply_bank(W, bank)
    return float(np.isfinite(X).mean())


# ------------------------------------------------------------------ shared Ridge machinery

def make_ridge(alpha):
    return make_pipeline(SimpleImputer(strategy='median'), StandardScaler(),
                         Ridge(alpha=alpha))


def forward_alpha(X, r, folds):
    """Alpha chosen on two forward windows inside the outer training set, never on outer."""
    table = []
    for alpha in ALPHAS:
        sse = 0.0
        for trn, val in folds:
            m = make_ridge(alpha).fit(X[trn], r[trn])
            sse += float(np.sum((r[val] - m.predict(X[val])) ** 2))
        table.append(dict(alpha=alpha, sse=sse))
    best = min(table, key=lambda t: t['sse'])
    return best['alpha'], table


def forward_folds(train_idx, days=7, n=2):
    """Two non-overlapping 7-day validation windows at the end of the training set."""
    train_idx = pd.DatetimeIndex(train_idx).sort_values()
    out = []
    for k in range(n, 0, -1):
        hi = train_idx.max() - pd.Timedelta(days=days * (k - 1))
        lo = hi - pd.Timedelta(days=days)
        val = np.flatnonzero((train_idx > lo) & (train_idx <= hi))
        trn = np.flatnonzero(train_idx <= lo)
        if len(val) > 96 and len(trn) > 480:
            out.append((trn, val))
    return out


# ------------------------------------------------------------------ B0/B1: learned models
#
# Section 1 of the plan is explicit that the MLP failures of sections 50-54 do not test this:
# those were tabular MLPs on summary features. A dilated 1-D convolution with weight sharing over
# a 193-point window is a different function class, and B0 exists precisely to tell "neural
# training helps" from "temporal convolution helps". Everything below is frozen before the run.

TORCH_TRAIN = dict(lr=1e-3, weight_decay=1e-2, batch=64, max_epochs=160, patience=15,
                   grad_clip=1.0)


def _torch():
    import torch
    torch.manual_seed(0)
    torch.use_deterministic_algorithms(False)
    return torch


class ThermalWindowNet:
    """Dilated temporal CNN plus a scalar path. Receptive field 1 + 4*(1+3+9+27) = 161 points,
    80 hours, inside the 96-hour window. The head is zero-initialised so an untrained model
    returns the physical anchor exactly."""

    @staticmethod
    def build(n_scalar, n_in=2 * len(sd.CHANNELS)):
        torch = _torch()
        from torch import nn

        class Net(nn.Module):
            def __init__(self):
                super().__init__()
                layers, c = [], n_in
                for dilation in (1, 3, 9, 27):
                    layers += [nn.Conv1d(c, 16, kernel_size=5, dilation=dilation,
                                         padding=2 * dilation), nn.GELU(), nn.Dropout(0.1)]
                    c = 16
                self.temporal = nn.Sequential(*layers)
                self.scalar = nn.Sequential(nn.Linear(n_scalar, 8), nn.GELU())
                self.head = nn.Linear(24, 1)
                nn.init.zeros_(self.head.weight)
                nn.init.zeros_(self.head.bias)

            def forward(self, sequence, scalar):
                t = self.temporal(sequence)
                centre = t[:, :, t.shape[-1] // 2]
                return self.head(torch.cat([centre, self.scalar(scalar)], dim=1)).squeeze(1)

        return Net()


class ScalarNet:
    """B0: the same training recipe on the scalar block alone, F -> 32 -> 32 -> 1."""

    @staticmethod
    def build(n_scalar, n_in=None):
        _torch()
        from torch import nn

        class Net(nn.Module):
            def __init__(self):
                super().__init__()
                self.body = nn.Sequential(nn.Linear(n_scalar, 32), nn.GELU(), nn.Dropout(0.1),
                                          nn.Linear(32, 32), nn.GELU(), nn.Dropout(0.1))
                self.head = nn.Linear(32, 1)
                nn.init.zeros_(self.head.weight)
                nn.init.zeros_(self.head.bias)

            def forward(self, sequence, scalar):
                return self.head(self.body(scalar)).squeeze(1)

        return Net()


def count_parameters(model):
    return int(sum(p.numel() for p in model.parameters() if p.requires_grad))


def _loader(torch, W, S, r, batch, shuffle, seed=0):
    ds = torch.utils.data.TensorDataset(torch.tensor(W, dtype=torch.float32),
                                        torch.tensor(S, dtype=torch.float32),
                                        torch.tensor(r, dtype=torch.float32))
    gen = torch.Generator().manual_seed(seed)
    return torch.utils.data.DataLoader(ds, batch_size=batch, shuffle=shuffle, generator=gen)


def train_net(builder, W, S, r, val, seed, epochs=None, cfg=TORCH_TRAIN):
    """Train one network. With `val` given, early-stop on it and return the chosen epoch; with
    `epochs` given, refit from scratch for exactly that many epochs and no early stopping."""
    torch = _torch()
    torch.manual_seed(seed)
    model = builder.build(S.shape[1])
    opt = torch.optim.AdamW(model.parameters(), lr=cfg['lr'], weight_decay=cfg['weight_decay'])
    loss_fn = torch.nn.MSELoss()
    train_loader = _loader(torch, W, S, r, cfg['batch'], True, seed)
    best, best_epoch, bad = np.inf, 0, 0
    limit = epochs if epochs is not None else cfg['max_epochs']
    for epoch in range(1, limit + 1):
        model.train()
        for wb, sb, rb in train_loader:
            opt.zero_grad()
            loss = loss_fn(model(wb, sb), rb)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), cfg['grad_clip'])
            opt.step()
        if val is not None:
            model.eval()
            with torch.no_grad():
                pv = model(torch.tensor(val[0], dtype=torch.float32),
                           torch.tensor(val[1], dtype=torch.float32)).numpy()
            sse = float(np.mean((val[2] - pv) ** 2))
            if sse < best - 1e-9:
                best, best_epoch, bad = sse, epoch, 0
            else:
                bad += 1
                if bad >= cfg['patience']:
                    break
    return model, (best_epoch if val is not None else limit), best


def predict_net(model, W, S):
    torch = _torch()
    model.eval()
    with torch.no_grad():
        return model(torch.tensor(W, dtype=torch.float32),
                     torch.tensor(S, dtype=torch.float32)).numpy()
