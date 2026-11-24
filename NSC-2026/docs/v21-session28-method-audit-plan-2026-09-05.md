# Audit metode setelah sesi 27 dan rencana improvements sesi 28

> Untuk pelaksana: gunakan skill `executing-plans`, jalankan checklist berurutan. Semua eksperimen yang diusulkan di sini belum dijalankan; angka diagnostik berasal dari artefak sesi 27 yang dihitung ulang pada sesi audit ini.

**Goal:** menguji apakah representasi lintasan dan estimasi keadaan kelembapan malam dapat meningkatkan RMSE akhir, setelah memisahkan kelemahan metode, pemilihan parameter, dan keterbatasan validasi.

**Architecture:** bekukan dua kontrol—v21 public dan physics+half-deshrink—pada harness sesi 27. Gunakan satu kontrak seleksi yang menilai seluruh pipeline setelah rekonsiliasi. Prioritaskan eksperimen terkontrol yang membedakan fitur lag, learner, dan kalibrasi; model night-state menjadi mekanisme kedua yang berbeda.

**Tech stack:** Python `.venv`, pandas/NumPy, LightGBM, scikit-learn, SciPy sparse. Root repo: `C:/Users/Raphael Angelo/Code/Competitions/NSC UB`.

## 1. Kesimpulan audit

**Masih ada celah yang masuk akal, dan beberapa kesimpulan “sudah tertutup” dalam log terlalu luas.** Tetapi skor tim lain yang lebih baik tidak menentukan metode mana yang salah atau menjamin setiap ide berikutnya akan meningkatkan skor kita. Itu alasan untuk terus menguji representasi dan prosedur yang berbeda, bukan alasan mengendurkan validasi.

Rencana sesi 28 paling layak adalah:

1. Perbaiki seleksi distributed-lag agar memilih berdasarkan RMSE hasil solve, dengan seed dan factor yang sesuai kandidat.
2. Pisahkan efek **informasi lag** dari efek **mengganti LightGBM menjadi Ridge**. LightGBM dengan tambahan lag belum diuji oleh eksperimen Ridge distributed-lag.
3. Uji satu model keadaan malam dengan target fisik vapor pressure rata-rata malam. Itu berbeda dari daily RH offset yang sudah gagal.

Tidak ada model baru dilatih, pipeline diubah, atau submission dikirim pada sesi audit ini. Dokumen membaca pembaruan `progress.md` §190–198 seluruhnya, kode utama `an47`, `an53`, `an54`, `an56`, serta cache prediksi dan hasil sesi 27. Riwayat sebelum itu mengacu pada audit sebelumnya dan dicocokkan pada mekanisme yang relevan.

## 2. Fakta yang tidak boleh tertukar

Public terakhir yang diketahui tetap **`v21_increment_v16.csv`: 2.86595**, menurut pengguna. `v21_increment_v16_phys_dsh.csv` masih kandidat lokal; tidak ada skor public baru yang diketahui untuk file itu.

| Konfigurasi pada harness sesi 27 | Pooled B1+B2 | Δ dari kontrol lokal | Status |
|---|---:|---:|---|
| v21 public | 5.535894 | +0.039933 | Kontrol eksternal yang sudah mendapat skor |
| Physics+half-deshrink | **5.495961** | 0 | Kontrol lokal |
| Forward factor | **5.481378** | −0.014583 | B1/B2 menang, di bawah batas 0,02 |
| Distributed-lag Ridge blend | 5.500387 | +0.004426 | B1/B3 menang, B2 kalah |
| Level contributions | 5.505798 | +0.009836 | B1 kalah; B2 identik karena fallback |
| Block bagging | 5.514244 | +0.018283 | B1 menang, B2/B3 kalah |

Physics/deshrink tetap memberi manfaat lokal setelah perbaikan harness. Temuan audit berikut tidak berarti hasil itu bocor dari label test. Jangan memakai baseline sesi 26 untuk menilai kandidat sesi 27/28.

Ke 2,7 dari 2.86595 perlu sekitar **11,25% penurunan MSE**. Tidak ada konversi pasti dari gain CV ke leaderboard. Pembagian public/private belum diketahui; near/far kronologis bukan public/private. Private pesaing juga tidak diketahui.

## 3. Kesalahan eksperimen dan interpretasi yang ditemukan

