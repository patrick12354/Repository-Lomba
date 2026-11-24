# Paper Semifinal ICC CDW 2026: SINAPS

Draf karya ilmiah Bab 1 sampai 3 untuk babak semifinal Innovation Case Competition (lihat
`../guide lomba.md`). Format mengikuti templat resmi panitia ICC CDW 2026
(`Template Paper Semifinal ICC 2026.docx/.pdf` di root repo; salinannya `script/template/icc2026_template.docx`).

```
paper/
├── README.md                 file ini
├── .venv/                    venv Python 3.14 khusus paper (TIDAK di-commit)
├── .env                      OPENAI_API_KEY + OPENAI_MODEL untuk a05_llm.py (TIDAK di-commit)
├── output/                   HASIL AKHIR: <NamaTim>_ICC2026_Semifinal.docx dan .pdf
└── script/
    ├── content.py            SEMUA TEKS PAPER (judul, penulis, abstrak, isi, tabel, referensi)
    ├── figures.py            semua grafik/ilustrasi (matplotlib) + pengecek teks bertumpuk
    ├── docx_builder.py       pengisi templat ICC 2026 (jarang perlu disentuh)
    ├── build.py              satu perintah: figur -> DOCX -> PDF -> preview + cek otomatis
    ├── template/
    │   ├── icc2026_template.docx  TEMPLAT AKTIF: templat semifinal ICC 2026 dari panitia (lihat catatan 1)
    │   ├── ieee_strict.docx       templat IEEE A4 lama (tidak dipakai lagi)
    │   └── template_base.docx     templat IEEE lama versi save-as Word (tidak dipakai lagi)
    ├── analysis/             eksperimen yang menghasilkan angka di paper
    │   ├── a01_kohort.py         statistik 1.505 pasien + 1.456 lesion mask  (+-1 mnt)
    │   ├── a02a_unduh.py         unduh DWI+ADC 250 subjek SOOP tambahan ke data/train_extra (+-5 mnt, ~540 MB)
    │   ├── a02_segmentasi.py     aturan ambang vs U-Net 2.5D: latih 250 pasien, uji 30 subjek sampel held-out (+-10 mnt, MPS)
    │   ├── a03_penilaian.py      600 anotasi sintetis, ambang dipelajari & diuji per-subjek (5-fold) vs Dice saja (+-2 mnt)
    │   ├── a04_bkt.py            simulasi BKT adaptif vs acak + analisis sensitivitas 12 skenario (<1 mnt)
    │   ├── a05_llm.py            uji tutor LLM: tanpa/dengan fakta x tanpa/dengan tekanan mahasiswa (+-10 mnt, API OpenAI)
    │   └── a06_ci.py             CI 95% (bootstrap per pasien/subjek/kasus, Wilson bila 0%/100%) dari hasil a02/a03/a05 (<10 dtk)
    ├── results/              keluaran analysis/ (json, csv, npz) yang dibaca content.py & figures.py
    ├── figures/              PNG hasil figures.py (dibuat ulang tiap build)
    └── preview/              PNG per halaman PDF untuk dicek visual (dibuat ulang tiap build)
```

## Alur edit (WAJIB lewat script)

**Jangan edit `output/*.docx` atau `.pdf` langsung.** Semua perubahan akan hilang di build berikutnya.

1. Edit teks di `script/content.py` (atau grafik di `script/figures.py`).
2. Build ulang dari folder `script/`:

   ```bash
   cd "semi-final/paper/script"
   ../.venv/bin/python build.py            # build penuh (+-40 detik)
   ../.venv/bin/python build.py --no-fig   # kalau hanya teks yang berubah
   ```
3. Buka `script/preview/hal-XX.png` (atau PDF-nya) dan cek visual: figur tidak menimpa teks,
   tidak ada ruang kosong janggal, caption dan nomor benar.
4. PDF dibuat **oleh MS Word dari DOCX yang sama**, jadi isi dan tata letak DOCX dan PDF identik.

Setup venv di mesin baru (Mac):

```bash
cd "semi-final/paper"
python3 -m venv .venv
.venv/bin/pip install python-docx matplotlib numpy pandas nibabel scipy scikit-image pymupdf lxml torch
```

Data MRI (`semi-final/data/`, tidak di-commit) hanya dibutuhkan untuk `analysis/` dan dua figur
yang menampilkan slice MRI (`fig_mri`, `fig_mockup`). Kalau data tidak ada, build tetap jalan
selama `figures/*.png` dan `results/` sudah ada: pakai `--no-fig`.

