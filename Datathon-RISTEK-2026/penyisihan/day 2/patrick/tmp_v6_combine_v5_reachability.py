from __future__ import annotations

import json
import os
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")
os.environ.setdefault("USE_TF", "0")
os.environ.setdefault("TRANSFORMERS_NO_TF", "1")

import nbformat
import numpy as np
import pandas as pd
from scipy import sparse

ROOT = Path("/Users/timotiuspatrick/Documents/Patrick/Kuliah & Coding/Dataton/day 2/patrick")
SOURCE = ROOT / "notebooks/source/datathon_task2_v5_pretrained_semantic_pair_ranker_source.ipynb"
REPORTS = ROOT / "reports"

nb = nbformat.read(SOURCE, as_version=4)
ns = {"display": lambda *args, **kwargs: None}
for index in (2, 4, 6, 8, 11, 12, 14, 15, 17, 20, 22, 24):
    exec(compile("".join(nb.cells[index].source), f"v5-cell-{index}", "exec"), ns)

n = ns["n_articles"]
links = ns["links_v3"][["source_id", "candidate_id"]].drop_duplicates().astype(int)
degree = links.groupby("source_id").size().reindex(range(n), fill_value=0).to_numpy(np.float64)
row, col = links.source_id.to_numpy(int), links.candidate_id.to_numpy(int)
P = sparse.csr_matrix((1.0 / np.maximum(degree[row], 1.0), (row, col)), shape=(n, n))
train = ns["train"]
target_lookup = train.set_index("state_id").target_article_id.to_dict()
targets = sorted(train.target_article_id.unique())
gamma = 0.30
values = {}
for target in targets:
    seed = np.zeros(n); seed[int(target)] = 1.0
    value = seed.copy(); frontier = seed.copy()
    for _ in range(16):
        frontier = gamma * (P @ frontier); value += frontier
    values[int(target)] = np.log1p(1e6 * value).astype(np.float32)

locked = [item for item in ns["predictions"] if item["config_id"] == ns["LOCKED_CONFIG"]]
alphas = [-0.10, -0.08, -0.06, -0.05, -0.04, -0.03, -0.02, -0.01, 0.0, 0.01]
betas = [0.10, 0.15, 0.20, 0.25, 0.30]
rows = []
items = []
for item in locked:
    target = np.asarray([target_lookup[int(q)] for q in item["q"]], dtype=np.int32)
    reach = np.asarray([values[int(t)][int(c)] for t, c in zip(target, item["c"])], dtype=np.float32)
    temp = pd.DataFrame({"q": item["q"], "v": reach})
    reach = (temp.v - temp.groupby("q").v.transform("mean")).to_numpy(np.float32)
    items.append({**item, "reach": reach})
    for beta in betas:
        for alpha in alphas:
            score = item["anchor"] + beta * item["probability"] + alpha * reach
            rows.append({"fold": item["fold"], "beta": beta, "alpha": alpha, **ns["evaluate_scores"](item["y"], item["q"], item["c"], score)})
search = pd.DataFrame(rows)
summary = search.groupby(["beta", "alpha"], as_index=False).agg(mean_accuracy=("accuracy", "mean"), std_accuracy=("accuracy", "std"), top3=("top3", "mean"), top5=("top5", "mean")).sort_values(["mean_accuracy", "std_accuracy"], ascending=[False, True])
nested_rows = []
for held in range(3):
    selection = search[search.fold.ne(held)].groupby(["beta", "alpha"]).accuracy.mean().sort_values(ascending=False)
    beta, alpha = map(float, selection.index[0])
    score = float(search[(search.fold.eq(held)) & (search.beta.eq(beta)) & (search.alpha.eq(alpha))].accuracy.iloc[0])
    nested_rows.append({"held_fold": held, "beta": beta, "alpha": alpha, "selection_accuracy": float(selection.iloc[0]), "held_accuracy": score})
nested = pd.DataFrame(nested_rows)
summary.to_csv(REPORTS / "datathon_task2_v6_v5_reachability_search.csv", index=False)
nested.to_csv(REPORTS / "datathon_task2_v6_v5_reachability_nested.csv", index=False)
report = {"best_same_fold": summary.iloc[0].to_dict(), "nested_mean": float(nested.held_accuracy.mean()), "nested": nested.to_dict("records")}
(REPORTS / "datathon_task2_v6_v5_reachability_diagnosis.json").write_text(json.dumps(report, indent=2))
print(summary.head(15).to_string(index=False)); print(nested.to_string(index=False)); print(json.dumps(report, indent=2))
