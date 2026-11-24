# Paket unggah YouTube — SINAPS

File di folder ini:

| File | Untuk |
|---|---|
| `../renders/sinaps-demo_v5.mp4` | video v5 (5:14, 1080p) — versi v4 (pembuka Pak Budi) ada di `youtube_v4.md` dan `../renders/sinaps-demo_v4.mp4` |
| `sinaps-demo.id.srt` | teks film Bahasa Indonesia — YouTube Studio → Subtitel → Tambah bahasa (Indonesia) → Unggah file → "Dengan pengaturan waktu" |
| `thumbnail-1.png` … `thumbnail-5.png` | pilihan thumbnail 1280×720 (sumber: `thumbs-src/`, buat ulang: `node tools/thumbs.mjs`) |

Pilihan thumbnail:
1. **KOAS BINGUNG BACA MRI?!** — Dika cemas dikelilingi slice MRI dan tanda tanya
2. **CHATBOT 74% NGARANG vs SINAPS 0** — layar terbelah merah vs teal, maskot Sina
3. **1,9 JUTA NEURON HILANG TIAP MENIT!** — otak dari titik neuron yang padam
4. **RADIOLOG CUMA 0,8** — satu radiolog dikerumuni mahasiswa, latar kuning
5. **LATIHAN MRI LANGSUNG DINILAI!** — rekaman MVP asli, lesi dilingkari, Dika menunjuk

---

## Judul (pilih satu, maks. 100 karakter)

- Mahasiswa Kedokteran Bingung Baca MRI Stroke? Kami Bikin Tutor AI yang Nggak Ngarang | SINAPS
- Chatbot AI Ngarang 74%, Tutor Ini 0 dari 432 — SINAPS untuk Belajar MRI Stroke
- Belajar Baca MRI Stroke Sendiri, Langsung Dinilai AI | SINAPS · ICC 2026

---

## Deskripsi

```
Minggu depan Dika ujian membaca MRI stroke. Masalahnya, kampusnya tidak punya rumah sakit sendiri, dan data MRI pasien bersifat rahasia, jadi yang ia punya hanya gambar statis dari buku dan slide. Padahal stroke tersumbat dan perdarahan tampak sama dari luar dan obatnya berlawanan, sementara Indonesia hanya punya 0,8 radiolog per 100.000 penduduk, dan radiolog yang langka itulah yang juga mengajar. Dosennya kewalahan, chatbot AI malah ngarang. Lalu, apa jalan keluarnya?

SINAPS (Sistem Interaktif Neuroradiologi Adaptif untuk Pembelajaran Stroke) adalah tutor berbasis web tempat mahasiswa kedokteran berlatih membaca MRI stroke sendiri, dinilai secara objektif, dan dibimbing AI yang tidak mengarang.

🧠 Yang bisa dilakukan di SINAPS
• Membaca MRI asli langsung di browser: gulir slice, atur window/level, bandingkan DWI dan ADC
• Menandai lesi dengan kuas, lalu dinilai otomatis terhadap lesion mask buatan ahli (Dice, recall per lesi, galat volume, HD95)
• Tahu jenis kesalahanmu: hampir benar, terlalu luas, terlalu sempit, lesi kecil terlewat, atau salah lokasi
• Tutor Sokratik yang membimbing dengan pertanyaan dan hanya membaca fakta terstruktur, tanpa menebak dari gambar
• Kasus berikutnya dipilih untuk kompetensi terlemahmu (Bayesian Knowledge Tracing)
• Dasbor dosen: peta penguasaan kelas, kesalahan tersering, dan audit setiap jawaban tutor

📊 Hasil uji pada kode yang sudah di-deploy
• Jenis kesalahan anotasi dikenali dengan akurasi 97,8% (IK 95% 96,0–99,1; 672 anotasi, 36 subjek), dibanding 47,3% bila hanya memakai Dice
• 0 dari 432 jawaban tutor keluar dari fakta (4 skenario uji)
Catatan jujur: akurasi diuji pada anotasi sintetis (batas atas). Efek belajar pada mahasiswa belum diukur dan menjadi tahap pilot berikutnya.

▶ Coba MVP: https://mvp-lemon-ten.vercel.app

⏱ Bab
0:00 Malam itu: Dika, ujian, tanpa data
0:22 Gejala sama, penyebab berbeda
0:46 Waktu = otak, dan radiolog yang langka
1:15 Cerita di kelas: Dika dan dosennya
1:47 Chatbot AI yang terlalu yakin
2:09 Peluang: dataset terbuka SOOP
2:27 Kenalan dengan SINAPS
2:41 Satu siklus latihan
3:00 Arsitektur: enam modul
3:23 Kenapa tutornya tidak mengarang
3:36 Kasus yang dipilih untukmu
3:48 Demo: beranda dan viewer MRI
4:09 Demo: tandai lesi dan skor otomatis
4:25 Demo: tutor Sokratik dan dasbor dosen
4:46 Hasil uji
5:04 Penutup

👥 Tim Rizzz · Sains Data, Universitas Airlangga
ICC 2026 · Campus Data Week

📚 Sumber data dan rujukan
• Dataset SOOP: Absher dkk., Scientific Data 2024 — OpenNeuro ds004889 (CC0)
• Penyebab kematian: Kemenkes 2024, SKI 2023
• 1,9 juta neuron per menit: Saver, Stroke 2006
• Jendela trombolisis 4,5 jam: PNPK Tata Laksana Stroke 2019
• Jumlah radiolog: Yunus 2024; Brady 2025
• Halusinasi chatbot pada citra medis: von der Stück dkk. 2026

⚠ SINAPS adalah alat bantu belajar, bukan alat diagnosis. Semua data pasien pada video berasal dari dataset terbuka dan akun demo.

Animasi dibuat dengan HyperFrames. Voiceover, musik, dan efek suara dihasilkan dengan ElevenLabs.

#SINAPS #MRI #Stroke #PendidikanKedokteran #Neuroradiologi #AI #ICC2026 #SainsData #Unair
```

---

## Tag (kolom Tag di YouTube Studio)

```
SINAPS, MRI stroke, belajar MRI, membaca MRI, neuroradiologi, mahasiswa kedokteran, pendidikan kedokteran, stroke iskemik, DWI ADC, radiologi, tutor AI, AI kedokteran, halusinasi AI, chatbot medis, Bayesian Knowledge Tracing, U-Net, dataset SOOP, ICC 2026, Campus Data Week, Universitas Airlangga, Sains Data
```
