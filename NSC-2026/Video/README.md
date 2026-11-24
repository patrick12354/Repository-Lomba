# Video Berkas 734

Video untuk deck NSC 2026 sesuai `Referensi/KEPUTUSAN_FINAL_VIDEO_BERKAS_734.md`. Font: Rustic Printed Stamp untuk judul/stempel, Poppins untuk teks lain.

| File di `output/` | Slide | Durasi | Audio |
|---|---|---|---|
| `slide01-opening-45s.mp4` | 1 | 45 s | tanpa audio; pacing diperlambat untuk dibawakan presenter; 734 (43,0 s) dan >15 HARI (43,6 s) muncul di akhir video |
| `slide03-bukti-70s.mp4` | 3 | 70 s | tanpa audio; papan investigasi: lonjakan suhu asli 54,1 °C → LOO kuadratik (perkiraan 11,0 °C, residual 43,1 °C) → rasio MAD 5,75 / 6,86 / 1,20 → Hampel selektif |
| `slide04-petunjuk-60s.mp4` | 4 | 60 s | tanpa audio; 7 indeks harian → dua jalur rekonstruksi Tmin (kurva asli dari dataset) → 0,047 °C → titik embun → RH = 100 × e / es(T) |
| `slide08-ensemble-55s.mp4` | 8 | 55 s | tanpa audio; 5 model → 3 pita waktu → NNLS (bobot ≥ 0) per pita → shrinkage → kontrol acak, 0,080 vs 0,007 |
| `slide09-pola-55s.mp4` | 9 | 55 s | tanpa audio; residual berurutan searah → ≈0,93 lag-1 → level vs increment 30 menit / 2 jam (jembatan ke slide 10) |
| `slide10-rekonsiliasi-75s.mp4` | 10 | 75 s | tanpa audio; storyline vektor rekonsiliasi (presenter bicara langsung; versi VO ElevenLabs bisa dirender ulang dari sumber) |
| `slide14-case-closed-35s.mp4` | 14 | 35 s | tanpa audio; meja detektif: laporan 2,82744 (detik 1) + sticky note validasi (5,71 → 4,81, ≈15,8 %, 9/9) → 5 kartu pelajaran diarsipkan ke map CASE #734 slide 1 → map ditutup (flip 3D) + kutipan → kembali ke kebun Pak Anton: celah "? ? ?" terisi 734 prediksi asli, tanaman pulih, cap CASE CLOSED, jempol |

`output/` hanya berisi MP4 final: satu video per slide, semuanya tanpa audio. Versi lain (slide 1 tanpa angka / 20 s, slide 10 dengan VO, slide 10 lama) bisa dirender ulang dari sumber (slide 1 tanpa `--variables` atau `_backup/index.20s.html`, slide 10 lama dari `script/slide10-rekonsiliasi/_v1/index.v1.html`).

## Struktur

```
script/
  shared/make_textures.py        tekstur kertas + arang (prosedural, seed tetap)
  shared/make_cork.py            tekstur papan gabus + grain + kertas grafik slide 10
  slide01-opening/               proyek HyperFrames slide 1
    index.html                   animasi 2D vektor: rumah kaca, Pak Anton (boneka bersendi + IK lengan), sensor, buku catatan, map bukti
  slide10-rekonsiliasi/          proyek HyperFrames slide 10
    index.html                   storyline vektor: rumah kaca Pak Anton → papan gabus investigasi → gulungan grafik 734 titik
    _v1/                         versi lama (index.v1.html + snapshot)
    vo-lines.json                teks VO per kalimat (dari script final)
    tools/vo.mjs                 generate VO per kalimat via ElevenLabs (key di Video/.env)
    tools/assemble-vo.mjs        potong jeda, tempo 1,04x, susun ke assets/vo.wav + vo-timing.json
    tools/sfx.mjs                generate SFX (pin, kertas, stempel, spidol, gulungan, whoosh) ke assets/sfx/
    assets/pred.js               734 prediksi dari submission_nsc26_air_humidity.csv
  shared/board.js                kit papan gabus bersama untuk slide 3, 4, 8, 9 (kertas sobek, pin, benang, stempel, kaca pembesar + tangan Pak Anton, kamera); `lens(R, cx, cy)` bisa diarahkan ke posisi layar tertentu
  shared/assemble.sh             bikin index.html dari skeleton.head/body.html + scene.js
  shared/build-all.sh            sync board.js + assemble keempat proyek papan (jalankan setelah edit shared/)
  shared/make_desk.py            tekstur meja kayu walnut slide 14 (prosedural, seed tetap)
  slide14-case-closed/           mandiri: index.html (rig kamera) + scene.js (adegan + timeline) + garden.js (kebun & Pak Anton, disalin dari slide 1); versi papan lama di _v1/
  slide03-bukti/ slide04-petunjuk/ slide08-ensemble/ slide09-pola/
    scene.js                     seluruh adegan + timeline (angka detik ditulis per beat script, dikomentari)
    index.html                   hasil assemble, jangan diedit langsung
output/                          MP4 final
```

