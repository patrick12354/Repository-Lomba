---
title: Datathon Task 2 - Project Knowledge and Experiment Log
date: 2026-07-19
tags:
  - datathon
  - wikipedia
  - next-click-prediction
  - machine-learning
status: active
last_updated: 2026-07-19
update_policy: every-important-milestone
---

# Datathon Task 2 - Project Knowledge and Experiment Log

Dokumen ini adalah sumber utama insight, keputusan, eksperimen, dan hasil Patrick untuk Day 2. Problem statement lengkap berada di [[penjelasan_lomba]].

> [!important] Aturan wajib pembaruan
> Setiap milestone penting harus langsung diikuti update `codex.md` sebelum handoff atau melanjutkan fase berikutnya.

## Milestone update protocol

Yang dianggap milestone penting:

- audit dataset atau EDA baru selesai;
- candidate-link extractor selesai dibuat atau diubah;
- baseline/model baru selesai diuji;
- validation scheme berubah;
- notebook berhasil atau gagal dijalankan;
- score local validation atau leaderboard baru tersedia;
- submission dibuat atau dikirim;
- bug penting ditemukan, didiagnosis, atau diperbaiki;
- artifact penting dibuat, dipindahkan, atau diganti versi.

Setiap update minimal mencatat:

1. tanggal dan status;
2. path artifact;
3. konfigurasi, split, feature, model, dan seed;
4. hasil terukur, termasuk accuracy/top-k coverage/runtime;
5. insight;
6. keputusan;
7. next action.

Template:

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

## Struktur proyek

```text
day 2/
├── dataset-task2/
│   ├── screenshots/
│   ├── articles.csv
│   ├── categories.csv
│   ├── states_train.csv
│   ├── states_test.csv
│   └── sample_submission.csv
└── patrick/
    ├── codex.md
    ├── penjelasan_lomba.md
    ├── notebooks/
    │   ├── source/
    │   │   ├── datathon_task2_v1_eda_ocr_graph_ranker_source.ipynb
    │   │   └── datathon_task2_v2_shortest_path_tiebreak_ranker_source.ipynb
    │   └── runs/
    ├── checkpoints/
    ├── reports/
    ├── output/
    └── submissions/
```

Dataset tetap satu salinan lokal bersama di `day 2/dataset-task2/` dan di-ignore oleh Git. Folder dataset Day 2 tidak memakai Git LFS karena terdiri dari ribuan file kecil. Artifact eksperimen disimpan sesuai jenisnya setelah diunduh dari Kaggle.

## Kaggle notebook workflow

Source notebook V1:

```text
patrick/notebooks/source/datathon_task2_v1_eda_ocr_graph_ranker_source.ipynb
```

Path dataset kompetisi yang wajib digunakan di Kaggle:

```text
/kaggle/input/competitions/datathon-task-2/dataset-task2
```

Kontrak eksekusi:

- source notebook disimpan di `notebooks/source/`;
- notebook dijalankan manual oleh Patrick di Kaggle;
- output sementara, cache, checkpoint, report, dan submission ditulis ke `/kaggle/working`;
- executed notebook yang sudah diunduh disimpan di `notebooks/runs/`;
- checkpoint dipindahkan ke `checkpoints/`;
- diagnostics dan experiment tables dipindahkan ke `reports/`;
- submission CSV dipindahkan ke `submissions/`;
- setiap hasil, error, insight, keputusan, dan next action langsung dicatat di `codex.md`.

Notebook V1 mengikuti pola final Day 1: setup reproducible, dataset audit, EDA, leakage checks, grouped validation, beberapa baseline/model, error analysis, final refit, submission audit, diagnostics export, dan milestone handoff. Full run Kaggle selesai pada 2026-07-19; hasil audit aktual dicatat pada milestone V1 di bawah.

## Local dan Kaggle execution policy

> [!info] V2 local-first
> Patrick sudah memberi persetujuan eksplisit untuk full V2 di laptop karena pipeline CPU-only dan runtime pendek. OCR/full image extraction tetap sebaiknya di Kaggle atau memakai cache V1.

Aturan operasional mulai setelah audit V2:

- jangan membuat venv baru; gunakan `/Users/timotiuspatrick/Documents/Patrick/Kuliah & Coding/.venv` hanya untuk local smoke test;
- V2 default local memakai full 9.000 rows, 400+400 search, dan LambdaRank; `DATATON_LOCAL_SMOKE=1` mengaktifkan subset cepat;
- local verification cukup membuktikan notebook dapat berjalan end-to-end dan menghasilkan submission dengan schema valid;
- hindari mengulang full 9.000-row CV/model search tanpa hipotesis atau perubahan yang jelas;
- OCR 4.604 screenshots tidak diulang di local; gunakan reusable graph V1;
- hasil local subset tidak boleh dicatat sebagai score model resmi;
- eksperimen baru yang jauh lebih berat dari V2 perlu estimasi runtime sebelum dijalankan local.

## Ringkasan masalah

- Input state: `current_article_id` dan `target_article_id`.
- Kandidat: link biru yang terlihat pada screenshot current article.
- Output: satu `predicted_next_article_id`.
- Metric: exact-match accuracy.
- Train: 9.000 states.
- Test: 6.000 states.
- Artikel/screenshot: 4.604.

## Dataset audit awal

### Integritas file

- `articles.csv`: 4.604 artikel, ID `0..4603`, seluruh title unik.
- `screenshots/`: 4.604 PNG, tepat satu untuk setiap article ID.
- `categories.csv`: 5.204 mappings dan 129 kategori unik.
- `states_train.csv`: 9.000 unique state IDs.
- `states_test.csv`: 6.000 unique state IDs.
- Train-test state ID disjoint dan union-nya tepat `0..14999`.
- Seluruh current, target, dan next article foreign key valid.
- `sample_submission.csv` mempunyai state ID dan ordering yang identik dengan test.

### Category coverage

- 4.598 dari 4.604 artikel memiliki kategori.
- 598 artikel memiliki lebih dari satu kategori.
- Maksimum tiga kategori per artikel.
- Enam artikel tanpa kategori: `34`, `1625`, `1949`, `2761`, `2960`, `4478`.

Feature pipeline tidak boleh menganggap setiap artikel pasti memiliki kategori. Artikel tanpa kategori perlu empty-set/unknown representation.

### Struktur split target

Temuan terpenting dari audit:

- total target unik: 600;
- setiap target mempunyai tepat 25 state;
- train: 360 target unik, seluruhnya hanya ada di train;
- test: 240 target unik, seluruhnya tidak pernah menjadi target di train;
- overlap target train-test: 0.

Konsekuensi:

- model harus generalize ke unseen target;
- target-ID embedding murni tidak akan berguna pada test;
- random row validation akan bocor secara semantik karena target yang sama dapat muncul di kedua sisi;
- validation utama wajib group split berdasarkan `target_article_id`;
- title/category/text representation target harus transferable.

### Coverage current article

- current article unik di train: 3.866;
- current article unik di test: 3.312;
- 446 current article test tidak pernah menjadi current pada train;
- 755 dari 6.000 test states memakai current article yang belum pernah menjadi current di train;
- current-page coverage train terhadap test states: 87,42%.

Karena 12,58% test states memiliki unseen current page, lookup kebiasaan click berdasarkan current saja tidak cukup. Screenshot/link extraction diperlukan untuk generalisasi.

### Label distribution dan sanity baselines

- `next_article_id` unik di train: 1.023.
- Label paling populer adalah article `237`, muncul 1.048 kali.
- Global-most-popular training accuracy: 11,64%.
- Direct-to-target terjadi 67 kali atau 0,74%.
- Tidak ada train row dengan `next_article_id == current_article_id`.
- In-sample current-page majority lookup mencapai 62,46%, tetapi ini bukan validation score dan sangat rentan overfit.

