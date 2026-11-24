# Datathon Task 1 — V3 T4 Run Analysis

## Verdict

V3 berhasil penuh dan menghasilkan improvement yang material. Final balanced temporal-validation MSE adalah **26.2185**, dibanding V2 **27.4269**: turun **1.2084 MSE atau 4.41%**. Submission valid dan aman dikirim ke Kaggle.

Angka 26.2185 adalah perhitungan MSE yang benar pada holdout lokal balanced 50/50. Karena inferred test composition adalah 68.89% m1-like dan 31.11% m2-like, estimasi yang lebih test-like adalah **27.1327**. Keduanya bukan leaderboard score.

## Results

| Model | h5 | h10 | h15 | Balanced mean | Test-weighted mean |
|---|---:|---:|---:|---:|---:|
| AR | 26.4471 | 30.0473 | 33.4565 | 29.9836 | — |
| PCA | 26.2245 | 29.5089 | 32.5136 | 29.4156 | — |
| V2 reference, single seed | 24.9893 | 28.3706 | 31.2338 | 28.1979 | 28.8259 |
| Global FiLM, search seed | 24.1826 | 26.9262 | 29.4531 | 26.8540 | 27.7813 |
| Global FiLM + EMA | 23.9055 | 26.9523 | 30.0716 | 26.9765 | 28.0034 |
| Global FiLM + EMA + soft MoE | 23.8953 | 26.9129 | 30.1136 | 26.9739 | 28.0609 |
| Global FiLM, 3-seed average | 23.6515 | 26.3660 | 28.9547 | 26.3241 | 27.3262 |
| Final PCA/GNN blend | **23.6354** | **26.2748** | **28.7454** | **26.2185** | **27.1327** |

## Honest-evaluation audit

- Target formula sesuai metric resmi: mean squared error atas sample, road, dan tiga horizon.
- Temporal validation berada setelah train; random-window split tidak digunakan.
- Train target tidak menyentuh future validation targets.
- Test target tidak pernah tersedia atau digunakan.
- Test history hanya dipakai secara unsupervised untuk mengestimasi proporsi regime dan membuat prediksi, yang normal untuk competition inference.
- Submission memiliki 2.041.200 unique IDs, urutan ID identik dengan sample submission, tanpa NaN, range 0–99.51 km/h.

Sumber optimism yang perlu dicatat:

1. architecture, early stopping, seed assessment, dan ensemble weights dipilih/dilaporkan pada holdout yang sama;
2. TF-IDF/SVD fit pada seluruh train text termasuk validation text, walaupun tidak memakai target;
3. validation windows sangat overlap sehingga score stabil tetapi bukan independent samples;
4. test-weighted score mengasumsikan conditional error test sama dengan m1/m2 validation.

Ini bukan kecurangan, tetapi berarti 26.2185 bukan unbiased promise untuk leaderboard. Rolling out-of-fold validation diperlukan untuk konfirmasi yang lebih kuat.

Minor presentation issue: plot jumlah event clause memakai delimiter `" | "`, sedangkan dokumen sebenarnya dipisahkan oleh titik. Karena itu median clause pada plot tercetak 1. Ini tidak memengaruhi TF-IDF, training, validation, atau submission; hanya visualisasi text-length yang perlu diperbaiki pada notebook berikutnya.

## Model insight

- Global FiLM adalah breakthrough V3: 26.8540 vs V2 reference 28.1979 pada search yang sama.
- EMA tidak membantu overall; ia sedikit membantu h5 tetapi merusak h15.
- Soft MoE juga tidak membantu. Regime paling efektif sebagai conditioning, bukan pemisahan expert.
- Seed averaging memberi gain besar: individual seed mean 26.72–26.89 menjadi 26.3241.
- PCA blend memberi gain kecil tetapi konsisten, terutama h15; bobot PCA naik 0.089 → 0.185 → 0.259.
- Improvement terbesar muncul pada horizon jauh, menunjukkan global context membantu city-wide evolution.

## Submission behavior

V3 lebih berani daripada V2:

- mean absolute V3–V2 adalah 0.760/0.918/1.006 km/h;
- correlation masih tinggi 0.9977/0.9962/0.9953;
- horizon separation naik dari 0.338/0.241 menjadi 0.465/0.319 km/h;
- koreksi terhadap mean-last-3 naik menjadi 1.96/2.26/2.43 km/h.

Prediksi tetap konservatif, tetapi tidak lagi hampir identik dengan V2.

## Recommended next work

1. Submit V3 sekarang dan simpan leaderboard result.
2. Sebelum V4, buat 3-fold rolling temporal validation untuk mengukur optimism.
3. Kandidat V4 utama: clause-level event encoder dengan road-conditioned attention; current TF-IDF memadatkan seluruh dokumen dan kehilangan struktur event/location.
4. Kandidat kedua: infer cyclical time-of-day dari global history, kemudian masukkan soft phase embedding ke FiLM.
5. Kandidat ketiga: compact diffusion temporal graph network/Graph WaveNet dengan adaptive adjacency, diuji melawan Global FiLM pada rolling folds.
6. Jangan prioritaskan EMA, hard regime experts, zero auxiliary yang lebih berat, KNN analog, LightGBM residual, atau per-road ridge karena bukti saat ini negatif.
