# Kerangka PPT dan script Grand Final NSC 2026 — Heisenberg

Disusun 11 Oktober 2026. Kerangka ini untuk mempresentasikan pekerjaan penyisihan, bukan mengusulkan model baru. Belum berupa deck PPTX atau video jadi.

Arah narasi terbaru: lihat **[SCRIPT_FINAL_DETECTIVE_NSC_2026.md](SCRIPT_FINAL_DETECTIVE_NSC_2026.md)**. Versi terbaru memakai empat babak TKP–Suspect–Bukti–Pelaku, 14 slide utama, anggaran 13:40, dan video mekanisme 75 detik pada slide 10. Susunan/waktu/video pada dokumen lama di bawah merupakan rancangan terdahulu; dokumen ini tetap menjadi acuan ketentuan dan bahan teknis.

Rubrik diverifikasi kembali dari PDF workspace **f15702c4-786c-4330-8f50-b340ce839074.pdf**. Panduan implementasi tiap bobot dan bank Q&A: **[STRATEGI_RUBRIK_FINAL_NSC_2026.md](STRATEGI_RUBRIK_FINAL_NSC_2026.md)**.

## 1. Ketentuan yang sudah diperiksa

Sumber utama: **Juknis Grand Final Data Science NSC 2026.pdf**, 3 halaman, dari folder Downloads. Halaman 1 memuat ketentuan, halaman 2 rubrik, halaman 3 jadwal. Tabel rubrik juga diperiksa dari render halaman asli, bukan hanya hasil ekstraksi teks.

| Butir | Ketentuan juknis final | Konsekuensi untuk deck |
|---|---|---|
| Materi | Analisis dan pemodelan yang dilakukan pada penyisihan, §1.a | Konsisten dengan paper dan notebook yang dikumpulkan |
| Susunan | Panduan opsional; bebas menyesuaikan susunan dan isi | Boleh membuka dengan problem statement dan hook |
| Presentasi | 15 menit, §1.g | Target latihan 13:35; cadangan 1:25 |
| Tanya jawab | 24 menit, §1.g | Siapkan appendix dengan bukti dan keputusan analisis |
| Jumlah slide/halaman PPT | **Tidak dicantumkan pada ketiga halaman juknis final** | 14 slide utama merupakan rekomendasi, bukan batas panitia |
| Batas 10 halaman | Aturan laporan penyisihan dalam panduan lama | Jangan menerapkannya sebagai batas PPT |
| Format pengumpulan | **.pptx**, §1.c | Siapkan PPTX; PDF hanya salinan pendamping |
| Deadline | **17 Oktober 2026, 23.59 WIB**, §1.c | Sisakan waktu untuk memeriksa video di file final |
| Nama file | `Nomor Tim_Nama Tim_PPT Grand Final Data Science` | `NSC26-DS042_Heisenberg_PPT Grand Final Data Science.pptx` |
| Pengumpulan | Google Form di website NSC, Event – Data Science – Grand Final | Ikuti tautan resmi panitia |
| Pelaksanaan | 25 Oktober 2026, UB; jadwal cabang 08.30–11.20 WIB | Jam tampil tim mengikuti undian TM |
| Identitas | Dilarang memakai atribut/identitas instansi dan menyebut asal instansi, §1.h–i | Hilangkan logo kampus, afiliasi, email kampus, serta identitas kampus pada QR dan video |
| Kehadiran | Jika belum datang hingga 10 menit sebelum presentasi, diskualifikasi; keterlambatan harus menghubungi LO, §1.e | Datang dengan cadangan waktu |
| Perangkat | Semua alat komunikasi dititipkan kepada panitia selama presentasi, §1.j | Materi dan video harus bisa dibuka offline |
| Pakaian | Atasan batik bebas sopan, bawahan kain hitam, bersepatu | Berlaku untuk final dan closing |

**Perubahan terhadap `guide_lomba.md`:** juknis final terbaru memakai **presentasi 60, Q&A 40**, bukan laporan 35, presentasi 40, Q&A 25. Untuk strategi final, gunakan dokumen final ini. Jangan mengulang bobot lama.

Tidak ada larangan video dalam juknis yang dibaca, tetapi juknis **tidak menjelaskan** izin teknis pemutaran, autoplay, audio, perangkat presenter, batas ukuran unggahan, atau apakah appendix dihitung dalam aturan tambahan TM. Konfirmasi detail ini ke LO berdasarkan informasi TM sebelum ekspor final. Kerangka dan storyboard tetap bisa disiapkan sekarang.

### Rubrik dan alokasi perhatian

Persen subkriteria berikut dihitung terhadap bobot kategori induknya.

| Komponen | Bobot dalam kategori | Kontribusi ke nilai total |
|---|---:|---:|
| Struktur dan keruntutan | 15% × 60 | 9 |
| Penguasaan materi dan pemahaman data | 25% × 60 | 15 |
| Ketepatan metode dan interpretasi hasil | 25% × 60 | 15 |
| Visualisasi data dan penyampaian insight | 20% × 60 | 12 |
| Waktu, intonasi, ekspresi, sikap | 15% × 60 | 9 |
| Q&A: kejelasan, ketepatan, logika | 35% × 40 | 14 |
| Q&A: penguasaan metode, data, hasil | 40% × 40 | 16 |
| Q&A: pertanggungjawaban keputusan | 25% × 40 | 10 |

Implikasinya: visual yang menarik harus membantu juri memahami keputusan metode. Menyisakan 24 menit Q&A tanpa appendix akan membuang kesempatan pada 40% penilaian.

## 2. Cerita utama: mengapa kelembapan penting, lalu bagaimana kita memprediksinya

**Revisi arah:** buka dari kebutuhan manusia dan keputusan yang bergantung pada kelembapan. Setelah itu baru masuk ke masalah data lomba, hasil, dan cara kerja model. Bahasa utama memakai istilah sehari-hari; nama metode muncul sebagai label kecil atau dibahas di appendix.

