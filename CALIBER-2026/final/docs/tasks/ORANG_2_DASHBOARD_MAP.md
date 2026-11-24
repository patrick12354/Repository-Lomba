# Orang 2 — Peta Dashboard PartPulse (rancangan v1)

> Pelengkap [ORANG_2_APP_DECK.md](ORANG_2_APP_DECK.md). File itu mengatur **stack, endpoint, deploy**. File ini mengatur **apa yang tampil di layar**: halaman, section, alert, dan aturan supaya mudah dibaca orang yang tidak paham AI.
> Angka di copy UI ada dua jenis. Yang berasal dari EDA (164, 116, 35,5%, Rp 413.8 B, 89/100, dll.) sudah dicek di `docs/01`–`03`. Sisanya (57%, 23 part, 120 hari, Order 48, Rp 3.2 M/yr, dll.) **hanya placeholder ilustrasi**. Angka final di app harus dari `partpulse.db`.

---

## 0. Ringkasan 30 detik

- **6 halaman + 1 halaman detail.** Judul tiap halaman berupa **pertanyaan**, jadi orang langsung tahu halaman itu untuk apa.
- Setiap halaman dibuka dengan **satu kalimat jawaban** yang dibuat otomatis dari data. Angka baru muncul setelahnya, dan istilah model disembunyikan di "Show the math".
- **Satu bahasa status** untuk seluruh app: *Act now / Plan / Watch / Ready / Excess / Idle / Use twin*. Selalu pakai warna + ikon + kata.
- **3D: tidak untuk inti.** Penggantinya **Furnace Map 2D isometrik** (P2), karena 119 dari 360 part turnaround memang terpasang di 12 furnace BF-101..112. Alasan lengkap di §6.

| # | Halaman (route) | Judul di UI = pertanyaan | Modul brief yang dijawab | Prioritas | Endpoint |
|---|---|---|---|---|---|
| 1 | **Shutdown Readiness** (`/`) | *Are we ready for the next turnaround?* | Forecast (event) + Recommendation | **P0 hero** | `/api/ta-readiness` |
| 2 | **Today** (home di HP, tab di Actions desktop) | *What needs attention today?* | Recommendation (alert) | **P0** (HP) | `/api/alerts` *(baru)* |
| 3 | **Actions** (`/actions`) | *What should we do, part by part?* | AI Recommendation & Cost-Risk | **P0** | `/api/parts` |
| 4 | **Part detail** (`/parts/[id]`) | *{Part name}: what to do, and why?* | Forecast + Dynamic Min–Max | **P0** | `/api/parts/[id]` |
| 5 | **Stock Health** (`/health`) | *Where is money stuck, and where are we exposed?* | Inventory Health Monitoring | P1 | `/api/overview` |
| 6 | **Demand Outlook** (`/forecast`) | *What will we need in the next 6 months?* | Demand Forecasting (KQ1) | P1 | `/api/forecast-summary` *(baru)* |
| 7 | **Scenarios** (`/scenarios`) | *What if we keep more or less stock?* | Dynamic Optimization + Cost-Risk Scenario | P1 | `/api/scenario` |
| 8 | **Data Trust** (`/trust`) | *Can we trust these numbers?* | Governance (slide Risk) | P1 | `/api/trust` |

Kalau waktu mepet: **Demand Outlook digabung** (section B dan E pindah ke Data Trust dan Stock Health). Halaman lain jangan dibuang, karena masing-masing menutup satu modul di brief.

---

## 1. Siapa yang membaca, dan aturan "orang awam AI pun paham"

| Pembaca | Pertanyaan di kepalanya | Halaman utamanya |
|---|---|---|
| Maintenance Planner | "Apa yang harus saya PR minggu ini supaya TA aman?" | Readiness, Today, Part detail |
| Warehouse / Inventory | "Barang apa yang numpuk, mana yang harus dihitung ulang?" | Stock Health, Actions (Reduce) |
| Procurement | "PR ini perlu nggak? Kapan paling lambat?" | Part detail, Actions |
| Plant / Maintenance Manager | "Kita siap atau nggak? Berapa modal yang terkunci?" | Readiness, Stock Health, Scenarios |
| **Juri** (laptop + HP, demo 3 menit) | "Input masuk, output keluar sesuai case?" | Jalur demo §10 |

