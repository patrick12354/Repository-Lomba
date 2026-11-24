# 04 — Model Decisions & Insights (log untuk deck dan Q&A)

> Semua angka di sini berasal dari `pipeline/build_output.txt`, `analysis/*_output.txt`, atau eksperimen yang tercatat di bawah. Data dummy: jual mekanismenya, rupiah selalu disebut "on this dataset".
> Kode: `pipeline/build_db.py` (engine), `pipeline/domain_features.py` (layer domain), `docs/diagrams/architecture.png` (diagram).

---

## A. Temuan data understanding (dasar semua keputusan)

| # | Temuan | Bukti | Keputusan |
|---|---|---|---|
| D1 | `PO-Item Amount` = **harga satuan**, bukan total baris | CV dalam satu material ~2%, korelasi dengan qty 0,03 | Nilai = harga × qty. Jangan dibagi qty. Klaim lama "34% spend ke material tak terpakai" salah; angka yang benar 2,7% |
| D2 | Order **2030 = turnaround** (31 order Nov-25, 22 order Des-25), 2090 = kampanye | Lonjakan order per bulan | Demand dipisah jadi *event* (2030/2090) dan *rutin*. Model ML hanya belajar demand rutin. TA ditangani dengan replay kit (E1) |
| D3 | Harga hanya ada untuk 16,4% material, lead time untuk 16,7% | Coverage PR/PO | Fallback harga: material → kategori × unit → kategori. Fallback lead time: material → kategori → global. Sumbernya ditandai (`price_source`, `lt_source`) |
| D4 | Stok di BoM adalah snapshot **setelah** periode tes | Waktu snapshot | `stock` **tidak boleh** jadi fitur (leakage) |
| D5 | Level demand rutin 2025 jauh lebih tinggi dari 2026 | Rata-rata ~760 rb unit/180 hari (Sep–Feb) vs 283 rb (Mar–Agu) | Training diubah ke rolling dan ditumpuk (lihat C) |
| D6 | Siklus PM ditulis dalam **28 format teks** ("5 YEARLY", "Yearly", "12 WEEK", "4 MONTH") | `Cycle Descriptions` | Di-parse 100% menjadi kalender PM: PM yang jatuh tempo 90 hari ke depan, termasuk major overhaul (siklus ≥ 2 tahun) |
| D7 | Tag FL SAP bisa dipecah menjadi kelas equipment | PP pompa, HE exchanger, BF furnace, xCV control valve, KC/KT kompresor/turbin, tag berawalan angka = jalur pipa, suffix -M = motor | Fitur `eq_class` dan laju notifikasi per kelas equipment |
| D8 | Notifikasi punya `Required Start` di masa depan, dan part diambil median 7 hari setelah notifikasi | Join notif → order → movement | Fitur backlog: notif terbuka dan notif terjadwal 90 hari ke depan |
| D9 | **Notif tidak memicu pengambilan part yang terpasang di FL yang sama** | P(part di FL itu diambil ≤ 30 hari setelah notif) = **31,8%** vs 31,1% di bulan acak | Di dataset ini relasi FL ke part bersifat **cross-sectional** (equipment yang sibuk punya part yang sibuk), bukan sebab-akibat dalam waktu. Inilah kenapa fitur domain berbasis waktu tidak menambah lift (lihat E) |
| D11 | Mplan `ABC Indicator` ≠ `Priority`. ABC = criticality equipment (100% identik dengan criticality FL). Priority (2/3) = urgensi eksekusi task PM | Priority 2 dipakai 85% item. Di ABC S, 61% item ber-priority 3 (A 6%, B 21%, C 3%). Item S didominasi instrumen dengan task *SIL Sensor Test*, *Calibration*, *Partial Stroke Test*. 623 FL punya task dengan priority campuran | Criticality untuk stok diambil dari ABC/FL, bukan Priority. Priority adalah atribut task, bukan equipment, jadi tidak dipakai. S yang berisi task SIL dengan priority lebih rendah konsisten dengan jawaban panitia bahwa S bukan tier tertinggi |
| D10 | Kualitas data: 230 baris BoM duplikat, 6 PR dengan lead time negatif, 6,4% notif dengan Required Start sebelum tanggal notif, ledger stok 57,3% tidak seimbang | `dq_issues` | Trust score 0–1 per part. Part dengan skor < 0,5 diberi aksi MONITOR |

## B. Arsitektur yang dipilih (dan alasannya)

