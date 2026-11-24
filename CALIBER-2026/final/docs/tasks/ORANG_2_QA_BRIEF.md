# Orang 2 — QA/QC web Sparekit + apa yang perlu di-improve

> Snapshot 4 Nov 2026, diperbarui setelah pull commit `8d72a90` (criticality A > B > C > S). Web dibangun di `app/` (Next.js 16 + SQLite), membaca `app/data/partpulse.db` dari Orang 1.
> Rancangan awalnya ada di [ORANG_2_DASHBOARD_MAP.md](ORANG_2_DASHBOARD_MAP.md). Bedanya di versi yang dibangun: nama dan layout dirombak (lihat §1).

## 1. Yang sudah jadi

| Menu (URL) | Pertanyaan di halaman | Visual utama |
|---|---|---|
| Shutdown (`/`) | Are we ready for the next turnaround? | Dinding 360 kotak (1 kotak = 1 part TA, warna = status) per criticality, runway deadline per minggu, board 3 lajur (kartu gaya kanban 21st), peta furnace isometrik BF-101..112, bukti "Max < kebutuhan TA" |
| To do (`/todo`) | What should we do? | Tab **Urgent now** (feed gaya task-list 21st, approve/reject) dan **All parts** (5 kartu kata kerja, filter S/A/B/C, twin, search, tabel dengan gauge Min–Max lama vs baru) |
| Part (`/parts/[id]`) | (nama part) | Kalimat rekomendasi, gauge stok vs range lama/baru, timeline pesan→datang→TA, 10 titik peluang dipakai, grafik 17 bulan, ikon "Why", data check, twin, "Show the math" |
| Stock (`/stock`) | Where is money stuck, and where are we exposed? | Bar 100% jumlah part vs uang per kondisi, matriks risiko × uang, top 10 uang di atas Max, umur pemakaian terakhir, guardrail 35,5% |
| Forecast (`/forecast`) | What will we need in the next 6 months? | Grafik part per bulan (rutin vs TA), peluang per criticality, daftar part belum pernah dipakai tapi kemungkinan dibutuhkan |
| What if (`/what-if`) | What if we keep more or less stock? | Preset Recommended / Lean / Pick a budget, slider di sepanjang frontier engine, 3 kartu perbandingan, grafik frontier |
| Data check (`/check`) | Can we trust these numbers? | 100 titik "berapa kali benar dari 100" (92 vs 84; part baru 85 vs 61), 8 jebakan data, level trust, register asumsi |

**Update setelah pull `8d72a90`:**
- Urutan criticality di seluruh app sekarang **A > B > C > S** (A tertinggi, S = special, terendah). Urutan tile, sortir, kelompok "kritis" = A dan B, headline "A and B parts are 59% ready", kuadran Stock, dan scenario fill rate A/B.
- Spend dan guardrail memakai PR PO yang sudah di-dedup: **Rp 1,634 B dan 36,0%** (sebelumnya Rp 3,144.5 B dan 35,5%).
- **Approve/Reject disimpan ke SQLite** lewat `GET/POST/DELETE /api/decisions` (opsi `/tmp` di §3 `04_SCOPE_FINAL.md`, tanpa layanan luar). Data analitik tetap read-only. Di Vercel, keputusan bertahan selama instance hangat; cold start memulai sesi demo baru. UI menulis "saved to SQLite" dan ada tombol Reset.

Perubahan dari rancangan: nama **PartPulse → Sparekit** (ada di satu tempat: `app/lib/brand.ts`). Sidebar ala PlantPulse diganti nav atas berbentuk segmented. Today dan Actions digabung jadi "To do". Kartu bergaris kiri tidak dipakai di mana pun.

## 2. QA/QC yang sudah dijalankan (hasil nyata)

| Cek | Hasil |
|---|---|
| `tsc --noEmit` + `eslint` | Bersih |
| `next build` (production) | Sukses, 23 route. `/parts/[id]` partial prerender, API dinamis |
| Semua halaman di production server | 200. HTML: `/` 359 KB (terbesar), lainnya 54–129 KB |
| 9 endpoint API + manifest + ikon + `sw.js` | 200. `/api/parts/1` → 404 dengan pesan jelas |
| Interaksi | Tombol "Bigger" memanggil `/api/ta-readiness` dan headline berubah. Approve di UI → reload → masih "Approved", baris ada di `/api/decisions`, localStorage kosong. POST dengan decision tidak valid → 400. Data uji sudah dihapus |
| Angka setelah pull | A 182/306 siap (124 kurang) + B 13/26 (13 kurang) = **137 A/B kurang**, sama dengan `00_TEAM_PLAN` |
| Console browser | Tidak ada error |
| HP 375 px | Tidak ada scroll horizontal. Bottom nav (Shutdown, To do, Stock, More), board jadi geser horizontal |
| Detector impeccable | 0 temuan |
| Scan copy AI-tells (ai-paraphrase) | 1 temuan low (tanda kutip tipografis, sengaja). Beberapa kalimat teknis diganti bahasa awam |
| Review desain | Dua ronde screenshot (desktop 1280 + HP 375). Reviewer independen tidak dijalankan; review dilakukan di thread yang sama |

## 3. Yang HARUS dibahas dengan Orang 1 (sebelum deck dikunci)

