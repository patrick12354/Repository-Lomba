"""Cluster register records into failure families. Deterministic (fixed seed, sorted output)."""
from __future__ import annotations
import os, sys
import numpy as np
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import silhouette_score

OPEN = {"NEW REGISTERED", "RCA PROCESS", "CA/PA EXECUTION", "MONITORING RESULT"}

def _doc(r: dict) -> str:
    # Structured fields repeated so they outweigh free text.
    return " ".join([f"type_{r['eq_type']}"] * 2 + [f"comp_{r['component'].replace(' ', '_')}"] * 3 + [f"mech_{r['mechanism']}"] + [r["title"]])

def _order(r: dict):
    # "L3-12" -> ("L3", 12): natural order, so the result never depends on how the rows were fetched.
    prefix, _, num = r["id"].rpartition("-")
    return (prefix, int(num) if num.isdigit() else 0, r["id"])


def build_clusters(rows: list[dict], k_range=range(6, 21)) -> list[dict]:
    rows = sorted(rows, key=_order)
    docs = [_doc(r) for r in rows]
    X = TfidfVectorizer(min_df=1, ngram_range=(1, 2)).fit_transform(docs)
    best = None
    for k in k_range:
        if k >= len(rows):
            break
        labels = KMeans(n_clusters=k, n_init=10, random_state=42).fit_predict(X)
        score = silhouette_score(X, labels) if len(set(labels)) > 1 else -1
        if best is None or score > best[0] + 1e-9:
            best = (score, labels)
    labels = best[1]
    vec = TfidfVectorizer(min_df=1).fit(docs)
    out = []
    for lab in sorted(set(labels)):
        idx = [i for i, l in enumerate(labels) if l == lab]
        members = [rows[i] for i in idx]
        tf = np.asarray(vec.transform([docs[i] for i in idx]).mean(axis=0)).ravel()
        terms = [vec.get_feature_names_out()[j] for j in tf.argsort()[::-1][:6]]
        out.append({
            "member_ids": sorted(r["id"] for r in members),
            "plants": sorted({r["plant"] for r in members}),
            "actual_usd": int(sum(r["actual_usd"] for r in members)),
            "open_count": sum(r["status"] in OPEN for r in members),
            "top_terms": terms,
        })
    out.sort(key=lambda c: (-len(c["plants"]), -c["actual_usd"], c["member_ids"][0]))
    for i, c in enumerate(out):
        c["cluster_key"] = f"FP-{i + 1:02d}"
    return out

def main():
    """`python -m analytics.patterns` writes to Supabase; `--local` runs on the bundled snapshot and prints JSON."""
    if "--local" in sys.argv:
        import json
        from pathlib import Path
        snap = json.loads((Path(__file__).parent.parent / "prototype/src/data/case2.json").read_text(encoding="utf8"))
        print(json.dumps(build_clusters(snap["incidents"]), indent=1))
        return 0
    from supabase import create_client
    sb = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_ROLE_KEY"])
    snap = sb.table("snapshots").select("id").eq("status", "published").single().execute().data
    rows = sb.table("incidents").select("id,plant,eq_type,component,mechanism,title,actual_usd,status").eq("snapshot_id", snap["id"]).execute().data
    clusters = build_clusters(rows)
    sb.table("failure_patterns").delete().eq("snapshot_id", snap["id"]).execute()
    sb.table("failure_patterns").insert([{**c, "snapshot_id": snap["id"]} for c in clusters]).execute()
    print(f"{len(clusters)} clusters over {len(rows)} records; {sum(len(c['plants']) > 1 for c in clusters)} span several plants")

if __name__ == "__main__":
    sys.exit(main())