1. **Driver-based, bukan time series per part.** 74% part tidak punya histori konsumsi, jadi Croston/SBA tidak bisa apa-apa untuk mereka. Demand dimodelkan dari installed base, beban maintenance di FL tempat part terpasang, histori, dan pengadaan.
2. **Two-part model.** LightGBM classifier menjawab "dipakai atau tidak", LightGBM **Tweedie** menjawab "berapa banyak". Tweedie dipilih karena datanya banyak nol dan ekornya panjang.
3. **Prediksi berupa distribusi, bukan satu angka.** Simulasi Monte Carlo compound Poisson menghasilkan q50/q90/q95 dan demand selama lead time (dengan lead time acak berdistribusi gamma). Hasil ini yang dipakai untuk SS/ROP.
4. **Optimizer cost–risk per criticality.** Service level A/B/C/S = 99/97/95/90% (urutan criticality A > B > C > S, lihat I). Untuk part dengan p_move < 0,3, ROP diambil dari kuantil Monte Carlo karena rumus normal tidak cocok untuk demand jarang. Max = ROP + EOQ. Part kritis A minimal punya 1 unit insurance spare.
5. **Frontier.** Per part dibuat convex hull dari kombinasi biaya dan risiko, lalu dialokasikan greedy mulai dari pengurangan risiko per rupiah terbesar.
6. **Lapisan shutdown terpisah.** Replay kit TA terakhir, tidak dicampur ke Min–Max harian. Ini inti pesan "Min–Max was built for normal days".
7. **Explainability.** TreeSHAP top-3 driver per part, ditambah konteks domain (PM jatuh tempo, notif terbuka, PR terbuka, kelas equipment), dirangkai jadi kalimat `reason`.
8. **Tidak memakai deep learning.** Datanya tabular, cuma 17 bulan, dan sebagian besar part tidak punya histori. Untuk kondisi ini gradient boosting plus model probabilistik adalah pilihan yang tepat. LSTM/Transformer butuh deret panjang.

## C. Evolusi model forecast (rekam jejak eksperimen)

| Versi | Setup | Hasil validasi | Keputusan |
|---|---|---|---|
| v0 | 1 jendela latih 180 hari (fitur < Sep-25), tes Mar–Agu-26 | AUC 0,893, cold 0,839, **bias +201%**, MAE 81 | Bias berasal dari pergeseran level musiman (D5) |
| v0-cal | + kalibrasi skala per demand class | Bias 0 **in-sample**, MAE 25 | **Ditolak.** Skala yang didapat cuma mengukur musim, tidak bisa dipakai di model produksi |
| v1 | 14 jendela 90 hari ditumpuk + flag musim TA | AUC 0,899, bias +212% | Flag TA tidak berpengaruh (hasil identik dengan tanpa flag) |
| v1-tw | + Tweedie | bias +188%, MAE 77 | Lebih baik, dipertahankan |
| v2 | **Validasi rolling-origin** di 4 origin (Apr–Jul-26), horizon 90 hari | AUC 0,916, cold 0,846 | Cara validasi yang jujur: setiap origin dilatih ulang dengan data masa lalu saja |
| v2-lvl | × koreksi level dari aktual 90 hari terakhir | \|bias\| memburuk dari 0,67 ke 1,34 | **Ditolak** |
| v2-rec | + fitur momentum 90 hari terakhir + bobot recency (half-life 3 bulan) | cold 0,850, \|bias\| 0,588 | Dipertahankan |
| **v3 (produksi)** | + blend 50/50 dengan run-rate 90 hari terakhir | AUC 0,916, cold 0,850 (dengan urutan criticality lama) | **Final** |
| v3 + criticality A>B>C>S | Urutan criticality dikoreksi sesuai jawaban panitia | AUC 0,915, cold 0,845 | Digantikan |
| **v3 + dedup PR PO (produksi)** | Setelah dedup PR PO dan TA 2027-06-01 | **AUC 0,916, cold 0,848, MAE 22,2 (naive 22,5), bias Jun/Jul −22%/−7%, q95 menutup 97,7% part** | **Angka utama** |
| v3 strict | Tanpa `mn`, `mx`, `mrp` (snapshot BoM yang dibaca setelah periode tes; temuan Orang 3) | AUC 0,892, cold 0,773, MAE 22,1, \|bias\| 52% | **Disclaimer berdampingan.** Model utama tetap memakai Min/Max planner karena di produksi nilainya diketahui saat forecast dibuat. Kalimat deck: "uses current planner Min/Max as input; strict variant: AUC 0,89" |

## D. Metrik final (validasi rolling, demand rutin 90 hari)

