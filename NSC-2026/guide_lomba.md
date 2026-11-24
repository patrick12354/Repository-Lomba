# Panduan Lengkap — Penyisihan Data Science, National Statistics Challenge 2026

> Sumber:
> 1. *Petunjuk Teknis Penyisihan Cabang Lomba Data Science NSC 2026* (selanjutnya: **Juknis**)
> 2. *Petunjuk Pelaksanaan Umum Cabang Lomba Data Science NSC 2026* (selanjutnya: **Guidebook**)
>
> Keduanya terbitan Studio Statistika, Fakultas Sains, Teknologi, dan Matematika,
> Universitas Brawijaya.
> Dokumen ini merangkum seluruh isi kedua berkas, menerjemahkannya menjadi daftar tindakan, dan
> memetakan setiap butir penilaian ke artefak yang sudah kita punya. Bagian yang hanya ada di
> Guidebook ditandai **[G]**; yang hanya ada di Juknis ditandai **[J]**. Di mana keduanya berbeda,
> perbedaannya dituliskan apa adanya, tidak dipilih salah satu diam-diam.

---

## 0. Yang paling penting, dibaca lebih dulu

### 0.1 Bobot penilaian yang sebenarnya

Juknis memberi bobot bertingkat. Kalau dikalikan sampai persen total, gambarannya berubah drastis:

| komponen | bobot dalam juknis | **bobot terhadap nilai akhir** |
|---|---|---:|
| Laporan — **Pembahasan** | 60 % × 90 % | **54,0 %** |
| Model — **Skor Leaderboard Kaggle** | 40 % × 80 % | **32,0 %** |
| Model — **Notebook** | 40 % × 20 % | **8,0 %** |
| Laporan — Penulisan | 60 % × 5 % | 3,0 % |
| Laporan — Kesimpulan | 60 % × 5 % | 3,0 % |
| | | **100 %** |

**Bagian Pembahasan laporan bernilai 54 % — lebih dari 1,5 kali skor leaderboard.** Ini kesimpulan
paling penting dari seluruh juknis. Tim dengan skor Kaggle terbaik tetapi pembahasan tipis akan
kalah dari tim dengan skor sedikit lebih buruk tetapi pembahasan yang tajam.

Konsekuensi praktis untuk kita: skor leaderboard sudah selesai (2,82744). Seluruh sisa tenaga harus
masuk ke laporan, khususnya bagian pembahasan.

**Dan bobotnya belum berhenti di situ.** Guidebook §1.6 memperlihatkan laporan yang sama dinilai
lagi di Grand Final dengan bobot **35 dari 100**, dengan proporsi internal identik (Pembahasan
90 %). Jadi Pembahasan bernilai **54 % di penyisihan dan 31,5 % lagi di final**, atas dokumen yang
tidak bisa direvisi lagi setelah malam ini. Lihat §6.2.

### 0.2 Tenggat — dan satu kontradiksi antar-dokumen

**Tanggal operasional: 9 September 2026 pukul 23.59 WIB**, untuk **keduanya** — submission Kaggle
dan laporan ilmiah (.pdf). Notebook + model juga dikumpulkan lewat Google Form panitia.

Guidebook 1.4.2 menegaskan jam dan sanksinya:

> "Laporan ilmiah yang dikirimkan setelah batas akhir pengumpulan (lewat dari 9 September 2026
> pukul 23.59 WIB) dianggap tidak sah dan peserta akan **didiskualifikasi**."

> ⚠️ **Kontradiksi yang harus ditanyakan ke panitia, bukan ditebak.**
> Guidebook §1.5.1.3 butir 6 menulis laporan dikumpulkan **"dari 17 September 2026 hingga
> 19 September 2026"**, sementara Juknis 3f, Guidebook §1.4.2, Guidebook §1.5.1.1 butir 4, dan
> tabel timeline §1.3 semuanya menyebut **9 September 2026**. Empat sumber melawan satu, dan yang
> satu itu berada di sub-bagian yang paling mudah luput saat penyuntingan.
>
> **Sikap yang aman: perlakukan 9 September 2026 23.59 WIB sebagai tenggat sebenarnya**, karena
> mengumpulkan lebih awal tidak pernah menjadi pelanggaran sedangkan terlambat berarti
> diskualifikasi. Kalau ingin kepastian, tanyakan ke CP (§7.3) — tetapi jangan menunggu jawabannya.

**Catatan waktu:** hari ini **9 September 2026**. Tenggat jatuh malam ini.

### 0.3 Risiko diskualifikasi — satu pasal, dan kita sudah menutupnya

> "Peserta akan didiskualifikasi apabila ditemukan **ketidaksesuaian yang signifikan** antara skor
> prediksi pada model/notebook yang dikumpulkan dengan skor yang tertera di submission Kaggle."

Ini bukan risiko teoretis — banyak tim mengumpulkan notebook "versi bersih" yang menghasilkan
angka berbeda dari berkas yang benar-benar mereka submit. Penangkal kita ada di Bagian 11.5
notebook: ia menghitung **digest atas nilai prediksi yang dibulatkan ke enam desimal** dan
mem-`assert` kesamaannya dengan digest berkas yang benar-benar di-submit. Kalau ada perbedaan nyata
— model, fitur, seed, urutan lipatan, konfigurasi bendera — notebook gagal keras alih-alih
diam-diam menghasilkan angka lain.

```
digest nilai (6 desimal) : 1922ffe19fd196acdf9b95876d72a0d2
md5 berkas mentah        : 70666a36066bb25b03ee4dce1b7fedcd
skor publik terkait      : 2.82744
```