## Markup di content.py

| tulis | hasil |
|---|---|
| `{cite:absher2024}` | nomor sitasi IEEE `[14]`, diurutkan otomatis sesuai kemunculan pertama |
| `{fig:mri}` | `Gambar 7` (nomor mengikuti urutan blok `fig` di BODY) |
| `{tab:kc}` | `Tabel 3` |
| `**tebal**`, `*miring*` | format run |
| `num(x, 2)`, `pct(x)` | angka gaya Indonesia (koma desimal, titik ribuan) dari `results/*.json` |

Di dalam f-string, kurung kurawal markup harus digandakan: `f"... {{fig:mri}} ..."`.
Blok figur: `("fig", kunci, caption)` untuk satu kolom, `("fig", kunci, caption, True)` untuk
lebar penuh. Kunci figur dipetakan ke nama PNG di `FIG` dalam `build.py`.
Referensi yang ada di `REFS` tapi tidak pernah disitasi akan dicetak sebagai peringatan dan
**tidak** muncul di daftar pustaka.

## Aturan gaya penulisan

- **Paper berbahasa Indonesia** (teks, figur, caption "Gambar 1."/"Tabel 1.", "Daftar Pustaka", angka 0,78 / 1.505).
  Versi bahasa Inggris sudah dihapus; kalau dibutuhkan lagi: `git show 9d84bfe:semi-final/paper/script/content.py`
  (figur Inggris: `figures.py` di commit yang sama).
- **Tidak boleh ada em dash (U+2014)**, juga en dash. `build.py` gagal kalau menemukannya
  (termasuk di referensi: rentang halaman pakai tanda hubung `263-266`).
- Tulisan harus terdengar manusia (skill `ai-paraphrase`): hindari kata pantauan seperti
  "delve", "crucial", "pivotal", "landscape", "not only ... but also", "furthermore".
  `build.py` mencetak peringatan `[gaya]` bila menemukannya.
- Alur default: masalah nyata dan angkanya (berita/data Indonesia dan dunia) dulu, baru solusi.
- Angka hasil eksperimen **tidak diketik manual**. Ubah skrip di `analysis/`, jalankan, lalu build.
- Klaim yang belum diuji ditandai eksplisit (lihat paragraf keterbatasan dan kata "simulasi").

## Catatan teknis (hal-hal yang tidak kelihatan dari kode)