`sample_submission.csv` mengisi prediction dengan current article untuk semua row. Itu hanyalah placeholder; men-submit tanpa menggantinya hampir pasti menghasilkan accuracy nol berdasarkan pola train.

## Validation protocol

Validation utama:

```text
GroupKFold groups = target_article_id
```

Prinsip:

- seluruh 25 state untuk satu target harus berada pada fold yang sama;
- jangan memakai target-ID embedding yang tidak dapat membentuk representasi unseen target;
- laporkan exact top-1 accuracy sebagai metric utama;
- laporkan candidate recall dan top-k ranking accuracy untuk memisahkan error extraction dari error ranking;
- simpan out-of-fold prediction per state untuk audit.

Metric development yang disarankan:

| Metric | Tujuan |
|---|---|
| Candidate recall | Apakah true next link berhasil masuk candidate set? |
| Top-1 accuracy | Sama dengan metric kompetisi. |
| Top-3/top-5 accuracy | Mengukur kualitas ranking sebelum argmax. |
| Accuracy seen/unseen current | Mengukur generalisasi page-level. |
| Accuracy direct/non-direct target | Memisahkan kasus target sudah tersedia sebagai link. |

## Modeling roadmap

Status phase 0-4: **sudah diimplementasikan dan dieksekusi penuh di Kaggle melalui notebook V1**. Heuristic graph-semantic menjadi pemenang grouped OOF dengan accuracy 65,09%; target-conditioned GNN belum diperlukan sebelum ablation dan tuning heuristic V2 selesai.

### Modeling framing yang dipilih

Task ini tidak diperlakukan sebagai image-tabular classification biasa. Screenshot bukan sinyal visual bebas seperti foto; screenshot adalah representasi terstruktur dari halaman dan hyperlink yang tersedia. Framing utama:

```text
screenshot current page -> ekstraksi candidate links -> directed hyperlink graph
(current, target, candidate features) -> goal-conditioned candidate ranking -> next click
```

Pembagian peran data:

- screenshot: menentukan candidate/outgoing links dan posisi link;
- `states_*.csv`: query `(current, target)` serta supervision `next`;
- `articles.csv`: title identity dan text similarity;
- `categories.csv`: semantic/category similarity;
- reconstructed hyperlink graph: distance dan routing features.

Keputusan awal:

- jangan memakai CNN/ViT/CLIP atas screenshot penuh sebagai model utama;
- gunakan computer vision/OCR sebagai preprocessing deterministik dan cache hasilnya;
- lakukan candidate masking agar model hanya memilih link yang tersedia;
- gunakan grouped-by-target validation karena seluruh test target unseen sebagai target;
- model ranking tabular/learning-to-rank menjadi anchor, dengan graph dan semantic features;
- GNN atau target-conditioned neural ranker hanya dipertimbangkan setelah candidate recall dan baseline ranking kuat.

### Urutan model yang direkomendasikan

1. **Sanity baselines:** global next popularity dan current-page majority dengan fallback global.
2. **Candidate extractor:** blue-pixel/link-region detection, OCR, lalu title matching ke `articles.csv`.
3. **Heuristic graph-semantic baseline:** direct-target flag, shortest-path distance, title similarity, category overlap, popularity, dan link position.
4. **Primary learned model:** LightGBM/XGBoost-style pairwise ranker atau binary candidate scorer, satu group per `state_id`.
5. **Ensemble:** blend learned score, graph distance, dan semantic score berdasarkan grouped OOF.
6. **Advanced only if justified:** target-conditioned GNN/value function setelah graph coverage, candidate recall, dan runtime terukur.

Model pertama yang direkomendasikan adalah candidate-masked gradient-boosted ranker, bukan end-to-end multimodal neural network. Dataset hanya memiliki 9.000 labeled states dan test target sepenuhnya unseen, sehingga feature yang transferable dan graph routing lebih sesuai daripada target-ID embedding atau screenshot encoder besar.

### Phase 0 - Reproducible audit dan baselines

1. Loader dan validation checks untuk seluruh CSV.
2. Grouped-by-target cross-validation.
3. Baseline global most-popular next article.
4. Baseline current-page majority dengan fallback global mode.
5. Baseline title/category semantic nearest article sebagai diagnostic.

Baseline unconstrained berguna sebagai sanity check, tetapi final approach sebaiknya melakukan candidate masking.

### Phase 1 - Candidate-link extraction

Screenshot merupakan sumber edge graph. Pipeline awal:

1. baca screenshot satu kali per article;
2. deteksi connected component piksel/link berwarna biru;
3. gabungkan komponen yang berada pada satu baris teks;
4. OCR hanya pada bounding box kandidat agar lebih cepat;
5. normalisasi OCR: casefold, punctuation, whitespace, dan Unicode;
6. exact/fuzzy match terhadap 4.604 title artikel;
7. simpan candidate IDs, OCR confidence, bounding box, dan posisi relatif ke cache.

Screenshot berasal dari 2007 Wikipedia Schools snapshot. Jangan menganggap hyperlink graph Wikipedia live identik dengan graph kompetisi; setiap sumber eksternal harus divalidasi terhadap screenshot.

Target artifact yang disarankan:

```text
patrick/cache/article_link_candidates.parquet
```

Candidate extraction harus dievaluasi pada train menggunakan label `next_article_id`. Candidate recall menjadi batas atas accuracy ranker.

### Phase 2 - Candidate ranking

Untuk setiap `(current, target, candidate)` bangun feature:

- title embedding similarity candidate-target;
- token overlap dan fuzzy title similarity;
- exact/ancestor category match;
- category embedding similarity;
- click frequency candidate secara global;
- click frequency candidate dari current page;
- posisi link pada screenshot;
- OCR confidence;
- apakah candidate sama dengan target;
- graph-neighbourhood/path feature jika link graph cukup lengkap.

Model awal yang masuk akal:

- weighted heuristic sebagai baseline transparan;
- logistic regression atau LightGBM ranker pada candidate pairs;
- embedding-based ranker dengan target-group CV;
- graph shortest-path/learned value function jika reconstructed graph memiliki recall tinggi.

### Phase 3 - Graph planning

Jika candidate extraction menghasilkan graph yang cukup lengkap, setiap artikel menjadi node dan setiap hyperlink menjadi directed edge. Untuk state `(A, B)`, kandidat adalah outgoing neighbours dari `A`.

Ranking dapat memakai:

- shortest-path distance kandidat ke target;
- category-aware edge cost;
- personalized PageRank menuju target;
- learned value function dari trajectories train;
- blend graph score dan semantic score untuk disconnected/noisy OCR cases.

Graph path harus dibangun hanya dari informasi halaman, bukan dari label validation.

### Phase 4 - Ensemble dan submission

- Tune bobot hanya pada grouped OOF.
- Pilih model utama berdasarkan top-1 grouped accuracy.
- Gunakan fallback berurutan: extracted candidates -> learned current links -> global valid-link prior.
- Audit prediction agar article ID valid dan, bila candidate set tersedia, benar-benar outgoing link current page.
- Buat submission dengan menyalin ordering `sample_submission.csv`.

## Risiko utama

### OCR pada screenshot sangat panjang

Sebagian screenshot jauh lebih tinggi dari layar biasa. Full-image OCR akan lambat dan dapat kehilangan teks kecil. Crop berdasarkan warna biru dan proses per-region lebih aman.

### Candidate recall membatasi accuracy

Ranker tidak dapat memilih true next jika extractor gagal memasukkannya. Optimasi extractor dan ranking harus dilaporkan terpisah.

### Popularity shortcut

Distribusi next label sangat skewed, sehingga global/current popularity dapat terlihat kuat. Grouped target validation diperlukan agar peningkatan benar-benar berasal dari goal-directed behavior.

### Unseen target dan unseen current

Semua test target unseen sebagai target, dan 12,58% state memakai current page unseen. Representasi harus berasal dari title/category/screenshot/graph, bukan ID lookup saja.

### Category tidak lengkap

