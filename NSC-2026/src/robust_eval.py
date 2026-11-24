"""Leakage-safe evaluation helpers for NSC private-regime robustness experiments."""

from __future__ import annotations

import re

import numpy as np
import pandas as pd


TARGET = "air_humidity"


def support_fraction(train: pd.DataFrame, other: pd.DataFrame) -> pd.Series:
    """Fraction of non-missing values inside the train 1--99% band.

    Missing values are neutral because every production learner already has a deterministic
    missing-value path; the diagnostic is intended to isolate numeric extrapolation.
    """
    common = train.columns.intersection(other.columns)
    lo = train[common].quantile(0.01)
    hi = train[common].quantile(0.99)
    return (((other[common] >= lo) & (other[common] <= hi)) | other[common].isna()).mean()


def _is_pressure_level(name: str) -> bool:
    return (
        name == "pressure"
        or name.startswith("pressure_c")
        or re.fullmatch(r"pressure_s-?\d+", name) is not None
    )


def _is_shifted_range(name: str) -> bool:
    return name.startswith("T_rng") or "air_temperature_qrng" in name or name == "esT_ratio_daily"


def feature_groups(
    columns: list[str] | pd.Index,
    coverage: pd.Series,
    bar: float = 0.916,
) -> dict[str, list[str]]:
    """Build predefined, target-free feature views used by robustness candidates."""
    full = [str(c) for c in columns if str(c) != TARGET]
    pressure_levels = {c for c in full if _is_pressure_level(c)}
    shifted_range = {c for c in full if _is_shifted_range(c)}
    stable = [
        c
        for c in full
        if float(coverage.get(c, 0.0)) >= bar
        and c not in pressure_levels
        and c not in shifted_range
    ]
    return {
        "full": full,
        "no_pressure": [c for c in full if c not in pressure_levels],
        "no_shifted_range": [c for c in full if c not in shifted_range],
        "stable_core": stable,
    }


def block_descriptors(features: pd.DataFrame, block_days: int = 3) -> pd.DataFrame:
    """Summarise consecutive fixed-width blocks without consulting the target."""
    if not isinstance(features.index, pd.DatetimeIndex):
        raise TypeError("features must use a DatetimeIndex")
    if block_days <= 0:
        raise ValueError("block_days must be positive")
    required = {"pressure", "T_rng48"}
    missing = required.difference(features.columns)
    if missing:
        raise ValueError(f"missing descriptor columns: {sorted(missing)}")

    origin = features.index.min()
    width = pd.Timedelta(days=block_days)
    group_number = (features.index - origin) // width
    keys = origin + group_number * width
    grouped = features.groupby(keys)
    out = pd.DataFrame(
        {
            "pressure": grouped["pressure"].median(),
            "temp_range": grouped["T_rng48"].median(),
            "missing": grouped.apply(
                lambda d: float(d.isna().mean().mean()), include_groups=False
            ),
            "n_rows": grouped.size(),
        }
    )
    out.index.name = "block"
    out["block_end"] = out.index + width
    out["season"] = (out.index - origin).total_seconds() / 86400.0
    return out


def score_blocks_against_reference(
    blocks: pd.DataFrame, reference: pd.Series
) -> pd.Series:
    """Higher-is-closer robust distance to a target-free private-regime descriptor."""
    columns = ["pressure", "temp_range", "missing", "season"]
    missing = [c for c in columns if c not in blocks or c not in reference.index]
    if missing:
        raise ValueError(f"missing private-similarity descriptors: {missing}")
    q25 = blocks[columns].quantile(0.25)
    q75 = blocks[columns].quantile(0.75)
    scale = (q75 - q25).replace(0, np.nan)
    scale = scale.fillna(blocks[columns].std()).replace(0, 1.0).fillna(1.0)
    distance = np.sqrt(
        (((blocks[columns] - reference[columns]) / scale) ** 2).mean(axis=1)
    )
    return -distance


def make_stress_splits(
    index: pd.DatetimeIndex,
    descriptors: pd.DataFrame,
    n: int = 3,
    embargo_hours: int = 96,
    min_train_rows: int = 1_000,
) -> list[tuple[pd.DatetimeIndex, pd.DatetimeIndex]]:
    """Select the highest target-free stress blocks and return past-only splits."""
    if "stress_score" not in descriptors or "block_end" not in descriptors:
        raise ValueError("descriptors require stress_score and block_end")
    chosen = descriptors.sort_values("stress_score", ascending=False)
    embargo = pd.Timedelta(hours=embargo_hours)
    splits: list[tuple[pd.DatetimeIndex, pd.DatetimeIndex]] = []
    for start, row in chosen.iterrows():
        valid = index[(index >= start) & (index < row.block_end)]
        train = index[index <= start - embargo]
        if len(valid) == 0 or len(train) < min_train_rows:
            continue
        splits.append((train, valid))
        if len(splits) == n:
            break
    return sorted(splits, key=lambda pair: pair[1].min())


def _check_unique(frame: pd.DataFrame, name: str) -> None:
    keys = ["family", "fold", "datetime"]
    if frame.duplicated(keys).any():
        raise ValueError(f"duplicate fold timestamps in {name}")


def paired_summary(base: pd.DataFrame, candidate: pd.DataFrame) -> pd.DataFrame:
    """Return fold-level paired RMSE differences after one-to-one timestamp matching."""
    _check_unique(base, "base")
    _check_unique(candidate, "candidate")
    keys = ["family", "fold", "datetime", "y"]
    merged = base[keys + ["pred"]].merge(
        candidate[keys + ["pred"]],
        on=keys,
        suffixes=("_base", "_candidate"),
        validate="one_to_one",
    )
    if len(merged) != len(base) or len(merged) != len(candidate):
        raise ValueError("base and candidate rows do not align exactly")
    merged["se_base"] = (merged.pred_base - merged.y) ** 2
    merged["se_candidate"] = (merged.pred_candidate - merged.y) ** 2
    out = (
        merged.groupby(["family", "fold"])
        .agg(
            base=("se_base", lambda x: float(np.sqrt(x.mean()))),
            candidate=("se_candidate", lambda x: float(np.sqrt(x.mean()))),
        )
        .reset_index()
    )
    out["delta"] = out.candidate - out.base
    return out


def passes_gate(
    summary: pd.DataFrame, stress: pd.DataFrame
) -> tuple[bool, list[str]]:
    """Apply the predeclared private-robustness adoption gate."""
    reasons: list[str] = []
    required = {"P", "Q", "R"}
    present = set(summary.family)
    if present != required:
        reasons.append(f"families must be exactly P/Q/R, got {sorted(present)}")
    for family, rows in summary.groupby("family"):
        if float(rows.delta.mean()) >= 0:
            reasons.append(f"family {family} mean did not improve")
    if int((summary.delta < 0).sum()) <= len(summary) / 2:
        reasons.append("no overall fold majority")
    if stress.empty:
        reasons.append("OOD stress result is missing")
    else:
        if float(stress.mean_delta.iloc[0]) > 0 or float(stress.worst_delta.iloc[0]) > 0:
            reasons.append("OOD stress score regressed")
    return not reasons, reasons
