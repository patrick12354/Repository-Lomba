# Case 1 — Prediksi Magnitudo Gempa (EEW)

Regresi magnitudo gempa dari **satu** stasiun seismik: 5 detik waveform 3-komponen
(1 detik sebelum P-wave, 4 detik sesudah) @ 200 Hz, plus metadata stasiun-event.

**Setiap kali muncul insight baru** (fitur yang terbukti/gagal, mekanisme CV↔LB, trik yang
berhasil, dsb.) — **langsung tambahkan ke file ini**, jangan ditunda sampai akhir sesi.

Analisis lengkap dengan angka: [`penjelasan_case.md`](penjelasan_case.md).
Notebook EDA + baseline: [`eda.ipynb`](eda.ipynb).
**LB terbaik: `notebook_8.csv` = 0,1849 — peringkat 3.** (Peringkat 1 = 0,1835 Letdown,
peringkat 2 = 0,1837 Kingpul.) Riwayat: nb1 0,2005, nb2 0,2262, nb3 0,1996, nb5 0,2063,
nb6 0,1952, nb8 **0,1849**, nb9 0,1856, nb10 0,1871.

**Batch Kaggle ke-2 (notebook 06-08) sudah dijalankan 22 Agu 2026: 3 dari 3 GAGAL.**
Tidak ada `notebook_11`. Augmentasi agresif, pra-latih SSL, dan kepala distribusi
semuanya memberi gain holdout **positif** (menang <= 3/12), termasuk ketujuh kombinasi
gabungannya. Rincian di [`sudah_run/README.md`](sudah_run/README.md).

**BATCH KE-3 (notebook 09-10) SUDAH DIJALANKAN 22 Agu 2026 malam. Antrian KOSONG.**
Notebook 10 **GAGAL** telak (`bias_rnd` +0,115, menang 0/12) — keluarga "input LightGBM
digabung ke dalam CNN" ditutup. Notebook 09 **BELUM TERJAWAB**: gerbang kontrolnya memakai
konstanta yang salah jenis, jadi verdiktnya tidak bisa dibaca apa adanya.

**SUDAH TERJAWAB 23 Agu 2026** lewat `tools/serap_nb12.py` (tanpa GPU, dari
`cnn12*_syms.npz` yang selamat). Dengan gap lingkungan dinetralkan, `cnn12b_tta` mendapat
gain **+0,00029, menang 6/12** — meleset dari ambang (gain < 0 dan menang ≥ 7/12), tapi ini
kandidat **terdekat** yang pernah ada. **TTA dan bobot record `is_clipped` DITUTUP.**
Jangan jalankan ulang di pipeline lokal — alasannya di bawah.

Generator: `tools/mk_kaggle4.py` (nb 10), `tools/mk_kaggle3.py` (nb 09).

**Tiga submission terakhir semuanya lebih buruk dari `notebook_8`.** Dua perturbasi
independen terhadap blend nb8 — nb9 (menambah koreksi set-transformer) dan nb10 (menggeser
bobot blend) — dua-duanya merugi. **Perlakukan blend `notebook_8` sebagai setelan baku dan
jangan diutak-atik lagi**; yang tersisa cuma menambah kandidat yang lebih akurat per-record.
Baca [`submission/LEADERBOARD.md`](submission/LEADERBOARD.md) sebelum mengubah apapun.

**Yang punya file submission tapi BELUM/TIDAK disubmit** (aturan 0 di `LEADERBOARD.md`):

| file | status | alasan |
|---|---|---|
| `notebook_7.csv` | tidak disubmit | gain di dalam derau (menang 7–8/12), digantikan nb8 |
| `notebook_4.csv` | tidak disubmit (arsip) | + CNN v2 bobot 0,10 + refit 100% data |
| `notebook_3.csv` | **menurut user tidak disubmit** | tapi tercatat LB 0,1996 dan dipakai sebagai titik kalibrasi — lihat catatan di bawah |

> **Konflik `notebook_3` sudah tidak relevan.** Titik LB ke-4 (`notebook_9` = 0,1856,
> offset **+0,0138**) memperlihatkan offset-nya memang tidak stabil, dengan atau tanpa nb3.
> Berhenti memakai `lb_real` untuk menjanjikan angka LB.

**Kalibrasi `lb_real` -> LB (5 titik):**
```
offset: nb3 +0,0051 | nb6 +0,0107 | nb8 +0,0087 | nb9 +0,0138 | nb10 +0,0098
5 titik   : mean +0,0096, sd 0,0032
TANPA nb9 : mean +0,0086, sd 0,0025      <- nb9 outlier tunggal
```
**`lb_real` adalah kriteria peringkat yang sah** — 4 dari 5 titik konsisten, dan arahnya
benar di nb8→nb10. Satu-satunya kegagalan arah adalah nb9, dan sebabnya spesifik (lihat
"Set-transformer: DITOLAK"). **Jangan pernah submit kandidat yang `lb_real`-nya lebih buruk
dari juara bertahan** — `notebook_10` melanggar ini atas dasar teori dan rugi 0,0022.

> **JANGAN menilai kandidat dengan `eb_twmae(y, p, ev)` mentah** — bobotnya cacat di sisi
> depth-bulat (lihat "TEMUAN TERBESAR" di bawah). Pakai `lb_real` dari `lab_common.py`.
>
> **Satu pengecualian sempit:** untuk metode yang secara eksplisit **menyeragamkan
> prediksi di dalam grup depth** (smoothing sisi bulat, attention antar-record, pooling
> posterior), `lb_real` membayar berlebihan — record dari gempa berbeda yang berbagi
> `(depth, magnitude)` punya `y` identik di train. Itu yang membunuh `notebook_9`.
> Pengecualian ini **hanya** berlaku untuk kelas metode itu. `notebook_10` menggeneralisasi
> pengecualian ini ke pemilihan bobot blend dan rugi 0,0022 — jangan diulang.

### Struktur kode sejak notebook_6

Pipeline dipecah jadi modul supaya eksperimen bisa mengambil OOF dari cache alih-alih
melatih ulang tiap kali:

| file | isi |
|---|---|
| `lab_common.py` | data, `eb_twmae`, **`lb_real`/`part_real`/`cv_real`**, ekstraksi fitur, `make_sw`, smoothing/ekspansi |
| `lab_models.py` | runner LightGBM (`cv_lgb`) + `cached(name, fn)` -> `cache/<name>.npz` |
| `lab_cnn.py` | CNN gaya MagNet (bentuk ternormalisasi + skala sebagai skalar) |
| `lab_group.py` | classifier pasangan co-membership + soft smoothing |
| `lab_cnn3.py` | CNN v3 multi-task (dipakai notebook_8, LB 0,1849) + Net4-Net8 |
| `lab_set.py` | set-transformer atas grup depth (target di-demean per subset) |
| `lab_blend.py` | protokol blend nb6/nb8 dipakai ulang (`search`, `nb8_ref`) |
| `fastscore.py` | `Scorer`/`Post` versi bincount, ~5000x lebih cepat — untuk pencarian bobot |

### Tata letak folder

Root `Case 1/` hanya berisi `.md` dan `.ipynb`. Semua `.py` tinggal di subfolder:

```
Case 1/
├── notebook_*.ipynb         hasil yang di-commit beserta output
├── CLAUDE.md, penjelasan_case.md
├── lab/                     modul pipeline (lab_*.py, fastscore.py)
├── experiments/             exp*.py — probe sekali-pakai, satu ide per file
│   └── _path.py             shim sys.path
├── tools/                   mk_nb*.py — generator notebook_6/7/8/9, mk_kaggle.py
│   └── _path.py             shim sys.path
├── belum_run/               ANTRIAN run GPU panjang (>30 mnt) — lihat "Konvensi run GPU"
│   └── ref/nb8_ref.npz      prediksi 8 kandidat nb8, input untuk notebook Kaggle
└── sudah_run/               ARSIP run yang selesai
    ├── README.md            ringkasan verdikt tiap notebook
    └── hasil/               versi tereksekusi + zip hasil tiap notebook
```


**Notebook** membuka dengan dua baris bootstrap sebelum import apa pun:

```python
import sys, os
sys.path.insert(0, os.path.abspath("lab"))   # modul pipeline ada di lab/
```

Ini mengandalkan cwd = `Case 1/`, yang sudah dijamin `jupyter.notebookFileRoot`
(`${fileDirname}`) dan juga perilaku default `nbconvert --execute`. Kalau menambah
notebook baru, salin dua baris ini ke sel kode pertama.

**Skrip di `experiments/` dan `tools/`** cukup diawali `import _path`, yang menaruh
`lab/` dan `Case 1/` di `sys.path` serta menyediakan `_path.ROOT` (= `Case 1/`).

Path data/cache/submission di `lab_common.py` diikat ke lokasi file modul (bukan cwd),
jadi skrip bisa dijalankan dari folder mana pun:

```bash
C:/Patrick/coding/.venv/Scripts/python.exe "Case 1/experiments/exp15.py"
```

`cache/` di-gitignore. Clone baru menjalankan ulang model (~25 menit CPU + 20 menit GPU).

## Konvensi run GPU panjang: `belum_run/` -> `sudah_run/`

**Kapan dipakai.** Begitu sebuah ide butuh GPU dan estimasi waktunya **> 30 menit**, jangan
dijalankan langsung di sesi ini. Mesin lokal (RTX 4060) pernah dipakai 3 jam untuk dua
notebook dan **dihentikan sebelum menghasilkan angka apa pun** — waktunya nyata, hasilnya
nol. Bungkus jadi notebook mandiri, taruh di `belum_run/`, serahkan ke user untuk
dijalankan di Kaggle.

```
Case 1/
├── belum_run/          ANTRIAN — notebook siap jalan, hasilnya belum ada
│   ├── README.md       urutan yang disarankan + estimasi waktu + apa yang diuji
│   ├── ref/            input yang dibutuhkan notebook (mis. nb8_ref.npz)
│   └── NN_nama.ipynb   satu ide per notebook, diberi nomor urut prioritas
└── sudah_run/          ARSIP — sudah dijalankan, hasilnya sudah diserap
    ├── README.md       ringkasan verdikt tiap notebook (yang menang DAN yang gagal)
    ├── NN_nama.ipynb   notebook sumbernya
    └── hasil/
        ├── NN_nama.ipynb   versi TEREKSEKUSI dari Kaggle (beserta output)
        └── NN_nama.zip     zip mentah dari /kaggle/working
```

**Aturan mainnya:**

1. **Satu notebook = satu ide.** Kalau dua ide digabung dan hasilnya gagal, tidak ketahuan
   yang mana yang salah. Beri nomor urut sesuai prioritas (murah + peluang tinggi duluan).
2. **Notebook harus berdiri sendiri** — jangan `import` apa pun dari `lab/`, karena folder
   itu tidak ada di Kaggle. Salin kode intinya (`lb_real`, ekstraksi fitur, protokol blend)
   apa adanya supaya angkanya sebanding dengan run lokal.

   **Pengecualian: artefak dari run sebelumnya.** Kalau notebook butuh hasil run lain
   (prediksi OOF/test model terdahulu, bobot terlatih, cache fitur) dan **melatih ulang
   dari nol akan makan > 30 menit tambahan**, jangan dilatih ulang — pakai artefaknya.
   Yang berdiri sendiri itu **kodenya**, bukan datanya.

   Tapi Kaggle tidak bisa membaca file dari repo lokal, jadi prosedurnya:

   1. Simpan artefaknya sekecil mungkin ke `belum_run/ref/` (mis. `nb8_ref.npz`, 334 KB —
      cuma prediksi 8 kandidat + bobot blend, bukan modelnya).
   2. **Bilang ke user untuk meng-upload folder itu sebagai Kaggle Dataset**, lalu minta
      **slug**-nya. User yang punya akun; agen tidak bisa upload sendiri. Tanpa langkah ini
      notebooknya akan jalan berjam-jam lalu mati di `KeyError`.
   3. Tulis slug yang user berikan ke `REF_KNOWN` di notebook, **plus penelusuran rekursif
      `/kaggle/input` sebagai cadangan** — slug bisa berubah kalau dataset di-upload ulang.
      Polanya ada di bagian "Path di notebook Kaggle" di bawah.
   4. **Validasi artefaknya di sel Setup**, bukan berjam-jam kemudian: hitung ulang sesuatu
      yang nilainya sudah diketahui dan bandingkan (`nb8_ref.npz` harus mereproduksi
      `lb_real` 0,1762). Cetak COCOK / TIDAK COCOK.
   5. Kalau file wajibnya tidak ketemu, **berhenti di sel Setup** dengan instruksi
      pemasangan lengkap + daftar isi `/kaggle/input` saat itu.

   Yang **tidak** boleh dijadikan artefak: apa pun yang lebih murah dihitung ulang daripada
   diunggah, dan waveform mentah (126 MB — sudah ada sebagai dataset kompetisi).
3. **`belum_run/README.md` wajib mencantumkan estimasi waktu per notebook** dan urutan
   yang disarankan kalau kuota GPU terbatas.
4. **Cetak sisa waktu tiap fold selesai.** Run yang diam berjam-jam tidak bisa dibedakan
   dari run yang menggantung.
5. **Tiap notebook mencetak verdikt eksplisit** terhadap target LB + ketiga diagnostik
   transfer, supaya user bisa menilai tanpa menunggu agen.
6. **Sel terakhir membungkus semua output jadi satu zip** di `/kaggle/working/`, supaya
   user cukup mengunduh satu file dari panel Output.
7. **Begitu hasilnya kembali:** ekstrak `.npz` ke `cache/`, pindahkan notebooknya dari
   `belum_run/` ke `sudah_run/`, taruh versi tereksekusi + zip di `sudah_run/hasil/`, lalu
   tulis verdiktnya di `sudah_run/README.md` — **termasuk yang gagal beserta alasannya.**
   Yang gagal justru yang paling sering dicoba ulang kalau tidak dicatat.
8. **Verdikt yang dicetak notebook tetap wajib diperiksa ulang.** Batch 21-22 Agu 2026
   membuktikannya: notebook 01 melabeli `bias_rnd = +0,059` sebagai AMAN karena ambangnya
   dipasang 0,08, padahal nb5 rugi di LB pada +0,056.

## Path di notebook Kaggle — pola yang dipakai kelima notebook batch pertama

Notebook harus jalan **di Kaggle maupun di lokal tanpa diedit**. Polanya: coba path Kaggle
dulu, jatuh ke path lokal kalau tidak ada.

```python
# --- data kompetisi + folder output ---
KG   = "/kaggle/input/competitions/ai-innovation-case-task-1-seismic-magnitude-prediction/seismic-dataset"
DATA = Path(KG) if os.path.exists(KG) else Path("seismic-dataset")
OUT  = Path("/kaggle/working") if os.path.isdir("/kaggle/working") else Path("cache")
OUT.mkdir(exist_ok=True, parents=True)
```

Di Kaggle: **Add Input -> Competitions -> `ai-innovation-case-task-1-seismic-magnitude-prediction`**.

