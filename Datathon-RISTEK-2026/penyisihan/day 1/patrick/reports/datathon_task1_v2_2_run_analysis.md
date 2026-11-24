# Datathon Task 1 — V2.2 T4 Run Analysis

## Outcome

V2.2 berhasil dijalankan penuh di Kaggle T4 dalam sekitar 8 menit 41 detik. Final local temporal-validation MSE adalah **27.4269**, membaik dari V1 **27.8935** sebesar **0.4666 MSE (1.67%)**. Improvement ini nyata, tetapi belum merupakan breakthrough besar.

## Validation results

| Candidate | Mean MSE |
|---|---:|
| AR | 29.9828 |
| PCA residual | 29.4135 |
| temporal only | 29.1315 |
| directed graph | 28.9507 |
| graph + text gate | 28.5643 |
| graph + text + zero auxiliary | 28.5580 |
| 3-seed GNN average | 27.6004 |
| final blend | **27.4269** |

Final blend per horizon: h5 **24.4498**, h10 **27.5477**, h15 **30.2832**.

## What worked

- Graph membantu dibanding temporal-only.
- Text gate memberi tambahan signal yang lebih besar daripada perubahan graph direction saja.
- Averaging tiga seed memberi gain cukup jelas dan menstabilkan model.
- PCA residual tetap complementary, khususnya pada horizon lebih jauh.

## What did not produce a breakthrough

- Zero auxiliary hanya berbeda sekitar 0.006 MSE dari text-gated model.
- V2 dan V1 sangat berkorelasi (0.9988–0.9993). V2 terutama melakukan koreksi kecil terhadap pola prediksi yang sama.
- Per-road ridge dengan graph summaries: 29.5543.
- PCA nearest-neighbor analog: 38.5907.
- Global LightGBM residual: 30.0566.
- Hard AR expert per regime: 30.1766 vs shared AR 29.9688.

## Reverse-engineering insight

Global history statistics memisahkan train m1 dan m2 secara hampir sempurna. Test terdiri dari 372 sample m1-like dan 168 m2-like (68.89%/31.11%), nyaris sama dengan proporsi panjang dua continuous train block. Karena validation lama mengambil jumlah window sama dari kedua block, mean validation 50/50 kemungkinan tidak persis merepresentasikan test.

Implikasinya bukan melatih dua model terpisah—hard expert justru memburuk—melainkan memasukkan regime/global city state sebagai soft conditioning dan mengevaluasi model dengan dua score:

1. balanced score 50/50 untuk konsistensi historis;
2. inferred test-composition score 68.89%/31.11% untuk pemilihan kandidat.

## V3 direction

- Pertahankan V2 graph + text sebagai reference ablation.
- Tambahkan global trajectory encoder dan FiLM modulation.
- Uji EMA untuk mengurangi noise antar-epoch/seed.
- Uji soft mixture-of-experts yang dikondisikan probabilitas regime, bukan hard split.
- Gunakan natural train proportions, leakage-safe temporal cutoff, textual metric tables, visual diagnostics, dan `tqdm` pada loop lambat.
