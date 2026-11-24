# 02 — Blueprint Solusi: Arah, Edge, Arsitektur, Pembagian Tugas

> Ini **baseline arah**, bukan model final. Semua angka diambil dari `analysis/eda_output.txt` dan `analysis/backtest_output.txt`. Data dummy, jadi yang kita jual adalah **mekanisme + bukti backtest**, bukan rupiah absolut.
> Deadline submit: **Kamis 5 Nov 2026, 06.00**. Wajib: MVP di Vercel + SQLite + zip + screenshot, dan deck.

---

## 1. Big idea (1 kalimat untuk juri)

**"Stop forecasting parts. Forecast the equipment that consumes them."**

Demand spare part bukan time series. Demand muncul dari tiga hal:
- **Populasi equipment** yang memasang part itu (installed base).
- **Kegagalan** equipment tersebut (notif).
- **Pekerjaan terencana** (PM dan shutdown).

Mesin kita memprediksi demand dari ketiga driver itu. Hasilnya bukan satu angka, tapi **distribusi probabilistik**. Distribusi ini langsung dipakai optimizer cost–risk berbasis criticality untuk menentukan stok.

Nama kerja: **PartPulse** (bisa diganti).

---

## 2. KQ1: bisa bikin mesin prediksi yang bagus? Bisa, dan ini buktinya

### 2.1 Kenapa forecasting biasa pasti gagal di data ini

- **79% material BoM (5.895 dari 7.481) tidak punya histori konsumsi** di jendela fit. Croston, SBA, TSB, ARIMA, Prophet, dan LSTM semuanya akan memprediksi 0 untuk material ini.
- Masalahnya, **40% material yang bergerak di periode test (344 dari 868) justru berasal dari kelompok tanpa histori itu.** Tim yang hanya mem-forecast material ber-histori sudah buta terhadap 40% kejadian sebelum mulai.
- Material yang punya histori pun sangat jarang bergerak: median 1 bulan aktif dari 17. Hanya 31 material yang polanya "smooth".
- Lonjakan Nov–Jan **bukan musiman**. Hampir seluruhnya berasal dari order tipe **2030** (907 baris di Nov 2025, padahal biasanya 15–90 baris per bulan), lalu tipe 2010 ikut naik di Des–Jan. Ini pola shutdown/turnaround. Model time series akan salah membacanya sebagai tren.

### 2.2 Sinyal yang ternyata kuat (sudah diuji)

| Sinyal | Bukti |
|---|---|
| **Installed base** (jumlah FL yang memasang material) | Material yang dipasang di 1 FL: 15% pernah bergerak. Di 2 FL: 27%. Di 3–5 FL: 51%. Di 6–10 FL: 80%. Di 11–50 FL: 97%. Korelasi log(qty) vs log(installed qty) = **0,76** |
| **Populasi PM di FL tempat part terpasang** | Fitur #1 di model "siapa yang akan bergerak" |
| **Histori notif/failure di FL tempat part terpasang** | Masuk 5 fitur teratas |
| **Kategori part** (gasket, studbolt, packing tergolong consumable; blade dan impeller tergolong insurance) | Tingkat bergerak: packing set 56%, gasket 47%, bearing 15%, blade 5% |
| **Tipe order** (2010 corrective vs 2030/2090 event) | Memisahkan base demand dari event demand |

### 2.3 Backtest out-of-time (jujur, tanpa leakage)

Fit pada Mei 2025 – Feb 2026, test pada Mar – Sep 2026 (7 bulan yang tidak pernah dilihat model). Universe-nya **semua 7.481 material**. Model ML dilatih pada cut-off yang lebih awal (Okt 2025), lalu baru diterapkan. Fitur `stock` dibuang karena snapshot-nya diambil setelah periode test.

| Metode | AUC "siapa yang bergerak" | AUC pada material tanpa histori |
|---|---|---|
| Naive mean | 0,791 | 0,500 (buta) |
| SBA (Croston) | 0,787 | 0,613 |
| TSB | 0,790 | n/a |
| **Driver-based ML (LightGBM: installed base + PM + notif + kategori + procurement)** | **0,887** | **0,841** |

Untuk **memprediksi *siapa* yang akan butuh part, driver-based jauh mengalahkan semua metode klasik**, terutama pada part tanpa histori.

