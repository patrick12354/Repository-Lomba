# Evaluasi ulang v21 dan rencana eksperimen lanjutan — 5 September 2026

**Baseline public tetap `v21_increment_v16.csv`, skor 2.86595 menurut pengguna.** Masih ada pendekatan berbeda yang layak diuji. Prioritas saya: perbaiki pengukuran, evaluasi ulang physics/deshrink, lalu optimalkan kombinasi level dan increment terhadap RMSE akhir. Setelah itu, coba spline fisik dengan informasi lintasan suhu dan anchor RH pada batas train. Belum ada bukti untuk menjanjikan skor 2,7.

Tujuan: memilih kandidat berikutnya berdasarkan evaluasi kronologis yang cocok dengan produksi, bukan menambah variasi karena CV lama turun. Arsitektur eksperimen: pipeline v21 dibekukan sebagai kontrol, cache prediksi bertanggal, kalibrasi dari inner rolling origins, dan pengukuran akhir pada blok outer. Tech stack: Python di `.venv`, pandas/NumPy, SciPy sparse/optimasi, LightGBM/CatBoost, dan scikit-learn.

Dokumen ini melanjutkan audit v20 dan meninjau pembaruan `progress.md` sampai §179, `final_pipeline.py`, harness produksi, analisis error/oracle/deshrink, tabel eksperimen, dan log kandidat. Perhitungan ulang di bawah dijalankan dari artefak repo. Pada sesi ini hanya dokumen ini yang ditambahkan; skrip analisis dan produksi belum diperbaiki, model baru belum dilatih, submission belum dibuat atau dikirim.

## 1. Posisi sebenarnya sekarang

| Artefak | Status | MD5 terverifikasi |
|---|---|---|
| `v21_increment_v16.csv` | Public **2.86595**, incumbent | `5396077ee744458aa8d21b2ea336f61a` |
| `v21_increment_v16_phys.csv` | Kandidat lokal, public belum diketahui | `24ead6b72bf62d9f0492f3d72aff1c31` |
| `v21_increment_v16_phys_dsh.csv` | Kandidat lokal, public belum diketahui | `4272e15f36d73d459a36ea7efeca3b2b` |

Ketiganya berada di `outputs/submissions/`. Jangan menyebut dua terakhir sebagai peningkatan leaderboard yang sudah terbukti. Dari 2.86595 ke 2,7 perlu penurunan sekitar **11,25% MSE**, atau 0,16595 RMSE. Selisih public v16 → v21 sebesar −0,15991 tidak menjadi kurs konversi untuk eksperimen berikutnya.

Public/private tidak pernah dikonfirmasi kronologis. Pembagian acak juga masih dugaan pengguna. Evaluasi utama tetap forecasting 15 hari karena seluruh test berada setelah train; kemungkinan public acak tidak membenarkan random train/validation split. Potongan 220/514 secara kronologis hanya skenario near/far.

## 2. Koreksi baru yang memengaruhi keputusan

### 2.1 Ada bug pasangan tanggal pada koreksi error harian

Di `src/an40_error_anatomy.py`, prediksi daily residual disusun menurut tanggal hasil `groupby`, lalu diterapkan dengan:

```python
adj = e - np.repeat(pred, Q.groupby('day').size().to_numpy())
```

Namun cache Q tersusun **B1 lalu B2**, sedangkan tanggal terurut dimulai dari B2. Pemeriksaan ulang menemukan **1.440/1.440 baris berbeda pasangan** dibanding mapping eksplisit berdasarkan tanggal.

| Pengukuran dari cache yang sama | RMSE |
|---|---:|
| Increment baseline | 5.53694197 |
| Koreksi salah pasangan, seperti §163 | 5.49433491 |
| Koreksi dengan pasangan tanggal benar | **5.57769530** |

Jadi klaim gain −0,0426 harus ditarik. Perbaikan yang direncanakan:

```python
pred_day = pd.Series(pred, index=day_err.index)
adj = e - Q['day'].map(pred_day).to_numpy()
```

LOO R² −0,0816 tidak berubah oleh perbaikan mapping ini. Namun LOO tersebut melatih dengan hari yang lebih baru untuk memprediksi hari lebih lama, standardisasi dilakukan sebelum split, dan fitur berasal dari full grid. Itu diagnostik retrospektif, bukan validasi produksi untuk daily correction. Satu Ridge pada sekitar 31 hari tidak membuktikan bahwa semua informasi level tidak tersedia.

