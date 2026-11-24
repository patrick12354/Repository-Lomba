"""Test a stable-feature Huber-LightGBM as an additional v16 blend member."""

from __future__ import annotations

import json
import pickle
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "src")]
import final_pipeline as fp  # noqa: E402
from exp43_robust_baseline import fit_meta_predict, score_stack  # noqa: E402
from robust_eval import (  # noqa: E402
    block_descriptors,
    feature_groups,
    make_stress_splits,
    passes_gate,
    score_blocks_against_reference,
    support_fraction,
)


CACHE_PATH = ROOT / "outputs" / "robust_core_oof_v2.pkl"
RESULT_PATH = ROOT / "outputs" / "robust_core_result_v2.json"
MODELS_BASE = list(fp.MODELS_L2)
CANDIDATE = "robust_hbt"


def _fit_member(
    name: str,
    train_x: pd.DataFrame,
    train_y: pd.Series,
    valid_x: pd.DataFrame,
    train_t: pd.Series,
    valid_t: pd.Series,
) -> np.ndarray:
    train_e = train_y.values * fp.es(train_t.values) / 100.0
    return np.clip(
        fp.predict(
            name,
            train_x,
            train_y.values,
            valid_x,
            fp.es(valid_t.values),
            train_e,
            fp.SEEDS_OOF,
        ),
        5,
        100,
    )


def _fold_table(base_folds: pd.DataFrame, candidate_folds: pd.DataFrame) -> pd.DataFrame:
    out = base_folds.merge(candidate_folds, on=["family", "fold"], suffixes=("_base", "_candidate"))
    out["delta"] = out.rmse_candidate - out.rmse_base
    return out


