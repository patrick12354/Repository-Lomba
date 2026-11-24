# Rancangan visual — Berkas 734

Dasar isi: `SCRIPT_FINAL_DETECTIVE_NSC_2026.md` di root workspace. Rancangan ini mengikuti seluruh 14 slide dalam script baru, termasuk lima ACT dan video 75 detik pada slide 10. Visual slide 2 lama tidak digunakan. Aset lama hanya menjadi referensi gaya, bukan acuan isi, judul, pembabakan, atau susunan slide.

Status: rancangan untuk produksi slide, bukan PPTX atau video yang sudah dibuat. Angka di bawah mengikuti script; beberapa angka juga ditemukan dalam ekstraksi paper final. Dokumen ini tidak menjalankan ulang eksperimen atau memverifikasi leaderboard secara langsung.

## Arah visual

**Satu berkas investigasi yang semakin terbuka.** Awalnya penonton melihat persoalan Pak Anton, kemudian membuka catatan sensor, memeriksa bukti, menguji model, dan akhirnya memahami bagaimana 734 prediksi menjadi satu lintasan.

Gunakan tema detektif hitam-krem yang sudah ada, tetapi dengan komposisi lebih lapang. Setiap slide memiliki satu objek atau exhibit dominan. Kertas sobek, selotip, dan anotasi tangan menjadi bingkai cerita; grafik tetap bersih dan terbaca.

- Kanvas 16:9. Margin aman sekitar 5% pada semua sisi.
- Latar arang `#191919`, lembar bukti krem `#F2E8D5`, tinta hampir hitam `#24211D`, aksen merah `#A52B25`. Warna ilustrasi kebun mengikuti karakter yang sudah ada.
- Merah menandai sesuatu yang perlu diperiksa: nilai hilang, anomali, ketidakcocokan, atau keputusan. Jangan membuat semua elemen merah.
- Judul pendek, sekitar 32–40 pt. Angka utama 64–88 pt. Label dan isi 22–26 pt. Sumber sekitar 14–16 pt dan tidak memuat pesan utama.
- Teks isi idealnya 15–30 kata per slide, di luar nama model, label grafik, dan sumber. Penjelasan lengkap tetap pada script.
- Pak Anton hadir pada pembukaan. Setelah slide 2, fokus berpindah ke bukti ilmiah; karakter tidak perlu muncul di semua halaman.
- Tidak perlu ilustrasi tomat di seluruh tepi slide. Sisakan ruang untuk exhibit.
- Nama babak mengikuti script: THE MYSTERY, THE CLUES, THE INVESTIGATION, THE BREAKTHROUGH, CASE CLOSED. Tidak menambahkan slide divider.
- Grafik, angka, label, dan persamaan dibuat sebagai objek editable ketika diproduksi. Ilustrasi menjadi aset terpisah. Jangan mengandalkan gambar generatif untuk menulis angka atau menggambar hasil eksperimen.

**Motif pengikat:** lembar berkas pada slide 1 berubah menjadi timeline slide 2. Titik pada timeline menjadi titik sensor, kemudian titik residual, lalu simpul lintasan slide 10. Berkas ditutup kembali pada slide 14.

## Peta 14 slide

