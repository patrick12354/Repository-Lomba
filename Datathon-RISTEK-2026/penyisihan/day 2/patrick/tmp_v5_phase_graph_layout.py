from __future__ import annotations

import json
import os
from collections import defaultdict, deque
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")
os.environ["USE_TF"] = "0"
os.environ["TRANSFORMERS_NO_TF"] = "1"

import nbformat
import numpy as np
import pandas as pd


ROOT = Path("/Users/timotiuspatrick/Documents/Patrick/Kuliah & Coding/Dataton/day 2/patrick")
SOURCE = ROOT / "notebooks/source/datathon_task2_v4_shortest_path_mass_source.ipynb"
REPORTS = ROOT / "reports"
OUTPUT = ROOT / "output/v5"


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
links = ns["links"]
recovery = ns["recovery"]
raw_ocr = ns["raw_ocr"]
n_articles = ns["n_articles"]
in_degree = ns["in_degree"]

article_embeddings = np.load(OUTPUT / "datathon_task2_v5_minilm_article_embeddings.npz")["embeddings"].astype(np.float32)
article_embeddings /= np.maximum(np.linalg.norm(article_embeddings, axis=1, keepdims=True), 1e-8)


def graph_reverse_adjacency(edge_frame):
    reverse = [[] for _ in range(n_articles)]
    for source, candidate in edge_frame[["source_id", "candidate_id"]].drop_duplicates().astype(int).itertuples(index=False):
        reverse[candidate].append(source)
    return reverse


accepted_edges = links[["source_id", "candidate_id"]].drop_duplicates().copy()
exact_recovery = recovery[recovery.recovery_method.eq("exact_segment")][["source_id", "candidate_id"]]
exact_edges = pd.concat([accepted_edges, exact_recovery], ignore_index=True).drop_duplicates()
full_edges = pd.concat([accepted_edges, recovery[["source_id", "candidate_id"]]], ignore_index=True).drop_duplicates()
reverse_graphs = {
    "accepted": graph_reverse_adjacency(accepted_edges),
    "exact": graph_reverse_adjacency(exact_edges),
    "full": graph_reverse_adjacency(full_edges),
}
distance_caches = {name: {} for name in reverse_graphs}


def graph_distances(graph_name, target):
    target = int(target)
    cache = distance_caches[graph_name]
    if target in cache:
        return cache[target]
    dist = np.full(n_articles, 99, dtype=np.int16)
    dist[target] = 0
    queue = deque([target])
    reverse = reverse_graphs[graph_name]
    while queue:
        node = queue.popleft()
        next_distance = int(dist[node]) + 1
        for previous in reverse[node]:
            if dist[previous] == 99:
                dist[previous] = next_distance
                queue.append(previous)
    cache[target] = dist
    return dist


# Rich layout metadata from every occurrence, not only the first y-position.
accepted_regions = raw_ocr[raw_ocr.status.eq("accepted") & raw_ocr.candidate_id.notna()].copy()
accepted_regions["candidate_id"] = accepted_regions.candidate_id.astype(int)
accepted_regions["x_norm"] = accepted_regions.box_x / accepted_regions.groupby("source_id").box_x.transform("max").clip(lower=1)
layout = accepted_regions.groupby(["source_id", "candidate_id"]).agg(
    first_y=("position_y", "min"), mean_y=("position_y", "mean"), first_x=("x_norm", "min"),
    occurrence_count=("candidate_id", "size"), box_width=("box_w", "max"), box_height=("box_h", "max"),
).reset_index()
layout["lead_like"] = layout.first_y.lt(0.22).astype(float)
layout["top_half"] = layout.first_y.lt(0.50).astype(float)
layout["infobox_like"] = (layout.first_y.lt(0.45) & layout.first_x.gt(0.62)).astype(float)
layout_map = {
    (int(row.source_id), int(row.candidate_id)): (
        float(row.first_y), float(row.mean_y), float(row.first_x), float(row.occurrence_count),
        float(row.box_width), float(row.box_height), float(row.lead_like), float(row.top_half), float(row.infobox_like),
    )
    for row in layout.itertuples(index=False)
}
for row in recovery.itertuples(index=False):
    key = (int(row.source_id), int(row.candidate_id))
    if key not in layout_map:
        x_norm = min(1.0, max(0.0, float(row.box_x) / max(800.0, float(row.box_x) + 200.0)))
        y = float(row.position_y)
        layout_map[key] = (y, y, x_norm, 1.0, 0.0, 0.0, float(y < .22), float(y < .50), float(y < .45 and x_norm > .62))

