# AGENTS.md

> **BACA FILE INI DULU DI AWAL SETIAP SESI, SEBELUM MENGERJAKAN APAPUN.**
> Sebelum sesi berakhir atau setiap kali ada temuan/keputusan baru, **tambahkan entry ke bagian Insight Log / Milestone di bawah.**

---

## 0. Protokol Agent (wajib)

**Di awal sesi:**

1. Baca `AGENTS.md` (file ini) — konteks, keputusan, dan status terkini.
2. Baca `docs/penjelasan_lomba.md` — aturan & rubrik lomba.
3. Cek bagian **Status Saat Ini** dan **Next Actions** di bawah sebelum mulai kerja.

**Selama sesi:**

- Kalau menemukan sesuatu yang non-obvious (kondisi data, kendala teknis, keputusan arah, hasil eksperimen) → **langsung catat ke Insight Log**, jangan tunggu diminta.
- Kalau menyelesaikan tahap besar → **catat ke Milestone Log**.
- Update **Status Saat Ini** dan **Next Actions** kalau berubah.

**Format entry:** `- [YYYY-MM-DD] <isi singkat dan konkret>`

**Aturan menulis:** faktual dan spesifik. Tulis angka, nama file, dan error persis. Jangan menulis insight yang belum diverifikasi tanpa menandainya sebagai asumsi.

---

## 1. Konteks Proyek

**Lomba:** Datathon RISTEK Fasilkom UI 2026 — Preliminary Round, University Track
**Deliverable yang digarap di folder ini:** AI Product Concept Paper (bobot **60%** dari nilai preliminary)
**Deadline:** 23 Juli 2026, 23:59 WIB
**Format:** NeurIPS 2015 template, maksimal 5 halaman (di luar cover/bibliography/appendix)
**Nama file submit:** `TeamName_ConceptPaper.pdf`

Aturan lengkap & rubrik → lihat `docs/penjelasan_lomba.md`.

**Prioritas rubrik (jangan lupa):** Impact 25% > Technical Quality 15% > Originality 10% > Scalability 7.5% > Report Structure 2.5%. Kualitas argumen masalah lebih menentukan daripada kecanggihan model.

---

## 2. Isi Folder

```
project/
├── AGENTS.md                       # file ini
├── .gitignore                      # cache Python, .DS_Store, artefak LaTeX
│
├── docs/                           # dokumen kerja yang ditulis sendiri
│   ├── penjelasan_lomba.md         # ringkasan aturan & rubrik lomba
│   └── riset_impact.md             # angka bersumber untuk Introduction & Literature Review
│
├── referensi/                      # bahan mentah dari pihak lain, read-only
│   ├── Datathon TM Preliminary UNI.pdf  # TM deck asli (PDF berbasis gambar, bukan teks)
│   ├── nips2015.docx / nips2015.pdf     # template NeurIPS 2015
│   └── contoh tahun sebelum/            # concept paper pemenang 2025 (Timnya Olip, Blekping)
│
├── poc_eyetracking.ipynb           # notebook POC (dijalankan user, bukan agent)
├── poc_hasil.json                  # angka hasil POC (ditimpa otomatis saat notebook dijalankan)
├── late_fusion.py                  # implementasi weighted late fusion + quality gate
├── test_late_fusion.py             # uji unit fusion, missing modality, dan pembelajaran bobot
├── recompute_metrics.py            # reproduksi poc_hasil.json: AUC level anak, nested CV, efek ukuran
├── recompute_protokol.py           # reproduksi dekomposisi protokol A-D (augmentasi, jalankan setelah yang di atas)
├── setup_kernel.sh                 # daftarkan .venv yang sudah ada sebagai kernel Jupyter
├── .vscode/                        # settings.json mengarah ke .venv + extensions.json
│
├── figs/                           # arsitektur.pdf, bukti.pdf, mockup.pdf + skrip generatornya
│   └── png/                        # versi PNG untuk pratinjau cepat
│
├── paper/
│   ├── Rizzz_ConceptPaper.pdf      # BERKAS SUBMIT (hanya ini yang ada di paper/)
│   └── sumber/                     # semua berkas kerja LaTeX
│       ├── concept_paper.tex       # sumber LaTeX (kompilasi 3x!)
│       ├── concept_paper.pdf       # keluaran mentah, disalin ke ../Rizzz_ConceptPaper.pdf
│       └── *.aux, *.log, *.out     # artefak kompilasi, tidak di-track git
│
├── Multimodal Autism Dataset/      # dataset multimodal: images, voice, motion, physio
└── autism eye tracking dataset/    # TCImages/, TSImages/ — eye-tracking scanpath
```

**Kenapa skrip, notebook, dan dataset tetap di root:** notebook mencari folder
`autism eye tracking dataset` relatif terhadap cwd, `recompute_*.py` memakai
`Path(__file__).parent` sebagai ROOT, dan notebook meng-import `late_fusion`
dari folder induk dataset. Semuanya sudah konsisten satu sama lain, jadi
memindahkannya ke `src/` atau `data/` hanya menambah risiko tanpa manfaat.
`concept_paper.tex` merujuk gambar dengan `../../figs/`, jadi `figs/` juga
harus tetap di root.

### Catatan dataset

#### A. Multimodal Autism Dataset — ⚠️ SINTETIS, TIDAK DIPAKAI SEBAGAI BUKTI

**Sumber:** https://www.kaggle.com/datasets/kadhiravanucet/multimodal-autism-dataset

- 100 sampel, 4 modalitas: `images/` (100 .jpg), `voice/` (100 .wav), `motion/` (100 .json), `physio/` (100 .csv)
- Index: `autism_dataset_index.csv` + `autism_dataset_metadata.json`
- Label: `severe_asd` 33, `typical` 25, `mild_asd` 23, `moderate_asd` 19
- Struktur per modalitas: motion = dict `{head,left_hand,right_hand,torso}` masing-masing 300×3 (30 fps, 10 s) + flag `stimming_detected`; physio = 100 baris `Time,HR,GSR,TEMP`; voice = WAV PCM 16-bit mono 16 kHz, **persis 2.0 detik semua**; images = JPEG wajah anak, ukuran bervariasi (100 ukuran berbeda, ±170–200 px).
- ⚠️ **Mismatch filename:** index merujuk `images/child_XXX.png`, file aslinya `Child (N).jpg`.

**⚠️ TEMUAN KRITIS — dataset ini noise acak, label tidak bisa diprediksi.** Sudah diverifikasi (lihat Insight Log 2026-07-21): rata-rata fitur tiap modalitas **identik di keempat kelas**. Jangan pakai untuk klaim empiris apa pun.

#### B. Autism Eye Tracking Dataset — ✅ REAL, INI ANCHOR TEKNIS

**Sumber:** https://www.kaggle.com/datasets/aqilamalfa/autism-eye-tracking
**Sumber asli (untuk sitasi paper):** Carette et al. — visualisasi scanpath eye-tracking ASD vs TD.

- 547 PNG 640×480, latar hitam, berisi trace scanpath (garis saccade + titik fiksasi, warna cyan/oranye).
- `TCImages/` = 328 gambar, kontrol / typically developing (TD)
- `TSImages/` = 219 gambar, kasus ASD
- **Pola nama `T{C,S}###_PP.png`**: `###` = indeks rekaman, **`PP` = ID partisipan**. TS memakai PP `01–29` (29 partisipan ASD), TC memakai PP `30–59` (30 partisipan TD). Total 54 partisipan unik hadir di folder.
- 🔴 **Wajib GroupKFold per partisipan (`PP`).** Satu partisipan menyumbang banyak gambar; random split = kebocoran data.

---

### Hasil POC final & penulisan paper (2026-07-21)