| Slide | Teks utama yang disarankan | Visual dominan | Durasi |
|---|---|---|---:|
| 1 | BERKAS 734 | Pak Anton dan catatan kelembapan yang kosong | 45 dtk |
| 2 | Jejak sensor masih tersedia | Timeline train/test dan kanal yang tetap teramati | 45 dtk |
| 3 | Sebagian bukti perlu diperiksa | Pembacaan suhu dan pemeriksaan satu titik | 70 dtk |
| 4 | Catatan harian menyimpan petunjuk fisika | Dua jalur rekonstruksi suhu minimum | 60 dtk |
| 5 | Kondisi pada periode uji berubah | Distribusi suhu dan perubahan irigasi | 50 dtk |
| 6 | Lima model membaca jejak yang berbeda | Lima anggota tim investigasi | 65 dtk |
| 7 | Model diuji pada waktu berikutnya | Rolling-origin CV dengan jendela 15 hari | 65 dtk |
| 8 | Waktu membantu penggabungan model | Ensemble per bagian hari dan kontrol acak | 55 dtk |
| 9 | Kesalahan masih memiliki pola waktu | Residual berurutan dan autokorelasi | 55 dtk |
| 10 | Nilai dan perubahan diselaraskan bersama | Video rekonsiliasi lintasan | 85 dtk |
| 11 | Rekonsiliasi memperbaiki hasil pengujian | Bukti increment dan RMSE publik sebelum/sesudah | 60 dtk |
| 12 | Bias muncul pada audit maju | Bias CatBoost dan koreksi parsial | 65 dtk |
| 13 | Bukti tambahan tidak selalu membantu | Eksperimen ditolak dan batas penerapan | 45 dtk |
| 14 | CASE CLOSED | Hasil publik dan validasi sebagai dua bukti terpisah | 55 dtk |

Jumlah target script: **820 detik / 13 menit 40 detik**, termasuk video. Ini belum merupakan hasil rehearsal. Jangan menambahkan jeda animasi di luar durasi bicara yang dialokasikan.

## Slide 1 — A Mysterious Case

**Yang harus langsung terbaca:** ada persoalan, ada dugaan, dan catatan yang diperlukan justru tidak tersedia.

**Komposisi:** sekitar dua pertiga kanvas menjadi ilustrasi rumah kaca. Pak Anton kartun memeriksa daun tomat yang layu, dengan sensor lingkungan terlihat pada tiang. Sepertiga kanan menjadi map investigasi yang awalnya tertutup. Hindari tiga inset tambahan yang saling berebut perhatian.

**Teks layar:** `BERKAS 734`, `The Missing Humidity Case`, `734 nilai kelembapan tidak diketahui`. Nama tim kecil di bawah. Satu keterangan: `Kebun Pak Anton merupakan ilustrasi.`

**Urutan kemunculan:** kebun dan Pak Anton saat diperkenalkan; lingkaran tipis pada sensor saat sensor disebut; map terbuka saat script mulai menelusuri catatan; lembar kelembapan kosong dan angka 734 muncul pada kalimat tentang periode yang hilang. Pertanyaan Pak Anton bisa berupa tetes air dan tanda tanya, tanpa diagnosis penyakit.

**Transisi:** lembar catatan di dalam map membesar menjadi timeline slide 2. Jangan membuka dengan skor atau nama algoritma.

## Slide 2 — Entering the Crime Scene

**Desain sepenuhnya baru dari script.** Slide 2 lama tidak dipakai, termasuk komposisi kebun, judul, dan susunan elemennya.

**Komposisi:** satu lembar bukti lebar memenuhi bagian tengah. Sumbu waktu horizontal terbagi menjadi periode latih di kiri dan periode uji di kanan, kira-kira dengan proporsi jumlah baris 4:1. Baris teratas adalah target kelembapan; bagian latih memiliki jejak teramati dan bagian uji berupa ruang kosong dengan tanda tanya. Di bawahnya, beberapa pita sensor tetap berlanjut melewati batas train/test.

Pita sensor cukup dikelompokkan menjadi `Suhu`, `Tekanan udara`, `Tanah`, `Irigasi`, dan `Sensor lain`, dengan kurung `24 kanal sensor`. Jangan menggambar 24 grafik kecil. Gunakan tanda ketersediaan data, bukan kurva buatan yang tampak sebagai pengukuran.

**Teks layar:** `2.933 catatan latih`, `734 baris uji`, `Target tidak diberikan`, `24 kanal sensor tetap tersedia`. Label periodenya tetap terlihat.

