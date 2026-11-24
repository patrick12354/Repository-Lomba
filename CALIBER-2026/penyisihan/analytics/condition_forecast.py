# analytics/condition_forecast.py
"""Condition and energy forecasts with Chronos-2 (zero-shot), backtested against the linear trend already in the repo.

Pure functions come first and are unit-tested without torch. The Chronos-2 adapter imports `chronos` lazily, so CI
(analytics/requirements.txt) never needs it. Output: prototype/src/data/condition_forecast.json for the offline demo.
"""
from __future__ import annotations
import json, sys
from datetime import date, datetime, timezone
from pathlib import Path
import numpy as np

ROOT = Path(__file__).parent.parent
HORIZON = 8          # weeks
LEVELS = (0.1, 0.5, 0.9)


def _first(path, limit, direction):
    for i, v in enumerate(path):
        if (v >= limit - 1e-9) if direction == "high" else (v <= limit + 1e-9):
            return i + 1
    return None


def crossing_window(q10, q50, q90, limit, direction):
    """Weeks ahead (1-based) at which each quantile path first crosses the limit; None = not within the horizon."""
    if direction == "high":
        return {"earliest": _first(q90, limit, direction), "likely": _first(q50, limit, direction), "latest": _first(q10, limit, direction)}
    return {"earliest": _first(q10, limit, direction), "likely": _first(q50, limit, direction), "latest": _first(q90, limit, direction)}


def linear_offset(values, limit, direction, fit_points=6, horizon=HORIZON):
    y = np.asarray(values[-fit_points:], dtype=float)
    a, b = np.polyfit(np.arange(len(y)), y, 1)
    path = [a * (len(y) - 1 + k) + b for k in range(1, horizon + 1)]
    return _first(path, limit, direction)


def actual_offset(values, cutoff, limit, direction):
    for j in range(cutoff + 1, len(values)):
        if (values[j] >= limit) if direction == "high" else (values[j] <= limit):
            return j - cutoff
    return None


def score_windows(cases, horizon=HORIZON):
    """cases: dicts with actual, earliest, likely, latest (None = beyond horizon) and linear."""
    covered = sum(1 for c in cases if c["earliest"] is not None and c["earliest"] <= c["actual"] <= (c["latest"] or horizon + 1))
    lik = [abs(c["likely"] - c["actual"]) for c in cases if c["likely"] is not None]
    lin = [abs(c["linear"] - c["actual"]) for c in cases if c["linear"] is not None]
    return {"cases": len(cases), "coverage": covered / len(cases) if cases else 0.0,
            "mae_likely": float(np.mean(lik)) if lik else None, "missed_likely": sum(1 for c in cases if c["likely"] is None),
            "linear_mae": float(np.mean(lin)) if lin else None, "linear_missed": sum(1 for c in cases if c["linear"] is None)}


def exceed_events(actual, lo, hi, run, t, first_off, sustain=3):
    """Hours where any running signal leaves its forecast band for `sustain`+ consecutive hours."""
    n = len(run)
    flags = [[k for k in actual if run[i] == "ON" and lo[k][i] is not None and not (lo[k][i] <= actual[k][i] <= hi[k][i])] for i in range(n)]
    events, i = [], 0
    while i < n:
        if flags[i] and i + sustain <= n and all(flags[j] for j in range(i, i + sustain)):
            j = i
            while j < n and flags[j]:
                j += 1
            events.append({"start_index": i, "end_index": j - 1, "start_at": t[i], "end_at": t[j - 1],
                           "tags": sorted({k for x in range(i, j) for k in flags[x]}),
                           "lead_hours": float(first_off - i) if first_off is not None and first_off > i else None})
            i = j
        else:
            i += 1
    return events


def _qcol(df, level):
    return str(level) if str(level) in df.columns else level


def load_pipeline():
    from chronos import Chronos2Pipeline  # lazy: keeps CI free of torch
    return Chronos2Pipeline.from_pretrained("amazon/chronos-2", device_map="cpu")


