"""Reproduce the frozen v12/v16 nested baselines from the existing per-fold caches."""

from __future__ import annotations

import hashlib
import json
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import nnls


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import final_pipeline as fp  # noqa: E402


BASE_MODELS = list(fp.MODELS)
L2_MODELS = list(fp.MODELS_L2)


def assemble_long(
    base_cache: dict,
    l2_cache: dict,
    target: pd.Series,
) -> pd.DataFrame:
    """Align cached member predictions to truth with one row per fold/timestamp."""
    rows = []
    keys = sorted(k for k in base_cache if len(k) == 3 and k[2] == "base")
    for family, fold, _ in keys:
        base = base_cache[(family, fold, "base")].copy()
        if base.index.has_duplicates:
            raise ValueError(f"duplicate timestamps in {family}{fold} base cache")
        l2 = l2_cache.get((family, fold))
        if l2 is None:
            raise ValueError(f"missing L2 predictions for {family}{fold}")
        if l2.index.has_duplicates:
            raise ValueError(f"duplicate timestamps in {family}{fold} L2 cache")
        if not base.index.equals(l2.index):
            raise ValueError(f"member index mismatch in {family}{fold}")
        truth = target.reindex(base.index)
        if truth.isna().any():
            raise ValueError(f"missing truth in {family}{fold}")
        base["l2"] = l2.values
        base["y"] = truth.values
        base["tod"] = base.index.hour + base.index.minute / 60.0
        base["family"] = family
        base["fold"] = int(fold)
        base["datetime"] = base.index
        rows.append(base.reset_index(drop=True))
    out = pd.concat(rows, ignore_index=True)
    if out.duplicated(["family", "fold", "datetime"]).any():
        raise ValueError("duplicate fold timestamps in assembled baseline")
    return out


def fit_meta_predict(
    meta: pd.DataFrame,
    valid: pd.DataFrame,
    models: list[str],
) -> tuple[np.ndarray, dict]:
    """Fit the production meta-stack on labelled OOF rows and predict member rows."""
    if len(meta) < len(models):
        raise ValueError("insufficient meta rows")
    uniform = np.ones(len(models)) / len(models)
    weights, _ = nnls(meta[models].values, meta.y.values)
    weights = weights / weights.sum() if weights.sum() else uniform.copy()
    weights = (1 - fp.BLEND_SHRINK) * weights + fp.BLEND_SHRINK * uniform

    work = meta.copy()
    work["blend"] = np.clip(work[models].values @ weights, 5, 100)
    edges, band_weights = fp.tod_blend_weights(work, weights, models=models)
    work["blend"] = np.clip(
        fp.apply_tod_blend(work[models].values, work.tod.values, edges, band_weights), 5, 100
    )
    pred = np.clip(
        fp.apply_tod_blend(valid[models].values, valid.tod.values, edges, band_weights), 5, 100
    )
    harmonic = fp.harm_bias(work)
    pred = np.clip(fp.apply_harm_bias(pred, valid.tod.values, harmonic), 5, 100)
    return pred, {"weights": weights, "edges": edges, "band_weights": band_weights,
                  "harmonic": harmonic}


def score_stack(frame: pd.DataFrame, models: list[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Nested-LOO blend, time-of-day weights, and harmonic correction."""
    scored = []
    fold_keys = frame[["family", "fold"]].drop_duplicates().itertuples(index=False, name=None)
    for family, fold in fold_keys:
        valid_mask = (frame.family == family) & (frame.fold == fold)
        train = frame.loc[~valid_mask].copy()
        valid = frame.loc[valid_mask].copy()
        valid["pred"], _ = fit_meta_predict(train, valid, models)
        scored.append(valid)

    all_scored = pd.concat(scored, ignore_index=True)
    folds = (
        all_scored.groupby(["family", "fold"])
        .apply(lambda d: fp.rmse(d.y, d.pred), include_groups=False)
        .rename("rmse")
        .reset_index()
    )
    return all_scored, folds


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    base_path = ROOT / "outputs" / "dropblend_oof.pkl"
    l2_path = ROOT / "outputs" / "l2_member.pkl"
    with base_path.open("rb") as handle:
        base_cache = pickle.load(handle)
    with l2_path.open("rb") as handle:
        l2_cache = pickle.load(handle)

    grid = fp.load_grid()
    frame = assemble_long(base_cache, l2_cache, grid[fp.TARGET])
    scored5, folds5 = score_stack(frame, BASE_MODELS)
    scored6, folds6 = score_stack(frame, L2_MODELS)
    joined = folds5.merge(folds6, on=["family", "fold"], suffixes=("_v12", "_v16"))
    joined["delta"] = joined.rmse_v16 - joined.rmse_v12

    result = {
        "rows": int(len(frame)),
        "unique_fold_timestamps": int(
            frame[["family", "fold", "datetime"]].drop_duplicates().shape[0]
        ),
        "v12_mean": float(folds5.rmse.mean()),
        "v16_mean": float(folds6.rmse.mean()),
        "delta": float(joined.delta.mean()),
        "folds_won": int((joined.delta < 0).sum()),
        "n_folds": int(len(joined)),
        "families": {
            family: {
                "v12": float(group.rmse_v12.mean()),
                "v16": float(group.rmse_v16.mean()),
                "delta": float(group.delta.mean()),
                "won": int((group.delta < 0).sum()),
                "n": int(len(group)),
            }
            for family, group in joined.groupby("family")
        },
        "cache_sha256": {"base": _sha256(base_path), "l2": _sha256(l2_path)},
    }
    with (ROOT / "outputs" / "robust_baseline.pkl").open("wb") as handle:
        pickle.dump({"frame": frame, "v12": scored5, "v16": scored6, "folds": joined}, handle)
    (ROOT / "outputs" / "robust_baseline.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8"
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