**Aturan keterbacaan (wajib di semua halaman):**

1. **Satu halaman = satu pertanyaan.** Judul halaman adalah pertanyaannya.
2. **Kalimat dulu, angka kedua, model terakhir.** Section pertama setiap halaman adalah *headline sentence* yang dibuat dari template. Contoh: *"Next turnaround in 120 days. S-critical parts are 57% ready. 23 parts must be ordered this week."*
3. **Kata kerja, bukan skor.** Yang ditampilkan "Order now", bukan "p_move 0.73". Aksi selalu berupa kata kerja.
4. **Terjemahkan istilah model** (tabel di bawah). Istilah asli boleh muncul hanya di panel "Show the math" yang tertutup secara default.
5. **Status = warna + ikon + kata.** Tidak boleh warna saja (buta warna, layar HP di bawah matahari, print hitam putih).
6. **Maksimal 4 kartu KPI per halaman.** Setiap kartu punya satu baris arti, misalnya *"Rp 413.8 B sits above Max — money we could free."*
7. **Semua angka bisa diklik.** Mengklik angka membuka daftar part di baliknya (pola "everything routes" dari Prelim).
8. **Tandai asal angka.** Fakta tercatat tampil polos. Estimasi model diberi tag kecil `Estimate`. Approve/reject diberi tag `Demo` karena disimpan di localStorage.
9. **Tanggal selalu disertai sisa hari**: "Order by 12 Nov · 8 days left". Orang membaca sisa hari lebih cepat daripada tanggal.

**Kamus terjemahan (internal → yang tampil di UI):**

| Kolom / istilah | Tampil di UI | Contoh |
|---|---|---|
| `p_move` | "Chance it's needed in the next 6 months" dalam bentuk *x in 10* | "7 in 10 chance" |
| `q50` / `q95` | "Most likely" / "In a bad case" | "Most likely 4 EA, up to 9 in a bad case" |
| `rop`, `safety_stock` | "Reorder when stock drops to" / "Buffer" | "Reorder at 6 · buffer 2" |
| `min_new`/`max_new` vs `min_cur`/`max_cur` | "New range" vs "Current range" | "Range 5–10 → 6–14" |
| `lt_p90` | "Supplier can take up to" | "up to 160 days" |
| `order_by_date` | "Order by" + sisa hari | "Order by 12 Nov · 8 days left" |
| `cold_start = 1` | "Never used before. Estimate borrowed from similar parts on similar equipment" | — |
| `drivers` (JSON) | 3–5 bullet kalimat | "Installed in 12 places, 9 of them S-critical" |
| `trust_score` | 3 level: **High** (≥0,7) / **Medium** / **Check first** (<0,4) | "Check first: stock record doesn't match receipts" |
| `hold_cost_yr` / `risk_cost_yr` | "Cost to keep per year" / "Cost if we run out per year" | — |
| AUC backtest | "Out of 100 pairs, picks the right part N times" | "89 of 100 (classic method: 79)" |
| Criticality S/A/B/C | Badge huruf + tooltip "S = highest criticality … C = lowest" | **Jangan mengarang definisi S/A/B/C versi perusahaan** |

**Format angka (penting untuk UI bahasa Inggris):**
- Rupiah ditulis **"Rp 11.35 B"** (billion) dan **"Rp 850 M"** (million), dengan titik desimal. Di dokumen tim, "Rp11,35 M" artinya *miliar*. Kalau ini disalin mentah ke UI Inggris, juri akan membacanya sebagai *million*, salah 1.000×.
- Setiap rupiah ditambah catatan kecil *"on this dataset"* (aturan tim).
- Kuantitas selalu dengan satuan (EA, SET, M). Unit campuran **tidak boleh dijumlah** lintas material.

---

## 2. Bahasa status (satu untuk seluruh app)

Ada dua sumbu yang **tidak boleh dicampur warnanya**: **risiko** (merah → hijau) dan **uang terkunci** (ungu/abu). Kelebihan stok itu masalah modal, bukan bahaya, jadi tidak boleh merah.