def weekly_quantiles(pipeline, series, horizon=HORIZON, levels=LEVELS):
    """series: {id: (dates, values)} → {id: {level: [horizon floats]}}."""
    import pandas as pd
    # Series have a regular 7-day step but different weekdays; Chronos needs one shared frequency, so use a common weekly anchor.
    anchor = pd.Timestamp("2026-01-01")
    rows = [{"id": k, "timestamp": anchor + pd.Timedelta(days=7 * i), "target": float(v)} for k, (ds, vs) in series.items() for i, (d, v) in enumerate(zip(ds, vs))]
    pred = pipeline.predict_df(pd.DataFrame(rows), prediction_length=horizon, quantile_levels=list(levels),
                               id_column="id", timestamp_column="timestamp", target="target")
    return {k: {q: g.sort_values("timestamp")[_qcol(g, q)].astype(float).tolist() for q in levels} for k, g in pred.groupby("id")}


def hourly_bands(pipeline, doc, targets, context=168, step=24, levels=(0.05, 0.95)):
    """Rolling 24 h forecasts from the previous 168 h, with PLANT_RATE as a covariate. Returns lo/hi per target per hour."""
    import pandas as pd
    n = len(doc["t"]); ts = pd.to_datetime(doc["t"]); s = doc["series"]
    lo = {k: [None] * n for k in targets}; hi = {k: [None] * n for k in targets}
    ctx, fut = [], []
    for start in range(context, n - step + 1, step):
        wid = f"w{start}"
        ctx += [{"id": wid, "timestamp": ts[i], **{k: s[k][i] for k in targets}, "PLANT_RATE": s["PLANT_RATE"][i]} for i in range(start - context, start)]
        fut += [{"id": wid, "timestamp": ts[i], "PLANT_RATE": s["PLANT_RATE"][i]} for i in range(start, start + step)]
    pred = pipeline.predict_df(pd.DataFrame(ctx), future_df=pd.DataFrame(fut), prediction_length=step, quantile_levels=list(levels),
                               id_column="id", timestamp_column="timestamp", target=list(targets))
    for (wid, name), g in pred.groupby(["id", "target_name"]):
        start = int(wid[1:])
        for j, (_, r) in enumerate(g.sort_values("timestamp").iterrows()):
            lo[name][start + j] = float(r[_qcol(g, levels[0])]); hi[name][start + j] = float(r[_qcol(g, levels[1])])
    return lo, hi


def energy_forecast(pipeline, doc):
    """Motor current (A) for the test window, same split as the naive baselines in the snapshot, PLANT_RATE as covariate."""
    import pandas as pd
    fc = doc["forecast"]; train = fc["train_hours"]; target = fc["target"]; n = len(doc["t"])
    ts = pd.to_datetime(doc["t"]); s = doc["series"]
    ctx = pd.DataFrame({"id": "e", "timestamp": ts[:train], target: s[target][:train], "PLANT_RATE": s["PLANT_RATE"][:train]})
    fut = pd.DataFrame({"id": "e", "timestamp": ts[train:n], "PLANT_RATE": s["PLANT_RATE"][train:n]})
    pred = pipeline.predict_df(ctx, future_df=fut, prediction_length=n - train, quantile_levels=[0.1, 0.5, 0.9],
                               id_column="id", timestamp_column="timestamp", target=target).sort_values("timestamp")
    p50 = pred[_qcol(pred, 0.5)].astype(float).tolist()
    actual = s[target][train:n]
    wape = 100 * sum(abs(a - p) for a, p in zip(actual, p50)) / sum(abs(a) for a in actual)
    return {"p10": pred[_qcol(pred, 0.1)].astype(float).round(3).tolist(), "p50": [round(v, 3) for v in p50],
            "p90": pred[_qcol(pred, 0.9)].astype(float).round(3).tolist(), "wape_pct": round(wape, 2)}


