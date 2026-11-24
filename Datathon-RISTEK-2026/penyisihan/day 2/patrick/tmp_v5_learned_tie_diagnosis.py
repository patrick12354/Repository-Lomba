from __future__ import annotations

import json
import os
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")

import lightgbm as lgb
import nbformat
import numpy as np
import pandas as pd


ROOT = Path("/Users/timotiuspatrick/Documents/Patrick/Kuliah & Coding/Dataton/day 2/patrick")
SOURCE = ROOT / "notebooks/source/datathon_task2_v4_shortest_path_mass_source.ipynb"
REPORTS = ROOT / "reports"


def run_cell(nb, index, ns):
    exec(compile("".join(nb.cells[index].source), f"v4-cell-{index}", "exec"), ns)


nb = nbformat.read(SOURCE, as_version=4)
ns = {"display": lambda *args, **kwargs: None}
for index in (2, 4, 6, 8, 12, 14, 16, 18, 20):
    run_cell(nb, index, ns)

FEATURES = ns["FEATURES"]
fold_cache = ns["fold_cache"]
evaluate_scores = ns["evaluate_scores"]
path_feature_for_pairs = ns["path_feature_for_pairs"]
V3_FEATURES = ns["V3_FEATURES"]
V3_WEIGHTS = ns["V3_WEIGHTS"]
LOCKED_ALPHA = 0.20

MODEL_FEATURES = [
    "word_cosine", "char_cosine", "category_exact_jaccard", "category_token_jaccard",
    "ocr_conf_max", "ocr_conf_mean", "title_match_max", "first_position", "log_mentions",
    "log_global_clicks", "log_current_clicks", "observed_edge", "log_out_degree", "log_in_degree",
    "word_rank", "char_rank", "position_rank", "category_overlap_count", "category_prefix_jaccard",
    "out_neighbor_jaccard", "in_neighbor_jaccard", "reciprocal_link",
]
MODEL_INDEX = [FEATURES.index(name) for name in MODEL_FEATURES]
MIN_INDEX = FEATURES.index("is_min_neighbor_distance")


def query_rank(values, qids):
    frame = pd.DataFrame({"value": values, "qid": qids})
    return frame.groupby("qid").value.rank(pct=True, method="average").to_numpy(np.float32)


PARAMS = [
    {"num_leaves": 7, "min_child_samples": 20, "reg_lambda": 3.0},
    {"num_leaves": 15, "min_child_samples": 20, "reg_lambda": 3.0},
    {"num_leaves": 15, "min_child_samples": 50, "reg_lambda": 5.0},
    {"num_leaves": 31, "min_child_samples": 30, "reg_lambda": 8.0},
]
BETAS = [0.0, 0.1, 0.2, 0.4, 0.7, 1.0, 1.5, 2.0, 3.0]

