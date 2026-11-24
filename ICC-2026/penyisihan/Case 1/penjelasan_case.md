# Case 1 — Prediksi Magnitudo Gempa dari Waveform Stasiun Tunggal

Dokumen ini merangkum pemahaman soal, hasil analisis data aktual (bukan asumsi), dan
rekomendasi strategi pemodelan. Semua angka di bawah dihitung dari data di
`seismic-dataset/` menggunakan Python 3.11 lokal.

---

## 1. Ringkasan Soal

| Aspek | Detail |
|---|---|
| Tipe task | Supervised regression (target kontinu) |
| Target | `magnitude` — moment magnitude final dari gempa |
| Input | Waveform 3 komponen `(1000, 3)` @ 200 Hz = 5 detik (P-wave di detik ke-1) + metadata tabular |
| Metrik | **EB-TWMAE** (Event-Balanced Tail-Weighted MAE), lebih kecil lebih baik |
| Deadline | 7 hari tersisa (per 2026-08-20) |

Intinya: ini masalah **Earthquake Early Warning (EEW)**. Hanya 4 detik sinyal setelah
P-wave yang tersedia — jauh sebelum gelombang S dan puncak guncangan tiba. Ini yang
membuat soal sulit: informasi tentang seberapa besar gempa akhirnya belum sepenuhnya
"terekam" dalam jendela waktu tersebut.

### Metrik EB-TWMAE — ini yang menentukan strategi

```
1. Untuk tiap gempa e:   MAE_e = rata-rata |y - y_hat| dari semua record stasiun gempa itu
2. Skor akhir:           SUM(w_e * MAE_e) / SUM(w_e)
```

Bobot `w_e` berdasar magnitudo sebenarnya:

| Range magnitudo | Bobot |
|---|---|
| M < 5.5 | 1.0 |
| 5.5 <= M < 6.0 | 1.5 |
| 6.0 <= M < 6.5 | 2.0 |
| M >= 6.5 | 2.5 |

Dua konsekuensi penting yang **sering dilewatkan**:

1. **Event-balanced** — gempa dengan 400 record stasiun dan gempa dengan 1 record
   punya bobot yang sama di skor akhir. Optimasi MAE per-record itu salah target.
2. **Tail-weighted** — gempa besar dibobot 2.5x, padahal jumlahnya cuma ~1% dari data.
   Model yang "aman" (prediksi mendekati rata-rata) akan dihukum berat di sini.

---

## 2. Inventaris Data

```
seismic-dataset/
├── train/train_waveforms.npy    126 MB   float32 (10505, 1000, 3)
├── train/train_meta.csv         10.505 baris
├── train/train_labels.csv       10.505 baris
├── test/test_waveforms.npy      27.6 MB  float32 (2300, 1000, 3)
├── test/test_meta.csv           2.300 baris
└── sample_submission.csv        2.300 baris (semua diisi konstan 5.2)
```

Total 148 MB. Urutan baris CSV sama persis dengan urutan array `.npy`.

### Kualitas data — bersih

- **Tidak ada** nilai NaN atau Inf, baik di metadata maupun waveform.
- **Tidak ada** `sample_id` duplikat, **tidak ada** overlap ID antara train dan test.
- Semua kolom metadata terisi penuh.

Praktis tidak ada pekerjaan data-cleaning. Fokus bisa langsung ke feature engineering.

### Distribusi metadata

| Fitur | Train (mean / max) | Test (mean / max) | Catatan |
|---|---|---|---|
| `distance_km` | 127.0 / 200.0 | 122.5 / 199.8 | Dipotong keras di 200 km |
| `depth_km` | 57.1 / 457.9 | 58.0 / 375.0 | Ekor panjang (gempa dalam) |
| `snr_db` | 29.2 / 65.8 | 28.8 / 72.6 | |
| `is_clipped` | 176 True (1.7%) | 87 True (3.8%) | Test 2x lebih sering clipped |

Distribusi train dan test **mirip** — tidak ada tanda distribution shift besar. Satu-satunya
perbedaan yang perlu diperhatikan: proporsi record clipped di test dua kali lipat train.

### Distribusi target

- Range: **4.3 – 7.8**, hanya **32 nilai unik** (dibulatkan ke 1 desimal).
- Sangat terkonsentrasi: M 4.9–5.3 saja sudah mencakup ~58% data.

