# Rencana Semifinal — TATAP

**Periode:** 30 Juli – 10 Agustus 2026 · **Deadline deliverable: 10 Agustus 2026**
**Kondisi:** dikerjakan sendiri, ~10 hari, platform web PWA in-browser.
**Sumber aturan:** `Datathon2026-TM_Semifinal.pdf` (TM Semifinal, University Track).

---

## 1. Tiga deliverable

| # | Deliverable | Ketentuan |
|---|---|---|
| 1 | **AI Product Proposal/Paper** | Versi final concept paper. NeurIPS 2015, struktur sama **+ section Results and Discussion**. **Maks 12 halaman**, PDF. Masalah & produk **wajib konsisten** dengan preliminary — TATAP tidak boleh diganti. |
| 2 | **Implementation** | Link repo GitHub berisi codebase penuh + README (setup & cara menjalankan). Bobot model & dataset **wajib di Hugging Face**, dikirim sebagai link terpisah. Repo boleh privat selama semifinal, **wajib publik setelah deadline**. |
| 3 | **Video Demo** | 3–5 menit. ≥1 menit sisi bisnis, ≥2 menit produk berjalan. Link unlisted YouTube / Google Drive. |

> Kalimat kunci panitia: *"Make sure the features claimed in your paper are actually present and testable."*
> Untuk video: *"Focus on demonstrating the product working, not on slide presentations or mockups."*

## 2. Rubrik dan implikasinya

| Kelompok | Kriteria | Bobot |
|---|---|---|
| Impact (45%) | Value Creation & Demonstrated Impact | 20% |
| | Adoption, Feasibility & Scalability | 10% |
| | Innovation & Meaningful Differentiation | 15% |
| Implementation (45%) | Functional Product & User Experience | 10% |
| | **AI Implementation & Technical Excellence** | **20%** |
| | Evaluation, Reliability & Responsible AI | 10% |
| | System Design, Engineering & Reproducibility | 5% |
| Demo (10%) | Product Demonstration & Presentability | 10% |

**Pergeseran dari preliminary:** Impact naik 25%→45%, dan sub-kriteria *Impact Evidence* sekarang secara eksplisit meminta bukti yang bisa dijalankan — usability testing, pilot results, quantitative comparisons. Argumen masalah saja tidak lagi cukup; harus ada angka dari sistem yang benar-benar berjalan.

**Bobot tunggal terbesar adalah AI Implementation & Technical Excellence (20%)**, yang menuntut penjelasan data pipeline, proses inferensi, trade-off, plus robustness/latency/edge case. Ini yang paling menentukan, dan kebetulan paling cocok dengan kekuatan proyek ini.

**Posisi TATAP relatif kuat di dua tempat:** Innovation (15%) sudah dijawab gap analysis yang ada, dan Responsible AI (bagian dari 10%) sudah dijawab framing triase-bukan-diagnosis, aturan abstain, dan quality gate — yang jarang dimiliki tim lain.

---

## 3. Risiko blocking — wajib dijawab Hari 1

### 3.1 Fitur tidak menerima input dari produknya sendiri

19 fitur di `recompute_metrics.py:49` diekstrak dari **gambar render-an Carette**, dan 4 di antaranya membaca kanal warna:

```python
f["vel_mean"], f["vel_std"] = r_i.mean(), r_i.std()
f["acc_mean"], f["jerk_mean"] = g_i.mean(), b_i.mean()
```

Ini mengasumsikan Carette meng-encode velocity/acceleration/jerk ke R/G/B dengan normalisasi tertentu — **asumsi yang belum diverifikasi**. Pipeline webcam menghasilkan `(x, y, t)`, bukan PNG ber-encoding itu.

**Jalan A** — render gaze webcam ke encoding Carette yang identik. Setia ke model lama, tapi kalau konstanta normalisasinya meleset, fitur keluar dari skala training dan model rusak **diam-diam tanpa error**. Risiko tinggi, sulit diverifikasi tanpa kode generator Carette.

**Jalan B (diutamakan)** — latih ulang tanpa 4 fitur turunan RGB, sisa **15 fitur geometri murni**. Menghasilkan model **device-agnostic**: jalan sama baiknya dari eye-tracker maupun webcam.