| Origin | AUC | AUC cold | AUC naive | Bias | MAE (naive) | q95 menutup movers / semua part |
|---|---|---|---|---|---|---|
| Apr-26 | 0,911 | 0,841 | 0,822 | +132% | 30,4 (34,1) | 75,5% / 98,3% |
| May-26 | 0,912 | 0,844 | 0,828 | +59% | 23,9 (20,7) | 74,4% / 98,1% |
| Jun-26 | 0,916 | 0,847 | 0,836 | −22% | 17,8 (18,1) | 56,0% / 96,8% |
| Jul-26 | 0,925 | 0,860 | 0,855 | −7% | 16,8 (17,0) | 63,5% / 97,5% |
| *Strict (tanpa Min/Max/MRP), mean* | *0,892* | *0,773* | *0,835* | *\|bias\| 52%* | *22,1 (22,5)* | — |

Arti dalam bahasa sehari-hari:
- **AUC 0,92:** dari pasangan acak satu part yang terpakai dan satu yang tidak, model menempatkan part yang terpakai lebih tinggi dalam 92% kasus.
- **Cold 0,85:** sama, khusus part yang belum pernah keluar gudang.
- **Bias −7%:** total prediksi 7% di bawah aktual (origin Jul).
- **MAE 22:** rata-rata meleset 22 unit per part per 90 hari. Ini setara dengan baseline naive.
- **q95 97,7%:** kalau stok diisi sampai q95, 97,7% part tidak kehabisan.

**Disclaimer wajib:**
- Data cuma 17 bulan dengan 1 musim shutdown.
- Origin awal masih membawa bias regime 2025.
- Konfigurasi dipilih di origin yang sama dengan tesnya, jadi metriknya sedikit optimistis.
- Keunggulan model ada di *siapa yang bergerak* dan *cold start*, bukan volume.
- Model utama memakai Min/Max/MRP planner saat ini sebagai input. Tanpa ketiganya (strict): AUC 0,892, cold 0,773. Tampilkan berdampingan.

## E. Fitur domain: hasil ablation (penting untuk Q&A)

Hipotesis: fitur yang hanya bisa didapat dari domain knowledge akan menaikkan akurasi. Tujuh grup diuji dengan validasi rolling yang sama (mean 4 origin). Ablation ini dijalankan sebelum koreksi urutan criticality; kesimpulannya tidak berubah. Ablation ulang di varian strict (tanpa Min/Max/MRP): baseline 0,892 / 0,773, semua fitur domain 0,893 / 0,768. Juga tidak ada lift:

| Konfigurasi | AUC | AUC cold | MAE | \|bias\| |
|---|---|---|---|---|
| baseline (v3) | **0,9164** | **0,8497** | 22,14 | **0,560** |
| + kalender PM (28 format di-parse) | 0,9163 | 0,8501 | 22,47 | 0,554 |
| + backlog notif (terbuka/terjadwal) | 0,9158 | 0,8470 | **21,77** | 0,593 |
| + kelas equipment dari tag FL | 0,9159 | 0,8463 | 22,16 | 0,566 |
| + sibling di equipment yang sama | 0,9161 | 0,8464 | 22,42 | 0,578 |
| + partner kit (co-issue per order) | 0,9161 | 0,8481 | 22,06 | 0,576 |
| + PR terbuka (intent planner) | 0,9152 | 0,8469 | 22,33 | 0,582 |
| + twin pooling | 0,9150 | 0,8470 | 22,11 | 0,564 |
| semua sekaligus | 0,9152 | 0,8441 | 22,32 | 0,592 |

Lift univariat (P(dipakai 90 hari ke depan) kelompok tinggi ÷ kelompok rendah, mean 4 origin):

| Sinyal | Semua part | Part cold start |
|---|---|---|
| PR terbuka | 8,6× | **9,2×** (20,5% vs 2,3%) |
| Partner kit aktif | 9,2× | n/a |
| Major overhaul jatuh tempo 90 hari | 5,8× | 2,9× |
| PM jatuh tempo 90 hari | 4,0× | 1,6× |
| Notif terjadwal 90 hari | 4,9× | 1,5× |
| Installed qty (fitur lama) | 7,4× | 2,4× |

**Kesimpulan:**
- Sinyal domain **nyata secara individual**: lift 2–9×. Tapi informasinya **sudah tertangkap** oleh fitur yang ada (installed base, beban PM/notif, histori PR), sehingga tidak menambah lift di model. Selain itu, D9 menunjukkan dataset dummy ini tidak punya hubungan waktu antara notif dan part.
- **Keputusan:** model tetap ramping (v3). Fitur domain dipakai sebagai **konteks untuk planner** di `forecast.drivers` (`pm_due_90`, `pm_major_due_90`, `fl_open_notif`, `open_pr_lines`, `eq_class`) dan di kalimat `reason`. Contoh: "upcoming work on its FLs: 191 PM due in 90d, 53 open notifications". Ini muncul di 1.093 rekomendasi.
- **Kalimat untuk juri:** "We engineered 12 domain signals (PM calendar from 28 cycle formats, SAP tag → equipment class, backlog, kit co-consumption, open PRs) and **ablation-tested every one**. On this dataset they add no lift beyond installed base and history, so we kept the model lean and use them as planner context. On real plant data, where notifications do trigger part draws, the PM-calendar and backlog signals become leading indicators."