| Bin bobot | Jumlah record | % |
|---|---|---|
| M < 5.5 | 7.518 | 71,6% |
| 5.5 <= M < 6.0 | 2.277 | 21,7% |
| 6.0 <= M < 6.5 | 580 | 5,5% |
| M >= 6.5 | **130** | **1,2%** |

Hanya 130 record di bin dengan bobot tertinggi. Ini masalah utamanya: bin yang paling
dihukum justru yang datanya paling sedikit.

---

## 3. Temuan Kunci

### 3.1 Tidak ada `event_id` — tapi event bisa direkonstruksi

Metrik dihitung per-gempa, tapi dataset **tidak menyediakan kolom event**. Setiap
`sample_id` adalah satu record stasiun, dan beberapa record berasal dari gempa yang sama.

Pasangan `(depth_km, magnitude)` bisa dipakai sebagai proxy event ID:

- **905 pseudo-event** dari 10.505 record → rata-rata ~11,6 stasiun/gempa.
- Sangat tidak seimbang: median 6 record, tapi ada satu event dengan **401 record**.
- 184 event hanya punya 1 record.

Kenapa ini penting — dua hal:

1. **Cross-validation wajib `GroupKFold` berdasar event.** Kalau record dari gempa yang
   sama tersebar di train dan validation fold, model bisa "menghafal" magnitudo lewat
   `depth_km` yang identik. Skor CV jadi optimis palsu.
2. **Sample weighting harus membagi dengan jumlah record per event** (lihat §3.4).

Catatan: grouping ini heuristik. `depth_km` saja punya 750 nilai unik, dengan satu nilai
(kemungkinan default 10.0 km) dipakai 1.633 record — jelas bukan satu gempa. Menggabungkan
dengan `magnitude` mempersempitnya jadi wajar, tapi tetap perkiraan. Untuk test set,
grouping tidak bisa dihitung sama sekali (tidak ada label) — jadi ini murni alat CV.

### 3.2 Waveform kemungkinan besar adalah akselerasi, dan skalanya asli (tidak dinormalisasi)

- Amplitudo puncak per record: p1 = 8,9e-06, p50 = 2,7e-04, p99 = 1,0e-02, max = 1,33.
- **Tidak ada** record dengan puncak tepat 1.0 → data tidak dinormalisasi per-record.

Ini kabar baik: **skala amplitudo absolut dipertahankan**, dan amplitudo absolut adalah
sinyal fisik utama untuk magnitudo. Jangan melakukan per-record normalization saat
preprocessing — itu akan membuang informasi paling berharga.

Struktur jendela terkonfirmasi: amplitudo maksimum setelah indeks 200 (= P-wave arrival)
rata-rata **8,5x lebih besar** dari jendela noise sebelum P. Hanya 66 record (0,6%) yang
tidak menunjukkan pola ini — kandidat record bermasalah.

### 3.3 Metadata mentah hampir tidak informatif; fitur fisika jauh lebih kuat

Korelasi Pearson metadata mentah terhadap magnitudo sangat lemah:

| Fitur | Pearson | Spearman |
|---|---|---|
| `distance_km` | 0,042 | 0,052 |
| `depth_km` | −0,031 | −0,159 |
| `snr_db` | −0,154 | −0,125 |

Sebaliknya, fitur EEW klasik yang diturunkan dari waveform jauh lebih kuat. Saya menghitung
Pa (peak acceleration), Pv (peak velocity, 1x integrasi), dan Pd (peak displacement,
2x integrasi) — masing-masing dengan high-pass Butterworth 0,075 Hz sebelum integrasi untuk
menahan baseline drift — pada jendela kumulatif setelah P:

| Jendela | log Pa | log Pv | log Pd |
|---|---|---|---|
| 0,5 s | 0,183 | 0,412 | **0,450** |
| 1 s | 0,224 | 0,448 | **0,463** |
| 2 s | 0,298 | 0,480 | **0,489** |
| 3 s | 0,350 | **0,500** | 0,451 |
| 4 s | 0,385 | 0,444 | 0,422 |

Tiga hal yang terbaca:

- **Integrasi sangat membantu.** Pd dan Pv mengalahkan Pa telak, persis seperti literatur
  EEW. Konten frekuensi rendah membawa informasi ukuran sumber; frekuensi tinggi tidak.
- **Jendela pendek sudah kuat.** Pd pada 0,5 detik saja (r = 0,45) hampir sebaik jendela
  penuh. Informasinya datang cepat.
- **Pd menurun setelah 2 detik** — kemungkinan kontaminasi gelombang S atau drift integrasi.
  Jangan asal pakai jendela terpanjang; ekstrak multi-window dan biarkan model memilih.

