# Revisi v4: rencana dan status

Status: **dikerjakan 3 Okt 2026** (render: renders/plantpulse-demo-v4.mp4, 176.8 s). Opsi visual: A (ilustrasi, tanpa stock). Font: semua IBM Plex Sans + Plex Mono.

## 1. Pembukaan baru: dari mesin ke masalah, tanpa jargon

Masalah v3: penonton langsung dikasih "KO-3201 trips, microns vs mm/s, alert limit 60 vs 45". Orang awam tidak
tahu itu mesin apa, kenapa penting, dan apa masalahnya.

Prinsip baru: **tunjukkan dulu mesinnya, baru ceritanya, baru masalahnya.** Bahasa sehari-hari; istilah teknis
cukup muncul kecil di layar, tidak diucapkan.

| # | Scene | ~Durasi | Voiceover (draf) | Visual |
|---|---|---|---|---|
| A1 | Pabriknya | 9 s | "This is a compressor in a petrochemical plant. It is one of hundreds of machines that keep the plant running, and when it stops, production stops with it." | Siluet pabrik (kolom distilasi, flare stack, pipe rack) tergambar garis demi garis gaya blueprint, aliran produk berupa garis putus-putus bergerak di pipa. Kamera menyelam ke satu unit, lalu kompresor 3D asli dari app berputar dengan label "Compressor: pushes gas through the cracker". |
| A2 | Mesinnya rusak | 11 s | "On April twenty-ninth, twenty twenty-six, compressor K O thirty-two oh one started shaking harder and harder, until it shut itself down. Thirty-two hours offline. One point five eight million dollars lost." | Kompresor bergetar (gelombang getar), jarum gauge naik ke zona merah, lampu alarm merah berkedip, aliran di pipa berhenti. Grafik getaran lama tetap ada, mengecil di pojok dengan label awam "vibration = how hard it shakes". Tag KO-3201 TRIP muncul, jam berputar 32 h, counter uang US$1.58M. |
| A3 | Kenapa susah dicari | 13 s | "To find out why, an engineer has to dig through four different files: spreadsheets, sensor logs, and a slide deck. And they don't even agree. One says the alarm limit is sixty, another says forty-five." | Meja kerja: empat file dengan ikon yang langsung dikenali (Excel, PowerPoint, grafik sensor, database) beterbangan dan menumpuk. Kaca pembesar menyisir. Dua catatan tempel "60" dan "45" bertabrakan dengan tanda ≠. Jargon "micron vs mm/s" dibuang. |
| A4 | Selesai palsu | 10 s | "So the machine is repaired, it runs fine again, and the case looks closed. But the fixes that stop it from happening again are still unfinished." | Kunci pas memperbaiki mesin, lampu hijau "RUNNING", aliran pipa jalan lagi, centang besar "Case closed". Centangnya retak, dua kartu tugas naik dengan bahasa awam: "Install oil-quality sensor · overdue" dan "Replace leaking cooler tubes · not started". |
| A5 | Tesis + logo | 9 s | (tetap) "PlantPulse is built on one rule. A repair is not a fix until the evidence says so." | Tetap, dengan perbaikan ring (poin 2). |

Total babak 1 sekitar 52 s (v3: 53 s), jadi babak demo tidak perlu dipotong kecuali tempo suara clone lebih lambat.

Alasan urutan ini: penonton awam dapat tiga hal dalam 20 detik pertama: (1) ini mesin penting, (2) mesin itu
rusak dan mahal, (3) penyebabnya susah dicari dan perbaikan pencegahannya terbengkalai. Baru setelah itu
PlantPulse masuk sebagai jawaban.

Visual tambahan di babak demo (s05–s11) tetap pakai capture app asli, plus ikon kecil per konsep
(kunci pas untuk action, perisai untuk Evidence Guard, gembok untuk log tamper-evident).

## 2. Ring di 0:52 tidak di tengah maskot

Penyebab: dua ring "ping" di `compositions/s04-thesis.html` diposisikan dengan persen kotak 290×290
(`left: 50.5%; top: 41%`), bukan dari titik tengah dial di gambar maskot. Hasilnya ring melenceng ke kiri atas.
Perbaikan: ukur pusat dial dari frame render, jadikan pusat ring di koordinat itu, dan taruh ring di dalam
`#s04-body` supaya ikut squash/settle maskot. Cek juga ring + sparks di lockup s12 dengan cara yang sama.

## 3. Voice: clone suara Raphael di ElevenLabs

- Akun: Starter, instant voice cloning aktif, sisa sekitar 31k karakter. Naskah sekitar 2.6k karakter, jadi cukup
  untuk 2–3 take penuh plus revisi per baris.
- Sampel: `~/Downloads/voice recording raphael.m4a` (37 s). Bersihkan dulu (high-pass, denoise ringan,
  normalisasi) sebelum upload supaya clone tidak ikut membawa noise ruangan.
- Model `eleven_multilingual_v2`, stability sekitar 0.5, similarity 0.85, style 0. Uji 1 baris dulu, dengarkan, baru generate semua.
- Script baru `scripts/make-voice-11labs.mjs` memakai endpoint `with-timestamps` lalu mengubah timing per
  karakter jadi `NN-name.words.json` dengan format yang sama, sehingga `prep-audio.sh`, `build.mjs` dan captions tetap jalan.
- API key dibaca dari `videos/.env`, tidak pernah ditulis ke file lain.

Risiko utama: semua animasi di tiap scene dikunci ke timing kata dari suara lama (Jonah). Supaya tidak
re-timing manual satu per satu, setiap waktu GSAP di tiap scene di-warp secara piecewise-linear dari timestamp
kata lama ke timestamp kata baru. Setelah itu tinggal cek visual per scene.

## 4. Font

Web mode light (default) sudah memakai font yang sama dengan video: Archivo 800 expanded untuk judul,
IBM Plex Sans untuk UI, IBM Plex Mono untuk tag. Mode dark yang baru memakai Google Sans Flex / Google Sans Code.
Perlu konfirmasi mana yang dimaksud (lihat pertanyaan).

## 5. Perlu record ulang web atau tidak?

Sudah dicek dengan git diff + screenshot app lokal dibandingkan capture lama:
- Perubahan setelah capture (commit 6c9ece3, 8ba1c51) hampir semuanya di **dark theme** (Prado + mesh shader).
  Video memakai light theme.
- Yang terlihat di light: tombol "Ask PlantPulse" sekarang ada Pipo (muncul di pojok hampir semua capture), warna
  chart lifecycle di Overview sekarang memakai token series, dan loading screen ada Pipo.
- Palet 3D light tidak berubah → `machine.mp4`, `replay.mp4`, `site.mp4` **tidak perlu direkam ulang**.

Keputusan: **capture ulang semua screenshot** (otomatis lewat script yang sudah ada, sekitar 10 menit) supaya
tombol Pipo dan warna chart konsisten dengan web sekarang. Lalu image-diff dengan capture lama; callout
diposisikan ulang hanya di capture yang layout-nya bergeser (`measure.mjs`). Klip 3D tetap.

## Urutan kerja

1. Clone suara, uji 1 baris, minta approval suara.
2. Kunci naskah babak 1 baru, generate semua VO, lalu prep audio.
3. Recapture app + diff + perbaiki callout.
4. Bangun scene A1–A4 baru (ilustrasi mesin/pabrik + klip 3D), perbaiki ring s04/s12.
5. Time-warp animasi s04–s12 ke suara baru, `build.mjs`, `hyperframes check`.
6. Render draf, review per scene, render final.
