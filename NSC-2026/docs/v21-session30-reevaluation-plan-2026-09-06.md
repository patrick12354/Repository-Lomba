# V21 session 30: evaluasi ulang dan rencana eksperimen

> **For agentic workers:** Gunakan skill `executing-plans` untuk mengerjakan rencana ini secara berurutan. Checklist membedakan audit yang sudah dijalankan dari eksperimen yang belum dijalankan.

**Goal:** Menemukan perbaikan terhadap v21 public 2.86595 yang bertahan lintas episode, dengan memisahkan kegagalan representasi, kalibrasi, dan perubahan komposisi evaluasi.

**Architecture:** Pertahankan prediksi v21 sebagai kontrol. Gunakan cache berprovenance untuk audit tanggal yang sama; kemudian jalankan ablation sensor yang sempit dan satu keluarga koreksi level berkapasitas kecil. Setiap perubahan dinilai pada RH setelah rekonsiliasi dengan isolasi label berdasarkan timestamp.

**Tech Stack:** Python di `.venv`, pandas, NumPy, SciPy sparse, scikit-learn, LightGBM; harness `an47`, kontrak `an59`, artefak `an64`–`an66`.

Dokumen ini membaca progress sampai §213 dan menambahkan audit baru, bukan mengklaim sudah melatih kandidat baru. Skor tim lain 2.6 berasal dari informasi pengguna; metode mereka dan skor private tidak diketahui. Dari 2.86595 ke 2.6 diperlukan penurunan MSE **17.698%**. Keuntungan lokal kecil pada increment belum cukup untuk memproyeksikan lompatan itu.

## 1. Apa yang berhasil dan gagal

| Metode | Bukti yang bertahan | Batas kesimpulan / keputusan |
|---|---|---|
| v21 increment asli | Public 2.86595; kontrol yang konsisten dan dapat direproduksi | Tetap kandidat banked. |
| Physics + de-shrink + lag | Pooled 15 hari membaik 0.064938; public justru 2.93028 | Paket gagal transfer pada public. Belum bisa membebankan seluruh kerugian kepada satu komponen. |
| Lag tanpa physics/de-shrink | Pooled 15 hari membaik 0.026025, B1/B2/B3 membaik | Sinyalnya kecil dan sangat tergantung episode; bukan otomatis gagal karena histori final lebih panjang. |
| Physics + lag tanpa de-shrink | Pooled 15 hari membaik 0.036612; 7 hari membaik 0.007799 | Masih layak menjadi pembanding, belum cukup bukti untuk menggantikan banked. |
| De-shrink | Membantu beberapa episode, memperburuk B3; paket dengan de-shrink kalah pada protokol 7 hari | Nonaktifkan pada eksperimen baru agar arah koreksi dapat diatribusikan. |
| Relative dynamics 57 fitur | B3 membaik 0.086713, tetapi B2 memburuk 0.099072 | Kegagalan desain gabungan ini tidak menutup hipotesis tekanan absolut; banyak fitur termal turut hilang. |
| Night-state, physical spline, Cat-h1 hybrid, block bagging, solver gain, daily residual terdahulu | Kandidat spesifik gagal pada gate masing-masing | Jangan diulang tanpa perubahan yang jelas dan pembanding yang tepat. |

MLP, kernel ridge, target dewpoint/vapour pressure, smooth-level constraint, penggantian learner increment, dan recent-window juga sudah dicoba. Menamainya kembali bukan pendekatan baru. Hasil lama yang memakai meta-validation bocor tidak boleh dicampur sebagai bukti setara dengan evaluasi yang sudah diperbaiki (§145 dan audit sesudahnya).

## 2. Temuan baru: sebagian besar “collapse” lag adalah komposisi kalender

Audit baru `src/an67_v21_calendar_audit.py` menggunakan prediksi tersimpan, tanpa refit:

1. Ambil B1+B2 saja: 1.440 timestamp unik, bukan B3 yang overlap.
2. Batasi prediksi 15 hari tersebut ke 1.008 timestamp yang juga dinilai protokol 7 hari.
3. Bandingkan terhadap prediksi 7 hari pada timestamp dan label identik.

Angka berikut adalah **ΔMSE terhadap v21 pada populasi masing-masing**, negatif lebih baik:

