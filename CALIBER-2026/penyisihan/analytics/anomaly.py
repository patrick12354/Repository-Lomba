"""Robust multivariate anomaly score for hourly PI series. No future data in the reference window."""
from __future__ import annotations
import os, sys
import numpy as np

def detect(series: dict[str, list[float]], run: list[str], t: list[str], reference_hours=168, threshold=4.0, sustain=3) -> list[dict]:
    tags = sorted(series)
    X = np.array([series[k] for k in tags], dtype=float).T
    on = np.array([r == "ON" for r in run])
    ref = X[:reference_hours][on[:reference_hours]]
    med = np.median(ref, axis=0)
    mad = 1.4826 * np.median(np.abs(ref - med), axis=0)
    mad[mad == 0] = 1e-9
    Z = (X - med) / mad
    score = np.sqrt(np.mean(Z ** 2, axis=1))
    score[~on] = 0.0
    off_idx = next((i for i in range(reference_hours, len(run)) if not on[i]), None)
    events, i = [], reference_hours
    while i < len(score):
        if score[i] > threshold and all(score[j] > threshold for j in range(i, min(i + sustain, len(score)))) and i + sustain <= len(score):
            j = i
            while j < len(score) and score[j] > threshold:
                j += 1
            peak = int(i + np.argmax(score[i:j]))
            contrib = sorted(({"tag": tags[k], "z": round(float(Z[peak, k]), 2)} for k in range(len(tags))), key=lambda c: -abs(c["z"]))
            events.append({"start_index": i, "end_index": j - 1, "start_at": t[i], "end_at": t[j - 1], "peak_score": round(float(score[peak]), 2),
                           "contributors": contrib[:4], "first_off_at": t[off_idx] if off_idx is not None else None,
                           "lead_hours": float(off_idx - i) if off_idx is not None and off_idx > i else None})
            i = j
        else:
            i += 1
    return events

def events_for(doc: dict) -> list[dict]:
    # Motor current is an energy proxy, kept out of condition scoring.
    numeric = {k: v for k, v in doc["series"].items() if not k.endswith("_AMP")}
    return detect(numeric, doc["run"], doc["t"])


def main():
    """`python -m analytics.anomaly` writes to Supabase; `--local` runs on the bundled snapshot and prints JSON."""
    if "--local" in sys.argv:
        import json
        from pathlib import Path
        snap = json.loads((Path(__file__).parent.parent / "prototype/src/data/case2.json").read_text(encoding="utf8"))
        out = {h["tag_prefix"]: events_for(h) for h in snap["hourly"]}
        print(json.dumps(out, indent=1))
        return 0
    from supabase import create_client
    sb = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_ROLE_KEY"])
    snap = sb.table("snapshots").select("id").eq("status", "published").single().execute().data
    rows = sb.table("hourly_series").select("tag_prefix,doc").eq("snapshot_id", snap["id"]).execute().data
    sb.table("anomaly_events").delete().eq("snapshot_id", snap["id"]).execute()
    for r in rows:
        evs = events_for(r["doc"])
        for e in evs:
            sb.table("anomaly_events").insert({"snapshot_id": snap["id"], "tag": r["tag_prefix"], "start_at": e["start_at"], "end_at": e["end_at"],
                "peak_score": e["peak_score"], "contributors": e["contributors"], "first_off_at": e["first_off_at"], "lead_hours": e["lead_hours"]}).execute()
        lead = evs[0]["lead_hours"] if evs else None
        print(f"{r['tag_prefix']}: {len(evs)} events; first lead before OFF = {lead} h")
    return 0

if __name__ == "__main__":
    sys.exit(main())