1. **Frontier dan titik "optimized" tidak konsisten.** Di tabel `frontier`, risiko terendah kurva = 38% dari hari ini. Tapi titik `optimized` = 6%, jadi titiknya jatuh **di bawah** kurva yang katanya "risiko terendah untuk tiap budget". Juri bisa menangkap ini di halaman What if. Kemungkinan grid kuantil frontier (maks 0,999) dan ROP kebijakan dihitung dengan cara berbeda. Minta Orang 1 menyamakan, atau menambahkan titik optimized ke hull.
2. **Jalankan `py pipeline/app_tables.py` setelah `build_db.py`.** Script ini menambah `material_location` (peta furnace) dan `app_facts` (angka 35,5% spend) ke db. Tanpanya peta furnace disembunyikan dan kartu "Before you buy" hilang. App tidak error. Paling aman, panggil script ini di akhir `build_db.py`.
3. **Asumsi TA 1 Nov 2026 (32 hari).** Akibatnya 152 dari 360 part sudah "too late". Ini cerita yang kuat ("order-by date"). Tapi saat demo, geser tanggal ke Mar 2027 supaya juri juga melihat rencana pesan per minggu.
4. **Jumlah "Act now" = 394** (part TA A/B yang terlambat atau harus dipesan minggu ini, plus part A/B kosong yang masih dipakai). Angkanya benar, tapi besar. Sepakati definisinya supaya angka di deck dan app sama.
5. **Nama produk belum seragam.** `04_SCOPE_FINAL.md` menulis "PartPulse — Shutdown-ready spare parts", sementara app memakai **Sparekit** (permintaan Orang 2 supaya tidak mirip PlantPulse). Pilih satu untuk deck; di app cukup ganti `app/lib/brand.ts`.
6. **Risiko berupa indeks, bukan rupiah** (tidak ada downtime cost di data). App sudah menulis "today = 100". Deck harus konsisten.

## 4. Saran improve (urut dampak ke juri)

| # | Ide | Kenapa | Effort |
|---|---|---|---|
| 1 | **"Check a purchase request"**: form input material + qty → keluar vonis (OK / sudah di atas Max / ada twin / tanggal realistis) | Juri minta *proven solution: input masuk, output keluar*. Ini input→output paling jelas dan menjawab guardrail 35,5% | 1–2 jam, data sudah ada |
| 2 | **Kalender order-by** (`visualize-booking-calendar` 21st): petak hari + badge jumlah part yang harus dipesan hari itu | Tanggal jadi visual. Planner langsung lihat minggu yang padat | 1 jam |
| 3 | **Notifikasi PWA** saat part melewati order-by (P2 di brief) | Momen demo di HP | 1 jam |
| 4 | **Slider service level per S/A/B/C** di What if | Brief Orang 2 meminta ini. Butuh Orang 1 menyimpan tabel kuantil LTD per material (sekarang hanya ada `frontier` jadi) | Butuh engine |
| 5 | **Transfer twin** sebagai aksi sendiri ("Move 566 from 4100075099") dengan approve | Mengurangi stockout tanpa membeli. Edge E4 jadi bisa diklik | 1 jam |
| 6 | Kecilkan payload halaman `/` (360 part ikut dikirim) | HTML 359 KB. Masih oke, tapi di sinyal seluler terasa | 30 menit |
| 7 | `pipeline/dev_seed.py` sudah tidak dipakai | Perintah hapus ditahan guard, jadi hapus manual biar tidak membingungkan | 1 menit |

## 5. Saran gaya UI dari library 21st (belum dipakai)

| Kebutuhan | Entry di library | Pakai untuk |
|---|---|---|
| Visual 3D pabrik/furnace | `landing/lunar-gravity-card` (three + r3f: objek 3D + cincin partikel) | Kartu hero 3D "furnace bank" untuk video/deck. Jangan di halaman kerja (berat di HP) |
| Scene 3D yang dibuat desainer | `landing/splite-spline-scene` (Spline + spotlight) | Kalau ada yang sempat memodelkan cracker/furnace di Spline. Paling cepat untuk "wow" |
| 2D ↔ 3D data | `data-viz/contribution-skyline` (sudah jadi inspirasi peta furnace), `data-viz/circularium-ring` | Ring 12 bulan × kategori: kapan part dipakai (menunjukkan lonjakan TA) |
| Kalender deadline | `forms/visualize-booking-calendar`, `dashboard/event-manager-calendar` | Saran #2, plus jadwal PM |
| Checklist persiapan TA | `dashboard/agent-plan-tree` (status per item, dependensi) | "TA prep plan": PR → PO → GR → kitting per furnace |
| Tampilan produk di deck/video | `landing/hero-195-tabs-borderbeam` | Slide Solution: tab berisi screenshot tiap halaman |

Belum ada di library dan layak dicari di 21st.dev:
- **Alur supply chain**: diagram node atau sankey PR → PO → gudang → work order, yang menyorot di mana lead time hilang.
- **Notification stack / toast** untuk peringatan order-by di PWA.

Kalau ketemu prompt-nya, tempel saja; nanti saya pakai dan tanyakan dulu sebelum menyimpannya ke library.

## 6. Yang belum dilakukan

- **Belum deploy ke Vercel** dan belum ada screenshot timestamp. Deploy pertama sebaiknya segera untuk menguji bundling SQLite (`outputFileTracingIncludes` sudah dipasang).
- **Belum commit.** `app/data/partpulse.db` juga berubah karena `app_tables.py` menambah 2 tabel ke db Orang 1.
- Scope final memotong PWA service worker. App masih punya `sw.js` sederhana (network-first, tidak mengganggu). Boleh dibiarkan atau dihapus.
- Server lokal mengunci file db di Windows. Matikan `npm start` sebelum `git pull`, kalau tidak pull akan gagal menulis `partpulse.db`.
- DESIGN.md (dokumentasi design system) belum ditulis.
