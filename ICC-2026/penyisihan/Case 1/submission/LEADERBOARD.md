# Catatan Submission — Case 1

Log CV vs LB tiap submission. **Selalu update setelah dapat skor LB**, karena hubungan
CV↔LB di case ini tidak lurus dan hanya bisa dipelajari dari akumulasi titik nyata.

| # | File | CV lama | `lb_real` | Estimasi LB | **LB aktual** | `bias_rnd` | Perubahan kunci |
|---|---|---|---|---|---|---|---|
| 1 | `notebook_1.csv` | 0,1826 | — | 0,1953 | **0,2005** | +0,076 | Fitur EEW + smoothing per event + ekspansi global |
| 2 | `notebook_2.csv` | 0,1789 | — | 0,1902 | **0,2262** ❌ | +0,137 | Fitur grup di-mask (NaN) untuk depth bulat |
| 3 | `notebook_3.csv` | 0,1855 | 0,1945 | 0,1988 | **0,1996** ✅ | +0,047 | Balik ke fitur grup penuh, ekspansi per-subset |
| 4 | `notebook_4.csv` | 0,1850 | — | 0,1983 | tidak disubmit | +0,048 | + CNN v2 (bobot 0,10) + refit 100% data |
| 5 | `notebook_5.csv` | 0,1790 | — | 0,1932 | **0,2063** ❌ | +0,056 | Anchor ridge + bobot blend per-subset |
| 6 | `notebook_6.csv` | 0,1803 | **0,1845** | 0,191 | **0,1952** ✅ | +0,027 | Metrik CV diperbaiki; blend 7 kandidat + CNN MagNet |
| 7 | `notebook_7.csv` | — | 0,1822 | 0,194 | tidak disubmit | +0,026 | + fitur depth taksiran, CNN-residual; rata-rata 3 himpunan blend |
| 8 | `notebook_8.csv` | — | **0,1762** | 0,187–0,192 | **0,1849** ✅✅ | +0,031 | **CNN v3 multi-task + augmentasi derau pre-P (bobot CNN 0,53)** |
| 9 | `notebook_9.csv` | — | **0,1718** | 0,1800 | **0,1856** ❌ | +0,029 | **Koreksi set-transformer (Kaggle, 3 seed) di-demean saat apply, lam 0,50** |
| 10 | `notebook_10.csv` | — | 0,1773 | tidak diestimasi | **0,1871** ❌❌ | +0,028 | **Bobot blend condong sisi desimal (`FD_sel` 0,80); Model B 0,32 → 0,16** |

## Dua kegagalan prediksi, satu penyebab

notebook_2 dan notebook_5 sama-sama memperbaiki CV lalu memburuk di LB. Selama ini keduanya
didiagnosis terpisah (fitur bocor; bobot blend overfit). Penyebab sebenarnya satu, dan ada di
**fungsi evaluasinya sendiri**.

`ev = groupby(["depth_km","magnitude"])` melebur record depth-bulat jadi pseudo-event sebesar
**401 record**. Karena EB-TWMAE menimbang per event, satu pseudo-event raksasa bermagnitudo
5,1 dapat bobot 1,0 di CV padahal di LB ia ~50 gempa dengan total bobot 50. Hasilnya CV
**over-weight ekor di sisi depth-bulat sebesar 3×**:

| Bobot metrik, sisi depth-bulat | CV | realistis |
|---|---|---|
| event M >= 5,5 | 0,891 | 0,638 |
| event M >= 6,5 | **0,155** | **0,052** |

Setiap tuning sisi bulat — alpha ekspansi, importance weighting, bobot blend per-subset —
mengoptimalkan target yang salah. Terlihat langsung di sweep alpha: kriteria lama monoton
membaik sampai 1,15 (dan seterusnya), kriteria realistis punya optimum interior di 1,05.

## Metrik pengganti: `lb_real`

```python
# lab_common.py
make_ev_real(seed, chunk=8)   # pecah pseudo-event depth-bulat DANGKAL (<100 km) jadi ~8 record
                              # depth >=100 km TIDAK dipecah (grup 67-100% murni)
lb_real(p) = 0.49*part_real(p, dec=True) + 0.51*part_real(p, dec=False)
```

Rata-rata 8 undian acak. **Pakai untuk memeringkat kandidat, bukan memprediksi angka LB** —
ia bias rendah ~0,005 sebagai penduga absolut (nb3: `lb_real` 0,1945 vs LB 0,1996).

## Tiga diagnostik transfer (semua wajib dicatat sebelum submit)

| Submission | `bias_rnd` | mean prediksi subset bulat<100km | sd prediksi sisi bulat | LB |
|---|---|---|---|---|
| notebook_1 | +0,076 | 5,293 | — | 0,2005 |
| notebook_2 | +0,137 | 5,385 | — | 0,2262 |
| notebook_3 | +0,047 | 5,276 | 0,424 | **0,1996** |
| notebook_5 | +0,056 | 5,282 | 0,447 | 0,2063 |
| notebook_6 | +0,027 | 5,265 | 0,388 | 0,1952 |
| notebook_8 | **+0,031** | **5,261** | **0,396** | **0,1849** |

Fit kuadratik atas tiga titik pertama menaruh minimum di mean ≈ **5,272**. notebook_6 paling
dekat. Tambahan pelajaran dari nb5: **sd prediksi sisi bulat naik = LB memburuk** — nb5 satu-
satunya yang menaikkannya, dan satu-satunya yang rugi tanpa `bias_rnd` melonjak.

## Status submission

- `notebook_3.csv` — **menurut user TIDAK disubmit**, walaupun tabel di atas mencatat
  LB 0,1996. Angka dan kalibrasinya sengaja **dibiarkan apa adanya** atas permintaan user;
  dicatat di sini supaya konfliknya tidak hilang. Kalau 0,1996 memang bukan skor LB nyata,
  kalibrasi 3 titik di bawah efektif tinggal 2 titik (nb6 dan nb8) dan offsetnya bergeser
  dari +0,0082 ke ~+0,0097 — estimasi LB `notebook_9` jadi ~0,1815, bukan 0,1800.
  **Belum dihitung ulang.**
- `notebook_9.csv` — **DISUBMIT, LB 0,1856** — lebih buruk dari nb8 (0,1849). Prediksi
  0,1800 meleset **+0,0056**, miss terbesar sejauh ini. Post-mortem lengkap di bagian
  "KEGAGALAN KETIGA" di bawah. **Peringkat tetap dari `notebook_8.csv`.**
