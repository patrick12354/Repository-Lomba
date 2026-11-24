from __future__ import annotations

import json
import os
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")

import nbformat
import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.decomposition import TruncatedSVD
from sklearn.preprocessing import normalize


ROOT = Path("/Users/timotiuspatrick/Documents/Patrick/Kuliah & Coding/Dataton/day 2/patrick")
SOURCE = ROOT / "notebooks/source/datathon_task2_v3_ocr_recovery_reverse_engineering_source.ipynb"
REPORT_DIR = ROOT / "reports"


def execute_cell(nb, index, namespace):
    source = "".join(nb.cells[index].source)
    exec(compile(source, f"{SOURCE.name}:cell-{index}", "exec"), namespace)


nb = nbformat.read(SOURCE, as_version=4)
ns = {"display": lambda *args, **kwargs: None}
execute_cell(nb, 2, ns)
execute_cell(nb, 4, ns)

# Reuse V3's persisted recovery result. No OCR/fuzzy matching is repeated here.
recovery = pd.read_csv(REPORT_DIR / "datathon_task2_v3_recovered_edges.csv")
recovery["match_score"] = 1.0
recovery = recovery[[
    "source_id", "candidate_id", "ocr_text", "ocr_confidence", "match_score", "position_y", "recovery_method"
]]
links = ns["links"]
links_v3 = pd.concat([links, recovery[links.columns]], ignore_index=True)
links_v3 = links_v3.sort_values(["source_id", "candidate_id", "match_score", "ocr_confidence"], ascending=[True, True, False, False])
links_v3 = links_v3.drop_duplicates(["source_id", "candidate_id"], keep="first").reset_index(drop=True)
ns.update({"recovery": recovery, "links_v3": links_v3})

for index in (10, 14, 16, 18, 20):
    execute_cell(nb, index, ns)

n_articles = ns["n_articles"]
features = ns["FEATURES"]
evaluate_scores = ns["evaluate_scores"]
winner_table = ns["winner_table"]
fold_cache = ns["fold_cache"]
train = ns["dev_train"]
distances_to_target = ns["distances_to_target"]
ocr_candidates = ns["ocr_candidates"]
out_degree = ns["out_degree"]

diagnostics = json.loads((ROOT / "output/v3/datathon_task2_v3_diagnostics.json").read_text())
base_cfg = diagnostics["best_hardmin"]
base_features = [key for key in base_cfg if key != "search_id"]
base_weights = np.asarray([base_cfg[key] for key in base_features], dtype=np.float32)

# Directed OCR graph and low-rank structural representations.
rows = links_v3.source_id.to_numpy(np.int32)
cols = links_v3.candidate_id.to_numpy(np.int32)
adj = sparse.csr_matrix((np.ones(len(rows), dtype=np.float32), (rows, cols)), shape=(n_articles, n_articles))
adj.data[:] = 1.0
adj.eliminate_zeros()
row_normalized = normalize(adj, norm="l1", axis=1)

svd = TruncatedSVD(n_components=96, n_iter=7, random_state=42)
out_embedding = normalize(svd.fit_transform(row_normalized), norm="l2", axis=1).astype(np.float32)
in_svd = TruncatedSVD(n_components=96, n_iter=7, random_state=43)
in_embedding = normalize(in_svd.fit_transform(normalize(adj.T, norm="l1", axis=1)), norm="l2", axis=1).astype(np.float32)


target_graph_cache = {}


def target_graph_features(target):
    target = int(target)
    if target in target_graph_cache:
        return target_graph_cache[target]
    dist = distances_to_target(target)
    finite = dist < 99
    max_distance = int(dist[finite].max()) if finite.any() else 0
    path_count = np.zeros(n_articles, dtype=np.float64)
    path_probability = np.zeros(n_articles, dtype=np.float64)
    path_count[target] = 1.0
    path_probability[target] = 1.0
    # Only propagate through distance-reducing edges, which exactly describes
    # the shortest-path DAG toward this target.
    for depth in range(1, max_distance + 1):
        for node in np.flatnonzero(dist == depth):
            children = np.fromiter(ocr_candidates.get(int(node), ()), dtype=np.int32)
            if children.size == 0:
                continue
            shortest_children = children[dist[children] == depth - 1]
            if shortest_children.size:
                path_count[node] = min(1e12, path_count[shortest_children].sum())
                path_probability[node] = path_probability[shortest_children].sum() / max(1, int(out_degree[node]))
    log_paths = np.log1p(path_count).astype(np.float32)
    log_probability = np.log1p(path_probability * 1e6).astype(np.float32)
    target_graph_cache[target] = (log_paths, log_probability)
    return target_graph_cache[target]


