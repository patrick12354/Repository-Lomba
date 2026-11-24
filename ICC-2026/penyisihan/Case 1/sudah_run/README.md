# `sudah_run/` — notebook GPU yang sudah dijalankan di Kaggle

> **SUDAH DIJALANKAN SEMUA (21–22 Agu 2026) — DUA BATCH, 8 notebook.** Notebook sumber
> ada di root folder ini, versi tereksekusi + zip hasilnya di `hasil/`. `.npz` tiap model
> sudah disalin ke `Case 1/cache/`.
>
> **Skor akhir kedua batch: 7 dari 8 gagal.** Batch 1 (01–05) di bagian atas, batch 2
> (06–08) di bagian bawah. Satu-satunya yang lolos protokol — set-transformer (01) —
> jadi `notebook_9` dan **rugi di LB** (0,1856 vs 0,1849). `belum_run/` sekarang kosong.
> `notebook_8` tetap submission terbaik.

Lima notebook yang butuh GPU lama. Semuanya **berdiri sendiri**: tidak mengimpor apa pun
dari `lab/`, karena folder itu tidak ada di Kaggle. Kode inti (`lb_real`, ekstraksi fitur,
input CNN gaya MagNet, protokol blend 12-belahan) disalin apa adanya supaya angkanya
sebanding dengan run lokal.

Titik berangkatnya `notebook_8`: **LB 0,1849, peringkat 2**, `lb_real` 0,1762.

## HASIL — 4 dari 5 gagal, 1 berhasil besar

| # | Notebook | model tunggal `lb_real` | gain holdout | menang | vonis |
|---|---|---|---|---|---|
| 01 | set-transformer | — (koreksi, bukan model) | **−0,0042** | **12/12** | ✅ **DIPAKAI** |
| 02 | `cnn8` Inception multi-skala | 0,2169 | +0,0014 | 0/12 | GAGAL |
| 03 | `cnn7` TCN dilatasi | 0,2106 | +0,0016 | 1/12 | GAGAL |
| 04 | `cnn5` konvolusi dalam | 0,2103 | +0,0012 | 2/12 | GAGAL |
| 05 | `cnn6` transformer | 0,2253 | +0,0015 | 0/12 | GAGAL |

### Kenapa keempat arsitektur deep itu gagal: redundan, bukan lemah

Tak satu pun mengalahkan `cnn3_avg` (0,2074) sebagai model tunggal, tapi itu bukan
sebab utamanya. Sebabnya **korelasi**: keempatnya berkorelasi **0,92–0,96** terhadap
`cnn3_avg`. Pelajaran nb8 — "korelasi rendah lebih berharga daripada skor tunggal yang
bagus" — berlaku terbalik di sini. CNN v3 menang karena korelasinya 0,878; keempat
arsitektur baru ini pada dasarnya melihat hal yang sama dengan CNN v3.

Menggabungkan keempatnya sekaligus juga tidak menolong (diuji lokal, protokol 12 belahan):

| kandidat blend | `lb_real` | gain | menang |
|---|---|---|---|
| nb8 + keempat CNN baru | 0,1756 | +0,0012 | 4/12 |
| nb8 + `cnn5` + `cnn7` | 0,1755 | +0,0008 | 4/12 |
| nb8 + `cnn7` saja | 0,1757 | +0,0016 | 1/12 |

**Keluarga "arsitektur CNN 1D baru atas waveform yang sama" dinyatakan habis.**

### 01 berhasil, tapi verdikt notebook-nya harus dikoreksi

Notebook 01 memilih `lam = 0,50` pada koreksi **mentah** dan melabeli `bias_rnd = +0,059`
sebagai AMAN karena ambangnya dipasang di 0,08. Itu terlalu longgar: `notebook_5` rugi di
LB dengan `bias_rnd` hanya **+0,056**.

Demean di dalam training (`demean=True`) **tidak cukup** — model tetap memulihkan prior
katalog lewat fitur; koreksi hasilnya bermean **+0,0556** di subset depth-bulat dangkal.
Obatnya sepele: **demean lagi pada koreksi itu sendiri saat diterapkan.**

