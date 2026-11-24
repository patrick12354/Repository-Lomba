# Orang 2 — App (Web + HP), Deploy, Deck

**Misi:** MVP yang **benar-benar jalan** di Vercel dan membaca SQLite, bisa dipakai di HP, plus deck 6 slide wajib.

Juri sudah bilang mereka mencari *proven solution*: masukkan input, keluar output yang sesuai case. Bukan mockup.

**Input dari Orang 1:** `app/data/partpulse.db` sesuai kontrak di [00_TEAM_PLAN.md](00_TEAM_PLAN.md). v0 datang jam 21.00. Sebelum itu, buat db dummy kecil dengan skema yang sama supaya bisa langsung coding.

---

## Stack (sudah diputuskan, jangan diganti)

- **Next.js (App Router) + TypeScript**, deploy ke **Vercel**, folder `app/`.
- **SQLite read-only** pakai `better-sqlite3`.
  - Buka db dengan `{ readonly: true, fileMustExist: true }`, path `path.join(process.cwd(), 'data/partpulse.db')`.
  - Wajib tambahkan `outputFileTracingIncludes` di `next.config` supaya file db ikut terbundel ke serverless function. **Cek ini di deploy pertama.**
  - Filesystem Vercel read-only. Tidak ada write ke db. Approve/reject rekomendasi disimpan di `localStorage` dan diberi label "demo".
- **API:** Route Handlers `app/api/*`. Bagian ini yang membuat app "bukan static HTML".
- **UI:** Tailwind + shadcn/ui (atau komponen sendiri) + Recharts. Seluruh teks UI dalam bahasa Inggris.
- **Mobile:** **PWA** (manifest + service worker sederhana + ikon) dengan layout mobile-first dan bottom navigation di layar < 768px.
  - Expo/React Native **hanya** kalau semua P0–P1 sudah live sebelum 01.30. Expo memakai API yang sama.

## Endpoint

| Endpoint | Isi |
|---|---|
| `GET /api/overview` | KPI: jumlah per `health`, nilai stok, nilai over-Max, readiness TA A/B, jumlah REORDER yang order-by-nya ≤ 7 hari |
| `GET /api/ta-readiness?date=YYYY-MM-DD&scale=1.0` | **Hero.** Hitung on-the-fly dari `ta_kit` + `materials`: readiness % per criticality, daftar part dengan `order_by = date − lt_p90 − 14`, status (`READY` / `ORDER_NOW` / `TOO_LATE`) |
| `GET /api/parts?action=&crit=&health=&q=` | List + filter + search |
| `GET /api/parts/[id]` | Detail: materials + forecast + policy + twins + reason |
| `GET /api/scenario?sl_S=..&holding=..&dt_S=..` | Hitung ulang SS/ROP dari `ltd_mean`/`ltd_var` per material dengan parameter slider. Output: total nilai stok vs expected risk cost vs fill-rate A/B. Bandingkan dengan `frontier` |
| `GET /api/trust` | `dq_issues` + distribusi `trust_score` + `backtest` |

## Layar (urutan prioritas)

**P0 (live di Vercel sebelum 00.30, walaupun masih pakai db v0):**
1. **Shutdown Readiness (hero, halaman pertama)**
   - Pilih tanggal TA (date picker), plus slider skala TA (0,5–1,5×).
   - Gauge readiness S / A / B / C.
   - Countdown hari.
   - Tabel "Order this week" / "Too late — expedite or find twin" / "Ready".
   - Kalimat headline, contoh: *"Next turnaround in 120 days — 59% ready on A-critical parts. 23 parts must be ordered this week."*
2. **Parts list + Part detail**
   - Badge `action`, `order_by_date`, penjelasan `reason`.
   - Grafik konsumsi bulanan dan forecast band (q50–q95).
   - Faktor pendorong (`drivers`).

**P1 (sebelum 03.00):**

3. **Optimizer / Scenario**
   - Slider service level per criticality, holding rate, dan downtime cost index.
   - Kurva frontier (budget vs risk), dengan titik "current" vs "optimized".
4. **Overview**: kartu KPI + donut `health` + top 10 nilai over-Max.
5. **Data Trust**
   - Tabel `dq_issues` dan backtest (AUC kita vs Croston/SBA).
   - Catatan khusus "PO-Item Amount = unit price".

**P2:** twin-stock suggestion di Part detail ("Twin 4100075099 has 566 above Max → transfer before buying"). Tambahkan juga push/notifikasi lokal di PWA untuk part yang melewati order-by.

**Versi HP** harus benar-benar enak dipakai untuk 3 alur ini:
- (a) Buka app, langsung melihat feed "Critical at risk today".
- (b) Cari material, lihat stok, aksi, dan alasan.
- (c) Approve atau tolak rekomendasi.

Uji pakai viewport 375px dan "Add to Home Screen".

## Deploy & submission checklist

- [ ] Deploy pertama ke Vercel **sebelum 22.00**, walau masih kosong. Tujuannya menemukan masalah bundling SQLite lebih awal.
- [ ] Tidak ada secret di repo. Kalau ada LLM, teks penjelasan di-*pre-generate* di pipeline, bukan dipanggil saat runtime.
- [ ] Deploy final sebelum 03.30. Lalu ambil **screenshot timestamp** halaman Vercel Deployments (status Ready + waktu) dan app yang terbuka.
- [ ] Zip: source code + `app/data/partpulse.db` + `pipeline/`. Exclude `node_modules` dan `.next`.
- [ ] Buka URL dari HP (jaringan seluler), pastikan semua layar P0 jalan.

## Deck (bahasa Inggris, format brief hal. 9)

| # | Slide | Isi (angka dari Orang 1 / `docs/03_EDGE_PROPOSALS.md`) |
|---|---|---|
| 1 | Cover | Nama tim + nama anggota |
| 2 | Background & Problem | Hook: *"Shutdowns break Min–Max by design"*. Isi: 79 part stok (71 A/B) Max < kebutuhan satu TA, + 85 part kit dengan Max = 0; replay TA: 154 kurang, 137 A/B (124 A); 37,7% stock item di atas Max; 36,0% spend ke material yang sudah di atas Max; 17,8% PR rush → 92,5% terlambat (angka setelah dedup PR PO) |
| 3 | Solution | Arsitektur 4 modul (Forecast → Optimize → Health → Recommend) + hero Shutdown Readiness + fitur unik (cold-start forecast, order-by date, twin stock, trust layer) + screenshot app web & HP |
| 4 | Business Impact | Success metrics (A/B readiness, nilai stok dilepas, % PR sebelum order-by, forecast AUC) + 5 angka dari Orang 1. Asumsi dicantumkan |
| 5 | Roadmap & Risk Management | Fase pilot (furnace BF-1xx + TA berikutnya) → scale semua unit PX/PY → integrasi SAP MM/PM. Stakeholder: Maintenance Planner, Warehouse, Procurement, Reliability. Risiko: data quality (E5), asumsi downtime, adopsi planner, model drift → mitigasinya |
| 7 | Team Profile & Key Technologies | Tabel anggota. Python, pandas, LightGBM, Empirical Bayes/compound Poisson, SQLite, Next.js, Vercel, PWA |
| – | Appendix | Backtest, data quality, assumption register, metodologi TA replay |

Catatan: penomoran di brief memang lompat dari 5 ke 7. Ikuti urutan isinya.

Draft action titles sebelum 02.00, isi final 05.00. Orang 3 menyumbang slide edge tambahan dan bank Q&A.
