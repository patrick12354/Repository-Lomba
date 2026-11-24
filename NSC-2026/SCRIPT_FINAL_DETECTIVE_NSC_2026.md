# BERKAS 734
## The Missing Humidity Case
**Tim Heisenberg — NSC 2026**

*Script presentasi utama. Teks dalam tanda kurung siku adalah arahan penyampaian, bukan untuk dibacakan.*

*Diselaraskan dengan video final di `Video/output/` (Oktober 2026). Pada slide yang memakai video, angka `[mm,s s]` di depan kalimat adalah detik video ketika visual kalimat itu muncul. Visual selalu muncul di awal kalimat lalu diam, jadi presenter cukup mulai bicara saat visualnya tampil. Semua video tanpa audio; presenter berbicara langsung.*

| Slide | File video | Durasi | Putar |
|---|---|---|---|
| 1 | `slide01-opening-45s.mp4` | 45 s | otomatis saat slide dibuka |
| 3 | `slide03-bukti-70s.mp4` | 70 s | on click, saat mulai bicara |
| 4 | `slide04-petunjuk-60s.mp4` | 60 s | on click |
| 8 | `slide08-ensemble-55s.mp4` | 55 s | on click |
| 9 | `slide09-pola-55s.mp4` | 55 s | on click |
| 10 | `slide10-rekonsiliasi-75s.mp4` | 75 s | on click, setelah pengantar ±5 s |
| 14 | `slide14-case-closed-35s.mp4` | 35 s | on click |

Slide 2, 5, 6, 7, 11, 12 dan 13 tetap slide statis. Video tidak di-loop; frame terakhirnya menjadi latar sampai pindah slide.

---

### ACT I — THE MYSTERY

### SLIDE 1 — A Mysterious Case
**Durasi target: 45 detik**

**Visual (video 45 s, animasi 2D):** Rumah kaca tomat; kamera mendekat ke Pak Anton (label "Pak Anton") → daun yang dipegangnya layu, wajah bingung, gelembung pikiran (tetes air + tanda tanya) → pandangan ke sensor lingkungan, lalu ke buku catatan sensor → buku dibuka: sensor lain penuh titik, baris kelembapan bolong "? ? ?" → halaman disobek dan masuk map **CASE #734**; frame akhir menyerupai slide 1 (kebun di kiri, map BUKTI AWAL di kanan). **734** muncul di 43,0 s dan **>15 HARI** di 43,6 s.

**Script:**

"[00,0 s] Perkenalkan, ini Pak Anton. Pak Anton punya kebun tomat, dan kebunnya dipasangi sensor untuk memantau kondisi lingkungan.

[08,5 s] Nah, suatu pagi, Pak Anton melihat beberapa tanamannya mulai layu. Beliau bingung, kenapa ini bisa terjadi?

[17,9 s] Dugaan pertamanya: jangan-jangan kelembapannya terlalu tinggi. Jadi kami coba cek catatan sensornya untuk memastikan.

[29,1 s] Tapi ternyata ada masalah. Sensor lain seperti suhu dan tekanan masih lengkap catatannya, tapi catatan kelembapannya justru kosong.

[38,6 s] Catatan yang bolong inilah barang bukti pertama kami.

[43,0 s] Totalnya ada **734 nilai kelembapan yang hilang, lebih dari 15 hari.**

**Kami tim Heisenberg, dan hari ini kami akan mengajak Anda memecahkan Berkas 734.**"

*Kalimat 734 sengaja di akhir, karena angka 734 dan >15 HARI baru muncul di 43 s. Kalimat perkenalan tim diucapkan di atas frame akhir yang diam.*

**Transisi:** [Munculkan tampilan berkas investigasi yang terbuka, berubah menjadi timeline dataset.]

*Catatan: Pak Anton dan tanaman layu adalah ilustrasi. Tidak ada klaim bahwa dataset berasal dari kebunnya ataupun bahwa penyebab tanaman layu sudah diketahui.*

---

### SLIDE 2 — Entering the Crime Scene
**Durasi target: 45 detik**

**Visual:** Timeline berisi 2.933 baris latih dan 734 baris uji. Target kelembapan pada periode uji ditandai dengan tanda tanya, sementara sensor lainnya tetap memiliki data.