Untuk file pendukung (mis. `nb8_ref.npz`), upload folder `belum_run/ref/` sebagai **Kaggle
Dataset** lalu Add Input. Slug dataset bisa berubah, jadi jangan hardcode satu path —
coba lokasi yang diketahui dulu, baru telusuri rekursif sebagai cadangan:

```python
REF_KNOWN = ["/kaggle/input/datasets/timotiuspatrick/nb8-ref/nb8_ref.npz",
             "/kaggle/input/nb8-ref/nb8_ref.npz"]
def _find_ref():
    for p in REF_KNOWN:
        if os.path.exists(p): return Path(p)
    for root in ("/kaggle/input", "/kaggle/working", ".", "..",
                 "belum_run/ref", "../belum_run/ref"):
        if not os.path.isdir(root): continue
        for dp, _, fs in os.walk(root):
            if "nb8_ref.npz" in fs: return Path(dp)/"nb8_ref.npz"
    return None
REFP = _find_ref()
```

**Tiga hal yang wajib ada di sel Setup**, semuanya karena kegagalan nyata:

```python
print("DATA :", DATA, "| ada:", DATA.exists())     # 1. cetak path yang KETEMU, bukan yang diharapkan
print("REF  :", REFP)
import torch
DEV = "cuda" if torch.cuda.is_available() else "cpu"
print("DEV  :", DEV, torch.cuda.get_device_name(0) if DEV=="cuda" else "")
if DEV != "cuda":
    print("PERINGATAN: GPU tidak aktif. Settings -> Accelerator -> GPU.")   # 2. gagal keras, jangan diam
```

3. **Validasi file input SEKARANG, bukan berjam-jam kemudian.** Kalau ada acuan yang harus
   bisa direproduksi, cek di sel Setup:

```python
_v = sc(post_tr(REF["__w__"] @ ref_stack()[0]))
print("COCOK" if abs(_v-0.1762) < 0.0005 else "TIDAK COCOK -- verdikt tidak bisa dipercaya")
```

Kalau file wajibnya hilang, **cetak instruksi pemasangan lengkap + isi `/kaggle/input`
sekarang** lalu hentikan — jangan biarkan user menunggu 2 jam untuk `KeyError`.

## Data

```
seismic-dataset/
├── train/train_waveforms.npy   float32 (10505, 1000, 3)   126 MB
├── train/train_meta.csv        sample_id, distance_km, depth_km, is_clipped, snr_db
├── train/train_labels.csv      sample_id, magnitude
├── test/test_waveforms.npy     float32 (2300, 1000, 3)
├── test/test_meta.csv          kolom sama dengan train_meta
└── sample_submission.csv       2300 baris, semua diisi konstan 5.2
```

Urutan baris CSV **sama persis** dengan urutan array `.npy` — `X[i]` berpasangan dengan
`meta.iloc[i]`. Tidak perlu join berbasis indeks.

Data bersih: nol NaN/Inf, nol duplikat `sample_id`, nol overlap ID train/test.

Konstanta penting: `FS = 200` (Hz), `P_IDX = 200` (indeks P-arrival), `N_SAMP = 1000`.

## Metrik: EB-TWMAE

```
1. Per gempa e:  MAE_e = mean(|y - y_hat|) atas semua record stasiun gempa itu
2. Skor akhir:   SUM(w_e * MAE_e) / SUM(w_e)
```

Bobot `w_e` dari magnitudo sebenarnya: 1.0 (<5.5), 1.5 (5.5–6.0), 2.0 (6.0–6.5), 2.5 (>=6.5).
Lebih kecil lebih baik. Implementasi ada di `eda.ipynb` (fungsi `eb_twmae`).

Metrik ini rata-rata **per event dulu**, baru dibobot. Urutan itu penting — jangan
membobot per-record lalu merata-rata.

## Empat hal yang gampang salah

**1. Tidak ada `event_id` di dataset, padahal metriknya per-event.**
Rekonstruksi dengan `groupby(["depth_km", "magnitude"]).ngroup()` → 905 pseudo-event dari
10.505 record. Ukuran sampel efektif adalah **905**, bukan 10.505 — ini yang membatasi
kompleksitas model. Grouping ini heuristik, bukan ground truth.

**2. Wajib `GroupKFold` berbasis event, bukan `KFold`.**
Sudah diukur: `KFold` biasa memberi 0,2654 vs `GroupKFold` 0,2962 — optimisme palsu 0,031
karena record gempa yang sama bocor antar-fold lewat `depth_km` identik.

**3. Jangan normalisasi amplitudo per-record.**
Waveform **tidak** dinormalisasi (nol record berpuncak tepat 1.0; amplitudo membentang
5 orde magnitudo). Skala absolut adalah prediktor fisik utama magnitudo — normalisasi
per-record membuangnya.

**4. Sample weighting adalah gain terbesar dan termurah.**
`sample_weight = w(M) / n_record_per_event` memangkas error **18%** tanpa fitur baru.
Faktor pertama meniru tail-weighting, faktor kedua meniru event-balancing.

## Hasil (OOF, GroupKFold berbasis pseudo-event)

Baseline EDA (`eda.ipynb`, HistGradientBoostingRegressor + loss MAE):

| Setup | EB-TWMAE |
|---|---|
| `sample_submission` (konstan 5.2) | 0,4670 |
| Metadata saja | 0,4572 |
| Fitur fisika saja | 0,3061 |
| Metadata + fisika | 0,2962 |
| **+ sample weighting** | **0,2420** |

Komponen pipeline `notebook_3.ipynb` (LightGBM + 3 seed):

| Tahap | EB-TWMAE |
|---|---|
| A: 196 fitur | 0,2160 |
| B: agregat grup penuh | 0,2057 |
| Blend A+B (w_B = 0,35) | 0,2031 |
| + smoothing per event (desimal saja) | 0,1904 |
| **+ ekspansi per-subset → FINAL** | **0,1855** |

| Notebook | CV | `bias_rnd` | LB aktual |
|---|---|---|---|
| notebook_1 | 0,1826 | +0,076 | **0,2005** |
| notebook_2 | 0,1789 | +0,137 | **0,2262** ❌ |
| notebook_3 | 0,1855 | +0,047 | **0,1996** ✅ |
| notebook_4 | 0,1850 | +0,049 | tidak disubmit |
| notebook_5 | 0,1790 | +0,056 | belum (prediksi 0,1942) |

**CV terbaik justru LB terburuk.** Konfigurasi di `submission/notebook_*_score.json`,
riwayat lengkap di `submission/LEADERBOARD.md`.

## PALING PENTING: CV dan LB pernah bergerak BERLAWANAN

notebook_2 CV membaik 0,0037 tapi LB memburuk 0,0257. Jangan pernah memilih kandidat
hanya dari CV. Riwayat lengkap: [`submission/LEADERBOARD.md`](submission/LEADERBOARD.md).

### Mekanismenya: prior katalog yang tidak bisa ditransfer

Di train, tipe depth berkorelasi dengan magnitudo — depth bulat rata-rata **M 5,45** vs
depth desimal **M 5,19**. Itu artefak katalog (kedalaman tak terselesaikan → nilai default
10,0/35,0 km, dan gempa besar lebih sering di sana), bukan fisika.

Fitur apapun yang membiarkan model **mengenali tipe depth** akan dipakai sebagai jalan
pintas: naikkan prediksi untuk depth bulat. Karena metrik membobot gempa besar 2,5×, itu
**memperbaiki CV**. Tapi proporsi depth-bulat 32% di train vs **51% di test**, jadi prior
itu merugi di LB.

notebook_2 memasang indikator paling terang-terangan: `grp_size = NaN` ⟺ depth bulat.
Akibatnya bias OOF pada subset depth-bulat melonjak +0,076 → +0,137, dan LB ikut jeblok.

### Diagnostik wajib: `bias_rnd`

```python
MR = rnd_tr & (d_tr < 100)
bias_rnd = oof[MR].mean() - y[MR].mean()
```

Sejauh ini memprediksi kegagalan LB jauh lebih baik daripada CV.
**Tolak kandidat dengan `bias_rnd` > ~0,08 berapapun bagusnya CV.**

### Ekspansi varians harus dipusatkan PER SUBSET

`p_mean + alpha*(p - p_mean)` global mendorong menjauh dari mean keseluruhan, sehingga
subset depth-bulat (yang rata-ratanya di atas mean) ikut terdorong naik — memperbesar
`bias_rnd`. Memusatkan ekspansi di mean tiap subset menghilangkan efek samping ini:
`bias_rnd` +0,076 → +0,047 dengan ongkos CV cuma 0,003.

## Koreksi komposisi: berguna, tapi ada syaratnya

CV mentah **selalu optimis** dibanding LB, dan itu bukan overfitting. Smoothing per event
hanya berlaku untuk record berdepth desimal; proporsinya **68% di train tapi hanya 49% di
test**. Ini menjelaskan 72% dari selisih CV→LB notebook_1 (0,1826 vs 0,2005).

Selalu evaluasi pakai skor yang ditimbang ulang ke komposisi test:

```python
lb_est = 0.49 * skor_event_depth_desimal + 0.51 * skor_event_depth_bulat
```

Akurasinya: notebook_1 meleset 0,005 (baik), notebook_2 meleset 0,036 (gagal total).
Metode ini mengasumsikan performa per-subset ikut pindah ke test — asumsi yang runtuh
persis ketika model punya bias per-subset. **Hanya valid kalau `bias_rnd` kecil.**

## JANGAN mask fitur grup jadi NaN (sudah dicoba, LB jeblok)

Penalarannya kelihatan benar: agregat grup untuk `depth = 10.0` mencampur 1.633 record dari
21 gempa berbeda, jadi memang derau. Masking memperbaiki CV Model B 0,2057 → 0,1952.

**Tapi LB memburuk 0,2005 → 0,2262.** Yang keliru bukan membuang informasinya, melainkan
membuangnya **dengan cara yang meninggalkan penanda** — `NaN` jadi indikator sempurna tipe
depth, dan model memakainya untuk menerapkan prior katalog train.

Pakai fitur grup versi **penuh** (tanpa masking), seperti notebook_1 dan notebook_3.

## Kemurnian depth-bulat naik terhadap kedalaman

| Rentang | Grup murni |
|---|---|
| < 20 km | 0% (default katalog: 10,0 / 5,0) |
| 20–50 km | 32% |
| 50–100 km | 68% |
| > 100 km | 83% (gempa dalam asli) |

Karena itu depth bulat **≥ 100 km** boleh di-smooth (lam 0,5); yang dangkal jangan sama sekali.

Catatan: metadata mentah saja bahkan **kalah dari tebakan konstan terbaik** (0,4452).
Seluruh sinyal ada di waveform.

## Fitur yang sudah terbukti

Pipeline: high-pass Butterworth 0,075 Hz → integrasi kumulatif → peak per window.

- **Pd** (2x integrasi) dan **Pv** (1x) jauh mengalahkan **Pa** (mentah). Sesuai literatur EEW.
- Multi-window `[0.5, 1, 2, 3, 4]` detik setelah P. Pd puncak di 2 detik lalu **menurun** —
  jangan asal pakai window terpanjang.
- `log_dist` sebagai koreksi jarak: Pd(2s) r = 0,489 → 0,551 saat digabung.
- `tau_c` **tidak berguna** (r ≈ −0,07). Sudah diuji, tidak perlu dicoba lagi.

## Dua trik yang memberi lompatan terbesar di `notebook_1.ipynb`

**Smoothing per event (−6,3%).** Metrik merata-ratakan error per gempa, jadi menurut
ketaksamaan Jensen memberi prediksi yang sama ke semua stasiun dalam satu gempa
**tidak pernah memperburuk** MAE per-event. Kuncinya grouping: `depth_km` **desimal**
(84.18, 225.43) adalah hasil inversi presisi dan 98% murni per magnitudo — aman di-smooth.
`depth_km` **bulat** (10.0, 35.0) adalah nilai default katalog, cuma 51% murni — jangan
di-smooth. Pakai median, bukan mean (tahan outlier stasiun ter-clip).

**Ekspansi varians (−4,1%).** `p_mean + alpha*(p - p_mean)` dengan alpha 1,15. Smoothing
memperkuat kompresi prediksi ke arah mean, padahal metrik membobot ekor 2,5×.


## Tiga hal yang berhasil di `notebook_5.ipynb`

**1. Target residual relasi EEW (gain terbesar).** Pohon keputusan **tidak bisa
mengekstrapolasi** — prediksinya terkurung di rentang nilai daun. Padahal metrik membobot
ekor 2,5×. Perbaikannya: fit ridge linear **di dalam fold** lebih dulu, boosting hanya
memodelkan residualnya.

```python
A_BASE = ["Cd_2","Cv_2","Ca_4","logdist","loghypo","logE","snr_db"]
rg = Ridge(alpha=1.0).fit(Xa[ti], y[ti], sample_weight=SW[ti])
m.fit(X.iloc[ti], y[ti] - rg.predict(Xa[ti]), ...)   # prediksi = m.predict(..) + rg.predict(..)
```

Model B 0,2057 → **0,2009**. Versi paling sederhana yang menang; semua variasi lebih buruk
(daftar di bagian "sudah dicoba").

**2. Bobot blend terpisah per subset.** `lb_est = 0,49·dec + 0,51·rnd` dihitung dari dua
himpunan event yang saling lepas, jadi bobot boleh dipilih terpisah untuk tiap sisi — itu
mengoptimalkan `lb_est` langsung, bukan proxy. Menang **12/12 belahan holdout**.
Di sinilah importance weighting akhirnya berguna: sebagai kandidat khusus **sisi bulat**
(bobot 0,58 di sana), bukan dipasang global (di sana ia rugi).

**3. Smoothing depth bulat & dalam** (≥100 km, lam 0,35). Ini sebenarnya ada di nb2 tapi
ikut terbuang waktu nb2 dibatalkan — padahal kegagalan nb2 disebabkan masking fitur grup,
bukan ini. Kemurnian grup naik terhadap kedalaman (83% di >100 km). Gain 0,0006.

**Wajib: ukur optimisme pemilihan bobot, jangan asumsikan nol.** Cari argmin di ribuan
undian bobot lalu laporkan skornya = menipu diri sendiri. Protokolnya: belah event dua,
pilih bobot di satu belahan, ukur di belahan lain. Di nb5 optimismenya 0,0035 (separuh
data) → koreksi +0,0025 untuk seleksi data penuh. `lb_est` mentah 0,1907 dilaporkan
sebagai **0,1932**.

## Grouping event terbukti MUSTAHIL — jangan coba metode clustering lagi

`notebook_5` membalik pertanyaan: bukan "metode clustering mana yang jalan", tapi
**"apakah co-membership event bisa diprediksi sama sekali?"** Classifier pasangan pada
73.088 pasangan record bulat-dangkal, split by event:

| Set fitur | AUC |
|---|---|
| hanya proxy amplitudo | 0,570 |
| tanpa amplitudo | 0,548 |
| semua | 0,568 |

