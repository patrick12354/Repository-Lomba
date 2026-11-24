# 00 — Rencana Tim & Kontrak Data (baca ini dulu)

**Deadline submit: Kamis 5 Nov 2026, 06.00 WIB.**

Yang harus disubmit (brief hal. 8):
- MVP di Vercel. Tidak boleh static HTML.
- Database SQLite.
- Zip berisi source code + database.
- Screenshot timestamp dari versi Vercel terakhir.
- Deck dalam bahasa Inggris.

## Siapa mengerjakan apa

| Orang | Peran | File brief | Output utama |
|---|---|---|---|
| **1** | **Engine Data** (Python): semua logika KQ1 + KQ2 | [ORANG_1_ENGINE.md](ORANG_1_ENGINE.md) | `app/data/partpulse.db` sesuai kontrak di bawah |
| **2** | **App + Deploy + Deck**: Next.js di Vercel + versi HP (PWA) | [ORANG_2_APP_DECK.md](ORANG_2_APP_DECK.md) | URL Vercel live, zip, screenshot, deck PDF |
| **3** | **Edge Hunter**: mencari dan membuktikan edge baru dari data | [ORANG_3_EDGE_HUNTER.md](ORANG_3_EDGE_HUNTER.md) | Kartu edge baru di `docs/03_EDGE_PROPOSALS.md` + script bukti |

Konteks wajib baca (15 menit):
1. `docs/03_EDGE_PROPOSALS.md`: hero dan storyline.
2. `docs/02_BLUEPRINT.md`: arsitektur.
3. `docs/01_EDA_FINDINGS.md`: semua angka EDA.

## Ide besar (sudah disepakati sebagai arah, boleh diasah)

> **"Your Min–Max was built for normal days. Shutdowns break it by design."**

- **Hero, E1 Shutdown Readiness:** order berawalan 2030 adalah order turnaround. Kalau turnaround terakhir diulang hari ini, 154 dari 360 part-nya kurang, 137 di antaranya kritis A/B (124 di A). *(Diperbarui 4 Nov: panitia menyatakan urutan criticality A > B > C > S.)* Pada 164 part, kebutuhan turnaround lebih besar dari Max-nya.
- **Mesin:**
  - E3: forecast part tanpa histori (AUC 0,84 vs 0,61 untuk SBA).
  - E2: order-by date. Saat ini 17,8% PR minta lebih cepat dari setengah lead time normal, dan 92,5% dari PR itu terlambat (setelah dedup PR PO).
  - Optimizer cost–risk per criticality.
- **Pendukung:**
  - E4: material kembar. Ada 57 grup di mana satu kembaran kurang dan kembaran lain di atas Max.
  - E5: trust layer. `PO-Item Amount` adalah harga satuan, dan ledger stok tidak seimbang.

## Checkpoint

| Jam | Siapa | Apa |
|---|---|---|
| **+30 menit** | 1 + 2 | Kontrak tabel di bawah dikunci. Perubahan setelahnya wajib diumumkan di grup |
| **21.00** | 1 | `partpulse.db` **v0**: tabel `materials`, `ta_kit`, `meta` terisi data asli (boleh kasar). Orang 2 langsung pakai |
| **23.00** | 3 | Batch pertama edge baru diserahkan ke 1 & 2 (maks. 2 edge terbaik) |
| **00.30** | 1 | db **v1** lengkap (forecast, policy, frontier, twins, dq) |
| **01.00** | semua | **Cut-off fitur baru.** Setelah jam ini, edge baru hanya masuk deck/Q&A, tidak masuk app |
| **03.30** | 2 | Freeze app, deploy final, screenshot |
| **05.00** | 2 (+1, 3 bantu) | Deck final PDF |
| **05.30** | 2 | Submit: zip + screenshot + deck |

## Kontrak data: `app/data/partpulse.db` (SQLite)

Aturan umum:
- Semua tanggal ditulis sebagai `TEXT` ISO `YYYY-MM-DD`.
- Uang dalam IDR (`REAL`).
- Kolom yang dihitung dari asumsi wajib tercatat di `meta`.
- **Harga = `PO-Item Amount` (harga satuan). Nilai = harga × qty.** Jangan bagi dengan qty.