| Status di UI | Warna (saran token) | Ikon (lucide) | Aturan dari data | Contoh kalimat |
|---|---|---|---|---|
| **Act now** | merah `--act` #C9372C | `alert-octagon` | TA `TOO_LATE`, atau `order_by` ≤ 7 hari pada S/A, atau `health = STOCKOUT` dan dipakai, pada S/A | "Too late to buy in time — expedite or use a twin." |
| **Plan** | amber `--plan` #B86E00 | `clock` | `order_by` 8–30 hari, atau `BELOW_MIN` | "Order by 2 Dec · 28 days left." |
| **Watch** | biru `--watch` #2563EB | `eye` | `action = MONITOR` | "Usage is picking up. No order needed yet." |
| **Ready / OK** | hijau `--ok` #15803D | `check-circle` | stok ≥ kebutuhan, `MAINTAIN` | "Enough stock for the turnaround." |
| **Excess** | ungu `--excess` #7C3AED | `package` | `OVER_MAX`, `action = REDUCE` | "862 SET on shelf, Max is 30. Rp X tied up." |
| **Idle** | abu `--idle` #6B7280 | `archive` | `NON_MOVING`, `OBSOLETE_CANDIDATE`, `DISPOSE_REVIEW` | "Not used in 17 months. Review for disposal." |
| **Use twin** | teal `--save` #0F766E | `repeat` | ada `twins.role = DONOR` | "Same part under 4100075099 has 566 above Max." |

Warna interaktif (tombol, link, tab aktif) = **navy/ink**, bukan biru, supaya biru hanya berarti *Watch*.

**Usulan kecil untuk `/api/ta-readiness`:** kontrak sekarang hanya punya 3 status (`READY` / `ORDER_NOW` / `TOO_LATE`). Akibatnya part yang order-by-nya masih 3 bulan lagi ikut terhitung "order now", dan itu menyesatkan. Tambahkan:
- `PLAN`: order-by 8–30 hari lagi.
- `LATER`: order-by > 30 hari lagi.

Rumusnya tetap `order_by = TA_date − lt_p90 − 14`.

---

## 3. Anatomi alert / kartu aksi

Satu komponen `ActionCard` dipakai di Today, Readiness board, Actions (mode kartu di HP), dan notifikasi PWA.

```
┌───────────────────────────────────────────────────────────────┐
│ ● ACT NOW   S                                  Order by 12 Nov │  ← status chip + crit badge + deadline (sisa hari tebal)
│ Gasket spiral wound 6" 300#                      8 days left   │  ← nama polos dulu
│ 4100012345 · Gasket · EA                                       │  ← nomor material kecil, mono
│                                                                │
│ Turnaround needs 40, you have 6. Supplier takes up to 65 days. │  ← SATU kalimat "why", ≤ 20 kata
│                                                                │
│ [ Approve order of 34 EA ]  [ Use twin (566 spare) ]   Why? ▾  │  ← 1 tombol utama + 1 alternatif + expander
└───────────────────────────────────────────────────────────────┘
```

Aturan kartu:
- Rumus kalimat: **apa yang terjadi → kenapa (1 alasan terkuat) → lakukan apa → kapan.**
- Hanya satu tombol utama. "Why?" membuka bullet `drivers` dan link ke Part detail.
- Urutan feed: status (Act now > Plan > Watch) → criticality (S > A > B > C) → sisa hari (kecil dulu) → nilai gap (besar dulu).
- Home/Today maksimal **5 kartu**, sisanya di "See all 23".

**8 tipe alert = "Expected AI capabilities" di brief hal. 4.** Tampilkan juga di deck slide Solution supaya juri bisa mencentang satu per satu.

