# Evaluasi setelah sesi 26 dan rencana improvements sesi 27

> Untuk pelaksana: gunakan skill `executing-plans` saat implementasi, kerjakan checklist secara berurutan. Dokumen ini adalah rancangan eksperimen, bukan laporan kandidat baru yang sudah menang.

**Goal:** menemukan peningkatan yang berbeda dari eksperimen §180–189, dengan kalibrasi yang benar-benar berada sebelum origin dan penilaian RMSE akhir pada tanggal yang sama.

**Architecture:** pertahankan v21 public dan physics+half-deshrink sebagai dua kontrol. Perbaiki cache kalibrasi sebelum memasang parameter baru. Setelah itu uji kontribusi model level setelah rekonsiliasi, temporal block bagging, dan satu representasi lintasan exogenous yang sederhana.

**Tech stack:** Python `.venv`, pandas/NumPy, SciPy sparse dan optimasi, LightGBM, scikit-learn. Semua path relatif di dokumen ini terhadap `C:/Users/Raphael Angelo/Code/Competitions/NSC UB`.

Audit ini membaca pembaruan `progress.md` §180–189 seluruhnya, menghubungkannya dengan riwayat yang sudah diaudit, memeriksa `an47`–`an51`, kode pipeline, tests, manifest, dan CSV hasil. Pemeriksaan cache dan perhitungan diagnostik dijalankan; tidak ada retraining atau perubahan produksi pada sesi penulisan ini. Rencana sebelumnya tetap menjadi catatan historis.

## 1. Apa yang sudah berubah sejak rencana sebelumnya

Public terakhir yang diketahui tetap **v21_increment_v16.csv = 2.86595**, menurut laporan pengguna. Tidak ada laporan public baru untuk physics/deshrink. Rekomendasi lokal terkini adalah `v21_increment_v16_phys_dsh.csv`, tetapi statusnya masih kandidat lokal.

| Konfigurasi | Pooled B1+B2 | B1 | B2 | B3 | Hasil sesi 26 |
|---|---:|---:|---:|---:|---|
| v21 public | 5.514359 | 4.192670 | 6.575548 | 4.736085 | Kontrol |
| +physics | 5.502920 | 4.185580 | 6.560882 | 4.734760 | Kecil, di bawah batas gain 0,02 |
| +physics+half-deshrink | **5.474126** | 4.159154 | 6.529437 | 4.768597 | Lolos batas sesi 26 |
| +physics+full-deshrink | 5.459406 | 4.154385 | 6.507790 | 4.830724 | Ditolak: B3 memburuk 0,09464 dari v21 |
| Half-deshrink + fitted gains | 5.470885 | 4.150616 | 6.529437 | 4.812309 | Gain tambahan hanya 0,00324 |
| Hybrid Cat-h1/LGB-h4 | 5.487650 | 4.165576 | 6.548021 | 4.764847 | Kalah |
| Hybrid + gains | 5.484122 | 4.156274 | 6.548021 | 4.809581 | Kalah |
| Physical spline | 5.634084 | 4.165952 | 6.791955 | 4.829161 | Kalah |
| Spline/LGB 50:50 | 5.525893 | 4.121918 | 6.639336 | 4.749782 | B1 menang, B2 kalah besar |

Boundary anchor juga sudah dicoba: pooled B1+B2 memburuk sekitar 0,00094. Gain awal horizon terutama berasal dari B3. Ini bukan prioritas untuk horizon 15 hari.

**Keputusan:** jangan mengulang hybrid, spline additive, anchor pendek, atau sweep gain global sebagai eksperimen utama. Physics+half-deshrink layak dipertahankan sebagai pembanding lokal. Namun belum ada alasan mengklaim semua learner, daily-level information, atau sensor preprocessing sudah habis.

## 2. Celah evaluasi yang masih ada: inner calibration belum label-isolated

### Temuan yang direproduksi

Di `src/an47_v21_forward_benchmark.py::build_block`, `prior` dipilih berdasarkan nomor fold:

```python
prior = O.loc[O.fold.isin(fids[:k])]
```

