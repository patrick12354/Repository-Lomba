# 01 — Pemahaman Data & EDA: Case 3 Spare Part Intelligence

> CALIBER 2026 Final (hackathon 24 jam, 4–5 Nov 2026). Semua angka di sini berasal dari `py analysis/eda.py` (output lengkap: `analysis/eda_output.txt`). Data **dummy/sintetis**: strukturnya meniru SAP PM/MM, tapi nilainya bukan nilai asli (catatan di diagram relasi hal. 2). Jadi yang dijual adalah **pola dan mekanismenya**, bukan rupiah absolutnya.

## 0. Brief (sumber: `docs/CALIBER 2026 - Final Case Brief.pdf`)

**Case:** *Spare Part Intelligence & Inventory Optimization — AI-Powered Forecasting & Dynamic Optimization.*

**Objective** (hal. 2): forecasting yang lebih baik, keputusan inventory yang dinamis, excess inventory dan working capital turun, dan availability part kritis tetap terjaga.

**Masalah menurut brief** (hal. 2–3):
- Saat shutdown, part kritis justru kosong, sementara part slow-moving yang tidak dibutuhkan menumpuk.
- Penyebabnya:
  1. *Static planning*: perencanaan hanya berbasis histori konsumsi, dengan Min–Max statis.
  2. *Suboptimal balancing*: criticality dan lead time tidak konsisten dipakai dalam keputusan stok.
- Dampaknya: emergency procurement, biaya beli dan biaya simpan naik, working capital terkunci, dan downtime.

**Expected solution** (hal. 4), empat modul:
1. Demand Forecasting.
2. Dynamic Inventory Optimization (Min–Max, Safety Stock, ROP, qty replenishment).
3. Inventory Health Monitoring (excess, slow-moving, non-moving, obsolete).
4. AI Recommendation & Cost–Risk Optimization (reorder / maintain / reduce / monitor).

Output yang diminta: Stockout Risk, Overstock Risk, Reorder Recommendation, Slow-Moving Alert, Dynamic Inventory Parameters, dan Cost–Risk Scenarios.

**Key Questions (wajib dijawab di bagian Solution atau Business Impact)**:
- **KQ1** (hal. 5): *How can the Company improve demand predictability for spare parts with irregular and uncertain consumption patterns?* Yang perlu dipertimbangkan: histori konsumsi, failure history, planned/PM maintenance, shutdown/TA, installed population, kondisi operasi, konsumsi abnormal, serta lead time dan variabilitas supply.
- **KQ2** (hal. 6): *How can the Company dynamically optimize spare part inventory while balancing inventory cost, availability, and operational risk?* Yang perlu dipertimbangkan: risiko stockout part kritis, overstock, kapan reorder, qty reorder dan Min–Max dinamis, slow/dead stock, holding cost, biaya dan lead time procurement, criticality, downtime/production loss, trade-off cost vs risk, serta **scenario simulation** naik/turun stok.

**Deliverable** (hal. 8–9), deadline **Kamis 5 Nov 2026, 06.00 WIB**:
1. **Prototype MVP**:
   - Bukan static HTML, dan di-deploy di **Vercel**.
   - Database **SQLite**.
   - Source code + DB dalam bentuk .zip.
   - Screenshot timestamp dari versi terakhir yang ter-deploy di Vercel.
2. **Deck (bahasa Inggris)**:
   1. Cover (nama tim + anggota)
   2. Background & Problem
   3. Solution (fitur unik + key tech)
   4. Business Impact (success metrics + benefit)
   5. Roadmap & Risk Management (timeline, output, stakeholder, risiko dan mitigasi)
   6. Team Profile & Key Technologies (tabel peran, AI models & tools)

   Appendix opsional. Penomoran slide di brief loncat dari 5 ke 7.

**Data tambahan** boleh dipakai, asal ada justifikasi bisnisnya. Arsitektur data yang rapi lebih dihargai daripada sekadar menambah sumber data.

