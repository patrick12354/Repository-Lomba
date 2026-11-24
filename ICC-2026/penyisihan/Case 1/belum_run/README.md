# `belum_run/` — ANTRIAN KOSONG

Status per **22 Agustus 2026, malam**. **`notebook_8.csv` tetap submission terbaik:
LB 0,1849, peringkat 3.**

Notebook 09 dan 10 sudah dijalankan dan dipindahkan ke [`../sudah_run/`](../sudah_run/README.md).
Tidak ada notebook baru di sini.

# ANTRIAN: 1 notebook — `11_pseudo_label.ipynb`

| notebook | waktu (T4) | ide | peluang |
|---|---|---|---|
| `11_pseudo_label.ipynb` | **~4,3 jam** (arm A ~85 mnt + arm B ~170 mnt) | 2.300 record test ikut dilatih dengan label dari blend nb8 | sedang — satu-satunya sumbu yang belum pernah dijalankan |

Generator: `tools/mk_kaggle5.py`. Butuh `ref/nb8_ref.npz` (sudah ter-upload user di
`/kaggle/input/datasets/timotiuspatrick/nb8-ref/`).

**Sudah diuji asap di lokal** (`experiments/exp52_uji_runpl.py`, 1 seed / 2 epoch di RTX
4060): kode jalan, tidak ada NaN, tiap record test terisi tepat sekali, belahan test tidak
memecah grup depth, skala prediksi masuk akal. **Jangan lewati uji ini kalau notebooknya
diubah.**

**Alternatif lokal:** arm A+B di RTX 4060 diperkirakan ~2,8 jam (2,5 s/fold-epoch diukur
dari uji asap). Lebih lama dari batas 30 menit, tapi menghindari gap lingkungan 0,0049 —
jadi kalau kandidatnya menang, versi lokalnya yang layak disubmit, bukan versi Kaggle.

## KALAU KAMU MEMBAWA HASILNYA KE SINI — baca bagian ini dulu

Notebook sudah mencetak verdiktnya sendiri di Kaggle. **Verdikt itu bahan mentah, bukan
kesimpulan** — dua kali sebelumnya verdikt notebook salah dan cuma ketahuan waktu dihitung
ulang (nb01 ambang `bias_rnd` kelonggaran, nb09 konstanta kontrol salah jenis).

### Yang harus diunduh dari panel Output Kaggle

```
hasil_cnn14_pl.zip      berisi cnn14a.npz + cnn14b.npz
```

**`cnn14a.npz` (KONTROL) sama wajibnya dengan `cnn14b.npz`.** Tanpa arm A, UJI 2 tidak bisa
dihitung dan verdiktnya jatuh kembali ke perbandingan lintas-lingkungan yang sudah terbukti
salah di notebook 09. Kalau sel verdikt sempat error, **zip-nya tetap ambil** — kedua
`.npz` ditulis sebelum sel verdikt, dan itu yang menyelamatkan nb09.

### Satu perintah

```bash
python "Case 1/tools/serap_nb14.py" <folder-atau-zip-hasil-Kaggle>
```

Menerima folder unduhan, path zip, atau `.npz` langsung. Butuh ~5 menit (3 kali protokol
blend 12-belahan). Tidak butuh GPU.

### Urutan membaca outputnya

| bagian | isi | cara membaca |
|---|---|---|
| **1. KOLAPS TEST** | korelasi `pte` − korelasi `oof`, arm B vs arm A | **gerbang pembatal.** > 0,02 berarti label-semu bocor ke prediksi test dan seluruh verdikt blend tidak sah, berapa pun angkanya |
| **2. Kontrol lingkungan** | arm A vs `cnn3` lokal 0,1898 | gap > 0,004 → verdikt tetap sah (pembandingnya se-lingkungan), tapi kalau menang, **jalankan ulang di lokal sebelum submit** |
| **3. Efek terisolasi** | gain PL + porsi dari sisi bulat | kalau gain-nya **tidak** menumpuk di sisi bulat, mekanisme komposisi BUKAN yang bekerja — kemungkinan distilasi. Catat apa adanya |
| **4. UJI 1 / UJI 2** | verdikt blend | **UJI 2 yang menentukan**; UJI 1 cuma untuk kesebandingan dengan angka batch sebelumnya |

### Ambang lolos

```
KOLAPS TEST aman  DAN  gain < 0  DAN  menang >= 7/12  DAN  bias_rnd <= 0,05
```

