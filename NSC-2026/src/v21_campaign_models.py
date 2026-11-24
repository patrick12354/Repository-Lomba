"""Session 38: one adapter per campaign family, all fit-once/predict-many.

Each adapter returns the `hbt`-slot prediction `q` and the increment `terms` for one trial at one
origin. Everything a trial does not name stays incumbent, and every adapter is required to
reproduce the control exactly when its parameters are the incumbent's -- `zero_change` below is
that assertion, and `an89` runs it before scoring anything.

The families differ in which single thing they move:

    hbt_view       the sensor reconstruction the level member is TRAINED on (A)
    hbt_params     the level member's capacity (B)
    history        how far back labels are used, for one component only (C)
    inc_params     the increment learners' capacity (D)
    joint_level    the level member's objective and its supervision (E)
    inference_avg  the reconstruction the level member PREDICTS from (F)

Row counts matter here. Family A deliberately keeps `n_train` rows at weight 1, because session 37
showed that duplicating the frame costs +0.065 pooled on its own and would swamp any view effect.
"""
import hashlib
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import lightgbm as lgb

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
import final_pipeline as fp
import v21_soil_features as sf
import an47_v21_forward_benchmark as a47
import v21_sensor_masking as sm
import v21_joint_level_loss as jl
import v21_campaign_registry as reg

CLIP = (5.0, 100.0)


# ------------------------------------------------------------------ level member
def fit_hbt(X, y, train_idx, seeds, params=None):
    kw = reg.hbt_params(params)
    return [lgb.LGBMRegressor(random_state=s, **kw).fit(X.loc[train_idx], y.reindex(train_idx))
            for s in seeds]


def predict_hbt(models, X, idx):
    return np.mean([m.predict(X.loc[idx]) for m in models], axis=0)


# ------------------------------------------------------------------ increments
def fit_increments_kw(F, y, train_mask, seeds, params=None):
    """`fp.fit_increments` at the v21 configuration with `INC_KW` overridable.

    Identical selection to the incumbent: the later endpoint is a labelled training row, the
    target exists, and the earlier endpoint is a training row too. Truncating `train_mask` before
    the call is what family C uses, and it restricts BOTH endpoints because the mask is shifted.
    """
    kw = reg.inc_params(params)
    out = {'physics': False, 'cols': fp.INC_COLS, 'lags': False}
    for h, _lam in fp.INC_SPEC:
        X = fp.increment_design(F, h, fp.INC_COLS, False, False)
        tgt = (y - y.shift(h)).reindex(X.index)
        m = train_mask.reindex(X.index, fill_value=False)
        m = m & tgt.notna() & m.shift(h, fill_value=False)
        rows = X.index[m.to_numpy()]
        assert len(rows) > 200, 'horizon %d has only %d training edges' % (h, len(rows))
        out[h] = [lgb.LGBMRegressor(random_state=s, **kw).fit(X.loc[rows], tgt.loc[rows])
                  for s in seeds]
        out[('n_edges', h)] = len(rows)
    return out


def truncate_mask(mask, origin, days):
    cut = pd.Timestamp(origin) - pd.Timedelta(days=days)
    out = mask & (mask.index > cut)
    assert int(out.sum()) > 300, 'history window leaves only %d rows' % int(out.sum())
    return out


# ------------------------------------------------------------------ family A helpers
def episode_choice(index, grid_start, seed, hours=24):
    """One original/masked decision per 24-hour episode, stable under row order."""
    idx = pd.DatetimeIndex(index)
    ep = np.floor((idx - pd.Timestamp(grid_start)).total_seconds() / 3600.0 / hours).astype(int)
    out = np.empty(len(idx), bool)
    cache = {}
    for i, e in enumerate(ep):
        if e not in cache:
            h = hashlib.blake2b(('%d|%d' % (int(seed), int(e))).encode(), digest_size=8).digest()
            cache[e] = (int.from_bytes(h, 'big') / 2.0 ** 64) < 0.5
        out[i] = cache[e]
    return out


def view_frame(g, ctx, seed, p):
    """The masked TRAINING view at the requested strength.

    `p` must be threaded through: defaulting it here would make A01/A02/A03 identical runs with
    different labels, which is exactly the kind of silent collapse the registry exists to stop.
    """
    _F0, Fm, audit = sm.build_views(g, ctx['horizon_end'], ctx['origin'], seed, p=p)
    return Fm, audit


# ------------------------------------------------------------------ dispatcher
_AUG, _COLS = {}, {}


def _augmented_at(g, ctx):
    """The soil-restored frame for this block's horizon, cached per horizon end."""
    he = pd.Timestamp(ctx['horizon_end'])
    if he not in _AUG:
        _AUG[he] = sf.augmented_features(g.loc[g.index <= he])
    return _AUG[he]


def _frozen_columns(g, name):
    """Column names for an arm, derived ONCE from the full grid so every block scores the
    same set rather than one re-derived from each block's own support."""
    if name not in _COLS:
        _COLS[name] = sf.column_set(g, sf.augmented_features(g), name)
    return _COLS[name]


