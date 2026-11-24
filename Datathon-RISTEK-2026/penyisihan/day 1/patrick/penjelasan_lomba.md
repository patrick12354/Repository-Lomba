---
title: Datathon Task 1 - Penjelasan Lomba
date: 2026-07-18
tags:
  - datathon
  - competition
  - traffic-forecasting
status: active
---

# Datathon Task 1 - City Network Traffic Forecasting

## Overview

Traffic tidak bergerak secara acak. Pergerakannya merespons:

- struktur jaringan jalan;
- waktu dalam sehari;
- accident;
- road closure;
- weather;
- gatherings;
- event lain yang dilaporkan melalui aliran teks.

Peserta diberi satu jam history speed terbaru pada 1.260 road segment yang saling terhubung, serta live event-text feed yang menjelaskan kondisi lapangan. Tugasnya adalah memprediksi kecepatan traffic 20, 40, dan 60 menit ke depan.

Pada saat deskripsi awal dibagikan, kompetisi ditampilkan baru mulai sekitar lima menit sebelumnya dan akan ditutup sekitar lima jam kemudian. Informasi waktu ini bersifat snapshot saat itu, bukan jadwal permanen.

## Input yang diberikan

Setiap sample memiliki tiga sumber sinyal.

### 1. Speed history

- Window berisi 15 timestep berturut-turut.
- Window mewakili satu jam history.
- Setiap timestep memiliki speed untuk seluruh 1.260 road segment.
- Speed menggunakan satuan km/h.
- Karena 15 timestep = 60 menit, satu timestep = 4 menit.

Secara konseptual, shape satu history sample adalah:

```text
(15 timestep, 1260 roads)
```

### 2. Event text

Event text adalah natural-language description tentang kondisi yang sedang terjadi di network. Informasi dapat mencakup:

- traffic accident;
- construction;
- road closure;
- broken-down vehicle;
- traffic control;
- prohibited turns;
- announcements;
- event lain yang relevan terhadap traffic.

Teks ini menyerupai informasi yang dibaca dispatcher manusia sebelum memperkirakan bagaimana traffic akan berubah.

### 3. Road network

- Adjacency matrix berukuran `1260 x 1260`.
- Matrix menjelaskan hubungan antar-road segment.
- Geometry dan metadata tersedia untuk setiap segment.
- Metadata mencakup coordinates, length, road/link identifiers, road class, formway, dan road name.

## Target prediksi

Untuk setiap test sample, peserta harus memprediksi speed seluruh 1.260 road pada tiga horizon:

| Horizon ID | Timestep ke depan | Waktu ke depan |
|---|---:|---:|
| h5 | 5 | 20 menit |
| h10 | 10 | 40 menit |
| h15 | 15 | 60 menit |

Jika terdapat 540 test sample, jumlah prediction yang harus dibuat adalah:

$$
540 \times 3 \times 1260 = 2{,}041{,}200
$$

## Evaluation metric

Submission dinilai menggunakan Mean Squared Error (MSE) antara predicted speed dan held-out ground truth. MSE dirata-ratakan atas seluruh sample, ketiga horizon, dan seluruh road.

$$
\mathrm{MSE} = \frac{1}{N}\sum_{i=1}^{N}(\hat{y}_i-y_i)^2
$$

Keterangan:

- $\hat{y}_i$ adalah predicted speed;
- $y_i$ adalah true speed;
- $N$ adalah total prediction yang dinilai: samples x horizons x roads.

Implikasi metric:

- Error besar dihukum secara kuadrat.
- Prediksi ekstrem yang salah sangat merugikan.
- Model yang stabil sering lebih aman daripada model dengan extrapolation agresif.
- Semua horizon dan road ikut dinilai.

## Submission format

Submission harus memiliki dua kolom:

```csv
id,speed
test_00000_h5_r0,44.0
test_00000_h5_r1,73.0
```

ID menggunakan format:

```text
test_{sample}_h{horizon}_r{road}
```

Dengan ketentuan:

- `sample`: test sample, misalnya `00000` sampai `00539` pada dataset aktual;
- `horizon`: salah satu dari `5`, `10`, atau `15`;
- `road`: indeks `0` sampai `1259`.

Contoh interpretasi:

```text
test_00012_h10_r347
```

berarti predicted speed untuk:

- test sample 12;
- 40 menit ke depan;
- road segment 347.

Urutan ID dari `sample_submission.csv` harus dipertahankan. Pada dataset aktual, ordering-nya adalah:

```text
sample -> horizon -> road
```

Artinya untuk satu sample, seluruh road h5 muncul dahulu, kemudian seluruh road h10, lalu seluruh road h15.

