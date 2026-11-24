# V21 session 31: audit struktural dan rencana sequence model

> **For agentic workers:** Gunakan `executing-plans` untuk implementasi berurutan. Checklist audit sudah selesai; checklist training masih rencana. Pertahankan kandidat v21 banked dan artefak historis.

**Goal:** Menguji apakah urutan sensor selama beberapa hari menyediakan informasi RH yang tidak tertangkap fitur ringkasan dan koreksi residual existing.

**Architecture:** Satu pembentuk window exogenous, dua learner temporal berkapasitas terkendali, dan evaluasi melalui solver v21 yang sama. Model baru belajar langsung dari label training dengan baseline fisik deterministik, bukan residual meta-stack yang hanya menyisakan sedikit origin. Kontrol scalar, temporal-linear, dan nonlinear memisahkan manfaat representasi dari penambahan model.

**Tech Stack:** NumPy, pandas, SciPy sparse, scikit-learn; PyTorch CPU untuk CNN bila tahap itu dijalankan. Virtualenv sekarang belum memiliki torch, sktime, numba, atau tensorflow. Audit yang sudah selesai tidak membutuhkan paket baru.

## Keputusan utama

**Prioritas riset berikutnya: model temporal kecil untuk level RH, bukan putaran de-shrink, sensor deletion, atau kalibrasi daily bias lagi.** Urutan paling hemat adalah random temporal convolution + Ridge sebagai screen, kemudian CNN dengan filter yang dipelajari. Ini pilihan yang paling beralasan dari celah yang ditemukan, bukan klaim probabilitas menang yang sudah terukur.

Public banked tetap **2.86595**. Paket physics/de-shrink/lags **2.93028** kalah. Target pesaing 2.6 adalah informasi pengguna; kita tidak mengetahui metode, keabsahan perbandingan detail, atau private mereka. Target 2.6 menuntut **17.698% penurunan MSE**, sehingga memperbaiki angka lokal 0.001 bukan strategi utama untuk lompatan tersebut.

## 1. Cakupan review dan status bukti

Review mengikuti progress sampai §222, indeks seluruh bagian historis, implementasi an68–an70, output prediksi, serta audit sebelumnya. Eksperimen lama tidak semuanya dilatih ulang; angka lama yang belum direproduksi pada harness terbaru tetap bukti historis dengan batas protokolnya. Indeks navigasi tersimpan di `outputs/audit_v21_s31/progress_section_index.csv`.

| Kelompok | Apa yang diuji / hasil | Implikasi saat ini |
|---|---|---|
| Cleaning, pruning, Tmin/quantiles (§8,19,27–30) | Fitur ringkasan thermal memberikan kemajuan awal; cleaning tambahan kemudian gagal | Pertahankan ringkasan penting sebagai jalur scalar model baru. Bentuk urutan penuh belum setara dengan menambah quantile. |
| Model tabular dan bobot (§50–54,61,69,73,98) | Keragaman linear/tree dan beberapa kalibrasi membantu; MLP/KRR tabular gagal | Jangan mengulang MLP yang sama. Kegagalan tersebut tidak menguji convolution dengan weight sharing dan konteks temporal. |
| Pergantian target, slow/fast decomposition, pseudo-label (§18,50,51,158,164) | Tidak ada gain yang dapat diandalkan | Baseline fisik dipakai sebagai residual anchor; jangan mengklaim target vapour pressure sebagai inovasi baru. |
| Robust-core, pressure-member, blend floor (§105–143) | Banyak pembalikan CV/public; sebagian justifikasi memakai asumsi split atau meta CV yang kemudian dikoreksi | Jangan memakai narasi private lama sebagai ground truth. Ablation refit bukan ukuran pengaruh sensor pada model tetap. |
| Increment v21 (§147–157) | Public 2.86595, perbaikan yang terbukti eksternal | Pertahankan sebagai kontrol dan komponen forecast. |
| Extension solver, learner increment, spline, gain, anchor, bagging (§158–205) | Mayoritas gagal; physics/de-shrink/lags kecil dan episode-dependent | Jangan memasang tiga perubahan sekaligus lagi. Solver gain dua angka bukan training model end-to-end. |
| Lag standalone (§209) | Masih positif kecil; sebagian besar penyusutan gain 7 hari akibat perubahan kalender | Belum diketahui public standalone-nya, tetapi bukan bukti lompatan ke 2.6. |
| Relative 57 fitur dan endpoint fix (§210,218) | Fix hanya -0.001165 terhadap arm relative yang tetap kalah | Kesalahan fitur nyata tetapi bukan penyebab dominan kegagalan relative. Tutup kontrol ini. |
| Sensor ablation (§219) | Pressure -0.000435 pooled; CO₂ +0.012129; keduanya +0.019917; semua B2 memburuk | Tidak promotable. Klaim “model hampir tidak menggunakan pressure” terlalu kuat karena model dilatih ulang. |
| Slow-member (§220) | Zero menang B1/B3; B2 fallback | Kandidat aktif tidak terbukti. Ada masalah replay origin yang membatasi klaim gate; tidak otomatis menjadi kandidat bagus setelah diperbaiki. |

