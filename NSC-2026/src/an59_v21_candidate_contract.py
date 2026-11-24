"""Session 28: loss/provenance primitives shared by bounded candidate experiments.

The four arms are fixed designs. select_final is available for future properly nested
selection, but this round does not silently expand its candidate count into a grid search.
"""
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'outputs' / 'audit_v21_s28'


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()


def lead_hours(idx, origin):
    return np.asarray((pd.DatetimeIndex(idx) - pd.Timestamp(origin)).total_seconds() / 3600.)


def require_matching_config(selected, inference):
    differences = [k for k in set(selected) | set(inference)
                   if selected.get(k) != inference.get(k)]
    if differences:
        raise ValueError('selection/inference mismatch: ' + ', '.join(sorted(differences)))


def select_final(candidates, evaluate_final_loss):
    scores = {key: float(evaluate_final_loss(value)) for key, value in candidates.items()}
    if not scores or not np.isfinite(list(scores.values())).all():
        raise ValueError('final losses must be finite and nonempty')
    return min(scores, key=scores.get), scores


def direction(y, p, q):
    e, u = np.asarray(p) - np.asarray(y), np.asarray(q) - np.asarray(p)
    alignment, movement = float(2*np.mean(e*u)), float(np.mean(u*u))
    return dict(alignment=alignment, movement_mse=movement, d_mse=alignment+movement,
                control_sd=float(np.std(p, ddof=1)), candidate_sd=float(np.std(q, ddof=1)))


def training_record(rows, origin, horizon_end, config):
    rows = pd.DatetimeIndex(rows)
    if len(rows) == 0 or rows.max() > pd.Timestamp(origin):
        raise ValueError('training rows must be nonempty and stop at origin')
    return dict(origin=str(origin), horizon_end=str(horizon_end), n_train=len(rows),
                training_rows_hash=digest(rows.astype(str).tolist()),
                config=config, config_hash=digest(config))


def write_json(path, value):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(value, indent=2, default=str, allow_nan=False), encoding='utf-8')


def join_predictions(base, candidate):
    keys = ['block', 'datetime']
    a, b = base.loc[base.score].copy(), candidate.loc[candidate.score].copy()
    if 'scope' in a:
        a = a.loc[a.scope == 'outer']
    if 'scope' in b:
        b = b.loc[b.scope == 'outer']
    out = a.merge(b[keys + ['recon']], on=keys, suffixes=('', '_q'),
                  how='outer', validate='one_to_one', indicator=True)
    if not out['_merge'].eq('both').all():
        raise ValueError('candidate and control must have identical scored timestamps')
    return out.drop(columns='_merge').sort_values(keys).reset_index(drop=True)
