# 03 — Usulan Edge (untuk diskusi tim)

> Semua angka dari `py analysis/edge_tests.py` → `analysis/edge_tests_output.txt`, kecuali yang ditandai lain. Ini bahan diskusi, belum keputusan.

## Kenapa blueprint v1 belum cukup tajam

Forecast + Min/Max + dashboard + slider adalah jawaban yang **diminta brief**. Artinya hampir semua dari 10 tim akan menyajikannya. Edge harus datang dari sesuatu yang:
1. ditemukan di data dan **tidak tertulis di brief maupun diagram**,
2. langsung menjawab *trigger* di brief hal. 2: *"When a shutdown happens, the critical part we need is out of stock"*,
3. bisa didemokan dalam 30 detik.

---

## E1 ★ Shutdown Replay & Readiness Countdown (usulan hero)

**Temuan yang tidak ditulis di mana pun:** order berawalan **2030** adalah order kampanye shutdown/turnaround.
- Normalnya 1–5 order per bulan, lalu melonjak ke **31 order di Nov 2025** dan **22 di Des 2025**.
- Ke-57 order TA itu memakai **360 material**. Hasil pemakaian ini kita sebut **TA bill of parts**, yang selama ini tidak ada di sistem.

**Replay: "kalau TA yang sama terjadi hari ini?"**
- **154 dari 360** material TA stoknya kurang dari kebutuhan TA terakhir. **137** di antaranya di FL kritis **A/B** (124 di A), dan 77 stoknya nol. *(Urutan criticality A > B > C > S sesuai panitia, 4 Nov.)*
- **Kebutuhan TA melebihi Max pada 164 material (149 di A/B).** Artinya Min–Max statis *secara desain* tidak akan pernah bisa menutup shutdown, karena Max-nya lebih kecil dari kebutuhan satu event. Ini bukti kuantitatif untuk akar masalah "static planning" di brief hal. 3.
- 82 material di kit TA bertipe *Non Stock*, jadi tidak pernah direncanakan sama sekali.
- Gap untuk material yang punya harga: **Rp11,35 M**. Lead time P90 part yang kurang: median 65 hari, P90 213 hari.
- **Procurement tidak bereaksi terhadap TA.** PR untuk material kit TA flat 430–480 baris per bulan, sebelum maupun sesudah TA.

**Fitur:**
1. User memilih tanggal TA berikutnya (misalnya slider). App memutar ulang TA bill of parts dengan skala tertentu.
2. Untuk tiap part, app menghitung **latest safe order date = tanggal TA − lead time P90** (lead time per supplier/material).
3. Output: **readiness % per criticality**, daftar "harus PR minggu ini", dan countdown.
4. Di HP: notifikasi saat sebuah part melewati batas tanggal pesan aman.

**Kenapa tim lain hampir pasti tidak punya ini:** label "2030 = shutdown" tidak ada di data maupun di diagram. Kebanyakan tim akan membaca lonjakan Nov–Jan sebagai musiman atau outlier, lalu membuangnya.

**Momen demo:** *"Your next turnaround is in 120 days. Today you are 59% ready on A-critical parts. These 23 parts must be ordered this week or they will arrive after the shutdown starts."*

---

## E2 ★ Planning-Lag Detector: "Latest Safe Order Date" untuk semua part

**Temuan:**
- **17,8%** baris PR meminta tanggal kirim **kurang dari setengah lead time normal** material tersebut. Baris-baris ini mewakili **19,7%** nilai PR IDR. *(dedup PR PO, 4 Nov)*
- **92,5%** dari PR "mustahil" ini akhirnya dijadwalkan terlambat. Sebagai pembanding, PR normal terlambat 52,9%.
- Ini bukti langsung untuk *"Planning lags behind"* (brief hal. 2): kebutuhan baru disadari saat sudah terlambat.

**Fitur:**
- Setiap part punya **order-by date** yang dihitung dari forecast KQ1 + stok + lead time P90.
- **PR coach:** saat PR dibuat dengan tanggal yang tidak realistis, sistem memberi peringatan dan menunjukkan tanggal realistisnya.
- KPI: "% PR yang dibuat sebelum order-by date", yang menjadi success metric di slide Business Impact.

**Catatan jujur:** di data ini tidak ada premi harga untuk PR rush (rasio harga 1,00). Jadi biaya rush ditanggung lewat **keterlambatan dan risiko downtime**, bukan lewat harga beli. Jangan klaim "rush lebih mahal".

---

## E3 Cold-start forecast: memprediksi part yang belum pernah dipakai (dari blueprint v1)

- 40% part yang bergerak di periode test (344 dari 868) tidak punya histori sama sekali.
- Pada part tanpa histori, model driver-based kita mencapai AUC **0,841**, sementara SBA hanya **0,613** (lihat `analysis/backtest_output.txt`).
- Peran di cerita: **mesin** di balik E1 dan E2, bukan hero-nya.

---

## E4 Twin Materials: "stok tersembunyi" di master data