## Edit dan render ulang

```bash
cd script/slide10-rekonsiliasi
npx hyperframes preview --background      # buka Studio untuk melihat/mengedit
npx hyperframes render -w 3 --crf 19 -o ../../output/slide10-vo.mp4      # render dengan VO (jangan simpan di output/)
ffmpeg -y -i ../../output/slide10-vo.mp4 -an -c:v copy ../../output/slide10-rekonsiliasi-75s.mp4 && rm ../../output/slide10-vo.mp4
```

Slide 1 (versi di output, dengan angka): `npx hyperframes render --variables '{"showNumbers":true}' -o ../../output/slide01-opening-45s.mp4`.

Ganti teks VO: edit `vo-lines.json`, jalankan `SPEED=1.12 node tools/vo.mjs` lalu `node tools/assemble-vo.mjs`. Waktu animasi di `index.html` mengikuti `assets/vo-timing.json`; kalau durasi kalimat berubah, geser angka detik di blok timeline terkait.

Slide 3, 4, 8, 9: edit `scene.js` di proyeknya (atau `shared/board.js` lalu `sh shared/build-all.sh`), lalu dari folder proyek:

```bash
npx hyperframes render -w 3 --crf 19 -o ../../output/slide03-bukti-70s.mp4
```

## Yang perlu diketahui

- **Slide 14 (meja detektif → kebun Pak Anton, tanpa audio):** komposisi mandiri, tidak di-assemble dari `shared/`. Edit `script/slide14-case-closed/scene.js` (timeline) atau `garden.js` (rumah kaca, tanaman, Pak Anton; kode gambarnya disalin dari `slide01-opening/index.html`), lalu render dari folder itu: `npx hyperframes render -w 3 --crf 19 -o ../../output/slide14-case-closed-35s.mp4`. Awal tiap beat sama dengan v1 (0 / 5,4 / 9,4 / 12,6 / 14,7 / 17,9 / 24,1 / 27,6 / 30,6 / 32 s). Validasi hanya satu sticky note di laporan; grafik batang lama dihapus. Kartu Fisika memakai kurva Tmin asli (`assets/tmin.js`); kartu Lintasan dan garis yang mengisi celah catatan sensor memakai prediksi submission asli. Tanaman pulih dan jempol Pak Anton adalah ilustrasi penutup, bukan klaim dampak ke tanaman. Versi papan gabus lama: `_v1/`.
- **Slide 3, 4, 8, 9 (papan investigasi, tanpa audio):** dunia yang sama dengan slide 10 (papan gabus, kertas sobek, pin, benang). Pacing: satu beat per kalimat script (`SCRIPT_FINAL_DETECTIVE_NSC_2026.md`). Semua visual untuk kalimat itu muncul di ~1,5 s pertama beat, lalu diam sampai kalimat berikutnya supaya presenter bisa bicara; awal tiap beat dihitung dari jumlah kata kalimatnya dan dipadatkan ke durasi target (70/60/55/55 s; slide 14 sengaja dipersingkat ke 35 s). Tiap beat di `scene.js` diberi komentar kalimatnya. Tidak ada count-up angka.
  - Asli: lonjakan suhu slide 3 (train.csv, 7 Agu 2023 02.00, 54,1 °C; perkiraan LOO 11,0 °C dihitung dari 4 tetangga), nama 7 indeks dan kurva Tmin dua jalur slide 4 (`assets/tmin.js`, median harian train+test), 734 prediksi submission di slide 14. Angka 5,75/6,86/1,20, 0,047, 0,080/0,007, ≈0,93, 2,82744, 5,71/4,81, 15,8 %, 9/9 dari laporan.
  - Ilustrasi (diberi label di layar bila perlu): pola residual slide 9, pita waktu slide 8 (tanpa jam batas, benang model sama tebal karena bobot asli per pita tidak digambar), batas Hampel slide 3.
  - `hyperframes check`: lint/runtime bersih; contrast checker masih menandai teks SVG di atas kertas bertekstur (false positive yang sama seperti slide 10).