Koreksi jarak menambah kekuatan lagi (amplitudo meluruh terhadap jarak, jadi harus
di-*de-trend*):

| Fitur gabungan | Pearson |
|---|---|
| log Pd (2s) + log(dist) | **0,551** |
| log Pd (1s) + log(dist) | 0,523 |
| log Pd (3s) + log(dist) | 0,509 |

`tau_c` (periode dominan, estimator ukuran sumber klasik) ternyata **tidak berguna** di sini
(r = −0,072). Jangan buang waktu ke sana.

### 3.4 Sample weighting yang cocok dengan metrik = kemenangan terbesar

Saya jalankan baseline `HistGradientBoostingRegressor` (loss MAE, 400 iterasi) dengan
`GroupKFold(5)` berbasis pseudo-event. Hasil out-of-fold:

| Model | EB-TWMAE | MAE per-record |
|---|---|---|
| Konstan 5.2 (seperti sample_submission) | 0,4670 | 0,2932 |
| Konstan 5.4 (konstan terbaik) | 0,4452 | 0,3336 |
| Metadata saja | 0,4572 | 0,3170 |
| Fitur fisika saja | 0,3061 | 0,2270 |
| Metadata + fisika | 0,2962 | 0,2231 |
| **Metadata + fisika, sample_weight = w(M) / n_record_event** | **0,2420** | — |

Perhatikan dua hal:

1. **Metadata saja hampir tidak mengalahkan tebakan konstan** (0,4572 vs 0,4452 — bahkan
   lebih buruk dari konstan terbaik). Semua sinyal ada di waveform.
2. **Sample weighting saja memangkas error 18%** (0,2962 → 0,2420) tanpa mengubah fitur
   atau arsitektur model. Ini rasio effort-terhadap-hasil terbaik di seluruh eksperimen.

Bobotnya: `w(M) / jumlah_record_event`. Faktor pertama meniru tail-weighting metrik;
faktor kedua meniru event-balancing (supaya event dengan 401 stasiun tidak mendominasi
gradien). Loss L2 lebih buruk dari L1 (0,2764 vs 0,2746 dengan bobot magnitudo saja) —
konsisten karena metriknya berbasis MAE.

### 3.5 Model mengompres prediksi ke arah rata-rata — dan ini yang paling mahal

Baseline tanpa weighting memprediksi dalam rentang **4,69 – 6,42**, padahal target
sebenarnya membentang **4,3 – 7,8**. Model tidak pernah berani memprediksi gempa besar.

Error per-bin (baseline tanpa weighting) menunjukkan dampaknya:

| Bin | MAE per-record | Bobot metrik |
|---|---|---|
| M < 5.5 | 0,182 | 1,0 |
| 5.5–6,0 | 0,258 | 1,5 |
| 6,0–6,5 | 0,486 | 2,0 |
| **M >= 6.5** | **0,821** | **2,5** |

Bin M >= 6.5 punya error **4,5x lebih besar** dari bin terkecil, dan dikalikan bobot 2,5.
Hanya 1,2% data, tapi kontribusinya ke skor akhir tidak proporsional.

Weighting memperbaiki ini secara alami: prediksi maksimum naik dari 6,42 → **6,95**.
Saya juga menguji kalibrasi eksplisit (mengembangkan varians prediksi di sekitar mean
dengan faktor alpha):

- Pada baseline tanpa weighting: alpha = 1,3–1,4 memperbaiki skor 0,2962 → 0,2783.
  Perbaikannya besar — kalibrasi memang menambal kompresi prediksi.
- Pada model dengan weighting: alpha = 1,1 hanya memberi 0,2420 → **0,2401**, lalu memburuk
  (alpha = 1,2 → 0,2431; alpha = 1,4 → 0,2653).

Artinya, sample weighting sudah menangani sebagian besar kompresi ini di level training.
Sisa gain dari kalibrasi post-hoc tinggal marginal (~0,8%) dan jendela alpha-nya sempit —
berisiko overfit ke CV. Kalibrasi adalah tambalan untuk model yang tidak diberi bobot;
kalau weighting sudah dipakai, jangan berharap banyak dari menumpuk keduanya.

---

## 4. Rekomendasi Strategi

### Prioritas berdasar rasio hasil terhadap effort