> **Mengapa digest nilai, bukan md5 berkas mentah?** Kami mencoba md5 mentah lebih dulu dan ia
> **gagal** pada eksekusi penuh pertama. Penyebabnya: **satu baris berbeda sebesar 3,55e-15**.
> Penyelesai jarang `spsolve` tidak reproducible sampai bit terakhir antar-jalankan karena
> penjadwalan BLAS. Perbedaan sebesar itu tidak dapat menggeser skor pada presisi mana pun yang
> dilaporkan Kaggle, tetapi cukup untuk mengubah satu baris teks CSV dan karenanya md5 berkas.
> Kontrak yang gagal karena derau presisi mesin adalah kontrak yang akan gagal di komputer panitia
> tanpa alasan. Digest pada enam desimal kebal terhadap derau itu dan tetap keras terhadap
> perbedaan nyata. md5 mentah tetap dicetak sebagai informasi.

---

## 1. Tema, kelayakan peserta, dan administrasi **[G]**

### 1.1 Tema

Tema besar NSC 2026:

> *The Voyager of Data: Navigating the Ocean of Statistics to Discover Treasures of Knowledge,
> Experience, and Achievement*

Tema cabang Data Science:

> *"Transforming Present Multivariate Insights to Shape the Future of Predictive Analytics"*

> **Ini bukan hiasan.** Tema cabang menyebut **multivariat** dan **predictive analytics** secara
> eksplisit. Pendahuluan laporan sebaiknya menyambungkan diri ke frasa itu dalam satu kalimat:
> kita memang memakai 25 kolom eksogen multivariat untuk meramalkan 734 titik ke depan. Juri
> membaca laporan sambil memegang tema; kalimat penghubung itu murah dan mudah lupa ditulis.

### 1.2 Kelayakan peserta

| butir | ketentuan |
|---|---|
| G-1 | Mahasiswa **aktif** jenjang **Diploma atau Sarjana** di PTN/PTS/PTK Indonesia, dibuktikan dengan **KTM** atau surat keterangan aktif |
| G-3 | Tim **2–3 orang**; boleh beda prodi/angkatan/jurusan/fakultas, **wajib satu instansi yang sama** |
| G-4 | Nama tim bebas, **tanpa unsur SARA, pornografi, umpatan, politik** |
| G-5 | Satu peserta hanya boleh mendaftar **satu cabang lomba** di NSC 2026 |
| G-6 | Hanya **satu laporan** per tim untuk penyisihan. Jika mengirim lebih dari sekali, **yang dinilai adalah kiriman pertama** |
| G-7 | Dari seluruh peserta penyisihan dipilih **3 tim terbaik** ke Grand Final |
| G-9 | Pemenang atas akumulasi nilai tertinggi. **Jika nilai akhir seri, penentu adalah waktu pengumpulan** |
| G-10 | Keputusan dewan juri mutlak |
| G-12 | Panitia berhak memanfaatkan karya untuk keperluan lomba, dengan mencantumkan identitas pemilik |
| G-14 | Semua peserta yang mengumpulkan karya berhak atas **e-sertifikat** |

> **Dua butir yang punya konsekuensi nyata bagi kita hari ini.**
>
> **G-6 — kiriman pertama yang dinilai.** Bukan yang terakhir, bukan yang terbaik. Jadi jangan
> mengunggah laporan "versi aman" lebih dulu dengan niat menyusulkan revisi. Unggah **sekali**,
> saat berkasnya sudah final.
>
> **G-9 — waktu pengumpulan memutus seri.** Lebih cepat mengumpulkan berarti lebih diuntungkan saat
> nilai akhir seri. Ini alasan tambahan untuk tidak mengejar pukul 23.58 WIB.

### 1.3 Pendaftaran dan biaya (arsip)

Ditulis di sini untuk kelengkapan; periodenya sudah lewat.

| gelombang | periode | biaya per tim |
|---|---|---|
| Early Bird | 18 Juli – 1 Agustus 2026 | Rp90.000 |
| Gelombang I | 2 – 15 Agustus 2026 | Rp105.000 |
| Gelombang II | 16 – 21 Agustus 2026 | Rp120.000 |

Berkas yang diunggah saat pendaftaran: pas foto formal 3×4 latar polos (bukan swafoto, tanpa
atribut instansi, maks. 1 MB), pindaian KTM/KTMS/bukti mahasiswa aktif (maks. 1 MB), bukti unggah
twibbon ber-caption dengan tag **@nscub2026** (maks. 1 MB), dan bukti pembayaran (maks. 1 MB).
Konfirmasi berisi **nomor tim** dikirim panitia dari **nscub26@gmail.com**.

> **Nomor tim itu dipakai di nama berkas laporan** (`{Nomor Tim}_{Nama Tim}_Data Science.pdf`).
> Cari e-mail dari nscub26@gmail.com sekarang, bukan nanti — formatnya `NSC26-DS0XX`.

---

## 2. Timeline resmi **[G §1.3]**

| # | kegiatan | pelaksanaan |
|---:|---|---|
| 1 | Registrasi & verifikasi pembayaran Early Bird | 18 Juli – 1 Agustus 2026 |
| 2 | Registrasi & verifikasi pembayaran Gelombang I | 2 – 15 Agustus 2026 |
| 3 | Registrasi & verifikasi pembayaran Gelombang II | 16 – 21 Agustus 2026 |
| 4 | Technical Meeting Penyisihan | 22 Agustus 2026 |
| 5 | **Penyisihan dan pengumpulan laporan Data Science** | **24 Agustus – 9 September 2026** |
| 6 | Pengumuman peserta Grand Final | 5 Oktober 2026, pukul 16.00 WIB |
| 7 | Registrasi ulang Grand Final | 5 – 7 Oktober 2026 |
| 8 | Technical Meeting Grand Final | 10 Oktober 2026 |
| 9 | Pengumpulan Power Point | 11 – 17 Oktober 2026 |
| 10 | Grand Final dan Closing Ceremony | 25 Oktober 2026 |

