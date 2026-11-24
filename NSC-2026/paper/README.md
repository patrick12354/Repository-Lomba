# Laporan Ilmiah NSC 2026 — Penyisihan Data Science

Naskah laporan untuk babak penyisihan beserta kode yang **membangun ulangnya dari
nol** setiap kali dijalankan: gambar, teks, tabel, rumus, penomoran, sampai ekspor
DOCX dan PDF. Berkas final ada di `output/`.

> ## Aturan pertama, dan yang paling penting
>
> **Jangan menyunting DOCX atau PDF hasilnya secara langsung.** Setiap suntingan
> manual akan tertimpa begitu `build.py` dijalankan lagi, dan tidak akan pernah
> ikut ke build berikutnya.
>
> Sunting berkas di `script/`, lalu **regenerate**. Itu satu-satunya jalur yang
> sah. Alasannya bukan kerapian: naskah ini masih akan dinilai lagi di Grand
> Final atas dokumen yang sama, jadi ia harus tetap bisa disunting dan dibangun
> ulang berbulan-bulan dari sekarang tanpa kehilangan apa pun.

---

## 1. Sekali saja: pemasangan

```bash
pip install python-docx pypdf docx2pdf pymupdf pandas numpy matplotlib
```

| paket | dipakai untuk | wajib? |
|---|---|---|
| `python-docx` | menyusun DOCX | ya |
| `pandas`, `numpy`, `matplotlib` | membangkitkan gambar | ya |
| `docx2pdf` | ekspor PDF lewat Microsoft Word | salah satu |
| LibreOffice di PATH | ekspor PDF alternatif | salah satu |
| `pypdf` | menimpa metadata PDF, menghitung halaman | opsional |
| `pymupdf` | `preview.py`, memeriksa render per halaman | opsional |

Tanpa Word maupun LibreOffice, DOCX tetap terbentuk dan tinggal disimpan sebagai
PDF lewat Word (File → Save As → PDF).

---

## 2. Menjalankan

Dua perintah, berurutan, dari folder `script/`:

```bash
python make_figures.py
```

```bash
python build.py
```

`make_figures.py` hanya perlu dijalankan ulang kalau gambar atau angkanya berubah.
`build.py` dijalankan setiap kali teks, tabel, atau tata letak berubah.

Ada satu skrip ketiga yang **tidak** perlu dijalankan rutin:

```bash
python pembanding.py
```

Ia melatih ulang enam metode pembanding dan satu kendali kausalitas pada
protokol lipatan yang sama dengan stack, lalu menuliskan hasilnya ke
`outputs/baselines_summary.json` dan `outputs/causal_cost.json`. Jalankan hanya
kalau angka Tabel IV atau Gambar 6 perlu dihitung ulang; setelah itu perbarui
blok `MEASURED_PEMBANDING`, `MEASURED_PERLIPATAN`, dan `MEASURED_KAUSAL` di
`make_figures.py` dari kedua berkas itu. Waktunya sekitar satu menit dan
hasilnya deterministik.

Keluarannya:

```
output/NSC26-DS042_Heisenberg_Data Science.docx
output/NSC26-DS042_Heisenberg_Data Science.pdf
```

Di akhir build, isi `output/` disapu sampai tersisa tepat dua berkas itu. Folder
inilah yang dilihat manusia saat mengunggah, jadi isinya dijaga bersih.

### Nomor tim — satu hal yang masih harus diisi

Juknis 3e mensyaratkan nama berkas `{Nomor Tim}_{Nama Tim}_{Data Science}`.
Nomor tim sudah terisi sebagai bawaan (`NSC26-DS042`, dari e-mail konfirmasi
pendaftaran nscub26@gmail.com), jadi perintah polos di atas langsung memberi nama
berkas yang benar. Kalau perlu nomor lain, isikan lewat variabel lingkungan tanpa
menyunting berkas apa pun:

```bash
NOMOR_TIM=NSC26-DS099 python build.py
```

Di PowerShell:

```bash
$env:NOMOR_TIM = "NSC26-DS099"; python build.py
```

### Border NSC