state_lookup = train.set_index("state_id")[["current_article_id", "target_article_id", "next_article_id"]]


def additional_features(qids, candidates):
    frame = pd.DataFrame({"state_id": qids.astype(int), "candidate": candidates.astype(int)})
    frame = frame.join(state_lookup, on="state_id")
    result = np.zeros((len(frame), 8), dtype=np.float32)
    names = [
        "svd_out_cosine", "svd_in_cosine", "svd_cross_cosine",
        "log_shortest_path_count", "log_shortest_path_probability",
        "shortest_path_count_rank", "shortest_path_probability_rank", "shortest_successor_fraction",
    ]
    for target, idx in frame.groupby("target_article_id", sort=False).groups.items():
        idx = np.asarray(list(idx), dtype=int)
        cand = frame.loc[idx, "candidate"].to_numpy(int)
        current = frame.loc[idx, "current_article_id"].to_numpy(int)
        log_paths, log_probability = target_graph_features(int(target))
        result[idx, 0] = np.einsum("ij,j->i", out_embedding[cand], out_embedding[int(target)])
        result[idx, 1] = np.einsum("ij,j->i", in_embedding[cand], in_embedding[int(target)])
        result[idx, 2] = np.einsum("ij,j->i", out_embedding[cand], in_embedding[int(target)])
        result[idx, 3] = log_paths[cand]
        result[idx, 4] = log_probability[cand]
        dist = distances_to_target(int(target))
        successor_fraction = np.zeros(len(cand), dtype=np.float32)
        for j, candidate in enumerate(cand):
            children = np.fromiter(ocr_candidates.get(int(candidate), ()), dtype=np.int32)
            if children.size:
                successor_fraction[j] = np.mean(dist[children] == max(0, int(dist[candidate]) - 1))
        result[idx, 7] = successor_fraction
    feature_frame = pd.DataFrame(result, columns=names)
    # Within-state percentile ranks make path mass comparable across targets.
    feature_frame["state_id"] = qids
    feature_frame[names[5]] = feature_frame.groupby("state_id")[names[3]].rank(pct=True, method="average")
    feature_frame[names[6]] = feature_frame.groupby("state_id")[names[4]].rank(pct=True, method="average")
    return feature_frame[names].to_numpy(np.float32), names


fold_data = []
base_rows = []
for cache in fold_cache:
    fold = cache["fold"]
    x_val, y_val, q_val, c_val = cache["val"]
    base_x = x_val[:, [features.index(name) for name in base_features]]
    base_score = base_x @ base_weights
    extra_x, extra_names = additional_features(q_val, c_val)
    base_metric = evaluate_scores(y_val, q_val, c_val, base_score)
    base_rows.append({"fold": fold, **base_metric})
    fold_data.append({
        "fold": fold, "y": y_val, "q": q_val, "c": c_val,
        "base_score": base_score, "extra": extra_x,
    })


def evaluate_config(weights):
    rows = []
    for data in fold_data:
        score = data["base_score"] + data["extra"] @ np.asarray(weights, dtype=np.float32)
        metric = evaluate_scores(data["y"], data["q"], data["c"], score)
        rows.append({"fold": data["fold"], **metric})
    return rows


# Include zero, single-feature sweeps, and conservative random combinations.
configs = [{"config_id": 0, "family": "baseline", **{name: 0.0 for name in extra_names}}]
config_id = 1
weight_grids = {
    "svd_out_cosine": [-2, -1, -.5, -.2, .2, .5, 1, 2],
    "svd_in_cosine": [-2, -1, -.5, -.2, .2, .5, 1, 2],
    "svd_cross_cosine": [-2, -1, -.5, -.2, .2, .5, 1, 2],
    "log_shortest_path_count": [-.5, -.2, -.1, -.05, .05, .1, .2, .5],
    "log_shortest_path_probability": [-.5, -.2, -.1, -.05, .05, .1, .2, .5],
    "shortest_path_count_rank": [-2, -1, -.5, -.2, .2, .5, 1, 2],
    "shortest_path_probability_rank": [-2, -1, -.5, -.2, .2, .5, 1, 2],
    "shortest_successor_fraction": [-2, -1, -.5, -.2, .2, .5, 1, 2],
}
for name, grid in weight_grids.items():
    for weight in grid:
        cfg = {feature: 0.0 for feature in extra_names}
        cfg[name] = weight
        configs.append({"config_id": config_id, "family": f"single_{name}", **cfg})
        config_id += 1

