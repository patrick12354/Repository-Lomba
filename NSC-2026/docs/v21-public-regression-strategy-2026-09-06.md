# Public 2.93028: audit regresi dan strategi setelah sesi 28

**Kesimpulan:** paket `physics + deshrink + lags` kalah terhadap v21 pada public. Belum ada dasar untuk menganggap private akan menyelamatkannya. Bukti paling kuat menunjuk pada transfer koreksi yang bergantung episode dan ketidakjelasan kontribusi tiga komponen, bukan bug file yang sudah terbukti. Strategi berikutnya harus memisahkan komponen dan mengurangi ketergantungan increment pada level sensor yang bergeser.

**Goal:** mencari kandidat yang memperbaiki v21 public melalui mekanisme yang dapat diuji secara terpisah, bukan terus menambahkan komponen pada paket yang baru kalah.

**Architecture:** v21 tanpa physics/deshrink/lags menjadi anchor terukur. Harness sesi 27 tetap digunakan dengan prediksi per timestamp; B3 tetap sensitivity yang tidak menambah observasi independen. Eksperimen berikutnya berfokus pada ablation deshrink/lag dan increment dengan input perubahan relatif.

**Tech stack:** Python, pandas/NumPy, LightGBM, SciPy sparse; dataset resmi repo saja. Root: `C:/Users/Raphael Angelo/Code/Competitions/NSC UB`.

Audit ini membaca hasil terbaru `progress.md` sampai §205 dan menghitung ulang prediksi lokal/submission dengan `src/an63_v21_public_regression_audit.py`. Tidak ada training atau submission baru pada tahap audit ini. Skor Kaggle berasal dari laporan pengguna; label test tidak tersedia.

## 1. Fakta public dan identitas artefak

| File | Public | MD5 file lokal |
|---|---:|---|
| `v21_increment_v16.csv` | **2.86595** | `5396077ee744458aa8d21b2ea336f61a` |
| `v21_increment_v16_phys_dsh_lags.csv` | **2.93028** | `dbec78e8d3340cdcc52c19a189dea902` |

Regresi **+0,06433 RMSE**, atau **+0,372871 MSE / +4,54% MSE**. Kedua file lokal memiliki 734 timestamp yang sama, urutan cocok, dan angka finite. Log build, integrasi desain, dan production rescore mendukung bahwa kode yang dipromosikan konsisten secara lokal. Tanpa akses artefak yang diunggah di Kaggle, pemeriksaan ini tidak membuktikan byte unggahan identik; tidak ada indikasi lokal bahwa salah file merupakan penyebab.

Physics dan physics+deshrink belum memiliki skor public yang dilaporkan. Karena itu tidak sah menyebut **lag sendiri** menyebabkan +0,06433. Selisih public menguji tiga perubahan sekaligus terhadap v21.

## 2. Perubahan sebenarnya pada 734 prediksi test

| Tahap | RMS perubahan | SD sebelum → sesudah, ddof=0 | Maksimum perubahan |
|---|---:|---|---:|
| v21 → physics | 0.213096 | 18.8894 → 18.9140 | 1.372552 |
| physics → deshrink | **0.330935** | 18.9140 → **19.1951** | 0.870470 |
| deshrink → lags | 0.262021 | 19.1951 → **19.1104** | 0.969810 |
| v21 → paket lengkap | **0.419682** | 18.8894 → 19.1104 | 1.379529 |

RMS perubahan tidak dapat dijumlahkan karena arah koreksi berkorelasi. Mean seluruh test berubah sekitar 5e-16: tidak ada global offset baru dari paket ini. Namun mean per jam berubah:

| Jam | Mean perubahan lengkap dari v21 | RMS |
|---|---:|---:|
| 00–05 | +0.1564 | 0.4752 |
| 06–11 | −0.1632 | 0.3703 |
| 12–17 | −0.2531 | 0.3872 |
| 18–23 | +0.2569 | 0.4381 |

Paket mendorong malam naik dan siang turun. Itu berguna bila v21 terlalu kecil amplitudenya pada episode tersebut, dan bisa merugikan bila v21 sudah cukup lebar. Lag sendiri justru **mengurangi** ekspansi yang dibuat deshrink pada test. Maka saran langsung “tambahkan matched factor yang lebih besar” berisiko memperkuat mekanisme yang belum teridentifikasi manfaat public-nya.

## 3. Kegagalan transfer sudah tampak pada B3

