---
title: Datathon Task 1 - Project Knowledge and Experiment Log
date: 2026-07-18
tags:
  - datathon
  - traffic-forecasting
  - machine-learning
status: active
last_updated: 2026-07-18
update_policy: every-important-milestone
---

# Datathon Task 1 - Project Knowledge and Experiment Log

Dokumen ini adalah sumber ringkas untuk seluruh insight, keputusan, eksperimen, dan hasil yang sudah diperoleh. Problem statement lengkap berada di [[penjelasan_lomba]].

> [!important] Aturan wajib pembaruan
> **Setiap milestone penting harus langsung diikuti update `codex.md` sebelum handoff atau melanjutkan fase berikutnya.** Aturan ini berlaku untuk semua pekerjaan berikutnya di proyek ini.

## Milestone update protocol

Yang dianggap milestone penting:

- dataset/EDA baru selesai dianalisis;
- baseline atau model baru selesai dibuat;
- notebook berhasil atau gagal dijalankan;
- validation/leaderboard score baru tersedia;
- submission baru dibuat atau dikirim;
- bug penting ditemukan, didiagnosis, atau diperbaiki;
- keputusan approach, ensemble, preprocessing, atau validation berubah;
- file/artifact penting dibuat, dipindahkan, atau diganti versinya.

Setiap update milestone minimal mencatat:

1. **Tanggal dan status** - selesai, gagal, pending, atau superseded.
2. **Artifact** - path notebook, submission, report, atau model terkait.
3. **Konfigurasi** - split, features, model, seed, epoch, dan setting penting.
4. **Hasil terukur** - MSE per horizon, mean MSE, runtime, leaderboard, atau traceback.
5. **Insight** - apa yang terbukti, tidak terbukti, atau berubah dari asumsi sebelumnya.
6. **Keputusan** - model/artifact mana yang dipertahankan, ditolak, atau dijadikan fallback.
7. **Next action** - eksperimen atau tindakan konkret berikutnya.

Template update:

```markdown
### YYYY-MM-DD - Nama milestone

- Status:
- Artifact:
- Configuration:
- Result:
- Insight:
- Decision:
- Next action:
```

> [!important] Interpretasi score
> Semua MSE yang tercatat di sini adalah **local temporal-validation MSE**, bukan leaderboard score. V1 sudah menghasilkan submission valid, tetapi performa test sebenarnya hanya dapat diketahui setelah submission ke kompetisi.

## Struktur proyek

```text
Dataton/
├── codex.md
├── penjelasan_lomba.md
├── dataset-task1/
│   ├── train/
│   ├── test/
│   ├── static/
│   └── sample_submission.csv
├── notebooks/
│   ├── source/
│   │   ├── datathon_task1_v1_ar_graphsage_source.ipynb
│   │   ├── datathon_task1_v2_2_model_search_kaggle_runtime_safe.ipynb
│   │   ├── datathon_task1_v3_regime_global_context_source.ipynb
│   │   ├── datathon_task1_v4_purged_day_phase_clause_diffusion_source.ipynb
│   │   └── datathon_task1_v5_rapid_malfa_lowrank_hybrid_source.ipynb
│   └── runs/
│       ├── datathon_task1_v1_ar_graphsage_kaggle_run.ipynb
│       ├── datathon_task1_v2_failed_torch_utils_kaggle_run.ipynb
│       ├── datathon_task1_v2_2_t4_kaggle_run.ipynb
│       └── datathon_task1_v3_t4_kaggle_run.ipynb
├── submissions/
│   ├── datathon_task1_v1_ar_graphsage_blend.csv
│   ├── datathon_task1_v2_2_blend.csv
│   └── datathon_task1_v3_regime_global_blend.csv
└── reports/
    ├── datathon_task1_v1_run_analysis.md
    ├── datathon_task1_v2_2_experiment_results.csv
    ├── datathon_task1_v2_2_run_analysis.md
    ├── datathon_task1_v3_experiment_results.csv
    └── datathon_task1_v3_run_analysis.md
```

## Ringkasan masalah

- Prediksi speed untuk 1.260 road segment.
- Input setiap test sample: 15 timestep atau satu jam history, event text, dan road graph.
- Horizon: h5 (+20 menit), h10 (+40 menit), dan h15 (+60 menit).
- Metric: Mean Squared Error (MSE), dirata-ratakan atas sample, horizon, dan road.
- Test berisi 540 sample, sehingga submission memiliki 540 x 3 x 1.260 = 2.041.200 baris.

## Dataset audit

### Shapes dan distribution

| Split | Shape | Mean | Std | Zero rate | Min | Max |
|---|---:|---:|---:|---:|---:|---:|
| Train m1 | `(11160, 1260)` | 54.992 | 17.048 | 1.036% | 0 | 142 |
| Train m2 | `(5039, 1260)` | 49.184 | 26.218 | 16.672% | 0 | 151 |
| Test history | `(540, 15, 1260)` | 52.729 | 20.416 | 5.937% | 0 | 137 |

Insight utama:

- Ada distribution shift besar antara m1 dan m2, terutama pada zero rate.
- Test berada di antara keduanya, tetapi tidak identik dengan salah satu blok.
- Nilai nol tidak diimputasi secara agresif karena dapat berarti closure, berhenti total, atau missing regime yang juga mungkin muncul di target.
- Model neural memakai zero mask agar dapat membedakan nol dari speed rendah biasa.

### Struktur temporal

- 15 timestep = 60 menit, sehingga satu timestep = 4 menit.
- Satu hari = 24 x 60 / 4 = 360 timestep.
- Train m1 memiliki 11.160 timestep = 31 x 360, tepat 31 hari.
- Window train sangat overlap, sehingga random split akan menghasilkan leakage.
- Validation menggunakan dua hari terakhir dari masing-masing block; train hanya menggunakan masa lalu sebelum cut point.

### Road graph

- Adjacency shape: `(1260, 1260)`.
- Matrix directed dan tidak simetris.
- Terdapat 5.122 nilai satu jika diagonal/self-loop ikut dihitung.
- Setelah self-loop dibuang dan arah digabung pada V1, degree min/median/mean/p95/max adalah 0 / 3 / 3.09 / 6 / 10.
- Graph sangat sparse, sehingga sparse message passing jauh lebih efisien daripada dense matrix multiplication.

### Event text

Event text semi-terstruktur dan berisi template seperti:

```text
road closure on ...
construction on ...
a general traffic accident on ...
prohibit left turn on ...
```

| Split | Documents | Unique clauses | Median clauses/document |
|---|---:|---:|---:|
| Train m1 | 11.160 | 1.755 | 27 |
| Train m2 | 5.039 | 1.104 | 28 |
| Test | 540 | 948 | 29 |

- Sebanyak 182 dari 948 exact test clauses tidak muncul verbatim di train.
- Exact sentence lookup tidak cukup robust.
- Word n-gram TF-IDF dipilih karena dapat menggunakan kata penyusun event dan lokasi ketika kombinasi kalimat baru muncul.
- TF-IDF dipadatkan dengan Truncated SVD sebelum masuk ke neural model.

### Leakage checks

- Test history tidak identik dengan full train windows.
- Consecutive test windows tidak saling overlap secara exact.
- Hanya sangat sedikit test text yang identik dengan train text.
- Tidak ditemukan shortcut untuk mengambil target langsung dari train.

## Eksperimen awal

### Simple temporal baselines pada continuous series

| Block | Model | h5 | h10 | h15 |
|---|---|---:|---:|---:|
| m1 | Persistence | 52.362 | 65.707 | 74.855 |
| m1 | Mean last 3 | 44.173 | 56.408 | 65.269 |
| m2 | Persistence | 39.740 | 44.911 | 48.886 |
| m2 | Mean last 3 | 31.044 | 35.846 | 39.838 |

Mean tiga timestep terakhir konsisten lebih baik daripada memakai latest speed saja. Ini menunjukkan smoothing adalah prior yang kuat.

### Tail-validation experiments sebelum V1