### Peta temuan → Key Questions

| KQ | Poin dari brief | Temuan pendukung |
|---|---|---|
| KQ1 | Pola irregular / abnormal | F4: 63% material hanya 1 bulan ada issue, lonjakan Nov–Jan |
| KQ1 | PM, shutdown, TA | F7: 5.415 PM due 12 bln, 179 event berisiko lead time |
| KQ1 | Failure history | F8: 17,6% notif ada issue part, link order lemah (20,5%) |
| KQ1 | Failure frequency per equipment | F10: 10 FL menyumbang 9,9% notif, furnace BF-1xx 553 notif |
| KQ1 | Lead time & supply variability | F6: P90 155 hari, CV 0,38, impor ~210 hari, single-source. F11: on-time per supplier 22–58% |
| KQ1 | Installed equipment population | F9: 2.134 FL A/B tanpa BoM dan tanpa PM. F11: 635 material terpakai di ≥5 FL (pooling) |
| KQ2 | Stockout part kritis | F2: 115 material stok nol di FL A/B padahal dikonsumsi |
| KQ2 | Overstock / slow / dead | F1: 37,7% di atas Max, 68% tidak bergerak, Rp318,8 M non-moving |
| KQ2 | Min–Max dinamis | F3: Min/LTD median 2,43; 20% under-protected, 42% over-protected |
| KQ2 | Biaya procurement / PR | F5: 36,0% spend ke material yang stoknya sudah di atas Max |
| KQ2 | Downtime / production loss | Tidak ada di data. Butuh asumsi (biaya downtime per kelas criticality), dicatat di assumption register |

## 1. Peta data

| File | Grain | Baris | Kunci | Catatan |
|---|---|---|---|---|
| FuncLoc list | 1 FuncLoc | 14.484 | Functional Location | Criticality S/A/B/C (33 null = level SITE). Prefix PX 90%, PY 10% |
| BoM | material × FuncLoc | 20.653 | FL + Material No | 7.481 material unik. Stock/Min/Max **level material** (konsisten antar-FL). 230 baris duplikat |
| Movement Material | 1 transaksi issue | 17.518 | Material, Order | Hanya tipe *Issue* (tidak ada receipt). 6 Mei 2025 – 30 Sep 2026 (16,8 bulan) |
| Notif History | 1 notifikasi | 5.795 | Notification, Order, FL | N1 3.871, N3 1.788, N2 (Emergency) 135 |
| PR PO | 1 PR item ↔ 1 PO item | 11.609 | PR-Material | 1.250 material, 124 supplier, 5 mata uang (99% IDR). **Tidak ada tanggal GR aktual**, hanya PO-Delivery Date |
| Mitem & Mplan | 1 maintenance item | 10.153 | Maint. Item, FL | 51 jenis task, 28 variasi penulisan cycle (`YEARLY`/`Yearly`/`1 YEARLY`). **Tidak memuat kebutuhan part** |

Integritas join: semua FL di BoM/Notif/Mplan ada di master. Semua material di Movement dan PR/PO ada di BoM.

Coverage antartabel lemah:
- Hanya **25,8%** material BoM pernah di-issue, dan hanya **16,7%** pernah dibeli.
- Hanya **20,5%** order di Movement yang bisa ditelusuri ke notifikasi. Sisanya kemungkinan order PM/project yang tidak ada di Notif.
- Hanya **56,3%** FuncLoc yang punya PM plan juga punya BoM.

## 2. Temuan utama (dengan *so what*)

### F1. Stok tidak seimbang: kelebihan dan kekurangan terjadi bersamaan
Dari 3.656 stock item:
- **37,7%** stoknya di atas Max.
- **13,8%** di bawah Min, dan **12,9%** stoknya nol.
- **68,2%** tidak pernah di-issue sama sekali selama 16,8 bulan.