- `notebook_4.csv` — arsip, tidak disubmit.
- `notebook_8.csv` — **disubmit, LB 0,1849** (peringkat **2**, dari 0,1952 di nb6).
  `lb_real` 0,1762 (jujur 0,1774), gain −0,0084 holdout, **menang 12/12** belahan, dan
  **kedua sisi membaik** (dec 0,1506 -> 0,1437, rnd 0,2171 -> 0,2074). Kuncinya CNN v3,
  bukan post-processing.
- `notebook_7.csv` — tidak disubmit (gain di dalam derau, digantikan nb8).
  **Prediksi LB ~0,194** — gain-nya kecil dan di dalam derau (menang 7-8/12 belahan).
  Nilai utamanya di titik kalibrasi, bukan di skor. Perubahan vs nb6: fitur kedalaman
  taksiran, CNN target-residual, `resB_p05`, dan bobot = rata-rata 3 himpunan kandidat.
- `notebook_6.csv` — **disubmit, LB 0,1952** (personal best, peringkat 4).
  Prediksi 0,191, meleset +0,004. Perubahan vs notebook_3:
  1. kriteria seleksi diganti `lb_real` (semua tuning sisi bulat dihitung ulang)
  2. `alpha` sisi bulat 1,15 -> 1,05; smoothing depth-bulat-dalam (>=150 km, lam 0,5)
  3. keluarga model baru: anchor-residual × `sqrt(cnt)` weighting
  4. CNN gaya MagNet (bentuk ternormalisasi + skala disuntik balik), bobot 0,23
  5. bobot blend = rata-rata lintas 12 belahan, bukan argmin data penuh


## KALIBRASI `lb_real` -> LB dengan 3 titik (INI YANG DIPAKAI SEKARANG)

| submission | `lb_real` | LB aktual | offset |
|---|---|---|---|
| notebook_3 | 0,1945 | 0,1996 | +0,0051 |
| notebook_6 | 0,1845 | 0,1952 | +0,0107 |
| notebook_8 | 0,1762 | **0,1849** | +0,0087 |

**Aturan pakai:**

```
LB ~ lb_real + 0,0082          (sd 0,0028; paling sederhana, cukup akurat)
LB ~ 0,791 * lb_real + 0,0468  (regresi 3 titik, R2 = 0,92)
```

### Koreksi penting: "hanya 44% gain yang transfer" itu SALAH

Ditulis setelah nb3 -> nb6 (Delta`lb_real` −0,0100 vs DeltaLB −0,0044) dan membuat estimasi
nb8 terlalu pesimistis (diprediksi 0,187–0,192, aktual **0,1849**). Di nb6 -> nb8 rasionya
justru **1,24** — gain-nya transfer **lebih besar** dari yang diukur di OOF.

Pelajarannya: **rasio yang dihitung dari 2 titik itu tidak bermakna.** Selisih `lb_real`
nb3->nb6 kecil (0,0100) sehingga rasionya sangat sensitif terhadap derau LB, dan LB publik
cuma 30% data test. Pakai **model offset tetap**, bukan rasio.

### Target peringkat 1

Peringkat 1 (Kingpul) ada di **0,1837**, kita **0,1849** — selisih **0,0012**.

```
LB 0,1837  <->  lb_real ~ 0,1755 (offset tetap)  atau  ~0,1730 (regresi)
lb_real sekarang: 0,1762
```

Jadi jaraknya **0,0007–0,0032 di `lb_real`** — satu perbaikan model berukuran sedang.
Ingat juga LB publik hanya 30% data test; selisih 0,0012 antara peringkat 1 dan 2 sebagian
besar derau, dan peringkat final dihitung dari 70% sisanya.

## Peringkat leaderboard publik (per submission notebook_8)

| # | Tim | Skor |
|---|---|---|
| 1 | Kingpul | 0,1837 |
| **2** | **Rizzz (kita)** | **0,1849** |
| 3 | EspressoCampurRedbull | 0,1860 |
| 4 | Letdown | 0,1898 |

Naik dari peringkat 4 (0,1952) ke peringkat 2 dalam satu submission.

## Aturan submission

0. Kalau file submission sudah dibuat tapi belum disubmit, tandai eksplisit di "Status
   submission" — jangan tertukar dengan yang sudah punya skor.
1. Satu perubahan terkendali per submission kalau memungkinkan.
2. Catat `lb_real`, `bias_rnd`, mean **dan sd** prediksi subset depth-bulat **sebelum** submit.
3. Update tabel di atas begitu skor LB keluar.
4. Curigai fitur apapun yang berkorelasi dengan tipe depth atau ukuran grup.
5. **Jangan pernah menilai kandidat dengan `eb_twmae(y, p, ev)` mentah lagi.**

## Optimisme pemilihan bobot — selalu diukur, jangan diasumsikan nol

| notebook | kandidat | optimisme (separuh data) | koreksi data penuh |
|---|---|---|---|
| notebook_5 | 6 | +0,0035 | +0,0025 |
| notebook_6 | 7 | +0,0020 | +0,0014 |

notebook_6 memakai **rata-rata bobot lintas 12 belahan** alih-alih argmin di data penuh, jadi
lebih tahan derau seleksi (skornya kebetulan sama, 0,1845, tapi variansnya lebih kecil).

**Bukti kehati-hatian ini perlu:** waktu MLP divergen (OOF 0,778) ikut jadi kandidat di nb5,
pencarian bobot tetap memberinya 0,36 dan "memperbaiki" skor. Jaga kandidat tetap sedikit.

## Delapan keluarga ide di notebook_7 — tujuh gagal

Semua dinilai dengan `lb_real` + `bias_rnd`.

| Ide | Hasil | Vonis |
|---|---|---|
| Soft grouping dari classifier co-membership (AUC 0,79) | merebut 0,3–1,0% headroom oracle | GAGAL |
| Koreksi covariate shift, density ratio train-vs-test (AUC 0,80) | resA 0,2245 vs 0,2101 | GAGAL |
| Eksponen tail `w(M)^0,5` / `^1,5` | 0,2120 / 0,2099 vs 0,2101 | nol |
| CNN 2D di spektrogram STFT | `lb_real` 0,2536 (korelasi 0,84) | lemah |
| **Cari hyperparameter ULANG** di bawah metrik terkoreksi (8 konfigurasi) | terbaik 0,2029 vs baseline 0,2031 | GAGAL |
| Koreksi bias residual (geser per subset + tren SNR/Pd) | gain holdout −0,0007, menaikkan mean sisi bulat ke 5,285 | **DITOLAK** |
| Smoothing penuh grup depth-bulat-dalam di test | sd prediksi `depth=375` cuma 0,089, sudah rapat | nol |
| **Taksiran kedalaman dari waveform** | resA 0,2101 -> **0,2088**, resB 0,2036 -> **0,2031** | ✅ kecil |