| Tahap | ΔRMSE B1 | ΔRMSE B2 | ΔRMSE B3 |
|---|---:|---:|---:|
| v21 → physics | −0.006975 | −0.014756 | −0.000852 |
| physics → deshrink | −0.025502 | −0.031503 | **+0.029994** |
| deshrink → lags | −0.009698 | −0.035808 | **+0.004561** |
| v21 → lengkap | **−0.042176** | **−0.082067** | **+0.033703** |

Pada B3, sebagian besar kemunduran paket berasal dari tahap deshrink. Ini bukan pembuktian deshrink kalah pada test, tetapi bukti paling langsung bahwa koreksi dapat berubah arah manfaat antar-episode. B3 overlap blok utama; jangan menganggapnya fold independen, tetapi juga jangan mengabaikan pola kegagalannya hanya karena bukan primary.

Lag-only upgrade terhadap kontrol lokal lolos bar engineering dengan gain pooled 0,0250. Namun interval bootstrap ΔMSE 3 hari **[−0.6173,+0.0558]**, dan 7 hari **[−0.7026,+0.1091]**, masih melintasi nol. Setelah pencarian puluhan kandidat pada kalender yang sama, itu bukti kandidat, bukan kepastian generalisasi. Klaim §204 bahwa ini “informasi baru yang membantu” perlu dibatasi menjadi hasil pada holdout yang diuji.

Pada 29 Agustus, bagian hari terakhir B1 sebelum train berakhir, lag menambah MSE **+3,4783** terhadap physics+deshrink, meskipun 23/31 hari membaik. Hanya 30 baris pada hari itu dan fitur berada di ujung horizon, jadi tidak membuktikan seluruh test mengikuti episode yang sama. Ini menunjukkan win-count harian dapat menyembunyikan ukuran kekalahan; evaluasi harus menyertakan besar SSE dan efek boundary.

## 4. Apakah hanya kebetulan public split?

Dilakukan 20.000 simulasi sampel 220 baris acak tanpa pengembalian dari **masing-masing holdout 720 baris**. Seluruh prediksi dibekukan. Yang dibandingkan adalah v21 vs paket lengkap, persis pasangan public.

| Kalender simulasi | Persentil 2,5–97,5 ΔRMSE | Sampel yang paketnya kalah | Sampel dengan kenaikan ≥0,06433 |
|---|---|---:|---:|
| B1 | [−0.09769,+0.01077] | 5,98% | 0,005% |
| B2 | [−0.13040,−0.03345] | 0,045% | 0 dari 20.000 |
| B3 | [−0.01608,+0.08256] | **90,77%** | **10,84%** |

Ini **bukan probabilitas private menang** atau p-value untuk leaderboard. Simulasi mengondisikan pada label/episode lama yang sudah berkali-kali dipakai, ukuran horizon berbeda sedikit dari test, dan asumsi public random 220 belum dikonfirmasi. Nol kejadian bukan probabilitas sebenarnya nol.

Interpretasi yang sah: “public kebetulan sial” bukan penjelasan tunggal yang didukung B1/B2. Dengan struktur error seperti B3, pembalikan seperti public justru masuk rentang biasa. Prioritaskan investigasi transfer episode dan amplitudo, bukan berharap random split akan membalik hasil private.

## 5. Shift data yang terukur

Fitur dihitung sampai akhir horizon tiap fold; batas distribusi berasal dari train sebelum originnya.

| Slice | Mean T train → forecast | Mean pressure train → forecast | Pressure forecast di luar p01–p99 train |
|---|---|---|---:|
| B1 | 27.205 → 28.445 | 1008.848 → 1009.233 | 8,19% |
| B2 | 27.716 → 26.145 | 1009.284 → 1007.944 | 4,58% |
| B3 | 27.327 → 28.061 | 1008.006 → 1013.199 | 4,58% |
| Test | **27.509 → 24.641** | **1008.942 → 1013.203** | **14,99%** |

Test menggabungkan suhu lebih dingin dan pressure lebih tinggi. Coverage min–max pressure test di luar train 6,27%, dibanding 1,25–2,78% pada holdout ini. Tidak ada satu fold yang mereplikasi semua kondisi test sekaligus.

Lag pressure/CO2 absolut dapat membawa informasi episode selain dinamika. Ini hipotesis yang layak diuji, belum causal attribution. Pressure-removal pada **level members** sudah dicoba sebelumnya; itu tidak sama dengan membuat **increment input** invariant terhadap offset sensor. Jangan menghidupkan kembali seluruh no-pressure ensemble hanya berdasarkan tabel ini.

## 6. Private: jawaban yang bisa dipertanggungjawabkan

