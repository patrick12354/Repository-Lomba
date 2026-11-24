# AGENTS.md — memori lintas sesi TATAP

> ## 🔴 ATURAN WAJIB
>
> 1. **Baca file ini lebih dulu di awal setiap sesi**, sebelum mengerjakan apa pun.
> 2. **Setiap insight baru SELALU ditulis di bagian [Insight](#insight) paling atas**, di urutan teratas (terbaru di atas). Jangan tunggu diminta — begitu ada temuan non-obvious, langsung catat.
> 3. **Tetap ringkas.** Satu baris per temuan. Hapus entry yang sudah usang atau tergantikan, jangan ditumpuk. File ini adalah memori kerja, bukan buku harian — kalau sudah lewat ~150 baris, padatkan.
> 4. **Faktual dan spesifik.** Tulis angka, nama file, dan error persis. Tandai asumsi yang belum diverifikasi sebagai asumsi.
>
> Format: `- [YYYY-MM-DD] <isi singkat dan konkret>`
> Riwayat lengkap versi lama: `docs/arsip/agents_lengkap_2026-07-30.md` dan git commit `4f375b2`.

---

## Insight

### Semifinal (2026-07-31 →)

- [2026-07-31] 🔴 **Ablasi 19 vs 13 fitur: K1 lulus, K2 gagal.** AUC anak geometri **0,8310** (≥0,80 ✓); selisih geometri−penuh **−0,0137**, CI 95% **[−0,059, +0,025]**, batas bawah meleset 0,009 dari margin −0,05. Hasil di `research/hasil/ablasi.json`.
- [2026-07-31] **Geometri menang atau imbang di 4 dari 5 model** (NB +0,025, SVM +0,006, GB +0,003, RF −0,004). Hanya regresi logistik — model pra-tetap — yang turun berarti (−0,014). Nasib buruk, bukan pola.
- [2026-07-31] ⚠️ **Titik kerja geometri goyah:** pada sens ≥90% mendarat di **100% / spesifisitas 21,4%**, vs penuh 92,3% / 42,9%. Dengan 26 anak ASD satu anak = 3,8% sensitivitas, jadi pemilihan ambang meloncat kasar. Perlu ambang yang dipilih lebih halus; ini lebih penting daripada selisih AUC.
- [2026-07-31] ✅ **Encoding Carette TERDOKUMENTASI, bukan asumsi** (lihat entry 2026-07-21 di bawah). Palet citra diverifikasi ulang dan cocok: cyan (R rendah, G/B tinggi) = fiksasi, oranye (R tinggi, B nol) = sakade. TS007_20 cyan 3,1% vs TC001_39 cyan 27,1% — sinyalnya besar dan nyata.
- [2026-07-31] 🔑 **Halangan sebenarnya untuk 6 fitur kinematik bukan encoding, tapi laju sampling.** Carette SMI Red-m **250 Hz** vs webcam tablet **30 fps**. Jerk adalah turunan ketiga; pada 30 fps dari estimasi pandang berisik, nilainya praktis penguatan noise. **Harus diuji di studi degradasi Hari 3** sebelum 13 fitur dikunci permanen — kalau kinematik ternyata bertahan, boleh dimasukkan lagi.
- [2026-07-31] **Aturan pra-tetap yang aku tulis salah framing:** menguji geometri lawan penuh sebagai dua opsi setara, padahal penuh-19 tidak bisa dikirim ke produk apa pun hasilnya. Pertanyaan yang benar hanya K1. Yang tetap wajib ditulis jujur di paper: pada n=54 studi ini **tidak punya daya** membuktikan non-inferioritas pada margin 0,05.
- [2026-07-31] **Semifinal 30 Jul–10 Agu 2026.** Tiga deliverable: paper 12 halaman (+ section Results and Discussion), repo GitHub + README, video demo 3–5 menit. Bobot & rincian di `docs/rencana_semifinal.md`. Rubrik bergeser: Impact 45%, Implementation 45%, Demo 10%; **AI Implementation & Technical Excellence sendirian 20%**.
- [2026-07-31] Dikerjakan **sendiri**, platform **web PWA in-browser**. Konsekuensi ruang lingkup: cabang pandangan penuh & hidup; kepala/wajah dan vokalisasi hanya sinyal + skor kualitas tanpa model terlatih. Konsisten dengan garis putus-putus di Gambar 1.

### Dataset

- [2026-07-21] 🔴 **Multimodal Autism Dataset = SINTETIS / noise acak.** Rata-rata fitur tiap modalitas identik di keempat kelas (HR 89,99–90,04; voice RMS 0,3674–0,3677; motion std 0,100 semua). **Dilarang dipakai untuk klaim empiris apa pun** — hanya ilustrasi arsitektur. Filename mismatch: index menyebut `images/child_XXX.png`, aslinya `Child (N).jpg`.
- [2026-07-21] ✅ **Eye-tracking Carette = REAL, satu-satunya anchor bukti.** 547 PNG 640×480, `TCImages/` 328 TD + `TSImages/` 219 ASD. Pola nama `T{C,S}###_PP.png` → **`PP` = ID partisipan**, 54 partisipan unik. 🔴 **Wajib GroupKFold per `PP`** — satu anak menyumbang banyak citra.
- [2026-07-21] 🔑 **Skema warna Carette (dari paper, DOI 10.5220/0007402601030112):** kanal **R = velocity, G = akselerasi, B = jerk**; fiksasi = cyan, sakade = kuning/putih; nilai di-cap pada **seperempat diagonal layar**; citra **dicerminkan vertikal** (origin di bawah); threshold 200 titik per citra. Protokol: stimulus ±5 menit, SMI Red-m 250 Hz, monitor 17" 1280×1024, jarak ±60 cm, kalibrasi 5 titik.
- [2026-07-21] 🔴 **Partisipan Carette rata-rata 7,88 tahun — anak usia sekolah, BUKAN balita.** Produk menyasar <30 bulan. Dataset ini memvalidasi **prinsip** bahwa geometri scanpath diskriminatif, bukan performa pada balita. Asumsi transfer wajib dinyatakan eksplisit; jangan pernah diklaim sebaliknya.
- [2026-07-21] ⚠️ **Confound yang diakui penulisnya:** partisipan ASD cenderung melihat ke **bagian bawah layar, tempat eye-tracker diletakkan**. Kalau fitur bias vertikal muncul penting, bahas sebagai limitasi, jangan dirayakan.
- [2026-07-21] **Kebocoran Carette terkonfirmasi:** augmentasi 5× dilakukan **sebelum** cross-validation, dan tidak ada grouping partisipan sama sekali. Angka non-neural mereka (AUC ≈0,7) justru konsisten dengan baseline jujur kita — bukti bahwa lompatan ke >0,9 adalah artefak metodologis.

### Metodologi & angka POC

- [2026-07-22] **Dekomposisi penggelembungan AUC (A 0,8158 · B 0,7968 · C 0,7484 · D 0,7531):** kebocoran salinan augmentasi A−B **+0,019**; tanpa grouping partisipan B−C **+0,048**; augmentasi ketika split sudah benar C−D **−0,005**. → **Sumber terbesar adalah pengelompokan per anak, bukan augmentasi.**
- [2026-07-22] **Unit keputusan = anak, bukan citra.** AUC anak ternyata *lebih tinggi* daripada AUC citra (0,845 vs 0,753 untuk LR) karena metrik level citra membebani berlebih anak dengan banyak citra. Selalu agregasi dulu.
- [2026-07-22] **Angka POC berlaku:** LR pra-tetap, AUC anak **0,8448** (CI 0,730–0,944), AUC rekaman 0,753, titik kerja sens 92,3% / spes 42,9%, **PPV 1,6% pada prevalensi 1% (62 rujukan per kasus)**.
- [2026-07-22] ⚠️ **Klaim "38,2% variasi dari identitas anak, bukan kondisinya" TIDAK SAH.** Identitas bersarang di dalam diagnosis, jadi varians diagnosis ikut terhitung. Formulasi yang benar: "38,2% variasi fitur berada pada tingkat antarpartisipan, sehingga rekaman berulang bukan pengamatan independen."
- [2026-07-22] **Nested GroupKFold: bias pemilihan model nol** (NB terpilih 5/5 lipatan). Tapi peringkat model tidak stabil — LR pra-tetap justru mengungguli "model terbaik" di level anak. **Titik kerja jauh lebih rapuh daripada peringkat model**; ini dipakai di paper sebagai temuan, bukan disembunyikan.
- [2026-07-21] **19 fitur sebenarnya hanya ~5–6 dimensi independen.** Korelasi |r|>0,85: `n_active_cells`–`grid_entropy` 0,93; `jerk_mean`–`acc_mean` 0,93; `fixation_ratio`–`saccade_ratio` −0,92; `span_x`–`std_x` 0,90; `span_y`–`std_y` 0,90.
- [2026-07-21] **Efek ukuran teratas (level anak) semuanya geometri:** `n_active_cells` d=1,685 · `ink_frac` 1,500 · `span_y` 1,478 · `grid_entropy` 1,471 · `radial_mean` 1,374. Rata-rata |d| geometri 1,068 vs warna 0,800.
- [2026-07-21] **Sengaja tidak memakai CNN:** interpretabilitas untuk adopsi klinis, jalan di tablet murah tanpa GPU, dan dengan 54 partisipan CNN hampir pasti menghafal.

### Jebakan teknis (yang pernah menggigit)

- [2026-07-31] **Format `.ipynb`: tiap elemen `source` harus menyertakan newline-nya sendiri.** `src.split("\n")` membuat semua baris menempel jadi satu → SyntaxError. Pakai `splitlines(keepends=True)`.
- [2026-07-31] `DataFrame.pivot` dengan `values=[...]` menghasilkan MultiIndex kolom; `.to_dict()`-nya bertuple-key dan **tidak bisa di-JSON**. Ratakan kolomnya dulu.
- [2026-07-31] **Restrukturisasi jadi repo mandiri. Path yang diperbaiki:** `research/features.py` → `ROOT/"data"/...`; `poc/recompute_metrics.py` → `ROOT.parent/"data"/...`; notebook POC sel 5 (pencarian dataset naik satu tingkat lagi), sel 65 (`late_fusion` kini di `research/`), sel 67 (`MM_DIR` ke `data/`). `pyproject.toml` pythonpath jadi `["research", "poc"]`.
- [2026-07-31] ⚠️ **`recompute_protokol.py` mengimpor dari `recompute_metrics`** — keduanya wajib satu folder (`poc/`). Hanya `recompute_metrics.py` yang punya `DATA_DIR`.
- [2026-07-30] **`figs/` harus tetap di root** — `.tex` merujuknya dengan `../../figs/`.
- [2026-07-22] **`.tex` merujuk gambar dengan `../../figs/`.** Kompilasi harus dari dalam `paper/sumber/`, **3×**, lalu salin manual ke `paper/Rizzz_ConceptPaper.pdf`.
- [2026-07-22] **`figs/generate_arsitektur.py` punya tata letak otomatis** (lebar kotak diukur dari teks ter-render). Kalau mengubah isi Gambar 1, **cukup ubah `SPEC`, jangan sentuh koordinat.**
- [2026-07-22] ⚠️ **Memangkas 10–15 kata sering tidak mengurangi jumlah baris sama sekali** — teks langsung mengalir ulang. Yang berhasil: menghapus **satu kalimat utuh** (~95 karakter di lebar blok ini). `\looseness=-1` efeknya kecil dan tidak bisa diandalkan.
- [2026-07-22] ⚠️ **Cek `execution_count` dan mtime `poc_hasil.json` sebelum mengutip angka.** Notebook pernah di-Run All user di tengah sesi dan JSON tertimpa; RF 0,8681→0,8640 dan GB 0,8613→0,8626 berubah tanpa pemberitahuan.

---

## Status Saat Ini

- **Tahap: Semifinal Hari 1** (31 Juli 2026). Preliminary selesai & lolos; `paper/Rizzz_ConceptPaper.pdf` final 10 lembar.
- Rencana lengkap 10 hari: **`docs/rencana_semifinal.md`**.
- Hari 1 selesai: `research/features.py`, `research/evaluate.py`, `research/01_ablasi_fitur.ipynb` (sudah dieksekusi), `research/hasil/ablasi.json`.
- **Keputusan geometri-13 belum final** — menunggu studi degradasi Hari 3 menguji apakah fitur kinematik bertahan di 30 fps.

## Next Actions

- [ ] **Hari 2** — `02_training.ipynb`: latih model final, kalibrasi inner-fold, ambang yang lebih halus (perbaiki titik kerja 21,4%), ekspor `model.json`. Push model + tabel fitur ke Hugging Face.
- [ ] **Hari 3** — `03_degradasi.ipynb`: sweep noise gaze / laju sampling / dropout → kurva AUC vs error. Sekaligus uji apakah 6 fitur kinematik bertahan di 30 fps.
- [ ] **Hari 4–7** — app PWA: MediaPipe WASM lokal, kalibrasi 9 titik, stimulus canvas, fusi + abstain, layar laporan (mockup Lampiran F), mode replay.
- [ ] **Hari 8** — test suite, latency di tablet, README lengkap.
- [ ] **Hari 9** — paper 12 halaman + Results and Discussion.
- [ ] **Hari 10** — video demo 3–5 menit di tablet Android. Submit 10 Agustus.
- [ ] Belum terjawab: akun Hugging Face sudah ada? Nama tim tetap Rizzz?

---

## Keputusan Terkunci

*(jangan dibahas ulang tiap sesi)*

- **Produk: TATAP, alat TRIASE SKRINING di Posyandu/Puskesmas.** 🔴 **BUKAN alat diagnosis** — keluaran adalah skor risiko + rekomendasi rujukan; keputusan klinis tetap di tenaga medis. Framing ini wajib konsisten di seluruh paper dan produk.
- **Sasaran: anak 16–30 bulan**, sesi pada kunjungan 18 dan 24 bulan, menyisip di alur SDIDTK meja 4. Diberikan ke **semua anak**, bukan hanya yang positif M-CHAT — justru anak yang terlewat ceklis yang jadi sasaran.
- **Bukti empiris hanya cabang pandangan.** Cabang gerak, suara, dan fusi ditulis eksplisit sebagai prospektif. Fusi pada subjek berbeda tidak dapat ditafsirkan.
- **Arsitektur: quality-aware weighted late fusion.** Tiap cabang punya kalibrasi dan skor kualitas $q_m$ sendiri; yang mengalir ke fusi adalah pasangan $(p_m, q_m)$. Bobot produksi hanya boleh dipelajari dari prediksi out-of-fold pada kohort prospektif berpasangan.
- **Aturan abstain:** sistem menahan keputusan bila cabang pandangan gagal ambang kualitas, **atau** kurang dari dua modalitas lolos ambang.
- **Positioning vs pembanding:** M-CHAT = pelengkap, bukan pengganti (sensitivitas 49,2%, tapi PPV 90,6% untuk ASD *atau* gangguan perkembangan lain — jangan cherry-pick). SenseToKnow (Perochon dkk. 2023, AUC 0,90) adalah pembanding digital **terdekat**; kebaruan TATAP ada di operasi kader Posyandu, luring, stimulus Indonesia, dan evaluasi group-aware — **bukan** pada kamera tablet untuk gaze screening itu sendiri.
- **Diferensiasi utama: rigor metodologis.** Pemenang 2025 tidak memakai group-aware split, tidak ada CI, tidak ada baseline pembanding. Bar-nya tidak setinggi dugaan.

---

## Konteks Lomba

**Datathon RISTEK Fasilkom UI 2026, University Track.** Preliminary 13–23 Juli (concept paper, 60%) — **selesai & lolos**. Semifinal 30 Juli–10 Agustus, 35 tim. Final 30 Agustus, 7 tim.

Aturan preliminary → `docs/penjelasan_lomba.md`. Aturan + rubrik semifinal → `docs/rencana_semifinal.md`.

Pola pemenang 2025: produk multimodal, punya nama & branding, domain spesifik dan terukur, ada mockup visual. Keduanya 12–13 halaman — patokan **kualitas**, bukan panjang.

---

## Peta Berkas

Repo berdiri sendiri sejak 2026-07-31, remote `Dataton_Project_Rizzz` (privat sampai deadline).

```
project/                         # ← git root
├── AGENTS.md                    # file ini — memori lintas sesi
├── README.md · requirements.txt · pyproject.toml
│
├── data/
│   ├── autism eye tracking dataset/   # 🔑 anchor bukti (real)
│   └── Multimodal Autism Dataset/     # ⚠️ sintetis, ilustrasi saja
│
├── research/                    # kode & eksperimen semifinal
│   ├── features.py              # 🔑 SATU sumber kebenaran extractor (19 fitur, 2 set)
│   ├── evaluate.py              # helper CV, bootstrap, titik kerja, PPV
│   ├── late_fusion.py           # weighted late fusion + quality gate
│   ├── 01_ablasi_fitur.ipynb    # 19 vs 13 fitur
│   └── hasil/                   # fitur.csv, ablasi.json, (nanti model.json)
│
├── poc/                         # artefak preliminary — BEKU, jangan diubah
│   ├── poc_eyetracking.ipynb    # dijalankan USER, bukan agent
│   ├── poc_hasil.json           # angka POC (ditimpa saat notebook dijalankan)
│   └── recompute_metrics.py · recompute_protokol.py
│
├── docs/
│   ├── rencana_semifinal.md     # 🔴 rencana 10 hari, rubrik, ruang lingkup
│   ├── penjelasan_lomba.md · riset_impact.md
│   └── arsip/                   # AGENTS.md versi lengkap lama
│
├── paper/Rizzz_ConceptPaper.pdf # BERKAS SUBMIT
├── paper/sumber/concept_paper.tex  # kompilasi dari sini, 3×
├── figs/                        # arsitektur/bukti/mockup + skrip generator
├── tests/                       # pytest
└── referensi/                   # bahan pihak lain, tidak di-track git
```

---

## Milestone

- [2026-07-31] Semifinal Hari 1: `features.py` + `evaluate.py` dibuat, ablasi 19 vs 13 dijalankan, berkas dirapikan.
- [2026-07-30] Penataan berkas: `docs/`, `referensi/`. Skrip & dataset sengaja tetap di root.
- [2026-07-22] Concept paper final 10 lembar (sampul + isi 5 + Referensi + Lampiran A–G), 0 overfull, 0 sitasi tak terselesaikan.
- [2026-07-21] POC eye-tracking selesai; multimodal ditolak sebagai sumber bukti; eye-tracking jadi anchor teknis.