def main() -> None:
    started = time.time()
    grid = fp.load_grid()
    features = fp.make_features(grid)
    target = grid[fp.TARGET]
    index = grid.index
    is_train = (grid.is_test == 0).values & target.notna().values
    is_test = (grid.is_test == 1).values
    coverage = support_fraction(features.loc[is_train], features.loc[is_test])
    groups = feature_groups(features.columns, coverage)
    robust_columns = groups["stable_core"]

    with (ROOT / "outputs" / "robust_baseline.pkl").open("rb") as handle:
        baseline_artifact = pickle.load(handle)
    frame = baseline_artifact["frame"].copy()
    cache = pickle.load(CACHE_PATH.open("rb")) if CACHE_PATH.exists() else {}

    for family, fold in frame[["family", "fold"]].drop_duplicates().itertuples(index=False, name=None):
        key = (family, int(fold))
        valid_index = pd.DatetimeIndex(
            frame.loc[(frame.family == family) & (frame.fold == fold), "datetime"]
        )
        if key in cache:
            cached = cache[key]
            if cached.index.equals(valid_index):
                continue
            raise ValueError(f"stale robust-core cache for {family}{fold}")
        cutoff = valid_index.min() - pd.Timedelta(minutes=30)
        train_mask = is_train & (index <= cutoff)
        valid_mask = index.isin(valid_index)
        prediction = _fit_member(
            "hbt",
            features.loc[train_mask, robust_columns],
            target.loc[train_mask],
            features.loc[valid_mask, robust_columns],
            features.loc[train_mask, "T"],
            features.loc[valid_mask, "T"],
        )
        cache[key] = pd.Series(prediction, index=index[valid_mask])
        with CACHE_PATH.open("wb") as handle:
            pickle.dump(cache, handle)
        print(f"fit {family}{fold} ({len(robust_columns)} columns, {time.time() - started:.0f}s)", flush=True)

    frame[CANDIDATE] = np.nan
    for (family, fold), values in cache.items():
        mask = (frame.family == family) & (frame.fold == fold)
        aligned = values.reindex(pd.DatetimeIndex(frame.loc[mask, "datetime"]))
        if aligned.isna().any():
            raise ValueError(f"robust-core alignment failed for {family}{fold}")
        frame.loc[mask, CANDIDATE] = aligned.values

    scored_base, folds_base = score_stack(frame, MODELS_BASE)
    scored_candidate, folds_candidate = score_stack(frame, MODELS_BASE + [CANDIDATE])
    standard = _fold_table(folds_base, folds_candidate)

    rng = np.random.default_rng(20260904)
    boot = np.array(
        [rng.choice(standard.delta.values, len(standard), replace=True).mean() for _ in range(20_000)]
    )

    train_features = features.loc[is_train]
    descriptors = block_descriptors(train_features, block_days=3)
    private_features = features.loc[is_test].iloc[220:]
    reference = pd.Series(
        {
            "pressure": private_features.pressure.median(),
            "temp_range": private_features.T_rng48.median(),
            "missing": private_features.isna().mean().mean(),
            "season": (private_features.index.min() - train_features.index.min()).total_seconds() / 86400.0,
        }
    )
    descriptors["stress_score"] = score_blocks_against_reference(descriptors, reference)
    stress_splits = make_stress_splits(
        train_features.index, descriptors, n=3, embargo_hours=96, min_train_rows=1_000
    )

    stress_rows = []
    for split_id, (train_index, valid_index) in enumerate(stress_splits):
        train_mask = index.isin(train_index)
        valid_mask = index.isin(valid_index) & is_train
        members = pd.DataFrame(index=index[valid_mask])
        for model in MODELS_BASE:
            members[model] = _fit_member(
                model,
                features.loc[train_mask, MODELS_FEATURES := list(features.columns)],
                target.loc[train_mask],
                features.loc[valid_mask, MODELS_FEATURES],
                features.loc[train_mask, "T"],
                features.loc[valid_mask, "T"],
            )
        members[CANDIDATE] = _fit_member(
            "hbt",
            features.loc[train_mask, robust_columns],
            target.loc[train_mask],
            features.loc[valid_mask, robust_columns],
            features.loc[train_mask, "T"],
            features.loc[valid_mask, "T"],
        )
        members["tod"] = members.index.hour + members.index.minute / 60.0
        members["y"] = target.reindex(members.index).values

        meta = frame[frame.datetime <= train_index.max()].copy()
        pred_base, _ = fit_meta_predict(meta, members, MODELS_BASE)
        pred_candidate, _ = fit_meta_predict(meta, members, MODELS_BASE + [CANDIDATE])
        base_rmse = fp.rmse(members.y, pred_base)
        candidate_rmse = fp.rmse(members.y, pred_candidate)
        stress_rows.append(
            {
                "split": split_id,
                "start": str(valid_index.min()),
                "end": str(valid_index.max()),
                "n_train": int(len(train_index)),
                "n_valid": int(len(valid_index)),
                "base": base_rmse,
                "candidate": candidate_rmse,
                "delta": candidate_rmse - base_rmse,
                "base_bias": float(np.mean(pred_base - members.y.values)),
                "candidate_bias": float(np.mean(pred_candidate - members.y.values)),
            }
        )
        print(f"stress {split_id}: {base_rmse:.4f} -> {candidate_rmse:.4f}", flush=True)

    stress_detail = pd.DataFrame(stress_rows)
    stress_gate = pd.DataFrame(
        {
            "mean_delta": [float(stress_detail.delta.mean())],
            "worst_delta": [float(stress_detail.candidate.max() - stress_detail.base.max())],
        }
    )
    passed, reasons = passes_gate(standard, stress_gate)
    result = {
        "candidate": CANDIDATE,
        "n_features_full": int(features.shape[1]),
        "n_features_robust": int(len(robust_columns)),
        "removed": sorted(set(features.columns) - set(robust_columns)),
        "standard": {
            "base": float(standard.rmse_base.mean()),
            "candidate": float(standard.rmse_candidate.mean()),
            "delta": float(standard.delta.mean()),
            "folds_won": int((standard.delta < 0).sum()),
            "n_folds": int(len(standard)),
            "bootstrap_ci": [float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))],
            "families": {
                family: {
                    "delta": float(group.delta.mean()),
                    "won": int((group.delta < 0).sum()),
                    "n": int(len(group)),
                }
                for family, group in standard.groupby("family")
            },
        },
        "stress": stress_rows,
        "stress_mean_delta": float(stress_gate.mean_delta.iloc[0]),
        "stress_worst_delta": float(stress_gate.worst_delta.iloc[0]),
        "passed": passed,
        "reasons": reasons,
        "seconds": float(time.time() - started),
    }
    RESULT_PATH.write_text(json.dumps(result, indent=2), encoding="utf-8")
    with (ROOT / "outputs" / "robust_core_scored.pkl").open("wb") as handle:
        pickle.dump({"frame": frame, "base": scored_base, "candidate": scored_candidate,
                     "standard": standard, "stress": stress_detail}, handle)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