Fold inner berukuran 8 hari dengan langkah 2 hari. Akibatnya, prior fold berakhir **6 hari setelah origin fold yang sedang diprediksi**. Nomor fold yang lebih kecil tidak berarti seluruh labelnya berada sebelum origin sekarang.

Lebih jauh, untuk fold scored pertama ada pengecualian:

```python
if k == 1:
    cut = vs
```

Artinya seluruh 8 hari dihitung, termasuk 6 hari yang labelnya ikut fitting stack. Hasil audit timestamp langsung dari cache:

| Outer block | Inner scored rows | Bertumpang tindih dengan label prior meta | Porsi |
|---|---:|---:|---:|
| B1 | 960 | 288 | 30,00% |
| B2 | 480 | 288 | **60,00%** |
| B3 | 864 | 288 | 33,33% |
| Total entri kalibrasi | 2.304 | **864** | **37,50%** |

Ini jumlah entri per block, bukan 2.304 observasi kalender independen. Pada fold berikutnya tail dua hari tidak punya overlap label langsung, tetapi metanya tetap dipasang dengan label setelah origin. Rekonsiliasi juga menghubungkan seluruh lintasan; menghapus skor enam hari pertama saja tidak membuat prediksi yang sudah dibangun menjadi label-isolated.

**Implikasi yang tepat:** hasil pemilihan gains dan penjelasan bahwa “deshrink sudah mengambil semua gain” belum dapat dianggap tuntas. Namun hasil outer tiga kontrol tidak memakai kalibrasi gains tersebut: temuan ini tidak otomatis membatalkan pooled 5.474126 atau berarti test-label leakage. Jangan memakai bug ini sebagai alasan untuk membuka kembali puluhan konfigurasi.

### Yang harus diperbaiki sebelum kalibrasi baru

- Pilih meta rows dengan `dt <= inner_origin`, bukan nomor fold saja; pastikan model pembentuk OOF row juga dilatih sebelum timestamp prediksinya.
- Jika tidak ada meta rows yang sah, jangan memaksakan fold itu untuk belajar parameter. Gunakan fallback yang dibekukan: uniform member weights dan harmonic correction nol, lalu tandai provenance-nya; atau tidak gunakan fold itu untuk kalibrasi.
- Gunakan scored tail dua hari secara konsisten. Laporkan jumlah hari yang tersisa setelah semua guard; jangan mempertahankan 480 rows B2 dengan melonggarkan batas.
- Uji label perturbation pada **seluruh level-stack-calibration-reconciliation chain** di setiap inner origin. Tests sesi 26 memeriksa increment dan deshrink; belum menguji keseluruhan rantai ini.
- `choose_penalty` di `an48` memakai leave-one-inner-fold-out. Itu tidak membuka outer labels, tetapi bisa melatih pada periode lebih baru saat memilih penalti. Untuk klaim forward calibration, gunakan pemilihan chronological atau satu penalti tetap jika data tidak cukup.

## 3. Kontrak fitur, cache, dan deshrink perlu dibuat eksplisit

Audit kali ini mengecek bahwa MD5 `final_pipeline.py`, `an36`, `an47`, dan cache sesuai manifest yang tersimpan. Jadi temuan di atas berasal dari artefak yang cocok, bukan cache dengan versi kode berbeda.

Tetap ada tiga lubang implementasi:

1. **Load tidak menegakkan manifest.** `an47.main` membaca pickle yang tersedia tanpa membandingkan config/input/code hash. `--train-features-at-origin` tanpa `--rebuild` bisa memuat cache lama. Config harus menjadi bagian identitas cache dan diperiksa saat load.
2. **Ablation strict belum lengkap.** Dalam `build_block`, `F_train` dipakai untuk inner member fits, tetapi outer `member_preds` masih menerima F yang dibangun sampai akhir horizon. Flag itu belum mengubah training features outer seperti namanya. `member_preds` juga menerima satu matriks saja untuk training dan inference; interface harus memisahkan keduanya jika ingin menjalankan ablation tersebut.
3. **Deshrink forward-OOF dari rencana lama belum diuji.** `fit_increments` masih menggunakan blocked leave-chunk-out dengan train pada dua sisi validation chunk. Kedua endpoint target belum dipurge di split internal. Ini tidak menyentuh outer labels, tetapi faktor dispersion yang diperoleh dari interpolasi waktu belum tentu cocok untuk forecast.

