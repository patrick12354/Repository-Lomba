# Orang 1 — Engine Data (KQ1 + KQ2)

**Misi:** ubah 6 file Excel menjadi `app/data/partpulse.db` sesuai kontrak di [00_TEAM_PLAN.md](00_TEAM_PLAN.md). Semua "otak" solusi ada di sini. App hanya membaca db dan menghitung ulang slider.

**Mulai dari kode yang sudah ada:**
- `analysis/build_mat.py`: tabel level material, harga dan lead time sudah dikoreksi.
- `analysis/forecast_backtest.py`: fitur dan model.
- `analysis/edge_tests.py`: TA replay, rush PR, twins, ledger.

Buat `pipeline/build_db.py` yang menulis db dari nol. Pastikan bisa dijalankan ulang dengan `py pipeline/build_db.py`.

> Windows: pakai `py`, bukan `python`. `lightgbm` sudah ter-install.

---

## Prioritas (kerjakan berurutan, jangan loncat)

### P0: db v0 sebelum 21.00 (Orang 2 menunggu ini)

1. **`materials`**
   - Sebagian besar kolomnya sudah ada di `build_mat.build()`.
   - Tambahan:
     - `stock_value`
     - `health`
     - `demand_class` (Syntetos-Boylan, lihat `eda.py` bagian 3)
     - `lt_source`, dengan fallback lead time: material → kategori → global
     - `price_source`, dengan fallback harga: median kategori×unit, diberi label `category_estimate`
   - Aturan `health`:
     - `STOCKOUT`: stok 0 dan ada pemakaian
     - `BELOW_MIN`
     - `OVER_MAX`
     - `NON_MOVING`: tidak ada issue dalam 17 bulan, tapi stok > 0
     - `OBSOLETE_CANDIDATE`: non-moving, semua FL tempat terpasang tidak punya PM maupun notif, dan stok > 0
2. **`ta_kit`**
   - Logika persis seperti `edge_tests.py` bagian E1.
   - Angka kontrol yang harus keluar: 360 material, 154 gap, 134 S/A, 164 `exceeds_max`.
3. **`meta`**: isi asumsi default (tabel di bawah).

### P1: db v1 sebelum 00.30

4. **`forecast`** (KQ1)
   - **Dekomposisi demand:**
     - `event` = order 2030/2090, dipodelkan sebagai event (TA kit × skala).
     - `base` = selebihnya.
   - **P(move):** pakai LightGBM classifier dari `forecast_backtest.py`. Fitur `stock` **tidak boleh dipakai** karena leakage.
     - Untuk produksi, latih ulang dengan cut-off 2026-03-01 dan target Mar–Sep 2026. Setelah itu, hitung fitur sampai 2026-09-30 lalu prediksi 180 hari ke depan.
   - **Kuantitas:** masalah utama yang belum beres. LGBM overforecast +215%, hybrid underforecast −61%.
     - Saran: `mean = p_move × E[qty | move]`, dengan `E[qty | move]` dari regressor Poisson yang dilatih **tanpa** order event.
     - Lalu kalibrasi satu faktor skala per demand_class pada jendela validasi (Okt-25..Feb-26 → Mar..Sep-26) supaya total bias ≈ 0.
     - Laporkan bias sebelum dan sesudah kalibrasi.
   - **Kuantil** `q50/q90/q95`: pakai compound Poisson. Jumlah event ~ Poisson, ukuran event = distribusi empiris ukuran issue material (atau kategori).
   - **`ltd_mean`, `ltd_var`:** demand selama lead time, dengan memperhitungkan variabilitas lead time:
     - `ltd_mean = d · L`
     - `ltd_var = L·σd² + d²·σL²`
   - **`drivers`:** JSON berisi 3 fitur terpenting per material, dipakai untuk kalimat penjelasan.
   - Isi tabel **`backtest`** dari `analysis/backtest_output.txt`, ditambah hasil kalibrasimu.