1. **Templat ICC 2026** (`icc2026_template.docx`) adalah ekspor Google Docs: Letter, margin 0,7" atas/bawah
   dan 0,65" kiri/kanan, section 1 kolom (judul, nama tim, penulis) lalu section kontinu 2 kolom 3,5" (jarak 0,2").
   Banner "Innovation Case Competition Campus Data Week 2026" ada di header section pertama saja (halaman 1),
   halaman berikutnya memakai header kosong; nomor halaman di kanan bawah. Builder **tidak** memakai style bernama;
   format tiap blok disalin dari paragraf contoh templat (indeks di `Builder.__init__`: judul 0, nama tim 2,
   penulis 3, abstrak 4, kata kunci 8, heading I 10, isi 13, heading A 18, figur 25, caption 30, caption tabel 32,
   tabel 33, persamaan 37, heading tanpa nomor 44, referensi 46). Kalau panitia mengganti templat, cek ulang
   indeks dengan dump struktur body. Label "Abstrak—"/"Kata Kunci—" memakai em dash karena begitu di templat
   (larangan em dash tetap berlaku untuk teks di content.py). Penyimpangan yang disengaja: margin sel tabel
   57 twip (templat 115) supaya kolom sempit seperti "KC" tidak pecah per huruf.
2. **PDF dirender MS Word** (`pdf_word` di build.py, AppleScript `save as ... format PDF`).
   Karena itu PDF = tampilan DOCX di Word. LibreOffice (`--soffice`) hanya cadangan; hasilnya
   sedikit berbeda (pemenggalan baris, posisi figur).
3. **Figur lebar penuh** dibuat dengan section break kontinu (2 kolom -> 1 kolom -> 2 kolom).
   Word menyeimbangkan kolom sebelum break, jadi posisi blok `("fig", ..., True)` di BODY
   menentukan apakah ada ruang kosong. Kalau muncul celah besar di bawah kolom, pindahkan blok
   figur lebar ke sebelum/sesudah satu paragraf lalu build ulang.
4. **Caption** ditulis manual oleh builder: "Gambar N. ..." di bawah figur dan "Tabel N. ..." di atas tabel,
   9pt rata tengah, angka Arab (templat: "Table 1", "Fig. 1").
5. **Penulis**: satu paragraf seperti templat, "Nama¹*, Nama¹, ..." lalu baris afiliasi bernomor superscript.
   Penulis pertama = corresponding author (asterisk). Afiliasi yang sama digabung jadi satu nomor.
6. **Persamaan**: format disalin dari persamaan contoh templat (tab tengah 2790 twip, nomor rata kanan 5040). Persamaan panjang harus
   dipecah (satu kolom hanya muat +-45 karakter).
7. **Cek figur**: `figures.check_overlap()` mencetak `[figur ...] tumpang-tindih` bila dua teks
   bertabrakan dan `teks keluar kotak` bila teks di dalam `box()` melebihi kotaknya. Cek ini tidak
   menangkap teks yang menimpa titik data atau garis, jadi tetap lihat PNG-nya. Semua figur dibuat
   dengan lebar final (COL = 3,38 in, FULL = 7 in) sehingga ukuran font di PNG sama dengan di kertas.
8. **Orientasi MRI**: data SOOP berorientasi LAS. Tampilkan `slice.T` dengan `origin="lower"`
   supaya konvensi radiologis (kiri pasien di kanan gambar) dan anterior di atas.
9. Skala ADC berbeda antar-pemindai (median otak 3.800 sampai 9.800 satuan mentah), jadi
   analisis memakai ADC relatif terhadap median otak.
10. `a02_segmentasi.py` di Apple M4 (MPS) butuh +-12 menit. Konfigurasi awal (160 px, 40 epoch)
    diperkirakan 50 menit, jadi diturunkan ke 128 px, 25 epoch.
11. **Ruang kosong di kolom** muncul di sekitar figur lebar penuh dan tabel (Word menyeimbangkan
    kolom; tabel lebar tidak dipecah, tabel satu kolom boleh berlanjut ke kolom berikutnya). Cara yang berhasil di draf ini: memindahkan blok figur lebar
    beberapa paragraf ke bawah (Gambar 6 dipindah ke tepat sebelum Gambar 7) dan menaruh figur
    kolom sebelum paragrafnya (Gambar 12). Judul "Daftar Pustaka" diberi keep-with-next.

12. **Tingkat kesulitan kasus** memakai indeks komposit D = -log10(volume) + log2(fokus >= 0,1 ml), dibagi per
    tersil (a01_kohort.py). Kriteria lama (multifokal = sulit) membuat ~67% kasus jadi "sulit".
13. **a05_llm.py** menyimpan jawaban mentah di `results/llm_raw.jsonl` dan melewati kasus yang sudah ada untuk model
    yang sama; hapus file itu untuk mengulang dari nol. Paragraf hasil di content.py otomatis berganti ke versi
    "protokol" kalau `results/llm.json` tidak ada.

## Status dan yang masih perlu diisi

- Harga GPT-5.6 Luna di content.py (`TARIF_IN/OUT`) = US$0,20/1,20 per 1 juta token (harga turun 80% per 30 Jul 2026;
  cek ulang di developers.openai.com/api/docs/pricing sebelum final). Estimasi jam radiolog ada di `JAM_RADIOLOG`.
- Mitra klinis (FK Unair, RSUD Dr. Soetomo) ditulis sebagai mitra yang dituju. Kalau sudah ada dosen/radiolog yang
  bersedia, sebut namanya di paragraf tim (Bab III.H) supaya kelayakan lebih meyakinkan.

- Penulis: 4 orang (nama, NIM, Sains Data, Universitas Airlangga) di `META["penulis"]`
  (content.py). Section penulis otomatis dibuat 4 kolom (`_authors` di docx_builder.py).
- Nama tim untuk nama file: `NAMA_TIM` di build.py (sekarang "Rizzz").
- Angka KKI 0,8 radiolog/100.000 dikutip lewat sumber sekunder (artikel BADR). Kalau ada akses
  ke data KKI langsung, ganti referensi `kki2024`.
- Final (23 Okt 2026) butuh Bab 4 (hasil) dan Bab 5 (penutup): tambahkan blok `h1` baru di BODY.