Enam artikel tidak punya kategori dan sebagian artikel multi-label. Gunakan multi-hot/embedding aggregation dengan fallback unknown.

## Milestone log

### 2026-07-19 - Dataset Day 2 dipasang dan diaudit

- Status: selesai.
- Artifact: `day 2/dataset-task2/`, `patrick/penjelasan_lomba.md`, dan `patrick/codex.md`.
- Configuration: audit integritas CSV, article/screenshot mapping, foreign keys, state split, category coverage, target grouping, dan current coverage.
- Result: 4.604 artikel/screenshot cocok 1:1; 9.000 train + 6.000 test membentuk 15.000 state valid; 360 train targets dan 240 test targets disjoint, masing-masing 25 states.
- Insight: split dilakukan berdasarkan target article; validation harus group-by-target. Candidate extraction dari screenshot adalah komponen inti, terutama untuk unseen current pages.
- Decision: dataset disimpan satu salinan lokal bersama dan di-ignore oleh Git; Day 2 tidak memakai Git LFS. Dokumentasi dan seluruh experiment log Patrick dipusatkan di folder ini.
- Next action: siapkan kerangka folder dan notebook Kaggle tanpa mengimplementasikan model.

### 2026-07-19 - Kerangka workspace dan notebook Kaggle disiapkan

- Status: selesai sebagai scaffold; belum dijalankan di Kaggle dan belum ada model.
- Artifact: `patrick/notebooks/source/datathon_task2_v1_experiment_scaffold.ipynb`, `patrick/checkpoints/`, `patrick/notebooks/runs/`, `patrick/reports/`, dan `patrick/submissions/`.
- Configuration: seed 42; Kaggle input `/kaggle/input/competitions/datathon-task-2/dataset-task2`; output `/kaggle/working`; local fallback mencari `dataset-task2` dari current directory dan parent directories.
- Result: notebook memiliki setup reproducible, loader lima CSV, manifest, integrity checks, target-split assertions, validation contract, planned output paths, dan handoff checklist. Tidak ada OCR, training, model, atau submission yang dibuat.
- Insight: pola notebook final Day 1 dipertahankan pada level struktur, tetapi implementasi Day 2 sengaja ditunda sampai eksperimen berikutnya.
- Decision: Patrick akan menjalankan notebook secara manual di Kaggle. Source dan executed run dipisahkan agar history eksperimen tetap jelas.
- Next action: upload scaffold ke Kaggle dan jalankan audit cells; setelah output diterima, simpan executed notebook di `notebooks/runs/` dan catat semua hasil/error di milestone berikutnya.

### 2026-07-19 - Source notebook V1 end-to-end dibuat

- Status: source selesai; belum dijalankan di Kaggle sehingga belum ada score atau submission aktual.
- Artifact: `patrick/notebooks/source/datathon_task2_v1_eda_ocr_graph_ranker_source.ipynb`.
- Configuration: seed 42; 3-fold `GroupKFold(target_article_id)`; Kaggle input `/kaggle/input/competitions/datathon-task-2/dataset-task2`; output `/kaggle/working`; maksimum 40 candidate pair saat training dan 80 saat validation/test.
- Pipeline: integrity audit; EDA artikel, kategori, state, split, dan screenshot; blue-pixel region detection; batched Tesseract OCR; fuzzy title matching; directed hyperlink graph; word/character TF-IDF; reverse-BFS distance; fold-safe click priors; global/current baselines; heuristic ranker; logistic ranker; histogram gradient boosting; fixed rank ensemble; current-mode with ranker fallback; error analysis; full refit; strict submission audit; model/diagnostics export.
- Evaluation design: exact top-1 accuracy sebagai metric utama, ditambah top-3, top-5, candidate recall, per-fold stability, dan error slices. Seluruh transition prior pada OOF hanya dibentuk dari fold-training.
- Runtime safety: OCR memakai checkpoint/resume setiap 100 halaman; `DATATON_FAST_MODE=1` dan `DATATON_OCR_PAGE_LIMIT` tersedia untuk smoke test; pipeline mempunyai fallback jika OpenCV/Tesseract tidak tersedia.
- Planned artifacts: `datathon_task2_v1_ocr_graph_ranker.csv`, `datathon_task2_v1_diagnostics.json`, `datathon_task2_v1_cv_results.csv`, `datathon_task2_v1_rankers.joblib`, dan cache candidate links.
- Insight: keberhasilan V1 terutama dibatasi candidate recall. Jika recall rendah, OCR/title matching harus diperbaiki sebelum menambah kompleksitas model; jika recall tinggi namun accuracy rendah, fokus beralih ke semantic/graph ranking.
- Decision: gunakan candidate-masked histogram gradient boosting/rank ensemble sebagai primary learned family; current/global popularity tetap diagnostic baseline. Jangan memulai GNN sebelum hasil grouped OOF V1 tersedia.
- Next action: jalankan notebook V1 di Kaggle full mode, unduh executed notebook dan artifacts, lalu catat runtime, recall, CV, error, serta leaderboard score di milestone berikutnya.

### 2026-07-19 - V1 local fast-mode smoke test dan visual EDA expansion

- Status: selesai; verification-only, bukan eksperimen performa.
- Artifact: source yang diuji adalah `patrick/notebooks/source/datathon_task2_v1_eda_ocr_graph_ranker_source.ipynb`; output lokal sementara sudah dihapus setelah verifikasi.
- Configuration: memakai existing venv `/Users/timotiuspatrick/Documents/Patrick/Kuliah & Coding/.venv`; `DATATON_FAST_MODE=1`; `DATATON_OCR_PAGE_LIMIT=3`; backend plot non-interaktif; seluruh 20 code cells dijalankan berurutan.
- Result: 20/20 code cells berhasil; OCR tiga halaman menghasilkan 23 directed links; pipeline membentuk 6.000 test predictions tanpa NaN dan lolos strict submission audit. Source tetap memiliki 42 cells: 22 Markdown explanation dan 20 code cells tanpa saved output.
- Visual EDA: title/category distributions, category multiplicity, current frequency, next-label long tail, cumulative popularity, target split, seen/unseen-current share, grouped fold balance, identity overlap, screenshot height/blue density, original-vs-blue-mask preview, graph degrees, candidate recall, graph page coverage, reachability, grouped CV comparison, top-k accuracy, logistic coefficients, dan error slices.
- Textual interpretation: setiap kelompok visual mencetak `INSIGHT ARTICLE`, `INSIGHT STATE`, `INSIGHT VALIDATION`, `INSIGHT SCREENSHOT`, `INSIGHT CANDIDATE`, `INSIGHT GRAPH`, `INSIGHT CV`, atau `INSIGHT ERROR` berdasarkan angka run aktual agar hasil tetap machine-readable.
- Smoke-only result: dengan OCR dibatasi tiga halaman, current-mode terpilih pada reduced fast validation. Nilai ini tidak boleh dianggap score V1 karena raw OCR candidate recall hanya 0,06% pada konfigurasi sengaja-terbatas tersebut.
- Insight: model selection sekarang mencakup baseline dan learned rankers; full run dapat memilih current/global mode jika memang mengalahkan ranker, sedangkan error analysis tetap memakai best pair ranker.
- Decision: jangan menyimpan atau membandingkan score smoke. Jangan membuat venv baru; gunakan venv existing untuk verifikasi lokal dan Kaggle environment untuk full run.
- Next action: jalankan full notebook di Kaggle tanpa `DATATON_FAST_MODE` dan tanpa `DATATON_OCR_PAGE_LIMIT`, lalu catat hasil sebenarnya pada milestone baru.

### 2026-07-19 - Pre-run runtime expectation untuk Kaggle T4 x2