| Kandidat | 15 hari, seluruh 1.440 | Prediksi 15 hari, kalender sama 1.008 | Prediksi 7 hari, kalender sama 1.008 |
|---|---:|---:|---:|
| physics_dsh | -0.440533 | -0.242027 | +0.039074 |
| physics_dsh_lags | -0.714767 | -0.239176 | +0.019251 |
| physics_lags | -0.404024 | -0.092526 | -0.071273 |
| v21_lags | -0.287467 | -0.048113 | -0.026089 |
| relative_dynamics | +0.610226 | -0.170668 | +0.020501 |

Untuk `v21_lags`, perubahan komposisi kalender menjelaskan secara aritmetis **91.6%** penyusutan keuntungan ΔMSE antara kolom pertama dan ketiga. Untuk `physics_lags`, **93.6%**. Ini dekomposisi deskriptif dengan urutan standardisasi di atas, bukan estimasi kausal atau probabilitas transfer.

Protokol 7 hari menghilangkan **432 baris pada 30 Juli 15:00–8 Agustus 14:30**. Pada baris yang hilang itu, ΔMSE `v21_lags` = **-0.845960**, `physics_lags` = **-1.130852**, tetapi relative dynamics = **+2.432311**. Relative dynamics justru membaik -0.170668 pada kalender yang dipertahankan jika tetap memakai prediksi 15 hari. Tanggal 5–7 Agustus termasuk sumber kerugian besarnya; ini bahan error analysis, bukan tanggal untuk membuat aturan koreksi.

Karena itu §211–213 terlalu cepat mengarahkan penyebab ke history/horizon. Setelah kalender sama, masih ada perbedaan origin, histori training, lead, feature horizon, dan fitted model. Audit ini belum memisahkan kelimanya. Namun, **membangun ulang seluruh harness sebelum mencoba mekanisme lain bukan konsekuensi wajib dari hasil tersebut**.

Semua kandidat baru tetap lebih buruk pada H1 terbaru. Itu stress signal yang perlu dihormati, tetapi bukan bukti bahwa kandidat pasti memburuk pada histori 61 hari. Protokol 7 hari memakai kalender yang sudah pernah dianalisis, sehingga bukan konfirmasi dari data independen baru.

## 3. Temuan baru: ruang perbaikan level masih besar, tetapi belum terbukti dapat diprediksi

Untuk residual e, pisahkan mean residual per kalender-hari **di dalam masing-masing origin**:

    mean(e²) = mean(mean_day(e)²) + mean((e - mean_day(e))²)

| Protokol | Prediksi | MSE total | MSE bias harian | MSE dalam hari |
|---|---|---:|---:|---:|
| 15 hari | Level sebelum reconcile | 32.188058 | 12.265641 | 19.922417 |
| 15 hari | V21 sesudah reconcile | 30.646121 | 12.243698 | 18.402423 |
| 7 hari | Level sebelum reconcile | 21.971550 | 8.834576 | 13.136974 |
| 7 hari | V21 sesudah reconcile | 20.915239 | 8.777872 | 12.137367 |

Bias harian menyumbang **39.95% / 41.97%** MSE v21. Rekonsiliasi sekarang terutama mengurangi error dalam hari. Ini konsisten dengan operator perbedaan yang tidak memiliki informasi konstanta: sebelum clipping, jika hanya memakai term increment, `D 1 = 0` membuat jumlah z sama dengan jumlah p pada setiap komponen graf yang terhubung. Mean per hari tidak harus persis terjaga karena ada edge antarhari.

Pengurangan mean residual harian menggunakan label adalah **oracle diagnostic**, bukan kandidat submission. Angka 40% tidak berarti 40% MSE dapat dipulihkan. Namun, angka itu memberi alasan konkret untuk membatasi putaran increment berikutnya dan membuka kembali satu metode level yang berbeda dari daily Ridge lama.

## 4. Kesalahan dan klaim yang harus diperbaiki

**Endpoint physical feature tidak konsisten.** `final_pipeline.py` menggunakan `rh_tmin48.shift(h) * (ratio - 1)`, sedangkan `an65.rel_design` menggunakan proxy saat t dengan pengali yang sama. Untuk `ratio = es(T[t-h])/es(T[t])`, identitas constant-vapour adalah:

    ΔRH = RH[t-h] * (ratio - 1)
        = RH[t] * (1 - 1/ratio)