Alasan Jalan B kemungkinan besar menang: 4 dari 5 efek terbesar semuanya geometri, bukan warna —
`n_active_cells` d=1,685 · `ink_frac` d=1,500 · `span_y` d=1,478 · `grid_entropy` d=1,471.
Fitur warna tidak muncul sama sekali di daftar teratas.

**Aksi:** jalankan ablasi 15-fitur (±1 jam, pakai kode yang ada). Kalau AUC anak bertahan di ≥0,80, kunci Jalan B dan seluruh arsitektur mengikuti. Kalau anjlok, baru pertimbangkan Jalan A dengan verifikasi encoding.

### 3.2 Parameter rendering harus dikalibrasi

Fitur geometri (`ink_frac`, `n_active_cells`, `bbox_fill`) sensitif terhadap **lebar garis dan resolusi** raster. Scanpath webcam yang dirender harus memakai kanvas 640×480 dan lebar garis yang menghasilkan distribusi `ink_frac` sebanding dengan citra Carette. Ini dikalibrasi sekali, lalu dikunci sebagai konstanta produk.

---

## 4. Dua eksperimen yang mengisi Results and Discussion

Keduanya bisa dijalankan **tanpa data anak baru**, dan berpasangan membentuk argumen tertutup.

### 4.1 Studi degradasi domain (angka utama)

Rusak scanpath eye-tracker ke kualitas kamera tablet, lalu ukur ulang AUC level anak:

- noise gaze σ ∈ {0; 0,5; 1; 1,5; 2; 3}° sudut pandang
- laju sampling {120, 60, 30} Hz (eye-tracker → webcam)
- dropout tracking {0, 10, 20, 30}%
- jitter gerak kepala

**Keluaran:** kurva *AUC anak vs error gaze* → **anggaran presisi** yang harus dipenuhi webcam. Ini mengisi kriteria go/no-go Lampiran A dengan angka nyata, bukan janji.

### 4.2 Pengukuran presisi gaze webcam (angka pendamping)

Kalibrasi 9 titik di dalam app, lalu layar validasi mengukur error sendiri dalam derajat. Subjek dewasa (diri sendiri/teman) — tidak ada isu etis, dan **bukan** validasi klinis, murni pengukuran presisi instrumen.

**Kalimat Results yang dituju:** *"Kamera tablet mencapai error X°; studi degradasi menunjukkan AUC level anak bertahan di atas ambang sampai Y°; karena X < Y, premis pengukuran produk terpenuhi."*

Ini jawaban paling langsung untuk *Impact Evidence* dan *Reliability & Error Analysis* tanpa mengarang klaim klinis apa pun.

---

## 5. Ruang lingkup — apa yang dibangun dan apa yang tidak

Karena dikerjakan sendiri dalam 10 hari, cakupan dipangkas secara sadar dan **statusnya ditulis jujur di paper**.

| Cabang | Status implementasi | Alasan |
|---|---|---|
| **Pandangan** | **Penuh & hidup.** Kalibrasi, estimasi titik pandang, scanpath, 15 fitur, model terkalibrasi, skor. | Satu-satunya cabang yang punya bukti empiris. Ini inti produk. |
| **Kepala/wajah** | Sinyal + skor kualitas dihitung (pose kepala sudah gratis dari MediaPipe), **tanpa model terlatih**. | Tidak ada kohort berpasangan untuk melatih bobot. Paper sudah memposisikannya sebagai prospektif (garis putus-putus). |
| **Vokalisasi** | VAD + latensi respons nama dihitung, **tanpa model terlatih**. | Sama. Dataset multimodal yang ada terbukti noise acak. |

**Fusi:** `late_fusion.py` di-port ke JS dan benar-benar berjalan, dengan quality gate dan renormalisasi bobot. Default: bobot pandangan 1,0 (fusi satu cabang). Ada mode **"prospektif"** yang bisa dinyalakan, memakai bobot prior yang belum dikalibrasi dan **diberi label jelas di UI**. Dengan begitu jalur kode fusi ada dan bisa diuji juri, tanpa mengklaim yang tidak ada.