| Approach | Mean MSE | Keputusan |
|---|---:|---|
| Persistence | sekitar 44.015 | Terlalu lemah |
| Mean last 3 | sekitar 34.379 | Base forecast yang stabil |
| Linear trend extrapolation | sekitar 304.458 | Ditolak; error mudah meledak |
| Shared AR Ridge | sekitar 30.022 | Dipakai sebagai anchor |
| PCA/low-rank correction | sekitar 29.304 | Menjanjikan sebagai ensemble component |
| Daily seasonal lookup | sekitar 46-310, tergantung adjustment | Ditolak sebagai model utama |
| Linear text residual | sekitar 29.97-30.01 | Kontribusi kecil jika berdiri sendiri |

Insight:

- Traffic sangat ditentukan recent history.
- Linear extrapolation berbahaya untuk MSE karena shock sesaat menghasilkan prediksi ekstrem.
- Daily seasonality ada, tetapi regime antarhari/blok berubah.
- Text lebih cocok sebagai contextual correction daripada model utama.

## V1 - AR + residual GraphSAGE + text + blend

### Konfigurasi

- Full mode, CUDA.
- Batch size 16.
- Training stride 2.
- 7.366 training windows dan 1.410 validation windows.
- Hidden size 48.
- Maksimum 12 epoch, best epoch 9.
- Runtime sekitar dua menit di Kaggle.

Runtime tersebut valid karena:

- graph sangat sparse;
- model compact;
- setiap epoch hanya sekitar empat detik;
- validation stage sekitar 50 detik;
- full refit sembilan epoch sekitar 36 detik.

### Validation result

| Horizon | AR MSE | GNN MSE | GNN blend weight | Blend MSE | Improvement blend vs AR |
|---|---:|---:|---:|---:|---:|
| h5 | 26.4689 | 24.7776 | 0.8608 | 24.7321 | 6.56% |
| h10 | 30.0597 | 28.1663 | 0.7766 | 27.9955 | 6.87% |
| h15 | 33.4695 | 31.2688 | 0.7384 | 30.9529 | 7.52% |
| **Mean** | **29.9994** | **28.0709** | - | **27.8935** | **7.02%** |

Kesimpulan V1:

- Run berhasil secara teknis.
- GNN mengalahkan AR pada semua horizon.
- Blend mengalahkan kedua individual model pada semua horizon.
- Error AR dan GNN bersifat complementary.
- Bobot GNN menurun saat horizon semakin jauh; AR semakin penting ketika uncertainty meningkat.
- Menambah epoch tanpa perubahan lain tidak disarankan karena validation terbaik di epoch 9 dan plateau setelahnya.

### Submission V1 audit

- File: `submissions/datathon_task1_v1_ar_graphsage_blend.csv`.
- Rows: 2.041.200.
- Unique IDs: 2.041.200.
- NaN: 0.
- ID pertama: `test_00000_h5_r0`.
- ID terakhir: `test_00539_h15_r1259`.

| Horizon | Mean | Std | Min | Max | Exact zeros | Correlation dengan mean-last-3 |
|---|---:|---:|---:|---:|---:|---:|
| h5 | 52.7128 | 19.5392 | 0 | 101.4833 | 16.535 | 0.9899 |
| h10 | 52.7250 | 19.4167 | 0 | 101.4539 | 18.913 | 0.9866 |
| h15 | 52.7494 | 19.3464 | 0 | 101.2645 | 22.235 | 0.9844 |

Diagnosis submission V1:

- Prediksi sangat konservatif dan dekat dengan mean-last-3.
- Mean absolute correction dari mean-last-3 hanya sekitar 1.68, 1.87, dan 1.97 km/h.
- Mean absolute difference h5-h10 hanya 0.30 km/h; h10-h15 hanya 0.19 km/h.
- Ini aman untuk MSE, tetapi mengindikasikan horizon-specific dynamics masih mungkin underfit.

## Hal yang belum dibuktikan oleh V1

V1 belum melakukan ablation terpisah untuk:

- speed-only neural model;
- speed + road embedding;
- speed + graph;
- speed + graph + text.

Karena itu, yang sudah terbukti hanya **kombinasi GNN berguna**. Kontribusi graph dan text secara individual belum dapat diklaim.

## V2 - Validation-driven model search

Notebook terkini: `notebooks/source/datathon_task1_v2_2_model_search_kaggle_runtime_safe.ipynb`.

Status: **notebook selesai dan lolos fast-mode smoke test, tetapi belum dijalankan full di Kaggle**.

### Kandidat V2

1. Shared AR Ridge.
2. PCA city-state residual.
3. `temporal_only`.
4. `directed_graph`.
5. `graph_text_gate`.
6. `graph_text_zero_aux`.

### Perubahan dari V1

- Incoming dan outgoing graph aggregation dipelajari terpisah.
- Text memakai road-specific bilinear gate.
- Ada auxiliary classification untuk future-zero regime.
- Arsitektur dipilih melalui ablation validation.
- Final neural model memakai stride 1.
- Final neural prediction merata-ratakan seed 42, 2026, dan 3407.
- AR, PCA, dan GNN digabung dengan non-negative simplex weights per horizon.
- Notebook membandingkan full V2 validation score dengan referensi V1 27.8935.

### V2 smoke-test result

- 26 total cells dan 12 code cells.
- Semua code cells berjalan tanpa error dalam fast mode.
- Seluruh jalur AR, PCA, empat ablation, selection, seed confirmation, refit, dan submission sudah diuji.
- Smoke submission berisi 2.041.200 unique IDs tanpa NaN.
- Score smoke **tidak boleh dibandingkan** dengan V1 karena hanya memakai subset kecil dan satu epoch.

### Kaggle runtime incident dan V2.1 fix

Run V2 pertama di Kaggle berhenti sebelum neural training saat membuat `torch.optim.AdamW`:

```text
AttributeError: module 'torch' has no attribute '_utils'
```

Evidence:

- AR berhasil: mean validation MSE 29.9828.
- PCA residual berhasil: mean validation MSE 29.4135.
- TF-IDF/SVD berhasil.
- Error muncul tepat saat optimizer pertama dibuat untuk `temporal_only`.
- Notebook tidak menimpa variable `torch`, tidak menjalankan `pip install`, dan memakai package PyTorch dari Kaggle.

Root cause: import state/build PyTorch Kaggle menyediakan internal module `torch._utils`, tetapi tidak memasangnya sebagai atribut top-level `torch`. Import `torch._dynamo` oleh AdamW mengharapkan atribut tersebut.

V2.1 fix:

```python
if not hasattr(torch, "_utils"):
    torch._utils = importlib.import_module("torch._utils")
```

Cell konfigurasi sekarang juga melakukan satu AdamW backward/step sebagai preflight. Jika runtime optimizer rusak lagi, notebook gagal dalam beberapa detik sebelum PCA dan TF-IDF, bukan setelah preprocessing mahal. Reproduksi lokal dengan atribut `torch._utils` sengaja dihapus menghasilkan error yang sama; bootstrap di atas membuat AdamW step berhasil.

Saat menjalankan V2.1 di Kaggle, gunakan **Restart Session** lalu **Run All** agar tidak mewarisi partial `torch._dynamo` import dari run yang gagal.

### 2026-07-18 - V2.2 DataLoader worker runtime fix

- **Status:** fix selesai dan menunggu full Kaggle rerun.
- **Artifact:** `notebooks/source/datathon_task1_v2_2_model_search_kaggle_runtime_safe.ipynb`.
- **Configuration:** `NUM_WORKERS=0` untuk seluruh DataLoader; optimizer bootstrap dari V2.1 tetap dipertahankan.
- **Result:** V2.1 melewati AdamW preflight dan mulai `temporal_only`, tetapi gagal pada batch pertama di `DataLoader worker process 0` dengan `AttributeError: module 'torch' has no attribute 'dtype'`.
- **Insight:** main PyTorch process sudah sehat; namespace rusak hanya terjadi pada multiprocessing worker ketika default collate membuat shared storage. Local smoke sebelumnya tidak menangkap masalah karena local branch memang menggunakan zero workers.
- **Decision:** hentikan multiprocessing DataLoader di Kaggle. Dataset hanya sekitar 7.366 experiment windows/epoch dan 14.731 final windows, sehingga stabilitas lebih penting daripada prefetch worker.
- **Next action:** restart Kaggle session, upload V2.2, pastikan configuration output menampilkan `num_workers: 0`, lalu Run All.

