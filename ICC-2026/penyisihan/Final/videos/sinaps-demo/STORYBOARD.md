---
format: 1920x1080
duration: 290s
message: "SINAPS membuat mahasiswa kedokteran bisa berlatih membaca MRI stroke sendiri, dinilai objektif dan dibimbing tutor yang tidak mengarang"
arc: Mahasiswa tanpa RS & data → Kenapa materinya menyangkut nyawa → Waktu & radiolog langka → Cerita kelas → Peluang → Produk → Arsitektur → Demo → Bukti → Penutup
audience: juri ICC 2026 dan penonton YouTube
mode: collaborative
---

# Arah global

- **Konsep:** "Satu sinyal sinaps." Butir neurotransmiter oranye dari logo SINAPS adalah benang merah
  seluruh film — ia menyeberang di setiap transisi (celah sinaps), menjadi kursor cerita, dan akhirnya
  menyala di logo. Semua aset SVG buatan sendiri.
- **Karakter:** *Dika* (mahasiswa kedokteran, jas putih, stetoskop; ekspresi: bingung, kewalahan, yakin) dan
  *Sina* (maskot neuron dari logo: tubuh bulat sage, dendrit seperti rambut, mata besar, membawa butir
  oranye). Rig SVG dengan kepala/mata/lengan terpisah supaya bisa kedip, menoleh, melambai.
- **Palet (dari MVP):** kanvas krem `#f1efe6`, tinta `#10313a`, teal `#195764`, sage `#aad39c`,
  terakota `#f09a6c` (aksen tunggal = neurotransmiter), merah bata `#a2462a` untuk bahaya.
  Adegan MRI pindah ke "ruang baca" gelap `#0b1220` (konvensi radiologi, sama seperti viewer MVP).
- **Tipografi (dari MVP):** Oswald (display, kapital berjarak), Arvo (serif isi), Geist Mono (label data).
- **Audio (v2):** VO ElevenLabs `eleven_v4`, voice Senandika (`eESTQeTcGUli0jYysKtx`); musik latar
  ElevenLabs v2 yang lebih semangat (elektronik 124 bpm, drum bertenaga, build-up ke drop di reveal SINAPS,
  groove di arsitektur & demo, klimaks di hasil), volume 0,45 + voiceover carve 0,8; palet 61 SFX
  (`tools/sfx.mjs` + varian nada `tools/sfx_var.mjs`) — tiap transisi punya bunyi sendiri, urutan reveal
  memakai nada marimba berjenjang, angka mendarat memakai punch/impact. Isyarat SFX bisa berjangkar kata VO
  (`nama@~kata[.n][±dtk]:vol`).
- **Tipografi & motion (v2, untuk layar lebar):** semua teks dibesarkan dan ditebalkan, detail dipangkas
  (biar VO yang menjelaskan). Setiap frame punya latar ambient bergerak + kamera drift; angka penting
  mendarat dengan burst + guncangan; judul muncul per kata; babak Demo & Hasil dibuka kartu judul ("DEMO",
  "HASIL UJI"); rekaman demo diberi punch-in kamera ke bagian yang dibicarakan.
- **Demo:** rekaman layar MVP asli (lokal, data demo), dibingkai jendela peramban SVG + zoom & callout.

## Frame 1: Dika belajar sendiri (0-23s)

- act: Babak 1 — Mahasiswa
- status: animated
- vo_at: 0.6
- src: compositions/frames/01-dika-malam.html
- duration: 21.6s
- transition_in: cut
- blueprint: character-intro + dolly-in dramatis + kartu masalah bergantian
- scene: Malam, kamar kos Dika (mahasiswa kedokteran) di meja belajar dengan lampu dan laptop; kartu hitung mundur "Ujian blok neurologi · 7 hari lagi · membaca MRI stroke"; kamera mendorong pelan ke wajah Dika, hentakan saat "Masalahnya"; kartu "Kampus ✕ rumah sakit sendiri"; folder MRI pasien digembok stempel RAHASIA; buku teks terbuka dengan satu gambar MRI kecil; lampu meredup.
- voiceover: "Ini Dika, mahasiswa kedokteran. Minggu depan, ujian blok neurologi: membaca MRI stroke. Masalahnya, kampusnya tidak punya rumah sakit sendiri. Data MRI pasien tersimpan di rumah sakit, dan sifatnya rahasia. Yang ia punya, hanya beberapa gambar dari buku dan slide kuliah."