- **Slide 10 v2 (storyline):** 0–2 s rumah kaca dari slide 1 (Pak Anton menatap sensor, data terkirim) → whip pan ke papan gabus. Catatan sensor (halaman robek dari slide 1, masih "? ? ?") bercabang lewat benang ke dua kartu: Level dan Increment Prediction. Titik level = pin bundar abu, increment = benang putus-putus (4 × 30 menit di atas, 2 jam menggantung di bawah). Ketidakcocokan diperlihatkan lewat kaca pembesar yang dipegang tangan Pak Anton, stempel BELUM KONSISTEN. Kartu kasus TEMPORAL RECONCILIATION + dua kriteria, lalu pin merah + benang merah bergerak serentak (tether ke posisi awal). Catatan menumpuk di papan (disesuaikan bersama, posisi + dinamika, bukan smoothing, dua sumber). Penutup: gulungan kertas grafik dibuka berisi 734 prediksi asli, titik dulu lalu disambung jadi satu lintasan, dan celah "? ? ?" di catatan sensor terisi garis merah.
- Slide 10 memakai prinsip yang sama: tiap kalimat VO (`assets/vo-timing.json`) memunculkan visualnya di awal kalimat, bukan per kata. Versi sebelum perubahan ini: `_v1/index.v3-before-frontload.html`.
- Teks slide 10 diperbesar untuk proyektor: label/sumbu sekitar 32–40 px di layar, teks inti 40–60 px.
- Pak Anton (kedua video) digambar ulang: hidung bulat jadi bagian dari garis wajah, kumis duduk di bawah hidung di dalam wajah, lengan panjang dengan siku menyambung (tidak ada lagi "bantalan" bulat di siku). Versi lama slide 1 ada di `script/slide01-opening/_backup/`.
- Label "Ilustrasi mekanisme" tetap terlihat: di pojok kertas timeline dan terukir di bingkai kaca pembesar saat close-up.
- SFX bisa dibisukan per klip di Studio (track 6+), atau hapus tag `<audio id="sfx…">` di index.html.

- Titik level, increment, dan hasil WLS di slide 10 adalah **ilustrasi mekanisme** (nilai skematis; WLS benar-benar dihitung, w_level=1, w_increment=2). Kurva 734 titik di akhir adalah **prediksi submission asli**, diberi label di layar.
- Slide 1 durasi 45 s: beat animasi masih ditulis di jam 20 s lama, lalu dipetakan ke 45 s lewat tabel `MAP` di `index.html` (jeda ditambah setelah tiap beat, gerakan maksimal 1,6x lebih lambat). Geser angka kanan di `MAP` untuk mengubah kapan tiap scene muncul. Versi 20 s ada di `_backup/index.20s.html`.
- Slide 1 sekarang animasi 2D vektor yang digambar ulang (bukan zoom gambar slide), jadi close-up tetap tajam. Alur: rumah kaca → daun layu → wajah bingung + gelembung pikiran → sensor → buku catatan dibuka, pensil menelusuri baris, kelembapan bolong (? ? ?) → halaman disobek dan masuk map CASE #734 → frame akhir mirip slide 1.
- Codex image-gen lokal gagal (error sandbox Windows), jadi tidak ada aset gambar generate.
- Embed di PowerPoint: Insert → Video → This Device, set Start "Automatically" (slide 1) / "On Click" sesuai rehearsal, jangan loop.