- **LOLOS** → skrip menyimpan `cache/blend_cnn14.npz`. Langkah berikutnya berurutan:
  (1) kalau gap kontrol > 0,004, jalankan ulang arm A+B di lokal (~2,8 jam RTX 4060);
  (2) tulis `notebook_11.ipynb` di root `Case 1/` + `submission/notebook_11.csv`;
  (3) catat di `submission/LEADERBOARD.md` **sebelum** tahu skor LB-nya.
- **TIDAK LOLOS** → `notebook_8.csv` tetap yang terbaik. Catat kegagalannya di
  `sudah_run/README.md` dan `CLAUDE.md` **beserta jawaban bagian 3**. Yang gagal tanpa
  catatan pasti dicoba ulang.

Lalu pindahkan notebooknya ke `sudah_run/`, taruh versi tereksekusi + zip di
`sudah_run/hasil/`, sesuai konvensi di `CLAUDE.md`.

### Kalau notebooknya error di tengah

Bukan masalah selama `.npz`-nya sudah tertulis. `simpan()` dipanggil **tepat setelah tiap
arm selesai training**, jauh sebelum sel verdikt — jadi crash di verdikt tidak menghanguskan
4 jam GPU. Bawa saja apa pun yang ada di `/kaggle/working/`.

---

## Kenapa pseudo-labeling, dan seberapa besar mekanismenya SEBENARNYA

Ini satu-satunya sumbu yang tidak ada di daftar tertutup. `experiments/exp34_pseudo.py`
cuma pernah menghitung labelnya (`cache/pseudo_te.npy`) lalu berhenti — trainingnya tidak
pernah dijalankan, dan nol vonis tercatat.

Klaim mekanismenya: proporsi depth-bulat 32% di train vs 51% di test. **Tapi ukuran
sebenarnya lebih kecil dari kesan itu**, dan sudah diukur:

| | nilai |
|---|---|
| proporsi depth-bulat per record, train | 31,5% |
| proporsi depth-bulat **berbobot** (yang dilihat loss), train | 34,3% |
| proporsi berbobot setelah PL ditambahkan | **39,9%** |
| porsi bobot total yang dipegang record PL | 25,9% |

Jadi pergeserannya **34,3% → 39,9%**, bukan ke 51%. Catat ini sebelum menafsirkan hasilnya:
kalau gain-nya besar, mekanismenya kemungkinan bukan komposisi.

Yang mungkin lebih menentukan: label-semu berasal dari blend nb8 (`lb_real` 0,1762 post
0,1762) sementara CNN-nya sendiri di 0,1888 — jadi ini **distilasi dari guru yang lebih
baik**, bukan sekadar geser komposisi. Itu memperbesar peluang menang, sekaligus
memperbesar risiko kandidatnya jadi terlalu mirip nb8 dan diserap blend.

## Dua kegagalan mirip yang TIDAK memvonis ini

- **Density-ratio nb7** (gagal, 0,2245 vs 0,2101): memberi bobot lebih ke record train yang
  sudah ada. Reweighting tidak bisa menciptakan record depth-bulat yang tidak ada di train.
- **Pra-latih SSL nb07** (gagal, 0,2112 vs 0,2074): memakai waveform test **tanpa label**.
  Hipotesis "kurang data mentah" memang mati; PL menambah **sinyal supervisi**, bukan data.

## Jebakan yang ditutup notebook ini

Kalau record test dilatih dengan label-semu dari nb8, prediksi test-nya runtuh ke arah nb8
sementara OOF tetap terlihat beragam — pencarian bobot lalu membaca diversitas yang tidak
ada di test. **Tidak satu pun diagnostik lama menangkap itu.**

Penutupnya: test dibelah dua menurut `depth_km` (dialokasikan greedy supaya seimbang per
record: 1150 vs 1150), dan tiap fold melatih dua model bersilang. Tidak ada record test
yang diprediksi model yang melihat label-semunya sendiri. Ongkosnya 2× training.

Gerbang **KOLAPS TEST** dicetak eksplisit: korelasi `pte` vs `oof` terhadap arm A. Kalau
selisihnya > 0,02, verdikt blend dibatalkan berapa pun skornya.

## Arm A adalah KONTROL dan wajib diunduh

Resepnya identik `cnn3` → `lb_real` harus mendarat di **0,1898** (angka SETELAH `post_tr`;
mentahnya 0,2091 — tertukarnya dua jenis angka ini yang merusak verdikt notebook 09).

