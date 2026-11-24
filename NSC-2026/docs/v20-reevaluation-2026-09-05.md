# Evaluasi ulang v20 — 5 September 2026

Ada pendekatan yang belum diuji dalam log lama dan sekarang memberi perbaikan terukur:
**mempelajari perubahan RH pada 30 menit dan 2 jam, kemudian merekonsiliasikannya dengan
prediksi level RH**. Kandidat ini memperbaiki 12/12 fold yang tersedia untuk audit
kronologis dan 5/5 blok stress. Ini kandidat pengembangan berikutnya, bukan klaim skor
public 2,7 atau jaminan menjadi model terbaik secara global.

Audit ini membaca riwayat §1–143, pipeline final, kode pembentuk fitur, evaluasi dan
cache eksperimen. File produksi dan submission lama tidak diubah. Skrip analisis baru
ada di `src/an30_v20_audit.py` sampai `src/an34_increment_stress.py`;
hasil lengkap ada di `outputs/audit_v20/`.

## 1. Fakta terbaru dan koreksi terhadap log

- Pengguna melaporkan **public v20 = 3.05372**. Ini +0.02786 dari v16 (3.02586),
  dan +0.04783 dari best public historis v11 (3.00589).
- Menurut pengguna, tidak pernah ada konfirmasi public memakai 220 baris pertama.
  Split mungkin acak, tetapi itu juga belum dikonfirmasi. Karena itu, sebutlah
  **near/far**, bukan public/private, untuk potongan kronologis tersebut.
- Skor public dua pesaing sekitar 2,7 tidak memberi informasi pasti tentang skor
  private mereka. Kita juga tidak punya dasar untuk menyebut hasil mereka hanya
  akibat banyak submission.
- Dari 3.05372 ke 2,7 perlu penurunan **21,82% MSE**. Tidak tepat mengonversi
  gain CV menjadi janji leaderboard memakai regresi empat titik di log lama.

Simulasi 2.000 partisi acak 220/514 baris, seed 20260905, pada fitur test saja:

| Coverage pressure | Hasil |
|---|---:|
| Seluruh test | 0.8410 |
| 220 baris pertama | 0.9345 |
| 514 baris terakhir | 0.8010 |
| Public simulasi acak, rentang persentil 2,5–97,5 | 0.8036–0.8791 |
| Private simulasi acak, rentang persentil 2,5–97,5 | 0.8247–0.8570 |

Asimetri pressure kronologis memang ada. Namun jika split acak, kedua bagian
mencampur episode cuaca yang sama. Klaim §78/130/138 bahwa suatu metode pasti
menolong atau merugikan **private** berdasarkan potongan akhir harus ditarik kembali.
Curve §138 juga berasal dari sembilan holdout yang saling terkait; crossover 0,74
bukan hukum transfer dan prediksi +0,016 private bukan skor yang diketahui.

## 2. Masalah utama: label validasi masuk kembali ke meta-model

`src/exp43_robust_baseline.py:score_stack` menahan satu `(family, fold)`, bukan
menahan seluruh tanggal label validasi. Fold lain masih membawa target yang sama.
Pola yang sama ada pada evaluasi shrinkage, harmonic, dan beberapa analisis residual.
`src/h7.py:nested` juga memakai nomor fold lebih kecil tanpa memastikan semua label
fold tersebut sudah tersedia pada tanggal forecast berikutnya.

Hasil hitung aktual:

- 14.400 baris fold hanya memuat **1.584 timestamp unik**.
- Pada **17 dari 18 fold**, seluruh timestamp yang dinilai juga ada di meta-training.
- Pada R0, 912 dari 1.008 timestamp masuk kembali lewat fold lain.
- Uji negatif P8: tambah 10 pada label tanggal validasi **di salinan meta-training**,
  pertahankan fitur dan seluruh prediksi member. Prediksi legacy berubah sampai
  **5.84623 RH**. Pada meta-training yang hanya memakai masa lalu, perubahan **0.0**.

Ini adalah kebocoran dalam **evaluasi pemilihan blend**. Temuan ini tidak berarti
submission final memakai target test: target test memang tidak tersedia.
Namun bukti bahwa perubahan tertentu pasti lebih baik menjadi tidak dapat dipercaya.