“Closed” berarti konfigurasi yang dicoba tidak layak diteruskan tanpa hipotesis berbeda. Itu tidak membuktikan semua anggota keluarga model tidak dapat berhasil.

## 2. Temuan audit baru yang benar-benar dihitung

### 2.1 Laporan matched-calendar sensor memasukkan B3

`an69.matched` memakai `.set_index('datetime').loc[idx]` pada P15 yang masih berisi B1+B2+B3. Karena B3 overlap, 1.008 timestamp menghasilkan **1.680 baris**, bukan 1.008 observasi unik. Kolom `15d_all` juga memakai 2.160 baris, berbeda dari primary 1.440. Ini kesalahan pelaporan populasi; primary `a47.report` masih benar.

Audit baru membuang B3 sebelum join dan memeriksa keunikan timestamp:

| Arm | ΔRMSE primary, 1.440 | Matched lama, 1.680 | Matched benar, 1.008 |
|---|---:|---:|---:|
| drop_pressure_abs | -0.000435 | -0.013636 | **-0.017545** |
| drop_co2_abs | +0.012129 | -0.023969 | **-0.029550** |
| drop_both_abs | +0.019917 | -0.027629 | **-0.034995** |

Keputusan menolak ketiganya tetap sama. Angka yang diperbaiki tersimpan terpisah di `sensor_calendar_corrected.csv`; file lama tetap menggambarkan run lama.

### 2.2 Gate slow-member belum sepenuhnya mereplay forecast origin

`an70.calibration_chunks` mensyaratkan setidaknya tiga origin secara keseluruhan, kemudian membagi timestamp menjadi tiga bagian. `select_alpha` melatih pada chunk sebelumnya. Itu menjamin urutan timestamp target, tetapi tidak menjamin seluruh label training calibrator sudah tersedia **saat origin prediksi validation dibuat**.

| Blok / split aktif | Baris validation | Baris dengan origin lebih awal daripada akhir label kalibrasi |
|---|---:|---:|
| B1 split 1 | 288 | 0 |
| B1 split 2 | 288 | **288** |
| B3 split 1 | 256 | **32** |
| B3 split 2 | 256 | **256** |

Contoh B1 split 2: prediksi berasal dari origin **6 Agustus 14:30**, tetapi calibrator sudah membaca label sampai **8 Agustus 14:30**. Tidak ada timestamp target validation yang beririsan langsung dengan target calibration; ini mismatch ketersediaan informasi pada origin, bukan bukti outer/test target dibaca. B2 tidak aktif setelah guard, sehingga angka potensial B2 tidak dianggap leak pada hasil final.

Kesimpulan yang masih sah: arm tertulis memilih nol, dan primary tidak bergerak. Bahkan best-alpha dalam gate lama lebih buruk **14.58% SSE pada B1** dan **22.23% pada B3** dibanding nol; bukan kalah tipis karena margin 1%. Kesimpulan yang terlalu kuat: “lima contrast tidak membawa sinyal pada genuine forecast replay.” Jangan menjanjikan perbaikan chronology akan mengubah kegagalan besar ini menjadi kemenangan.

### 2.3 Bias harian 40% bukan nullspace increment 40%

Audit lama benar bahwa `D 1 = 0`, tetapi beberapa bagian berikutnya menyamakannya dengan seluruh bias harian tidak terjangkau. Graph increment menghubungkan hari-hari. Yang benar-benar tidak dapat diubah increment saja adalah mean **per komponen graf yang terhubung**, bukan mean masing-masing hari.

Audit diagonalizes `L = 4 D1.T D1 + D4.T D4` pada timestamp aktual dan memproyeksikan residual v21. Setiap holdout yang diperiksa memiliki satu komponen terhubung.