Arm A juga pembanding se-lingkungan untuk UJI 2, dan sel Setup sekarang mencetak **sidik
jari input** (jumlah |.| Wtr/Str/Wte/Ste/A_BASE vs acuan lokal) untuk akhirnya memisahkan
"gap lingkungan lahir di input" dari "lahir di training".

---

## Riwayat: batch ke-3 selesai 23 Agu 2026

`serap_nb12.py` sudah dijalankan atas `cnn12*_syms.npz` yang selamat. **UJI 2:
`cnn12b_tta` gain +0,00029, menang 6/12** — meleset dari ambang (gain < 0 dan menang
≥ 7/12), jadi **TTA dan bobot record clipped DITUTUP**. Jangan jalankan ulang di
pipeline lokal: gain +0,0043 itu ada di tingkat model tunggal, dan di tingkat blend
efeknya netral. Rincian di [`../sudah_run/README.md`](../sudah_run/README.md).

Satu-satunya yang masih terbuka: **gap lingkungan Kaggle vs lokal 0,0049** (korelasi
OOF resep identik cuma 0,9722 vs 0,9875 antar-paket seed lokal). Bisa diperiksa tanpa
GPU dengan membandingkan versi `scipy` dan menghitung ulang `A_BASE` di kedua tempat.

<details>
<summary>Instruksi lama (sudah dijalankan)</summary>


`09_tta_klip` mati di sel verdikt, tapi dua artefak pentingnya **sudah tertulis sebelum
crash**: `cnn12a_syms.npz` dan `cnn12b_syms.npz` di `/kaggle/working/`. Keempat kandidatnya
bisa direkonstruksi dari situ tanpa melatih ulang apa pun.

```bash
python "Case 1/tools/serap_nb12.py" <folder-unduhan-dari-Kaggle>
```

**Ambil dua file itu dari panel Output Kaggle selagi sesinya masih hidup.** Kalau hilang,
run 160 menit itu harus diulang dari nol.

Alasannya: gerbang kontrol notebook 09 memakai konstanta yang **salah jenis** (`lb_real`
mentah 0,2091 dibandingkan terhadap angka yang sudah di-post-process; yang benar 0,1898).
Setelah dikoreksi, run Kaggle ternyata **0,0049 lebih buruk** dari run lokal untuk resep
identik — dan verdikt blend-nya membandingkan kandidat Kaggle terhadap kandidat lokal,
sehingga handicap itu terhitung sebagai kerugian ide. `serap_nb12.py` menjalankan ulang
protokol blend dengan pembanding yang provenance-nya sama. Rincian lengkap di
[`../sudah_run/README.md`](../sudah_run/README.md) bagian "Batch ke-3".

**Jangan bikin notebook GPU baru sebelum langkah itu selesai.** Jawabannya menentukan
apakah sumbu TTA + bobot clipped ditutup atau justru dipindahkan ke pipeline lokal.

</details>

## Kalau `serap_nb12.py` (UJI 2) lolos

Berarti idenya benar dan yang salah lingkungannya. Yang dikerjakan berikutnya **bukan**
submit file Kaggle-nya — ia tetap membawa handicap 0,0049 — melainkan menerapkan TTA +
bobot loss record clipped di pipeline **lokal** (`lab/lab_cnn3.py`), tempat baselinenya
`cnn3_avg` = 0,1888 post. Aritmetikanya 0,1888 − 0,0043 ≈ **0,1845**.

Estimasi waktu di RTX 4060: ~80 menit per paket 3 seed, jadi **> 30 menit → notebook
Kaggle**, dengan konstanta kontrol yang sudah diperbaiki di `tools/mk_kaggle3.py`.

## Kalau UJI 2 gagal

Tutup kedua sumbu (TTA dan bobot clipped), catat di `CLAUDE.md`, dan berhenti. Setelah
batch ini, keluarga yang tersisa habis: model deep baru (7 dari 8 gagal), grouping (2 usaha
gagal), post-processing (menang 1/12), input gabungan (notebook 10, `bias_rnd` +0,115).

---

# BACA INI DULU KALAU KAMU CLAUDE DI SESI BARU

Konteks minimum untuk menganalisa hasil kedua notebook ini tanpa membaca seluruh repo.

## Posisi

- Metrik **EB-TWMAE**: rata-rata MAE **per gempa dulu**, baru dibobot magnitudo
  (1,0 / 1,5 / 2,0 / 2,5). Lebih kecil lebih baik.
