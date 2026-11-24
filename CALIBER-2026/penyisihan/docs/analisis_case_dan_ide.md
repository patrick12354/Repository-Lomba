# CALIBER 2026: Analisis Case, Ide, Feasibility & Kompetitor

Dibuat 25 Sep 2026. Deadline proposal **4 Okt 2026 23.59 WIB** (sisa ±9 hari).
Semua angka di bawah dihitung langsung dari file di `Supporting Data/` (pakai `Kuliah & Coding/.venv`).

---

## 1. Rekomendasi: **Pilih Case 2 (Intelligence Manufacturing)**

Alasan utama: data Case 2 bisa dipakai buat **membuktikan business impact dengan angka keras**, dan ada insight yang bisa jadi "hook" cerita (lihat §3). Case 1 lebih gampang di-build, tapi idenya (chatbot RAG) paling generik dan hampir pasti dipilih mayoritas tim.

### Perbandingan

| Aspek | Case 1: Knowledge Hub | Case 2: Intelligence Manufacturing |
|---|---|---|
| Inti solusi | RAG / Q&A assistant atas SOP, datasheet, P&ID, OPL, maintenance log | Unified dashboard + early warning + RCA assist + action tracking |
| Kualitas data | Bagus & konsisten: 8 equipment × (datasheet, GA drawing, interlock C&E, P&ID png, plot plan, 7 OPL) + 211 work order. Semua dokumen saling cross-reference pakai tag (mis. `TJC-LLD-PID-1201`, `SEQ-1201`) | Kaya & kuantitatif: 380 incident (2024–2026), 5 kasus RCA lengkap (deck RCA + condition monitoring 26 minggu + PI data per jam 1 bulan) |
| Gap data | P&ID cuma PNG (perlu vision/OCR atau tagging manual). Tidak ada data "waktu cari info" untuk hitung impact | **Tidak ada data energi & emisi**, padahal Key Question 2 minta *Energy Forecasting*. Harus pakai dummy/public data + justifikasi |
| Business impact bisa dikuantifikasi? | Susah. Downtime 434 jam & biaya Rp538 jt di maintenance log, tapi hubungan ke "knowledge" harus diasumsikan | **Mudah & kuat**: $67.2M loss, 2,261 jam downtime, 220 incident masih open, dan 5 kasus gagal padahal alarm sudah bunyi 6–15 minggu sebelumnya |
| Kemudahan build prototype | Paling gampang: RAG di atas ±60 PDF teks | Sedang: dashboard + scoring + retrieval, tapi data sudah tabular & bersih |
| Daya tarik demo video 3 menit | Chat UI (umum, kurang wow) | Dashboard + "replay" kasus nyata (visual, dramatis) |
| Diferensiasi vs tim lain | Rendah. RAG chatbot = ide default semua tim yang ngerti AI | Lebih tinggi kalau dieksekusi dengan backtest data asli |
| Chemical domain relevance | Tinggi (interlock, SIL, API seal plan) | Tinggi (seal, bearing, fouling, vibration, CAPA 4M+1E) |
| Risiko | Jawaban halu di konteks safety-critical, harus kuat di traceability | Energy forecasting pakai data sintetis, bisa dikritik juri |

**Kapan Case 1 lebih masuk akal:** kalau tim lebih kuat di NLP/LLM engineering daripada analitik, atau mau prototype yang benar-benar live (tanya apa aja, dijawab dari dokumen). Ide Case 1 tetap dicatat di §5 sebagai cadangan.

---

## 2. Temuan Data (hasil cek langsung)

