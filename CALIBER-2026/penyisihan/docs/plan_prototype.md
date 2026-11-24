# Plan Prototype: PlantPulse (CALIBER 2026, Case 2)

> **Untuk Claude di chat baru:** dokumen ini adalah spesifikasi lengkap untuk membangun prototype. Baca juga [keputusan_build.md](keputusan_build.md) (keputusan final) dan [daftar_ide.md](daftar_ide.md) (detail fitur). Konteks lomba ada di [penjelasan_lomba.md](penjelasan_lomba.md). Kerjakan per milestone di §10, dan konfirmasi ke user sebelum lanjut ke milestone berikutnya.

Root project: `/Users/timotiuspatrick/Documents/Patrick/Kuliah & Coding/Caliber 2026/`
Python: **pakai venv** `/Users/timotiuspatrick/Documents/Patrick/Kuliah & Coding/.venv/bin/python` (sudah ada pandas, openpyxl, python-pptx). Jangan bikin venv baru.
LLM: **OpenAI API** (user punya credits). Key di `.env` → `OPENAI_API_KEY`. **Jangan pernah** masuk ke frontend/repo.
Deadline submit: **4 Okt 2026 23.59 WIB**. Target prototype selesai: **1 Okt**.

---

## 1. Tujuan & Batasan

**Tujuan:** prototype web yang bisa dinavigasi juri, pakai **data asli** dari `Supporting Data/Case 2_ Intelligence Manufacturing/`, dan menunjukkan alur **Detect → Prioritize → Diagnose → Act → Track** untuk 5 kasus RCA, plus dashboard eksekutif atas 380 incident.

**Cerita yang harus terbukti di prototype:**
> "5 kegagalan senilai $2.58M sudah terlihat 5–6 minggu sebelumnya. Sensornya tidak salah; yang gagal adalah jalur dari alarm ke aksi."

**Batasan wajib (dari booklet):**
- **Semua teks UI dalam bahasa Inggris.**
- Prototype diakses via **link** (Vercel) tanpa login. Total 3 materi ≤ 10 MB, jadi prototype jangan di-upload sebagai file besar.
- Harus menjawab 3 Key Questions (mapping di §9).
- Semua output AI ditampilkan dengan **sumber, confidence, dan tombol Approve/Reject** (human-in-the-loop).
- Output AI **pre-generated** (JSON statis). Prototype tidak memanggil API apa pun saat runtime.

---

## 2. Stack & Struktur Folder

- **Pipeline data & AI:** Python (venv di atas) + `openai`, `numpy`, `pandas`, `python-dotenv`, `statsmodels` (install ke venv kalau belum ada).
- **Frontend:** Vite + React + TypeScript + Tailwind CSS + Recharts (atau ECharts kalau butuh anotasi chart lebih kaya) + React Router. State global pakai Zustand.
- **Deploy:** Vercel (static build). Jangan pakai backend.

```
Caliber 2026/
├── docs/                         # semua catatan (dokumen ini)
├── Supporting Data/              # data mentah dari panitia (JANGAN diubah)
├── pipeline/
│   ├── config/equipment_meta.json   # metadata manual (spare, voltage, channel mapping)
│   ├── config/signature_library.json
│   ├── 01_extract.py             # Excel/PPTX → data/interim/*.json
│   ├── 02_analytics.py           # time-to-trip, health, priority, backtest, energy, signature
│   ├── 03_embed_incidents.py     # OpenAI embeddings → similar incidents
│   ├── 04_ai_generate.py         # OpenAI: root cause, RCA draft, action guidance
│   ├── 05_blind_test.py          # OpenAI: blind test B
│   ├── 06_export.py              # gabung → prototype/src/data/*.json
│   └── common.py
├── ai_runs/                      # log prompt + raw response + timestamp (bukti validasi)
├── prototype/                    # Vite app
│   ├── src/data/                 # JSON hasil pipeline (di-commit)
│   ├── src/pages/ …
│   └── src/components/ …
├── .env                          # OPENAI_API_KEY=...  (gitignored)
└── .gitignore                    # .env, node_modules, ai_runs/raw (opsional)
```

---

## 3. Sumber Data (struktur persis)

Base: `Supporting Data/Case 2_ Intelligence Manufacturing/`