Pada 764 stock item yang punya harga PO (IDR), nilai stoknya Rp484,2 M. Dari jumlah itu, **Rp413,8 M** ada di atas Max dan **Rp318,8 M** ada di item yang tidak bergerak. Nilai ini sangat terkonsentrasi: 10% item teratas memegang 93,6% nilai. *(Dikoreksi 4 Nov: `PO-Item Amount` adalah harga satuan, lihat bagian 3.)* Contohnya bearing thrust pad: stok 862 SET padahal Max-nya 30 dan konsumsinya nol.

→ *So what:* masalahnya bukan "stok kurang" atau "stok lebih". **Parameter stok tidak dikalibrasi.** Modal terkunci di part yang tidak dipakai, sementara part yang dipakai justru habis.

### F2. Criticality tidak dipakai untuk menentukan kebijakan stok
- Rasio below-Min hampir sama di semua kelas criticality: S 13,0%, A 13,6%, B 13,8%, C 15,9%.
- Ada **155** material yang sedang dikonsumsi tapi stoknya di bawah Min. **117** di antaranya terpasang di FL kritis A/B.
- Ada **154** material yang stoknya nol padahal dikonsumsi. **115** di antaranya di FL A/B.
- Keterlambatan penyelesaian notifikasi juga flat terhadap criticality: 44–47% di semua kelas.

→ *So what:* equipment kritis (A/B; urutan criticality A > B > C > S sesuai panitia) tidak mendapat proteksi stok atau prioritas eksekusi yang lebih baik. Ini **hook** yang kuat untuk *criticality-driven stocking*.

### F3. Min/Max tidak nyambung dengan demand × lead time
Pembandingan dilakukan pada 672 material yang punya demand dan lead time. Rasio Min terhadap *lead-time demand* (LTD):

| Kuantil | P10 | P25 | P50 | P75 | P90 |
|---|---|---|---|---|---|
| Min / LTD | 0,62 | 1,23 | 2,43 | 5,15 | 9,64 |

- **20,2%** material punya Min < LTD. Artinya stok akan habis sebelum barang pengganti datang.
- **41,8%** material punya Min > 3× LTD, alias over-protected.
- Median months-of-cover untuk item yang bergerak adalah 11,2 bulan, dan P90-nya 67,8 bulan.

→ *So what:* Min/Max kelihatannya ditetapkan statis (feeling atau rekomendasi vendor). Re-kalkulasi Min/Max berbasis data bisa sekaligus menurunkan stockout dan inventory.

### F4. Demand spare part hampir seluruhnya intermittent atau lumpy
Klasifikasi Syntetos-Boylan dilakukan pada 1.930 material yang pernah di-issue:

| Kelas | Jumlah material |
|---|---|
| Hanya 1 bulan ada issue | 1.220 |
| Intermittent | 414 |
| Lumpy | 153 |
| Erratic | 112 |
| Smooth | 31 |

Median material hanya punya issue di 1 dari 17 bulan. Issue juga melonjak di **Nov 2025 – Jan 2026**: 1.860, 2.580, dan 2.184 baris per bulan, sementara baseline-nya sekitar 600–900. Ini kemungkinan turnaround/shutdown. PR bulanan justru flat di kisaran 650–750, jadi pembelian tidak mengikuti lonjakan tersebut.

→ *So what:* forecasting time-series biasa (ARIMA/ML) tidak cocok. Pendekatan yang tepat:
- **Croston/SBA atau bootstrap** untuk material intermittent.
- **Demand berbasis event** (PM plan dan turnaround) untuk lonjakan.
- **Insurance spare berbasis criticality** untuk part yang hampir tidak pernah dipakai.