| Share SSE | 15 hari, 1.440 | 7 hari, 1.008 |
|---|---:|---:|
| Komponen konstan / nullspace L | **2.44%** | **11.48%** |
| Mode lambat, 0 < eigenvalue ≤ 0.085 | **44.16%** | **36.29%** |
| Mode menengah, 0.085 < eigenvalue ≤ 0.337 | 18.88% | 25.39% |
| Mode lebih cepat, eigenvalue > 0.337 | 34.52% | 26.83% |

Band eigenvalue dibekukan untuk deskripsi. Pada grid reguler interior, batas tersebut kira-kira memisahkan variasi di sekitar 48 jam dan 24 jam, karena `L(ω)=8(1-cos ω)+2(1-cos 4ω)`. Di graph dengan gaps/boundary ini bukan Fourier period persis. Share bias kalender-harian 39.95% / 41.97% adalah partisi lain; jangan dijumlahkan dengan tabel spectral.

Alasan perubahan lambat susah dikoreksi oleh increment lebih halus dari “mustahil”. Untuk mode λ, kalau learner increment mengusulkan error-path q yang konsisten, perpindahan melalui solver adalah:

    δz = (I+L)^-1 L q  ->  gain per mode λ/(1+λ)

Pada λ=0.085, hanya **7.83%** amplitudo q yang diteruskan. Mode nol benar-benar tidak dapat bergerak. Mode lambat lain bisa bergerak, tetapi sangat diredam. Sebaliknya perubahan level p melewati gain **1/(1+λ)**, sekitar **92.17%** pada batas yang sama.

**Implikasi metode:** model baru yang lebih baik memprediksi level lambat punya jalur masuk yang lebih langsung daripada memperbesar semua increment. Jangan menaikkan lambda global untuk “mengatasi” ini: eksperimen solver terdahulu sudah menunjukkan tradeoff terhadap frekuensi lain.

Ini analisis kapasitas operator, bukan bukti sensor memprediksi mode tersebut. Nilai 44% tidak boleh dikonversi menjadi prediksi leaderboard.

### 2.4 Mengapa pressure ablation bukan pengukuran pengaruh kausal

Menghapus fitur lalu melatih ulang memungkinkan fitur lain menggantikan informasinya. Δscore dekat nol mengukur kinerja pipeline alternatif pada kalender lama, bukan sensitivitas model asli ketika pressure pada test bergeser. Apalagi pressure tetap ada pada level stack.

Tidak ada alasan mengulang sweep pressure setelah hasil negatif ini. Cukup ganti klaim luasnya: **penghapusan pressure absolut pada learner increment tidak menghasilkan keuntungan pada protokol yang diuji**. Eksperimen itu melemahkan kandidat penghapusan, bukan membuktikan sensor tidak dipakai atau pasti aman di test.

## 3. Mengapa pendekatan sequence berbeda dari percobaan lama

Fitur existing merangkum minima, quantile, mean, range, dan beberapa lag. Dua lintasan dapat memiliki Tmin, range, dan quantile yang serupa tetapi berbeda dalam durasi cooling, urutan plateau, pemulihan setelah ventilasi, dan keterkaitan T–CO₂ selama satu sampai beberapa hari. Hipotesis berikutnya adalah **informasi bentuk/urutan tersebut membantu estimasi RH**, bukan klaim bahwa setiap pola memiliki penjelasan fisik yang sudah terbukti.

Dataset tetap kecil: 2.933 label setengah jam tidak berarti 2.933 episode independen. Oleh karena itu jangan mulai dari Transformer besar atau foundation-model fine-tuning. Tiga jalur dipertimbangkan:

| Pendekatan | Manfaat | Risiko | Prioritas |
|---|---|---|---|
| Random temporal convolution + Ridge | Menguji representasi nonlinear urutan tanpa training filter neural; CPU, deterministik | Pooling bisa menghilangkan posisi relatif, fitur banyak bisa overfit | **Screen pertama** |
| CNN temporal kecil + jalur fitur scalar | Filter mempelajari pola yang relevan langsung; weight sharing membatasi jumlah parameter | Data episode sedikit, optimisasi dan regularisasi sensitif | **Kandidat utama dengan potensi lebih besar** |
| Learner increment dilatih melalui loss solver | Mengatasi mismatch tujuan training dengan RH final | OOF level dan Hessian lintastimestamp menambah kompleksitas; jalur lambat tetap teredam | Cadangan setelah dua jalur di atas |