### Metrik seleksi boleh di-override oleh diagnostik transfer

Koreksi bias residual lolos semua uji internal — tren residualnya nyata (`snr_db` kuintil
terendah −0,083 vs tertinggi +0,012), parameternya konsisten di 12 belahan, `lb_real`
membaik. Tapi ia mendorong rata-rata prediksi subset depth-bulat 5,265 -> **5,285**, dan dua
submission yang pernah ke wilayah itu (nb2 5,385, nb5 5,282) dua-duanya rugi di LB. Ditolak.

**`lb_real` mengukur data train; `bias_rnd` dan mean subset mengukur jarak ke test. Kalau
bertabrakan, yang kedua menang.**

### Taksiran kedalaman: kecil tapi mekanismenya benar

`depth = 10.0` adalah nilai default katalog — kedalaman aslinya tidak terselesaikan, padahal
`sqrt(dist^2 + depth^2)` memakainya dan itu masuk ke semua fitur terkoreksi jarak. Regressor
kedalaman dilatih **hanya di record depth-desimal** (kedalaman asli), semua fitur turunan
depth dibuang: holdout event desimal R² **0,458**, dan untuk record `depth = 10.0`
taksirannya bermedian **19,2 km** — default katalog memang terlalu dangkal.

Gain-nya kecil (−0,0013) tapi **seluruhnya jatuh di sisi depth-bulat**, persis subset yang
kedalamannya palsu. Itu yang membuatnya layak dipakai, bukan angkanya.

### Yang belum pernah diuji di LB dan paling layak berikutnya

**Refit 100% data** untuk prediksi test — sekarang test diprediksi rata-rata 5 model fold
yang masing-masing dilatih 80% data. Dengan hanya ~905 event efektif, selisih 80% vs 100%
lebih berarti dari biasanya. **Tidak bisa divalidasi lewat OOF**; satu-satunya cara tahu
adalah submit. `notebook_4` sempat memakainya tapi tidak pernah disubmit.

## TEROBOSAN nb8: model deep-nya yang kurang dilatih, bukan datanya yang habis

Sekitar **25 keluarga ide** berturut-turut memberi <= 0,001 setelah nb6. Kesimpulan
"informasi dataset ini sudah habis" terasa makin masuk akal — dan salah. Satu perubahan
memberi **−0,0070 `lb_real`, menang 12/12 belahan**, lebih besar dari semua tambalan
sebelumnya digabung.

| CNN | `lb_real` |
|---|---|
| v1 / v2 (waveform mentah) | — (CV 0,2494 / 0,2447) |
| MagNet-style (nb6) | 0,2232 |
| + target residual anchor | 0,2206 |
| **v3** | **0,2091** |

Empat perubahan di v3, tidak ada yang eksotis:
1. **Multi-task** — kepala kedua memprediksi `log10(depth)`, dihitung hanya untuk record
   depth-desimal (bobot 0,15).
2. **Augmentasi derau fisik** — tempel jendela pre-P dari record lain, amplitudo acak
   0–0,6x. Derau stasiun sungguhan, bukan Gaussian sintetis.
3. Blok Squeeze-Excitation, jaringan lebih lebar (w=64, 5 blok).
4. Jadwal lebih panjang: 80 epoch, rata-rata 10 epoch terakhir, 3 seed.

Di blend ia dapat **bobot 0,404** — kandidat tunggal terbesar — walau sebagai model tunggal
masih kalah dari LightGBM terbaik (0,2028). Sebabnya korelasinya cuma **0,878**.

### Dua pelajaran

**"Sudah plateau" adalah pernyataan tentang keluarga ide, bukan tentang data.** Ini kedua
kalinya kesimpulan plateau di repo ini terbukti salah (nb4: metriknya yang cacat; nb7: model
deep-nya yang kurang dilatih). Sebelum menyatakan plateau, tanyakan **keluarga apa yang belum
pernah digarap sungguh-sungguh**, bukan berapa banyak ide yang sudah gagal.

**Catatan "jangan lakukan X" harus menyebutkan untuk siapa.** "Jangan normalisasi amplitudo
per-record" benar untuk fitur pohon dan salah total untuk CNN — aturan tanpa cakupan itu
menahan model deep selama empat notebook.

## Batas teoretis — dihitung ulang dengan metrik terkoreksi

| | sekarang (nb6) | oracle grouping | headroom |
|---|---|---|---|
| sisi desimal | 0,1541 | 0,1488 | 0,0053 |
| sisi bulat | 0,2188 | 0,1596 | **0,0592** |
| gabungan `lb_real` | 0,1845 | 0,1543 | 0,0328 |

Headroom sisi bulat ternyata **lebih besar** dari perkiraan lama (0,059 vs 0,039) — tapi
sudah dibuktikan tidak bisa dipanen: classifier co-membership mencapai AUC 0,79 (bukan 0,57
seperti klaim nb5 yang labelnya cacat), namun soft/hard smoothing berbasis probabilitas itu
hanya merebut **0,3–1,0%** dari headroom. Classifier cuma yakin untuk pasangan yang
prediksinya sudah mirip.

Konsekuensi: batas praktis pendekatan ini ada di sekitar `lb_real` 0,18, yaitu LB ~0,185.
Untuk menembus LB 0,18 kemungkinan besar dibutuhkan sumber informasi baru.

---

# Sesi lanjutan sesudah notebook_8 — empat ide non-deep, semuanya gagal

Semua dinilai dengan `lb_real` + protokol holdout jujur (pilih di separuh event, ukur di
separuh lain, 12 belahan). Acuan: nb8 `lb_real` 0,1762.

| Ide | Hasil holdout jujur | Vonis |
|---|---|---|
| **Sidik derau pre-P sebagai identitas stasiun** | AUC co-membership 0,56; smoothing tetangga memperburuk di 16/16 setelan | GAGAL |
| **Agregasi grup berbobot presisi** (SNR / jarak / clipped, bukan median) | gain +0,0012, menang **1/12** | GAGAL |
| **Koreksi geser record clipped** | gain +0,0004, menang **3/12** | GAGAL |
| **Sapuan gabungan 729 konfigurasi post-processing** | gain +0,0014, menang **1/12** | GAGAL |
| **Set-transformer atas grup depth** | gain **−0,0021**, menang **11/12** | ✅ tapi lihat catatan |

## Sidik derau: hipotesisnya benar, sinyalnya terlalu lemah

Dataset tidak punya `station_id`, padahal derau ambient sebelum P adalah sidik jari situs.
Klaster PSD pre-P memang menunjukkan efek nyata: pada sisi depth-desimal (grup ≈ event
sungguhan), record satu event jatuh di klaster yang sama **jauh di atas peluang acak** —
K=40 memberi fraksi klaster unik 0,700 vs 0,811 acak.

