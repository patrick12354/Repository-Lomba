"""Dekomposisi penggelembungan AUC pada protokol evaluasi A sampai D.

Dijalankan terpisah dari recompute_metrics.py karena augmentasi mahal.
Hasil digabungkan ke poc_hasil.json.
"""

from __future__ import annotations

import json
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import GroupKFold, StratifiedKFold, cross_val_predict
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from recompute_metrics import (
    RANDOM_STATE,
    augment_variants,
    extract_features,
    features_from_rgb,
    load_metadata,
)

ROOT = Path(__file__).resolve().parent
CACHE = ROOT / ".cache_augmented.npz"


def rows_for_image(args: tuple[int, str, int, str]) -> tuple[list[dict], list[int], list[str], list[int]]:
    index, path, label, participant = args
    path = Path(path)
    rows = [extract_features(path)]
    for variant in augment_variants(path, n=5, seed=index):
        rows.append(features_from_rgb(variant))
    return rows, [label] * 6, [participant] * 6, [index] * 6


def build_augmented(meta: pd.DataFrame, features: list[str]):
    if CACHE.exists():
        data = np.load(CACHE, allow_pickle=True)
        print("Memakai cache augmentasi.")
        return data["X"], data["y"], data["g"], data["src"]

    tasks = [
        (i, str(p), int(lab), str(g))
        for i, (p, lab, g) in enumerate(
            zip(meta.path, meta.label, meta.participant)
        )
    ]
    all_rows, all_y, all_g, all_src = [], [], [], []
    with ProcessPoolExecutor() as pool:
        for rows, ys, gs, srcs in pool.map(rows_for_image, tasks, chunksize=8):
            all_rows.extend(rows)
            all_y.extend(ys)
            all_g.extend(gs)
            all_src.extend(srcs)

    X = pd.DataFrame(all_rows)[features].values
    y = np.array(all_y)
    g = np.array(all_g)
    src = np.array(all_src)
    np.savez_compressed(CACHE, X=X, y=y, g=g, src=src)
    print(f"Augmentasi selesai: {X.shape[0]} sampel.")
    return X, y, g, src


def main() -> None:
    meta = load_metadata()
    X_df = pd.DataFrame([extract_features(p) for p in meta.path])
    features = list(X_df.columns)
    X_plain = X_df.values
    y_plain = meta.label.values
    groups = meta.participant.values

    X_aug, y_aug, g_aug, src_aug = build_augmented(meta, features)

    model = make_pipeline(
        StandardScaler(), LogisticRegression(max_iter=5000, random_state=RANDOM_STATE)
    )

    def auc_with(cv, groups_arg=None, X=X_aug, y=y_aug) -> float:
        pred = cross_val_predict(
            model, X, y, cv=cv, groups=groups_arg, method="predict_proba"
        )[:, 1]
        return float(roc_auc_score(y, pred))

    auc_a = auc_with(StratifiedKFold(5, shuffle=True, random_state=RANDOM_STATE))
    auc_b = auc_with(GroupKFold(n_splits=5), src_aug)
    auc_c = auc_with(GroupKFold(n_splits=5), g_aug)
    auc_d = auc_with(GroupKFold(n_splits=5), groups, X_plain, y_plain)

    print(f"A augmentasi + split acak per citra   {auc_a:.4f}")
    print(f"B augmentasi + group per citra sumber {auc_b:.4f}")
    print(f"C augmentasi + group per partisipan   {auc_c:.4f}")
    print(f"D tanpa augmentasi + group partisipan {auc_d:.4f}")
    print(f"  kebocoran salinan augmentasi A-B = {auc_a - auc_b:+.4f}")
    print(f"  tanpa grouping partisipan    B-C = {auc_b - auc_c:+.4f}")
    print(f"  augmentasi saat split benar  C-D = {auc_c - auc_d:+.4f}")
    print(f"  total                        A-D = {auc_a - auc_d:+.4f}")

    path = ROOT / "poc_hasil.json"
    payload = json.loads(path.read_text())
    payload["protokol"] = {
        "A_augmentasi_split_acak": round(auc_a, 4),
        "B_augmentasi_group_citra_sumber": round(auc_b, 4),
        "C_augmentasi_group_partisipan": round(auc_c, 4),
        "D_tanpa_augmentasi_group_partisipan": round(auc_d, 4),
    }
    payload["dekomposisi"] = {
        "kebocoran_salinan_augmentasi_A_B": round(auc_a - auc_b, 4),
        "tanpa_grouping_partisipan_B_C": round(auc_b - auc_c, 4),
        "efek_augmentasi_split_benar_C_D": round(auc_c - auc_d, 4),
        "total_A_D": round(auc_a - auc_d, 4),
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    print(f"Diperbarui: {path}")


if __name__ == "__main__":
    main()