fold_predictions = []
feature_names = MODEL_FEATURES + ["log_shortest_path_count"]
for cache in fold_cache:
    fold = cache["fold"]
    x_fit, y_fit, q_fit, c_fit = cache["fit"]
    x_val, y_val, q_val, c_val = cache["val"]
    fit_min = x_fit[:, MIN_INDEX] == 1
    val_min = x_val[:, MIN_INDEX] == 1
    # Only train on queries whose true candidate is in the shortest-distance set.
    valid_fit_queries = np.unique(q_fit[fit_min & (y_fit == 1)])
    train_mask = fit_min & np.isin(q_fit, valid_fit_queries)
    train_path = path_feature_for_pairs(q_fit, c_fit)
    val_path = path_feature_for_pairs(q_val, c_val)
    xt = np.column_stack([x_fit[train_mask][:, MODEL_INDEX], train_path[train_mask]])
    yt = y_fit[train_mask]
    qt = q_fit[train_mask]
    xv = np.column_stack([x_val[:, MODEL_INDEX], val_path])
    # Equal total weight per query, then balance positive and negative mass within query.
    sizes = pd.Series(qt).value_counts().to_dict()
    weights = np.asarray([
        0.5 if label == 1 else 0.5 / max(1, sizes[int(qid)] - 1)
        for label, qid in zip(yt, qt)
    ], dtype=np.float32)
    base = x_val[:, [FEATURES.index(name) for name in V3_FEATURES]] @ V3_WEIGHTS + LOCKED_ALPHA * val_path
    for config_id, params in enumerate(PARAMS):
        model = lgb.LGBMClassifier(
            objective="binary", n_estimators=350, learning_rate=0.03,
            subsample=0.9, colsample_bytree=0.9, random_state=42 + fold,
            verbosity=-1, n_jobs=-1, **params,
        )
        model.fit(xt, yt, sample_weight=weights)
        probability = model.predict_proba(xv)[:, 1].astype(np.float32)
        rank = query_rank(probability, q_val)
        fold_predictions.append({
            "fold": fold, "config_id": config_id, "model": model,
            "y": y_val, "q": q_val, "c": c_val, "base": base,
            "probability": probability, "rank": rank,
            "importance": dict(zip(feature_names, model.feature_importances_.tolist())),
        })
        print(f"fold={fold} config={config_id} trained")

rows = []
for item in fold_predictions:
    for signal_name in ("probability", "rank"):
        signal = item[signal_name]
        for beta in BETAS:
            score = item["base"] + beta * signal
            rows.append({
                "fold": item["fold"], "config_id": item["config_id"],
                "signal": signal_name, "beta": beta,
                **evaluate_scores(item["y"], item["q"], item["c"], score),
            })
search = pd.DataFrame(rows)
summary = search.groupby(["config_id", "signal", "beta"], as_index=False).agg(
    mean_accuracy=("accuracy", "mean"), std_accuracy=("accuracy", "std"),
    top3=("top3", "mean"), top5=("top5", "mean"),
).sort_values(["mean_accuracy", "std_accuracy"], ascending=[False, True])

nested_rows = []
for held_fold in range(3):
    train_search = search[search.fold.ne(held_fold)].groupby(["config_id", "signal", "beta"], as_index=False).accuracy.mean()
    selected = train_search.sort_values("accuracy", ascending=False).iloc[0]
    held = search[
        (search.fold.eq(held_fold)) &
        (search.config_id.eq(int(selected.config_id))) &
        (search.signal.eq(selected.signal)) &
        (search.beta.eq(float(selected.beta)))
    ].iloc[0]
    nested_rows.append({
        "held_fold": held_fold, "config_id": int(selected.config_id),
        "signal": selected.signal, "beta": float(selected.beta),
        "selection_accuracy": float(selected.accuracy), "held_accuracy": float(held.accuracy),
    })
nested = pd.DataFrame(nested_rows)

importance_rows = []
for item in fold_predictions:
    for name, value in item["importance"].items():
        importance_rows.append({"fold": item["fold"], "config_id": item["config_id"], "feature": name, "importance": value})
importance = pd.DataFrame(importance_rows)
importance_summary = importance.groupby("feature", as_index=False).importance.mean().sort_values("importance", ascending=False)

summary.to_csv(REPORTS / "datathon_task2_v5_learned_tie_search.csv", index=False)
nested.to_csv(REPORTS / "datathon_task2_v5_learned_tie_nested.csv", index=False)
importance_summary.to_csv(REPORTS / "datathon_task2_v5_learned_tie_importance.csv", index=False)

best = summary.iloc[0]
report = {
    "v4_anchor": 0.7735555555555557,
    "best_same_fold": best.to_dict(),
    "nested_folds": nested.to_dict("records"),
    "nested_mean": float(nested.held_accuracy.mean()),
    "top_features": importance_summary.head(10).to_dict("records"),
}
(REPORTS / "datathon_task2_v5_learned_tie_diagnosis.json").write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))
