"""Extract the CALIBER Case 2 files into one provenance-carrying JSON snapshot.

Reads the organiser files without modifying them. Every record keeps the file,
sheet/slide and row it came from, and every file is fingerprinted with SHA-256.
Usage:  python pipeline/extract_case2.py
Writes: data/generated/case2.json  (and a copy for the prototype build)
"""
from __future__ import annotations

import json
import re
import shutil
from collections import Counter
from datetime import date, datetime
from decimal import Decimal
from hashlib import sha256
from pathlib import Path

import numpy as np
from openpyxl import load_workbook
from pptx import Presentation

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "Supporting Data" / "Case 2_ Intelligence Manufacturing"
OUT = ROOT / "data" / "generated" / "case2.json"
PROTO_COPY = ROOT / "prototype" / "src" / "data" / "case2.json"
REVIEW_DATE = "2026-10-02"
OPEN_STATUSES = ["NEW REGISTERED", "RCA PROCESS", "CA/PA EXECUTION", "MONITORING RESULT"]
# Forecast split used in the design audit (§8.3): 552 h reference, 168 h test.
TRAIN_HOURS = 552

sources: dict[str, dict] = {}


def register(path: Path, sid: str, kind: str) -> str:
    sources[sid] = {
        "id": sid,
        "kind": kind,
        "relative_path": str(path.relative_to(ROOT)).replace("\\", "/"),
        "file_name": path.name,
        "sha256": sha256(path.read_bytes()).hexdigest(),
        # The organiser files carry no publication time; never substitute ingestion time.
        "source_updated_at": None,
        "ingested_at": REVIEW_DATE,
    }
    return sid


def k_to_usd(v) -> int | None:
    if v is None:
        return None
    return int((Decimal(str(v)) * 1000).to_integral_value())