### F5. Pembelian tidak mengikuti pemakaian
- **36,0%** spend PO (IDR, total Rp1.634,2 M = harga satuan × qty, setelah 5.420 baris PR PO duplikat dibuang) dipakai untuk material yang **sekarang stoknya sudah di atas Max**.
- Hanya 2,7% spend untuk material yang tidak pernah di-issue. *(Angka lama 34,1% salah karena `PO-Item Amount` dijumlah sebagai nilai baris.)*
- **51,1%** material yang dibeli punya kuantitas PR lebih dari 2× kuantitas yang di-issue.
- 25,7% baris PR adalah material ber-tipe *Non Stock*, padahal **44%** material Non Stock ternyata memegang stok.

→ *So what:* tidak ada pengecekan "apakah kita memang butuh ini?" sebelum PR dibuat. Ini quick win untuk **PR guardrail**: cek stok, Max, demand, dan open PO sebelum approve.

### F6. Lead time panjang, tidak pasti, dan semuanya single-source
- Median lead time PR→PO-delivery 42 hari, P90-nya 155 hari.
- Lead time impor jauh lebih lama: EUR 213 hari dan USD 210 hari, dibanding IDR 42 hari.
- Lead time per kategori: blade 257 hari, impeller 222, seal dan trim set sekitar 160, bearing 60.
- **60,6%** PO dijadwalkan datang setelah tanggal yang diminta PR, dan 14,3% lebih dari 30 hari terlambat.
- Variasi lead time dalam satu material cukup besar (median CV 0,38).
- **100%** material hanya punya satu supplier. 10 supplier teratas memegang 62% spend.
- Harga satuan material yang sama stabil antar-PO (median max/min 1,04).

→ *So what:* safety stock harus memperhitungkan **variabilitas lead time**, bukan hanya rata-ratanya. Material impor dan single-source yang kritis butuh strategi khusus.

### F7. PM plan adalah sinyal demand yang tidak terhubung ke spare part
- Ada **5.415** PM item yang jatuh tempo dalam 12 bulan ke depan (as-of 4 Nov 2026). Puncaknya Des 2026 dengan 816 item.
- Ada **628** event PM intrusive (overhaul/cleaning/recert/oil change) dalam 6 bulan ke depan. Event ini mencakup 3.800 baris BoM, dan 1.345 baris di antaranya stoknya lebih kecil dari Installed Qty.
- Hasilnya, **404 event** punya part yang kurang, dan pada **179 event** lead time part-nya lebih panjang daripada sisa hari menuju jadwal PM. Kalau baru dipesan hari ini, part tidak akan sampai tepat waktu.
- Catatan: angka ini adalah **batas atas**. BoM berisi semua part yang terpasang di FL, bukan part yang benar-benar dibutuhkan per task. Diagram data sendiri menyatakan Mplan tidak memuat kebutuhan part.

→ *So what:* celah inti datanya adalah **tidak adanya mapping task PM → kit part**. Ini peluang AI yang bisa didemokan: inferensi kit dari (a) histori issue per order dan FL, (b) tipe task, dan (c) BoM. Hasilnya dipakai untuk *kitting* dan PR otomatis H-lead-time sebelum PM.

### F8. Eksekusi maintenance: backlog besar, tapi part bukan bottleneck utama di data ini
- Ada 1.305 notifikasi berstatus In Progress, dengan median umur 107 hari. **63,7%** sudah melewati Required End.
- Durasi notifikasi yang memakai part dan yang tidak memakai part sama saja (median 41 hari). Median jarak dari notifikasi ke issue part pertama 6 hari, dan 1 hari untuk Emergency.

→ *So what:* jangan klaim "part shortage menyebabkan delay" sebagai fakta dari data ini. Data tidak mendukungnya. Framing yang jujur: **risiko** ke depan (F2, F7) dan **modal terkunci** (F1, F5).

### F9. Banyak equipment kritis yang "buta" spare part
Dari 5.249 FL dengan criticality A/B (urutan A > B > C > S sesuai panitia):
- **3.070** tidak punya BoM sama sekali.
- **2.930** tidak punya PM plan.
- **2.134** tidak punya keduanya.