Private bisa lebih baik atau lebih buruk; **saat ini tidak diketahui**. Bila public/private merupakan sampel acak dari seluruh periode yang sama, keduanya berbagi risiko shift itu. Tidak ada alasan struktural menganggap masalah akan hilang pada private. Bila split kronologis, efek episode berbeda mungkin menghasilkan pembalikan, tetapi struktur split tidak pernah dikonfirmasi.

Secara aljabar, dengan bobot public 30%, kenaikan public MSE +0,372871 memerlukan ΔMSE private <−0,15980 untuk mengompensasinya pada seluruh test. Ini hanya kondisi aritmetis, bukan prediksi. RMSE private baseline v21 tidak diketahui sehingga tidak dapat dikonversi menjadi target RMSE private yang pasti.

Keputusan sekarang: **v21 public 2.86595 kembali menjadi pilihan utama berbasis hasil eksternal**. Simpan paket lags sebagai alternatif berisiko, bukan rekomendasi utama dengan janji private. Keputusan akhir tetap dapat mempertimbangkan jumlah slot final, tetapi jangan mengorbankan incumbent hanya karena alternatif CV-nya lebih rendah.

## 7. Kesalahan metode versus kesalahan kesimpulan

**Belum ditemukan bug baru yang terbukti menjelaskan skor public.** Row alignment dan schema cocok; production rescore mendukung implementasi; test sebelumnya membatasi target leakage. Tes itu tidak menguji generalisasi.

Kelemahan yang nyata:

- Membandingkan public paket tiga perubahan dengan v21 tanpa public intermediate membuat atribusi komponen tidak teridentifikasi.
- Rasio sd(actual)/sd(prediction) tetap bukan estimasi otomatis untuk amplitude conditional mean. OOF factor cocok dengan learner tidak menjamin expansion optimal pada test.
- Penolakan full deshrink pada B3 sudah memberi peringatan bahwa manfaat expansion bergantung episode. Versi setengah mengurangi risiko, tidak menghapusnya.
- Threshold gain 0,02 dan toleransi B3 0,05 adalah rule engineering. Ia memungkinkan kandidat dengan bukti lemah/berubah arah lolos, apalagi sesudah banyak pencarian.
- Winner dipilih pada training histories sekitar 31/46 hari; final fit sekitar 61 hari. Estimasi bias/variance yang diperoleh model dengan history pendek tidak otomatis sama dengan final model.
- Metode baru masih memuat seluruh F pada increment design. Banyak fitur level yang dapat mengidentifikasi kalender tetap ikut model perubahan.

Ada juga kekeliruan eksperimen sebelumnya yang sudah diperbaiki: overlap meta, salah pasangan tanggal, definisi pooled, seed count, mask lag, dan lead-time interpretation. Jangan menyalahkan ulang bug historis yang tidak berada pada jalur artefak saat ini. Jangan juga menyimpulkan semua masalah telah selesai hanya karena test suite hijau.

## 8. Strategi baru yang paling layak diuji

### A. Isolasi lag tanpa memaksakan deshrink

**Prioritas pertama.** Selesaikan tabel 2×2 lag/deshrink dengan physics tetap:

| | Tanpa lag | Dengan lag |
|---|---|---|
| Tanpa deshrink | Physics, sudah ada | **Physics+lag, belum diuji sebagai arm terpisah** |
| Half deshrink | Physics+dsh, sudah ada | Paket yang mendapat 2.93028 |

Tambahkan satu ablation v21+lag **tanpa physics dan tanpa deshrink**. Ini menguji apakah manfaat trajectory dapat berdiri sendiri. Dua arm baru, flags lainnya tidak berubah; bukan grid strength.

Bandingkan incremental effect terhadap parent masing-masing **dan** terhadap v21. Jika lag hanya membantu sesudah expansion dan merugikan B3, jangan menyebutnya sinyal yang transferable. Tidak perlu mengirim semua arm ke Kaggle untuk mengidentifikasi label atau split; keputusan utama tetap dari forward evaluation.

### B. Increment dengan input perubahan relatif, bukan raw levels

**Mekanisme baru yang paling sesuai diagnosis shift.** Pertahankan prediksi level p dari v21. Ganti hanya increment model dengan desain ringkas yang tidak memuat seluruh F:

- Current T, es(T) ratio antarendpoint, harmonic jam.
- ΔT pada 1/2/4/8/16/24/48 langkah.
- Untuk pressure dan CO2: `x(t)-x(t-k)`, causal rolling range/std, bukan level absolut atau lag absolut.
- Proxy RH level untuk skala termodinamika, dengan lag dinyatakan sebagai perubahan terhadap nilai saat ini.