**Script:**

"Sebagai detektif, langkah pertama kami bukan langsung menebak jawabannya. Kami periksa dulu TKP-nya.

Nah, di TKP ini ada **2.933 catatan yang bisa kami pelajari**. Selain kelembapan, ada **24 sensor lain**, mulai dari suhu, tekanan udara, kondisi tanah, sampai irigasi.

Di periode yang kosong, kelembapannya memang tidak ada. Tapi sensor-sensor lain tetap merekam, jadi jejaknya masih ada.

Artinya, tugas kami bukan meramal tanpa petunjuk. Tugas kami adalah menyusun ulang kelembapan dari jejak sensor lain yang masih tersedia.

Pertanyaannya: **apakah jejak ini cukup untuk mengungkap 734 nilai yang hilang?**

Tapi sebelum kami percaya begitu saja, ada sesuatu yang mencurigakan di barang bukti ini."

**Transisi:** [Sorot anomali ekstrem pada grafik suhu.]

---

### ACT II — THE CLUES

### SLIDE 3 — Contaminated Evidence
**Durasi target: 70 detik**

**Visual (video 70 s, papan investigasi "SEBAGIAN BUKTI PERLU DIPERIKSA"):** Kurva suhu asli `train.csv` (6–7 Agu 2023) dengan lonjakan **54,1 °C** pada 7 Agu 02.00 → dua kemungkinan (lingkungan ekstrem / sensor bermasalah) → titik itu ditutup dan diperkirakan dari empat tetangga dengan kuadratik LOO (**11,0 °C**, residual 43,1 °C) → rasio MAD suhu **5,75**, tekanan **6,86**, kelembapan **1,20** → Hampel selektif hanya pada lonjakan.

**Script:**

"[00,3 s] Waktu kami periksa catatan sensornya, ada beberapa angka yang aneh.

[05,5 s] Contohnya di sini: suhunya tiba-tiba melonjak sampai 54 derajat, jam dua pagi.

[09,9 s] Nah, kemungkinannya cuma dua: lingkungannya memang ekstrem, atau sensornya yang error.

[14,6 s] Tapi kami tidak mau asal buang data yang kelihatan aneh, karena bisa jadi justru itu petunjuknya.

[21,4 s] Jadi kami uji pakai **Leave-One-Out Quadratic Interpolation**.

[25,0 s] Caranya sederhana: satu titik kami tutup dulu, lalu kami tebak nilainya dari empat titik di sekitarnya pakai kurva kuadratik.

[33,0 s] Tebakannya 11 derajat. Selisih tebakan dengan nilai aslinya ini disebut residual.

[37,0 s] Lalu kami hitung **rasio MAD**. Kalau mendekati satu, datanya wajar. Kalau jauh di atas satu, ada lonjakan ekstrem.

[43,8 s] Hasilnya: suhu 5,75, tekanan 6,86, sedangkan kelembapan cuma 1,20.

[49,0 s] Jadi yang bermasalah itu sensor masukannya, bukan kelembapannya.

[53,0 s] Makanya kami pakai **Hampel Filter**, tapi cuma untuk lonjakan ekstremnya saja, bukan untuk meratakan semua data.

[59,8 s] **Barang bukti pertama sudah diperiksa. Tapi ternyata, masih ada petunjuk lain yang tersembunyi di dalam catatan.**"

*Maksudnya (untuk presenter): titik 54 °C ditutup, lalu ditebak dari tetangganya, hasilnya 11 °C. Selisih 43 °C terlalu jauh, jadi itu error sensor, bukan cuaca. Rasio MAD membandingkan sebaran residual biasa (SD) dengan sebaran yang kebal lonjakan (MAD). Kalau keduanya hampir sama (≈1), tidak ada lonjakan. Kalau SD jauh lebih besar, berarti ada beberapa titik ekstrem yang menarik angkanya. Hampel Filter hanya mengganti titik yang terlalu jauh dari median tetangganya; titik lain dibiarkan apa adanya.*

**Istilah yang terlihat pada layar:** Leave-One-Out Quadratic Interpolation · MAD · Hampel Filter.

