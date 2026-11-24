# 04 — Scope Final (menggantikan scope di 02 & 03 bila bertentangan)

> Disusun Rabu 4 Nov 2026 ~10:30, setelah stress-test "court" (12 juri, vonis **GUILTY 12–0** untuk rencana PartPulse + SPARC versi penuh). Vonis lengkap: `Case Final/.court/20261104-094900/VERDICT.md` (di luar repo).
> Inti vonis: **idenya kuat, rencananya terlalu besar.** Tiga syarat lolos ada di bawah, dan dokumen ini menjalankannya.

## 0. Tiga syarat dari juri → keputusan

| Syarat juri | Keputusan |
|---|---|
| 1. Satu hero, satu tagline. SPARC & cold-start forecast hanya jadi **bukti** di belakang hero (11/12 juri) | Hero tunggal = **Shutdown Readiness**. Modul lain = "mesin" di balik readiness, bukan fitur yang dijual terpisah. SPARC tidak jadi produk/brand kedua |
| 2. Dedup PR PO, hitung ulang semua angka spend & PR-line sebelum dipakai (10/12) | Orang 1, **sebelum 13:00**. Daftar angka yang wajib dihitung ulang ada di §4 |
| 3. Skeleton Next.js di Vercel yang membaca SQLite live sebelum 21:00 (4/12) | Dimajukan ke **14:00**, karena `partpulse.db` v1 sudah ada sejak 10:12 |
| (+) Jangan klaim "akan menang" | Deck mengklaim **"the only entry that replays your last shutdown"**, bukan "best solution" |

## 1. Satu produk, satu kalimat

**PartPulse — Shutdown-ready spare parts.**
Tagline: ***"Your Min–Max was built for normal days. Shutdowns break it by design."***

Cerita satu alur (bukan daftar fitur):
1. **Masalah:** Min–Max statis tidak bisa menutup shutdown. Kebutuhan TA terakhir melebihi Max pada 164 part. Kalau TA terakhir diulang hari ini, 154 dari 360 part kurang (134 di FL kritis S/A).
2. **Hero:** pilih tanggal TA berikutnya → readiness % per criticality + daftar "order this week / too late / ready" + countdown.
3. **Mesin di baliknya (bukti, bukan fitur terpisah):**
   - Forecast "siapa yang bergerak" (AUC 0,92 vs 0,84 naive; cold-start 0,85).
   - Policy ROP/SS/Max per criticality + order-by date.
   - **Policy backtest** (dari SPARC): Min–Max sekarang dibandingkan policy kita pada histori Feb–Sep 2026.
4. **Mode harian (mesin yang sama, antara dua TA):** daftar aksi REORDER / REDUCE / DISPOSE_REVIEW / MONITOR dengan alasan. Ini sekaligus memenuhi 4 komponen wajib brief (forecasting, dynamic optimization, health monitoring, recommendation & cost–risk), tanpa menjadi produk kedua.

## 2. Scope app (urut prioritas, potong dari bawah kalau telat)

| Prio | Layar / fitur | Komponen brief yang dipenuhi | Sumber data | Selesai |
|---|---|---|---|---|
| **P0** | **Shutdown Readiness** (halaman pertama): date picker TA + slider skala, gauge S/A/B/C, countdown, 3 tabel status, kalimat headline | Forecast (event demand), dynamic optimization (kapan & berapa) | `ta_kit`, `materials`, `meta` | 17:00 |
| **P0** | **Parts list + Part detail**: action badge, order-by date, reason, grafik konsumsi bulanan + band q50–q95, drivers | Forecast, recommendation | `materials`, `forecast`, `policy`, `consumption_monthly` | 17:00 |
| **P0** | **Overview kecil**: kartu health (STOCKOUT/BELOW_MIN/OVER_MAX/NON_MOVING/OBSOLETE_CANDIDATE) + top over-Max | Inventory health monitoring | `materials` | 17:00 |
| **P1** | **Scenario** (budget ↔ risk): slider SL per criticality + holding rate, kurva frontier dengan titik current vs optimized | Cost–risk scenario simulation (diminta eksplisit di brief) | `frontier`, `forecast.ltd_*` | 21:00 |
| **P1** | **Approve / Reject tersimpan di SQLite** (lihat §3) | Kepatuhan "database SQLite" | tabel `decisions` | 21:00 |
| **P1** | **Data Trust panel**: `dq_issues` + `backtest` + catatan "PO-Item Amount = unit price" | Kredibilitas, risk slide | `dq_issues`, `backtest` | 21:00 |
| P2 | Twin stock di Part detail ("use twin before buying") | — | `twins` | 23:00 |
| P2 | Tombol **Export MRP changes (CSV format MM17)** dari `policy` (Min/Max/ROP baru per material) | Detail "last mile ke SAP" untuk juri praktisi | `policy` | 23:00 |

