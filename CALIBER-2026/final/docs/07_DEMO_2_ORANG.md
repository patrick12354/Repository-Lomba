# Demo live Sparekit untuk juri: dibagi 2 orang, total 10 menit

Naskah ucapan dalam bahasa Inggris, web juga dalam bahasa Inggris (toggle **EN**). Instruksi ditulis dalam bahasa Indonesia. Angka sudah dicocokkan dengan web per 4 Nov 2026 (data 30 Sep 2026).

| | Orang 1 | Orang 2 |
|---|---|---|
| Tema | Kesiapan turnaround + satu mesin (Compressors) + **Key Question 1** (prediksi kebutuhan, dijelaskan lewat satu part) | **Key Question 2** (stok dinamis: biaya, ketersediaan, risiko) + eksekusi singkat + penutup |
| Halaman | Plant map → Compressors → Forecast → satu part (Gasket 6IN) → Replay | What if → Stock → To do → Data check (10 detik) → Plant map |
| Waktu | 0:00 – 5:30 | 5:30 – 10:00 |
| Kata diucapkan | ± 542 (± 3,4 menit bicara + ± 1,5 menit klik, scroll, dan jeda = 4:55, sisa ± 35 detik) | ± 487 (± 3 menit bicara + ± 0,9 menit klik = 3:55, sisa ± 35 detik cadangan) |

Cara baca tiap bagian:
- **Buka**: halaman yang harus tampil di layar.
- **Lakukan**: klik, geser, ketik, atau scroll, sesuai urutan.
- **Fokus**: bagian layar yang harus ditunjuk (pakai kursor, berhenti diam di situ 1–2 detik).
- **Ucapkan**: kalimat yang dibacakan. Teks **tebal** adalah angka yang wajib keluar.

---

## Persiapan (5 menit sebelum mulai)

1. Buka web, login **Log in as demo** (masuk sebagai Nadia, Inventory Planner).
2. Pastikan toggle bahasa di kanan atas = **EN**.
3. Buka **To do**, tekan **Reset demo**, lalu konfirmasi. Ini wajib, karena Orang 2 akan menekan Approve.
4. Buka **Plant map**, pastikan **Size = Same as last** dan **Supplier delay = +0 days**.
5. Tutup tutorial/tour kalau muncul. Zoom browser 100%, layar 1920×1080.
6. Terakhir, tetap di **Plant map** dan scroll ke paling atas. Orang 1 mulai dari sini.

---

# ORANG 1: Kesiapan, satu mesin, dan Key Question 1 (0:00 – 5:30)

## 1.1 Apakah kita siap? Plant map (0:00 – 0:40)

**Buka:** Plant map (sudah terbuka dari persiapan).

1. **Fokus:** kalimat judul di atas peta (36% / 96% / 18 parts).
   > "This is Sparekit. Are we ready for the turnaround on 1 June 2027? If we order nothing, only **36%** of critical parts will be ready. With on-time orders, **96%**. And **18** parts are already too late."
2. **Lakukan:** scroll ke kartu **Max too low for a turnaround · 79 parts**.
   > "The root cause: SAP limits were set for normal months. **79** parts used more than their Max in a single turnaround. This one has a Max of **25**, and used **200**."

## 1.2 Satu mesin dari dekat: Compressors (0:40 – 1:20)

**Buka:** klik **Compressors** di menu kiri (tepat di bawah Plant map).

1. **Fokus:** kalimat judul (**97** of the 152 parts) dan lingkaran **36%** di kanan atas.
   > "One machine up close: the compressors. **97** of their **152** parts will be short. Only **36%** are ready."
2. **Lakukan:** klik **Open the machine**, lalu klik titik **18 · Bearings**, lalu titik **20 · Gaskets**. **Fokus:** daftar di kanan. Catatan: Gaskets sudah terpilih saat halaman dibuka (titik 20 berwarna hitam), dan kalau titik yang sedang terpilih diklik lagi, daftarnya malah tertutup. Karena itu klik Bearings dulu.
   > "Open the machine, and each numbered dot is a group of parts on the real machine. Gaskets: **20** of **27** are short. This ring gasket: we have **0** of **100**, order by **21 February**."