**Urutan:** periode latih muncul; periode uji menyambung; hanya jalur kelembapan terputus; jalur sensor lain tetap menerus. Penonton perlu melihat bahwa ketidaktersediaan target tidak sama dengan ketidaktersediaan seluruh informasi.

**Transisi:** sorot jalur suhu, lalu perbesar menjadi grafik slide 3. Keterangan bawah: `Skema ketersediaan data, bukan grafik pengukuran.`

## Slide 3 — Contaminated Evidence

**Komposisi:** grafik suhu besar di kiri, sekitar 65% area isi. Satu anomali menjadi fokus. Kanan berisi perbandingan tiga rasio residual, disusun vertikal: suhu **5,75**, tekanan **6,86**, kelembapan **1,20**. Beri label jelas bahwa angka ini adalah rasio, bukan nilai suhu atau tekanan.

**Urutan:** tampilkan potongan data nyata; tandai titik yang diperiksa; sembunyikan titik itu sementara; empat tetangga tetap terlihat; tampilkan perkiraan kuadratik sebagai titik kosong; buka kembali nilai asli dan tarik garis selisihnya. Label pendek `Residual` muncul pada selisih itu.

Sesudah tiga rasio muncul, tunjukkan Hampel menangani lonjakan terpilih. Titik yang tidak perlu diubah tetap berada di tempatnya. Jika contoh interpolasi dibuat konseptual, tulis `Ilustrasi pemeriksaan satu titik` dan jangan menyebutnya hasil data asli.

**Teks layar:** `Periksa lonjakan sebelum mempercayai sensor`. Istilah metode cukup di satu baris bawah: `LOO quadratic interpolation · MAD · Hampel`.

**Aset calon:** `paper/figures/02-residu-loo.png` dan `11-despiking.png`, sebagai sumber untuk membangun ulang exhibit, bukan ditempel sekaligus sebagai dua halaman paper.

## Slide 4 — The Hidden Clue

**Komposisi:** tujuh tab catatan agronomi di kiri mengarah ke dua jalur persamaan di tengah. Kedua jalur bertemu pada satu hasil `Suhu minimum`. Di kanan, angka **0,047 °C** dengan label `SD selisih dua rekonstruksi`. Di bawahnya ada hubungan fisika singkat antara proksi titik embun, tekanan uap, dan RH.

**Urutan:** catatan harian dibuka; dua jalur rekonstruksi terlihat bergantian; kedua hasil bertemu. Jika menggunakan garis hampir berhimpit, pakai hasil rekonstruksi yang tersedia dan satu inset kecil untuk memperlihatkan selisih. Jangan menggambar dua kurva buatan sebagai bukti kesesuaian.

**Persamaan yang boleh terlihat:** `RH = 100 × e / eₛ(T)`. Label `e: tekanan uap aktual` dan `eₛ(T): tekanan uap jenuh` menjelaskan simbol. Detail dua rumus invers masuk lampiran saat produksinya.

**Teks layar:** `Dua jalur, rekonstruksi hampir identik`, `Tmin sebagai proksi titik embun`. Nilai 0,047 adalah konsistensi antara dua rekonstruksi, bukan galat terhadap pengukuran titik embun.

**Aset calon:** `paper/figures/04-dekomposisi-fisis.png` dan `13-proksi-titik-embun.png`. Fokus pada informasi yang diturunkan, bukan ilustrasi mesin AI.

## Slide 5 — The Crime Scene Has Changed

**Komposisi:** satu halaman perbandingan dengan dua kolom berlabel `Train` dan `Test`. Bagian atas menunjukkan distribusi suhu pada sumbu yang sama; angka **27,51 °C** dan **24,64 °C** ditempatkan dekat mean masing-masing. Bagian bawah menunjukkan irigasi: bervariasi pada train, konstan pada test.

**Urutan:** train terlihat terlebih dahulu; test muncul pada skala yang sama; penanda mean berpindah; kemudian kontras irigasi dibuka. Terakhir, label kelompok `Tanah` dan `Irigasi` dicoret pada daftar fitur yang dipertahankan.