### Case 2
- **Incident Database** (380 baris, Jan 2024 – Jul 2026, 12 plant): total downtime 2,261 jam, total loss **$67.2M**.
  - Status: 113 closed, 47 canceled, **220 masih open** (RCA PROCESS 71, CA/PA EXECUTION 92, MONITORING 37, NEW 20), senilai **$44.3M**.
  - Failure mechanism teratas: Leakage (101), High Vibration (57), Worn Out (47). Component teratas: Bearing, Valve, Coupling, Seal.
  - Kolom yang berguna untuk action tracking: `PIC (RCA)` (13 PIC), `Overall Status`, `RCA Due Date`, `Risk Score`, `Pre-Risk`.
- **5 kasus RCA** (PU-2101B seal, KO-3201 vibration, PM-4405B motor bearing, HE-3301 fouling, BL-5702 misalignment). Tiap kasus punya:
  - Deck RCA (chronology, 4P parameter verification, 4M+1E, CAPA, PIC, status).
  - Equipment Performance: condition monitoring **mingguan 26 minggu** (4 parameter + alarm/trip limit + health status) + KPI summary (availability, MTBF, MTTR, loss).
  - Production Data: **PI tag per jam, 720 jam** (feed, pressure, vibration, temp, ampere, plant rate, run status) + metadata tag.
  - Kelima tag ini **ada di Incident Database** (baris 1–5), jadi join by `Tag Number` bisa jalan. ✅
- **Temuan kunci: alarm sudah bunyi lama sebelum trip, tapi tidak ada tindakan:**

| Kasus | Alarm pertama | Trip | Lead time | Loss |
|---|---|---|---|---|
| RCA1 PU-2101B seal leak | 29 Jan 2026 | 12 Mar 2026 | **6 minggu** | $226k |
| RCA2 KO-3201 vibration trip | 11 Feb 2026 | 29 Apr 2026 | **11 minggu** | $1,584k |
| RCA3 PM-4405B motor bearing | 27 May 2026 | 8 Jul 2026 | **6 minggu** | $112k |
| RCA4 HE-3301 fouling | 12 Mar 2026 | 21 May 2026 | **10 minggu** | $184k |
| RCA5 BL-5702 misalignment | 4 Mar 2026 | 17 Jun 2026 | **15 minggu** | $479k |
| **Total** | | | | **$2.58M** |

  Plus: deck RCA1 menyebut seal MTBF turun 26 → 9 bulan dan seal flush sudah di bawah minimum berulang kali. Kelima RCA juga masih berstatus **CA/PA EXECUTION padahal due date sudah lewat** (Apr–Agu 2026). Ini bukti langsung untuk masalah "alert tidak diprioritaskan & follow-up tidak ter-track".
- ⚠️ **Inkonsistensi dummy data:** vibration di PI data per jam RCA1 masih ±3.8 mm/s sampai 9 Mar, padahal data mingguan sudah 10.2 mm/s di 5 Mar. Pakai **data mingguan untuk cerita early warning**, data per jam untuk anomaly detection 48 jam terakhir. Jangan menaruh dua grafik ini berdampingan.
- ⚠️ **Tidak ada data energi & emisi eksplisit**, tapi kelima file PI punya **motor ampere (`_AMP`) + `PLANT_RATE` per jam**, jadi kWh & SEC (kWh/ton) level equipment bisa dihitung sebagai proxy. Level plant & emisi tetap perlu data sintetis + justifikasi. Detail di [daftar_ide.md](daftar_ide.md) #9.

### Case 1
- Maintenance History: 211 WO (Jun 2024 – Des 2025), 8 equipment, unit LLDPE. 31 breakdown, 434 jam downtime, Rp538 jt. Downtime terbesar: EA-5601 (124 jam, fouling), FA-8901, YD-2301.
- Kolom `Related_Interlock` menghubungkan WO ke interlock C&E. Datasheet menulis cross-reference eksplisit ke P&ID, interlock, OPL, dan maintenance history. **Knowledge graph berbasis tag bisa langsung dibangun.** ✅
- Semua PDF (datasheet, interlock, OPL) bisa di-extract teksnya (`pdftotext`). OPL berisi tabel *Symptom → Likely Cause → Action*, bahan yang pas untuk "failure memory". ✅
- P&ID hanya PNG ±1 MB → perlu vision LLM untuk ekstrak tag/koneksi (8 gambar, masih feasible manual).
- Tidak ada SOP formal, EDMS, AIMS, atau data real-time. Yang ada hanya OPL + datasheet, jadi integrasi EDMS/AIMS/Digital Twin cuma bisa di level arsitektur/mock.