Desain relative memakai kombinasi kedua endpoint yang berbeda dari identitas tersebut. Itu **bukan label leakage dan bukan kesalahan target**, tetapi eksperimen tidak mempertahankan physical feature parent seperti yang diklaim. Karena hanya fitur proxy, memperbaikinya belum tentu memperbaiki skor. Buat arm terpisah; jangan mengubah artefak lama diam-diam.

**Ablation relative terlalu luas.** Hilangnya banyak fitur temperatur, statistik multiskala, dan konteks lain terjadi bersamaan dengan pembuangan pressure/CO₂ absolut. Menggunakan hyperparameter sama tidak menjamin kapasitas efektif sama; `colsample_bytree=0.8` juga beroperasi atas jumlah dan komposisi kolom berbeda. Kalahnya arm 57 fitur tidak mengisolasi peran tekanan.

**Histori final tidak bisa direplikasi persis.** Dengan sekitar 61 hari label, kita tidak bisa membuat validasi forward independen dengan 61 hari training ditambah 15 hari target. `TimeSeriesSplit` tidak menciptakan label tambahan. Solusinya mengukur sensitivitas pada histori yang tersedia dan menyatakan batas extrapolasinya, bukan menjanjikan harness yang “match final” secara persis.

**Manifest harus divalidasi ketika dibaca.** `an66.main` memuat cache jika file ada, tanpa memeriksa manifest. Audit ini sudah memverifikasi hash cache aktual `bd55dc3b06edf9d5e92811e33f50eac4` cocok dengan manifest. Jadi bukan bukti angka sekarang salah, tetapi loader belum fail-closed terhadap perubahan di masa depan. Sebelum menggunakan ulang untuk training, cocokkan juga input dan fingerprint fungsi yang relevan.

