from __future__ import annotations

import json
import os
from pathlib import Path

os.environ.setdefault("USE_TF", "0")
os.environ.setdefault("TRANSFORMERS_NO_TF", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("MPLBACKEND", "Agg")

import nbformat
import numpy as np
import pandas as pd
from sentence_transformers import CrossEncoder


ROOT = Path("/Users/timotiuspatrick/Documents/Patrick/Kuliah & Coding/Dataton/day 2/patrick")
SOURCE = ROOT / "notebooks/source/datathon_task2_v4_shortest_path_mass_source.ipynb"
MODEL_DIR = ROOT / "output/v6/ms-marco-MiniLM-L-6-v2"
REPORTS = ROOT / "reports"
MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"


def run_cell(nb, index, namespace):
    exec(compile("".join(nb.cells[index].source), f"v4-cell-{index}", "exec"), namespace)


nb = nbformat.read(SOURCE, as_version=4)
ns = {"display": lambda *args, **kwargs: None}
for index in (2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24):
    run_cell(nb, index, ns)

articles = ns["articles"]
categories = ns["categories"]
fold_cache = ns["fold_cache"]
FEATURES = ns["FEATURES"]
V3_FEATURES = ns["V3_FEATURES"]
V3_WEIGHTS = ns["V3_WEIGHTS"]
path_feature_for_pairs = ns["path_feature_for_pairs"]
evaluate_scores = ns["evaluate_scores"]

category_text = categories.groupby("article_id").category.apply(lambda x: "; ".join(sorted(set(map(str, x))))).to_dict()
title = articles.set_index("article_id").title.astype(str).to_dict()


def doc(article_id):
    article_id = int(article_id)
    return f"{title[article_id]}. Categories: {category_text.get(article_id, '')}"


pair_frames = []
fold_items = []
min_index = FEATURES.index("is_min_neighbor_distance")
for item in fold_cache:
    fold = int(item["fold"])
    x, y, q, c = item["val"]
    anchor = x[:, [FEATURES.index(name) for name in V3_FEATURES]] @ V3_WEIGHTS + 0.20 * path_feature_for_pairs(q, c)
    target_lookup = ns["train"].set_index("state_id").target_article_id.to_dict()
    target = np.asarray([target_lookup[int(state)] for state in q], dtype=np.int32)
    minimum = x[:, min_index] > 0.5
    frame = pd.DataFrame({
        "fold": fold,
        "row": np.arange(len(q)),
        "state_id": q.astype(int),
        "candidate_id": c.astype(int),
        "target_id": target,
        "is_min": minimum,
    })
    pair_frames.append(frame[minimum])
    fold_items.append({"fold": fold, "x": x, "y": y, "q": q, "c": c, "anchor": anchor, "minimum": minimum})

pairs = pd.concat(pair_frames, ignore_index=True)
unique = pairs[["target_id", "candidate_id"]].drop_duplicates().reset_index(drop=True)
texts = [(doc(target_id), doc(candidate_id)) for target_id, candidate_id in unique.itertuples(index=False)]

model_source = str(MODEL_DIR) if MODEL_DIR.exists() else MODEL_NAME
model = CrossEncoder(model_source, max_length=256, device="cpu")
scores = model.predict(texts, batch_size=64, show_progress_bar=True).astype(np.float32)
unique["cross_score"] = scores
score_map = {(int(t), int(c)): float(s) for t, c, s in unique.itertuples(index=False)}

alpha_grid = [0.0, 0.01, 0.02, 0.03, 0.05, 0.08, 0.10, 0.15, 0.20, 0.30, 0.50, 0.80, 1.0]
search_rows = []
enriched = []
for item in fold_items:
    frame = pair_frames[item["fold"]]
    cross = np.zeros(len(item["q"]), dtype=np.float32)
    idx = frame.row.to_numpy(int)
    cross[idx] = np.asarray([score_map[(int(t), int(c))] for t, c in frame[["target_id", "candidate_id"]].itertuples(index=False)])
    # Query-wise centering makes the scale comparable across different targets.
    temp = pd.DataFrame({"q": item["q"], "score": cross})
    centered = temp.score - temp.groupby("q").score.transform("mean")
    centered = centered.to_numpy(np.float32)
    enriched.append({**item, "cross": centered})
    for alpha in alpha_grid:
        metrics = evaluate_scores(item["y"], item["q"], item["c"], item["anchor"] + alpha * centered)
        search_rows.append({"fold": item["fold"], "alpha": alpha, **metrics})

search = pd.DataFrame(search_rows)
summary = search.groupby("alpha", as_index=False).agg(
    mean_accuracy=("accuracy", "mean"), std_accuracy=("accuracy", "std"), top3=("top3", "mean"), top5=("top5", "mean")
).sort_values(["mean_accuracy", "std_accuracy"], ascending=[False, True])
nested_rows = []
for held_fold in range(3):
    selection = search[search.fold.ne(held_fold)].groupby("alpha").accuracy.mean().sort_values(ascending=False)
    alpha = float(selection.index[0])
    held_accuracy = float(search[(search.fold.eq(held_fold)) & (search.alpha.eq(alpha))].accuracy.iloc[0])
    nested_rows.append({"held_fold": held_fold, "selected_alpha": alpha, "selection_accuracy": float(selection.iloc[0]), "held_accuracy": held_accuracy})
nested = pd.DataFrame(nested_rows)

MODEL_DIR.parent.mkdir(parents=True, exist_ok=True)
if not MODEL_DIR.exists():
    model.model.save_pretrained(MODEL_DIR)
    model.tokenizer.save_pretrained(MODEL_DIR)
summary.to_csv(REPORTS / "datathon_task2_v6_crossencoder_search.csv", index=False)
nested.to_csv(REPORTS / "datathon_task2_v6_crossencoder_nested.csv", index=False)
diagnosis = {
    "model": MODEL_NAME,
    "unique_pairs": len(unique),
    "best_same_fold": summary.iloc[0].to_dict(),
    "nested_mean": float(nested.held_accuracy.mean()),
    "nested_folds": nested.to_dict("records"),
    "v4_anchor": 0.7735555555555556,
}
(REPORTS / "datathon_task2_v6_crossencoder_diagnosis.json").write_text(json.dumps(diagnosis, indent=2))
print(summary.head(10).to_string(index=False))
print(nested.to_string(index=False))
print(json.dumps(diagnosis, indent=2))