## F. Keputusan kebijakan dan asumsi

| Keputusan | Nilai | Alasan |
|---|---|---|
| as_of | 2026-09-30 | Data terakhir |
| Horizon forecast | 180 hari | Melewati TA berikutnya dan lead time P90 mayoritas part |
| Next TA | 2026-11-01 (asumsi) | 12 bulan setelah TA terakhir. Slider di app |
| Holding rate | 25%/tahun | Kisaran umum (asumsi) |
| Order cost | Rp 500 rb/PR | Asumsi biaya administrasi |
| Downtime cost | Indeks 100/30/5/1 per hari (A/B/C/S) | Tidak ada di data. Bukan rupiah. Slider |
| Downtime days | lt_p50 part | Waktu menunggu part datang |
| Aturan REORDER | Brief + "A/B dengan stok < ROP" | Supaya spare kritis tidak terlewat walaupun peluang pakainya kecil |
| Insurance floor | Max ≥ 1 untuk Stock Item kritis A | Spare kritis tidak boleh disarankan habis sampai nol |
| `base_demand_scale` | 1,0 | Level demand tidak bisa diprediksi dengan 1 musim. Diserahkan ke slider |

## G. Angka Business Impact (on this dataset)

1. **Kesiapan TA untuk A/B** (TA berikutnya 2027-06-01, asumsi perencanaan, 244 hari lagi): 58,7% hari ini → 97,3% kalau setiap PR TA keluar sebelum order-by date-nya (A saja: 59,5% → 97,1%). Dari 239 part yang kurang untuk TA: 25 sudah terlambat (19 A/B), 5 harus dipesan bulan ini, 209 bisa nanti.
2. **Stok yang bisa dilepas (REDUCE + DISPOSE_REVIEW):** Rp 421.6 B untuk part berharga PO (207 part). Termasuk harga estimasi Rp 5,546 B, tapi angka ini hanya disebut sebagai estimasi.
3. **Part A/B berisiko stockout:** 1.575 → 167 setelah REORDER.
4. **AUC:** 0,916 vs naive 0,835. Cold start 0,848. Backtest lama: 0,886 vs SBA 0,787 (cold 0,836 vs 0,613). Strict: 0,892 / 0,773.
5. **PR rush:** 17,8% dari semua PR, dan 92,5% di antaranya terlambat vs 52,9% PR normal. Klaim "88–93% bisa dicegah" **dibuang**, karena tes yang sama pada PR non-rush memberi 92% (temuan Orang 3).
6. **Skenario** (semua titik memakai lot size yang sama, jadi bedanya hanya level reorder): Min sekarang = Rp 501 B, risiko 7,51 jt, fill A 94,2%. Di frontier, modal yang sama memberi risiko 0,08 jt (fill A 99,6%). Kebijakan default (`optimized`) Rp 580 B, risiko 0,52 jt (−93%), fill A 99,1%. Titik lean menyamai risiko hari ini dengan Rp 71 B.

## K. Metrik bisnis: policy backtest (4 Nov, sore)

**Kenapa:** AUC/MAE adalah metrik ML. Juri case ini menilai dengan fill rate part kritis, stockout, dan modal kerja. Karena itu kebijakan diuji langsung dengan **memutar ulang demand aktual Mar–Sep 2026** (`pipeline/policy_backtest.py`, tabel `policy_backtest`).

**Desain yang jujur:**
- Kebijakan PartPulse dihitung point-in-time per 1 Mar 2026 (model dan lead time hanya memakai data sebelumnya).
- Review harian (s, S). Demand yang tidak terpenuhi = hilang (emergency buy).
- Semua kebijakan mulai dari Max-nya masing-masing.
- Lead time diacak dari histori tiap part, dengan undian yang sama untuk semua kebijakan.

| Kebijakan | Fill unit (A/B) | Fill baris A/B | Stockout-days A/B | Nilai stok rata-rata (PO-priced) |
|---|---|---|---|---|
| Min–Max sekarang | 35,9% (35,8%) | 66,9% | 57.055 | Rp 1,005 B (Rp 80 B) |
| PartPulse default | 96,2% (96,5%) | 98,6% | 2.830 (−95%) | Rp 1,401 B (Rp 514 B) |
| **PartPulse lean** (SL 95/90/85/80) | **94,7% (95,0%)** | **97,5%** | **9.406 (−84%)** | **Rp 782 B (−22%)** (Rp 352 B) |
| Strict default / lean | 96,1% / 94,5% | 98,6% / 97,2% | 2.606 / 10.052 | Rp 1,586 B / 766 B |

