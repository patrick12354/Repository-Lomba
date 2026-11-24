# Note dari Orang 2 untuk tim (4 Nov 2026)

Web sudah jalan di `app/` dan membaca `app/data/partpulse.db` (commit `8d72a90`). **Belum di-deploy ke Vercel.** Detail QA ada di [ORANG_2_QA_BRIEF.md](ORANG_2_QA_BRIEF.md).

## Untuk semua

- **Cara jalan lokal:** `cd app && npm install && npm run dev` lalu buka http://localhost:3000. Untuk versi production: `npm run build && npm start`.
- **7 halaman** (judul tiap halaman berupa pertanyaan, jawabannya satu kalimat di bawah judul):

  | Menu | Isi |
  |---|---|
  | Shutdown (hero) | Tanggal TA + ukuran TA → % siap per criticality, 360 kotak (1 kotak = 1 part), deadline per minggu, board Too late / This week / Later, peta furnace, bukti "Max < kebutuhan TA" |
  | To do | Urgent now (approve/reject) dan All parts (Order / Reduce / Review disposal / Watch / Keep) |
  | Part detail | Rekomendasi 1 kalimat, stok vs Min–Max lama dan baru, kapan pesan dan kapan datang, grafik 17 bulan, alasan, twin, data check |
  | Stock, Forecast, What if, Data check | Health, KQ1, frontier budget vs risiko, jebakan data + bukti forecast |
- **Criticality di app sudah A > B > C > S** (A tertinggi). "Kritis" = A dan B.
- **Approve/Reject tersimpan di SQLite** lewat `/api/decisions` (file sementara di `/tmp`, opsi tanpa layanan luar dari scope final §3). Di Vercel, data hilang saat server cold start. Saat demo, sebut "demo session".
- **Nama produk perlu diputuskan.** App memakai **Sparekit** supaya tidak mirip PlantPulse dari babak penyisihan. Scope final masih menulis PartPulse. Pilih satu sebelum deck dikunci; di app cukup ganti `app/lib/brand.ts`.
- **Windows:** matikan server lokal sebelum `git pull`. Server mengunci `partpulse.db`, dan pull akan gagal menulis file itu.

## Untuk Orang 1 (Engine)

1. **Dedup PR PO belum masuk pipeline.** `analysis/build_mat.py` belum memanggil `pp.drop_duplicates()` (scope final §4). Lead time, harga, `policy`, dan `frontier` di db masih dihitung dari 5.420 baris dobel. Angka spend di app sudah memakai versi dedup (**Rp 1,634 B, 36,0%**) lewat `pipeline/app_tables.py`, jadi angka deck harus mengikuti versi itu.
2. **Frontier tidak konsisten dengan titik optimized.** Risiko terendah kurva `frontier` = 3,1 juta (indeks), tapi `optimized` = 0,53 juta. Di halaman What if, titik "Recommended" jatuh di bawah kurva yang katanya "risiko terendah untuk tiap budget". Mohon disamakan, misalnya titik optimized ikut masuk hull atau grid kuantil diperluas.
3. **Setelah `build_db.py`, jalankan `py pipeline/app_tables.py`.** Script ini menambah `material_location` (peta furnace) dan `app_facts` (angka spend dan % di atas Max) ke db. Tanpa script ini app tidak error, tapi peta furnace dan kartu "Before you buy" hilang. Paling aman, panggil di akhir `build_db.py`.
4. **`next_ta_default` masih 2026-11-01.** Scope final mengusulkan **2027-06-01** dengan label planning assumption. Dengan tanggal sekarang, 152 dari 360 part sudah "too late". Itu cerita yang kuat, tapi rencana pesan per minggu jadi kosong.
5. **Kolom yang dibaca app (tolong kabari kalau mau diganti nama):**
   - `frontier.fill_rate_A/B`
   - `consumption_monthly.ym / qty / qty_event / n_lines`
   - `policy.order_by_date / min_new / max_new / reason`
   - `forecast.p_move / q50 / q95 / cold_start / drivers`
   - `backtest` method `engine_rolling_mean` (AUC naive dibaca dari kolom `note`) dan `sba`
   - `meta`: `as_of_date`, `next_ta_default`, `ta_buffer_days`, `holding_rate`, `service_level_*`, `criticality_order`, `order_cost_idr`
6. **Opsional:** slider service level per A/B/C/S di What if butuh kuantil lead-time-demand per material, misalnya tabel `ltd_quantiles(material_no, q80, q90, q95, q97, q99, q995)`. Tanpa tabel itu, What if tetap bergeser di sepanjang `frontier`.
7. Definisi "Act now" di app saat ini: part TA A/B yang too late atau harus dipesan minggu ini, plus part A/B kosong yang masih dipakai. Hasilnya **394**. Cocokkan dengan angka di deck.

## Untuk Orang 3 (Edge, backtest, Q&A)

1. **Hasil policy backtest (scope final §5.1)** bisa langsung tampil di halaman Data check. Kirim sebagai baris tabel `backtest` dengan method berawalan `policy_` (misal `policy_minmax_current`, `policy_partpulse`) dan isi fill rate, stockout-days, dan nilai stok di kolom `note`. Saya yang menambahkan tampilannya.
2. **Angka yang sudah tampil di app** (boleh dipakai di deck, semua "on this dataset"):
   - Readiness A+B 59%: 137 kurang, 124 di antaranya A.
   - 164 part butuh lebih dari Max-nya untuk satu TA.
   - Forecast benar 92 dari 100 vs baseline 84 (part tanpa histori: 85 vs 61 SBA).
   - Rp 414 B stok di atas Max (priced items).
   - 36,0% spend ke part yang sudah di atas Max.
3. **Bahan Q&A dari sisi app:**
   - Kenapa keputusan di `/tmp`: Vercel read-only, tetap SQLite, dan untuk produksi diganti tabel di SQL Server/SAP.
   - Risiko adalah indeks, bukan rupiah, karena tidak ada data downtime cost.
   - Criticality mengikuti urutan panitia A > B > C > S.
4. **Screenshot untuk deck** paling kuat dari: Shutdown (360 kotak + board), Part detail (gauge Min–Max lama vs baru + timeline), What if (setelah poin Orang 1 #2 beres), dan tampilan HP dari To do.

## Yang dikerjakan Orang 2 berikutnya

1. Deploy pertama ke Vercel dan cek SQLite ikut terbundel. Lalu screenshot timestamp.
2. "Check a purchase request" (input material + qty → vonis). Ini input→output paling jelas untuk juri.
3. Export perubahan Min/Max ke CSV (P2 di scope final), kalau waktu cukup.