**Stimulus:** video adegan sosial 2 menit belum ada. Diganti **stimulus canvas** — animasi wajah vs objek non-sosial dengan koordinat AOI yang diketahui persis, plus 2 penanda panggil-nama. Ini justru lebih baik untuk sisi ilmiahnya karena ground truth AOI-nya eksak, dan jauh lebih murah dibuat sendiri.

**Mode replay wajib ada.** Juri harus bisa menguji produk tanpa webcam: sesi bawaan yang bisa diputar ulang lewat pipeline yang sama. Ini yang membuat klaim "testable" benar-benar terpenuhi.

---

## 6. Arsitektur repo

Direstrukturisasi 31 Juli 2026 menjadi repo mandiri (remote `Dataton_Project_Rizzz`). Artefak preliminary dibekukan di `poc/`, kode aktif di `research/`, produk akan masuk `app/`.

```
project/                         # git root
├── README.md · requirements.txt · pyproject.toml
├── data/                        # dataset mentah
├── app/                         # PWA (Vite + TypeScript) — belum dibuat
│   ├── src/capture/             # kamera, mic, QC perekaman
│   ├── src/gaze/                # MediaPipe FaceLandmarker → kalibrasi → titik pandang
│   ├── src/scanpath/            # render trace + ekstraksi 13 fitur (port JS)
│   ├── src/fusion/              # port JS late_fusion + quality gate + aturan abstain
│   ├── src/stimulus/            # stimulus canvas 2 menit + penanda panggil-nama
│   ├── src/report/              # layar laporan sesuai mockup Lampiran F
│   ├── src/replay/              # mode replay sesi bawaan
│   └── public/models/           # koefisien model + WASM MediaPipe (di-bundle, offline)
├── research/
│   ├── features.py              # ✅ extractor bersama, satu sumber kebenaran
│   ├── evaluate.py              # ✅ helper CV group-aware, bootstrap, titik kerja
│   ├── late_fusion.py           # ✅ fusion + quality gate
│   ├── 01_ablasi_fitur.ipynb    # ✅ selesai
│   ├── 02_training.ipynb        # ekspor model.json
│   ├── 03_degradasi.ipynb       # kurva AUC vs error gaze
│   └── hasil/                   # JSON hasil tiap notebook
├── poc/                         # artefak preliminary, beku
├── tests/
│   ├── test_late_fusion.py      # ✅ 4 lulus
│   ├── test_feature_parity.py   # golden vector Python vs JS
│   └── test_abstain.py          # aturan quality gate & abstain
└── paper/, figs/, docs/
```

**Model tidak perlu ONNX.** Regresi logistik hanyalah dot product — ekspor koefisien + parameter scaler + kalibrator ke `model.json`. Lebih ringan, lebih mudah diinspeksi juri, dan menghilangkan satu dependensi berat. MediaPipe WASM di-bundle lokal, bukan dari CDN, supaya klaim luring benar-benar berlaku.

**Hugging Face:** satu repo model berisi `model.json` + koefisien + kartu model (metrik, batasan, data latih), dan satu repo dataset berisi tabel 15 fitur turunan dari 547 citra + label + ID partisipan.

---

## 7. Jadwal 10 hari

