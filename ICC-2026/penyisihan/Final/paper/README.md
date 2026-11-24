# Paper Final ICC CDW 2026: SINAPS

Karya ilmiah lengkap Bab I sampai V untuk babak final Innovation Case Competition (ketentuan:
`../penjelasan_lomba.md`, `../Ketentuan Final ICC 2026.pdf`). Pipeline disalin dari `semi-final/paper/` lalu
diperluas: Bab I sampai III direvisi supaya cocok dengan MVP, Bab IV (hasil + pengujian MVP) dan Bab V (penutup)
ditulis baru. Format tetap templat resmi panitia (`script/template/icc2026_template.docx`).

```
paper/
├── README.md                 file ini
├── arsip/                    PDF draf semifinal (Bab I-III) sebagai pembanding
├── output/                   HASIL AKHIR: Rizzz_ICC2026_Final.docx dan .pdf (jangan diedit manual)
└── script/
    ├── content.py            SEMUA TEKS (judul, abstrak, Bab I-V, tabel, referensi, lampiran)
    ├── figures.py            semua figur (matplotlib) + tangkapan layar MVP yang dipotong
    ├── docx_builder.py       pengisi templat ICC 2026 (jarang disentuh)
    ├── build.py              satu perintah: figur -> DOCX -> PDF (MS Word) -> preview + cek
    ├── template/             templat panitia
    ├── analysis/             skrip yang menghasilkan angka di paper
    │   ├── a01-a06_*.py          uji kelayakan semifinal (butuh data MRI SOOP, tidak ada di repo ini)
    │   ├── a07_mvp_e2e.py        uji ujung ke ujung API MVP (5 akun uji x 33 kasus, latensi Vercel)   +-1,5 mnt
    │   ├── a08_tutor_mvp.py      uji tutor MVP: 36 kasus x 4 skenario x 3 rumusan + penilai gpt-5.5   +-15 mnt
    │   ├── a09_latensi_tutor.py  latensi tutor tanpa beban paralel (20 permintaan)                     +-2 mnt
    │   ├── a10_ci_final.py       ringkasan + IK 95% + AUDIT MANUAL jawaban tutor -> results/final.json  <5 dtk
    │   └── a11_tangkapan_layar.py tangkapan layar MVP lokal (Playwright)                              +-1 mnt
    ├── results/              keluaran analysis/ (json, csv) + layar/*.png (tangkapan layar)
    ├── figures/              PNG hasil figures.py
    └── preview/              PNG per halaman PDF (dibuat ulang tiap build, tidak di-commit)
```

## Alur edit (WAJIB lewat script)

1. Edit teks di `script/content.py` (grafik di `script/figures.py`).
2. Build dari folder `script/` (Windows, venv bersama):

   ```bash
   cd "Final/paper/script"
   C:/Patrick/coding/.venv/Scripts/python.exe build.py --no-fig   # teks saja (+-15 dtk)
   C:/Patrick/coding/.venv/Scripts/python.exe build.py            # + regenerasi figur
   ```
   Figur yang butuh data MRI (`fig_mri`, `fig_mockup`) otomatis dilewati bila `semi-final/data/` tidak ada;
   PNG lamanya di `figures/` tetap dipakai.
3. Lihat `script/preview/hal-XX.png`: tidak ada celah besar di kolom, figur tidak menimpa teks, tabel tidak
   memenggal kata per huruf.
4. PDF dibuat MS Word dari DOCX yang sama (COM `win32com` di Windows, AppleScript di Mac), jadi DOCX dan PDF identik.

Dependensi tambahan di venv bersama (sudah terpasang): `python-docx pymupdf pywin32 pillow playwright fastapi
sqlalchemy openai httpx uvicorn`.

## Menjalankan ulang pengujian Bab IV

Semua angka Bab IV dibaca dari `results/` lewat `content.py`; jangan diketik manual.