- LB terbaik **0,1849** (`notebook_8`), peringkat 3. Peringkat 1 **0,1835**, peringkat 2
  **0,1837**.
- Metrik seleksi internal: **`lb_real`** (bukan `eb_twmae` mentah — lihat di bawah).
  `notebook_8` = `lb_real` **0,1762**. Kalibrasi kasar: **`LB ≈ lb_real + 0,0086`**.
- Riwayat LB: nb1 0,2005 · nb2 0,2262 · nb3 0,1996 · nb5 0,2063 · nb6 0,1952 ·
  **nb8 0,1849** · nb9 0,1856 · nb10 0,1871. **Tiga submission terakhir semuanya lebih
  buruk dari nb8.**

## Lima aturan yang tidak boleh dilanggar

1. **Jangan pernah menilai kandidat dengan `eb_twmae` mentah.** Tidak ada `event_id` di
   dataset; event direkonstruksi lewat `groupby(depth_km, magnitude)`, yang melebur record
   depth-bulat jadi pseudo-event sampai **401 record**. Akibatnya CV over-weight ekor ~3×.
   Pakai `lb_real`, yang memecah pseudo-event itu jadi potongan seukuran event nyata.
2. **`lb_real` memperbaiki BOBOT metrik, bukan LABEL-nya.** `y` tetap identik untuk semua
   record yang berbagi `(depth, magnitude)`. Jadi metode apa pun yang **menyeragamkan
   prediksi di dalam satu grup depth** dibayar berlebihan. Itu yang membunuh `notebook_9`.
3. **Skor blend mentah tidak boleh dipercaya.** Kandidat ke-N selalu bisa menurunkan angka
   di data tempat bobotnya dipilih. Yang menentukan: **gain holdout (12 belahan split-by-
   event) dan berapa belahan yang dimenangkan.** CNN+BiGRU menurunkan 0,1762 → 0,1756 tapi
   menang 1/12 → ditolak, dan itu benar.
4. **Kalau `lb_real` dan diagnostik transfer bertabrakan, diagnostik transfer menang.**
   `lb_real` mengukur data train; `bias_rnd` mengukur jarak ke test. Ambang `bias_rnd`
   **+0,05** (nb5 rugi di LB pada +0,056).
5. **Blend `notebook_8` adalah setelan baku — jangan diutak-atik.** Dua perturbasi
   independen (nb9 menambah kandidat, nb10 menggeser bobot) dua-duanya merugi.

## Derau LB — ini mengubah cara membaca semua angka

LB publik cuma **30% data test**. Diukur dengan bootstrap:

| yang diukur | sd |
|---|---|
| skor absolut di sub-sampel 30% | 0,0098 |
| selisih dua submission **mirip** (corr 0,999) | 0,0008 |
| selisih dua submission **beda** (corr 0,888) | **0,0038** |

Jarak ke peringkat 1 = 0,0014 = **0,4 sigma**. **Kita sudah efektif seri dengan peringkat
1.** Dan kompetisi ini **cuma mengizinkan SATU submission final** — tidak ada lindung
nilai. Konsekuensinya: kandidat yang cuma menang tipis di `lb_real` **bukan** alasan cukup
untuk menggeser `notebook_8`.

## Keluarga ide yang SUDAH DITUTUP — jangan diusulkan lagi

| keluarga | bukti |
|---|---|
| post-processing, kalibrasi, reweighting | ~25 keluarga ide, semua ≤ 0,001 |
| grouping / co-membership | 2 usaha independen: AUC 0,79 tapi cuma panen 0,3–1,0% headroom; sidik derau AUC 0,56 |
| attention antar-record (set-transformer) | lolos semua protokol, **LB tetap rugi** (nb9) |
| arsitektur CNN 1D baru atas input yang sama | 4 dari 4 gagal, korelasi 0,92–0,96 |
| regime training baru (augmentasi agresif, SSL, kepala distribusi) | 3 dari 3 gagal, korelasi 0,89–0,97 |
| stacking | `bias_rnd` meledak +0,027 → +0,095 |
| menggeser bobot blend nb8 | nb10, rugi 0,0022 |

**Tujuh dari delapan notebook GPU gagal**, semuanya mendarat di `lb_real` 0,208–0,232.

## Tiga hal yang DIUKUR ULANG 22 Agu 2026 (sore) — penting untuk menilai hasil