---

## 3. Ide Utama (Case 2): *"Early warning yang benar-benar ditindaklanjuti"*

Nama kerja: **PlantPulse** (bebas diganti).

**Narasi pitch:** *"Lima kegagalan senilai $2.58M sebenarnya sudah terdeteksi 6–15 minggu sebelumnya. Sensornya tidak salah; yang gagal adalah jalur dari alarm ke aksi."* Solusinya bukan sekadar dashboard baru, tapi rantai **Detect → Prioritize → Diagnose → Act → Track**.

### Komponen & mapping ke Key Questions

| Key Question | Komponen | Isi | Data |
|---|---|---|---|
| KQ1: Rasionalisasi dashboard & data foundation | **Data Source Map + KPI Dictionary** | Peta sumber (PI historian, CMMS/WO, incident/RCA DB, condition monitoring, energy meter). `Tag Number` sebagai master key. Satu definisi KPI (Availability, MTBF, MTTR, Loss, CAPA closure rate). Tunjukkan "12 dashboard → 1" sebagai ilustrasi | Semua file Case 2 (sudah terbukti bisa di-join via tag) |
| KQ2: Single pane of glass (eksekutif) | **Executive Dashboard** | KPI plant-wide, heatmap loss per plant × failure mechanism, top bad actors, open risk $44.3M, **Energy Forecasting** panel, **Similar-incident retrieval**, **AI root-cause indication** | Incident DB (380), Equipment Performance; energi = sintetis |
| KQ3: RCA + prioritized follow-up | **Problem Tank + Alert Priority Engine + Action Tracker** | Setiap alarm jadi "problem card". Skor prioritas = f(risk score, laju degradasi / estimasi time-to-trip, potential loss, kekritisan equipment). AI mencari 3 incident paling mirip (tag type + component + mechanism + teks), mengusulkan probable cause dalam format 4M+1E **dengan sumber**, lalu menyusun draft CAPA dengan PIC, due date, dan status. Eskalasi otomatis kalau overdue | Condition History, Incident DB, 5 deck RCA |

### Fitur pembeda (yang bikin menang)
1. **Backtest dengan data asli**: "Kalau PlantPulse jalan sejak Jan 2026, PU-2101B sudah jadi alert P1 pada 29 Jan, 42 hari sebelum trip." Dijalankan untuk 5 kasus sekaligus. Ini jadi slide Business Impact.
2. **Time-to-trip estimation**: regresi linear sederhana pada tren mingguan ke batas trip. Mudah dijelaskan, transparan, cocok untuk juri non-ML.
3. **Traceable AI**: setiap rekomendasi menampilkan sumbernya (incident ID, slide RCA, parameter mana yang breach) + confidence. **Human-in-the-loop**: engineer approve/reject, feedback masuk ke model.
4. **Overdue CAPA radar**: 5 RCA yang lewat due date dijadikan contoh nyata.

### Business impact (draft angka, perlu dirapikan)
- Loss yang bisa dihindari di 5 kasus: $2.58M (asumsi konservatif 50% tercegah = **$1.29M**).
- Proyeksi ke 380 incident: failure mode yang biasanya didahului degradasi (vibration/bearing/seal/fouling/worn out) mencakup sebagian besar dari $67.2M. Pakai asumsi yang disebut eksplisit.
- KPI: lead time alarm→WO, % alert ditindaklanjuti < 48 jam, CAPA on-time closure, MTBF, jam validasi data per insiden.