Tapi begitu diukur langsung sebagai AUC pasangan, hasilnya cuma **0,561**. Smoothing
tetangga-terdekat berbasis jarak derau memperburuk skor di **seluruh 16 kombinasi**
(k ∈ {4,8,16,32} × lam ∈ {0,15…0,6}); yang terbaik 0,1769 vs 0,1762.

Catat juga: AUC dari kemiripan prediksi saja adalah **0,981** — dan itu **sirkular**,
persis kelemahan yang membunuh classifier co-membership nb7. Record satu event punya label
sama, jadi model bagus otomatis memberi prediksi mirip. Angka itu tidak boleh dibaca
sebagai "grouping hampir terpecahkan".

**Ini kegagalan kedua yang independen dalam memulihkan grouping.** Jalur itu ditutup.

## Post-processing dikonfirmasi habis

Sapuan gabungan `lam_dec` × `lam_deep` × `T_deep` × `a_dec` × `a_rnd` × kuantil agregasi
(729 konfigurasi) menemukan optimum data penuh di 0,1758 — tapi holdout jujurnya
**+0,0014, menang 1/12**, dan parameter terpilih berhamburan di 12 belahan. Setelan
warisan notebook_6 sudah berada di optimum yang datar.

Median juga terkonfirmasi sebagai agregator yang benar: **semua** varian rata-rata
berbobot presisi kalah. Median tahan terhadap kontaminasi grup campuran (`depth = 10.0`
mencampur 1.633 record dari 21 gempa), rata-rata berbobot tidak.

## Set-transformer: gain nyata, tapi separuhnya jebakan lama

Ide: biarkan attention memutuskan record mana saling co-belong, alih-alih median grup buta.
Set dibentuk **hanya dari record yang tersedia di himpunan yang dinilai** (fold validasi
untuk OOF, test untuk test) supaya meniru test-time.

| | `lb_real` | dec | rnd | `bias_rnd` |
|---|---|---|---|---|
| nb8 | 0,1762 | 0,1437 | 0,2074 | +0,031 |
| + koreksi set, lam 0,30 | **0,1734** | 0,1453 | **0,2004** | **+0,044** |
| + koreksi set **di-demean** | 0,1741 | — | — | +0,031 |

Sisi bulat membaik −0,0070 — pertama kalinya ada yang menembus sisi itu. Tapi diagnostik
membongkar bahwa **separuh gain-nya adalah pergeseran rata-rata sisi depth-bulat** (mean
koreksi di MR = +0,042), bukan koreksi per-record. Itu persis prior katalog train (depth
bulat rata-rata M 5,45 vs desimal 5,19) yang membuat notebook_2 dan notebook_5 rugi di LB.

Versi di-demean per subset menahan **−0,0011 dengan `bias_rnd` tidak bergerak sama sekali**,
dan korelasi koreksi vs residual sejati di MR tetap **0,32** — jadi ada isi nyata di
baliknya. Versi itulah yang dipakai di `sudah_run/01_set_transformer.ipynb`.

**Aturan lama berlaku lagi:** `lb_real` mengukur data train; `bias_rnd` mengukur jarak ke
test. Kalau bertabrakan, yang kedua menang.

## Bug yang ditemukan sambil jalan

`kurt` punya **9 nilai non-finite** di train. LightGBM menelan NaN secara native, jadi ini
tidak pernah terlihat selama 8 notebook — tapi di jaringan saraf NaN merambat ke seluruh
batch dan membuat run pertama set-transformer menghasilkan NaN total. Fitur apa pun yang
dipakai model non-pohon harus lewat `nan_to_num` dulu.

## Status: yang tersisa cuma model deep

Sisi desimal sudah mentok (0,1437 vs oracle ~0,1488). Hampir seluruh headroom ada di sisi
depth-bulat (0,2074 vs oracle 0,1596), dan dua usaha independen memulihkan grouping gagal.
Lima notebook GPU disiapkan di **`belum_run/`** untuk dijalankan di Kaggle (sekarang di `sudah_run/`) — set-transformer
demean plus empat arsitektur deep baru (Inception multi-skala, TCN dilatasi, v3 diperlebar,
transformer). Masing-masing mencetak verdikt eksplisit terhadap target LB.

**Aritmatika targetnya keras dan sebaiknya dicatat:** LB 0,17 butuh `lb_real` 0,1618, yaitu
**dua kali lipat** terobosan CNN v3 (−0,0070). LB 0,16 butuh `lb_real` 0,1518 — **di bawah
batas oracle-grouping 0,1543**, jadi di luar jangkauan pendekatan ini. Target yang realistis
dari satu perbaikan berukuran sedang tetap **peringkat 1 di 0,1837**.

---

# Sesi Kaggle — 5 notebook GPU dijalankan, 1 berhasil

Detail lengkap di `sudah_run/README.md`. Ringkasnya:

**Empat arsitektur deep baru semuanya gagal** (Inception, TCN dilatasi, konvolusi dalam,
transformer). Gain holdout +0,0012 s/d +0,0016, menang 0–2/12. Sebabnya bukan lemah tapi
**redundan** — korelasinya 0,92–0,96 terhadap `cnn3_avg`. Digabung berempat pun tetap rugi
(gain +0,0012, menang 4/12). Keluarga "arsitektur CNN 1D baru atas waveform yang sama"
ditutup.

**Set-transformer berhasil**, tapi verdikt notebook Kaggle-nya harus dikoreksi dulu.

## notebook_9 — set-transformer dengan demean saat apply

| | `lb_real` | dec | rnd | `bias_rnd` | mean test bulat | sd |
|---|---|---|---|---|---|---|
| notebook_8 | 0,1762 | 0,1437 | 0,2074 | +0,031 | 5,259 | 0,396 |
| koreksi **mentah**, lam 0,50 | 0,1714 | 0,1450 | 0,1967 | **+0,059** ⚠ | 5,276 | 0,404 |
| **koreksi di-demean, lam 0,50** | **0,1718** | 0,1443 | **0,1982** | **+0,029** ✅ | **5,253** | 0,404 |

Notebook Kaggle memilih baris tengah dan melabeli `bias_rnd = +0,059` AMAN karena ambangnya
dipasang 0,08. **Ambang itu salah** — `notebook_5` rugi di LB pada +0,056. Demean di dalam
training tidak cukup: model tetap memulihkan prior katalog lewat fitur (mean koreksi di
subset depth-bulat dangkal +0,0556). Demean ulang pada koreksinya saat diterapkan menghapus
seluruh pergeseran itu dengan ongkos **0,0004 `lb_real`**.