**Teks layar:** `Distribution shift`, `Fitur tanah dan irigasi dikeluarkan dari konfigurasi akhir`.

Untuk distribusi, bangun grafik dari dataset atau gunakan exhibit hasil analisis yang tersedia. Dua mean saja tidak cukup untuk membuat bentuk histogram. Jika data belum diambil saat produksi, pakai dot plot mean yang jujur tanpa mengarang sebaran.

**Transisi:** fitur yang dipertahankan menjadi masukan tim model pada slide 6. Aset calon: `paper/figures/05-audit-dukungan.png`.

## Slide 6 — Assembling the Investigation Team

**Komposisi:** lima lembar identitas pendek tersusun dalam satu baris, masing-masing punya nama dan satu peran. Kelimanya bergabung menuju satu jejak kelembapan di bawah. Gunakan metafora alat investigasi, bukan tahanan atau tersangka penyebab tanaman layu.

| Anggota | Label peran di slide | Cue visual |
|---|---|---|
| LightGBM Huber | Pengaruh galat ekstrem dibatasi | Jejak bercabang dan titik ekstrem yang ditandai |
| CatBoost Huber | Pola galat berbeda | Kaca pembesar pada jejak lain |
| ElasticNet | Hubungan linear teratur | Penggaris dan garis sederhana |
| Ridge berbasis tekanan uap | Hubungan fisika kelembapan | Diagram tekanan uap sederhana |
| LightGBM L2 | Peka terhadap galat besar | Selisih prediksi yang diperbesar |

**Urutan:** anggota muncul satu per satu sesuai script; kartu LightGBM Huber sedikit lebih dominan sebagai model utama. Saat CatBoost dibahas lagi, sorot perbedaan galatnya. Jangan memberi ranking atau bobot tanpa exhibit pendukung.

**Teks penutup:** `Peran berbeda, prediksi saling melengkapi`. Aset slide 6 lama yang berjudul SUSPECT tidak menjadi rancangan isi baru.

## Slide 7 — Testing Their Alibis

**Komposisi:** timeline bergulir memenuhi sekitar 75% area. Train berwarna tinta gelap, validation diberi bingkai merah dengan label besar `15 hari`. Kanan memuat `9 titik awal` dan satu rumus RMSE sederhana.

**Urutan:** tampilkan satu jendela training dari masa lalu; munculkan validation sesudahnya; geser origin ke posisi kedua dan ketiga; kemudian tampilkan sembilan baris tipis yang sejajar sebagai rangkuman. Training berhenti pada origin tiap baris. Jangan menampilkan baris acak sebagai visual dominan.

**Teks layar:** `Belajar dari masa lalu. Uji pada waktu berikutnya.`, `OOF untuk penggabungan`. Keterangan yang harus terbaca: `Jendela validasi tumpang tindih.`

Rumus cukup `RMSE = √mean((prediksi − aktual)²)` tanpa uraian panjang. Bila lokasi sembilan origin digambar berskala, ambil waktunya dari konfigurasi yang benar. Skema konseptual perlu diberi label.

**Aset calon:** `paper/figures/06-titik-asal-bergulir.png`. Transisi memindahkan hasil OOF menuju penggabungan slide 8.

## Slide 8 — Combining the Evidence

**Komposisi:** bagian kiri menunjukkan lima jalur prediksi masuk ke penggabungan berdasarkan bagian hari. Gunakan pita waktu lurus dengan pergantian terang/gelap, tanpa menambahkan jam atau jumlah band yang belum dicocokkan dengan implementasi. Bagian kanan menunjukkan hasil kontrol sebagai dua batang horizontal.

**Angka:** `Penurunan RMSE`, `Berdasarkan waktu: 0,080`, `Pembagian acak: 0,007`. Kedua batang memiliki nol dan skala yang sama. Menulis besar penurunan sebagai angka positif menghindari kebingungan arah; catatan dapat menyebut perubahan RMSE masing-masing −0,080 dan −0,007.