state_lookup = train.set_index("state_id")[["current_article_id", "target_article_id"]]
EXTRA_FEATURES = [
    "min_accepted", "min_exact", "min_vote_count", "distance_spread",
    "minilm_similarity", "top_proximity", "lead_like", "infobox_like", "log_occurrence",
    "phase_far_degree", "phase_mid_degree", "phase_near_degree",
    "phase_far_semantic", "phase_mid_semantic", "phase_near_semantic",
    "phase_far_top", "phase_mid_top", "phase_near_top",
    "phase_far_occurrence", "phase_mid_occurrence", "phase_near_occurrence",
]


def extra_features(qids, candidates):
    frame = pd.DataFrame({"row": np.arange(len(qids)), "state_id": qids.astype(int), "candidate": candidates.astype(int)})
    frame = frame.join(state_lookup, on="state_id")
    result = np.zeros((len(frame), len(EXTRA_FEATURES)), dtype=np.float32)
    for target, idx_values in frame.groupby("target_article_id", sort=False).groups.items():
        idx = np.asarray(list(idx_values), dtype=int)
        candidates_group = frame.loc[idx, "candidate"].to_numpy(int)
        current_group = frame.loc[idx, "current_article_id"].to_numpy(int)
        distances = {name: graph_distances(name, int(target)) for name in reverse_graphs}
        candidate_dist = np.column_stack([np.minimum(distances[name][candidates_group], 20) for name in ("accepted", "exact", "full")])
        state_min = pd.DataFrame(candidate_dist, index=idx).groupby(frame.loc[idx, "state_id"].to_numpy()).transform("min").to_numpy()
        min_flags = candidate_dist == state_min
        result[idx, 0] = min_flags[:, 0]
        result[idx, 1] = min_flags[:, 1]
        result[idx, 2] = min_flags.sum(axis=1)
        result[idx, 3] = candidate_dist.max(axis=1) - candidate_dist.min(axis=1)
        semantic = np.einsum("ij,j->i", article_embeddings[candidates_group], article_embeddings[int(target)])
        result[idx, 4] = semantic
        layout_values = np.asarray([layout_map.get((int(current), int(candidate)), (1, 1, .5, 1, 0, 0, 0, 0, 0)) for current, candidate in zip(current_group, candidates_group)], dtype=np.float32)
        top = 1.0 - np.clip(layout_values[:, 0], 0, 1)
        occurrence = np.log1p(layout_values[:, 3])
        result[idx, 5] = top
        result[idx, 6] = layout_values[:, 6]
        result[idx, 7] = layout_values[:, 8]
        result[idx, 8] = occurrence
        current_distance = np.minimum(distances["full"][current_group], 20)
        far = current_distance >= 4
        mid = current_distance == 3
        near = current_distance <= 2
        degree = np.log1p(in_degree[candidates_group]).astype(np.float32)
        result[idx, 9] = far * degree
        result[idx, 10] = mid * degree
        result[idx, 11] = near * degree
        result[idx, 12] = far * semantic
        result[idx, 13] = mid * semantic
        result[idx, 14] = near * semantic
        result[idx, 15] = far * top
        result[idx, 16] = mid * top
        result[idx, 17] = near * top
        result[idx, 18] = far * occurrence
        result[idx, 19] = mid * occurrence
        result[idx, 20] = near * occurrence
    return result


fold_data = []
anchor_rows = []
for cache in fold_cache:
    fold = cache["fold"]
    x_val, y_val, q_val, c_val = cache["val"]
    path_mass = path_feature_for_pairs(q_val, c_val)
    anchor = x_val[:, [FEATURES.index(name) for name in V3_FEATURES]] @ V3_WEIGHTS + 0.20 * path_mass
    extra = extra_features(q_val, c_val)
    fold_data.append({"fold": fold, "y": y_val, "q": q_val, "c": c_val, "anchor": anchor, "extra": extra})
    anchor_rows.append({"fold": fold, **evaluate_scores(y_val, q_val, c_val, anchor)})


def make_config(config_id, family, **weights):
    config = {name: 0.0 for name in EXTRA_FEATURES}
    config.update(weights)
    config.update({"config_id": config_id, "family": family})
    return config


configs = [make_config(0, "v4_anchor")]
config_id = 1
# Transparent single-feature ablations.
for feature, grid in {
    "min_accepted": [-3, -1, -.3, .3, 1, 3],
    "min_exact": [-3, -1, -.3, .3, 1, 3],
    "min_vote_count": [-2, -1, -.5, .5, 1, 2, 4],
    "distance_spread": [-1, -.5, -.2, .2, .5, 1],
    "minilm_similarity": [-3, -2, -1, -.5, .5, 1, 2, 3],
    "top_proximity": [-1, -.5, -.2, .2, .5, 1],
    "lead_like": [-1, -.5, -.2, .2, .5, 1],
    "infobox_like": [-1, -.5, -.2, .2, .5, 1],
    "log_occurrence": [-1, -.5, -.2, .2, .5, 1],
}.items():
    for weight in grid:
        configs.append(make_config(config_id, f"single_{feature}", **{feature: weight}))
        config_id += 1