Border juknis 1d sudah terpasang otomatis; tidak ada langkah manual. Bingkainya
dibaca dari `template/Border Data Science (MAKE A COPY).pdf`, dirasterkan sekali
ke `figures/border_nsc.png`, lalu ditanam di header setiap section sehingga
terulang di keenam belas halaman di belakang teks.

Ada satu benturan yang harus diketahui sebelum menyentuh angkanya. Bingkai itu
digambar untuk dokumen Word satu kolom — berkas panitia sendiri memakai margin
kiri 113,8 pt — dan dinding kayunya memakan 78 pt di atas serta 63 pt di bawah,
sementara template IEEE hanya menyisakan 27 pt di atas. Dipasang apa adanya, ia
memakan 5,7 % ruang teks dan mendorong daftar pustaka ke halaman ke-11, yang
melanggar batas 10 halaman pada juknis 3b.

Karena itu ada tiga mode, dipilih lewat variabel lingkungan `BORDER`:

| mode | skala | margin (A/B/K/Ka) | badan naskah | catatan |
|---|---|---|---|---|
| `muat` **(bawaan)** | 1,03 | 68 / 52 / 37 / 37 | **10 hal.** | bingkai terpotong 12,6 pt atas, 25,3 pt bawah, 9,0 pt tiap sisi |
| `utuh` | 1,00 | 78 / 63 / 45 / 45 | 11 hal. | bingkai utuh, **melanggar juknis 3b** kecuali naskah dipangkas dulu |
| `off` | — | 27 / 72 / 44,6 / 44,6 | 10 hal. | margin IEEE asli, tanpa bingkai |

```bash
BORDER=utuh python build.py
```

Angka margin itu bukan tebakan: ia hasil pencarian atas piksel bingkainya
sendiri. `periksa_border()` mengulang ujinya setiap build dan mencetak jarak
bebas per sisi; kalau kotak teks menyentuh satu piksel non-putih, build berhenti
alih-alih menghasilkan PDF yang teksnya tertimpa kayu. Jadi margin boleh diubah,
asal buildnya masih lolos.

Satu jebakan yang sudah ditutup: template IEEE memasang `w:titlePg`, sehingga
halaman pertama mengambil header *first* yang kosong dan bingkainya hilang
justru di halaman judul. `pasang_border()` mendaftarkan ketiga jenis header
(*default*, *first*, *even*) ke bagian header yang sama.

### Memeriksa hasil render

```bash
python preview.py
```

Merender setiap halaman PDF menjadi PNG di `preview/`, untuk memeriksa hal-hal
yang tidak terlihat dari kode: gambar terpotong, tabel melebar keluar kolom,
tabel terbelah dua kolom, keterangan gambar terpisah dari gambarnya, dan jumlah
halaman. `python preview.py 3 4` merender halaman tertentu saja. Folder
`preview/` adalah artefak sekali pakai.

---

## 3. Susunan berkas

```
paper/
├─ README.md                     ← berkas yang sedang kamu baca
├─ script/                       ← SEMUA suntingan dilakukan di sini
│  ├─ content.py                 ← teks badan naskah       ← paling sering disunting
│  ├─ content_lampiran.py        ← teks lampiran
│  ├─ tables.py                  ← isi seluruh tabel, badan maupun lampiran
│  ├─ make_figures.py            ← seluruh gambar + angka yang dikutip naskah
│  ├─ pembanding.py             ← pembanding sejawat + kendali kausalitas
│  ├─ build.py                   ← urutan bagian, letak gambar/tabel, ekspor
│  ├─ build_lib.py               ← lapisan bantu docx, jarang disentuh
│  ├─ preview.py                 ← render per halaman untuk diperiksa mata
│  ├─ conference-template-a4.docx← template IEEE asli
│  └─ base.docx                  ← template ternormalisasi (lihat §8)
├─ figures/                      ← PNG 300 dpi + tabel_kanal.json, dari make_figures.py
├─ output/                       ← DOCX + PDF final
├─ preview/                      ← PNG per halaman, artefak sekali pakai
└─ template/                     ← salinan template dari panitia
```

Seluruh jalur bersifat relatif terhadap lokasi skrip, jadi folder ini bisa
dipindah asal susunan relatifnya tetap. `make_figures.py` membaca
`../../Dataset/` dan `../../outputs/`.