- Status: estimasi sebelum full run, belum merupakan runtime Kaggle aktual.
- Evidence: local fresh smoke memproses tiga screenshot OCR sekitar 1,1 detik dan menyelesaikan pipeline reduced sekitar 17-20 detik. Source default menggunakan `DATATON_FAST_MODE=0`, `DATATON_OCR_PAGE_LIMIT=0`, sehingga seluruh 4.604 screenshot tetap diproses.
- Expected bottleneck: blue-link detection dan Tesseract OCR. Tahap ini CPU/I/O-bound; TF-IDF, reverse BFS, logistic regression, dan histogram gradient boosting juga berjalan di CPU.
- GPU utilization: notebook V1 tidak memakai PyTorch/CUDA. Kaggle T4 x2 tidak memberi speedup berarti pada pipeline saat ini; accelerator yang lebih menentukan adalah CPU dan disk throughput.
- Estimated full runtime: sekitar 45-90 menit pada Kaggle, dengan working estimate 60 menit. OCR diperkirakan 30-70 menit; EDA/TF-IDF/graph 2-8 menit; 3-fold pair modeling, final refit, dan export 5-15 menit.
- Runtime guards: OCR checkpoint/resume setiap 100 halaman; training candidate cap 40; validation/test candidate cap 80; tiga grouped folds; histogram gradient boosting dibatasi 140 iterations.
- Decision: pertahankan V1 CPU-oriented karena estimasi masih aman di bawah jendela lima jam. Jangan menambah GPU neural model sebelum runtime, candidate recall, dan grouped OOF V1 aktual tersedia.
- Next action: catat runtime per stage dari full Kaggle output dan ganti estimasi ini dengan hasil terukur.

### 2026-07-19 - Reusable OCR output bundle untuk V2

- Status: selesai di source dan lolos local fast-mode smoke test; full bundle akan dibuat saat Kaggle full run.
- Artifact output: `/kaggle/working/datathon_task2_v1_reusable/` dan `/kaggle/working/datathon_task2_v1_reusable_bundle.zip`.
- Bundle contents: accepted `task2_v1_link_candidates.csv`; seluruh `task2_v1_ocr_raw_regions.csv`; `task2_v1_ocr_processed.json`; `task2_v1_ocr_quality_by_page.csv`; `task2_v1_ocr_manual_review_sample.csv`; annotated JPEG pada `ocr_review_images/`; `manifest.json`; dan `README_REUSE.txt`.
- Manual review convention: bounding box hijau adalah OCR region yang berhasil dipetakan ke article ID; box merah adalah region unmatched/self-link yang perlu diperiksa. Raw CSV menyimpan bounding box, OCR text/confidence, matched candidate/title, match score, relative position, dan status.
- Reuse workflow: setelah full run, save/download folder atau ZIP dari Kaggle output; upload sebagai Kaggle Dataset; attach dataset tersebut sebagai input notebook V2; periksa `manifest.json` memiliki `is_complete=true`; lalu load `task2_v1_link_candidates.csv` sebagai precomputed hyperlink graph tanpa mengulang OCR.
- Verification: smoke run tiga halaman menghasilkan bundle ZIP valid berisi 11 entries, 23 accepted links, 31 raw OCR regions, tiga annotated review images, dan manifest `processed_pages=3`, `expected_pages=4604`, `is_complete=false`. Nilai false benar untuk deliberately limited smoke run.
- Decision: candidate graph hanya akan dianggap reusable penuh jika manifest complete dan manual sample/quality summary menunjukkan OCR cukup akurat. Jika kualitas kurang, V2 dapat memakai raw regions dan review images untuk memperbaiki matcher tanpa mengulang seluruh EDA/modeling logic.
- Next action: jalankan full V1, review visual dan quality CSV, kemudian upload reusable bundle yang disetujui sebagai input V2.

### 2026-07-19 - Full Kaggle run V1 selesai dan diaudit

- Status: selesai tanpa cell error; seluruh 20 code cells mempunyai execution output dan tidak ada traceback. Artifact sudah dipindahkan dari Downloads ke struktur project pada milestone berikutnya.
- Artifact: submission `submissions/datathon_task2_v1_ocr_graph_ranker.csv`; diagnostics dan CV di `reports/`; fitted rankers di `checkpoints/`; reusable OCR/cache di `output/v1/`; dan executed notebook di `notebooks/runs/datathon_task2_v1_eda_ocr_graph_ranker_kaggle_run.ipynb`.
- Configuration: full mode, seed 42, 3-fold `GroupKFold(target_article_id)`, 40 maksimum training candidates, 80 validation/test candidates, blue-link Tesseract OCR CPU, word/character TF-IDF, reverse-BFS graph distance, fold-safe click priors, heuristic/logistic/histogram-GBDT/rank ensemble/current fallback.
- Runtime: total 47,57 menit. OCR/review pack selesai pada 46,55 menit, sehingga sekitar 97,9% runtime berada sebelum modeling; semantic graph selesai 46,73 menit, grouped OOF 47,25 menit, dan final output 47,57 menit. GPU T4 tidak dipakai oleh pipeline ini.
- OCR result: semua 4.604 pages ditandai processed; 121.460 raw regions; 93.256 unique directed edges; 4.545 pages memiliki accepted outgoing link; median out-degree 16 dan p95 54. Raw OCR train candidate recall 97,83% atau 8.805/9.000 states; OCR plus fold-safe observed transitions 98,37%.
- OCR quality caution: mean matcher accepted-rate 99,05% pada 4.546 pages yang memiliki detected region bukan ground-truth precision. Ada 58 pages tanpa detected region dan satu page (`1577`, The Iron Bridge) dengan region tetapi nol accepted link. Manual review memperlihatkan failure `Iron -> lron`, OCR `Iodine/lodine`, dan beberapa link abad yang tergabung menjadi satu region. Sebanyak 195 train states miss dari raw graph, terkonsentrasi pada 154 current pages; missed next paling sering adalah World War II (50), Iron (19), United Kingdom (16), dan United States (11).
- Graph result: median target dapat dijangkau dari 4.545 nodes; median finite distance sekitar tiga langkah. Extracted graph cukup connected dan graph-distance layak menjadi sinyal utama.
- CV result: heuristic `0,6509 ± 0,0146` top-1, top-3 `0,8991`, top-5 `0,9480`; logistic `0,4383`; rank ensemble `0,4286`; current+rank fallback `0,3867`; histogram GBDT `0,2866`; current mode `0,2381`; global mode `0,1164`. Per-fold heuristic: `0,6630`, `0,6347`, `0,6550`. Direct-target slice 67/67 benar; non-direct accuracy 64,83%; current-once 65,51% dan current-multiple 65,02%, sehingga heuristic tidak bergantung pada repeated-current lookup.
- Model selection: final submission memakai fixed heuristic graph-semantic score, bukan fitted logistic/HGB. Joblib rankers tetap berguna untuk audit/eksperimen tetapi bukan model pembuat submission V1.
- Submission audit: 6.000 rows, ordering `state_id` identik dengan test/sample, seluruh article ID valid, tanpa NaN, 891 unique predictions, dan tidak pernah memprediksi current article. Sebanyak 5.938/6.000 atau 98,97% predictions adalah raw OCR outgoing link; 62 sisanya seluruhnya didukung observed train transition dari current page. Notebook melaporkan candidate-pool validity 100%.
- Reusable bundle audit: `manifest.json` menyatakan `processed_pages=expected_pages=4604` dan `is_complete=true`; ZIP berisi 16 entries dan lolos CRC test tanpa corrupt member. Bundle dapat di-upload ulang sebagai Kaggle Dataset dan V2 cukup membaca `task2_v1_link_candidates.csv`, raw regions, quality table, serta review images tanpa mengulang OCR 46 menit.
- Insight: V1 sudah membuktikan bahwa task ini terutama graph routing, bukan image classification. Candidate extraction hampir mencapai ceiling, sedangkan gap heuristic top-1 65,09% ke top-3 89,91% menunjukkan peluang terbesar berikutnya ada pada ranking/tie-breaking. Learned V1 tertinggal jauh; menambah model kompleks tanpa ablation dan feature calibration belum justified.
- Decision: submission V1 valid dan layak dijadikan baseline/submit untuk memperoleh leaderboard anchor. Reuse bundle disetujui untuk V2, tetapi accepted-rate tidak boleh disebut OCR precision. Jangan mengulang OCR kecuali matcher/region detector memang diubah; lakukan ablation heuristic, tune bobot hanya pada grouped OOF, perbaiki 195 missed train cases dari raw OCR, lalu uji ranker yang lebih cocok untuk per-state ranking.
- Next action: submit V1 untuk leaderboard anchor dan bangun V2 dari reusable bundle dengan graph/heuristic ablation, weight tuning, serta shortest-path reranking.