### 3.1 Tail dua hari bukan lead dua hari

§193/197 menyimpulkan inner mengukur “2-day leads” lalu gagal pada 15 hari. Audit langsung `forward_predictions.pkl` memberikan:

| Block | Inner scored rows | Minimum lead | Maximum lead |
|---|---:|---:|---:|
| B1 | 576 | **144,5 jam** | **192 jam** |
| B2 | 96 | **144,5 jam** | **192 jam** |
| B3 | 480 | **144,5 jam** | **192 jam** |

Itu hari ke-7–8 dari forecast berukuran 8 hari. Lebar slice adalah dua hari; jaraknya dari origin enam sampai delapan hari. Perbedaan horizon tetap ada terhadap outer 15 hari, tetapi kegagalan theta pada B1 tidak membuktikan short-lead → long-lead reversal yang dinyatakan log. Perubahan panjang training, kalender, meta weights, dan distribusi episode juga berubah bersamaan.

Perbaikan: simpan dan laporkan `lead_hours` dari timestamp, jangan menurunkannya dari ukuran scored slice. Primary tetap horizon 15 hari; inner evaluation perlu menunjukkan bagian lead mana yang dicakup.

### 3.2 B2 punya 96 baris karena rancangan harness; bukan batas informasi universal

96 baris memang benar untuk konfigurasi sekarang. Namun jumlah itu bergantung pada inner windows 8 hari, step 2 hari, minimum training, minimum meta 192 rows/4 hari, penolakan fallback folds, dan aturan score-tail. Itu bukan bukti bahwa semua parameter tidak mungkin dipelajari secara jujur dari train sebelum 30 Juli.

Ada beda antara **memasang dua parameter meta tanpa cukup validasi transfer** dan **melatih model target langsung dari seluruh train**. Forward factor dan distributed-lag sudah melakukan yang kedua dengan split internal yang sah terhadap outer origin. Keduanya dapat bergerak pada B2. Jadi klaim “seluruh keluarga inner-fitted calibration structurally unable” harus dipersempit menjadi konfigurasi/gate yang digunakan `an54`.

Jangan menurunkan minimum rows setelah melihat hasil. Sebaliknya, pilih mekanisme yang tidak memerlukan meta calibration bertingkat pada B2, atau rancangan validation yang dibekukan sebelum kandidat dijalankan. Kalender baru hasil pembagian ulang tetap bukan data independen baru.

### 3.3 Distributed-lag dipilih dengan objektif yang tidak sama dengan tujuan akhir

`src/an56_v21_distributed_lag.py::select_alpha_and_blend` memilih minimum:

```python
mse = np.mean((mix - truth) ** 2)
```

Itu MSE mentah dari dua target increment, bukan RMSE z setelah rekonsiliasi. Evaluasi outer memang memakai z, tetapi pemilihan alpha/blend tidak. Hal ini sudah berkali-kali diketahui bermasalah sejak §174; bukan sekadar kandidat baru yang “ternyata tidak transfer”.

Tambahan ketidakcocokan:

- Seleksi memakai LightGBM **satu seed**, sedangkan inference rata-rata lima seed. Bobot campuran dapat dipilih untuk meredam noise satu model yang berkurang pada ensemble akhir.
- Seleksi belum menerapkan factor deshrink yang nanti dipakai. Saat inference, factor dipasang dari LightGBM saja ke vector campuran LGB+Ridge.
- MSE dua horizon dijumlah mentah. Error h4 yang lebih besar cenderung mendominasi, padahal final solve memakai operator dan lambda berbeda.
- Multi-output Ridge dengan alpha bersama bukan pembelajaran struktur temporal bersama yang kaya: untuk squared-error Ridge, koefisien tiap target tetap dapat diestimasi terpisah. Menghasilkan dua kolom tidak otomatis belajar konsistensi d4 dengan empat d1.
- Angka gain 3–15% adalah score minimum pada window yang **dipakai memilih** alpha dan blend, dari beberapa pasangan kandidat. Itu bukti eksploratif, bukan gain out-of-selection yang sudah dikonfirmasi.

Konsekuensi: representasi lag belum diuji dengan prosedur seleksi yang cocok dengan pipeline. Namun tidak otomatis benar bahwa factor yang cocok akan menyelamatkannya.