---

## 4. Mau mengubah apa, sunting yang mana

| Yang mau diubah | Berkas | Yang dicari |
|---|---|---|
| Judul makalah | `content.py` | `JUDUL` |
| Nama, NIM, surel penulis | `content.py` | `PENULIS`, `PRODI`, `FAKULTAS`, `UNIV` |
| Nama tim | `content.py` | `NAMA_TIM` |
| Abstrak | `content.py` | `INTISARI` |
| Kata kunci | `content.py` | `KATA_KUNCI` |
| Paragraf mana pun di badan naskah | `content.py` | variabel per bagian, lihat §5 |
| Paragraf mana pun di lampiran | `content_lampiran.py` | `LAMP_*`, lihat §6 |
| Isi atau angka sebuah tabel | `tables.py` | `T1` … `T10`, `TA1` … `TA3` |
| Lebar kolom tabel | `tables.py` | daftar bobot di baris terakhir tiap tabel |
| Rumus | `content.py` | daftar `EQ_*` |
| Daftar pustaka | `content.py` | `PUSTAKA` |
| Sebuah gambar | `make_figures.py` | fungsi `gambar_NN_*` |
| Urutan bagian | `build.py` | blok di bawah komentar `# --- I PENDAHULUAN` dst. |
| Letak gambar atau tabel | `build.py` | baris `figure_block(...)` / `table_block(...)` |
| Ukuran font sebuah tabel | `build.py` | argumen `size=` pada `table_block(...)` |
| Nomor tim di nama berkas | — | variabel lingkungan `NOMOR_TIM`, lihat §2 |

### Peta variabel teks di `content.py`

| Bagian di naskah | Variabel |
|---|---|
| I Pendahuluan | `PENDAHULUAN_LATAR`, `KONTRIBUSI_PEMBUKA`, `KONTRIBUSI_ITEMS`, `KONTRIBUSI_PENUTUP` |
| II-A Anatomi dataset | `DATA_ANATOMI` |
| II-B Bentuk pemisahan latih–uji | `DATA_PEMISAHAN` |
| II-C Apakah targetnya berderau | `DATA_KORUPSI` |
| III pembuka | `METODE_PEMBUKA` |
| III-A Kerangka fisis | `METODE_FISIS` |
| III-B Batas oracle | `METODE_ORACLE` |
| III-C Proksi titik embun | `METODE_PROKSI` |
| III-D Rekayasa balik blok agronomi | `METODE_AGRO` |
| III-E Pergeseran distribusi | `METODE_GESER` |
| III-F Desain validasi | `METODE_VALIDASI` |
| IV-A Despiking | `PRA_DESPIKE` |
| IV-B Rekayasa fitur | `PRA_FITUR` |
| V-A Enam anggota | `MODEL_ANGGOTA` |
| V-B Blending | `MODEL_BLEND` |
| V-C De-bias level | `MODEL_DEBIAS` |
| V-D Rekonsiliasi lintasan | `MODEL_INCREMENT` |
| V-E Bukti buta-target | `MODEL_BUTA` |
| VI-A Pembanding sejawat | `EVAL_PEMBANDING` |
| VI-B Hasil menyeluruh | `EVAL_HASIL` |
| VI-C Anatomi galat | `EVAL_ANATOMI` |
| VI-D Papan peringkat sebagai instrumen | `EVAL_INSTRUMEN` |
| VI-E Katalog kegagalan | `EVAL_KEGAGALAN` |
| VI-F Keterbatasan | `EVAL_BATAS` |
| VII Kesimpulan | `KESIMPULAN` |

Setiap variabel yang berupa daftar berarti **satu elemen = satu paragraf**.
Menambah paragraf cukup menambah satu string ke daftarnya.

### Markup di dalam teks

Berlaku di `content.py` maupun `tables.py`:

| Ditulis | Hasil |
|---|---|
| `**begini**` | **tebal** |
| `*begini*` | *miring* |
| `` `begini` `` | monospace, tanda backtick-nya tidak ikut tercetak |
| `_{s}` | subskrip |
| `^{2}` | superskrip |

