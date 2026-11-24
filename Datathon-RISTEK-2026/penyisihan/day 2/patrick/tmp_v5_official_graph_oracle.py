from __future__ import annotations

import json
import os
from collections import deque
from pathlib import Path
from urllib.parse import unquote

os.environ.setdefault("MPLBACKEND", "Agg")

import nbformat
import numpy as np
import pandas as pd


ROOT = Path("/Users/timotiuspatrick/Documents/Patrick/Kuliah & Coding/Dataton/day 2/patrick")
SOURCE = ROOT / "notebooks/source/datathon_task2_v4_shortest_path_mass_source.ipynb"
EXTERNAL = ROOT / "output/external/wikispeedia/wikispeedia_paths-and-graph"
REPORTS = ROOT / "reports"


def run_cell(nb, index, namespace):
    exec(compile("".join(nb.cells[index].source), f"v4-cell-{index}", "exec"), namespace)


nb = nbformat.read(SOURCE, as_version=4)
ns = {"display": lambda *args, **kwargs: None}
for index in (2, 4, 6, 8, 12, 14, 16, 18, 20):
    run_cell(nb, index, ns)

articles = ns["articles"]
n_articles = ns["n_articles"]
fold_cache = ns["fold_cache"]
FEATURES = ns["FEATURES"]
evaluate_scores = ns["evaluate_scores"]
V3_FEATURES = ns["V3_FEATURES"]
V3_WEIGHTS = ns["V3_WEIGHTS"]
path_feature_for_pairs = ns["path_feature_for_pairs"]
train = ns["dev_train"]


def decode_title(value):
    return unquote(str(value)).replace("_", " ").strip()


title_to_id = articles.groupby("title").article_id.first().to_dict()
official = pd.read_csv(EXTERNAL / "links.tsv", comment="#", sep="\t", header=None, names=["source", "candidate"])
official["source_id"] = official.source.map(lambda value: title_to_id.get(decode_title(value)))
official["candidate_id"] = official.candidate.map(lambda value: title_to_id.get(decode_title(value)))
assert official[["source_id", "candidate_id"]].notna().all().all()
official = official[["source_id", "candidate_id"]].astype(int).drop_duplicates()
official_candidates = official.groupby("source_id").candidate_id.apply(set).to_dict()
official_reverse = [[] for _ in range(n_articles)]
official_out_degree = np.zeros(n_articles, dtype=np.int32)
official_in_degree = np.zeros(n_articles, dtype=np.int32)
for source, candidate in official.itertuples(index=False):
    official_reverse[candidate].append(source)
    official_out_degree[source] += 1
    official_in_degree[candidate] += 1

distance_cache = {}
path_cache = {}


def official_distance(target):
    target = int(target)
    if target in distance_cache:
        return distance_cache[target]
    dist = np.full(n_articles, 99, dtype=np.int16)
    dist[target] = 0
    queue = deque([target])
    while queue:
        node = queue.popleft()
        next_distance = int(dist[node]) + 1
        for previous in official_reverse[node]:
            if dist[previous] == 99:
                dist[previous] = next_distance
                queue.append(previous)
    distance_cache[target] = dist
    return dist


def official_log_path_mass(target):
    target = int(target)
    if target in path_cache:
        return path_cache[target]
    dist = official_distance(target)
    finite = dist < 99
    counts = np.zeros(n_articles, dtype=np.float64)
    counts[target] = 1.0
    for depth in range(1, int(dist[finite].max()) + 1):
        for node in np.flatnonzero(dist == depth):
            children = np.fromiter(official_candidates.get(int(node), ()), dtype=np.int32)
            if children.size:
                shortest = children[dist[children] == depth - 1]
                if shortest.size:
                    counts[node] = min(1e12, counts[shortest].sum())
    result = np.log1p(counts).astype(np.float32)
    path_cache[target] = result
    return result


state_target = train.set_index("state_id").target_article_id.to_dict()