Audit baru membatasi label meta sampai origin forecast. Dua kontrol dipakai:
tetap mempertahankan baris berulang, dan satu prediksi OOF terbaru per timestamp.
Sensitivitas ketiga menambahkan jeda 48 jam pada batas label meta.
Hasil di bawah memakai **11 fold identik** yang tersedia pada semua prosedur.
Metric adalah pooled RMSE, dengan pembobotan fold-row yang sama antarmodel.

| Evaluasi meta | v16 | v20 | v20 − v16 |
|---|---:|---:|---:|
| Legacy leave-one-fold-out | 4.13973 | 4.09266 | −0.04707 |
| Label hanya masa lalu, duplikat tetap | 4.59084 | 4.64955 | +0.05871 |
| Label hanya masa lalu, satu timestamp satu prediksi | 4.49517 | 4.60139 | +0.10622 |
| Prosedur sebelumnya + jeda label 48 jam | 4.36193 | 4.44026 | +0.07833 |

**Arah keunggulan v20 berbalik**, termasuk pada kontrol yang tetap mempertahankan
duplikat. Jadi hasilnya tidak hanya akibat deduplikasi. Penghapusan label masa depan
juga memperkecil data meta; inilah keterbatasan yang memang dialami forecasting nyata.

Angka ini bukan estimasi public, dan 11 fold tersebut tetap saling overlap. Audit cache
tidak membuat dataset menjadi holdout baru. Fitur lama juga dibangun dari grid penuh:
evaluasi produksi berikutnya perlu membangun ulang fitur sampai akhir horizon validasi,
sehingga tidak memanfaatkan sensor setelah akhir horizon yang disimulasikan.

## 3. Breakdown error yang dihitung ulang

Gunakan v20 dengan meta-training masa lalu; untuk setiap timestamp ambil forecast
terbaru yang eligible. Tersisa **1.200 timestamp**, 4 Agustus 15:00 sampai
29 Agustus 14:30. Ini diagnostik kalender yang berbeda dari rata-rata fold.

| Ukuran | Hasil |
|---|---:|
| RMSE | 6.02413 |
| Bias prediksi − aktual | −0.59546 RH |
| Bagian SSE dari 10% timestamp terburuk | **62,62%** |
| Bagian MSE dari mean error per hari | **36,31%** |
| Bagian MSE dari error di dalam hari | **63,69%** |
| Autokorelasi error lag satu | 0.9330 |

Pembagian mean error harian + deviasinya bersifat ortogonal, sehingga kedua bagian
MSE di atas benar-benar menjumlah menjadi 100%. Ini lebih mudah diinterpretasikan
daripada menganggap dua komponen moving-average selalu ortogonal.

| Jam | RMSE | Bagian SSE |
|---|---:|---:|
| 00–06 | 7.1546 | 35,26% |
| 06–12 | 5.9094 | 24,06% |
| 12–18 | 4.9317 | 16,75% |
| 18–24 | 5.8932 | 23,93% |

Hari penuh terburuk: 5 Agustus (14.9657; bias −9.5305), 28 Agustus (9.2087;
bias −6.4238), dan 7 Agustus (8.7830; bias +5.1864).
29 Agustus hanya memuat 30 baris (RMSE 9.1746), sehingga tidak setara dengan hari penuh.
Bias berbalik tanda antarepisode: offset global bukan solusi yang terarah.

116 baris dengan suhu asli missing memiliki RMSE 5.2366; 1.084 baris lainnya 6.1024.
Enam baris suhu terobservasi yang diperbaiki cleaner hanya membawa 0,32% SSE.
Baris dengan perubahan suhu >2 C per 30 menit justru lebih mudah daripada perubahan
≤0,5 C. Ini observasi, bukan uji kausal, tetapi **tidak mendukung cleaning agresif
sebagai prioritas utama**. Keputusan lama mempertahankan Hampel yang longgar masuk akal.

Data tetap kecil: 2.933 target train pada interval setengah jam, 734 timestamp test,
118 fitur final; tiga `T_minus_soilT*` masih lolos filter meskipun log menyebut
"drop every soil column". Jumlah row tidak boleh dianggap jumlah observasi independen.

## 4. Kesimpulan lama yang terlalu luas

1. **§96 belum membuktikan information ceiling.** Gagalnya residual LightGBM/ridge
   pada satu representasi hanya menolak konfigurasi tersebut. Residual baseline yang
   dipakai juga berasal dari meta-evaluasi dengan overlap label. Tidak ada estimasi
   batas Bayes yang membuktikan seluruh sensor sudah habis informasinya.