Backtick dipakai untuk nama kolom, bendera, dan berkas. Istilah asing yang bukan
nama teknis ditulis miring sesuai kaidah bahasa Indonesia: *blend*, *stack*,
*oracle*, *increment*, *seed*, *submission*, *despiking*, *gradient boosting*.
Istilah yang sudah terserap tidak dimiringkan: model, data, blok, korelasi,
validasi, kalibrasi, prediksi, sensor.

Parsernya **rata, tidak bersarang**. `**tebal dengan `kode` di dalamnya**` akan
mencetak backtick-nya apa adanya, dan `*miring di dalam **tebal***` merusak
keduanya. Kalau satu frasa butuh dua gaya sekaligus, pecah jadi dua potong.

Subskrip dan superskrip **hanya** dikenali dalam bentuk berkurung kurawal, supaya
nama kolom seperti `water_volume_line1` tetap tertulis apa adanya. Untuk tanda
kurang pakai `−` (U+2212), bukan hyphen `-`, supaya lebarnya sejajar dengan angka
di dalam tabel.

Di dalam daftar `EQ_*` berlaku markup yang sama, ditambah kebiasaan matematika:
miringkan variabel satu per satu (`*z*`, `*T*`) dan biarkan nama fungsi tegak
(`exp`, `min`, `mean`). **Jangan menulis `*miring*` di dalam kurung kurawal
subskrip** — tanda bintang diproses lebih dulu dan akan merusak subskripnya.

---

## 5. Rujukan gambar, tabel, dan rumus ditulis simbolik

Nomor gambar, tabel, dan rumus dihitung otomatis dari urutan pemanggilan di
`build.py`. Yang **tidak** boleh ditulis manual adalah rujukan di dalam kalimat.
Tulis kuncinya, bukan angkanya:

| Ditulis di `content.py` / `tables.py` | Hasil di naskah |
|---|---|
| `Gambar {G:oracle} memuat kurvanya` | Gambar 3 memuat kurvanya |
| `Tabel {T:anatomi} merangkum` | Tabel I merangkum |
| `Bentuk ({E:rh}) tampak sepele` | Bentuk (1) tampak sepele |
| `parameterisasi Magnus–Bolton {R:bolton}` | parameterisasi Magnus–Bolton [1] |

Kuncinya didaftarkan di `build.py` pada `URUT_GAMBAR`, `URUT_TABEL`, dan
`URUT_RUMUS`, serta `URUT_GAMBAR_LAMP` dan `URUT_TABEL_LAMP` untuk lampiran.
Daftar-daftar itu adalah urutan yang **diharapkan**: kalau urutan pemanggilan
tidak cocok, build berhenti dengan pesan yang menyebut kunci mana yang meleset,
bukan diam-diam menomori salah.

Lampiran memakai seri penomorannya sendiri — `Gambar A.1`, `TABEL A.I` — yang
dinyalakan `mode_lampiran()` tepat sebelum bagian LAMPIRAN dibangun. Rujukan
simboliknya sama bentuknya: `{G:diurnal}` menghasilkan `A.2`, `{T:repro}`
menghasilkan `A.II`.

Konsekuensinya: menambah, memindahkan, atau membuang satu gambar hanya menuntut
satu suntingan pada daftar urutan, dan seluruh nomor di badan teks ikut benar
dengan sendirinya. Ini menutup kesalahan yang paling mudah luput saat naskah
dipangkas menuju batas halaman.

### Daftar pustaka: kunci, bukan nomor

Sitasi ditulis `{R:bolton}`, bukan `[8]`. `PUSTAKA` di `content.py` adalah dict
ber-slug, dan `build.py` memberi nomornya menurut **urutan kemunculan pertama di
naskah**, lalu mencetak daftarnya dalam urutan itu. Itu persis yang diminta IEEE
Style dan juknis 3c, dan ia gratis: memindahkan satu kalimat tidak pernah lagi
membuat nomor sesudahnya salah.

Urutan penulisan entri di dalam `PUSTAKA` karena itu tidak menentukan apa pun —
ia hanya dikelompokkan (perangkat lunak, lalu metode dan fisika) supaya enak
dibaca. Menambah rujukan berarti menambah satu entri **dan** menyitasinya.