3. **Lakukan:** scroll ke enam kartu angka di bawah model.
   > "In numbers: **5** parts already too late, **36** with a Max too low, and **Rp 7.9 billion** to buy."

## 1.3 Key Question 1: Forecast (1:20 – 2:00)

**Buka:** klik **Forecast** di menu kiri.

1. **Fokus:** judul halaman, lalu empat angka berderet (7,481 → 583 → 267 → 230), tunjuk dari kiri ke kanan.
   > "Key Question 1: how do we predict demand for parts that are used irregularly? Read it left to right. Of **7,481** parts, we expect about **846** to be used by the end of March. **583** are more likely than not, and **267** of those will run short. The turnaround adds more: **230** of its **360** parts will be short."
2. **Lakukan:** scroll sedikit ke tabel. **Fokus:** grup **Gasket → Sheet**, lalu klik baris pertama **6IN 300# graphite**.
   > "Below is the answer for every part, grouped by type, and red means act now. Let's open the first one."

## 1.4 Satu part dari dekat: Gasket, sheet 6IN 300# graphite (2:00 – 3:50)

Halaman yang terbuka: `/parts/4100014142`.

1. **Fokus:** kotak atas (We have 0 · We need 59 · Short by 59) dan bar abu-abu + oranye di bawahnya.
   > "Every part gets one clear answer. This graphite gasket is an A part. We have **0**, and we need **59** by the turnaround: **43** for normal use, in grey, and **16** for the turnaround job, in orange."
2. **Fokus:** kotak kuning **Order 59 pieces now**.
   > "So the action is: order **59** now. Delivery can take **65** days, and stock is already below the reorder point, so it cannot wait."
3. **Lakukan:** scroll ke **Why that much?** **Fokus:** grafik pemakaian 17 bulan, lalu kartu **Next 6 months** di kanan.
   > "Why that much? Look at its history: used in **11** of **17** months, never the same amount, with a turnaround spike in November. An average would mislead. So the model answers two questions separately: will it be used? Almost certain. How many? Most likely **32**, bad case **66**. That range comes from **2,000** simulated futures, not one number."
4. **Fokus:** baris lima angka di bawahnya (36 places · 44 notices · 65 days · 11/17 · 59 maintenance items).
   > "It also reads where the part is installed, how often that equipment breaks, and the planned maintenance on it. That is how even the **5,551** parts with no history at all still get a forecast."
5. **Lakukan:** scroll ke **Stock limits** dan **Cost and risk**.
   > "From that, new limits: SAP today says Min **7**, Max **10**. We suggest Min **20**, Max **56**. Keeping it costs about **Rp 2 million** a year. Running out would cost about **Rp 21 million**."
6. **Fokus:** dua grafik **How its limits moved, replay of March to September 2026**.
   > "Would it have worked? Over seven months it was asked for **29** pieces. With today's limits, **19** went unserved. With Sparekit, whose limits move every month, none."

## 1.5 Bukti untuk semua part: Replay (3:50 – 4:45)

**Buka:** klik **Replay** di menu kiri (grup "Can we trust it?").

1. **Lakukan:** klik tombol **Play**, biarkan berjalan Mar sampai Sep 26 (± 5 detik).
   > "Now across all parts. First, accuracy: on months the model never saw, it picks the right part **92** times out of 100, against **84** for a simple baseline. Then we replayed real use from March to September 2026, on every critical part kept on the shelf."