**Urutan:** ensemble biasa terlihat; penggabungan dipisah menurut waktu; label `NNLS: bobot ≥ 0` muncul; catatan `Shrinkage` menandai regularisasi. Baru kemudian buka hasil kontrol.

**Teks layar:** `Kontrol dengan kompleksitas setara`, `Audit validasi bersarang`. Diagram band adalah skema mekanisme; batang kontrol adalah angka eksperimen. Jangan menggambar tabel bobot fiktif atau menampilkan hasil ini sebagai skor publik.

## Slide 9 — The Pattern Nobody Noticed

**Komposisi:** grafik residual besar di kiri dan **≈0,93** di kanan, berlabel `Autokorelasi residual lag-1`. Garis nol terlihat tegas. Beri tanda hanya pada satu rentetan residual yang searah.

**Urutan:** residual muncul sepanjang waktu; satu rentetan disorot; angka autokorelasi dibuka. Pada pertanyaan tentang perubahan, bagian bawah memperlihatkan dua titik dengan selisih `Δ`, kemudian label `30 menit` dan `2 jam`.

**Teks layar:** `Kesalahan bertetangga cenderung searah`, `Nilai pada titik`, `Perubahan antartitik`.

Pilihan utama adalah residual validasi yang benar. Alternatifnya gunakan skema tanpa angka sumbu dan keterangan `Ilustrasi pola; angka autokorelasi berasal dari laporan`. Jangan menyajikan titik aktual periode test yang targetnya tidak diketahui.

**Transisi:** dua titik beserta hubungan Δ menjadi objek pertama dalam video slide 10. Aset calon: `paper/figures/09-anatomi-galat.png`.

## Slide 10 — Reconstructing the Timeline

**Komposisi:** video menempati hampir seluruh kanvas. Latar utama krem bersih, bingkai berkas tipis tetap hadir. Pertahankan posisi sumbu waktu sepanjang video agar penonton dapat mengikuti perubahan titik. Gunakan 6–8 simpul konseptual untuk memperjelas mekanisme, lalu perlihatkan gambaran lintasan yang lebih panjang pada akhir.

**Kode visual:** titik/garis level bertinta gelap; hubungan increment diberi garis merah putus-putus dengan label horizon. Bedakan juga bentuk dan jenis garis, sehingga pesan tidak bergantung pada warna saja.

### Storyboard video 75 detik

| Waktu video | Visual | Pesan / teks layar |
|---|---|---|
| 0–8 dtk | Satu sumber sensor bercabang menjadi dua jalur | `Level prediction` dan `Increment prediction` |
| 8–18 dtk | Titik level muncul di satu sumbu waktu | `Nilai pada setiap waktu` |
| 18–28 dtk | Hubungan 30 menit dan 2 jam muncul di antara simpul | `Perubahan antarwaktu` |
| 28–39 dtk | Sepasang titik diperbesar. Selisih level dan estimasi increment terlihat tidak cocok | `Dua estimasi belum konsisten` |
| 39–51 dtk | Bingkai optimasi mencakup semua simpul. Prediksi level tetap sebagai penanda awal | `Temporal reconciliation` dan `Weighted least squares` |
| 51–64 dtk | Titik-titik bergerak bersama ke kompromi. Tarikan ke level dan hubungan increment terlihat bersamaan | `Dekat dengan level. Sesuai dengan perubahan.` |
| 64–75 dtk | Tampilan melebar menjadi satu lintasan. Label `734 titik` muncul. Tahan frame akhir untuk kalimat terakhir VO | `Satu lintasan yang saling terhubung` |

Seluruh contoh bernilai konseptual, dengan label `Ilustrasi mekanisme`. Tidak perlu nilai RH buatan atau kurva aktual test. Kompromi berbobot tidak harus memenuhi seluruh hubungan secara persis; sisa ketidakcocokan dapat tetap terlihat.