| lam 0,50 | `lb_real` | `bias_rnd` | mean test bulat | sd |
|---|---|---|---|---|
| nb8 (acuan) | 0,1762 | +0,031 | 5,259 | 0,396 |
| koreksi mentah | 0,1714 | **+0,059** ⚠ | 5,276 | 0,404 |
| **koreksi di-demean saat apply** | **0,1718** | **+0,029** ✅ | 5,253 | 0,404 |

Ongkosnya cuma **0,0004 `lb_real`** dan `bias_rnd` tidak bergerak sama sekali. Gain holdout
jujurnya tetap **−0,0042, menang 12/12**, dan `lam` terpilih stabil (12 belahan memilih
0,4–0,6, median 0,5).

Ini juga mengoreksi pengukuran lokal sebelumnya yang menyimpulkan versi demean cuma
menahan −0,0011. Versi Kaggle (3 seed, 60 epoch) menahan **−0,0042** — modelnya yang
sebelumnya kurang dilatih, persis pola yang sama dengan CNN v3 di nb8.

Hasilnya jadi `submission/notebook_9.csv`.

---

## Urutan yang disarankan (arsip — semua sudah dijalankan)

| # | Notebook | Perkiraan waktu (T4) | Status ide |
|---|---|---|---|
| 01 | `01_set_transformer.ipynb` | ~30–45 menit | **sudah terukur di lokal**: −0,0021, menang 11/12 |
| 02 | `02_cnn8_inception.ipynb` | ~1,5–2,5 jam | hipotesis |
| 03 | `03_cnn7_tcn_dilatasi.ipynb` | ~1–2 jam | hipotesis |
| 04 | `04_cnn5_konvolusi_dalam.ipynb` | ~4–6 jam | hipotesis, **paling mahal** |
| 05 | `05_cnn6_transformer.ipynb` | ~2–3 jam | hipotesis, **varians tertinggi** |

Kalau kuota GPU terbatas, **01–03 dulu**. 01 satu-satunya yang gain-nya sudah diukur;
02 dan 03 jauh lebih murah dari 04 dengan peluang yang tidak lebih kecil.

04 dan 05 sempat mulai jalan di mesin lokal (RTX 4060) tapi dihentikan setelah 3 jam
sebelum menghasilkan angka — jadi waktunya nyata, hasilnya belum ada.

## Cara pakai

1. **Settings → Accelerator → GPU** (T4 atau P100).
2. **Add Input** → kompetisinya. Notebook mengharapkan path
   `/kaggle/input/competitions/ai-innovation-case-task-1-seismic-magnitude-prediction/seismic-dataset`
   dan otomatis jatuh ke `seismic-dataset/` lokal kalau tidak ketemu.
3. **Add Input** → dataset `nb8-ref` (berisi `nb8_ref.npz`, 334 KB — prediksi OOF + test
   8 kandidat `notebook_8` beserta bobot blend-nya). Sudah ter-upload di
   `/kaggle/input/datasets/timotiuspatrick/nb8-ref/nb8_ref.npz`; notebook mencarinya di
   situ dulu, lalu menelusuri seluruh `/kaggle/input` sebagai cadangan.

   | Notebook | Butuh ref? | Kalau tidak ada |
   |---|---|---|
   | **01** | **wajib** | berhenti — modelnya mempelajari koreksi atas blend nb8 |
   | 02–05 | opsional | training tetap penuh, tapi **sel verdikt dilewati** |

   Sel Setup memvalidasi file-nya langsung: blend 8 kandidat itu harus mereproduksi
   `lb_real` 0,1762. Kalau tercetak `COCOK`, verdiktnya bisa dipercaya.
4. **Run All.**
5. Sel terakhir membungkus semua hasil jadi **satu file zip** di `/kaggle/working/`
   (`hasil_*.zip`, ~280 KB). Unduh dari panel Output, ekstrak `.npz`-nya ke `Case 1/cache/`.

Tiap notebook mencetak sisa waktu setiap fold selesai, jadi progresnya kelihatan sejak
fold pertama — tidak diam berjam-jam seperti run lokal kemarin.