Dua penjaga menutup cacat yang tidak terlihat dari membaca naskah:

- Entri yang tidak pernah disitasi menghentikan build, menyebut kuncinya.
  Pustaka hantu hanya ketahuan dengan menyilangkan daftar dengan teksnya, dan
  itu pekerjaan yang tidak akan pernah dikerjakan dua kali dengan tangan.
- Sitasi baru yang muncul **sesudah** daftar pustaka dicetak juga menghentikan
  build. Lampiran dibangun setelah daftar pustaka, jadi rujukan yang hanya ada
  di lampiran tidak akan pernah tercetak nomornya. Kalau sebuah sumber memang
  perlu, sitasi dulu di badan naskah.

**Rujukan antar-bagian** (`Bagian VI-C`) masih ditulis manual. Setelah menambah
atau memindahkan sub-bagian, telusuri kata "Bagian" di `content.py`.

Kunci rujukan harus polos di dalam kurung kurawalnya. `{G:despiking}` benar;
`{G:*despiking*}` tidak dikenali pola substitusi, dan sebelum ada penjaga ia
lolos diam-diam sampai tercetak mentah di PDF. Sekarang `build.py` berhenti
dengan pesan yang menyebut kunci mana yang rusak. Ini bukan kasus hipotetis:
penyisiran otomatis yang memiringkan istilah asing pernah mengenai enam kunci
sekaligus karena kata seperti "despiking" dan "oracle" ada di dalamnya.

---

## 6. Aturan angka

Setiap angka di naskah harus dapat ditemukan di keluaran `make_figures.py`.
Jangan mengetik angka dari ingatan atau menyalinnya dari dokumen lama.

`make_figures.py` mencetak seluruh angka yang dihitungnya di akhir eksekusi:

```bash
python make_figures.py
```

Angkanya berasal dari tiga kelompok, dan `make_figures.py` menandai ketiganya:

1. **Dihitung ulang dari `Dataset/`** setiap kali skrip jalan — anatomi dataset,
   audit korupsi, kurva oracle, proksi titik embun, rekayasa balik blok agronomi,
   audit dukungan, efek despiking. Rutin `hampel()` dan `es()` disalin verbatim
   dari `final_pipeline.py` supaya identik dengan pipeline produksi.
2. **Dibaca dari artefak eksperimen** di `outputs/**.csv` — skor rekonsiliasi per
   blok, anatomi galat per pita jam.
3. **Konstanta terukur** yang tidak dapat dihitung ulang tanpa melatih ulang
   seluruh stack atau mengirim ulang berkas ke Kaggle: bias bertanda per anggota,
   tangga papan peringkat, anatomi galat, dan hasil pembanding. Semuanya
   dikumpulkan di blok `MEASURED_*` di bagian atas `make_figures.py`,
   masing-masing dengan penunjuk ke berkas sumbernya.

Satu catatan tentang anatomi galat. Seluruh angka Bagian VI-C berasal dari satu
frame, yaitu 6.480 baris luar-lipatan yang dicetak notebook Bagian 12.1. Versi
sebelumnya mencampur audit blok maju di `outputs/audit_v21/breakdown.csv` untuk
bagian SSE per pita dengan kemiringan kalibrasi dari frame luar-lipatan, dan
akibatnya naskah menyebut 40 % serta kemiringan 1,106 sementara notebook
mencetak 39 % dan 1,147 atas stack yang benar-benar dikapalkan. Angka dari dua
frame tidak boleh dicampur dalam satu sub-bagian; kalau `breakdown.csv` dipakai
lagi, pakai ia untuk seluruh sub-bagian atau tidak sama sekali.

Satu tabel dikecualikan dari penyalinan tangan. Tabel A.III memuat 24 baris
angka, dan menyalinnya manual adalah undangan salah ketik yang tidak akan pernah
ketahuan. `make_figures.py` menuliskannya ke `figures/tabel_kanal.json`, dan
`tables.py` hanya memformatnya. Karena itu `make_figures.py` **wajib** dijalankan
lebih dulu; kalau berkas itu belum ada, `build.py` berhenti dengan pesan yang
menyebutnya.