**AUC 0,57.** Dua record dari gempa yang sama tidak lebih mirip daripada dua record dari
gempa berbeda, selain lewat magnitudo yang justru sedang diprediksi. Ini membatasi setiap
metode grouping sekaligus dan menjelaskan seragam kenapa keduabelas percobaan sebelumnya
gagal.

### Aritmetika 0,18

`dec` = 0,155 (oracle 0,153 — habis). Untuk 0,18, `rnd` harus turun ke 0,206 dari 0,226,
sementara oracle grouping sempurna cuma sampai 0,187. Artinya 0,18 menuntut memanen
**setengah headroom grouping yang tidak ada sinyalnya**. Peringkat 1 kemungkinan besar
memakai informasi yang tidak ada di 5 detik waveform + 4 kolom metadata ini.

## TEMUAN TERBESAR SESI notebook_6: metrik CV sendiri yang cacat

`notebook_5` disubmit dan **LB-nya 0,2063** — lebih buruk dari notebook_3 (0,1996), padahal
prediksinya berkorelasi 0,98 dengan nb3 dan `lb_est`-nya memperkirakan 0,1942. Ini kegagalan
prediksi kedua setelah nb2. Penyebabnya akhirnya ketemu, dan bukan di modelnya.

### Mekanisme: pseudo-event menggabung gempa, dan itu merusak pembobotan metrik

`ev = groupby(["depth_km","magnitude"])` menghasilkan grup sebesar **401 record** di sisi
depth-bulat (semua record `depth = 10.0` dengan magnitudo sama dilebur jadi *satu* event).
Di test, 745 record ada di `depth = 10.0` — realistisnya itu ~90 gempa terpisah, bukan satu.

Karena EB-TWMAE menimbang **per event**, satu pseudo-event raksasa bermagnitudo 5,1 dapat
bobot 1,0 di CV padahal di LB ia jadi ~50 event dengan total bobot 50. Sebaliknya pseudo-event
kecil bermagnitudo 6,8 (3 record) tetap dapat bobot 2,5 di kedua tempat. Efeknya: **CV
melebih-lebihkan bobot ekor di sisi depth-bulat sebesar ~3×.**

| Bobot metrik pada sisi depth-bulat | CV (pseudo-event) | realistis |
|---|---|---|
| event M >= 5,5 | 0,891 | 0,638 |
| event M >= 6,5 | **0,155** | **0,052** |

Semua tuning sisi bulat selama ini (alpha ekspansi, importance weighting, bobot blend
per-subset di nb5) mengoptimalkan target yang over-weight ekor 3×. Itulah kenapa "CV selalu
membaik kalau prediksi ekor didorong naik" dan kenapa nb5 — yang mendorong varians sisi bulat
naik (sd 0,384 -> 0,413) — justru rugi di LB.

### Perbaikannya: evaluasi dengan event yang dipecah realistis

```python
def make_ev_real(seed, chunk=8):
    # pecah pseudo-event depth-bulat DANGKAL (<100 km) jadi potongan ~8 record,
    # seukuran event nyata di test. Depth >= 100 km JANGAN dipecah (67-100% murni).
```
Rata-ratakan 8 undian acak -> `cv_real`, `part_real`, `lb_real`. Pakai ini sebagai kriteria
utama, bukan `eb_twmae` mentah.

Efeknya langsung terlihat: optimum `alpha` ekspansi sisi bulat bergeser dari 1,15 (kriteria
lama, monoton membaik) ke **1,05** (kriteria realistis, ada optimum interior). Persis arah
yang ditunjukkan LB.

**Catatan kalibrasi:** `lb_real` bias rendah ~0,005 sebagai penduga absolut (nb3: `lb_real`
0,1945 vs LB 0,1996). Pakai untuk **memeringkat** kandidat, bukan memprediksi angka LB.

### Kemurnian grup depth-bulat vs kedalaman (diukur ulang, per record)

| Rentang | grup murni | record di grup murni |
|---|---|---|
| < 20 km | 0% | 0% |
| 20-50 km | 32% | 10% |
| 50-100 km | 68% | 60% |
| 100-150 km | 67% | 38% |
| >= 150 km | **100%** | **100%** |

Di test, `depth = 243.0` (68 record) dan `375.0` (47 record) hampir pasti masing-masing
**satu gempa dalam** — 115 dari 137 record depth-bulat-dalam.

### Sample weighting: cap `n_record_per_event` TIDAK berhasil

Hipotesisnya masuk akal — kalau pseudo-event depth-bulat 57x lebih besar dari event nyata,
`w(M)/cnt` menekan record itu 57x terlalu keras. Diuji `cnt` di-cap 5/8/15/30, `sqrt(cnt)`,
dan tanpa pembagi sama sekali:

| SW | A: lb_real | bias_rnd | B: lb_real | bias_rnd |
|---|---|---|---|---|
| `w/cnt` (baseline) | 0,2165 | +0,040 | **0,2097** | +0,064 |
| `w/min(cnt,30)` | 0,2158 | +0,021 | 0,2130 | +0,045 |
| `w/min(cnt,8)` | 0,2185 | −0,011 | 0,2243 | +0,026 |
| `w/sqrt(cnt)` | **0,2142** | **+0,006** | 0,2226 | +0,039 |
| `w(M)` saja | 0,2291 | −0,040 | 0,2440 | −0,005 |

Capping memang memangkas `bias_rnd` drastis (+0,040 -> −0,011) tapi skornya memburuk. Yang
menang justru **`w/sqrt(cnt)` untuk Model A**: skor terbaik *dan* bias hampir nol. Untuk
Model B (fitur grup) pembagi `cnt` penuh tetap yang terbaik. Jadi keduanya dipakai sebagai
kandidat blend yang saling melengkapi, bukan salah satu menggantikan yang lain.

## KOREKSI BESAR: "grouping event mustahil" ternyata SALAH

`notebook_5` menyimpulkan grouping mustahil dari classifier pasangan ber-AUC 0,57. Uji itu
**cacat di labelnya**: ia dilatih pada record depth-bulat-dangkal, di mana "event yang sama"
didefinisikan oleh `groupby(depth, magnitude)` — grup yang melebur sampai 401 record dari
puluhan gempa berbeda. Jadi mayoritas pasangan berlabel "positif" sebenarnya **bukan** dari
gempa yang sama. AUC 0,57 mengukur kualitas label, bukan kemungkinan grouping.

Uji yang benar memakai sisi **depth-desimal**, di mana event-nya asli (98% murni). Untuk
meniru situasi depth-bulat, pasangan hanya diambil di dalam pita kedalaman sempit dan semua
fitur turunan `depth` dibuang. Split by event, 84.250 pasangan:

| Set fitur | AUC |
|---|---|
| hanya `abs(delta prediksi magnitudo)` | 0,608 |
| **tanpa proxy amplitudo sama sekali** | **0,699** |
| semua fitur | **0,750** |

Co-membership **bisa** diprediksi, dan 0,699 tanpa amplitudo membuktikan sinyalnya bukan
sekadar "magnitudonya mirip" — ada identitas sumber nyata di bentuk spektrum, durasi, dan
polarisasi.

### Headroom-nya juga jauh lebih besar dari yang dikira

Diukur ulang dengan metrik terkoreksi (`lb_real`, event dipecah realistis):

| | sekarang | oracle grouping | headroom |
|---|---|---|---|
| sisi desimal | 0,1541 | 0,1488 | 0,0053 |
| **sisi bulat** | **0,2188** | **0,1596** | **0,0592** |
| gabungan | 0,1871 | 0,1543 | 0,0328 |

Aritmetika 0,18 versi lama ("butuh setengah headroom yang tidak ada sinyalnya") batal.
Dengan metrik terkoreksi, `lb_real` 0,175 hanya menuntut ~20% dari headroom grouping sisi
bulat — dan sinyal grouping-nya terbukti ada.

### ...tapi headroom itu tetap TIDAK BISA dipanen (ini yang sudah tuntas diuji)

Sinyalnya ada, tapi tidak actionable. Divalidasi di sisi desimal dengan `depth`
disembunyikan (pool = pita kedalaman, 3-fold split by event, AUC holdout **0,79**):

| metode | % headroom oracle yang direbut |
|---|---|
| soft smoothing, `w = prob^gamma`, semua tetangga | −125% s/d **+1,0%** |
| soft smoothing, top-k tetangga (k=8/15) | −44% s/d +0,8% |
| threshold keras `prob>=0,70` (presisi pasangan 0,86) | −6,0% s/d −0,9% |
| threshold keras `prob>=0,95` (presisi pasangan **0,98**) | **+0,3%** |

Sebabnya jelas begitu dilihat: classifier hanya yakin untuk pasangan yang **prediksinya sudah
mirip**, jadi merata-ratakannya tidak mengubah apapun (recall di ambang tinggi nyaris nol).
Di ambang rendah recall naik tapi rata-ratanya mencampur gempa berbeda, dan bias yang masuk
lebih besar dari derau yang dibuang.

**Kesimpulan yang benar:** bukan "co-membership tidak bisa diprediksi" (bisa, AUC 0,79),
melainkan **"co-membership yang bisa diprediksi tidak membawa informasi baru di luar
magnitudo yang sudah diprediksi"**. Efeknya sama: jangan pakai jalur ini lagi. Bedanya,
sekarang alasannya benar dan batasnya terukur.

## notebook_7: delapan keluarga ide, tujuh gagal

Ringkas di [`submission/LEADERBOARD.md`](submission/LEADERBOARD.md). Tiga hal penting:

**1. ~~`lb_real` melebih-lebihkan gain, pakai rasio 0,44~~ — KELIRU, sudah dikoreksi.**
Kesimpulan itu diambil dari 2 titik (nb3 -> nb6) dan terbantah di nb6 -> nb8, yang rasionya
justru **1,24**. Rasio dari 2 titik tidak bermakna: selisih `lb_real`-nya kecil (0,0100)
sehingga sangat sensitif terhadap derau LB, dan LB publik cuma 30% data test.
**Pakai model offset tetap** `LB ~ lb_real + 0,0082`, bukan rasio.

**2. Keputusan kita stabil terhadap tebakan `chunk`.** Bobot blend yang dipilih praktis
optimal di chunk 3, 8, dan 20 (selisih <= 0,0007). Yang bergeser cuma `a_rnd` optimum
(1,05 -> 1,15 seiring chunk membesar); dipakai 1,05, sisi konservatif.

**3. Diagnostik transfer meng-override metrik seleksi.** Koreksi bias residual lolos semua
uji internal tapi menaikkan mean prediksi subset depth-bulat ke 5,285 -- wilayah yang dua kali
terbukti merugikan di LB. Ditolak meski `lb_real` membaik.

### Taksiran kedalaman dari waveform (BERHASIL, kecil)

`depth = 10.0` adalah default katalog. Regressor kedalaman dilatih **hanya di record
depth-desimal**, semua fitur turunan depth dibuang -> R2 0,458 di holdout event desimal;
median taksiran untuk `depth = 10.0` adalah **19,2 km**. Fitur `dep_hat`, `loghypo_hat`,
`H*` memberi resA 0,2101 -> 0,2088 dan resB 0,2036 -> 0,2031, **seluruhnya dari sisi bulat**.

### CNN target-residual (BERHASIL, kecil)

Trik target residual anchor ridge dari nb5 menolong CNN juga: `lb_real` 0,2232 -> 0,2206,
dan di blend ia menggantikan hampir seluruh bobot `cnn_sqrt`.

## TEROBOSAN notebook_8: model deep-nya yang kurang dilatih, bukan datanya yang habis

Setelah ~25 keluarga ide memberi <= 0,001, satu keluarga perubahan memberi **−0,0084
`lb_real` dan menang 12/12 belahan**: CNN v3.

| CNN | `lb_real` | catatan |
|---|---|---|
| v1/v2 (waveform mentah) | 0,2494 / 0,2447 | konvolusi tidak bisa belajar dari rentang 5 orde magnitudo |
| MagNet-style (nb6) | 0,2232 | bentuk dinormalisasi + `log10(peak)` disuntik balik sebagai skalar |
| + target residual anchor | 0,2206 | trik nb5 ternyata berlaku untuk CNN juga |
| **v3** | **0,2091** | lihat di bawah |

Empat perubahan sekaligus di v3:
1. **Multi-task**: kepala kedua memprediksi `log10(depth)`, dihitung **hanya untuk record
   depth-desimal** (bobot 0,15). Memaksa jaringan belajar fitur kedalaman sumber.
2. **Augmentasi derau fisik**: tempel jendela pre-P (200 sampel) dari record lain, amplitudo
   acak 0-0,6x. Ini derau stasiun sungguhan, bukan Gaussian sintetis.
3. Blok SE + jaringan lebih lebar (w=64, 5 blok).
4. Jadwal lebih panjang: 80 epoch, rata-rata 10 epoch terakhir, 3 seed.

Varian: `cnn3_dir` (target langsung, bukan residual) 0,2116 dengan korelasi 0,926 -> tetap
memberi diversitas; `cnn3_avg` (rata-rata 6 seed) **0,2074**.

Hasil di blend: **bobot gabungan CNN 0,53**, korelasi cuma 0,878 dengan LightGBM.
`lb_real` 0,1845 -> **0,1762**, dan **kedua sisi** membaik (dec 0,1506 -> 0,1437,
rnd 0,2171 -> 0,2074).

**Pelajarannya:** waktu 25 ide gagal berturut-turut, kesimpulan "datanya sudah habis" itu
menggoda dan salah. Yang habis adalah *keluarga* ide yang sedang digali (post-processing,
kalibrasi, grouping, reweighting). Keluarga yang belum digarap serius — model deep — masih
punya isi, dan ukurannya jauh lebih besar dari semua tambalan itu digabung.

## notebook_8 DISUBMIT: LB 0,1849 — peringkat 4 -> peringkat 2

Konfirmasi terkuat sejauh ini bahwa arah model deep itu benar. `lb_real` 0,1845 -> 0,1762
(−0,0083) menghasilkan LB 0,1952 -> **0,1849** (−0,0103) — gain-nya transfer **lebih besar**
dari yang diukur di OOF, bukan lebih kecil.

| | `lb_real` | LB | offset |
|---|---|---|---|
| notebook_3 | 0,1945 | 0,1996 | +0,0051 |
| notebook_6 | 0,1845 | 0,1952 | +0,0107 |
| **notebook_8** | **0,1762** | **0,1849** | +0,0087 |

### Di mana kita berhenti, dan apa yang tersisa

Peringkat 1 ada di 0,1837, selisih **0,0012** — itu setara `lb_real` turun 0,0007–0,0032.
Bukan jurang. Yang sudah dicoba dan jenuh vs yang belum:

**Sudah jenuh (jangan diulang):**
- Post-processing, kalibrasi, reweighting, grouping — ~25 keluarga ide, semua <= 0,001.
- Seed CNN tambahan: `cnn3` + `cnn3_s2` (6 seed) menang, tapi seed ke-7 dst tidak akan
  menambah — korelasi antar-seed sudah 0,988.