def oracle_features(qids, candidates):
    frame = pd.DataFrame({"row": np.arange(len(qids)), "state_id": qids.astype(int), "candidate": candidates.astype(int)})
    frame["target"] = frame.state_id.map(state_target).astype(int)
    min_flag = np.zeros(len(frame), dtype=np.float32)
    path_mass = np.zeros(len(frame), dtype=np.float32)
    candidate_distance = np.zeros(len(frame), dtype=np.float32)
    for target, group in frame.groupby("target", sort=False):
        idx = group.row.to_numpy(int)
        cands = group.candidate.to_numpy(int)
        dist = official_distance(int(target))
        values = np.minimum(dist[cands], 20).astype(np.float32)
        state_ids = group.state_id.to_numpy(int)
        minimum = pd.Series(values).groupby(state_ids).transform("min").to_numpy(np.float32)
        min_flag[idx] = values == minimum
        candidate_distance[idx] = values
        path_mass[idx] = official_log_path_mass(int(target))[cands]
    return min_flag, path_mass, candidate_distance


ALPHAS = [-.2, -.1, 0.0, .05, .1, .15, .2, .25, .3, .4, .5]
MIN_WEIGHTS = [20, 50, 100, 150]
rows = []
fold_features = []
full_min_index = FEATURES.index("is_min_neighbor_distance")
for cache in fold_cache:
    fold = cache["fold"]
    x_val, y_val, q_val, c_val = cache["val"]
    v3_score = x_val[:, [FEATURES.index(name) for name in V3_FEATURES]] @ V3_WEIGHTS
    tie_without_graph = v3_score - 100.0 * x_val[:, full_min_index]
    official_min, official_path, official_dist = oracle_features(q_val, c_val)
    fold_features.append((fold, y_val, q_val, c_val, tie_without_graph, official_min, official_path, official_dist))
    for min_weight in MIN_WEIGHTS:
        for alpha in ALPHAS:
            score = tie_without_graph + min_weight * official_min + alpha * official_path
            rows.append({"fold": fold, "min_weight": min_weight, "alpha": alpha, **evaluate_scores(y_val, q_val, c_val, score)})

search = pd.DataFrame(rows)
summary = search.groupby(["min_weight", "alpha"], as_index=False).agg(
    mean_accuracy=("accuracy", "mean"), std_accuracy=("accuracy", "std"),
    top3=("top3", "mean"), top5=("top5", "mean"), candidate_recall=("candidate_recall", "mean"),
).sort_values(["mean_accuracy", "std_accuracy"], ascending=[False, True])
nested_rows = []
for held_fold in range(3):
    selection = search[search.fold.ne(held_fold)].groupby(["min_weight", "alpha"]).accuracy.mean().sort_values(ascending=False)
    min_weight, alpha = selection.index[0]
    held = search[(search.fold.eq(held_fold)) & (search.min_weight.eq(min_weight)) & (search.alpha.eq(alpha))].iloc[0]
    nested_rows.append({"held_fold": held_fold, "min_weight": float(min_weight), "alpha": float(alpha), "selection_accuracy": float(selection.iloc[0]), "held_accuracy": float(held.accuracy)})
nested = pd.DataFrame(nested_rows)

summary.to_csv(REPORTS / "datathon_task2_v5_official_graph_oracle_search.csv", index=False)
nested.to_csv(REPORTS / "datathon_task2_v5_official_graph_oracle_nested.csv", index=False)
best = summary.iloc[0]
report = {
    "official_unique_edges": len(official),
    "ocr_full_unique_edges": int(ns["out_degree"].sum()),
    "missing_edge_gap": int(len(official) - ns["out_degree"].sum()),
    "best_config": best.to_dict(),
    "nested_folds": nested.to_dict("records"),
    "nested_mean": float(nested.held_accuracy.mean()),
    "interpretation": "Uses official graph only, never external navigation-path labels.",
}
(REPORTS / "datathon_task2_v5_official_graph_oracle_diagnosis.json").write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))