→ *So what:* untuk FL ini, sistem tidak tahu part apa yang harus disiapkan kalau terjadi kerusakan. Optimasi Min/Max (opsi A) hanya mencakup FL yang sudah punya BoM. Perlu fitur **BoM gap / data completeness** untuk FL kritis, minimal sebagai daftar prioritas untuk dilengkapi.

### F10. Failure terkonsentrasi di furnace
- 10 FL teratas menyumbang **9,9%** dari seluruh notifikasi. Hampir semuanya furnace **PX_BF-1xx**, dengan BF-105 paling tinggi (114 notif).
- Total ada **553** notif furnace BF-1xx (9,5% dari semua notif), 20 di antaranya Emergency.
- Part yang di-issue ke order furnace didominasi firebrick, grease, dan gate valve. Ini sejalan dengan tingginya konsumsi castable refractory (F4) dan besarnya spend ke supplier refractory. Rajawali Refraktori adalah supplier refractory terbesar. *(Nilai rupiah lama dihitung dari jumlah `PO-Item Amount`, perlu dihitung ulang sebagai harga × qty.)*

→ *So what:* furnace adalah kandidat **pilot**. Failure-nya paling sering, part-nya spesifik (refractory), dan lonjakannya bisa diantisipasi lewat jadwal decoking/TA. Ini contoh yang konkret untuk demo forecasting berbasis event (KQ1).

### F11. Reliabilitas supplier dan peluang pooling
- Dari 59 supplier dengan minimal 50 PO line, porsi PO yang dijadwalkan lewat dari tanggal permintaan PR berkisar **42%–78%** (median 61%). Yang terburuk: Buana Teknik Sentosa 78%, Gemilang Refraktori Pratama 71%, dan Mitra Sarana Internasional 69%.
- Spend sangat terkonsentrasi: 10 supplier teratas memegang 78,0% spend, dan 20% supplier memegang 91,6% (setelah koreksi harga satuan × qty).
- Ada 2.165 material yang terpasang di lebih dari satu FL, maksimum 307 FL. **635** material yang benar-benar dikonsumsi terpasang di ≥5 FL.

→ *So what:*
- Lead time di safety stock sebaiknya dikoreksi per supplier, tidak cukup pakai rata-rata global (melengkapi F6).
- Material yang dipakai di banyak FL cocok dijadikan **stok pooling** dengan satu Min/Max level plant. Demand-nya juga lebih stabil karena digabung dari banyak FL, jadi lebih mudah di-forecast.

## 3. Kualitas data (masuk slide Feasibility dan Data Governance)

- **`PO-Item Amount` adalah harga satuan, bukan nilai baris.** Dalam satu material nilainya hampir konstan (median CV 2,1%) dan tidak berkorelasi dengan `PR-Quantity` (r = 0,03). Nilai baris = harga × qty. Kalau dijumlah langsung, spend terbaca ~18× lebih kecil (Rp89,2 M vs Rp1.634,2 M, setelah dedup).

- 230 baris BoM duplikat (FL + material).
- Cycle PM ditulis dalam 28 format.
- 6,4% notifikasi punya Required Start sebelum tanggal notifikasi, dan 6 PR punya PO-delivery sebelum PR-date.
- Tidak ada goods receipt, sehingga lead time aktual dan on-time delivery aktual tidak bisa dihitung. Yang tersedia hanya jadwal PO.
- Tidak ada histori snapshot stok, jadi stok di masa lalu tidak bisa direkonstruksi.
- Harga hanya tersedia untuk 16,4% material, sehingga valuasi penuh inventory perlu harga standar dari SAP MBEW.
- Hanya 20,5% order yang terhubung ke notifikasi.
- Notifikasi Mei 2025 melonjak ke 1.463, padahal bulan-bulan lain sekitar 130–390. Ini kemungkinan artefak dari load awal (backlog dimuat sekaligus), jadi bulan ini perlu dikeluarkan dari analisis tren.
- Ada 394 notifikasi di FL level SITE, yang criticality-nya null. Untuk analisis per criticality, notif ini perlu di-map ke kelas tertentu atau dikeluarkan.

