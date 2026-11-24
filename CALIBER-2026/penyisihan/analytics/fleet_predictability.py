# analytics/fleet_predictability.py
"""Can the incident register predict which failure family comes next? A time-split test kept as deck evidence.

Family = (equipment type, component). Families ranked by count before the cutoff are used as the "prediction"
for incidents after it. If the top families barely cover later incidents, a failure predictor on this data is not credible.
"""
from __future__ import annotations
import json, sys
from collections import Counter
from datetime import date
from pathlib import Path

ROOT = Path(__file__).parent.parent


def split_test(rows: list[dict], cutoff: str, top_k: int = 10) -> dict:
    fam = lambda r: (r["eq_type"], r["component"])
    before = Counter(fam(r) for r in rows if r["occurred"] < cutoff)
    after = Counter(fam(r) for r in rows if r["occurred"] >= cutoff)
    top = [k for k, _ in sorted(before.items(), key=lambda kv: (-kv[1], kv[0]))[:top_k]]
    families = set(before) | set(after)
    return {
        "cutoff": cutoff, "top_k": top_k, "after_total": sum(after.values()),
        "hits_topk": sum(after[k] for k in top),
        "seen_before": sum(v for k, v in after.items() if k in before),
        "families_total": len(families),
        "topk_family_share": len(top) / len(families) if families else 0.0,
    }


def same_asset_repeats(rows: list[dict]) -> int:
    c = Counter((r["plant"], r["tag"]) for r in rows)
    return sum(1 for v in c.values() if v > 1)


def main() -> int:
    snap = json.loads((ROOT / "prototype/src/data/case2.json").read_text(encoding="utf8"))
    rows = snap["incidents"]
    out = {"rows": len(rows), "same_asset_repeats": same_asset_repeats(rows),
           "splits": [split_test(rows, c) for c in ("2025-01-01", "2025-07-01", "2026-01-01")]}
    run = ROOT / "evaluation/runs" / f"{date.today().isoformat()}_fleet_predictability"
    run.mkdir(parents=True, exist_ok=True)
    (run / "result.json").write_text(json.dumps(out, indent=2), encoding="utf8")
    lines = ["# Fleet predictability time-split (internal)", "",
             f"{out['rows']} register rows; (plant, tag) pairs that repeat: {out['same_asset_repeats']}.", "",
             "| Cutoff | Later incidents | Hit by top-10 earlier families | Top-10 share of all families |", "|---|---|---|---|"]
    for s in out["splits"]:
        lines.append(f"| {s['cutoff']} | {s['after_total']} | {s['hits_topk']} ({100 * s['hits_topk'] / max(1, s['after_total']):.1f}%) | {100 * s['topk_family_share']:.1f}% |")
    lines += ["", "Reading: if the hit rate is close to the family share, history does not tell which family fails next."]
    (run / "result.md").write_text("\n".join(lines) + "\n", encoding="utf8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