## Frame 2: Dua otak, satu gejala (13-33s)

- act: Babak 1 — Pasien
- status: animated
- vo_at: 0.5
- src: compositions/frames/02-dua-otak.html
- duration: 23.9s
- transition_in: push
- blueprint: comparison-split + scan-beam reveal
- scene: Dua otak berdampingan: kiri pembuluh tersumbat (bekuan), kanan pembuluh pecah (perdarahan); di atas keduanya ikon gejala yang sama persis dengan tanda "="; vial obat penghancur bekuan meluncur ke masing-masing: kiri centang hijau "menyelamatkan", kanan silang merah "memperparah"; berkas pemindai menyapu, potongan MRI asli muncul dengan ikon mata "dibaca dengan benar".
- voiceover: "Padahal, materi ini menyangkut nyawa. Stroke bisa terjadi karena pembuluh darah tersumbat, atau pecah. Dari luar, gejalanya sama. Tapi obatnya berlawanan: obat penghancur bekuan bisa menyelamatkan yang tersumbat, dan memperparah yang berdarah. Karena itu, otaknya harus dipindai, dan seseorang harus membacanya dengan benar."

## Frame 3: Waktu dan pembaca yang langka (33-60s)

- act: Babak 1 — Taruhannya
- status: animated
- vo_at: 0.5
- src: compositions/frames/03-data-indonesia.html
- duration: 29.6s
- transition_in: batang warna (bars)
- blueprint: dataviz-countup x3 (rel geser: otak → peta → radiolog)
- scene: Tiga panel bergeser: otak dari titik neuron yang padam + penghitung 1.900.000 per menit + jam pasir "4,5 jam"; peta Indonesia + 18,5% kematian; radiolog 0,8 vs 12,7 per 100.000 (16× lebih sedikit dari rerata Uni Eropa).
- voiceover: "Dan jam terus berjalan. Setiap menit, otak kehilangan satu koma sembilan juta neuron, dan obat itu hanya bisa diberikan dalam empat setengah jam. Di Indonesia, stroke menyumbang delapan belas koma lima persen kematian. Tapi pembaca citranya langka. Radiolog hanya nol koma delapan per seratus ribu penduduk, enam belas kali lebih sedikit dari rerata Uni Eropa. Radiolog yang langka inilah yang juga mengajar di kampus."

## Frame 4: Kelas neuroradiologi (60-70s)

- act: Babak 1 — Cerita di kelas
- status: animated
- vo_at: 0.5
- src: compositions/frames/04-kelas.html
- duration: 8.4s
- transition_in: iris
- blueprint: spatial-pan-stations (kamera mundur dari Dika ke seluruh kelas)
- scene: Dekat ke Dika dan teman-temannya di bangku kuliah, label nama muncul; kamera mundur memperlihatkan seluruh kelas, dosen di depan layar proyektor berjudul "Neuroradiologi · MRI stroke".
- voiceover: "Dika dan teman-temannya masuk kelas neuroradiologi: belajar membaca MRI stroke."

## Frame 5: Dika bingung (70-83s)

- act: Babak 1 — Cerita di kelas
- status: animated
- vo_at: 0.5
- src: compositions/frames/05-dika-bingung.html
- duration: 13s
- transition_in: whip pan
- blueprint: overwhelm-surround
- scene: Dosen menunjuk satu potongan MRI statis di layar; lalu potongan itu pecah jadi tumpukan puluhan slice dan tiga sekuens yang berputar di sekitar kepala Dika; tanda tanya bermunculan, teman-temannya saling pandang.
- voiceover: "Di layar, dosen menunjukkan satu potongan MRI. Padahal di klinik, satu pasien punya puluhan slice dan beberapa sekuens. Dika bingung harus mulai dari mana."

## Frame 6: Dosen kewalahan (83-95s)

- act: Babak 1 — Cerita di kelas
- status: animated
- vo_at: 0.5
- src: compositions/frames/06-dosen.html
- duration: 10.5s
- transition_in: push
- blueprint: overwhelm-surround + rules stat-bars-and-fills
- scene: Satu dosen di tengah, tangan mahasiswa terangkat di mana-mana, tumpukan lembar jawaban di meja terus meninggi, jam berputar cepat, dosen berkeringat dan menggeleng.
- voiceover: "Dosennya juga kewalahan. Satu dosen, satu kelas penuh. Tidak mungkin memeriksa bacaan tiap mahasiswa satu per satu."