### 2026-07-18 - Kaggle accelerator decision for V2.2

- **Status:** **superseded** setelah P100 gagal dan T4 berhasil menjalankan notebook penuh.
- **Artifact:** `notebooks/source/datathon_task1_v2_2_model_search_kaggle_runtime_safe.ipynb`.
- **Configuration:** pilih single GPU P100; `NUM_WORKERS=0`; training FP32; belum memakai AMP, `DataParallel`, atau DistributedDataParallel.
- **Result:** notebook memakai `torch.device("cuda")`, sehingga hanya GPU pertama yang digunakan. Opsi T4 x2 tidak memberi multi-GPU speedup pada kode saat ini.
- **Insight:** P100 lebih cocok untuk workload V2.2 saat ini karena FP32 throughput dan memory bandwidth per GPU lebih tinggi. T4 baru lebih menarik jika notebook diubah ke mixed precision dan/atau benar-benar diparalelkan ke dua GPU.
- **Decision:** keputusan P100 dibatalkan. Gunakan T4 untuk notebook proyek ini karena telah terbukti stabil pada runtime Kaggle yang tersedia.
- **Next action:** pertahankan konfigurasi stabil FP32, `NUM_WORKERS=0`, dan optimizer preflight pada V3.

### 2026-07-18 - V2.2 full Kaggle run on T4

- **Status:** selesai dan berhasil penuh.
- **Artifact:** `notebooks/runs/datathon_task1_v2_2_t4_kaggle_run.ipynb`, `reports/datathon_task1_v2_2_experiment_results.csv`, dan `submissions/datathon_task1_v2_2_blend.csv`.
- **Configuration:** Kaggle T4, PyTorch 2.10.0+cu128, FP32, `NUM_WORKERS=0`, experiment stride 2, final/confirmation stride 1, seed 42/2026/3407.
- **Runtime:** sekitar 8 menit 41 detik, dari 05:50:05 sampai 05:58:46.
- **Result:**

| Model | h5 | h10 | h15 | Mean |
|---|---:|---:|---:|---:|
| AR | - | - | - | 29.9828 |
| PCA residual | - | - | - | 29.4135 |
| temporal only | - | - | - | 29.1315 |
| directed graph | - | - | - | 28.9507 |
| graph + text gate | - | - | - | 28.5643 |
| graph + text + zero auxiliary | - | - | - | 28.5580 |
| 3-seed GNN average | 24.4820 | 27.7241 | 30.5951 | 27.6004 |
| final AR/PCA/GNN blend | **24.4498** | **27.5477** | **30.2832** | **27.4269** |

- **Improvement:** V2 membaik 0.4666 MSE atau 1.67% relatif dari V1 27.8935. Ini improvement valid, tetapi belum breakthrough besar.
- **Ablation insight:** graph memberi nilai tambah di atas temporal-only; text gate memberi gain lebih besar daripada perubahan directed graph; zero auxiliary hanya memperbaiki sekitar 0.006 MSE sehingga manfaatnya nyaris netral.
- **Seed insight:** seed 42/2026/3407 menghasilkan mean 27.9860/28.2856/28.1193; seed averaging menurunkan mean menjadi 27.6004, sehingga variance model nyata dan ensemble seed berguna.
- **Blend insight:** bobot GNN adalah 0.8815/0.7691/0.7275 untuk h5/h10/h15; AR mendapat bobot nol dan PCA makin berguna pada horizon jauh.
- **Submission audit:** 2.041.200 baris, range 0-100.45 km/h, tanpa indikasi output rusak. Prediksi V2 masih sangat dekat dengan V1 (`corr` 0.9988-0.9993), hanya sedikit lebih horizon-specific.
- **Decision:** V2 dipertahankan sebagai submission utama sementara, tetapi V3 harus mencari sumber sinyal baru, bukan hanya menambah epoch atau seed.
- **Next action:** bangun V3 dengan global city context, regime-aware conditioning, evaluasi test-composition-weighted, EMA, soft mixture ablation, visualisasi, dan progress bar.

### 2026-07-18 - Manual reverse engineering after V2.2

- **Status:** selesai untuk rangkaian diagnosis awal.
- **Artifact:** hasil dirangkum di `reports/datathon_task1_v2_2_run_analysis.md`.
- **Regime finding:** classifier logistic sederhana dari trajectory global history (`mean`, `std`, `zero-rate`, kuantil) memisahkan m1 vs m2 pada validation dengan accuracy/AUC 1.0. Test terklasifikasi 372 m1-like dan 168 m2-like atau 68.89%/31.11%, hampir identik dengan proporsi panjang train 68.89%/31.11%.
- **Validation implication:** validation lama memakai 705 window per block sehingga membobot regime 50/50, sedangkan test tampaknya mengikuti proporsi natural train. V3 harus tetap melaporkan balanced score untuk perbandingan, tetapi memilih model berdasarkan score berbobot komposisi test yang diinferensikan.
- **Rejected experiments:** per-road calibrated ridge + graph summary menghasilkan mean 29.5543; PCA nearest-neighbor analog 38.5907; global LightGBM residual 30.0566. Ketiganya lebih buruk dari V2 dan tidak diteruskan sebagai model utama.
- **Hard expert finding:** AR terpisah per regime menghasilkan mean oracle 30.1766, lebih buruk dari shared AR 29.9688. Regime tidak boleh dipakai sebagai hard split model; gunakan sebagai soft global context/gating.
- **V1 vs V2 finding:** mean absolute difference prediksi hanya 0.42/0.47/0.54 km/h untuk h5/h10/h15. Horizon separation V2 memang naik, tetapi belum mengubah karakter model secara material.
- **Decision:** fokus V3 pada global FiLM conditioning dan optional soft mixture-of-experts, dengan hard regime experts hanya dicatat sebagai eksperimen gagal.
- **Next action:** jalankan ablation V2-reference vs global-FiLM vs global-FiLM+EMA vs global-FiLM+EMA+soft-MoE.

### 2026-07-18 - V3 regime-aware global-context notebook

- **Status:** source selesai; fast-mode end-to-end smoke test berhasil; full T4 run pending.
- **Artifact:** `notebooks/source/datathon_task1_v3_regime_global_context_source.ipynb`.
- **Configuration:** 27 cells/12 code cells, Kaggle T4 FP32, `NUM_WORKERS=0`, optimizer preflight, experiment stride 2, confirmation/final stride 1, seed 42/2026/3407, `tqdm` pada preprocessing/training/refit/inference.
- **Model search:** `v2_reference`, `global_film`, `global_film_ema`, dan `global_film_ema_soft_moe`.
- **Validation change:** cutoff train kini sepenuhnya leakage-safe sampai horizon terjauh; notebook melaporkan balanced 50/50 score dan inferred-test-composition score sekitar 69/31. Natural block proportions dipertahankan saat training.
- **Visualization:** dataset distributions, zero-rate, temporal network mean, graph degree, text length, test regime scatter/probability, baseline bars, training curves, ablation bars, block heatmap, seed stability, ensemble weights, horizon MSE, submission distributions, horizon deltas, dan example forecast trajectory.
- **Smoke result:** semua 12 code cells selesai tanpa traceback; 2.041.200 prediction rows; `submission_v3.csv`, experiment CSV, diagnostics JSON, dan checkpoint path berhasil dibuat. Fast subset memilih `global_film`, tetapi smoke score tidak comparable dan tidak dipakai sebagai evidence performa.
- **Insight:** pipeline global context/EMA/MoE sudah teknis valid. Benefit sebenarnya hanya dapat dinilai setelah full T4 run; complexity tidak otomatis diterima karena ablation akan memilih model paling sederhana jika lebih baik.
- **Decision:** V3 siap di-upload dan dijalankan dengan T4. P100 tidak dipakai.
- **Next action:** Run All di Kaggle T4, download executed notebook, `submission_v3.csv`, `v3_experiment_results.csv`, dan `v3_diagnostics.json`; kemudian bandingkan balanced serta test-weighted metric dan leaderboard dengan V2.

### 2026-07-18 - V3 full Kaggle T4 result and evaluation audit

