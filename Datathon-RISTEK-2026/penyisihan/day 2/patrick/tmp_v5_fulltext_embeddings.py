from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import unquote

os.environ["USE_TF"] = "0"
os.environ["TRANSFORMERS_NO_TF"] = "1"

import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer


ROOT = Path("/Users/timotiuspatrick/Documents/Patrick/Kuliah & Coding/Dataton/day 2/patrick")
DATA = ROOT.parent / "dataset-task2"
PLAIN = ROOT / "output/external/wikispeedia/plaintext_articles"
OUTPUT = ROOT / "output/v5"

articles = pd.read_csv(DATA / "articles.csv").sort_values("article_id")
text_by_title = {}
for path in PLAIN.glob("*.txt"):
    title = unquote(path.stem).replace("_", " ")
    text_by_title[title] = path.read_text(errors="ignore")

documents = []
missing = []
for row in articles.itertuples(index=False):
    text = text_by_title.get(str(row.title), "")
    if not text:
        missing.append(str(row.title))
    # Keep the title and the leading article content. The encoder itself caps
    # inputs at 256 word pieces, matching the model's intended use.
    documents.append(f"{row.title}. {text}")

model = SentenceTransformer(str(OUTPUT / "all-MiniLM-L6-v2"), device="cpu")
embeddings = model.encode(
    documents, batch_size=32, show_progress_bar=True,
    normalize_embeddings=True, convert_to_numpy=True,
).astype(np.float32)
destination = OUTPUT / "datathon_task2_v5_minilm_fulltext_embeddings.npz"
np.savez_compressed(destination, embeddings=embeddings.astype(np.float16))
print({"documents": len(documents), "missing": len(missing), "shape": embeddings.shape, "path": str(destination)})