Gain holdout jujur **−0,0042, menang 12/12**. `lam` stabil: 12 belahan memilih 0,4–0,6
(median 0,50), jadi bukan puncak sempit.

**Estimasi LB = 0,1718 + 0,0082 = 0,1800** (sd 0,0028). Peringkat 1 ada di 0,1837, jadi
ini melewatinya dengan margin **0,0037 ≈ 1,3 sd** — bukan kepastian, tapi bukan tipis juga.

Satu-satunya diagnostik yang memburuk: **sd prediksi sisi bulat 0,396 -> 0,404**. Kenaikan
sd pernah menyertai kerugian LB di nb5, tapi di sana lompatannya 0,424 -> 0,447 (+0,023)
sementara di sini +0,008, dan dua diagnostik lain (`bias_rnd`, mean) justru sedikit membaik.
Risikonya diterima, tapi dicatat supaya bisa dibaca balik kalau LB meleset.

## Koreksi metodologis untuk dipakai seterusnya

Demean **di dalam training** bukan jaminan. Kalau sebuah koreksi tidak boleh menggeser
rata-rata subset, **paksakan di titik penerapan**, bukan hanya di target training. Model
punya cukup fitur untuk memulihkan prior yang dibuang dari label.

---

# KEGAGALAN KETIGA (notebook_9, LB 0,1856): labelnya yang cacat, bukan bobotnya

`notebook_9` disubmit dan **LB-nya 0,1856** — lebih buruk dari `notebook_8` (0,1849).
Prediksinya 0,1800, jadi melesetnya **+0,0056**, miss terbesar sejauh ini. Peringkat kita
tetap dipegang `notebook_8.csv`.

| | `lb_real` | LB | offset |
|---|---|---|---|
| notebook_3 | 0,1945 | 0,1996 | +0,0051 |
| notebook_6 | 0,1845 | 0,1952 | +0,0107 |
| notebook_8 | 0,1762 | 0,1849 | +0,0087 |
| **notebook_9** | **0,1718** | **0,1856** | **+0,0138** |

Δ`lb_real` nb8→nb9 = **−0,0044**, ΔLB = **+0,0007**. Gain-nya tidak transfer sebagian —
ia **tidak transfer sama sekali**, malah sedikit terbalik.

> **Catatan ukuran efek.** Selisih LB 0,0007 itu sendiri hampir pasti derau: nb8 dan nb9
> berkorelasi 0,994 dan cuma 48 dari 2.300 record bergeser >0,1 (≈14 record di 30% LB
> publik). Yang harus dibaca bukan "nb9 lebih buruk", melainkan **"perbaikan −0,0044 di
> `lb_real` bernilai nol di LB"**. Itu tetap kesimpulan yang keras.

## Post-mortem: `experiments/exp_nb9_postmortem.py`

### Bukti 1 — seluruh gain hidup di sisi yang pseudo-event-nya PALSU

| sisi | pseudo-event | nb8 | nb9 | Δ |
|---|---|---|---|---|
| desimal | **event nyata** (98% murni) | 0,1437 | 0,1443 | **+0,0006** ❌ |
| bulat | **artefak katalog** (grup s/d 401 record) | 0,2074 | 0,1982 | −0,0092 |

Kalau set-transformer benar-benar belajar co-membership, ia mestinya menang **paling besar
di sisi desimal** — di sana co-membership itu nyata dan bisa diverifikasi. Yang terjadi
justru sebaliknya: di sisi desimal ia **rugi**. Seluruh gain-nya ada persis di satu-satunya
tempat yang labelnya tidak bisa dipercaya.

### Bukti 2 — yang dipelajarinya adalah "tarik ke median grup depth"

Korelasi koreksi terhadap dua hal:

| sisi | vs residual sejati | vs tarik-ke-median-grup |
|---|---|---|
| desimal | +0,480 | **+0,497** |
| bulat<100km | +0,375 | +0,323 |

Di sisi desimal ia lebih menyerupai operator tarik-ke-median daripada residual sejati. Dan
di test ia memang merapatkan grup: **sd dalam-grup sisi bulat 0,1727 → 0,1484 (−14%)**.

### Bukti 3 — kenapa merapatkan grup dibayar di train tapi tidak di test

Fraksi pasangan **berlabel sama** di dalam satu grup depth train, sisi bulat dangkal:

| depth | n | frac pasangan selabel |
|---|---|---|
| 10,0 | 1633 | 0,133 |
| 6,0 | 72 | 0,651 |
| 46,0 | 59 | 0,686 |
| **rata-rata berbobot record** | | **0,239** |

Di train, 24% pasangan di dalam grup depth **punya label identik** — merapatkan mereka
adalah gain gratis. Di LB, event ID-nya asli: grup `depth = 10.0` berisi puluhan gempa
berbeda, jadi operasi yang sama merata-ratakan gempa yang magnitudonya memang berbeda.

## Konsekuensi metodologis (ini yang paling penting dari sesi ini)

> **`lb_real` memperbaiki BOBOT metrik, bukan LABEL-nya.**
>
> `make_ev_real` memecah pseudo-event raksasa supaya bobot per-event realistis. Tapi `y`
> tetap **identik** untuk semua record yang berbagi (depth, magnitude). Jadi setiap metode
> yang mekanismenya **"buat prediksi di dalam satu grup depth lebih seragam"** tetap
> dibayar berlebihan oleh `lb_real` di sisi bulat, berapa pun benarnya pembobotannya.

Ini kali **ketiga** metrik evaluasinya sendiri yang jadi biang kegagalan LB:

| | yang cacat | korban |
|---|---|---|
| nb2, nb5 | bobot per-event (pseudo-event raksasa dapat bobot 1,0) | LB 0,2262 / 0,2063 |
| nb9 | **label per-event (record beda gempa berbagi `y`)** | LB 0,1856 |

### Aturan baru: validasi metode sisi-bulat di sisi DESIMAL dengan depth disembunyikan

Sisi desimal punya event nyata. Protokol ini sudah dipakai sekali di nb7 (untuk classifier
co-membership) dan terbukti membongkar kebenarannya:

1. Ambil hanya record depth-desimal (event asli, 98% murni).
2. Buang semua fitur turunan `depth`; bentuk "grup" dari pita kedalaman, bukan nilai depth.
3. Ukur gain metode di sana.

**Metode sisi-bulat apa pun yang tidak menang di uji ini harus ditolak,** berapa pun bagus
`lb_real`-nya. `notebook_9` gagal uji ini (+0,0006) dan tetap disubmit — itu kesalahannya.

### Ambang diagnostik lama tidak menangkap kegagalan ini