1. **Sample weighting `w(M) / n_event`** — sudah terbukti −18%. Kerjakan pertama.
2. **`GroupKFold` berbasis pseudo-event** — tanpa ini semua angka CV tidak bisa dipercaya.
3. **Fitur multi-window Pa/Pv/Pd** — sumber sinyal utama; ekstrak di 0,5/1/2/3/4 detik,
   per-komponen dan gabungan horizontal-vertikal.
4. **Koreksi jarak** — masukkan `log(dist)` sebagai fitur, dan juga sebagai interaksi
   eksplisit (`log Pd + log dist`) supaya model tidak perlu menemukannya sendiri.
5. **Perlakuan khusus record clipped** — 3,8% di test vs 1,7% di train. Amplitudonya
   tidak bisa dipercaya (record clipped punya magnitudo rata-rata 5,65 vs 5,28), jadi
   `is_clipped` harus jadi fitur, dan pertimbangkan feature-set alternatif untuk mereka.

### Fitur tambahan yang layak dicoba

- **Spektral**: energi per pita frekuensi (0,1–1, 1–5, 5–20, 20–50 Hz), frekuensi dominan,
  centroid spektral. Rasio energi frekuensi-rendah terhadap frekuensi-tinggi adalah proxy
  ukuran sumber yang lebih stabil dari tau_c.
- **Bentuk envelope**: laju kenaikan amplitudo (rise time), luas di bawah envelope
  kumulatif, waktu untuk mencapai 50%/90% energi.
- **Antar-komponen**: rasio horizontal/vertikal, polarisasi (rectilinearity) — informasi
  arah sumber.
- **Statistik per-window**: RMS, kurtosis, zero-crossing rate di beberapa sub-jendela.

### Arsitektur model

**Rute utama — gradient boosting di atas fitur turunan.** Ini yang saya rekomendasikan
sebagai fondasi: cepat, stabil, mudah didebug, dan sudah mencapai 0,2420. LightGBM/XGBoost
kemungkinan sedikit lebih baik dari `HistGradientBoostingRegressor` sklearn.

**Rute kedua — 1D CNN di atas waveform mentah.** Berpotensi menangkap pola yang tidak
ter-*hand-engineer*. Catatan penting kalau menempuh ini:
- **Jangan normalisasi per-record** (§3.2) — pakai log-amplitude atau normalisasi global.
- Masukkan metadata lewat concat di layer akhir.
- Dengan hanya 905 event efektif (bukan 10.505 sampel independen), risiko overfitting
  tinggi. Augmentasi (time shift, penambahan noise, dropout kanal) hampir wajib.
- Bisa dilatih di GPU lokal (RTX 4060, torch+CUDA sudah siap) — lihat §5.

**Ensemble keduanya** kemungkinan jadi solusi terbaik. Diversitas antara model
fitur-eksplisit dan model end-to-end biasanya menghasilkan gain nyata.

### Yang sebaiknya dihindari

- Optimasi MAE per-record — bukan itu metriknya.
- Normalisasi amplitudo per-record — membuang sinyal utama.
- `KFold` biasa — bocor lewat event.
- tau_c sebagai fitur andalan — sudah diuji, tidak berkontribusi.
- Kalibrasi ekspansi varians **di atas** model yang sudah diberi bobot — redundan dan
  sedikit merugikan.

---

## 5. Kaggle (GPU) atau Lokal?

**Jawaban singkat: kerjakan sepenuhnya di lokal. Kaggle tidak diperlukan sama sekali —
termasuk untuk rute deep learning.**

Mesin ini punya **NVIDIA RTX 4060 (8 GB VRAM)** dengan `torch 2.6.0+cu124` sudah terpasang
dan `torch.cuda.is_available() == True`. Jadi pertanyaan "perlu Kaggle buat GPU?" jadi tidak
relevan: GPU-nya sudah ada di sini, dan tanpa batasan sesi 9 jam / kuota mingguan Kaggle.

### Pengukuran aktual di mesin ini

| Operasi | Waktu |
|---|---|
| Load kedua array `.npy` (154 MB) | 0,1 s |
| High-pass filter + integrasi ganda, seluruh 10.505 record | 1,2 s |
| Ekstraksi set fitur fisika lengkap | 1,8 s |
| Training `HistGradientBoostingRegressor` 5-fold CV | 6 s |
| **Satu siklus eksperimen penuh** | **< 10 detik** |
| Eksekusi penuh `eda.ipynb` (58 sel, semua CV) | ~2 menit |