**Yang belum beres (tugas Orang 1):** kalibrasi **kuantitas**.
- LightGBM 2-part overforecast +215%, karena regressor dilatih di jendela yang mengandung lonjakan TA.
- Model hybrid (LightGBM untuk "siapa" × Empirical-Bayes installed base untuk "berapa") justru underforecast −61%.
- Model EB installed-base saja di kuantil 95% menutup **74%** material yang bergerak dengan **364 ribu** unit stok. Sebagai pembanding, SBA hanya menutup **56%** dengan **993 ribu** unit.
- Catatan: unit ini campuran (EA, SET, M, dll.), jadi angka unit hanya indikatif. Metrik final harus dalam rupiah dan per kelas criticality.

### 2.4 Edge KQ1: hal yang hampir pasti tidak dikerjakan tim lain

1. **Cold-start forecasting via installed base + reliability.** Kita bisa memprediksi part yang *belum pernah dipakai*, dengan meminjam kekuatan statistik dari part sejenis (kategori) dan dari equipment sejenis (Empirical Bayes / hierarchical Poisson-Gamma). Tim lain akan memfilter "material yang ada movement" lalu menjalankan Prophet.
2. **Demand decomposition:** demand = **base** (corrective acak, order 2010/2040) + **planned** (PM per FL) + **event** (shutdown/TA, order 2030/2090). Masing-masing diramal dengan cara yang paling cocok.
   - Base: Poisson/NegBin yang di-pool per installed base.
   - Planned: kalender PM × kit part.
   - Event: *TA bill-of-parts* dari TA terakhir × skala.
3. **Output probabilistik, bukan angka tunggal.** Setiap part punya P(dibutuhkan dalam lead time) dan distribusi qty. Output ini langsung menjadi ROP dan safety stock di KQ2. Tim lain akan menyajikan MAPE, yang tidak bermakna untuk demand yang 90%-nya nol.
4. **Evaluasi dengan metrik bisnis.** Yang ditunjukkan adalah "berapa part kritis yang ter-cover per rupiah stok", bukan MAPE. Kita sajikan kurva trade-off backtest di deck.
5. **Inferensi kit PM (PM → part).** Data Mplan tidak memuat part (diakui di diagram data). Kita isi celah ini dengan menebak kit dari BoM FL + tipe task + histori issue. Ini membuka sinyal "known future demand" yang diminta brief (hal. 7, butir 6).
6. **Abnormal consumption detector.** Flag issue yang jauh di atas distribusi part itu (misalnya studbolt 96 EA dalam satu order). Ini termasuk butir "abnormal or unexpected consumption" di KQ1.

---

## 3. KQ2: alur integrasi data terbaik + optimizer

### 3.1 Alur data (dari 6 file ke keputusan)

```
 RAW (6 Excel)                    CLEAN / CONFORM                     FEATURE & MODEL                      DECISION                     APP
 ─────────────                    ───────────────                     ───────────────                      ────────                     ───
 FuncLoc list ──┐                 dim_funcloc (crit S/A/B/C,          equipment_driver                     part_policy                  Web (Vercel)
                │                   parent/child dari kode FL)          (#notif, #N2, #PM due per FL)       (ROP, SS, Min, Max,           + Mobile
 BoM ───────────┼─► dedup 230 ─►  bridge_fl_material                   material_features                    service level per crit)
                │   baris dup      (installed qty, criticality         (installed base, kategori,
 Notif History ─┤                   terkuat = crit part)               lead-time dist, harga)              part_risk
                │                 fact_issue (order type 2010/2030..)                                       (P stockout dlm LT,
 Movement ──────┤                 fact_notif  (durasi, telat)          demand_forecast                      expected downtime cost)
                │                 fact_po (LT = PO-del − PR-date,      (P(move), qty P50/P90/P95,
 PR PO ─────────┤                   slip, harga unit IDR, kurs)         base/planned/event)                  action
                │                 fact_pm_due (cycle dinormalisasi                                           (REORDER / MAINTAIN /
 Mitem & Mplan ─┘                   dari 28 format → bulan,           pm_kit_inferred                       REDUCE / MONITOR /
                                    next due date)                     (FL × task → part)                    DISPOSE + alasan)
                                  dq_issues (tabel temuan kualitas
                                    data, ditampilkan di app)                                               scenario_frontier
                                                                                                            (budget ↔ risk)
```