### 3.4 Ada bug kecil pada target mask distributed-lag

`lag_mask` memperbarui m lalu menggeser m yang sudah diperbarui:

```python
m = mask.reindex(index, fill_value=False)
for h in horizons:
    m = m & m.shift(h, fill_value=False)
```

Untuk h=(1,4), ini mensyaratkan timestamp t, t−1, t−4 **dan t−5**. t−5 bukan endpoint kedua target. Reproduksi grid sintetis 20 half-hours dengan satu label missing menghasilkan dua exclusion tambahan dibanding mask yang benar, termasuk exclusion dekat gap.

Implementasi yang direncanakan:

```python
base = mask.reindex(index, fill_value=False)
m = base.copy()
for h in horizons:
    m &= base.shift(h, fill_value=False)
return m
```

Ini over-exclusion, bukan leakage; tidak ada bukti ia menjelaskan seluruh gap skor. Perbaiki karena kontrak target salah, bukan karena berharap satu baris tambahan memberi lonjakan leaderboard.

### 3.5 Diagnosis “Ridge memberi path lebih datar” hanya berlaku pada B2

Diambil langsung dari prediksi outer yang tersedia:

| Block | SD path kontrol | SD path lag blend | Perubahan |
|---|---:|---:|---|
| B1 | 17,4107 | **17,5399** | Melebar |
| B2 | 16,4183 | **16,2764** | Menyempit |
| B3 | 17,6736 | **17,7080** | Melebar |

Dispersion memang bagian masalah, tetapi pola ini tidak membuktikan satu global amplitude fix akan memperbaiki semua episode. Lebih informatif adalah dekomposisi paired MSE.

Definisikan e=prediksi kontrol−y dan u=prediksi kandidat−prediksi kontrol. Identitas tepat:

`ΔMSE = 2 mean(e*u) + mean(u²)`.

| Kandidat | Block | 2 mean(e*u) | mean(u²) | ΔMSE |
|---|---|---:|---:|---:|
| Distributed lag | B1 | −0.845376 | 0.265337 | −0.580039 |
| Distributed lag | B2 | **+0.389067** | 0.288318 | **+0.677386** |
| Distributed lag | B3 | −0.397078 | 0.072528 | −0.324550 |
| Block bagging | B2 | **+0.567941** | 0.193628 | +0.761569 |
| Forward factor | B2 | **−0.329728** | 0.048695 | −0.281033 |
| Forward factor | B3 | **+0.201436** | 0.033348 | +0.234784 |

Pada B2 arah perubahan lag sudah salah terhadap residual kontrol, bukan hanya terlalu besar. Untuk prediksi **tetap yang sama**, setiap positive blend weight a memberi `2a mean(e*u)+a²mean(u²)>0`. Jadi sekadar mengecilkan campuran prediksi akhir lag tidak bisa menyelamatkan B2. Factor yang mengubah d1/d4 dapat mengubah arah u, sehingga masih bisa diuji, tetapi itu hipotesis baru.

Semua dekomposisi ini memakai outer labels untuk diagnosis, bukan untuk memilih bobot submission atau membuat aturan khusus B2.

## 4. Ruang perbaikan yang benar-benar masih terbuka

### A. LightGBM dengan representasi lag: pisahkan fitur dari learner

Sesi 27 mengubah fitur **dan** learner menjadi Ridge sekaligus. Tidak ada ablation yang menjawab apakah tree nonlinear dengan lintasan yang sama lebih baik. Menyebut multi-lag sudah dicoba seluruhnya karena Ridge blend kalah terlalu luas.

Eksperimen utama: pertahankan LGB physics, hyperparameters, seeds, h1/h4, lambda, dan estimator factor kontrol. Tambahkan fitur `lag_design` yang belum ada, deduplicate nama/kolom identik. Tidak ada tambahan capacity tuning. Ini membedakan representasi dari perubahan learner.

Bandingkan LGB physics vs LGB physics+lags. Laporkan increment RMSE, z RMSE, paired direction term di atas, dan pola malam/episode. Jika kalah, baru simpulkan “lag design ini belum membantu LGB ini”, bukan semua sequence tak berguna. TCN belum prioritas.

### B. Estimasi factor untuk pipeline campuran yang benar-benar digunakan

