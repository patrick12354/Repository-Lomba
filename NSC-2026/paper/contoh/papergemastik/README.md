# Technical Report SENDI — GEMASTIK XIX Penambangan Data

*Naskah babak penyisihan beserta generatornya.*

Folder ini berisi naskah technical report untuk babak penyisihan beserta kode
yang **membangun ulangnya dari nol** setiap kali dijalankan: teks, tabel,
gambar, penomoran, sampai ekspor PDF. Berkas final ada di `keluaran\`.

> **Aturan pertama, dan yang paling penting.**
> Jangan menyunting DOCX hasilnya secara langsung. Setiap suntingan manual akan
> tertimpa begitu `build.py` dijalankan lagi. Sunting `content.py` atau
> `tables.py`, lalu jalankan ulang.

---

## 1. Sekali saja: pemasangan

```powershell
pip install python-docx pypdf
```

`python-docx` wajib. `pypdf` dipakai untuk menimpa metadata PDF; tanpa itu DOCX
dan PDF tetap terbentuk, hanya metadata PDF-nya dibiarkan apa adanya.

Untuk ekspor PDF otomatis, LibreOffice perlu ada di PATH. Kalau tidak ada,
skrip tetap menghasilkan DOCX dan tinggal disimpan sebagai PDF lewat Word
(File → Save As → PDF).

## 2. Menjalankan

```powershell
cd C:\Patrick\Gemastik\DataMining\Project\paper
python build.py
```

Keluarannya masuk ke subfolder `keluaran\`:

```
keluaran\GEMASTIK XIX Penambangan Data - 260010041911738 - Rizzz - SENDI.docx
keluaran\GEMASTIK XIX Penambangan Data - 260010041911738 - Rizzz - SENDI.pdf
```

Polanya mengikuti Pedoman GEMASTIK XIX halaman 29, Bab III bagian C butir 2.g:
`GEMASTIK XIX Penambangan Data - <ID Tim> - <Nama Tim> - <Judul Karya>.pdf`.
Ketiga bagian itu ada di konstanta `ID_TIM`, `NAMA_TIM`, dan `JUDUL_KARYA` di
`build.py`. `JUDUL_KARYA` diisi `SENDI`, bukan judul penuh naskah, karena judul
penuh memuat titik dua yang terlarang pada nama berkas Windows dan membuat
panjang path mendekati batas 260 karakter. Skrip menolak berjalan kalau nama
yang terbentuk memuat karakter terlarang.

ID tim sudah terisi sebagai bawaan, jadi perintah polos di atas langsung memberi
nama berkas yang benar. Kalau perlu ID lain:

```powershell
$env:ID_TIM = "12345"
python build.py
```

Di akhir setiap build, isi `keluaran\` disapu sampai tersisa tepat dua berkas
tersebut. LibreOffice meninggalkan berkas kunci `.~lock` dan berkas `.tmp`, dan
build lama dengan nama berbeda akan menumpuk kalau dibiarkan. Folder ini yang
dilihat manusia saat mengunggah ke laman lomba, jadi isinya dijaga bersih.

Skrip akan mencetak jumlah gambar, jumlah tabel, dan ukuran PDF-nya. Ukuran PDF
harus di bawah 10 MB sesuai ketentuan lomba.

## 3. Susunan berkas

```
Project\
├─ reports\figures\*.png            ← gambar, dibaca otomatis
├─ scripts\build_figures.py         ← pembangkit gambar hasil eksperimen
├─ scripts\figur_encoder.py         ← pembangkit Gambar 1 (arsitektur IndoBERT)
├─ docs\paper\                      ← kerangka, tabel.md, referensi.bib (bahan)
└─ paper\                           ← FOLDER INI (naskah jadi)
   ├─ README.md                     ← berkas yang sedang kamu baca
   ├─ content.py    ← SELURUH TEKS naskah       ← paling sering disunting
   ├─ tables.py     ← isi seluruh tabel
   ├─ build.py      ← urutan bagian, letak tabel/gambar
   ├─ build_lib.py  ← lapisan bantu docx, jarang disentuh
   ├─ conference-template-a4.docx   ← template IEEE asli
   ├─ base.docx     ← template ternormalisasi, dibuat otomatis
   └─ keluaran\     ← DOCX + PDF final, ikut di-commit