- **Status:** full run berhasil; submission siap dikirim; leaderboard pending.
- **Artifact:** `notebooks/runs/datathon_task1_v3_t4_kaggle_run.ipynb`, `reports/datathon_task1_v3_experiment_results.csv`, `reports/datathon_task1_v3_run_analysis.md`, dan `submissions/datathon_task1_v3_regime_global_blend.csv`.
- **Result:** final balanced MSE 26.2185 (h5 23.6354, h10 26.2748, h15 28.7454); inferred-test-weighted MSE 27.1327. Improvement balanced vs V2 27.4269 adalah 1.2084 atau 4.41%.
- **Ablation:** Global FiLM 26.8540 mengalahkan V2 reference 28.1979 pada search yang sama. EMA 26.9765 dan EMA+soft-MoE 26.9739 tidak mengalahkan FiLM biasa.
- **Seed result:** seed mean 26.7808/26.7202/26.8892; averaging menurunkan mean menjadi 26.3241. Median best epoch untuk refit adalah 6.
- **Ensemble:** PCA weight 0.0886/0.1851/0.2594 untuk h5/h10/h15; AR weight nol; blend memperbaiki GNN seed-average sebesar 0.1055 MSE.
- **Regime result:** classifier tetap memisahkan validation dengan accuracy/AUC 1.0 dan menemukan test 372 m1-like/168 m2-like atau 68.89%/31.11%.
- **Evaluation audit:** formula dan temporal target split benar; tidak ada test target leakage. Angka 26.2185 valid untuk holdout balanced, tetapi bukan unbiased leaderboard estimate karena model selection, early stopping, dan blend fit menggunakan holdout yang sama. TF-IDF/SVD juga melihat validation text tanpa label. Ini acceptable/transductive, bukan cheating, tetapi rolling OOF dibutuhkan untuk estimasi lebih ketat.
- **Minor EDA issue:** plot clause count memakai delimiter `" | "`, padahal text dipisahkan oleh titik; median clause 1 pada plot tidak benar. Ini hanya bug visualisasi dan tidak memengaruhi TF-IDF, model, metric, atau submission.
- **Submission audit:** 2.041.200 unique IDs, urutan persis sample submission, NaN 0, range 0–99.5052 km/h.
- **Prediction insight:** dibanding V2, MAE perubahan 0.760/0.918/1.006 km/h dan correlation 0.9977/0.9962/0.9953. Horizon separation meningkat; V3 adalah perubahan model yang lebih material daripada V1→V2.
- **Decision:** submit V3 sekarang sebagai entry terpisah. Jangan mengklaim leaderboard 26 sebelum score resmi keluar; ekspektasi lokal test-like lebih dekat 27.13.
- **Next action:** catat leaderboard V3. Jika waktu memungkinkan, V4 dimulai dari rolling CV, clause-level event-to-road attention, inferred time-of-day conditioning, lalu compact diffusion/adaptive graph model.

### 2026-07-18 - V3 public leaderboard gap diagnosis

- **Status:** public result audited; validation design root cause identified.
- **Artifact:** `reports/datathon_task1_v3_public_lb_gap_analysis.md`; Kaggle public score screenshot supplied by user.
- **Result:** V3 public MSE 38.639 vs local balanced 26.2185 and local test-weighted 27.1327.
- **Code audit:** submission ID/order, sample-horizon-road reshape, h5/h10/h15 target offsets, MSE formula, and absence of NaN all remain correct. No evidence of a code-formatting failure or test-target leakage.
- **Root cause:** the single validation fold uses the last two days, which are unusually easy in both blocks. Mean-last-3 MSE is 35.6338 on test-weighted tail validation but 49.1895 across all natural train origins. Daily MSE ranges 35.57–72.13 on m1 and 27.62–41.32 on m2.
- **Cross-check:** V3 improves the easy tail baseline by 23.86%; transferring that ratio to the full-period baseline predicts 37.45, close to public 38.639. The leaderboard gap is therefore quantitatively consistent with sampling shift.
- **Validation decision:** replace the tail split with purged 5-fold day-block CV, fold-local preprocessing, natural OOF aggregation, and OOF ensemble fitting. Keep an untouched fold/nested selection for the final estimate.
- **Reverse engineering:** nearest text cosine median sekitar 0.75, tetapi closest history among top-10 text neighbors still has median RMSE 8.29 km/h and no near-exact matches; analog lookup is low priority. Time-of-day can be inferred with median OOF phase error sekitar 34 menit and is a promising feature.
- **Model decision:** reaching public area 20 is not an enhancement-only step. V4 should combine inferred cyclical time, clause-level road-conditioned event attention, and a compact diffusion/adaptive spatiotemporal graph model; Global FiLM remains useful context.
- **Next action:** if another submission slot/time remains, use V3 as current benchmark. Build and rank V4 only with corrected day-block OOF; do not optimize against the old 26.22 tail score.

### 2026-07-18 - V4 purged-day phase/clause diffusion notebook

- **Status:** source selesai; final fast-mode smoke test berhasil; full Kaggle T4 run pending.
- **Artifact:** `notebooks/source/datathon_task1_v4_purged_day_phase_clause_diffusion_source.ipynb`.
- **Validation:** 3-fold day-block OOF dengan origin yang history dan h15 target-nya tetap di hari yang sama; fold assignment `day % 3`; CV stride 2; natural block proportions; fixed 8 epochs; ensemble weights dievaluasi cross-fit antar-fold.
- **Model ablations:** `global_tcn_diffusion`, `phase_tcn_diffusion`, dan `phase_clause_geo_diffusion`.
- **Architecture:** gated dilated temporal convolution (dilation 1/2/4), global FiLM, inferred cyclical phase auxiliary task, 126-road spatial anchor snapshot, clause-level hashed event/location encoding, road-conditioned attention, directed physical diffusion, geometry kNN, dan learnable edge gates.
- **Leakage controls:** validation tidak lagi menggunakan easy two-day tail; window tidak melintasi day fold; text location hashing tidak fit ke validation/test; fold normalization fit hanya pada train fold; epoch fixed; ensemble score memakai held-fold weights.
- **Runtime controls:** T4 FP32, batch 12, `NUM_WORKERS=0`, `tqdm`, 3 seeds hanya untuk neural candidates dengan OOF weight di atas 5%. Estimasi runtime 25–90 menit bergantung active candidates dan T4 throughput.
- **Smoke result:** 22 cells/10 code cells; seluruh 10 code cells berjalan tanpa traceback di local fast mode; OOF, cross-fit weights, dynamic refit, checkpoint, diagnostics, dan 2.041.200-row submission path berhasil dibuat. Fast score tidak comparable.
- **Visuals:** daily difficulty, fold assignment, parsed event types/clause counts, graph degree/geometry, OOF horizon bars, training curves, fold stability, cross-fit/final weights, submission distributions, horizon deltas, dan correction scatter.
- **Decision:** V4 adalah notebook kandidat berikutnya; gunakan T4 dan Run All. Ranking model hanya berdasarkan corrected natural OOF/crossfit score, bukan old local 26.22.
- **Expected outputs:** `submission_v4.csv`, `v4_cv_results.csv`, `v4_crossfit_weights.csv`, `v4_final_weights.csv`, `v4_diagnostics.json`, checkpoint active models, dan executed notebook.
- **Next action:** jalankan full di Kaggle T4, download seluruh output, lalu bandingkan `crossfit_mean` dengan public V3 38.639 dan submit V4 sebagai entry terpisah jika audit valid.

### 2026-07-18 - Raphael low-rank notebook comparison