| Capability di brief | Tipe alert kita | Template kalimat (English) |
|---|---|---|
| Stockout Risk | **Will run out** | "{part} may run out before new stock arrives. Order by {date}." |
| Reorder Recommendation | **Order now / Plan** | "Order {qty} {unit} by {date} ({n} days left)." |
| Overstock Risk | **Excess** | "{stock} on shelf, about {q95} needed in 6 months. {Rp} tied up." |
| Slow-Moving Alert | **Idle** | "Not used for {n} months." / "Never used in 17 months — review for disposal." |
| Dynamic Inventory Parameters | **Range update** | "Change range {min_cur}–{max_cur} → {min_new}–{max_new}: supplier now takes up to {lt} days." |
| Cost-Risk Optimization Scenarios | **Scenario hint** (di Scenarios) | "At this budget, risk drops {x}% for {Rp} more stock." |
| *(edge E1)* | **Shutdown gap** | "Turnaround needs {ta_qty}, you have {stock}." |
| *(edge E4)* | **Use twin** | "Same part under {no} has {n} above Max — transfer before buying." |

---

## 4. Navigasi

```
DESKTOP (sidebar kiri, 240px, bisa dilipat)        HP (< 768px, bottom nav 4 tab)
────────────────────────────────────────          ─────────────────────────────
 PartPulse                                          [Today] [Shutdown] [Search] [More]
 ─ Shutdown Readiness   ← halaman pertama              │        │          │        └ Health, Outlook,
 ─ Actions  (tab: Today | All parts)                   │        │          │          Scenarios, Trust
 ─ Stock Health                                        │        │          └ cari nomor/nama → Part detail
 ─ Demand Outlook                                      │        └ versi ringkas halaman 1
 ─ Scenarios                                           └ feed ActionCard + approve/reject
 ─ Data Trust
 ─────────────
 as of 4 Nov 2026 · dataset: dummy · Demo mode
Header: breadcrumb · search (Ctrl K: nomor material / nama part) · chip "TA in 120 days"
```

Part detail di desktop dibuka sebagai **drawer kanan** dari list (konteks list tidak hilang) dan punya URL sendiri (`/parts/[id]`) supaya bisa dibagikan. Di HP, Part detail tampil satu halaman penuh.

---

## 5. Isi tiap halaman (urutan section = urutan di layar)

### 5.1 Shutdown Readiness (`/`), P0 hero

| # | Section | Isi | Visual | Catatan |
|---|---|---|---|---|
| A | **Control bar** | Tanggal TA (default `meta.next_ta_default`) + ukuran TA dengan 3 preset: *Smaller 0.7× · Same as last 1.0× · Bigger 1.3×* + slider 0,5–1,5× | date picker + segmented button | Label slider: "How big is the turnaround? 1.0× = same as the last one (Nov 2025–Jan 2026)" |
| B | **Headline sentence** | "Next turnaround in **120 days**. S-critical parts are **57% ready**. **23 parts** must be ordered this week." | teks besar, 24–28px | Dibuat dari template dan berubah live saat slider digeser. Ini momen demo |
| C | **Readiness per criticality** | 4 kartu: S, A (lebih besar), B, C. Isi: "57% ready · 86 of 150 parts" | progress bar tebal / ring dengan angka di tengah | Selalu tulis pecahannya ("86 of 150"), jangan persen saja |
| D | **Deadline wall** | Sumbu waktu hari ini → tanggal TA. Batang = jumlah part yang order-by-nya jatuh di minggu itu. Zona merah di kiri "Already too late: 31" | bar chart mingguan horizontal | Klik batang → board di bawah terfilter ke minggu itu |
| E | **Action board** | 4 lajur: **Too late** (expedite / twin) · **Order this week** · **Plan (8–30 d)** · **Ready** (tertutup, cuma hitungan) | kolom kartu `ActionCard` (tanpa drag) | Tabel wajib di brief Orang 2 = lajur ini |
| F | **Why Min–Max can't cover this** | "**164 parts** need more for one turnaround than their Max allows." + 10 contoh | dumbbell: titik Max vs titik kebutuhan TA | Bukti untuk hook deck slide 2 |
| G | *(P2)* **Furnace map** | 12 furnace BF-101..112 diwarnai % siap. Klik furnace → board terfilter | SVG isometrik 2D | Lihat §6 |

### 5.2 Today, P0 (home di HP, tab pertama di Actions desktop)

