---
title: Datathon Task 2 - Penjelasan Lomba
date: 2026-07-19
tags:
  - datathon
  - competition
  - wikipedia
  - next-click-prediction
status: active
---

# Datathon Task 2 - Wikipedia Next Click Prediction

## Overview

Membaca Wikipedia membentuk sebuah urutan navigasi. Seorang pengguna memulai dari satu artikel, mengeklik link ke artikel lain, lalu terus bergerak menuju informasi yang dicari.

Task ini mengubah proses tersebut menjadi **single-step prediction**. Untuk setiap state, diketahui:

- artikel yang sedang dibuka (`current_article_id`);
- artikel tujuan (`target_article_id`);
- seluruh link yang terlihat pada screenshot artikel saat ini.

Tugas peserta adalah memprediksi **artikel mana yang diklik berikutnya** dari link-link yang tersedia pada halaman saat ini.

Secara ringkas:

```text
(current article, target article, visible links) -> next clicked article
```

Kompetisi yang dibagikan memiliki durasi sangat singkat. Teks awal menampilkan kompetisi baru berjalan sekitar lima menit dan akan ditutup sekitar lima jam kemudian. Informasi ini merupakan snapshot saat deskripsi diberikan.

## Evaluation metric

Metric kompetisi adalah **accuracy dengan exact match**.

$$
\mathrm{Accuracy} = \frac{1}{N}\sum_{i=1}^{N}\mathbf{1}(\hat{y}_i=y_i)
$$

Keterangan:

- $\hat{y}_i$ adalah `predicted_next_article_id`;
- $y_i$ adalah artikel yang benar-benar diklik berikutnya;
- hasil hanya dianggap benar jika article ID sama persis;
- tidak ada partial credit untuk prediksi yang secara topik dekat tetapi ID-nya salah.

Implikasinya, output akhir harus memilih tepat satu artikel untuk setiap state. Model ranking top-k tetap berguna saat development, tetapi submission hanya memakai kandidat peringkat pertama.

## Submission format

Submission harus memiliki dua kolom:

```csv
state_id,predicted_next_article_id
0,1842
6,77
8,3590
```

Ketentuan penting:

- satu row untuk setiap state pada `states_test.csv`;
- `state_id` harus dipertahankan persis seperti test;
- `predicted_next_article_id` harus berupa ID artikel yang valid;
- urutan paling aman adalah mengikuti `sample_submission.csv`;
- tidak boleh ada state duplikat, prediction kosong, atau ID di luar `articles.csv`.

Nilai awal pada `sample_submission.csv` sama dengan `current_article_id`. Nilai tersebut hanya placeholder dan harus diganti. Pada train aktual, tidak ada label `next_article_id` yang sama dengan `current_article_id`.

## Struktur dataset

```text
dataset-task2/
├── screenshots/
│   ├── 0.png
│   ├── 1.png
│   └── ...
├── articles.csv
├── categories.csv
├── states_train.csv
├── states_test.csv
└── sample_submission.csv
```

### `screenshots/<article_id>.png`

- Satu screenshot untuk setiap artikel.
- Screenshot menunjukkan halaman dari sudut pandang pembaca.
- Header halaman mengidentifikasi sumbernya sebagai **2007 Wikipedia Schools snapshot**, bukan Wikipedia live saat ini.
- Link dari artikel ke artikel digambar dengan warna biru.
- Nama file adalah `article_id` dari `articles.csv`.
- Screenshot mempunyai lebar 900 piksel, sedangkan tingginya dapat sangat bervariasi sesuai panjang artikel.

Screenshot adalah sumber utama untuk mengetahui kandidat link yang benar-benar tersedia dari current article. Dataset tidak menyediakan edge-list hyperlink secara terpisah.

Karena snapshot bersifat historis, title, isi, dan hyperlink Wikipedia live dapat berbeda. Data eksternal hanya aman dipakai setelah dicocokkan dengan screenshot dan daftar artikel kompetisi.

### `articles.csv`

| Kolom | Arti |
|---|---|
| `article_id` | ID integer artikel. |
| `title` | Judul artikel Wikipedia. |

Dataset aktual memiliki 4.604 artikel dengan ID berurutan `0` sampai `4603`. Seluruh title unik dan seluruh artikel memiliki screenshot.

### `categories.csv`