### 2026-07-19 - Artifact V1 dirapikan mengikuti struktur Day 1

- Status: selesai; folder `/Users/timotiuspatrick/Downloads/results` dan notebook `/Users/timotiuspatrick/Downloads/dataton-day-2.ipynb` sudah dipindahkan, bukan diduplikasi.
- Runs: `patrick/notebooks/runs/datathon_task2_v1_eda_ocr_graph_ranker_kaggle_run.ipynb`.
- Reports: `patrick/reports/datathon_task2_v1_cv_results.csv` dan `patrick/reports/datathon_task2_v1_diagnostics.json`.
- Checkpoint: `patrick/checkpoints/datathon_task2_v1_rankers.joblib`.
- Submission: `patrick/submissions/datathon_task2_v1_ocr_graph_ranker.csv`.
- Bulk output: `patrick/output/v1/` berisi reusable directory, ZIP bundle, raw cache, dan rendered notebook files. Folder `output/` di-ignore Git agar artifact puluhan MB tidak masuk repository.
- Decision: gunakan struktur canonical ini untuk seluruh versi berikutnya; executed notebook tidak boleh disimpan di `source/`.
- Next action: gunakan reusable dataset V1 sebagai input V2 tanpa OCR ulang.

### 2026-07-19 - V2 shortest-path tie-break dirancang dan diverifikasi lokal

- Status: source selesai dan berhasil dijalankan lokal top-to-bottom; belum dijalankan di Kaggle dan belum memiliki leaderboard score.
- Artifact: `patrick/notebooks/source/datathon_task2_v2_shortest_path_tiebreak_ranker_source.ipynb`, `patrick/reports/datathon_task2_v2_design_analysis.md`, `patrick/reports/datathon_task2_v2_preliminary_cv.csv`, dan `patrick/reports/datathon_task2_v2_local_analysis.json`.
- Kaggle input: competition `/kaggle/input/competitions/datathon-task-2/dataset-task2`; reusable utama `/kaggle/input/datasets/timotiuspatrick/datatonday2output/datathon_task2_v1_reusable`; notebook memiliki short-path dan manifest auto-discovery fallback.
- Configuration: seed 42; 3-fold `GroupKFold(target_article_id)`; candidate cap 100; 400 seeded soft configurations; 400 seeded hard-min tie-break configurations; leave-one-row-out training click priors; optional specialized LightGBM LambdaRank.
- New insight: candidate recall V2 98,36%; truth berada pada minimum graph distance pada 95,08% states; hanya 28,32% states memiliki minimum-distance candidate unik. Bottleneck utama adalah tie-breaking di antara beberapa shortest paths.
- Result: V1 rebuilt 64,60%; soft tuned graph-semantic 74,06%; hard shortest-path tie-break **75,93%** dengan fold 77,90% / 74,63% / 75,27%, top-3 92,33%, dan top-5 95,58%. Nested held-fold configuration selection juga 75,93% dan selalu memilih konfigurasi yang sama. Specialized tie LambdaRank sekitar 62,39% dan tidak dipilih.
- Runtime: verifikasi sebelumnya memakai full 9.000 train rows dan selesai 2,06 menit tanpa OCR; 16/16 code cells executed dan tidak ada traceback. Beberapa eksperimen pendahuluan juga sempat diulang pada full data lokal. Ini menjadi run full lokal terakhir tanpa persetujuan eksplisit; setelah milestone ini local hanya smoke/subset dan full run dipindahkan ke Kaggle.
- Execution switch: setelah Patrick mengizinkan local-first, source V2 memakai full local run secara default. `DATATON_LOCAL_SMOKE=1` tetap tersedia untuk 750 rows, 30 targets, search 24+24, dan LambdaRank off. Kaggle tetap memakai full configuration.
- Decision: primary V2 adalah transparent hard-min graph rule; learned LambdaRank hanya comparator. Notebook membuat primary `datathon_task2_v2_hardmin_tiebreak.csv`, soft alternative, OOF, search results, diagnostics, best weights, dan artifact ZIP.
- Caveat: 75,93% adalah local grouped OOF, bukan Kaggle leaderboard. External validation tetap diperlukan sebelum menganggap peningkatan test terkonfirmasi.
- Next action: jalankan source V2 di Kaggle dengan reusable dataset attached, submit primary hard-min CSV, catat public/private leaderboard score, lalu putuskan apakah soft alternative perlu diuji.

### 2026-07-19 - Public leaderboard V1 memvalidasi grouped evaluation

- Status: submission V1 sudah dikirim ke Kaggle oleh Patrick.
- Submission: `patrick/submissions/datathon_task2_v1_ocr_graph_ranker.csv`.
- Local validation: grouped OOF heuristic `0,650889` dengan `GroupKFold(target_article_id)`.
- Public leaderboard: **0,637** berdasarkan screenshot hasil submission Patrick.
- Validation gap: `0,013889` atau sekitar **1,39 percentage points**; public score mempertahankan sekitar 97,87% dari local grouped accuracy.
- Insight: kedekatan public score dengan grouped OOF mendukung bahwa split berdasarkan target dan evaluation pipeline V1 sudah representatif. Random row split tetap tidak boleh digunakan karena target train/test disjoint.
- Caveat: public leaderboard hanya memakai public test subset; private leaderboard masih dapat berbeda. Temuan ini memvalidasi arah evaluasi, bukan menjamin setiap improvement local akan berpindah satu-ke-satu ke leaderboard.
- Decision: pertahankan `GroupKFold(target_article_id)` sebagai validation utama V2. Gunakan leaderboard terutama untuk external calibration, bukan untuk mengganti validation scheme.
- Next action: submit primary hard-min hasil full local terhadap anchor V1 `0,637`, lalu catat gap OOF-to-public V2.

### 2026-07-19 - V2 diubah menjadi local-first dan full run disimpan

- Status: selesai; Patrick memberi persetujuan eksplisit untuk full local V2 karena pipeline CPU-only.
- Source: `patrick/notebooks/source/datathon_task2_v2_shortest_path_tiebreak_ranker_source.ipynb` memakai absolute local data/reuse/output paths. Local full adalah default; smoke subset diaktifkan hanya dengan `DATATON_LOCAL_SMOKE=1`. Kaggle fallback tetap tersedia.
- Configuration: full 9.000 train rows, 3 grouped folds, candidate cap 100, soft search 400, hard-min search 400, dan LightGBM LambdaRank aktif; OCR tidak dijalankan ulang.
- Runtime: 1,36 menit pada laptop menggunakan existing `.venv`; execution mode tercetak `LOCAL FULL`.
- Result: hard-min grouped OOF 75,93%, top-3 92,33%, top-5 95,58%, candidate recall 98,36%; soft tuned 74,06%; tie LambdaRank 62,39%. Best hard-min config tetap ID 269 dan nested held-fold accuracy tetap 75,93%.
- Verification: 16/16 code cells executed, tidak ada traceback; primary submission 6.000 rows, 6.000 unique states, tanpa NaN atau invalid article ID.
- Executed run: `patrick/notebooks/runs/datathon_task2_v2_shortest_path_tiebreak_local_run.ipynb`.
- Primary submission: `patrick/submissions/datathon_task2_v2_hardmin_tiebreak.csv`.
- Alternative submission: `patrick/submissions/datathon_task2_v2_soft_tuned.csv`.
- Full output: `patrick/output/v2/`; artifact ZIP: `patrick/output/datathon_task2_v2_artifacts.zip`; diagnostics/CV copy berada di `patrick/reports/`.
- Decision: V2 tidak perlu dirun ulang di Kaggle untuk komputasi. Kaggle tetap diperlukan hanya untuk submit dan memperoleh public/private leaderboard score.
- Next action: submit `datathon_task2_v2_hardmin_tiebreak.csv`, catat public score, lalu bandingkan gap terhadap grouped OOF 0,7593 dan anchor V1 public 0,637.