Datasetnya kecil. Seluruh train set muat di RAM dalam 126 MB. Tidak ada satupun operasi
yang mendekati batas mesin. Iterasi 10 detik di lokal jauh lebih produktif daripada
menunggu commit Kaggle — dan untuk GBM, GPU pun tidak dibutuhkan.

### Rute CNN — juga di lokal

RTX 4060 lebih dari cukup untuk dataset ini. 10.505 x 1000 x 3 float32 = 126 MB, muat penuh
di 8 GB VRAM sekaligus, jadi tidak perlu data loader yang rumit. Untuk 1D CNN kecil,
perkiraan waktu per epoch hanya beberapa detik — training multi-fold penuh selesai dalam
hitungan menit, bukan jam.

Yang perlu diperhatikan justru bukan komputasi, melainkan **ukuran sampel efektif**: hanya
905 event independen. Batasannya adalah overfitting, bukan GPU.

### Environment: pakai venv `C:\Patrick\coding\.venv`

Semua pekerjaan pakai venv bersama yang sudah ada — **tidak perlu bikin venv baru** di folder ini.
Isinya sudah lengkap:

```
Python 3.11.6   —  C:\Patrick\coding\.venv\Scripts\python.exe
numpy 1.26.4      pandas 2.3.3      scipy 1.17.1     scikit-learn 1.6.1
matplotlib 3.7.5  seaborn 0.13.2    lightgbm 4.6.0   xgboost 3.0.3
torch 2.6.0+cu124 (CUDA aktif, RTX 4060 8 GB)        ipykernel 6.30.0
```

**Tidak ada yang perlu diinstal.** lightgbm, xgboost, dan torch sudah tersedia.

VS Code sudah dikonfigurasi lewat [`.vscode/settings.json`](../.vscode/settings.json) di root
supaya interpreter dan kernel notebook otomatis menunjuk ke venv ini.

> **Peringatan:** jangan pakai `python` polos dari PATH — itu menunjuk ke Python 3.14 sistem
> yang **kosong** (numpy pun tidak ada). Di terminal, aktifkan venv dulu atau panggil
> path lengkapnya.

```bash
C:/Patrick/coding/.venv/Scripts/python.exe -m jupyter nbconvert --to notebook --execute --inplace "Case 1/eda.ipynb"
```

---

## 6. Rencana Kerja yang Disarankan

Dengan 7 hari tersisa:

| Tahap | Isi |
|---|---|
| **1. Fondasi** | Modul ekstraksi fitur + `GroupKFold` + fungsi metrik EB-TWMAE. Submit baseline berbobot (target ~0,24) sebagai jangkar. |
| **2. Perluasan fitur** | Tambah fitur spektral, envelope, antar-komponen. Ukur setiap tambahan terhadap CV. |
| **3. Model** | Tuning LightGBM/XGBoost. Perlakuan khusus record clipped. |
| **4. Deep learning** *(opsional)* | 1D CNN di GPU lokal (RTX 4060) kalau waktu memungkinkan. |
| **5. Ensemble & finalisasi** | Blend, verifikasi format submission, cek sanity distribusi prediksi test. |

Prioritaskan tahap 1–3. Tahap 4 hanya kalau tahap 1–3 sudah solid — gain dari sample
weighting dan feature engineering lebih pasti daripada gain dari CNN pada dataset sekecil ini.

### Catatan verifikasi submission

`sample_submission.csv` berisi konstanta 5.2 di semua baris (EB-TWMAE ~ 0,467). Pastikan
file akhir: header `sample_id,magnitude`, 2.300 baris, urutan dan isi `sample_id` sama
persis dengan `test_meta.csv`.

---

## 7. Keterbatasan Analisis Ini

Beberapa hal yang perlu diketahui saat membaca angka di atas:

- **Pseudo-event grouping adalah heuristik.** Semua angka EB-TWMAE di §3.4 bergantung pada
  asumsi bahwa `(depth_km, magnitude)` mengidentifikasi gempa. Kalau grouping sebenarnya
  berbeda, angka absolutnya bergeser — meski urutan peringkat antar-metode kemungkinan tetap.
- **Angka CV bukan skor leaderboard.** Test set punya distribusi grouping yang tidak
  diketahui dan proporsi clipped 2x lebih tinggi.
- **Baseline belum di-tuning.** Hyperparameter GBM dipakai apa adanya; angka 0,2420 adalah
  lantai, bukan plafon.
- Analisis fitur spektral, envelope, dan antar-komponen di §4 **belum diuji** — itu
  rekomendasi berdasar literatur EEW, bukan hasil pengukuran.