### Feasibility build dalam 9 hari

| Item | Cara | Feasible? |
|---|---|---|
| Data prep | Python/pandas → JSON (5 kasus + 380 incident) | ✅ 1 hari |
| Prototype | HTML/Next.js statis + chart (Recharts/ECharts) di-host (Vercel) atau Figma. Data asli di-embed | ✅ 3–4 hari |
| Priority score & time-to-trip | Rumus + regresi linear di Python, hasil di-embed | ✅ |
| Similar-incident retrieval | TF-IDF/embedding atas title + component + mechanism (380 baris, kecil) | ✅ |
| Root-cause indication (LLM) | Pre-generate pakai LLM dengan sumber, tampilkan sebagai output. Tidak wajib live | ✅ |
| Energy forecasting | Data sintetis + model sederhana (Prophet/ARIMA) untuk demo. Tulis jujur di deck bahwa ini ilustratif | ⚠️ perlu justifikasi |
| Video 3 menit | Screen record prototype + voice over | ✅ tapi lihat batas ukuran ⬇ |

⚠️ **Batas total 10 MB untuk 3 materi.** Video 3 menit harus ≤ ±7 MB → bitrate ±300 kbps (720p H.264/H.265, UI statis masih oke). Prototype sebaiknya dikirim sebagai **link** (Vercel/Figma) supaya tidak makan kuota. Deck PDF kompres gambar (< 2 MB). Tes export lebih awal.

---

## 4. Riset Kompetitor

### a) Tim peserta lain
- CALIBER 2025: **363 tim dari 81 universitas** (naik 252% dari 2024). Asumsikan 2026 skalanya mirip atau lebih besar, dan hanya **10 tim** lolos final (±3%).
- Tema 2024 (plastic waste) dan 2025 (zero-carbon building) murni business strategy. Pemenang: **UI "Smansasiers"** (juara 1 2024, ACE Strategy), **ITB CIRC-M** (juara 3 2025). Juri menyukai **kolaborasi lintas disiplin**.
- **2026 adalah tahun pertama temanya AI + wajib prototype + video.** Implikasinya:
  - Banyak tim bisnis/teknik kimia akan kesulitan di prototype. Prototype yang benar-benar jalan dengan data asli langsung jadi pembeda.
  - Tim IT kemungkinan besar pilih Case 1 (RAG chatbot), sehingga Case 1 akan ramai dan mirip-mirip.
  - Tim dari kampus teknik kimia (ITB, UI, UGM, ITS) unggul di domain knowledge. **Tim kita perlu anggota/advisor Teknik Kimia/Mesin** untuk skor *Chemical Domain Relevance*, atau minimal mempelajari 5 deck RCA sampai benar-benar paham.

### b) Produk komersial (benchmark & posisi)

| Produk | Yang dilakukan | Relevan untuk |
|---|---|---|
| Honeywell Forge Production Intelligence | Sentralisasi data, prioritas pattern, root cause & recommended actions | Case 2 (benchmark langsung) |
| AspenTech Mtell | Predictive maintenance ML, deteksi pola failure berminggu-minggu sebelumnya | Case 2 (early warning) |
| Seeq | Analitik data proses, deteksi abnormal, investigasi loss | Case 2 |
| Cognite Data Fusion / Atlas AI | Industrial knowledge graph + agent yang menelusuri data untuk root cause | Case 1 & 2 |
| Siemens Industrial Copilot (maintenance) | GenAI assistant berbasis RAG atas dokumentasi & tiket, digitalisasi P&ID legacy | Case 1 (benchmark langsung) |

**Positioning di deck:** jangan mengklaim bersaing dengan produk-produk ini. Framing yang tepat: *"lapisan orkestrasi ringan di atas stack yang sudah ada (PI historian, SAP PM), fokus pada gap alarm→action yang tidak diselesaikan tools monitoring."* Framing ini sekaligus menjawab feasibility (tidak rip-and-replace, bisa pilot di 1 plant). Harga lisensi enterprise tools tersebut bisa jadi argumen cost-benefit (build vs buy).