**Dipotong dari app (boleh disebut di deck sebagai roadmap):**
- PWA service worker, push notification, Expo app. Cukup layout responsif yang rapi di 375px.
- LLM saat runtime. Kalimat `reason` dari template di pipeline sudah cukup.
- Poisson insurance-spare optimizer & capital release / redeploy (CA-EDC, Aster). Hanya masuk deck: 1 baris di Business Impact + roadmap fase 2.
- Action Inbox sebagai layar terpisah (sudah tercakup oleh Parts list + Approve/Reject).

## 3. Kepatuhan SQLite untuk keputusan (Approve/Reject)

Juri Lawyer menyorot: approval di `localStorage` bisa dibaca sebagai "bukan SQLite". Pilihan, urut rekomendasi:
1. **Turso / libSQL (SQLite-compatible, persisten).** Tabel `decisions(material_no, action, decision, note, decided_at)`. Butuh satu anggota membuat akun dan database gratis, lalu menaruh token di env Vercel. Estimasi 20–30 menit. Analitik tetap dari `partpulse.db` read-only yang dibundel.
2. **Fallback:** di cold start, salin `partpulse.db` ke `/tmp`, lalu tulis `decisions` ke sana. Tetap SQLite, tetapi data hilang saat instance berganti. Beri label "demo session" di UI.

Keputusan tim (isi): ☐ Turso ☐ /tmp

## 4. Perbaikan data wajib (Orang 1, sebelum 13:00)

- **Bug:** `analysis/build_mat.py` (dan `pipeline/build_db.py` yang memakainya) tidak membuang 5.420 baris duplikat persis di PR PO (46,7% dari 11.609). Kunci PR + PR-Item seharusnya unik, dan setelah dedup tersisa **6.189** baris. Fix: `p = pp.drop_duplicates().copy()` sebelum fitur PR dihitung.
- Dampak yang sudah dicek: spend IDR Rp3.144,5 M → **Rp1.634,2 M**. Porsi spend ke material di atas Max 35,5% → **36,0%**, jadi klaim persentasenya aman.
- **Wajib dihitung ulang lalu update di `pipeline/README.md`, `docs/03`, dan deck:**
  - E2: rush share 17,3% dan late share 91,9% vs 54,0%.
  - PR lines per bulan untuk kit TA (430–480).
  - E5: rasio received/issued 2,19× dan ledger negatif 57,3%.
  - Business Impact #5 (88,3% rush bisa dicegah).
  - Lead time p50/p90 per material (duplikat memberi bobot ganda pada sebagian PR).
  - Tabel `frontier` & `policy` (bergantung pada lead time dan harga).
- `meta`: tandai `price_source=category_estimate` dan downtime cost sebagai **assumption** di UI.

**Tanggal TA default (`next_ta_default`):** saat ini 2026-11-01, yang sudah lewat relatif terhadap tanggal presentasi. Sumber publik menyebut TAM Cilegon terjadi Mei 2024 dan Jan–Feb 2026 (lihat `Case Final/analysis/01_riset_chandra_asri.md`), jadi jaraknya ~20 bulan. Usulan: default **2027-06-01**, dengan label "planning assumption — editable". Efeknya, part impor (LT p90 ~210 hari) jatuh ke "order this month", yang menjadi momen demo terkuat. Jangan klaim ini jadwal resmi.

## 5. Peran SPARC setelah dipangkas (Orang 3)

Tugas bukti, bukan fitur:
1. **Policy backtest untuk policy tim sendiri** (paling penting): putar `policy` hasil pipeline (ROP/Max per material) di simulator replenishment, lalu bandingkan dengan Min–Max sekarang pada Feb–Sep 2026. Metriknya fill rate, stockout-days, dan rata-rata nilai stok.
   - Acuan dari spike bootstrap-ROP: Min–Max 53% fill, 463 stockout-days, Rp38,8 M. Usulan 80% fill di Rp34,7 M; 87,5% di Rp40,7 M; 93% & 296 stockout-days di Rp63 M.
   - Script acuan: `Case Final/analysis/spikes/s4_frontier.py`.
   - Hasilnya jadi **1 chart di slide Solution/Impact** dan masuk tabel `backtest`.
2. Satu angka insurance spare untuk deck (spike `s5_insurance.py`): optimum tetap menyimpan ≥ 1 unit, tetapi ~91–95% nilai unit berlebih bisa dilepas, dan hasil ini robust pada penalti Rp0,5–10 M.
3. Bank Q&A: data dummy, kenapa bukan deep learning, asumsi downtime, integrasi SAP.

Cut-off edge baru masuk app: **19:00**. Setelah itu, edge hanya masuk deck dan Q&A.

## 6. Jadwal baru (sekarang ~10:30)