---

### SLIDE 4 — The Hidden Clue
**Durasi target: 60 detik**

**Visual (video 60 s, papan "CATATAN HARIAN MENYIMPAN PETUNJUK"):** Tujuh kartu indeks agronomi harian (nama kolom asli dataset) → dua jalur persamaan merekonstruksi Tmin harian, dua kurva asli yang hampir berhimpit → SD selisih **0,047 °C** → Tmin sebagai pendekatan titik embun → **RH = 100 × e / es(T)**.

**Script:**

"[00,3 s] Di antara catatan sensor, kami menemukan tujuh indeks agronomi harian.

[07,0 s] Sekilas cuma variabel tambahan. Tapi waktu kami cek rumusnya, ternyata indeks ini dihitung dari suhu maksimum dan suhu minimum harian.

[16,4 s] Jadi rumusnya kami balik. Ini yang kami sebut **Algebraic Inverse Reconstruction**. Suhu minimum kami hitung lewat dua jalur: dari rata-rata harian, dan dari indeks Crop Heat Unit.

[29,6 s] Hasil keduanya hampir sama persis, selisihnya cuma 0,047 derajat. Jadi rekonstruksinya terbukti benar.

[37,8 s] Kenapa ini penting?

[39,6 s] Karena suhu minimum bisa dipakai sebagai pendekatan titik embun. Dan titik embun menunjukkan seberapa banyak uap air di udara.

[44,8 s] Sementara **kelembapan relatif, secara definisi, adalah perbandingan uap air yang ada dengan uap air maksimum pada suhu itu**.

[50,4 s] Jadi fitur ini bukan hasil hitung-hitungan asal. Fitur ini diturunkan langsung dari hukum termodinamika yang mengatur kelembapan.

[55,2 s] Petunjuk tersembunyi sudah ditemukan.

[57,0 s] **Tapi, apakah pola lingkungan saat kasus terjadi masih sama dengan pola yang selama ini kami pelajari?**"

*Maksudnya (untuk presenter): jalur 1 `Tmin = 2 × rata-rata − Tmax`; jalur 2 membalik rumus Ontario CHU. Bahannya beda tapi hasilnya sama, jadi Tmin-nya bisa dipercaya. Tmin dari indeks ini juga lebih bersih daripada Tmin sensor, karena indeks dihitung sebelum data sensor terkontaminasi. Malam hari udara mendingin sampai mendekati titik embun, jadi Tmin ≈ titik embun. Fitur yang masuk ke model: `RH ≈ 100 × es(Tmin) / es(T)`, dengan es = tekanan uap jenuh dan RH = kelembapan relatif (target lomba).*

**Istilah layar:** Algebraic Inverse Reconstruction · Dew Point Proxy · Vapor Pressure.

---

### SLIDE 5 — The Crime Scene Has Changed
**Durasi target: 50 detik**

**Visual:** Dua panel distribusi train dan test. Suhu rata-rata 27,51°C versus 24,64°C. Catatan irigasi berubah dari bervariasi menjadi konstan. Beberapa fitur diberi tanda tidak dipakai.

**Script:**

"Ternyata, tidak.

Waktu kami bandingkan data yang kami pelajari dengan periode yang harus ditebak, kondisinya ternyata cukup berbeda.

Suhu rata-ratanya turun, dari 27,51 jadi 24,64 derajat. Bahkan data irigasi yang tadinya naik-turun, di periode tebakan malah diam, konstan.

Nah, ini namanya **Distribution Shift**. Artinya, data yang mau ditebak tidak mirip lagi dengan data yang dipakai untuk belajar.

Bahayanya, model bisa jago di kondisi lama, tapi gagal waktu ketemu kondisi baru. Seperti murid yang hafal soal latihan, lalu bingung waktu soal ujiannya beda.

Makanya kami lakukan **Feature Distribution Analysis**, yaitu kami cek satu per satu, fitur mana yang berubah drastis. Hasilnya, fitur tanah dan irigasi yang tidak stabil kami keluarkan.

Jadi sekarang ada dua tantangan: barang buktinya belum sempurna, dan TKP-nya sudah berubah.