Pengumuman finalis disiarkan lewat grup peserta, Instagram **@nscub2026**, dan
<https://nsc.mipa.ub.ac.id/>.

---

## 3. Ketentuan umum penyisihan

| butir | isi | status kita |
|---|---|---|
| 1a | Tim terdiri atas **2–3 orang** | — |
| 1b | Penyisihan online lewat **Kaggle Competition**, disertai **laporan ilmiah** yang mendukung metode | ✅ Kaggle selesai · ⬜ laporan |
| 1c | Narasi dan dataset diunduh lewat Kaggle | ✅ |
| 1d | **Border template** laporan diunduh dari <https://nsc.mipa.ub.ac.id/> | ⬜ **wajib dicek** |
| 1e | **Template laporan IEEE** dari <https://www.ieee.org/conferences/publishing/templates> | ⬜ |
| 1f | Tenggat **9 September 2026** untuk prediksi Kaggle **dan** laporan | ⬜ |

| **G** | Selain narasi dan dataset, website resmi juga menyediakan **template Cover**, **template Lembar Pernyataan Orisinalitas**, dan **template Lembar Jawaban** | ⬜ **wajib dicek** |
| **G** | Berkas-berkas itu berada di menu **Event – Data Science – Penyisihan** dan **dilindungi password** yang diberikan panitia | ⬜ |

> **Catatan tentang 1d.** "Border template" adalah bingkai/kop resmi NSC yang harus dipasang pada
> laporan, terpisah dari template IEEE. Dua berkas berbeda, keduanya wajib. Unduh dari website
> resmi NSC, jangan berasumsi template IEEE polos sudah cukup.

> ⚠️ **Temuan baru dari Guidebook §1.5.1.1 butir 3 — tiga berkas yang tidak disebut Juknis sama
> sekali.** Juknis hanya menyebut border template dan template IEEE. Guidebook menambahkan
> **template Cover**, **template Lembar Pernyataan Orisinalitas**, dan **template Lembar Jawaban**,
> semuanya di menu *Event – Data Science – Penyisihan* dan terkunci password panitia.
>
> Ini persis jenis butir yang memicu sanksi "pengurangan nilai karena tidak sesuai ketentuan"
> (§7.1): tidak menggugurkan, tetapi memotong nilai Penulisan dan mungkin lebih. **Lembar
> Pernyataan Orisinalitas khususnya biasanya wajib ditandatangani seluruh anggota** dan dilampirkan
> bersama laporan. Buka halaman itu sekarang dan pastikan ketiganya sudah terpasang — kalau
> passwordnya hilang, tanyakan ke CP (§7.3) hari ini juga.
>
> Perhatikan juga bahwa Guidebook menyebut **"template Lembar Jawaban"** untuk cabang Data Science.
> Frasa itu lebih lazim dipakai untuk cabang lomba lain; kalau setelah membuka halaman ternyata
> tidak ada berkas semacam itu untuk Data Science, catat saja bahwa laporan IEEE-lah lembar
> jawabannya, dan jangan mengarang format sendiri.

---

## 4. Model dan notebook

### 4.1 Aturan dan status

| butir | aturan | status |
|---|---|---|
| 2a | Bebas memakai **tools, library, algoritma, dan software apa pun** | ✅ LightGBM, CatBoost, scikit-learn, SciPy |
| 2b | **Dilarang** memakai data di luar dataset panitia | ✅ hanya `train.csv`, `test.csv`, `sample_submission.csv` |
| 2c | Submission lewat Kaggle; **wajib bergabung ke tim Kaggle** sesuai pendaftaran; **satu tim Kaggle saja**; **nama tim harus sama** dengan saat pendaftaran | ⬜ **verifikasi ulang** |
| 2d | Maksimum **3 submission per hari** | ✅ |
| 2e | Unggah **.ipynb** + **model** (.pkl/.h5/.pt/.tf/format relevan) lewat Google Form | ✅ notebook + `model_nsc26_air_humidity.pkl` |
| 2f | Penjelasan dataset, studi kasus, metrik evaluasi ada di dokumen penjelasan dataset terpisah | ⬜ baca ulang sebelum menulis laporan |

> **Butir 2c layak dicek dua kali.** Nama tim di Kaggle harus identik dengan nama saat pendaftaran,
> dan seluruh anggota harus sudah tergabung di tim Kaggle yang sama. Kesalahan di sini menggugurkan
> submission tanpa memandang skor.

### 4.2 Lima syarat wajib notebook, dan bagaimana kita memenuhinya

Juknis 2.e memerinci lima syarat. Ini pemetaannya ke `NSC26_DataScience_AirHumidity.ipynb`:

| syarat juknis | di mana dipenuhi |
|---|---|
| **1. Mendokumentasikan seluruh tahapan** — akuisisi, eksplorasi, pra-pemrosesan, pemodelan, evaluasi, serta penjelasan/visualisasi yang informatif | Bagian 2 (akuisisi) · 3–6 (eksplorasi) · 7 (pra-pemrosesan) · 8–10 (fitur & pemodelan) · 11–12 (evaluasi). 13 gambar, seluruhnya dihasilkan notebook sendiri |
| **2. Menyertakan seed untuk setiap proses acak, dan reproducible tanpa error** | Bagian 1 mendaftarkan seluruh sumber keacakan di satu sel: `SEEDS_OOF=(0,1,2)`, `SEEDS_FIT=(0,1,2,3,4)`, `INC_SEED=20260905` × 5. Tidak ada RNG global yang dipakai jalur kode mana pun. Notebook sudah dieksekusi penuh dari atas ke bawah tanpa galat (8,8 menit, 0 error, 13 gambar) |
| **3. Pretrained model wajib dijelaskan rinci** | **Tidak ada pretrained model.** Dinyatakan eksplisit di Bagian 15 |
| **4. Mencantumkan semua sumber**: referensi model, library, kode eksternal, pustaka ilmiah | Bagian 15 — 16 rujukan gaya IEEE (7 perangkat lunak, 9 metode/fisis), plus pernyataan eksplisit "kode eksternal: tidak ada" |
| **5. Skor notebook harus sesuai skor Kaggle** | Bagian 11.5 — `assert` atas digest nilai prediksi (6 desimal) terhadap berkas yang di-submit; lihat §0.3 |