**Catatan teknis untuk produksi:** adegan harus memperlihatkan penyesuaian bersama, bukan filter yang sekadar menghapus tonjolan. Jangan membuat semua titik bergerak menuju garis datar. Hubungan 2 jam harus melewati beberapa interval, bukan menjadi duplikat hubungan 30 menit.

Pengantar presenter sekitar 5 detik, video 75 detik, transisi presenter sekitar 5 detik. VO dalam script menjadi dasar final timing setelah direkam. Storyboard ini bukan animasi yang sudah dirender.

**Fallback statis dalam slide yang sama:** diagram `Level + Increment + WLS = Lintasan rekonsiliasi`, memakai posisi sebelum dan sesudah yang dibedakan jelas. Formula objektif lengkap masuk lampiran bila dibutuhkan juri.

## Slide 11 — The Breakthrough Is Real

**Komposisi:** satu lembar hasil dengan dua area yang terbuka berurutan. Pertama, perbandingan RMSE increment 30 menit: `Dari selisih level 1,91` dan `Model increment 1,81`. Kedua, bukti utama berukuran lebih besar: RMSE publik **3,02586 menjadi 2,86595**.

**Urutan:** buka perbandingan increment saat pemeriksaan pertama; tampilkan label `30 menit diberi bobot relatif lebih besar`; pada pemeriksaan kedua, buka hasil publik. Tutup dengan satu keterangan `Arah perbaikan konsisten pada 3 blok audit maju`.

**Teks layar:** `RMSE lebih kecil berarti lebih baik`, `Perbaikan publik ≈0,160`.

Jangan menggambar besar hasil horizon dua jam karena script tidak memberi angka. Grafik prediksi sebelum/sesudah hanya boleh memakai blok validasi dengan aktual yang tersedia, serta label periode dan sumber. Tanpa data itu, gunakan angka atau batang pembanding, bukan kurva hasil yang dikarang.

Angka validasi increment dan skor publik berada di area yang berlabel berbeda. Aset calon: `paper/figures/07-rekonsiliasi-increment.png` dan `10-tangga-leaderboard.png` sebagai sumber bukti untuk dibangun ulang.

## Slide 12 — The Hidden Bias

**Komposisi:** garis nol pada sumbu bias horizontal, dengan dua titik CatBoost: `In-sample −0,006 %RH` dekat nol dan `Audit maju −2,89 %RH` jauh di kiri. Besar skala harus konsisten; label nilai in-sample dapat diletakkan terpisah agar terbaca.

**Urutan:** titik in-sample muncul; audit maju dibuka untuk menunjukkan kontras; lalu masukkan alur terpisah `Estimasi bias dari OOF`, `Koreksi parsial 50%`, `Prediksi CatBoost`. Gunakan stempel kecil `Tidak membaik` untuk kontrol arah salah dan kontrol model hampir tidak bias.

**Teks layar:** `Bias negatif: prediksi cenderung rendah`, `Koreksi dihitung dari OOF`.

Jangan menggambar panah koreksi tepat setengah jarak −2,89 menuju nol. Angka audit maju adalah bukti diagnosis, sedangkan besar koreksi berasal dari estimasi OOF yang berbeda. Tanpa besar koreksi aktual, alur koreksi tetap konseptual.

Jangan menambahkan skor setelah bias correction yang tidak disebut pada slide ini. Aset calon: `paper/figures/08-bias-anggota.png`.

## Slide 13 — The Rejected Evidence

**Komposisi:** satu lembar eksperimen besar, sekitar dua pertiga area, diberi cap `REJECTED`. Di dalamnya angka **2,86595 menjadi 2,93028**, dengan label `RMSE publik meningkat`. Sepertiga kanan berupa catatan ringkas batas penerapan.