| Hari | Tanggal | Target | Keluaran |
|---|---|---|---|
| **1** | 31 Jul | **De-risk.** Ablasi 15 fitur geometri → putuskan Jalan A/B. Kalibrasi parameter rendering. Scaffold repo. | Keputusan arsitektur terkunci |
| **2** | 1 Agu | `features.py` terima citra & deret. `train.py`: GroupKFold, kalibrasi inner-fold, ekspor `model.json`. Push ke HF. | Model + link HF |
| **3** | 2 Agu | **Studi degradasi.** Sweep noise/framerate/dropout → kurva AUC vs error. | `hasil_degradasi.json` + figur — **angka utama Results** |
| **4** | 3 Agu | App: scaffold PWA, MediaPipe WASM lokal, deteksi wajah, QC perekaman. | Kamera + QC jalan |
| **5** | 4 Agu | Kalibrasi 9 titik + estimasi titik pandang + layar validasi error. | **Angka presisi gaze (derajat)** |
| **6** | 5 Agu | Stimulus canvas 2 menit, render scanpath, port extractor JS + uji parity, skor. | Sesi menghasilkan skor |
| **7** | 6 Agu | Fusi + quality gate + abstain. Layar laporan (Lampiran F, dua varian). Mode replay. | **Produk utuh** |
| **8** | 7 Agu | Test suite, latency & ukuran model di tablet, edge case, README, rapikan repo. | Repo siap dinilai |
| **9** | 8 Agu | Paper: tambah Results and Discussion, naikkan Lampiran A/B/G ke badan teks dengan angka nyata, kompilasi 3×. | PDF 12 halaman |
| **10** | 9 Agu | Video demo: naskah, rekam di tablet Android, edit. | Link video |
| — | 10 Agu | Submit ketiga link. Set repo publik. | Selesai |

**Urutan ini tidak boleh ditukar:** angka harus jadi sebelum app (app memakai model), app harus jadi sebelum paper (Results butuh angka dari app), paper sebelum video (naskah video mengikuti klaim paper).

### Checkpoint keras — akhir Hari 5

Kalau estimasi titik pandang belum jalan pada akhir 4 Agustus, **langsung turun ke rencana cadangan**: produk berbasis unggah video, bukan kamera langsung. Pengguna mengunggah rekaman sesi → pipeline yang sama memproses → laporan keluar. Tetap memenuhi "working product", tetap bisa didemokan, dan menyelamatkan 4 hari terakhir untuk paper & video. Jangan bertaruh pada gaze langsung sampai Hari 7.

---

## 8. Pemetaan ke rubrik

| Kriteria | Bobot | Dijawab oleh |
|---|---|---|
| Value Creation & Demonstrated Impact | 20% | Studi degradasi + presisi webcam terukur (argumen tertutup), analisis PPV pada prevalensi nyata, argumen masalah yang sudah ada di paper |
| Adoption, Feasibility & Scalability | 10% | PWA di tablet kelas menengah bawah, inferensi luring, integrasi meja 4 Posyandu/SDIDTK, latency & ukuran model terukur |
| Innovation & Meaningful Differentiation | 15% | Gap analysis yang sudah ada, quality-aware late fusion dengan abstain, jembatan eye-tracker→webcam yang dikuantifikasi |
| Functional Product & UX | 10% | Alur sesi utuh, layar laporan bahasa kader, mode replay, penanganan sesi gagal |
| **AI Implementation & Technical Excellence** | **20%** | Model device-agnostic, GroupKFold per partisipan, kalibrasi inner-fold, uji parity Python↔JS, latency, edge case |
| Evaluation, Reliability & Responsible AI | 10% | Nested CV, CI bootstrap, kurva degradasi, aturan abstain, framing triase-bukan-diagnosis, batasan ditulis eksplisit |
| System Design, Eng & Reproducibility | 5% | README, test suite, skrip reproduksi angka, artefak di HF |
| Product Demonstration | 10% | Video di tablet Android asli, alur sesi nyata dari awal sampai laporan |

---

## 9. Hal yang sengaja tidak dikerjakan

Dicatat supaya tidak dibahas ulang, dan supaya bisa ditulis jujur sebagai batasan di paper:

- Model terlatih untuk cabang kepala/wajah dan vokalisasi — tidak ada kohort berpasangan.
- Bobot fusi yang dipelajari dari data nyata — butuh data prospektif berpasangan.
- Validasi pada anak balita — di luar cakupan etis dan waktu.
- Video stimulus adegan sosial dengan aktor manusia — diganti stimulus canvas ber-AOI eksak.
- Native Android — PWA dipilih karena satu codebase dan demo jauh lebih mudah.

---

## 10. Pertanyaan terbuka

- Apakah tim akan tetap bernama Rizzz (nama file paper `Rizzz_ConceptPaper.pdf`)?
- Apakah sudah ada akun Hugging Face untuk hosting model & dataset?
- Perangkat lain yang tersedia untuk demo selain tablet Android (jawaban "something else" saat perencanaan belum terisi).
