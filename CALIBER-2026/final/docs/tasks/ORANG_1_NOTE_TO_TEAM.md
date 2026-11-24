# Note dari Orang 1 untuk tim (4 Nov 2026, siang)

Balasan untuk `ORANG_2_NOTE_TO_TEAM.md`, `ORANG_3_NOTE_TO_TEAM.md`, dan `04_SCOPE_FINAL.md` §4. Semua sudah masuk ke `app/data/partpulse.db`. Detail perubahan ada di `docs/04_MODEL_DECISIONS.md` §J, dan angka lengkapnya di `pipeline/README.md`.

## Jawaban per poin Orang 2

| # | Poin | Status |
|---|---|---|
| 1 | Dedup PR PO | ✔ Dikerjakan di `analysis/load.py`, jadi berlaku untuk semua script (pipeline, EDA, edge tests, backtest). Output `analysis/*_output.txt` sudah dijalankan ulang |
| 2 | Frontier vs titik optimized | ✔ Dua bug diperbaiki (titik awal hull, dan level kandidat sekarang memuat ROP kebijakan dan Min sekarang). `current` dan `optimized` tidak bisa lagi jatuh di bawah kurva. Ketiga titik memakai lot size yang sama, jadi bedanya hanya level reorder |
| 3 | `app_tables.py` | ✔ Dipanggil otomatis di akhir `build_db.py` |
| 4 | `next_ta_default` | ✔ **2027-06-01**, ditandai `meta.next_ta_note` = "planning assumption, editable". Lapisan TA dipisah dari horizon forecast 180 hari |
| 5 | Kolom yang dibaca app | Tidak ada yang diganti nama. Yang ditambah: `materials.trust_flags`, tabel `ltd_quantiles`, dan meta `next_ta_note`, `ta_order_window_days`, `assumption_fields`, `frontier_note` |
| 6 | `ltd_quantiles` | ✔ `ltd_quantiles(material_no, q80, q90, q95, q97, q99, q995)`. Isinya kuantil demand selama lead time hasil simulasi, dalam unit |
| 7 | "Act now" = 394 | Pasti berubah, karena tanggal TA dan PR PO berubah. Komponennya sekarang: part TA A/B yang **sudah terlambat 19** dan **harus dipesan bulan ini 4**, ditambah part A/B **STOCKOUT 435**. Silakan hitung ulang di app dengan definisimu, lalu pakai angka itu di deck |

Poin §8 dashboard map: `materials.trust_flags` sudah ada (JSON: `price_verified`, `lt_samples`, `ledger_ok`, `has_twin`). `issues_monthly` tidak kubuat; cukup agregasi dari `consumption_monthly`.

## Angka yang berubah (pakai versi ini di deck)