**Karena itu, kami butuh lebih dari satu cara untuk membaca petunjuknya.**"

*Maksudnya (untuk presenter): fitur yang di periode uji perilakunya beda jauh dari periode latih justru bisa menyesatkan model, karena model belajar hubungan yang tidak berlaku lagi. Irigasi yang konstan juga tidak memberi informasi apa-apa di periode uji. Jadi lebih aman fitur itu dibuang.*

---

### ACT III — THE INVESTIGATION

### SLIDE 6 — Assembling the Investigation Team
**Durasi target: 65 detik**

**Visual:** Lima kartu model disusun seperti tim investigasi. Setiap kartu memiliki spesialisasi, bukan label tersangka.

**Script:**

"Sekarang kami mulai menyusun tim investigasinya.

Tapi kami tidak mau asal coba banyak algoritma lalu ambil yang skornya paling bagus. Setiap model harus punya alasan kenapa dia ada di tim.

Pertama, **LightGBM dengan Huber Loss**. Ini model utama kami. Huber Loss membuat model tidak terlalu terpengaruh oleh kesalahan yang ekstrem.

Kedua, **CatBoost Huber**. Cara belajarnya beda dari LightGBM, jadi kesalahan yang dia buat juga beda.

Ketiga, **ElasticNet**. Ini model linear yang sederhana. Gunanya, waktu kondisinya berubah seperti di slide tadi, model linear masih bisa mengikuti trennya.

Keempat, **Ridge Regression berbasis tekanan uap**. Model ini memakai langsung rumus fisika kelembapan yang tadi kami temukan.

Dan terakhir, **LightGBM dengan L2 Loss**, yang justru sensitif terhadap kesalahan besar, jadi dia tidak membiarkan kesalahan besar lolos.

Nah, yang menarik, CatBoost kalau sendirian bukan yang terbaik. Tapi kesalahannya beda arah dengan model utama, jadi kalau digabung, mereka bisa saling menutupi.

**Pertanyaannya: bagaimana kami membuktikan bahwa gabungan ini benar-benar membantu, bukan cuma bikin sistemnya makin ribet?**"

*Maksudnya (untuk presenter): Huber Loss = untuk kesalahan kecil dihukum kuadrat, untuk kesalahan besar dihukum linear, jadi outlier tidak mendominasi. L2 Loss = semua kesalahan dihukum kuadrat. Model berbasis pohon (LightGBM, CatBoost) tidak bisa menebak di luar rentang data latihnya, sedangkan model linear bisa, dan ini penting karena suhu di periode uji lebih rendah. Prinsip tim: model yang kesalahannya berbeda lebih berguna digabung daripada model yang sama-sama bagus tapi salahnya di tempat yang sama.*

**Istilah layar:** Gradient Boosting · Huber Loss · ElasticNet · Ridge · Model Diversity.

---

### SLIDE 7 — Testing Their Alibis
**Durasi target: 65 detik**

**Visual:** Timeline bergulir. Bagian masa lalu bertanda training, blok 15 hari berikutnya bertanda validation. Sembilan titik awal pengujian. Rumus RMSE sederhana di sisi kanan.

**Script:**

"Dalam investigasi, setiap dugaan harus diuji. Begitu juga model kami.

Kami tidak pakai **Random Cross-Validation**, karena data kami berurutan waktu. Data jam 2 dan jam 2.30 itu hampir kembar. Kalau diacak, yang satu masuk latihan, yang satu masuk ujian. Jadinya seperti nyontek: skornya bagus, padahal tidak.

Jadi kami pakai **Rolling-Origin Cross-Validation**.

Caranya: model belajar dari data masa lalu, lalu diuji di 15 hari berikutnya. Persis seperti tantangan aslinya. Ini kami ulang dari sembilan titik awal yang berbeda.

Untuk mengukur kesalahannya, kami pakai **RMSE, Root Mean Squared Error**. Sederhananya, rata-rata seberapa jauh tebakan kami meleset. Makin kecil, makin bagus.

Hasil tebakan dari tiap ujian kami simpan, namanya prediksi **Out-of-Fold** atau OOF. Prediksi inilah yang kami pakai untuk mengatur penggabungan model, bukan tebakan pada data yang sudah dihafal.