Tetapkan LightGBM yang sama, lima seeds, h1/h4 dan lambda sama. Mulai **tanpa deshrink** agar penyebab gain tidak bercampur. Ini bukan menghapus pressure dari level model: p tidak berubah, informasi pressure dynamics tetap ada di d.

Tes invariance yang bermakna: menambahkan konstanta +c ke seluruh pressure history tidak boleh mengubah increment design/prediction; begitu juga offset CO2 bila seluruh fitur CO2 hanya selisih/range/std. Tes ini membuktikan properti desain terhadap nuisance offsets, bukan bahwa shift sesungguhnya hanya offset.

Jika tidak mengalahkan v21 di beberapa episode, jangan menambahkan calibration untuk menyembunyikan kekalahan. Cara ini layak karena mengubah induktif bias yang berbeda dari banyak eksperimen kapasitas/seed yang sudah gagal.

### C. Validasi transfer yang lebih informatif

Pertahankan B1/B2 pooled sebagai laporan historis. Tambahkan **diagnostik** rolling holdout 7 hari dengan history lebih panjang untuk menguji mendekati final training size, dan laporkan lead bands pada 15-day holdouts. Jangan menyebut fold baru sebagai data baru atau mengganti primary diam-diam.

Untuk setiap kandidat tampilkan gain vs v21, vs parent, ΔMSE per episode, loss pada tails terburuk, dan gerakan prediksi di test menurut kondisi exogenous. Jarak prediksi kecil bukan bukti benar; gerakan besar di wilayah input unsupported adalah alasan meminta bukti tambahan.

Gunakan tahap ini untuk membedakan kegagalan history length, edge-of-horizon features, dan pergeseran sensor. Jangan memilih panjang history setelah melihat fold mana yang menang.

## 9. Rencana kerja terbatas

> Gunakan `executing-plans` bila meneruskan implementasi. Nama file di bawah masih rancangan; `an63` audit di atas sudah dijalankan.

- [ ] **Ablation:** buat `src/an64_v21_lag_without_expansion.py`, dua arm saja: physics+lags tanpa dsh; v21+lags tanpa physics/dsh. Refit melalui production `fit_increments`/`reconcile`, parent control wajib identik. Simpan predictions, d1/d4, config hash, actual endpoint masks, dan factors yang dinonaktifkan.
- [ ] **Relative dynamics:** buat `src/an65_v21_relative_dynamics.py` dan `tests/test_v21_relative_dynamics.py`. Freeze fitur sebagaimana §8B, alpha/hyperparameters sama; test additive-offset invariance, target-blindness, chronological endpoints, dan exact timestamp lag sebelum training.
- [ ] **Stress:** buat `src/an66_v21_transfer_report.py`. Cache 7-day holdouts dengan horizon-truncated features dan meta labels sebelum origin; bandingkan kandidat dan v21 pada row set sama. Report terpisah dari primary B1/B2.
- [ ] **Batas pencarian:** tiga arm baru maksimum. Jangan menambahkan matched factor, night-state relaxation, atau alpha sweep pada putaran yang sama.
- [ ] **Decision:** tetap laporkan bar historis; setelah public failure, kelulusan bar itu saja tidak cukup untuk menyebut kandidat lebih aman daripada v21. Tampilkan apakah B3 dan stress mendukung atau bertentangan, serta semua interval yang melintasi nol. Bila bukti konflik, incumbent tetap pilihan utama.
- [ ] **Provenance:** setiap statistik berasal dari file/config yang sama. Tidak ada public probing atau rekonstruksi split. Bila nanti kandidat dipilih untuk submission, satu kandidat final yang jelas, bukan seri bobot interpolasi untuk membaca leaderboard.

Strategi ini meningkatkan kualitas hipotesis dan peluang menemukan perbaikan yang transferable, tetapi data yang tersedia tidak mendukung klaim probabilitas tinggi mencapai skor tertentu. Langkah paling defensible sekarang adalah mempertahankan v21, menguji trajectory tanpa expansion, lalu menguji relative dynamics sebagai perubahan bias model yang berbeda.

## 10. Artefak audit yang tersedia

`outputs/audit_v21_public_regression/` berisi `public_audit.json`, `submission_moves.csv`,
`submission_move_slices.csv`, `stage_holdouts.csv`, `stage_daily.csv`, `feature_support.csv`.
Log eksekusi: `outputs/public_regression_audit.log`. Simulasi seed 20260906, 20.000 draws per
holdout; bukan hasil test/private. Skrip `an63` membaca prediksi dan data resmi untuk analisis,
tidak mengubah model/submission.