- **Status:** external notebook audited; reported filename/public result sekitar 37.6; proper local OOF 32.6757.
- **Artifact:** `/Users/timotiuspatrick/Downloads/notebook raphael dapet 37,6.ipynb` (external, tidak dipindahkan).
- **Validation:** five purged rolling-origin folds pada endpoint 60/70/80/90/100%, validation sekitar 6% tiap block, natural m1/m2 counts 669/302 per fold. Ini lebih representative daripada old V3 easy tail dan menghasilkan gap local→public yang lebih kecil.
- **Winner:** enhanced direct low-rank PCA forecasting (`k=64`, stride 1, flat/direct target, ridge 0.01, 8 road clusters), q005 clipping, diblend dengan cluster temporal model. Proper OOF 32.6757; h5/h10/h15 29.2052/33.0040/35.8179.
- **Ablation:** low-rank share naik per horizon 0.688/0.736/0.779; text residual memberi relative gain sekitar 0.5%; graph residual ditolak; LightGBM residual ditolak.
- **Important distinction:** notebook juga menampilkan optimistic same-fold ensemble 28.9763, tetapi final evidence memakai cross-fold/proper OOF 32.6757. Angka 37.6 tidak tercetak sebagai local validation di notebook dan kemungkinan adalah public leaderboard result.
- **Transferable insight:** tambahkan enhanced low-rank direct model sebagai kandidat OOF/ensemble V4 atau V4.1. Jangan mengasumsikan graph/text complexity pasti membantu; ablation Raphael mendukung low-rank city-state sebagai anchor utama.
- **Decision:** biarkan V4 yang sedang berjalan selesai. Setelah output tersedia, bandingkan corrected crossfit OOF dan public score; jika V4 neural tidak jelas mengalahkan, buat blend/V4.1 dengan Raphael-style low-rank direct component.

### 2026-07-18 - Malfa public 37.1 notebook comparison

- **Status:** external notebook audited; filename/public score sekitar 37.1; local inferred-test-weighted blend 32.5292.
- **Artifact:** `/Users/timotiuspatrick/Downloads/notebook malfa (37,1).ipynb` (external, tidak dipindahkan).
- **Lineage:** notebook memakai arsitektur/pipeline V3 Global FiLM, lalu mengganti easy tail validation dengan randomized 5-way purged day assignment dan satu holdout fold.
- **Validation result:** validation 3.339 origins (m1 2.346, m2 993); PCA 37.4570; selected single-seed soft-MoE 34.3610 weighted; three-seed average 33.3530; final PCA/GNN blend 32.5292 weighted.
- **Selected model:** `global_film_ema_soft_moe`, berbeda dari original V3 yang memilih plain Global FiLM. PCA weight naik per horizon 0.190/0.282/0.349; GNN weight 0.810/0.718/0.651.
- **Insight:** public gain vs V3 terutama berasal dari representative day split yang mengubah architecture/ensemble selection, bukan model family baru. Single randomized holdout masih lebih optimistis daripada V4 full 3-fold crossfit, tetapi jauh lebih baik daripada easy tail.
- **Comparison:** Raphael memakai proper 5 rolling folds + enhanced low-rank direct model dan mendapat sekitar 37.6; Malfa memakai one purged randomized day fold + V3 neural/PCA dan mendapat sekitar 37.1; V4 memakai all 3 day folds, fixed epochs, cross-fitted weights, phase/TCN/clause/geometry, tetapi full performance masih pending.
- **Decision:** jangan hentikan V4 hanya karena runtime. Jika V4 corrected crossfit mean jelas di bawah sekitar 32.5 dan stabil antar-fold, peluang mengalahkan 37.1 masuk akal. Jika di atas 34, prioritaskan hybrid low-rank/PCA + Malfa/V4 blend daripada menambah graph complexity.

### 2026-07-18 - Deadline status: V4 refit and V5 rapid hybrid

- **Status:** sekitar 1,5 jam tersisa menurut user; V4 masih menjalankan full refit; V5 rapid source selesai dan smoke-tested.
- **V4 progress:** OOF selesai setelah sekitar 59 menit dengan 7.469 rows dan natural proportions 68.90%/31.10%. Cross-fitted MSE h5/h10/h15 30.5275/34.6128/37.1528, mean 34.0977.
- **V4 decision signal:** OOF 34.10 lebih buruk daripada local proper Malfa 32.53 dan Raphael 32.68. Semua tiga V4 neural candidates mendapat weight >5%, sehingga refit menjalankan 3 architectures × 3 seeds × 8 epochs. Pada elapsed sekitar 90 menit, refit sudah berjalan sekitar 31 menit; sisa diperkirakan 45–80 menit.
- **Runtime insight:** T4×2 tidak memberi speedup karena kode memakai satu `cuda:0`. Tidak ada log baru selama refit karena cell baru mencetak setelah seluruh model/test inference selesai; `Output 0 B` sebelum selesai adalah normal.
- **V5 artifact:** `notebooks/source/datathon_task1_v5_rapid_malfa_lowrank_hybrid_source.ipynb`.
- **V5 design:** fixed Malfa winner `global_film_ema_soft_moe`, dua validation/final seeds, 10/12 epoch caps with patience, plus Raphael-inspired direct low-rank PCA (`k=64`, whitened flat 15-step latent Ridge alpha 100), existing PCA residual, AR, and per-horizon non-negative simplex ensemble.
- **V5 validation:** purged randomized-day holdout Malfa; no four-model architecture search. DirectLR gets deployed only if validation simplex assigns positive weight.
- **V5 runtime target:** 20–45 menit pada T4. Source memiliki 27 cells/12 code cells; full fast-mode Run All completed without traceback; submission path produced 2.041.200 rows. Smoke scores are not comparable.
- **Decision:** V5 adalah final under-one-hour attempt with best evidence transfer from Malfa/Raphael. Tidak ada jaminan mengalahkan public 37.1. Jika V4 selesai tepat waktu, simpan submission V4; jalankan V5 hanya bila masih tersedia sekitar 45–60 menit/session quota.
- **Next action:** Run All V5 pada T4, download `submission_v5.csv`, `v5_experiment_results.csv`, `v5_diagnostics.json`, dan executed notebook; submit sebagai entry terpisah.

### 2026-07-18 - V5 rapid hybrid full Kaggle result

- **Status:** full Kaggle T4 run selesai tanpa exception dalam 579 detik atau 9 menit 39 detik; submission lolos audit dan siap disubmit.
- **Artifacts dari Kaggle:** executed notebook `/Users/timotiuspatrick/Downloads/dataton-task-1.ipynb` dan folder `/Users/timotiuspatrick/Downloads/results` berisi `submission_v5.csv`, diagnostics, experiment CSV, serta dua neural checkpoint.
- **Individual validation:** PCA 37.4570 balanced; Direct Low-Rank 32.6686 balanced; two-seed `global_film_ema_soft_moe` 31.1509 balanced dan 33.5191 inferred-test-weighted.
- **Final blend:** balanced h5/h10/h15 26.5988/29.1804/31.0176, mean **28.9323**; inferred-test-weighted h5/h10/h15 28.3321/31.3501/33.4092, mean **31.0305**.
- **Improvement versus Malfa local reference:** inferred-test-weighted MSE membaik 1.4987 atau 4.61% dari 32.5292; balanced MSE membaik sekitar 1.4124 atau 4.65% dari 30.3447.
- **Ensemble insight:** AR mendapat bobot 0 pada semua horizon; PCA mendapat 0.131/0.117/0.111; DirectLR naik 0.403/0.546/0.596; GNN turun 0.466/0.337/0.293. Ini evidence kuat bahwa low-rank city-state paling komplementer dan makin penting untuk horizon jauh.
- **Submission audit:** 2.041.200 baris, urutan ID persis sample submission, 540 samples × 3 horizons × 1.260 roads, duplikat/NaN/Inf nol, range 0–99.0485 km/h.
- **Validation caveat:** 31.0305 bukan unbiased leaderboard estimate karena simplex weights di-fit dan di-score pada randomized-day holdout yang sama; TF-IDF/SVD juga transductive terhadap validation text. Tidak ada target leakage atau format bug, tetapi absolute score tetap optimistis.
- **Leaderboard expectation:** bila gap local-to-public Malfa sekitar 4.57 terbawa secara kasar, V5 berpotensi berada sekitar 35.6; ini hanya heuristic, bukan jaminan. Submit V5 sebagai entry terpisah sebelum eksperimen berikutnya.
- **Next action:** V6 rapid harus menggunakan satu PCA maksimum untuk membuat multi-rank DirectLR candidates, alpha per horizon, seed neural ketiga, dan calibration/evaluation split untuk mengecek stabilitas ensemble. Jangan menghabiskan runtime pada AR atau architecture search yang sudah kalah.

### 2026-07-18 - V6 compute-budget decision