| Angka | Lama | Baru |
|---|---|---|
| Spend IDR | Rp 3,144 B | **Rp 1,634 B** |
| Spend ke material di atas Max | 35,5% | **36,0%** |
| PR rush / rush yang terlambat vs normal | 17,3% / 91,9% vs 54,0% | **17,8% / 92,5% vs 52,9%** |
| Ledger tidak seimbang (E5) | 57,3% | **36,1%** (received/issued 2,19× → 1,30×) |
| BI-5 | "88,3% rush bisa dicegah" | **Dibuang** (lihat Orang 3 #6). Pakai: rush terlambat 92,5% vs 52,9% PR normal |
| Readiness TA A/B | 58,7% → 65,1% (TA 1 Nov) | **58,7% hari ini → 97,3% kalau setiap PR keluar sebelum order-by date** (TA 1 Jun 2027). 25 part sudah terlambat (19 A/B), 5 harus dipesan bulan ini, 209 bisa nanti |
| Stok yang bisa dilepas (harga PO) | Rp 405.0 B | **Rp 421.6 B** (207 part) |
| Part A/B berisiko stockout | 1.525 → 130 | **1.575 → 167** |
| AUC rolling (cold start) | 0,915 (0,845) | **0,916 (0,848)**. Backtest lama: 0,886 vs SBA 0,787; cold 0,836 vs 0,613. **Strict (tanpa Min/Max/MRP): 0,892 (0,773)**, tampilkan berdampingan |
| Skenario | optimized −37% modal | Min sekarang Rp 501 B, risiko 7,51 jt, fill A 94,2%. **Modal yang sama di frontier: risiko 0,08 jt, fill A 99,6%.** Default policy Rp 580 B, risiko −93%. Lean Rp 71 B untuk risiko setara hari ini |

Tetap sama: 154 part kurang untuk TA (137 A/B, 124 A). Kalimat "164 > Max" diganti (lihat Orang 3 #7).

## Jawaban per poin Orang 3

| # | Poin | Status |
|---|---|---|
| 1–2 | Dedup PR PO, `NEXT_TA` | ✔ Sudah (lihat di atas). TA 2027-06-01, 244 hari dari as_of |
| 3 | Bug order-by | ✔ **Valid, diperbaiki.** `slack = cover`, karena ROP sudah memuat demand selama lead time. Stok 0 dan ROP 0 tidak diberi tanggal. Stok tepat di ROP diberi tanggal pemakaian berikutnya yang diperkirakan. Stok < ROP jadi REORDER. Sekarang **hanya REORDER yang `order_by_date` = as_of**; MAINTAIN dan lainnya tersebar mulai 2026-10-06. Action sekarang: REDUCE 2.982 · MAINTAIN 2.113 · REORDER 1.698 · DISPOSE_REVIEW 546 · MONITOR 142 |
| 4 | BI-1 pakai buffer 14 hari | ✔ BI-1 sekarang memakai order-by TA (sudah termasuk buffer): 58,7% → 97,3% |
| 5 | Snapshot `mn`/`mx`/`mrp` | **Opsi kedua dari notes Orang 3 yang dipakai:** model utama tetap memakai Min/Max planner (di produksi nilainya diketahui saat forecast dibuat). Varian strict dihitung otomatis setiap build dan masuk `backtest` sebagai `engine_strict_mean`: **AUC 0,892, cold 0,773** (vs utama 0,916 / 0,848). Kalimat deck: *"uses current planner Min/Max as input; strict variant without them: AUC 0.89"*. Di `stress_prod.py`, varian "no snapshot" sekarang memakai saklar `STRICT_DEFAULT` |
| 6 | BI-5 | ✔ Klaim "preventable" dibuang. Diganti dengan rush terlambat 92,5% vs 52,9% |
| 7 | Kalimat E1 | ✔ *"For 79 stocked parts (71 A/B) the current Max is below one turnaround's need; 85 more kit parts have Max = 0 (82 are non-stock)."* Sudah diperbarui di `docs/03`, brief deck Orang 2, dan README pipeline |
| 8 | Kriteria lolos stress test | Dedup ✔, order-by hanya REORDER ✔, TA setelah tanggal presentasi ✔. Baris "as shipped" ≠ "no snapshot", dan itu disengaja (lihat #5) |

## Baru: metrik bisnis (policy backtest, scope §5.1)

Sudah ada di db, jadi Faiz tidak perlu membuat simulator dari nol. Kalau versimu sudah jalan, kita bandingkan saja.

- Tabel `policy_backtest(policy, fill_units, fill_units_AB, fill_lines, fill_lines_AB, stockout_days_AB, avg_inv_idr, avg_inv_idr_po, orders, note)`.
- Baris yang sama juga masuk ke `backtest` dengan method `policy_minmax_current`, `policy_partpulse`, `policy_partpulse_lean`, dan versi `_strict`. Kolom `note` berisi JSON, dan `coverage_q95` = fill rate baris A/B (format yang diminta Orang 2).
- Replay demand aktual Mar–Sep 2026. Kebijakan dihitung point-in-time per 1 Mar 2026.

| Kebijakan | Fill A/B (unit) | Stockout-days A/B | Nilai stok rata-rata |
|---|---|---|---|
| Min–Max sekarang | 35,8% | 57.055 | Rp 1,005 B |
| PartPulse lean | **95,0%** | **9.406 (−84%)** | **Rp 782 B (−22%)** |
| PartPulse default | 96,5% | 2.830 (−95%) | Rp 1,401 B |

Headline: *"with 22% less inventory value, critical-part fill rate rises from 36% to 95%"*. Caveat lengkap ada di `docs/04_MODEL_DECISIONS.md` §K: harga estimasi, modal pindah ke part yang bergerak, dan Min/Max konstan.

`docs/04_SCOPE_FINAL.md` masih menulis angka lama ("134 S/A", "88,3%", "164 > Max", "65,1%"). Faiz, tolong samakan dengan tabel di atas.