Koreksi terhadap asumsi audit terdahulu: kode produksi saat ini memang memakai fitur joint train+test secara default; `strict_features` default false. Itu sah untuk exogenous yang tersedia. Jangan mengubahnya menjadi strict tanpa mencatat perubahan model. Untuk simulasi tiap inner forecast, batasi **akhir data exogenous pada akhir horizon inner tersebut**, bukan akhir outer yang jauh lebih baru. Bedakan fitur joint-window yang sah dengan fitur di luar simulated forecast horizon.

## 4. Apa yang sebenarnya dikatakan breakdown terbaru

### Bias cooling belum menjadi aturan yang dapat dipakai

§187 melaporkan bias cooling −1,36 dan warming +0,03. Tetapi dari `breakdown.csv`, setelah dibagi jam, untuk v21 public:

| Jam | Cooling: n / bias | Warming: n / bias |
|---|---|---|
| 00–05 | 246 / −1,3567 | 114 / **−1,8086** |
| 06–11 | 14 / −3,8289 | 346 / +0,1958 |
| 12–17 | 181 / −0,6089 | 179 / +0,5381 |
| 18–23 | 340 / −1,6559 | 20 / +3,0390 |

Pada dini hari warming justru lebih underpredict. Dua sel ekstrem hanya 14/20 baris. Cooling berasosiasi dengan jam; agregatnya belum memisahkan efek fase, jam, episode, dan magnitude ΔT. Karena itu **jangan langsung membuat offset positif saat cooling**.

### Bias menurut RH aktual bukan bukti cukup untuk ekspansi

Model conditional mean yang terkalibrasi pun dapat underpredict pada kelompok yang dipilih berdasarkan y aktual tinggi, karena noise positif ikut menentukan keanggotaan kelompok. Itu berbeda dari bias menurut prediksi atau fitur yang tersedia saat inference.

Sebelum calibration, hitung `E[y−pred | pred_bin]` dengan bin dari prediksi inner yang sah, serta residual phase setelah mengontrol harmonic jam. Lakukan pada inner saja dan cek transfer antarperiode. Target-tercile tetap diagnostik, bukan rule inference atau bukti bahwa 50,2% SSE dapat dihapus lewat ekspansi.

### Daily-level dan sensor-repair belum terbukti mustahil

“87,6% day-level share pada jam 00–05” berarti mean error per hari **di dalam slice enam jam itu**, bukan 87,6% error disebabkan offset yang konstan sepanjang 24 jam. `slice_stats` menghitung mean ulang setelah slicing. Kegagalan Ridge daily 24-jam tidak otomatis menutup model night-state atau low-frequency error.

Demikian juga, repaired rows RMSE 5,40 vs clean 5,56 tidak merupakan ablation cleaning. Perbaikan sensor memengaruhi rolling features pada baris tetangga. Tidak perlu menjadikan cleaning prioritas, tetapi sebut “belum ada bukti untuk mengubah cleaning”, bukan “hipotesis tertutup”.

## 5. Arah improvements berikutnya

### Prioritas 1 — optimalkan kontribusi level members setelah rekonsiliasi

Hampir semua eksperimen terakhir membekukan p, lalu mengganti d1/d4. Padahal:

`z = A⁻¹(p + b)`, dengan `A = I + Σ λ DᵀD` dan `b = Σ λ Dᵀd`.

Untuk incumbent p0 dan member pj, sensitivitas perubahan level adalah:

`u_j = A⁻¹(p_j − p0)`.

Ini membuka eksperimen berbeda dari `an48`: **ubah kontribusi model level**, bukan gain increment. Member yang kalah pada level mentah dapat membawa komponen residual yang berguna setelah operator A⁻¹. Bobot blend lama dipilih untuk level sebelum rekonsiliasi; belum terlihat fitting member contribution pada loss akhir di §180–189.

