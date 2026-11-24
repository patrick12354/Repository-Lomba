# Datathon Task 2 V2 - Shortest-Path Tie-Break Analysis

Status: local full-data validation selesai; source notebook siap dijalankan di Kaggle. Angka pada dokumen ini bukan leaderboard score.

## Evidence from V1

- Full V1 grouped OOF accuracy: 65,09%.
- Raw OCR candidate recall: 97,83%.
- V1 top-3/top-5: 89,91% / 94,80%.
- OCR menghabiskan sekitar 46,55 dari total 47,57 menit, sehingga V2 wajib memakai reusable graph dan tidak mengulang OCR.

## New route insight

Feature generation V2 memakai 3-fold `GroupKFold(target_article_id)` dan fold-safe candidate augmentation.

- Candidate recall dengan cap 100: 98,36%.
- Truth berada pada minimum graph distance: 95,08% states.
- Truth adalah satu-satunya minimum-distance candidate: 26,19% states.
- State yang hanya memiliki satu minimum-distance candidate: 28,32%.

Artinya extraction bukan bottleneck utama. Sebagian besar state memiliki beberapa kandidat shortest-path dan kompetisi terutama menjadi masalah tie-breaking.

## Preliminary local grouped OOF

| Method | Accuracy | Top-3 | Top-5 |
|---|---:|---:|---:|
| V1 heuristic rebuilt | 64,60% | 89,46% | 94,59% |
| V2 soft tuned graph-semantic | 74,06% | 92,10% | 95,56% |
| V2 hard shortest-path tie-break | **75,93%** | **92,33%** | **95,58%** |
| Specialized tie LambdaRank | 62,39% | diagnostic | diagnostic |

Hard-min per-fold accuracy: 77,90%, 74,63%, dan 75,27%. Dalam leave-one-fold-out configuration selection, konfigurasi hard-min yang sama terpilih pada ketiga held folds dan mean held accuracy tetap 75,93%.

## Modeling decisions

- Primary submission memakai hard constraint minimum graph distance.
- Tie-break memakai exact category overlap, category hierarchy, global click popularity, candidate in-degree, shared incoming/outgoing neighbours, title TF-IDF, dan posisi link.
- Click prior pada training feature menggunakan leave-one-row-out count untuk menghapus self-label leakage yang ada pada training design V1.
- LambdaRank tetap diuji sebagai learned comparator tetapi tidak dipilih karena grouped OOF lebih rendah.
- Notebook mengekspor soft-tuned alternative untuk controlled leaderboard comparison.

## Kaggle contract

Competition input:

`/kaggle/input/competitions/datathon-task-2/dataset-task2`

Reusable V1 input utama:

`/kaggle/input/datasets/timotiuspatrick/datatonday2output/datathon_task2_v1_reusable`

Notebook juga mendukung `/kaggle/input/datatonday2output/datathon_task2_v1_reusable` dan auto-discovery `manifest.json` jika mount path Kaggle berbeda.

Source notebook:

`patrick/notebooks/source/datathon_task2_v2_shortest_path_tiebreak_ranker_source.ipynb`

Expected primary output:

`/kaggle/working/datathon_task2_v2/datathon_task2_v2_hardmin_tiebreak.csv`

Local top-to-bottom verification selesai dalam 2,06 menit tanpa notebook error. Runtime Kaggle diperkirakan beberapa menit karena tidak ada OCR.