Satu catatan: sembilan ujian ini sebagian saling tumpang tindih. Jadi hasilnya kami baca sebagai bukti bahwa model konsisten, bukan sembilan percobaan yang benar-benar terpisah.

**Setelah semua kandidat diuji, kami menemukan bahwa cara menggabungkan mereka ternyata sama pentingnya dengan modelnya sendiri.**"

*Maksudnya (untuk presenter): datanya per 30 menit dan autokorelasi lag-1-nya 0,979, jadi baris yang bersebelahan hampir kembar. Rolling-origin: 9 lipatan, tiap lipatan maju 2 hari, minimal 30 hari data latih, validasi 15 hari. Karena majunya cuma 2 hari sedangkan jendelanya 15 hari, jendela validasinya banyak yang beririsan, makanya disebut tumpang tindih. RMSE = akar dari rata-rata (tebakan − asli)², jadi kesalahan besar dihukum lebih berat.*

---

### SLIDE 8 — Combining the Evidence
**Durasi target: 55 detik**

**Visual (video 55 s, papan "WAKTU MEMBANTU PENGGABUNGAN MODEL"):** Lima kartu model → **tiga pita waktu** dalam sehari (ilustrasi, tanpa jam batas) → satu NNLS per pita dengan bobot ≥ 0 (benang sama tebal; bobot asli tidak digambar) → *shrinkage* → kontrol acak dengan parameter setara: perbaikan **0,080** (per waktu) vs **0,007** (acak).

**Script:**

"[00,3 s] Kami menemukan satu pola menarik.

[02,6 s] Model yang bagus pada satu bagian hari belum tentu paling akurat di bagian hari yang lain.

[08,6 s] Karena itu, kami menggunakan **Time-Banded Ensemble dengan Non-Negative Least Squares, atau NNLS**.

[12,5 s] Sederhananya, kami mencari kombinasi bobot model yang meminimalkan kesalahan, dengan syarat bobotnya tidak negatif.

[17,8 s] Bobot ini kami pelajari secara terpisah berdasarkan bagian waktu dalam sehari, lalu kami beri *shrinkage* agar tidak terlalu mengikuti data validasi.

[25,0 s] Tetapi kami perlu memastikan satu hal: apakah peningkatannya benar-benar berasal dari informasi waktu, atau hanya karena jumlah parameter bertambah?

[31,9 s] Kami mengujinya dengan **Equal-Parameter Random Control**.

[34,6 s] Hasilnya, pembagian berdasarkan waktu memberikan perbaikan RMSE sebesar 0,080, sedangkan pembagian acak dengan kompleksitas setara hanya 0,007 dalam audit validasi bersarang.

[42,4 s] Artinya, informasi waktu memang membantu.

[44,8 s] **Sepertinya kasus ini hampir selesai. Namun ketika kami memeriksa kesalahan prediksinya satu per satu, muncul petunjuk yang jauh lebih besar.**"

---

### ACT IV — THE BREAKTHROUGH

### SLIDE 9 — The Pattern Nobody Noticed
**Durasi target: 55 detik**

**Visual (video 55 s, papan "KESALAHAN MASIH MEMILIKI POLA WAKTU"):** Deret residual (ilustrasi pola, diberi label) dengan titik-titik yang meleset berturut-turut ke arah sama → angka besar **lag-1 ≈ 0,93** → dua kartu: prediksi level (pin per titik) vs prediksi increment (busur 30 menit dan tautan 2 jam). Strip bawah menjadi jembatan ke slide 10.

**Script:**

"[00,3 s] Setelah mendapatkan prediksi gabungan, kami tidak langsung puas dengan skor RMSE.

[05,0 s] Kami memeriksa pola residualnya melalui **Residual Autocorrelation Analysis**.

[08,6 s] Dan hasilnya sangat menarik.

[10,7 s] Ketika satu titik diprediksi terlalu rendah, titik-titik di sekitarnya cenderung ikut diprediksi terlalu rendah.

[16,5 s] Autokorelasi residual pada lag pertama mencapai sekitar 0,93.