Rancangan konservatif: simpan seluruh member predictions, bentuk `pθ = (1−Σθj)p0 + Σθj pj`, dengan θj ≥ 0 dan Σθj ≤ 0,25. Fit θ pada inner yang sudah benar untuk SSE z, dengan penalti menuju nol. Batas 0,25 dibekukan, bukan disweep. p0 tetap membawa TOD dan harmonic incumbent. Tidak perlu membuangnya atau menambah intercept baru.

Gunakan paling banyak dua arah berdasarkan keluarga yang sudah ada: satu L2 tree dan satu linear/vapour-pressure member, dipilih menurut residual inner, bukan outer. Jika tidak ada manfaat inner antarepisode, θ=0 dan eksperimen berhenti. Fixed d dan fixed A membuat evaluasi murah; sparse basis harus sama dengan solve langsung, termasuk clipping akhir. Tidak boleh mengasumsikan affine identity sesudah clipping tanpa pemeriksaan.

### Prioritas 2 — temporal block bagging yang benar-benar mengubah data

Seed averaging sudah dicoba, recent cutoff sudah dicoba; keduanya bukan bootstrap episode. Coba satu konfigurasi: blok kalender 3 hari, sampling dengan replacement, lima bags, horizon dan learner tetap LightGBM physics. Semua bags berasal dari train sebelum origin. Endpoint increment dibangun sekali pada kalender asli; row weight mengikuti blok **later endpoint**. Jangan concatenate blok teracak lalu menghitung lag.

Setiap bag wajib memiliki hash sample weights, jumlah timestamp unik, proporsi baris berbobot nol, dan bobot setiap episode. Ini menguji sensitivitas terhadap dominasi episode. Fit baseline dengan total ensemble size yang sama agar gain tidak sekadar tambahan model. Mulai dari increment saja agar biaya terkendali; jangan sekaligus mengganti level bagging dan deshrink.

Jangan fit faktor deshrink baru pada outer; perlakukan faktor incumbent sebagai kontrol tetap pada screen pertama. Jika bagging membantu, konfirmasi faktor dengan forward OOF yang cocok dengan bagging pada tahap berikutnya.

### Prioritas 3 — distributed-lag linear model sebelum neural sequence

Sequence masih belum dicoba, tetapi langsung menambah neural network pada dua bulan data berisiko hanya menambah kapasitas. Gunakan satu baseline lintasan: causal exogenous lags pada 0, 1, 2, 4, 8, 16, 24, 48 half-hour steps untuk T, CO2, pressure, dan proxy RH. Tambahkan ΔT warming/cooling serta harmonic jam yang sudah dikenal; prediksi dua target ΔRH sekaligus dengan Ridge teratur.

Perbedaannya dari spline additive: model melihat beberapa titik lintasan yang sama-sama jauh dari waktu t, bukan hanya ringkasan dan satu selisih horizon. Scaling/regularisasi di inner chronological split; tidak membaca actual RH lag di test. Mask training mensyaratkan kedua endpoint target sah, dan missing lag ditangani dengan train-fitted imputer plus mask. Jangan menganggap target t−h tersedia hanya karena t−h juga berada dalam test.

Nilai sebagai correction/blend terhadap increment incumbent dengan kekuatan dipilih inner, bukan pengganti penuh secara otomatis. Jika residual lintasan tidak komplementer setelah solve, jangan lanjut TCN. Jika ada bukti transfer yang stabil, satu TCN kecil menjadi tahap berikutnya, bukan bagian putaran awal.

### Cadangan — phase-conditioned correction, hanya jika diagnostic gate lolos

Residualize cooling indicator terhadap harmonic jam pada inner, lalu fit satu koefisien koreksi dengan shrinkage menuju nol. Lakukan koreksi pada level sebelum solve agar operator final tetap diperhitungkan. Syarat: arah koefisien stabil pada chronological subperiods dan gain inner bukan seluruhnya dari sel kecil. Bila tanda berubah, tutup varian ini tanpa memeriksa outer. Ini bukan eksperimen prioritas di putaran sekarang.

## 6. Rencana eksekusi sesi 27

Semua nama skrip baru di bawah adalah rancangan, belum dibuat. Jangan menjalankan perintah skrip tersebut sebelum implementasi. Tidak perlu mengubah `final_pipeline.py` untuk audit awal.

