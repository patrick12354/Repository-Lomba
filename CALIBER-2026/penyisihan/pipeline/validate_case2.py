"""Quality gates and reproduction checks for data/generated/case2.json.

Each check states what was expected (from the design audit, Appendix A/B of
docs/rancangan_solusi_plantpulse.md) and what the snapshot actually contains.
A failed check is reported, never patched by changing the expectation.
Usage:  python pipeline/validate_case2.py
Writes: data/generated/validation_report.json and validation_report.md
"""
from __future__ import annotations

import json
from collections import Counter
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GEN = ROOT / "data" / "generated"
snap = json.loads((GEN / "case2.json").read_text(encoding="utf-8"))
inc = snap["incidents"]
meta = snap["meta"]
OPEN = set(meta["open_statuses"])
REVIEW = meta["review_date"]

checks: list[dict] = []


def check(cid, gate, description, expected, actual):
    checks.append({"id": cid, "gate": gate, "description": description,
                   "expected": expected, "actual": actual, "pass": expected == actual})


def dsum(rows, key):
    return int(sum((Decimal(r[key] or 0) for r in rows), Decimal(0)))


opened = [r for r in inc if r["status"] in OPEN]

check("V01", "identity", "Incident rows", 380, len(inc))
check("V02", "identity", "Unique snapshot IDs (source + serial)", 380, len({r["id"] for r in inc}))
check("V03", "identity", "AR placeholder 'n/a' rows normalised to null", 226, sum(r["ar"] is None for r in inc))
check("V04", "identity", "Non-placeholder AR values appearing twice",
      {"AR-2026-OP2-0171": 2, "AR-2024-ZCU-0236": 2},
      {k: v for k, v in Counter(r["ar"] for r in inc if r["ar"]).items() if v > 1})
check("V05", "identity", "Distinct (plant, tag) pairs — no same-asset recurrence provable", 380,
      len({(r["plant"], r["tag"]) for r in inc}))
check("V06", "financial", "Recorded actual loss (USD)", 61_886_460, dsum(inc, "actual_usd"))
check("V07", "financial", "Recorded potential loss (USD)", 5_307_970, dsum(inc, "potential_usd"))
check("V08", "financial", "Actual + potential = total on every row", 0,
      sum((r["actual_usd"] + r["potential_usd"]) != r["total_usd"] for r in inc))
check("V09", "status", "Open-status incidents", 220, len(opened))
check("V10", "financial", "Actual loss on open-status incidents (USD)", 39_026_860, dsum(opened, "actual_usd"))
check("V11", "status", f"Open-status with RCA due date before {REVIEW}", 183,
      sum(bool(r["rca_due"]) and r["rca_due"] < REVIEW for r in opened))
check("V12", "financial", "Downtime hours (sum)", "2261.1",
      str(sum((Decimal(str(r["downtime_h"])) for r in inc), Decimal(0))))
check("V13", "identity", "Detailed equipment joined to exactly one incident (tag + AR)", [1, 1, 1, 1, 1],
      [e["join_count"] for e in snap["equipment"]])
five_loss = sum(Decimal(str(next(s["value"] for s in e["summary"] if s["kpi"].startswith("Estimated Loss")))) for e in snap["equipment"])
check("V14", "financial", "Five-case estimated loss (k USD) equals linked incident actual loss", True,
      all(Decimal(str(next(s["value"] for s in e["summary"] if s["kpi"].startswith("Estimated Loss")))) * 1000
          == next(r for r in inc if r["id"] == e["linked_incident"])["actual_usd"] for e in snap["equipment"]))
check("V15", "financial", "Five-case recorded loss (USD)", 2_584_840, int(five_loss * 1000))
check("V16", "time", "Every weekly TRIP falls in week 21", [21] * 5,
      [next(h["week"] for h in e["history"] if h["status"] == "TRIP") for e in snap["equipment"]])
check("V17", "unit", "KO-3201 weekly vibration unit vs hourly PI unit differ (must not be overlaid)",
      ["micron", "MM/S"],
      [next(p["unit"] for p in e["params"] if "Vibration" in p["name"]) for e in snap["equipment"] if e["tag"] == "KO-3201"]
      + [next(t["unit"] for t in h["pi_tags"] if t["name"].endswith("_VIB")) for h in snap["hourly"] if h["tag_prefix"] == "KO3201"])
check("V18", "unit", "Hourly OFF rows that still carry non-zero current (kept as-is, flagged)", 85,
      sum(h["off_with_nonzero_amp"] for h in snap["hourly"]))
check("V19", "unit", "HE-3301 (heat exchanger) has a 'MOTOR AMPERE' PI tag — excluded from motor-energy demo", True,
      any("MOTOR AMPERE" in (t["description"] or "") for h in snap["hourly"] if h["tag_prefix"] == "HE3301" for t in h["pi_tags"]))
check("V20", "time", "Linear-trend flag dates (6-pt fit, ≤8 weeks to trip)",
      {"PU-2101B": "2026-01-29", "KO-3201": "2026-03-25", "PM-4405B": "2026-05-27", "HE-3301": "2026-04-16", "BL-5702": "2026-05-13"},
      {e["tag"]: e["linear_flag"]["date"] for e in snap["equipment"]})
check("V21", "time", "Forecast test window is 168 h for every series", [168] * 5,
      [h["forecast"]["test_hours"] for h in snap["hourly"]])
check("V22", "status", "KO-3201 RCA action statuses (snapshot)", ["Closed", "In Progress", "Open", "Open"],
      [a["status"] for r in snap["rca"] if r["tag"] == "KO-3201" for a in r["actions"]])
check("V23", "status", "KO-3201 retube plan date is after review date (not overdue)", True,
      next(a["plan_date"] for r in snap["rca"] if r["tag"] == "KO-3201" for a in r["actions"] if "Retube" in a["text"]) > REVIEW)

passed = sum(c["pass"] for c in checks)
report = {"review_date": REVIEW, "checks": checks, "passed": passed, "total": len(checks),
          "source_hashes": {k: v["sha256"] for k, v in snap["sources"].items()}}
(GEN / "validation_report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

lines = [f"# Validation report — snapshot reviewed {REVIEW}", "",
         f"**{passed} of {len(checks)} checks pass.** Generated by `pipeline/validate_case2.py` from `data/generated/case2.json`.",
         "Passing these fixtures does not prove the absence of other defects.", "",
         "| ID | Gate | Check | Expected | Actual | Result |", "|---|---|---|---|---|---|"]
for c in checks:
    lines.append(f"| {c['id']} | {c['gate']} | {c['description']} | `{c['expected']}` | `{c['actual']}` | {'pass' if c['pass'] else '**FAIL**'} |")
(GEN / "validation_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
# Ship the summary with the prototype so the Data Foundation panel shows real results.
(ROOT / "prototype" / "src" / "data" / "validation_report.json").write_text(json.dumps(report, ensure_ascii=False), encoding="utf-8")
print(f"{passed}/{len(checks)} checks pass")
for c in checks:
    if not c["pass"]:
        print("FAIL", c["id"], c["description"], "expected", c["expected"], "actual", c["actual"])
raise SystemExit(0 if passed == len(checks) else 1)