## Isi output tiap notebook

| file | isi |
|---|---|
| `<nama>.npz` | OOF + prediksi test model baru — ini yang dipakai blend lokal berikutnya |
| `blend_<nama>.npz` | hasil blend gabungan dengan 8 kandidat `notebook_8` |
| `blend_<nama>_submission.csv` | siap disubmit langsung dari Kaggle kalau verdiktnya bagus |
| `blend_<nama>_score.json` | `lb_real`, gain, `bias_rnd`, mean/sd sisi bulat |
| `hasil_<nama>.zip` | keempatnya dibungkus |

---

## Aritmatika target — baca sebelum menilai hasil apa pun

Kalibrasi dari 3 submission nyata (R² 0,92): **LB ≈ `lb_real` + 0,0082** (sd 0,0028).

| Target LB | butuh `lb_real` | Δ dari nb8 (0,1762) |
|---|---|---|
| 0,1837 (peringkat 1) | 0,1755 | −0,0007 |
| 0,1800 | 0,1718 | −0,0044 |
| 0,1750 | 0,1668 | −0,0094 |
| **0,1700** | **0,1618** | **−0,0144** |
| **0,1600** | **0,1518** | −0,0244 |

Terobosan terbesar yang pernah ditemukan di repo ini — CNN v3 di `notebook_8` — bernilai
**−0,0070**. **LB 0,17 butuh dua kali lipat terobosan terbesar itu.**

**LB 0,16 butuh `lb_real` 0,1518, dan itu di BAWAH batas oracle-grouping 0,1543** — skor
yang dicapai kalau kita *tahu persis* record mana milik event mana. Post-processing tidak
bisa menembusnya dengan model dasar sekarang. Perlakukan **0,16 sebagai di luar jangkauan**
pendekatan ini; 0,17 sebagai stretch yang butuh beberapa notebook di sini berhasil
sekaligus; **0,1837 (peringkat 1) sebagai target yang realistis dari satu perbaikan sedang.**

Tiap notebook mencetak verdikt eksplisit terhadap kelima ambang itu.

## Dua aturan yang tidak boleh dilanggar

**Jangan menilai kandidat dengan `eb_twmae` mentah.** Rekonstruksi event lewat
`groupby(depth_km, magnitude)` melebur record depth-bulat jadi pseudo-event sampai
**401 record**, sehingga CV over-weight ekor sekitar **3×**. Pakai `lb_real`.

**Kalau `lb_real` dan diagnostik transfer bertabrakan, diagnostik transfer menang.**
`lb_real` mengukur data train; `bias_rnd` serta mean dan sd prediksi subset depth-bulat
mengukur jarak ke test. `notebook_2` dan `notebook_5` dua-duanya memperbaiki CV lalu
memburuk di LB karena aturan ini dilanggar. Notebook di sini mencetak ketiganya dengan
label AMAN/AWAS/BAHAYA.

## Kenapa yang tersisa cuma model deep

Empat ide non-deep diuji di sesi ini dengan protokol holdout jujur, **semuanya gagal**:

| ide | hasil | vonis |
|---|---|---|
| sidik derau pre-P sebagai identitas stasiun | AUC co-membership 0,56 | GAGAL |
| agregasi grup berbobot presisi (SNR/jarak/clipped) | gain +0,0012, menang 1/12 | GAGAL |
| koreksi geser record clipped | gain +0,0004, menang 3/12 | GAGAL |
| sapuan gabungan 729 konfigurasi post-processing | gain +0,0014, menang 1/12 | GAGAL |

Sisi desimal sudah mentok (`lb_real` 0,1437 vs oracle ~0,1488). Hampir seluruh headroom
ada di sisi depth-bulat (0,2074 vs oracle 0,1596), dan dua usaha independen memulihkan
grouping sudah gagal. Yang tersisa: **membuat model per-record-nya benar-benar lebih baik.**
Itulah isi folder ini.

---

# Batch ke-2 (notebook 06-08) — dijalankan 22 Agu 2026: **3 dari 3 GAGAL**