Revisit distributed-lag hanya sekali dengan alasan prosedural yang eksplisit. Tetapkan Ridge alpha/blend melalui inner selection **atas hasil solve**, dengan ensemble seed count sama. Setelah alpha/blend ditetapkan, estimasi factor dari forward predictions **campuran tersebut**, bukan LightGBM saja.

Jangan memilih alpha/blend dan mengklaim skor pada window pemilihan itu sebagai konfirmasi. Gunakan split bertingkat di dalam train jika cukup; jika tidak cukup, bekukan satu alpha dan blend sebelum outer run dan laporkan bahwa ini fixed-design experiment. Prioritas bukan memperbesar grid.

Konfigurasi fixed fallback untuk putaran ini: alpha=100 dan blend=0,25, dipilih sebagai regularisasi konservatif sebelum eksperimen baru, bukan sebagai optimum dari outer. Harus dibandingkan dengan campuran yang sama memakai factor lama; dengan demikian efek factor bisa dipisahkan. Jangan membandingkan hanya dengan hasil lama yang alpha/blend-nya berbeda antarorigin.

Factor tetap clip [1;1,5], strength 0,5. Gunakan lima-seed ensemble untuk forward LGB prediction. Target yang dipakai untuk factor adalah increment RH actual pada train-forward windows; jangan memakai distribusi y test atau standard deviation outer.

### C. Night-state: model fisik rendah dimensi, bukan daily RH bias ulang

§196 mengukur bahwa constant 24-hour offset hanya menjelaskan sekitar 24–38% error malam, sedangkan mean per-night menjelaskan lebih banyak. Ini membuka model target lain, tetapi belum membuktikan prediktabilitasnya.

Model yang diusulkan: prediksi **rata-rata actual vapor pressure per malam**, bukan residual seluruh hari. Definisikan malam 18:00–06:00, ditandai tanggal mulai. Dari training labels:

`e_t = RH_t * es(T_t) / 100`, `s_n = mean(e_t untuk malam n)`.

Gunakan malam yang seluruh label targetnya selesai sebelum training origin, serta fitur exogenous dari malam tersebut: T minimum/range, mean CO2, perubahan CO2, pressure tendency, dan proxy vapor pressure dari minimum T. Enam fitur, Ridge alpha tetap 100 setelah scaling. Model direct target ini tidak memerlukan 96-row residual-meta set B2. Effective sample size tetap jumlah malam, bukan jumlah half-hours.

Target inference dari exogenous malam boleh memakai semua sensor yang tersedia dalam forecast horizon. Untuk malam parsial di ujung horizon, jangan mengarang statistik full-night: tidak pasang constraint pada malam itu dalam eksperimen pertama.

Tambahkan satu constraint per malam ke solve:

`μ ||M_n z − s_hat_n||²`, dengan koefisien `M_n[t]=es(T_t)/(100*n_n)` untuk t pada malam tersebut.

Normalisasikan row M dan target dengan norma row yang sama agar μ tidak memiliki skala sewenang-wenang karena unit hPa vs %RH. Tetapkan μ=0,25, tanpa sweep; μ=0 adalah kontrol. Ini dapat mengubah level malam serta mean total, sehingga assertion mean-preserving milik increment-only tidak berlaku.

Bedanya dari smooth-level §158: target vapor pressure per malam, jumlah observasi efektif diakui, model kecil, dan operator mengikuti termodinamika. Tetap mungkin gagal karena sinyal kelembapan tidak ada pada enam fitur itu. Uji target predictability secara forward terhadap proxy fisik dan mean historis sebelum outer reconciliation. Bila tidak mengalahkan keduanya secara konsisten, hentikan.

## 5. Rencana implementasi sesi 28

Output baru di `outputs/audit_v21_s28/`. Cache s27 dibaca immutable setelah hash check. Nama skrip berikut rencana, belum dibuat. Jangan melakukan full rebuild model level hanya karena kode reporting berubah; pisahkan build-path fingerprint dari reporting fingerprint dengan manifest tetap lengkap.

### Tahap 0 — kunci diagnosis, bukan audit tak berujung

Files: tambah `src/an58_v21_method_contract.py`, `tests/test_v21_method_contract.py`; perbaiki `lag_mask` di `src/an56_v21_distributed_lag.py` saat implementasi.