```sql
-- master + kondisi sekarang, 1 baris per material (7.481)
CREATE TABLE materials (
  material_no   INTEGER PRIMARY KEY,
  description   TEXT, category TEXT, unit TEXT,
  mrp_type      TEXT,            -- 'Stock Item' | 'Non Stock'
  criticality   TEXT,            -- A/B/C/S, urutan A > B > C > S (A tertinggi); diambil yang tertinggi dari FL tempat terpasang
  n_funcloc     INTEGER, installed_qty REAL,
  stock REAL, min_cur REAL, max_cur REAL,
  unit_price    REAL,            -- IDR, median harga satuan PO
  price_source  TEXT,            -- 'po' | 'category_estimate' | 'none'
  stock_value   REAL,            -- stock * unit_price
  lt_p50 REAL, lt_p90 REAL,      -- hari, dari PR-Date -> PO-Delivery Date
  lt_source     TEXT,            -- 'material' | 'category' | 'global'
  main_supplier TEXT,
  qty_issued_17m REAL, months_active INTEGER, last_issue TEXT,
  demand_class  TEXT,            -- smooth/intermittent/erratic/lumpy/single/none
  health        TEXT,            -- OK / BELOW_MIN / STOCKOUT / OVER_MAX / NON_MOVING / OBSOLETE_CANDIDATE
  trust_score   REAL             -- 0..1 (E5)
);

-- forecast 180 hari ke depan (KQ1)
CREATE TABLE forecast (
  material_no INTEGER PRIMARY KEY,
  p_move REAL,                   -- P(ada pemakaian dalam 180 hari)
  mean_qty REAL, q50 REAL, q90 REAL, q95 REAL,
  base_qty REAL, event_qty REAL, -- dekomposisi: corrective/rutin vs turnaround
  ltd_mean REAL, ltd_var REAL,   -- demand selama lead time (dipakai slider di app)
  cold_start INTEGER,            -- 1 = tidak punya histori
  drivers TEXT                   -- JSON: top faktor, mis. {"n_funcloc":12,"fl_notif_90d":3}
);

-- kebijakan stok + aksi (KQ2), pada asumsi default
CREATE TABLE policy (
  material_no INTEGER PRIMARY KEY,
  service_level REAL, safety_stock REAL, rop REAL, min_new REAL, max_new REAL,
  action TEXT,                   -- REORDER / MAINTAIN / REDUCE / MONITOR / DISPOSE_REVIEW
  order_qty REAL,
  order_by_date TEXT,            -- E2: tanggal terakhir aman untuk PR
  hold_cost_yr REAL, risk_cost_yr REAL,
  reason TEXT                    -- kalimat penjelasan (Inggris), dibuat dari template
);

-- E1: bill of parts turnaround terakhir (order 2030, Nov-25..Jan-26)
CREATE TABLE ta_kit (
  material_no INTEGER PRIMARY KEY,
  ta_qty_last REAL, stock REAL, gap REAL, gap_value REAL,
  exceeds_max INTEGER, lt_p90 REAL, criticality TEXT
);

-- frontier anggaran vs risiko (slider skenario)
CREATE TABLE frontier (
  scenario TEXT, budget_idr REAL, exp_risk_cost REAL,
  fill_rate_A REAL, fill_rate_B REAL, n_parts_funded INTEGER   -- diganti 4 Nov (dulu fill_rate_S/A)
);

CREATE TABLE twins (group_id INTEGER, material_no INTEGER, role TEXT);   -- role: SHORT / DONOR / OTHER
CREATE TABLE dq_issues (issue TEXT, n INTEGER, example TEXT, impact TEXT);
CREATE TABLE backtest (method TEXT, auc_all REAL, auc_cold REAL, coverage_q95 REAL, note TEXT);
CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT);
-- meta wajib: as_of_date, data_window, holding_rate, service_level_S/A/B/C,
--             downtime_cost_per_day_S/A/B/C, ta_last_window, next_ta_default
```

## Aturan bersama

- **Angka di deck dan app harus berasal dari db atau dari file `analysis/*_output.txt`.** Jangan ketik angka dari ingatan.
- Data ini **dummy**. Jual mekanismenya. Rupiah selalu disebut sebagai "on this dataset".
- Klaim yang **dilarang** (sudah diuji dan tidak terbukti):
  - "Rush PR lebih mahal."
  - "Kekurangan part menyebabkan delay maintenance."
  - "Teks notifikasi bisa menebak part."
  - "34% spend ke material tak terpakai." Angka ini salah. Yang benar 2,7%, dan yang berlaku sekarang adalah 36,0% spend (setelah dedup PR PO) ke material yang stoknya sudah di atas Max.
- Commit sering ke `main`, lalu `git pull --rebase` sebelum push.