### Tahap A — perbaikan evaluasi yang sempit

Files: tambah `src/an52_v21_inner_contract.py` dan `tests/test_v21_inner_contract.py`; perbaiki `src/an47_v21_forward_benchmark.py`; gunakan folder baru `outputs/audit_v21_s27/` agar cache lama tidak tertimpa.

- [ ] Tulis regression test overlap: pada origin i, assert seluruh `meta_label_timestamp <= origin_i`. Reproduksi kegagalan pemilihan berdasarkan fold-id.
- [ ] Tulis test mengubah label di `(origin_i, horizon_end_i]`: **seluruh** prediksi inner harus identik, termasuk stack, harmonic, factor, dan solve. Jangan hanya menguji `fit_increments`.
- [ ] Terapkan filter timestamp, hapus first-fold full-window exception, dan tandai fold tanpa kalibrasi cukup. Simpan fallback reason.
- [ ] Pisahkan training/inference feature matrices untuk ablation; default tetap joint-exogenous sampai akhir horizon masing-masing. Uji exogenous setelah horizon diubah: prediksi tidak berubah; exogenous di dalam horizon boleh memengaruhi hasil.
- [ ] Validasi manifest saat load; mismatch config/code/input harus error yang jelas atau rebuild ke namespace baru. Test flag strict tidak memakai cache joint dan outer training benar-benar memakai matrix yang diminta.
- [ ] Jalankan tests baru dan existing evaluation suite; simpan jumlah usable days per origin. Audit bukan alasan mengurangi standar agar jumlah rows tetap besar.

Perintah yang direncanakan:

```powershell
.venv/Scripts/python.exe -m unittest discover -s tests -p "test_v21*py"
.venv/Scripts/python.exe src/an52_v21_inner_contract.py
```

Hasil wajib: zero timestamp violations, zero prediction difference pada label-perturbation check, cache config mismatch ditolak. Jika B2 tidak punya cukup calibration data, gunakan θ=0 untuk model kalibrasi; jangan memakai B1 inner yang beririsan dengan B2 outer.

### Tahap B — controls dan satu diagnostic deshrink

Files: tambah `src/an53_v21_controls_forward_factor.py`; keluaran `controls.csv`, `factor_diagnostics.csv`, dan prediksi per row di folder s27.

- [ ] Rebuild tiga kontrol: v21, physics, physics+half-deshrink. Gunakan lima increment seeds, seed convention member sama dengan produksi. Catat jika angka bergeser setelah feature-horizon changes; semua kandidat dibandingkan pada harness yang sama.
- [ ] Tambahkan tepat satu varian factor forward OOF, clip [1; 1,5], strength 0,5. Purge kedua endpoint di tiap split; prediction ensemble untuk factor harus jelas seed count-nya. Jika forward history tidak cukup, factor=1 dan log fallback.
- [ ] Hitung calibration menurut prediction bins, jam×phase, dan kontribusi day/night dengan definisi eksplisit. Semua pemilihan parameter memakai inner.
- [ ] Jangan menerima varian hanya karena factor lebih dekat satu atau dispersion lebih dekat target. Nilai pooled z akhir.

### Tahap C — dua eksperimen pertama, maksimum dua mekanisme

Files: tambah `src/an54_v21_level_contributions.py` dan `src/an55_v21_block_bagging.py`.

- [ ] Cache member predictions dan increment terms per origin. Key wajib memuat block, scope, origin, timestamp, model, config hash.
- [ ] Untuk level contributions, bangun basis `A⁻¹(pj−p0)`. Test θ=0 sama dengan incumbent dan θ nonzero sama dengan direct solve. Pakai constraint dan dua arah seperti §5; regularisasi dipilih dari inner saja, dengan default θ=0 bila evidence tipis.
- [ ] Untuk block bagging, bangun lima sample-weight vectors dengan seed dibekukan `20260905 + bag_id`; verifikasi set bobot memang berbeda dan label sesudah origin tidak masuk.
- [ ] Score pooled B1+B2 dan B3, serta kontribusi harian/lead time. Jangan menggabungkan dua mekanisme jika masing-masing belum lolos.
- [ ] Satu screen biaya rendah boleh untuk menemukan bug, tetapi keputusan model memakai ensemble size yang disamakan. Ukur runtime satu fold dahulu; hentikan variasi tambahan setelah dua mekanisme ini selesai dinilai.