**Bridge kunci yang kita bangun (dan jadi nilai jual data architecture):**
- **Order → FL.** Hanya 20,5% order movement yang punya notif. Untuk sisanya, FL disimpulkan dari BoM (FL mana yang memasang material itu), dengan skor keyakinan.
- **Material → criticality.** Criticality material = max criticality FL tempat ia terpasang. Material yang terpasang di banyak FL juga mendapat skor *commonality* (risk pooling).
- **Lead time sebagai distribusi**, bukan satu angka. Diambil per material, atau di-fallback ke kategori, supplier, lalu mata uang/impor. Datanya: median 42 hari, P90 155 hari, impor ~210 hari, CV dalam material 0,38.
- **Harga:** baru ada untuk 16% material. Fallback ke median kategori × unit, dan diberi flag "estimated".

### 3.2 Optimizer cost–risk (inti KQ2)

Untuk setiap material *i* dan level stok *s*:

```
Expected cost(s) = holding_rate × unit_price × s                                  (carrying)
                 + P(demand selama LT > s) × [emergency premium + downtime_cost(crit) × downtime_days]   (risk)
```

- Demand selama LT diperoleh dari konvolusi distribusi demand KQ1 dengan distribusi lead time (Monte Carlo).
- `downtime_cost(crit)` dan `holding_rate` adalah **asumsi yang diatur lewat slider** dan masuk ke assumption register, karena data downtime tidak tersedia.
- Output per part:
  - s* optimal, yang menjadi **Min (ROP)**. **Max** = ROP + EOQ, atau lot procurement historis.
  - Aksi: **REORDER** jika stok di bawah ROP dan ada demand, **REDUCE/DISPOSE** jika stok melebihi Max dan P(move) rendah, **MAINTAIN**, atau **MONITOR**.
- **Portfolio view (pembeda):** semua part disusun berdasarkan "risk dikurangi per rupiah". Hasilnya **efficient frontier** budget inventory vs expected downtime cost. Slider budget menunjukkan part mana yang masuk atau keluar dari daftar. Ini menjawab langsung butir brief *"scenario simulation of increasing or reducing inventory levels"*.
- **Guardrail PR:** PR baru dicek terhadap stok, Max, P(move), dan open PO. Dasarnya F5: 35,5% spend dipakai untuk material yang stoknya sudah di atas Max.

### 3.3 Edge KQ2

1. **Criticality × probabilistic lead time.** Brief bilang criticality dan lead time "not consistently considered". Kita memasukkan keduanya ke satu fungsi biaya, bukan sekadar label.
2. **Efficient frontier + slider** di app. Juri bisa menggeser budget dan langsung melihat trade-off-nya.
3. **Explainability per rekomendasi.** Contoh: *"REORDER 4 EA: terpasang di 12 FL kritis S; 3 notif leak 90 hari terakhir; LT P90 160 hari; stok 0."* Penjelasan ini dibuat dengan template, lalu diringkas LLM. Rekomendasi tetap butuh persetujuan planner (human in the loop).
4. **Data quality sebagai fitur.** Panel yang jujur menampilkan duplikat, cycle tidak standar, harga hilang, dan order tanpa notif. Panel ini sekaligus menjawab bagian governance dan risk di slide Roadmap & Risk.

---

## 4. Web (Vercel) + App HP: bisa? Bisa, dengan arsitektur ini

```
Python pipeline (offline, laptop)        Next.js on Vercel                         Clients
───────────────────────────────          ───────────────────                       ───────
6 Excel → clean → forecast → optimize    /api/* (Route Handlers)                   1. Web dashboard (desktop):
  → partpulse.db (SQLite, ±10–30 MB)  ─►    baca SQLite read-only (better-sqlite3)    Overview, Forecast, Optimizer,
                                            scenario dihitung on-the-fly            Part detail, Data Quality
                                            (tanpa write ke disk)                   2. Mobile:
                                                                                      a) PWA (installable dari browser)
                                                                                      b) Expo React Native app → API yang sama
```

- **Satu API, dua client.** Web dan HP memanggil endpoint yang sama, jadi tidak ada duplikasi logic.
- **Rekomendasi:**
  - **PWA wajib dulu.** Satu codebase, layout mobile-first, bisa di-"Add to Home Screen". Biayanya hampir nol.
  - **Expo app jadi bonus** kalau ada satu orang yang bebas setelah jam ~01.00. Bisa didemokan lewat Expo Go/QR saat pitching. Jangan sampai Expo mengorbankan MVP web, karena yang dinilai panitia adalah Vercel.
