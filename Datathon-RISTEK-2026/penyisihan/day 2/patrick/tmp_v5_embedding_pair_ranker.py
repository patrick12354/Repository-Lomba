from __future__ import annotations

import json
import os
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")

import lightgbm as lgb
import nbformat
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA


ROOT = Path("/Users/timotiuspatrick/Documents/Patrick/Kuliah & Coding/Dataton/day 2/patrick")
SOURCE = ROOT / "notebooks/source/datathon_task2_v4_shortest_path_mass_source.ipynb"
OUTPUT = ROOT / "output/v5"
REPORTS = ROOT / "reports"


def run_cell(nb, index, namespace):
    exec(compile("".join(nb.cells[index].source), f"v4-cell-{index}", "exec"), namespace)


nb = nbformat.read(SOURCE, as_version=4)
ns = {"display": lambda *args, **kwargs: None}
for index in (2, 4, 6, 8, 12, 14, 16, 18, 20):
    run_cell(nb, index, ns)

FEATURES = ns["FEATURES"]
fold_cache = ns["fold_cache"]
evaluate_scores = ns["evaluate_scores"]
V3_FEATURES = ns["V3_FEATURES"]
V3_WEIGHTS = ns["V3_WEIGHTS"]
path_feature_for_pairs = ns["path_feature_for_pairs"]
train = ns["dev_train"]

EMBEDDING_FILE = os.getenv("V5_EMBEDDING_FILE", "datathon_task2_v5_minilm_article_embeddings.npz")
REPORT_TAG = os.getenv("V5_REPORT_TAG", "embedding_pair_ranker")
embedding = np.load(OUTPUT / EMBEDDING_FILE)["embeddings"].astype(np.float32)
embedding /= np.maximum(np.linalg.norm(embedding, axis=1, keepdims=True), 1e-8)
pca = PCA(n_components=48, whiten=True, random_state=42)
embedding_pca = pca.fit_transform(embedding).astype(np.float32)
embedding_pca /= np.maximum(np.linalg.norm(embedding_pca, axis=1, keepdims=True), 1e-8)

state_lookup = train.set_index("state_id")[["current_article_id", "target_article_id"]]
TABULAR = [
    "word_cosine", "char_cosine", "category_exact_jaccard", "category_token_jaccard",
    "log_global_clicks", "log_current_clicks", "log_in_degree", "log_out_degree",
    "word_rank", "char_rank", "position_rank", "category_overlap_count", "category_prefix_jaccard",
    "out_neighbor_jaccard", "in_neighbor_jaccard", "reciprocal_link",
]
TABULAR_INDEX = [FEATURES.index(name) for name in TABULAR]
MIN_INDEX = FEATURES.index("is_min_neighbor_distance")


def pair_embedding_features(qids, candidates):
    frame = pd.DataFrame({"state_id": qids.astype(int), "candidate": candidates.astype(int)})
    frame = frame.join(state_lookup, on="state_id")
    candidate = embedding_pca[frame.candidate.to_numpy(int)]
    target = embedding_pca[frame.target_article_id.to_numpy(int)]
    current = embedding_pca[frame.current_article_id.to_numpy(int)]
    product = candidate * target
    absolute_difference = np.abs(candidate - target)
    direction = candidate - current
    target_direction = target - current
    scalar = np.column_stack([
        np.sum(candidate * target, axis=1),
        np.sum(candidate * current, axis=1),
        np.sum(current * target, axis=1),
        np.sum(direction * target_direction, axis=1),
        np.linalg.norm(target_direction, axis=1) - np.linalg.norm(target - candidate, axis=1),
    ]).astype(np.float32)
    return np.column_stack([product, absolute_difference, candidate, target, scalar]).astype(np.float32)


PARAMS = [
    {"num_leaves": 7, "min_child_samples": 30, "reg_lambda": 8.0},
    {"num_leaves": 15, "min_child_samples": 30, "reg_lambda": 10.0},
    {"num_leaves": 15, "min_child_samples": 60, "reg_lambda": 15.0},
    {"num_leaves": 31, "min_child_samples": 50, "reg_lambda": 20.0},
]
BETAS = [0.0, .05, .1, .2, .3, .5, .8, 1.2, 2.0]