Sumber di root folder ini, versi tereksekusi + zip di `hasil/`, `.npz` sudah di `cache/`.
Titik berangkat tetap `notebook_8`: LB 0,1849, `lb_real` 0,1762.

| # | Notebook | model | tunggal `lb_real` | corr maks vs nb8 | gain holdout | menang | vonis |
|---|---|---|---|---|---|---|---|
| 06 | `06_augmentasi_agresif` | `cnn9_aug` | 0,2080 | **0,970** (cnn3_avg) | +0,0011 | 1/12 | GAGAL |
| 07 | `07_ssl_pretrain` | `cnn10_ssl` | 0,2112 | **0,953** (cnn3_avg) | +0,0012 | 2/12 | GAGAL |
| 08 | `08_head_distribusi` | `cnn11_dist` | 0,2322 | 0,895 (cnn3_dir) | +0,0013 | 0/12 | GAGAL |

**Tidak ada `notebook_11`. `notebook_8` tetap submission terbaik.**

## Gabungan pun tidak menolong — sudah diuji ketujuh kombinasinya

Pertanyaan yang tidak bisa dijawab notebook manapun sendirian (tiap notebook cuma melihat
modelnya sendiri + 8 kandidat nb8). Protokol blend 12-belahan, semua kombinasi:

| kandidat tambahan | `lb_real` | jujur | gain | menang |
|---|---|---|---|---|
| `cnn9_aug` | 0,1760 | 0,1772 | +0,00114 | 1/12 |
| `cnn10_ssl` | 0,1756 | 0,1772 | +0,00122 | 2/12 |
| `cnn11_dist` | 0,1762 | 0,1773 | +0,00126 | 0/12 |
| `cnn9_aug`+`cnn10_ssl` | 0,1756 | 0,1771 | +0,00111 | 2/12 |
| `cnn9_aug`+`cnn11_dist` | 0,1761 | 0,1772 | +0,00114 | 2/12 |
| `cnn10_ssl`+`cnn11_dist` | 0,1757 | 0,1771 | +0,00107 | 3/12 |
| **ketiganya** | 0,1757 | 0,1772 | **+0,00103** | **2/12** |

Polanya seragam dan sangat rapat: `lb_real` mentah turun 0,0002-0,0006, **gain holdout
jujur positif di ketujuh kombinasi**, menang maksimal 3/12. Ini persis pola yang menolak
CNN+GRU di nb8 — kandidat ke-N selalu bisa menurunkan angka di data tempat bobotnya
dipilih. Diagnostik transfer semuanya aman (`bias_rnd` +0,030…+0,032, mean 5,257…5,259,
sd 0,395…0,396); yang gagal kriteria utamanya.

## Kenapa gagal: sebab yang sama dengan batch 1, plus satu yang baru

**06 dan 07 — redundan.** Korelasi 0,970 dan 0,953 terhadap `cnn3_avg`. Ini persis vonis
keempat CNN batch 1 (0,92-0,96). Augmentasi lebih agresif dan pra-latih SSL sama-sama
menghasilkan **model yang melihat hal yang sama** dengan CNN v3, cuma sedikit lebih buruk.

Khusus 07 ini penting karena SSL adalah **prioritas 1 di `CLAUDE.md` sejak notebook_8** —
satu-satunya cara menambah data efektif (12.805 waveform tak berlabel). Hipotesisnya
"batasannya jumlah event, bukan jumlah record". Hasilnya: pra-latih memang jalan (bobot
encoder ter-transfer, ada `enc_pretrain.pt` 7 MB), dan tetap **0,2112 — lebih buruk dari
`cnn3_avg` 0,2074 yang dilatih dari nol**. Dapat bobot blend 0,17, gain tetap positif.
**Hipotesis "kurang data" ditolak dengan bukti langsung.**

**08 — modelnya memang lebih lemah.** 0,2322 raw, terburuk dari ketiganya. Korelasinya
paling rendah (0,895) tapi tidak cukup rendah untuk menebus selisih skor; bobot blend yang
diberikan cuma 0,011.

### Ringkasan sebaran 41-bin sudah disapu ulang — tidak ada yang tersembunyi di sana

