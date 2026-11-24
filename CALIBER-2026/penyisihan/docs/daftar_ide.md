# Daftar Ide / Fitur: Case 2 (PlantPulse)

Konteks: lihat [analisis_case_dan_ide.md](analisis_case_dan_ide.md). Semua input di bawah merujuk ke file di `Supporting Data/Case 2_ Intelligence Manufacturing/`.

Singkatan file:
- **CH**: `Equipment Performance - RCAx` → sheet *Condition History* (26 minggu, 4 parameter, health status)
- **EI**: sheet *Equipment Info* (nameplate + batas alarm/trip per parameter)
- **PS**: sheet *Performance Summary* (availability, MTBF, MTTR, production loss, est. loss)
- **PI**: `Production Data - RCAx` (per jam, 720 jam: FEED, DISP, VIB, TEMP, **AMP**, PLANT_RATE, RUN_STATUS)
- **IDB**: `Incident Database.xlsx` (380 incident: tag, eq type, component, F mechanism, risk score, PIC, status, due date, downtime, loss)
- **RCA**: 5 deck `RCAx - ....pptx` (chronology, 4P, 4M+1E, CAPA, PIC)

---

## Ringkasan Rating

Skala 1–5. **Juri** = seberapa besar dampaknya ke skor juri (problem, impact, novelty). **Build** = gampang dibuat dalam 9 hari (5 = paling gampang). **Beda** = diferensiasi dari tim lain. **KQ** = Key Question yang dijawab.

