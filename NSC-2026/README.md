# NSC UB — Prediksi Kelembapan Udara (National Statistics Challenge 2026)

> 🥈 **Juara 2 dari 70 tim** — National Statistics Challenge (NSC) 2026, Universitas Brawijaya (Okt 2026). Repo asli: [patrick12354/NSC_2026_Heisenberg](https://github.com/patrick12354/NSC_2026_Heisenberg)

Penyisihan cabang Data Science, Studio Statistika FSTM Universitas Brawijaya. Memprediksi
`air_humidity` (%RH) untuk 734 stempel waktu setengah-jaman, 29 Agustus – 13 September 2023, dari
2933 baris latih dan 25 sensor eksogen yang **juga tersedia sepanjang jendela uji**. Metrik RMSE,
makin kecil makin baik.

**Skor publik terbaik: 2,82744** (`submission_nsc26_air_humidity.csv`). Titik awal tanpa rekayasa
apa pun ada di 4,755; peringkat 4 tercatat saat skor masih 2,84953.

---

## Baca dulu

| File | Isi |
|---|---|
| [`NSC26_DataScience_AirHumidity.ipynb`](NSC26_DataScience_AirHumidity.ipynb) | **Deliverable utama.** Notebook end-to-end: akuisisi, EDA, kerangka fisis, pra-pemrosesan, fitur, validasi, pemodelan, evaluasi, dan pembangunan ulang berkas submission. 74 sel, keluaran tersimpan. |
| [`guide_lomba.md`](guide_lomba.md) | Rangkuman juknis menjadi daftar tindakan, plus pemetaan tiap butir penilaian ke artefak yang sudah ada. Bobot sebenarnya: Pembahasan 54 %, Leaderboard 32 %, Notebook 8 %. |
| [`progress.md`](progress.md) | Log 48 sesi eksperimen, ±11 300 baris. Setiap percobaan dicatat termasuk yang **gagal**, lengkap dengan alasannya. Bagian yang kemudian terbantah diberi tanda dan penunjuk ke koreksinya. |
| [`final_pipeline.py`](final_pipeline.py) | Pipeline produksi, mandiri, deterministik. Hanya membaca tiga berkas resmi lomba. md5 `f7acb165175ea5fb056c7839978f9878`. |
| [`submission_nsc26_air_humidity.csv`](submission_nsc26_air_humidity.csv) | Berkas yang dikirim ke Kaggle. |
| [`model_nsc26_air_humidity.pkl`](model_nsc26_air_humidity.pkl) | Artefak model untuk diunggah ke panitia (juknis 2.e). |

Kalau hanya punya waktu sepuluh menit: baca ringkasan eksekutif di notebook, lalu tabel
"Riwayat leaderboard" di bawah.

---

## Hasil

| Submission | Perubahan | Publik | Δ |
|---|---|---:|---:|
| `v8_qblock` | dasar: 5 model, blending NNLS | 3,04904 | — |
| `v10_todblend` | bobot blend per pita waktu-hari | 3,02942 | −0,01962 |
| `v11_seed5` | + koreksi bias diurnal per pita | 3,00589 | −0,02353 |
| `final_submission` | + kemiringan dispersi **dan** fitur terpotong | 3,28564 | +0,237 |
| `v16_l2member` | anggota LightGBM L2 keenam | 3,02586 | +0,00300 |
| `v20_shrinkonly` | lantai penyusutan NNLS dilepas | 3,05372 | +0,02786 |
| **`v21_increment_v16`** | **rekonsiliasi inkremen** | **2,86595** | **−0,15991** |
| `..._phys_dsh_lags` | tiga penghalusan inkremen sekaligus | 2,93028 | +0,06433 |
| `..._noridge` | anggota `ridge` dibuang | 2,85383 | −0,01212 |
| `..._noridge_todbias` | bentuk pita menggantikan harmonik | 2,84953 | −0,00430 |
| **`..._todbias_catdb`** | **de-bias level anggota `cat`** | **2,82744** | **−0,02209** |
| `..._catdb_cal0.25` | kemiringan dispersi, kekuatan seperempat | 2,83299 | +0,00555 |

Dua submission terakhir dipakai sebagai **alat ukur**, bukan sekadar tebakan — lihat bagian
berikutnya.

---

## Tiga hal yang menentukan hasil ini

**1. Rekonsiliasi inkremen bernilai sepuluh kali perubahan lain mana pun (−0,160).**
Seluruh pipeline lain menilai 734 baris uji satu per satu: fiturnya per-baris, anggotanya
per-baris, blendnya per-baris. Rekonsiliasi adalah satu-satunya komponen yang memperlakukan jendela
uji sebagai **deret waktu**. Model kedua memprediksi *perubahan* RH pada 30 menit dan 2 jam, lalu
satu penyelesaian kuadrat-terkecil jarang mengikat 734 baris menjadi satu sistem linear:

```
min_z  ||z − p||²  +  4·||D₁z − d₁||²  +  ||D₄z − d₄||²
```

Galat model level berautokorelasi lag-satu 0,9356, jadi hampir seluruhnya saling meniadakan pada
selisih dua titik berdekatan — di situlah informasi baru masuk.

**2. Satu anggota blend membawa bias level −2,9 %RH yang tak bisa dijangkau apa pun (−0,022).**
Dalam 46 sesi, galat bertanda rata-rata tiap anggota tidak pernah dicetak. Ternyata `cat`
(CatBoost, `Huber:delta=4`) meleset −2,89 %RH ke depan sementara lima anggota lain berada dalam
±0,8, dan bias **dalam-sampel**-nya −0,006 — jadi ini sifat maju, bukan artefak pemasangan. Pada
target ber-simpangan-baku 18 %RH, gradien huber terpotong di atas 4 membuat anggota itu mengejar
median bersyarat dan mendarat rendah begitu diminta meramal melewati jendela latihnya. Bobot NNLS
tak-negatif dan ternormalisasi, jadi blend tidak punya intersep; `tod_bias` dan `harm_bias`
keduanya memasang intersep lalu sengaja membuangnya. Tidak ada satu pun komponen yang bisa
menyerapnya.

**3. Skor yang kembali dipakai untuk mengukur, lalu menutup dua sumbu.**
Karena perubahan pada butir 2 nyaris murni pergeseran level, `ΔMSE = 2·mean(d·e) + mean(d²)` bisa
dibalik untuk memperoleh galat level yang sesungguhnya:

| besaran | nilai |
|---|---:|
| mean(d) | +0,20244 |
| MSE 8,11982 → 7,99442 | −0,12540 |
| **⇒ galat level pada slice publik** | **−0,4145 %RH** |

Blok validasi maju menaksirnya −0,98: **tandanya benar, ukurannya berlebih 2,4×**. Sisa sumbu level
tinggal −0,008, jadi **tertutup**. Submission berikutnya melakukan hal yang sama untuk momen kedua
dan memberi `s* = 1,00502` — model sudah terkalibrasi dalam dispersi, sisa −0,0016, **juga
tertutup**. Kedua koreksi post-hoc yang secara teori paling besar ternyata habis; sisanya ada pada
offset per-hari, yaitu 36 % galat dengan kemiringan kompresi 1,106 yang **tidak dapat ditaksir**
dari 13–23 hari riwayat.

---

## Setup

```bash
python -m venv .venv
.venv/Scripts/pip install pandas numpy scipy scikit-learn lightgbm catboost matplotlib joblib
```

Versi yang dipakai: pandas 2.2.3, numpy 2.4.6, scipy 1.17.1, scikit-learn 1.9.0, LightGBM 4.7.0,
CatBoost 1.2.10. `.venv/` tidak ikut di-commit.

## Reproduksi

Berkas yang dikirim dibangun ulang persis oleh:

```bash
python final_pipeline.py --selftest --tod-blend --tod-bias --l2-member --increment --drop-ridge --cat-debias
```

`--selftest` membuktikan tidak ada fitur yang bergantung pada target: seluruh matriks fitur dibangun
ulang dengan kolom target dihapus dan dibandingkan bit per bit. Setiap model membawa seed tetap,
jadi menjalankan ulang menghasilkan berkas yang sama. Waktu jalan ±25 menit pada CPU.

Notebook melakukan hal yang setara dari data mentah, dengan penjelasan dan visualisasi di setiap
tahap, lalu memverifikasi hasilnya terhadap berkas yang dikirim.

Uji: **584 tes, semuanya lulus.**

```bash
python -m unittest discover -s tests -p "test_*.py"
```

---

## Struktur

```
NSC UB/
├── NSC26_DataScience_AirHumidity.ipynb   deliverable notebook
├── final_pipeline.py                     pipeline produksi
├── submission_nsc26_air_humidity.csv     berkas terkirim
├── model_nsc26_air_humidity.pkl          artefak model
├── guide_lomba.md                        juknis → daftar tindakan
├── progress.md                           log 48 sesi
├── Dataset/                              train.csv, test.csv, sample_submission.csv
├── docs/                                 rencana dan reevaluasi per sesi
├── src/                                  106 skrip analisis (an01…an106, exp*, v21_*)
├── tests/                                41 berkas, 584 tes
└── outputs/                              log, metrik, ledger, submissions
```

`src/` bersifat eksploratif dan tidak dipanggil oleh produksi. Yang menghasilkan berkas terkirim
hanya `final_pipeline.py`. Instrumen validasi yang menopang keputusan sesi terakhir:
`an100`–`an106` (de-bias anggota, gate stres OOD, dekomposisi galat, proksi level bebas-target,
sapuan hyperparameter `hbt`).

---

## Metode, singkat

**Pra-pemrosesan.** Penapis Hampel terpusat pada sensor eksogen, lalu interpolasi waktu. Audit
lonjakan: sisa regresi kuadratik leave-one-out pada `air_temperature` punya rasio simpangan-baku
terhadap simpangan-baku kokoh **5,52** dengan 39 pencilan; pada `pressure` **6,76**. Pada target
rasionya **1,20** — targetnya bersih, jadi tidak ada lantai derau label untuk disalahkan.
Pembersihan menghapus 57 dari 62 lonjakan suhu di atas 2,5 °C dan menyisakan nol di jendela uji.

**Fitur.** 194 kolom. Jangkar fisisnya: RH = 100·e/es(T), sehingga soalnya sebenarnya menaksir
tekanan uap `e`. Blok `tmin` memakai minimum harian sebagai proksi titik embun bebas-parameter
(udara lembap mendingin semalam sampai mencapai titik embunnya lalu berhenti di situ), blok
kuantil memisahkan malam cerah dari malam berawan, dan blok kecenderungan menangkap adveksi
sinoptik. Blok agronomi direkayasa balik: kolom itu konstan pada hari 22.00–22.00 dengan jitter
0,06–0,12 °C, `daily_mean_temperature = (Tmax+Tmin)/2` berlaku sampai simpangan-baku 0,023 pada
61 hari, dan dihitung **sebelum** lonjakan disuntikkan.

**Model.** Enam anggota — LightGBM huber, CatBoost huber, ElasticNet, ridge dalam ruang tekanan
uap, LightGBM L2 — digabung dengan NNLS yang disusutkan, bobot terpisah per pita waktu-hari,
koreksi bias diurnal per pita, de-bias level anggota, lalu rekonsiliasi inkremen.

**Validasi.** Origin bergulir 15 hari ke depan, ditambah enam blok maju yang membangun ulang
seluruh tumpukan dari titik asalnya sendiri. Gate stres OOD terpisah untuk perubahan yang berisiko
tidak menyeberang regime. Setiap kandidat diuji dengan **kontrol arah** (perubahan yang sama dengan
tanda dibalik) dan **kontrol nol**, karena tanpa itu selisih kecil tidak bisa dibedakan dari derau.

---

## Catatan integritas

**Berkas terkirim dan berkas produksi identik secara numerik.** `submission_nsc26_air_humidity.csv`
dan `outputs/submissions/v21_increment_v16_noridge_todbias_catdb.csv` punya md5 berbeda
(`a4658c49…` vs `70666a36…`) tetapi selisih nilai maksimumnya **tepat 0**. Bedanya satu baris
saja — `24.807549586807102` versus `24.8075495868071` — dua representasi teks untuk *double* yang
sama. Dicatat di sini supaya tidak terbaca sebagai ketidaksesuaian.

**Cache prediksi tidak ikut di-commit.** 113 berkas `.pkl`/`.npy` di bawah `outputs/` (95 MB)
adalah cache yang bisa dibangun ulang oleh skrip di `src/`. Log, metrik, ledger, dan seluruh
submission tetap ada. `model_nsc26_air_humidity.pkl` di akar folder adalah deliverable dan ikut.

**Tanpa data luar.** Pipeline hanya membaca `Dataset/train.csv`, `Dataset/test.csv`, dan
`Dataset/sample_submission.csv`. Tidak ada pretrained model, tidak ada probing leaderboard untuk
membangun fitur.

**Satu pilihan transduktif, disengaja.** Jendela bergulir terpusat pada baris uji merata-ratakan
pembacaan sensor dari baris uji tetangga. Itu data fitur masa depan, bukan target masa depan, dan
memang itu yang diminta soal — 25 kolom eksogen disediakan penuh di `test.csv`.