2. **Fokus:** tabel dua baris, setelah Play selesai. Tunjuk baris **Today's Min and Max**, lalu **Sparekit**.
   > "With today's Min and Max, parts were on the shelf **53%** of the time they were asked for. With Sparekit, **98%**. Empty-shelf days fall from **8,905** to **2,239**. For the money we count all **3,656 stocked parts**: average stock falls from **Rp 1,005 billion** to **Rp 310 billion**, because money leaves idle parts and goes to the parts that get used."

## 1.6 Serah terima ke Orang 2 (4:45 – 4:55, sisa ± 35 detik sampai 5:30)

**Lakukan:** berhenti di Replay, geser posisi ke Orang 2.

> "So that is Key Question 1: we know what we will need, and when. Now my partner will show how we act on it."

---

# ORANG 2: Key Question 2, kepercayaan, dan penutup (5:30 – 10:00)

## 2.1 Key Question 2: What if (5:30 – 6:50)

**Buka:** klik **1. What if** di menu kiri.

1. **Fokus:** tiga langkah bernomor di bagian atas halaman (1 Choose the stock plan, 2 See what is short or extra, 3 Approve and act).
   > "Key Question 2: how do we manage stock dynamically, while balancing cost, availability and risk? We answer it in three steps, shown at the top of every page: choose the plan, see the impact, then act."
2. **Fokus:** grafik **What each stock level costs a year** (area biru dan oranye).
   > "Step one, What if. This chart shows two costs pulling against each other. Blue is the cost of holding stock. Orange is the cost of running out. The cheapest point sits in between."
3. **Fokus:** kartu **Average stock, once settled: Rp 458 billion → Rp 186 billion** dan **Shortage days −85%**.
   > "Once settled, the recommended plan holds about **Rp 186 billion** of stock instead of **Rp 458 billion**, and cuts shortage days by **85%**. Less stock and fewer shortages at the same time, because today the money sits in the wrong parts."
4. **Fokus:** kartu **The yearly bill: holding stock plus shortages** (Today Rp 490 billion vs Recommended Rp 104 billion).
   > "Put both costs together, and the yearly bill falls from about **Rp 490 billion** today to about **Rp 104 billion**. And it is dynamic: as my partner showed in the replay, these limits are recalculated every month as new use comes in."
5. **Lakukan:** geser slider **Cost of one day without an A part** sedikit ke kanan, tunggu titik termurah bergeser, lalu kembalikan ke **Rp 5 million**. Saat slider digeser, pilihan rencana otomatis pindah ke **Pick a budget**, jadi setelah slider kembali, klik **Recommended** lagi.
   > "The cost of downtime is not in the data, so we do not invent it. The planner sets the assumption here, and the cheapest point moves. The recommended plan stays cheaper than today at any setting."

## 2.2 Langkah 2: Stock (6:50 – 7:55)

**Buka:** klik **2. Stock** di menu kiri.

1. **Lakukan:** scroll ke kotak **What to deal with first**. **Fokus:** pojok kiri atas **Fix now · 320**, lalu pojok kanan bawah **Free up the cash · 918**.
   > "Step two, Stock. Once the plan is chosen, we see which parts are too low and which are too high. This box sorts parts by how critical they are and how much stock they hold. Top left: **320** critical parts too low. Fix them now. Bottom right: **918** less critical parts with extra stock. That is cash we can free up."
2. **Fokus:** kartu di sebelahnya, **Where the most extra money sits** (Bearing thrust pad Rp 163 billion, Blade rotor Rp 91.2 billion, label Stop buying).
   > "Risk is weighed too. Two critical parts that were never used in 17 months hold about **Rp 254 billion** above Max: this thrust pad and this rotor blade. Sparekit says stop buying them, but a person checks before anything is cut, because a critical spare can still be insurance."
3. **Lakukan:** klik tab **Slow and dead stock**. **Fokus:** tiga judul kolom (389 / 2,313 / 768).
   > "We also look ahead. **389** parts are becoming slow, **2,313** are already dead stock, and **768** parts, worth **Rp 230 billion**, may age on the shelf before they are ever used."