| # | Section | Isi |
|---|---|---|
| A | Sapaan + tanggal + chip countdown | "Wed, 4 Nov · Turnaround in 120 days" |
| B | 3 penghitung besar | **Act now 12** · **Plan 31** · **Use twin 9** (klik → list terfilter) |
| C | Feed 5 `ActionCard` teratas | approve / reject langsung di kartu (tag `Demo`) |
| D | "Done today" | jumlah yang sudah di-approve dan di-reject di device ini |

Endpoint baru `GET /api/alerts?limit=5` menggabungkan TA `TOO_LATE`/`ORDER_NOW`, `policy.action = REORDER` dengan `order_by` ≤ 7 hari, `STOCKOUT` S/A, dan twin donor, lalu mengurutkannya dengan aturan §3.

### 5.3 Actions (`/actions`), P0

| # | Section | Isi | Visual |
|---|---|---|---|
| A | **Verb strip** | *Order 48 (Rp 2.1 B) · Reduce 312 (frees Rp 41 B) · Review disposal 90 · Watch 1,200 · Keep 5,800*. Klik = filter | 5 pil besar dengan angka |
| B | **Filter** | Chip crit S/A/B/C · health · kategori · "Deadline ≤ 30 days" · search nomor/nama | bar filter + chip aktif yang bisa dihapus |
| C | **List** | Desktop: tabel `Status · Part · Crit · Stock vs new range (mini bar) · Order by · Why (1 kalimat) · Approve`. HP: `ActionCard` | tabel, baris 48px |
| D | **Bulk** | "Approve selected (demo)" + "Download CSV" (client-side) | — |

### 5.4 Part detail (`/parts/[id]`), P0

| # | Section | Isi | Visual |
|---|---|---|---|
| A | **Header** | Nama polos · nomor · badge crit · kategori · chip status. Kalimat rekomendasi: "**Order 4 EA by 12 Nov** (8 days left)." + Approve / Reject | — |
| B | **Stock gauge** | "Stock **2** · current range 5–10 · new range **6–14**" | satu bar horizontal: marker stok, kotak abu = range lama, kotak berwarna = range baru. **Visual ini sendirian sudah menjelaskan "dynamic Min–Max"** |
| C | **Timeline** | Today → Order by → Arrives (LT P90) → Turnaround / next need | garis dengan 4 titik |
| D | **Demand** | 17 bulan batang konsumsi (bulan TA diarsir + label "turnaround") + pita forecast 6 bulan: "Most likely 4, up to 9 in a bad case" | bar + band q50–q95 |
| E | **Why** | 3–5 bullet dari `drivers`: "Installed in 12 places (9 S-critical)", "3 breakdowns on this equipment in 90 days", "Supplier takes up to 160 days" | bullet + bar kecil pembanding |
| F | **Keep vs run out** | "Keeping it costs **Rp 3.2 M/yr**. Running out risks **Rp 410 M/yr**." | 2 angka berdampingan |
| G | *(P2)* **Twin stock** | "Same part under 4100075099 has 566 above Max → transfer before buying" + tombol | kartu teal |
| H | **Data check** | ✓ price from 6 POs · ✓ lead time from 12 orders · ⚠ stock record doesn't match receipts → "Count before ordering" | checklist |
| I | **Show the math** (tertutup) | service level, SS, ROP, q50/q90/q95, ltd_mean/var, rumus, sumber lead time (`lt_source`) dan harga (`price_source`) | tabel kecil |

Kalau `cold_start = 1`, tampilkan banner di section D: *"Never used before. Estimate borrowed from {n} similar parts installed on the same kind of equipment."* Ini edge E3, jadi tunjukkan dengan bangga.

### 5.5 Stock Health (`/health`), P1 (gabungan "Overview" + modul Health)