### 2026-07-19 - Executed V2 notebook dengan output dibuat eksplisit

- Status: selesai.
- Artifact: `patrick/notebooks/runs/V2 Final Local Notebook.ipynb`.
- Verification: 34 cells, 16/16 code cells executed, 37 output blocks tersimpan, dan tidak ada error output.
- Clarification: source notebook di `notebooks/source/` memang sengaja tanpa output agar reusable; notebook hasil run yang berisi table/plot/log selalu berada di `notebooks/runs/`.
- Decision: gunakan nama `Vx Final Local Notebook.ipynb` untuk executed local notebook agar tidak tertukar dengan source.

### 2026-07-19 - V3 OCR recovery dan error reverse-engineering selesai

- Status: full local run selesai; belum ada leaderboard score.
- Source: `patrick/notebooks/source/datathon_task2_v3_ocr_recovery_reverse_engineering_source.ipynb`.
- Executed notebook: `patrick/notebooks/runs/V3 Final Local Notebook.ipynb`; 18/18 code cells executed, 44 output blocks, tanpa traceback.
- V2 diagnosis: dari 9.000 OOF states terdapat 6.834 correct, 1.723 shortest-path tie-break errors, 295 truth-not-shortest graph errors, dan 148 candidate misses.
- Rejected ideas: fold-safe graph augmentation dari observed train transitions hanya memberi sekitar +0,01 pp; reading order, candidate ID order, shortest-path branching, dan regime-gated config tidak meningkatkan nested accuracy secara stabil.
- OCR recovery: 1.690 suspicious/merged regions menghasilkan 2.162 new edges; 1.482 exact multi-title segmentation dan 680 conservative fuzzy matches. Recovery tidak memakai train labels.
- Graph result: candidate recall naik dari 98,36% ke 99,39%; truth-shortest rate naik dari 95,08% ke 96,93%.
- CV result: recovered hard-min **76,90%** dengan fold 78,63% / 75,50% / 76,57%, top-3 93,92%, top-5 97,17%, dan nested held-fold 76,90%. V2 hard-min adalah 75,93%, sehingga net improvement +0,97 pp atau 87 additional correct OOF states.
- V3 error taxonomy: 6.921 correct, 1.803 shortest-path tie-break errors, 221 truth-not-shortest errors, dan 55 candidate misses. Dari 359 changed predictions, 194 diperbaiki, 107 mengalami regression, dan 58 tetap salah.
- Model decision: primary tetap transparent hard-min config 269 pada recovered graph. Regime-specific nested score 76,69% dan LambdaRank 61,54%, sehingga keduanya tidak dipilih.
- Runtime: 1,37 menit local full, CPU-only, tanpa menjalankan ulang OCR engine.
- Primary submission: `patrick/submissions/datathon_task2_v3_ocr_recovered_hardmin.csv`.
- Alternative: `patrick/submissions/datathon_task2_v3_soft_tuned.csv`.
- Full artifacts: `patrick/output/v3/`, ZIP `patrick/output/datathon_task2_v3_artifacts.zip`, dan `patrick/reports/datathon_task2_v3_run_analysis.md`.
- Insight: extraction ceiling hampir selesai; arah V4 harus mempelajari deterministic tie policy atau richer context di antara shortest-path candidates. Menambah OCR recall saja kini memiliki diminishing returns.
- Next action: submit primary V3, bandingkan public score dengan V1 `0,637` dan V2 jika tersedia, lalu gunakan leaderboard calibration untuk memutuskan apakah reverse-engineering tie policy diteruskan.
# Kebijakan eksperimen aktif (mulai V4)

- Versi tidak menunggu target accuracy akhir. Setiap peningkatan terverifikasi atau milestone diagnosis penting langsung dibekukan sebagai `V4`, `V5`, dan seterusnya agar progres, output, dan keputusan tidak hilang.
- Target jangka panjang tetap mencari accuracy setinggi mungkin, tetapi setiap versi harus punya hipotesis, grouped OOF, error analysis, output notebook, dan reusable artifacts sendiri.
- Run lokal wajib memakai interpreter `/Users/timotiuspatrick/Documents/Patrick/Kuliah & Coding/.venv/bin/python`; workspace sudah diarahkan lewat `.vscode/settings.json`. Jangan membuat venv baru.
- Jangan mengulang OCR penuh. Gunakan cache V1 dan `reports/datathon_task2_v3_recovered_edges.csv`. Recovery hanya menjadi fallback bila artifact tersebut belum dilampirkan sebagai Kaggle input.
- Candidate recall V3 sudah `99,39%`; fokus utama setelah V3 adalah ranking dan shortest-path tie-break. Full run lokal/Kaggle hanya dilakukan untuk hipotesis yang sudah lolos diagnosis murah.

### 2026-07-19 - V4 shortest-path mass selesai dan tersimpan sebagai milestone

- Status: full local run selesai; belum ada leaderboard score.
- Hipotesis: di antara kandidat dengan minimum graph distance yang sama, kandidat yang membuka lebih banyak shortest paths menuju target lebih mungkin dipilih navigator.
- Pre-diagnosis yang ditolak: target-state chain tidak berguna karena next click menjadi current lain pada target sama hanya `0,58%`; deterministic BFS dengan urutan candidate ID, OCR position, atau title hanya menghasilkan sekitar `46–50%`; graph SVD/spectral cosine tidak memberi gain stabil.
- New feature: `log(1 + shortest_path_count)` dihitung pada target-conditioned shortest-path DAG, tanpa label. Production weight dikunci `0,20` di atas skor hard-min V3.
- Grouped OOF: V3 `76,90%` menjadi V4 **77,36%**, naik `0,46 pp` atau 41 additional correct states. Fold V4: `79,60% / 75,67% / 76,80%`; top-3 `94,43%`; top-5 `97,41%`; candidate recall tetap `99,39%`.
- Honest nested alpha selection: `77,17%`, tetap di atas anchor V3 `76,90%`. Alpha terpilih per held fold `0,30 / 0,20 / 0,15`, sehingga arah fitur stabil walaupun magnitude optimal sedikit berbeda.
- Prediction changes: 291 state berubah; 129 error V3 diperbaiki, 88 prediction benar mengalami regression, 74 tetap salah; net +41.
- V4 error taxonomy: 6.962 correct, 1.762 shortest-path tie-break errors, 221 truth-not-shortest, dan 55 candidate missing. Sisa bottleneck tetap tie-break semantics/context.
- Runtime: `0,50` menit lokal karena memakai persisted V3 recovered-edge cache; OCR engine dan fuzzy recovery tidak diulang.
- Source: `patrick/notebooks/source/datathon_task2_v4_shortest_path_mass_source.ipynb` (bersih, 0 output blocks).
- Executed notebook: `patrick/notebooks/runs/V4 Final Local Notebook.ipynb`; 15/15 code cells executed, 34 output blocks, tanpa traceback.
- Primary submission: `patrick/submissions/datathon_task2_v4_shortest_path_mass.csv`; audit 6.000 rows/6.000 unique states, tanpa NaN/invalid ID. Test prediction berbeda dari V3 pada `3,28%` states.
- Reusable output: `patrick/output/v4/` berisi alpha search, grouped CV, nested selection, OOF error pack, recovered edges, dan compressed target path-mass cache `datathon_task2_v4_target_path_mass.npz`. ZIP: `patrick/output/datathon_task2_v4_artifacts.zip`.
- Workspace: `.vscode/settings.json` menunjuk existing `/Users/timotiuspatrick/Documents/Patrick/Kuliah & Coding/.venv/bin/python`; tidak ada venv baru.
- Decision: V4 resmi disimpan sebagai milestone meski target akhir belum tercapai. Submit primary untuk external calibration; V5 harus membedah 1.762 tie errors dan menguji link-context semantics, bukan menambah OCR lagi.
- Next action: diagnosis error V4 berdasarkan pasangan predicted-vs-truth, lalu uji context text di sekitar blue link atau semantic target similarity hanya pada shortest-path tie set.