[20,0 s] Ini menunjukkan bahwa kesalahan model masih memiliki struktur waktu yang kuat.

[24,7 s] Dari sini, muncul hipotesis baru.

[27,2 s] Selama ini, model kami berfokus memprediksi **berapa nilai kelembapan pada setiap titik**.

[32,2 s] Tetapi bagaimana dengan **seberapa besar kelembapan berubah di antara dua titik waktu**?

[37,3 s] Untuk mengujinya, kami membangun **Increment Prediction Model**, yang secara khusus mempelajari perubahan kelembapan dalam interval 30 menit dan dua jam.

[44,1 s] Sekarang kami memiliki dua jawaban: prediksi nilainya, dan prediksi perubahannya.

[48,4 s] **Masalahnya, kedua jawaban tersebut belum tentu saling cocok.**"

---

### SLIDE 10 — Reconstructing the Timeline
**Durasi target: 85 detik, termasuk video 75 detik**

**Visual (video 75 s, storyline):** Rumah kaca slide 1 (Pak Anton menatap sensor, data terkirim) → whip pan ke papan gabus. Catatan sensor "? ? ?" bercabang ke kartu **Level Prediction** (pin bundar abu per titik) dan **Increment Prediction** (benang putus-putus: 4 × 30 menit dan satu tautan 2 jam) → kaca pembesar di tangan Pak Anton memperlihatkan dua estimasi yang tidak cocok, cap **BELUM KONSISTEN** → kartu **TEMPORAL RECONCILIATION** + dua kriteria → pin merah dan benang merah bergerak serentak (tether ke posisi awal) → catatan "posisi + dinamika, bukan smoothing, dua sumber" → gulungan kertas grafik dibuka berisi **734 prediksi asli**, titik lalu disambung menjadi satu lintasan; celah "? ? ?" terisi garis merah. Titik level/increment/WLS adalah ilustrasi mekanisme (diberi label di layar); kurva 734 titik adalah prediksi submission asli.

**Pengantar presenter (±5 s, sebelum video diputar):**

"Prediksi level memberi tahu posisinya. Prediksi increment memberi tahu pergerakannya. Inilah cara kami merekonstruksi keduanya."

**Narasi selama video (±75 s).** Video yang diputar tidak bersuara; presenter membacakan narasi berikut mengikuti cue detik. Versi dengan VO ElevenLabs bisa dirender ulang dari `Video/script/slide10-rekonsiliasi` bila dibutuhkan.

"[00,4 s] Dari data sensor yang sama, kami membangun dua jalur prediksi yang berbeda.

[04,4 s] Jalur pertama disebut **Level Prediction**, yang memperkirakan nilai kelembapan pada setiap titik waktu.

[10,4 s] Jalur kedua disebut **Increment Prediction**, yang memperkirakan perubahan kelembapan untuk interval 30 menit dan dua jam.

[18,2 s] Namun, kedua prediksi ini dapat menghasilkan jawaban yang berbeda.

[22,1 s] Sebagai contoh, selisih antara dua prediksi level belum tentu sama dengan perubahan yang diperkirakan model increment.

[29,4 s] Untuk menyelesaikannya, kami menggunakan **Temporal Reconciliation berbasis Weighted Least Squares**.

[37,1 s] Prinsipnya adalah mencari satu lintasan kelembapan yang tetap dekat dengan prediksi level, sekaligus meminimalkan ketidaksesuaian terhadap prediksi perubahan.

[45,5 s] Melalui optimasi ini, seluruh titik disesuaikan secara bersama-sama.

[49,8 s] Prediksi level menjaga posisi setiap titik, sementara prediksi increment mempertahankan dinamika perubahan antarwaktu.

[56,3 s] Hasilnya bukan sekadar *smoothing* atau menghaluskan grafik.

[59,3 s] Kami merekonstruksi rangkaian prediksi berdasarkan dua sumber informasi yang saling melengkapi.

[65,0 s] **Kini 734 titik tidak lagi diperlakukan sebagai prediksi terpisah, melainkan sebagai satu lintasan yang saling terhubung.**"

**Transisi presenter — ±5 detik:**