- **Decision:** user menolak penambahan seed ketiga; V6 tetap memakai seed 42 dan 2026.
- **Reasoning:** seed averaging memang konsisten membantu, tetapi marginal gain seed ketiga jauh lebih kecil daripada gain DirectLR dan harus membayar validation training serta full-data refit sekali lagi. Ini low-ROI untuk notebook rapid.
- **Reallocated budget:** DirectLR sweep dipersempit ke rank 48/64/80 dan alpha 30/100/300 dari satu maximum PCA, ditambah fixed road-local residual variants dan split-calibrated ensemble weights.
- **Runtime target:** sekitar 12–18 menit pada T4, dekat dengan runtime V5 9m39s dan jauh di bawah satu jam.
- **Artifact:** `notebooks/source/datathon_task1_v6_stable_multirank_lowrank_hybrid_source.ipynb`; final fast-mode smoke test berhasil 12/12 code cells tanpa error dan menghasilkan submission, experiment CSV, serta diagnostics JSON.

### 2026-07-18 - Raphael V2 PCA + directed residual-GNN audit

- **Status:** external executed notebook selesai tanpa error dalam 11.56 menit; belum memiliki public leaderboard score.
- **Artifact:** `/Users/timotiuspatrick/Downloads/notebook raphael baru (belom di submit kaggle).ipynb` (external, tidak dipindahkan).
- **Validation:** five grouped-day folds memakai `day % 5`; folds 0/1/2 untuk development, fold 3 sebagai locked audit, fold 4 cheap PCA check. Semua history dan h15 target diwajibkan berada pada hari yang sama, sehingga train/validation day groups disjoint.
- **Main result:** PCA48 + directed residual-GNN mendapat natural development OOF 31.8935 dan locked audit 32.8835. Berdasarkan `pca_df` dengan weighting yang sama, PCA48 murni sekitar 33.0451 pada development dan 34.0666 pada locked fold; residual-GNN memberi gain sekitar 1.15 dan 1.18 MSE.
- **Architecture ablation fold 0:** temporal 32.6043; +road embedding 32.5833; +directed graph 32.4436; +global FiLM 32.4823; +text 33.3273. Winner adalah road embedding + directed graph tanpa FiLM dan tanpa text.
- **Core transferable idea:** forecast low-rank PCA dijadikan anchor; neural network tidak memprediksi speed absolut, melainkan residual per-road/per-horizon. Head diinisialisasi nol, residual dinormalisasi per road/horizon, loss memakai 0.9 MSE + 0.1 SmoothL1, lalu residual didamp secara cross-fitted dengan beta h5/h10/h15 0.966/0.905/0.862.
- **PCA detail:** rank 48 sedikit dipilih atas rank 64; latent direct ridge memakai scale-aware diagonal regularization `0.01 * diag(X'X)`, bukan satu alpha absolut. PCA juga fit fold-local dan memakai per-road q0.005/q0.995 clipping untuk corrected anchor.
- **Robustness:** hybrid menang pada 100% development validation days menurut notebook, correction magnitude hanya 0.807 km/h, dan locked audit tetap membaik. Ini lebih kredibel daripada selection/weight score pada holdout yang sama.
- **Reporting caveat:** final comparison table mencampur block-macro baseline dengan natural-weighted hybrid, sehingga angka PCA48 `31.0845` tidak directly comparable dengan hybrid `31.8935`. Daily table juga mengisi `pca_mse` dan `linear_mse` dari variabel linear anchor yang sama. Acceptance guard tidak membandingkan langsung terhadap pure PCA, walaupun consistent natural fold scores tetap menunjukkan hybrid menang.
- **Seed insight:** final notebook menjalankan seed tambahan secara runtime-gated, tetapi tidak menyediakan OOF ablation yang membuktikan marginal gain seed kedua/ketiga. Ini tidak mengubah keputusan V6 untuk tetap dua seed.
- **Decision for current V6:** jangan hentikan V6 yang sedang berjalan. V6 sudah menguji rank 48/64/80, local residual persistence, dan split-calibrated ensemble weights, tetapi neural component-nya masih absolute forecast. Setelah V6 selesai, bandingkan primary crossfit/stability dengan Raphael locked 32.8835.
- **Best next architecture if needed:** V7 rapid sebaiknya memakai V6 best low-rank anchor + zero-init compact directed residual-GNN, normalized residual target, SmoothL1 mixture, and cross-fitted horizon damping; skip text, FiLM, architecture search, dan seed ketiga.

### 2026-07-18 - V6 stable multi-rank full Kaggle result

- **Status:** full Kaggle T4 run selesai tanpa exception dalam 601 detik atau 10 menit 01 detik; 12/12 code cells executed dan submission lolos audit.
- **Artifacts dari Kaggle:** `/Users/timotiuspatrick/Downloads/dataton-task-1.ipynb` dan `/Users/timotiuspatrick/Downloads/results` berisi V6 submission, experiment CSV, diagnostics, dan dua checkpoints.
- **Primary result:** cross-fitted balanced MSE 29.1613 dan inferred-test-weighted MSE **31.2587**. Robust averaged-weight diagnostic adalah 29.0873 balanced dan 31.1688 weighted.
- **Low-rank breakthrough:** V5 DirectLR balanced 32.6686 turun menjadi 30.0756 pada V6, gain 2.5929 atau 7.94%. Dua selected variants adalah rank48/alpha30/resid-soft dan rank64/alpha30/resid-soft; rank80 serta alpha100/300 kalah.
- **Residual insight:** fixed local residual scales 0.30/0.15/0.05 selalu menang atas base variant pada top candidates. Local road detail berguna terutama h5 dan harus semakin didamp pada horizon jauh.
- **Ensemble weights:** combined DirectLR 44.63%/62.21%/66.21% untuk h5/h10/h15; GNN 53.33%/33.48%/25.51%; PCA hanya 2.04%/2.02%/3.17%; AR 0%/2.29%/5.10%.
- **Weight stability:** A/B L1 differences 0.1065/0.1248/0.2042; crossfit-to-diagnostic gap hanya 0.0899 MSE. Same-fold weight optimism kecil, walaupun h15 paling tidak stabil.
- **Comparison with V5:** V6 robust diagnostic 31.1688 tidak mengalahkan V5 same-fold 31.0305, selisih +0.1384 atau 0.45%. Perbandingan ini tetap tidak fair karena V5 tidak punya cross-fitted-weight score.
- **Prediction comparison:** V6 vs V5 correlation 0.999669, MAE 0.3338 km/h, delta RMSE 0.4995 km/h. Final output belum berubah cukup besar untuk disebut breakthrough leaderboard.
- **Submission audit:** 2.041.200 unique ordered IDs, NaN/Inf/duplicate nol, range 0–99.1477 km/h, mean/std 52.8388/19.4197.
- **Decision:** submit V6 sebagai entry terpisah dan pertahankan V5. Jangan tambah seed atau memperluas rank sweep. Next high-value path adalah V6 best low-rank anchor + Raphael-style zero-init directed residual-GNN with normalized residual and cross-fitted horizon damping.
- **Analysis artifact:** `reports/datathon_task1_v6_run_analysis.md`.

### 2026-07-18 - V7 DirectLR residual directed-GNN source