- **Fitur HP** (peran: planner/warehouse/manager di lapangan):
  - Feed "Critical at risk" hari ini.
  - Scan/cari material, lalu lihat stok, ROP, aksi, dan alasan.
  - Approve/tolak rekomendasi. Statusnya disimpan di client/localStorage untuk demo, karena SQLite di Vercel read-only.
  - Countdown PM/TA dengan readiness part.
- **Catatan teknis:** di Vercel, SQLite hanya bisa dibaca (filesystem read-only, dan tulisan tidak persisten). Jadi semua hasil berat dihitung di pipeline Python, sementara slider skenario menghitung ulang di server/JS dari tabel distribusi yang sudah disimpan.

---

## 5. Pembagian tugas (sampai 06.00)

| Orang | Fokus | Output konkret | Selesai paling lambat |
|---|---|---|---|
| **1. Forecast lead** | KQ1: kalibrasi kuantitas (EB installed-base + LightGBM P(move) + event layer TA/PM), inferensi kit PM, abnormal detector, kurva trade-off backtest | Tabel `demand_forecast` (P(move), P50/P90/P95 per material), 1 chart backtest untuk deck | 23.00 |
| **2. Optimizer & data architecture** | KQ2: tabel clean/bridge, distribusi lead time, fungsi biaya cost–risk, ROP/Min/Max/aksi, efficient frontier, guardrail PR, panel DQ | `partpulse.db` lengkap (dim/fact/policy/action/frontier) + diagram alur data | 00.30 |
| **3. App + deck** | Next.js + API SQLite + UI (web + PWA mobile), deploy Vercel, screenshot. Lalu deck 7 slide + appendix backtest | URL Vercel live, zip, screenshot, deck PDF | App 03.30, deck 05.00 |

**Kontrak antar-orang** (disepakati di awal supaya bisa paralel): skema tabel SQLite.
- `materials(id, desc, cat, unit, crit, n_fl, stock, min_cur, max_cur, price, price_est)`
- `forecast(id, p_move, q50, q90, q95, base, planned, event)`
- `leadtime(id, lt_p50, lt_p90, source)`
- `policy(id, rop, ss, min_new, max_new, action, reason, risk_cost, hold_cost)`
- `frontier(budget, exp_risk_cost, n_parts)`
- `dq_issues(type, count, example)`

Orang 3 bisa mulai dengan data dummy berskema sama sebelum Orang 1 dan 2 selesai.

Checkpoint:
- **21.00**: skema dikunci.
- **00.30**: db v1 masuk app.
- **03.30**: freeze fitur.
- **05.30**: submit.

---

## 6. Storyline deck (draft action titles)

1. **Cover**
2. **Problem:** "Stock is high where it isn't needed and empty where it is." Isi: 37,7% di atas Max, 68% tidak bergerak, 115 part kritis A/B stok nol tapi dipakai, 35,5% spend ke material yang stoknya sudah di atas Max.
3. **Solution:** "We forecast the equipment, not the part." Isi: driver-based probabilistic forecast (AUC 0,89 vs 0,79 klasik; 0,84 vs 0,61 pada part tanpa histori) → cost–risk optimizer per criticality → aksi + app web/HP.
4. **Business impact:** success metrics.
   - Critical-part availability per kelas S/A.
   - Nilai excess/dead stock yang dilepas.
   - Jumlah emergency PR.
   - Inventory turns.
   - Forecast hit-rate.

   Benefit dihitung dari backtest + asumsi yang tertulis.
5. **Roadmap & risk:**
   - Pilot 1 unit PX → scale → integrasi SAP MM/PM.
   - Risiko: data quality, adopsi planner, asumsi downtime cost, model drift.
6. **Team & key tech:** Python, LightGBM, Empirical Bayes, Monte Carlo, SQLite, Next.js, Vercel, LLM untuk penjelasan.
7. **Appendix:** backtest, data quality, assumption register.

---

## 7. Keputusan yang perlu dikunci tim

1. Nama produk dan big idea ("forecast the equipment, not the part").
2. Asumsi: service level per criticality, holding rate (/tahun), downtime cost per kelas, emergency premium.
3. Mobile: PWA saja, atau PWA + Expo.