Kalau eksperimen dijalankan ulang, perbarui `MEASURED` dari log yang
bersangkutan, lalu jalankan ulang kedua skrip. Arahnya selalu dari berkas hasil
ke naskah, tidak pernah sebaliknya.

---

## 7. Batas 10 halaman, dan lampiran

Juknis 3b: **maksimal 10 halaman termasuk daftar pustaka**, kertas A4, template
IEEE. Juknis 3d: **lampiran boleh ditambahkan** (dokumentasi, screenshot, data).
Kedua pasal itu tidak menyatakan secara eksplisit apakah lampiran ikut dihitung
ke dalam sepuluh halaman.

Sikap yang diambil di sini aman untuk kedua pembacaan: **badan naskah beserta
daftar pustaka dijaga berdiri sendiri di bawah 10 halaman**, dan lampiran dimulai
di halaman baru sesudahnya. Tidak ada satu pun argumen di Bagian I–VII yang
menuntut pembaca membuka lampiran. Kalau juri menghitung batas 10 halaman secara
ketat, laporan tetap memenuhinya; kalau tidak, lampirannya jadi nilai tambah.

`build.py` memeriksa ini sendiri setiap build dan mencetak, misalnya:

```
13 halaman total; badan + daftar pustaka 10 halaman (batas juknis 10) -> OK
lampiran mulai halaman 11
```

Angka yang harus diperhatikan adalah yang tengah, bukan total. Skrip menemukannya
dengan mencari halaman pertama yang memuat kata `LAMPIRAN` di dalam PDF.

Kalau badan naskah melewati batas, urutan pemangkasan yang paling murah lebih
dulu:

1. **Pindahkan ke lampiran.** Gambar penjelas, tabel rinci, dan bahan pendukung
   tidak harus ada di badan naskah. Ini pilihan pertama, bukan terakhir.
2. Perpendek gambar — tinggi `figsize` di `make_figures.py`. Satu inci gambar
   selebar dua kolom setara dua inci kolom teks.
3. Buang baris tabel yang mengulang isi gambar.
4. Padatkan kalimat di Bagian I–V.
5. **Bagian VI dipangkas paling akhir.** Ia bernilai 54 % dari nilai akhir
   penyisihan dan 31,5 % lagi di Grand Final; memangkasnya untuk menghemat
   setengah halaman adalah pertukaran yang buruk.

### Isi lampiran sekarang

| | Isi | Asalnya |
|---|---|---|
| A | Dekomposisi fisis RH, *e*ₛ(*T*), *e* (Gambar A.1) | tidak muat di Bagian III-A |
| B | Proksi titik embun bebas-parameter (Gambar A.2) | dipindahkan dari Bagian III-C |
| C | Despiking Hampel pada penggal terburuk (Gambar A.3) | dipindahkan dari Bagian IV-A |
| D | Audit dukungan per kanal (Gambar A.4) | dipindahkan dari Bagian III-E |
| E | Katalog blok fitur (Tabel A.I) | dipindahkan dari Bagian IV-B |
| F | Klimatologi diurnal tiga kanal (Gambar A.5) | tidak muat di Bagian II |
| G | Diagram protokol titik-asal bergulir (Gambar A.6) | tidak muat di Bagian III-F |
| H | Katalog kegagalan selengkapnya (Tabel A.II dan A.III) | dipindahkan dari Bagian VI-E |
| I | Kontrak reproduksibilitas: seed, md5, versi (Tabel A.IV) | baru |
| J | Anatomi dataset dan audit 24 kanal (Tabel A.V dan A.VI) | dipindahkan dari Bagian II-A |

Enam gambar itu turun ke lampiran saat naskah dipangkas kembali ke 10 halaman
setelah Bagian VI-A ditambahkan. Kriteria pemilihannya satu: pesan gambar atau
tabel tersebut sudah lengkap terbawa oleh angka di badan teks, dan tidak ada
argumen di Bagian VI yang bersandar padanya.

Menambah bahan ke lampiran: tulis teksnya di `content_lampiran.py`, tabelnya di
`tables.py` (prefiks `TA`), lalu pasang `figure_block(...)` / `table_block(...)`
di blok `LAMPIRAN` pada `build.py` beserta kuncinya di `URUT_GAMBAR_LAMP` /
`URUT_TABEL_LAMP`.

