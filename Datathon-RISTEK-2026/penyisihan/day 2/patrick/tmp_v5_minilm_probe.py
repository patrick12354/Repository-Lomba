from __future__ import annotations

import json
import os
from pathlib import Path

os.environ["USE_TF"] = "0"
os.environ["TRANSFORMERS_NO_TF"] = "1"

import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer


ROOT = Path("/Users/timotiuspatrick/Documents/Patrick/Kuliah & Coding/Dataton/day 2/patrick")
DATA = ROOT.parent / "dataset-task2"
OUTPUT = ROOT / "output/v5"
REPORTS = ROOT / "reports"
MODEL_DIR = OUTPUT / "all-MiniLM-L6-v2"
OUTPUT.mkdir(parents=True, exist_ok=True)

articles = pd.read_csv(DATA / "articles.csv").sort_values("article_id").reset_index(drop=True)
categories = pd.read_csv(DATA / "categories.csv")
category_text = categories.groupby("article_id").category.apply(
    lambda values: " ".join(values.astype(str).str.replace("subject.", "", regex=False).str.replace(".", " ", regex=False))
).to_dict()
article_docs = [f"{row.title}. Categories: {category_text.get(int(row.article_id), '')}" for row in articles.itertuples(index=False)]

if MODEL_DIR.exists():
    model = SentenceTransformer(str(MODEL_DIR), device="cpu")
    model_source = str(MODEL_DIR)
else:
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2", device="cpu")
    model.save(str(MODEL_DIR))
    model_source = "downloaded sentence-transformers/all-MiniLM-L6-v2"

article_embedding_path = OUTPUT / "datathon_task2_v5_minilm_article_embeddings.npz"
if article_embedding_path.exists():
    article_embeddings = np.load(article_embedding_path)["embeddings"].astype(np.float32)
else:
    article_embeddings = model.encode(
        article_docs, batch_size=64, show_progress_bar=True,
        normalize_embeddings=True, convert_to_numpy=True,
    ).astype(np.float32)
    np.savez_compressed(article_embedding_path, embeddings=article_embeddings.astype(np.float16))

pairs = pd.read_csv(REPORTS / "datathon_task2_v5_context_probe_pairs.csv")
context_cache = pd.read_csv(REPORTS / "datathon_task2_v5_context_probe_cache.csv")
contexts = context_cache.context_text.fillna("").astype(str).tolist()
context_embedding_path = OUTPUT / "datathon_task2_v5_minilm_context_embeddings.npz"
if context_embedding_path.exists():
    context_embeddings = np.load(context_embedding_path)["embeddings"].astype(np.float32)
else:
    context_embeddings = model.encode(
        contexts, batch_size=64, show_progress_bar=True,
        normalize_embeddings=True, convert_to_numpy=True,
    ).astype(np.float32)
    np.savez_compressed(
        context_embedding_path,
        source_id=context_cache.source_id.to_numpy(np.int32),
        candidate_id=context_cache.candidate_id.to_numpy(np.int32),
        embeddings=context_embeddings.astype(np.float16),
    )

context_index = {
    (int(row.source_id), int(row.candidate_id)): i
    for i, row in context_cache.reset_index(drop=True).iterrows()
}
rows = []
for row in pairs.itertuples(index=False):
    target = int(row.target_article_id)
    truth = int(row.truth_id)
    prediction = int(row.prediction_id)
    truth_context_idx = context_index[(int(row.current_article_id), truth)]
    pred_context_idx = context_index[(int(row.current_article_id), prediction)]
    target_embedding = article_embeddings[target]
    rows.append({
        "state_id": int(row.state_id),
        "article_truth_similarity": float(article_embeddings[truth] @ target_embedding),
        "article_prediction_similarity": float(article_embeddings[prediction] @ target_embedding),
        "context_truth_similarity": float(context_embeddings[truth_context_idx] @ target_embedding),
        "context_prediction_similarity": float(context_embeddings[pred_context_idx] @ target_embedding),
    })
result = pd.DataFrame(rows)
result["article_prefers_truth"] = result.article_truth_similarity > result.article_prediction_similarity
result["context_prefers_truth"] = result.context_truth_similarity > result.context_prediction_similarity
result.to_csv(REPORTS / "datathon_task2_v5_minilm_probe_pairs.csv", index=False)

report = {
    "model_source": model_source,
    "article_documents": len(article_docs),
    "context_documents": len(contexts),
    "embedding_dimension": int(article_embeddings.shape[1]),
    "error_pairs": len(result),
    "article_semantic_prefers_truth": float(result.article_prefers_truth.mean()),
    "context_semantic_prefers_truth": float(result.context_prefers_truth.mean()),
    "mean_article_margin": float((result.article_truth_similarity - result.article_prediction_similarity).mean()),
    "mean_context_margin": float((result.context_truth_similarity - result.context_prediction_similarity).mean()),
}
(REPORTS / "datathon_task2_v5_minilm_probe_diagnosis.json").write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))
