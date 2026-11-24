from __future__ import annotations

import io
import json
import csv
import subprocess
import tempfile
from pathlib import Path

import cv2
import numpy as np
import pandas as pd
from PIL import Image
from scipy import sparse
from sklearn.feature_extraction.text import TfidfVectorizer


ROOT = Path("/Users/timotiuspatrick/Documents/Patrick/Kuliah & Coding/Dataton/day 2/patrick")
DATA = ROOT.parent / "dataset-task2"
REUSE = ROOT / "output/v1/datathon_task2_v1_reusable"
REPORTS = ROOT / "reports"
CACHE = REPORTS / "datathon_task2_v5_context_probe_cache.csv"

articles = pd.read_csv(DATA / "articles.csv").sort_values("article_id").reset_index(drop=True)
categories = pd.read_csv(DATA / "categories.csv")
oof = pd.read_csv(ROOT / "output/v4/datathon_task2_v4_oof_error_pack.csv")
errors = oof[oof.error_type.eq("shortest_tiebreak_error")].copy()
raw = pd.read_csv(REUSE / "task2_v1_ocr_raw_regions.csv")
raw = raw[raw.candidate_id.notna()].copy()
raw["candidate_id"] = raw.candidate_id.astype(int)
recovery = pd.read_csv(REPORTS / "datathon_task2_v3_recovered_edges.csv")

# Probe only the true and V4-predicted link for each remaining tie error.
pairs = []
for row in errors.itertuples(index=False):
    pairs.append({"state_id": int(row.state_id), "source_id": int(row.current_article_id), "target_id": int(row.target_article_id), "candidate_id": int(row.next_article_id), "role": "truth"})
    pairs.append({"state_id": int(row.state_id), "source_id": int(row.current_article_id), "target_id": int(row.target_article_id), "candidate_id": int(row.prediction), "role": "prediction"})
pairs = pd.DataFrame(pairs).drop_duplicates(["source_id", "candidate_id"])

meta = pd.concat([
    raw[["source_id", "candidate_id", "box_x", "box_y", "box_w", "box_h", "ocr_text", "match_score"]],
    recovery.assign(box_y=np.nan, box_w=np.nan, box_h=np.nan, match_score=1.0)[["source_id", "candidate_id", "box_x", "box_y", "box_w", "box_h", "ocr_text", "match_score"]],
], ignore_index=True)
meta = meta.sort_values("match_score", ascending=False).drop_duplicates(["source_id", "candidate_id"])
pairs = pairs.merge(meta, on=["source_id", "candidate_id"], how="left")
pairs = pairs[pairs.box_x.notna()].copy().reset_index(drop=True)


def make_crop(row):
    path = DATA / "screenshots" / f"{int(row.source_id)}.png"
    image = cv2.imread(str(path))
    height, width = image.shape[:2]
    y = float(row.box_y) if pd.notna(row.box_y) else float(recovery.loc[(recovery.source_id.eq(row.source_id)) & (recovery.candidate_id.eq(row.candidate_id)), "position_y"].iloc[0]) * height
    box_h = float(row.box_h) if pd.notna(row.box_h) else 22.0
    box_w = float(row.box_w) if pd.notna(row.box_w) else max(50.0, len(str(row.ocr_text)) * 9.0)
    x0 = max(0, int(float(row.box_x) - 500))
    x1 = min(width, int(float(row.box_x) + box_w + 500))
    y0 = max(0, int(y - 18))
    y1 = min(height, int(y + box_h + 18))
    crop = image[y0:y1, x0:x1]
    crop = cv2.resize(crop, None, fx=1.35, fy=1.35, interpolation=cv2.INTER_CUBIC)
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    return cv2.threshold(gray, 210, 255, cv2.THRESH_BINARY)[1]


def ocr_batches(frame, batch_size=40):
    results = []
    for start in range(0, len(frame), batch_size):
        batch = frame.iloc[start:start + batch_size]
        crops = [make_crop(row) for row in batch.itertuples(index=False)]
        max_width = max(crop.shape[1] for crop in crops)
        heights = [crop.shape[0] + 18 for crop in crops]
        canvas = np.full((sum(heights), max_width + 20), 255, dtype=np.uint8)
        spans = []
        cursor = 0
        for crop, total_height in zip(crops, heights):
            canvas[cursor + 9:cursor + 9 + crop.shape[0], 10:10 + crop.shape[1]] = crop
            spans.append((cursor, cursor + total_height))
            cursor += total_height
        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp:
                temp_path = Path(temp.name)
            Image.fromarray(canvas).save(temp_path)
            command = ["tesseract", str(temp_path), "stdout", "--psm", "6", "tsv"]
            completed = subprocess.run(command, capture_output=True, text=True, timeout=120)
            if completed.returncode != 0:
                raise RuntimeError(completed.stderr[-1000:])
            words = pd.read_csv(
                io.StringIO(completed.stdout), sep="\t", quoting=csv.QUOTE_NONE,
                on_bad_lines="skip", engine="python",
            ).dropna(subset=["text"])
            words = words[pd.to_numeric(words.conf, errors="coerce").fillna(-1).ge(0)]
            for low, high in spans:
                center = words.top + words.height / 2
                selected = words[(center >= low) & (center < high)].sort_values(["top", "left"])
                results.append(" ".join(selected.text.astype(str)).strip())
        finally:
            if temp_path and temp_path.exists():
                temp_path.unlink()
        checkpoint = frame.iloc[:len(results)][["source_id", "candidate_id"]].copy()
        checkpoint["context_text"] = results
        if CACHE.exists():
            checkpoint = pd.concat([pd.read_csv(CACHE), checkpoint], ignore_index=True)
        checkpoint.drop_duplicates(["source_id", "candidate_id"], keep="last").to_csv(CACHE, index=False)
        print(f"context OCR {min(start + batch_size, len(frame))}/{len(frame)}", flush=True)
    return results