def iso(v) -> str | None:
    if v is None:
        return None
    if isinstance(v, (datetime, date)):
        return v.strftime("%Y-%m-%d")
    s = str(v).strip()
    for fmt in ("%Y-%m-%d", "%d-%b-%Y", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(s, fmt).strftime("%Y-%m-%d")
        except ValueError:
            pass
    return s


def clean(s):
    return s.replace("—", "—") if isinstance(s, str) else s


# ---------------------------------------------------------------- incidents
def extract_incidents():
    path = BASE / "Incident Database" / "Incident Database.xlsx"
    sid = register(path, "L3", "incident_register")
    ws = load_workbook(path, data_only=True)["Incident Database"]
    rows = list(ws.values)
    header = rows[2]
    out = []
    for excel_row, r in enumerate(rows[3:], start=4):
        if r[0] is None:
            continue
        d = dict(zip(header, r))
        ar = d["AR No."]
        out.append({
            # Snapshot identity = source id + serial. AR is an attribute, never a key.
            "id": f"L3-{d['Serial No']}",
            "serial": d["Serial No"],
            "mto": d["MTO No."],
            "ar_raw": ar,
            "ar": None if (ar is None or str(ar).strip().lower() == "n/a") else ar,
            "plant": d["Plant"],
            "tag": d["Tag Number"],
            "eq_class": d["Eq. Class"],
            "occurred": iso(d["Date of Occur."]),
            "title": clean(d["Risk Case Title"]),
            "impact": d["Highest Impact"],
            "pre_risk": d["Pre-Risk"],
            "risk_score": d["Risk Score"],
            "pic_rca": d["PIC (RCA)"],
            "status": d["Overall Status"],
            "discipline": d["Discipline"],
            "eq_type": d["Eq. Type"],
            "component": d["Component"],
            "mechanism": d["F Mechanism"],
            "downtime_h": d["Downtime (hrs)"],
            "actual_usd": k_to_usd(d["Act. Loss (k US$)"]),
            "potential_usd": k_to_usd(d["Pot. Loss (k US$)"]),
            "total_usd": k_to_usd(d["Total Loss (k US$)"]),
            "rca_due": iso(d["RCA Due Date"]),
            "src": {"source": sid, "sheet": "Incident Database", "row": excel_row},
        })
    return out


# ---------------------------------------------------------------- equipment
PARAM_RE = re.compile(r"^(.*?)\s*\(([^)]*)\)\s*$")


def parse_param(label: str, limits: str):
    name, unit = PARAM_RE.match(label.replace("\n", " ")).groups()
    alarm, trip = (float(x) for x in limits.split("/"))
    return {
        "name": name.strip(),
        "unit": unit.strip(),
        "alarm": alarm,
        "trip": trip,
        # Rising parameter if trip > alarm, falling (e.g. pressure, flow, duty) otherwise.
        "direction": "high" if trip > alarm else "low",
    }


def linear_flags(rows, params):
    """Re-run of the §2.5 diagnostic: 6-point linear fit, flag when the
    projected crossing of a trip limit is ≤ 8 weeks away. Uses only rows up to
    the evaluated week."""
    trip_idx = next(i for i, r in enumerate(rows) if r["status"] == "TRIP")
    for i in range(5, trip_idx):
        horizons = []
        for j, p in enumerate(params):
            y = np.array([rows[k]["values"][j] for k in range(i - 5, i + 1)], float)
            slope, intercept = np.polyfit(np.arange(6), y, 1)
            if slope == 0 or (p["trip"] - y[-1]) * slope <= 0:
                continue
            d = (p["trip"] - (slope * 5 + intercept)) / slope
            if d > 0:
                horizons.append((float(d), p["name"]))
        if horizons and min(horizons)[0] <= 8:
            h, name = min(horizons)
            return {"date": rows[i]["date"], "week": rows[i]["week"], "horizon_weeks": round(h, 2), "parameter": name}
    return None


def extract_equipment(incidents):
    out = []
    for n, path in enumerate(sorted((BASE / "Equipment Performance").glob("*.xlsx")), start=1):
        sid = register(path, f"E{n}", "equipment_performance")
        wb = load_workbook(path, data_only=True)
        info = list(wb["Equipment Info"].values)
        meta = {r[0]: r[1] for r in info[3:] if r[0]}
        params = [parse_param(info[j][2], info[j][3]) for j in range(4, 8)]
        hist_rows = list(wb["Condition History"].values)
        history = [{
            "week": r[0], "date": iso(r[1]), "values": [r[2], r[3], r[4], r[5]],
            "status": r[6], "remark": clean(r[7]), "row": k,
        } for k, r in enumerate(hist_rows[1:], start=2)]
        summary = [{"kpi": r[0], "value": r[1], "basis": r[2], "row": k}
                   for k, r in enumerate(list(wb["Performance Summary"].values)[3:], start=4) if r[0]]
        tag = meta["Equipment Tag"]
        linked = [i for i in incidents if i["ar"] == meta["Linked RCA / AR No."] and i["tag"] == tag]
        first_alarm = next(h for h in history if h["status"] == "ALARM")
        trip = next(h for h in history if h["status"] == "TRIP")
        out.append({
            "tag": tag,
            "source": sid,
            "name": meta["Equipment Name"],
            "type": meta["Equipment Type"],
            "eq_class": meta["Equipment Class"],
            "plant_unit": meta["Plant / Unit"],
            "discipline": meta["Discipline"],
            "criticality": meta["Criticality"],
            "design_life": meta["Design Life"],
            "monitoring": meta["Monitoring Method"],
            "linked_ar": meta["Linked RCA / AR No."],
            # Answer-revealing fields kept apart so masked modes can drop them.
            "target_fields": {"failure_date": iso(meta["Failure Date"]), "dominant_failure_mode": clean(meta["Dominant Failure Mode"])},
            "params": params,
            "history": history,
            "summary": summary,
            "linked_incident": linked[0]["id"] if len(linked) == 1 else None,
            "join_count": len(linked),
            "first_alarm": first_alarm["date"],
            "trip_date": trip["date"],
            "linear_flag": linear_flags(history, params),
        })
    return out


# ---------------------------------------------------------------- production (hourly)
def wape(actual, pred):
    return float(100 * np.sum(np.abs(actual - pred)) / np.sum(np.abs(actual)))


def extract_hourly():
    out = []
    for n, path in enumerate(sorted((BASE / "Production Data").glob("*.xlsx")), start=1):
        sid = register(path, f"P{n}", "production_hourly")
        wb = load_workbook(path, data_only=True)
        tags = [dict(zip(list(wb["PI Tag"].values)[0], r)) for r in list(wb["PI Tag"].values)[1:] if r[0]]
        rows = list(wb["Sheet2"].values)
        cols = list(rows[0])
        data = [r for r in rows[1:] if r[0] is not None]
        amp_col = next(c for c in cols if str(c).endswith("_AMP"))
        ai = cols.index(amp_col)
        x = np.array([r[ai] for r in data], float)
        on = np.array([r[cols.index("RUN_STATUS")] == "ON" for r in data])
        train, actual = x[:TRAIN_HOURS], x[TRAIN_HOURS:]
        preds = {
            "last_value": np.repeat(train[-1], len(actual)),
            "repeat_24h": np.resize(train[-24:], len(actual)),
            "repeat_168h": np.resize(train[-168:], len(actual)),
        }
        tag_prefix = amp_col.split("_")[0]
        out.append({
            "source": sid,
            "tag_prefix": tag_prefix,
            "pi_tags": [{"name": t["Name"], "description": t["Description"], "unit": t["engunits"], "instrument": t["instrumenttag"]} for t in tags],
            "columns": cols,
            # Compact series: timestamp strings + numeric columns + run status.
            "t": [str(r[0]) for r in data],
            "series": {c: [r[k] for r in data] for k, c in enumerate(cols) if c not in ("Timestamp", "RUN_STATUS")},
            "run": [r[cols.index("RUN_STATUS")] for r in data],
            "off_rows": int((~on).sum()),
            "off_with_nonzero_amp": int(((~on) & (x != 0)).sum()),
            "forecast": {
                "target": amp_col,
                "train_hours": TRAIN_HOURS,
                "test_hours": len(actual),
                "cutoff": str(data[TRAIN_HOURS - 1][0]),
                "test_start": str(data[TRAIN_HOURS][0]),
                "test_off_hours": int((~on[TRAIN_HOURS:]).sum()),
                "train_median_A": float(np.median(train)),
                "predictions": {k: [round(float(v), 3) for v in p] for k, p in preds.items()},
                "wape_pct": {k: round(wape(actual, p), 2) for k, p in preds.items()},
                "mae_A": {k: round(float(np.mean(np.abs(actual - p))), 3) for k, p in preds.items()},
            },
        })
    return out


# ---------------------------------------------------------------- RCA decks
def slide_texts(slide):
    texts = []
    for sh in slide.shapes:
        if sh.has_text_frame and sh.text_frame.text.strip():
            texts.append(clean(sh.text_frame.text.strip()))
    return texts


def parse_action_slide(texts):
    """Slide 9: corrective block then pro-active block, each row = RC, text, plan, PIC, status."""
    actions = []
    kind = None
    i = 0
    while i < len(texts):
        t = texts[i]
        if t == "Corrective Action":
            kind = "corrective"; i += 4; continue  # skip header row Plan Date, PIC, Status
        if t == "Pro-Active Action":
            kind = "proactive"; i += 4; continue
        if kind and re.fullmatch(r"[PX]\d", t) and i + 4 < len(texts):
            rc, text, plan, pic, status = texts[i:i + 5]
            actions.append({"kind": kind, "rc": rc, "text": text, "plan_date": iso(plan), "pic": pic, "status": status})
            i += 5; continue
        i += 1
    return actions


def parse_preventive(texts):
    """Slide 10 preventive rows: item, possible root cause, action, plan, PIC. The source records no status."""
    rows = []
    if "Preventive Action" not in texts:
        return rows
    i = texts.index("Preventive Action") + 3
    while i + 4 < len(texts) and re.fullmatch(r"[PX]\d", texts[i]):
        item, cause, action, plan, pic = texts[i:i + 5]
        rows.append({"kind": "preventive", "rc": item, "cause": cause, "text": action, "plan_date": iso(plan), "pic": pic, "status": None})
        i += 5
    return rows


def parse_table(texts, start_marker):
    rows = []
    i = texts.index("Evidence / Finding") + 1 if "Evidence / Finding" in texts else 0
    while i + 3 < len(texts):
        if re.fullmatch(r"[PX]\d", texts[i]):
            rows.append({"id": texts[i], "item": texts[i + 1], "result": texts[i + 2], "finding": texts[i + 3]})
            i += 4
        else:
            i += 1
    return rows


def extract_rca(equipment):
    out = []
    for n, path in enumerate(sorted((BASE / "RCA - Downtime Data").glob("*.pptx")), start=1):
        sid = register(path, f"R{n}", "rca_deck")
        prs = Presentation(path)
        slides = [slide_texts(s) for s in prs.slides]
        tag = slides[0][4].split("|")[0].strip() if len(slides[0]) > 4 else None
        tag = next((e["tag"] for e in equipment if e["tag"] in path.name), tag)
        s3 = slides[2]
        chron = []
        for k, t in enumerate(s3):
            if re.match(r"\d{2}-[A-Za-z]{3}-\d{4}", t) and k + 1 < len(s3):
                chron.append({"when": t, "event": s3[k + 1]})
        root = next((t.split(":", 1)[1].strip() for t in slides[6] if t.startswith("ROOT CAUSE:")), None)
        statement = slides[1][slides[1].index("PROBLEM STATEMENT") + 1] if "PROBLEM STATEMENT" in slides[1] else None
        out.append({
            "source": sid,
            "tag": tag,
            "title": slides[0][3] if len(slides[0]) > 3 else path.stem,
            "ar": next((t for t in slides[0] if t.startswith("AR-")), None),
            "problem_statement": statement,
            "chronology": chron,
            "past_performance": slides[3],
            "four_p": parse_table(slides[5], "P"),
            "four_m": parse_table(slides[6], "X"),
            "root_cause": root,
            "actions": parse_action_slide(slides[8]),
            "preventive": parse_preventive(slides[9]),
            "slides": slides,
        })
    return out


def main():
    register(ROOT / "Booklet CALIBER 2026 - Registration Extended.pdf", "L0", "booklet")
    register(ROOT / "The Case - CALIBER 2026.pdf", "L1", "casebook")
    register(BASE / "Data Set Explanation for Case 2 Intelligence Manufacturing.pptx", "L2", "dataset_explanation")
    incidents = extract_incidents()
    equipment = extract_equipment(incidents)
    hourly = extract_hourly()
    rca = extract_rca(equipment)
    ar_counts = Counter(i["ar_raw"] for i in incidents)
    snapshot = {
        "meta": {
            "snapshot": "CALIBER 2026 Case 2 dataset snapshot",
            "review_date": REVIEW_DATE,
            "open_statuses": OPEN_STATUSES,
            "currency": "USD (converted once from k US$ × 1,000)",
            "generator": "pipeline/extract_case2.py",
            "ar_placeholder_count": ar_counts.get("n/a", 0),
            "duplicate_ar": {k: v for k, v in ar_counts.items() if k != "n/a" and v > 1},
        },
        "sources": sources,
        "incidents": incidents,
        "equipment": equipment,
        "hourly": hourly,
        "rca": rca,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(snapshot, ensure_ascii=False, separators=(",", ":"), default=str), encoding="utf-8")
    PROTO_COPY.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(OUT, PROTO_COPY)
    print(f"wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size/1024:.0f} KB): "
          f"{len(incidents)} incidents, {len(equipment)} equipment, {len(hourly)} hourly series, {len(rca)} RCA decks")


if __name__ == "__main__":
    main()