"Mekanismenya sudah jelas. Tapi dalam investigasi, sebuah teori tetap harus dibuktikan dengan hasil pengujian."

---

### SLIDE 11 — The Breakthrough Is Real
**Durasi target: 60 detik**

**Visual:** Grafik perbandingan prediksi sebelum dan sesudah rekonsiliasi, lalu skor publik 3,02586 → 2,86595.

**Script:**

"Untuk memastikan rekonstruksi tadi benar-benar membantu, kami melakukan dua pemeriksaan.

Pertama, kami membandingkan akurasi prediksi perubahan dengan perubahan yang langsung dihitung dari prediksi level.

Pada interval 30 menit, RMSE model increment mencapai 1,81, lebih baik daripada 1,91 dari prediksi level.

Untuk interval dua jam, selisih keunggulannya lebih kecil.

Karena itu, kedua horizon tidak kami perlakukan sama. Dalam rekonsiliasi, kami memberi bobot relatif lebih besar pada informasi 30 menit.

Kedua, kami memeriksa dampaknya pada hasil akhir.

Setelah **Temporal Reconciliation**, skor RMSE publik membaik dari **3,02586 menjadi 2,86595**, turun sekitar 0,160.

Arah perbaikan juga konsisten pada tiga blok audit maju yang dilaporkan.

Ini menjadi terobosan terbesar dalam investigasi kami.

**Namun masih ada satu hal yang belum dijelaskan oleh RMSE: apakah seluruh model melakukan kesalahan dengan arah yang sama?**"

---

### SLIDE 12 — The Hidden Bias
**Durasi target: 65 detik**

**Visual:** Grafik residual CatBoost dengan garis nol. In-sample bias −0,006 %RH dibanding audit maju −2,89 %RH. Panah menuju koreksi parsial.

**Script:**

"RMSE mengukur seberapa besar kesalahan prediksi, tetapi tidak menunjukkan apakah model cenderung menebak terlalu tinggi atau terlalu rendah.

Karena itu, kami melakukan **Residual Bias Analysis**.

Hasilnya mengungkap temuan lain.

Salah satu anggota ensemble, CatBoost, hampir tidak memiliki bias pada data belajar, hanya sekitar minus 0,006 persen kelembapan relatif.

Namun pada audit maju, biasnya mencapai minus 2,89. Artinya, prediksi CatBoost cenderung terlalu rendah pada periode tersebut.

Untuk menanganinya, kami menggunakan **Partial Bias Correction**.

Besar koreksinya dihitung dari prediksi Out-of-Fold, bukan dengan menyalin besar bias dari audit maju. Kami hanya menerapkan separuh dari estimasi koreksi tersebut untuk mengurangi risiko overcorrection.

Kami juga melakukan **Negative Control**, yaitu mencoba koreksi dengan arah yang salah dan pada model yang hampir tidak bias.

Keduanya tidak memberikan perbaikan.

Dengan demikian, koreksi ini memiliki dasar yang terukur, bukan sekadar menambahkan angka sampai skor terlihat lebih bagus.

**Tetapi sebelum menutup investigasi, kami juga harus memastikan bahwa semua temuan tambahan benar-benar layak dipertahankan.**"

---

### SLIDE 13 — The Rejected Evidence
**Durasi target: 45 detik**

**Visual:** Satu kartu eksperimen tambahan dicap "REJECTED". Skor 2,86595 → 2,93028. Panel kecil "Deployment Limitations".

**Script:**

"Dalam investigasi ini, tidak semua hipotesis berhasil.

Salah satu paket tambahan untuk prediksi increment justru memperburuk RMSE publik dari 2,86595 menjadi 2,93028.

Karena tidak memberikan manfaat, pendekatan itu kami tinggalkan.

Ini penting, karena dalam data science, kompleksitas yang lebih tinggi tidak selalu menghasilkan model yang lebih baik.

Kami juga menyadari batas penelitian ini.

Pada kompetisi, seluruh sensor selain target tersedia selama periode prediksi. Untuk penerapan real-time, sistem harus diuji kembali menggunakan informasi yang benar-benar sudah tersedia pada waktu pengambilan keputusan.

