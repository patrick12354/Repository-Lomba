from __future__ import annotations

from collections import deque
from pathlib import Path
import json

import networkx as nx
import numpy as np
import pandas as pd


ROOT = Path("/Users/timotiuspatrick/Documents/Patrick/Kuliah & Coding/Dataton/day 2")
PATRICK = ROOT / "patrick"
DATA = ROOT / "dataset-task2"
RAW = PATRICK / "output/v1/datathon_task2_v1_reusable/task2_v1_ocr_raw_regions.csv"
RECOVERY = PATRICK / "reports/datathon_task2_v3_recovered_edges.csv"
REPORT_CSV = PATRICK / "reports/datathon_task2_v6_bfs_generator_probe.csv"
REPORT_JSON = PATRICK / "reports/datathon_task2_v6_bfs_generator_diagnosis.json"

train = pd.read_csv(DATA / "states_train.csv")
articles = pd.read_csv(DATA / "articles.csv")
title = articles.set_index("article_id").title.astype(str).to_dict()
n_nodes = int(articles.article_id.max()) + 1

raw = pd.read_csv(RAW)
accepted = raw[raw.accepted.fillna(False)].copy()
accepted["source_id"] = accepted.source_id.astype(int)
accepted["candidate_id"] = accepted.candidate_id.astype(int)
accepted["origin"] = "accepted"
recovery = pd.read_csv(RECOVERY)
recovery["box_y"] = recovery.position_y * 2000.0
recovery["box_w"] = 0.0
recovery["box_h"] = 0.0
recovery["origin"] = "recovery"
edges = pd.concat(
    [accepted[["source_id", "candidate_id", "box_x", "box_y", "box_w", "box_h", "origin"]],
     recovery[["source_id", "candidate_id", "box_x", "box_y", "box_w", "box_h", "origin"]]],
    ignore_index=True,
)
edges["candidate_title"] = edges.candidate_id.map(title).fillna("")
edges["row_order"] = np.arange(len(edges))
edges = edges.drop_duplicates(["source_id", "candidate_id"], keep="first")


def adjacency(order_cols, ascending=True):
    frame = edges.sort_values(["source_id", *order_cols], ascending=[True, *([ascending] * len(order_cols))])
    out = [[] for _ in range(n_nodes)]
    for source, candidate in frame[["source_id", "candidate_id"]].itertuples(index=False):
        out[int(source)].append(int(candidate))
    return out


ORDERS = {
    "yx_asc": adjacency(["box_y", "box_x"]),
    "yx_desc": adjacency(["box_y", "box_x"], False),
    "xy_asc": adjacency(["box_x", "box_y"]),
    "candidate_id_asc": adjacency(["candidate_id"]),
    "candidate_id_desc": adjacency(["candidate_id"], False),
    "title_asc": adjacency(["candidate_title"]),
    "title_desc": adjacency(["candidate_title"], False),
    "raw_order": adjacency(["row_order"]),
    "raw_order_reverse": adjacency(["row_order"], False),
}


def forward_bfs_first_hop(source, target, out):
    source, target = int(source), int(target)
    if source == target:
        return source
    seen = np.zeros(n_nodes, dtype=np.uint8)
    first = np.full(n_nodes, -1, dtype=np.int32)
    seen[source] = 1
    q = deque([source])
    while q:
        node = q.popleft()
        for nxt in out[node]:
            if seen[nxt]:
                continue
            seen[nxt] = 1
            first[nxt] = nxt if node == source else first[node]
            if nxt == target:
                return int(first[nxt])
            q.append(nxt)
    return out[source][0] if out[source] else source


def reverse_tree_predictions(target, out, reverse_source_order=False):
    incoming = [[] for _ in range(n_nodes)]
    # Iterating sources in a stable order reproduces a common reverse-BFS tree.
    sources = range(n_nodes - 1, -1, -1) if reverse_source_order else range(n_nodes)
    for source in sources:
        for candidate in out[source]:
            incoming[candidate].append(source)
    next_hop = np.full(n_nodes, -1, dtype=np.int32)
    seen = np.zeros(n_nodes, dtype=np.uint8)
    seen[int(target)] = 1
    q = deque([int(target)])
    while q:
        node = q.popleft()
        for previous in incoming[node]:
            if seen[previous]:
                continue
            seen[previous] = 1
            next_hop[previous] = node
            q.append(previous)
    return next_hop


truth = train.next_article_id.to_numpy(int)
rows = []
predictions = {}
for order_name, out in ORDERS.items():
    pred = np.fromiter(
        (forward_bfs_first_hop(s, t, out) for s, t in train[["current_article_id", "target_article_id"]].itertuples(index=False)),
        dtype=np.int32,
        count=len(train),
    )
    predictions[f"forward__{order_name}"] = pred
    rows.append({"method": f"forward__{order_name}", "accuracy": float((pred == truth).mean())})

    for reverse_sources in (False, True):
        pred = np.empty(len(train), dtype=np.int32)
        for target_id, idx in train.groupby("target_article_id", sort=False).groups.items():
            tree = reverse_tree_predictions(int(target_id), out, reverse_sources)
            currents = train.loc[idx, "current_article_id"].to_numpy(int)
            values = tree[currents]
            fallback = np.asarray([out[c][0] if out[c] else c for c in currents], dtype=np.int32)
            pred[np.asarray(idx)] = np.where(values >= 0, values, fallback)
        suffix = "source_desc" if reverse_sources else "source_asc"
        predictions[f"reverse__{order_name}__{suffix}"] = pred
        rows.append({"method": f"reverse__{order_name}__{suffix}", "accuracy": float((pred == truth).mean())})

# NetworkX's bidirectional shortest path is a separate generator hypothesis.
for order_name in ("yx_asc", "yx_desc", "candidate_id_asc", "candidate_id_desc", "title_asc", "raw_order"):
    out = ORDERS[order_name]
    graph = nx.DiGraph()
    graph.add_nodes_from(range(n_nodes))
    for source in range(n_nodes):
        graph.add_edges_from((source, candidate) for candidate in out[source])
    pred = []
    for source, target in train[["current_article_id", "target_article_id"]].itertuples(index=False):
        try:
            path = nx.bidirectional_shortest_path(graph, int(source), int(target))
            pred.append(path[1] if len(path) > 1 else int(source))
        except nx.NetworkXNoPath:
            pred.append(out[int(source)][0] if out[int(source)] else int(source))
    pred = np.asarray(pred, dtype=np.int32)
    predictions[f"bidirectional__{order_name}"] = pred
    rows.append({"method": f"bidirectional__{order_name}", "accuracy": float((pred == truth).mean())})

result = pd.DataFrame(rows).sort_values("accuracy", ascending=False).reset_index(drop=True)
result.to_csv(REPORT_CSV, index=False)
best_name = result.iloc[0].method
best_pred = predictions[best_name]
diagnosis = {
    "states": len(train),
    "graph_edges": int(sum(map(len, ORDERS["yx_asc"]))),
    "best_method": best_name,
    "best_accuracy": float((best_pred == truth).mean()),
    "top_methods": result.head(12).to_dict("records"),
    "interpretation": "Direct generator-replication probe; no train labels are used to construct an individual prediction.",
}
REPORT_JSON.write_text(json.dumps(diagnosis, indent=2))
print(result.head(20).to_string(index=False))
print(json.dumps(diagnosis, indent=2))