**Skenario pembuka:** pengelola rumah kaca tomat menghadapi malam yang semakin dingin. Udara semakin lembap dan air dapat mengembun pada daun. Kelembapan tinggi dan permukaan tanaman basah mendukung perkembangan beberapa penyakit jamur. Informasi kelembapan membantu pengelola mempertimbangkan pengaturan ventilasi dan lingkungan rumah kaca.

Landasan skenario: [UConn Extension — Foliar Diseases on Greenhouse Tomatoes](https://ipm.cahnr.uconn.edu/foliar-diseases-on-greenhouse-tomatoes/), terutama bagian penyakit jamur dan pencegahan. Sumber mendukung hubungan kelembapan, daun basah, dan risiko penyakit. **Pengelola dan kejadian malam tersebut adalah ilustrasi**, bukan kasus lapangan yang diamati tim. Kita tidak mengklaim dataset berasal dari rumah kaca tomat tertentu atau model sudah mengurangi penyakit.

**Masalah dunia nyata:** keputusan pengelolaan lingkungan membutuhkan informasi kelembapan yang dapat dipercaya. Pemantauan memberi pembacaan saat ini; prediksi atau perkiraan dari sensor lain dapat menambah informasi, sesuai data yang tersedia.

**Masalah yang diuji dalam lomba:** memperkirakan 734 pembacaan kelembapan pada periode sekitar 15 hari, ketika nilai kelembapannya tidak tersedia tetapi pembacaan sensor lainnya tersedia.

**Pertanyaan riset, bahasa lisan:** “Bisakah kita memperkirakan kelembapan dengan lebih baik dengan membaca pola sensor lain dan perubahan dari waktu ke waktu?”

**Pesan utama:** statistik membantu kita memahami data dan menilai apakah hasilnya dapat dipercaya. Machine learning mempelajari hubungan sensor yang rumit. Keduanya bertemu saat prediksi digabungkan dan diperiksa kembali.

Judul pendek: **“Membaca Kelembapan, Memahami Perubahannya”**. Identitas cukup Heisenberg, NSC26-DS042, dan nama anggota tanpa afiliasi.

Urutan cerita: **kepentingan nyata → masalah lomba → cuplikan hasil → temuan statistik → penjelasan AI/ML → pengujian → hasil → batas penggunaan → jawaban penutup**.

### Menjangkau juri statistik dan juri komputer

| Bagian | Nilai bagi juri statistik | Nilai bagi juri komputer / AI-ML | Bahasa yang didengar semua juri |
|---|---|---|---|
| Membaca data, slide 4–6 | Data hilang, pencilan, perubahan sebaran, pola waktu, hubungan suhu–kelembapan | Menentukan masukan model dan membuang masukan yang tidak stabil | “Tidak semua sensor bisa dipercaya dengan cara yang sama.” |
| Membangun model, slide 7 | Regresi linear, penggabungan berbobot, koreksi kecenderungan galat | LightGBM, CatBoost, rekayasa fitur, ensemble, prediksi perubahan | “Model membaca angka kelembapan dan arah perubahannya.” |
| Menguji hasil, slide 8–10 | Validasi berurutan, ukuran galat, pembanding setara, ketergantungan antar-periode | Generalisasi ke periode baru, kontribusi komponen, pipeline akhir | “Kami menguji pada waktu yang belum dipakai untuk belajar.” |
| Memeriksa kelemahan, slide 11–13 | Bias prediksi, perubahan sebaran, batas kesimpulan | Kalibrasi model, kegagalan kandidat, kebutuhan penggunaan langsung | “Hasil yang baik tetap harus diperiksa saat kondisinya berubah.” |

Jangan memisahkan presentasi menjadi kuliah statistik lalu kuliah AI. Setiap keputusan menunjukkan apa yang ditemukan pada data, bagaimana model merespons, dan apa bukti hasilnya. Statistik mempunyai peran nyata pada penggabungan model dan pengujian, bukan sekadar EDA.

## 3. Hook: malam di rumah kaca, 45 detik

**Judul slide 1:** “Malam yang semakin lembap dapat meningkatkan risiko penyakit tanaman.”

**Visual:** ilustrasi rumah kaca tomat menjelang malam, pengelola melihat tanaman, dan pembesaran daun dengan tetes embun. Label kecil “Ilustrasi skenario”. Teks utama hanya satu pertanyaan: **“Kapan udara menjadi terlalu lembap?”** Sumber UConn Extension di footer. Jangan tampilkan 734 titik atau RMSE pada slide pertama.

**Script pembuka:**

> “Bayangkan Anda mengelola rumah kaca tomat. Tanamannya tampak sehat saat sore hari. Namun ketika malam semakin dingin, kelembapan bisa meningkat dan air mengembun pada daun. Kondisi lembap dan daun basah dapat mendukung perkembangan penyakit jamur. Anda perlu mempertimbangkan kapan ventilasi harus diatur. Untuk itu, Anda membutuhkan informasi kelembapan yang bisa dipercaya. Inilah mengapa memperkirakan kelembapan penting: angkanya membantu memahami kondisi yang dihadapi tanaman.”

**Transisi ke slide 2:** “Lalu, bagaimana jika nilai kelembapan yang kita butuhkan tidak tersedia, sementara sensor lainnya masih merekam?”

Jangan menyatakan model lomba sudah memberi peringatan penyakit, mengendalikan ventilasi, atau menyelamatkan panen. Skenario menjelaskan kebutuhan informasinya; eksperimen kita menguji prediksi kelembapan.

### Tiga momen yang kuat

1. **Slide 1:** juri memahami keputusan nyata yang membutuhkan informasi kelembapan.
2. **Slide 7:** video memperlihatkan dua pertanyaan sederhana: “Berapa kelembapannya?” dan “Sedang naik atau turun?” Jawaban keduanya membentuk prediksi yang lebih baik.
3. **Slide 10:** ide tersebut dibayar dengan bukti: galat publik turun dari **3,02586 menjadi 2,86595** setelah langkah penyelarasan antar-waktu.

Kurva oracle tekanan uap tetap tersedia pada A4 untuk pertanyaan mendalam. Ia tidak perlu menjadi pusat presentasi utama yang ditujukan pada juri lintas bidang.

## 4. Kerangka 14 slide utama

Total anggaran tetap **815 detik = 13:35**, termasuk video 90 detik. Cadangan **1:25**. Waktu ini belum merupakan hasil rehearsal.

| # | Waktu | Durasi | Judul / pesan yang mudah dipahami | Visual utama |
|---:|---|---:|---|---|
| 1 | 00:00–00:45 | 45 dtk | **Malam yang semakin lembap dapat meningkatkan risiko penyakit tanaman.** | Skenario rumah kaca dan daun berembun |
| 2 | 00:45–01:30 | 45 dtk | **Kami memperkirakan kelembapan ketika hanya sensor lain yang tersedia.** | Target kosong, sensor lain tetap merekam |
| 3 | 01:30–02:10 | 40 dtk | **Gabungan model kami menghasilkan galat lebih kecil pada sembilan pengujian waktu.** | Hasil validasi dan publik dalam dua panel berbeda |
| 4 | 02:10–03:10 | 60 dtk | **Data mencakup sekitar dua bulan pengamatan dan 15 hari yang harus diprediksi.** | Timeline belajar dan periode prediksi |
| 5 | 03:10–04:05 | 55 dtk | **Sebagian pembacaan sensor perlu dibersihkan; sebagian hubungan berubah.** | Temuan data dan keputusan terhadap masukan model |
| 6 | 04:05–05:05 | 60 dtk | **Kelembapan berubah mengikuti suhu dan pola waktu.** | Satu grafik pola dalam sehari, dengan anotasi hubungan suhu |
| 7 | 05:05–06:45 | 100 dtk | **Model memperkirakan besar kelembapan sekaligus arah perubahannya.** | Satu slide video arsitektur 90 detik |
| 8 | 06:45–07:50 | 65 dtk | **Kami belajar dari masa lalu dan menguji pada periode sesudahnya.** | Skema pengujian berdasarkan waktu |
| 9 | 07:50–09:00 | 70 dtk | **Gabungan model mengurangi galat 15,8% dibanding satu LightGBM.** | RMSE validasi 5,71 vs 4,81 |
| 10 | 09:00–10:05 | 65 dtk | **Memperhitungkan perubahan antar-waktu membuat prediksi lebih akurat.** | RMSE publik 3,02586 vs 2,86595 |
| 11 | 10:05–11:05 | 60 dtk | **Satu model cenderung memprediksi terlalu rendah pada periode baru.** | Kecenderungan galat sebelum dan setelah pemeriksaan |
| 12 | 11:05–12:00 | 55 dtk | **Tambahan yang tampak menjanjikan belum tentu memperbaiki hasil.** | Satu percobaan gagal dan pelajarannya |
| 13 | 12:00–12:55 | 55 dtk | **Penggunaan langsung membutuhkan pengujian dengan data yang tersedia saat itu.** | Informasi tersedia sekarang vs sepanjang periode |
| 14 | 12:55–13:35 | 40 dtk | **Statistik dan machine learning membantu membaca kelembapan dengan lebih baik.** | Jawaban utama dan hasil akhir berlabel publik |

Tidak perlu daftar isi atau slide profil kampus. Istilah teknis tetap tercantum kecil agar juri ahli mengenali metode, tetapi judul dan narasi menjelaskan fungsinya.

## 5. Script inti per slide

Draft ini fondasi narasi. Tambahkan penjelasan yang menunjuk bukti visual saat latihan, bukan mengisi durasi dengan jargon.

### Slide 1 — mengapa informasi kelembapan penting

Gunakan script skenario di §3. Jangan menampilkan skor atau arsitektur pada pembuka. Satu visual yang menjelaskan konteks dan satu pertanyaan keputusan sudah cukup.

### Slide 2 — jembatan dari skenario ke tugas lomba

**Layar:** 734 pembacaan yang harus diperkirakan, sekitar 15 hari, sensor lain tersedia. Pertanyaan utama: “Bisakah sensor lain membantu kita membaca kelembapan?”

> “Dalam lomba ini, kami menghadapi masalah yang lebih spesifik. Ada 734 pembacaan kelembapan selama sekitar 15 hari yang nilainya tidak diberikan. Namun data suhu dan sensor lainnya tersedia. Kami ingin mengetahui apakah pola sensor tersebut, ditambah perubahan dari waktu ke waktu, bisa membantu memperkirakan kelembapan dengan lebih baik.”

**Catatan presenter:** rumah kaca adalah konteks ilustrasi, bukan identitas lokasi dataset. Target berada setelah periode belajar, tetapi pembacaan sensor lain sepanjang periode itu tersedia. Jelaskan batas ini pada slide 4 dan 13.

### Slide 3 — hasil singkat sebagai janji pembuktian

**Layar:** kiri “Pengujian berdasarkan waktu: 5,71 menjadi 4,81; galat turun 15,8%; unggul 9/9”. Kanan “Skor publik lomba: RMSE 2,82744”. Jangan menghubungkan kedua panel dengan panah.

> “Hasil awal yang ingin kami tunjukkan adalah ini. Pada sembilan pengujian waktu yang sama, gabungan model kami menghasilkan galat lebih kecil daripada satu LightGBM. Penurunannya sekitar 15,8%. Submission akhir mendapat RMSE publik 2,82744. RMSE adalah ukuran galat prediksi: semakin kecil, semakin baik. Angka pengujian internal dan angka lomba berasal dari data penilaian berbeda. Berikutnya kami jelaskan bagaimana kami sampai ke hasil itu.”

RMSE dalam poin persentase RH. Jangan mengubahnya menjadi persentase akurasi atau batas galat maksimum tiap titik.

### Slide 4 — data dan informasi yang tersedia

**Layar:** 2.933 pengamatan untuk belajar; 734 untuk diprediksi; interval 30 menit; 24 kanal sensor. Waktu tidak dihitung sebagai kanal sensor.

> “Kami memiliki sekitar dua bulan data untuk belajar. Setelah itu ada sekitar 15 hari yang kelembapannya harus diprediksi, dengan satu pembacaan setiap setengah jam. Ada 24 kanal sensor lain yang tersedia. Informasi ini menentukan cara kerja solusi kami. Kami dapat membaca pola sensor sepanjang periode prediksi, termasuk pembacaan sesudah suatu titik waktu, tetapi tidak dapat membaca nilai kelembapan yang disembunyikan.”

**Jembatan:** “Sebelum meminta model belajar, kami perlu memeriksa apakah data sensornya layak dipakai.”

### Slide 5 — statistik menentukan perlakuan terhadap data

**Layar:** satu diagram temuan-keputusan. Lonjakan sensor menjadi penanganan pencilan. Perubahan pola tanah/irigasi menjadi penghapusan kelompok masukan yang tidak stabil. Angka audit rinci di A1.

> “Di sinilah statistik membantu keputusan pertama. Kami memeriksa nilai yang hilang, lonjakan yang berbeda dari pengamatan di sekitarnya, dan perubahan sebaran antara periode belajar dan periode prediksi. Beberapa lonjakan sensor perlu dibersihkan. Ada pula kelompok pembacaan tanah dan irigasi yang polanya berubah, sehingga tidak kami gunakan pada masukan akhir. Tujuannya agar model belajar dari informasi yang lebih dapat dipercaya.”

Label kecil metode: **analisis sebaran, penanganan pencilan Hampel, interpolasi waktu**. Statistik dipakai untuk menentukan tindakan, bukan sebagai daftar ringkasan data saja.

### Slide 6 — pola waktu dan hubungan sensor memberi petunjuk

**Layar:** satu grafik pola kelembapan dalam sehari dari data latih. Anotasi jam dan hubungan suhu, tanpa dua sumbu yang sulit dibaca. Sumber `paper/figures/12-klimatologi-diurnal.png` sebagai bahan, buat ulang untuk panggung. Rumus tekanan uap di appendix.

> “Kelembapan memiliki pola dalam sehari dan berkaitan dengan suhu. Ketika udara mendingin, kelembapan relatif dapat meningkat, bahkan bila jumlah uap airnya tidak berubah. Karena itu kami tidak hanya memberikan pembacaan sesaat kepada model. Kami juga merangkum kondisi beberapa jam di sekitarnya dan pola waktu dalam sehari. Statistik membantu membaca polanya, sedangkan hubungan fisis membantu memilih informasi yang masuk akal untuk dipelajari.”

Hubungan yang teramati bukan bukti sebab-akibat semua sensor. Contoh udara mendingin menjelaskan mekanisme kelembapan relatif; jangan menyebut suhu sebagai satu-satunya penentu.

### Slide 7 — AI/ML, dengan satu video arsitektur

**Pengantar 5 detik:** “Sekarang kita lihat bagaimana model memakai informasi tadi untuk menjawab dua pertanyaan: berapa kelembapannya, dan bagaimana perubahannya?”

**Video 90 detik:** lihat §6. Label besar memakai bahasa fungsi. Nama model kecil tetapi terlihat. Kelompok boosting: LightGBM dan CatBoost. Kelompok linear: ElasticNet dan Ridge-e. Jelaskan bahwa keduanya melengkapi cara membaca hubungan sensor, bukan lima model selalu lebih baik.

**Transisi 5 detik:** “Setelah prediksi terbentuk, pertanyaan berikutnya adalah bagaimana mengujinya secara adil.”

Catatan teknis produksi: lima anggota aktif; satu LightGBM memakai Huber, satu memakai L2. Koreksi bias anggota sebelum penggabungan; koreksi harian setelahnya; prediksi perubahan masuk pada penyelarasan akhir. Detail tetap mengikuti pipeline final.

### Slide 8 — statistik menjaga pengujian tetap relevan

**Layar:** belajar dari masa sebelum garis potong, uji 15 hari sesudahnya. Ulangi pada beberapa titik awal. Label kecil “rolling-origin, 9 lipatan, langkah 2 hari”.

> “Kami tidak mencampur semua waktu secara acak. Itu dapat membuat model belajar dari kondisi yang terlalu dekat dengan data yang sedang diuji. Kami mengikuti bentuk tugas lomba: belajar dari masa lalu, lalu menguji sekitar 15 hari sesudahnya. Proses ini diulang pada sembilan titik awal. Beberapa periode uji saling bertumpang tindih, jadi hasilnya menunjukkan konsistensi pada pengujian yang tersedia, bukan sembilan percobaan yang sepenuhnya terpisah.”

Catatan Q&A A2: pisahkan prediksi model dasar yang luar-lipatan, fitting bobot/koreksi, dan audit maju/nested. OOF model dasar tidak otomatis menjamin evaluasi model gabungan bebas optimisme. Jangan menamai semua skor sebagai holdout independen.

### Slide 9 — pembanding setara dan arti besar perbaikan

**Layar:** dua bar RMSE 5,71 dan 4,81; label “data dan pengujian waktu yang sama”. Angka 15,8% dan 9/9 sebagai anotasi. Istilah pooled RMSE di catatan sumber.

> “Untuk menilai apakah gabungan model ini bermanfaat, kami membandingkannya dengan satu LightGBM pada pengujian yang sama. Galat turun dari 5,71 menjadi 4,81, sekitar 15,8%. Gabungan model juga unggul pada setiap periode pengujian. Ini menunjukkan bahwa kombinasi cara membaca data memberi manfaat pada evaluasi kami. Perbaikan tersebut belum menjadi jaminan hasil yang sama di lokasi lain.”

15,8% adalah perbandingan pipeline lengkap terhadap model tunggal, bukan kontribusi satu komponen saja.

### Slide 10 — perubahan antar-waktu menjadi faktor pembeda

**Layar:** dua skor publik 3,02586 dan 2,86595. Anotasi “setelah prediksi antar-waktu diselaraskan”. Caption teknis kecil “rekonsiliasi increment”.

> “Bagian yang memberi perubahan besar adalah langkah ini. Model pertama memperkirakan besar kelembapan di setiap waktu. Model kedua memperkirakan seberapa besar kelembapan berubah dalam 30 menit dan dua jam. Kami lalu menyelaraskan kedua informasi tersebut. Pada penilaian publik, galat turun dari 3,02586 menjadi 2,86595. Jadi manfaatnya datang dari membaca angka pada setiap titik sekaligus hubungan titik itu dengan waktu di sekitarnya.”

Penyelarasan bukan smoothing biasa: mengikuti perubahan yang dipelajari, bukan sekadar membuat garis lebih halus. Jika menunjukkan kurva aktual, gunakan blok validasi berlabel. Jangan menggambar aktual test yang tidak tersedia.

### Slide 11 — pemeriksaan galat menemukan masalah model

**Layar:** “terlihat baik saat belajar” vs “cenderung terlalu rendah pada periode baru”. Cantumkan bias −0,006 vs −2,89 %RH pada audit yang dilaporkan. Definisi kecil: bias = prediksi dikurangi aktual.

> “Pemeriksaan statistik juga membantu kami menemukan kelemahan salah satu model. Saat diperiksa pada data yang dipakai belajar, rata-rata kesalahannya hampir nol. Namun pada pengujian ke depan, prediksinya cenderung terlalu rendah. Kami mengukur kecenderungan itu dari prediksi pada data yang tidak dipakai melatih model dasarnya, lalu memperbaikinya. Koreksi terkait menurunkan skor publik dari 2,84953 menjadi 2,82744.”

Angka −2,89 adalah bias anggota CatBoost pada audit, bukan bias ensemble. Besar koreksi mengikuti aturan yang dipelajari dari OOF, bukan langsung menambahkan 2,89 pada seluruh hasil. Detail di A6.

### Slide 12 — eksperimen gagal menjelaskan disiplin pemilihan

**Layar:** satu kandidat “penyesuaian sebaran + perubahan masukan”, RMSE publik 3,28564, label “tidak dipakai pada konfigurasi akhir”. Detail teknis di A7.

> “Kami juga mencoba tambahan yang tampak menjanjikan pada evaluasi internal, tetapi hasilnya lebih buruk pada penilaian publik. Salah satunya penyesuaian sebaran prediksi bersama perubahan masukan. Kondisi periode uji ternyata berbeda dari kondisi saat penyesuaian itu dipelajari. Percobaan ini tidak masuk konfigurasi akhir. Pelajarannya: model yang semakin rumit tetap harus membuktikan manfaatnya.”

Dua komponen berubah pada kandidat awal. Jangan mengatribusikan seluruh kegagalan hanya kepada satu komponen. Jangan mengatakan leaderboard tidak pernah memengaruhi penerimaan atau penolakan koreksi akhir.

### Slide 13 — hubungkan ke rumah kaca tanpa melampaui bukti

**Layar:** “Teruji: memperkirakan kelembapan dari sensor yang tersedia” dan “Langkah berikutnya: pengujian langsung dan pengaruh terhadap keputusan”.

> “Kembali ke pengelola rumah kaca tadi, informasi kelembapan memang relevan untuk memahami kondisi tanaman. Namun yang telah kami uji di sini adalah kemampuan memperkirakan kelembapan pada data lomba. Sensor lain tersedia sepanjang periode prediksi. Untuk penggunaan langsung, kami perlu menguji sistem hanya dengan informasi yang sudah tersedia saat keputusan dibuat. Setelah itu, barulah diuji apakah informasinya membantu keputusan pengelolaan. Pengurangan penyakit atau peningkatan hasil panen belum diukur dalam pekerjaan ini.”

Bawa kontrol kausal LightGBM 5,71 vs 8,22 ke A8. Kontrol itu bukan ukuran biaya kausal seluruh ensemble.

### Slide 14 — tutup pada kebutuhan dan jawaban

**Layar:** visual rumah kaca kembali, ditemani kurva berlabel “prediksi kelembapan”. Pesan singkat: “Pahami data. Pelajari hubungan sensor. Uji hasilnya.” Skor 2,82744 berlabel publik.

> “Di awal, kita melihat mengapa informasi kelembapan penting bagi pengelolaan lingkungan tanaman. Dalam tugas ini, statistik membantu kami memahami kualitas data dan menguji hasil dengan tepat. Machine learning membantu mempelajari hubungan sensor dan perubahan kelembapan. Gabungan model unggul pada sembilan pengujian waktu dan mencapai RMSE publik akhir 2,82744. Inilah langkah yang kami buktikan menuju informasi kelembapan yang lebih dapat dipercaya. Terima kasih.”

Kesimpulan tetap tampil saat Q&A. Jangan menyebut sistem sudah mencegah penyakit tanaman atau menyediakan peringatan operasional.

### Padanan istilah untuk slide dan narasi

| Istilah teknis di catatan | Istilah utama yang dipakai saat berbicara |
|---|---|
| Eksogen | Sensor lain yang tersedia |
| Feature engineering | Menyiapkan informasi yang dipelajari model |
| Ensemble / stack | Gabungan model |
| Increment | Perubahan kelembapan |
| Rekonsiliasi | Menyelaraskan prediksi kelembapan dan perubahannya |
| Bias | Kecenderungan memprediksi terlalu tinggi atau rendah |
| Distribution shift | Pola data berubah pada periode baru |
| Rolling-origin | Belajar dari masa lalu, menguji pada waktu sesudahnya |
| OOF | Prediksi pada data yang tidak dipakai melatih model dasar terkait |
| RMSE | Ukuran galat prediksi, semakin kecil semakin baik |

Istilah aslinya tetap dicantumkan sekali dalam label kecil agar ahli mengenali metode. Jangan menjelaskan RMSE sebagai rata-rata galat absolut, atau mengatakan prediksi setiap titik pasti meleset kurang dari angka RMSE.

## 6. Motion graphic arsitektur: 90 detik, satu slide

**Rekomendasi durasi: 1 menit 30 detik.** Anggaran slot 1:40 termasuk pengantar dan transisi. Dua menit atau lebih akan mengambil waktu dari validasi dan bukti yang bernilai besar dalam rubrik.

Ini **storyboard untuk produksi video berikutnya**, belum animasi atau video jadi. Gerakan dipakai untuk memperlihatkan hubungan data dan metode. Hindari intro logo, opening sinematik panjang, katalog hiperparameter, dan detil matriks yang tidak sempat dijelaskan.

| Detik | Visual / gerakan | Pesan narasi |
|---|---|---|
| 0–12 | Data untuk belajar dan periode prediksi. Pembacaan sensor lain tetap tersedia | Kita memperkirakan kelembapan dari sensor lainnya |
| 12–25 | Tandai pembacaan bermasalah, lalu tampilkan ringkasan pola sensor | Data diperiksa dan informasi penting dirangkum |
| 25–42 | Lima anggota dalam kelompok linear dan boosting. Nama algoritma tampil kecil | Cara membaca hubungan sederhana dan rumit saling melengkapi |
| 42–56 | Urutan koreksi anggota, penggabungan berbobot, lalu koreksi pola harian | Periksa kecenderungan salah dan gabungkan prediksi sesuai bukti |
| 56–71 | Cabang perubahan menghubungkan titik berjarak 30 menit dan dua jam | Seberapa besar kelembapan naik atau turun? |
| 71–86 | Dua jawaban bergabung dan seluruh titik menyesuaikan bersama | Selaraskan besar kelembapan dengan perubahan antar-waktu |
| 86–90 | Diagram lengkap berhenti pada lintasan hasil. Tampilkan label “734 prediksi RH” | Satu lintasan akhir |

Urutan komputasi **dalam diagram yang benar**:

```text
Sensor eksogen tersedia pada train dan test
  Pembersihan dan fitur
    Cabang level:
      LightGBM Huber / CatBoost Huber / ElasticNet / Ridge-e / LightGBM L2
      Koreksi bias anggota CatBoost dari OOF
      Blending NNLS dengan shrinkage dan bobot per pita waktu
      Koreksi bias diurnal
      Prediksi level p
    Cabang perubahan:
      Model increment 30 menit dan 2 jam
      Prediksi d1 dan d4
  Rekonsiliasi p, d1, d4
  Pembatasan rentang keluaran mengikuti pipeline
  734 prediksi RH
```

Lima anggota aktif, bukan enam: ridge biasa merupakan kandidat yang dibuang. Jika ingin menyebut enam kandidat, tampilkan ridge biasa sebagai kandidat yang dieliminasi, bukan cabang produksi aktif. Jangan menggambar seluruh ensemble di ruang tekanan uap; hanya anggota `ridge_e` menggunakan target tersebut.

Rumus rekonsiliasi berikut merupakan catatan produksi dan bahan appendix A5. Tidak perlu dibacakan atau ditampilkan besar pada video utama:

`min_z ||z − p||² + 4 ||D1 z − d1||² + ||D4 z − d4||²`

`D1` berarti selisih 30 menit; `D4` selisih empat langkah, yaitu dua jam. Narasi cukup menyebut “menjaga kedekatan dengan level dan dengan perubahan yang diprediksi”. Detail alasan bobot 4:1 dipindah appendix.

### Draft voice-over, bahasa sederhana

> “Kami mulai dari pembacaan sensor, seperti suhu dan kondisi lingkungan lainnya. Sebelum model belajar, data diperiksa, pembacaan yang bermasalah ditangani, dan pola beberapa jam dirangkum.
>
> Selanjutnya, dua kelompok model membantu membaca data. Model linear menangkap hubungan yang lebih sederhana. LightGBM dan CatBoost mempelajari hubungan yang lebih rumit. Lima model yang dipertahankan kemudian digabungkan, dengan bobot yang dipelajari dari hasil pengujian. Kecenderungan prediksi terlalu rendah atau terlalu tinggi juga diperiksa dan dikoreksi sesuai urutan ini.
>
> Bagian tersebut menjawab pertanyaan pertama: berapa kelembapan pada waktu ini?
>
> Model lain menjawab pertanyaan kedua: seberapa besar kelembapan berubah dalam tiga puluh menit dan dua jam?
>
> Kedua jawaban itu kemudian diselaraskan. Prediksi pada setiap waktu tetap memiliki pijakan, sekaligus memperhitungkan perubahan antar-waktu. Hasilnya adalah 734 perkiraan kelembapan yang tersusun sebagai satu rangkaian.”

Durasi rekaman ditakar saat produksi. Istilah besar di video: “pemeriksaan data”, “gabungan model”, “prediksi kelembapan”, “prediksi perubahan”, dan “penyelarasan hasil”. Label algoritma kecil tetap terlihat untuk juri AI/ML.

### Ketahanan saat tampil

- Video MP4 H.264 16:9, idealnya 1080p, **tertanam di PPTX**, bukan tautan streaming. Ini rekomendasi teknis, bukan format yang disebut juknis.
- Subtitle Indonesia agar video tetap bermakna tanpa audio. Hindari musik yang menutupi penjelasan.
- Diagram statis sebagai poster/fallback pada slide yang sama. Presenter menyiapkan penjelasan lisan 60–90 detik jika pemutaran gagal.
- PDF pendamping berisi diagram lengkap, bukan bingkai awal video yang kosong.
- Tes pada perangkat yang akan dipakai, tanpa jaringan. Kepastian audio dan pemutaran mengikuti konfirmasi LO.

## 7. Appendix untuk 24 menit tanya jawab

Rekomendasi **8 slide appendix + 1 referensi**, sehingga file berisi **23 slide total**. Jumlah ini usulan editorial, bukan batas panitia. Referensi dan appendix tidak dipresentasikan berurutan dalam slot utama.

| Slide | Materi | Pertanyaan yang dilayani |
|---|---|---|
| A1 | Kontrak train/test, 24 sensor, target-blind feature selftest | “Ada kebocoran target? Mengapa boleh centered window?” |
| A2 | Rolling-origin, fitting meta, audit maju/nested, overlap fold | “Apakah OOF cukup? Apakah sembilan fold independen?” |
| A3 | Baseline lengkap dan skor per fold | “Mengapa ensemble? Apakah pembandingnya adil?” |
| A4 | Oracle tekanan uap, cara perhitungan dan batas tafsir | “Apakah oracle memakai label? Apa arti resolusi 6,1 jam?” |
| A5 | Objective rekonsiliasi, model increment, bobot 4:1 | “Apakah hanya smoothing? Mengapa 30 menit dan dua jam?” |
| A6 | Bias CatBoost, koreksi OOF, kontrol nol dan arah terbalik | “Mengapa model bias dipertahankan? Koreksinya berasal dari mana?” |
| A7 | Ledger kegagalan dan penggunaan feedback leaderboard | “Seberapa bergantung keputusan pada leaderboard?” |
| A8 | Reproduksi, digest nilai, batas kausal dan evaluasi lanjutan | “Bisa dijalankan ulang? Apa yang dibutuhkan untuk deployment?” |
| R | Referensi yang benar-benar dipakai | Rujukan data/metode/rumus |

### Pola jawaban Q&A

Jawab **inti pertanyaan terlebih dahulu**, kemudian satu bukti, baru batasnya. Target jawaban awal 30–60 detik, bukan langsung monolog tiga menit.

- **“Ini forecast 15 hari sungguhan?”** Targetnya berada pada blok 15,3 hari setelah train. Eksogen sepanjang blok tersedia, sehingga formulasi tepatnya rekonstruksi/prediksi dengan eksogen diketahui. Peramalan langsung memerlukan evaluasi kausal tambahan.
- **“Centered rolling itu leakage?”** Ia memakai eksogen setelah titik prediksi. Dalam kontrak lomba eksogen tersebut tersedia. Fitur tidak memakai target uji. Untuk deployment kausal, centered rolling harus diubah dan dievaluasi ulang.
- **“Apakah 2,82744 berarti akurasi 97,17%?”** Tidak. Itu RMSE dalam poin persentase RH pada slice publik. Ia bukan persentase akurasi dan bukan jaminan setiap titik berjarak maksimal 2,82744.
- **“Menang 9/9 artinya signifikan?”** Menunjukkan arah yang konsisten pada protokol yang dipakai. Blok tumpang tindih, sehingga kemenangan itu tidak diperlakukan sebagai sembilan percobaan independen.
- **“Kenapa tidak pakai deep learning?”** Data latih relatif singkat. Eksperimen MLP/kernel/representasi urutan yang dilaporkan tidak memberi hasil lebih baik. Kesimpulannya terbatas pada kandidat dan setup yang diuji.
- **“Apakah leaderboard dipakai memilih keputusan?”** Bedakan pemilihan model/fitting parameter lewat evaluasi internal dengan feedback publik yang memengaruhi penerimaan atau penolakan koreksi pasca-model. Jangan mengatakan leaderboard tidak pernah memengaruhi keputusan final.
- **“15,8% itu kontribusi increment saja?”** Tidak, itu stack dibanding LightGBM tunggal pada protokol validasi sama. Bukti increment tersendiri memiliki konteks dan angka terpisah.
- **“Mengapa CatBoost dipertahankan meskipun bias?”** Nilai anggota dilihat dari kontribusi gabungan dan keragaman residu, bukan bias sendiri saja. Audit maju mengukur offsetnya; koreksi dipelajari dari OOF. Tunjukkan bukti pada A6.
- **“Apa dampaknya bagi petani?”** Ada potensi untuk redundansi sensor dan analisis mikroklimat. Dampak irigasi, biaya, hasil panen, atau pencegahan penyakit belum diukur oleh eksperimen ini.

## 8. Pembagian pembicara dan latihan

Usulan dua pembicara, nama dapat diputuskan saat latihan:

- **Pembicara A:** slide 1–6, masalah sampai ide fisis.
- **Video:** slide 7. Pembicara B memberi pengantar dan mengambil alur setelah video.
- **Pembicara B:** slide 8–13, evaluasi sampai batas penggunaan.
- **Pembicara A:** slide 14, menutup pertanyaan pembuka.

Total hanya dua perpindahan lisan. Keduanya harus menguasai metode dan data untuk Q&A. Jawaban diarahkan pada orang yang paling menguasai bukti terkait, setelah dipersilakan moderator.

Latihan pertama menguji **alur dan durasi aktual**. Latihan kedua menguji **Q&A**, khususnya centered features, pemasangan meta-model, peran leaderboard, dan attribution eksperimen. Latihan terakhir memakai PPTX final dan video offline.

Jika latihan melewati 14 menit, pangkas detail slide 5 dan 11 terlebih dahulu. Pertahankan problem statement, validasi, bukti perbandingan, batas kausal, dan closing. Jangan mempercepat video untuk menghemat waktu.

## 9. Visual dan daftar produksi

- 16:9 sebagai rekomendasi kerja, sebab juknis tidak menentukan rasio. Satu font sans-serif, isi minimal 20–24 pt, judul 28–32 pt.
- Konten analitis menggunakan latar terang. Hook dan penutup boleh berlatar gelap dengan kontras tinggi. Maksimum tiga warna bermakna: teks, baseline, model utama.
- Satu exhibit utama per slide. Anotasi langsung pada bukti. Hindari screenshot tabel notebook atau seluruh halaman paper.
- Tulis sumber ringkas di footer, misalnya “Paper penyisihan, Tabel pembanding” atau “Ledger submission publik”. Referensi lengkap di R.
- Buat ulang grafik paper dengan label besar. Angka tidak diubah untuk mempercantik cerita.
- Hindari identitas instansi pada slide utama, appendix, metadata yang terlihat saat tampil, voice-over, video, tautan, dan footer.

| Bahan yang sudah tersedia | Untuk slide | Pekerjaan berikutnya |
|---|---|---|
| Ilustrasi rumah kaca dan rujukan UConn | 1 dan 14 | Buat visual skenario; tidak dianggap foto kasus lapangan |
| `paper/figures/01-target-dan-jendela.png` | 2 dan 4 | Buat timeline panggung yang lebih sederhana |
| `paper/figures/02-residu-loo.png`, `11-despiking.png`, `05-audit-dukungan.png` | 5, A1 | Ambil temuan paling relevan; detail ke appendix |
| `paper/figures/03-kurva-oracle.png` | A4 | Simpan eksperimen oracle untuk Q&A teknis |
| `paper/figures/12-klimatologi-diurnal.png` | 6 | Buat ulang grafik pola sehari dengan bahasa sederhana |
| `final_pipeline.py` | 7, A5 | Diagram mengikuti cabang produksi final |
| `paper/figures/06-titik-asal-bergulir.png` | 8, A2 | Perbesar satu fold dan batas waktunya |
| `outputs/baselines_summary.json`, `paper/figures/14-pembanding.png` | 9, A3 | Gunakan pooled RMSE, konsisten di semua label |
| `paper/figures/07-rekonsiliasi-increment.png` | 10, A5 | Simpan bukti blok maju di appendix |
| `paper/figures/08-bias-anggota.png` | 11, A6 | Perjelas tanda bias dan konteks maju |
| `paper/script/tables.py`, tabel histori publik | 10–12, A7 | Pilih pasangan submission yang tepat |
| Notebook bagian reproduksi | A8 | Salin bukti tersimpan dan presisi digest, jangan klaim run baru |

### Status bukti dan koreksi istilah

**Dibaca dan diperiksa untuk kerangka:** sumber UConn Extension untuk skenario rumah kaca; juknis final, paper PDF terkirim, sumber teks/tabel paper, pipeline final, baseline summary, dan grafik yang tersedia sebagai inventaris.

**Hasil eksperimen historis:** 2,82744 publik, perbandingan 5,71/4,81, audit increment dan bias. Angka ditelusuri ke artefak proyek; model tidak dilatih ulang dan leaderboard tidak diakses live pada penyusunan kerangka ini.

**Belum dibuat/divalidasi:** PPTX, voice-over, video, durasi rehearsal, playback perangkat panitia. Target waktu merupakan rencana.

Gunakan **24 kanal sensor**, bukan 25 sensor: waktu adalah kolom tambahan. Gunakan **lima anggota aktif** setelah ridge biasa dibuang. README memuat beberapa ringkasan lama yang tidak sepenuhnya konsisten dengan paper terkirim.

### Checklist sebelum pengumpulan

- [ ] Slide 1 menjelaskan pentingnya kelembapan lewat skenario yang berlandaskan sumber.
- [ ] Slide 2 menghubungkan skenario ke tugas lomba, tanpa mengklaim lokasi atau dampak yang belum diuji.
- [ ] Statistik dan AI/ML masing-masing mempunyai peran yang terlihat pada data, model, dan pengujian.
- [ ] Narasi memakai bahasa sederhana; detail rumus dan istilah berat tersedia di appendix.
- [ ] 14 slide utama bercerita dari masalah sampai jawaban.
- [ ] Tidak ada logo/afiliasi/ucapan asal instansi.
- [ ] RMSE validasi dan publik selalu diberi konteks berbeda.
- [ ] Tidak ada ground truth test buatan, angka dampak lapangan, atau persentase “akurasi” hasil konversi RMSE.
- [ ] Diagram video mengikuti urutan produksi final dan lima anggota aktif.
- [ ] Video 90 detik, tertanam, subtitle terbaca, fallback statis tersedia.
- [ ] Appendix memuat bukti untuk keputusan utama dan kegagalan.
- [ ] Konfirmasi LO tentang video/audio/perangkat dan aturan tambahan TM selesai.
- [ ] File final dibuka dan diuji offline pada perangkat presentasi.
- [ ] Rehearsal aktual maksimal 14 menit termasuk video.
- [ ] Format .pptx dan nama file sesuai §1.c.
- [ ] Unggah sebelum 17 Oktober 2026 pukul 23.59 WIB dan simpan bukti pengumpulan.

## Sumber konteks dan sumber lokal

- [UConn Extension — Foliar Diseases on Greenhouse Tomatoes](https://ipm.cahnr.uconn.edu/foliar-diseases-on-greenhouse-tomatoes/) — hubungan kelembapan tinggi, permukaan tanaman basah, dan penyakit jamur; dasar ilustrasi pembuka. Ini bukan bukti dampak model tim.

- `C:/Users/Raphael Angelo/Downloads/Juknis Grand Final Data Science NSC 2026.pdf`
- `deliverables/NSC26-DS042_Heisenberg_Data Science.pdf` — laporan yang dijadikan acuan isi.
- `paper/script/content.py`, `paper/script/tables.py` — penjelasan dan angka paper.
- `final_pipeline.py` — alur produksi dan komponen aktif.
- `outputs/baselines_summary.json` — hasil pembanding tersimpan.
- `guide_lomba.md` — dipakai untuk mengenali perbedaan aturan lama, bukan menggantikan juknis final.

Ekstraksi lokal juknis: `docs/final/juknis-final-extracted.md`. Ekstraksi paper: `docs/final/paper-extracted.md`. Keduanya alat bantu pencarian; pembacaan dua kolom pada paper PDF dapat tercampur, sehingga narasi/angka juga dicocokkan dengan sumber paper.