## 2.3 Langkah 3: To do, singkat saja (7:55 – 8:35)

**Buka:** klik **3. To do** di menu kiri.

1. **Fokus:** baris ringkasan di bawah nama Nadia (255 urgent · Rp 131 billion).
   > "Step three: act. Every recommendation becomes a task for the right person: **255** urgent tasks, and **Rp 131 billion** of suggested buying."
2. **Lakukan:** klik **Approve** di kartu **kedua** kolom To decide, **Bearing, journal size SV126 incoloy** (kartu pertama adalah Trim set FG409, lewati).
   > "The planner approves with one click, and the task moves to procurement. If she rejects it, she gives a reason, and that reason is recorded."
3. **Lakukan:** klik tombol **Send to SAP** di kanan atas, tunjuk menu yang muncul, lalu tekan Esc.
   > "And the new Min and Max export in a format that loads straight into SAP."

## 2.4 Semua keputusan berbasis data: Data check (8:35 – 8:50, cukup 10 detik)

**Buka:** klik **Data check** di menu kiri.
**Fokus:** kalimat judul "We checked the data before using it and found **9** problems". Tidak perlu scroll.

> "And every decision you saw rests on the plant's own data. We checked that data first: **9** problems found and handled, before a single number was computed."

## 2.5 Penutup (8:50 – 9:25)

Sisa ± 35 detik sampai 10:00 sengaja dibiarkan kosong sebagai cadangan, karena demo live biasanya lebih lambat dari latihan (loading halaman, model 3D, jeda bicara).

**Buka:** klik **Plant map** supaya layar kembali ke angka 36% → 96%.

> "So Sparekit turns static Min and Max into a decision for every part: what we have, what we need, what to do, and when. Two numbers to remember. Turnaround readiness rises from **36%** to **96%** if orders go out on time. And on real use from March to September, critical stocked parts were on the shelf **98%** of the time, up from **53%**, with **69%** less stock across the whole stocked warehouse. Thank you."

---

## Kalau ada yang macet saat demo

| Kejadian | Yang dilakukan |
|---|---|
| Halaman lama loading | Tetap bicara kalimat pertama bagian itu, angka yang sama ada di naskah. Jangan diam menunggu. |
| Model 3D Compressors lambat muncul | Tetap bacakan langkah 1 sambil menunggu. Kalau tombol Open the machine belum bisa diklik, lewati ke langkah 3 (kartu angka). |
| Peta 3D Plant map tidak muncul | Tunjuk kalimat judul dan kartu "Critical parts ready for the turnaround 36%" di bawahnya. |
| Slider Supplier delay tidak kembali tepat ke +0 | Klik **Same as last** lalu geser slider ke paling kiri. Angka harus kembali 36% / 96% / 18. |
| Baris 6IN 300# graphite tidak ada di tabel Forecast | Ketik `4100014142` di **Find a part** (kiri atas, Ctrl K) lalu buka hasilnya. |
| Tombol Play di Replay tidak jalan | Langsung tunjuk tabel. Angkanya tetap tampil tanpa Play. |
| Kartu SV126 sudah tidak ada di To decide | Artinya Reset demo belum ditekan. Pakai kartu paling atas di kolom To decide, dan sebut angka di kartu itu. |
| Waktu habis | Orang 1: lewati 1.4 langkah 4 (lima angka). Orang 2: lewati 2.2 langkah 3 (slow and dead stock). Penutup jangan dilewati. |

## Video panduan

Setelah naskah ini disetujui, akan dibuat 2 video HyperFrames (Orang 1 ± 5,5 menit, Orang 2 ± 4,5 menit). Isinya rekaman klik nyata di web, VO bahasa Inggris dengan suara berbeda untuk tiap orang, subtitle yang menyala per kata, kartu "lakukan sekarang" (KLIK / TUNJUK / GESER / KETIK), dan timer berjalan supaya tahu harus sudah di mana pada menit ke berapa.
