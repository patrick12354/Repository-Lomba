# Keputusan Build: CALIBER 2026

Terakhir diupdate: 25 Sep 2026. Referensi: [penjelasan_lomba.md](penjelasan_lomba.md) · [analisis_case_dan_ide.md](analisis_case_dan_ide.md) · [daftar_ide.md](daftar_ide.md)

## Keputusan

| Topik | Keputusan |
|---|---|
| Case | **Case 2: Intelligence Manufacturing** |
| Nama kerja | PlantPulse (boleh diganti) |
| Cerita utama | "5 kegagalan senilai $2.58M sudah terlihat 5–6 minggu sebelumnya; yang gagal adalah jalur dari alarm ke aksi" |
| Alur solusi | Detect → Prioritize → Diagnose → Act → Track |
| Pendekatan early warning | Trend + limit (rule-based, transparan). ML = roadmap, karena data cuma 5 failure |
| Prototype | HTML (bukan Figma), data asli di-embed, di-host sebagai link |
| Interaksi utama | **Time Machine slider** (replay minggu 1–26, alert terpicu otomatis). What-if slider opsional untuk 1 equipment |
| Output AI | **Pre-generated** (disimpan sebagai JSON), bukan live call dari prototype |

## Fitur yang Dibangun

**Core (wajib):**
- #1 Early Warning + Time-to-Trip (sudah dites: 5/5 kasus ter-flag 35–42 hari sebelum trip)
- #2 Alert Priority Engine
- #3 Backtest & Impact Simulator
- #4 Similar-Incident Retrieval
- #5 AI Root Cause Indication (4M+1E)
- #6 Problem Tank + Action Tracker
- #7 Executive Dashboard (+ #10 Pareto bad actor)
- #8 Data Source Map + KPI Dictionary (sebagian besar di slide/appendix)
- #9 Energy Forecasting versi kecil (proxy dari motor ampere + plant rate)

**Diferensiasi AI:**
- **A** Auto-draft RCA Report dalam format form Chandra Asri
- **B** Blind-test akurasi AI vs root cause terverifikasi (hasil dilaporkan apa adanya)
- **C** Failure Signature Matching (kemiripan pola tren)
- **D** Pro-Active Roll-out Finder (cukup UI)
- **H** Cost-of-delay (cukup UI)
- **E** CAPA Effectiveness Auto-Verify (kalau sempat)

**Skip:** #11 chat "Ask PlantPulse". #12 mobile cukup 1 frame mockup (opsional).

## LLM: OpenAI (pakai credits yang ada)

### Dipakai di mana

| Kegunaan | Fitur | Jenis model |
|---|---|---|
| Menulis draft RCA 11 bagian (4P, 4M+1E, root cause statement, CAPA) | A | Chat model terbaru di akun (structured output / JSON schema) |
| Blind-test: tebak root cause dari data sensor saja | B | Model yang sama dengan A (supaya klaimnya konsisten) |
| Probable cause + bukti + sitasi + confidence | #5 | Chat model |
| Embedding teks 380 incident untuk similar-incident | #4 | Embedding model (mis. `text-embedding-3-small`, murah) |
| Guidance langkah action card, ringkasan eksekutif mingguan | #6, #7 | Chat model |
| Roll-out finder: alasan kenapa equipment X mirip | D | Chat model (opsional; matching-nya sendiri rule-based) |

**Tidak pakai LLM** (cukup Python/numerik, lebih akurat & transparan): #1 time-to-trip, #2 priority score, #3 backtest, C signature matching (kemiripan vektor/DTW), #9 forecast, H cost-of-delay.

### Aturan pakai (aman)
1. **Diizinkan lomba** (FAQ #8): boleh pakai AI tools asal legal & sesuai T&C. Semua output AI **wajib divalidasi**, jadi setiap output A/#5 harus dicek manual terhadap deck RCA sebelum masuk prototype.
2. **API key jangan pernah masuk ke prototype HTML / repo publik.** Simpan di `.env` lokal (masuk `.gitignore`). Karena output pre-generated, prototype tidak butuh key sama sekali.
3. Data yang dikirim ke API adalah dummy data lomba ("sample data for CALIBER purposes only"), jadi aman. Data API OpenAI secara default tidak dipakai untuk training.
4. Simpan prompt + raw output + tanggal ke folder (mis. `ai_runs/`) sebagai bukti validasi & bahan appendix.
5. Blind-test B: jalankan sekali dengan prompt yang dikunci, laporkan hasil apa adanya (termasuk yang salah).
6. **Di deck (Feasibility/cybersecurity):** untuk implementasi nyata, sebut deployment via **Azure OpenAI / private endpoint di tenant perusahaan** (data tidak keluar, SSO, audit log), atau model open-source on-prem sebagai opsi. Jangan tulis "pakai API OpenAI publik" untuk produksi.
7. Deck & naskah video ditulis tim sendiri. LLM boleh bantu polishing, tapi isi & angka harus dicek.