- [ ] Test lead dihitung dari datetime−origin: cache inner sekarang memiliki interval 144,5–192 jam. Pisahkan `score_window_hours` dan `lead_hours` di metadata.
- [ ] Test mask dengan satu missing label dan h=(1,4): persyaratan tepat t, t−1, t−4. Tulis failing regression test sebelum memperbaiki mask.
- [ ] Test pemilihan kandidat menerima callable evaluator hasil solve, bukan hardcoded raw increment MSE. Sertakan contoh dua kandidat yang urutan raw-loss dan final-loss-nya berlawanan.
- [ ] Test seed count dan factor provenance identik antara candidate-selection predictions dan inference config.
- [ ] Simpan dekomposisi ΔMSE dan pred_sd yang dihitung pada audit ini. Jangan memperlakukan oracle blend weights sebagai parameter yang boleh digunakan.

Perintah setelah implementasi:

```powershell
.venv/Scripts/python.exe -m unittest discover -s tests -p "test_v21_method_contract.py"
.venv/Scripts/python.exe src/an58_v21_method_contract.py
```

Hasil yang diharapkan: endpoint mask tepat, identitas ΔMSE sesuai direct SSE, lead bukan salah label dua hari. Tidak perlu melatih ulang seluruh eksperimen yang tidak memakai mask atau selector yang berubah.

### Tahap 1 — kontrak split untuk satu putaran model

Files: tambah `src/an59_v21_candidate_contract.py`.

- [ ] Setiap record berisi origin, horizon_end, training_rows hash, candidate config hash, member seed list, factor training origins, dan prediction timestamps.
- [ ] Pertahankan outer B1/B2/B3. Candidate fitting tidak membaca outer labels; exogenous matrix berhenti di akhir horizon simulasi masing-masing.
- [ ] Untuk selector, evaluasi full window internal, laporkan lead 0–2/2–6/6–8 hari bila tersedia. Tidak perlu hanya mempertahankan tail untuk fitting per-origin; overlap harus diberi bobot/deduplicate saat pelaporan, bukan dianggap observasi independen.
- [ ] Jika hanya satu usable internal window, jangan melakukan nested search yang berpura-pura tervalidasi. Gunakan fixed config fallback yang disebutkan di §4 dan labeli hasilnya dengan jelas.
- [ ] Reproduksi kontrol lokal pada outer sebelum membandingkan kandidat. Simpan row-wise prediction dan d1/d4 agar diagnosis tidak memerlukan retraining berikutnya.

### Tahap 2 — eksperimen representasi dan factor

Files: tambah `src/an60_v21_lag_factor_ablation.py`.

- [ ] Jalankan LGB physics+lags dengan estimator factor kontrol, melawan LGB physics kontrol. Hyperparameters dan seeds sama.
- [ ] Jalankan fixed Ridge/LGB blend alpha=100, w=0,25 dengan factor LGB lama, lalu **blend yang sama** dengan forward factor milik campuran. Dua arm ini wajib berpasangan.
- [ ] Seleksi berbasis solve yang lebih adaptif hanya dijalankan bila data internal cukup; perlakukan sebagai kandidat lain dalam putaran berikutnya, bukan tambahan grid tersembunyi sekarang.
- [ ] Untuk factor forward: latih dari label sebelum split, rebuild exogenous horizon yang sesuai, prediksi campuran lima-seed LGB dan deterministic Ridge, kumpulkan OOF vector, hitung rasio sd lalu clip dan half-strength. Jika factor tidak dapat diestimasi, gunakan 1 dan catat fallback.
- [ ] Laporkan raw increment RMSE sebagai diagnostik, paired final RMSE sebagai primary, serta `2 mean(e*u)` dan `mean(u²)` per block. Jangan mengklaim amplitude sudah menjelaskan kegagalan tanpa data vector.

### Tahap 3 — satu night-state candidate

Files: tambah `src/an61_v21_night_state.py`, `tests/test_v21_night_state.py`.