### 3.1 Incident Database: `Incident Database/Incident Database.xlsx`
- Sheet `Incident Database`, **header di baris ke-3** → `pd.read_excel(..., sheet_name="Incident Database", header=2)`. 380 baris.
- Kolom: `Serial No, MTO No., AR No., Plant, Tag Number, Eq. Class, Date of Occur. (string), Risk Case Title, Highest Impact, Pre-Risk, Risk Score, PIC (RCA), Overall Status, Discipline, Eq. Type, Component, F Mechanism, Downtime (hrs), Act. Loss (k US$), Pot. Loss (k US$), Total Loss (k US$), RCA Due Date (string), Month - Year`
- 12 plant: ARP, ZCU, NUP, OPP, SMX, CRP, OP2, BRP, OP3, OPU, BDX, TKX. 15 Eq. Type: PU, CO, EM, HB, BL, TR, VA, PZ, SW, RX, FA, TX, TK, SX, CD.
- Status: RISK CLOSED 113, CA/PA EXECUTION 92, RCA PROCESS 71, RISK CANCELED 47, MONITORING RESULT 37, NEW REGISTERED 20.
- **Baris Serial No 1–5 = 5 kasus RCA** (PU-2101B, KO-3201, PM-4405B, HE-3301, BL-5702).
- Sheet `Dashboard` = ringkasan (total 380 / 2,261.1 jam / $67,194k). Pakai untuk cross-check angka.

### 3.2 Equipment Performance: `Equipment Performance/Equipment Performance - RCA{1..5} {TAG}.xlsx`
- Sheet `Equipment Info` (`header=None`):
  - Nameplate di kolom 0–1, baris 3–14: Equipment Tag, Equipment Name, Equipment Type, Equipment Class, Plant / Unit, Discipline, Criticality, Design Life, Monitoring Method, Linked RCA / AR No., Failure Date, Dominant Failure Mode.
  - Limit di kolom 2–3, baris 4–7: `Parameter` | `"alarm / trip"` (string, split `/`). Arah ditentukan dari trip vs alarm: trip > alarm = naik itu buruk; trip < alarm = turun itu buruk (mis. seal flush 5.0 / 4.0).
- Sheet `Condition History`: 26 baris mingguan. Kolom: `Week, Date, <4 parameter, nama mengandung \n + unit>, Health Status (NORMAL/ALARM/TRIP), Remark`.
- Sheet `Performance Summary` (`header=2`): KPI | Value | Basis. Termasuk Total Downtime, Availability, MTBF, MTTR, ALARM/TRIP/NORMAL readings, PM Compliance, **Production Loss (ton)**, **Estimated Loss (k USD)**.

Limit per equipment (sudah dicek):

| Tag | Param 1 | Param 2 | Param 3 | Param 4 |
|---|---|---|---|---|
| PU-2101B | Overall Vibration mm/s 7/11 | Seal Flush Flow L/min 5/4 | Discharge Pressure barg 8.5/7.5 | Bearing Temp °C 80/95 |
| KO-3201 | DE Radial Vibration µm 45/75 | Lube Oil Water ppm 500/1500 | Lube Oil Supply Press barg 1.4/1.1 | Bearing Metal Temp °C 95/110 |
| PM-4405B | Motor DE Bearing Temp °C 75/90 | Motor Vibration mm/s 5/8 | Motor Ampere A 150/165 | Winding Temp °C 120/140 |
| HE-3301 | Tube-side dP bar 0.6/0.9 | Heat Duty % 90/70 | Cold Outlet Temp °C 110/95 | Feed Heavy-ends % 1.5/2.4 |
| BL-5702 | Overall Vibration mm/s 7/11 | 2X Harmonic mm/s 3/5 | Coupling Offset mm 0.05/0.3 | Bearing Temp °C 80/95 |

### 3.3 Production Data: `Production Data/Production Data - RCA{n} {TAG}.xlsx`
- Sheet `PI Tag`: metadata (Name, Description, engunits, span, typicalvalue, zero, instrumenttag).
- Sheet `Sheet2`: 720 baris per jam. Kolom: `Timestamp, {TAG}_FEED, {TAG}_DISP, {TAG}_VIB, {TAG}_TEMP, {TAG}_AMP, PLANT_RATE, RUN_STATUS (ON/OFF)` (tag tanpa tanda hubung, mis. `PU2101B_`).
- ⚠️ **Inkonsistensi:** nilai VIB per jam tidak cocok dengan data mingguan (RCA1: per jam ±3.8 sampai 9 Mar, mingguan sudah 10.2 pada 5 Mar). **Aturan:** data mingguan untuk early warning & backtest; data per jam hanya untuk tab Energy dan panel "last 48h" di sekitar trip. Jangan overlay keduanya dalam satu chart.