## Frame 7: Chatbot yang terlalu yakin (95-117s)

- act: Babak 1 — Cerita di kelas
- status: animated
- vo_at: 0.5
- src: compositions/frames/07-chatbot.html
- duration: 22.3s
- transition_in: glitch
- blueprint: prompt-type-submit-generate + rules chromatic-glitch
- scene: Dika mengetik ke chatbot generik; jawaban mengalir penuh percaya diri lalu glitch merah; stempel "halusinasi 74,4%"; kartu "Yang Dika butuhkan": tempat berlatih sendiri yang menilai bacaannya; diakhiri pertanyaan besar "Lalu, apa jalan keluarnya?".
- voiceover: "Jadi mahasiswa lari ke chatbot AI. Masalahnya, untuk citra medis, chatbot umum sering salah dengan sangat yakin. Satu evaluasi mencatat tingkat halusinasi sampai tujuh puluh empat persen. Dika butuh tempat berlatih yang benar-benar menilai bacaannya. Lalu, apa jalan keluarnya?"

## Frame 8: Kunci jawaban (66.2-83.4s)

- act: Babak 1 — Latar belakang
- status: animated
- vo_at: 0.5
- src: compositions/frames/08-kunci-jawaban.html
- duration: 17.2s
- transition_in: iris
- blueprint: grid-card-assemble → zoom-out-workspace-reveal (dibalik: push-in ke satu ubin)
- scene: Dinding ubin MRI berhitung sampai 1.505 pasien; kamera masuk ke satu ubin; lesion mask oranye melukis dirinya; ikon kunci berputar masuk.
- voiceover: "Tapi ada peluang. Dataset terbuka SOOP berisi MRI dari seribu lima ratus lima pasien stroke, lengkap dengan lesion mask buatan ahli. Untuk setiap kasus, kita tahu persis jaringan mana yang infark. Itu kunci jawaban."

## Frame 9: SINAPS lahir (83.4-98s)

- act: Babak 2 — Produk & arsitektur
- status: animated
- vo_at: 1.4
- src: compositions/frames/09-sinaps-reveal.html
- duration: 14.6s
- transition_in: zoom-in blur
- blueprint: logo-assemble-lockup
- scene: Dua ujung neuron tumbuh dan bertemu membentuk huruf S logo; tiga butir oranye meletup; wordmark SINAPS + kepanjangannya; Sina melompat keluar dari logo dan melambai.
- voiceover: "Dari kunci jawaban itu, kami membangun SINAPS: tutor neuroradiologi tempat mahasiswa berlatih membaca MRI stroke sendiri, dinilai secara objektif, dan dibimbing AI yang tidak mengarang."

## Frame 10: Satu siklus latihan (98-116.6s)

- act: Babak 2 — Produk & arsitektur
- status: animated
- vo_at: 0.5
- src: compositions/frames/10-siklus.html
- duration: 18.6s
- transition_in: crossfade
- blueprint: constellation-hub (ring 5 stasiun) + rules svg-path-draw
- scene: Lingkaran lima stasiun (pilih kasus → baca & tandai → dinilai → tutor menjelaskan → penguasaan diperbarui); Sina berlari mengikuti lingkaran sebagai sinyal, tiap stasiun menyala saat dilewati.
- voiceover: "Kenalan dulu dengan Sina. Di SINAPS, latihan berjalan dalam satu siklus. Sistem memilih kasus untuk kompetensi terlemahmu. Kamu membaca MRI dan menandai lesi. Jawabanmu dinilai otomatis, tutor menjelaskan, lalu penguasaanmu diperbarui."

## Frame 11: Enam modul (116.6-139.8s)

- act: Babak 2 — Produk & arsitektur
- status: animated
- vo_at: 0.5
- src: compositions/frames/11-arsitektur.html
- duration: 23.2s
- transition_in: slide-up
- blueprint: spatial-pan-stations (kamera menyusuri diagram) + rules svg-path-draw
- scene: Diagram arsitektur dibangun: Viewer (Cornerstone3D) → Orkestrator FastAPI → Bank kasus, Modul visi (U-Net 2.5D), Penilaian, Adaptasi (BKT) → Tutor LLM; Dasbor dosen di samping. Paket data berjalan di garis.
- voiceover: "Di balik layar ada enam modul. Viewer berbasis Cornerstone3D berjalan langsung di peramban. Semua permintaan lewat orkestrator FastAPI. Di belakangnya ada bank kasus, modul visi dengan U-Net dua koma lima D, modul penilaian, dan modul adaptasi berbasis Bayesian Knowledge Tracing. Dosen memantau semuanya lewat dasbor."