Notebook 08 menyimpan posterior penuh (`cnn11_dist_raw.npz`) dan memilih `q0.60` memakai
`lb_real` **tunggal**. Untuk blend yang menentukan dekorelasi, jadi seluruh keluarga
ringkasan disapu ulang di lokal (mean, mode, kuantil bin-keras 0,50-0,65, kuantil
**interpolasi** 0,55-0,75 — yang terakhir ini tidak dicoba notebook sama sekali):

| ringkasan | `lb_real` raw | `bias_rnd` | corr maks vs nb8 |
|---|---|---|---|
| `mean` | 0,2331 | −0,023 | 0,907 |
| `mode` | 0,2484 | −0,021 | 0,864 |
| `q0.60` (pilihan notebook) | 0,2322 | +0,012 | 0,895 |
| **`qi0.70`** (interpolasi, terbaik) | **0,2314** | +0,024 | 0,892 |

Selisihnya 0,0008 — di dalam derau. Diuji di blend: `qi0.70` memberi gain **+0,00124
(menang 0/12)** sendirian, dan +0,00103 (2/12) bersama dua yang lain — sama persis dengan
`q0.60`. **Pilihan ringkasan bukan penyebab kegagalannya; kepalanya yang memang lebih
lemah.** Jangan ulangi sapuan ini.

## Yang ditutup oleh batch ini

1. **Augmentasi lebih agresif** (time-jitter picker P, channel dropout, cutout, mixup).
2. **Pra-latih self-supervised** — prioritas 1 yang tertunda sejak nb8. Ditolak dengan bukti.
3. **Kepala distribusi / prediksi ekor lewat kuantil** — termasuk seluruh keluarga ringkasan.

Digabung dengan batch 1, **keluarga "model deep baru atas waveform yang sama" habis
seluruhnya: 7 dari 8 notebook GPU gagal, dan satu-satunya yang lolos protokol (set-transformer)
justru rugi di LB.** Tujuh arsitektur/regime training berbeda semuanya mendarat di
`lb_real` 0,208-0,232 dengan korelasi 0,89-0,97 terhadap CNN v3. Itu bukan kebetulan —
itu plafon informasi 5 detik waveform yang bisa dicapai konvolusi 1D.


---

# Batch ke-3 (notebook 09-10) — dijalankan 22 Agu 2026, malam

**Tidak ada `notebook_11`. `notebook_8.csv` tetap submission terbaik (LB 0,1849).**
Tapi vonis kedua notebook ini **tidak setara**: notebook 10 gagal bersih, notebook 09
**belum benar-benar terjawab** karena gerbang kontrolnya cacat.

| # | notebook | model | vonis |
|---|---|---|---|
| 09 | `09_tta_klip` | `cnn12a/b` (± TTA) | **TERTUNDA** — konstanta kontrol salah jenis, hasil bisa diselamatkan tanpa GPU |
| 10 | `10_cnn_fitur_gabung` | `cnn13_join` | **GAGAL** telak dan bersih |

Kedua notebook juga mati di sel verdikt dengan `ValueError: could not convert string to
float` — `simpan()` memanggil `float(v)` pada `res["_nama"]` yang berisi string, dan
`np.isscalar("teks")` bernilai `True`. **Sudah diperbaiki** di `tools/mk_kaggle.py` dan
kedua notebook. Yang hilang karenanya cuma `_score.json` dan zip bundel; `.npz` dan
`_submission.csv` sudah tertulis sebelum crash.

## notebook 10 — `cnn13_join`: GAGAL, tutup keluarganya

Satu jaringan melihat waveform **dan** 196 fitur rekayasa sekaligus, menggantikan cabang
skalar 8-dim `Net3` dengan cabang fitur 196-dim ber-MLP. Ini "satu-satunya yang berbentuk
terobosan" menurut antrian batch 3.

| | nilai | ambang |
|---|---|---|
| `lb_real` blend | **0,2167** (jujur 0,2865) | harus < 0,1762 |
| gain holdout | **+0,0957** | harus < 0 |
| menang | **0/12** | harus ≥ 7/12 |
| `bias_rnd` | **+0,115** | harus ≤ 0,05 |