```

Seluruh jalur bersifat relatif terhadap lokasi skrip, jadi folder ini bisa
dipindah atau di-clone ke mana pun asal susunan relatifnya tetap. Kalau figur
diregenerasi lewat `..\scripts\build_figures.py`, cukup jalankan ulang
`build.py` dan gambar di naskah ikut terbarui — tidak ada yang perlu disalin.

Template dicari berurutan di folder ini, lalu `Project\`, lalu folder induk.
Salinannya sengaja disimpan di sini supaya naskah tetap dapat dibangun ulang
dari isi repositori saja.

> **Catatan git.** `reports/figures/*.png` masuk `.gitignore`, jadi gambarnya
> tidak ikut ter-commit dan perlu dibangkitkan ulang dengan
> `python scripts\build_figures.py` di mesin baru. DOCX dan PDF di `keluaran\`
> ikut di-commit, sehingga hasil finalnya selalu tertelusur meskipun gambarnya
> belum dibangkitkan.

---

## 4. Mau mengubah apa, sunting yang mana

| Yang mau diubah | Berkas | Yang dicari |
|---|---|---|
| Judul makalah | `content.py` | `JUDUL` |
| Nama, NIM, email penulis | `content.py` | `PENULIS`, `PRODI`, `FAKULTAS`, `UNIV` |
| Abstrak | `content.py` | `INTISARI` |
| Kata kunci | `content.py` | `KATA_KUNCI` |
| Paragraf mana pun di naskah | `content.py` | variabel per bagian, lihat §5 |
| Angka atau baris di dalam tabel | `tables.py` | `T1` … `T16` |
| Lebar kolom tabel | `tables.py` | daftar bobot di baris terakhir tiap tabel |
| Daftar pustaka | `content.py` | `REFERENSI` |
| Urutan bagian | `build.py` | blok di bawah komentar `# --- I PENDAHULUAN` dst. |
| Letak tabel atau gambar | `build.py` | baris `table_block(...)` / `figure_block(...)` |
| Ukuran font sebuah tabel | `build.py` | argumen `size=` pada `table_block(...)` |
| Gambar mana yang dipakai | `build.py` | `fig('08-arsitektur.png')` |

## 5. Peta variabel teks di `content.py`

Nama variabelnya mengikuti bagian naskah, jadi bisa dicari langsung dengan
Ctrl+F:

| Bagian di naskah | Variabel |
|---|---|
| I-A Latar Belakang | `PENDAHULUAN_LATAR` |
| I-B Tujuan | `PENDAHULUAN_TUJUAN` |
| I-C Manfaat | `PENDAHULUAN_MANFAAT` |
| I-D Batasan | `PENDAHULUAN_BATASAN`, `BATASAN_ITEMS` |
| II-A…II-F Kajian pustaka | `KAJIAN` (daftar pasangan judul + paragraf) |
| Jembatan sebelum II-G | `KAJIAN_ANTARA` |
| II-G Leksikon | `KAJIAN_LEKSIKON`, `KAJIAN_LEKSIKON_2` … `_4`, rumus di `EQ_LEKSIKON_1` … `_3` |
| II-H TF-IDF | `KAJIAN_TFIDF`, `KAJIAN_TFIDF_2` … `_4`, rumus di `EQ_TFIDF_1` … `_3` |
| II-I Transformer | `KAJIAN_TRANSFORMER`, `KAJIAN_TRANSFORMER_2` … `_5`, rumus di `EQ_TRANSFORMER_1` … `_4` |
| Penutup Bagian II | `KAJIAN_PENUTUP` |
| III-A Deskripsi Solusi | `SOL_DESKRIPSI` |
| III-B Dataset | `SOL_DATASET` |
| III-C Metode | `SOL_METODE_PENGUMPULAN` |
| III-D Perbedaan | `SOL_PERBEDAAN` |
| III-E Metrik | `SOL_METRIK` |
| IV-A Korpus | `HASIL_KORPUS` |
| IV-B NER | `HASIL_NER` |
| IV-C Sentimen | `HASIL_SENTIMEN` |
| IV-D Asosiasi | `HASIL_ASOSIASI` |
| IV-E Event study | `HASIL_EVENT` |
| IV-F Cakupan | `HASIL_CAKUPAN` |
| IV-G Backtest | `HASIL_BACKTEST` |
| IV-H Ketahanan | `HASIL_KETAHANAN` |
| IV-I Anotasi | `HASIL_ANOTASI` |
| IV-J Penilai vs manusia | `HASIL_PENILAI` |
| V-A NER gagal | `AN_NER` |
| V-B Disambiguasi | `AN_DISAMBIGUASI` |
| V-C Transformer vs TF-IDF | `AN_TRANSFORMER` |
| V-D Uji perbaikan label | `AN_UJI_LABEL` |
| V-E Akurasi vs agregat | `AN_AGREGAT` |
| V-F Asimetri berbalik | `AN_ASIMETRI` |
| V-G Strategi merugi | `AN_STRATEGI` |
| V-H Implikasi | `AN_IMPLIKASI` |
| VI Kesimpulan | `KESIMPULAN` |
| VI-A Saran | `SARAN` |
| VI-B Ketersediaan | `KETERSEDIAAN` |

Setiap variabel yang berupa daftar (tanda `[ ... ]`) berarti **satu elemen = satu
paragraf**. Menambah paragraf cukup menambah satu string ke daftarnya.

### Markup di dalam teks

Berlaku di `content.py` maupun `tables.py`:

| Ditulis | Hasil |
|---|---|
| `**begini**` | **tebal** |
| `*begini*` | *miring* |

Sisanya ditulis apa adanya. Untuk tanda kurang, pakai `−` (U+2212), bukan
hyphen `-`, supaya lebarnya sejajar dengan angka di dalam tabel.

### Markup khusus rumus

Berlaku **hanya** di dalam daftar `EQ_*`, karena hanya daftar itu yang dilewatkan
`add_math_runs()`. Menulisnya di paragraf biasa akan tampil apa adanya.

| Ditulis | Hasil |
|---|---|
| `*d*` | *d* (variabel dimiringkan) |
| `_{k}` atau `_k` | subskrip |
| `^{⊤}` atau `^2` | superskrip |

Nama fungsi seperti `softmax`, `GELU`, `exp`, dan `clip` sengaja dibiarkan tegak,
jadi jangan dibungkus tanda bintang. Di paragraf biasa, tulis variabel dengan
`*d*` saja dan hindari subskrip; kalau notasinya butuh subskrip, pindahkan ke
rumus bernomor.

---

## 6. Contoh suntingan

**Mengubah satu paragraf.** Cari variabelnya di `content.py`, ubah stringnya:

```python
HASIL_KORPUS = [
    "Komposisi korpus disajikan pada Tabel I dan sebaran bulanannya pada "
    "Gambar 2. Dari 40.009 judul terkumpul, ...",
]
```

**Menambah baris ke tabel.** Di `tables.py`, tambahkan satu daftar ke isi tabel:

```python
T1 = ("Komposisi Korpus Judul Berita Keuangan", [
    ["Ukuran", "Nilai"],
    ["Judul terkumpul", "40.009"],
    ["Baris baru", "123"],          # ← tambahan
    ...
```

**Memindahkan gambar.** Di `build.py`, pindahkan barisnya ke posisi baru:

```python
figure_block(fig('03-caar-event-study.png'),
             'CAAR berita positif dan negatif pada event window [−1, +5].',
             width=COL_W)
```

**Membuat tabel atau gambar selebar dua kolom.** Bungkus dengan `full_width`:

```python
full_width(lambda: figure_block(fig('01-sebaran-korpus.png'),
                                'Keterangan gambar.', width=FULL_W))
```

Fungsi yang dibungkus harus mengembalikan paragraf terakhir blok tersebut —
`figure_block` dan `table_block` sudah melakukannya, jadi cukup ikuti pola di atas.

---

## 7. Metadata berkas

Template IEEE bawaan membawa jejak penulis aslinya — `Author: IEEE`,
`Last modified by: Diana Romeo`, `Title: Paper Title (use style: paper title)` —
dan itu ikut terbawa ke PDF kalau dibiarkan. Skrip menimpanya setiap kali
dijalankan, jadi properti berkas menampilkan tim penulis yang sebenarnya:

| Properti | Isi |
|---|---|
| Author / Creator (DOCX) | ketiga nama penulis, dipisah titik koma |
| Last modified by | sama dengan Author |
| Title | judul makalah |
| Subject | keterangan lomba dan cabang |
| Keywords | sama dengan kata kunci di naskah |
| Company | fakultas dan universitas |
| Application | `python-docx` |
| Producer (PDF) | `LibreOffice` |

Dua baris terakhir sengaja diisi jujur sesuai perkakas yang benar-benar dipakai,
bukan dipalsukan menjadi Microsoft Word. Yang penting sudah tercapai: tidak ada
lagi nama pihak lain yang menempel di berkas.

Nilainya diatur lewat konstanta `META_*` di bagian konfigurasi `build.py`, dan
sebagian besar diturunkan otomatis dari `content.py` — mengubah `PENULIS` atau
`JUDUL` di sana sudah cukup.

Memeriksa hasilnya:

```powershell
# Windows: klik kanan berkas → Properties → Details
# atau, kalau ada poppler:
pdfinfo "keluaran\GEMASTIK XIX Penambangan Data - [ID TIM] - Rizzz - SENDI.pdf"
```

---

## 8. Penomoran — satu hal yang perlu diperiksa manual

Nomor tabel (TABEL I, II, …), gambar (Gambar 1, 2, …), dan rumus ((1), (2), …)
**dihitung otomatis** mengikuti urutan pemanggilan di `build.py`. Menambah atau
memindahkan salah satunya akan menggeser seluruh nomor sesudahnya, dan itu benar
dengan sendirinya.

Yang **tidak** otomatis adalah rujukan di dalam kalimat. Kalimat seperti
"hasilnya pada Tabel VIII" ditulis manual di `content.py`. Jadi setelah menambah
atau memindahkan tabel, gambar, atau rumus, telusuri lagi kata "Tabel",
"Gambar", dan "Persamaan" di `content.py` dan sesuaikan nomornya.

### Rumus

Rumus ditulis lewat `equations([...])` di `build.py`, satu pemanggilan untuk satu
kelompok rumus yang berdekatan:

```python
equations(C.EQ_LEKSIKON_1)
```

Setiap kelompok dibangun sebagai satu tabel tanpa garis, kolom kiri untuk rumus
terpusat dan kolom kanan untuk nomornya. Bentuk ini dipilih setelah versi
paragraf-bertab gagal: tab tengah dan tab kanan dalam satu paragraf ditafsirkan
berbeda oleh Word dan LibreOffice, sehingga sebagian nomor berhenti di tengah
kolom alih-alih di tepi kanan.

Konsekuensinya, **dua pemanggilan `equations()` berturut-turut tanpa paragraf di
antaranya akan menyatu menjadi satu tabel** di Word. Kalau dua rumus memang
berdampingan, taruh keduanya dalam satu daftar.

Hal yang sama berlaku untuk nomor sitasi `[n]`: nomornya mengikuti urutan daftar
`REFERENSI` di `content.py`. Menyisipkan referensi di tengah daftar akan
menggeser seluruh nomor sesudahnya.

## 9. Aturan angka

Setiap angka di naskah harus dapat ditemukan di `Project\reports\angka.json`.
Jangan mengetik angka dari ingatan atau dari dokumen lama.

Kalau eksperimen dijalankan ulang, bangkitkan dulu angkanya, baru salin ke sini:

```powershell
cd ..
python scripts\report_numbers.py
python scripts\build_tabel.py
python scripts\build_figures.py
```

Lalu salin angka barunya dari `docs\paper\tabel.md` ke `tables.py` dan
`content.py`. Arahnya selalu dari berkas hasil ke naskah, tidak pernah
sebaliknya.

## 10. Kalau ada masalah

| Gejala | Sebab dan tindakan |
|---|---|
| `ModuleNotFoundError: docx` | `pip install python-docx` — perhatikan namanya `python-docx`, bukan `docx` |
| `(metadata PDF dilewati)` | `pip install pypdf` |
| Properti berkas masih tertulis IEEE / Diana Romeo | Hapus PDF lama di `keluaran\`, jalankan ulang |
| `Template ... tidak ditemukan` | `conference-template-a4.docx` harus ada di folder ini, di `Project\`, atau di folder induknya |
| `base.docx belum ada dan LibreOffice tidak ditemukan` | Pasang LibreOffice, atau pakai `base.docx` yang sudah disertakan di folder ini |
| PDF tidak terbuat, DOCX ada | LibreOffice tidak di PATH. Buka DOCX di Word, Save As PDF |
| `Gambar tidak ditemukan` | Jalankan `python ..\scripts\build_figures.py` — figur tidak ikut di-commit ke git |
| `Gambar tidak ditemukan: 14-encoder-indobert.png` | Jalankan `python ..\scripts\figur_encoder.py` — gambar ini tidak dibangkitkan `build_figures.py` |
| Rumus tampil sebagai `_{k}` apa adanya | Markup rumus ditulis di paragraf biasa; pindahkan ke daftar `EQ_*` atau tulis tanpa subskrip |
| Dua kelompok rumus menyatu jadi satu blok | Dua `equations()` berturut-turut; gabung isinya ke satu daftar |
| Template diganti, hasilnya masih gaya lama | Hapus `base.docx`, jalankan lagi supaya dikonversi ulang |
| Tabel terpotong atau melebar keluar kolom | Turunkan `size=` di `build.py`, atau ubah bobot lebar kolom di `tables.py` |
| Nomor tabel di kalimat tidak cocok | Lihat §8 — rujukan dalam kalimat ditulis manual |

## 11. Catatan teknis

`conference-template-a4.docx` disimpan dalam format OOXML **Strict**, yang tidak
dapat dibaca python-docx. Saat pertama dijalankan, skrip mengonversinya ke
Transitional lewat LibreOffice dan menyimpan hasilnya sebagai `base.docx`.

Konversi itu merusak penomoran otomatis bawaan template (Heading, caption
gambar, caption tabel, daftar pustaka). Karena itu penomoran bawaan sengaja
dimatikan oleh `strip_numbering()` dan seluruh nomor ditulis sendiri oleh skrip.
Ini disengaja, bukan bug — jangan dikembalikan.

Tata letak dua kolom memakai section break kontinu. Wilayah selebar dua kolom
dibuat dengan menutup section dua kolom, menempatkan isi di section satu kolom,
lalu membuka section dua kolom lagi. Itulah yang dikerjakan `full_width()`.