- **Status:** source selesai; final FAST_MODE smoke test berhasil 21/21 code cells tanpa exception dan menghasilkan anchor/final submissions, experiment CSV, daily CSV, serta diagnostics JSON.
- **Artifact:** `notebooks/source/datathon_task1_v7_directlr_residual_directed_gnn_source.ipynb`.
- **Core design:** fold-local whitened DirectLR rank 48/64, alpha 30, V6 soft local residual scales 0.30/0.15/0.05 menjadi anchor; zero-initialized compact neural network belajar normalized `truth - anchor` residual.
- **Neural search:** hanya temporal, road embedding, dan directed graph. Text, Global FiLM, EMA, MoE, architecture expansion, dan seed tambahan sengaja dikeluarkan berdasarkan Raphael residual ablation dan V6 evidence.
- **Validation:** day-group folds 0/1/2 untuk development, fold 3 locked audit, fold 4 cheap anchor diagnostic; history sampai h15 wajib berada dalam hari yang sama. Rank dipilih hanya dari development folds.
- **Residual controls:** per-road/per-horizon residual scaling fit pada train fold, 0.9 MSE + 0.1 SmoothL1, zero-init head, cross-fitted held-fold beta, daily/block/horizon checks, dan correction-magnitude guard.
- **Acceptance gate:** residual dipakai hanya jika development gain >0.10, locked gain >0.05, h5/h15 constraints lolos, kedua blocks tidak memburuk, daily win rate >=60%, dan correction magnitude <10 km/h. Jika gagal, `submission_v7.csv` otomatis identik dengan DirectLR anchor.
- **Seed/runtime:** satu neural seed 42; target full T4 sekitar 12–18 menit. `tqdm` tersedia pada anchor folds, cache, training epochs, OOF, full anchor, dan inference.
- **Smoke evidence:** rank 8 fast subset; development gain 0.0754 dan locked gain 0.0440 tidak melewati gate, sehingga `ACCEPT_NEURAL=False` dan fallback anchor dipilih. Ini expected proof bahwa gate tidak memaksakan model; smoke score tidak comparable.
- **Expected Kaggle outputs:** `submission_v7.csv`, `submission_v7_anchor.csv`, `v7_experiment_results.csv`, `v7_daily_results.csv`, `v7_diagnostics.json`, dan checkpoint `v7_residual_gnn_seed42.pt` hanya jika neural accepted.
- **Next action:** upload source V7, gunakan T4, Run All, lalu download executed notebook beserta seluruh V7 outputs. Decision utama adalah locked anchor→hybrid gain dan `accepted`, bukan development score saja.

### 2026-07-18 - V7 full Kaggle result and final submission decision

- **Status:** full Kaggle T4 run berhasil tanpa exception; 21/21 code cells executed. Total notebook timestamp span 433.7 detik atau sekitar 7m14s; modeled runtime diagnostic 6.85 menit.
- **Artifacts dari Kaggle:** `/Users/timotiuspatrick/Downloads/dataton-task-1-2.ipynb` dan `/Users/timotiuspatrick/Downloads/results-2`.
- **Selected anchor:** whitened DirectLR rank 48, alpha 30, local residual scales 0.30/0.15/0.05. Rank48 resid-soft mengalahkan rank64 resid-soft pada setiap fold yang dilaporkan.
- **Selected residual model:** directed graph + road embedding, raw/un-normalized residual target, 5 epochs, one seed 42. Fold0 ablation temporal/road-embedding/directed adalah 31.7767/31.7532/31.7092.
- **Development result:** anchor 31.6777 menjadi hybrid crossfit **31.1223**, gain 0.5554. Horizon anchor→hybrid 29.5206→28.4398, 31.8992→31.4644, dan 33.6133→33.4627.
- **Locked audit result:** anchor 32.5591 menjadi hybrid **32.0414**, gain 0.5177. Rank, architecture, normalization, epochs, dan beta sudah frozen sebelum fold ini dibuka.
- **Stability:** residual menang pada seluruh 28 development validation days; daily gain min/median/max 0.2458/0.5661/0.7920 MSE; kedua blocks dan semua horizon constraints lolos; correction magnitude hanya 0.427 km/h.
- **Damping:** cross-fitted final beta h5/h10/h15 0.8798/0.7945/0.6484. Neural correction paling berguna pada h5 dan semakin didamp untuk horizon jauh.
- **Acceptance:** `accepted=true`; `submission_v7.csv` adalah output yang direkomendasikan notebook, bukan anchor fallback.
- **Submission audit:** 2.041.200 exact ordered unique IDs, NaN/Inf/duplicate nol, range 0–100.1473 km/h, mean/std 52.7465/19.4495.
- **Prediction diversity:** V7 vs V5 corr 0.997893, MAE 0.7438, delta RMSE 1.2651; V7 vs V6 corr 0.997762, MAE 0.7592, delta RMSE 1.3040. V7 berbeda secara material tetapi tidak tampak rusak.
- **Final decision:** stop improvement dan submit V7 sebagai primary. V5 menjadi backup/diversity candidate. V6 tidak diprioritaskan karena V5/V6 corr 0.999669 dan V6 robust diagnostic sedikit lebih buruk daripada V5 same-fold diagnostic.
- **Caveat:** angka V5/V6/V7 tidak directly comparable karena validation protocol berbeda. V7 dipilih karena kekuatan bukti locked audit dan day stability, bukan karena raw local number paling kecil.
- **Comparison artifact:** `reports/final_submission_comparison_v5_v6_v7.md`.
- **Next action:** submit V7 sekarang. Jika submission/final-selection slot lebih dari satu, submit V5 terpisah sebagai backup; jangan membuat blend tanpa common locked validation. Catat public score berikutnya di `codex.md`.

### Archived expected Kaggle V3 outputs

```text
/kaggle/working/submission_v3.csv
/kaggle/working/v3_experiment_results.csv
/kaggle/working/v3_diagnostics.json
/kaggle/working/v3_<selected_model>_seed42.pt
/kaggle/working/v3_<selected_model>_seed2026.pt
/kaggle/working/v3_<selected_model>_seed3407.pt
```

## Final consolidated insights

### Problem and data

- Dataset berisi 1.260 roads, history 15 langkah atau 60 menit, dan target h5/h10/h15 atau +20/+40/+60 menit.
- Traffic memiliki low-rank city-state yang sangat kuat: autocorrelation global masih sekitar 0.98/0.93/0.86 pada 20/40/60 menit dan pola harian tetap tinggi.
- Block m1 dan m2 berbeda besar. Test composition diinferensikan sekitar 68.89% m1-like dan 31.11% m2-like; validation 50/50 atau easy tail menghasilkan benchmark yang menyesatkan.
- Road graph valid dan directed, tetapi edge correlation hanya sedikit lebih tinggi dari random-pair correlation. Graph berguna sebagai residual correction, bukan sebagai pengganti temporal/low-rank anchor.
- Event text panjang dan banyak duplikat, tetapi hanya dua metadata road names yang langsung cocok dengan English event text. Exact test/train text matches juga sangat sedikit. Text tidak memberi gain stabil pada residual model.
- Tidak ditemukan exact/rounded history leakage atau test-chain overlap yang dapat dipakai sebagai lookup. Analog nearest-neighbor juga tidak cukup dekat untuk menjadi model utama.
- Zero speeds adalah bagian nyata dari data, khususnya m2; submission harus mempertahankan non-negativity tanpa menganggap semua zero sebagai missing value.

### Validation lessons

- V3 local 26.2185 tetapi public 38.639 membuktikan bahwa single easy-tail validation tidak dapat dipakai sebagai absolute leaderboard estimate.
- Window validation harus menjaga history sampai h15 target di dalam day group yang sama. Train dan validation days harus disjoint.
- Same-fold architecture selection, early stopping, dan ensemble fitting membuat metric optimistis walaupun bukan cheating atau target leakage.
- Cross-fitted weights lebih baik daripada same-fold weights, tetapi model selection tetap perlu locked audit.
- V7 protocol paling kuat: folds 0/1/2 untuk development, fold 3 locked audit, fold 4 cheap anchor diagnostic; configuration frozen sebelum audit.
- Jangan membandingkan V5 31.0305, V6 31.2587, dan V7 locked 32.0414 secara mentah karena protocol dan weighting berbeda. Kekuatan evidence harus ikut menentukan pilihan.

### Modeling lessons