### 2.2 “Pooled” menunjuk beberapa statistik berbeda

`an36_increment_production.py` menghitung pooled summary dengan B3 ikut masuk. B3 overlap B1/B2. `an41_increment_oracle.py` menamai **rata-rata RMSE blok** sebagai pooled. Definisi primary selanjutnya harus:

`pooled_rmse = sqrt(sum(SSE blok) / sum(n blok))`, memakai B1+B2 saja.

| Sumber/konfigurasi | Pooled B1+B2 yang dihitung ulang |
|---|---:|
| Cache level v16 | 5.644891 |
| Cache increment, satu seed | 5.536942 |
| Physics screen, satu seed | 5.505093 |
| Physics + half deshrink screen, satu seed | 5.476466 |
| Oracle script, increment lima seed | 5.514359 |
| Oracle script, true increments | 4.600206 |

Untuk oracle, angka §169 sebesar 5.3841 → 4.4447 adalah **mean RMSE**, bukan pooled. Perbaikan pooled dari true increments pada eksperimen itu −0,914153. Itu eksperimen memakai label holdout sebagai oracle, bukan hasil kandidat deployable.

Cache produksi dibuat dengan `fit_increments(...)` tanpa parameter seeds, sehingga memakai default satu seed. `an41` secara eksplisit memakai lima. Seed count adalah alasan tambahan mengapa baseline angka antarskrip tidak boleh dipertukarkan. Tabel ini tidak mengklaim physics/deshrink sudah lolos outer evaluation lima seed.

### 2.3 Sembilan fold pipeline bukan konfirmasi independen

`final_pipeline.py` memasang NNLS, bobot time-of-day, dan harmonic bias pada seluruh O, lalu melaporkan skor pada O yang sama. Setelahnya increment diterapkan ke prediksi level itu. Ini tidak membocorkan label test, tetapi validasi meta bersifat in-sample.

Maka §158/164/170/176 memakai “konfirmasi” yang tidak layak menjadi hakim terakhir, baik untuk menerima physics/deshrink maupun menolak smoothed-level. Selain itu, kalendernya sudah berulang kali dipakai; protokol berbeda tidak menciptakan observasi baru.

Tulisan “9/9 better” pada log physics/deshrink membandingkan hasil dengan **level sebelum increment**, bukan dengan v21 atau physics incumbent. Di kode pembandingnya `pf_i < pf_b`. Hitung paired delta antarkandidat secara eksplisit; jangan mengambil win count tersebut sebagai bukti upgrade.

### 2.4 Deshrink belum dibuktikan sebagai solusi umum

Di `fit_increments`, OOF factor dibuat dengan tiga bagian waktu, tetapi train adalah `rows.difference(va)`: ada data setelah validation chunk. Target increment pada sisi split juga dapat berbagi endpoint label dengan increment di sisi lain karena belum dipurge. Tidak ada label outer/test yang masuk, tetapi ini bukan forward OOF yang menyerupai forecasting.

Rasio `sd(y)/sd(pred)` lebih dari satu bukan bukti forecast perlu diekspansi. Conditional mean yang optimal untuk MSE memang dapat memiliki variance lebih kecil daripada target. Slope regresi justru `Cov(y,pred)/Var(pred)`, bukan rasio standar deviasi. Untuk pipeline ini keduanya tetap harus dinilai lewat **RMSE z setelah solve**, bukan sekadar dispersion.

Half deshrink memperbaiki B1 −0,02551 dan B2 −0,03175, tetapi merugikan B3 **+0,03428** terhadap physics pada screen satu seed. Ini kandidat masuk akal dengan risiko transfer, bukan otomatis default terbaru.

### 2.5 Beberapa kesimpulan matematis perlu dipersempit