Selain itu, kami belum menguji dampaknya secara langsung terhadap hasil panen ataupun kesehatan tanaman.

Jadi, **kesimpulan kami dibatasi pada kemampuan merekonstruksi kelembapan, berdasarkan evaluasi yang telah dilakukan.**

Dan sekarang, seluruh bukti telah terkumpul."

---

### ACT V — CASE CLOSED

### SLIDE 14 — Case Closed: Berkas 734
**Durasi target: ±40 detik (video 35 detik)**

**Visual (video 35 s):** Meja detektif di bawah lampu. Tangan Pak Anton meletakkan laporan akhir, **2,82744** dicap di detik 1 → sticky note validasi ditempel: **5,71 → 4,81**, lalu **≈15,8 % lebih baik · 9/9 fold** → kamera mundur ke seluruh meja: lima kartu **PELAJARAN** berserakan → satu per satu diarsipkan ke map **CASE #734** dari slide 1, dengan tab SENSOR · FISIKA · SHIFT · ENSEMBLE · LINTASAN → laporan masuk paling atas, map ditutup (flip 3D) bersamaan dengan kutipan → kembali ke kebun Pak Anton: celah "? ? ?" di catatan sensor terisi garis merah prediksi asli (**734 nilai direkonstruksi**), tanaman layu kembali segar, sensor mengirim data, Pak Anton tersenyum → cap **CASE CLOSED** menghantam layar, Pak Anton mengacungkan jempol → "Tim Heisenberg · NSC 2026 — Terima kasih".

Lima pelajaran di kartu:

| Tab | Pelajaran | Bukti |
|---|---|---|
| SENSOR | Saksi pertama belum tentu jujur. | lonjakan 54,1 °C → Hampel |
| FISIKA | Hukum alam ikut bersaksi. | RH = 100 × e / es(T), Tmin dua jalur |
| SHIFT | Masa depan tak mirip masa lalu. | periode uji ≠ latih |
| ENSEMBLE | Satu saksi tidak pernah cukup. | 5 model, NNLS, bobot ≥ 0 |
| LINTASAN | Kesalahan pun punya pola. | lag-1 ≈ 0,93 → level + increment |

**Script:**

"[00,0 s] Setelah seluruh pemeriksaan, rekonstruksi, dan pengujian, inilah solusi terbaik yang kami peroleh untuk Berkas 734.

**RMSE publik akhir: 2,82744.**

[05,4 s] Dalam sembilan rolling-origin validation yang sama, solusi lengkap kami menurunkan RMSE dari 5,71 pada baseline LightGBM menjadi 4,81.

[09,4 s] Artinya, terdapat perbaikan sekitar **15,8 persen**, dengan hasil lebih baik pada kesembilan fold tersebut.

[12,6 s] Namun bagi kami, temuan terpenting bukan hanya angka akhirnya.

[14,7 s] Kami belajar bahwa solusi yang baik dimulai dengan memahami bukti, bukan sekadar memilih algoritma.

[17,9 s] Saksi pertama belum tentu jujur. Hukum alam ikut bersaksi. Masa depan tidak selalu mirip masa lalu. Satu saksi tidak pernah cukup. Dan kesalahan pun punya pola.

[23,0 s] [Diam sejenak, laporan masuk ke map.]

[24,1 s] **Karena dalam sebuah investigasi, petunjuk terpenting bukan selalu yang paling terlihat. Melainkan yang berhasil kita pahami.**

[27,6 s] 734 nilai kelembapan yang semula tidak diketahui kini memiliki rekonstruksi yang dapat diuji dan dipertanggungjawabkan.

[30,6 s] **Berkas 734: Case Closed.**

[32,0 s] Kami Heisenberg. Terima kasih."

*Kalimat [17,9 s] mengikuti lima kartu pelajaran yang diarsipkan (satu kartu per detik). Bila ingin versi teknis, ganti dengan: "Kami memeriksa kualitas sensor, merekonstruksi informasi fisika, mengantisipasi distribution shift, menggabungkan model yang saling melengkapi, lalu menggunakan pola residual untuk menemukan informasi yang sebelumnya terlewat." Urutannya sama dengan kartu.*

---

**END OF MAIN PRESENTATION**