5. **`policy`** (KQ2)
   - `SS = z(SL_crit) · sqrt(ltd_var)`, dan `ROP = ltd_mean + SS`.
   - Untuk demand sangat jarang (p_move < 0,3), pakai kuantil compound Poisson pada level service, bukan rumus normal.
   - `max_new = ROP + EOQ`. Kalau EOQ tidak bisa dihitung, pakai median qty PR historis.
   - Aturan `action` (urut prioritas):
     - `REORDER`: stok ≤ ROP **dan** p_move ≥ 0,3, atau material ada di ta_kit dengan gap > 0
     - `DISPOSE_REVIEW`: health = OBSOLETE_CANDIDATE
     - `REDUCE`: stok > max_new **dan** p_move < 0,3
     - `MONITOR`: cold_start = 1 dengan p_move ≥ 0,3, atau trust_score < 0,5
     - `MAINTAIN`: selebihnya
   - **`order_by_date` (E2):**
     - Kasus normal: `as_of + max(0, (stok − ROP) / demand harian) − lt_p90`. Jika hasilnya < as_of, isi as_of (artinya "sudah telat, PR hari ini").
     - Untuk part TA: `next_ta − lt_p90 − 14 hari buffer`. Pilih tanggal yang lebih awal di antara keduanya.
   - **`reason`:** template bahasa Inggris. Contoh: *"REORDER 4 EA — installed on 12 S-critical FLs, 3 notifications in last 90d, lead time P90 160d, stock 0, needed for last turnaround (40 EA)."*
   - Biaya:
     - `hold_cost_yr = holding_rate × unit_price × rata-rata stok`
     - `risk_cost_yr = P(stockout per siklus) × siklus/tahun × downtime_cost_per_day(crit) × downtime_days`
6. **`frontier`**: urutkan part berdasarkan *pengurangan risk cost per rupiah tambahan stok*, lalu hitung kumulatif. Buat 3 skenario: `current`, `optimized`, `lean`.

### P2: kalau masih ada waktu sebelum 01.00

7. **`twins`** (E4):
   - Kelompokkan berdasarkan deskripsi yang dinormalisasi (lihat `edge_tests.py`).
   - Peran: `SHORT` jika di bawah Min atau stockout, `DONOR` jika di atas Max.
8. **`trust_score`** (E5):
   - Rata-rata dari 4 flag: harga dari PO, lead time dari ≥ 3 sampel, ledger konsisten (`start ≥ 0` di E5), dan bukan bagian grup twin.
9. **`dq_issues`**:
   - 230 BoM duplikat
   - 28 format cycle
   - 6,4% notif dengan Required Start < notif date
   - 6 PR dengan lead time negatif
   - harga hanya 16,4% material
   - 20,5% order yang terhubung ke notif
   - `PO-Item Amount` = harga satuan
   - ledger 57,3% tidak seimbang

---

## Asumsi default (tulis ke `meta`, umumkan di grup, Orang 2 jadikan slider)

| Key | Default | Alasan |
|---|---|---|
| as_of_date | 2026-09-30 | Data terakhir |
| holding_rate | 0,25 / tahun | Kisaran umum biaya simpan inventory (asumsi, sebut di deck) |
| service_level S/A/B/C | 0,99 / 0,97 / 0,95 / 0,90 | Asumsi berbasis criticality |
| downtime_cost_per_day S/A/B/C | slider. Default relatif 100 / 30 / 5 / 1 (unit indeks) | **Tidak ada di data.** Jangan tulis angka rupiah tanpa sumber |
| downtime_days_if_stockout | lt_p50 material (bisa dipangkas emergency) | Asumsi |
| ta_last_window | 2025-11-01..2026-01-31 | Dari data order 2030 |
| next_ta_default | 2026-11-01 (12 bln setelah TA terakhir), bisa diubah | Asumsi, bukan jadwal resmi |

## Definition of done

- `py pipeline/build_db.py` jalan bersih dan menghasilkan db < 30 MB.
- Script mencetak **angka kontrol**: jumlah baris per tabel, 154/134/164 untuk ta_kit, distribusi `action`, dan bias forecast setelah kalibrasi.
- Buat `pipeline/README.md` (≤ 1 halaman) berisi cara jalan, asumsi, dan angka kontrol. Orang 2 akan memakainya untuk slide Business Impact dan Key Technologies.
- Sebelum 04.00, kirim ke Orang 2 **5 angka untuk Business Impact**:
  1. Readiness S/A untuk TA: sekarang vs setelah rekomendasi.
  2. Nilai stok over-Max/non-moving yang bisa dilepas (`REDUCE` + `DISPOSE_REVIEW`).
  3. Jumlah part S/A yang berpindah dari risiko ke aman.
  4. Perbandingan AUC backtest.
  5. Persentase PR rush yang bisa dicegah lewat order-by date.