- [2026-07-21] ~~**Notebook sudah dijalankan penuh oleh user. Angka final:** 547 citra, 54 partisipan, 19 fitur. Model terbaik Naive Bayes, **AUC group-aware 0,7753 (CI 95% 0,683–0,858)**. Sensitivitas 90,4% pada spesifisitas 34,8%, PPV 48,1%. Varians dari identitas anak **38,2%**.~~ ⚠️ **SUPERSEDED 2026-07-22** — angka ini level citra, dan CI-nya sudah diganti. Lihat entry 2026-07-22 di bawah untuk angka yang berlaku.
- [2026-07-21] 🔑 **Temuan terkuat untuk paper adalah ukuran efeknya, bukan AUC-nya:** `n_active_cells` d=1,685; `ink_frac` d=1,500; `span_y` d=1,478; `grid_entropy` d=1,471; `radial_mean` d=1,374. Semua jauh di atas ambang efek besar (0,8). Okupansi zona tengah TD 54,0% vs ASD 43,2%. Ini yang dipakai sebagai bukti utama di paper, bukan angka akurasi model.
- [2026-07-21] ~~**Replikasi protokol Carette:** A 0,816 · B 0,797 · C 0,748 · D 0,753. → Penggelembungan +0,063 AUC, dan hampir seluruhnya berasal dari augmentasi (+0,067), bukan dari grouping partisipan (−0,005).~~ ⚠️ **SALAH, DIKOREKSI 2026-07-22.** Angka A-D-nya benar, tapi interpretasinya terbalik: +0,067 itu selisih A−C yang mengukur mekanisme split, bukan augmentasi. Dekomposisi yang benar ada di entry 2026-07-22.
- [2026-07-21] ⚠️ **KOREKSI PENTING atas asumsi awal: kurva belajar TIDAK menanjak di paruh akhir.** Kemiringan paruh awal +0,0379 tapi paruh akhir **−0,0238**; AUC naik 0,729 (8 partisipan) ke 0,781 (32 partisipan) lalu turun-naik tidak stabil sampai 0,766 (44 partisipan), dengan std melonjak 0,047 ke 0,102. Penyebabnya set uji mengecil ketika partisipan latih bertambah. → **Klaim "data lebih banyak pasti membantu" TIDAK BOLEH dipakai.** Di paper ditulis jujur sebagai: data yang ada belum cukup untuk menentukan batas atas performa pendekatan ini.
- [2026-07-21] ⚠️ Ambang pada sensitivitas 90% jatuh di 0,000 karena probabilitas Naive Bayes tersaturasi (fitur banyak yang berkorelasi |r|>0,85). Kalibrasi model perlu jadi pekerjaan lanjutan; tidak dibahas di paper karena fokus paper bukan pada model.
- [2026-07-21] `centroid_y` hanya peringkat 15 dari 19 pada permutation importance → **confound posisi eye-tracker tidak menggerakkan hasil.** Tetap ditulis sebagai limitasi di paper.
- [2026-07-21] **Nama produk final: TATAP** (Tes Atensi Tumbuh-kembang Anak berbasis Pandangan).
- [2026-07-21] Paper ditulis di LaTeX (`paper/sumber/concept_paper.tex`), tata letak NeurIPS 2015 direkonstruksi manual: letter, blok teks 5,5×9 inci, Times 10pt, satu kolom. **Badan teks pas 5 halaman, Referensi mulai halaman 6.** Struktur: Pendahuluan (porsi terbesar, untuk Impact 25%) → Tinjauan Pustaka + tabel gap analysis → Metodologi (konsep, arsitektur, data, pemodelan, POC 1 paragraf, skalabilitas) → Etika & Limitasi → Kesimpulan.
- [2026-07-21] **Nama tim: Rizzz.** Berkas submit: `paper/Rizzz_ConceptPaper.pdf` (versi LaTeX).
- [2026-07-21] **Identitas tim sudah masuk paper:** Timotius C. P. Sihombing (timotiuspatrick@gmail.com), Raphael Angelo A. Purnama (raphael.adikara@gmail.com), Aqila Malfa Zahira (aqilamalfa@gmail.com), Fakultas Teknologi Maju dan Multidisiplin, Universitas Airlangga.
- [2026-07-21] Versi DOCX sempat dibuat lalu **dihapus atas permintaan user**; yang dipakai hanya versi LaTeX karena tipografinya lebih rapi. Kalau suatu saat butuh DOCX lagi, catatan tata letaknya: letter, margin 1,5 inci kiri-kanan dan 1 inci atas-bawah, Times New Roman 10pt, satu kolom, gambar sekitar 4,5 dan 4,05 inci, dan badan teks baru muat 5 halaman setelah space_after paragraf ditekan ke 1pt.
- [2026-07-21] **Metadata PDF sudah diatur** lewat `\hypersetup`: Title judul lengkap, Author "Timotius Christopher Patrick Sihombing", Subject, Keywords. Creator dan Producer sengaja dikosongkan. Sudah diverifikasi tidak ada jejak nama tool AI apa pun di metadata maupun isi berkas.
- [2026-07-21] **Soal indentasi paragraf:** paragraf pertama setelah heading memang rata kiri tanpa indent, paragraf berikutnya menjorok. Ini konvensi tipografi standar dan perilaku bawaan kelas `article`, bukan kesalahan. Indentasi menandai pergantian paragraf, dan setelah heading pergantian itu sudah jelas.
- [2026-07-21] ⚠️ **Jebakan yang sempat terjadi:** menghapus `*.aux` lalu mengompilasi sekali saja membuat semua sitasi jadi `[?]`. LaTeX butuh minimal 2 kali kompilasi setelah `.aux` hilang. Sekarang sudah dikompilasi 3 kali, semua sitasi `[1]`–`[12]` ter-resolve.
- [2026-07-21] Notebook dan paper sudah dibersihkan dari em-dash, emoji, dan catatan proses. ⚠️ **8 judul grafik di dalam notebook ikut diubah, jadi gambar PNG yang tersimpan masih memuat judul lama.** Perlu satu kali Run All lagi agar gambarnya ikut segar.

## 3. Status Saat Ini

- Tahap: **revisi putaran keempat (audit eksternal ketiga) sudah diterapkan. PDF dan notebook selaras. Tinggal Run All notebook + submit.**
- Produk final: **TATAP**, triase skrining ASD multimodal dengan weighted late fusion untuk Posyandu; bukti empiris saat ini tetap hanya cabang pandangan.
- **Model utama sekarang regresi logistik (pra-tetap), dievaluasi pada unit anak.** Angka utama: AUC anak 0,845 (CI 0,730-0,944), AUC rekaman 0,753, titik kerja sens 92,3% / spes 42,9%, PPV 1,6% pada prevalensi 1% (62 rujukan per kasus).
- 🔴 **Struktur berkas BERUBAH: abstrak sekarang ada di dalam badan teks 5 halaman, bukan di sampul.** Sampul hanya judul + penulis + afiliasi. Susunan: sampul + isi 5 halaman (abstrak di halaman 1) + Referensi (hal. 6) + **Lampiran A-G**. Total 10 lembar.
- `poc_hasil.json` memakai skema baru (`auc_record_level`, `auc_child_level`, `titik_kerja_anak_primary`). Notebook sel 63 menulis skema yang sama. **Angka tidak berubah pada revisi putaran keempat.**

## 4. Next Actions

- [ ] **Restart Kernel + Run All di notebook** (wajib): sel 46-47, 50-55, 62-63 sudah diubah dan outputnya sengaja dikosongkan; angka akan sama persis dengan `poc_hasil.json` (sudah diverifikasi lewat `/tmp/verify_cells.py`)
- [ ] **Kompilasi ulang `paper/sumber/concept_paper.tex` dengan Tectonic 3x lalu salin ke `paper/Rizzz_ConceptPaper.pdf`.** PDF yang ada sekarang dihasilkan pdflatex di sandbox dengan stub hyphenation Inggris (estimasi konservatif). Sisa ruang di halaman isi terakhir sekitar 5 baris, jadi aman.
- [x] Baca sekali lagi `Rizzz_ConceptPaper.pdf` untuk cek typo dan suara penulisan
- [x] Revisi final berdasarkan audit rubrik: SenseToKnow, konsistensi AUC, studi jembatan, dan sitasi
- [x] Revisi putaran kedua berdasarkan audit metodologis: dekomposisi A-D, klaim 38,2%, AUC level anak, nested CV, framing prospektif, baseline M-CHAT, klaim prevalensi
- [x] Revisi putaran keempat: abstrak masuk badan teks, Gambar 1 quality gate per cabang, klaim dipersempit, Lampiran A tiga kolom, throughput konsisten, reference standard klinis, kalibrasi inner-fold + aturan abstain, penanda status Tabel gap, mockup produk (Lampiran F), rincian POC (Lampiran G)
- [ ] Submit lewat form panitia sebelum 23 Juli 2026, 23:59 WIB
- [ ] (Opsional) Lengkapi lubang riset di `docs/riset_impact.md` §9 kalau ada waktu
- [ ] (Opsional, sengaja dilewat karena batas halaman) Estimasi biaya per perangkat/BOM, jadwal pembaruan model luring, target latency dan ukuran model, jalur regulasi dan ethical approval, mekanisme support perangkat di lapangan
- ~~Putuskan posisi dataset sintetis~~ selesai, jadi ilustrasi arsitektur saja
- ~~Finalkan definisi masalah + kuantifikasi urgensi~~ selesai, lihat `docs/riset_impact.md`
- ~~Baca 2 concept paper pemenang~~ selesai, kalibrasi tercatat di Insight Log
- ~~Gap analysis vs solusi eksisting~~ selesai, lihat `docs/riset_impact.md` §8
- ~~Baca PDF Carette dkk.~~ selesai, kebocoran terkonfirmasi
- ~~Eksperimen eye-tracking final~~ selesai, angka di `poc_hasil.json`
- ~~Tentukan nama & branding produk~~ selesai, TATAP
- ~~Buat gambar arsitektur~~ selesai, `figs/arsitektur.pdf`
- ~~Draft paper NeurIPS 2015~~ selesai, `paper/sumber/concept_paper.pdf`

---

## 5. Keputusan Penting

*(catat keputusan arah yang sudah disepakati supaya tidak dibahas ulang tiap sesi)*

- [2026-07-21] Concept paper digarap paralel/duluan sebelum Kaggle (13–17 Juli), sesuai saran panitia.
- [2026-07-21] **Posisi dua dataset sudah final:**
  - **Eye-tracking (real)** = satu-satunya sumber validasi empiris. Semua angka di paper harus berasal dari sini, dengan GroupKFold per partisipan.
  - **Multimodal (sintetis)** = dipakai **hanya sebagai ilustrasi rancangan arsitektur** produk (menunjukkan modalitas apa saja yang akan diintegrasikan di roadmap). **Dilarang keras** mengambil angka akurasi/metrik apa pun darinya, dan statusnya sebagai data sintetis/placeholder harus ditulis eksplisit di paper.
  - Konsekuensi penulisan: framing "multimodal" tetap dipertahankan (sesuai pola pemenang 2025), tapi diposisikan sebagai *future work / product roadmap*, sementara *proof of concept* berdiri di atas modalitas gaze.
- [2026-07-21] **Sudut produk sudah final: alat TRIASE SKRINING di level Posyandu/Puskesmas.**
  - Konsep: anak menonton video adegan sosial ±2 menit di tablet Android biasa → kamera depan mengestimasi arah pandang (webcam-based gaze estimation) → ekstraksi fitur geometri scanpath → keluaran **skor risiko + rekomendasi rujukan**.
  - 🔴 **BUKAN alat diagnosis.** Framing ini wajib konsisten di seluruh paper — output adalah triase/rujukan, keputusan klinis tetap di tangan tenaga medis. Ini sekaligus pertahanan etis dan pembeda dari klaim berlebihan.
  - Positioning gap: M-CHAT = ceklis subjektif, false positive tinggi; eye-tracker klinis (Tobii, EarliPoint) = akurat tapi mahal & hanya di klinik. Belum ada yang **webcam-based, dioperasikan kader, konteks Indonesia**.
  - Angle teknis orisinal: representasi **scanpath-sebagai-citra** → model visi bisa dipakai tanpa butuh koordinat gaze mentah (x, y, t), sekaligus menghasilkan output yang bisa dibaca manusia (peta pandangan) → menjawab hambatan trust pada AI medis black-box.
  - Jalur adopsi: menyisip di program **SDIDTK Kemenkes** lewat Posyandu yang sudah menjangkau hampir tiap desa. Inferensi on-device, jalan offline.
  - Strategi diferensiasi vs pemenang 2025: **rigor metodologis** (GroupKFold per partisipan, confidence interval, baseline pembanding, limitasi eksplisit) — celah nyata karena pemenang tahun lalu tidak melakukannya.