| # | Section | Isi | Visual |
|---|---|---|---|
| A | **4 KPI** | Stock value (priced items) · **Above Max: Rp 413.8 B** · **Critical parts at zero stock: 116** · **Never used in 17 months: 68.2%** | stat tile + 1 baris arti |
| B | **Health bar** | 3.656 stock item dipecah: Stockout · Below Min · OK · Above Max · Not moving · Obsolete candidate | **satu bar 100% bertumpuk** (lebih mudah dibaca daripada donut) |
| C | **Risk × Money (2×2)** | Critical & short = *Fix now* · Critical & excess = *Review* · Non-critical & short = *Watch* · Non-critical & excess = *Free cash* | 4 kotak besar dengan angka |
| D | **Top 10 money tied up** | bar horizontal nilai di atas Max + chip "Reduce" | — |
| E | **Last used** | <3 bln · 3–6 · 6–12 · >12 · never | bar bertingkat |
| F | **Before you buy** | "**35.5%** of PO spend went to parts already above Max." → penjelasan guardrail PR | callout |

### 5.6 Demand Outlook (`/forecast`), P1 (KQ1 tampil di layar)

| # | Section | Isi | Visual |
|---|---|---|---|
| A | Headline | "About **N parts** will likely be needed in 6 months. **M** of them have never been used before." | teks |
| B | **History** | Baris issue per bulan selama 17 bulan. Lonjakan Nov–Jan diberi anotasi: *"Turnaround orders (2030), not seasonality."* | line/bar + anotasi |
| C | **Where demand comes from** | Jumlah part yang demand-nya terutama *breakdown & routine* vs *turnaround* (hitung part atau Rp, **bukan unit campuran**) | 2 batang |
| D | **Likelihood by criticality** | Very likely (≥7 in 10) · Possible · Unlikely, per S/A/B/C | stacked bar |
| E | **Hidden demand** | List part `cold_start = 1`, peluang tinggi, stok 0: "Never used, 8 in 10 chance. Installed in 14 places." | list kartu |
| F | Proof mini | "Picks the right part 89 of 100 times" → link ke Trust | chip |

### 5.7 Scenarios (`/scenarios`), P1

| # | Section | Isi | Visual |
|---|---|---|---|
| A | **Preset** | *Current policy · Lean (free cash) · Balanced (recommended) · Safe for critical* | 4 tombol besar. Orang awam cukup memakai ini |
| B | **3 hasil** | Stock value · Expected risk cost / yr · "Critical parts on the shelf when needed" S / A, masing-masing dengan selisih vs current dalam kata: "−Rp 120 B vs today" | stat tile |
| C | **Frontier** | Kurva budget vs risk. Titik "Today" vs titik preset terpilih + kalimat: "Same risk as today with Rp X less stock." | line + 2 titik berlabel |
| D | **What changes** | "+42 parts get stock · −310 parts reduced" → daftar | 2 list |
| E | **Adjust assumptions** (tertutup) | slider service level per crit, holding rate, downtime cost/hari per crit. Tiap slider punya kalimat arti dan tag `Assumption` | slider |
| F | Catatan | "Downtime cost and holding rate are assumptions, not company data." | footnote |

### 5.8 Data Trust (`/trust`), P1

| # | Section | Isi | Visual |
|---|---|---|---|
| A | Headline | "We checked the data before using it. We found {n} traps." | teks |
| B | **Data traps** | Satu kartu per `dq_issues`, dengan format **found → what it would break → what we did**. Wajib ada: *PO-Item Amount is a unit price* (spend terbaca ~19× terlalu kecil), ledger tidak seimbang (57,3%), duplikat BoM, harga hilang, kembaran | kartu |
| C | **Forecast proof** | "Pick one part that was used and one that wasn't. Our model ranks the used one higher **89 times out of 100** (classic SBA: 79). For parts with no history: **84 vs 61**." | 2 pasang batang |
| D | **Trust levels** | High / Medium / Check first + daftar "Count these first" (prioritas cycle count) | bar + list |
| E | **Assumption register** | isi `meta`: holding rate, service level, downtime cost, TA window | tabel |

---

## 6. 3D model: perlu atau tidak?

**Putusan: jangan untuk inti. Ganti dengan Furnace Map 2D isometrik (P2). 3D sungguhan hanya kalau semua P0–P1 sudah live sebelum 00.30.**