### 4.3 Isi notebook yang sudah dibangun

```
NSC26_DataScience_AirHumidity.ipynb   — 74 sel (39 markdown, 35 kode), runtime terukur 8,8 menit
├── 1  Kontrak reproduksibilitas, seed, pemuatan data
├── 2  Akuisisi & anatomi dataset
├── 3  Eksplorasi: struktur target, audit korupsi data, siklus diurnal
├── 4  Kerangka fisis: RH = 100·e/es(T), kurva oracle, proksi titik embun
├── 5  Rekayasa balik blok agronomi
├── 6  Pergeseran distribusi latih → uji (audit dukungan)
├── 7  Pra-pemrosesan: Hampel + interpolasi waktu
├── 8  Rekayasa fitur (5 blok) + blok increment
├── 9  Desain validasi (titik-asal bergulir)
├── 10 Pemodelan: 6 anggota, blending, de-bias level, bukti buta-target
├── 11 Pelatihan, submission, verifikasi kesesuaian, artefak model
├── 12 Anatomi galat + papan peringkat sebagai instrumen ukur
├── 13 Katalog kegagalan
├── 14 Keterbatasan & kesimpulan
└── 15 Referensi
```

**Berkas keluaran notebook:**
- `submission_nsc26_air_humidity.csv` — prediksi identik sampai enam desimal dengan berkas ber-skor 2,82744
- `model_nsc26_air_humidity.pkl` — anggota terpasang, bobot blend, koreksi bias, model increment

---

## 5. Laporan ilmiah

### 5.1 Aturan format