- Arsitektur alternatif: **CNN + BiGRU + attention** (0,2101 sendirian, setara CNN v3) tapi
  korelasi 0,967 — di blend malah **memburuk holdout, menang 1/12**. Ditolak.

**Belum dicoba sama sekali (urutan prioritas untuk sesi berikutnya):**
1. **Pre-training self-supervised** di waveform train+test (masked autoencoding / contrastive).
   12.805 waveform tanpa label bisa dipakai semua; ini satu-satunya cara menambah data
   efektif. Transduktif dan sah.
2. **CNN v3 lebih besar / lebih lama** — v3 baru w=64, 80 epoch. Belum pernah dicek apakah
   sudah mentok kapasitas atau masih underfit.
3. **Augmentasi lebih agresif** — sekarang cuma rotasi horizontal, flip vertikal, dan tempel
   derau pre-P. Belum: time-jitter di sekitar P, channel dropout, cutout.
4. **Model deep dengan target berbeda** — misal klasifikasi bin magnitudo halus + expectation,
   atau quantile head yang cocok dengan bobot metrik.

### Aturan yang terbukti dan harus dipertahankan

1. Nilai kandidat dengan `lb_real`, **jangan pernah** `eb_twmae` mentah.
2. Bobot blend dipilih lewat split-by-event 12 belahan, bobot final = **rata-rata lintas
   belahan**, dan optimisme seleksi selalu diukur.
3. Kandidat ke-N selalu bisa menurunkan `lb_real` mentah di data tempat bobotnya dipilih.
   **Yang menentukan adalah gain holdout dan berapa belahan yang dimenangkan.** CNN+GRU
   menurunkan skor mentah 0,1762 -> 0,1756 tapi menang 1/12 — ditolak, dan itu benar.
4. Cek `bias_rnd`, mean, dan sd prediksi subset depth-bulat sebelum tiap submit.

## Sudah dicoba dan TIDAK berhasil — jangan diulang

- **XGBoost / HistGBM / ExtraTrees**: lebih buruk sendirian (0,2205 / 0,2245 / 0,2442) dan
  korelasi 0,99 dengan LightGBM → blending nol perbaikan.
- **1D CNN** pada waveform mentah (GPU, augmentasi rotasi horizontal): OOF 0,2494, hanya
  menambah 0,0005 setelah smoothing. **Penyebabnya ketemu di notebook_6: waveform-nya tidak
  dinormalisasi.** Amplitudo membentang 5 orde magnitudo, konvolusi tidak bisa belajar dari
  itu. Perbaikannya normalisasi **bentuk** gelombang lalu suntik balik `log10(peak)` sebagai
  skalar (gaya MagNet, Mousavi & Beroza) + kanal kecepatan/simpangan hasil integrasi (9 kanal)
  + skalar jarak/kedalaman/SNR. **OOF 0,2250**, korelasi dgn LightGBM cuma 0,91, dan di blend
  notebook_6 ia dapat bobot **0,23**. Catatan "jangan normalisasi per-record" di atas berlaku
  untuk fitur pohon, **bukan** untuk CNN.
- **Tuning hyperparameter**: 18 konfigurasi hanya merentang 0,2151–0,2230.
- **`tau_c`**, kurtosis/skew/ZCR, growth rate: nyaris tidak menggerakkan skor.
- **10-fold / lebih banyak seed**: selisih < 0,001.
- **Filter bank** 8 pita x 4 window (+92 fitur): 0,2160 vs 0,2151 — sudah tertangkap fitur spektral.
- **Fit atenuasi per event** (intercept regresi log-amp vs log-jarak): 0,1974 vs 0,1956.
- **Kalibrasi isotonic** sebagai pengganti ekspansi linear: 0,1971 vs 0,1798 — jauh lebih buruk.
- **KMeans di ruang prediksi** untuk memecah grup depth-bulat: self-fulfilling, tidak menambah info.
- **Agregasi berbobot reliabilitas** (SNR / jarak / inverse-error): setara median biasa.
- **Presisi tersembunyi `depth_km`**: tidak ada, CSV memang menyimpan `10.0`.
- **Kebocoran urutan baris / `sample_id`**: tidak ada, data teracak dan ID berupa hash.
- **Sample weighting `w(M)^p`** (p=0,5/1,5/2): CV 0,2165–0,2216 vs 0,2151. Trade-off murni —
  menaikkan akurasi ekor selalu memperburuk CV.
- **Boost bobot ekor eksplisit** (M>=6.5 dikali 2 atau 3): CV 0,2210–0,2221. MAE ekor membaik
  (0,374 -> 0,307) tapi metrik keseluruhan memburuk.
- **Objective quantile** (alpha 0,55/0,60/0,65): CV 0,2187–0,2282, dan `bias_rnd` melonjak.
- **Koreksi stasiun dari sidik-jari noise pre-P**: klaster noise memang menjelaskan residual
  (R²=0,067 vs kontrol acak 0,007 — sinyal nyata), tapi menguranginya memperburuk CV
  0,2155 -> 0,2185. Yang dibuang justru bias yang disengaja weighted loss.
- **PCA noise pre-P sebagai fitur**: CV 0,2171–0,2174 vs 0,2151.
- **Monotonic constraints**: LightGBM tidak mendukungnya dengan objective `regression_l1`.
- **CNN v2** (residual+SE, augmentasi rotasi horizontal, rata-rata 8 epoch terakhir tanpa
  intip validasi): OOF **0,2447** — jujur, dan lebih baik dari CNN v1 (0,2494 yang bias
  optimis). Tapi korelasi dengan Model A 0,903, jadi blend hanya menyumbang −0,0007.
- **Kuantisasi / pembuangan `depth_km` dari fitur** untuk menutup "bocor tipe depth":
  `bias_rnd` **tidak turun sama sekali** (+0,047 → +0,050). Depth memang terbaca dari
  waveform, jadi jalur itu tidak bisa ditutup lewat metadata. Membuang `grp_size` juga nol.
- **Importance weighting komposisi secara global** (record bulat ×2,235): CV 0,1879
  vs 0,1856. Berguna **hanya** sebagai kandidat blend khusus sisi bulat.
- **Snapping prediksi ke grid 0,1** (magnitudo memang diskrit, 32 nilai): 0,1994 vs 0,1990.
  Derau prediksi (~0,19) jauh lebih besar dari langkah grid (0,05), jadi tidak ada gunanya.
- **Klasifikasi ordinal 32 kelas + weighted median**: 0,2693/0,2595 mentah vs 0,2161/0,2065.
  Jauh lebih buruk. **Pooling posterior antar-record** dalam grup: 0,2636. Juga jauh lebih buruk.
- **`linear_tree=True`** (daun linear LightGBM): 0,2225. **Anchor sebagai fitur** biasa
  alih-alih target residual: 0,2076. Yang menolong khusus *target* residualnya.
- **Variasi anchor**: Huber (0,2020 vs ridge 0,2010), set fitur lebih besar (0,2019–0,2063),
  `alpha` selain 1,0, membobot ekor saat memfit anchor (0,2024–0,2038). Semua lebih buruk.
- **Smoothing adaptif per pita ukuran grup** untuk depth bulat-dangkal: optimum di lam = 0
  untuk semua pita. **Smoothing-kNN di ruang prediksi**: 0,2252 vs 0,2260 — di dalam derau.
- **MLP di ruang fitur**: divergen (OOF 0,778). Yang penting dari kegagalan ini: pencarian
  bobot blend **tetap memberinya bobot 0,36** dan "memperbaiki" skor. Jaga jumlah kandidat
  tetap sedikit, dan selalu ukur optimisme seleksi.

- **Koreksi covariate shift lewat density ratio** train-vs-test (classifier AUC 0,80 -- shift-nya
  nyata): resA `lb_real` 0,2245 vs 0,2101, resB 0,2200 vs 0,2036. Sama seperti importance
  weighting kasar, arahnya salah.
- **CNN 2D di spektrogram STFT** (33x64, 3 komponen): `lb_real` 0,2536, jauh di bawah CNN 1D
  (0,2206). Korelasinya rendah (0,84) sehingga pencarian bobot tetap memberinya 0,11 -- pola
  menipu yang sama dengan MLP di nb5.
- **Cari hyperparameter ULANG di bawah metrik terkoreksi** (8 konfigurasi: leaves 15/63,
  colsample 0,4, `reg_lambda` 10, `min_child_samples` 150, lr 0,005, huber, subsample 0,5):
  terbaik 0,2029 vs baseline 0,2031. Kesimpulan HP lama ternyata tetap berlaku.
- **Koreksi bias residual** (geser konstan per subset + tren linear SNR/Pd): gain holdout
  -0,0007 (menang 7/12) tapi menaikkan mean prediksi subset bulat ke 5,285. Ditolak.
- **Smoothing penuh grup depth-bulat-dalam di test**: sd prediksi di `depth = 375,0` cuma
  0,089 (vs median sd dalam-event 0,140) -- sudah rapat, tidak ada yang bisa dihaluskan.

- **Kebocoran depth train-test**: hanya 2 nilai depth desimal (12,7 dan 23,24) plus 1 depth
  bulat (105,0) muncul di train **dan** test. Diperiksa: model menolak ketiganya dengan tegas
  (depth 12,7 -> model 5,37 vs train M 4,4; itu **6,6 sigma** di atas sebaran error median-grup
  yang sd-nya 0,146). Jadi itu tabrakan nilai, bukan gempa yang sama — split kompetisi memang
  per-event. Jangan cari kebocoran ke sana lagi.
- **Stacking** (meta-LightGBM di atas prediksi OOF 9 base model + fitur konteks): `lb_real`
  0,1847-0,1849 vs blend linear 0,1845, tapi **`bias_rnd` meledak +0,027 -> +0,095**. Stacker
  memakai `is_rnd`/`depth_km` untuk menghafal prior katalog — mode kegagalan nb2 persis.
  Blend linear justru aman karena tidak bisa mengkondisikan pada fitur.
- **Koreksi site term dari sidik-jari derau pre-P, versi dipusatkan + shrink empirical-Bayes**
  (bentuk spektrum derau -> PCA 12 -> KMeans 40/100/250 klaster): **R2 out-of-fold NEGATIF di
  semua konfigurasi** (−0,08 s/d −0,001). Efek klaster tidak generalisasi antar-fold sama
  sekali. Klaim lama "R2=0,067, sinyal nyata" tidak bertahan waktu diukur out-of-fold.
- **10-fold** (tiap model fold melihat 90% data, bukan 80%), diuji ulang di bawah metrik
  terkoreksi pada 5 kandidat terbaik: 0,2142/0,2108/0,2032/0,2036/0,2028 vs 5-fold
  0,2142/0,2088/0,2031/0,2047/0,2030. Nol perbaikan sistematis, dan `bias_rnd` `resB_dep`
  malah naik +0,064 -> +0,074.
- **Koreksi ekor** `p' = p + c*max(0, p - t)`: optimum jujurnya cuma `c = 0,1` (terpilih
  12/12 belahan), gain −0,0007.

  > **KOREKSI 22 Agu 2026 (sore).** Paragraf lama di sini mengklaim kalibrasi yang dibin
  > menurut prediksi "menunjukkan under-prediction nyata di ekor — koreksi +0,13 s/d +0,17
  > untuk prediksi > 6,0". **Itu terbalik.** Diukur ulang pada blend nb8:
  >
  > | bin prediksi | n | mean pred | mean y | koreksi yang dibutuhkan |
  > |---|---|---|---|---|
  > | 5,9–6,2 | 470 | 6,025 | 5,965 | **−0,060** |
  > | 6,2–6,5 | 248 | 6,330 | 6,270 | **−0,060** |
  > | ≥ 6,5 | 53 | 6,658 | 6,468 | **−0,190** |
  >
  > Modelnya **kelebihan** menembak di atas, bukan kekurangan. `c = 0,1` yang "cuma sedikit"
  > itu sebenarnya konsisten dengan "jangan dikoreksi sama sekali". Lihat bagian
  > "Ekor magnitudo: fatamorgana terbesar di case ini" di bawah.

- **CNN + BiGRU + attention pooling** (arsitektur gaya MagNet asli, frontend konvolusi lalu
  GRU dua arah): `lb_real` 0,2101 sendirian — praktis setara CNN v3 (0,2091) — tapi korelasinya
  0,967 dengan `cnn3_avg`. Ditambahkan ke blend: `lb_real` mentah "membaik" 0,1762 -> 0,1756,
  tapi **holdout jujur memburuk +0,0011 dan cuma menang 1/12 belahan**. Ditolak.
  Contoh bagus kenapa skor blend mentah tidak boleh dipercaya: kandidat ke-9 selalu bisa
  menurunkan angka di data yang sama tempat bobotnya dipilih.

## Plateau: di mana kita berhenti dan kenapa

Sisi depth-desimal **sudah menyentuh oracle event-sejati** — grouping lewat depth desimal
praktis sebagus mengetahui event ID. Tidak ada sisa di sana.

Sisi depth-bulat (51% record test) masih berjarak dari oracle, tapi menutupnya berarti
memisahkan gempa yang berbagi nilai depth default — semua metode gagal (lihat daftar di atas).

Model per-record berbasis **fitur** memang jenuh: penambahan fitur (filter bank, fit
atenuasi, PCA noise) konsisten memberi nol. **Tapi model deep tidak** — lihat "TEROBOSAN
notebook_8" di atas. Bagian di bawah ini ditulis sebelum itu dan terlalu pesimistis.

**Untuk konteks:** oracle dengan event ID sebenarnya memberi CV 0,1686; peringkat 1 di LB
ada di 0,18. Jadi 0,18 kira-kira setara grouping event yang mendekati sempurna. Kalau ada
jalan ke sana, bentuknya kemungkinan besar **cara identifikasi event yang belum ditemukan**,
bukan model lebih besar atau fitur lebih banyak. Polanya konsisten: tiap kali grouping
membaik skornya melompat, tiap kali model diperbaiki skornya bergeming.

Satu asumsi yang belum pernah diuji langsung di LB: apakah smoothing benar-benar membantu di
test. Estimasi komposisi menyiratkan iya, tapi itu bukti tak langsung. Submit versi tanpa
smoothing akan menutup pertanyaan itu (CV memperkirakan ~0,215, jadi nilainya di kepastian
bukan di skor).

## Catatan `is_clipped`

3,8% di test vs 1,7% di train — dua kali lipat. Record clipped punya magnitudo rata-rata
lebih tinggi (5,65 vs 5,28) dan amplitudo puncaknya **terpotong**, jadi fitur amplitudo
tidak bisa dipercaya di sana. Selalu sertakan `is_clipped` sebagai fitur.

## Format submission

Header `sample_id,magnitude`, 2.300 baris, urutan dan isi `sample_id` sama persis dengan
`test_meta.csv`.

## Sesi sesudah notebook_8 — grouping ditutup, post-processing ditutup

Rincian angka di [`submission/LEADERBOARD.md`](submission/LEADERBOARD.md). Ringkasnya:

**Empat ide non-deep diuji dengan holdout jujur, semuanya gagal.** Sidik derau pre-P
sebagai identitas stasiun (AUC co-membership cuma 0,56), agregasi grup berbobot presisi
(menang 1/12), koreksi geser record clipped (menang 3/12), dan sapuan gabungan 729
konfigurasi post-processing (menang 1/12).

**Grouping resmi ditutup.** Sudah dua usaha independen gagal memulihkannya: classifier
pasangan nb7 (AUC 0,79 tapi cuma memanen 0,3–1,0% headroom) dan sidik derau (AUC 0,56).

**Hati-hati dengan AUC co-membership dari kemiripan prediksi — itu sirkular.** Angkanya
0,981, dan itu bukan kabar baik: record satu event punya label sama, jadi model bagus
otomatis memberi prediksi mirip. Jangan pernah dibaca sebagai "grouping hampir terpecahkan".

**Median adalah agregator yang benar, bukan sekadar default.** Semua varian rata-rata
berbobot presisi (SNR, jarak, clipped) kalah. Median tahan kontaminasi grup campuran;
rata-rata berbobot tidak.

**`kurt` punya 9 nilai non-finite di train.** LightGBM menelan NaN secara native jadi ini
tidak terlihat selama 8 notebook, tapi di jaringan saraf NaN merambat ke seluruh batch.
**Fitur apa pun yang masuk model non-pohon harus lewat `nan_to_num` dulu.**

**Set-transformer atas grup depth: satu-satunya yang berhasil** (−0,0021, menang 11/12) —
dan pertama kalinya ada yang menembus sisi depth-bulat (0,2074 → 0,2004). Tapi separuh
gain-nya ternyata pergeseran rata-rata sisi bulat (+0,042), yaitu prior katalog train yang
membunuh nb2 dan nb5. Versi dengan **target di-demean per subset** menahan −0,0011 dengan
`bias_rnd` tidak bergerak, dan korelasi koreksi vs residual sejati di MR tetap 0,32.

### Aritmatika target — pakai ini sebelum menjanjikan angka

`LB ≈ lb_real + 0,0082`. Dari `lb_real` 0,1762 sekarang:

| Target LB | butuh `lb_real` | Δ |
|---|---|---|
| 0,1837 (peringkat 1) | 0,1755 | −0,0007 — satu perbaikan sedang |
| 0,1700 | 0,1618 | −0,0144 — **2× terobosan CNN v3** |
| 0,1600 | 0,1518 | **di bawah oracle-grouping 0,1543 — di luar jangkauan** |

### Yang tersisa: model deep — SUDAH SELESAI, 1 dari 5 berhasil

Sisi desimal mentok (0,1437 vs oracle ~0,1488); hampir seluruh headroom ada di sisi bulat.
Lima notebook GPU berdiri sendiri **sudah dijalankan di Kaggle (21–22 Agu 2026)**.
Sumber, versi tereksekusi, dan zip hasilnya ada di [`sudah_run/`](sudah_run/README.md);
tiap `.npz` sudah disalin ke `cache/`.

| notebook | model | keluaran `.npz` | waktu (T4) | status ide |
|---|---|---|---|---|
| `01_set_transformer` | set-transformer atas grup depth | `set2.npz` (`corr`,`cte`) | 11 mnt | ✅ **−0,0042, menang 12/12 → notebook_9** |
| `02_cnn8_inception` | Inception 1D multi-skala | `cnn8.npz` | 86 mnt | GAGAL +0,0014, menang 0/12 |
| `03_cnn7_tcn_dilatasi` | TCN dilatasi tanpa pooling | `cnn7.npz` | 124 mnt | GAGAL +0,0016, menang 1/12 |
| `04_cnn5_konvolusi_dalam` | v3 diperlebar (w=80, 6 blok) | `cnn5.npz` | 202 mnt | GAGAL +0,0012, menang 2/12 |
| `05_cnn6_transformer` | konvolusi + transformer | `cnn6.npz` | 108 mnt | GAGAL +0,0015, menang 0/12 |

Keempat CNN gagal karena **redundan**, bukan lemah: korelasinya 0,92–0,96 terhadap
`cnn3_avg`. Digabung berempat sekaligus pun rugi (+0,0012, menang 4/12). Keluarga
"arsitektur CNN 1D baru atas waveform yang sama" ditutup.

Set-transformer berhasil, **tapi hanya setelah koreksinya di-demean per subset saat
diterapkan**. Notebook Kaggle memakai koreksi mentah pada lam 0,50 dan mendorong
`bias_rnd` ke +0,059 sambil melabelinya AMAN (ambang 0,08 terlalu longgar — nb5 rugi
di +0,056). Demean di dalam training tidak cukup; model memulihkan prior katalog lewat
fitur. Demean ulang saat apply: `lb_real` 0,1718 (vs 0,1714 mentah) dengan `bias_rnd`
+0,029, tidak bergerak dari nb8. Gain holdout jujur −0,0042, menang 12/12.
Itu yang jadi `submission/notebook_9.csv`, estimasi LB **0,1800**.


Ketergantungan: notebook 01 **wajib** punya `belum_run/ref/nb8_ref.npz` (prediksi 8
kandidat nb8) karena ia mempelajari koreksi atas blend nb8. Notebook 02-05 hanya
memakainya untuk sel verdikt. Sudah ter-upload user di
`/kaggle/input/datasets/timotiuspatrick/nb8-ref/nb8_ref.npz`.

## CARA MENYERAP HASIL KAGGLE (baca ini kalau user mengunggah zip `hasil_*.zip`)

Tiap notebook menghasilkan `hasil_<nama>.zip` (~280 KB) berisi `.npz` prediksi, submission,
dan skor. **Jangan analisa manual — sudah ada skripnya:**

```bash
C:/Patrick/coding/.venv/Scripts/python.exe "Case 1/tools/serap_hasil.py" <folder-atau-zip> ...
```

Skrip itu mengekstrak `.npz` ke `cache/`, mengenali kandidat baru, lalu menjalankan
**protokol blend 12-belahan dengan semua kandidat baru sekaligus** — pertanyaan yang tidak
bisa dijawab notebook manapun sendirian, karena tiap notebook cuma melihat modelnya sendiri
plus 8 kandidat nb8. Lalu ia mencetak verdikt terhadap target LB, tiga diagnostik transfer,
dan menulis `submission/notebook_9.csv` **hanya kalau lolos ambang** (gain holdout negatif
DAN menang >= 7/12 DAN ketiga diagnostik aman). Sudah diuji: kandidat duplikat
(korelasi 0,998) benar ditolak dan tidak menghasilkan submission.

**SUDAH DIKERJAKAN untuk batch Kaggle 21–22 Agu 2026** — `notebook_9.ipynb` dibuat lewat
`tools/mk_nb9.py`. **Skor LB-nya sudah keluar: 0,1856 — GAGAL,** lebih buruk dari nb8.
Post-mortem lengkap ada di `LEADERBOARD.md` bagian "KEGAGALAN KETIGA"; ringkasnya di
bagian "Set-transformer: DITOLAK" di bawah.

Satu catatan penting dari batch itu: **skrip `serap_hasil.py` tidak cukup.** Ambang otomatisnya
akan meloloskan koreksi set-transformer versi **mentah** (gain −0,0045, menang 12/12,
`bias_rnd` +0,059) karena ambang `bias_rnd`-nya dipasang di 0,08. Itu terlalu longgar —
`notebook_5` rugi di LB pada **+0,056**. Titik kegagalan nyata yang tercatat: +0,056 (nb5),
+0,076 (nb1), +0,137 (nb2); semua submission yang menang ada di +0,027…+0,047. **Ambang yang
jujur ada di sekitar +0,05, bukan 0,08.** Verdikt otomatis apapun tetap wajib dibaca manusia.

## Set-transformer: DITOLAK setelah LB 0,1856 (notebook_9)

`notebook_9` = blend nb8 + koreksi set-transformer, `lb_real` 0,1762 → **0,1718**
(−0,0044, menang **12/12** belahan, ketiga diagnostik transfer aman). Disubmit, dan
**LB-nya 0,1856** — lebih buruk dari nb8 (0,1849). Gain −0,0044 bernilai **nol** di LB.

Post-mortem (`experiments/exp_nb9_postmortem.py`) menemukan mekanismenya:

1. **Seluruh gain hidup di sisi bulat** (0,2074 → 0,1982) sementara di sisi desimal ia
   **rugi** (0,1437 → 0,1443). Kalau ia benar-benar belajar co-membership, sisi desimal —
   yang event-nya nyata dan bisa diverifikasi — mestinya menang paling besar.
2. Yang dipelajarinya sebenarnya **"tarik ke median grup depth"**: korelasi terhadap
   operator itu +0,497 di sisi desimal, lebih tinggi dari korelasi terhadap residual sejati
   (+0,480). Di test ia merapatkan grup: sd dalam-grup sisi bulat **−14%**.
3. Di train, **24% pasangan** di dalam satu grup depth bulat punya **label identik** (`y`
   sama), jadi merapatkan mereka adalah gain gratis. Di LB event ID-nya asli, dan grup
   `depth = 10.0` berisi puluhan gempa berbeda — operasi yang sama merata-ratakan gempa
   yang magnitudonya memang berbeda.

### `lb_real` memperbaiki BOBOT metrik, bukan LABEL-nya

`make_ev_real` memecah pseudo-event raksasa supaya bobotnya realistis, tapi `y` tetap
identik untuk semua record yang berbagi `(depth, magnitude)`. Jadi **setiap metode yang
mekanismenya "seragamkan prediksi di dalam satu grup depth" dibayar berlebihan oleh
`lb_real` di sisi bulat** — berapa pun benar pembobotannya.

Ini kali **ketiga** metrik evaluasi sendiri yang jadi biang kegagalan LB: nb2/nb5 (bobot
per-event) dan sekarang nb9 (label per-event).

### Diagnostik ke-4 (uji sisi-desimal) — CABUTAN SEBAGIAN, baca ini

Sesi sesudah nb9 menetapkan aturan *"gain di sisi desimal harus negatif juga"* dan
membangun `notebook_10` untuk memaksimalkannya. **LB `notebook_10` = 0,1871, rugi 0,0022.
Aturan itu DICABUT sebagai objektif seleksi.**

Kenapa salah: sisi desimal sudah **menyentuh oracle** (0,1437 vs oracle ~0,1488). Tidak ada
lagi yang bisa dipanen di sana, jadi mengoptimalkannya cuma mengorbankan sisi bulat — 51%
metrik dan tempat **seluruh** headroom yang tersisa.

**Yang masih berlaku (versi sempit).** Gain sisi desimal tetap berguna sebagai **layar
khusus** untuk metode yang mekanismenya menyeragamkan prediksi di dalam grup: smoothing
sisi bulat, attention antar-record, pooling posterior, agregasi grup ulang. Untuk metode
seperti itu, gain yang muncul **hanya** di sisi bulat memang mencurigakan.

**Untuk apa pun yang lain — terutama pemilihan bobot blend — abaikan.**

`SideScorer` sudah tertanam di `tools/mk_kaggle.py` dan ikut tercetak di verdikt notebook
Kaggle. Angkanya tetap berguna; **kalimat "BAHAYA / TOLAK kandidat ini" yang menyertainya
sudah usang** di notebook 06/07/08 yang dijalankan 22 Agu 2026. Lihat
[`belum_run/README.md`](belum_run/README.md) bagian "Yang harus diabaikan".

### Ambang `bias_rnd`

Ambang jujur ada di **+0,05**, bukan 0,08 (nb5 rugi di LB pada +0,056). Tapi ambang ini
tidak cukup sendirian: `bias_rnd` nb9 cuma +0,029 dan nb10 +0,028, dan dua-duanya gagal.

## notebook_10 GAGAL (LB 0,1871) — Model B ternyata sah

Audit sesudah nb9 menemukan Model B (satu-satunya keluarga berfitur agregat grup) paling
condong ke sisi bulat: ia **kalah dari `resA_dep` di kedua sisi** tapi dapat bobot 0,32
murni dari dekorelasi. `notebook_10` memangkasnya ke 0,16 lewat objektif seleksi
`FD_sel = 0,80`. Keempat diagnostik membaik, `lb_real` memburuk 0,0011 — dan **LB memburuk
0,0022**.

**Kesimpulannya terbalik dari yang diduga:** agregat grup sebagai **fitur** membawa sinyal
nyata yang transfer ke test. Bobot 0,32-nya sah.

| | mekanisme | vonis LB |
|---|---|---|
| set-transformer (nb9) | menyeragamkan prediksi dalam grup secara **eksplisit** | gain palsu, −0,0007 |
| Model B | agregat grup sebagai **fitur input** | **sinyal nyata — jangan diutak-atik** |

Bedanya bukan "menyentuh grup atau tidak", melainkan **apakah ia memaksa prediksi dalam
satu grup jadi lebih mirip**. Set-transformer menurunkan sd dalam-grup test 14%; Model B
tidak melakukan apa pun ke sd itu.

### Tiga aturan yang lahir dari dua kegagalan ini

1. **Blend `notebook_8` adalah setelan baku. Berhenti mengutak-atiknya.** Dua perturbasi
   independen — menambah kandidat koreksi (nb9) dan menggeser bobot (nb10) — dua-duanya
   merugi. Pakai `cache/w_nb9.npy` + `FD_sel = 0,49` apa adanya.
2. **Jangan submit kandidat yang `lb_real`-nya lebih buruk dari juara bertahan.** nb10
   melanggar ini atas dasar teori. Satu kegagalan (nb9) bukan dasar yang cukup untuk
   membatalkan metrik peringkat yang benar 4 dari 5 kali.
3. **Satu kegagalan LB tidak boleh melahirkan aturan umum.** Post-mortem nb9 benar tentang
   *mekanismenya* tapi salah tentang *cakupannya*, dan cakupan yang terlalu lebar itu
   langsung memakan satu submission. Ketika ragu, uji cakupannya dengan perubahan
   sekecil mungkin — bukan dengan menggeser bobot 0,16.

## Batch Kaggle ke-2: `belum_run/` — hanya akurasi per-record

Setelah nb9, satu-satunya sumbu yang tersisa adalah **akurasi per-record model deep**.
Semua yang lain tertutup: grouping (2 usaha gagal), post-processing (menang 1/12),
arsitektur CNN 1D baru (4 dari 4 gagal, redundan), attention antar-record (nb9).

| # | notebook | waktu (T4) | ide |
|---|---|---|---|
| 06 | `06_augmentasi_agresif` | ~130 mnt | time-jitter picker P, channel dropout, cutout, jitter skala konsisten, mixup |
| 07 | `07_ssl_pretrain` | ~165 mnt | masked autoencoder di 12.805 waveform train+test lalu fine-tune |
| 08 | `08_head_distribusi` | ~120 mnt | kepala 41-bin label lunak, ringkasan dipilih sesudah training |

Digenerate oleh `tools/mk_kaggle2.py`. Rincian di [`belum_run/README.md`](belum_run/README.md).