def main() -> int:
    snap = json.loads((ROOT / "prototype/src/data/case2.json").read_text(encoding="utf8"))
    pipe = load_pipeline()
    # Weekly backtest: every param, every cutoff from the end of the baseline to the week before the trip.
    series, meta = {}, {}
    for eq in snap["equipment"]:
        vals = np.array([h["values"] for h in eq["history"]]); dates = [h["date"] for h in eq["history"]]
        trip = [h["status"] for h in eq["history"]].index("TRIP")
        for pi, p in enumerate(eq["params"]):
            for c in range(5, trip):
                k = f"{eq['tag']}|{pi}|{c}"
                series[k] = (dates[: c + 1], vals[: c + 1, pi].tolist()); meta[k] = (eq, pi, p, c, vals[:, pi].tolist())
    q = weekly_quantiles(pipe, series)
    cases, display = [], {}
    for k, (eq, pi, p, c, full) in meta.items():
        w_trip = crossing_window(q[k][0.1], q[k][0.5], q[k][0.9], p["trip"], p["direction"])
        act = actual_offset(full, c, p["trip"], p["direction"])
        lin = linear_offset(full[: c + 1], p["trip"], p["direction"])
        if act is not None and act <= HORIZON:
            cases.append({"actual": act, **w_trip, "linear": lin, "tag": eq["tag"], "param": p["name"], "cutoff": c})
        first_alarm = [h["status"] for h in eq["history"]].index("ALARM")
        if c == max(first_alarm, 5):
            display.setdefault(eq["tag"], {"cutoff_index": c, "cutoff_date": eq["history"][c]["date"], "params": []})["params"].append({
                "name": p["name"], "unit": p["unit"], "direction": p["direction"], "alarm": p["alarm"], "trip": p["trip"],
                "q10": [round(v, 3) for v in q[k][0.1]], "q50": [round(v, 3) for v in q[k][0.5]], "q90": [round(v, 3) for v in q[k][0.9]],
                "alarm_window": crossing_window(q[k][0.1], q[k][0.5], q[k][0.9], p["alarm"], p["direction"]),
                "trip_window": w_trip, "linear_trip_offset": lin, "actual_trip_offset": act})
    backtest = score_windows(cases)
    # Hourly bands vs the existing MAD detector (first OFF hour after the 168 h reference = the shutdown).
    hourly = {}
    for doc in snap["hourly"]:
        targets = [k for k in doc["series"] if not k.endswith("_AMP") and k != "PLANT_RATE"]
        lo, hi = hourly_bands(pipe, doc, targets)
        first_off = next((i for i in range(168, len(doc["run"])) if doc["run"][i] != "ON"), None)
        ev = exceed_events({k: doc["series"][k] for k in targets}, lo, hi, doc["run"], doc["t"], first_off)
        hourly[doc["tag_prefix"]] = {"events": ev, "first_off_at": doc["t"][first_off] if first_off is not None else None}
    # Energy: motor current proxy, HE-3301 excluded (asset mapping unexplained, design rule).
    energy = {doc["tag_prefix"]: {**energy_forecast(pipe, doc), "naive_wape_pct": doc["forecast"]["wape_pct"]}
              for doc in snap["hourly"] if doc["tag_prefix"] != "HE3301"}
    out = {"model": "amazon/chronos-2", "mode": "zero-shot, CPU", "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "weekly": display, "backtest": backtest, "hourly": hourly, "energy": energy}
    (ROOT / "prototype/src/data/condition_forecast.json").write_text(json.dumps(out, indent=1), encoding="utf8")
    run = ROOT / "evaluation/runs" / f"{date.today().isoformat()}_condition_forecast"
    run.mkdir(parents=True, exist_ok=True)
    (run / "result.json").write_text(json.dumps({"backtest": backtest, "cases": cases, "hourly": hourly,
                                                 "energy": {k: {"chronos_wape": v["wape_pct"], "naive_wape": v["naive_wape_pct"]} for k, v in energy.items()}}, indent=1), encoding="utf8")
    print(json.dumps({"backtest": backtest, "energy": {k: (v["wape_pct"], v["naive_wape_pct"]) for k, v in energy.items()},
                      "hourly_first_lead": {k: (v["events"][0]["lead_hours"] if v["events"] else None) for k, v in hourly.items()}}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