if CACHE.exists():
    cached = pd.read_csv(CACHE)
    pairs = pairs.merge(cached[["source_id", "candidate_id", "context_text"]], on=["source_id", "candidate_id"], how="left")
    missing = pairs.context_text.isna()
    if missing.any():
        pairs.loc[missing, "context_text"] = ocr_batches(pairs[missing])
else:
    pairs["context_text"] = ocr_batches(pairs)
pairs[["source_id", "candidate_id", "context_text"]].to_csv(CACHE, index=False)

context_lookup = pairs.set_index(["source_id", "candidate_id"]).context_text.to_dict()
title = articles.set_index("article_id").title.to_dict()
category_doc = categories.groupby("article_id").category.apply(lambda values: " ".join(values.astype(str))).to_dict()
article_docs = [f"{title[i]} {title[i]} {category_doc.get(i, '')}".replace("subject.", " ").replace(".", " ").replace("_", " ") for i in range(len(articles))]
context_docs = pairs.context_text.fillna("").astype(str).tolist()

word = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, min_df=2).fit(article_docs + context_docs)
char = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), sublinear_tf=True, min_df=2, max_features=40000).fit(article_docs + context_docs)
article_word = word.transform(article_docs)
context_word = word.transform(context_docs)
article_char = char.transform(article_docs)
context_char = char.transform(context_docs)
pair_index = {(int(row.source_id), int(row.candidate_id)): i for i, row in pairs.iterrows()}


def cosine_row(matrix_a, row_a, matrix_b, row_b):
    return float(matrix_a[row_a].multiply(matrix_b[row_b]).sum())


analysis_rows = []
for row in errors.itertuples(index=False):
    truth_key = (int(row.current_article_id), int(row.next_article_id))
    pred_key = (int(row.current_article_id), int(row.prediction))
    if truth_key not in pair_index or pred_key not in pair_index:
        continue
    target = int(row.target_article_id)
    ti, pi = pair_index[truth_key], pair_index[pred_key]
    truth_word = cosine_row(context_word, ti, article_word, target)
    pred_word = cosine_row(context_word, pi, article_word, target)
    truth_char = cosine_row(context_char, ti, article_char, target)
    pred_char = cosine_row(context_char, pi, article_char, target)
    analysis_rows.append({
        "state_id": int(row.state_id), "current_article_id": int(row.current_article_id), "target_article_id": target,
        "truth_id": int(row.next_article_id), "prediction_id": int(row.prediction),
        "truth_context": context_lookup[truth_key], "prediction_context": context_lookup[pred_key],
        "truth_word": truth_word, "prediction_word": pred_word,
        "truth_char": truth_char, "prediction_char": pred_char,
    })
analysis = pd.DataFrame(analysis_rows)
analysis["word_prefers_truth"] = analysis.truth_word > analysis.prediction_word
analysis["char_prefers_truth"] = analysis.truth_char > analysis.prediction_char
analysis["combined_prefers_truth"] = (analysis.truth_word + analysis.truth_char) > (analysis.prediction_word + analysis.prediction_char)
analysis.to_csv(REPORTS / "datathon_task2_v5_context_probe_pairs.csv", index=False)

report = {
    "tie_errors": len(errors),
    "unique_pairs_requested": len(pairs),
    "paired_states_with_context": len(analysis),
    "coverage": len(analysis) / len(errors),
    "nonempty_context_rate": float(pairs.context_text.fillna("").str.len().gt(0).mean()),
    "word_similarity_prefers_truth": float(analysis.word_prefers_truth.mean()),
    "char_similarity_prefers_truth": float(analysis.char_prefers_truth.mean()),
    "combined_similarity_prefers_truth": float(analysis.combined_prefers_truth.mean()),
}
(REPORTS / "datathon_task2_v5_context_probe_diagnosis.json").write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))
print(analysis[["truth_context", "prediction_context", "truth_word", "prediction_word"]].head(10).to_string(index=False))