| # | Ide | KQ | Juri | Build | Beda | Total | Status |
|---|---|---|---|---|---|---|---|
| 1 | **Early Warning + Time-to-Trip** | 3 | 5 | 5 | 4 | **14** | ⭐ Core |
| 2 | **Alert Priority Engine** | 3 | 5 | 4 | 4 | **13** | ⭐ Core |
| 3 | **Backtest & Impact Simulator** | Impact | 5 | 4 | 5 | **14** | ⭐ Core (senjata utama) |
| 4 | **Similar-Incident Retrieval** | 2, 3 | 4 | 5 | 3 | **12** | ⭐ Core (wajib, disebut eksplisit di KQ2) |
| 5 | **AI Root Cause Indication (4M+1E)** | 2, 3 | 5 | 3 | 4 | **12** | ⭐ Core (wajib, disebut eksplisit) |
| 6 | **Problem Tank + Action Tracker** | 3 | 5 | 4 | 3 | **12** | ⭐ Core (wajib, disebut eksplisit) |
| 7 | **Executive Single Pane Dashboard** | 2 | 4 | 4 | 2 | 10 | Wajib (KQ2) |
| 8 | **Data Source Map + KPI Dictionary** | 1 | 4 | 4 | 2 | 10 | Wajib (KQ1) |
| 9 | **Energy Forecasting + SEC monitor** | 2 | 3 | 3 | 3 | 9 | Wajib (disebut di KQ2), versi kecil |
| 10 | Bad Actor & Recurrence Pareto | 2 | 3 | 5 | 1 | 9 | Masuk ke dashboard (#7) |
| 11 | "Ask PlantPulse": chat NL di atas dashboard | 2 | 2 | 3 | 1 | 6 | ❌ Skip (pasaran, makan waktu) |
| 12 | Mobile shift-brief / notifikasi WA | 3 | 2 | 4 | 2 | 8 | Opsional, cukup mockup 1 layar |

**Rating tertinggi: #1 + #3 (Early Warning + Backtest).** Dua ide ini yang bikin cerita *"5 kegagalan senilai $2.58M sebenarnya sudah kelihatan 6–15 minggu sebelumnya"*. Fitur lain adalah rantai lanjutan dari alert itu (#2 → #4 → #5 → #6). #7, #8, dan #9 wajib ada karena diminta eksplisit di Key Questions, tapi bukan pembeda.

**Alur demo (1 alert, dari awal sampai akhir):**
`#1 alert muncul` → `#2 jadi P1` → `#4 3 incident mirip` → `#5 probable cause + sumber` → `#6 action card ke PIC, tracking` → `#3 "tercegah $226k"`, dengan `#7` sebagai layar pembuka dan `#8` di slide/appendix.

---

## Detail per Ide

### 1. Early Warning + Time-to-Trip ⭐
**Apa:** Setiap equipment dapat *health score* dan estimasi "berapa hari lagi sampai trip" dari tren degradasi parameter.
- **Input:**
  - CH: 4 parameter mingguan (mis. RCA1: vibration, seal flush flow, discharge pressure, bearing temp)
  - EI: batas alarm/trip tiap parameter (mis. vibration 7.0 / 11.0 mm/s; seal flush 5.0 / 4.0 L/min)
  - PI: data per jam untuk deteksi anomali jangka pendek (48 jam terakhir)
- **Proses:** regresi linear / EWMA pada 4–6 titik terakhir per parameter → ekstrapolasi ke batas trip → ambil parameter tercepat. Health score = jarak ke limit (0–100).
- **Output:**
  - Health score per equipment (0–100) + status Normal/Watch/Alarm/Critical
  - **Estimasi hari ke trip** + parameter penyebabnya (mis. "Seal flush flow, ±21 hari")
  - Grafik tren + garis limit + proyeksi
- **Feasible?** ✅ Data lengkap untuk 5 equipment. Logika sederhana dan transparan (juri bisa ikuti).
- **Sudah dites (25 Sep):** regresi linear 6 minggu terakhir, flag kalau estimasi ≤ 8 minggu ke trip:

  | Kasus | Flag pertama | Parameter pemicu | Estimasi | Trip aktual | Lebih awal |
  |---|---|---|---|---|---|
  | RCA1 PU-2101B | 5 Feb | Vibration 7.88 mm/s | 7.0 mgg | 12 Mar | 35 hari |
  | RCA2 KO-3201 | 25 Mar | DE radial vib 55.9 µm | 5.9 mgg | 29 Apr | 35 hari |
  | RCA3 PM-4405B | 27 May | Winding temp 117.8 °C | 7.6 mgg | 8 Jul | 42 hari |
  | RCA4 HE-3301 | 16 Apr | Heat duty 83.1 % | 6.8 mgg | 21 May | 35 hari |
  | RCA5 BL-5702 | 13 May | Vibration 7.98 mm/s | 6.6 mgg | 17 Jun | 35 hari |

  Semua 5 kasus ter-flag **5–6 minggu sebelum trip**. Estimasi linear cenderung sedikit terlalu optimis (degradasi makin cepat menjelang failure), jadi perbaikannya pakai fit eksponensial/kuadratik atau safety factor.
- **Batasan data:** cuma 5 equipment × 26 minggu × 1 failure masing-masing. Tidak cukup untuk training model ML, jadi pendekatannya **trend + limit (rule-based)**, dan ML disebut sebagai roadmap setelah data historian penuh tersedia. Kalau dashboard perlu lebih banyak equipment, tambahkan equipment dummy "sehat" dan beri label jelas.

### 2. Alert Priority Engine ⭐
**Apa:** Mengurutkan alert supaya yang paling mahal & paling mendesak ditangani dulu, bukan sekadar "semua merah".
- **Input:**
  - Output #1 (hari ke trip, health score)
  - IDB: `Risk Score`, `Pre-Risk`, `Eq. Class` (A/B)
  - PS: `Production Loss (ton)`, `Estimated Loss` → loss per jam downtime
  - EI: criticality, ada spare (mis. PU-2101A standby) atau tidak
- **Proses:** skor = urgensi (1/hari ke trip) × konsekuensi (loss/jam × MTTR historis) × faktor kritikalitas (Class A > B, tanpa spare > dengan spare). Hasil dipetakan ke P1–P4.
- **Output:**
  - Daftar alert P1–P4 yang terurut
  - **Breakdown alasan** per alert ("P1 karena: 21 hari ke trip, loss $12k/jam, Class A, tanpa spare")
  - Expected loss kalau tidak ditindak ($)
- **Feasible?** ✅ Rumus bisa di-tuning, dan transparansi = poin "traceable".

### 3. Backtest & Impact Simulator ⭐ (senjata utama)
**Apa:** Replay data historis 5 kasus: kapan sistem akan alert, berapa loss yang bisa dicegah.
- **Input:** CH + EI (untuk replay #1 dan #2 minggu per minggu), PS (loss aktual), RCA (tanggal trip aktual & chronology)
- **Proses:** jalankan #1 dan #2 secara "time-travel" per minggu, lalu catat tanggal pertama jadi P1/P2.
- **Output:**
  - Timeline per kasus: *"PlantPulse alert P1: 29 Jan · Trip aktual: 12 Mar · Lead time 42 hari"*
  - Tabel 5 kasus: lead time, loss aktual, loss tercegah (skenario konservatif/realistis)
  - **Slider ROI**: % tercegah → $ saved/tahun, payback period (dipakai di slide Business Impact)
- **Feasible?** ✅ Data sudah terbukti mendukung (6–15 minggu lead time, $2.58M).

### 4. Similar-Incident Retrieval ⭐
**Apa:** Saat ada alert, tampilkan kejadian masa lalu yang paling mirip beserta penyebab dan penyelesaiannya.
- **Input:**
  - IDB 380 baris: `Risk Case Title`, `Eq. Type`, `Component`, `F Mechanism`, `Discipline`, downtime, loss, status
  - RCA 5 deck: root cause terverifikasi + CAPA (sebagai "knowledge" yang lebih kaya)
  - Konteks alert dari #1 (equipment type + parameter yang breach)
- **Proses:** skor kemiripan = match terstruktur (eq type, component, mechanism) + kemiripan teks (TF-IDF/embedding pada judul). 380 baris kecil, jadi bisa di-precompute.
- **Output:**
  - Top 3–5 incident mirip + % kemiripan
  - Untuk tiap incident: root cause, CAPA, downtime, loss, status, link ke RCA
  - Statistik: "Seal leakage di pompa: 7 kejadian, rata-rata downtime X jam"
- **Feasible?** ✅ Sangat. Catatan: hanya 5 incident yang punya deck RCA lengkap, sisanya cuma metadata.

### 5. AI Root Cause Indication (4M+1E) ⭐
**Apa:** LLM menyusun hipotesis probable cause terurut, lengkap dengan bukti & sumber, dalam format yang biasa dipakai tim reliability (4P / 4M+1E).
- **Input:**
  - Parameter yang menyimpang dari #1 (mis. seal flush ↓, vibration ↑, bearing temp ↑)
  - Hasil #4 (incident mirip + root cause mereka)
  - RCA: struktur 4P / 4M+1E sebagai template & contoh
  - EI: spesifikasi equipment (mis. seal plan, NPSH)
- **Proses:** LLM dengan prompt terstruktur + retrieval hanya dari sumber di atas, wajib sitasi. Untuk prototype: **pre-generate** output untuk 5 kasus (tidak perlu live API).
- **Output:**
  - 3 probable cause terurut + confidence (High/Med/Low)
  - Tiap cause: bukti (parameter mana, trennya), sumber (incident ID / slide RCA), kategori 4M+1E
  - **"Verify first" checklist** (mis. "cek seal flush orifice, cek NPSH margin")
  - Tombol Approve / Reject oleh engineer (human-in-the-loop)
- **Feasible?** ✅ dengan pre-generate. Validasi: bandingkan output AI vs root cause asli di deck RCA sebagai bukti akurasi di appendix.

### 6. Problem Tank + Action Tracker ⭐
**Apa:** Setiap alert/insight jadi "problem card" dengan action, owner, due date, dan progress. Kalau overdue, eskalasi otomatis.
- **Input:**
  - Output #2 (prioritas), #5 (root cause yang di-approve)
  - RCA: daftar CAPA/PAA + PIC + status sebagai contoh action
  - IDB: `PIC (RCA)` (13 PIC), `Overall Status` (6 status), `RCA Due Date`
- **Proses:** mapping root cause → template action (dari CAPA historis) → assign PIC sesuai discipline → SLA due date berdasarkan prioritas.
- **Output:**
  - Kanban: New → RCA → CA/PA Execution → Monitoring → Closed
  - Action card: apa, siapa (PIC), kapan, langkah (guidance), bukti penyelesaian
  - **Overdue radar**: contoh nyata 5 RCA yang lewat due date
  - KPI: CAPA on-time closure %, rata-rata umur problem
- **Feasible?** ✅ UI + data IDB (220 item open = isi kanban nyata).

### 7. Executive Single Pane Dashboard (wajib KQ2)
- **Input:** IDB (agregat per plant, mechanism, bulan), PS (availability, MTBF, MTTR), PI (`PLANT_RATE`), output #1/#2/#6/#9
- **Output:**
  - KPI tiles: total loss YTD, downtime, open risk ($44.3M, 220 item), availability, CAPA on-time %
  - Heatmap plant × failure mechanism, tren loss bulanan, Top 10 bad actors (#10)
  - Panel "Active P1 alerts" (dari #2) dan panel energi (dari #9)
- **Feasible?** ✅ Standar. Pembedanya: angka asli + klik alert tembus ke #1–#6.

### 8. Data Source Map + KPI Dictionary (wajib KQ1)
- **Input:** skema kolom semua file (IDB, CH/EI/PS, PI + metadata `PI Tag`), plus sistem yang lazim di plant (PI historian, SAP PM/CMMS, LIMS, energy meter), diberi label "proposed"
- **Output:**
  - Diagram arsitektur/lineage: source → integration layer → governed data model (key: `Tag Number`) → dashboard/AI
  - **KPI Dictionary**: nama, definisi, formula, owner, sumber (mis. Availability = (Period − Downtime)/Period, dari PS)
  - Matriks rasionalisasi: dashboard lama per fungsi → digabung ke panel mana
- **Feasible?** ✅ Mostly slide/appendix + 1 layar di prototype.

### 9. Energy Forecasting + SEC Monitor (wajib disebut KQ2)
**Temuan baru:** semua 5 file PI punya **motor ampere (`_AMP`) + `PLANT_RATE` per jam**, jadi ada *proxy energi nyata*: kW ≈ √3 × 380 V × A × PF (asumsi PF 0.85) → kWh/jam, dan SEC = kWh/ton.
- **Input:** PI `_AMP`, `PLANT_RATE`, `RUN_STATUS` (5 equipment × 720 jam); tegangan & PF dari datasheet/asumsi. Untuk level plant: data sintetis yang disebut jelas di deck.
- **Proses:** hitung kWh & SEC per jam → forecast 7 hari (moving average musiman / Prophet) → deteksi deviasi SEC.
- **Output:**
  - Konsumsi energi per equipment + forecast 7 hari dengan interval
  - **SEC deviation alert** (mis. "motor ampere naik 8% di throughput sama → indikasi degradasi"), sehingga energi terhubung balik ke early warning #1
  - Estimasi biaya energi berlebih (Rp/kWh PLN industri)
- **Feasible?** ⚠️ Bisa, dengan catatan: hanya level equipment dan hanya 1 bulan per kasus. Jujur soal asumsi.

### 10. Bad Actor & Recurrence Pareto (masuk ke #7)
- **Input:** IDB (tag, eq type, component, mechanism, loss, downtime)
- **Output:** Pareto loss per mechanism/component, daftar equipment/eq type berulang, rekomendasi program reliability (mis. "Leakage = 101 kasus → program seal management")

### 11. ❌ "Ask PlantPulse" chat
Skip. Ide paling umum, tidak menjawab KQ secara spesifik, makan waktu. Cukup satu kotak "Ask" kecil di mockup kalau mau.

### 12. Mobile shift-brief (opsional)
- **Input:** output #2 + #6 untuk area/PIC tertentu
- **Output:** 1 layar mobile "Pagi ini: 1 P1, 2 action overdue", menunjukkan adopsi di lapangan. Cukup 1 frame mockup.

---

## Pembagian ke Deliverables
- **Prototype:** #7 (home) → #1/#2 (alert detail) → #4 + #5 (diagnose) → #6 (action) → #3 (backtest page) → #9 (energy tab)
- **Deck:** Slide 3 Solution = alur #1→#6 · Slide 4 Impact = #3 · KQ1 = #8 (appendix detail)
- **Video 3 menit:** walk-through 1 kasus (RCA1 atau RCA2, yang loss-nya $1.58M, paling dramatis) dari alert sampai "tercegah"

---

## Interaksi Prototype: Slider

Dua jenis slider:
1. **Time Machine (replay):** slider minggu 1–26 per equipment. Digeser → grafik tren, health score, estimasi hari ke trip, dan prioritas ikut berubah. Saat melewati titik tertentu, alert muncul dan rantai #2 → #4 → #5 → #6 ikut terisi. Di akhir tampil garis "trip aktual" + "PlantPulse alert 35 hari lebih awal". **Pakai data asli, jadi paling meyakinkan.** Ini inti demo video.
2. **What-if:** slider parameter (mis. seal flush flow, ramp rate feed) → time-to-trip & expected loss dihitung ulang. Cocok untuk menunjukkan "kalau action X dilakukan, risiko turun ke ...".

Rekomendasi: Time Machine wajib, What-if opsional (1 equipment saja).

---

## Diferensiasi AI (supaya tidak sama dengan tim lain)

Yang hampir pasti dibuat tim lain: dashboard + chatbot "tanya data" + "AI predictive maintenance" generik. Yang di bawah ini spesifik ke data & proses Chandra Asri:

| # | Fitur AI | Kenapa beda | Input | Output | Rating |
|---|---|---|---|---|---|
| A | **Auto-draft RCA Report** dalam format form perusahaan (Procedure RCA-P-0050-03 / Form RCA-F-0075-02) | Juri dari Chandra Asri langsung mengenali form mereka sendiri; menghemat jam kerja reliability engineer | Chronology dari data (alarm → trip), parameter breach (CH/EI/PI), incident mirip (#4), datasheet | Draft 11 bagian: problem statement, chronology, 4W impact, target, **4P table (G/NG + bukti)**, **4M+1E**, root cause statement, matrix prioritas, CAPA + pro-active action, PM schedule. Engineer tinggal review/approve | ⭐⭐⭐ |
| B | **Blind-test akurasi AI** | Tim lain cuma klaim "AI akurat". Kita punya bukti | 5 kasus: sembunyikan deck RCA, AI hanya dapat data CH/PI/IDB | Tabel "AI prediksi vs root cause terverifikasi" (mis. 4/5 match) → appendix + 1 kalimat di deck | ⭐⭐⭐ |
| C | **Failure Signature Matching** (kemiripan *pola tren*, bukan teks) | Similar-incident biasa hanya cocokkan teks. Ini mencocokkan *bentuk* degradasi multi-parameter (mis. seal flush ↓ + vib ↑ + temp ↑ = pola dry-running) | 4 parameter CH yang dinormalisasi terhadap limit (5 kasus sebagai library signature) | "Pola ini 87% mirip RCA1 (dry-running seal)" → langsung bawa root cause & CAPA kasus itu | ⭐⭐⭐ |
| D | **Pro-Active Roll-out Finder** | Form RCA mereka punya bagian "roll-out to similar equipment" yang saat ini manual | CAPA terverifikasi + IDB (380 incident: eq type, component, plant) | Daftar equipment lain yang berisiko sama ("12 pompa dengan seal leakage di 5 plant, rekomendasi roll-out flush-flow switch") | ⭐⭐ |
| E | **CAPA Effectiveness Auto-Verify** | Menutup loop: action tidak dianggap selesai sampai data membuktikan | CH minggu setelah repair (data ada: minggu 22–26 kembali normal) + status IDB | Auto-usul status "MONITORING RESULT → RISK CLOSED" + bukti grafik; kalau parameter memburuk lagi → reopen | ⭐⭐ |
| F | **Alarm Flood Grouping** | Satu masalah memicu banyak alarm; AI menggabungkannya jadi 1 problem card | Alarm serentak di beberapa parameter/equipment | 1 problem card berisi alarm terkait, bukan 4 alert terpisah (anti alert-fatigue) | ⭐ |
| G | **Energy-as-health signal** | Menghubungkan energi dan reliability: ampere/ton naik = degradasi mekanis | PI `_AMP` + `PLANT_RATE` | Alert "SEC naik 8% → cek bearing/alignment", sehingga energy forecasting (KQ2) ikut punya fungsi diagnosis | ⭐⭐ |
| H | **Cost-of-delay** | Mengubah alert jadi keputusan bisnis | Time-to-trip + loss/jam + probabilitas | "Menunda 1 minggu = +$38k risiko" di tiap problem card | ⭐⭐ |

**Rekomendasi ambil:** **A + B + C** (inti AI), D & H (murah, cukup UI), E kalau sempat.
Trust layer tetap wajib di semua fitur: sumber/sitasi, confidence, tombol approve (human-in-the-loop), dan "AI tidak yakin" kalau bukti kurang.

Cara build A/B: pakai LLM (OpenAI API, pakai credits yang ada) + prompt terstruktur yang berisi data kasus; output disimpan sebagai JSON, lalu ditampilkan di prototype (tidak perlu live). B dijalankan sungguhan dan hasilnya dilaporkan apa adanya.