Alasan:
1. **Keputusan di case ini soal part, tanggal, dan jumlah, bukan lokasi.** Pertanyaan "apa yang harus dipesan dan kapan" tidak terjawab lebih cepat oleh adegan 3D. Orang awam membaca daftar berwarna lebih cepat daripada model yang harus diputar.
2. **Data tidak punya koordinat.** FuncLoc cuma punya kode tag (BF, KC, PP, HE…). Peta 3D pabrik pasti hasil karangan, dan juri Chandra Asri akan langsung melihat "itu bukan plant kami". Di Prelim pun kita harus memberi label *"Schematic layout, not a plot plan"*.
3. **Biaya.** three.js + react-three-fiber menambah ratusan KB, berat di HP (padahal PWA wajib), dan butuh 2–4 jam dari jendela kerja ~8 jam.
4. **Pelajaran Prelim.** Nilai Presentation 13/20 karena *padat, banyak angka kecil, framing defensif*, bukan karena kurang 3D. 3D di Prelim (PlantSite, MachineView) tidak mengangkat skor itu.

Yang **didukung data** dan bisa jadi momen "wow" kecil:
- **119 dari 360** material TA terpasang di 12 furnace **BF-101..112** (35–44 material per furnace). Furnace juga kandidat pilot (F10: 553 notif, terbanyak).
- **Furnace Map:** 12 blok furnace dalam satu baris isometrik (CSS transform / SVG). Warnanya mengikuti % siap TA, dan klik satu furnace memfilter board di Readiness. Di samping peta ada kelompok lain sebagai tile: Compressors (KC), Pumps (PP), Exchangers (HE).
- Data yang dibutuhkan: tabel `material_location` (lihat §8). Kalau Orang 1 tidak sempat, Orang 2 bisa membuatnya dengan script kecil dari BoM (regex `BF-1\d\d`).
- Kalau tetap mau 3D: pakai ulang `components/three/` dari Prelim lewat `next/dynamic` dengan `ssr: false`, lazy-load, dan sediakan fallback 2D di HP. **Bukan P0.**

---

## 7. Diambil dari Prelim (PlantPulse) vs dibuang

Sumber: `CALIBER - Prelim/Caliber-2026-Heisenberg/prototype/DESIGN.md`, `prototype/docs/ui-rebuild-guide.md`, `docs/evaluasi_juri_project_dan_pitch_deck_2026-10-04.md`.

| Ambil | Kenapa |
|---|---|
| Kosakata status ketat, ikon + label, tidak pernah warna saja | Inti keterbacaan |
| **Stat tile** (garis warna 2px, label + ikon, nilai, 1 chip konteks, tanpa ring) | Sudah teruji, tinggal port `stat-tile.tsx` |
| "Everything routes": setiap angka/baris membuka halaman yang dijelaskannya | Juri bisa mengeksplorasi sendiri |
| Nama dulu, tag/nomor kecil mono | Material number 10 digit tidak terbaca orang awam |
| Intro halaman = 1 kalimat | Melawan "terlalu padat" |
| Pisahkan fakta tercatat / estimasi model / simulasi (tag `Estimate`, arsiran untuk `Demo`) | Kredibilitas di depan juri praktisi SAP |
| Font IBM Plex Sans + Plex Mono (tema light Prelim) | Wajah industrial dan angka tabular |

| Buang / ubah | Kenapa |
|---|---|
| Background WebGL mesh + tema gelap | Mahal waktu, menurunkan kontras. **Light only** untuk final |
| Framing defensif (guard, test passed) di layar utama | Feedback juri: *business value dulu*. Caveat cukup di Data Trust |
| Banyak angka kecil per kartu | Maks. 4 KPI, 1 angka besar per kartu |
| 3D sebagai fitur utama | §6 |
| Gauge melingkar untuk semua hal | Untuk readiness pakai bar/ring yang **menulis pecahannya** |

Komponen dari library 21st (`~/.claude/skills/ui-21st/library/INDEX.md`) yang cocok:
- `dashboard/dashboard-collapsible-sidebar` → shell.
- `dashboard/task-list-card` → feed Today dan lajur board.
- `dashboard/project-data-table` → tabel Actions.
- `forms/task-filters-panel` → filter Actions.
- `dashboard/kanban-board-pointer-drag` → **styling kartu saja**, tanpa drag.
- `data-viz/contribution-skyline` → referensi gaya isometrik untuk Furnace Map.