Tidak ada satu pun kriteria yang lewat, dan margin kegagalannya besar — ini bukan kandidat
tipis, ini model yang rusak. `bias_rnd` +0,115 adalah mode kegagalan `notebook_2`
(+0,137) yang sudah dikenal: begitu jaringan bisa membaca tipe depth dari 196 fitur, ia
memakai prior katalog train yang tidak transfer ke test. Penahan arsitekturalnya
(`p_feat_drop`) tidak cukup.

Gerbang korelasi lolos di varian pertama sehingga varian modality-dropout kuat
**dilewati** — menghemat ~1 jam GPU. Itu keputusan yang benar, bukan langkah terlupa.

**Keluarga "gabungkan input LightGBM ke dalam CNN" DITUTUP.**

## notebook 09 — gerbang kontrolnya membandingkan apel dengan jeruk

Notebook mencetak sendiri:

```
KONTROL: K=1 lb_real 0.1947   (cnn3 di lokal = 0,2091)
  TIDAK COCOK -- selisih > 0,004 dari cnn3. Verdikt di bawah TIDAK bisa dipercaya
```

lalu menjalankan seluruh verdiktnya. Selisih 0,0144 ke arah "Kaggle jauh lebih baik" itu
mustahil untuk resep yang identik, dan memang bukan itu yang terjadi:

- `sapu_tta()` menghitung `lb_real(post_tr(o))` — **sudah** lewat post-processing.
- Konstanta 0,2091 di `CLAUDE.md` adalah `lb_real` **MENTAH**.
- Post-processing memangkas **0,0193**. Seluruh "gain" itu artefak jenis angka.

Diukur ulang di lokal (`experiments/exp50_kontrol_nb12.py`), `Post(0,95 / 0,5 / 150 /
1,15 / 1,05)` persis notebook Kaggle:

| kandidat | MENTAH | post | dec | rnd |
|---|---|---|---|---|
| `cnn3` (3 seed) | 0,2091 | **0,1898** | 0,1439 | 0,2339 |
| `cnn3_s2` (3 seed) | 0,2089 | 0,1904 | 0,1451 | 0,2338 |
| `cnn3_avg` (6 seed) | 0,2074 | **0,1888** | 0,1438 | 0,2319 |

**Konstanta kontrol yang benar adalah 0,1898, bukan 0,2091.**

### Vonis yang benar: run A 0,0049 LEBIH BURUK, bukan 0,0144 lebih baik

| | `lb_real` (post) | dec | rnd | bias |
|---|---|---|---|---|
| `cnn3` lokal, 3 seed | **0,1898** | 0,1439 | 0,2339 | +0,028 |
| **A K=1 Kaggle, resep sama** | **0,1947** | 0,1457 | 0,2417 | +0,032 |
| A K=8 (+TTA) | 0,1936 | 0,1458 | 0,2396 | +0,032 |
| B K=1 (+bobot klip) | 0,1914 | 0,1443 | 0,2366 | +0,038 |
| **B K=8 (+TTA+klip)** | **0,1904** | 0,1429 | 0,2359 | +0,037 |
| `cnn3_avg` lokal, 6 seed | **0,1888** | 0,1438 | 0,2319 | +0,029 |

Gap lingkungan **+0,0049**, sementara derau antar-paket 3-seed di lokal cuma **0,0006**
(`cnn3` vs `cnn3_s2`). **8,4× derau seed — itu bukan kebetulan.** Dan letaknya bukan di
mana-mana: sisi desimal +0,0018, sisi bulat **+0,0078**. Gap yang menumpuk di sisi bulat
menunjuk ke anchor ridge / fitur `extract()`, bukan ke bobot konvolusinya.

### Yang tetap SAH dari notebook 09

Perbandingan A↔B dan K=1↔K=8 lewat jalur kode yang sama, tanpa menyentuh konstanta lokal,
jadi gap lingkungan saling meniadakan:

| efek terisolasi | besarnya |
|---|---|
| TTA (K=1 → K=8) | **+0,0011** |
| bobot loss record clipped ×2,26 | **+0,0033** |
| keduanya | **+0,0043** |
| └ khusus MAE record clipped | **+0,0093** |

Bobot clipped **tiga kali lebih besar dari TTA**, dan diagnostik yang menentukan (MAE
record clipped) bergerak benar — jadi mekanismenya nyata, bukan derau. `bias_rnd` bergeser
+0,000 / −0,001 saat TTA dinyalakan, persis seperti yang diprediksi dari simetri rotasi/flip.

### Kenapa verdikt blend-nya tetap negatif, dan kenapa itu belum final

`cnn12b_tta (ganti)` mendapat gain holdout **+0,00044, menang 4/12** — gagal ambang. Tapi
pencarian bobot itu membandingkan kandidat **Kaggle** (handicap 0,0049) terhadap kandidat
pembanding **lokal**. Handicap lingkungan masuk sebagai kerugian ide.

Perbandingan yang benar: `cnn12b_tta` 0,1904 vs `cnn3_avg` 0,1888 → **+0,0016 lebih
buruk**. Konsisten dengan gain blend +0,0004. Jadi angkanya koheren — yang belum terjawab
adalah **apakah TTA + bobot clipped memperbaiki resepnya kalau baselinenya sehat.**
Aritmetikanya: 0,1888 − 0,0043 ≈ **0,1845**, jauh di bawah `cnn3_avg`.

### Cara menyelesaikannya TANPA GPU

`cnn12a_syms.npz` dan `cnn12b_syms.npz` **sudah tertulis sebelum crash** (sel 15 dan 17),
dan isinya prediksi per elemen simetri berbentuk `(8, n)` — keempat kandidat bisa
direkonstruksi dari situ.

```bash
python "Case 1/tools/serap_nb12.py" <folder-unduhan-dari-Kaggle>
```

Skrip itu menjalankan dua uji: UJI 1 seperti nb09 (pembanding = blend nb8 dengan
`cnn3_avg` lokal), dan **UJI 2 dengan gap dinetralkan** — slot CNN di pembanding diisi
`cnn12a`, sehingga pembanding dan kandidat sama-sama dari Kaggle. UJI 2 yang menentukan.

- **UJI 2 lolos** → idenya benar, kegagalan nb09 murni gap lingkungan. Langkah berikutnya
  menerapkan TTA + bobot clipped di pipeline **lokal**, bukan submit file Kaggle-nya.
- **UJI 2 gagal** → tutup kedua sumbu, catat di `CLAUDE.md`.

**Ambil dua file itu dari panel Output Kaggle selagi sesinya masih hidup.** Kalau hilang,
run 160 menit itu harus diulang.

---

## nb09 TERJAWAB (23 Agu 2026): sumbunya DITUTUP, tapi bukan karena gap lingkungan

`cnn12a_syms.npz` + `cnn12b_syms.npz` diselamatkan dari zip Kaggle dan diserap lewat
`tools/serap_nb12.py`. Keempat kandidat direkonstruksi tanpa GPU. Angka-angka Kaggle
tereproduksi persis, jadi rekonstruksinya benar:

| kandidat | `lb_real` (post) | dec | rnd | bias |
|---|---|---|---|---|
| `cnn3` lokal (3 seed) | 0,1898 | 0,1439 | 0,2339 | +0,028 |
| `cnn3_avg` lokal (6 seed) | **0,1888** | 0,1438 | 0,2319 | +0,029 |
| `cnn12a` (Kaggle, resep sama) | 0,1947 | 0,1457 | 0,2417 | +0,032 |
| `cnn12a_tta` | 0,1936 | 0,1458 | 0,2396 | +0,032 |
| `cnn12b` | 0,1914 | 0,1443 | 0,2366 | +0,038 |
| `cnn12b_tta` | 0,1904 | 0,1429 | 0,2359 | +0,037 |

### UJI 2 — gap lingkungan dinetralkan, dan hasilnya tetap negatif

Pembanding = blend nb8 dengan slot `cnn3_avg` diisi `cnn12a`, sehingga pembanding dan
kandidat sama-sama dari Kaggle:

| kandidat | `lb_real` | jujur | gain | menang | bias |
|---|---|---|---|---|---|
| `cnn12a_tta` (TTA saja) | 0,1762 | 0,1774 | +0,00126 | 0/12 | +0,034 |
| `cnn12b` (klip saja) | 0,1755 | 0,1766 | +0,00036 | 5/12 | +0,035 |
| **`cnn12b_tta` (keduanya)** | 0,1754 | 0,1766 | **+0,00029** | **6/12** | +0,035 |

Ambangnya gain < 0 **dan** menang ≥ 7/12. `cnn12b_tta` meleset di dua-duanya, tapi
**ini kandidat terdekat yang pernah ada**: pembanding sebelumnya +0,00103 dengan 2/12,
dan batch 2 +0,0011…+0,0013 dengan 0-3/12. Bacaan jujurnya: **seri, bukan kalah telak.**
Di bawah aturan satu submission final tanpa lindung nilai, seri bukan alasan menggeser
`notebook_8`.

### Kenapa gain single-model +0,0043 menguap jadi +0,0003 di blend

Bukan misteri, dan bukan gap lingkungan — gap itu sudah dinetralkan di UJI 2. Blend nb8
punya **7 kandidat lain** yang sudah menutupi sebagian besar varians yang dibuang TTA dan
sebagian besar error record clipped. Ini pola yang persis sama dengan seluruh riwayat repo
ini: perbaikan kandidat ke-N diserap blend, bukan diteruskan.

**Konsekuensi praktisnya: menjalankan ulang TTA + bobot clipped di pipeline LOKAL tidak
lagi bisa dibenarkan.** Aritmetika 0,1888 − 0,0043 ≈ 0,1845 memang benar untuk model
tunggal, tapi UJI 2 menunjukkan pada tingkat blend efeknya netral pada provenance yang
sama. Baseline lokal yang lebih baik tidak mengubah mekanisme penyerapan itu. **Hemat
~160 menit GPU: jangan dijalankan.**

**TTA dan bobot record `is_clipped` DITUTUP sebagai sumbu.**

### Gap lingkungan: lebih besar dari sekadar skor

Korelasi OOF `cnn12a` vs `cnn3` untuk resep identik cuma **0,9722** — padahal dua paket
3-seed di lokal berkorelasi **0,9875**. Jadi run Kaggle bukan cuma lebih buruk 0,0049, ia
menghasilkan model yang **berbeda** lebih jauh dari yang bisa dijelaskan seed. Penyebabnya
tetap belum ditemukan; `build_input()` dan grup simetri sudah diperiksa dan identik, dan
gapnya menumpuk di sisi bulat (+0,0078 vs +0,0019 desimal) yang menunjuk ke anchor ridge /
`extract()`.

**Ini satu-satunya temuan yang masih terbuka**, dan nilainya bukan di sumbu ini melainkan
di setiap notebook Kaggle berikutnya: kalau ada, hasilnya membawa handicap 0,0049 yang
tidak pernah tercatat di batch 1 dan 2.

### nb10: gerbang korelasinya lolos karena modelnya RUSAK, bukan karena ia beragam

`cnn13_join.npz` diserap juga. Sebagai model tunggal: `lb_real` **0,3730** mentah
(0,3668 post), `bias_rnd` **+0,378**, korelasi maks terhadap kandidat nb8 cuma **0,226**.

Notebook memakai gerbang "korelasi maks < 0,95" dan melaporkan LOLOS, lalu melewati varian
modality-dropout kuat atas dasar itu. Gerbangnya memang lolos — tapi karena modelnya tidak
memprediksi apa-apa yang berguna, bukan karena ia melihat sesuatu yang baru.

> **Aturan baru: gerbang korelasi tidak sah tanpa gerbang skor.** Korelasi rendah cuma
> bermakna kalau kandidatnya sendiri kompetitif. `cnn13_join` (0,3730 vs `cnn3_avg` 0,2074
> mentah) seharusnya dihentikan oleh ambang skor sebelum korelasinya dibaca sama sekali.