## Dataset directory

```text
dataset-task1/
├── train/
│   ├── train_speed_m1_*.npy
│   ├── train_speed_m2_*.npy
│   ├── train_text_m1_*.json
│   └── train_text_m2_*.json
├── test/
│   ├── test_X_hist.npy
│   └── test_texts.json
├── static/
│   ├── matrix.npy
│   ├── Roads1260.json
│   └── active_mask.npy
└── sample_submission.csv
```

Path input ketika notebook dijalankan di Kaggle:

```text
/kaggle/input/competitions/datathon-task-1/dataset-task1
```

## Training data

Training speed diberikan sebagai continuous speed series, bukan fixed independent windows.

| File | Deskripsi |
|---|---|
| `train_speed_m1_*.npy` | Continuous speed series block 1. Rows adalah timestep dan columns adalah 1.260 road. |
| `train_speed_m2_*.npy` | Continuous speed series block 2 dengan road ordering yang sama. |
| `train_text_m1_*.json` | Event text yang aligned dengan setiap timestep block 1. |
| `train_text_m2_*.json` | Event text yang aligned dengan setiap timestep block 2. |

File aktual:

| File | Shape/entries |
|---|---:|
| `train_speed_m1_1_11160.npy` | `(11160, 1260)` |
| `train_speed_m2_1_5039.npy` | `(5039, 1260)` |
| `train_text_m1_1_11160.json` | 11.160 entries |
| `train_text_m2_1_5039.json` | 5.039 entries |

Untuk membentuk training sample yang history-nya berakhir pada timestep $t$:

- input history: rows $t-14$ sampai $t$;
- target h5: row $t+5$;
- target h10: row $t+10$;
- target h15: row $t+15$.

## Test data

| File | Deskripsi |
|---|---|
| `test_X_hist.npy` | Fixed history windows, satu per test sample, seluruh road. |
| `test_texts.json` | Satu event-text entry per test sample. |

Dataset aktual:

```text
test_X_hist.npy shape = (540, 15, 1260)
test_texts.json entries = 540
```

Berbeda dari train, test tidak diberikan sebagai continuous series dan tidak menyediakan future target.

## Static data

### `matrix.npy`

- Shape `(1260, 1260)`.
- Berisi adjacency antara road segment.
- Dataset aktual menggunakan nilai `0` dan `1`.
- Matrix tidak simetris, sehingga network bersifat directed atau orientation-nya penting.

### `Roads1260.json`

- Memiliki 1.260 entries, satu per road index.
- Setiap entry dapat berisi satu atau lebih geometry/link records.
- Field yang ditemukan mencakup:
  - `coordList`;
  - `formway`;
  - `length`;
  - `linkId`;
  - `roadName`;
  - `roadclass`.

### `active_mask.npy`

- Boolean mask yang menghubungkan underlying spatial grid dengan 1.260 active segments.
- Shape aktual `(1296,)`.

## `sample_submission.csv`

- Menyediakan exact ID list yang harus diprediksi.
- Kolom `speed` awalnya diisi `0.0`.
- Jangan membuat ulang ID order dari asumsi jika file ini tersedia.
- Cara paling aman adalah copy file tersebut lalu mengganti kolom `speed` dengan prediction yang sudah di-flatten dalam order yang benar.

## Hal penting untuk modeling

### Continuous train membutuhkan temporal split

Random split tidak valid karena adjacent windows memiliki 14 dari 15 timestep yang sama. Validation sebaiknya mengambil contiguous tail atau rolling folds.

### Multi-horizon prediction sebaiknya direct

Model dapat memprediksi h5, h10, dan h15 secara langsung. Recursive one-step prediction berisiko mengakumulasi error.

### Graph dapat membawa spatial signal

Congestion pada satu road dapat menyebar ke road yang terhubung. Karena adjacency sparse, graph message passing dapat dilakukan dengan edge list.

### Text adalah exogenous context

History speed mungkin belum mencerminkan event yang baru terjadi. Event text dapat memberikan early warning tentang accident, closure, atau construction.

### Distribution shift perlu diperhatikan

Train block m1, m2, dan test mempunyai mean, variance, serta zero rate yang berbeda. Model selection sebaiknya tidak hanya mengandalkan random validation pada satu distribution.

## Deliverable akhir

File submission yang valid harus:

- bernama bebas sesuai platform, misalnya `submission.csv`;
- memiliki kolom `id` dan `speed`;
- mempertahankan seluruh ID dan urutannya;
- memiliki satu numeric speed untuk setiap ID;
- tidak memiliki NaN;
- memiliki tepat satu prediction untuk setiap sample-horizon-road combination.