**Pencarian berulang belum mendapat data baru.** Bootstrap kalender mengukur variasi bersyarat pada kandidat yang sudah dipilih; ia tidak membatalkan selection bias dari puluhan eksperimen. Prinsip ini dibahas oleh [Cawley & Talbot, JMLR 2010](https://www.jmlr.org/papers/v11/cawley10a.html). Tetapkan keluarga dan aturan berhenti sebelum membuka hasil berikutnya.

## 5. Urutan eksperimen yang disarankan

### P0 — selesai: audit kalender; berikutnya satu kontrol endpoint

**Sudah dibuat:** `src/an67_v21_calendar_audit.py`, output `outputs/audit_v21_s30/{matched_calendar,calendar_exclusion,residual_energy}.csv` dan `provenance.json`.

- [x] Verifikasi hash cache 7 hari, keunikan timestamp, kesamaan label antarprotokol, dan identitas dekomposisi MSE.
- [x] Hitung tiga kolom kalender di atas tanpa refit.
- [ ] Buat `src/an68_v21_relative_endpoint.py` yang memakai semua kode an65 dan hanya mengganti physical feature ke endpoint sebelumnya; nama arm `relative_prev_endpoint`.
- [ ] Tambahkan `tests/test_v21_relative_endpoint.py` dengan fixture constant-vapour. Test inti berikut sengaja menguji identitas, bukan menyalin hasil model:

```python
import numpy as np
import unittest

class EndpointTest(unittest.TestCase):
    def test_constant_vapour_endpoints(self):
        es = np.array([20., 25., 30., 24., 22.])
        rh = 1200. / es
        ratio = es[:-1] / es[1:]
        actual = np.diff(rh)
        np.testing.assert_allclose(rh[:-1] * (ratio - 1), actual)
        np.testing.assert_allclose(rh[1:] * (1 - 1 / ratio), actual)
        self.assertFalse(np.allclose(rh[1:] * (ratio - 1), actual))
```

Perubahan fitur yang dimaksud, di salinan arm baru:

```python
X = a65.rel_design(F, h)
ratio = F['esT'].shift(h) / F['esT']
X['dRH_const_e'] = F['rh_tmin48'].shift(h) * (ratio - 1.0)
```

Jalankan `.venv/Scripts/python.exe -m unittest discover -s tests -p test_v21_relative_endpoint.py`, lalu arm melalui `a47.score_config` dengan builder/term-builder seperti an65. Bekukan seeds dan h=(1,4). Reproduksi relative lama sebelum membaca delta baru. Perbaikan ini kontrol metodologi, bukan prioritas submission. Gunakan unittest seperti suite repo; pytest tidak terpasang di virtualenv saat audit ini.

### P1 — prioritas pertama: ablation sensor yang mempertahankan fitur termal

**Files baru:** `src/an69_v21_sensor_ablation.py`, `tests/test_v21_sensor_ablation.py`; output `outputs/audit_v21_s30/sensor_*`. Gunakan parent **v21 tanpa physics, de-shrink, dan lag tambahan** agar satu perubahan dapat dibaca.

- [ ] Catat semua kolom desain parent dan dependency sumbernya. Tandai kolom yang berubah ketika pressure saja diberi offset, lalu CO₂ saja diberi offset, dengan seluruh feature engineering dibangun ulang pada prefix fold yang sama. Jangan hanya memodifikasi kolom mentah setelah turunan dibuat.
- [ ] Gunakan sensitivitas offset untuk menyusun whitelist fitur invariant; inspeksi dan bekukan daftar sebelum fitting. Kriteria numerik: `np.allclose(a,b, rtol=1e-9, atol=1e-6, equal_nan=True)`. Offset diagnostik +25 hPa dan +60 ppm, bukan augmentasi target. Laporkan fitur campuran yang ikut hilang, misalnya CO₂×T.
- [ ] Tiga arm saja: buang turunan pressure absolut; buang turunan CO₂ absolut; buang keduanya. Pertahankan seluruh fitur thermal/soil/time yang tidak bergantung pada sensor yang diablasi dan semua dinamika invariant yang sudah dimiliki parent.
- [ ] Test: offset tidak mengubah desain arm; arm pressure mempertahankan kolom CO₂ parent; arm CO₂ mempertahankan pressure; semua kolom termal yang tidak tergantung dua sensor identik; tidak ada target/lag target; perturbasi label setelah origin tidak mengubah prediksi.
- [ ] Jalankan B1/B2/B3 dan H1/H2/H3, serta tabel kalender-sama. Target evaluasi tetap `recon`, bukan hanya akurasi increment.
- [ ] Jika satu arm memberi arah perbaikan yang stabil, lakukan satu pembanding kapasitas: parent dan arm tersebut sama-sama memakai `colsample_bytree=1.0`. Ini diagnosis sensitivitas feature subsampling, bukan grid tuning.

Perbedaan dari eksperimen terdahulu: an65 mengurangi keseluruhan desain menjadi 57 fitur; ini membuang satu keluarga sumber informasi sambil mempertahankan konteks lain. Eksperimen no-pressure pada level member juga bukan pengganti ablation di increment ini. Tidak perlu asumsi bahwa pressure menyebabkan public loss untuk menguji hipotesis tersebut.

**Stop:** Jika tiga arm kalah pada 15 hari dan kalender-sama, tutup ablation ini tanpa sweep offset, fitur, atau threshold regime. Jika hanya menang B3/H2, catat sebagai episode-specific; jangan membuat gate berdasarkan nama blok.

### P2 — prioritas kedua, potensi lebih besar: koreksi level dari perbedaan member yang lambat

**Files baru:** `src/an70_v21_slow_member_correction.py`, `tests/test_v21_slow_member_correction.py`; output `outputs/audit_v21_s30/slow_member_*`.

Hipotesis: ketika model thermal-linear dan tree berbeda pada level yang bertahan berjam-jam, perbedaan itu mungkin mengandung arah bias, bukan sekadar ketidakpastian. Model harus membuktikan bisa memprediksi **tanda dan besar residual**. Disagreement saja tidak cukup.

Ini bukan menambahkan daily-mean RH predictor lagi, bukan target-space learner baru, dan bukan sekadar memilih bobot TOD. Model koreksi terbatas pada variasi lambat dari prediksi member existing, lalu koefisien dioptimalkan terhadap RH setelah solve. Keluarga smooth-level dan daily Ridge lama tetap pembanding kegagalan yang harus disebutkan.

Spesifikasi awal dibekukan:

1. Dari prediksi member OOF, buat lima contrast `m_j - level` untuk hbt, cat, ridge, enet, ridge_e. L2 dikeluarkan pada putaran pertama karena hampir duplikat tree; tidak dipilih ulang dari outer.
2. Haluskan setiap contrast dengan rolling mean 49 titik (24 jam span), centered, **di dalam forecast window masing-masing**, min_periods=1. Timestamp harus direindex pada grid 30 menit; jangan melintasi origin atau memakai label. Ini tersedia saat seluruh exogenous test diketahui.
3. Untuk setiap contrast lambat b_j, hitung `u_j = A^-1 b_j` dengan operator v21 yang sama. Koreksi akhir sebelum clip adalah `z_new = z_v21 + U beta`.
4. Fit ridge tanpa intercept pada residual OOF `y - z_v21`. Standardisasi U memakai meta-training saja; alpha grid dibekukan `{10,100,1000}` dengan pemilihan forward di dalam training origin. Kandidat nol ikut seleksi dan menang jika tidak ada gain forward. Tidak ada positive-only constraint karena contrast perlu dapat mengoreksi kedua arah.
5. Koefisien setiap outer origin hanya memakai label dan prediksi OOF yang seluruh proses pembuatannya mendahului origin tersebut. Satu timestamp satu prediksi kalibrasi; pilih forecast eligible terbaru. Regenerasi OOF penuh jika cache tidak menyediakan z_v21 yang jujur; jangan menggunakan residual training in-sample.
6. Minimum tiga chunk kalibrasi kronologis dengan sedikitnya 96 timestamp unik per chunk. Jika tidak cukup, gunakan beta=0 pada origin itu, laporkan fallback, dan jangan menafsirkan fallback sebagai kegagalan prediktor. Ini batas data desain, bukan alasan memasukkan label masa depan.

Aljabar inti, sesudah A, B, z dan mask meta-training tersedia:

```python
from scipy.sparse.linalg import spsolve
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge

U = spsolve(A, B)  # B: lima contrast lambat, shape (n, 5)
model = make_pipeline(StandardScaler(with_mean=False), Ridge(alpha=100., fit_intercept=False))
model.fit(U[train_mask], (y - z)[train_mask])
# Pada forecast baru: gunakan A/B/z milik forecast itu dan model yang sudah dibekukan.
correction = model.predict(U_forecast)
prediction = np.clip(z_forecast + correction, 5, 100)
```

Angka alpha=100 di snippet adalah satu anggota grid, bukan pemilihan setelah melihat outer. Scaling tidak mengurangi mean agar koreksi tetap berbentuk U beta tanpa intercept implisit. `U_forecast = spsolve(A_forecast, B_forecast)` dibentuk dari prediksi forecast, tidak dari residualnya. Training menggunakan z sebelum clipping agar kesetaraan linear tepat; scoring memakai clipping produksi. Jika artefak hanya menyimpan clipped z, rekonstruksi preclip dari term solver dan verifikasi reproduksi clipped control.

- [ ] Implementasikan pembentukan contrast per forecast dan simpan kolom, seed, origin, timestamp kalibrasi, alpha, koefisien, dan fallback.
- [ ] Test zero correction mereproduksi v21; kesetaraan `solve(A,rhs+B@beta)` dengan `z+solve(A,B)@beta`; tidak ada rolling lintas origin; kolom konstan/NaN ditangani dengan fallback yang tercatat; perubahan label heldout tidak mengubah koefisien/prediksi.
- [ ] Jalankan inner chronological selection, lalu outer sekali. Laporkan total MSE, komponen bias harian, within-day MSE, dan energi gerakan prediksi. Jangan hanya melaporkan daily-bias yang membaik jika total memburuk.
- [ ] Jika tanda koreksi tidak stabil antar-chunk atau kandidat nol menang, hentikan keluarga ini. Jangan mengganti ke random cross-fitting agar lebih banyak residual terlihat.

**Risiko:** Kalibrasi OOF lebih pendek daripada final, effective sample size dekat jumlah episode daripada jumlah baris, dan contrast mungkin tidak membawa informasi tambahan. Lima basis membuat eksperimen murah dan terbatas; bukan jaminan gain. B2 dapat fallback jika kalibrasi jujur terlalu sedikit. Hasil fallback wajib dipisahkan dari kemenangan model aktif agar pooled tidak menyamarkan jangkauan implementasi.

### P3 — hanya jika masih ada masalah tujuan pembelajaran: learner yang dilatih melalui solve

Cadangkan setelah P1/P2, bukan dijalankan bersamaan dengan banyak varian. `an48` hanya mengoptimalkan dua gain global setelah increment learner selesai; itu belum sama dengan melatih fungsi increment untuk loss RH hasil solve.

Untuk `z = A^-1(p + sum_h lambda_h D_h.T d_h)` dan `L = ||z-y||²/n`, gradien terhadap prediksi d_h:

    grad_dh = 2 * lambda_h * D_h @ solve(A.T, z-y) / n

Proposal lanjutan adalah residual learner kecil dengan gradien ini pada training sequences yang memiliki level OOF, bukan mengganti seluruh sistem menjadi Transformer. Sebelum fitting, wajib finite-difference gradient test, origin isolation, serta kontrol zero-update. Hessian antartimestamp tidak diagonal; jangan menyerahkan gradien ini ke LightGBM seolah loss row-independent tanpa membuktikan aproksimasinya. Dokumen implementasi khusus dibutuhkan jika P3 dipilih. Belum ada estimasi gain dan belum ada model P3 dalam sesi ini.

## 6. Evaluasi, anggaran pencarian, dan keputusan

- **Primary tetap 15 hari B1+B2** dengan pooled SSE/N. B3 stress overlap. Semua hasil menyertakan 7 hari dan kalender-sama; jangan mengganti primary setelah melihat arm menang.
- **Putaran awal dibatasi** satu kontrol endpoint, tiga sensor ablation, satu keluarga slow-member. Tidak menambahkan neural architecture, gain grid, dan night gate relaxation pada putaran yang sama.
- **Syarat promosi internal dibekukan:** gain pooled 15 hari minimal 0.02 RMSE; B1/B2 tidak memburuk; B3 memburuk maksimal 0.05; pooled 7 hari dan kalender-sama tidak memburuk; tidak ada H1/H2/H3 memburuk lebih dari 0.02. Ini aturan kehati-hatian baru, bukan interval keyakinan atau prediktor leaderboard; jangan dilonggarkan setelah hasil keluar.
- Laporkan bootstrap kalender 3 hari sebagai ketidakpastian bersyarat, beserta jumlah tanggal unik dan konsentrasi SSE. Jangan menjadikannya bukti lepas dari selection bias.
- Sebelum promosi, ulang parent pada jalur produksi, verifikasi seed, feature prefix, endpoint mask, cache hash, dan full-chain label perturbation. Cek fallback dan jangkauan kalibrasi final.
- Public/private split yang mungkin acak **tidak berarti training-validation harus acak**. Tugasnya tetap menggeneralisasi ke rentang tanggal setelah training. Split publik menentukan subset penilaian dari test, bukan ketersediaan label masa depan saat fit. Dokumentasi [TimeSeriesSplit](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.TimeSeriesSplit.html) menjelaskan pemisahan temporal dan kebutuhan spacing yang konsisten.
- Jangan melakukan pencarian public membership atau koreksi tanggal berdasarkan leaderboard. Tetap simpan v21 2.86595 sebagai banked. Private paket 2.93028 bisa lebih baik atau lebih buruk; bukti saat ini tidak memberikan probabilitas yang dapat dipercaya.

## 7. Status dan reproduksi

- [x] Audit progress §209–213, source an64–an66, dan riwayat kegagalan terkait.
- [x] Diagnostic kalender-sama dan residual-energy benar-benar dijalankan.
- [x] Production md5 tetap `d9ea928d20bed52b03e5802475158f72`.
- [ ] P0 endpoint control, P1, P2, dan P3 belum dilatih pada sesi audit ini.
- [ ] Tidak ada submission baru atau klaim public gain baru.

Reproduksi audit dari root repo:

```powershell
.venv/Scripts/python.exe src/an67_v21_calendar_audit.py
```

Expected: 18 baris perbandingan kandidat/protokol, empat baris dekomposisi residual, assertions lolos, CSV/JSON di `outputs/audit_v21_s30/`. Script hanya membaca artefak lama dan menulis direktori audit baru.

Setelah setiap keluarga eksperimen selesai, append progress dengan hipotesis, exact config, kontrol reproduksi, hasil semua blok, kalender-sama, fallback, keputusan, dan lokasi artefak. Jangan menulis “axis exhausted” dari satu keluarga yang gagal. Repo ini tidak memiliki `.git`; tidak ada langkah commit/push dalam rencana.