`bias_rnd` +0,029 (aman), mean subset bulat 5,253 (aman), sd 0,404 (naik +0,008, ditandai
AWAS). Ketiganya praktis lolos. Dibedah per sub-subset, sd **di dalam** subset bahkan turun
(bulat<100km 0,3499 → 0,3492; bulat≥100km 0,295 → 0,295) — kenaikan sd gabungan cuma
melebarnya jarak antar-mean sub-subset. Jadi ketiga diagnostik transfer **memang tidak
dirancang untuk menangkap mode kegagalan ini**, dan diagnostik keempat sekarang wajib:

4. **Gain di sisi desimal harus negatif juga.** Kalau sebuah perubahan hanya menang di sisi
   bulat dan rugi di sisi desimal, itu bendera merah — bukan "fokus di tempat yang tepat".

## Kalibrasi `lb_real` → LB, 4 titik

```
offset: +0,0051 / +0,0107 / +0,0087 / +0,0138   (mean +0,0096, sd 0,0036)
LB ~ 0,696 * lb_real + 0,0648        (regresi 4 titik, R2 0,92)
```

Offset-nya **tidak stabil** dan sd-nya naik dari 0,0028 ke 0,0036. Jangan pakai `lb_real`
untuk menjanjikan angka LB lagi — pakai untuk **memeringkat**, dan hanya setelah kandidatnya
lolos uji sisi-desimal di atas.

## Status peringkat setelah nb9

| # | Tim | Skor |
|---|---|---|
| 1 | Letdown | 0,1835 |
| 2 | Kingpul | 0,1837 |
| **3** | **Rizzz (kita)** | **0,1849** (nb8) |
| 4 | EspressoCampurRedbull | 0,1860 |

Turun ke peringkat 3 karena Letdown naik, bukan karena kita turun.

---

# notebook_10 — kandidat berikutnya: berhenti mendengarkan sisi bulat

Audit lanjutan sesudah nb9 (`experiments/exp_audit_dec.py`, `experiments/exp_fdsel.py`).
Pertanyaannya: **kalau set-transformer bisa tertipu label degenerate, apakah blend nb8
sendiri sudah tertipu dengan cara yang sama?**

## Ya. Model B punya mekanisme yang persis sama

Model B adalah satu-satunya keluarga yang memakai **fitur agregat grup**.

| kandidat | keluarga | desimal | bulat | rasio |
|---|---|---|---|---|
| swA_sqrt | A | 0,1565 | 0,2335 | 1,491 |
| **resA_dep** | A | **0,1515** | **0,2251** | 1,486 |
| resB_dep | B(grup) | 0,1669 | 0,2265 | **1,358** |
| resB_c30 | B(grup) | 0,1673 | 0,2292 | **1,370** |
| resB_p05 | B(grup) | 0,1669 | 0,2273 | **1,362** |
| cnnres | CNN | 0,1561 | 0,2418 | 1,549 |
| cnn3_avg | CNN | 0,1438 | 0,2319 | 1,613 |
| cnn3_dir | CNN | 0,1481 | 0,2370 | 1,600 |

Model B **kalah dari `resA_dep` di KEDUA sisi** dan tetap dapat bobot blend gabungan
**0,316** — murni dari dekorelasi. Rasionya paling rendah di tabel: kekuatannya paling
condong ke sisi yang labelnya palsu.

## Sapuan objektif seleksi

Objektif `FD_sel·dec + (1−FD_sel)·rnd`. Protokol tidak berubah (12 belahan, bobot final =
rata-rata lintas belahan). Skor yang dilaporkan tetap `lb_real` apa adanya.

| FD_sel | w_A | w_B | w_CNN | lb_real | dec | rnd | gain dec | menang dec | bias_rnd | sd_te | korel nb8 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **0,49 (nb8)** | 0,155 | **0,316** | 0,529 | **0,1762** | 0,1437 | 0,2074 | **+0,0009** | **3/12** | +0,031 | 0,396 | 1,000 |
| 0,60 | 0,178 | 0,265 | 0,557 | 0,1763 | 0,1427 | 0,2084 | +0,0001 | 7/12 | +0,031 | 0,396 | 1,000 |
| 0,70 | 0,191 | 0,215 | 0,595 | 0,1767 | 0,1420 | 0,2100 | −0,0005 | 9/12 | +0,029 | 0,395 | 0,999 |
| **0,80 ← dipakai** | **0,215** | **0,158** | **0,627** | 0,1773 | **0,1413** | 0,2118 | **−0,0010** | **9/12** | **+0,028** | **0,394** | **0,9986** |
| 0,90 | 0,163 | 0,119 | 0,718 | 0,1784 | 0,1405 | 0,2148 | −0,0016 | 10/12 | +0,028 | 0,396 | 0,997 |
| 1,00 | 0,172 | 0,092 | 0,736 | 0,1788 | 0,1403 | 0,2157 | −0,0015 | 9/12 | +0,027 | 0,396 | 0,996 |

**Blend `notebook_8` sendiri gagal uji sisi-desimal** — menang cuma 3/12.

## Kenapa FD_sel = 0,80

Satu-satunya baris yang membuat **keempat diagnostik bergerak benar sekaligus**:

| diagnostik | nb8 | nb10 | |
|---|---|---|---|
| bobot Model B | 0,316 | **0,157** | turun |
| gain sisi desimal | +0,0009 (3/12) | **−0,0010 (9/12)** | berbalik tanda |
| `bias_rnd` | +0,0314 | **+0,0276** | membaik |
| mean test bulat<100 | 5,2587 | **5,2628** | mendekati 5,272 |
| sd test sisi bulat | 0,3963 | **0,3942** | membaik |
| `lb_real` | 0,1762 | 0,1773 | **memburuk — disengaja** |

Bobot akhir: `cnn3_avg` 0,432, `cnn3_dir` 0,179, `resA_dep` 0,163, `resB_dep` 0,082,
`resB_c30` 0,055, `swA_sqrt` 0,052, `resB_p05` 0,021, `cnnres` 0,017.

## Ini taruhan, dan dinyatakan sebagai taruhan

**Mendukung:** nb9 membuktikan gain sisi bulat bisa bernilai nol di LB; Model B adalah
keluarga paling condong ke sisi bulat dan tidak menang di sisi mana pun sebagai model
tunggal; keempat diagnostik membaik.

**Melawan:** `lb_real` memburuk 0,0011, dan `lb_real` tetap satu-satunya angka yang pernah
berkorelasi dengan LB di empat submission.

**Rugi terbatas:** korelasi prediksi test vs nb8 = **0,9986** (delta mean +0,005, sd 0,018,
absmax 0,149). Kalau salah, ruginya seukuran selisih nb8↔nb9 (0,0007), bukan seukuran nb2
atau nb5.