rng = np.random.default_rng(20260719)
for _ in range(600):
    cfg = {
        "svd_out_cosine": float(rng.uniform(-1.5, 1.5)),
        "svd_in_cosine": float(rng.uniform(-1.5, 1.5)),
        "svd_cross_cosine": float(rng.uniform(-1.5, 1.5)),
        "log_shortest_path_count": float(rng.uniform(-.3, .3)),
        "log_shortest_path_probability": float(rng.uniform(-.3, .3)),
        "shortest_path_count_rank": float(rng.uniform(-1.2, 1.2)),
        "shortest_path_probability_rank": float(rng.uniform(-1.2, 1.2)),
        "shortest_successor_fraction": float(rng.uniform(-1.2, 1.2)),
    }
    configs.append({"config_id": config_id, "family": "combined_random", **cfg})
    config_id += 1

search_rows = []
for cfg in configs:
    weights = [cfg[name] for name in extra_names]
    for metric in evaluate_config(weights):
        search_rows.append({"config_id": cfg["config_id"], "family": cfg["family"], **metric})
search = pd.DataFrame(search_rows)
summary = search.groupby(["config_id", "family"], as_index=False).agg(
    mean_accuracy=("accuracy", "mean"), std_accuracy=("accuracy", "std"),
    mean_top3=("top3", "mean"), mean_top5=("top5", "mean"),
).sort_values(["mean_accuracy", "std_accuracy"], ascending=[False, True])

config_frame = pd.DataFrame(configs)
summary = summary.merge(config_frame, on=["config_id", "family"], how="left")

# Honest nested selection: pick on two folds, report on the untouched third.
nested_rows = []
for held_fold in sorted(search.fold.unique()):
    fit_rank = search[search.fold.ne(held_fold)].groupby("config_id").accuracy.mean().sort_values(ascending=False)
    selected = int(fit_rank.index[0])
    held = search[(search.fold.eq(held_fold)) & (search.config_id.eq(selected))].iloc[0]
    nested_rows.append({
        "held_fold": int(held_fold), "selected_config": selected,
        "selection_accuracy": float(fit_rank.iloc[0]), "held_accuracy": float(held.accuracy),
    })
nested = pd.DataFrame(nested_rows)

# Per-family bests clarify which signal is responsible for any apparent gain.
family_best = summary.sort_values("mean_accuracy", ascending=False).groupby("family", as_index=False).first()
best = summary.iloc[0]
best_cfg = config_frame[config_frame.config_id.eq(int(best.config_id))].iloc[0]
best_weights = [best_cfg[name] for name in extra_names]
winner_rows = []
for data in fold_data:
    score = data["base_score"] + data["extra"] @ np.asarray(best_weights, dtype=np.float32)
    winners = winner_table(data["y"], data["q"], data["c"], score)
    winners["fold"] = data["fold"]
    winner_rows.append(winners)
winners = pd.concat(winner_rows, ignore_index=True)
winners = winners.merge(train[["state_id", "current_article_id", "target_article_id", "next_article_id"]], on="state_id", how="left")

summary.to_csv(REPORT_DIR / "datathon_task2_v4_graph_semantics_search.csv", index=False)
nested.to_csv(REPORT_DIR / "datathon_task2_v4_graph_semantics_nested.csv", index=False)
family_best.to_csv(REPORT_DIR / "datathon_task2_v4_graph_semantics_family_best.csv", index=False)
winners.to_csv(REPORT_DIR / "datathon_task2_v4_graph_semantics_oof_winners.csv", index=False)

report = {
    "base_fold_accuracy": [row["accuracy"] for row in base_rows],
    "base_mean_accuracy": float(np.mean([row["accuracy"] for row in base_rows])),
    "best_same_fold_config": int(best.config_id),
    "best_same_fold_family": str(best.family),
    "best_same_fold_accuracy": float(best.mean_accuracy),
    "best_same_fold_weights": {name: float(best_cfg[name]) for name in extra_names},
    "nested_fold_accuracy": nested.held_accuracy.tolist(),
    "nested_mean_accuracy": float(nested.held_accuracy.mean()),
    "svd_explained_variance_out": float(svd.explained_variance_ratio_.sum()),
    "svd_explained_variance_in": float(in_svd.explained_variance_ratio_.sum()),
    "configs_tested": len(configs),
}
(REPORT_DIR / "datathon_task2_v4_graph_semantics_diagnosis.json").write_text(json.dumps(report, indent=2))

print(json.dumps(report, indent=2))
print("\nFamily best:\n", family_best[["family", "mean_accuracy", "std_accuracy"]].to_string(index=False))