```bash
cd "Final/paper/script/analysis"
C:/Patrick/coding/.venv/Scripts/python.exe a07_mvp_e2e.py       # memakai kode Final/mvp/ in-process, SQLite sementara
C:/Patrick/coding/.venv/Scripts/python.exe a08_tutor_mvp.py     # butuh OPENAI_API_KEY di Final/.env; cache di results/tutor_mvp_raw.jsonl
C:/Patrick/coding/.venv/Scripts/python.exe a09_latensi_tutor.py
C:/Patrick/coding/.venv/Scripts/python.exe a10_ci_final.py      # selalu jalankan terakhir
```

`a10_ci_final.py` memuat `AUDIT_DITANDAI` / `GAGAL_MANUAL` / `SAMPEL_TIDAK_DITANDAI`: putusan manual atas setiap
jawaban tutor yang ditandai penilai LLM atau pemeriksa aturan, plus sampel acak 30 jawaban yang tidak ditandai
(uji kedua 18 Okt 2026 malam: 432 jawaban, 89 ditandai, 0 gagal nyata; 2 jawaban bertoken sampah, kini disaring
`tutor.bersihkan()`). Uji pertama (pagi, 144 jawaban) diarsipkan sebagai `results/*_v1_18okt.*` dan dipakai sebagai
pembanding di Bab IV. **Kalau `a08` dijalankan ulang, jawaban tutor berubah: baca ulang daftar "kasus yang ditandai
gagal" dan sampel di `results/sampel_audit_tutor.json`, lalu perbarui konstanta audit di a10 sebelum build.**

Tangkapan layar (`a11`) butuh MVP lokal dengan data demo: `scripts/seed_demo.py` (SQLite `mvp/.local/sinaps.db`),
API di port 8000 dengan OPENAI_API_KEY (DATABASE_URL produksi sengaja TIDAK dipakai), web `npm run dev` di port 5173.

## Markup di content.py

| tulis | hasil |
|---|---|
| `{cite:absher2024}` | nomor sitasi IEEE, urut kemunculan pertama |
| `{fig:layar_latihan}` / `{tab:hasil}` | `Gambar N` / `Tabel N` |
| `**tebal**`, `*miring*` | format run |
| `num(x, 2)`, `pct(x)`, `ik(v)`, `ikp(v)` | angka gaya Indonesia, interval kepercayaan |

Di dalam f-string, kurung kurawal markup digandakan: `f"... {{fig:mri}} ..."`. Figur: `("fig", kunci, caption)`
satu kolom, `("fig", kunci, caption, True)` lebar penuh; kunci dipetakan ke PNG di `FIG` (build.py).

## Keputusan yang sudah diambil

- Bahasa Indonesia, templat ICC 2026, sitasi IEEE, tanpa em dash / en dash (build gagal kalau ada), gaya
  dicek terhadap daftar kata pantauan AI (`AI_WORDS` di build.py).
- **Topik dan RQ1 sampai RQ3 sama persis dengan semifinal** (aturan final). Yang direvisi hanya isi.
- Nama subbab Bab IV dan V mengikuti PPT ketentuan final (templat tidak mendefinisikannya):
  IV.A Hasil Implementasi, IV.B Pengujian, IV.C Pembahasan, IV.D Keterbatasan; V.A Kesimpulan,
  V.B Rencana Pengembangan, V.C Dampak.
- Bab III diselaraskan dengan MVP: soal per kasus (K1, K2, K3, K6 sekaligus), KC sasaran menentukan tingkat
  kesulitan, U-Net dilatih ulang pada 1.170 pasien, teritori (K4) dan usia lesi (K5) belum di MVP, korpus RAG baru
  catatan ajar tim. Figur mockup dan figur segmentasi semifinal dihapus dari Bab III (diganti tangkapan layar asli
  dan figur segmentasi MVP di Bab IV). Gantt pindah ke Bab V sebagai peta jalan.