---

## 8. Permintaan data tambahan ke Orang 1 (umumkan di grup, karena kontrak sudah dikunci)

| # | Tabel / kolom | Untuk | Prioritas |
|---|---|---|---|
| 1 | `consumption_monthly(material_no, month TEXT 'YYYY-MM', qty REAL, qty_ta REAL)` | Grafik konsumsi bulanan di Part detail. **Sudah diminta brief Orang 2, tapi belum ada di kontrak** | P0 |
| 2 | `issues_monthly(month, lines_total, lines_ta)` | Grafik history + anotasi TA di Demand Outlook | P1 |
| 3 | `materials.trust_flags TEXT` (JSON: `price_verified`, `ledger_ok`, `has_twin`, `lt_samples`) | Checklist "Data check" di Part detail. `trust_score` angka saja tidak terbaca orang awam | P1 |
| 4 | `material_location(material_no, equipment TEXT, equip_class TEXT)` (minimal untuk material TA) | Furnace Map | P2 |
| 5 | `meta.next_ta_default`, `meta.as_of_date` dipastikan terisi | Control bar + headline | P0 |

Endpoint baru di sisi Orang 2 (tidak mengubah db): `GET /api/alerts`, `GET /api/forecast-summary`.

---

## 9. Urutan build (selaras checkpoint di 00_TEAM_PLAN)

| Jendela | Kerjakan |
|---|---|
| Sebelum 21.00 (db dummy) | Shell + token status + komponen `ActionCard`, `StatTile`, `StockGauge`. Skeleton Readiness + Part detail. **Deploy kosong ke Vercel sebelum 22.00** (cek bundling SQLite) |
| 21.00–00.30 (db v0) | Readiness A–E lengkap, Actions, Part detail A–E + H, Today (HP), PWA manifest |
| 00.30–03.00 (db v1) | Scenarios, Stock Health, Data Trust, Demand Outlook. Lalu P2: twin, Furnace Map |
| 03.00–03.30 | Freeze. Jalankan checklist §11, cek 375px, screenshot |

Kalau waktu mepet, yang dipotong berurutan: Furnace Map → Demand Outlook (digabung) → section E Stock Health → bulk approve.

---

## 10. Jalur demo juri (layar dirancang mengikuti ini)

1. **Readiness**: baca headline → geser ukuran TA 1.0× → 1.3× → readiness S turun live → tunjuk lajur "Order this week".
2. Klik satu kartu → **Part detail**: stock gauge (range lama vs baru), timeline, "Why", dan tombol *Use twin*.
3. **Approve** (tag Demo).
4. **Scenarios**: Lean vs Safe for critical → titik bergeser di frontier.
5. **Data Trust**: "89 of 100" + jebakan *PO-Item Amount is a unit price*.
6. **HP**: buka PWA → Today → approve satu kartu.

---

## 11. Checklist keterbacaan sebelum freeze

- [ ] Setiap halaman dibuka dengan satu kalimat jawaban.
- [ ] Tidak ada `p_move`, `q95`, `ROP`, `AUC`, `LTD`, `service level` di luar "Show the math" / Scenarios advanced.
- [ ] Setiap status punya ikon + kata, tidak hanya warna.
- [ ] Rupiah ditulis B/M versi Inggris, dengan "on this dataset".
- [ ] Setiap tanggal disertai sisa hari.
- [ ] Maks. 4 KPI per halaman, dan setiap KPI punya kalimat arti.
- [ ] Setiap angka bisa diklik ke daftar di baliknya.
- [ ] Estimasi bertag `Estimate`, approve/reject bertag `Demo`.
- [ ] **Tes 5 detik:** tunjukkan satu halaman ke orang non-teknis selama 5 detik. Dia harus bisa menjawab "apa yang harus dilakukan?"
- [ ] HP 375px: tidak ada scroll horizontal, tombol ≥ 44px, angka utama ≥ 28px.