- `D_h` mempertahankan mean **seluruh komponen graf yang terhubung**, sebelum clipping. Tidak ada jaminan setiap mean harian tetap. Pengukuran daily MSE memang berubah: 12,159164 → 12,157089. Kecil, tetapi klaim bahwa rekonsiliasi mustahil mengubah day-level salah secara umum.
- Oracle daily-constant correction membatasi keluarga koreksi konstan per hari saja. Oracle true increments pada lambda tetap juga bukan batas universal RMSE: error increment tertentu dapat mengompensasi error level. Angka oracle menunjukkan sensitivitas mekanisme, bukan jaminan error itu bisa dipelajari dari sensor.
- “Tidak membantu dengan anchor hari pertama selama 15 hari” tidak menutup anchor yang dipakai dekat boundary lalu meluruh. `an40` memakai mean error **hari pertama holdout**, bukan menguji label RH terakhir sebelum origin.
- Simulasi coin-flip dan perkiraan SE public ±0,17 dalam log tidak boleh diperlakukan sebagai inferensi formal: fold berkorelasi dan mekanisme split belum diketahui. Kesamaan gain local/public bukan tes untuk membuktikan ada/tidaknya leakage.

## 3. Breakdown error yang masih tersisa

Berikut dari cache v16 + increment satu seed, **1.440 baris unik B1+B2**, bukan estimasi error test. Dua blok masing-masing 720 baris. Total SSE 44.147,126.

| Slice jam | n | RMSE | Persentase SSE, sekitar |
|---|---:|---:|---:|
| 00–05 | 360 | 6,862 | 38,40% |
| 06–11 | 360 | 4,746 | 18,37% |
| 12–17 | 360 | 4,633 | 17,50% |
| 18–23 | 360 | 5,617 | 25,73% |

Hari 5 Agustus sendiri menyumbang 7.032,807 SSE, sekitar **15,93%**, dari hanya 48 baris. Tiga hari terburuk, 5 Agustus, 28 Agustus, dan 7 Agustus, menyumbang sekitar **31,99% SSE**. Jangan mengubah model khusus tanggal-tanggal ini; cari kondisi sensor yang menjelaskan kegagalan lalu uji di hari lain.

Dalam cache yang sama, day-level sekitar 39,65% dan within-day 60,35% MSE. Jadi tidak benar bahwa “essentially all remaining headroom” ada di daily level. Keduanya besar. B2 RMSE 6,60114 dibanding B1 4,21193 juga menunjukkan ketergantungan pada episode.

Breakdown berikutnya harus memakai prediksi baru lima seed untuk semua kontrol:

- Jam × pemanasan/pendinginan; kondisi suhu sama dapat berasal dari fase berbeda.
- Kuantil |ΔT|, rentang T 48 jam, CO2/pressure tendency; ambang ditentukan pada train.
- Jarak dari origin: 0–6 jam, 6–24 jam, hari 2–3, 4–7, 8–15.
- Sensor missing/repaired dan jarak ke gap, dibanding baris normal.
- Untuk diagnostik saja: kuantil RH aktual dan perubahan RH aktual; jangan menjadi gating feature inference.
- Bias, RMSE, kontribusi SSE, daily mean, amplitude/phase, dan disagreement level–increment pada tiap slice. Selalu tampilkan jumlah hari, bukan hanya jumlah baris.

## 4. Yang sudah dicoba dan tidak perlu diulang begitu saja

| Keluarga | Bukti riwayat | Keputusan lanjutan |
|---|---|---|
| Lambda ×0,5/×2, tambah h2/h8 | §158 | Jangan sweep ulang global strength |
| Smoothed RH level | Menang screen, kalah pipeline CV meta in-sample | Ditunda; penolakannya belum merupakan bukti final, tetapi bukan prioritas pertama |
| Vapour-pressure increment langsung | §164, lima variasi mechanism | Jangan mengganti target RH dengan e lagi tanpa mekanisme berbeda |
| Per-row variance weights | §164 | Sudah dicoba; covariance antar-error adalah hipotesis berbeda |
| Capacity dan feature kitchen sink | §170–171 | Jangan menambah daftar fitur tanpa diagnosis |
| Linear leaf, CatBoost, ridge, ensemble increment | §174 | Same learner di kedua horizon sudah diuji; kombinasi horizon berbeda belum terlihat diuji |
| Raw/full/half deshrink | §176 | Sudah ada; uji transfernya, jangan menyebutnya ide baru |
| Recent-window training | Audit v20 dan eksperimen sebelumnya | Berbeda dari bagging episode; jangan mengulang cutoff semu |
| Global dispersion/offset | Berkali-kali gagal, termasuk public | Bukan default eksperimen berikutnya |

## 5. Pendekatan baru, menurut prioritas

### A. Kalibrasi dan kombinasi untuk loss setelah rekonsiliasi