def query_rank(values, qids):
    return pd.DataFrame({"value": values, "qid": qids}).groupby("qid").value.rank(pct=True, method="average").to_numpy(np.float32)


predictions = []
for cache in fold_cache:
    fold = cache["fold"]
    x_fit, y_fit, q_fit, c_fit = cache["fit"]
    x_val, y_val, q_val, c_val = cache["val"]
    fit_min = x_fit[:, MIN_INDEX] == 1
    valid_queries = np.unique(q_fit[fit_min & (y_fit == 1)])
    fit_mask = fit_min & np.isin(q_fit, valid_queries)
    fit_path = path_feature_for_pairs(q_fit, c_fit)
    val_path = path_feature_for_pairs(q_val, c_val)
    x_fit_model = np.column_stack([
        x_fit[fit_mask][:, TABULAR_INDEX], fit_path[fit_mask],
        pair_embedding_features(q_fit[fit_mask], c_fit[fit_mask]),
    ])
    x_val_model = np.column_stack([
        x_val[:, TABULAR_INDEX], val_path,
        pair_embedding_features(q_val, c_val),
    ])
    y_train = y_fit[fit_mask]
    q_train = q_fit[fit_mask]
    sizes = pd.Series(q_train).value_counts().to_dict()
    weights = np.asarray([
        .5 if label == 1 else .5 / max(1, sizes[int(qid)] - 1)
        for label, qid in zip(y_train, q_train)
    ], dtype=np.float32)
    anchor = x_val[:, [FEATURES.index(name) for name in V3_FEATURES]] @ V3_WEIGHTS + .20 * val_path
    for config_id, params in enumerate(PARAMS):
        model = lgb.LGBMClassifier(
            objective="binary", n_estimators=300, learning_rate=.025,
            colsample_bytree=.75, subsample=.9, random_state=42 + fold,
            verbosity=-1, n_jobs=-1, **params,
        )
        model.fit(x_fit_model, y_train, sample_weight=weights)
        probability = model.predict_proba(x_val_model)[:, 1].astype(np.float32)
        predictions.append({
            "fold": fold, "config_id": config_id, "y": y_val, "q": q_val, "c": c_val,
            "anchor": anchor, "probability": probability, "rank": query_rank(probability, q_val),
        })
        print(f"fold={fold} config={config_id}", flush=True)

rows = []
for item in predictions:
    for signal in ("probability", "rank"):
        for beta in BETAS:
            score = item["anchor"] + beta * item[signal]
            rows.append({
                "fold": item["fold"], "config_id": item["config_id"], "signal": signal, "beta": beta,
                **evaluate_scores(item["y"], item["q"], item["c"], score),
            })
search = pd.DataFrame(rows)
summary = search.groupby(["config_id", "signal", "beta"], as_index=False).agg(
    mean_accuracy=("accuracy", "mean"), std_accuracy=("accuracy", "std"),
    top3=("top3", "mean"), top5=("top5", "mean"),
).sort_values(["mean_accuracy", "std_accuracy"], ascending=[False, True])
nested_rows = []
for held_fold in range(3):
    selection = search[search.fold.ne(held_fold)].groupby(["config_id", "signal", "beta"]).accuracy.mean().sort_values(ascending=False)
    config_id, signal, beta = selection.index[0]
    held = search[(search.fold.eq(held_fold)) & (search.config_id.eq(config_id)) & (search.signal.eq(signal)) & (search.beta.eq(beta))].iloc[0]
    nested_rows.append({"held_fold": held_fold, "config_id": int(config_id), "signal": signal, "beta": float(beta), "selection_accuracy": float(selection.iloc[0]), "held_accuracy": float(held.accuracy)})
nested = pd.DataFrame(nested_rows)

summary.to_csv(REPORTS / f"datathon_task2_v5_{REPORT_TAG}_search.csv", index=False)
nested.to_csv(REPORTS / f"datathon_task2_v5_{REPORT_TAG}_nested.csv", index=False)
best = summary.iloc[0]
report = {
    "pca_dimensions": 48,
    "best": best.to_dict(),
    "nested_folds": nested.to_dict("records"),
    "nested_mean": float(nested.held_accuracy.mean()),
}
(REPORTS / f"datathon_task2_v5_{REPORT_TAG}_diagnosis.json").write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))
