"""Hitung ulang metrik POC TATAP dengan empat koreksi metodologis.

1. Metrik agregat level anak (unit keputusan produk), bukan hanya level rekaman.
2. Regresi logistik ditetapkan sebagai model pra-tetap; titik kerja dihitung
   pada unit anak dari probabilitas model itu, bukan dari model dengan AUC
   rekaman tertinggi.
3. Dekomposisi penggelembungan AUC yang benar: A-B, B-C, C-D.
4. Nested GroupKFold agar estimasi tidak memuat bias pemilihan model.

Menulis hasil ke poc_hasil.json. Kunci `protokol` dan `dekomposisi` yang
ditulis recompute_protokol.py dipertahankan bila sudah ada.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, roc_curve
from sklearn.model_selection import GroupKFold, StratifiedKFold, cross_val_predict
from sklearn.naive_bayes import GaussianNB
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

RANDOM_STATE = 42
GRID = 8
INK_THRESHOLD = 0.02
# Model pra-tetap: ditetapkan sebelum melihat hasil, dievaluasi pada unit anak.
PRIMARY_MODEL = "Logistic Regression"
np.random.seed(RANDOM_STATE)

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT.parent / "data" / "autism eye tracking dataset"

ZERO_KEYS = [
    "centroid_x", "centroid_y", "std_x", "std_y", "span_x", "span_y",
    "radial_mean", "radial_std", "vel_mean", "vel_std", "acc_mean", "jerk_mean",
    "fixation_ratio", "saccade_ratio", "grid_entropy", "n_active_cells",
    "bbox_fill", "aspect_ratio",
]


def features_from_rgb(a: np.ndarray) -> dict[str, float]:
    H, W = a.shape[:2]
    R, G, B = a[:, :, 0], a[:, :, 1], a[:, :, 2]
    ink = a.sum(axis=2) > INK_THRESHOLD

    f: dict[str, float] = {}
    n_ink = int(ink.sum())
    f["ink_frac"] = n_ink / (H * W)
    if n_ink < 5:
        for k in ZERO_KEYS:
            f[k] = 0.0
        return f

    ys, xs = np.nonzero(ink)
    xn, yn = xs / W, ys / H
    f["centroid_x"], f["centroid_y"] = xn.mean(), yn.mean()
    f["std_x"], f["std_y"] = xn.std(), yn.std()
    f["span_x"] = xn.max() - xn.min()
    f["span_y"] = yn.max() - yn.min()
    rad = np.hypot(xn - xn.mean(), yn - yn.mean())
    f["radial_mean"], f["radial_std"] = rad.mean(), rad.std()

    r_i, g_i, b_i = R[ink], G[ink], B[ink]
    f["vel_mean"], f["vel_std"] = r_i.mean(), r_i.std()
    f["acc_mean"], f["jerk_mean"] = g_i.mean(), b_i.mean()

    denom = max(n_ink, 1)
    f["fixation_ratio"] = ((r_i < g_i * 0.6) & (r_i < b_i * 0.6)).sum() / denom
    f["saccade_ratio"] = ((r_i > g_i * 0.9) & (r_i > 0.05)).sum() / denom

    cell = np.zeros((GRID, GRID))
    gi = np.clip((yn * GRID).astype(int), 0, GRID - 1)
    gj = np.clip((xn * GRID).astype(int), 0, GRID - 1)
    np.add.at(cell, (gi, gj), 1)
    p = cell.ravel() / cell.sum()
    p = p[p > 0]
    f["grid_entropy"] = float(-(p * np.log(p)).sum() / np.log(GRID * GRID))
    f["n_active_cells"] = float((cell > 0).sum() / (GRID * GRID))
    f["bbox_fill"] = f["ink_frac"] / max(f["span_x"] * f["span_y"], 1e-9)
    f["aspect_ratio"] = f["span_x"] / max(f["span_y"], 1e-9)
    return f


def extract_features(path: Path) -> dict[str, float]:
    arr = np.asarray(Image.open(path).convert("RGB")).astype(np.float64) / 255.0
    return features_from_rgb(arr)


def augment_variants(path: Path, n: int = 5, seed: int = 0) -> list[np.ndarray]:
    rng = np.random.default_rng(seed)
    im = Image.open(path).convert("RGB")
    W, H = im.size
    out = []
    for _ in range(n):
        ang = float(rng.uniform(-15, 15))
        tx = float(rng.uniform(-0.08, 0.08) * W)
        ty = float(rng.uniform(-0.08, 0.08) * H)
        zoom = float(rng.uniform(0.9, 1.1))
        im2 = im.rotate(ang, resample=Image.BILINEAR, translate=(tx, ty))
        nw, nh = max(int(W * zoom), 8), max(int(H * zoom), 8)
        im2 = im2.resize((nw, nh), Image.BILINEAR)
        canvas = Image.new("RGB", (W, H), (0, 0, 0))
        canvas.paste(im2, ((W - nw) // 2, (H - nh) // 2))
        out.append(np.asarray(canvas).astype(np.float64) / 255.0)
    return out


def build_models() -> dict:
    return {
        "Logistic Regression": make_pipeline(
            StandardScaler(),
            LogisticRegression(max_iter=5000, random_state=RANDOM_STATE),
        ),
        "SVM (RBF)": make_pipeline(
            StandardScaler(), SVC(probability=True, random_state=RANDOM_STATE)
        ),
        "Naive Bayes": make_pipeline(StandardScaler(), GaussianNB()),
        "Random Forest": RandomForestClassifier(
            n_estimators=400, min_samples_leaf=2,
            random_state=RANDOM_STATE, n_jobs=-1,
        ),
        "Gradient Boosting": GradientBoostingClassifier(random_state=RANDOM_STATE),
    }


def load_metadata() -> pd.DataFrame:
    records = []
    for label, sub, prefix in [(0, "TCImages", "TC"), (1, "TSImages", "TS")]:
        for f in sorted((DATA_DIR / sub).glob("*.png")):
            pid = f.stem.split("_")[1]
            records.append(
                {
                    "path": f,
                    "file": f.name,
                    "label": label,
                    "group": "TD" if label == 0 else "ASD",
                    "participant": f"{prefix}{pid}",
                }
            )
    return pd.DataFrame(records)


def aggregate_to_participants(
    probabilities: np.ndarray, labels: np.ndarray, groups: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    frame = pd.DataFrame({"p": probabilities, "y": labels, "g": groups})
    agg = frame.groupby("g").agg(p=("p", "mean"), y=("y", "max"), n=("p", "size"))
    return agg.p.values, agg.y.values.astype(int), agg.index.values


def bootstrap_auc(
    probabilities: np.ndarray, labels: np.ndarray, n_boot: int = 2000
) -> tuple[float, float]:
    rng = np.random.default_rng(RANDOM_STATE)
    n = len(labels)
    scores = []
    for _ in range(n_boot):
        idx = rng.integers(0, n, n)
        if len(np.unique(labels[idx])) < 2:
            continue
        scores.append(roc_auc_score(labels[idx], probabilities[idx]))
    return float(np.percentile(scores, 2.5)), float(np.percentile(scores, 97.5))


def operating_point(
    probabilities: np.ndarray, labels: np.ndarray, target_sensitivity: float = 0.90
) -> dict[str, float]:
    fpr, tpr, thresholds = roc_curve(labels, probabilities)
    feasible = np.flatnonzero(tpr >= target_sensitivity)
    i = feasible[np.argmin(fpr[feasible])]
    sensitivity, specificity = float(tpr[i]), float(1 - fpr[i])
    positives = labels.sum()
    negatives = len(labels) - positives
    tp = sensitivity * positives
    fp = (1 - specificity) * negatives
    ppv = float(tp / (tp + fp)) if (tp + fp) > 0 else float("nan")
    return {
        "threshold": float(thresholds[i]),
        "sensitivity": sensitivity,
        "specificity": specificity,
        "ppv": ppv,
    }


def ppv_at_prevalence(sensitivity: float, specificity: float, prevalence: float) -> float:
    tp = sensitivity * prevalence
    fp = (1 - specificity) * (1 - prevalence)
    return float(tp / (tp + fp))


def nested_group_cv(
    X: np.ndarray, y: np.ndarray, groups: np.ndarray
) -> tuple[np.ndarray, list[str]]:
    outer = GroupKFold(n_splits=5)
    predictions = np.zeros(len(y))
    chosen: list[str] = []
    for train_idx, test_idx in outer.split(X, y, groups):
        inner_groups = groups[train_idx]
        inner = GroupKFold(n_splits=4)
        best_name, best_auc = None, -np.inf
        for name, model in build_models().items():
            inner_pred = cross_val_predict(
                model, X[train_idx], y[train_idx], cv=inner,
                groups=inner_groups, method="predict_proba",
            )[:, 1]
            auc = roc_auc_score(y[train_idx], inner_pred)
            if auc > best_auc:
                best_name, best_auc = name, auc
        chosen.append(best_name)
        model = build_models()[best_name]
        model.fit(X[train_idx], y[train_idx])
        predictions[test_idx] = model.predict_proba(X[test_idx])[:, 1]
    return predictions, chosen


def main() -> None:
    meta = load_metadata()
    print(f"Citra {len(meta)}, partisipan {meta.participant.nunique()}")

    X_df = pd.DataFrame([extract_features(p) for p in meta.path])
    features = list(X_df.columns)
    X = X_df.values
    y = meta.label.values
    groups = meta.participant.values
    print(f"Matriks fitur: {X.shape}")

    # --- Perbandingan model, split participant-disjoint -----------------------
    record_level: dict[str, float] = {}
    child_level: dict[str, float] = {}
    oof: dict[str, np.ndarray] = {}
    for name, model in build_models().items():
        pred = cross_val_predict(
            model, X, y, cv=GroupKFold(n_splits=5), groups=groups,
            method="predict_proba",
        )[:, 1]
        oof[name] = pred
        record_level[name] = roc_auc_score(y, pred)
        p_prob, p_y, _ = aggregate_to_participants(pred, y, groups)
        child_level[name] = roc_auc_score(p_y, p_prob)

    best_record = max(record_level, key=record_level.get)
    best_child = max(child_level, key=child_level.get)
    print("\nAUC level rekaman vs level anak:")
    for name in record_level:
        print(f"  {name:22s} rekaman {record_level[name]:.4f}   anak {child_level[name]:.4f}")
    print(f"AUC rekaman tertinggi: {best_record}")
    print(f"AUC anak tertinggi   : {best_child}")
    print(f"Model pra-tetap POC  : {PRIMARY_MODEL}")

    # Endpoint utama: unit anak, model pra-tetap.
    prim_prob, p_y, p_ids = aggregate_to_participants(oof[PRIMARY_MODEL], y, groups)
    ci_primary = bootstrap_auc(prim_prob, p_y)
    op_primary = operating_point(prim_prob, p_y)

    # Pembanding: model dengan AUC rekaman tertinggi, dievaluasi pada unit anak.
    alt_prob, alt_y, _ = aggregate_to_participants(oof[best_record], y, groups)
    ci_best_record = bootstrap_auc(alt_prob, alt_y)
    op_best_record = operating_point(alt_prob, alt_y)

    print(f"\nLevel anak ({len(p_y)} anak, {int(p_y.sum())} ASD):")
    print(f"  {PRIMARY_MODEL} (pra-tetap): AUC {child_level[PRIMARY_MODEL]:.4f} CI {ci_primary}")
    print(f"    titik kerja sens>=90%: {op_primary}")
    print(f"  {best_record} (AUC rekaman tertinggi): AUC {child_level[best_record]:.4f} CI {ci_best_record}")
    print(f"    titik kerja sens>=90%: {op_best_record}")

    # --- Nested GroupKFold ---------------------------------------------------
    nested_pred, chosen = nested_group_cv(X, y, groups)
    nested_image = roc_auc_score(y, nested_pred)
    n_prob, n_y, _ = aggregate_to_participants(nested_pred, y, groups)
    nested_participant = roc_auc_score(n_y, n_prob)
    ci_nested = bootstrap_auc(n_prob, n_y)
    print(f"\nNested GroupKFold: citra {nested_image:.4f}, anak {nested_participant:.4f} CI {ci_nested}")
    print(f"  Model terpilih per fold: {chosen}")

    # --- Varians antarpartisipan --------------------------------------------
    def between_participant_share(values: np.ndarray, g: np.ndarray) -> float:
        frame = pd.DataFrame({"v": values, "g": g})
        means = frame.groupby("g").v.transform("mean")
        ss_total = ((frame.v - frame.v.mean()) ** 2).sum()
        ss_between = ((means - frame.v.mean()) ** 2).sum()
        return ss_between / ss_total if ss_total > 0 else 0.0

    shares = {f: between_participant_share(X_df[f].values, groups) for f in features}
    mean_share = float(np.mean(list(shares.values())))
    print(f"\nRata-rata varians antarpartisipan: {mean_share:.1%}")

    # --- Efek ukuran level partisipan ---------------------------------------
    pf = X_df.copy()
    pf["participant"] = groups
    pf["label"] = y
    p_level = pf.groupby("participant").mean(numeric_only=True)
    asd_p = p_level[p_level.label == 1]
    td_p = p_level[p_level.label == 0]

    def cohens_d(a: pd.Series, b: pd.Series) -> float:
        na, nb = len(a), len(b)
        sp = np.sqrt(
            ((na - 1) * a.var(ddof=1) + (nb - 1) * b.var(ddof=1)) / (na + nb - 2)
        )
        return float((a.mean() - b.mean()) / sp) if sp > 0 else 0.0

    effects = {f: cohens_d(asd_p[f], td_p[f]) for f in features}
    top_effects = dict(
        sorted(effects.items(), key=lambda kv: abs(kv[1]), reverse=True)[:5]
    )

    payload = {
        "evidence_scope": "gaze_only",
        "product_modalities": ["gaze", "head_face", "vocalization"],
        "fusion_method": "quality_aware_weighted_late_fusion",
        "fusion_status": "prospective_paired_validation_required",
        "decision_unit": "child",
        "n_citra": int(len(meta)),
        "n_partisipan": int(meta.participant.nunique()),
        "n_fitur": len(features),
        "n_anak_asd": int(p_y.sum()),
        "n_anak_td": int(len(p_y) - p_y.sum()),
        "model_pra_tetap": PRIMARY_MODEL,
        "model_auc_rekaman_tertinggi": best_record,
        "model_auc_anak_tertinggi": best_child,
        "auc_record_level": {k: round(v, 4) for k, v in record_level.items()},
        "auc_child_level": {k: round(v, 4) for k, v in child_level.items()},
        "auc_child_primary": round(child_level[PRIMARY_MODEL], 4),
        "ci95_child_primary": [round(ci_primary[0], 4), round(ci_primary[1], 4)],
        "auc_record_primary": round(record_level[PRIMARY_MODEL], 4),
        "auc_child_best_record_model": round(child_level[best_record], 4),
        "ci95_child_best_record_model": [
            round(ci_best_record[0], 4), round(ci_best_record[1], 4),
        ],
        "auc_record_best": round(record_level[best_record], 4),
        "nested_auc_record": round(nested_image, 4),
        "nested_auc_child": round(nested_participant, 4),
        "nested_ci95_child": [round(ci_nested[0], 4), round(ci_nested[1], 4)],
        "nested_model_per_fold": chosen,
        "titik_kerja_anak_primary": {k: round(v, 4) for k, v in op_primary.items()},
        "titik_kerja_anak_best_record_model": {
            k: round(v, 4) for k, v in op_best_record.items()
        },
        "ppv_prevalensi_1persen": round(
            ppv_at_prevalence(
                op_primary["sensitivity"], op_primary["specificity"], 0.01
            ),
            4,
        ),
        "ppv_prevalensi_2persen": round(
            ppv_at_prevalence(
                op_primary["sensitivity"], op_primary["specificity"], 0.02
            ),
            4,
        ),
        "rujukan_per_kasus_prevalensi_1persen": None,
        "rujukan_per_kasus_prevalensi_2persen": None,
        "varians_antarpartisipan": round(mean_share, 4),
        "cohens_d_teratas": {k: round(v, 3) for k, v in top_effects.items()},
    }
    for prevalence, key in [(0.01, "1persen"), (0.02, "2persen")]:
        ppv = payload[f"ppv_prevalensi_{key}"]
        payload[f"rujukan_per_kasus_prevalensi_{key}"] = round(1 / ppv, 1) if ppv else None

    out = ROOT / "poc_hasil.json"
    if out.exists():
        # Pertahankan kunci yang tidak dihitung skrip ini, misalnya protokol dan
        # dekomposisi dari recompute_protokol.py serta kurva belajar dari notebook.
        merged = json.loads(out.read_text())
        merged.update(payload)
        payload = merged
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    print(f"\nDitulis ke {out}")


if __name__ == "__main__":
    main()