- Persistence, mean3/mean10, AR, PCA residual sederhana, nearest analog, per-road calibrated ridge, global LightGBM residual, graph residual klasik, dan hard regime experts semuanya kalah dari low-rank/neural hybrids.
- Low-rank direct forecasting adalah anchor utama. Bobot low-rank meningkat seiring horizon, yang menunjukkan bahwa forecast jauh lebih didominasi city-state global.
- V6 membuktikan alpha 30 lebih baik daripada 100/300, rank 48/64 lebih baik daripada 80, dan soft local residual scales 0.30/0.15/0.05 selalu membantu top DirectLR candidates.
- V7 membuktikan rank 48 mengalahkan rank 64 pada semua fold yang diuji. DirectLR soft-residual juga mengalahkan pure DirectLR.
- Neural network lebih efektif belajar `truth - strong anchor` daripada memprediksi absolute speed sekaligus. Zero-initialized head membuat residual model mulai dari anchor yang aman.
- Directed graph memberi small but repeatable improvement pada residual model. Fold0 temporal/road-embedding/directed MSE adalah 31.7767/31.7532/31.7092.
- Raw residual target sedikit lebih baik daripada normalized residual pada V7: 31.7767 vs 31.7975. Normalization tetap aman sebagai ablation, tetapi tidak dipakai final.
- Cross-fitted residual damping harus turun dengan horizon. Final V7 beta 0.8798/0.7945/0.6484 konsisten dengan residual correction yang paling berguna pada h5.
- Text, Global FiLM, EMA, soft-MoE, dan seed tambahan tidak layak ditambahkan ke residual-GNN tanpa OOF evidence baru. Raphael text residual memburuk dari 32.4436 ke 33.3273; V7 sengaja menghapusnya.
- Seed averaging membantu absolute GNN variance, tetapi marginal gain seed ketiga rendah. V7 satu-seed residual correction sudah lolos locked audit dan seluruh daily checks.

### Version comparison

| Version | Method | Main local evidence | Main limitation | Final role |
|---|---|---:|---|---|
| V5 | Absolute Global-FiLM/EMA/MoE GNN + DirectLR/PCA blend | same-holdout weighted 31.0305 | architecture/epoch/weights memakai holdout sama | backup/diversity |
| V6 | Multi-rank/alpha DirectLR + V5 GNN + split-calibrated weights | crossfit weighted 31.2587; robust 31.1688 | model selection belum locked; output hampir sama dengan V5 | archive |
| V7 | Rank48/alpha30 DirectLR anchor + zero-init directed residual-GNN | development 31.1223; locked audit 32.0414 | public score belum diketahui | primary |

- V5→V6 DirectLR individual membaik 32.6686→30.0756 atau 7.94%, tetapi final blend tidak membaik secara jelas.
- V7 development anchor→hybrid 31.6777→31.1223, gain 0.5554.
- V7 locked anchor→hybrid 32.5591→32.0414, gain 0.5177.
- V7 menang pada 28/28 development days; daily gain min/median/max 0.2458/0.5661/0.7920 MSE.
- Development horizon gain V7 sekitar 1.081 h5, 0.435 h10, dan 0.151 h15.
- V5/V6 prediction correlation 0.999669 sehingga keduanya praktis satu submission family. V7 vs V5 correlation 0.997893 dengan MAE delta 0.7438 km/h, sehingga memberi perubahan nyata tetapi tetap structurally safe.

### Final submission decision

1. **Primary:** `submissions/datathon_task1_v7_directlr_residual_gnn.csv`.
2. **Backup/second final selection:** `submissions/datathon_task1_v5_rapid_hybrid.csv`.
3. **Archive only:** `submissions/datathon_task1_v6_stable_multirank.csv`.
4. Jika Kaggle mengizinkan beberapa submission, submit V7 dan V5 secara terpisah. Jangan blend tanpa common locked validation.
5. Jika final selection mengizinkan dua entries, pilih V7 dan submission V5/V6 dengan actual leaderboard terbaik; sebelum leaderboard evidence, V5 adalah backup default.

- **V7 file cleanup:** hanya `datathon_task1_v7_directlr_residual_gnn.csv` disimpan di folder `submissions`. Salinan `datathon_task1_v7_directlr_anchor.csv` dihapus dari project agar tidak tertukar karena full run menghasilkan `accepted=true`. Anchor asli masih tersedia di `/Users/timotiuspatrick/Downloads/results-2/submission_v7_anchor.csv` dan dapat diregenerasi dari executed notebook.
- **Executed notebook presentation cleanup:** seluruh 21 Markdown cells pada `notebooks/runs/V7 Final Notebook.ipynb` dirapikan menjadi gaya laporan eksperimen berbahasa Indonesia. Heading `Final AI-readable decision report` diganti menjadi `Kesimpulan dan Keputusan Akhir`; seluruh code source, 21 execution counts, 126 output objects, grafik, tabel, dan hasil Kaggle dipertahankan identik berdasarkan protected-content hash.

### Stop rule and next information

- Stop membuat V8 sebelum V7 disubmit. Menggunakan locked fold lagi untuk tuning akan mengurangi nilainya sebagai untouched audit.
- Tidak ada indikasi code-format error, target leakage, NaN, duplicate ID, atau horizon/reshape mismatch pada V5/V6/V7.
- Informasi bernilai tertinggi berikutnya adalah actual Kaggle public score V7, bukan local hyperparameter search tambahan.
- Setelah score keluar, catat public score, public-local gap, dan ranking V5/V6/V7 di milestone baru. Jangan mengubah model hanya karena satu public fluctuation jika private leaderboard masih relevan.

## Final decision rules

> [!success] Submit V7 sebagai primary
> Karena residual model lolos development OOF, locked audit, semua horizon/block guards, dan 28/28 daily comparisons.

> [!note] Simpan V5 sebagai backup
> V5 memakai model family berbeda dan merupakan backup lebih berguna daripada V6 yang hampir identik dengannya.

> [!warning] Jangan over-interpret raw local MSE
> Validation protocol berbeda; representative grouped-day OOF dan locked audit lebih dapat dipercaya daripada angka same-fold yang lebih kecil.

> [!important] Update `codex.md` pada milestone berikutnya
> Wajib catat setiap public/private leaderboard result, submission yang dipilih, failure, bug, atau insight baru sebelum melakukan perubahan model berikutnya.

### 2026-07-18 - Repository publication and Git LFS dataset decision (superseded)

- **Repository:** `patrick12354/Dataton-2026---Rizzz`, private, branch `main`.
- **Initial publication:** commit `cbca9eb` memuat struktur `day 1/{patrick,raphael,malfa}` dan `day 2/{patrick,raphael,malfa}`, README, seluruh artifact Patrick, serta submission; dataset dan smoke output awalnya dikecualikan.
- **Team layout:** dataset Day 1 berada sekali pada `day 1/dataset-task1`; Patrick berisi seluruh notebook/report/checkpoint/submission, sedangkan Raphael dan Malfa disiapkan sebagai workspace kosong. Day 2 masih berupa kerangka.
- **Historical large-file decision:** dataset 189 MB awalnya dimasukkan menggunakan Git LFS, bukan regular Git.
- **Superseded:** keputusan ini diganti pada 2026-07-19; dataset tidak lagi dilacak Git/LFS dan harus disiapkan terpisah oleh setiap collaborator.

### 2026-07-19 - Dataset dipindahkan menjadi local-only

- **Status:** selesai.
- **Artifact:** `.gitignore`, root `README.md`, dan `day 1/README.md`.
- **Configuration:** `day 1/dataset-task1/` dikeluarkan dari Git index dengan file lokal tetap dipertahankan; konfigurasi Git LFS repository dihapus.
- **Result:** dataset Day 1 dan Day 2 tidak lagi masuk commit GitHub.
- **Insight:** dataset kompetisi lebih aman didistribusikan terpisah agar repository kode dan artifact tetap ringan.
- **Decision:** seluruh dataset kompetisi bersifat local-only; collaborator menempatkan dataset pada path yang didokumentasikan.
- **Next action:** lanjutkan commit hanya untuk kode, notebook, dokumentasi, laporan, checkpoint terpilih, dan submission.

### 2026-07-18 - Final notebook team identity

- Sel Markdown pembuka pada `notebooks/runs/V7 Final Notebook.ipynb` dilengkapi identitas Tim RIZZZ, afiliasi Universitas Airlangga, dan daftar anggota: Timotius Christopher Patrick Sihombing, Raphael Angelo Adikara Purnama, dan Aqila Malfa Zahira. NIM tidak ditampilkan pada versi final.
- Judul laporan diubah menjadi deskriptif tanpa penanda versi: **Prediksi Kecepatan Lalu Lintas Menggunakan Direct Low-Rank Regression dan Directed Residual-GNN**.
- Perubahan hanya menyentuh sel Markdown pembuka; 21 execution counts dan 126 output objects hasil Kaggle tetap dipertahankan.