Semua gambar yang dibangkitkan `make_figures.py` sudah terpakai: delapan di
badan naskah, enam di lampiran.

---

## 8. Catatan teknis

**`base.docx`.** `conference-template-a4.docx` dari IEEE disimpan dalam format
OOXML **Strict**, yang tidak dapat dibaca `python-docx`. Saat pertama dijalankan,
`build.py` mengonversinya ke Transitional lewat LibreOffice atau Word dan
menyimpan hasilnya sebagai `base.docx`. Berkas itu ikut di-commit supaya naskah
tetap dapat dibangun ulang di mesin tanpa keduanya. Kalau templatenya diganti,
hapus `base.docx` dan jalankan ulang.

Konversi itu merusak penomoran otomatis bawaan template (Heading, keterangan
gambar dan tabel, daftar pustaka). Karena itu penomoran bawaan sengaja dimatikan
oleh `strip_numbering()` dan seluruh nomor ditulis sendiri oleh skrip. Ini
disengaja, bukan bug — jangan dikembalikan.

**Tata letak dua kolom** memakai *section break* kontinu. Wilayah selebar dua
kolom dibuat dengan menutup section dua kolom, menempatkan isi di section satu
kolom, lalu membuka section dua kolom lagi; itulah yang dikerjakan `full_width()`.
Fungsi yang dibungkusnya harus mengembalikan paragraf terakhir blok tersebut —
`figure_block` dan `table_block` sudah melakukannya.

**Rumus** dibangun sebagai tabel tanpa garis, kolom kiri untuk rumus terpusat dan
kolom kanan untuk nomornya. Bentuk ini dipilih setelah versi paragraf-bertab
gagal: tab tengah dan tab kanan dalam satu paragraf ditafsirkan berbeda oleh Word
dan LibreOffice, sehingga sebagian nomor berhenti di tengah kolom. Konsekuensinya
**dua pemanggilan `equations()` berturut-turut tanpa paragraf di antaranya akan
menyatu menjadi satu tabel** — kalau dua rumus memang berdampingan, taruh
keduanya dalam satu daftar.

**Tabel tidak boleh terbelah antar-kolom.** `cantSplit` hanya menjaga satu baris
tetap utuh, jadi `add_table()` juga memasang `keepNext` pada setiap paragraf
kecuali di baris terakhir. Tanpa itu, tabel pendek yang terbelah dua kolom
terbaca seperti dua tabel berbeda.

**Metadata.** Template IEEE bawaan membawa jejak penulis aslinya (`Author: IEEE`,
`Last modified by: Diana Romeo`, `Title: Paper Title`), dan itu ikut ke PDF kalau
dibiarkan. Skrip menimpanya setiap kali dijalankan dengan nama kedua penulis,
judul naskah, keterangan lomba, kata kunci, dan afiliasi. `Application` dan
`Producer` sengaja diisi jujur sesuai perkakas yang benar-benar dipakai.

**Pemisah desimal.** Naskah memakai koma. Gambar juga: `make_figures.py` memasang
formatter koma pada setiap sumbu berskala linear. Angka bertitik di dalam gambar
adalah cacat format yang mudah luput, jadi jangan menonaktifkan formatter itu.

---

## 9. Kalau ada masalah