`verdikt()` di `tools/mk_kaggle.py` sudah diperbarui: ambang `bias_rnd` 0,08 → **0,05**,
`LB_OFFSET` 0,0082 → 0,0096 dengan peringatan tidak stabil, dan **diagnostik ke-4 (gain
sisi desimal, lewat `SideScorer`) sekarang dihitung dan dicetak** dengan penjelasan
kegagalan nb9 kalau ia positif.

## Aritmatika menuju 0,17 — hitung ini sebelum menjanjikan apa pun

LB terbaik 0,1849. Target 0,17 menuntut **−0,0149**, yaitu **1,4× lompatan terbesar yang
pernah terjadi** di case ini (nb6 → nb8 = −0,0103, dan itu terobosan CNN v3 setelah 25 ide
gagal). Peringkat 1 ada di 0,1835 — **−0,0014**, satu perbaikan berukuran sedang.

Dan batas oracle-nya sekarang **lebih rendah dari yang tercatat**: angka "oracle grouping
`lb_real` 0,1543" dihitung dengan label degenerate yang sama, jadi sebagian headroom sisi
bulat (0,2074 → 0,1596) **ikut palsu** — persis headroom yang nb9 coba panen dan gagal.

**Yang realistis dari satu perbaikan bagus: peringkat 1 di 0,1835. 0,17 butuh sumber
informasi yang belum ditemukan siapa pun di papan ini** — peringkat 1 sendiri baru 0,1835
setelah 7 entri.


## DERAU LEADERBOARD PUBLIK SUDAH DIUKUR — baca sebelum mengejar 0,0014

LB publik cuma **30% data test**. Sampai sekarang setiap selisih LB dibaca seolah-olah
angka pasti. Diukur dengan bootstrap 30% event di OOF (`scratchpad an6`, 300 undian):

| yang diukur | sd |
|---|---|
| skor absolut di sub-sampel 30% | **0,0098** |
| selisih dua submission **mirip** (corr 0,999) | **0,0008** |
| selisih dua submission **beda** (corr 0,888) | **0,0038** |

**Konsekuensinya besar dan mengubah strategi:**

1. **Jarak ke peringkat 1 (0,0014) ada di dalam derau.** Itu selisih terhadap model tim
   lain, yang korelasinya pasti jauh di bawah 0,99 — jadi sd selisihnya orde **0,004**.
   Kita secara efektif sudah seri dengan peringkat 1; peringkat akhir di 70% data sisanya
   bisa jatuh ke mana saja. **Mengejar −0,0014 di LB publik adalah mengejar derau.**
2. **Kegagalan `notebook_9` (+0,0007) sendiri ada di dalam derau** (corr 0,994 → sd
   ~0,0008, jadi ~0,9 sd). Mekanisme yang ditemukan post-mortem tetap nyata dan tetap
   masuk akal, tapi **bukti LB-nya jauh lebih lemah dari yang tertulis**. `notebook_10`
   (+0,0022, ~2 sd) lebih meyakinkan, tapi juga bukan vonis keras.
3. Ini juga menjelaskan kenapa offset `lb_real` → LB tidak pernah stabil: penduganya
   sendiri punya sd ~0,01 terhadap skor test penuh.

**Aturan yang lahir dari ini:** yang menentukan peringkat akhir adalah **70% data yang
tidak terlihat**, jadi kandidat dipilih berdasarkan generalisasi jujur (gain holdout,
menang n/12, diagnostik transfer) — **bukan** dengan mengoptimasi ke angka LB publik.
Kebetulan itu persis aturan yang sudah dipakai, dan `notebook_8` menang di semuanya.

## Batch Kaggle ke-2: augmentasi, SSL, kepala distribusi — 3 dari 3 GAGAL

Angka lengkap di [`sudah_run/README.md`](sudah_run/README.md). Yang harus diingat:

| notebook | model | tunggal | corr maks vs nb8 | gain | menang |
|---|---|---|---|---|---|
| 06 augmentasi agresif | `cnn9_aug` | 0,2080 | **0,970** | +0,0011 | 1/12 |
| 07 pra-latih SSL | `cnn10_ssl` | 0,2112 | **0,953** | +0,0012 | 2/12 |
| 08 kepala distribusi | `cnn11_dist` | 0,2322 | 0,895 | +0,0013 | 0/12 |
| **ketiganya sekaligus** | — | — | — | **+0,0010** | **2/12** |

**Pra-latih self-supervised DITOLAK dengan bukti langsung.** Ini prioritas 1 di file ini
sejak `notebook_8` — satu-satunya cara menambah data efektif (12.805 waveform tak
berlabel), dengan hipotesis "batasannya jumlah event, bukan jumlah record". Pra-latihnya
benar-benar jalan (encoder ter-transfer, `enc_pretrain.pt` 7 MB) dan hasilnya **0,2112,
lebih buruk dari `cnn3_avg` 0,2074 yang dilatih dari nol**. Hipotesis "kurang data" mati.

**Kepala distribusi: seluruh keluarga ringkasan sudah disapu, bukan cuma yang dicoba
notebook.** Notebook memilih `q0.60` lewat `lb_real` tunggal; di lokal disapu ulang mean,
mode, kuantil bin-keras, dan kuantil **interpolasi** (yang tidak dicoba notebook sama
sekali). Terbaik `qi0.70` = 0,2314 vs `q0.60` 0,2322 — selisih 0,0008, dan di blend
hasilnya identik (gain +0,0012, menang 0/12). Pilihan ringkasan bukan penyebabnya.

### Keluarga "model deep baru atas waveform yang sama" DITUTUP

Dua batch, 8 notebook GPU, **7 gagal**. Tujuh arsitektur/regime training berbeda —
Inception, TCN dilatasi, konvolusi dalam, konvolusi+transformer, augmentasi agresif,
pra-latih SSL, kepala distribusi — semuanya mendarat di `lb_real` **0,208-0,232** dengan
korelasi **0,89-0,97** terhadap CNN v3. Itu bukan kebetulan: itu plafon yang bisa dicapai
konvolusi 1D dari 5 detik waveform. Notebook ke-9 dari keluarga ini tidak akan berbeda.

Satu-satunya yang lolos protokol (set-transformer, batch 1) bekerja lewat mekanisme yang
berbeda — attention antar-record — dan justru rugi di LB sebagai `notebook_9`.

## Aritmatika 0,17 — versi jujur setelah dua batch

`LB ~ lb_real + 0,0086`. Dari `lb_real` 0,1762 (LB 0,1849):

| target LB | butuh `lb_real` | Delta | penilaian |
|---|---|---|---|
| 0,1837 (peringkat 1) | 0,1751 | −0,0011 | **sudah di dalam derau LB (sd selisih ~0,004)** |
| 0,1800 | 0,1714 | −0,0048 | belum pernah dicapai oleh ide apa pun setelah nb8 |
| **0,1700** | **0,1614** | **−0,0148** | **1,4x lompatan terbesar yang pernah terjadi** |

Lompatan terbesar sepanjang case ini adalah nb6 → nb8 = **−0,0103**, dan itu hasil
terobosan CNN v3 setelah 25 keluarga ide gagal berturut-turut. **0,17 menuntut 1,4x itu,
dari posisi di mana keluarga penghasil terobosan itu sudah ditutup.**

Batas atasnya juga tidak menolong. Sisi desimal sudah **melewati** oracle-nya
(0,1437 vs ~0,1488) — nol sisa. Seluruh headroom yang tercatat ada di sisi bulat
(0,2074 vs "oracle" 0,1596), tapi oracle itu dihitung dengan label degenerate yang sama
yang membuat `notebook_9` gagal: di train, 24% pasangan dalam satu grup depth bulat punya
`y` identik. **Sebagian besar headroom sisi bulat itu palsu**, dan satu-satunya usaha
memanennya (nb9) rugi di LB.

**Vonis: 0,17 tidak bisa dicapai dari data ini.** Peringkat 1 sendiri baru 0,1835 setelah
7 entri, dan itu 0,0135 di atas 0,17. Yang realistis: **kita sudah efektif seri dengan
peringkat 1**, dan pertarungan sisanya ditentukan 70% data yang belum terlihat — bukan
oleh ide berikutnya.

## Sesi 22 Agu 2026 (sore): dua sumbu baru diukur, satu ide dibatalkan sebelum jalan

Setelah dua batch Kaggle habis, dicari sumbu yang **bukan** "model deep baru". Dua ketemu,
dan keduanya nol kemunculan di seluruh repo sebelum ini. Notebook: `belum_run/09_tta_klip.ipynb`
(generator `tools/mk_kaggle3.py`).

### Test-time augmentation: BELUM PERNAH DICOBA sama sekali

Kata "TTA" nol hit di `lab/`, `experiments/`, `tools/`, dan semua `.md`. CNN v3 dilatih
dengan rotasi horizontal acak + flip vertikal, tapi **saat inferensi cuma dilihat satu
orientasi** — jadi invariansinya cuma kira-kira, dan sisanya masuk sebagai derau prediksi.

Kenapa ini tidak melanggar penutupan keluarga "model deep baru": mekanismenya **pengurangan
varians**, bukan informasi baru. Arsitekturnya `Net3` persis nb8. Ukuran efek bisa ditaksir
dari sumbu varians yang sudah terukur — 3 → 6 seed memberi CNN **−0,0017** (0,2091 →
0,2074, korelasi antar-paket 3-seed 0,9875) — dan TTA menyerang komponen varians yang
**berbeda** dari seed.

Sifat yang tidak dimiliki satu pun ide yang gagal di dua batch: rotasi dan flip simetris,
jadi TTA **tidak bisa** menggeser mean prediksi subset depth-bulat. Aman terhadap ketiga
diagnostik transfer **secara konstruksi**.

### Record `is_clipped`: gap error-nya NYATA, tapi bukan karena saturasi

Diukur di OOF nb8. Yang penting di sini urutan pengukurannya — premis pertama runtuh dan
premis kedua bertahan:

| | MAE |
|---|---|
| record clipped (1,68% train / **3,78% test**) | 0,1990 |
| record non-clipped | 0,1338 |
| **clipped, distandarisasi ke distribusi magnitudo non-clipped** | **0,1838** |

Standarisasi itu wajib — record clipped magnitudonya lebih besar (5,65 vs 5,28), jadi
selisih mentah bisa saja cuma komposisi. **Gap +0,050 bertahan.** Plafon kalau ditutup
total: `0,0378 × 0,050 ≈ 0,0019 lb_real`.

**Kliping sintetis DIBATALKAN sebelum menghabiskan GPU — jangan hidupkan ulang.** Ide
awalnya "kliping merusak amplitudo puncak, latih CNN dengan kliping sintetis". Diukur dulu:

| fraksi sampel dengan \|a\| >= 0,98*max | median | p90 |
|---|---|---|
| record clipped (n=176) | 0,00167 | 0,00600 |
| record normal | 0,00133 | 0,00267 |

Record clipped di dataset ini cuma tersaturasi **~5 dari 3000 sampel** — setara memotong di
**c ~ 0,90**, nyaris tidak mengubah waveform. Augmentasinya akan jadi no-op. Gap +0,050 itu
nyata tapi **sebabnya bukan informasi amplitudo yang hilang.**

Yang tersisa dan diuji di notebook 09: subgrup ini **kurang terwakili 2,258x** relatif test,
jadi bobot sampelnya dinaikkan segitu di loss CNN (anchor ridge tidak diubah, supaya efeknya
terisolasi). **Peluangnya sedang, bukan tinggi** — importance weighting komposisi global
(depth-bulat x2,235) bentuknya sama dan gagal. Bedanya sasaran 1,68% dengan gap terukur vs
32% populasi. Diagnostik yang memutuskan: **MAE khusus record clipped**. Kalau itu tidak
membaik, perubahan `lb_real` apa pun di run B adalah derau.

### Protokol blend "ganti" — koreksi cara kerja yang dipakai 2 batch

Semua batch sebelumnya cuma **menambahkan** kandidat ke-9 ke blend nb8. Untuk kandidat yang
merupakan **versi lebih baik dari kandidat yang sudah ada di dalam blend** (TTA atas
`cnn3_avg`), itu salah bentuknya: blend jadi memegang dua salinan model yang sama dengan
korelasi ~0,99, persis situasi yang membuat pencarian bobot menipu diri sendiri.

Notebook 09 menguji dua-duanya: **tambah** (untuk kesebandingan) dan **ganti** (`cnn3_avg`
dikeluarkan, jumlah kandidat tetap 8, tidak ada inflasi derajat bebas). Jalur "ganti" sudah
divalidasi di lokal: menukar `cnn3_avg` (6 seed) dengan `cnn3_s2` (3 seed) dihukum
**+0,0011, menang 2/12** — protokolnya memang menghukum penurunan kualitas.

**Pakai protokol "ganti" untuk setiap kandidat masa depan yang menggantikan, bukan
menambah.** Ini berlaku umum, bukan cuma untuk notebook 09.

### Empat kandidat dari dua kali training

TTA cuma menyentuh inferensi, jadi gratis untuk dipisahkan dari training. Dua run
menghasilkan matriks 2x2 penuh (`cnn12a`, `cnn12a_tta`, `cnn12b`, `cnn12b_tta`), dan sapuan
K=1/2/4/8 keluar dari satu kali inferensi karena prediksi disimpan **per elemen simetri**
alih-alih langsung dirata-ratakan. Run A juga jadi **uji kewarasan lingkungan** — resepnya
identik `cnn3` jadi K=1 harus mendarat di ~0,2091; kalau tidak, verdikt notebook tidak bisa
dipercaya. Pola ini layak ditiru: **kalau sebuah perubahan hanya menyentuh inferensi,
jangan bayar training kedua untuknya.**

### Konteks strategis yang mengubah ambang: hanya SATU submission final

Dikonfirmasi user 22 Agu 2026: kompetisi ini **cuma mengizinkan satu submission final**.
Digabung dengan derau LB publik yang sudah terukur (sd selisih ~0,004 untuk model berbeda;
jarak ke peringkat 1 cuma 0,0014 = **0,4 sigma**), konsekuensinya: **tidak ada lindung
nilai.** Kandidat yang cuma menang tipis di `lb_real` bukan alasan cukup untuk menggeser
`notebook_8`. Ambangnya tetap gain holdout jujur + menang n/12 + ketiga diagnostik transfer.

## Ekor magnitudo: fatamorgana terbesar di case ini (diukur 22 Agu 2026)

Event M>=6,5 cuma **27 buah** tapi menyumbang **14,1% metrik**, dengan MAE **0,527** dan
bias **−0,290**. Dekomposisi bobot metrik yang realistis (pakai `EVR`):

| pita magnitudo event | n_event | MAE | % metrik |
|---|---|---|---|
| < 5,5 | 858 | 0,139 | 50,1 |
| 5,5–6,0 | 203 | 0,172 | 21,8 |
| 6,0–6,5 | 78 | 0,222 | 14,0 |
| **>= 6,5** | **27** | **0,527** | **14,1** |