**Temuan:**
- Ada **155 grup** deskripsi identik dengan nomor material berbeda, total **641 material**.
- Di **57 grup**, satu kembaran sedang kurang (di bawah Min, atau nol padahal dipakai) sementara kembaran lain **di atas Max**.
- Contoh: castable refractory insul 1300°C punya 4 nomor material. Satu bertipe Stock dengan stok 0, satu lagi Non Stock dengan stok 4.406.

**Fitur:** *Master-data agent* yang menggunakan LLM dan fuzzy matching untuk mengelompokkan material yang sama atau interchangeable. Untuk material yang kurang, agent menawarkan **"use twin stock"** sebelum PR baru dibuat.

**Kenapa tajam:** solusi ini mengurangi stockout *tanpa membeli apa-apa*. Penggunaan LLM-nya juga masuk akal, bukan tempelan.

---

## E5 Trust Layer: audit data sebelum dipercaya

**Jebakan data yang kami temukan:**
- `PO-Item Amount` adalah **harga satuan**, bukan nilai baris. Dalam satu material nilainya hampir konstan (median CV 2,1%) dan tidak berkorelasi dengan qty (r = 0,03), dicek dengan `py analysis/eda.py` dan diuji manual.
- Tim yang menjumlahkannya langsung akan membaca spend **~18× terlalu kecil**: Rp89,2 M, padahal Rp1.634,2 M (setelah dedup PR PO).
- Setelah dikoreksi, gambaran berubah. **36,0% spend jatuh ke material yang stoknya sudah di atas Max.** Klaim lama kita bahwa "34% spend ke material tak terpakai" ternyata hanya 2,7%, dan sudah dikoreksi di 01 dan 02.

**Ledger tidak seimbang:**
- Kuantitas PO yang dijadwalkan datang adalah **1,30×** kuantitas issue (median). *(dedup PR PO, 4 Nov)*
- Pada **36,1%** material, stok awal yang tersirat jadi negatif. Artinya receipt, issue, dan snapshot stok tidak saling cocok: ada GR yang tidak tercatat, konsumsi langsung ke order, atau stok fisik yang berbeda.

**Fitur:** panel **Data Trust Score** per material (harga terverifikasi, ledger cocok, ada/tidak kembaran, lead time cukup sampel), ditambah **daftar prioritas cycle count**. Rekomendasi dengan trust rendah diberi label dan butuh verifikasi manusia.

**Kenapa tajam:** juri Chandra Asri adalah praktisi SAP. Mereka akan menghargai tim yang menangkap jebakan data ini, dan ini juga menjawab bagian risk/governance di slide Roadmap & Risk.

---

## Hipotesis yang sudah diuji dan gugur (supaya tidak dipakai)

| Ide | Hasil | Keputusan |
|---|---|---|
| Teks notifikasi → tebak part yang dibutuhkan | Hit top-3 kategori **37,6%**, lebih buruk dari baseline popularitas **49,7%** | Gugur, karena di data dummy ini teks dan part tidak berkaitan |
| Redundansi pompa A/B dari nama FL sebagai pengganti downtime cost | Hanya 115 grup sibling dari 14.484 FL | Gugur |
| Premi harga untuk PR rush | Rasio harga 1,00 | Gugur. Biaya rush berbentuk keterlambatan, bukan harga |
| Jumlah PM jatuh tempo per bulan sebagai leading indicator issue bulanan | Korelasi 0,04 | Gugur di level agregat. PM tetap dipakai sebagai fitur per material (fitur #1 di model) |

---

## Rangkaian yang aku rekomendasikan

**Storyline:** *"Your Min–Max was built for normal days. Shutdowns break it by design."*

1. **Hook (problem):** pada 79 part yang distok (71 A/B), Max-nya lebih kecil dari kebutuhan satu TA; 85 part kit lain bahkan Max = 0. Replay TA terakhir: 137 part A/B (124 A) tidak siap hari ini.
2. **Hero feature:** E1 Shutdown Readiness Countdown, yang menjawab KQ1 (event demand) dan KQ2 (kapan dan berapa reorder).
3. **Mesin:** E3 cold-start forecast + E2 order-by date + optimizer cost–risk dari blueprint v1.
4. **Uang tanpa beli:** E4 twin stock, ditambah 36,0% spend ke material yang sudah di atas Max dijadikan PR guardrail.
5. **Trust:** E5 sebagai pembeda kredibilitas di slide Risk.

## Yang perlu kita putuskan bersama

1. Setuju E1 jadi hero? Alternatifnya E4 (lebih "AI") atau E2 (lebih "operasional").
2. Tanggal TA berikutnya di demo: dibuat slider, atau diasumsikan 12 bulan setelah TA terakhir (Nov 2026, yaitu *sekarang*)? Jangan klaim jadwal TA Chandra Asri yang sebenarnya tanpa sumber.
3. Berapa banyak dari E1–E5 yang realistis dibangun sampai 06.00? Usulanku: E1 + E2 + E3 wajib, E4 versi rule-based, E5 sebagai panel sederhana.