- [2026-07-21] **Keputusan final multimodal menggantikan status brainstorming:** TATAP memakai tiga model unimodal terpisah untuk pandangan, gerak kepala/wajah, dan vokalisasi. Setiap model menghasilkan probabilitas terkalibrasi; quality gate membuang sinyal gagal dan weighted late fusion menormalisasi ulang bobot modalitas yang tersedia. Rata-rata sama bobot adalah baseline, sedangkan bobot produksi hanya boleh dipelajari dari prediksi out-of-fold pada kohort prospektif berpasangan (modalitas dari anak/sesi yang sama). Fusi hanya diadopsi jika mengungguli model unimodal terbaik dan memperbaiki kalibrasi pada evaluasi terkelompok per anak.
- [2026-07-22] **Konfirmasi panitia: halaman sampul tidak boleh memuat abstrak.** Abstrak masuk hitungan 5 halaman isi. Sampul hanya judul, penulis, afiliasi, dan baris identitas lomba. Keputusan "titip abstrak di sampul" dari putaran ketiga dibatalkan.
- [2026-07-22] **Gambar 2 wajib tetap ada di halaman 1-5** (keputusan user). Ruang untuk abstrak dicari dari pemangkasan prosa, bukan dari memindahkan gambar ke lampiran.
- [2026-07-22] **Aturan abstain final:** sistem menahan keputusan bila cabang pandangan gagal ambang kualitas, atau bila kurang dari dua modalitas lolos ambang.
- [2026-07-21] **Batas klaim multimodal tetap final:** model unimodal boleh dipralatih pada kohort berbeda, tetapi fusion tidak boleh dievaluasi dengan memasangkan subjek lintas dataset. Dataset multimodal sintetis tidak dipakai untuk metrik performa. AUC 0,775 dan seluruh hasil POC tetap hanya untuk cabang pandangan; cabang gerak, suara, dan fusion ditulis eksplisit sebagai prospektif.

---

## 6. Insight Log

*(temuan non-obvious — kondisi data, kendala teknis, hasil eksperimen)*

### Revisi putaran keempat: audit eksternal ketiga (2026-07-22 malam)

**Konteks:** audit eksternal memberi estimasi 49,5/60 (82,5/100) dan mendaftar 8 revisi isi berprioritas. Seluruhnya diterapkan.