<!-- Frame 11a: overview modul visi (ditambahkan 2026-10-28, maks +30 dtk; baris spesifikasi dihapus atas permintaan user). Belum punya rekaman VO: "- vo: sintetis"
     berarti tools/naskah.mjs menulis assets/audio/vo/f11a.json dengan perkiraan waktu bicara presenter (bukan audio)
     dan mengisi duration. Angka dari mvp/pipeline/kaggle/train_unet.py dan mvp/pipeline/results/unet25d/metrics.json. -->

## Frame 11a: Modul visi U-Net

- act: Babak 2 — Produk & arsitektur
- status: animated
- vo: sintetis
- vo_at: 0.5
- src: compositions/frames/11a-unet.html
- duration: 19.8s
- transition_in: kartu "Modul visi" di frame 11 membesar menjadi seluruh layar
- scene: Enam slice MRI asli (DWI dan ADC z-1, z, z+1) masuk di kiri → diagram U ringkas (encoder turun, dasar U, decoder naik, skip connection melintang) → prediksi U-Net asli di atas DWI keluar di kanan → kegunaan: pembanding setelah submit, Dice 0,738 pada 36 kasus uji.
- voiceover: "Isinya U-Net 2.5D, masuk enam slice DWI dan ADC, keluar peta lesi per piksel. Encoder mengenali lesinya, decoder mengembalikan ke ukuran asli supaya batasnya presisi. Hasilnya jadi pembanding setelah mahasiswa submit, dengan Dice 0,738 pada data uji."

## Frame 12: Fakta terkunci (139.8-153.2s)

- act: Babak 2 — Produk & arsitektur
- status: animated
- vo_at: 0.5
- src: compositions/frames/12-fakta-terkunci.html
- duration: 13.4s
- transition_in: zoom-in blur
- blueprint: agent-progress-theater + rules card-morph-anchor
- scene: Modul hijau (deterministik) mengeluarkan kartu JSON fakta; tutor LLM oranye hanya bisa membaca kartu itu; gembok menutup di jalur kunci jawaban ke peramban.
- voiceover: "Kuncinya di sini. Tutor LLM ada di ujung rantai. Ia hanya menerima fakta terstruktur dari modul lain, dan kunci jawaban tidak pernah dikirim ke peramban sebelum kamu submit."

## Frame 13: Kasus yang pas (153.2-164.5s)

- act: Babak 2 — Produk & arsitektur
- status: animated
- vo_at: 0.5
- src: compositions/frames/13-bkt.html
- duration: 11.3s
- transition_in: push
- blueprint: dataviz-countup + rules stat-bars-and-fills
- scene: Batang penguasaan K1, K2, K3, K6 naik-turun; panah memilih yang terendah; dial tingkat kesulitan mudah/sedang/sulit berputar ke "sedang".
- voiceover: "Setiap jawaban memperbarui estimasi penguasaanmu per kompetensi. Kasus berikutnya dipilih untuk yang paling lemah, dengan tingkat kesulitan yang pas."

## Frame 14: Beranda (164.5-171.7s)

- act: Babak 3 — Demo produk
- status: animated
- vo_at: 0.5
- src: compositions/frames/14-demo-beranda.html
- duration: 7.2s
- transition_in: batang warna + kartu judul DEMO
- blueprint: device-surface-showcase
- scene: Rekaman asli halaman Beranda di jendela peramban yang melayang; callout "Langkah berikutnya: KC terlemah".
- voiceover: "Sekarang lihat langsung. Begitu masuk, SINAPS sudah menyarankan langkah berikutnya."

## Frame 15: Membaca MRI (171.7-185.5s)

- act: Babak 3 — Demo produk
- status: animated
- vo_at: 0.5
- src: compositions/frames/15-demo-viewer.html
- duration: 13.8s
- transition_in: push
- blueprint: device-surface-showcase + rules coordinate-target-zoom
- scene: Rekaman asli viewer: scroll slice, window/level, DWI vs ADC; zoom ke lesi; label "terang di DWI / gelap di ADC".
- voiceover: "Di viewer, Dika menggulir slice, mengatur window level, dan membandingkan DWI dengan peta ADC. Infark akut tampak terang di DWI, dan gelap di ADC."