**1. Ekor magnitudo adalah fatamorgana, bukan headroom.** Event M≥6,5 cuma 27 buah tapi
menyumbang **14,1% metrik**, MAE 0,527, bias **−0,290**. Kelihatan seperti tambang emas.
Tapi bias itu dibin menurut `y`, dan itu selalu menipu. Dibin menurut **prediksi** — satu-
satunya cara yang bisa diterapkan di test — modelnya justru **kelebihan** menembak:

| bin prediksi | n | mean pred | mean y | koreksi dibutuhkan |
|---|---|---|---|---|
| 5,9–6,2 | 470 | 6,025 | 5,965 | **−0,060** |
| 6,2–6,5 | 248 | 6,330 | 6,270 | **−0,060** |
| ≥ 6,5 | 53 | 6,658 | 6,468 | **−0,190** |

Bias −0,290 itu murni *regression dilution*. **Tidak ada koreksi ekor yang bisa dipanen.**
(Ini mengoreksi klaim lama di `CLAUDE.md` yang menulis arah sebaliknya.)

**2. Sisi depth-desimal benar-benar habis.** Dekomposisi error per-event pada prediksi
**mentah** (490 event nyata, ≥3 record):

| komponen | nilai |
|---|---|
| bias sistematik per event | 0,118 |
| derau per-record (hilang saat di-smooth) | 0,118 |
| MAE event mentah | 0,1475 |
| **MAE event setelah smoothing nb8** | **0,1133** |
| plafon teoretis smoothing sempurna | 0,1183 |

Smoothing nb8 sudah **melewati** plafon naifnya (median mengalahkan mean). Sisanya
seluruhnya bias sistematik: modelnya salah menilai gempa itu, konsisten di semua
stasiunnya. **Tidak ada trik agregasi yang menyentuh itu.**

**3. Gap sisi depth-bulat sebagian besar kemungkinan DERAU LABEL.** Sisi bulat lebih buruk
bahkan per-record (0,1950 vs 0,1501 setelah magnitudo distandarisasi). Dugaan "karena
depth-nya nilai default" diuji dengan membuang seluruh fitur turunan depth: rugi cuma
**0,0063**, jadi depth menjelaskan ~15% dari gap 0,041. Dipecah lebih jauh:

| jenis | n | MAE-std | sd resid |
|---|---|---|---|
| desimal (depth asli) | 7195 | 0,1501 | 0,207 |
| bulat **dangkal** (default katalog 10/35) | 3044 | **0,1942** | 0,259 |
| bulat **dalam** ≥150 km (depth asli, cuma dibulatkan) | 54 | **0,1694** | 0,163 |

Yang dihukum bukan "depth bulat", tapi khusus record yang **katalognya gagal menentukan
kedalaman**. Depth bulat yang asli justru skornya bagus. Tafsiran paling masuk akal: kalau
katalog tidak bisa memecahkan kedalaman, magnitudonya juga kurang terdefinisi — **derau di
label, bukan di model**, dan itu tidak bisa dikejar model secanggih apa pun.

**Kesimpulan gabungan: 0,17 hampir pasti tidak ada.** Yang realistis dari notebook 10:
peluang sedang untuk −0,002…−0,005 `lb_real`, yaitu LB 0,180–0,183.

---

# Notebook 10 — model gabungan (PRIORITAS 1)

## Idenya, dalam satu angka

```
fitur yang dilihat LightGBM : 196
skalar yang dilihat CNN     :   8
```

Ketujuh notebook deep yang gagal memvariasikan **arsitektur** di atas **8 skalar yang
sama** (3 × log10(peak), logdist, logdep, loghypo, snr/40, is_clipped). Tidak satu pun
mengubah input. CNN tidak pernah melihat 188 fitur sisanya — rasio pita spektral,
`tau_c`/`tau_p`, eigenvalue polarisasi, waktu-energi kumulatif, rise time, koreksi jarak.

LightGBM dan CNN cuma disatukan lewat **blend linear**, korelasi **0,878**. Korelasi
serendah itu berarti mereka melihat hal berbeda — dan blend linear tidak bisa mempelajari
**interaksi** apa pun di antaranya. **Itu satu-satunya sumbu input yang belum digeser.**

## Arsitektur