## 4. Root-cause hypothesis (issue tree singkat)

**Masalah:** modal terkunci tinggi **dan** risiko part tidak tersedia untuk equipment kritis.

1. **Parameter stok statis**: Min/Max tidak dihitung dari demand × lead time × service level (F1, F3).
2. **Criticality tidak masuk ke kebijakan stok maupun prioritas** (F2).
3. **Demand planning reaktif**: PM plan dan turnaround tidak diterjemahkan jadi kebutuhan part (F4, F7).
4. **Tidak ada guardrail saat procurement**: PR dibuat tanpa cek stok dan demand. Ditambah single-source dan lead time yang tidak pasti (F5, F6).
5. **Fondasi data terputus**: tidak ada link task ↔ part, tidak ada GR, master data tidak konsisten, dan banyak FL kritis tanpa BoM (bagian 3, F9).

## 5. Arah solusi kandidat (belum diputuskan)

| Opsi | Inti | Akar masalah yang disentuh | Bisa didemokan? |
|---|---|---|---|
| A. **Criticality-based Min/Max optimizer** | Hitung ulang reorder point dan safety stock (Croston/SBA + variabilitas LT + service level per criticality S/A/B/C). Output: daftar *raise / lower / dispose* | 1, 2 | Ya, langsung dari data |
| B. **PM-to-Parts readiness (AI kitting)** | Inferensi kit part per task PM dari histori issue + BoM. Timeline readiness 6 bulan ke depan, dan alarm "PR harus dibuat sebelum tanggal X" | 3, 5 | Ya. Hook: 179 event berisiko |
| C. **Smart PR guardrail + dead-stock liquidation** | Setiap PR dicek terhadap stok, Max, demand, dan open PO (flag/approve). Daftar dead/excess untuk redeploy atau dijual | 4, 1 | Ya. Hook: 36,0% spend ke material yang sudah di atas Max |
| D. Payung **Spare Part Intelligence cockpit** | A+B+C dalam satu workspace dengan explainability per rekomendasi dan human approval | Semua | Lebih berat dikerjakan dalam 24 jam |

Rekomendasi sementara setelah membaca brief: **D**, karena brief memang meminta keempat modul. Struktur yang diusulkan:

- **KQ1 (forecast):** hybrid demand.
  - Croston/SBA atau bootstrap untuk demand intermittent.
  - Ditambah demand event dari PM, shutdown, dan TA. Ini modul B, sekaligus pembeda kita.
  - Ditambah deteksi konsumsi abnormal.
- **KQ2 (optimisasi):** modul A menghitung ROP, safety stock, dan Min–Max per service level criticality dengan memperhitungkan variabilitas lead time.
- **Inventory health dan aksi:** modul C memberi label reorder / maintain / reduce / monitor.
- **Scenario slider:** service level atau budget dinaikkan dan diturunkan, lalu terlihat dampaknya ke nilai inventory vs expected stockout dan downtime cost.

Prototype harus berupa app dinamis di Vercel dengan SQLite, bukan static HTML.

## 6. Pertanyaan terbuka untuk tim

1. Stack prototype: misalnya Next.js di Vercel dengan SQLite read-only yang dibundel. Tulis ke SQLite di Vercel tidak persisten, jadi skenario dihitung on-the-fly.
2. Asumsi service level per criticality (misalnya S 99%, A 97%, B 95%, C 90%), holding cost (biasanya 20–25%/tahun), dan biaya downtime per kelas. Semuanya perlu disepakati sebelum menghitung impact.
3. Konteks perusahaan: Chandra Asri memakai SAP MM/PM. Perlu diputuskan apakah solusinya diposisikan sebagai layer di atas MRP SAP.