**Pilihan utama setelah evaluasi dibereskan.** Ensemble di §174 menurunkan RMSE increment kedua horizon, tetapi menaikkan RMSE akhir +0,0241 mean tiga blok. Ini bukti bahwa objektif intermediate tidak cukup.

Untuk `A = I + Σ λ_h D_hᵀD_h`, error akhir sebelum clipping adalah:

`z − y = A⁻¹[(p − y) + Σ λ_h D_hᵀ(d_h − D_h y)]`.

Jadi frekuensi error, covariance antarincrement, serta covariance dengan error level ikut menentukan hasil. Mencocokkan dispersion saja mengabaikan struktur tersebut.

Eksperimen pertama cukup kecil: `d'_h = mean(d_h) + a_h(d_h − mean(d_h))`, dua parameter untuk h1/h4, dipasang pada inner forward predictions untuk meminimalkan SSE **hasil solve**, dengan penalti menuju `a_h=1` dan batas tetap [0,8; 1,2]. Penalti dipilih di inner split saja. Ini berbeda dari memaksa sd target dan berbeda dari mengubah lambda.

Selanjutnya satu hybrid yang ditentukan dari bukti §174: CatBoost untuk h1, LightGBM physics untuk h4, dengan solve tetap. Bandingkan dengan LGB/LGB dan ensemble lama; jangan mensyaratkan tiap horizon harus menang sendiri jika final objective menang. Simpan d1/d4 dan hitung inconsistency `d4 − sum(empat d1)` pada interval lengkap sebagai diagnostik.