- Strategi rubrik: Bab IV memakai **metrik dan target Tabel 5 (Bab III)** apa adanya dan menandai yang belum tercapai
  atau belum diuji (juri menilai konsistensi + MVP yang membuktikan isi paper). Kelemahan yang ditemukan saat uji
  (kriteria lulus K6 meloloskan anotasi terlalu luas; aturan lesi terlewat; pemeriksa fakta memberi alarm palsu;
  latensi 8 paralel 9,8 dtk) dilaporkan terbuka, diperbaiki di MVP pada 18 Okt, lalu diuji ulang; Bab IV memuat
  angka sebelum dan sesudah. Yang belum diperbaiki (K6 meloloskan anotasi terlalu sempit, korpus PNPK/SKDI) masuk
  rencana pengembangan.

## Catatan teknis

1. Catatan templat, caption, persamaan, figur lebar penuh, orientasi MRI: lihat README semifinal
   (`semi-final/paper/README.md`, catatan 1 sampai 13); semuanya masih berlaku.
2. **Builder menskalakan setiap PNG ke lebar kolom/halaman.** Untuk mengecilkan figur lebar penuh, beri margin putih
   di PNG (`_gambar(..., kanvas=FULL)` di figures.py). Cara ini dipakai pada `f_layar_latihan` (78% lebar) supaya
   muat di sisa halaman 11; sebelumnya muncul celah setengah halaman di halaman 11 dan 12.
3. Tangkapan layar diambil dengan viewport 1240x800 (latihan) dan 1440x900 (lainnya) pada skala 2x. Viewer menomori
   slice terbalik dari `slice_lesi_terbesar` di `server_data/cases.json` (a11 memakai `n - z + 1`). Ruang hitam viewer
   dipangkas dengan `_potong()`; caption menyebutkannya.
4. Chromium headless butuh `--use-angle=swiftshader --enable-unsafe-swiftshader` agar Cornerstone3D (WebGL) merender.
5. Uji tutor memakai penilai gpt-5.5 (beda dari tutor gpt-5.6-luna); setiap jawaban yang ditandai tetap dibaca manual. Regex
   skenario D sengaja longgar (menandai MCA/ACA/PCA di mana pun) supaya tidak ada tebakan yang lolos tanpa dibaca.
6. Chat tutor merender markdown (`src/components/Markdown.tsx`, sejak 18 Okt); tangkapan layar sudah diambil ulang.
7. `a11` memilih percobaan tinjau ulang dengan Dice tertinggi di antara "lesi terlewat"; jawaban tutor di Gambar 13
   berubah tiap kali a11 dijalankan, jadi cek kalimat dan detiknya di Subbab IV.A setelah mengambil ulang.
8. Data demo lokal di-seed tanpa `SINAPS_PEPPER` produksi; API lokal untuk a11 juga harus tanpa pepper itu,
   kalau tidak login demo gagal 401.

## Yang masih perlu diisi / dicek tim sebelum submit (23 Okt 2026, 23.59 WIB)

- [x] `LINK_GITHUB` = https://github.com/raphaeladikara/satu-data-final (pastikan repo publik: per 18 Okt masih 404 tanpa login)
- [x] Turnitin < 15%: skor 11% di `TURNITIN` (content.py), tangkapan layar ringkasan di
      `script/lampiran/turnitin_ringkasan.png` (masuk DOCX + PDF). Opsional: laporan PDF lengkap sebagai
      `script/lampiran/turnitin.pdf` ditempel build di akhir PDF (DOCX tidak memuatnya).
- [ ] Baca ulang pernyataan penggunaan AI di lampiran; sesuaikan dengan pemakaian AI yang sebenarnya.
- [ ] Harga GPT-5.6 Luna (`TARIF_IN/OUT`) masih sama dengan halaman pricing OpenAI.
- [ ] Demo di https://mvp-lemon-ten.vercel.app cocok dengan Bab IV (siklus latihan, tinjau ulang, dasbor dosen, tutor).
- [ ] Checklist render: preview per halaman, em dash = 0 (build otomatis), DOCX dan PDF dari build yang sama.