## Frame 16: Menandai lesi (185.5-193.1s)

- act: Babak 3 — Demo produk
- status: animated
- vo_at: 0.5
- src: compositions/frames/16-demo-kuas.html
- duration: 7.6s
- transition_in: whip pan
- blueprint: cursor-ui-demo (rekaman asli) + rules cursor-click-ripple
- scene: Rekaman asli kuas labelmap mengecat lesi; ripple pada tombol Submit.
- voiceover: "Lalu ia menandai lesi dengan kuas, langsung di atas citra, dan menekan submit."

## Frame 17: Skor & jenis kesalahan (193.1-201.7s)

- act: Babak 3 — Demo produk
- status: animated
- vo_at: 0.5
- src: compositions/frames/17-demo-skor.html
- duration: 8.6s
- transition_in: zoom-in blur
- blueprint: device-surface-showcase + rules counting-dynamic-scale
- scene: Rekaman asli kartu hasil; angka Dice/recall/galat volume diperbesar dengan callout; overlay kunci vs jawaban; label jenis kesalahan.
- voiceover: "Dalam hitungan detik, skornya keluar: Dice, recall per lesi, galat volume, dan jenis kesalahannya."

## Frame 18: Tutor Sokratik (201.7-213.5s)

- act: Babak 3 — Demo produk
- status: animated
- vo_at: 0.5
- src: compositions/frames/18-demo-tutor.html
- duration: 11.8s
- transition_in: slide-up
- blueprint: prompt-type-submit-generate (rekaman asli streaming)
- scene: Rekaman asli panel tutor; pertanyaan diketik, jawaban streaming; Sina mengintip dari pojok dengan butir oranye.
- voiceover: "Dika bertanya ke tutor. Dalam mode Sokratik, tutor tidak langsung memberi jawaban. Ia membimbing dengan pertanyaan, berpijak pada temuan kasus ini."

## Frame 19: Dasbor dosen (213.5-223.1s)

- act: Babak 3 — Demo produk
- status: animated
- vo_at: 0.5
- src: compositions/frames/19-demo-dosen.html
- duration: 9.6s
- transition_in: push (3D carousel)
- blueprint: device-surface-showcase (carousel)
- scene: Rekaman asli dasbor dosen: ringkasan kelas → peta penguasaan → audit tutor; kartu bergeser seperti carousel.
- voiceover: "Di sisi dosen, ada peta penguasaan tiap mahasiswa, kesalahan yang paling sering muncul, dan audit setiap jawaban tutor."

## Frame 20: Hasil uji (223.1-240.5s)

- act: Babak 4 — Bukti & penutup
- status: animated
- vo_at: 0.5
- src: compositions/frames/20-hasil-uji.html
- duration: 17.4s
- transition_in: batang warna + kartu judul HASIL UJI
- blueprint: dataviz-countup + comparison-split
- scene: Dua angka besar: 97,8% vs 47,3% (aturan jenis kesalahan vs Dice saja), lalu 0/432 jawaban tutor di luar fakta, 341 panggilan API tanpa kebocoran. Catatan jujur kecil: angka dari anotasi sintetis; efek belajar belum diukur.
- voiceover: "Hasilnya? Modul penilaian mengenali jenis kesalahan dengan akurasi sembilan puluh tujuh koma delapan persen, dibanding empat puluh tujuh persen kalau hanya memakai Dice. Dan dari empat ratus tiga puluh dua jawaban tutor, tidak satu pun keluar dari fakta."

## Frame 21: Penutup (240.5-251s)

- act: Babak 4 — Bukti & penutup
- status: animated
- vo_at: 0.6
- src: compositions/frames/21-penutup.html
- duration: 10.5s
- transition_in: crossfade
- blueprint: logo-assemble-lockup (end card)
- scene: Dika kini yakin, tos dengan Sina; logo SINAPS, "Tim Rizzz — Sains Data, Universitas Airlangga", tautan mvp-lemon-ten.vercel.app, catatan "alat bantu belajar, bukan alat diagnosis".
- voiceover: "SINAPS. Latihan membaca MRI stroke, kapan saja, dengan umpan balik yang bisa dipercaya."