Jika perlu tahap kedua, uji covariance error berdimensi kecil dengan shrinkage kuat, bukan matriks bebas sepanjang test. Prinsip memakai covariance dalam rekonsiliasi didukung [paper MinT](https://robjhyndman.com/papers/MinT.pdf). Adaptasi ke graf level/increment di sini adalah hipotesis baru; jaminan pada hierarchical forecasting tidak otomatis berlaku untuk kasus ini.

### B. Spline fisik dengan informasi lintasan suhu

Belum terlihat implementasi physical GAM/spline di log. Coba satu additive model berkapasitas kecil: spline T/es(T), CO2, pressure tendency, T minimum/range; harmonic jam; interaksi terpilih ΔT × fase pemanasan/pendinginan. Untuk increment, pakai residual terhadap komponen constant-vapour yang **menggunakan proxy RH**, sehingga tidak memasukkan target saat inference. Bandingkan satu model increment dahulu; model level baru hanya jika ada residual OOF komplementer.

Alasannya: tree piecewise-constant, ridge linear, dan spline nonlinear smooth memiliki bias berbeda. Model ini dapat menguji hysteresis tanpa ribuan parameter. Constant-vapour bukan hukum bahwa Δe=0; residual tetap dipelajari. Fitur spline dan scaling harus fit di train tiap origin. Implementasi dapat memakai [SplineTransformer](https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.SplineTransformer.html) + Ridge.

### C. Boundary anchor dari RH train terakhir

`diff_operator(idx,h)` pada inference hanya menghubungkan timestamp di dalam idx test. Edge dari label train terakhir menuju timestamp test pertama belum digunakan. Tambahkan edge lintas batas dengan endpoint train sebagai konstanta yang diketahui; predict increment tetap dari exogenous features.

Uji satu konfigurasi dengan lambda bawaan, tanpa tuning 15-day offset. Efeknya harus diukur per lead time dan seluruh horizon. Label sebelum origin sah; label hari pertama holdout dilarang. Jalur ini terutama berpotensi membantu awal horizon, jadi jangan mengharapkan perbaikan 0,166 dari sini saja. Boundary anchor memang boleh mengubah overall mean; jangan mempertahankan assertion mean-preserving untuk varian ini.

### D. Sequence kecil atau temporal block bagging

Jika A/B belum memberi sinyal: satu model sequence kecil dengan input exogenous 24 jam dan dua output increment h1/h4, parameter dibatasi, early stopping hanya inner. Bisa memakai convolution yang berbagi bobot antarwaktu. Target histories hanya boleh masuk jika tersedia juga pada setiap titik inference; default gunakan exogenous saja. Ini menguji struktur lintasan yang belum ditangkap fitur ringkasan.

Alternatif lebih murah: lima bagging sample berbasis blok kalender 3 hari, semua dari train sebelum origin. Catat hash dan jumlah timestamp unik tiap sample; duplikasi blok menjadi sample weights. Jangan menyambung blok acak lalu membangun ulang lag sehingga muncul tetangga waktu palsu. Hitung ensemble akhir dan covariance error, bukan hanya RMSE member. Keduanya prioritas setelah A/B karena data hanya sekitar dua bulan.

## 6. Rencana pelaksanaan yang bisa langsung diikuti

Nama file berikut **rencana**, belum dibuat. Jangan menjalankan perintahnya sebelum implementasi tersedia. Folder kerja tetap root repo; Python `.venv/Scripts/python.exe`.

### Tahap 0 — benahi kontrak evaluasi dan provenance

- [ ] Tambahkan `src/an46_v21_eval_audit.py`: audit pasangan tanggal, metric pooled, seed counts, dan hash artefak; perbaiki mapping di `src/an40_error_anatomy.py` dan penamaan metric di `src/an41_increment_oracle.py`.
- [ ] Buat `tests/test_v21_evaluation.py`: hasil invariant ketika urutan baris/blok diacak; pooled sesuai SSE langsung; timestamp unik; perubahan label outer tidak mengubah prediksi; endpoint increment training tidak menyentuh validation labels.
- [ ] Tambahkan `src/an47_v21_forward_benchmark.py`, dengan cache `outputs/audit_v21/forward_predictions.parquet` dan `manifest.json`. Manifest berisi hash CSV input/kode, batas train/horizon, feature columns, seluruh config termasuk strength, dan seeds.
- [ ] Bekukan B1/B2 untuk pooled utama dan B3 untuk sensitivity. B3 tidak dihitung sebagai tambahan hari independen. Semua kalender sudah terekspos; jangan menyebutnya holdout baru yang belum pernah dilihat.
- [ ] Rebuild fitur train dari grid yang berhenti di origin, fitur inference dari grid yang berhenti di akhir horizon; ulangi aturan ini untuk tiap inner fold, bukan memakai satu matriks outer untuk semuanya. Samakan dengan kebijakan produksi; setiap penyimpangan dicatat sebagai ablation.
- [ ] Pakai inner forward origins untuk bobot/calibration. Purge berdasarkan timestamp **kedua endpoint target**. Gap tambahan karena ketergantungan waktu adalah sensitivity terpisah; jangan mengira sembarang gap memperbaiki semua masalah preprocessing. [TimeSeriesSplit](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.TimeSeriesSplit.html) menjelaskan pemisahan waktu dan parameter gap.
- [ ] Inner meta dapat memakai horizon pendek karena sejarah terbatas, tetapi laporkan perbedaannya. “Sama untuk semua kandidat” tidak menjamin selisih skor tidak berubah akibat interaksi model.

Perintah verifikasi yang direncanakan:

```powershell
.venv/Scripts/python.exe -m unittest discover -s tests -p test_v21_evaluation.py
.venv/Scripts/python.exe src/an46_v21_eval_audit.py
.venv/Scripts/python.exe src/an47_v21_forward_benchmark.py
```

### Tahap 1 — nilai tiga kontrol dengan implementasi sama

- [ ] Bandingkan v21 asli, +physics, +physics+half-deshrink, lima increment seeds untuk semua; pertahankan seed convention member produksi agar perubahan lain tidak tercampur.
- [ ] Tambahkan satu ablation deshrink dengan factor forward-OOF menggantikan blocked OOF. Jangan men-tune strength pada B1/B2/B3 lagi.
- [ ] Simpan prediksi per timestamp, origin, model, d1, d4, dan factor. Hitung ulang semua breakdown §3. Pisahkan episode dengan overlapping tanggal pada laporan secondary.
- [ ] Jika physics/deshrink tidak stabil, lanjut eksperimen baru dari v21; jangan mewariskan tambahan yang belum lolos hanya karena sudah ada flagnya.

### Tahap 2 — dua challenger utama

- [ ] Implementasikan `src/an48_v21_solver_loss.py`: dua gain inner-fitted dan hybrid Cat-h1/LGB-h4. Maksimum dua mekanisme, tanpa grid besar. Semua parameter learnable berhenti sebelum outer origin.
- [ ] Implementasikan `src/an49_v21_physical_spline.py`: satu desain fitur dan regularisasi hanya dipilih inner. Simpan hasil akhir dan covariance dengan incumbent.
- [ ] Screen satu seed hanya untuk debug/biaya; keputusan akhir wajib refit lima seeds. Batasi total empat konfigurasi baru pada putaran ini. Jangan menjalankan seluruh daftar ide sekaligus.

### Tahap 3 — boundary dan eksperimen cadangan

- [ ] Implementasikan `src/an50_v21_boundary.py` dan test sparse solve terhadap solusi dense pada contoh kecil dengan endpoint train diketahui. Pastikan mengubah label setelah origin tidak memengaruhi hasil.
- [ ] Jika A/B gagal atau hanya menghasilkan gain sangat kecil, pilih **salah satu** sequence kecil atau block bagging, dengan config dibekukan sebelum melihat outer score.
- [ ] Gunakan breakdown episode untuk menjelaskan failure mode; jangan membuat rule kalender atau memilih seeds berdasarkan hari terburuk.

### Kriteria keputusan

Primary: paired pooled RMSE B1+B2, dilaporkan juga sebagai ΔMSE, dengan row set identik. Secondary: RMSE tiap blok, B3, SSE malam, lead-time slices, dan worst-day contribution. Laporkan paired bootstrap kalender 3/7 hari; interval itu conditional pada pencarian yang sudah dilakukan, bukan koreksi selection bias.

Sebagai aturan engineering yang dibekukan sekarang, kandidat layak dipromosikan untuk dipertimbangkan jika pooled membaik setidaknya 0,02 RMSE, B1 dan B2 sama-sama membaik, dan B3 tidak memburuk lebih dari 0,05. Angka ini bukan batas signifikansi atau prediksi LB. Jika interval bootstrap melintasi nol, tandai bukti lemah dan prioritaskan incumbent; jangan mencari split tambahan sampai menjadi signifikan. Jika tidak ada yang lolos, hasil yang benar adalah tidak ada kandidat baru.

Random subset 220 baris dari prediksi outer yang dibekukan boleh dipakai untuk sensitivitas skenario public acak, bukan untuk memilih model/seed berdasarkan subset terbaik. Private tidak dapat disimpulkan dari public saja.

### Tahap 4 — hanya setelah kandidat lolos

- [ ] Integrasikan satu mekanisme terbaik ke `final_pipeline.py`, default baseline tetap dapat direproduksi.
- [ ] Jalankan tests relevan dan selftest, buat artefak dengan config hash, periksa 734 baris, urutan datetime, nilai finite/range, dan hasil dua build identik.
- [ ] Laporkan jarak prediksi dari v21, perubahan mean/amplitude, dan efek per lead time. Jangan menimpa filename untuk config strength lain seperti insiden §179.
- [ ] Catat keputusan dan hasil di `progress.md`; buat paling banyak satu submission kandidat final. Pengiriman Kaggle bukan bagian dari dokumen ini.

## 7. Keputusan yang disarankan sekarang

Pertahankan file public v21 sebagai baseline. Physics dan half-deshrink tetap kandidat yang perlu konfirmasi bersih. Prioritas implementasi adalah **harness forward yang benar → loss akhir rekonsiliasi/hybrid per horizon → spline fisik**, dengan boundary anchor sebagai eksperimen kecil yang berbeda dari offset lama.

Ruang perbaikannya belum tertutup. Bukti terkuat bukan klaim bahwa oracle dapat dicapai, melainkan kegagalan intermediate RMSE memprediksi kualitas hasil akhir, kelemahan validasi kandidat terbaru, dan belum dicobanya beberapa representasi lintasan. Perbaikan skor berikutnya harus dibuktikan lewat eksperimen tersebut.

## 8. Jejak verifikasi audit ini

- Reproduksi bug tanggal menggunakan cache asli dan estimasi RidgeCV yang sama: 1.440 pasangan berbeda, 5.49433491 → 5.57769530 setelah alignment.
- Hitung SSE langsung B1+B2 untuk tabel pooled, error per jam, dan hari terburuk; tidak melatih ulang model produksi.
- Periksa `increment_model_screen.csv`, `increment_dispersion.csv`, `increment_oracle.csv`, serta kode seed defaults untuk membedakan hasil satu/lima seed.
- Baca kode pembanding `pf_i < pf_b` dan log `v24_phys_log.txt`/`v25_dsh_log.txt` untuk makna 9/9.
- Verifikasi MD5 ketiga submission. Skor 2.86595 berasal dari laporan pengguna, bukan akses ke label test atau pembacaan halaman submission privat.