- [ ] Implementasikan group malam 18:00–06:00 dengan tepat 24 half-hours pada malam lengkap; pastikan midnight tidak mengganti group di tengah malam.
- [ ] Test target malam yang melewati origin ditolak, input inference target-blind, dan malam parsial tidak diberi full-night constraint.
- [ ] Fit scaler/Ridge hanya pada training nights. Laporkan jumlah malam per origin dan forward error terhadap dua baseline target: proxy fisik dan mean train.
- [ ] Jika gate predictability gagal, jangan jalankan outer variant. Jika lolos, tambahkan normalized M dengan μ=0,25 dan bandingkan μ=0. Test solve sparse vs dense kecil.
- [ ] Laporkan perubahan mean seluruh horizon, mean malam, error siang, dan worst-night SSE. Mekanisme harus membantu malam tanpa sekadar memindahkan error ke siang.

Perintah yang direncanakan:

```powershell
.venv/Scripts/python.exe src/an60_v21_lag_factor_ablation.py
.venv/Scripts/python.exe -m unittest discover -s tests -p "test_v21_night_state.py"
.venv/Scripts/python.exe src/an61_v21_night_state.py
```

### Tahap 4 — keputusan

- [ ] Maksimum **empat arm baru**: LGB+lags, fixed Ridge blend+factor lama, fixed Ridge blend+matched factor, night-state. Controls tidak dihitung sebagai challenger. Tidak mengubah konfigurasi setelah melihat outer result.
- [ ] Primary tetap SSE-pooled B1+B2 pada row set identik. Laporkan delta terhadap kontrol lokal serta v21 public secara terpisah.
- [ ] Pertahankan bar lama untuk promosi sesi ini: gain ≥0,02, B1/B2 membaik, B3 memburuk ≤0,05. Jangan turunkan menjadi 0,014 agar forward factor lama tiba-tiba lolos.
- [ ] Forward factor lama boleh disimpan sebagai komponen dengan sinyal kecil, bukan sebagai “metode salah”. Tidak lolos bar engineering bukan bukti bahwa expected gain nol.
- [ ] Bootstrap kalender 3/7 hari tetap conditional pada pencarian sebelumnya. Jangan melaporkan jumlah fold/seed sebagai jumlah pengulangan independen.
- [ ] Jika hanya satu blok menang, laporkan failure direction. Jangan membentuk gating rule B1/B2/B3 atau menimbang ensemble dari oracle outer weights.
- [ ] Jika kandidat lolos, baru integrasikan, selftest, validasi file 734 baris, build ulang dua kali, dan hash config/file/statistik. Jika tidak ada yang lolos, tidak ada submission baru.

## 6. Yang tidak perlu dikejar pada putaran ini

Tidak mengulang global lambda sweep, hybrid learner per horizon, additive spline yang sama, boundary anchor pendek, block bagging yang sama, atau phase offset. Fase sudah diuji dengan harmonic control dan tidak memberi dasar cukup untuk koreksi sederhana.

Tidak langsung melatih TCN besar. Belum ada ablation LGB+lag yang memisahkan manfaat fitur dari Ridge shrinkage; itu lebih murah dan lebih mudah dibaca hasilnya. Tidak menambahkan external data atau mencoba merekonstruksi public split dari leaderboard.

Tetap kritis terhadap narasi information ceiling. Kegagalan satu keluarga bukan bukti optimum global. Sebaliknya, oracle true increments bukan bukti bahwa sensor yang tersedia mampu mencapai oracle tersebut. Skor pesaing memberi target kompetitif, bukan sertifikat bahwa kandidat kita berikutnya pasti menang.

## 7. Bukti audit ini dan batasnya

- Lead time dihitung ulang dari cache s27: seluruh inner scored rows berada pada 144,5–192 jam.
- Target-mask bug direproduksi dengan contoh kecil yang membandingkan endpoint mask eksplisit.
- ΔMSE directional decomposition dan SD prediksi dihitung dari `preds_distributed_lag.pkl`, `preds_block_bagged.pkl`, `preds_v21_physics_forward_factor.pkl`, serta `preds_v21_physics_deshrink_half.pkl`, memakai join one-to-one per block/timestamp dan scope outer.
- Selector alpha/blend, seed satu vs lima, serta factor estimator yang dipakai campuran diperiksa pada kode `an56` dan `an53`.
- Angka tabel leaderboard adalah laporan pengguna; angka benchmark adalah artefak lokal. Tidak ada skor public baru, perbaikan production code, atau hasil training baru yang diklaim dalam dokumen ini.