**Headline deck:** *"Replaying Mar–Sep 2026: with 22% less inventory value, critical-part fill rate rises from 36% to 95% and A/B stockout-days fall 84% (on this dataset)."*

**Catatan untuk Q&A:**
- Nilai stok total memakai harga estimasi kategori untuk 84% part. Modal **pindah dari part mati ke part yang bergerak**: part berharga PO naik dari Rp 80 B ke Rp 352 B.
- Min/Max dianggap konstan selama jendela tes.
- Varian strict (tanpa snapshot) memberi gambaran yang sama.

**Metrik forecast versi bisnis** (validasi rolling):
- q95 menutup 72,5% part A/B yang bergerak (67,4% semua part yang bergerak).
- **WAPE berbobot rupiah 1,86 vs naive 1,46.** Volume pada part mahal adalah titik lemah model. Jangan dijadikan headline; simpan untuk appendix/Q&A. Inilah alasan keputusan stok memakai distribusi plus service level, bukan satu angka forecast.

## J. Revisi setelah notes Orang 2 dan scope final (4 Nov, siang)

| Revisi | Sebelum → sesudah | Dampak |
|---|---|---|
| Dedup PR PO di `load.py` | 11.609 → 6.189 baris | Spend IDR Rp 3,144 B → **Rp 1,634 B**. Spend ke material di atas Max 35,5% → **36,0%**. E2: rush 17,8%, terlambat 92,5% vs 52,9%. E5: ledger tidak seimbang 57,3% → **36,1%**, received/issued 2,19× → 1,30×. "Dibeli > 2× dari yang dikeluarkan" 51,1% → 28,4%. PR lead time negatif 6 → 2. Backtest lama: 0,887 → 0,886, cold 0,841 → 0,836 |
| `next_ta_default` | 2026-11-01 → **2027-06-01** (asumsi perencanaan, bisa diubah) | Lapisan TA dipisah dari horizon forecast 180 hari. Part TA jadi REORDER hanya kalau order-by date ≤ 30 hari lagi. REDUCE tidak memotong stok yang dibutuhkan TA |
| Frontier | Titik `optimized` jatuh di bawah kurva | Dua bug diperbaiki: (1) titik awal hull tidak sama dengan baseline risiko; (2) level kandidat tidak memuat ROP kebijakan dan Min sekarang. Ketiga skenario sekarang memakai lot size yang sama |
| Bug order-by (Orang 3) | Rumus `cover − lt90` mengurangi lead time dua kali, karena ROP sudah memuat demand selama lead time. Akibatnya hampir semua part bertanggal = as_of | Sekarang `slack = cover`. Stok 0 dan ROP 0 tidak diberi tanggal. Stok tepat di ROP diberi tanggal pemakaian berikutnya yang diperkirakan. Stok < ROP jadi REORDER. Hasilnya, hanya REORDER yang bertanggal = as_of |
| Snapshot Min/Max/MRP (Orang 3) | Kekhawatiran leakage | **Tetap dipakai di model utama** (diketahui saat forecast di produksi). Varian strict dihitung otomatis setiap build (`backtest.engine_strict_mean`), lalu ditampilkan berdampingan sebagai disclaimer |
| Klaim BI-5 (Orang 3) | "88–93% rush bisa dicegah" | Dibuang (tidak membedakan rush vs non-rush). Diganti dengan rush terlambat 92,5% vs 52,9% |
| Kalimat E1 (Orang 3) | "164 part kebutuhan TA > Max" | "79 part stok (71 A/B) Max-nya di bawah kebutuhan satu TA, ditambah 85 part kit dengan Max = 0" |
| Tabel baru | — | `ltd_quantiles` (slider service level), `materials.trust_flags` (JSON untuk checklist Data check), `meta.assumption_fields`. `app_tables.py` dipanggil otomatis di akhir `build_db.py` |

## I. Jawaban panitia di Technical Meeting (4 Nov 2026)