Sumber:
- [CALIBER 2025: 363 tim dari 81 universitas](https://chandra-asri.com/id/news/caliber-2025-catat-partisipasi-363-kelompok-dari-81-universitas-indonesia)
- [ITB juara 3 CALIBER 2025 (CIRC-M)](https://itb.ac.id/berita/mahasiswa-itb-juara-3-business-case-caliber-dengan-inovasi-circ-m/62107)
- [UI juara 1 CALIBER 2024](https://m.jpnn.com/news/tim-smansasiers-universitas-indonesia-menjuarai-kompetisi-caliber-2024)
- [Honeywell Forge Production Intelligence](https://process.honeywell.com/us/en/products/industrial-software/operational-excellence/honeywell-forge-production-intelligence)
- [Industrial AI software options 2026 (AspenTech, Seeq, dll.)](https://www.viewpointanalysis.com/post/industrial-ai-software-options-2026)
- [Siemens Industrial Copilot maintenance](https://press.siemens.com/global/en/pressrelease/siemens-expands-industrial-copilot-new-generative-ai-powered-maintenance-offering)
- [Siemens AI agents / Cognite agentic (ARC)](https://www.arcweb.com/blog/siemens-introduces-ai-agents-industrial-automation)
- [Chandra Asri: maintenance terjadwal plant Cilegon 2026](https://chandra-asri.com/en/news/ensure-long-term-reliability-cap-petrochemical-plants-undergo-scheduled-maintenance)

---

## 5. Ide Cadangan (Case 1): *Tag-centric Knowledge Graph + Cited Copilot*

- **Industrial Data Ops:** ingest ±60 PDF + 211 WO + 8 P&ID menjadi knowledge graph dengan node = equipment tag, instrument tag, interlock (SEQ-xxxx), dokumen (dengan rev & approval status), WO.
- **Q&A dengan sitasi wajib:** setiap jawaban menyebut dok no. + rev + halaman. Kalau tidak ada sumber, jawab "tidak tahu" (penting untuk safety).
- **Failure memory:** gabungkan tabel troubleshooting di OPL + root cause di WO → "gejala ini pernah terjadi 3×, penyebab X, tindakan Y".
- **Context mode:** pilih equipment → tampil interlock C&E, permissive start, OPL terkait, riwayat WO (mock digital twin).
- Feasibility: sangat bisa dibangun live (Claude API + vector store kecil). Kelemahan: impact susah diangka-kan dan idenya pasaran.

---

## 6. Rencana Kerja 9 Hari (Case 2)

| Tanggal | Target |
|---|---|
| 25–26 Sep | Final pilih case, bagi peran, baca 5 deck RCA sampai paham, data prep → JSON |
| 27–29 Sep | Build prototype (dashboard, problem tank, detail kasus + backtest), priority score |
| 30 Sep – 1 Okt | Deck 7 slide + appendix (data architecture, asumsi, perhitungan impact) |
| 2 Okt | Rekam & edit video 3 menit, kompres ≤ 7 MB |
| 3 Okt | Review total: cek 3 KQ terjawab eksplisit, bahasa Inggris, ukuran ≤ 10 MB, link prototype bisa diakses tanpa login |
| 4 Okt (siang, jangan mepet) | Submit (sekali saja) |

## 7. Hal yang Perlu Diputuskan Tim
- [ ] Case 1 atau 2 (rekomendasi: 2)
- [ ] Komposisi tim: ada anak Teknik Kimia/Mesin? Nama dosen pembimbing?
- [ ] Prototype: HTML (Vercel) atau Figma. Rekomendasi: HTML dengan data asli, karena lebih meyakinkan
- [ ] Sumber data energi sintetis + justifikasinya