**Urutan:** hasil paket tambahan diperlihatkan; cap muncul setelah script menyatakan pendekatan ditinggalkan; catatan keterbatasan dibuka pada bagian kedua narasi.

**Teks catatan:** `Sensor pendamping tersedia pada periode prediksi kompetisi`, `Real-time perlu evaluasi tersendiri`, `Dampak panen belum diuji`.

Cap hanya mengenai eksperimen tambahan, bukan seluruh pipeline. Jangan menambahkan klaim bahwa sistem sudah dipasang di kebun atau menyelamatkan tanaman. Scene kebun awal tidak dijadikan foto hasil implementasi pada slide ini.

**Transisi:** lembar rejected bergeser ke belakang map; halaman keputusan akhir muncul pada slide 14.

## Slide 14 — Case Closed: Berkas 734

**Komposisi:** map Berkas 734 terbuka di tengah. Hasil publik menjadi angka terbesar, **2,82744**, dengan label yang selalu terlihat `RMSE publik akhir`. Di bagian bawah terdapat exhibit validasi terpisah: **LightGBM 5,71** dan **Pipeline lengkap 4,81**.

Di sisi exhibit validasi, tampilkan **≈15,8%** dengan label `Perbaikan validasi`. Sembilan tanda sederhana di bawahnya berlabel `Lebih baik pada 9/9 fold`. Catatan: `Rolling-origin dengan jendela tumpang tindih`.

**Urutan:** angka publik dibuka dahulu; angka validasi muncul saat disebut; sorot penurunan dan sembilan fold. Pada rangkuman proses, tampilkan satu deretan kata singkat: `Sensor`, `Fisika`, `Shift`, `Ensemble`, `Lintasan`. Jangan mengulang seluruh pipeline dalam diagram padat.

Saat kalimat akhir dibacakan, cap `CASE CLOSED` muncul pada sampul tanpa menutupi angka. Tahan hasil akhir selama penutup dan Q&A. Tidak menambahkan slide Terima Kasih.

**Kalimat layar penutup:** `734 nilai direkonstruksi dengan bukti yang dapat diuji.` Tidak menampilkan kebun yang kembali sehat sebagai hasil model, karena dampak tanaman belum dievaluasi.

## Aturan sumber dan kesiapan produksi

1. Isi, urutan, dan durasi mengikuti script baru di root. Script dan aset versi lama tidak menentukan rancangan.
2. Data nyata, skema, dan konteks ilustratif memiliki keterangan yang berbeda. Pak Anton adalah ilustrasi. Diagram rekonsiliasi adalah ilustrasi mekanisme. Grafik hasil memakai data atau laporan yang disebut sumbernya.
3. Sumber exhibit ditempatkan dekat bagian bawah, memakai bagian/tabel laporan yang sudah dicocokkan ketika produksi. Kandidat gambar paper di atas belum berarti semua file itu telah diinspeksi atau siap ditempel.
4. Semua grafik RMSE memakai arah dan skala yang jelas. Pisahkan RMSE publik, rolling-origin validation, audit maju, dan validasi bersarang. Perbaikan 15,8% pada penutup berasal dari perbandingan validasi 5,71 dan 4,81.
5. Grafik suhu, residual, kurva rekonstruksi, dan prediksi tidak dibuat sebagai gambar generatif. Ambil data yang tepat, atau tampilkan skema berlabel tanpa mengarang hasil.
6. Saat produksi, cek setiap slide pada ukuran proyektor. Judul, angka, label sumbu, dan caveat penting harus terbaca; kurangi elemen sebelum mengecilkan huruf.
7. Video perlu frame akhir statis, playback lokal, dan pemeriksaan durasi dengan VO. Animasi slide lain muncul sambil presenter berbicara, tanpa jeda tambahan.

**Keputusan rancangan:** seluruh deck mengikuti script baru. Gaya detektif dipertahankan sebagai bahasa visual, dengan isi dan komposisi tiap slide dibangun ulang sesuai fungsi narasinya.