| Pertanyaan | Jawaban panitia | Valid? | Dampak ke kita |
|---|---|---|---|
| FuncLoc ada yang kosong dan duplikat? | Sengaja, bagian dari challenge | ✔ Sesuai data: 33 FL tanpa criticality, 230 baris BoM duplikat | Sudah ditangani (dedup, criticality = maksimum dari FL yang terisi). Jual sebagai trust layer |
| Tier tertinggi S atau A? | **A paling tinggi. Urutannya A > B > C > S. S itu "special", tapi bukan yang tertinggi** | ✔ Didukung data: notif per FL A 0,79 vs S 0,45 vs B 0,45 vs C 0,18. Emergency share A 2,7% (tertinggi). Mplan `ABC Indicator` identik dengan criticality FL | **Asumsi kita salah (S tertinggi). Sudah diubah di pipeline, EDA, dan edge tests.** Replay TA tetap 154 part kurang, tapi pembagiannya jadi **A 124, B 13, C 11, S 6** (sebelumnya "134 S/A"). Criticality material: A 3.686, S 1.582, C 1.119, B 1.094 |
| Non-stock perlu dijadikan stock? | Itu kondisi sekarang. Boleh disesuaikan dengan asumsi sendiri | ✔ | Peluang: rekomendasi ubah MRP Non Stock → Stock untuk part di kit TA (82 part) atau yang p_move tinggi dengan lead time panjang |
| `PO-Item Amount` harga satuan atau total? | **Harga per item** | ✔ Sama dengan temuan D1 | Tidak ada perubahan. Klaim "PO amount = unit price" sekarang dikonfirmasi panitia |
| Arti PR type dan purchasing group? | Jenis dokumen ERP biasa, boleh diabaikan | ✔ | Tidak dipakai. Tidak ada perubahan |

## H. Klaim yang dilarang / sudah gugur

- "Rush PR lebih mahal." Rasio harga satuan rush/normal = 1,00.
- "Kekurangan part menyebabkan delay maintenance."
- "Teks notifikasi bisa menebak part." kNN 0,376 vs baseline popularitas 0,497.
- "Notifikasi memicu pengambilan part di FL itu." 31,8% vs 31,1% acak (D9).
- "34% spend ke material tak terpakai." Yang benar 2,7%. Yang berlaku sekarang: 35,5% spend ke material yang stoknya sudah di atas Max.
- "Model akurat memprediksi jumlah unit." Volume setara naive. Yang kuat adalah *siapa yang bergerak*.

## L. Audit konsistensi angka (4 Nov, malam)

Setiap angka di web ditelusuri ke query dan basisnya. Yang diubah:

| Angka lama | Masalah basis | Sekarang |
|---|---|---|
| 435 part kritis kosong (Stock) | Termasuk 320 part Non Stock yang memang dibeli per pekerjaan | **115** Stock Item A/B kosong + **205** di bawah Min = 320, sama dengan kotak "Fix now" dan langkah 2 |
| To order 666 part, Rp 134 B (Stock) | Dari `policy.REORDER`, sedangkan To do memakai daftar tugas gabungan (gap TA + reorder) | **693 part, Rp 131 B untuk 470 yang ber-harga PO**, sama dengan To do |
| "A parts on the shelf 94,2% → 97,9%" (What if) | Cycle service level model, dirata-rata atas semua part A termasuk yang tidak pernah dipakai; bertabrakan dengan replay 36% | Diganti "hari kekurangan per tahun, setara part A" 75.135 → 11.418 (−85%), plus baris replay 36% → 95% |
| Part tanpa histori 85 vs 61 | 85 dari uji bergulir, 61 dari uji hold-out lama (set uji beda) | **84 vs 61** di uji hold-out yang sama; 85 disebut terpisah |
| "Estimasi tinggi cukup untuk ~98% part" | Penyebut termasuk part yang tidak dipakai (otomatis tertutup) | **67%** dari part yang benar-benar dipakai |
| Replay Rp 1.005 B → Rp 782 B | Termasuk harga perkiraan untuk 84% part | Tetap, dengan catatan: part ber-harga PO naik Rp 80 B → Rp 352 B (modal pindah ke part yang dipakai) |
| Supplier "usually 100 days" | Rata-rata termasuk lead time fallback kategori | Rata-rata lead time per material saja: **104 hari** |
| "Rush: normal delivery takes N days" | Itu P90 (kasus lambat), bukan normal | "delivery can take N days" |

Aturan basis rupiah: posisi hari ini = hanya part ber-harga PO (1.229 dari 7.481). Perbandingan kebijakan = semua part dengan harga perkiraan. Dua basis ini tidak dibandingkan satu sama lain.

## M. Improvement dari ide M3C (4 Nov, malam)