**Nilai informasinya lebih besar dari nilai skornya.** LB membaik → sisi bulat `lb_real`
memang tidak bisa dipercaya, dan seluruh pipeline harus dipilih ulang di bawah `FD_sel`
tinggi. LB memburuk → kegagalan nb9 khusus milik set-transformer dan Model B boleh
dibiarkan. Kedua jawaban mengubah pekerjaan berikutnya.

**Tidak ada estimasi LB yang dicetak** — offset `lb_real` → LB terbukti tidak stabil di
nb9, dan mencetak angka palsu justru yang membuat nb9 disubmit.


---

# notebook_10 GAGAL (LB 0,1871) — dan kegagalannya MENGOREKSI kesimpulan nb9

`notebook_10` memangkas bobot Model B 0,32 → 0,16 dengan objektif seleksi condong ke sisi
desimal. **LB-nya 0,1871** — 0,0022 lebih buruk dari nb8, dan lebih buruk dari nb9. Ini
selisih yang jauh di atas ambang keterbacaan (~0,0005 untuk perbandingan berpasangan),
jadi jawabannya tegas.

## Yang dibuktikan: `lb_real` BAIK-BAIK SAJA. Saya yang terlalu jauh menggeneralisasi.

Kalibrasi dengan lima titik, dan pisahkan nb9:

| | `lb_real` | LB | offset |
|---|---|---|---|
| notebook_3 | 0,1945 | 0,1996 | +0,0051 |
| notebook_6 | 0,1845 | 0,1952 | +0,0107 |
| notebook_8 | 0,1762 | 0,1849 | +0,0087 |
| notebook_9 | 0,1718 | 0,1856 | **+0,0138 ← outlier tunggal** |
| notebook_10 | 0,1773 | 0,1871 | +0,0098 |

```
5 titik      : mean +0,0096, sd 0,0032
TANPA nb9    : mean +0,0086, sd 0,0025   <- jauh lebih rapat
```

Dan **arah**-nya:

| perubahan | Δ`lb_real` | ΔLB | arah |
|---|---|---|---|
| nb8 → nb9 | −0,0044 | +0,0007 | **SALAH** |
| nb8 → nb10 | +0,0011 | +0,0022 | **BENAR** |

`lb_real` memperkirakan arah nb10 dengan **benar** — ia memang bilang nb10 lebih buruk,
dan nb10 memang lebih buruk. Saya submit tetap, atas teori bahwa sisi bulat `lb_real`
tidak bisa dipercaya. **Teori itu salah.**

## Sintesis yang benar (gantikan kesimpulan sesi sebelumnya)

`nb9` **bukan** bukti bahwa sisi bulat `lb_real` busuk secara umum. Ia bukti bahwa **satu
kelas metode tertentu** — yang secara eksplisit menyeragamkan prediksi di dalam grup
depth — mendapat gain palsu di sana. Set-transformer melakukan itu terang-terangan (sd
dalam-grup test turun 14%).

Model B **tidak** melakukan itu. Ia memakai agregat grup sebagai **fitur**, dan agregat itu
ternyata membawa sinyal nyata yang transfer ke test. Bobot 0,32-nya sah. Memangkasnya
merugikan 0,0022 — kira-kira dua kali kerugian nb9.

| | mekanisme | vonis LB |
|---|---|---|
| set-transformer (nb9) | menyeragamkan prediksi dalam grup secara eksplisit | gain palsu, −0,0007 |
| Model B (fitur agregat grup) | agregat grup sebagai fitur input | **sinyal nyata, jangan diutak-atik** |

## RETRAKSI: diagnostik ke-4 tidak boleh jadi objektif seleksi

Sesi sebelumnya menetapkan aturan:

> ~~"Gain di sisi desimal harus negatif juga. Perubahan yang hanya menang di sisi bulat
> adalah bendera merah."~~

`notebook_10` dibangun untuk memaksimalkan persis kriteria itu — dan LB-nya memburuk
0,0022. **Aturan itu dicabut sebagai objektif seleksi.**

Kenapa ia salah: sisi desimal sudah **menyentuh oracle** (0,1437 vs oracle ~0,1488). Tidak
ada lagi yang bisa dipanen di sana. Mengoptimalkannya berarti mengorbankan sisi bulat —
51% metrik dan tempat **seluruh** headroom yang tersisa.

**Yang masih berlaku (versi sempit):** gain sisi desimal tetap berguna sebagai **layar
khusus** untuk metode yang mekanismenya menyeragamkan prediksi dalam grup — smoothing sisi
bulat, attention antar-record, pooling posterior, agregasi ulang. Untuk metode seperti itu,
gain yang hanya muncul di sisi bulat memang mencurigakan. **Untuk apa pun yang lain — dan
terutama untuk memilih bobot blend — abaikan.**

## Aturan yang menggantikannya

1. **`lb_real` tetap kriteria peringkat utama.** Empat dari lima titik konsisten dengan
   offset +0,0086 ± 0,0025.
2. **Jangan pernah submit kandidat yang `lb_real`-nya lebih buruk dari juara bertahan.**
   nb10 melanggar ini atas dasar teori, dan teorinya salah. Satu kegagalan (nb9) bukan
   dasar yang cukup untuk membatalkan metrik peringkat yang sudah benar 4 dari 5 kali.
3. **Bobot blend `notebook_8` sudah bagus — jangan diutak-atik lagi.** Dua perturbasi
   independen (nb9 menambah koreksi, nb10 menggeser bobot) dua-duanya merugi. Perlakukan
   `w_nb9.npy` + `FD_sel = 0,49` sebagai setelan baku.
4. **Yang tersisa cuma menambah kandidat yang lebih akurat per-record**, lalu blend dengan
   protokol standar tanpa modifikasi.

## Status peringkat

| # | Tim | Skor |
|---|---|---|
| 1 | Letdown | 0,1835 |
| 2 | Kingpul | 0,1837 |
| **3** | **Rizzz (kita)** | **0,1849** (`notebook_8`, tidak tergeser) |
| 4 | EspressoCampurRedbull | 0,1860 |

Tiga submission terakhir (nb9 0,1856, nb10 0,1871) tidak menggeser skor terbaik. Ongkos
dua submission itu adalah **dua fakta LB yang mahal dan tidak bisa didapat dengan cara
lain** — tapi tetap dua submission.


---

## Batch Kaggle ke-2 (22 Agu 2026): tidak menghasilkan submission

Tiga notebook dijalankan, tiga-tiganya gagal protokol. **Tidak ada `notebook_11.csv`;
`notebook_8.csv` tetap yang terbaik.** Verdikt lengkap di
[`../sudah_run/README.md`](../sudah_run/README.md).