| Kolom | Arti |
|---|---|
| `article_id` | ID artikel. |
| `category` | Kategori topik artikel. |

Satu artikel dapat mempunyai lebih dari satu kategori. Dataset aktual memiliki:

- 5.204 row kategori;
- 129 kategori unik;
- 4.598 artikel yang memiliki minimal satu kategori;
- 598 artikel multi-category;
- maksimal tiga kategori pada satu artikel;
- enam artikel tanpa kategori: `34`, `1625`, `1949`, `2761`, `2960`, dan `4478`.

### `states_train.csv`

| Kolom | Arti |
|---|---|
| `state_id` | ID unik state. |
| `current_article_id` | Artikel yang sedang dibuka. |
| `target_article_id` | Artikel tujuan navigator. |
| `next_article_id` | Label: artikel yang diklik berikutnya. |

Dataset aktual memiliki 9.000 labeled states.

### `states_test.csv`

| Kolom | Arti |
|---|---|
| `state_id` | ID unik state. |
| `current_article_id` | Artikel yang sedang dibuka. |
| `target_article_id` | Artikel tujuan navigator. |

Dataset aktual memiliki 6.000 states tanpa label.

### `sample_submission.csv`

File ini berisi 6.000 row dengan kolom:

```text
state_id,predicted_next_article_id
```

Daftar dan urutan `state_id` sama persis dengan `states_test.csv`.

## Audit dataset aktual

| Pemeriksaan | Hasil |
|---|---:|
| Artikel | 4.604 |
| Screenshot PNG | 4.604 |
| Screenshot hilang/tambahan | 0 / 0 |
| Train states | 9.000 |
| Test states | 6.000 |
| Total state unik | 15.000 |
| Duplicate state ID | 0 |
| Foreign key artikel invalid | 0 |
| Target unik pada train | 360 |
| Target unik pada test | 240 |
| Target train-test overlap | 0 |
| State per target | 25 |

`state_id` train dan test tidak masing-masing membentuk rentang kontinu, tetapi union keduanya tepat mencakup `0` sampai `14999`. Karena itu jangan mengasumsikan nomor row sama dengan `state_id`.

## Temuan split yang sangat penting

Dataset berisi tepat 600 target article dan masing-masing target mempunyai 25 state:

- 360 target hanya muncul di train: `360 x 25 = 9.000` states;
- 240 target hanya muncul di test: `240 x 25 = 6.000` states;
- tidak ada target article yang muncul di kedua split.

Artinya test menguji kemampuan **generalisasi ke target baru**, bukan menghafal pola click untuk target yang sama. Validation lokal harus meniru kondisi ini dengan membagi data berdasarkan `target_article_id`, misalnya `GroupKFold`. Random row split berisiko terlalu optimistis karena state dengan target yang sama akan masuk ke train dan validation.

## Intuisi modeling

Sebuah prediksi yang baik membutuhkan dua komponen.

### 1. Candidate extraction

Model harus mengetahui artikel apa saja yang benar-benar dapat diklik dari current page. Kandidat dapat diekstrak dari screenshot melalui kombinasi:

- deteksi warna biru untuk menemukan area link;
- OCR pada area tersebut;
- normalisasi dan fuzzy matching hasil OCR terhadap title di `articles.csv`;
- cache hasil ekstraksi agar setiap screenshot hanya diproses sekali.

### 2. Goal-directed ranking

Setelah kandidat tersedia, model memilih link yang paling menjanjikan untuk mencapai target. Sinyal yang dapat dipakai antara lain:

- semantic similarity judul kandidat dengan judul target;
- kesamaan atau kedekatan kategori;
- kemiripan teks di sekitar link dengan target;
- prior click dari train untuk current page;
- graph distance atau learned path score jika hyperlink graph berhasil direkonstruksi;
- posisi link pada halaman sebagai behavioural prior.

Karena metric adalah exact accuracy, kandidat yang tidak terdapat pada halaman current harus dicegah melalui candidate masking.

## Deliverable akhir

Submission valid harus:

- berisi tepat 6.000 row;
- mempunyai kolom `state_id` dan `predicted_next_article_id`;
- mempertahankan seluruh test `state_id` dan urutannya;
- memiliki satu integer prediction per state;
- tidak mengandung NaN atau duplicate state;
- memakai article ID valid;
- idealnya memastikan prediction merupakan link yang tersedia pada screenshot current article.