# Literature-informed phase models plus random exploration around plausible ranges.
research_configs = [
    dict(phase_far_degree=.5, phase_mid_top=.5, phase_near_semantic=1.0),
    dict(phase_far_degree=1.0, phase_mid_top=.7, phase_near_semantic=1.5),
    dict(phase_far_semantic=-1.0, phase_mid_top=.5, phase_near_semantic=1.0),
    dict(phase_far_degree=.7, phase_far_semantic=-.7, phase_mid_top=.7, phase_near_semantic=1.5, phase_mid_occurrence=.2),
]
for weights in research_configs:
    configs.append(make_config(config_id, "research_phase", **weights))
    config_id += 1

rng = np.random.default_rng(20260719)
for _ in range(1200):
    weights = {
        "min_accepted": float(rng.uniform(-1.5, 1.5)),
        "min_exact": float(rng.uniform(-1.5, 1.5)),
        "min_vote_count": float(rng.uniform(-1.2, 1.2)),
        "distance_spread": float(rng.uniform(-.5, .5)),
        "phase_far_degree": float(rng.uniform(-.3, 1.5)),
        "phase_mid_degree": float(rng.uniform(-.5, 1.0)),
        "phase_near_degree": float(rng.uniform(-1.0, .5)),
        "phase_far_semantic": float(rng.uniform(-2.5, .5)),
        "phase_mid_semantic": float(rng.uniform(-1.5, 1.5)),
        "phase_near_semantic": float(rng.uniform(-.5, 3.0)),
        "phase_far_top": float(rng.uniform(-.3, 1.0)),
        "phase_mid_top": float(rng.uniform(-.3, 1.5)),
        "phase_near_top": float(rng.uniform(-.7, .7)),
        "phase_far_occurrence": float(rng.uniform(-.3, .7)),
        "phase_mid_occurrence": float(rng.uniform(-.3, .7)),
        "phase_near_occurrence": float(rng.uniform(-.5, .5)),
    }
    configs.append(make_config(config_id, "combined_phase_random", **weights))
    config_id += 1

search_rows = []
for config in configs:
    weights = np.asarray([config[name] for name in EXTRA_FEATURES], dtype=np.float32)
    for data in fold_data:
        score = data["anchor"] + data["extra"] @ weights
        search_rows.append({
            "config_id": config["config_id"], "family": config["family"], "fold": data["fold"],
            **evaluate_scores(data["y"], data["q"], data["c"], score),
        })
search = pd.DataFrame(search_rows)
config_frame = pd.DataFrame(configs)
summary = search.groupby(["config_id", "family"], as_index=False).agg(
    mean_accuracy=("accuracy", "mean"), std_accuracy=("accuracy", "std"),
    top3=("top3", "mean"), top5=("top5", "mean"),
).merge(config_frame, on=["config_id", "family"]).sort_values(["mean_accuracy", "std_accuracy"], ascending=[False, True])

nested_rows = []
for held_fold in range(3):
    selection = search[search.fold.ne(held_fold)].groupby("config_id").accuracy.mean().sort_values(ascending=False)
    selected_id = int(selection.index[0])
    held = search[(search.fold.eq(held_fold)) & (search.config_id.eq(selected_id))].iloc[0]
    nested_rows.append({
        "held_fold": held_fold, "selected_config": selected_id,
        "selection_accuracy": float(selection.iloc[0]), "held_accuracy": float(held.accuracy),
    })
nested = pd.DataFrame(nested_rows)
family_best = summary.groupby("family", as_index=False).first().sort_values("mean_accuracy", ascending=False)

summary.to_csv(REPORTS / "datathon_task2_v5_phase_graph_layout_search.csv", index=False)
nested.to_csv(REPORTS / "datathon_task2_v5_phase_graph_layout_nested.csv", index=False)
family_best.to_csv(REPORTS / "datathon_task2_v5_phase_graph_layout_family_best.csv", index=False)

best = summary.iloc[0]
report = {
    "v4_anchor_folds": [row["accuracy"] for row in anchor_rows],
    "v4_anchor_mean": float(np.mean([row["accuracy"] for row in anchor_rows])),
    "best_same_fold_config": int(best.config_id),
    "best_same_fold_family": str(best.family),
    "best_same_fold_accuracy": float(best.mean_accuracy),
    "best_weights": {name: float(best[name]) for name in EXTRA_FEATURES if float(best[name]) != 0.0},
    "nested_folds": nested.to_dict("records"),
    "nested_mean": float(nested.held_accuracy.mean()),
    "graph_edges": {"accepted": len(accepted_edges), "exact": len(exact_edges), "full": len(full_edges)},
    "configs_tested": len(configs),
}
(REPORTS / "datathon_task2_v5_phase_graph_layout_diagnosis.json").write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))
print("\nFamily best:\n", family_best[["family", "mean_accuracy", "std_accuracy"]].to_string(index=False))