def run_trial(trial, g, y, ctx, seeds_hbt, seeds_inc, grid_start, view_cache=None):
    """`(q, terms, info)` for one trial at one origin. `q` is unclipped; the caller clips once."""
    comp = trial['component']
    par = trial['params']
    F, idx, train = ctx['F'], ctx['idx'], ctx['train']
    mask = ctx['mask']
    info = dict(component=comp, params=dict(par))
    terms = None

    if comp in ('hbt_params', 'joint_level', 'hbt_view', 'inference_avg') or \
            (comp == 'history' and par['target'] == 'hbt'):
        inc = fit_increments_kw(F, ctx['yh'], mask, seeds_inc)
        terms = a47.increment_terms(F, idx, inc, None, 0.0)

    if comp == 'hbt_params':
        models = fit_hbt(F, y, train, seeds_hbt, par)
        q = predict_hbt(models, F, idx)

    elif comp == 'hbt_features':
        # Only `hbt`'s feature set changes. The increment terms above were built from the
        # incumbent `F`, so a delta here is the level member's columns and nothing else.
        # The column NAMES come from the full grid once -- the support audit reads test
        # EXOGENOUS, which is the shipped transductive policy `low_support` and `stable_core`
        # already use -- and are then applied by name to this block's truncated frame, so
        # every block scores the same set.
        A = _augmented_at(g, ctx)
        cols = [c for c in _frozen_columns(g, par['columns']) if c in A.columns]
        info['n_columns'] = len(cols)
        models = fit_hbt(A[cols], y, train, seeds_hbt)
        q = predict_hbt(models, A[cols], idx)

    elif comp == 'history':
        if par['target'] == 'hbt':
            tr = train[train > pd.Timestamp(ctx['origin']) - pd.Timedelta(days=par['days'])]
            assert len(tr) > 300, 'history window leaves only %d rows' % len(tr)
            info['n_train_used'] = len(tr)
            q = predict_hbt(fit_hbt(F, y, tr, seeds_hbt), F, idx)
        else:
            q = predict_hbt(fit_hbt(F, y, train, seeds_hbt), F, idx)
            m2 = truncate_mask(mask, ctx['origin'], par['days'])
            inc = fit_increments_kw(F, ctx['yh'], m2, seeds_inc)
            info['n_train_used'] = int(m2.sum())
            info['n_edges'] = {h: inc[('n_edges', h)] for h, _l in fp.INC_SPEC}
            terms = a47.increment_terms(F, idx, inc, None, 0.0)

    elif comp == 'inc_params':
        q = predict_hbt(fit_hbt(F, y, train, seeds_hbt), F, idx)
        inc = fit_increments_kw(F, ctx['yh'], mask, seeds_inc, par)
        info['n_edges'] = {h: inc[('n_edges', h)] for h, _l in fp.INC_SPEC}
        terms = a47.increment_terms(F, idx, inc, None, 0.0)

    elif comp == 'hbt_view':
        preds, digests = [], []
        for i, s in enumerate(seeds_hbt):
            aseed = reg.AUG_SEEDS[i % len(reg.AUG_SEEDS)]
            Fm, audit = view_frame(g, ctx, aseed, par['p'])
            if par['mode'] == 'episode':
                take_orig = episode_choice(train, grid_start, aseed, par.get('episode_hours', 24))
                Xtr = F.loc[train].where(pd.Series(take_orig, index=train), Fm.loc[train])
                info['episode_original_share'] = float(take_orig.mean())
            else:
                Xtr = Fm.loc[train]
            assert len(Xtr) == len(train), 'family A keeps exactly n_train rows'
            m = lgb.LGBMRegressor(random_state=s, **reg.hbt_params()).fit(Xtr, y.reindex(train))
            preds.append(m.predict(F.loc[idx]))
            digests.append(sm.audit_digest(audit))
        q = np.mean(preds, axis=0)
        info['aug_digests'] = digests

    elif comp == 'joint_level':
        m = jl.JointLevelModel(par['beta'], seeds_hbt).fit(F.loc[train], y.reindex(train), train)
        q = m.predict(F.loc[idx])
        info.update(m.info())
        info['train_log'] = m.log_[-3:]

    elif comp == 'inference_avg':
        models = fit_hbt(F, y, train, seeds_hbt)
        q_orig = predict_hbt(models, F, idx)
        outs = []
        for vseed in reg.VIEW_SEEDS[:par['n_views']]:
            key = (ctx['horizon_end'], vseed)
            if view_cache is not None and key in view_cache:
                Fs = view_cache[key]
            else:
                Fs, _au = sm.stress_frame(g, ctx['horizon_end'], ctx['origin'], vseed, p=par['p'])
                if view_cache is not None:
                    view_cache[key] = Fs
            outs.append(predict_hbt(models, Fs, idx))
        w = par['weight']
        q = (1.0 - w) * q_orig + w * np.mean(outs, axis=0)
        info['n_views'] = par['n_views']
        info['rms_view_shift'] = float(np.sqrt(np.mean((np.mean(outs, axis=0) - q_orig) ** 2)))

    else:
        raise ValueError('unknown component %r' % comp)

    if terms is None:
        inc = fit_increments_kw(F, ctx['yh'], mask, seeds_inc)
        terms = a47.increment_terms(F, idx, inc, None, 0.0)
    return q, terms, info


def zero_change(g, y, ctx, seeds_hbt, seeds_inc):
    """The control: incumbent hbt and incumbent increments at the given seeds."""
    F, idx, train = ctx['F'], ctx['idx'], ctx['train']
    q = predict_hbt(fit_hbt(F, y, train, seeds_hbt), F, idx)
    inc = fit_increments_kw(F, ctx['yh'], ctx['mask'], seeds_inc)
    return q, a47.increment_terms(F, idx, inc, None, 0.0)