### 3.4 RCA decks: `RCA - Downtime Data/RCA{n} - ....pptx`
11 slide, format form perusahaan (Procedure RCA-P-0050-03, Form RCA-F-0075-02):
1 Cover (AR no, tag/plant, date, pre-risk, PIC) · 2 Problem Identification (AR details, immediate action, severity, downtime, loss, problem statement) · 3 Chronology · 4 Past Performance + 4W impact · 5 Target setting · 6 **4P Parameter Verification (G/NG + evidence)** · 7 **4M+1E Verification + ROOT CAUSE statement** · 8 Matrix priority (impact vs control) · 9 **CAPAA (corrective + pro-active roll-out, plan date, PIC, status)** · 10 Preventive & risk analysis + PM schedule · 11 (penutup/ringkasan).
Ekstrak dengan `python-pptx` (teks + tabel). Script contoh: iterasi `slide.shapes`, ambil `text_frame.text` dan `table.rows`.

**Ground truth root cause (untuk blind test B & validasi):**

| Kasus | Plant | Immediate action (spare?) | Root cause terverifikasi |
|---|---|---|---|
| RCA1 PU-2101B | ARP (Aurora Resin Plant) | Swap ke spare **PU-2101A** | Intermittent dry-running: suction cavitation saat feed swing menurunkan NPSH, seal-flush < 6 L/min, tidak ada interlock proteksi seal |
| RCA2 KO-3201 | ZCU (Zeta Cracker Unit) | Controlled shutdown train (**tanpa spare**) | Babbitt journal bearing rusak: oil film lemah karena **water ingress dari tube lube-oil cooler bocor**, tidak ada online water-in-oil monitoring |
| RCA3 PM-4405B | NUP (Nova Utility Plant) | Start standby **PM-4405C** | Bearing DE motor gagal: **grease degradasi** karena interval re-lubrikasi terlalu panjang/non-risk-based, tidak ada trending bearing temp |
| RCA4 HE-3301 | ZCU | Bypass via **spare train** | Fouling coke/polymer tube-side karena **feed heavy-ends di atas desain**, tidak ada trigger cleaning berbasis dP / KPI fouling |
| RCA5 BL-5702 | OPP (Orion Polypropylene Plant) | Stop blower (**tanpa spare**) | **Coupling misalignment** + soft-foot + elemen coupling elastomer tua; cek alignment/soft-foot tidak ada di PM, interval vibration route terlalu panjang |

### 3.5 Tanggal kunci (dari Condition History)

| Kasus | Minggu 1 | Status ALARM pertama | Trip | Loss |
|---|---|---|---|---|
| RCA1 PU-2101B | 2025-10-23 | 2026-01-29 | 2026-03-12 | $226.44k |
| RCA2 KO-3201 | 2025-12-10 | 2026-02-11 | 2026-04-29 | $1,584k |
| RCA3 PM-4405B | 2026-02-18 | 2026-05-27 | 2026-07-08 | $112k |
| RCA4 HE-3301 | 2026-01-01 | 2026-03-12 | 2026-05-21 | $183.6k |
| RCA5 BL-5702 | 2026-01-28 | 2026-03-04 | 2026-06-17 | $478.8k |

---

## 4. Pipeline Data (Python)

### 4.1 `01_extract.py` → `data/interim/`
- `incidents.json`: 380 baris, kolom di-rename ke snake_case, tanggal di-parse ke ISO, `is_open = status in {NEW REGISTERED, RCA PROCESS, CA/PA EXECUTION, MONITORING RESULT}`, `is_overdue = is_open and rca_due_date < SIM_TODAY` (SIM_TODAY default 2026-09-25).
- `equipment/{tag}.json` untuk 5 equipment: nameplate, params `[ {key, label, unit, alarm, trip, direction: "up"|"down"} ]`, weekly `[ {week, date, values{key:val}, status, remark} ]`, summary KPI, hourly PI (720 baris) + PI tag metadata.
- `rca/{tag}.json`: hasil parse deck (per slide: judul, teks, tabel). Dipakai sebagai ground truth & template, **bukan** input blind test.

### 4.2 `pipeline/config/equipment_meta.json` (isi manual)
```json
{
  "PU-2101B": {"has_spare": true,  "spare_tag": "PU-2101A", "voltage_v": 380,  "pf": 0.85,
               "channels": {"vibration": "overall_vibration", "flow_pressure": "seal_flush_flow", "pressure": "discharge_pressure", "temperature": "bearing_temp"}},
  "KO-3201":  {"has_spare": false, "voltage_v": 6600, "pf": 0.85, "channels": {...}},
  "PM-4405B": {"has_spare": true,  "spare_tag": "PM-4405C", ...},
  "HE-3301":  {"has_spare": true,  "spare_tag": "spare train", ...},
  "BL-5702":  {"has_spare": false, ...}
}
```
Voltage adalah **asumsi** (tulis di KPI dictionary & appendix). Kalau nilai AMP per jam tidak masuk akal untuk voltage tsb, sesuaikan dan catat.