Kelihatan seperti tambang emas: menolkan bias ekor bernilai ~0,008, lebih besar dari
terobosan CNN v3. **Itu salah, dan cara mengukurnya yang menipu.**

Bias −0,290 dibin menurut **`y`**, dan binning menurut `y` SELALU menunjukkan shrinkage
semu. Yang bisa diterapkan di test cuma binning menurut **prediksi**, dan di sana arahnya
terbalik:

| bin prediksi | n | mean pred | mean y | koreksi yang dibutuhkan |
|---|---|---|---|---|
| 5,6–5,9 | 1227 | 5,727 | 5,676 | −0,051 |
| 5,9–6,2 | 470 | 6,025 | 5,965 | −0,060 |
| 6,2–6,5 | 248 | 6,330 | 6,270 | −0,060 |
| **>= 6,5** | **53** | **6,658** | **6,468** | **−0,190** |

Modelnya sudah **kelebihan** menembak di atas. `c = 0,1` yang dulu terpilih 12/12 belahan
sebenarnya konsisten dengan "jangan dikoreksi sama sekali". **Keluarga koreksi ekor
DITUTUP dengan bukti, bukan cuma dengan gain kecil.**

Pelajaran metodologisnya lebih luas dari kasus ini: **setiap kali sebuah headroom dihitung
dengan mengelompokkan menurut `y`, angkanya hampir pasti fiktif.** Kelompokkan menurut
prediksi.

## Sisi depth-desimal: habis, dan sekarang ada buktinya

Sebelumnya "habis" disimpulkan dari perbandingan dengan oracle grouping (0,1437 vs ~0,1488).
Dekomposisi langsung lebih kuat. Prediksi **mentah** (sebelum smoothing), 490 event nyata
sisi desimal dengan >=3 record:

| komponen | nilai |
|---|---|
| bias sistematik per event | 0,118 |
| derau per-record (hilang saat di-smooth) | 0,118 |
| MAE event mentah | 0,1475 |
| plafon teoretis smoothing sempurna (= bias saja) | 0,1183 |
| **MAE event setelah smoothing nb8** | **0,1133** |

Smoothing nb8 sudah **melewati** plafon naifnya sebesar 0,0050 — karena median mengalahkan
mean. Sisa error seluruhnya bias sistematik per-event: modelnya salah menilai gempa itu,
konsisten di semua stasiunnya. **Tidak ada trik agregasi, grouping, atau smoothing yang
menyentuh itu.** Yang tersisa cuma model per-record yang benar-benar lebih baik.

## Gap sisi depth-bulat: sebagian besar kemungkinan DERAU LABEL

Sisi bulat lebih buruk **bahkan per-record**, sebelum grouping ikut bermain: MAE 0,1950 vs
0,1501 (distandarisasi ke distribusi magnitudo sisi desimal). Jadi "sisi bulat = masalah
grouping" tidak lengkap.

**Hipotesis depth diuji dan sebagian besar DITOLAK.** Dugaan: `depth_km` mereka nilai
default katalog, dan depth masuk fisika lewat jarak hiposentral. Diuji dengan melatih ulang
LightGBM tanpa **seluruh** fitur turunan depth (`depth_km`, `logdep`, `hypo`, `loghypo`):

```
depth diketahui : MAE-std desimal 0,1826
depth dibuang   : MAE-std desimal 0,1889   -> tahu depth cuma bernilai 0,0063
```

Gap antar-sisi 0,041, jadi depth menjelaskan **~15%** saja. Estimator depth yang lebih baik
plafonnya kecil — konsisten dengan `dep_hat` yang dulu "berhasil, kecil".

**Yang menjelaskan sisanya, kemungkinan besar: derau di label.** Dipecah menurut jenis
nilai depth:

| jenis | n | MAE-std | sd resid |
|---|---|---|---|
| desimal (depth asli) | 7195 | 0,1501 | 0,207 |
| bulat **dangkal** <100 km (default katalog 10/35) | 3044 | **0,1942** | 0,259 |
| bulat **dalam** >=150 km (depth asli, cuma dibulatkan) | 54 | **0,1694** | 0,163 |

Yang dihukum bukan "depth bulat" melainkan khusus record yang **katalognya gagal menentukan
kedalaman**. Depth bulat yang asli (gempa dalam) justru skornya bagus — lebih baik dari
rata-rata sisi desimal. Tafsiran paling masuk akal: kalau katalog tidak bisa memecahkan
kedalaman sebuah gempa, magnitudonya juga kurang terdefinisi. Sd derau tambahannya 0,156,
dan **derau label tidak bisa dikejar model secanggih apa pun.**

n=54 untuk sisi dalam memang kecil (14 gempa), jadi ini indikasi kuat, bukan vonis. Tapi
arahnya konsisten dan menjelaskan kenapa dua usaha grouping independen gagal.

## Satu-satunya keluarga yang tersisa: INPUT model, bukan arsitekturnya

```
fitur yang dilihat LightGBM : 196
skalar yang dilihat CNN     :   8
```

Ketujuh notebook deep yang gagal memvariasikan **arsitektur** di atas **8 skalar yang
sama** (3 x log10(peak), logdist, logdep, loghypo, snr/40, is_clipped). Tidak satu pun
mengubah input. CNN tidak pernah melihat 188 fitur sisanya — rasio pita spektral,
`tau_c`/`tau_p`, eigenvalue polarisasi, waktu-energi kumulatif, rise time, koreksi jarak.

LightGBM dan CNN cuma disatukan lewat **blend linear**, korelasi **0,878**. Korelasi
serendah itu justru bukti mereka melihat hal berbeda — dan blend linear **tidak bisa
mempelajari interaksi** apa pun di antaranya.

`belum_run/10_cnn_fitur_gabung.ipynb` menguji itu: `Net3` nb8 dengan cabang skalar 8-dim
diganti cabang fitur 196-dim ber-MLP sendiri. Sisanya disalin apa adanya.

**Mode kegagalan yang paling mungkin, dan ditahan secara arsitektural:** jaringan bersandar
penuh pada cabang fitur (yang sudah matang dan mudah dibaca), konvolusinya kurang terlatih,
hasilnya LightGBM mahal dengan korelasi ~0,99. `p_feat_drop` mematikan seluruh cabang fitur
secara acak saat training untuk menahannya.

**Gerbang kedua wajib: korelasi maks terhadap kandidat nb8 < 0,95.** CNN+BiGRU skornya
0,2101 (setara CNN v3) tapi korelasi 0,967 -> menang 1/12 -> ditolak. Skor tunggal tidak
pernah cukup.

**Bahaya utamanya `bias_rnd`.** Stacking meledak +0,027 -> +0,095 karena memakai
`is_rnd`/`depth_km` untuk menghafal prior katalog — mode kegagalan nb2. Model gabungan
punya kemampuan yang sama. Yang menahan: `get_feats()` mengembalikan 196 fitur per-record
**tanpa agregat grup**, jadi `grp_size` yang NaN untuk depth bulat tidak ada di sini
(notebook meng-`assert` itu), dan LightGBM sudah memakai 196 fitur yang sama 8 notebook
tanpa masalah.

### Fitur yang masuk jaringan saraf: dua hal wajib

1. **`nan_to_num`** — diukur ulang: **18** nilai non-finite di train (bukan 9 seperti
   tertulis sebelumnya), dari `kurt`. LightGBM menelannya native; jaringan saraf tidak, dan
   satu NaN merambat ke seluruh batch **tanpa memunculkan error**.
2. **Standardisasi memakai statistik fold TRAINING saja.** Menghitung mean/sd di seluruh
   data adalah kebocoran.

## Protokol blend "ganti" — berlaku umum mulai sekarang

Semua batch sebelumnya cuma **menambahkan** kandidat ke-9. Untuk kandidat yang merupakan
**versi lebih baik dari kandidat yang sudah ada di dalam blend**, itu salah bentuknya:
blend memegang dua salinan berkorelasi ~0,99, persis situasi yang membuat pencarian bobot
menipu diri sendiri.

Divalidasi di lokal: menukar `cnn3_avg` (6 seed) dengan `cnn3_s2` (3 seed) dihukum
**+0,0011, menang 2/12**. Protokolnya memang menghukum penurunan kualitas, bukan menerima
apa pun yang baru.

**Pakai protokol ini untuk setiap kandidat masa depan yang menggantikan, bukan menambah.**

## Kalau sebuah perubahan hanya menyentuh INFERENSI, jangan bayar training kedua

TTA di `09_tta_klip.ipynb` cuma menyentuh inferensi, jadi dua kali training menghasilkan
**empat** kandidat (matriks 2x2 dengan/tanpa TTA). Sapuan K=1/2/4/8 juga keluar gratis dari
satu kali inferensi, karena prediksi disimpan **per elemen simetri** alih-alih langsung
dirata-ratakan. Pola ini layak ditiru.

Dan run kontrol yang resepnya identik model lama bukan cuma baseline — ia **uji kewarasan
lingkungan**. Kalau `cnn3` tidak bisa direproduksi di Kaggle, seluruh verdikt notebook itu
tidak bisa dipercaya.

## Konteks strategis: hanya SATU submission final

Dikonfirmasi user 22 Agu 2026. Digabung dengan derau LB publik yang sudah terukur (sd
selisih ~0,004 untuk model berbeda; jarak ke peringkat 1 cuma 0,0014 = **0,4 sigma**):
**tidak ada lindung nilai.** Kandidat yang cuma menang tipis di `lb_real` bukan alasan cukup
untuk menggeser `notebook_8`. Ambangnya tetap gain holdout jujur + menang n/12 + ketiga
diagnostik transfer.

## Gerbang kontrol nb09: pelajaran metodologis yang lebih mahal dari idenya sendiri

Notebook `09_tta_klip` memasang gerbang kewarasan yang benar secara konsep — resep run A
identik `cnn3`, jadi kalau angkanya meleset berarti lingkungan Kaggle tidak mereproduksi
run lokal. Gerbangnya menyala, notebook mencetak "verdikt di bawah TIDAK bisa dipercaya",
**lalu menjalankan seluruh verdiktnya sampai selesai.**

Dan gerbangnya sendiri salah:

```
sapu_tta()  ->  lb_real(post_tr(o))     angka POST-PROCESSED
konstanta   ->  0,2091                  lb_real cnn3 MENTAH
selisih dua jenis itu: 0,0193
```

Post-processing (smoothing per event + ekspansi varians) memangkas 0,0193, jadi gerbangnya
melaporkan "Kaggle 0,0144 lebih baik" — mustahil untuk resep identik, dan sepenuhnya
artefak. **Konstanta kontrol yang benar: `cnn3` = 0,1898, `cnn3_avg` = 0,1888**
(`Post(0,95 / 0,5 / 150 / 1,15 / 1,05)`, persis default notebook Kaggle dan
`lab_blend.search`). Diukur di `experiments/exp50_kontrol_nb12.py`.

> **Perhatikan: `fastscore.Post` punya default LAIN** (`lam_deep` 0,35, `T_deep` 100).
> Selisihnya cuma ~0,0010 tapi cukup untuk menggeser perbandingan. Selalu lewatkan
> `POST_ARGS` eksplisit.

### Aturan yang lahir dari ini

1. **Setiap konstanta pembanding di notebook Kaggle wajib disebutkan JENISNYA** — mentah
   atau post — dan jenisnya harus sama dengan angka yang dihitung notebook. Ini kelas
   kesalahan yang tidak bisa ditangkap review kode, cuma bisa ditangkap dengan menulis
   jenisnya di sebelah angkanya.
2. **Gerbang yang menyala harus MENGHENTIKAN notebook, bukan cuma mencetak peringatan.**
   Notebook 09 mencetak peringatan lalu melanjutkan 3 sel verdikt, dan verdikt itulah yang
   nyaris terlanjur diserap sebagai kesimpulan.
3. **Verdikt blend yang mencampur kandidat lintas-lingkungan tidak valid.** Kandidat
   `cnn12*` dilatih di Kaggle; 8 kandidat pembandingnya dilatih di lokal. Selisih
   lingkungannya masuk sebagai kerugian ide. Kalau tidak bisa dihindari, pembandingnya
   harus diganti dengan kandidat dari lingkungan yang sama (itu yang dilakukan UJI 2 di
   `tools/serap_nb12.py`).

### Gap lingkungan Kaggle vs lokal: +0,0049, nyata, dan belum dijelaskan

| | `lb_real` (post) | dec | rnd |
|---|---|---|---|
| `cnn3` lokal (3 seed) | **0,1898** | 0,1439 | 0,2339 |
| A K=1 Kaggle (resep sama) | **0,1947** | 0,1457 | 0,2417 |
| selisih | **+0,0049** | +0,0018 | **+0,0078** |

Derau antar-paket 3-seed di lokal cuma **0,0006** (`cnn3` 0,1898 vs `cnn3_s2` 0,1904), jadi
gap ini **8,4× derau seed** — bukan variasi seed. `build_input()` dan grup simetri sudah
dibandingkan baris demi baris dengan `lab_cnn.build_input` / `lab_cnn3.run` dan **identik**.
Gapnya menumpuk di **sisi bulat** (+0,0078 vs +0,0018 di desimal), yang menunjuk ke anchor
ridge / `extract()`, bukan ke bobot konvolusinya — sisi bulat paling bergantung pada fitur
`A_BASE`. Kandidat penyebab yang belum diperiksa: versi `scipy` (`filtfilt`, `welch`) dan
`torch`/cuDNN di image Kaggle.

**Konsekuensi untuk semua batch sebelumnya:** notebook 02-08 membandingkan angka **mentah**
terhadap konstanta mentah, jadi gerbangnya konsisten — tapi verdikt **blend**-nya tetap
mencampur OOF Kaggle dengan OOF lokal. Kalau gap 0,0049 ini berlaku umum, semua kandidat
Kaggle di dua batch itu ditolak sambil membawa handicap yang sama. Itu tidak membalik
vonisnya (margin kegagalannya +0,0011…+0,0016, dan menang ≤ 3/12), tapi menjadikannya
**lebih tipis dari yang tercatat**.

### Yang tetap SAH dari nb09 — dan ini bukan angka kecil

Perbandingan internal Kaggle (A↔B, K=1↔K=8) lewat jalur kode yang sama, jadi gap
lingkungan saling meniadakan:

| efek terisolasi | besarnya |
|---|---|
| TTA (K=1 → K=8) | +0,0011 |
| **bobot loss record clipped ×2,26** | **+0,0033** |
| keduanya | **+0,0043** |
| └ khusus MAE record clipped | **+0,0093** |

Bobot clipped **3× lebih besar dari TTA**, dan diagnostik penentunya (MAE record clipped)
bergerak benar — jadi mekanismenya nyata. `bias_rnd` bergeser +0,000/−0,001 saat TTA
dinyalakan, persis prediksi dari simetri rotasi/flip.