`Net13` = `Net3` notebook_8 dengan **satu** perubahan: cabang skalar 8-dim diganti cabang
fitur 196-dim yang punya MLP sendiri (196 → 128 → 64, dropout 0,30). Bagian konvolusinya
(`Blk`, w=64, 5 blok, SE, dua kepala, anchor ridge, augmentasi) disalin apa adanya — kalau
itu ikut berubah, gain/ruginya tidak bisa dipisahkan.

`p_feat_drop = 0,15` mematikan **seluruh cabang fitur** secara acak saat training (modality
dropout). Tanpa ini jaringan cenderung bersandar pada fitur — yang sudah matang dan mudah
dibaca — lalu membiarkan konvolusinya kurang terlatih, dan hasilnya jadi **LightGBM mahal
dengan korelasi ~0,99**. Itu mode kegagalan paling mungkin, jadi ditahan secara
arsitektural.

## DUA gerbang, keduanya wajib lolos

1. **gain holdout negatif DAN menang ≥ 7/12 belahan**;
2. **korelasi maks terhadap 8 kandidat nb8 < 0,95.**

Gerbang kedua itu yang membunuh CNN+BiGRU di nb8: skor tunggalnya 0,2101 (setara CNN v3
0,2091) tapi korelasi 0,967 → menang 1/12 → ditolak. Pembanding: CNN v3 **menang** dengan
korelasi 0,878; keempat CNN batch 1 gagal di 0,92–0,96.

Notebook menjalankan varian kedua (`p_feat_drop = 0,40`) **hanya kalau gerbang korelasi
gagal**. Kalau gerbang pertama lolos, sel itu dilewati dan menghemat ~1 jam GPU — itu
keputusan yang benar, bukan langkah terlupa.

## Bahaya utama: `bias_rnd`

**Stacking** membuat `bias_rnd` melonjak **+0,027 → +0,095**: stacker memakai
`is_rnd`/`depth_km` untuk menghafal prior katalog train — mode kegagalan `notebook_2`
(LB 0,2262, kegagalan terburuk di case ini). Blend linear aman justru karena ia tidak bisa
mengkondisikan pada fitur. **Model gabungan bisa.**

Yang menahannya: `get_feats()` mengembalikan 196 fitur **per-record saja, TANPA agregat
grup** — jadi `grp_size` yang `NaN` untuk depth bulat (penanda tipe depth paling terang,
pembunuh nb2) tidak ada di sini. Notebook meng-`assert` itu. Dan LightGBM sudah memakai 196
fitur yang sama selama 8 notebook tanpa `bias_rnd` meledak (Model A +0,040, Model B +0,064).

Notebook mencetak `bias_rnd` di tiap tahap dan menolak di atas **+0,05**.

## Dua hal wajib untuk fitur yang masuk jaringan saraf

1. **`nan_to_num`** — diukur di lokal: **18 nilai non-finite di train**, dari `kurt`.
   LightGBM menelan NaN secara native jadi ini tidak terlihat selama 8 notebook, tapi di
   jaringan saraf satu NaN merambat ke seluruh batch dan seluruh run jadi sampah **tanpa
   memunculkan error**. Di-`assert`.
2. **Standardisasi memakai statistik FOLD TRAINING saja** — menghitung mean/sd di seluruh
   data adalah kebocoran.

## Sudah di-smoke-test

`Net13` sudah dijalankan 1 fold × 2 epoch di RTX 4060 lokal: 1,94 juta parameter, keluaran
finite, tidak ada error bentuk. Estimasi 73 menit lokal untuk 15 fold × 80 epoch → **~2–2,5
jam di T4**.

## Keluaran

| file | isi |
|---|---|
| `cnn13_join.npz` | OOF + test model gabungan — ini yang dipakai blend lokal berikutnya |
| `cnn13_drop40.npz` | varian modality-dropout kuat, **hanya ada kalau gerbang korelasi gagal** |
| `blend_cnn13.npz` + `_submission.csv` + `_score.json` | blend terbaik dari 4 kombinasi (tambah/ganti × 2 varian) |
| `hasil_cnn13_join.zip` | semuanya dibungkus, ~300 KB |

## Cara membaca hasilnya (untuk sesi Claude baru)

Urutan periksa, dan **jangan lompat**:

1. **`bias_rnd` ≤ +0,05?** Kalau tidak, tolak apa pun skornya — ini mode kegagalan nb2.
2. **korelasi maks < 0,95?** Kalau tidak, model ini salinan mahal. Tutup keluarga ini.
3. **gain holdout < 0 DAN menang ≥ 7/12?** Kalau tidak, tolak — lihat aturan 3 di atas.
4. **`lb_real` blend < 0,1762?** Kalau tidak, tolak (aturan yang dilanggar nb10).
5. Baru sesudah keempatnya lolos: bandingkan protokol **tambah** vs **ganti**, dan pilih
   yang gain holdout-nya lebih baik. Kalau seri, pilih **ganti** — kandidat lebih sedikit
   berarti derajat bebas pencarian bobot lebih sedikit, jadi lebih dipercaya.

Kalau gagal: **catat di `sudah_run/README.md`** — skor tunggal, korelasi maks, `bias_rnd`,
gain, menang n/12, **dan alasannya**. Yang gagal justru yang paling sering dicoba ulang
kalau alasannya tidak dicatat.

---

# Notebook 09 — TTA + bobot clipped (PRIORITAS 2)

Dua sumbu yang belum pernah disentuh, dan **tidak satu pun** masuk keluarga "model deep
baru". `Net3` identik notebook_8.

## 1. Test-time augmentation

CNN v3 dilatih dengan rotasi horizontal acak + flip vertikal — simetri fisik yang sah,
karena orientasi stasiun terhadap azimut sumber memang sembarang. Tapi saat inferensi model
cuma dilihat **satu** orientasi, jadi invariansinya cuma kira-kira. TTA merata-ratakan atas
grup simetri itu dan menghilangkan sisanya secara eksak.

Mekanismenya **pengurangan varians**, bukan informasi baru — jadi vonis "plafon informasi 5
detik waveform" tidak berlaku untuknya. Patokan ukuran: 3 → 6 seed memberi CNN **−0,0017**
(0,2091 → 0,2074, korelasi antar-paket 0,9875). TTA menyerang komponen varians yang
**berbeda** dari seed.

Karena rotasi dan flip simetris, TTA **tidak bisa** menggeser mean prediksi subset
depth-bulat — aman terhadap ketiga diagnostik transfer **secara konstruksi**.

## 2. Bobot record `is_clipped`

| | train | test |
|---|---|---|
| proporsi `is_clipped` | 1,68% (n=176) | **3,78% (n=87)** |

MAE record clipped **0,1838** vs non-clipped **0,1338** — **setelah** distribusi
magnitudonya distandarisasi (standarisasi itu wajib; record clipped magnitudonya memang
lebih besar, 5,65 vs 5,28). Gap +0,050 bertahan. Plafon: `0,0378 × 0,050 ≈ 0,0019 lb_real`.

Run B menaikkan bobot sampel record clipped ×2,258 di loss CNN. **Anchor ridge tidak
diubah**, supaya efeknya terisolasi.

> **Peringatan.** *Importance weighting* komposisi global (depth-bulat ×2,235) bentuknya
> sama dan **gagal**. Bedanya sasaran 1,68% dengan gap terukur vs 32% populasi. Peluangnya
> **sedang**. Diagnostik yang memutuskan: **MAE khusus record clipped** — kalau itu tidak
> membaik, perubahan `lb_real` apa pun di run B adalah derau, dan notebook bilang begitu
> eksplisit. Kalau gagal, **tutup keluarga ini.**

### Kliping sintetis: DIBATALKAN sebelum menghabiskan GPU — jangan hidupkan ulang

Ide awalnya "kliping merusak amplitudo puncak, latih CNN dengan kliping sintetis". Diukur
dulu, dan premisnya runtuh:

| fraksi sampel dengan \|a\| ≥ 0,98·max | median | p90 |
|---|---|---|
| record clipped (n=176) | 0,00167 | 0,00600 |
| record normal | 0,00133 | 0,00267 |

Record clipped di dataset ini cuma tersaturasi **~5 dari 3000 sampel** — setara memotong di
**c ≈ 0,90**, nyaris tidak mengubah waveform. Augmentasinya akan jadi no-op. Gap +0,050 itu
nyata tapi **sebabnya bukan informasi amplitudo yang hilang**.

## Empat kandidat dari dua kali training

TTA cuma menyentuh inferensi, jadi gratis dipisahkan dari training:

| | tanpa TTA | dengan TTA |
|---|---|---|
| A: resep nb8 apa adanya | `cnn12a` (**kontrol**) | `cnn12a_tta` |
| B: + bobot clipped ×2,258 | `cnn12b` | `cnn12b_tta` |

