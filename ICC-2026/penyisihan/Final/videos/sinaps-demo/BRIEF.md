---
workflow: general-video
flow: automation
storyboard: yes
message: "SINAPS membuat mahasiswa kedokteran bisa berlatih membaca MRI stroke sendiri, dinilai objektif dan dibimbing tutor yang tidak berhalusinasi"
destination: youtube
aspect: 1920x1080
language: id
audience: juri ICC 2026 (Campus Data Week, Unair) dan penonton YouTube
length: 3-4 min
angle: background -> arsitektur -> demo produk
voice: elevenlabs:eESTQeTcGUli0jYysKtx
---

## Intent

Video demo SINAPS (Sistem Interaktif Neuroradiologi Adaptif untuk Pembelajaran Stroke) untuk
submission / YouTube, 3-4 menit. Tiga babak: latar belakang masalah, penjelasan arsitektur
keseluruhan, dan demo produk. User minta "banyak motion graphics, flex your effect and motion
graphic skills", "go all out as a motion designer and video editor", dan aset dibuat sendiri
pakai SVG dengan karakter yang bergerak.

## Assets

- ../../mvp/src/components/BrandMark.tsx — logo SINAPS (S dari dua ujung neuron + 3 butir neurotransmiter), dipakai untuk logo dan dasar maskot.
- ../../mvp/ — MVP asli; dijalankan lokal dan direkam layarnya untuk babak demo.
- ../../paper/script/content.py — sumber angka latar belakang dan hasil uji (semua klaim di VO harus berasal dari sini / README MVP).

## Customizations

- Karakter: mahasiswa koas (protagonis) + maskot neuron "Sina" dari logo SINAPS yang jadi tutor. Semua SVG buatan sendiri, dianimasikan (kedip, gerak, ekspresi).
- Demo produk: rekaman layar / screenshot MVP asli yang berjalan, dibingkai motion graphics (bukan UI tiruan) — penting karena demo palsu = pelanggaran lomba.
- Voiceover Bahasa Indonesia via ElevenLabs, voice id `eESTQeTcGUli0jYysKtx`, model ElevenLabs v4 ("biar bagus").
- Musik latar + SFX lengkap di-generate ElevenLabs.

## Notes

- Kunci ElevenLabs di `C:\Patrick\Satu Data\.env` (variabel `ELEVENLABS`). Jangan di-commit.
- Angka di VO hanya dari hasil terukur (paper/README); tandai asumsi.
- Bahasa dokumen/komentar Indonesia, istilah teknis boleh Inggris.

## Versi presentasi (2026-10-27)

- Video utama sekarang versi potong: frame 1-13 (sampai sebelum demo), tanpa audio, untuk diputar
  sambil presenter bicara. `node tools/build.mjs --cut` menulis `compositions/cut/` + `index.html`;
  `SCRIPT_PRESENTASI.md` = script presenter per scene; `node tools/cues.mjs` mencetak ulang tabel waktu beat bila ritme berubah.
- Ritme: tiap kalimat VO lama = satu beat. Animasinya dipadatkan ke awal kalimat (mendarat < ~1,5 dtk),
  lalu layar diam selama kalimat itu diucapkan (+0,35 dtk per beat). Saat jeda hanya tokoh yang hidup (kedip, napas).
- Gaya anti-template: tanpa kicker/eyebrow, judul pojok, label huruf kapital berjarak, baris sumber kecil,
  pil berangka, burst/guncangan/kilat/konfeti, stabilo, latar titik bergerak, kurva memantul. Satu tata bahasa
  transisi (push; cut untuk pergantian babak; zoom sekali ke logo). Latar = permukaan kertas diam (`.ground`).
- 2026-10-28: scene 11a "Modul visi: U-Net" disisipkan setelah scene 11 (+20,9 dtk, batas dari user maks +30 dtk; hanya
  overview: apa yang dikerjakan U-Net, kegunaan, satu angka Dice). Nomor frame boleh bersufiks huruf
  (`## Frame 11a:`). Frame tanpa rekaman VO ditandai `- vo: sintetis`; `node tools/naskah.mjs` menulis perkiraan waktu
  bicara presenter ke `assets/audio/vo/<id>.json` dan mengisi duration. Bahan gambar: `tools/ekspor_unet.py`.
- Versi penuh (VO + demo + audio) masih bisa dibangun dengan `node tools/build.mjs` -> `index-full.html`
  (hapus dulu dari root sebelum `hyperframes check`, karena dua root composition = error lint).