**Aritmetika yang membuat ini layak diselesaikan:** `cnn3_avg` lokal = 0,1888 post.
0,1888 − 0,0043 ≈ **0,1845** — jauh di bawah kandidat CNN mana pun yang pernah ada di repo
ini. Itu sebabnya sumbu ini tidak boleh ditutup berdasarkan verdikt nb09 yang terkontaminasi.

### Bug `simpan()` yang membunuh kedua notebook

```python
json.dump({k:(np.asarray(v).tolist() if not np.isscalar(v) else float(v)) ...
```

`np.isscalar("teks")` bernilai `True`, jadi `res["_nama"]` (string) masuk ke `float(v)` dan
melempar `ValueError`. Sudah diperbaiki di `tools/mk_kaggle.py` dan kedua notebook. `.npz`
dan `_submission.csv` ditulis sebelum baris itu, jadi yang hilang cuma `_score.json` dan
zip bundel. **Setiap nilai non-numerik yang masuk `res` harus dites `isinstance(v, str)`
lebih dulu** — pola ini akan terulang begitu ada key metadata baru.

## Sisa jalan setelah batch ke-3

| sumbu | status |
|---|---|
| model deep baru atas waveform yang sama | **DITUTUP** — 7 dari 8 notebook gagal, korelasi 0,89-0,97 |
| grouping / co-membership | **DITUTUP** — 2 usaha independen gagal |
| post-processing / kalibrasi / koreksi ekor | **DITUTUP** — menang 1/12, koreksi ekor terbukti terbalik arah |
| input gabungan (196 fitur ke dalam CNN) | **DITUTUP** — nb10, `bias_rnd` +0,115, menang 0/12 |
| bobot blend nb8 | **JANGAN DISENTUH** — nb9 dan nb10 dua-duanya merugi |
| TTA + bobot record clipped | **DITUTUP 23 Agu 2026** — UJI 2 gain +0,00029, menang 6/12 |
| **gap lingkungan Kaggle 0,0049** | **BELUM DIJELASKAN** — satu-satunya yang masih terbuka |

## Sumbu TTA + bobot clipped: DITUTUP, dan alasannya penting

`tools/serap_nb12.py` merekonstruksi keempat kandidat `cnn12*` dari prediksi per-elemen
simetri dan menjalankan protokol blend dua kali. **UJI 2** memakai pembanding yang
provenance-nya sama (slot `cnn3_avg` diisi `cnn12a`, dua-duanya dari Kaggle), sehingga gap
lingkungan 0,0049 tidak lagi terhitung sebagai kerugian ide:

| kandidat | gain | menang | ambang |
|---|---|---|---|
| `cnn12a_tta` (TTA saja) | +0,00126 | 0/12 | gain < 0 **dan** menang ≥ 7/12 |
| `cnn12b` (klip saja) | +0,00036 | 5/12 | |
| **`cnn12b_tta`** | **+0,00029** | **6/12** | |

Meleset, tapi **ini kandidat terdekat sepanjang case ini** (pembanding: batch 2 memberi
+0,0011…+0,0013 dengan 0-3/12). Bacaan jujurnya **seri**, bukan kalah. Di bawah aturan satu
submission final tanpa lindung nilai, seri bukan alasan menggeser `notebook_8`.

### Kenapa +0,0043 di model tunggal jadi +0,0003 di blend

Bukan gap lingkungan — itu sudah dinetralkan di UJI 2. Blend nb8 punya **7 kandidat lain**
yang sudah menutupi sebagian besar varians yang dibuang TTA dan sebagian besar error record
clipped. Ini pola yang sama persis dengan seluruh riwayat repo: perbaikan kandidat ke-N
diserap blend alih-alih diteruskan (CNN+BiGRU 0,2101 setara CNN v3 → menang 1/12;
`cnn9_aug` 0,2080 → 1/12).

> **JANGAN jalankan ulang TTA + bobot clipped di pipeline lokal.** Aritmetika
> `cnn3_avg` 0,1888 − 0,0043 ≈ 0,1845 benar untuk **model tunggal**, tapi UJI 2 menunjukkan
> di tingkat **blend** efeknya netral pada provenance yang sama. Baseline lokal yang lebih
> baik tidak mengubah mekanisme penyerapan itu. Menghemat ~160 menit GPU.

### Pelajaran umum: ukur efek di tingkat yang sama dengan keputusannya

Efek terisolasi +0,0043 diukur di **model tunggal**; keputusannya diambil di **blend**.
Selisih dua tingkat itu 15×. Setiap kali sebuah ide dinilai lewat efek terisolasi, angkanya
harus diterjemahkan dulu ke tingkat tempat keputusan diambil — kalau tidak, ide yang
sebenarnya netral akan terus terlihat menjanjikan.

### Gap lingkungan lebih dalam dari sekadar skor

Korelasi OOF `cnn12a` vs `cnn3` untuk resep **identik** cuma **0,9722**, padahal dua paket
3-seed di lokal berkorelasi **0,9875**. Jadi Kaggle bukan cuma menghasilkan model 0,0049
lebih buruk, tapi model yang **berbeda lebih jauh dari yang bisa dijelaskan seed**.
`build_input()` dan grup simetri sudah diperiksa baris demi baris — identik. Gapnya
menumpuk di sisi bulat (+0,0078 vs +0,0019 desimal) → curigai anchor ridge / `extract()`,
yaitu versi `scipy` (`filtfilt`, `welch`). **Belum diperiksa.** Nilainya bukan di sumbu ini
melainkan di setiap notebook Kaggle berikutnya, kalau ada.

### Gerbang korelasi tidak sah tanpa gerbang skor (dari nb10)

`cnn13_join` sebagai model tunggal: `lb_real` **0,3730** mentah, `bias_rnd` **+0,378**,
korelasi maks terhadap kandidat nb8 cuma **0,226**. Notebook memakai gerbang
"korelasi < 0,95", melaporkan LOLOS, dan melewati varian kedua atas dasar itu. Gerbangnya
lolos karena modelnya **rusak**, bukan karena ia beragam. **Ambang skor harus dievaluasi
lebih dulu; korelasi rendah hanya bermakna untuk kandidat yang kompetitif.**

## Batch Kaggle ke-4: pseudo-labeling — satu-satunya sumbu yang belum pernah dijalankan

`belum_run/11_pseudo_label.ipynb` (generator `tools/mk_kaggle5.py`), ~4,3 jam T4.

**Kenapa ini bukan ide daur ulang.** `experiments/exp34_pseudo.py` cuma pernah menghitung
label-semunya (`cache/pseudo_te.npy`) lalu berhenti — trainingnya butuh GPU dan tidak pernah
dijalankan. Nol vonis tercatat di file ini, dan ia tidak ada di daftar sumbu tertutup.

### Ukuran mekanismenya SUDAH diukur, dan lebih kecil dari kesan klaimnya

| | nilai |
|---|---|
| depth-bulat per record, train | 31,5% |
| depth-bulat **berbobot** (yang dilihat loss weighted-L1), train | 34,3% |
| berbobot, setelah 2.300 record PL ditambahkan | **39,9%** |
| porsi bobot total yang dipegang record PL | 25,9% |

Pergeserannya **34,3% → 39,9%**, bukan "32% → 51%". Catat ini sebelum menafsirkan hasil:
**kalau gain-nya besar, mekanisme yang bekerja kemungkinan bukan komposisi** — melainkan
distilasi, karena label-semu berasal dari blend nb8 (0,1762) sementara CNN-nya sendiri di
0,1888. Guru yang lebih baik dari muridnya.

Itu memperbesar peluang menang **dan** memperbesar risiko: murid yang meniru blend akan
berkorelasi tinggi dengan blend, lalu diserap seperti semua kandidat sebelumnya.

### Dua kegagalan mirip yang TIDAK memvonis ini

- **Density-ratio nb7** (0,2245 vs 0,2101): reweighting record train yang sudah ada.
  Tidak bisa menciptakan record depth-bulat yang tidak ada di train; PL bisa.
- **Pra-latih SSL nb07** (0,2112 vs 0,2074): waveform test **tanpa label**. Hipotesis
  "kurang data mentah" memang mati; PL menambah **sinyal supervisi**, bukan data mentah.

### Jebakan senyap yang ditutup, dan kenapa ia layak dibayar 2× training

Kalau record test dilatih dengan label-semu dari nb8, model mencocokkan record itu — jadi
**prediksi test-nya runtuh ke arah nb8 sementara OOF tetap terlihat beragam**. Pencarian
bobot blend membaca diversitas dari OOF lalu menerapkannya ke prediksi test yang sudah
kolaps. **Tidak satu pun diagnostik yang ada sebelumnya bisa menangkap ini** — `bias_rnd`,
mean/sd subset bulat, dan gain sisi desimal semuanya buta terhadapnya.

Penutupnya: test dibelah dua menurut `depth_km`, dan tiap fold melatih dua model bersilang.
Tidak ada record test yang diprediksi model yang melihat label-semunya sendiri.

**Belahannya harus seimbang PER RECORD, bukan per nilai depth.** Membelah 170 nilai depth
50:50 menghasilkan **1633 vs 667** record, karena `depth = 10,0` sendirian memuat ~745
record. Akibatnya separuh prediksi test lahir dari model ber-PL kuat dan separuh lagi dari
model ber-PL lemah. Alokasi greedy menurut jumlah record memberi 1150 vs 1150.

Gerbang baru **KOLAPS TEST**: korelasi `pte` dikurangi korelasi `oof`, keduanya terhadap
arm kontrol. Kalau > 0,02, verdikt blend dibatalkan berapa pun skornya. **Gerbang ini
berlaku umum untuk setiap metode transduktif** — apa pun yang memakai record test saat
training.

### Uji asap wajib sebelum membakar GPU

`experiments/exp52_uji_runpl.py` menjalankan `run_pl` dengan 1 seed / 2 epoch di RTX 4060
(~2 menit) dan memeriksa hal yang gagal **senyap** di Kaggle: setiap slot OOF dan test
terisi tepat sekali, tidak ada NaN, belahan tidak memecah grup depth, irisan
{dilatih}×{diprediksi} kosong, dan skala prediksi masuk akal. Uji ini menemukan cacat
belahan 1633/667 sebelum ia sempat memakan 4 jam.

> **Pola yang layak ditiru untuk setiap notebook Kaggle berikutnya:** ekstrak fungsi
> training dari notebook, jalankan dengan `epochs=2, seeds=(0,)` di lokal, dan periksa
> invarian struktural — bukan skornya. Ongkosnya 2 menit; yang dicegah 4 jam.

### Sidik jari input — akhirnya bisa memisahkan gap input dari gap training

Sel Setup `tools/mk_kaggle.py` sekarang mencetak jumlah `|.|` untuk `Wtr`, `Str`, `Wte`,
`Ste`, dan `Ftr[A_BASE]` terhadap acuan lokal, plus versi numpy/scipy/torch:

```
Wtr 1.964203e+07 | Str 1.907536e+05 | Wte 4.208731e+06 | Ste 4.244618e+04
A_BASE 4.658112e+05 | nonfinite di Ftr: 18
lokal: numpy 1.26.4 | scipy 1.17.1 | torch 2.6.0+cu124
```

Kalau cocok, input identik dan gap 0,0049 lahir di training (torch/cuDNN). Kalau tidak,
inputnya sendiri yang beda dan tidak ada gunanya menyalahkan training. Gap itu sudah
terbuka sejak nb09 dan tidak pernah bisa dipersempit karena **tidak ada satu pun angka
input yang pernah dicetak untuk dibandingkan.**

### Kalau kandidatnya menang, jalankan ulang di LOKAL sebelum submit

Kandidat Kaggle membawa handicap lingkungan 0,0049. UJI 2 menetralkannya untuk **menilai
idenya**, tapi file submission-nya tetap lahir dari model yang lebih lemah. Estimasi lokal
di RTX 4060: **~2,8 jam** untuk arm A+B (2,5 detik/fold-epoch, diukur di uji asap).

### Diversitas lintas-lingkungan: GAGAL (23 Agu 2026)

Gap Kaggle 0,0049 dengan korelasi OOF cuma 0,9722 (vs 0,9875 antar-paket seed lokal)
terlihat seperti diversitas gratis — dekorelasi yang tidak bisa dibeli dengan seed
tambahan, dan modelnya sudah terlatih. Diuji di `experiments/exp51_lintas_env.py`, 20
konfigurasi:

| konfigurasi | gain terbaik | menang |
|---|---|---|
| `mean(cnn3_avg, cnn12b_tta)` a=0,5 menggantikan `cnn3_avg` | **+0,00028** | 5/12 |
| `mean(cnn3_avg, cnn12b)` a=0,4 | +0,00033 | 5/12 |
| `cnn12X` ditambahkan sebagai kandidat ke-9 | +0,00077 … +0,00153 | 1-3/12 |

Terbaiknya setara `cnn12b_tta` sendirian (+0,00029, 6/12) — merata-ratakan dua lingkungan
tidak menambah apa pun di atas memilih yang terbaik. **Sumbu ditutup.**

Pelajarannya bukan "korelasi 0,972 terlalu tinggi": `cnn3_dir` korelasinya 0,930 dan tetap
dapat bobot 0,217 di blend nb8. Bedanya `cnn3_dir` **kompetitif** (0,1934 post), sedangkan
`cnn12a` 0,0049 lebih buruk dari kembarannya. **Dekorelasi hanya berharga kalau kandidatnya
tidak membayar untuk itu dengan akurasi.** Gap lingkungan adalah dekorelasi yang dibayar
dengan akurasi, jadi ia derau, bukan diversitas.

### Pembagian kerja Kaggle vs lokal — kenapa verdikt dihitung DUA KALI

Notebook Kaggle mencetak verdiktnya sendiri, dan `tools/serap_nb*.py` menghitungnya ulang
di lokal. Itu bukan duplikasi sia-sia:

| | di Kaggle | di lokal |
|---|---|---|
| training | 4,3 jam, sekali jalan | — |
| verdikt | dicetak, sebagai bahan mentah | dihitung ulang, sebagai kesimpulan |
| kandidat pembanding | 8 (lewat `nb8_ref.npz`, 334 KB) | **70** di `cache/` |
| ongkos memperbaiki bug verdikt | ulang 4,3 jam | 2 menit |

Empat kejadian nyata yang membenarkan pemisahan ini: sel verdikt nb09 **crash** setelah 160
menit training (yang menyelamatkan run itu `.npz` yang ditulis sebelumnya); verdikt nb01
melabeli `bias_rnd` +0,059 AMAN; verdikt nb09 memakai konstanta kontrol salah jenis; dan
pertanyaan lintas-kandidat (mis. "bagaimana kalau digabung `cnn12b_tta`?") tidak bisa
dijawab notebook mana pun karena Kaggle cuma memegang 8 kandidat.

**Aturannya: yang mahal dan sekali-jalan di Kaggle, yang murah dan berulang di lokal.**
Dan `simpan()` harus dipanggil **tepat setelah tiap arm selesai training**, jauh sebelum
sel verdikt — supaya crash di verdikt tidak pernah menghanguskan jam-jam GPU.