2. **§99 bukan penjelasan hasil pesaing.** Perhitungan maksimum N normal memerlukan
   asumsi joint distribution antarpercobaan; submission yang mirip tidak independen.
   Angka sigma dari perubahan kita tidak otomatis berlaku pada metode pesaing.
3. **AUC adversarial 1 bukan bukti semua CV mustahil.** Classifier dapat mengenali
   fingerprint episode pada statistik rolling, terlebih dengan split acak per baris.
   Itu tidak membuktikan setiap representasi stabil tidak memiliki overlap support.
4. **§115 tidak benar-benar menguji temporal bagging secara luas.** Window recent45
   identik dengan seluruh sejarah pada **16/18 fold**; pada dua fold lain hanya
   membuang 53 baris. Korelasi 0,999 sangat mungkin merupakan akibat eksperimen yang
   hampir tidak mengubah input training, bukan bukti drift tidak ada.
5. **NNLS lalu normalisasi bukan optimisasi least-squares simplex secara langsung.**
   Kontrol SLSQP dengan batas bobot nonnegatif dan sum=1 memperbaiki v20 sedikit pada
   audit masa lalu, tetapi belum mengalahkan v12/v16 secara konsisten. Bukan prioritas.

Untuk evaluasi temporal, dokumentasi [TimeSeriesSplit](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.TimeSeriesSplit.html)
menjelaskan mengapa training pada masa depan dan scoring pada masa lalu tidak sesuai.
Risiko overfitting pada kriteria pemilihan model sendiri dibahas oleh
[Cawley & Talbot, JMLR 2010](https://www.jmlr.org/papers/v11/cawley10a.html).
Kedua sumber dipakai untuk metodologi, bukan menambah data kompetisi.

## 5. Pendekatan baru yang benar-benar diuji

Prediksi level RH dan prediksi **perubahan RH** merupakan dua tugas berbeda.
Offset cuaca yang bergeser lambat dapat banyak hilang ketika mengambil selisih.
Ini hipotesis yang diuji, bukan asumsi bahwa selisih pasti invariant.

Untuk h=1 dan h=4 slot, latih LightGBM memprediksi `y[t]−y[t−h]`, memakai
fitur exogenous pada t, beberapa fitur pada t−h, serta perubahan fitur.
Kedua endpoint target harus berada di sisi train. Tidak ada nilai RH validasi atau
test yang menjadi input inferensi. Tidak diperlukan recursive feeding target test.

Gabungkan level p dengan perubahan terprediksi d melalui masalah kuadrat:

    min_z ||z-p||² + 4 ||D_1 z-d_1||² + ||D_4 z-d_4||²

`D_h z` adalah selisih z antar h slot. Solusi sparse mengembalikan satu kurva RH
yang dekat dengan level baseline sekaligus mengikuti dinamika yang dipelajari.
Koefisien 4 dan 1 adalah regularisasi eksperimen, ditetapkan sebelum screening awal,
bukan disetel dari skor leaderboard. Model increment: L2, 500 trees, learning rate
0,03, 15 leaves, min child 30, lambda 5, feature fraction 0,8, seed 20260905.

Screen awal juga memasukkan 6 jam. Ablasi dilakukan **setelah** melihat hasil screen,
dan menemukan 6 jam merusak baseline yang lebih kuat. Karena pemilihan ablasinya
adaptif, hasil ini harus dilabeli eksploratif; bootstrap tidak menghapus selection bias.

| Kandidat pada v12 | Mean delta RMSE | Fold membaik |
|---|---:|---:|
| Perubahan 30 menit | −0.07962 | 12/12 |
| Perubahan 2 jam | −0.12994 | 12/12 |
| Perubahan 6 jam | +0.06254 | 5/12 |
| **30 menit + 2 jam** | **−0.15429** | **12/12** |
| 30 menit + 2 jam + 6 jam | −0.02635 | 8/12 |

Kandidat 30 menit + 2 jam, dibandingkan dengan baseline masing-masing:

| Baseline | Pooled sebelum | Pooled sesudah | Stress sebelum | Stress sesudah |
|---|---:|---:|---:|---:|
| **v12** | **4.68487** | **4.52516** | **4.04371** | **3.88320** |
| v16 | 4.70154 | 4.53534 | 4.07590 | 3.91554 |
| v20 | 4.83036 | 4.59435 | 4.10073 | 3.84105 |

Seluruh baseline membaik pada 12/12 fold dan 5/5 blok stress. Stress memakai lima
blok terpisah yang sudah ada, embargo training 96 jam dan meta-label masa lalu yang
dideduplikasi. Skornya berbeda dari stress legacy karena prosedur meta diperbaiki.
Blok stress tetap berasal dari kalender train yang sama, bukan validasi eksternal
atau independen dari seluruh pencarian sebelumnya.

Pada 15 hari terakhir (P8), v12 membaik **4.36926 → 4.30324**;
v20 **4.58978 → 4.44822**. Jadi bukan hanya menang pada fold awal yang sangat buruk.
Pada v12, delta mean P/Q/R berturut-turut −0.15850/−0.14768/−0.15486.

Setelah satu forecast per timestamp, v12 membaik 5.72669 → 5.54110.
Bootstrap circular blok kalender 3 hari, 4.000 resample, memberi interval
delta **[−0.28191, −0.07707]**; blok 7 hari [−0.27629, −0.06885]. Ini interval
sampling bersyarat pada kandidat yang sudah dipilih, bukan interval transfer ke test.

Kontrol zero-increment pada kekuatan screen awal jauh lebih buruk (mean 13.0362
versus baseline 5.1035 pada empat fold screen). Artinya gain konfigurasi ini berasal
dari perubahan yang dipelajari, bukan sekadar menghaluskan prediksi. Kontrol tersebut
tidak menolak semua kemungkinan smoothing pada kekuatan lain.

Recent21/recent30 juga diuji ulang pada empat fold dengan member **dan meta-OOF**
yang sama-sama dilatih ulang pada window tersebut. Mean baseline 5.10355;
recent21 5.26579, recent30 5.17853. Jadi truncation sederhana belum layak, walaupun
alasan penutupan recent45 di log lama salah. Bagging episode/block tetap berbeda
dari mengganti satu member dengan window pendek, dan belum diuji di sini.

## 6. Rekomendasi dan batas pekerjaan ini

**Prioritas pertama: dua model increment (30 menit dan 2 jam) di atas baseline
regularized v12/v16, dengan evaluasi meta yang benar-benar kronologis.**
V12+increment paling baik pada pooled temporal audit; v20+increment paling baik
pada stress audit. Karena urutannya belum seragam, belum ada bukti satu backbone
menang mutlak. Kandidat incremental sendiri memiliki arah yang konsisten pada semuanya.

Tahap berikut untuk menghasilkan submission yang dapat dipertanggungjawabkan:

1. Bekukan dua horizon dan regularisasi tersebut; jangan lanjut grid-search blend lama.
2. Bangun ulang OOF dari CSV dengan seluruh meta-label sebelum origin, cutoff fitur
   pada akhir horizon validasi, dan jumlah seed yang cocok dengan final inference.
3. Bandingkan satu origin per blok kalender, full horizon 15 hari, serta stress yang
   meliputi **seluruh test**, bukan diasumsikan private di ujung. Laporkan overlap dan
   interval blok kalender; jangan menyebut 12 fold sebagai 12 bukti independen.
4. Periksa kestabilan increment terhadap seed dan episode; kegagalan model 6 jam
   menunjukkan bahwa model dinamika pun mempunyai batas skala.
5. Jika hasil bertahan, implementasikan satu flag baru pada `final_pipeline.py`,
   verifikasi fitur target-blind, reproduksi dua kali dan validasi schema submission.

Pendekatan lain yang belum diuji tuntas: model spline/GAM pada representasi fisika
berdimensi kecil; model sequence kecil dengan input exogenous beberapa jam;
temporal block bagging yang benar-benar mengubah sampel training; audit optimisasi
CatBoost Huber (bukan hanya mengganti loss atau menambah seed). Ini prioritas kedua,
bukan alasan untuk menjalankan seluruh model zoo sekali lagi.

Belum ada CSV v21, perubahan pipeline produksi, atau submission ke leaderboard dari
sesi audit ini. Klaim yang didukung adalah **ada jalur baru yang lolos screening
dan stress lokal**. Skor 2,7 dan private pesaing tetap belum diketahui.

## Reproduksi dan verifikasi

Jalankan dari root repo dengan Python `.venv/Scripts/python.exe`:

    src/an30_v20_audit.py
    src/an31_dynamics_screen.py
    src/an32_increment_validation.py
    src/an33_audit_summary.py
    src/an34_increment_stress.py

Audit mereproduksi angka legacy v12=4.759265, v16=4.746445, v20=4.688225;
assertion memastikan meta-label kronologis tidak overlap, kedua endpoint increment
berada di train, dan residual persamaan linear <1e-7. Sepuluh unittest lama dan
tujuh pemeriksaan `test_session16.py` lulus. Tes lama tidak mendeteksi kebocoran
meta di atas; uji perubahan label dan audit timestamp yang mengungkapnya.

---

## Tindak lanjut — sesi 21, 5 September 2026

Rekomendasi §6 sudah dikerjakan. Rinciannya ada di `progress.md` §150–156; ringkasnya:

1. **Dua horizon dibekukan** pada 30 menit dan 2 jam dengan bobot 4 dan 1. Tidak ada
   pencarian grid baru. Semuanya masuk `final_pipeline.py` sebagai flag `--increment`.
2. **OOF dibangun ulang dari CSV** pada tiga holdout 15 hari, dengan fitur dibangun dari
   grid yang dipotong di akhir horizon validasi, meta-label sepenuhnya sebelum origin, dan
   jumlah seed sama dengan final fit (`src/an36_increment_production.py`). Sembilan dari
   sembilan sel blok-backbone membaik.
3. **Interval blok kalender dilaporkan apa adanya.** Pada dua blok yang tidak tumpang tindih,
   interval blok 3 hari **melewati nol** untuk v12 dan v16. Tiga puluh hari kalender bukan
   tiga puluh observasi bebas, dan angka itu mengatakannya. Yang menopang adopsi adalah arah
   yang sama pada 12/12 fold cache, 9/9 fold pipeline, 5/5 blok stress, 9/9 sel holdout, dan
   60/60 sel fold-seed — bukan dua blok ini sendirian.
4. **Kestabilan seed dan episode diuji** (`src/an35_increment_seed_episode.py`). Enam puluh
   dari enam puluh sel fold×seed membaik pada setiap backbone; sebaran seed 0,004 terhadap
   efek 0,16–0,24. Seed 20260905 yang dibekukan ternyata **paling buruk** dari lima, jadi
   angka screen §5 terlalu rendah, bukan hasil pemilihan yang menguntungkan. Per hari, hanya
   20 dari 26 hari membaik untuk v12: arahnya konsisten, variansinya nyata.
5. **Satu flag, verifikasi target-blind, reproduksi dua kali, validasi schema.** `--selftest`
   kini juga memeriksa matriks desain increment. Dibangun dua kali dari nol, log identik,
   md5 `5396077ee744458aa8d21b2ea336f61a`.

Dua koreksi terhadap dokumen ini:

- Kalimat "Belum ada CSV v21" sudah tidak berlaku. Tiga file ada:
  `v21_increment_v12.csv`, `v21_increment_v16.csv`, `v21_increment_v20.csv`.
  **Rekomendasi: `v21_increment_v16.csv`.** Belum ada yang dikirim ke leaderboard.
- §6 menyebut backbone belum jelas. Pada evaluasi holdout yang menghormati horizon fitur dan
  meta kronologis, v20 justru **terakhir pada dua dari tiga blok dan terakhir secara pooled**
  — urutan yang sama dengan leaderboard publik, dan kebalikan dari CV pipeline. Ini menguatkan
  §2. v12 dan v16 tetap seri; v16 dipilih karena satu-satunya perbedaan di antara keduanya
  (member L2, §98 log lama) punya bukti nested sendiri.

Kontrol zero-increment §5 kini juga dijalankan **pada baris test yang akan dinilai**, karena
kontrol itu tidak memerlukan label: penghalusan pada kekuatan yang sama menggeser submission
5,83 %RH, sedangkan jalur hasil rekonsiliasi hanya bergerak 1,07 %RH dan berjarak 5,75 %RH
dari jalur yang dihaluskan. Jadi yang bekerja adalah perubahan yang dipelajari, bukan
penghalusan.

Skor 2,7 dan private pesaing tetap belum diketahui, dan tidak ada delta holdout di sini yang
diterjemahkan menjadi prediksi skor leaderboard.