### 2026-07-19 - Diagnosis pasca-V4 untuk calon V5

- Status: diagnosis selesai sebagian; **belum dibekukan sebagai V5 final** karena belum ada gain nested yang mengalahkan V4.
- Learned tie classifier: LightGBM binary classifier dilatih hanya pada minimum-distance candidate set dengan query-balanced sample weights dan 23 graph/semantic/OCR features plus path mass.
- Learned result: best same-fold mencapai `77,47%`, hanya `+0,11 pp` di atas V4 `77,36%`; honest nested selection `77,27%`, sehingga lebih rendah dari V4 locked. Model banyak bergantung pada `log_global_clicks`, degree, dan semantic ranks. Decision: tidak dipakai sebagai primary dan tidak dibuat notebook V5.
- Learned reports: `reports/datathon_task2_v5_learned_tie_search.csv`, `reports/datathon_task2_v5_learned_tie_nested.csv`, `reports/datathon_task2_v5_learned_tie_importance.csv`, dan `reports/datathon_task2_v5_learned_tie_diagnosis.json`.
- Context-only OCR probe: untuk menghindari OCR seluruh halaman, ekstraksi dibatasi pada pasangan truth-vs-V4-prediction di 1.762 shortest-path tie errors. Sebanyak 3.209 unique link-context crops diproses dalam batch dan checkpoint disimpan setiap 40 crop.
- Context cache: `reports/datathon_task2_v5_context_probe_cache.csv`; 3.209/3.209 crop memiliki text. Error-state pair coverage `1.748/1.762 = 99,21%`.
- Context TF-IDF result: word similarity memilih truth `18,19%`, char similarity `49,54%`, dan combined similarity tepat `50,00%`. Artinya surrounding sentence tersedia, tetapi bag-of-words tidak memberi sinyal tambahan yang berguna. Decision: TF-IDF context ditolak.
- Context reports: `reports/datathon_task2_v5_context_probe_pairs.csv` dan `reports/datathon_task2_v5_context_probe_diagnosis.json`.
- Dependency experiment: semantic encoder `all-MiniLM-L6-v2` dipilih untuk probe karena menghasilkan 384-dimensional sentence embeddings. Existing `.venv` kini memiliki pinned `sentence-transformers==3.4.1`, `transformers==4.48.3`, `huggingface-hub==0.28.1`, dan `tokenizers==0.21.0`; tidak ada venv baru.
- Dependency caveat: import semantic encoder masih perlu dijalankan dengan TensorFlow disabled (`USE_TF=0` / `TRANSFORMERS_NO_TF=1`) karena `.venv` memiliki Keras 3. Verifikasi terakhir terhenti oleh user sebelum selesai; model MiniLM belum di-download dan embedding belum dibuat. Jangan menganggap semantic probe selesai.
- Current best: **V4 77,36% grouped OOF**, nested alpha `77,17%`, source dan executed notebook lengkap, submission siap. V1 public leaderboard tetap `0,637`; V4 belum memiliki leaderboard score.
- Next action: verifikasi text-only MiniLM import tanpa mengubah environment lagi, encode hanya context-probe + article title/category documents, lalu ukur apakah semantic similarity memilih truth secara material di atas 50%. Hanya jika menjanjikan, perluas context cache ke seluruh candidate set dan bekukan sebagai V5.

### 2026-07-19 - MiniLM dihentikan dan arah V5 dikembalikan ke competition-only methods

- Compliance decision: Patrick mengingatkan bahwa LLM/pretrained language model kemungkinan tidak diperbolehkan. MiniLM bukan generative/chat LLM, tetapi tetap external pretrained transformer encoder; eksperimen dihentikan sampai rules membuktikan penggunaannya diizinkan.
- Tidak ada MiniLM model weight yang sudah di-download dan tidak ada embedding yang dibuat. Package Python sempat dipasang ke existing `.venv`, tetapi tidak boleh dipakai dalam submission pipeline saat ini.
- Rules belum dapat diverifikasi dari public web karena halaman kompetisi tidak terindeks/terbuka. Minta screenshot atau salinan bagian rules tentang external data dan pretrained models sebelum mengaktifkan kembali metode tersebut.
- OCR evidence: raw OCR memiliki 121.460 detected blue regions; 120.268 accepted (`99,02%` accepted-region rate), rata-rata confidence `0,942`, dan mean title-match `0,992`. Candidate recall OOF setelah recovery `99,39%`.
- Important distinction: accepted-region rate hanya mengukur region yang berhasil dideteksi. Ia tidak mengukur blue links yang sama sekali terlewat oleh color-mask, dan candidate recall hanya mengukur apakah immediate truth tersedia—not whether all downstream graph edges needed for exact shortest distance are complete.
- V4 top-3 `94,43%` dan top-5 `97,41%` menunjukkan jawaban hampir selalu sudah dekat. Untuk mencapai accuracy `0,90`, fokus utama harus reranking/tie-policy dan graph correctness, bukan OCR text recognition.
- Prioritas V5 competition-only:
  1. edge ablation: bandingkan accepted-only, exact recovery, dan fuzzy recovery untuk mengukur false-edge impact pada distance/ties;
  2. exact 2D reading order memakai `box_y + box_x`, occurrence index, width/height, serta body/infobox/sidebar zone—V3 belum memakai layout lengkap sebagai deterministic adjacency policy;
  3. reverse-engineer generator policy dengan BFS/shortest-path tree under multiple adjacency orders dan path-sequence tie rules;
  4. shortest-path DAG features: path entropy, bottleneck/branch robustness, best second-hop semantics, dan consensus across graph variants;
  5. audit possible structural leakage yang sah dari `state_id`, article ID ordering, 25-state target groups, repeated current/next transitions, dan path-length regimes;
  6. pairwise error-only reranker hanya setelah fitur graph/layout baru tersedia; LightGBM pada fitur lama tidak stabil.
- Versioning decision: diagnosis ini belum disebut V5 final. V5 baru dibekukan ketika salah satu competition-only hypothesis meningkatkan grouped/nested OOF atau menghasilkan milestone diagnosis yang mengubah pipeline secara material.

### 2026-07-19 - V5 pretrained semantic pair-ranker selesai