Run A adalah **uji kewarasan lingkungan**: resepnya identik `cnn3`, jadi `lb_real` di K=1
harus mendarat di ~0,2091. Kalau tidak, ada yang beda di Kaggle dan seluruh verdikt
notebook itu tidak bisa dipercaya. Notebook mencetak COCOK / TIDAK COCOK.

Sapuan K=1/2/4/8 keluar **gratis** dari satu kali inferensi (prediksi disimpan per elemen
simetri). Kalau K=1 → K=8 datar, TTA ditutup; kalau bergerak tapi belum jenuh, itu argumen
untuk K=16 tanpa training ulang.

---

# Protokol blend "ganti" — berlaku umum, bukan cuma untuk notebook ini

Semua batch sebelumnya cuma **menambahkan** kandidat ke-9. Untuk kandidat yang merupakan
**versi lebih baik dari kandidat yang sudah ada di dalam blend**, itu salah bentuknya:
blend jadi memegang dua salinan berkorelasi ~0,99, persis situasi yang membuat pencarian
bobot menipu diri sendiri.

Kedua notebook menguji dua-duanya: **tambah** (untuk kesebandingan dengan batch lama) dan
**ganti** (kandidat lama dikeluarkan, tidak ada inflasi derajat bebas). Notebook 09
mengganti `cnn3_avg`; notebook 10 mengganti `cnn3_avg` **dan** `resA_dep` sekaligus, karena
ia melihat kedua sumber.

Jalur "ganti" sudah divalidasi di lokal: menukar `cnn3_avg` (6 seed) dengan `cnn3_s2`
(3 seed) dihukum **+0,0011, menang 2/12** — protokolnya memang menghukum penurunan
kualitas, bukan menerima apa pun yang baru.

**Pakai protokol ini untuk setiap kandidat masa depan yang menggantikan, bukan menambah.**

---

# Cara pakai di Kaggle

1. **Settings → Accelerator → GPU** (T4 atau P100).
2. **Add Input → Competitions →**
   `ai-innovation-case-task-1-seismic-magnitude-prediction`.
3. **Add Input → Datasets → `nb8-ref`** (berisi `nb8_ref.npz`, 334 KB — prediksi OOF + test
   8 kandidat `notebook_8` beserta bobot blend-nya). Sudah ter-upload di
   `/kaggle/input/datasets/timotiuspatrick/nb8-ref/nb8_ref.npz`; notebook mencarinya di
   situ dulu lalu menelusuri seluruh `/kaggle/input` sebagai cadangan.

   Sel Setup memvalidasinya langsung: blend 8 kandidat itu harus mereproduksi `lb_real`
   **0,1762**. Kalau tercetak `COCOK`, verdiktnya bisa dipercaya. Tanpa file ini kedua
   notebook tetap melatih modelnya, tapi **sel verdikt dilewati**.
4. **Run All.**
5. Sel terakhir membungkus semua hasil jadi **satu zip** di `/kaggle/working/`. Unduh dari
   panel Output, ekstrak `.npz`-nya ke `Case 1/cache/`.

Kedua notebook mencetak sisa waktu setiap fold selesai, jadi progresnya kelihatan sejak
fold pertama.

## Sesudah hasilnya kembali

```bash
C:/Patrick/coding/.venv/Scripts/python.exe "Case 1/tools/serap_hasil.py" <folder-atau-zip>
```

Skrip itu mengekstrak `.npz` ke `cache/`, mengenali kandidat baru, lalu menjalankan
**protokol blend 12-belahan dengan semua kandidat baru sekaligus** — pertanyaan yang tidak
bisa dijawab notebook manapun sendirian, karena tiap notebook cuma melihat modelnya sendiri
plus 8 kandidat nb8.

> **Verdikt otomatis apa pun tetap wajib dibaca manusia.** Ambang `bias_rnd` di
> `serap_hasil.py` pernah dipasang 0,08 dan meloloskan koreksi set-transformer versi mentah
> (`bias_rnd` +0,059) yang seharusnya ditolak — `notebook_5` rugi di LB pada +0,056.

Lalu: pindahkan notebooknya ke `sudah_run/`, taruh versi tereksekusi + zip di
`sudah_run/hasil/`, dan **tulis verdiktnya di `sudah_run/README.md` termasuk yang gagal
beserta alasannya.**

## Isi folder

- `ref/nb8_ref.npz` — **jangan dihapus.** Dibutuhkan kedua notebook untuk sel verdikt dan
  untuk protokol "ganti".