| Ide M3C | Implementasi di Sparekit | Bukti / lokasi |
|---|---|---|
| Bandingkan AI dengan alternatif non-AI terbaik | Policy `policy_classic_lean` di `pipeline/policy_backtest.py`: ROP klasik dari 180 hari terakhir, target dan lead time sama; part tanpa pemakaian baru tetap memakai Min/Max SAP | Fill A/B 91,5%, stockout-days 29.853, stok Rp 1.185 B. Sparekit lean: 95,0%, 9.406, Rp 782 B. Tabel replay di Forecast |
| Memori + flywheel | Loop belajar 3 lapis (bulanan, setiap keputusan, setiap TA). Reject meminta alasan (5 kode); catatan bebas diklasifikasi AI (`lib/reason-ai.ts`, fallback kata kunci) | Panel "How Sparekit keeps learning" di Data check, dialog reject di To do, kolom `decisions.reason` di SQLite demo |
| Override rate dipantau | Tingkat persetujuan per jenis saran yang pernah ditolak | Panel learning |
| AI does / does not | Daftar eksplisit | Panel learning |
| Robustness asumsi | Rekomendasi lebih kecil stok dan risikonya dari hari ini, jadi menang di semua nilai slider (56/56 kombinasi holding 10–50% x Rp 0,5–50 jt dicek) | Kalimat di What if |
| Gate per fase | Tabel roadmap F0–F2 | Naskah bagian 9b, untuk slide Roadmap |
| Daftar keputusan + justifikasi | 20 pertanyaan "Choices we made, and why" | `components/choices.tsx` di Data check |

Lain-lain: unit cadangan (suffix huruf berpasangan, mis. PP-128A/C) ditampilkan di halaman part tanpa menurunkan criticality. Lead time P90 > 365 hari diberi tanda "konfirmasi ke procurement".

## N. Pemeriksaan terhadap "Participants should consider" (4 Nov, malam)

Semua 20 poin casebook dicek ke web dan kode. Yang diperbaiki:

| Temuan | Perbaikan |
|---|---|
| Choices menyatakan rencana pemeliharaan dan notifikasi bukan input model, padahal `fl_notif`, `fl_emerg`, `fl_pm` ada di `X_cols` | Teks diganti: jumlahnya masuk model, sinyal waktu menjadi konteks |
| Kondisi produksi dan operasi belum disebut di mana pun | Entri baru di Choices dan usulan data tambahan (jam operasi, throughput dari historian) di naskah 9b |
| Forecast menulis tanggal turnaround, halaman part menulis "now", alasan menulis jumlah lain | Forecast memakai jumlah dan tanggal dari task. Halaman part menjelaskan beda jumlah dan beda tanggal |
| Tanggal aman yang sama dengan hari ini ditulis "passed" | "Order today"; "passed" hanya untuk tanggal yang benar-benar lewat |
| Safety Stock dan Reorder Point tidak tertulis | Label di Show the math, teks Stock limits, dan Word guide (ditambah Stockout risk dan Overstock risk) |
| "Planner agrees with 0% of cut stock" berasal dari 2 keputusan demo | Tingkat persetujuan baru tampil setelah minimal 5 keputusan, dengan jumlah keputusannya |
| Rp 414 B dan Rp 443 B tampil tanpa penjelasan | Rp 443 B diberi label "above our new Max". Entri Choices baru: Rp 254 B (61%) dari Rp 414 B ada pada 2 part A tanpa pemakaian, dan Rp 286 B ada pada part tidak terpakai |

## O. Replay bulanan pada part yang distok (4 Nov, malam)

**Kenapa:** replay lama (bagian K) menghitung part Non Stock sebagai gagal. 225 dari 720 part A/B yang terpakai adalah Non Stock dengan Max 0, jadi fill-nya 0% secara otomatis, dan 48.150 dari 57.055 hari rak kosong berasal dari sini. Ini bertentangan dengan alasan yang membuang angka 435. Angka 95% juga butuh Non Stock ikut distok (sekitar Rp 477 miliar), padahal file SAP hanya mengekspor Stock Item. Selain itu, batas ditahan konstan sejak 1 Maret, jadi kata "dinamis" belum terbukti.

**Yang dibuat:** `pipeline/replay_timeline.py`. Batas Sparekit dan rumus klasik dihitung ulang tiap tanggal 1 memakai data sebelum hari itu saja. Non Stock tetap pada pengaturan SAP dan tidak dihitung. Halaman `/replay` memutarnya bulan demi bulan.

| 495 part A/B Stock Item, Mar–Sep 2026 | Unit | Per permintaan | Hari rak kosong | Rata-rata stok | Stok ber-harga PO |
|---|---|---|---|---|---|
| Min/Max sekarang | 53,0% | 85,4% | 8.905 | Rp 1.005 miliar | Rp 80 miliar |
| Klasik, diperbarui bulanan | 93,3% | 96,4% | 3.490 | Rp 1.066 miliar | Rp 127 miliar |
| Sparekit, sekali set 1 Mar | 97,9% | 98,4% | 2.642 | Rp 305 miliar | Rp 183 miliar |
| **Sparekit, diperbarui bulanan** | **97,7%** | **98,2%** | **2.239** | **Rp 310 miliar** | Rp 184 miliar |
| Sparekit tanpa Min/Max sebagai input | 97,5% | 97,9% | 2.826 | Rp 320 miliar | Rp 182 miliar |
| Mulai dari rak tercatat: sekarang / Sparekit | 60,5% / 92,9% | 87,4% / 96,0% | 9.624 / 5.576 | Rp 6.038 / 6.040 miliar | — |