- Status: full local CPU run selesai; V5 resmi dibekukan sebagai milestone kecil di atas V4. Belum ada leaderboard score.
- Research identification: ukuran dataset cocok persis dengan Wikispeedia. Official SNAP source berisi 4.604 articles, 119.882 links, 51.318 finished paths, dan 24.875 unfinished paths. Primary references: West & Leskovec `Human Wayfinding in Information Networks` dan Lamprecht et al. `How the structure of Wikipedia articles influences user navigation`.
- Research insight: literatur menemukan zoom-out menuju high-degree hubs pada fase awal, article structure pada fase tengah, dan content similarity pada homing-in phase. Semua hipotesis diterjemahkan menjadi diagnostic features sebelum modeling.
- MiniLM: `all-MiniLM-L6-v2` dipakai sebagai frozen 384-D article encoder. Encoding 4.604 article title+category dan 3.209 context probes berjalan cepat di CPU; model weight sekitar 88 MB dan article embedding cache disimpan sebagai float16 NPZ.
- MiniLM probe result: article cosine memilih truth hanya `40,56%` pada V4 tie errors; context cosine `50,97%`. Cosine tunggal dan context similarity tidak dipakai sebagai primary.
- Rejected phase/layout result: research-informed degree/semantic/top-position gating tidak mengalahkan V4. Best graph/layout same-fold `77,38%`, nested `77,18%`; full phase random lebih buruk.
- Wikispeedia path leakage firewall: 240 competition test targets diblacklist sebelum audit. Setelah blacklist, external path corpus hanya overlap `0,9%` dengan train `(current,target)` states dan covered majority accuracy sekitar `27%`; direct lookup tidak menjelaskan leaderboard dan tidak dipakai.
- Official graph oracle: 119.882 official unique edges dibanding 95.418 OCR-recovered edges, tetapi mengganti distance dengan official full graph menurunkan grouped OOF ke `69,09%`. Competition labels bukan shortest-path policy pada full Wikispeedia graph; official graph tidak dipakai di submission.
- Winning V5 method: PCA 48-D pada cached MiniLM vectors, kemudian LightGBM classifier mempelajari nonlinear candidate–target product, absolute difference, candidate/target coordinates, directional semantic progress, dan V4 tabular features. Training hanya pada minimum-distance candidate queries dengan balanced per-query weights.
- Blend: V5 probability diberi bobot kecil `0,20` di atas locked V4 shortest-path mass score. Shortest-path anchor tetap dominan.
- Grouped OOF: V4 `77,3556%` menjadi V5 **77,4889%**, naik `0,1333 pp` atau 12 net correct states. Top-3 `94,3556%`; top-5 `97,4111%`; candidate recall `99,3889%`.
- Honest nested selection: **77,3889%**, di atas V4 nested `77,1667%`. Gain kecil tetapi bertahan ketika configuration dipilih tanpa melihat held-out fold.
- Change audit: 130 OOF predictions berubah; 58 diperbaiki, 46 regression, 26 tetap salah; net +12.
- Runtime: `1,10` menit full local CPU. GPU tidak diperlukan karena embedding sudah cached dan model yang dilatih kecil.
- Source: `patrick/notebooks/source/datathon_task2_v5_pretrained_semantic_pair_ranker_source.ipynb`; 0 output blocks.
- Executed notebook: `patrick/notebooks/runs/V5 Final Local Notebook.ipynb`; 17/17 code cells executed, 38 output blocks, tanpa traceback.
- Primary submission: `patrick/submissions/datathon_task2_v5_semantic_pair_blend.csv`; 6.000 rows/6.000 states, tanpa NaN/invalid IDs. V5 berbeda dari V4 pada `1,7333%` test states.
- Reusable artifacts: `patrick/output/v5/` menyimpan MiniLM model, article/context embeddings, PCA+LightGBM joblib, CV, nested search, OOF error pack, diagnostics, dan submissions. ZIP `patrick/output/datathon_task2_v5_artifacts.zip` sekitar 85,6 MB.
- Compliance: V5 memakai pretrained encoder yang Patrick konfirmasi diperbolehkan. External Wikispeedia navigation GT tidak dimuat atau dipakai oleh final notebook/model/submission.
- Decision: submit V5 dan V4 sebagai external comparison karena expected delta kecil. Untuk V6, jangan mengulang graph/layout/cosine experiments yang sudah ditolak; fokus pada stronger pairwise pretrained model atau cross-encoder di Kaggle GPU, dengan grouped validation dan V4 anchor.

### 2026-07-19 - Final pre-deadline ensemble dan full-text probes

- Public leaderboard: V4 dan V5 sama-sama memperoleh `0,767`. Perubahan V5 pada 1,73% test states belum menghasilkan perbedaan public score tiga desimal.
- Ensemble sweep sebenarnya sudah menjadi bagian V5: `V4 + beta × semantic probability`. Best grouped OOF adalah beta `0,20` dan `0,30`, keduanya `77,4889%`; beta `0,10` menghasilkan `77,4778%`; beta `0,50` turun ke `77,1222%`.
- Ready variants: `submissions/datathon_task2_v5_semantic_pair_blend_beta030.csv` dan `submissions/datathon_task2_v5_semantic_pair_blend_beta010.csv`. Beta 0,30 menjadi alternative submission prioritas.
- Full Wikispeedia plaintext: 4.604 article files berhasil dipetakan tanpa missing title dan di-encode menjadi cached 384-D MiniLM embeddings pada CPU sekitar satu menit.
- Full-text pair-ranker: best same-fold `77,5111%`, hanya `+0,0222 pp` dari title+category V5; nested selection turun ke `77,20%` dari V5 `77,3889%`. Decision: tidak stabil, tidak dipilih sebagai primary.
- Insight: full article content, scalar weighting, dan shallow semantic pair interactions tidak menjelaskan gap ke leaderboard `0,9`. Missing breakthrough kemungkinan membutuhkan stronger cross-encoder/VLM reasoning atau competition-generation-specific structure, bukan ensemble bobot kecil.

### 2026-07-19 - V6 discounted reachability selesai

- Status: full local CPU run selesai dan V6 resmi dibekukan sebagai milestone baru; leaderboard score belum tersedia.
- Rejected generator hypothesis: forward BFS, reverse BFS tree, dan NetworkX bidirectional shortest-path dengan sembilan adjacency orders hanya mencapai maksimum `50,87%`; label bukan hasil satu BFS ordering sederhana.
- Rejected cross-encoder: zero-shot `cross-encoder/ms-marco-MiniLM-L-6-v2` menilai 35.274 unique candidate–target pairs. Bobot terbaik adalah `0`; alpha positif langsung menurunkan OOF. Model disimpan pada `output/v6/ms-marco-MiniLM-L-6-v2` untuk riset setelah lomba, tetapi tidak dipakai V6 final.
- Winning hypothesis: discounted random-walk reachability menghitung `e_t + gamma P e_t + gamma^2 P^2 e_t + ...` pada graph OCR-recovered, dengan transition probability dinormalisasi out-degree. Fitur mencakup semua walk pendek, bukan hanya shortest paths, sehingga membedakan kandidat yang mengarah ke hub bercabang besar.
- Locked configuration: V4 shortest-path anchor + `0,20 × V5 semantic probability - 0,06 × reachability`, dengan `gamma=0,30` dan 16 propagation steps.
- Grouped OOF: V4 `77,3556%`; V5 `77,4889%`; V6 **`77,6222%`**. V6 naik `+0,1333 pp` atau 12 net correct states dibanding V5.
- Honest nested selection: **`77,5111%`**, di atas V5 nested `77,3889%`. Held-fold selections: `(beta=0,20, alpha=-0,06)`, `(0,10,-0,02)`, dan `(0,20,-0,06)`.
- Change audit vs V5: 145 predictions berubah; 62 fixed, 50 regressed, 33 tetap salah; net +12.
- Runtime: `1,16` menit full local memakai existing `.venv`; OCR, recovery, dan MiniLM embedding tidak diulang. GPU tidak diperlukan.
- Source: `notebooks/source/datathon_task2_v6_discounted_reachability_source.ipynb`.
- Executed notebook: `notebooks/runs/V6 Final Local Notebook.ipynb`.
- Primary submission: `submissions/datathon_task2_v6_discounted_reachability.csv`; 6.000 rows/6.000 states, tanpa NaN atau invalid article ID. V6 berbeda dari V5 pada `1,75%` test states.
- Reusable output: `output/v6/`; ZIP `output/datathon_task2_v6_artifacts.zip`; reports V6 disalin ke `reports/`.
- Decision: submit V6 sebagai kandidat utama terakhir. Expected leaderboard movement kecil karena local gain hanya 0,13 pp dan public score dibulatkan tiga desimal; V5/V4 tetap fallback yang sudah memperoleh `0,767`.