| Jam | Siapa | Output |
|---|---|---|
| 11:00 | semua | Scope ini disetujui. Pilih Turso atau /tmp (§3) |
| 13:00 | 1 | Dedup + rerun pipeline + angka kontrol baru + `next_ta_default` |
| 14:00 | 2 | Skeleton Next.js live di Vercel: 1 API + 1 halaman membaca `partpulse.db` |
| 17:00 | 2 | Semua P0 live |
| 19:00 | 3 | Policy backtest tim + angka insurance. **Cut-off fitur app baru** |
| 21:00 | 2 (+1) | P1 live (Scenario, decisions di SQLite, Trust) |
| 23:00 | 2 | P2 jika sempat, lalu **feature freeze** |
| 01:00 | 1 + 3 | Draft deck lengkap (action titles + angka dari db) |
| 03:00 | semua | Deck final + gladi 1× |
| 04:00 | 2 | Deploy final + screenshot timestamp Vercel |
| 05:00 | 2 | Zip (source + db + pipeline, tanpa `node_modules`/`.next`) + submit. Buffer 1 jam |

## 7. Klaim yang boleh dan dilarang di deck

- **Boleh:**
  - "Only entry that replays your last shutdown against today's stock."
  - "Knows which parts will move, including parts with no history (AUC 0.85 cold-start)."
  - "Same capital, higher fill rate in backtest." Ini hanya boleh setelah §5.1 selesai dengan policy tim.
- **Dilarang:**
  - "Will win" / "best".
  - Rupiah absolut tanpa "on this dataset".
  - Rp5.535 M (mayoritas harga estimasi) sebagai headline.
  - Klaim yang sudah gugur: rush lebih mahal, teks notif → part, kekurangan part menyebabkan delay.
  - Jadwal TA resmi Chandra Asri.

## 8. Unique point tambahan (brief 4 Nov, diselaraskan dengan scope ini)

UI, arsitektur, UX, akurasi model, insight, dan explainability adalah syarat minimum yang juga dipenuhi tim lain. Pembeda kita harus datang dari tiga lapis yang biasanya kosong: **bukti di sejarah mereka sendiri**, **bahasa keuangan**, dan **jalur adopsi ke SAP**. Semua butir di bawah memperkuat hero Shutdown Readiness dan tidak menjadi produk kedua.

| # | Unique point | Isi | Masuk ke | Status scope |
|---|---|---|---|---|
| U1 ★ | **Time Machine: replay TA Jan–Feb 2026** | Mesin dijalankan seolah sudah dipakai sejak Mei 2025: part A/B mana yang kurang saat TA bisa dicegah, kapan PR seharusnya keluar, berapa tambahan modalnya | Hero (slide Solution) + 1 chart | = §5.1 policy backtest. Bingkai ulang sebagai "Time Machine", bukan fitur baru |
| U2 ★ | **Inventory sebagai portofolio asuransi** | Holding cost diperlakukan sebagai premi, downtime yang dihindari sebagai klaim. Satu KPI: *"Uncovered downtime exposure"* = Σ P(stockout) × downtime cost × hari tunggu, untuk part A/B | Overview (1 kartu) + Business Impact | **Baru, P1.** Pakai `risk_cost_yr` yang sudah ada. Indeks bisa dikonversi ke rupiah lewat slider asumsi (publik: ~US$3 jt/hari downtime Cilegon, ucapan manajemen). Tetap dilabeli assumption |
| U3 | **Supply Shock simulator** | Slider "+X hari lead time impor" (dan kurs). Output: part A/B yang lewat order-by date dan berapa poin readiness TA turun | Halaman Readiness (slider kedua) | **Baru, P2.** Murah: cukup geser `lt_p90` lalu hitung ulang readiness/order-by di client |
| U4 | **SAP-native write-back** | Tombol Approve menghasilkan CSV MM17 (Min/Max/ROP baru) plus daftar draft PR "order this week" | Parts list | = P2 di §2. Tetap P2; jadikan jawaban Q&A "bagaimana masuk ke SAP?" |
| U5 | **TA Readiness Gate** | Gate T-180 / T-120 / T-90 hari sebelum TA, KPI readiness % A/B dimiliki bersama Maintenance dan Procurement | Slide Roadmap | Deck saja |
| U6 | **Group-level capital release** | Excess dialihkan sebagai initial spares CA-EDC (COD 2027), pooling dengan Aster, return-to-vendor, merge twin | Business Impact + roadmap fase 2 | Deck saja (sudah di §2 "dipotong dari app") |

**Tidak diambil:** chatbot (semua tim punya), teks notif → part (gugur), Expo app.

**Catatan criticality:** brief awal menulis "S/A". Mengikuti jawaban panitia (A > B > C > S), semua KPI U1–U3 memakai **A/B**.