| butir | aturan |
|---|---|
| 3a | Struktur wajib memuat: **latar belakang · akuisisi dan eksplorasi data · metode analisis · pra-pemrosesan · pemodelan · evaluasi akhir** |
| 3b | Template **IEEE**, kertas **A4**, **maksimal 10 halaman termasuk daftar pustaka** |
| 3c | Seluruh referensi wajib dicantumkan dengan **IEEE Style** (<https://s.id/IEEEReference>) |
| 3d | Lampiran boleh ditambahkan (dokumentasi, screenshot, data, dll.) |
| 3e | Format **.pdf**, nama berkas `{Nomor Tim}_{Nama Tim}_{Data Science}` — contoh: `NSC26-DS00X_Bayesian_Data Science` |
| 3f | Dikumpulkan lewat Google Form di <https://nsc.mipa.ub.ac.id/>, tenggat 9 September 2026 |
| **G** | Jalur unggah persisnya: menu **Event – Data Science – Penyisihan** |
| **G** | Hanya **satu laporan** per tim; jika mengirim lebih dari sekali, **yang dinilai kiriman pertama** |
| **G** | Konfirmasi keberhasilan unggah dikirim dari **nscub26@gmail.com**; jika 3 hari tidak ada, hubungi CP |

> **Perbedaan redaksi soal batas 10 halaman.** Juknis 3b menulis batas itu melekat pada
> **format/template A4**: "batas maksimal laporan adalah 10 halaman yang sudah memuat daftar
> pustaka". Guidebook §1.5.1.3 justru menempelkan angka itu pada butir **daftar pustaka**:
> "...daftar pustaka ditulis dengan IEEE Style ... dengan maksimal 10 halaman". Pembacaan yang
> masuk akal dan aman sama untuk keduanya: **seluruh laporan maksimal 10 halaman, daftar pustaka
> ikut dihitung.** Itu pembacaan yang lebih ketat, jadi memenuhinya otomatis memenuhi pembacaan
> mana pun. Guidebook juga tidak mengulang kata "A4" — pakai A4 sesuai Juknis.

> **10 halaman termasuk daftar pustaka** itu ketat. Template IEEE dua kolom memuat sekitar
> 900–1 000 kata per halaman. Dengan gambar dan tabel, anggaran realistis adalah **6 000–6 500
> kata plus 8–10 gambar/tabel**. Rencanakan pemangkasan sejak awal, jangan menulis 15 halaman lalu
> memotong.

### 5.2 Kerangka laporan yang disarankan, dipetakan ke notebook

Kerangka ini mengikuti urutan wajib juknis 3a, dan setiap bagiannya sudah punya bahan jadi di
notebook. Angka halaman adalah anggaran, bukan aturan.

| § | Judul | Hal. | Isi inti | Sumber di notebook |
|---|---|---:|---|---|
| I | **Pendahuluan / Latar Belakang** | 0,75 | Mengapa kelembapan udara penting untuk pertanian presisi (VPD, penyakit jamur, penjadwalan irigasi); rumusan masalah: ramalkan 734 titik setengah-jaman untuk 15 hari ke depan; kontribusi utama tulisan (3 poin) | Ringkasan eksekutif |
| II | **Akuisisi dan Eksplorasi Data** | 1,5 | Anatomi dataset (25 eksogen, 2 933 latih / 734 uji); **bentuk pemisahan latih-uji dan mengapa itu menentukan segalanya**; audit nilai hilang; **audit korupsi**: target bersih (rasio 1,20) vs prediktor terlonjaki (5,75 dan 6,86); siklus diurnal | Bagian 2, 3 |
| III | **Metode Analisis** | 2,0 | **Kerangka fisis** RH = 100·e/es(T) dan implikasinya; **kurva oracle** — pengetahuan tentang `e` pada resolusi berapa memberi RMSE berapa; proksi titik embun bebas-parameter (r = 0,908); **rekayasa balik blok agronomi**; audit pergeseran distribusi; **desain validasi titik-asal bergulir** dan mengapa lipatan acak berbohong | Bagian 4, 5, 6, 9 |
| IV | **Pra-pemrosesan** | 0,75 | Penapis Hampel dan pembenarannya lewat statistik residu LOO; interpolasi berbasis waktu (bukan baris) karena lompatan 7 jam; kolom kumulatif → laju; keputusan membuang blok tanah dan bukti dukungannya | Bagian 6, 7 |
| V | **Pemodelan** | 2,25 | Enam anggota dan **alasan masing-masing ada** (terutama `cat` yang sengaja salah-spesifikasi demi dekorelasi, dan `ridge_e` di ruang tekanan uap); NNLS + lantai penyusutan; bobot per pita waktu-hari + kontrol konditioner acak; koreksi bias diurnal; **de-bias level per anggota**; **rekonsiliasi increment** dengan rumusnya dan tiga angka galat perubahan | Bagian 8.2, 10 |
| VI | **Evaluasi dan Pembahasan** | 2,0 | Hasil validasi silang per lipatan sebelum/sesudah rekonsiliasi; skor leaderboard bertahap; **anatomi galat** (39 % offset harian, kemiringan 1,147 vs 1,054); **papan peringkat sebagai instrumen** — dua probe dan dua besaran yang diselesaikannya; **katalog kegagalan** | Bagian 11, 12, 13 |
| VII | **Kesimpulan** | 0,4 | Empat kalimat: reformulasi fisis, deret waktu vs baris bebas, cacat kalibrasi yang tak terlihat, merancang submission agar terukur | Bagian 14.2 |
| — | **Daftar Pustaka** | 0,35 | 12–16 rujukan IEEE Style | Bagian 15 |

**Total ± 10 halaman.**

### 5.3 Di mana nilai Pembahasan (54 %) sebenarnya diperoleh

Bagian pembahasan biasanya dinilai atas **kedalaman penalaran**, bukan panjang. Enam hal berikut
adalah yang paling membedakan tulisan kita dari tulisan yang sekadar melaporkan pipeline:

1. **Reformulasi fisis yang dibayar dengan angka.** Jangan hanya menulis "kami memakai fitur
   fisis". Tunjukkan kurva oracle: mengetahui `e` sebagai satu rerata harian memberi RMSE 8,37;
   pada 6,5 jam memberi 3,00; model kita 2,827 berada di antara oracle 2,5 jam dan 6,5 jam. Itu
   mengubah klaim kualitatif menjadi pengukuran.
2. **Bukti bahwa target bersih dan prediktor kotor.** Statistik residu LOO memisahkan keduanya
   secara tegas, dan simpulannya nontrivial: tidak ada lantai derau label, sehingga nilai
   pra-pemrosesan seluruhnya ada pada rekonstruksi sinyal masukan.
3. **Rekayasa balik blok agronomi.** Dua rekonstruksi independen suhu minimum harian sepakat sampai
   sd 0,047 °C dan keduanya berbeda 0,43 °C dari minimum sensor — jadi 0,47 itu adalah derau sensor
   pada fitur fisis terkuat kita. Ini jenis temuan yang jarang muncul di laporan lomba.
4. **Rekonsiliasi increment sebagai satu-satunya komponen yang memperlakukan jendela uji sebagai
   deret waktu.** Tuliskan rumusnya, dan tuliskan tiga angka yang menjelaskan mengapa ia bekerja:
   perubahan 30 menit punya sinyal 3,54, level stack sendiri sudah menyiratkannya dengan galat
   2,02, dan model perubahan khusus mencapai 1,76.
5. **Cacat kalibrasi yang tidak terlihat instrumen mana pun.** Bias level −2,9 %RH pada satu
   anggota, bias di dalam sampel −0,006, dan alasan strukturalnya: NNLS non-negatif ternormalisasi
   tidak punya intersep, dan koreksi bias diurnal sengaja membuang intersepnya. Ini contoh bagus
   "mengapa sebuah kesalahan bisa bertahan lama".
6. **Papan peringkat sebagai instrumen ukur.** Merancang dua submission sebagai perturbasi murni
   pada satu momen distribusi, lalu membalik `ΔMSE = 2·d̄·ē + d̄²` untuk memperoleh galat level
   jendela uji (−0,4145 %RH) dan kemiringan kalibrasinya (1,0050). Ini metodologi, dan ia menutup
   dua keluarga koreksi secara kuantitatif.

**Ditambah satu hal yang sering diabaikan tim lain: laporkan kegagalan.** Bagian 13 notebook memuat
katalog arah yang ditolak beserta alasan terukurnya — analog/tetangga terdekat, prior kelengkungan,
horizon increment yang lebih panjang, ekspansi level harian, jaring saraf, penyapuan
hiperparameter. Menunjukkan *mengapa* sesuatu tidak bekerja adalah bukti pemahaman yang lebih kuat
daripada menunjukkan sesuatu bekerja.

### 5.4 Gambar dan tabel yang paling layak masuk laporan

Anggaran realistis 8–10 buah. Prioritas, terurut:

| # | Gambar/tabel | Mengapa masuk |
|---|---|---|
| 1 | Deret target + jendela uji terarsir, dengan suhu mentah di bawahnya | Memperkenalkan tugas **dan** memperlihatkan lonjakan dalam satu tarikan napas |
| 2 | Histogram residu LOO: target vs suhu vs tekanan (skala log) | Bukti visual "target bersih, prediktor kotor" |
| 3 | **Kurva oracle** RMSE vs resolusi pengetahuan `e` | Gambar paling informatif di seluruh analisis |
| 4 | Dekomposisi tiga panel: RH, `es(T)`, `e` | Menjelaskan reformulasi fisis dalam satu pandangan |
| 5 | Audit dukungan per kolom (bar horizontal) | Membenarkan pembuangan blok tanah dan penanganan anggota linear |
| 6 | Diagram titik-asal bergulir | Menjelaskan desain validasi lebih cepat daripada paragraf |
| 7 | RMSE per lipatan sebelum/sesudah rekonsiliasi increment | Bukti komponen terpenting |
| 8 | **Bias bertanda per anggota** (bar) | Temuan de-bias level, satu gambar |
| 9 | Anatomi galat: bagian SSE per pita 3 jam + kurva kalibrasi | Menopang seluruh pembahasan Bagian VI |
| 10 | Tabel tangga skor leaderboard | Menutup argumen "apa yang benar-benar memindahkan skor" |

Kalau harus memangkas, buang #4 dan #6 lebih dulu (bisa dijelaskan dengan teks), pertahankan
#3, #8, dan #9.

### 5.5 Gaya penulisan (bobot 3 %, tetapi mudah diamankan)

- Judul kolom IEEE dua kolom, 10 pt, gaya `IEEEtran`.
- Abstrak 150–200 kata: masalah, pendekatan, hasil kuantitatif, satu temuan yang mengejutkan.
- Kata kunci 4–6 buah: *air humidity forecasting, gradient boosting, forecast reconciliation,
  vapour pressure, model calibration, time-series cross-validation*.
- Setiap gambar dan tabel **harus dirujuk di badan teks** ("Gbr. 3 menunjukkan…"). Gambar yang
  tidak dirujuk adalah kesalahan format yang sering memotong nilai penulisan.
- Persamaan diberi nomor dan dirujuk sebagai (1), (2), …
- Angka desimal konsisten (koma untuk Indonesia, titik untuk Inggris — pilih satu bahasa dan
  patuhi).
- Sitasi IEEE: `[1]`, `[2]`, berurutan sesuai kemunculan pertama di teks, bukan alfabetis.

---

## 6. Babak Grand Final **[G]**

Relevan hanya jika kita lolos (3 besar, diumumkan 5 Oktober 2026), tetapi dua hal di dalamnya
memengaruhi keputusan hari ini — lihat catatan di akhir bagian.

### 6.1 Ketentuan pelaksanaan

| butir | ketentuan |
|---|---|
| Bentuk | **Luring** di Universitas Brawijaya, 25 Oktober 2026. Kehadiran **tidak dapat diwakilkan** |
| Registrasi ulang | 5 – 7 Oktober 2026 |
| Technical Meeting | 10 Oktober 2026 |
| Bahan presentasi | `.pdf`, `.pptx`, atau tautan, lewat Google Form: menu **Event – Data Science – Final** |
| Tenggat bahan | 11 – 17 Oktober 2026 |
| Isi presentasi | Analisis dan pemodelan yang dikerjakan **pada babak penyisihan** |
| Durasi | **Presentasi 15 menit**, dilanjutkan **tanya jawab 24 menit** |
| Urutan tampil | Diundi saat Technical Meeting |
| Jeda antar-tim | 5 menit |
| Tanya jawab | Juri memberi **minimal 1 pertanyaan** per tim; tim menjawab setelah dipersilakan moderator |
| Interaksi | Dilarang berinteraksi personal dengan juri selama agenda |
| Busana | Atasan **batik** bebas sopan, bawahan **kain hitam**, **tanpa atribut/almamater instansi** |
| Keterlambatan | Hubungi **Liaison Officer (LO)** masing-masing |
| Closing Ceremony | Wajib hadir, **minimal 15 menit sebelum mulai** |

### 6.2 Bobot penilaian Grand Final

| komponen | bobot | rincian | bobot terhadap nilai final |
|---|---:|---|---:|
| **Laporan Ilmiah** | 35 | Penulisan 5 % · **Pembahasan 90 %** · Kesimpulan 5 % | Pembahasan **31,5** |
| **Presentasi** | 40 | Keruntutan & kesesuaian PPT 25 % · **Penguasaan materi 37,5 %** · Efisiensi waktu 25 % · Lafal, intonasi, ekspresi, dan sikap 12,5 % | Penguasaan materi **15,0** |
| **Tanya Jawab** | 25 | Kecepatan pemahaman pertanyaan 40 % · **Kesesuaian & konsistensi jawaban 60 %** | Konsistensi jawaban **15,0** |
| **TOTAL** | **100** | | |

> **Dua implikasi yang berlaku mundur ke laporan penyisihan.**
>
> **1. Laporan penyisihan dinilai dua kali.** Bobotnya 60 di penyisihan dan **35 lagi di Grand
> Final** — atas dokumen yang sama, karena tidak ada kesempatan merevisi laporan setelah 9
> September. Setiap paragraf yang ditulis malam ini masih dinilai enam minggu kemudian.
>
> **2. Tanya jawab 24 menit itu lebih panjang daripada presentasinya, dan bernilai 25.** Sesi
> selama itu akan menembus jauh melewati lapisan permukaan: mengapa `cat` sengaja
> salah-spesifikasi, mengapa validasi titik-asal bergulir dan bukan lipatan acak, dari mana angka
> −0,4145 %RH berasal. Ini alasan kuat untuk **tidak** menuliskan klaim di laporan yang tidak bisa
> kita pertahankan selama 24 menit — sekaligus alasan kuat untuk memasukkan katalog kegagalan
> (§5.3, butir terakhir), karena pertanyaan "apa yang sudah dicoba dan gagal" hampir pasti muncul
> dan jawabannya sudah tertulis.

---

## 7. Sanksi, penghargaan, dan kontak **[G]**

### 7.1 Sanksi

| pelanggaran | sanksi |
|---|---|
| Model atau laporan **tidak sesuai ketentuan** | **Pengurangan nilai** |
| **Kecurangan atau plagiasi** | **Diskualifikasi** |
| Laporan terkirim lewat 9 September 2026 pukul 23.59 WIB | Dianggap tidak sah → **diskualifikasi** |
| Ketidaksesuaian signifikan skor notebook vs skor Kaggle | **Diskualifikasi** |
| Peserta terdiskualifikasi | Tidak berhak atas e-sertifikat maupun gelar juara |

> Perhatikan gradasinya: **format yang meleset memotong nilai, bukan menggugurkan**; yang
> menggugurkan adalah kecurangan, keterlambatan, dan ketidaksesuaian skor. Ketiganya sudah
> tertutup di pihak kita (§0.3, §8.4) — tinggal jangan terlambat.

### 7.2 Penghargaan

| juara | hadiah |
|---|---|
| 1 | Piala + Sertifikat + **Rp2.500.000** |
| 2 | Piala + Sertifikat + **Rp1.750.000** |
| 3 | Piala + Sertifikat + **Rp1.250.000** |

Seluruh peserta yang mengumpulkan karya memperoleh **e-sertifikat**.

### 7.3 Kontak

| kanal | keterangan |
|---|---|
| CP | **Naylil — 085190962007** (WhatsApp) |
| E-mail panitia | **nscub26@gmail.com** — pengirim konfirmasi pendaftaran dan pengumpulan |
| E-mail sekretariat | studiostatistika@ub.ac.id |
| Website | <https://nsc.mipa.ub.ac.id/> |
| Instagram | **@nscub2026** |

> Konfirmasi keberhasilan unggah dikirim panitia lewat e-mail. **Kalau dalam tiga hari tidak ada
> e-mail konfirmasi, hubungi CP.** Jangan menganggap "form tidak menampilkan galat" sama dengan
> "karya diterima".

---

## 8. Daftar periksa pengumpulan

### 8.1 Kaggle
- [ ] Nama tim di Kaggle **identik** dengan nama saat pendaftaran
- [ ] Seluruh anggota sudah tergabung di **satu** tim Kaggle
- [ ] Berkas `submission_nsc26_air_humidity.csv` sudah ter-submit dan terpilih sebagai entri final
- [ ] Skor publik terkonfirmasi: **2,82744**

### 8.2 Google Form (notebook + model)
- [ ] `NSC26_DataScience_AirHumidity.ipynb` — sudah dieksekusi penuh, **output tersimpan di dalam berkas**
- [ ] `model_nsc26_air_humidity.pkl`
- [ ] Notebook memuat seed, referensi, dan pernyataan "tanpa data eksternal / tanpa pretrained model"
- [ ] Sel verifikasi Bagian 11.5 lolos (digest `1922ffe19fd196acdf9b95876d72a0d2`)

### 8.3 Laporan
- [ ] Template **IEEE A4** dipakai
- [ ] **Border template NSC** dari website resmi dipasang
- [ ] **Template Cover NSC** dipakai **[G]**
- [ ] **Lembar Pernyataan Orisinalitas** diisi dan ditandatangani seluruh anggota **[G]**
- [ ] **Template Lembar Jawaban** dicek keberadaannya di halaman penyisihan **[G]**
- [ ] **Maksimal 10 halaman**, termasuk daftar pustaka
- [ ] Struktur memuat keenam bagian wajib juknis 3a
- [ ] Daftar pustaka **IEEE Style**, berurutan sesuai kemunculan
- [ ] Satu kalimat di Pendahuluan yang menautkan karya ke tema cabang **[G]**
- [ ] Nama berkas: `{Nomor Tim}_{Nama Tim}_{Data Science}.pdf` — **nomor tim dari e-mail nscub26@gmail.com**
- [ ] Dikumpulkan lewat Google Form: menu **Event – Data Science – Penyisihan**
- [ ] **Diunggah sekali saja** — kiriman pertama yang dinilai **[G]**
- [ ] Terkirim **sebelum 9 September 2026 pukul 23.59 WIB**
- [ ] E-mail konfirmasi dari **nscub26@gmail.com** diterima (kalau 3 hari nihil → hubungi CP)

### 8.4 Hal yang menggugurkan
- [ ] Tidak ada data eksternal — **terverifikasi**, notebook hanya membaca tiga berkas resmi
- [ ] Skor notebook = skor Kaggle — **terverifikasi lewat digest nilai prediksi**
- [ ] Satu tim Kaggle saja
- [ ] Tidak melebihi 3 submission per hari
- [ ] Terkirim sebelum 9 September 2026 23.59 WIB — **lewat batas = diskualifikasi** **[G]**
- [ ] Tidak ada plagiasi; seluruh sumber tercantum di laporan dan notebook **[G]**

---

## 9. Angka-angka kunci untuk dikutip di laporan

Semuanya dihasilkan ulang oleh notebook; jangan menyalin dari sini tanpa memeriksa keluaran sel.

**Dataset**
- 2 933 baris latih (2023-06-29 06:00 → 2023-08-29 14:30), 734 baris uji (2023-08-29 15:00 → 2023-09-13 21:30)
- 25 kolom eksogen, seluruhnya tersedia di jendela uji; nilai hilang 9–17 % per kolom
- Target: rerata 58,19 %RH, sd 18,00 %RH, rentang 18,47–97,09

**Audit korupsi (rasio sd terhadap sd robus pada residu LOO)**
- `air_humidity` 1,20 → bersih · `air_temperature` 5,75 → 53 lonjakan · `pressure` 6,86 → 54 lonjakan
- Despiking mengubah 0,5 % nilai, menghapus 57 dari 62 ekskursi > 2,5 °C, menyisakan 0 di jendela uji

**Fisika**
- Proksi titik embun bebas-parameter: r = 0,908 terhadap target, RMSE 9,1 mentah
- Oracle `e`: harian tunggal 8,37 · 24,5 j 7,61 · 12,5 j 4,53 · 6,5 j 2,96 · 4,5 j 2,34 · 2,5 j 1,60
- Model 2,827 setara mengetahui `e` pada resolusi 6,1 jam
- Rekonstruksi `T_min` harian: dua jalur independen sepakat sd 0,047 °C, keduanya berbeda 0,43 °C dari sensor

**Pergeseran distribusi**
- Rerata suhu latih 27,5 °C → uji 24,6 °C; 48 % baris uji di kuartil terdingin latih (vs 25 %)
- `water_volume_*` konstan sepenuhnya di jendela uji

**Pemodelan**
- Bobot blend global: `hbt` 0,489 · `cat` 0,217 · `enet` 0,194 · `ridge_e` 0,05 · `l2` 0,05
- Galat perubahan 30 menit: sinyal 3,54 · tersirat oleh level 2,02 · model increment 1,76
- Bias maju per anggota: `cat` −2,89 (dalam sampel −0,006), lima anggota lain di dalam ±0,8

**Hasil**
- Tangga leaderboard: 3,02586 → 2,86595 (increment) → 2,85383 (buang `ridge`) → 2,84953 (bias pita) → **2,82744** (de-bias anggota)
- Anatomi galat (6.480 baris luar-lipatan): 39 % offset per hari; kemiringan kalibrasi harian 1,147,
  dalam-hari 1,054, per-baris 1,063
- Pembanding sejawat pada lipatan yang sama: naif 18,82 · persistensi 13,38 · proksi fisis 10,93 ·
  klimatologi jam-hari 10,16 · regresi linear berganda 8,08 · LightGBM tunggal 5,71 · **stack 4,81**
- Kendali kausalitas: LightGBM yang sama dengan jendela ekor-belakang 8,18, yaitu +2,47 (+43 %)
- Terukur dari papan peringkat: galat level jendela uji −0,4145 %RH, kemiringan kalibrasi 1,0050
- Garis dasar: rerata latih 18,0 · proksi fisis bebas-parameter 10,0 · **model 2,827**

---

## 10. Saran urutan kerja menuju tenggat

1. **Baca ulang dokumen penjelasan dataset** dari panitia (juknis 2f). Ia memuat definisi resmi
   metrik dan studi kasus; laporan harus memakai bahasanya, bukan bahasa kita.
2. **Buka halaman *Event – Data Science – Penyisihan* dan unduh seluruh template**, bukan hanya
   dua: IEEE, border NSC, **Cover**, **Lembar Pernyataan Orisinalitas**, dan **Lembar Jawaban**
   (§3). Halaman itu terkunci password panitia — kalau passwordnya tidak ada di tangan, itu
   masalah yang harus diselesaikan lebih dulu, bukan belakangan. Setelah itu siapkan kerangka
   kosong dengan tujuh bagian pada §5.2 sebelum menulis satu kalimat pun. Ini mencegah laporan
   15 halaman yang harus dipangkas.
3. **Ekspor 8–10 gambar dari notebook** ke PNG 300 dpi. Jangan screenshot; simpan lewat
   `fig.savefig(..., dpi=300, bbox_inches='tight')`.
4. **Tulis Bagian VI (Evaluasi dan Pembahasan) lebih dulu.** Bagian itu bernilai 54 % dan paling
   sulit; menulisnya saat masih segar lebih baik daripada menyisakannya untuk jam terakhir.
5. **Tulis Pendahuluan dan Kesimpulan terakhir**, setelah tahu persis apa yang dikatakan badan
   laporan.
6. **Sisakan satu sesi penuh untuk pemangkasan ke 10 halaman** dan pemeriksaan format IEEE.
7. **Kumpulkan lebih awal dari tenggat.** Tiga alasan yang saling menguatkan: Google Form bisa
   tutup lebih cepat dari perkiraan, berkas `.pkl` (8,0 MB) tetap butuh waktu unggah, dan
   **waktu pengumpulan adalah pemutus seri** kalau nilai akhir sama (§1.2, G-9).
8. **Unggah sekali saja.** Kiriman pertama yang dinilai, bukan yang terakhir (§1.2, G-6). Periksa
   berkas sampai tuntas sebelum menekan submit, lalu tunggu e-mail konfirmasi dari
   nscub26@gmail.com.

---

## 11. Berkas yang relevan di repositori ini

| berkas | peran |
|---|---|
| `NSC26_DataScience_AirHumidity.ipynb` | **deliverable utama** — notebook lengkap, sudah tereksekusi |
| `submission_nsc26_air_humidity.csv` | keluaran notebook; prediksinya identik dengan berkas ber-skor 2,82744 |
| `model_nsc26_air_humidity.pkl` | artefak model untuk juknis 2.e |
| `final_pipeline.py` | pipeline produksi; notebook mengekstrak kodenya secara verbatim |
| `progress.md` | catatan riset 49 sesi — sumber bahan mentah untuk pembahasan laporan |
| `outputs/submissions/` | seluruh berkas submission historis beserta md5-nya |
| `guide_lomba.md` | dokumen ini |