**Catatan jujur:**
- Pembaruan bulanan tidak menaikkan ketersediaan dibanding sekali set. Manfaatnya: hari rak kosong −15%, dengan stok +2%. Manfaat terbesar datang dari batas yang tepat.
- Part berubah per bulan: Apr 1.524, Mei 740, Jun 1.668, Jul 1.001, Agu 992, Sep 954. Jun dominan turun (109 naik, 861 turun), Jul dominan naik (418 naik, 167 turun).
- **Cakupan (koreksi 5 Nov):** kolom unit, per permintaan dan hari rak kosong dihitung pada 495 part. Kolom rata-rata stok dihitung pada seluruh 3.656 Stock Item, karena `replay_timeline.py` menjumlah `on * price` atas semua part (Non Stock tetap di Max 0). Pada 495 part itu sendiri (dari `replay_parts.data`), rata-rata stok naik Rp 30,8 miliar → Rp 136,1 miliar dan bertahan sekitar Rp 135 miliar tiap bulan. Penyebab terbesar: batas Maret dihitung tepat setelah turnaround dan tiap rencana mulai penuh di Max-nya (contoh grease Max 48.088 kg untuk pemakaian 1.500 kg). Web, naskah, dan deck sudah memakai cakupan yang benar.
- Penghematan stok mengandaikan kelebihan sudah keluar dari rak. Dari rak tercatat, stok bertahan sampai ada retur, pindah, atau penghapusan. Catatan rak dibaca setelah periode ini, jadi hanya panduan kasar.
- Klasik mempertahankan Min/Max SAP untuk part tanpa pemakaian 180 hari terakhir. Itu sebagian alasan stoknya tinggi.
- 10 part menyumbang 54% unit A/B yang terpakai, jadi angka per permintaan ikut ditampilkan.
- Kurva What if masih memakai Min SAP 0 untuk Non Stock pada titik Today. Sudah ditulis di catatan halaman itu. Bukan angka untuk dikutip.

**Klaim yang dikoreksi di web dan naskah:**
- "Six methods" diganti "one model". `demand_class` hanya label. Percabangan nyata: blend run rate kalau ada pemakaian 90 hari terakhir, ukuran pemakaian dari riwayat sendiri kalau minimal 3 kali (selain itu dari kategori), dan ROP normal vs kuantil simulasi di `p_move` 0,3.
- Learning loop ditulis dengan statusnya. `pipeline/` tidak membaca tabel keputusan, jadi aturan per alasan adalah rencana fase F1. Latih ulang bulanan sudah diuji pada bulan-bulan lalu, tapi belum dijadwalkan. Pembaruan kit dilakukan setelah turnaround berikutnya.

**Riwayat batas per part:** `replay_parts` kini menyimpan peluang pakai, pemakaian selama menunggu kiriman, waktu kirim, permintaan gagal, dan pesanan per bulan untuk 495 part. Ditampilkan di Replay (bisa dicari) dan di halaman part. Dari 495 part, Min berubah pada 475 dan Max pada 493. Rata-rata Max dibanding pemakaian setahun: median 1,35x, P90 4,1x. Sebagian kecil part masih terlihat tinggi, jadi siapkan jawaban kalau ditanya.

**Hasil audit akhir yang diperbaiki:**
- Daftar beli Rp 130,9 miliar (693 part) dipecah: 405 part distok Rp 49,8 miliar, 60 part Non Stock untuk turnaround Rp 33,3 miliar, 228 part Non Stock berdasar forecast Rp 47,8 miliar. Yang terakhir diberi catatan dan punya file sendiri di Send to SAP. Jumlah part dan angka total tidak berubah.
- Persetujuan planner di panel learning berasal dari keputusan contoh, dan sekarang ditulis begitu.
- Forecast sekarang menyebut total perkiraan 846 part (jumlah `p_move`), dengan pembanding 807 part terpakai pada pekerjaan normal dalam 6 bulan terakhir. 583 adalah part dengan peluang minimal 50%.
- Kolom WERKS di file SAP diisi 1000, satu-satunya plant di PR PO.

**Tambahan:** `pipeline/maintenance_calendar.py` membuat kalender pemeliharaan sampai 1 Jun 2027: 10.353 pekerjaan, 485 bersiklus 2 tahun atau lebih, 68 di antaranya pada peralatan dengan part menipis. Tanggalnya tidak masuk skor model (bagian E), hanya untuk planner.

