from __future__ import annotations

import json
import os
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")

import nbformat
import numpy as np
import pandas as pd
from scipy import sparse


ROOT = Path("/Users/timotiuspatrick/Documents/Patrick/Kuliah & Coding/Dataton/day 2/patrick")
SOURCE = ROOT / "notebooks/source/datathon_task2_v4_shortest_path_mass_source.ipynb"
REPORTS = ROOT / "reports"


def run_cell(nb, index, namespace):
    exec(compile("".join(nb.cells[index].source), f"v4-cell-{index}", "exec"), namespace)


nb = nbformat.read(SOURCE, as_version=4)
ns = {"display": lambda *args, **kwargs: None}
for index in (2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24):
    run_cell(nb, index, ns)

n = ns["n_articles"]
links = ns["links_v3"][["source_id", "candidate_id"]].drop_duplicates().astype(int)
out_degree = links.groupby("source_id").size().reindex(range(n), fill_value=0).to_numpy(np.float64)
row = links.source_id.to_numpy(int)
col = links.candidate_id.to_numpy(int)
data = 1.0 / np.maximum(out_degree[row], 1.0)
transition = sparse.csr_matrix((data, (row, col)), shape=(n, n), dtype=np.float64)

FEATURES = ns["FEATURES"]
V3_FEATURES = ns["V3_FEATURES"]
V3_WEIGHTS = ns["V3_WEIGHTS"]
path_feature_for_pairs = ns["path_feature_for_pairs"]
evaluate_scores = ns["evaluate_scores"]
train = ns["train"]
target_lookup = train.set_index("state_id").target_article_id.to_dict()

gammas = [0.30, 0.50, 0.70, 0.85, 0.95]
iterations = 16
targets = sorted(train.target_article_id.unique())
value_cache = {}
for gamma in gammas:
    for target in targets:
        seed = np.zeros(n, dtype=np.float64)
        seed[int(target)] = 1.0
        value = seed.copy()
        frontier = seed.copy()
        for _ in range(iterations):
            frontier = gamma * (transition @ frontier)
            value += frontier
        value_cache[(gamma, int(target))] = np.log1p(1e6 * value).astype(np.float32)

alpha_grid = [-0.20, -0.10, -0.05, -0.02, -0.01, 0.0, 0.01, 0.02, 0.05, 0.10, 0.20, 0.40]
search_rows = []
fold_values = []
for item in ns["fold_cache"]:
    fold = int(item["fold"])
    x, y, q, c = item["val"]
    anchor = x[:, [FEATURES.index(name) for name in V3_FEATURES]] @ V3_WEIGHTS + 0.20 * path_feature_for_pairs(q, c)
    target = np.asarray([target_lookup[int(state)] for state in q], dtype=np.int32)
    for gamma in gammas:
        reach = np.asarray([value_cache[(gamma, int(t))][int(candidate)] for t, candidate in zip(target, c)], dtype=np.float32)
        # Center within each query; only relative reachability matters.
        temp = pd.DataFrame({"q": q, "v": reach})
        reach = (temp.v - temp.groupby("q").v.transform("mean")).to_numpy(np.float32)
        fold_values.append({"fold": fold, "gamma": gamma, "y": y, "q": q, "c": c, "anchor": anchor, "reach": reach})
        for alpha in alpha_grid:
            metrics = evaluate_scores(y, q, c, anchor + alpha * reach)
            search_rows.append({"fold": fold, "gamma": gamma, "alpha": alpha, **metrics})

search = pd.DataFrame(search_rows)
summary = search.groupby(["gamma", "alpha"], as_index=False).agg(
    mean_accuracy=("accuracy", "mean"), std_accuracy=("accuracy", "std"), top3=("top3", "mean"), top5=("top5", "mean")
).sort_values(["mean_accuracy", "std_accuracy"], ascending=[False, True])
nested_rows = []
for held_fold in range(3):
    selection = search[search.fold.ne(held_fold)].groupby(["gamma", "alpha"]).accuracy.mean().sort_values(ascending=False)
    gamma, alpha = map(float, selection.index[0])
    held = search[(search.fold.eq(held_fold)) & (search.gamma.eq(gamma)) & (search.alpha.eq(alpha))].iloc[0]
    nested_rows.append({"held_fold": held_fold, "gamma": gamma, "alpha": alpha, "selection_accuracy": float(selection.iloc[0]), "held_accuracy": float(held.accuracy)})
nested = pd.DataFrame(nested_rows)
summary.to_csv(REPORTS / "datathon_task2_v6_discounted_reachability_search.csv", index=False)
nested.to_csv(REPORTS / "datathon_task2_v6_discounted_reachability_nested.csv", index=False)
diagnosis = {
    "best_same_fold": summary.iloc[0].to_dict(),
    "nested_mean": float(nested.held_accuracy.mean()),
    "nested": nested.to_dict("records"),
    "v4_anchor": 0.7735555555555556,
}
(REPORTS / "datathon_task2_v6_discounted_reachability_diagnosis.json").write_text(json.dumps(diagnosis, indent=2))
print(summary.head(15).to_string(index=False))
print(nested.to_string(index=False))
print(json.dumps(diagnosis, indent=2))
