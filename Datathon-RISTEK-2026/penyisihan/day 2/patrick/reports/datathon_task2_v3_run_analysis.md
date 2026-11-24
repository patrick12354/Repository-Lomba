# Datathon Task 2 V3 - OCR Recovery and Route Reverse Engineering

Status: full local run selesai; belum ada leaderboard score.

## V2 error taxonomy

V2 grouped OOF menghasilkan 6.834 benar dan 2.166 salah:

| Outcome | States | Rate |
|---|---:|---:|
| Correct | 6.834 | 75,93% |
| Shortest-path tie-break error | 1.723 | 19,14% |
| Truth tidak shortest pada OCR graph | 295 | 3,28% |
| Candidate missing | 148 | 1,64% |

Fold-safe graph augmentation memakai train transitions hanya mengubah accuracy sekitar +0,01 pp. Link reading order, candidate ID order, dan shortest-path branching juga tidak memberikan peningkatan stabil. Karena itu V3 beralih ke raw OCR recovery.

## OCR recovery

- Suspicious/merged raw regions: 1.690.
- New recovered directed edges: 2.162.
- Exact multi-title segmentation: 1.482 edges.
- Conservative fuzzy recovery: 680 edges.
- Train labels tidak dipakai untuk membentuk recovered edge.

Contoh merged region yang berhasil dipecah:

- `Scotland Philosophy`;
- `Hurricane Katrina 2005 Atlantic hurricane season`;
- `Lilongwe Mauritius`;
- `Port Louis Mayotte`;
- `lron` dipulihkan menuju `Iron` melalui OCR-confusion rule.

## Grouped OOF comparison

| Version | Accuracy | Top-3 | Top-5 | Candidate recall |
|---|---:|---:|---:|---:|
| V2 hard-min | 75,93% | 92,33% | 95,58% | 98,36% |
| V3 recovered hard-min | **76,90%** | **93,92%** | **97,17%** | **99,39%** |

V3 fold accuracy: 78,63%, 75,50%, dan 76,57%. Nested hard-min selection juga 76,90% dan tetap memilih configuration ID 269.

## V3 error taxonomy

| Outcome | States | Rate |
|---|---:|---:|
| Correct | 6.921 | 76,90% |
| Shortest-path tie-break error | 1.803 | 20,03% |
| Truth tidak shortest pada recovered graph | 221 | 2,46% |
| Candidate missing | 55 | 0,61% |

V3 mengubah 359 OOF predictions: 194 error V2 diperbaiki, 107 prediction benar V2 menjadi salah, dan 58 tetap salah. Net gain adalah 87 correct states atau +0,97 percentage points.

## Decision

- Primary V3 menggunakan recovered graph dan hard-min tie-break config 269.
- Regime-specific config selection menghasilkan nested 76,69%, lebih rendah dari single stable config 76,90%; regime gate tidak dipakai.
- Specialized LambdaRank tetap lebih rendah dan tidak dipilih.
- Remaining bottleneck adalah multi-shortest-path tie-breaking, bukan candidate extraction.

## Artifacts

- Source: `notebooks/source/datathon_task2_v3_ocr_recovery_reverse_engineering_source.ipynb`.
- Executed output notebook: `notebooks/runs/V3 Final Local Notebook.ipynb`.
- Primary submission: `submissions/datathon_task2_v3_ocr_recovered_hardmin.csv`.
- Full output: `output/v3/`.
- Artifact ZIP: `output/datathon_task2_v3_artifacts.zip`.