Referensi primer: [ROCKET, Dempster dkk.](https://arxiv.org/abs/1910.13051) menunjukkan random convolution sebagai transform time series; paper itu menguji classification, sehingga penggunaan Ridge regression di sini adalah adaptasi yang belum terbukti pada data RH. [Bai, Kolter, Koltun](https://arxiv.org/abs/1803.01271) memberi dasar convolution sebagai alternatif sequence learner. Rancangan berikut memakai konteks exogenous dua arah, berbeda dari causal TCN pada paper. Kedua paper bukan bukti skor 2.6 dapat dicapai.

## 4. Kontrak data dan target untuk semua arm baru

**Tidak ada target RH history sebagai input.** Model baru belajar langsung:

    residual_train[t] = (RH[t] - rh_tmin48[t]) / 10
    q[t] = rh_tmin48[t] + 10 * f(exogenous_window[t], scalar_features[t])

`rh_tmin48` adalah proxy deterministik temperatur, bukan fitted banked prediction. Karena itu residual training tersedia untuk semua label yang sah sebelum origin; tidak tergantung 1–6 window meta-cache. Ini tidak sama dengan menggunakan residual in-sample dari fitted stack. Parent physical proxy sudah dicoba sebagai fitur; kebaruannya adalah learner dan bentuk input.

Spesifikasi input:

- Raw trajectory dari exogenous yang dibersihkan: T, CO₂, pressure; tambahan trajectory `rh_tmin48` berasal dari F prefix yang sama.
- Window **193 titik**, offset -96 sampai +96 half-hour: ±48 jam. Target berada di tengah. Cleaning/features dibangun hanya sampai horizon_end forecast tersebut, seperti kontrak existing.
- Empat channel nilai dan empat channel validitas sebelum imputation, shape `(n,8,193)`. Jangan isi NaN dengan target; median/scale hanya fit pada baris training. Mask menunjukkan missing/boundary sehingga padding tidak disamakan dengan observasi.
- Pertahankan seluruh F scalar parent yang tersedia, urutan kolom dibekukan. Transform scalar median/std training-only. Jangan membuang pressure atau range lagi pada putaran ini.
- Jangan melakukan normalisasi per window yang menghilangkan suhu absolut. Channel dinormalisasi dengan statistik training yang sama untuk semua window pada fold.
- Konteks future **exogenous** tersedia dalam task ini. Overlap window sensor tidak otomatis label leakage; yang dilarang adalah future RH masuk input, target preprocessing, early stopping, pemilihan alpha/epoch, atau meta fitting.
- Di ujung forecast, gunakan hanya prefix yang tersedia; padding normalized-zero dan mask nol. Jangan membangun window training/evaluasi dari fitur yang terlebih dahulu dibuat sampai akhir dataset lalu dipotong.

Untuk mengukur kontribusi pada sistem existing, gunakan satu bobot yang dibekukan:

    p_new = 0.75 * p_v21_level + 0.25 * q
    z_new = reconcile(p_new, v21_increment_terms)

Semua increment, lambda, clipping, dan level banked tetap sama. Evaluasi q standalone juga dilaporkan, tetapi seleksi utama memakai z_new. Bobot 0.25 tidak dipilih dari outer dan tidak di-sweep pada putaran ini. Jika perlu weight-selection kelak, itu eksperimen terpisah pada calibration origin yang benar.

## 5. Rancangan arm yang dibekukan

### A0: kontrol scalar Ridge

Target residual proxy di atas, input F scalar saja. Imputer median, StandardScaler, Ridge alpha `{100,1000,10000}`. Pilih alpha memakai dua validasi forward di dalam training outer, masing-masing 7 hari, tanpa overlap target. Ini kontrol target/learner, bukan kandidat baru yang diasumsikan kuat.

### A1: kontrol trajectory linear

Tambahkan channel trajectory pada offset `{-96,-48,-24,-12,-4,0,4,12,24,48,96}` kepada input A0, termasuk mask. Ridge dan alpha sama. Ini memisahkan akses konteks baru dari nonlinear convolution; jangan mengklaim semua linear lag sudah gagal jika kontrol level ini belum dijalankan.

### A2: random convolution Ridge — screen utama

Transform **ROCKET-inspired**, jangan menyebutnya implementasi ROCKET asli:

- 512 filter deterministik, seeds `{20260906,20260907,20260908}`; average tiga prediksi model, bukan pilih seed terbaik.
- Setiap filter memilih satu dari empat value channel, length dari `{7,9,11}`, dilation dari `{1,2,4,8}`. Bobot Gaussian dikurangi mean lalu dibagi norm; bias uniform [-1,1] pada skala normalized.
- Convolution valid. Pooling dilakukan terpisah pada response yang pusatnya sebelum dan sesudah titik target, sehingga posisi terhadap target tidak sepenuhnya hilang. Empat fitur/filter: maximum dan proportion-positive untuk masing-masing sisi.
- Response yang footprint-nya menyentuh invalid mask dibuang. Jika suatu sisi tidak punya response valid, hasil pooling NaN lalu diimpute memakai statistik training. Tidak ada quantile bias yang difit memakai label validation.
- Concatenate 2.048 pooling features dengan F scalar; imputer dan StandardScaler training-only; Ridge alpha `{100,1000,10000}`, dipilih pada dua fold forward yang sama dengan A0/A1.
- Catat jumlah fitur konstan, persentase response valid, alpha, dan ukuran efektif data per origin. Batasi thread BLAS agar reproducibility/runtime terukur.

Tidak ada kernel-count sweep. Jika kalah, jangan otomatis menggandakan filter. A2 positif memberi alasan bahwa bentuk nonlinear sequence membantu; A2 negatif tidak membuktikan learned convolution juga gagal, karena filter/pooling berbeda.

### B0/B1: kontrol scalar neural dan temporal CNN kecil

B0 adalah MLP scalar F→32→32→1, GELU, dropout 0.1, target residual proxy. B1 memakai CNN di bawah dengan jalur scalar. B0 menguji apakah keuntungan berasal dari training neural secara umum; parameter tidak identik tetapi berada pada orde yang sama dan jumlah aktual harus dilaporkan.

```python
import torch
from torch import nn

class ThermalWindowNet(nn.Module):
    def __init__(self, n_scalar):
        super().__init__()
        layers = []
        n_in = 8
        for dilation in (1, 3, 9, 27):
            layers += [nn.Conv1d(n_in, 16, kernel_size=5,
                                 dilation=dilation, padding=2*dilation),
                       nn.GELU(), nn.Dropout(0.1)]
            n_in = 16
        self.temporal = nn.Sequential(*layers)
        self.scalar = nn.Sequential(nn.Linear(n_scalar, 8), nn.GELU())
        self.head = nn.Linear(24, 1)
        nn.init.zeros_(self.head.weight)
        nn.init.zeros_(self.head.bias)

    def forward(self, sequence, scalar):
        temporal = self.temporal(sequence)
        center = temporal[:, :, temporal.shape[-1] // 2]
        return self.head(torch.cat([center, self.scalar(scalar)], dim=1)).squeeze(1)
```

Receptive field = `1 + 4*(1+3+9+27) = 161` titik, **80 jam span**, di dalam window 96 jam. Sekitar 5–6 ribu parameter, bergantung jumlah scalar. Ini bukan MLP 128×64 lama dan bukan urutan target autoregressive.

Training dibekukan: AdamW lr=0.001, weight_decay=0.01, batch=64, max_epochs=160, patience=15, MSE residual, gradient norm cap=1.0, tiga seeds sama dengan A2. Early stopping memakai 7 hari terakhir yang seluruhnya masih sebelum outer origin; data training network berhenti sebelum validation tersebut. Preprocessing early-stop fold difit ulang pada bagian training-nya saja.

Setelah epoch dipilih, refit dari awal pada seluruh training outer dengan jumlah epoch itu, preprocessing training outer, tanpa membaca label outer. Tidak ada early stopping pada public/B1/B2/B3. Jangan mengganti target loss ke Huber setelah melihat error wettest tercile.

## 6. Implementasi berurutan dan file yang disentuh

### Task 0 — perbaiki dua kontrak sempit, bukan rebuild seluruh harness

**Modify:** `src/an69_v21_sensor_ablation.py`, `src/an70_v21_slow_member_correction.py`.
**Tests:** `tests/test_v21_calendar_origin_contract.py`.

- [ ] Buat regression test bahwa B1/B2+B3 overlap tidak menambah matched row count. Fixture: B1 tanggal A,B, B3 duplikat B; query A,B harus tetap dua baris setelah pemilihan primary, bukan tiga.
- [ ] Perbaiki helper matched agar memilih primary dan assert uniqueness sebelum `.loc`:

```python
def primary_index(P):
    Q = P.loc[P.score & P.block.str.startswith(('B1_', 'B2_'))].copy()
    assert not Q.datetime.duplicated().any()
    return Q.set_index('datetime').sort_index()
```

- [ ] Ganti unit forward-selection slow-member dari potongan timestamp ke **origin validation**. Untuk origin o, calibration record sah hanya jika target timestamp `<=o`, record dibuat oleh predictor yang training-nya mendahului target, dan seluruh fitur/prediksi record direproduksi tanpa target validation. Deduplicate calibration timestamp setelah eligibility filter.
- [ ] Test inti untuk eligibility berdasarkan contoh B1: record target 8 Agustus 14:30 harus ditolak untuk validation origin 6 Agustus 14:30, walaupun validation target berada 9 Agustus. Record target 5 Agustus diterima jika predictor-nya valid.
- [ ] Recompute gate lama sebagai audit, tanpa mengubah frozen margin atau menjadikannya kandidat utama baru. Jika kurang tiga origin valid, laporkan fallback. Jangan mengklaim model kalah pada origin yang tidak pernah bisa dilatih.
- [ ] Run `.venv/Scripts/python.exe -m unittest discover -s tests -p test_v21_calendar_origin_contract.py`; harapkan semua pass sebelum reuse kontrak.

### Task 1 — pembentuk window bersama

**Create:** `src/v21_sequence_design.py`, `tests/test_v21_sequence_design.py`.

- [ ] Implementasikan pembentuk prefix, value/mask channels, normalization training-only, scalar passthrough, dan metadata `(target_timestamp, origin, horizon_end, feature_start, feature_end)` sesuai §4.
- [ ] Test timestamp lag menggunakan grid dengan satu timestamp hilang: offset 48 berarti tepat 24 jam, bukan 48 baris compressed.
- [ ] Test future RH perturbation tidak mengubah window, scaling, selected alpha/epoch, dan prediksi. Test future exogenous setelah horizon_end tidak mengubah fitur.
- [ ] Test center index=96 dan receptive field CNN=161; mask padding nol; inverse residual anchor mengembalikan rh_tmin48 saat f=0.
- [ ] Run `.venv/Scripts/python.exe -m unittest discover -s tests -p test_v21_sequence_design.py`.

### Task 2 — temporal screen tanpa framework neural

**Create:** `src/v21_temporal_models.py`, `src/an72_v21_sequence_benchmark.py`, `tests/test_v21_temporal_models.py`.

- [ ] Implement A0/A1/A2 persis §5; catat random kernel bank dan hash, feature dimension, alpha dan forecast origins dalam manifest.
- [ ] Test convolution pada fixture dengan kernel `[1,0,-1]`: respons harus berubah saat urutan dibalik meski mean/min/max sama. Test missing footprint diabaikan dan frozen seed memberi transform identik.
- [ ] Gunakan `a47.load_cache` untuk level kontrol; solver memakai produksi v21 tanpa physics/dsh/lags. Prediksi control harus cocok frozen v21 atol=1e-9 sebelum membaca angka kandidat.
- [ ] Jalankan `.venv/Scripts/python.exe src/an72_v21_sequence_benchmark.py --family random-conv`. Simpan semua origin dan kandidat ke `outputs/audit_v21_s31/sequence_*`; jangan overwrite s27–s30.
- [ ] Report standalone q dan blended/reconciled z, primary, matched 1.008, 7-day, B3, spectral error bands, movement energy, jumlah hari unik. Primary dan stress tidak dicampur.

### Task 3 — learned CNN dan scalar control

**Extend:** `src/v21_temporal_models.py`, `src/an72_v21_sequence_benchmark.py`, `tests/test_v21_temporal_models.py`.

- [ ] Pasang PyTorch CPU pada runtime yang dipilih ketika eksekusi, rekam versi aktual dan dependency lock; jangan mengasumsikan GPU atau paket sudah tersedia. Tidak ada dependency baru dipasang pada sesi perencanaan ini.
- [ ] Implement B0/B1 dan training §5. Zero-initialized head harus mereproduksi proxy sebelum training; synthetic deterministic sequence harus dapat di-overfit sebagai sanity check optimisasi, bukan bukti generalisasi.
- [ ] Test label perturbation pada seluruh jalur early-stop/refit, deterministic evaluation dropout-off, finite outputs, train-only scalers, parameter count dan receptive field.
- [ ] Jalankan `.venv/Scripts/python.exe src/an72_v21_sequence_benchmark.py --family learned-conv`. Seed dan hyperparameter tidak dipilih dari outer.
- [ ] Jika CNN membaik, bandingkan B0 untuk membaca kontribusi temporal. Jika keduanya gagal, catat apakah train fit gagal atau gap train-forward besar. Jangan menyebutnya information ceiling.

### Task 4 — keputusan dan reproduksi produksi

- [ ] Maksimal **lima arm** A0/A1/A2/B0/B1 pada putaran ini. Benchmark tetap memuat v21 banked sebagai kontrol. Pembanding lama physics_lags/v21_lags boleh dilaporkan dari cache, bukan di-retune.
- [ ] Gunakan primary B1+B2, matched-calendar unik, B3 stress, H1/H2/H3. Gate internal tetap dari rencana s30: pooled gain minimal 0.02, B1/B2 tidak memburuk, B3 hurt≤0.05, matched dan pooled7 tidak memburuk, worst H hurt≤0.02.
- [ ] Setiap hasil menyertakan day-level dan spectral decomposition, tetapi promosi ditentukan total RH error; penurunan satu band saja tidak cukup.
- [ ] Kandidat terbaik yang lolos harus di-refit melalui jalur final dengan preprocessing/epoch selection yang sama. Bangun CSV, cek ID/order/numeric finite/clip/hash dan simpan dibanding banked sebelum ada keputusan submit. Tidak ada submission otomatis dari benchmark.
- [ ] Update progress setelah Task 0, A0–A2, B0–B1, dan keputusan. Catat hasil negatif semua seed/arm agar tidak terseleksi diam-diam.

## 7. Hal yang sengaja tidak menjadi prioritas putaran ini

- Menambah faktor amplitude/de-shrink, gate cooling berbasis label, atau solver-strength grid. Itu variasi lokal yang sudah berulang kali diuji.
- Menyetel lagi daily Ridge/slow-member karena 40% terlihat besar. Tiga kandidat terdahulu tidak menunjukkan transfer, dan operator audit memberi alasan lebih spesifik untuk mencari representasi temporal langsung.
- Membuktikan pressure tidak berbahaya lewat ablation tambahan. Hasil sekarang tidak mengisolasi semua efek pressure, tetapi belum ada bukti cukup untuk menjadikan itu fokus utama.
- Random train/validation split demi histori panjang. Public/test membership mungkin acak, namun label test tetap berada setelah training. Random split akan menjawab task yang berbeda.
- Menjanjikan private rescue untuk paket 2.93028. Dua angka public tidak mengidentifikasi perilaku private.
- Mencari data asli, external target, atau membership public. Semua metode di atas memakai data kompetisi dan label training sesuai ketersediaannya.

## 8. Status audit dan reproduksi

- [x] `src/an71_v21_structural_audit.py` dijalankan: pemeriksaan graph nullspace, spectral energy conservation, primary uniqueness, sensor report correction, dan calibration-origin audit berhasil.
- [x] Output: `solver_reachability.csv`, `solver_spectrum.csv`, `sensor_calendar_corrected.csv`, `calibration_origin_audit.csv`, `progress_section_index.csv`, `provenance.json` di `outputs/audit_v21_s31/`.
- [ ] Task 0 memperbaiki source lama masih direncanakan; koreksi angka sudah tersedia dalam artefak audit baru.
- [ ] A0/A1/A2/B0/B1 belum dilatih. Tidak ada klaim gain baru atau file submission baru.

Reproduksi audit:

```powershell
.venv/Scripts/python.exe src/an71_v21_structural_audit.py
```

Expected: matched lama 1.680 versus unique 1.008; nullspace share 0.0243767 / 0.114817; mismatch origin aktif 288 di B1 dan 288 di B3. Loader cache s27 memverifikasi fingerprint build; note hash file produksi berbeda dari file historis tetap dicatat dan bukan diabaikan sebagai cache match penuh. Hash produksi sekarang `d9ea928d20bed52b03e5802475158f72`.

Tidak ada `.git` di workspace, sehingga tidak ada langkah commit/push. Rencana dapat dieksekusi berurutan tanpa menunggu desain baru untuk setiap arm, selama konfigurasi dan aturan evaluasi di atas dipertahankan.
