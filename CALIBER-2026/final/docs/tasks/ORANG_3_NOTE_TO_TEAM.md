# Note dari Orang 3 untuk tim (4 Nov 2026)

Stress test dan feasibility E1–E4 dijalankan terhadap engine produksi (`pipeline/build_db.py`, commit `8d72a90`) dan `app/data/partpulse.db`.
- Hasil per edge: [04_SCOPE_FINAL.md §9](../04_SCOPE_FINAL.md).
- Script: `py analysis/stress_prod.py` → `analysis/stress_prod_output.txt`. Script ini tidak menulis db.
- Unique point tambahan (U1–U6): [04_SCOPE_FINAL.md §8](../04_SCOPE_FINAL.md).

**Ringkas:** klaim E1 dan E4 lolos dengan rewording. E2 (order-by) dan E3 (angka cold-start) **belum lolos**.

## Untuk Orang 1 (Engine), urut prioritas, target sebelum 13:00 bersama scope §4

1. **Dedup PR PO** (scope §4; sama dengan note Orang 2 #1): di `analysis/build_mat.py`, `p = pp.drop_duplicates().copy()`. Efeknya ke engine kecil (AUC tidak berubah), tetapi angka spend di deck jadi **Rp1.634,2 M**.
2. **`NEXT_TA`** (`build_db.py:23`; sama dengan note Orang 2 #4) → `2027-06-01` sesuai scope §4, dengan label "planning assumption". Dengan tanggal sekarang (32 hari dari as_of), ke-137 part A/B kurang mendapat `order_by_date` = as_of semua. Hasil uji (lead time p90 + buffer 14 hari, dihitung dari as_of):

   | Jarak ke TA | Readiness A/B setelah order hari ini | Part A/B yang sudah terlambat |
   |---|---|---|
   | 180 hari | 93,7% | 21 |
   | 240 hari | 96,7% | 11 |

   Kalau ingin demo yang lebih tegang, ~2027-04-01 (±180 hari) bisa dipakai. Pilih salah satu, lalu samakan di `meta` dan deck.
3. **Bug order-by** (`build_db.py:355`): saat ini semua 1.628 REORDER **dan 1.776 MAINTAIN** mendapat `order_by_date` = as_of. Untuk demand normal, `slack = cover` (hari sampai stok menyentuh ROP), bukan `cover - lt90`, karena ROP sudah memuat demand selama lead time. Baris TA (`ob_ta = NEXT_TA − lt90 − TA_BUFFER`) sudah benar. Cek ulang setelah fix: part MAINTAIN harus punya tanggal ke depan yang tersebar, dan hanya REORDER yang boleh = as_of.
4. **BI-1** (`build_db.py:538`): `in_time` harus memakai `lt90 + TA_BUFFER` supaya sama dengan order-by. Dengan buffer, readiness setelah order 59,3%, bukan 65,1%.
5. **E3 leakage:** `mn`, `mx`, `mrp` adalah snapshot BoM yang dibaca setelah jendela tes, sama seperti `stock`. Buang ketiganya dari `X_cols` (`build_db.py:173`), beserta `X['mrp']` di `prep`.
   - Hasil uji tanpa ketiganya: AUC 0,915 → **0,892** (naive 0,835), cold 0,845 → **0,769**. Biayanya cuma −0,023 AUC all, dan klaimnya jadi aman dari pertanyaan juri.
   - Update juga: BI-4, `04_MODEL_DECISIONS.md` §C/§D, tabel `backtest`, dan `NICE['mn'/'mx']` di kalimat `reason`.
   - Angka baru untuk deck: **AUC 0,89 vs naive 0,84; cold-start 0,77**. Kalau tim memilih tetap memakai Min/Max, wajib disebut "uses current planner Min/Max as input" dan angka strict ditampilkan berdampingan.
6. **BI-5:** hapus klaim "88,3% preventable". Tes yang sama pada PR *non-rush* memberi 85,8%, jadi angka itu tidak membedakan apa pun. Ganti dengan statistik yang lolos uji: *"rush PRs arrive late 92.5% of the time vs 52.9% for normal PRs (de-duplicated)"*.
7. **Rewording E1 di `docs/03` dan deck:** *"For 79 stocked parts (71 A/B) the current Max is below one turnaround's need; 82 more kit parts are not stocked at all."* Jangan pakai "164 > Max" tanpa rincian ini, karena 85 di antaranya punya Max = 0.
8. **Setelah 1–5 selesai:** rerun `py pipeline/build_db.py`, lalu `py pipeline/app_tables.py` (note Orang 2 #3), lalu `py analysis/stress_prod.py`. Kriteria lolos:
   - baris "as shipped" sama dengan baris "no snapshot + dedup";
   - `order_by_date` = as_of hanya untuk REORDER;
   - `next_ta_default` jatuh setelah tanggal presentasi.

## Untuk Orang 2 (App + Deck)

- Twin stock (E4) valid tapi nilainya kecil (Rp0,18–0,66 M). Jual sebagai "fix without buying". Beri label "confirm interchangeability", karena 25 dari 57 grup punya kembaran di FL yang sama.
- Sampai butir 3 di atas di-fix, kolom "Raise PR by" di app akan menampilkan as_of untuk hampir semua part.