| Gejala | Sebab dan tindakan |
|---|---|
| `ModuleNotFoundError: docx` | `pip install python-docx` — namanya `python-docx`, bukan `docx` |
| `Gambar tidak ditemukan: ...` | Jalankan `python make_figures.py` lebih dulu |
| `Dataset tidak ditemukan` | `make_figures.py` membaca `../../Dataset/`; pastikan susunan foldernya utuh |
| `Urutan gambar tidak cocok pada Gambar N` | Kunci di `figure_block(...)` tidak sesuai daftar urutannya; samakan keduanya |
| `figures/tabel_kanal.json tidak ada` | Jalankan `python make_figures.py` lebih dulu |
| `Rujukan tidak dikenal di content.py: {G:xxx}` | Kunci itu belum terdaftar di `URUT_GAMBAR`/`URUT_TABEL`/`URUT_RUMUS` |
| `Sitasi ke pustaka yang tidak ada: {R:xxx}` | Entrinya belum ada di `PUSTAKA` di `content.py` |
| `Pustaka tidak pernah disitasi di badan naskah` | Sitasi entri itu dengan `{R:kunci}`, atau buang dari `PUSTAKA` |
| `Sitasi baru {R:xxx} muncul SESUDAH daftar pustaka` | Lampiran menyitasi sumber yang belum pernah dirujuk badan naskah; pindahkan sitasi pertamanya ke Bagian I–VII |
| `LEWAT BATAS` pada jumlah halaman | Lihat §7. Kalau baru muncul setelah mengubah border, itu memang harga mode `utuh` — lihat §2 |
| `Kotak teks menabrak border` | Margin di `BORDER_GEOM` terlalu sempit untuk skala itu; perlebar margin atau naikkan skalanya |
| `Border tidak ditemukan` | Unduh border dari laman NSC ke `paper/template/` |
| Border hilang di halaman 1 saja | Referensi header *first* tidak terpasang; lihat `pasang_border()` |
| PDF tidak terbuat, DOCX ada | Word dan LibreOffice tidak ditemukan. Buka DOCX di Word, Save As PDF |
| `(metadata PDF dilewati)` | `pip install pypdf` |
| Properti berkas masih tertulis IEEE / Diana Romeo | Hapus PDF lama di `output/`, jalankan ulang |
| `base.docx belum ada dan konversi template gagal` | Pasang LibreOffice atau Word, atau salin `base.docx` dari repositori |
| Rumus tampil sebagai `_{k}` apa adanya | Markup subskrip ditulis di tempat yang tidak diproses; periksa §4 |
| Dua kelompok rumus menyatu jadi satu blok | Dua `equations()` berturut-turut; gabung isinya ke satu daftar |
| Tabel melebar keluar kolom | Turunkan `size=` di `build.py`, atau ubah bobot lebar kolom di `tables.py` |
| Angka di gambar memakai titik, bukan koma | Sumbu itu memakai label teks tetap; format angkanya dengan `n()` di `make_figures.py` |

---

## 10. Daftar periksa sebelum mengumpulkan

- [ ] `python make_figures.py` lalu `python build.py` dijalankan berurutan, tanpa galat
- [ ] Tidak ada em dash di naskah kecuali pada `Abstrak—` dan `Kata kunci—`
- [ ] Rujukan "Bagian X-Y" ditelusuri ulang kalau ada sub-bagian yang berpindah huruf
- [ ] Baris jumlah halaman menyatakan **OK** — badan naskah + daftar pustaka ≤ 10 halaman
- [ ] Nama berkas memuat nomor tim yang benar (`NSC26-DS042`)
- [ ] `python preview.py` diperiksa halaman per halaman
- [x] **Border template NSC** — otomatis, mode `muat` (lihat §2)
- [ ] **Template Cover NSC** sudah dipakai
- [ ] **Lembar Pernyataan Orisinalitas** diisi dan ditandatangani seluruh anggota
- [ ] Lampiran mulai di halaman baru, sesudah daftar pustaka
- [ ] Setiap gambar dan tabel dirujuk di badan teks
- [ ] Daftar pustaka IEEE Style, berurutan sesuai kemunculan pertama — dijaga
      `build.py`, tidak perlu diperiksa dengan tangan
- [ ] Diunggah **sekali saja** — kiriman pertama yang dinilai

Border sudah ditangani skrip. Dua butir sisanya — **Cover** dan **Lembar
Pernyataan Orisinalitas** — berasal dari laman *Event – Data Science –
Penyisihan* di <https://nsc.mipa.ub.ac.id/> dan masih dipasang manual setelah
PDF terbentuk.

Sumber kedua kewajiban itu berbeda berkas, dan itu sebabnya mudah terlewat:
border disebut **Juknis §1.d**, sedangkan Cover, Lembar Pernyataan Orisinalitas,
dan Lembar Jawaban hanya disebut **Guidebook §1.5.1.1 butir 3**. Juknis tidak
menyebut ketiganya sama sekali.