## 9. Stress test & feasibility E1–E4 terhadap engine produksi (commit 8d72a90)

Sumber:
- `py analysis/stress_prod.py` → `analysis/stress_prod_output.txt`. Menjalankan ulang validasi rolling `pipeline/build_db.py` dan membaca `app/data/partpulse.db` tanpa menulis apa pun.
- `py analysis/stress_e1_e4.py` → `analysis/stress_e1_e4_output.txt`. Cek di level data: twins, mekanisme rush, single-event.

Kriteria lolos:
- **Klaim:** angka deck tetap berlaku setelah dedup PR PO, tanpa fitur yang bocor dari masa depan, dan tidak trivial menurut definisinya sendiri.
- **Feasibility:** fitur app menghasilkan keputusan yang berbeda-beda per part, bukan satu nilai yang sama untuk semua.

| Edge | Klaim saat ini | Hasil stress test | Klaim | Feasibility |
|---|---|---|---|---|
| **E1** Shutdown Readiness | 154 part kurang (A/B 137). 164 part kebutuhan TA > Max. Readiness A/B 58,7% → 65,1% | Robust: di skala TA 0,5× masih 105 part A/B kurang, dan dedup tidak mengubah LT p90 (68 hari). **Tapi** dari 164 "> Max", 85 punya Max = 0 (Non Stock); yang benar-benar "Min–Max kalah by design" hanya **79 Stock Item (71 A/B)**. 57% nilai gap berasal dari 5 part (grease, 3 firebrick, bearing) | ✅ dengan rewording | ❌ **`next_ta_default` = 2026-11-01, hanya 32 hari.** Ke-137 part A/B kurang punya `order_by_date` = as_of, sehingga layar hero cuma menampilkan "semua terlambat" tanpa daftar "order this week". BI-1 (65,1%) tidak memakai buffer 14 hari, padahal order-by memakainya; dengan buffer hasilnya 59,3% |
| **E2** Order-by date | 17,3% PR rush, telat 91,9% vs 54,0%. BI-5: 88,3% rush "bisa dicegah" | Rush robust: setelah dedup 17,8%, telat 92,5% vs 52,9%; dengan LT prior-only 20,5%, telat 90,8% vs 51,7%. **BI-5 tidak diskriminatif:** tes yang sama pada PR *non-rush* memberi 85,8% (dedup 92,9% vs 92,1%). Hampir semua PR memang untuk part yang pernah dipakai | ✅ statistik rush, ❌ BI-5 | ❌ **Bug order-by:** semua 1.628 REORDER **dan 1.776 MAINTAIN** mendapat `order_by_date` = as_of. Penyebabnya `slack = cover − lt90` (`build_db.py:355`) menghitung lead time dua kali, karena ROP sudah memuat demand selama lead time. Hanya 183 part MAINTAIN yang punya tanggal ke depan |
| **E3** Cold-start forecast | Rolling AUC 0,915, cold 0,845 (naive 0,835) | **Leakage dari snapshot BoM:** `mn`, `mx`, `mrp` ada di `X_cols`, padahal sama seperti `stock`, nilainya dibaca setelah jendela tes. Kalau ketiganya dibuang: AUC **0,892**, cold **0,769** (per origin 0,756–0,781). Dedup PR PO dan membuang `lt_med` tidak berpengaruh (0,893 / 0,772). Model tetap mengalahkan naive (0,892 vs 0,835); di backtest lama, gain cold vs SBA tetap +0,11 s/d +0,18 (CI 95% bootstrap) | ⚠️ angka cold turun ~0,08 | ✅ Engine jalan. Hanya angka headline dan teks driver ("current Min") yang perlu diganti |
| **E4** Twin stock | 57 grup, satu kembaran kurang sementara kembaran lain di atas Max | Valid: 0 grup dengan unit berbeda, semua deskripsi memuat spesifikasi (angka), 55/57 grup kekurangannya tertutup oleh stok donor, 55 menyentuh A/B. **Nilai kecil:** Rp0,18 M (pakai Min) s/d Rp0,66 M. 25/57 grup punya kembaran di FL yang sama, dan 16 order mengambil dua kembaran sekaligus. Bisa jadi itu posisi terpisah, jadi perlu konfirmasi manusia | ✅ sebagai cerita "tanpa beli", ❌ sebagai cerita uang | ✅ Tabel `twins` sudah siap. Tetap P2, dengan label "confirm interchangeability" |

### Notes untuk Orang 1

Delapan butir perbaikan (order-by bug, `NEXT_TA`, leakage snapshot, BI-1/BI-5, rewording E1, kriteria rerun) ada di [tasks/ORANG_3_NOTE_TO_TEAM.md](tasks/ORANG_3_NOTE_TO_TEAM.md).