### 4.3 `02_analytics.py`: algoritma (deterministik, tanpa LLM)
Semua dihitung **per minggu w** (untuk Time Machine) → output `timeline[w]`.

**a. Normalisasi ke limit (severity ratio)**
`baseline_p = median(nilai minggu 1–6)`
`r_p(w) = (x_p(w) − baseline_p) / (trip_p − baseline_p)` → 0 = baseline, 1 = trip. Clip ke [0, 1.2].

**b. Health score**
`health(w) = round(100 × (1 − max_p r_p(w)))`, clip 0–100.

**c. Time-to-trip (TTT)**
Untuk tiap parameter: fit pada 6 titik terakhir (w−5..w):
- linear `np.polyfit(t, y, 1)` dan kuadratik `np.polyfit(t, y, 2)`
- ambil akar positif terkecil yang menyentuh `trip_p` (dalam minggu), sesuai arah
- `ttt_p = min(linear, quadratic)` (lebih konservatif; linear saja terbukti ±1 minggu terlalu optimis)
- `ttt = min_p ttt_p`, `driver = argmin`. Kalau tren tidak menuju trip → `ttt = null` ("stable").
Hasil uji linear (25 Sep): semua 5 kasus ter-flag TTT ≤ 8 minggu pada 35–42 hari sebelum trip. Target setelah pakai kuadratik: flag tetap ≥ 35 hari, estimasi lebih dekat ke aktual.

**d. Status**
- `CRITICAL`: nilai ≥ trip, atau TTT ≤ 2 minggu
- `ALARM`: nilai melewati alarm limit
- `WATCH`: TTT ≤ 8 minggu tapi belum alarm ← **ini value add kita (lebih awal dari alarm DCS)**
- `NORMAL`: selain itu
Tampilkan juga status asli dari data (`Health Status`) sebagai pembanding "Legacy alarm".

**e. Priority score (Alert Priority Engine)**
```
loss_per_hour   = estimated_loss_usd / total_downtime_hours      (dari Performance Summary)
consequence_usd = loss_per_hour × mttr_hours × (0.5 if has_spare else 1.0)
U = clamp(1 − ttt_days/56, 0, 1)          (null TTT → 0; CRITICAL → 1)
C = clamp(log10(consequence_usd) / log10(2_000_000), 0, 1)
K = 1.0 if class A else 0.7
score = round(100 × (0.5·U + 0.35·C + 0.15·K))
P1 ≥ 70 · P2 50–69 · P3 30–49 · P4 < 30
```
Simpan `reasons[]` yang bisa dibaca manusia, mis. `["~21 days to trip (Seal Flush Flow)", "$12.2k loss/hour", "Class B, spare available (PU-2101A)"]`.
Bobot boleh di-tuning, tapi tetap sederhana & tulis di KPI dictionary.

**f. Cost of delay**
`cod_per_week = consequence_usd × min(1, 7 / max(ttt_days, 7))`. Tampilkan "Delaying 1 week adds ≈ $X risk".

