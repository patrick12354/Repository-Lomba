from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import unquote

import numpy as np
import pandas as pd


ROOT = Path("/Users/timotiuspatrick/Documents/Patrick/Kuliah & Coding/Dataton/day 2/patrick")
DATA = ROOT.parent / "dataset-task2"
EXTERNAL = ROOT / "output/external/wikispeedia/wikispeedia_paths-and-graph"
REPORTS = ROOT / "reports"

articles = pd.read_csv(DATA / "articles.csv")
train = pd.read_csv(DATA / "states_train.csv")
test = pd.read_csv(DATA / "states_test.csv")


def normalize_title(value):
    return unquote(str(value)).replace("_", " ").strip()


external_titles = pd.read_csv(EXTERNAL / "articles.tsv", comment="#", header=None, names=["encoded"], sep="\t")
external_titles["title"] = external_titles.encoded.map(normalize_title)
title_to_id = articles.groupby("title").article_id.first().to_dict()
external_titles["article_id"] = external_titles.title.map(title_to_id)

paths = pd.read_csv(
    EXTERNAL / "paths_finished.tsv", comment="#", sep="\t", header=None,
    names=["user", "timestamp", "duration", "path", "rating"],
)
blacklisted_test_targets = set(test.target_article_id.astype(int))
blacklisted_paths = 0

effective_votes = defaultdict(Counter)
forward_votes = defaultdict(Counter)
transition_rows = 0
mapped_paths = 0
for row in paths.itertuples(index=False):
    tokens = str(row.path).split(";")
    article_tokens = [token for token in tokens if token != "<"]
    if not article_tokens:
        continue
    target_title = normalize_title(article_tokens[-1])
    target = title_to_id.get(target_title)
    if target is None:
        continue
    # Strict leakage firewall: no path whose target appears in competition test
    # may contribute a transition, statistic, prediction, or learned parameter.
    if int(target) in blacklisted_test_targets:
        blacklisted_paths += 1
        continue
    stack = []
    forward_sequence = []
    fully_mapped = True
    for token in tokens:
        if token == "<":
            if len(stack) > 1:
                stack.pop()
            continue
        article_id = title_to_id.get(normalize_title(token))
        if article_id is None:
            fully_mapped = False
            break
        if stack:
            forward_votes[(int(stack[-1]), int(target))][int(article_id)] += 1
            transition_rows += 1
        stack.append(int(article_id))
        forward_sequence.append(int(article_id))
    if not fully_mapped or len(stack) < 2:
        continue
    mapped_paths += 1
    for current, next_article in zip(stack[:-1], stack[1:]):
        effective_votes[(int(current), int(target))][int(next_article)] += 1


def majority_prediction(votes, frame):
    predictions = []
    support = []
    confidence = []
    truth_seen = []
    for row in frame.itertuples(index=False):
        counter = votes.get((int(row.current_article_id), int(row.target_article_id)), Counter())
        if counter:
            article, count = counter.most_common(1)[0]
            predictions.append(int(article))
            support.append(int(sum(counter.values())))
            confidence.append(float(count / sum(counter.values())))
            truth = getattr(row, "next_article_id", None)
            truth_seen.append(bool(truth is not None and int(truth) in counter))
        else:
            predictions.append(np.nan)
            support.append(0)
            confidence.append(0.0)
            truth_seen.append(False)
    return pd.DataFrame({"prediction": predictions, "external_support": support, "external_confidence": confidence, "truth_seen_external": truth_seen})


audit_rows = []
prediction_tables = {}
for name, votes in [("effective_path", effective_votes), ("all_forward_clicks", forward_votes)]:
    train_prediction = majority_prediction(votes, train)
    covered = train_prediction.prediction.notna()
    correct = train_prediction.prediction.eq(train.next_article_id)
    prediction_tables[name] = train_prediction
    audit_rows.append({
        "corpus_policy": name,
        "unique_state_target_keys": len(votes),
        "train_coverage": float(covered.mean()),
        "train_accuracy_covered": float(correct[covered].mean()),
        "train_accuracy_all_if_uncovered_wrong": float(correct.mean()),
        "train_truth_seen_rate": float(train_prediction.truth_seen_external.mean()),
    })
audit = pd.DataFrame(audit_rows)
audit.to_csv(REPORTS / "datathon_task2_v5_wikispeedia_overlap_audit.csv", index=False)

best_policy = audit.sort_values(["train_accuracy_all_if_uncovered_wrong", "train_coverage"], ascending=False).iloc[0].corpus_policy
best_train = prediction_tables[best_policy]
train_pack = pd.concat([train.reset_index(drop=True), best_train.add_prefix("external_")], axis=1)
train_pack.to_csv(REPORTS / "datathon_task2_v5_wikispeedia_train_predictions.csv", index=False)

report = {
    "competition_articles": len(articles),
    "external_articles": len(external_titles),
    "exact_title_matches": int(external_titles.article_id.notna().sum()),
    "finished_paths": len(paths),
    "blacklisted_test_target_paths": blacklisted_paths,
    "fully_mapped_paths": mapped_paths,
    "forward_transition_rows": transition_rows,
    "policies": audit.to_dict("records"),
    "best_policy": str(best_policy),
    "warning": "All paths whose target occurs in competition test are excluded. Fold-level training must additionally exclude each validation fold target.",
}
(REPORTS / "datathon_task2_v5_wikispeedia_overlap_diagnosis.json").write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))