Perintah setelah implementasi:

```powershell
.venv/Scripts/python.exe src/an53_v21_controls_forward_factor.py
.venv/Scripts/python.exe src/an54_v21_level_contributions.py
.venv/Scripts/python.exe src/an55_v21_block_bagging.py
```

### Tahap D — sequence hanya jika dua arah awal tidak cukup

File rencana `src/an56_v21_distributed_lag.py`.

- [ ] Implementasikan satu lag design dan ridge two-output sebagaimana §5, dengan scaling/imputer di dalam training split.
- [ ] Test lag alignment melewati gap, target endpoints, serta inference tanpa target histories. Horizon h=4 berarti tepat dua jam, bukan empat baris setelah dropna.
- [ ] Pilih regularisasi dan blend coefficient melalui inner chronological validation; simpan zero-blend sebagai kontrol.
- [ ] Nilai final solve, bukan memilih karena increment RMSE saja. Neural sequence belum dijalankan kecuali baseline ini memberi bukti representasi lintasan berguna.

### Tahap E — keputusan dan provenance

- [ ] Pertahankan bar sesi 26: pooled gain ≥0,02 terhadap **kontrol lokal yang dinyatakan sebelum run**, B1/B2 keduanya membaik, B3 memburuk ≤0,05. Laporkan juga delta terhadap v21 public agar gain antarbaseline tidak tercampur.
- [ ] Laporkan paired calendar-block bootstrap 3 dan 7 hari, jumlah kelompok, delta RMSE/MSE, dan sensitivitas terhadap hari terburuk. Interval conditional tidak mengoreksi pencarian puluhan kandidat.
- [ ] Jangan menyebut porsi bootstrap draws sebagai probabilitas model menang di private. Jangan mengubah toleransi setelah melihat kandidat.
- [ ] Jika lolos, baru integrasikan satu perubahan, jalankan tests relevan/selftest, build dua kali dengan config hash, validasi 734 timestamp dan nilai finite. Filename dan statistik harus berasal dari artefak yang sama.
- [ ] Jika gagal, hasil sesi adalah tidak ada kandidat baru. Dokumentasikan keluarga yang benar-benar diuji; jangan memperluas kegagalan satu desain menjadi klaim information ceiling.

## 7. Batas kesimpulan dan urutan keputusan

Sesi 26 sudah mengurangi daftar ide secara nyata. Yang masih terbuka bukan mengulang spline atau hybrid dengan seed lain, melainkan **bagaimana level members berkontribusi setelah solve**, **bagaimana episode training memengaruhi increment**, dan **apakah lintasan multi-lag membawa informasi tambahan**.

Pengukuran harus didahulukan karena kalibrasi inner masih memiliki overlap label yang konkret. Perbaikan itu sendiri bukan janji peningkatan leaderboard; gunanya memilih kandidat dengan alasan yang dapat dipercaya. Public/private tetap belum diketahui pembagiannya, dan mengganti nama sesi atau preregister sekarang tidak membuat B1/B2 menjadi data baru.

Rekomendasi sekarang tetap: simpan v21 public sebagai incumbent terukur dan physics+half-deshrink sebagai kandidat lokal yang paling didukung. Rencana sesi 27 tidak memerlukan submission baru sebelum eksperimen selesai.

## 8. Verifikasi sesi penulisan

- Membaca seluruh tambahan §180–189 serta hasil controls/solver/spline/boundary/breakdown.
- Menghitung overlap inner dari cache asli dan origin generator: 288 baris per block, total 864/2.304; prior meta berakhir enam hari setelah inner origin.
- Memeriksa tabel jam×phase langsung dari `breakdown.csv`, termasuk sel 14/20 baris dan reversal pada 00–05.
- Memeriksa kode flag strict, pemuatan manifest, pemilihan penalty, dan test coverage.
- Memverifikasi code/cache hashes terhadap manifest. Tidak melatih model, mengubah pipeline, atau mengirim submission pada sesi ini.