**g. Backtest (#3)**
Untuk tiap kasus: minggu pertama status ≥ WATCH, minggu pertama P1/P2, minggu pertama "Legacy ALARM", tanggal trip. Output:
`{tag, first_watch_date, first_p1_date, legacy_alarm_date, trip_date, lead_days_vs_trip, lead_days_vs_legacy_alarm, actual_loss_usd}`.
ROI: `avoided = Σ actual_loss × capture_rate` (slider 25–75%, default 50%) → dipakai di halaman Impact.

**h. Energy (#9)**
Dari hourly PI: `kW = √3 × V × AMP × PF / 1000` (RUN_STATUS=OFF → 0), `kWh/jam`, `SEC = kWh / PLANT_RATE` (kWh/ton).
Forecast 7 hari: Holt-Winters (`statsmodels ExponentialSmoothing`, seasonal 24) pada kWh; interval sederhana ±1.96σ residual.
Deteksi deviasi: rolling 24h SEC vs baseline minggu pertama; flag kalau > +5%.
Biaya: tarif listrik industri PLN (asumsi, misalnya Rp1,115/kWh untuk golongan I-4; **verifikasi & tulis sumbernya**).
Level plant & emisi: **tidak ada data**. Tampilkan panel "Plant-level energy & emissions: requires meter integration (roadmap)" dengan data ilustratif berlabel **"Illustrative (synthetic)"**.

**i. Failure Signature Matching (C)**
- Map 4 parameter tiap equipment ke channel semantik: `vibration`, `temperature`, `flow_pressure`, `process/other` (lihat `equipment_meta.channels`).
- Vektor signature = untuk tiap channel: arah & besar slope dari `r_p` di 6 minggu terakhir → `[-1..1]`.
- Library (`signature_library.json`): 5 kasus nyata (leave-one-out saat match kasus itu sendiri) + ±8 pola textbook yang ditulis tangan, dengan sumber referensi umum reliability: dry-running seal, cavitation, bearing lubrication failure, oil contamination (water-in-oil), misalignment, unbalance, looseness/soft-foot, heat-exchanger fouling.
- Similarity = cosine(vektor) + bonus kecocokan equipment type. Output top-3 `{signature, similarity_pct, typical_root_causes, source}`.

### 4.4 `03_embed_incidents.py`: Similar incidents (#4)
- Teks per incident: `"{Risk Case Title} | {Eq. Type} | {Component} | {F Mechanism} | {Discipline}"`.
- `text-embedding-3-small`, simpan vektor di `data/interim/embeddings.npy` (jangan kirim ke frontend).
- Query untuk tiap kasus RCA = teks incident-nya sendiri + deskripsi parameter yang menyimpang.
- Skor = `0.6 × cosine + 0.4 × structured` (structured: eq type sama 0.4, component 0.3, mechanism 0.3).
- **Exclude incident itu sendiri** (Serial 1–5). Output top-5 per kasus → `similar_incidents.json`.
- Tambahkan statistik: jumlah incident dengan eq type + mechanism sama, rata-rata downtime & loss.

### 4.5 `04_ai_generate.py`: output LLM (OpenAI)
Umum:
- Model: chat model terbaru yang tersedia di akun user (cek `client.models.list()`), `temperature` rendah (0.2), **Structured Outputs / JSON schema**.
- Setiap call: simpan `ai_runs/{timestamp}_{task}_{tag}.json` berisi prompt, input, raw output, model, usage.
- System prompt inti: "You are a reliability engineer assistant in a petrochemical plant. Use ONLY the provided evidence. Cite evidence IDs for every claim. If evidence is insufficient, say so and lower confidence. Output English."

**(#5) Root cause indication:** per kasus, input = nameplate + limit + tren weekly (w−10..trip) + parameter breach + signature match (C) + similar incidents (#4). **Tidak** menyertakan deck RCA kasus itu sendiri.
Schema: `{hypotheses:[{rank, cause, category: Man|Machine|Method|Material|Environment, confidence: High|Medium|Low, evidence:[{type: param|incident|signature, ref, detail}], verify_first:[string]}], data_gaps:[string]}`

**(A) Auto-draft RCA report:** input = semua di atas + chronology otomatis dari data (tanggal WATCH, ALARM, TRIP, repair) + few-shot **struktur** dari deck RCA kasus LAIN (bukan kasus itu sendiri).
Schema mengikuti 11 bagian form: `cover, problem_identification{problem_statement, immediate_action, severity, downtime_h, loss_usd}, chronology[], past_performance{evidence, impact_4w}, target{actual, target, metric}, p4_verification[{id, parameter, result: G|NG, evidence}], m4e1_verification[{id, factor, category, result, evidence}], root_cause_statement, priority_matrix[{id, impact, control}], capaa{corrective[], proactive_rollout[]}[{rc_ref, action, plan_date, pic, status}], preventive{items[], risk_analysis[], pm_schedule[]}`.
Setelah generate: **tim membandingkan dengan deck asli** dan mencatat hasilnya di `ai_runs/validation_notes.md`.

**(#6) Action guidance:** untuk tiap problem card, 3–5 langkah + PIC discipline (ROT/STA/INS/ELE/REL) + SLA berdasarkan prioritas (P1 48 jam, P2 7 hari, P3 30 hari).

**(D) Roll-out finder:** rule-based: cari di 380 incident yang eq type + component/mechanism sama dengan root cause kasus → list tag + plant. LLM hanya menulis 1 kalimat alasan per grup.

**(Exec brief):** 1 paragraf ringkasan mingguan untuk halaman Overview.

### 4.6 `05_blind_test.py` (B)
- Input per kasus: **hanya** nameplate, limit, weekly data sampai minggu trip, similar incidents (exclude diri sendiri). Tanpa deck RCA, tanpa remark "FAILURE — …".
- Prompt dikunci, 1 run per kasus (plus 2 run tambahan untuk cek konsistensi, opsional).
- Grading: tim menilai manual top-1 / top-3 match terhadap ground truth §3.4 (Match / Partial / Miss) + alasan. Opsional LLM-judge sebagai pembanding, tapi **nilai resmi = penilaian manusia**.
- Output `blind_test.json`: `{tag, ai_top3[], ground_truth, grade_top1, grade_top3, notes}` + ringkasan "x/5 top-1, y/5 top-3". **Laporkan apa adanya**, termasuk yang miss.
- Catatan jujur: parameter seperti "Lube Oil Water Content" (RCA2) dan "Feed Heavy-ends" (RCA4) memberi petunjuk kuat. Sebutkan ini di appendix.

### 4.7 `06_export.py` → `prototype/src/data/`
- `overview.json` (agregat 380 incident: KPI, by plant × mechanism, monthly loss, top bad actors, open/overdue)
- `incidents.json` (kolom yang dibutuhkan UI saja)
- `equipment/{tag}.json` (meta + params + weekly + `timeline[w]` {health, status, ttt, driver, priority, reasons, cod})
- `energy/{tag}.json` (hourly kWh, SEC, forecast, deviasi)
- `ai/{tag}.json` (root cause, RCA draft, action guidance, signature, similar incidents, roll-out)
- `backtest.json`, `blind_test.json`, `kpi_dictionary.json`, `data_sources.json`
- Target total JSON < 3 MB. Hourly data boleh di-downsample kalau perlu.

---

## 5. Konsep UI Global

- **Header:** logo "PlantPulse", nav, dan **Global Time Machine**: slider tanggal (2025-10-23 → 2026-08-31, step 1 minggu) + tombol ▶ Play (auto-advance ±1 detik/minggu) + label "Simulated date". Semua halaman membaca `simDate` dari Zustand store dan hanya menampilkan data ≤ simDate.
- **Preset tombol:** "Jump to: PU-2101B early warning (5 Feb 2026)" dll. untuk demo video.
- **Badge AI konsisten:** setiap blok AI punya label "AI-generated · confidence · sources", tombol **Approve / Edit / Reject**, dan status review. Klik sumber → buka drawer bukti.
- **Warna status:** Normal hijau, Watch kuning, Alarm oranye, Critical merah. Prioritas P1–P4 sebagai chip.
- Tampilan desktop-first (juri buka di laptop), tapi tetap tidak rusak di layar 1280px.
- Footer kecil: "Prototype for CALIBER 2026 · data: CALIBER sample data · synthetic items labelled".

---

## 6. Halaman & Komponen

### P1. `/` Executive Overview (#7, #10, KQ2)
- KPI tiles: Total loss (YTD s/d simDate), Downtime hours, **Open risk $44.3M / 220 items**, **Overdue CAPA count**, Availability (5 monitored assets), Active P1/P2 alerts.
- Heatmap Plant × F Mechanism (loss $), dengan filter discipline.
- Monthly loss trend (bar) + count (line).
- Pareto: loss by mechanism & by component (Leakage 101 kasus, dst.).
- "Top bad actors" table.
- Panel **Active alerts** (dari 5 equipment pada simDate) → klik ke Equipment Detail.
- Panel Energy mini (total kWh 5 assets, SEC deviation) → ke Energy.
- AI Executive Brief (1 paragraf, badge AI).

### P2. `/alerts` Problem Tank: Alert Queue (#2)
- Tabel terurut priority score: tag, equipment, plant, status, health, TTT + driver, priority chip, **reasons**, cost-of-delay/week, owner, age.
- Toggle "Legacy view" yang meniru dashboard lama (semua alarm sama warna, tanpa urutan) untuk kontras before/after.
- Alarm-flood grouping (F, opsional): beberapa parameter breach di satu equipment digabung ke 1 card.

### P3. `/equipment/:tag` Equipment Detail (#1, H)
- Header: nameplate, class, criticality, spare, health gauge, status, priority chip.
- 4 chart tren mingguan (1 per parameter): garis data s/d simDate, garis **alarm** & **trip**, **proyeksi TTT** (putus-putus) dari fit, marker "Legacy ALARM" & "PlantPulse WATCH".
- Kartu "Time to trip: ~X days (driver: …)", "Cost of delay", "Priority reasons".
- Panel "Last 48h (hourly PI)", hanya muncul saat simDate dekat trip.
- **What-if slider (opsional, cukup PU-2101B):** geser seal flush flow / ramp rate → TTT & expected loss dihitung ulang di frontend (pakai fungsi yang sama dengan pipeline, port ke TS).
- Tombol "Diagnose →" dan "Create action →".

### P4. `/equipment/:tag/diagnose` Diagnose (#4, C, #5, A)
Tab:
1. **Signature match (C):** chart radar/bar channel signature + top-3 match dengan % dan penjelasan.
2. **Similar incidents (#4):** top-5 kartu (title, plant, date, downtime, loss, status, similarity %), statistik kelompok.
3. **Probable root causes (#5):** 3 hipotesis dengan kategori 4M+1E, confidence, evidence chips, checklist "Verify first", Approve/Reject per hipotesis.
4. **RCA draft (A):** render mirip form perusahaan (header "RCA & CAPA/PAA | AR-… | TAG"), bagian 4P tabel G/NG, 4M+1E, root cause statement, CAPAA. Banner: "AI draft — requires reliability engineer review". Tombol "Export PDF" boleh dummy.

### P5. `/actions` Action Tracker (#6, D, E)
- Kanban kolom mengikuti status perusahaan: NEW REGISTERED → RCA PROCESS → CA/PA EXECUTION → MONITORING RESULT → RISK CLOSED. Isi = incident open dari DB (220) + card baru dari alert 5 kasus.
- Action card: action, rc ref, PIC, due date, SLA, progress, guidance steps (AI).
- **Overdue radar:** list yang lewat `RCA Due Date` per simDate (termasuk 5 kasus RCA).
- **CAPA effectiveness (E):** untuk 5 kasus, setelah repair, cek minggu-minggu berikutnya kembali NORMAL → saran "Move to RISK CLOSED" + mini chart bukti. Kalau memburuk lagi, saran reopen.
- **Pro-active roll-out (D):** "Apply to similar equipment" → list tag/plant dari 380 incident.
- Filter by PIC / discipline / plant.

### P6. `/impact` Backtest & Impact (#3, B)
- Timeline 5 kasus (Gantt-like): Legacy ALARM, PlantPulse WATCH/P1, Trip. Tampilkan lead time.
- Tabel: lead days, actual loss, avoided loss (capture rate slider), total.
- ROI panel: avoided loss/tahun (ekstrapolasi ke 380 incident dengan asumsi yang ditulis), biaya implementasi (asumsi), payback.
- **Blind test (B):** tabel AI top-3 vs verified root cause, grade, dan skor total. Disclaimer metodologi.
- KPI success metrics: alarm→WO lead time, % P1 actioned < 48h, CAPA on-time closure, MTBF, jam validasi data/insiden.

### P7. `/energy` Energy Intelligence (#9, G)
- Pilih equipment → hourly kW, SEC, forecast 7 hari + interval.
- SEC deviation alert → link ke Equipment Detail ("energy as health signal").
- Panel plant-level & emissions berlabel **Illustrative (synthetic)** + catatan roadmap.
- Kotak asumsi: voltage, PF, tarif listrik.

### P8. `/data` Data Foundation (#8, KQ1)
- Diagram source → integration → governed model (key `Tag Number`) → apps. Sources: PI Historian (Production Data), CMMS/SAP PM, Incident/RCA DB, Condition Monitoring, Energy meters (proposed), LIMS (proposed).
- **KPI Dictionary** tabel: KPI, definisi, formula, sumber, owner, refresh.
- **Dashboard rationalization matrix:** dashboard lama per fungsi (ilustratif) → panel PlantPulse mana yang menggantikan.
- Data quality panel: contoh temuan nyata (inkonsistensi hourly vs weekly) sebagai bukti perlunya governed foundation.

---

## 7. Alur Demo (untuk video 3 menit)

Kasus utama: **RCA2 KO-3201** ($1.58M, tanpa spare, paling dramatis). Kasus cadangan: RCA1 PU-2101B.
1. (0:00–0:20) Overview: "$67M lost, 220 open risks, 5 failures seen but not acted on."
2. (0:20–0:50) Time Machine play → KO-3201 masuk WATCH jauh sebelum legacy alarm → naik jadi P1 di Alert Queue, lengkap dengan reasons & cost of delay.
3. (0:50–1:40) Diagnose: signature "water-in-oil / lubrication" → similar incidents → probable root cause dengan evidence → RCA draft form.
4. (1:40–2:15) Action: card ke PIC, SLA, roll-out ke equipment serupa, CAPA verification.
5. (2:15–2:45) Impact: backtest 5 kasus, avoided loss, blind test score.
6. (2:45–3:00) Data foundation + penutup.
Rekam 1080p, export 720p H.264 ±300 kbps → target ≤ 7 MB.

---

## 8. Kriteria Selesai (Acceptance)

- [ ] Semua angka di Overview cocok dengan sheet `Dashboard` Incident DB (380 / 2,261.1 h / $67,194k).
- [ ] Time Machine menggerakkan semua halaman; tidak ada data "dari masa depan" yang bocor.
- [ ] 5/5 kasus menunjukkan WATCH/P1 ≥ 35 hari sebelum trip di backtest.
- [ ] Setiap output AI punya sumber, confidence, dan Approve/Reject.
- [ ] Label "Illustrative (synthetic)" di semua data non-asli.
- [ ] UI 100% bahasa Inggris, tanpa typo.
- [ ] Tidak ada API key/secret di bundle (`grep -r "sk-" prototype/dist` kosong).
- [ ] Bisa dibuka via link Vercel di browser incognito tanpa login; load < 3 detik.
- [ ] Tiap Key Question punya halaman yang jelas (§9).
- [ ] `ai_runs/validation_notes.md` berisi hasil cek manual output AI vs deck RCA.

---

## 9. Mapping ke Key Questions & Penilaian

| Key Question / kriteria | Di prototype |
|---|---|
| KQ1: Rasionalisasi dashboard & data foundation | P8 Data Foundation (source map, KPI dictionary, rationalization matrix, data quality) |
| KQ2: Single pane of glass + Energy Forecasting, Similar-incident Retrieval, AI Root Cause Indication | P1 Overview, P7 Energy, P4 Diagnose |
| KQ3: Problem Tank, Root Cause Indication, Alert Prioritization, Action Tracking, Action Guidance | P2 Alert Queue, P4 Diagnose, P5 Action Tracker |
| Business impact | P6 Impact (backtest, ROI, KPI) |
| Traceability / human oversight / security | Badge AI + Approve/Reject di mana-mana; catatan deployment (Azure OpenAI/private endpoint) di deck |
| Chemical domain relevance | Konten 4P/4M+1E, signature library, istilah API seal plan, NPSH, fouling, babbitt |

---

## 10. Milestone (26 Sep – 1 Okt)

| # | Tanggal | Output | Cek |
|---|---|---|---|
| M0 | 26 Sep pagi | Scaffold folder, `.env`, `.gitignore`, install deps, Vite app kosong | `npm run dev` jalan |
| M1 | 26 Sep | `01_extract.py` + `equipment_meta.json` → interim JSON | Angka cocok dengan §3 |
| M2 | 27 Sep | `02_analytics.py` (health, TTT, status, priority, COD, backtest, energy, signature) | Backtest 5/5 ≥ 35 hari |
| M3 | 27–28 Sep | `03_embed` + `04_ai_generate` + `05_blind_test` + validasi manual | `validation_notes.md` terisi |
| M4 | 28–29 Sep | Frontend P1, P2, P3 + Time Machine | Demo alur detect → prioritize |
| M5 | 29–30 Sep | P4, P5, P6 | Alur penuh 1 kasus jalan |
| M6 | 30 Sep | P7, P8, polish UI, copy English | Acceptance §8 |
| M7 | 1 Okt | Deploy Vercel, test incognito, freeze | Link final ke tim |
| — | 2 Okt | Rekam video (§7) | ≤ 7 MB |
| — | 3–4 Okt | Deck 7 slide + appendix, submit (siang 4 Okt) | Total ≤ 10 MB |

**Kalau waktu mepet, potong urutan ini:** What-if slider → alarm-flood grouping → CAPA effectiveness (E) → energy forecast (sisakan kWh/SEC saja) → export PDF. **Jangan potong:** Time Machine, Alert Queue, Diagnose (C + #5 + A), Backtest, Blind test.

---

## 11. Prompt Pembuka untuk Chat Baru

Salin ini ke chat Claude baru (working dir: folder `Caliber 2026`):

```
Baca docs/plan_prototype.md, docs/keputusan_build.md, dan docs/daftar_ide.md.
Kita mau build prototype PlantPulse sesuai plan itu. Mulai dari milestone M0 dan M1.
Pakai venv di /Users/timotiuspatrick/Documents/Patrick/Kuliah & Coding/.venv.
LLM pakai OpenAI (key ada di .env). UI harus bahasa Inggris.
Setelah tiap milestone, kasih ringkasan + cek acceptance, lalu tunggu konfirmasi sebelum lanjut.
```