| kandidat tambahan atas blend nb8 | `lb_real` | gain holdout | menang |
|---|---|---|---|
| `cnn9_aug` (augmentasi agresif) | 0,1760 | +0,00114 | 1/12 |
| `cnn10_ssl` (pra-latih SSL) | 0,1756 | +0,00122 | 2/12 |
| `cnn11_dist` (kepala distribusi) | 0,1762 | +0,00126 | 0/12 |
| ketiganya sekaligus | 0,1757 | +0,00103 | 2/12 |

Ketujuh kombinasi diuji; tidak ada yang gain-nya negatif. Diagnostik transfer semuanya
aman — yang gagal kriteria utamanya. Ini pola penolakan CNN+GRU yang sama: `lb_real`
mentah turun 0,0002-0,0006 di data tempat bobotnya dipilih, holdout jujurnya memburuk.

## Derau LB publik sudah diukur — angka yang mengubah cara membaca tabel di atas

Bootstrap 30% event (ukuran LB publik) atas OOF, 300 undian:

| yang diukur | sd |
|---|---|
| skor absolut di 30% data | **0,0098** |
| selisih dua submission mirip (corr 0,999) | **0,0008** |
| selisih dua submission beda (corr 0,888) | **0,0038** |

Artinya:

- **Jarak ke peringkat 1 (0,0014) ada di dalam derau** — itu selisih terhadap model tim
  lain, sd-nya orde 0,004. Kita efektif seri; peringkat akhir ditentukan 70% sisanya.
- **Kerugian `notebook_9` (+0,0007) juga di dalam derau** (~0,9 sd). Mekanisme yang
  ditemukan post-mortem tetap masuk akal, tapi bukti LB-nya lebih lemah dari yang
  tertulis di dokumen ini. `notebook_10` (+0,0022, ~2 sd) lebih meyakinkan.
- Offset `lb_real` → LB tidak pernah stabil karena penduganya sendiri ber-sd ~0,01.

**Jangan optimasi ke angka LB publik.** Pilih kandidat lewat gain holdout, menang n/12,
dan diagnostik transfer — kriteria yang sudah dipakai, dan yang dimenangkan `notebook_8`.


---

## Batch Kaggle ke-3 (22 Agu 2026, malam): tidak menghasilkan submission — tapi satu hasil BELUM TERBACA

**Tidak ada `notebook_11.csv`. `notebook_8.csv` (LB 0,1849) tetap yang terbaik.**
Verdikt lengkap di [`../sudah_run/README.md`](../sudah_run/README.md) bagian "Batch ke-3".

| notebook | ide | vonis |
|---|---|---|
| `10_cnn_fitur_gabung` | 196 fitur rekayasa masuk ke dalam CNN | **GAGAL** — `lb_real` 0,2167, menang 0/12, `bias_rnd` +0,115 |
| `09_tta_klip` | TTA + bobot loss record clipped | **GAGAL tipis** — UJI 2 gain +0,00029, menang 6/12 |

### Kenapa nb09 belum bisa dicatat sebagai gagal

Notebook membandingkan angka **post-processed** terhadap konstanta **mentah** (0,2091).
Konstanta yang benar 0,1898. Setelah dikoreksi, run Kaggle ternyata **0,0049 lebih buruk**
dari run lokal untuk resep yang identik — dan verdikt blend-nya mengadu kandidat Kaggle
melawan kandidat lokal, sehingga handicap itu terhitung sebagai kerugian ide.

| | `lb_real` (post) |
|---|---|
| `cnn3` lokal (3 seed) | 0,1898 |
| A K=1 Kaggle (resep identik) | **0,1947** ← gap +0,0049 |
| B K=8 (+TTA+klip) | 0,1904 |
| `cnn3_avg` lokal (6 seed) | 0,1888 |

Efek terisolasi yang tetap sah (internal Kaggle, gap meniadakan): TTA **+0,0011**, bobot
clipped **+0,0033**, keduanya **+0,0043**, MAE record clipped **+0,0093**.

Aritmetikanya: 0,1888 − 0,0043 ≈ **0,1845**. Itu sebabnya sumbu ini tidak boleh ditutup
berdasarkan verdikt yang terkontaminasi.

**Langkah penyelesaiannya tidak butuh GPU:**

```bash
python "Case 1/tools/serap_nb12.py" <folder-unduhan-dari-Kaggle>
```

Butuh `cnn12a_syms.npz` + `cnn12b_syms.npz` dari `/kaggle/working/`; keduanya **sudah
tertulis sebelum crash**. Ambil selagi sesi Kaggle-nya hidup.

### Aturan baru untuk `LEADERBOARD.md`

**Jangan catat sebuah ide sebagai GAGAL kalau gerbang kontrol run-nya menyala.** Notebook
09 mencetak "TIDAK COCOK — verdikt di bawah TIDAK bisa dipercaya" lalu tetap mencetak
verdiktnya, dan verdikt itu nyaris terlanjur diserap. Ide yang salah dicatat sebagai
tertutup adalah kerugian permanen: tidak ada yang membukanya lagi.

### nb09 TERJAWAB 23 Agu 2026 — seri, dan seri tidak cukup

`cnn12*_syms.npz` diselamatkan dari zip Kaggle, keempat kandidat direkonstruksi tanpa GPU
lewat `tools/serap_nb12.py`. **UJI 2** (pembanding dan kandidat sama-sama dari Kaggle,
sehingga gap lingkungan 0,0049 netral):

| kandidat | `lb_real` | jujur | gain | menang |
|---|---|---|---|---|
| `cnn12a_tta` (TTA saja) | 0,1762 | 0,1774 | +0,00126 | 0/12 |
| `cnn12b` (klip saja) | 0,1755 | 0,1766 | +0,00036 | 5/12 |
| **`cnn12b_tta`** | **0,1754** | 0,1766 | **+0,00029** | **6/12** |

Ambang: gain < 0 **dan** menang ≥ 7/12. Meleset di dua-duanya — tapi ini **kandidat
terdekat sepanjang case ini** (batch 2 memberi +0,0011…+0,0013 dengan 0-3/12). Bacaan
jujurnya seri, bukan kalah.

**Kompetisi ini cuma mengizinkan satu submission final, jadi tidak ada lindung nilai:
seri bukan alasan menggeser `notebook_8` (LB 0,1849).** TTA dan bobot record `is_clipped`
ditutup sebagai sumbu.

Yang tidak boleh diulang: gain single-model **+0,0043** menguap jadi **+0,0003** di blend,
karena 7 kandidat lain sudah menutupi varians yang sama. **Efek terisolasi harus
diterjemahkan ke tingkat tempat keputusan diambil sebelum dipakai menjanjikan apa pun** —
di sini selisih dua tingkat itu 15×.