- [2026-07-22] 🔴 **KONFIRMASI PANITIA MENGUBAH STRUKTUR: halaman sampul TIDAK boleh memuat abstrak.** Abstrak dihitung sebagai bagian dari 5 halaman isi. Konsekuensinya sampul kini hanya judul, penulis, afiliasi, dan baris identitas lomba; abstrak pindah ke atas halaman isi 1. Ini membatalkan solusi "titip abstrak di sampul" dari putaran ketiga.
- [2026-07-22] 🔴 **Keputusan user soal Gambar 2: JANGAN dihilangkan dari halaman 1-5.** Alasannya halaman badan teks akan terasa sepi kalau hanya ada satu gambar. Jadi ruang untuk abstrak dicari dari pemangkasan prosa, bukan dari memindahkan Gambar 2 ke lampiran. Yang boleh dipendekkan bebas.
- [2026-07-22] **Keputusan user soal aturan abstain (revisi #7):** sistem menahan keputusan bila **cabang pandangan gagal ambang kualitas, ATAU kurang dari dua modalitas lolos**. Alasan: pandangan satu-satunya cabang yang punya bukti empiris, dan fusi baru bermakna bila ada minimal dua sinyal.
- [2026-07-22] **Keputusan user: mockup produk dibuat sebagai lampiran** (bukan menggantikan panel Gambar 2). Hasilnya `figs/mockup.pdf` dan Lampiran F: dua layar, (a) laporan sesi dengan satu modalitas dikeluarkan, (b) layar penahanan keputusan. Ini menutup kritik audit bahwa klaim "laporan yang dapat diaudit" hanya berupa teks.
- [2026-07-22] **Keputusan user soal statistik Impact: perbaiki sitasi + tambah skenario jangkauan.** Angka "1 dari 833" dan "Sleman 1 dari 150" **dihapus** karena tertempel ke sitasi [5] yang judulnya hanya membahas Pontianak. Diganti pernyataan jujur bahwa angka yang beredar berasal dari ekstrapolasi atau studi regional yang metodenya tidak sebanding, plus skenario operasional yang aritmetikanya transparan: 300 Posyandu x 10 anak/jam x 4 jam = sekitar 12 ribu sesi per bulan, sehingga bottleneck-nya kapasitas asesmen lanjutan, bukan jumlah perangkat.
- [2026-07-22] ⚠️ **Cakupan SDIDTK 70,8% (Kemenkes 2024) TIDAK dipakai.** Angka itu hanya muncul di ringkasan hasil pencarian, tidak berhasil diverifikasi dari Profil Kesehatan Indonesia 2024 secara langsung. Begitu juga populasi 0-4 tahun 22,75 juta dari BPS: halaman tabel BPS client-rendered dan tidak dapat difetch, jadi angkanya tidak dipakai sebagai sitasi. Skenario jangkauan dibangun hanya dari angka yang sudah tersitasi di paper (338.881 Posyandu) plus target Lampiran C.
- [2026-07-22] **Gambar 1 diregenerasi dengan quality gate dipecah.** Blok awal jadi *capture QC* (wajah, cahaya, audio) karena hanya itu yang dapat diperiksa sebelum pemodelan; skor kualitas $q_m$ dan kalibrasi probabilitas pindah ke dalam masing-masing cabang, dan yang mengalir ke fusi adalah pasangan $(p_m, q_m)$. Blok kalibrasi bersama yang lama dihapus karena bisa terbaca seolah kalibrasi dilakukan sekali untuk semua modalitas.
- [2026-07-22] 🔑 **`figs/generate_arsitektur.py` ditulis ulang dengan tata letak otomatis.** Lebar tiap kotak diukur dari teks yang sudah dirender (`get_window_extent`), kolom disusun kiri ke kanan, dan ada loop yang memperkecil seluruh fontsize serempak sampai total muat. Ini menyelesaikan jebakan lama secara permanen: sebelumnya koordinat kotak ditulis manual sehingga setiap perubahan teks membuat tulisan meluber keluar kotak atau kotak terpotong tepi kanan. **Kalau mengubah isi Gambar 1, cukup ubah `SPEC`, jangan sentuh koordinat.**
- [2026-07-22] **Tiga klaim dipersempit (revisi #3):** "Penyebabnya bukan ketiadaan alat, melainkan..." jadi "Hambatannya mencakup..."; "TATAP mengurangi ketergantungan" jadi "ditujukan untuk"; "bukti kuantitatif bahwa protokol evaluasi lazim menggelembungkan akurasi" jadi "reimplementasi terkendali yang mengukur seberapa besar protokol evaluasi lazim menaikkan AUC". Klaim M-CHAT juga tidak lagi digeneralisasi dari satu validasi: "Angkanya berbeda antar validasi dan populasi, tetapi arahnya konsisten".
- [2026-07-22] **Lampiran A jadi tiga kolom Lulus / Revisi dan uji ulang / Gagal** karena versi lama meninggalkan zona tengah yang tidak terdefinisi (galat 3-5 derajat, deteksi wajah 70-85%, ICC 0,60-0,75, dst). Ditambah pernyataan bahwa studi jembatan mengukur **kesetaraan pengukuran**, bukan akurasi diagnosis; baris "penurunan AUC subkelompok" karena itu dipindah ke Lampiran B tempat kohort prospektif dibahas.
- [2026-07-22] **Target waktu vs throughput diselaraskan (revisi #5).** Versi lama menetapkan <=5 menit/anak dan >=12 anak/jam, yang identik secara matematis (60/5) dan mensyaratkan utilisasi 100%. Sekarang: median <=5 menit, persentil ke-90 <=7 menit, kapasitas >=10 anak/jam. Bagian 3.6 menyebut margin ini eksplisit.
- [2026-07-22] **Reference standard klinis ditambahkan (revisi #6):** asesmen perkembangan terstandar + diagnosis konsensus oleh klinisi yang **dibutakan terhadap keluaran TATAP**, instrumen disepakati sebelum pengumpulan data, kasus belum pasti dipantau ulang. Ditambah dua aturan evaluasi: seluruh kunjungan anak yang sama (18 dan 24 bulan) wajib satu lipatan, dan satu lokasi disisihkan penuh sebagai validasi eksternal.
- [2026-07-22] **Kalibrasi dan pembelajaran bobot dinyatakan berjalan di lipatan dalam (revisi #7):** *constrained logistic stacking* berpenalti pada prediksi out-of-fold; anak dan lokasi pada lipatan luar tidak pernah ikut mengkalibrasi. Tanpa ini pembaca berhak curiga ada calibration leakage.
- [2026-07-22] **Tabel gap (Lampiran E) diberi penanda status VAL/PRO/REN** supaya rancangan TATAP tidak tampak setara dengan produk yang sudah diuji. Klaim "SenseToKnow perlu unggah data" diganti "luring tidak dilaporkan" karena paper tidak punya dasar untuk klaim yang lebih kuat.
- [2026-07-22] **Ambang monitoring di Lampiran D dibuat dua tingkat.** Audit menunjukkan "penurunan >0,05 AUC menghentikan penyebaran" tidak dapat dijalankan real-time karena AUC menuntut diagnosis konfirmasi. Sekarang: indikator harian yang tidak menunggu diagnosis (kegagalan sesi, sebaran $q_m$, proporsi keputusan ditahan, rujukan per 1.000 anak) dipantau terus; metrik berbasis diagnosis hanya dinilai pada tinjauan berkala, untuk subkelompok dengan minimal 30 anak dan 8 kasus, dan harus bertahan pada dua tinjauan berturut-turut.
- [2026-07-22] **Lampiran G dibuat untuk menampung detail POC yang dipindah dari Bagian 3.5:** tabel perbandingan lima model pada dua unit metrik, hasil nested GroupKFold, dan dekomposisi A-D lengkap. Badan teks kini hanya memuat angka utama plus rujukan ke lampiran.

### Kendala tata letak putaran keempat (2026-07-22 malam)

- [2026-07-22] 🔴 **Memindahkan abstrak ke badan teks membuat isi jadi 6 halaman; harus dipangkas ~27 baris.** Yang dilakukan: abstrak dipadatkan dari ~330 ke ~175 kata; detail ranking model dan dekomposisi A-D pindah ke Lampiran G; §2.2 dan §2.3 dirapatkan; caption Gambar 1 dan 2 dipersingkat; caption diubah dari `small` ke `footnotesize`; `titlespacing` section 1,15ex/0,75ex ke 0,9ex/0,6ex dan subsection 0,95ex/0,5ex ke 0,75ex/0,4ex; Gambar 1 dari 0,86 ke 0,76 lebar teks, Gambar 2 dari 0,76 ke 0,66.
- [2026-07-22] ⚠️ **Jebakan yang berulang: memangkas 10-15 kata sering tidak mengurangi jumlah baris sama sekali**, karena teks langsung mengalir ulang. Yang benar-benar berhasil adalah menghapus **satu kalimat utuh** (sekitar 95 karakter di lebar blok ini). Kalimat yang akhirnya dihapus: "Pemisahan ini memungkinkan pralatih pada kohort berbeda tanpa menganggap subjeknya berpasangan" di §3.4, aman karena isinya sudah dinyatakan di §3.3 sebagai "fusi pada subjek berbeda tidak dapat ditafsirkan".
- [2026-07-22] `\looseness=-1` disisipkan pada 8 paragraf panjang. Efeknya kecil dan tidak dapat diandalkan (TeX mengabaikannya kalau tidak bisa memampatkan tanpa melanggar badness), jadi jangan dihitung sebagai penghematan.
- [2026-07-22] **Sisa ruang di halaman isi terakhir sekitar 5 baris.** Ini buffer terhadap perbedaan hyphenation: sandbox memakai stub pola Inggris yang memberi lebih sedikit peluang pemenggalan, sehingga hasil Tectonic dengan pola Indonesia seharusnya sama atau lebih pendek.
- [2026-07-22] **Verifikasi PDF:** 10 lembar (sampul + isi 5 + Referensi + Lampiran A-G), 0 error, 0 overfull, 0 sitasi `[?]`, metadata Creator/Producer kosong, seluruh halaman diperiksa via render PNG.
- [2026-07-22] 🔴 **Notebook sudah di-Run All penuh oleh user pukul 21:02 di tengah sesi, dan `poc_hasil.json` ikut tertimpa.** Dua angka berubah dari versi sebelumnya: **Random Forest AUC anak 0,8681 → 0,8640** dan **Gradient Boosting 0,8613 → 0,8626** (keduanya model stokastik). Sisanya identik. Tabel Lampiran G dan sel 62 notebook sempat memakai angka lama dan sudah dikoreksi. **Pelajaran: cek `execution_count` dan mtime `poc_hasil.json` sebelum mengutip angka, jangan mengandalkan salinan JSON yang dibaca di awal sesi.**
- [2026-07-22] **Status eksekusi notebook terverifikasi bersih:** 38 sel kode dengan `execution_count` 2 sampai 39 berurutan sesuai urutan sel, seluruhnya punya output. Artinya benar-benar hasil satu Restart Kernel + Run All, bukan eksekusi sepotong-sepotong.
- [2026-07-22] **Verifikasi tanda hubung:** 0 em-dash (U+2014) di `.tex`, di PDF, maupun di notebook (source dan output). Empat kemunculan `---` di `.tex` semuanya di dalam baris komentar `% ---- ... ----` sehingga tidak pernah dirender. En-dash yang ada di PDF semuanya sah: rentang angka, rentang halaman referensi, dan selisih protokol (A--B, B--C, C--D).
- [2026-07-22] **Notebook diselaraskan tanpa mengubah satu angka pun:** sel 64 menambahkan penempatan capture QC vs $q_m$ per cabang, sel 68 menambahkan aturan abstain konkret dan pembedaan kegagalan perekaman vs ketiadaan respons, sel 70 menambahkan reference standard yang dibutakan, child-grouping lintas kunjungan, site held-out, kalibrasi inner-fold, dan ambang minimum subkelompok. Sel 62 (kesimpulan) sudah konsisten sejak putaran ketiga sehingga tidak diubah.

### Revisi putaran ketiga: audit eksternal kedua (2026-07-22)

- [2026-07-22] 🔴 **Keputusan user: regresi logistik jadi model pra-tetap, titik kerja ikut dihitung dari model itu.** Konsekuensi yang harus diingat: AUC anak memang naik (0,8448 vs 0,8338 Naive Bayes) **tetapi titik kerjanya lebih buruk** — pada sensitivitas 92,3% spesifisitasnya hanya **42,9%** (Naive Bayes 57,1%), PPV pada prevalensi 1% turun dari 2,1% ke **1,6%**, dan beban rujukan naik dari 47 ke **62 per satu kasus benar**. Angka jelek ini sengaja dipakai karena dipilih sebelum melihat hasil; di paper justru dipakai sebagai bukti bahwa titik kerja jauh lebih rapuh daripada peringkat model.
- [2026-07-22] **Efek samping yang menguntungkan: konflik AUC 0,775 vs 0,753 hilang total.** Protokol D pada Gambar 2c memakai regresi logistik, jadi 0,753 sekarang identik dengan AUC rekaman model utama. Caption tidak perlu lagi menjelaskan dua eksperimen berbeda.
- [2026-07-22] **Peringkat model tidak stabil dan itu ditulis eksplisit:** AUC rekaman tertinggi Naive Bayes 0,7753; AUC anak tertinggi Random Forest 0,8681, tetapi RF tidak pernah terpilih di nested GroupKFold (NB terpilih 5/5). Paper menyatakan POC tidak menetapkan model produksi.
- [2026-07-22] **Target populasi produk dikunci: usia 16-30 bulan, sesi pada kunjungan 18 dan 24 bulan.** Alasan yang ditulis: berimpit dengan jendela ESDM dan indikasi EarliPoint, serta membuat norma dibandingkan dalam kelompok umur sempit.
- [2026-07-22] **Protokol stimulus ditambahkan:** pada dua penanda waktu tetap aplikasi meminta pengasuh memanggil nama anak, sehingga respons terhadap nama dan latensi vokal punya titik awal. Quality gate sekarang membedakan **kegagalan perekaman** (turunkan $q_m$, buang modalitas) dari **ketiadaan respons pada rekaman berkualitas baik** (dipertahankan sebagai fitur perilaku).
- [2026-07-22] **Klaim 0,063 dipersempit** jadi hasil reimplementasi dengan model dan fitur identik, bukan koreksi universal yang bisa dikurangkan dari hasil orang lain.
- [2026-07-22] 🔴 **Batas 5 halaman hampir jebol: revisi menambah ~46 baris.** Yang menyelamatkan: **Tabel gap analysis dipindah ke Lampiran E** (menghemat ~12 baris sekaligus memungkinkan tabel diperluas jadi 10 dimensi), plus pemangkasan prosa di seluruh bagian, `parskip` 0,3em ke 0,24em, `textfloatsep` 6pt ke 4pt, Gambar 1 ke 0,86 dan Gambar 2 ke 0,76 lebar teks. Badan teks akhirnya kembali pas 5 halaman.
- [2026-07-22] **Lampiran A-E ditambahkan** (tidak dihitung batas halaman, sesuai aturan): A kriteria go/no-go studi jembatan (galat sudut, deteksi wajah, ICC fitur, kegagalan sesi, subkelompok), B kriteria penerimaan fusi (sensitivitas, beban rujukan, CI, calibration slope, decision curve, subkelompok, perbandingan alur), C target operasional pilot (≤5 menit/anak, ≥90% lolos percobaan pertama, ≥12 anak/jam, spesifikasi perangkat), D tata kelola data dan pelaporan performa per subkelompok, E tabel perbandingan 10 dimensi.
- [2026-07-22] **Gambar 1 diregenerasi** dengan blok rantai `wajah/mata, pose kepala → titik pandang layar → scanpath, 19 fitur` pada cabang pandangan. ⚠️ Jebakan: menaikkan `xlim` matplotlib tanpa menaikkan lebar figur membuat teks meluber keluar kotak, karena ukuran font tidak ikut menyusut. Perbaikannya mengembalikan `xlim` ke 10,15 dan menurunkan fontsize kotak tertentu ke 6,1-6,2.
- [2026-07-22] **Notebook disinkronkan:** `PRIMARY = "Logistic Regression"` ditambahkan di sel 50, sel 52 melaporkan `auc_record_level`/`auc_child_level` plus titik kerja dua model, sel 55 menghitung ambang pada **unit anak** (confusion matrix 54 anak, bukan 547 rekaman), sel 63 menulis skema JSON baru termasuk protokol dan dekomposisi. Output basi sel 46-47 (dekomposisi lama yang salah) dan sel 50-55 dikosongkan.
- [2026-07-22] ✅ **Verifikasi silang dilakukan tanpa menjalankan notebook penuh:** `/tmp/verify_cells.py` mengeksekusi source sel 50, 52, 53, 55 apa adanya di atas fitur yang sama, lalu mencocokkan 10 angka terhadap `poc_hasil.json`. Semua cocok sampai 4 desimal dan tidak ada error runtime.
- [2026-07-22] ⚠️ **Sandbox agent perlu `pip install scikit-learn --break-system-packages`** (tidak terpasang bawaan) dan proses latar harus dijalankan dengan `setsid nohup ... < /dev/null &`. Selain itu, **berkas yang baru diedit lewat file tool kadang belum tersinkron ke mount sandbox**: percobaan pertama menjalankan `recompute_metrics.py` masih memakai versi lama. Cek `grep` isi file di sandbox sebelum menjalankan skrip yang baru diedit.

### Revisi putaran kedua: audit metodologis (2026-07-22)

- [2026-07-22] 🔴 **KOREKSI TERPENTING: dekomposisi penggelembungan AUC pada versi lama SALAH dan sudah diperbaiki.** Notebook lama mencetak `auc_A - auc_C` sebagai "bagian yang murni dari augmentasi", padahal A dan C **sama-sama** memakai augmentasi sehingga selisihnya mengukur mekanisme split, bukan augmentasi. Dekomposisi yang benar memakai B sebagai perantara: **kebocoran antarsalinan augmentasi A−B = +0,0190; tidak mengelompokkan per partisipan B−C = +0,0484; augmentasi ketika split sudah benar C−D = −0,0048.** Artinya **sumber penggelembungan terbesar adalah pengelompokan per anak, bukan augmentasi** — kebalikan dari yang ditulis di paper versi lama. Angka penuh: A 0,8158 · B 0,7968 · C 0,7484 · D 0,7531.
- [2026-07-22] 🔴 **Klaim "38,2 persen variasi berasal dari identitas anak, bukan kondisinya" tidak sah dan sudah diganti.** Yang dihitung `variance_explained_by_group` adalah rasio SS_between/SS_total dengan pengelompokan partisipan. Karena tiap anak hanya berada pada satu kelompok diagnosis, identitas **bersarang di dalam** kondisi, sehingga varians diagnosis ikut masuk ke angka itu. Formulasi baru: "rata-rata 38,2 persen variasi fitur berada pada tingkat antarpartisipan, sehingga rekaman berulang dari anak yang sama bukan pengamatan independen". Pemisahan kausal butuh model hierarkis `fitur ~ diagnosis + (1|anak)`.
- [2026-07-22] ✅ **AUC level anak dihitung dan ternyata LEBIH TINGGI daripada level citra.** Split memang participant-disjoint, tetapi metrik lama dihitung atas 547 prediksi citra sehingga anak dengan banyak citra terbobot berlebih. Setelah probabilitas out-of-fold dirata-ratakan per anak (54 anak, 26 ASD, 28 TD): **Naive Bayes 0,8338 (CI 95% 0,716–0,934)** vs 0,7753 di level citra. Perbandingan lengkap level anak: Random Forest 0,8681 · Gradient Boosting 0,8613 · SVM 0,8489 · **Logistic Regression 0,8448** · Naive Bayes 0,8338. Paper melaporkan kedua metrik secara terpisah.
- [2026-07-22] ✅ **Nested GroupKFold dijalankan: bias pemilihan model ternyata nol.** Naive Bayes terpilih pada **kelima** lipatan luar, sehingga estimasi nested identik dengan estimasi biasa (0,7753 citra / 0,8338 anak). Tetapi peringkat model tidak stabil: garis dasar pra-tetap (regresi logistik) justru **mengungguli** "model terbaik" pada level anak (0,845 vs 0,834). Karena itu paper menyebut angkanya eksploratif.
- [2026-07-22] **Titik kerja pada unit anak jauh lebih baik daripada unit citra.** Ambang sensitivitas ≥90% di level anak memberi **sensitivitas 92,3%, spesifisitas 57,1%** (bandingkan versi lama level citra: 90,4% / 34,8%). PPV pada kohort ini 66,7% karena prevalensi sampel ~48%. Pada prevalensi hipotetis 1% PPV turun ke 2,1% (≈47 rujukan per satu kasus benar), pada 2% jadi 4,2% (≈24 rujukan). Angka ini masuk paper sebagai alasan ambang produksi harus ditetapkan dari kapasitas rujukan, bukan dari POC.
- [2026-07-22] **Keputusan produk yang diambil user:** (a) label tetap **risiko ASD** (Opsi A), dengan konsekuensi kohort prospektif wajib memuat *hard-negative developmental controls* (keterlambatan bahasa, gangguan pendengaran, keterlambatan umum); (b) TATAP diberikan ke **semua anak** pada kunjungan SDIDTK, bukan hanya yang positif M-CHAT, karena masalah utamanya justru anak yang terlewat ceklis; (c) evaluasi prospektif membandingkan empat alur: M-CHAT saja, pandangan saja, TATAP multimodal, M-CHAT+TATAP, dengan kriteria penerimaan eksplisit.
- [2026-07-22] **Klaim "basis data prevalensi" dihapus.** Data hasil skrining bukan data prevalensi (peserta Posyandu tidak representatif, hasil skrining bukan diagnosis, ada non-response). Diganti jadi "catatan risiko skrining terstandar untuk surveilans layanan dan perencanaan kapasitas rujukan", dengan pengakuan bahwa estimasi prevalensi tetap butuh sampling representatif dan konfirmasi diagnosis.
- [2026-07-22] **Abstrak dan kesimpulan diubah ke suara proposal.** Versi lama memakai present tense ("kamera dan mikrofon menangkap") yang berkesan sistem sudah tervalidasi, padahal bukti hanya gaze-only. Sekarang eksplisit "mengusulkan *rancangan*" dan "manfaat kamera tablet serta cabang gerak, suara, dan fusi akan diuji prospektif".

### Kendala tata letak dan cara mengatasinya (2026-07-22)

- [2026-07-22] 🔴 **Seluruh revisi menambah ~35 baris sedangkan badan teks sudah pas 5 halaman.** Pemangkasan prosa redundan hanya menutup ~14 baris. Kedua gambar diperiksa dan ternyata **sudah ter-crop rapat** (whitespace-nya di dalam plot matplotlib, bukan margin PDF), jadi tidak ada ruang yang bisa dipanen dari sana.
- [2026-07-22] **Solusi yang dipilih user: halaman sampul terpisah.** Aturan lomba menyatakan 5 halaman "tidak termasuk cover page", sehingga judul, penulis, afiliasi, dan abstrak dipindah ke halaman sampul tak bernomor; badan teks mulai halaman bernomor 1. Ini membebaskan ~32 baris. Catatan risiko: contoh pemenang 2025 menaruh judul dan abstrak di halaman 1 (tapi itu laporan final 12-13 halaman, bukan concept paper 5 halaman, jadi tidak sebanding).
- [2026-07-22] **Format NeurIPS 2015 diverifikasi langsung dari `referensi/nips2015.pdf`, bukan dari ingatan.** Konvensi yang dikonfirmasi dan diterapkan: dua garis horizontal mengapit judul (tebal di atas, tipis di bawah), abstrak menjorok 1/2 inci di kedua sisi (`\dimexpr\textwidth-1in`), heading "Abstrak" bold 12pt terpusat, dan **paragraf tanpa indentasi dengan spasi vertikal antar paragraf**. `\parindent` disetel 0 dan `\parskip` 0,3em; nilai 0,45em dan 0,35em sempat dicoba tapi membuat teks meluber.
- [2026-07-22] Gambar diperkecil ke `0.96\textwidth` sebagai penghematan terakhir.
- [2026-07-22] **Referensi dipindah ke halaman sendiri** lewat `\newpage` sebelum `thebibliography` (atas permintaan user). Struktur akhir: 1 lembar sampul + halaman 1-5 badan teks + halaman 6 referensi = 7 lembar. Seluruh 14 referensi muat dalam satu halaman. **Efek samping: sekarang ada ~9 baris ruang kosong di bawah Bagian 5 pada halaman 5** yang bisa dipakai kalau mau menambah konten (kandidat terkuat: tabel kriteria go/no-go studi jembatan).
- [2026-07-22] ⚠️ **Sandbox Linux tidak punya paket LaTeX bahasa Indonesia** (`bahasai.ldf` dan pola hyphenation `hyph-id` tidak ada, dan apt/CTAN diblokir). Verifikasi tata letak memakai stub `bahasa.ldf` di `/tmp/texstub` dengan pola hyphenation Inggris. **Ini justru estimasi konservatif**: pola Inggris memberi lebih sedikit peluang pemenggalan sehingga barisnya lebih longgar, jadi kalau muat di sini pasti muat di Tectonic. Seluruh 9 pemenggalan kata pada PDF final sudah dicek manual dan semuanya jatuh di batas suku kata Indonesia yang benar (aug-, di-, dikelom-, instru-, me-, men-, mener-, pener-, peren-).
- [2026-07-22] **`recompute_metrics.py` dan `recompute_protokol.py` ditambahkan** sebagai jalur reproduksi `poc_hasil.json` di luar notebook. Dipisah dua berkas karena augmentasi 3.282 sampel mahal; skrip protokol memakai `ProcessPoolExecutor` dan cache `.cache_augmented.npz` (cache dihapus setelah selesai). ⚠️ Proses background di sandbox **mati saat panggilan bash berakhir** kecuali dijalankan dengan `setsid nohup ... < /dev/null &`.
- [2026-07-22] **Folder `paper/` dirapikan atas permintaan user: hanya berisi `Rizzz_ConceptPaper.pdf`.** Seluruh berkas kerja LaTeX pindah ke `paper/sumber/`. ⚠️ **Konsekuensi yang harus diingat: path gambar di `.tex` berubah dari `../figs/` menjadi `../../figs/`.** Kompilasi harus dijalankan dari dalam `paper/sumber/`, lalu hasilnya disalin manual ke `paper/Rizzz_ConceptPaper.pdf`. Sudah diuji ulang dari lokasi baru: 0 error, 0 overfull, 0 sitasi `[?]`, tetap 7 lembar.
- [2026-07-22] **Sisa koreksi di sel kesimpulan POC notebook (Bagian 8).** Poin lama "Augmentasi sebelum split menjadi sumber utama penggelembungan; identitas anak menjelaskan bagian besar variasi antar-citra" salah pada kedua bagiannya dan sudah diganti dengan dekomposisi 0,019/0,048/-0,005. Ditambah poin baru soal unit metrik (0,775 rekaman vs 0,834 anak) dan nested CV. Baris tabel limitasi "Spesifisitas rendah" diperbarui ke angka level anak (57,1% pada sensitivitas 92,3%, PPV 2,1% pada prevalensi 1%). Sel 35 (PCA) sengaja **tidak** diubah: kalimat "model tinggal mengenali anaknya, bukan kondisinya" di sana adalah pernyataan tentang apa yang dimungkinkan kebocoran, bukan klaim dekomposisi varians, jadi tetap benar.
- [2026-07-22] **Notebook ditambah 2 sel (sekarang 71 sel)** tepat setelah sel hasil utama: markdown penjelasan unit keputusan, dan sel kode `to_participant_level` + titik kerja level anak + nested GroupKFold. Sel 46 (dekomposisi protokol), sel 38 (varians antarpartisipan), sel 39, 43, 44, dan 48 diperbaiki narasinya. Seluruh 71 sel lolos `compile()`.

- [2026-07-21] **Audit rubrik final `paper/Rizzz_ConceptPaper.pdf`: estimasi konservatif 48,0/60 (80/100 pada komponen concept paper).** Rincian: Impact 21,5/25; Technical Quality 11,5/15; Originality 7,5/10; Scalability 5,3/7,5; Report Structure 2,2/2,5. Ini estimasi karena TM hanya memberi bobot, bukan anchor skor terperinci.
- [2026-07-21] **Risiko penilaian terbesar adalah jembatan eye-tracker laboratorium -> kamera tablet pada balita.** Paper sudah mengakuinya, tetapi belum memberi baseline/literatur webcam gaze, spesifikasi galat estimasi yang dapat ditoleransi, kriteria lolos studi jembatan, atau mitigasi gerakan kepala/kalibrasi/pencahayaan. Ini membatasi Technical Quality dan Production Readiness.
- [2026-07-21] **Trade-off skrining perlu dibuat lebih konkret:** POC memiliki sensitivitas 90,4% pada spesifisitas 34,8%; pada prevalensi 1% PPV hanya sekitar 1,4% (sekitar 72 rujukan per kasus benar), dan pada prevalensi 2% PPV sekitar 2,7% (sekitar 37 rujukan per kasus benar). Paper mengakui beban rujukan, tetapi angka eksplisit atau target go/no-go diperlukan agar dampak operasional dapat dinilai.
- [2026-07-21] **Celah revisi bernilai tinggi lainnya:** referensi [3], [5]-[7], [10]-[11] tidak lengkap; beberapa statistik Indonesia tidak ditempeli sumber secara langsung; Tabel 1 menyebut biaya TATAP “sangat rendah” tanpa BOM/biaya per tes; belum ada throughput, kebutuhan pelatihan, jalur regulasi, monitoring drift, atau target tahap pilot; Gambar 2 informatif tetapi labelnya relatif kecil.
- [2026-07-21] **Koreksi skor setelah audit literatur primer: estimasi konservatif turun menjadi 45,5/60 (75,8/100).** Ada pembanding sangat dekat yang tidak dibahas: SenseToKnow memakai kamera depan tablet/smartphone untuk skrining balita di layanan primer. Studi prospektif 475 balita melaporkan AUC 0,90, sensitivitas 87,8%, spesifisitas 80,8%, PPV 40,6%; studi lanjutan remote pada 620 balita melaporkan AUC 0,92. Rincian skor revisi: Impact 20,5/25; Technical Quality 10,8/15; Originality 6,2/10; Scalability 5,8/7,5; Structure 2,2/2,5. Gap analysis dan klaim orisinalitas wajib direposisi ke deployment Posyandu Indonesia, offline/on-device, interpretabilitas, dan evaluasi group-aware—bukan kamera tablet untuk gaze screening itu sendiri.
- [2026-07-21] **Framing M-CHAT perlu diseimbangkan:** sumber [3] memang melaporkan sensitivitas 49,2%, spesifisitas 94,2%, dan PPV ASD 28,9%, tetapi juga menyatakan PPV 90,6% untuk mendeteksi ASD atau gangguan perkembangan/perilaku lain. Menyebut mayoritas hasil positif sebagai “rujukan berlebih” tanpa nuansa ini rentan dianggap cherry-picking; posisi yang lebih defensibel adalah TATAP sebagai pelengkap M-CHAT, bukan pengganti.
- [2026-07-21] **Inkonsistensi angka yang harus diperbaiki sebelum submit:** Bagian 3.5 dan abstrak melaporkan ROC-AUC 0,775, tetapi Gambar 2c menampilkan protokol D (tanpa augmentasi + group partisipan) sebesar 0,753 dan caption berkata “seluruh angka yang kami laporkan memakai D”. Jika 0,775 berasal dari pemilihan model/nested CV yang berbeda, konfigurasi itu harus dijelaskan; jika tidak, samakan angka teks, gambar, dan caption.
- [2026-07-21] **Kalibrasi ulang sebagai concept paper:** audit awal terlalu menuntut bukti deployment/pilot. Rubrik hanya meminta rencana pengembangan dan skalabilitas, sehingga unit economics rinci, throughput terukur, monitoring drift, dan bukti operasional adalah penguat opsional, bukan kekurangan fatal. Estimasi wajar direvisi naik menjadi **48,2/60 (80,3/100)**: Impact 21,5/25; Technical Quality 11,8/15; Originality 6,2/10; Scalability 6,5/7,5; Structure 2,2/2,5. Temuan yang tetap wajib dibenahi meski paper bersifat konsep: inkonsistensi AUC 0,775 vs 0,753, pembanding SenseToKnow yang sangat dekat, dan kelengkapan sitasi.
- [2026-07-21] **Revisi audit selesai diterapkan ke `paper/sumber/concept_paper.tex` dan `paper/Rizzz_ConceptPaper.pdf`.** SenseToKnow kini dibahas sebagai pembanding digital terdekat (475 balita, AUC 0,90, sensitivitas 87,8%, spesifisitas 80,8%) dan menggantikan ADOS-2 pada Tabel 1. Kebaruan TATAP direposisi secara eksplisit pada operasi kader Posyandu, luring, stimulus Indonesia, model gaze satu modalitas, dan laporan geometri scanpath.
- [2026-07-21] **Konflik AUC sudah dijelaskan tanpa mengubah hasil:** AUC 0,775 (CI 0,683--0,858) berasal dari Naive Bayes terbaik di antara lima model; panel protokol A--D memakai regresi logistik tetap untuk mengisolasi pengaruh evaluasi, sehingga D = 0,753 dan A = 0,816. Teks dan caption Gambar 2 sekarang membedakan kedua eksperimen tersebut.
- [2026-07-21] **Framing M-CHAT diseimbangkan:** TATAP diposisikan sebagai pelengkap ceklis, bukan pengganti. Paper mengakui bahwa PPV ASD rendah tidak berarti semua hasil positif sia-sia karena sebagian anak memiliki hambatan perkembangan lain.
- [2026-07-21] **Sitasi diperbaiki dan diperkuat:** referensi M-CHAT 2026 kini memuat penulis+DOI; studi Pontianak dikoreksi dari 2019 menjadi 2023 dengan penulis, volume, halaman, DOI; studi Jakarta dikoreksi menjadi 2021 dengan penulis, volume, halaman, DOI; jumlah Posyandu/kader mendapat sitasi Kemenko PMK; sumber SDIDTK diganti ke artikel Mardhika dkk. 2022; EarliPoint memakai nomor FDA K213882/K230337; SenseToKnow ditambahkan sebagai Perochon dkk. 2023.
- [2026-07-21] **Verifikasi PDF final:** kompilasi Tectonic exit 0; `Rizzz_ConceptPaper.pdf` berisi 6 halaman dengan isi utama berakhir di halaman 5 dan `Referensi` mulai halaman 6; tidak ada sitasi `[?]`, overfull box, teks terpotong, tabel meluber, atau cacat render pada inspeksi PNG seluruh halaman. Metadata Title/Author/Subject/Keywords terisi; Creator dan Producer dikosongkan.
- [2026-07-21] **BRAINSTORMING MULTIMODAL -- BELUM KEPUTUSAN FINAL:** sedang dipertimbangkan arsitektur beberapa model unimodal terpisah untuk gaze, gerak kepala/wajah, dan vokalisasi. Hipotesis sementara: dataset eye-tracking tetap menjadi bukti empiris utama, sedangkan dataset multimodal sintetis paling aman hanya untuk smoke test integrasi tanpa metrik performa. Alternatif yang sedang dipikirkan adalah memosisikan multimodal sebagai arsitektur prospektif yang baru divalidasi setelah tersedia data nyata.
- [2026-07-21] **BRAINSTORMING LATE FUSION -- BELUM KEPUTUSAN FINAL:** secara teori model unimodal boleh dilatih pada kohort berbeda dan probabilitasnya digabung untuk anak baru yang sama. Namun rata-rata probabilitas baru dapat diklaim valid setelah setiap model dikalibrasi serta fusion diuji pada set berpasangan yang memuat seluruh modalitas dari anak yang sama. Tanpa set berpasangan, skala probabilitas, definisi label, perbedaan usia/perangkat, korelasi error, dan manfaat fusion belum dapat diestimasi. Dataset sintetis yang ada juga belum layak dianggap komponen prediktif karena tidak menunjukkan sinyal label. Seluruh poin ini masih bahan diskusi, bukan arah implementasi yang disepakati.
- [2026-07-21] **Brainstorming multimodal/late fusion pada dua entry di atas kini ditutup oleh keputusan final.** Implementasi ada di `late_fusion.py`: weighted mean nonnegatif, quality-aware renormalization untuk modalitas hilang, dan optimasi bobot simplex dengan log loss. `test_late_fusion.py` memverifikasi 4 skenario dan seluruhnya lulus. Kode menerima probabilitas yang sudah dikalibrasi; kalibrasi model per modalitas tetap bagian pipeline pelatihan prospektif.
- [2026-07-21] **Paper multimodal selesai diverifikasi:** judul, abstrak, gap analysis, arsitektur, rencana data, pemodelan, skalabilitas, etika, dan kesimpulan telah konsisten dengan late fusion. `figs/arsitektur.pdf` dibuat ulang dari `figs/generate_arsitektur.py`. PDF submit tetap 6 halaman: isi utama selesai di halaman 5 dan `Referensi` mulai halaman 6; tidak ada overfull/undefined warning dan inspeksi PNG seluruh halaman tidak menemukan teks terpotong atau tumpang tindih. Metadata Creator/Producer dikosongkan.
- [2026-07-21] **Notebook diselaraskan dengan PDF multimodal:** `poc_eyetracking.ipynb` kini 69 sel dan judul/tujuan membedakan POC empiris gaze-only dari arsitektur produk multimodal. Bagian 9 menambahkan kontrak tiga model unimodal, audit dataset sintetis, quality-aware weighted late fusion, smoke test modalitas hilang, dan protokol validasi prospektif berpasangan. Tiga sel kode baru dieksekusi terisolasi tanpa error (execution count 35--37); smoke test ditandai eksplisit bukan metrik performa.
- [2026-07-21] **Klaim kurva belajar notebook dikoreksi:** kalimat lama "masih menanjak/belum jenuh" dan ekstrapolasi logaritmik dihapus karena kemiringan paruh akhir = -0,0238 dan set uji mengecil. Source sekarang menyatakan data belum menentukan batas atas performa. Sel visualisasi dieksekusi ulang dari tabel `lc` yang tersimpan (10 ukuran partisipan), sehingga output grafik dan narasi baru konsisten tanpa mengubah angka.
- [2026-07-21] Percobaan Run All agent mencapai sel 46/69 lalu dihentikan batas proses sekitar satu menit, bukan error notebook. Tiga sel multimodal dan sel kurva belajar kemudian dieksekusi lewat notebook mini dengan state eksplisit tanpa error; Run All penuh tetap menjadi tindakan lokal berikutnya untuk konfirmasi end-to-end dalam satu kernel bersih.

- [2026-07-21] `referensi/Datathon TM Preliminary UNI.pdf` adalah PDF berbasis gambar — ekstraksi teks (pdfplumber/pdftotext) menghasilkan kosong. Harus render halaman ke PNG lalu dibaca secara visual.
- [2026-07-21] Rubrik menempatkan **Impact di 25%**, jauh di atas Solution Technical Quality (15%). Argumen masalah harus jadi porsi terkuat paper, bukan kompleksitas model.
- [2026-07-21] Report Structure hanya 2.5% — jangan overinvest di polesan format, tapi tetap patuhi template NeurIPS & batas 5 halaman.
- [2026-07-21] Filename mismatch di Multimodal Autism Dataset: index CSV/JSON menyebut `images/child_XXX.png`, file aslinya `Child (N).jpg`. Perlu mapping sebelum loading data.
- [2026-07-21] Semua pemenang 2025 mengusung produk AI **multimodal** dengan branding produk (TracKO, ChickSense, Influensure, BantuBalik.in) dan domain masalah yang sangat spesifik — pola yang layak ditiru.

### Verifikasi dataset (2026-07-21)

- [2026-07-21] **Multimodal Autism Dataset terbukti sintetis / noise acak.** Diuji 100 sampel, agregasi fitur per label:
  - `motion.head` std = 0.100 di **keempat** kelas (uniform noise ±0.25); semua sampel 300 frame / 30 fps / 10 s.
  - `physio` HR rata-rata 89.99 / 90.01 / 90.02 / 90.04; GSR 2.189–2.191; TEMP 37.030 — identik lintas kelas.
  - `voice` RMS 0.3674–0.3677, durasi 2.0001 s, ZCR 0.079 — identik lintas kelas.
  - Flag `stimming_detected` tidak berkorelasi label (`moderate_asd` justru 3/19 = paling rendah, `typical` 8/25 = tinggi).
  - **Kesimpulan:** tidak ada sinyal yang bisa dipelajari. Model apa pun ≈ tebakan acak. Kalau dipakai untuk klaim akurasi di paper, hasilnya tidak reprodusibel dan berisiko dianggap tidak kredibel oleh juri.
  - Catatan: `images/` sendiri kemungkinan foto wajah asli (ukuran & kompresi bervariasi, khas hasil scraping), tapi karena mismatch filename, pemetaan gambar→label bersifat arbitrer → label gambar pun tidak dapat dipercaya.
- [2026-07-21] **Eye-tracking dataset punya sinyal nyata dan kuat.** Baseline cepat: 11 fitur global sederhana (fraksi piksel ber-"tinta", mean RGB, centroid x/y, sebaran x/y, span x/y) + regresi logistik →
  - **GroupKFold per partisipan, ROC-AUC = 0.786 ± 0.097** (fold: 0.61 / 0.80 / 0.82 / 0.91 / 0.79).
  - Random split (bocor) = 0.793 — mirip, artinya kebocoran belum parah di fitur global, tapi akan parah untuk CNN.
  - Arah pemisah konsisten dengan literatur ASD: scanpath ASD **lebih tersebar & lebih panjang** — `span_x` 0.59 vs 0.48, `span_y` 0.56 vs 0.39, fraksi tinta 0.031 vs 0.015 (ASD vs TD).
  - Implikasi: fitur geometri scanpath (dispersi, panjang lintasan, durasi/klaster fiksasi) sudah cukup informatif → cocok untuk argumen produk yang *interpretable*, bukan black-box.
### Kalibrasi dari paper pemenang 2025 (dibaca penuh 2026-07-21)

- [2026-07-21] **Struktur yang dipakai kedua pemenang identik:** Abstract → Pendahuluan (latar belakang + manfaat/kontribusi + batasan) → Kajian Teori → Solusi Usulan (arsitektur + modul per modul + strategi deployment) → Hasil Eksperimen → Analisis/Pembahasan → Kesimpulan & Saran → References. Ditulis dalam **Bahasa Indonesia**, template NeurIPS.
- [2026-07-21] ⚠️ **Kedua paper 12–13 halaman**, jauh di atas batas 5 halaman tahun ini. Jadi mereka adalah patokan **kualitas**, bukan patokan panjang. Konsekuensi: kita harus jauh lebih padat — kemungkinan besar tabel hasil + 1 gambar arsitektur, tanpa narasi bertele-tele.
- [2026-07-21] **Pemenang menjalankan eksperimen nyata, bukan sekadar proposal.** Olip: YOLOv11-seg precision 0.9473 / recall 0.7337, TimeSFormer akurasi 75.0% setelah domain adaptation. Blekping: YOLOv11s mAP50 0.976, CNN audio akurasi uji 90%. → **Concept paper kita wajib punya angka hasil eksperimen sendiri**, bukan hanya rancangan.
- [2026-07-21] **Pola bagian Impact (Blekping) = tumpukan angka rupiah & prevalensi konkret:** kerugian ND Rp 474.500.000 per farm/6 bulan, prevalensi 36,80%, mortalitas ND s.d. 100% dan CRD 30%, kerugian CRD Rp 342.114/bulan = −32,52% profit. Sitasi ke jurnal & BPS/Kementan. Inilah cara mengunci Impact 25%.
- [2026-07-21] **Celah kualitas pemenang yang bisa kita lampaui** (peluang diferensiasi):
  - Blekping: section 3.4 **copy-paste persis** dari 3.3; angka dataset kontradiktif (klaim 349 gambar / 314 train, lalu di analisis ditulis "dataset pelatihan yang hanya terdiri dari 24 gambar"); mengutip "akurasi hingga 100%" tanpa sikap kritis; integrasi multimodal diakui sendiri "belum diuji secara sistematis".
  - Olip: evaluasi akhir hanya pada **satu klip CCTV 20 detik** (n=1) — kesimpulan bisnis dibangun di atas sampel sangat kecil.
  - Keduanya: **tidak ada group-aware split, tidak ada confidence interval, tidak ada baseline pembanding.**
  - → Paper dengan metodologi jujur & rigor (GroupKFold per partisipan, CI, baseline, limitasi eksplisit) punya ruang menang di Technical Quality 15%, karena bar-nya ternyata tidak setinggi yang dikira.
- [2026-07-21] Keduanya memberi **nama produk & branding** (TracKO, ChickSense) dan menutup dengan bagian saran/roadmap konkret — bukan "bisa dikembangkan lebih lanjut" generik.

### Riset Impact (2026-07-21) — detail lengkap di `docs/riset_impact.md`

- [2026-07-21] **Rantai argumen Impact sudah terkunci dan semuanya bersumber:** (1) intervensi dini terbukti berdampak besar — ESDM RCT: **+17,6 poin IQ** vs +7,0 kelompok pembanding, manfaat terbesar pada anak <30 bulan; (2) tapi usia rata-rata diagnosis **55,97 bulan** sementara keresahan orang tua muncul di **23,64 bulan** → **jeda 32,33 bulan terbuang**; (3) di negara LMIC **40%** baru terdiagnosis usia ≥10 tahun vs 15% di negara maju; (4) instrumen skrining lini pertama bocor — **sensitivitas M-CHAT hanya 49,2%** di layanan primer, PPV 0,29–0,36; (5) alat objektif yang tervalidasi (EarliPoint, FDA-cleared) harganya **US$599 out-of-pocket** dan hanya di klinik.
- [2026-07-21] **Indonesia tidak punya data prevalensi ASD nasional.** Angka 2,4 juta anak adalah **ekstrapolasi prevalensi Hong Kong**, dan estimasi nasional terakhir (1:833) berumur 22 tahun. → Ini bisa dijadikan **klaim kontribusi kedua produk**: skrining terstandar di Posyandu sekaligus menutup celah surveilans nasional.
- [2026-07-21] ⚠️ Klaim populer "penderita autisme Indonesia bertambah 500 orang/tahun" **tidak masuk akal epidemiologis** untuk populasi sebesar Indonesia — kemungkinan itu jumlah kasus terlayani, bukan insidensi. **Jangan dipakai di paper.**
- [2026-07-21] **Basis Scalability sudah kuat:** Indonesia punya **338.881 Posyandu** dan **1.059.466 kader aktif**; SDIDTK sudah jadi program pokok Puskesmas. Tapi studi lapangan konsisten menemukan pelaksanaannya **tidak lengkap** (praktiknya hanya timbang & ukur tinggi) dan kader **belum mampu** deteksi dini komprehensif; cakupan Jatim 54,8% vs target 90%. → Jalur distribusi sudah ada, **kapasitas deteksi yang jadi bottleneck** — persis yang diserang produk kita.
- [2026-07-21] **Positioning vs EarliPoint sudah jelas dan jujur:** EarliPoint (FDA-cleared, 16–30 bln, Tobii) justru **menguatkan premis kita** bahwa sinyal gaze valid secara klinis dan diterima regulator. Klaim kita **bukan lebih akurat**, tapi **menjangkau populasi yang tidak akan pernah disentuh EarliPoint** (US$599 ≈ Rp 9–10 juta/pemeriksaan, butuh hardware khusus).
- [2026-07-21] ✅ **PDF Carette dkk. (BIOSTEC/HEALTHINF 2019, DOI 10.5220/0007402601030112) sudah dibaca penuh. Dugaan kebocoran TERKONFIRMASI — bahkan lebih parah dari dugaan awal:**
  1. **Augmentasi dilakukan SEBELUM cross-validation.** Mereka menambah 2.735 sampel sintetis (5 citra per citra asli), lalu menjalankan "10 rounds of cross-validation". Artinya **salinan augmentasi dari citra yang sama masuk ke train dan test sekaligus** — ini kebocoran berat dan sendirian sudah cukup menggelembungkan akurasi.
  2. **Tidak ada satu pun penyebutan grouping per partisipan.** Split-nya per-citra, padahal 547 citra hanya berasal dari 59 partisipan.
  3. **Angka mereka sendiri mendukung tesis kita:** model non-neural (Naive Bayes, Logistic Regression, SVM, Random Forest) hanya mencapai **AUC ≈ 0,7**; baru model neural yang tembus >0,9. Baseline jujur kita (**AUC 0,786 GroupKFold**) justru **konsisten dengan angka non-neural mereka** — ini bukti kuat bahwa lompatan ke >0,9 itu artefak metodologis, bukan kemampuan model.
  - → **Boleh diklaim di paper sebagai kontribusi metodologis.** Framing: bukan menyerang penulisnya, tapi menegaskan bahwa evaluasi group-aware itu wajib untuk klaim kelayakan klinis.
- [2026-07-21] 🔴 **LIMITASI KRITIS yang wajib ditulis jujur di paper: partisipan Carette rata-rata berusia 7,88 tahun (median 8,1) — anak usia sekolah, BUKAN balita.** Produk kita menyasar skrining dini (idealnya <30 bulan, mengikuti jendela ESDM). Jadi dataset ini **memvalidasi prinsip bahwa geometri scanpath diskriminatif**, bukan memvalidasi performa pada balita. Jangan pernah mengklaim POC ini membuktikan skrining pada balita. Ini asumsi transfer yang harus dinyatakan eksplisit.
- [2026-07-21] **Skema warna citra scanpath (dari paper) — penting untuk feature engineering yang interpretable:** kanal **R = kecepatan (velocity)**, **G = akselerasi**, **B = jerk**; **fiksasi = cyan** (velocity rendah, akselerasi & jerk tinggi), **sakade = kuning/putih** (velocity tinggi; putih = melebihi cap). Nilai di-cap pada seperempat panjang diagonal layar. Citra **dicerminkan vertikal** (origin di bawah). Threshold 200 titik per citra. → Fitur per kanal warna punya makna fisik langsung, bukan sekadar statistik piksel.
- [2026-07-21] ⚠️ **Potensi confound yang disebut penulisnya sendiri:** partisipan ASD cenderung melihat ke **bagian bawah layar, tempat perangkat eye-tracker diletakkan**. Jadi fitur "bias vertikal ke bawah" bisa jadi artefak setup, bukan sinyal perilaku ASD murni. Kalau fitur ini muncul penting di model kita, **harus dibahas sebagai limitasi**, bukan dirayakan sebagai temuan.
  - Detail protokol lain: stimulus video ±5 menit, eye-tracker SMI Red-m 250Hz, monitor 17" 1280×1024, jarak ±60 cm, kalibrasi 5 titik, bahasa Prancis.

### POC notebook (2026-07-21)

- [2026-07-21] `poc_eyetracking.ipynb` dibangun & lolos smoke test end-to-end. **Dijalankan oleh user, bukan agent** — sandbox agent membatasi proses 45 detik, sementara notebook butuh ±3–5 menit.
- [2026-07-21] **Angka smoke test (parameter dikecilkan, JANGAN dipakai di paper):** 19 fitur, model terbaik Naive Bayes, AUC group-aware **0,775** (CI 95% 0,694–0,854), sensitivitas 90,4% pada spesifisitas 34,8%, fitur teratas `ink_frac` > `span_x` > `span_y` > `std_y` > `radial_std`. Kurva belajar 0,691 (8 partisipan) → 0,763 (44 partisipan).
- [2026-07-21] ⚠️ **Koreksi penting terhadap narasi awal:** penggelembungan akibat split per-citra saja ternyata hanya **+0,044 AUC** — moderat, bukan dramatis. Alasannya fitur kita global/kasar sehingga tidak menyediakan sidik jari unik per anak. **Jangan melebih-lebihkan angka ini di paper.**
  - Karena itu notebook ditambah **replikasi protokol Carette** (augmentasi 5× sebelum split) dengan 4 protokol pembanding: A (augmentasi + split acak, ala literatur), B (augmentasi + group per citra sumber), C (augmentasi + group per partisipan), D (tanpa augmentasi + group per partisipan = angka kita). Ini memisahkan berapa kebocoran yang berasal dari augmentasi vs dari tidak-grouping. **Angka final menunggu user menjalankan notebook.**
- [2026-07-21] ⚠️ **Spesifisitas hanya ~35% pada sensitivitas 90%.** Ini lemah dan harus ditulis jujur. Implikasi produk: pada prevalensi lapangan yang jauh lebih rendah, PPV akan anjlok → beban rujukan besar. Ini justru memperkuat argumen bahwa POC ini bukti *premis*, bukan bukti *kesiapan*.
- [2026-07-21] **Notebook diperluas dengan 8 blok EDA bervisualisasi** (62 sel: 34 kode + 28 markdown). Struktur: 0 Lingkungan → 1 Dataset+komposisi → 2 Ekstraksi fitur → 3 EDA → 4 Kebocoran → 5 Hasil → 6 Kurva belajar → 7 Interpretabilitas → 8 Kesimpulan.
- [2026-07-21] 🔑 **Temuan EDA paling penting untuk paper — "sidik jari" partisipan terkuantifikasi:** rata-rata **38,2% varians antar-citra berasal dari identitas anak**, bukan dari kondisinya (`ink_frac` tertinggi: 63,8%). Ini **pembenaran kuantitatif** kenapa evaluasi wajib group-aware — jauh lebih kuat daripada sekadar argumen naratif. Divisualkan lewat PCA panel-b (titik tiap anak menggerombol rapat).
- [2026-07-21] Temuan EDA lain: PC1+PC2 menjelaskan 63,7% varians. Pasangan fitur sangat berkorelasi (|r|>0,85): `n_active_cells`–`grid_entropy` 0,93; `jerk_mean`–`acc_mean` 0,93; `fixation_ratio`–`saccade_ratio` −0,92; `span_x`–`std_x` 0,90; `span_y`–`std_y` 0,90. → 19 fitur sebenarnya mengukur ~5–6 dimensi independen; layak disebut di paper sebagai ruang penyederhanaan.
- [2026-07-21] Penggelembungan per model (split per-citra vs per-partisipan): SVM +0,072, LogReg +0,060, RF +0,041, GB +0,030, NB +0,017. **Model paling kompleks paling rentan bocor** — pola yang mendukung argumen memilih model sederhana.
- [2026-07-21] `.vscode/settings.json` + `extensions.json` dibuat supaya interpreter `.venv` terdeteksi otomatis; folder dataset besar di-exclude dari file watcher & search.
- [2026-07-21] Keputusan desain POC: **sengaja tidak memakai CNN**. Alasan: (a) interpretabilitas untuk adopsi klinis, (b) bisa jalan di tablet murah tanpa GPU, (c) dengan 54 partisipan, CNN hampir pasti menghafal. Fitur dibuat punya makna fisik langsung dari pemetaan kanal warna (R=velocity, G=akselerasi, B=jerk).

- [2026-07-21] **Risiko metodologis eye-tracking:** kelas tidak seimbang (328 TD vs 219 ASD), dan gambar hasil render — bukan data gaze mentah (x, y, t). Fitur temporal murni (kecepatan saccade, durasi fiksasi) hanya bisa diaproksimasi dari geometri gambar. Perlu disebut jujur sebagai limitasi di paper.

---

## 7. Milestone Log

*(pencapaian tahap besar)*

- [2026-07-22] Revisi putaran keempat selesai: abstrak dipindah ke badan teks setelah konfirmasi panitia, Gambar 1 diregenerasi dengan quality gate per cabang dan tata letak otomatis, mockup produk (Lampiran F) dan rincian POC (Lampiran G) ditambahkan, delapan item audit eksternal ketiga diterapkan, dan notebook diselaraskan tanpa mengubah angka. PDF submit 10 lembar dengan badan teks tetap 5 halaman, 0 overfull, 0 sitasi tak terselesaikan.
- [2026-07-22] Revisi putaran ketiga selesai: endpoint utama pindah ke unit anak dengan model pra-tetap, target usia 16-30 bulan dikunci, protokol stimulus panggilan nama ditambahkan, klaim penggelembungan dipersempit, rantai kamera ke pandangan digambar eksplisit, dan Lampiran A-E dibuat. PDF submit 9 lembar dengan badan teks tetap 5 halaman, 0 overfull, 0 sitasi tak terselesaikan.
- [2026-07-21] `docs/penjelasan_lomba.md` dibuat — aturan, struktur wajib, dan rubrik AI Product Concept Paper terangkum dari TM deck.
- [2026-07-21] Revisi final concept paper selesai: pembanding state-of-the-art, positioning originality, konsistensi eksperimen, rencana studi jembatan, dan bibliografi diperbaiki; PDF submit diverifikasi tetap memenuhi batas 5 halaman isi.
- [2026-07-21] Arsitektur multimodal weighted late fusion diimplementasikan pada paper, diagram, dan modul Python teruji; klaim performa tetap dibatasi pada POC pandangan sampai tersedia kohort berpasangan.
- [2026-07-21] Notebook POC dan `poc_hasil.json` diselaraskan dengan paper multimodal; metadata hasil kini mencatat `evidence_scope=gaze_only` dan `fusion_status=prospective_paired_validation_required`.
- [2026-07-21] `AGENTS.md` dibuat sebagai memori lintas sesi.
- [2026-07-21] Audit kedua dataset selesai (struktur, sumber, label, baseline sanity-check). Multimodal ditolak sebagai sumber bukti; eye-tracking ditetapkan sebagai anchor teknis dengan baseline AUC 0.786 (GroupKFold per partisipan).
- [2026-07-30] **Penataan ulang berkas.** Dokumen kerja pindah ke `docs/`, bahan mentah pihak lain pindah ke `referensi/`. `.gitignore` ditambahkan (cache Python, `.DS_Store`, artefak LaTeX). Berkas kosong `malfa_multiplemodel` dihapus, `concept_paper.aux`/`.out` di-untrack (tetap ada di disk supaya sitasi tidak perlu kompilasi ulang). Skrip, notebook, `figs/`, dan kedua folder dataset sengaja **tidak** dipindah karena saling terikat lewat cwd, `Path(__file__).parent`, dan `../../figs/` di `.tex`. Semua rujukan path di `AGENTS.md` dan `docs/penjelasan_lomba.md` sudah disesuaikan, termasuk dua rujukan lama `paper/concept_paper.tex` yang sebenarnya ada di `paper/sumber/`. Diverifikasi: `pytest` 4 lulus, ketiga modul Python meng-import bersih, `DATA_DIR` tetap ketemu.
