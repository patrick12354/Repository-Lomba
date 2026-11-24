# Reevaluasi motion — Berkas 734

Catatan pembaruan: keputusan format final ada di `KEPUTUSAN_FINAL_VIDEO_BERKAS_734.md`. Setelah dibandingkan dengan usulan pengguna, slide 1 dan 10 dipilih untuk video; slide 3, 4, 8, 9 untuk animasi mengikuti klik; slide 14 tetap penutupan native. Detail teknis di bawah merupakan rancangan sebelumnya.

Dasar: script baru `SCRIPT_FINAL_DETECTIVE_NSC_2026.md`, 14 visual yang dibuat untuk script tersebut, serta versi PowerPoint editable yang dirender dan diperiksa. Dokumen ini merupakan rancangan produksi. Belum menambahkan animasi atau video ke PPTX.

## Keputusan yang disarankan

**Satu video utama: slide 10, durasi 75 detik.** Slide 3, 7, 8, dan 9 memperoleh manfaat besar dari animasi penjelas di dalam slide. Slide 2, 4, dan 12 cukup memakai reveal bertahap sesuai narasi. Slide 11 dan 14 harus memberi waktu untuk membaca bukti, sehingga tidak membutuhkan video.

Alasannya: motion paling berguna ketika penonton perlu melihat sesuatu disembunyikan, diperkirakan, bergeser dalam waktu, dibandingkan, atau disesuaikan bersama. Angka hasil memerlukan perhatian yang stabil. Gerak menjadi cara menjelaskan mekanisme, bukan menambah durasi tontonan.

Paket utama: video slide 10 dan animasi slide 3, 7, 8, 9. Paket pelengkap: reveal slide 2, 4, 12. Durasi animasi di bawah berlangsung **di dalam durasi bicara yang sudah ada**, bukan ditambahkan sesudah script. Video 75 detik sudah termasuk dalam target slide 10 sebesar 85 detik. Total target script tetap 13 menit 40 detik sampai rehearsal membuktikan durasi aktual.

## Evaluasi seluruh slide

| Slide | Pilihan | Manfaat gerak | Keputusan |
|---|---|---|---|
| 1 — Misteri | Reveal map dan bukti 4–6 detik | Mengantar mata dari persoalan kebun ke data yang hilang | Opsional; tanpa video karakter panjang |
| 2 — TKP | Native build 10 detik | Memperjelas bahwa hanya target yang kosong saat test | Pelengkap |
| 3 — Bukti terkontaminasi | Native animation 20 detik | Prosedur leave-one-out menjadi terlihat | Prioritas tinggi |
| 4 — Petunjuk fisika | Native build 18 detik | Menunjukkan dua jalur invers dan alasan Tmin berguna | Pelengkap |
| 5 — Shift | Reveal perbandingan dan keputusan | Dua mean serta irigasi sudah jelas sebagai exhibit statis | Tanpa video |
| 6 — Tim model | Reveal anggota sesuai narasi | Mengikuti penjelasan peran, tanpa menambah mekanisme baru | Build sederhana |
| 7 — Uji alibi | Native animation 20 detik | Menjelaskan bagaimana satu fold berubah menjadi sembilan | Prioritas tinggi |
| 8 — Penggabungan | Native animation 22 detik | Memperlihatkan bobot per pita, regularisasi, dan kontrol | Prioritas tinggi |
| 9 — Pola residual | Native animation 16 detik | Membuat momen penemuan pola dan hipotesis increment terasa | Prioritas tinggi |
| 10 — Rekonsiliasi | Video 75 detik | Mismatch, kompromi, dan penyesuaian bersama sulit ditangkap dari gambar tunggal | Prioritas tertinggi |
| 11 — Bukti hasil | Reveal Bukti 1, lalu Bukti 2 | Membantu pemisahan validasi OOF dan publik | Tetap tenang; tanpa video |
| 12 — Bias | Native build 18 detik | Menjelaskan perbedaan diagnosis audit dan estimasi koreksi OOF | Pelengkap |
| 13 — Eksperimen ditolak | Reveal hasil, cap, kemudian batas penerapan | Membantu penutupan argumentasi | Build sederhana |
| 14 — Case Closed | Reveal publik, validasi, cap penutup | Memberi urutan perhatian pada kesimpulan | Frame akhir statis |

Jika semua segmen harus dibuat sebagai MP4, kandidat yang layak selain slide 10 adalah 3, 7, dan 8. Namun native animation lebih nyaman untuk ketiganya karena presenter dapat menahan tiap langkah sesuai penjelasan dan pertanyaan juri. Slide 9 bisa menjadi klip pendek pembuka slide 10, tetapi jangan mengulang penjelasan yang sudah disampaikan.

## Bahasa visual dan aturan gerak

Tetap dalam dunia Berkas 734: latar arang, lembar krem, tinta gelap, merah sebagai penanda fokus, dan alat investigasi yang punya fungsi. Pada video, kertas menjadi bidang kerja yang stabil. Judul, sumbu, legend, dan sumber tidak ikut mengambang.

- Kanvas video 1920 × 1080, 16:9. Margin aman sekitar 96 px. Cocok dengan rasio PPTX.
- Headline Impact 56–68 px; label Arial/Georgia 30–40 px; angka utama 100–150 px; caption sumber minimal 22–24 px.
- Warna: arang `#191919`, krem `#F3EBD9`, tinta `#25231F`, merah `#9E241F`, abu `#766F63`. Biru atau olive boleh membedakan sumber, dengan simbol/jenis garis sebagai pembeda tambahan.
- Reveal kelompok: 0,35–0,55 detik. Draw garis: 0,6–1,0 detik. Pergeseran titik penting: 1,2–2,0 detik. Kamera bergerak hanya bila perlu memperbesar hubungan yang sedang dibahas.
- Gunakan easing halus tanpa bounce pada data. Angka muncul langsung pada nilai final, bukan count-up melalui nilai sementara.
- Kaca pembesar hanya bergerak sekali menuju bukti yang diperiksa, lalu diam. Hindari loop yang terus berjalan ketika presenter menjelaskan.
- Elemen yang belum dibahas boleh redup; label yang diperlukan untuk memahami chart tetap terbaca.
- Pada akhir setiap build, tahan frame yang lengkap. Presenter harus bisa berhenti tanpa memperoleh layar kosong atau diagram setengah jadi.
- Native build tetap berada di **14 slide yang sama**. Jangan menambah slide duplikat atau hidden slides demi Morph. Gunakan Appear, Fade, Wipe, emphasis, atau motion path yang diperlukan.

Nama gerak yang dipakai: reveal bertahap, draw-on untuk hubungan, highlight satu fokus, dan perpindahan titik secara serentak. Hindari gerak kamera 3D pada grafik karena mengubah persepsi jarak dan membuat label sulit dibaca.

## Slide 10 — Video utama: dua jawaban menjadi satu lintasan

### Apa yang harus diperbaiki dari versi statis

Diagram saat ini menjelaskan adanya dua masukan dan sebuah kompromi. Video harus memperlihatkan **mengapa keduanya belum cocok, bagian apa yang diubah, serta bagaimana semua titik terhubung dalam penyelesaian yang sama**. Timbangan cukup menjadi cue singkat. Exhibit utama adalah titik dan hubungan antartitik.

### Komposisi

Bagian atas 15% untuk judul. Area tengah 65% menjadi satu timeline besar, sekitar x=250–1650 dan y=330–780. Bagian bawah 15% untuk takeaway dan keterangan ilustrasi. Awalnya ada dua jalur prediksi dalam dua lajur, lalu kedua lajur berpindah menjadi satu bidang kerja dengan koordinat waktu yang sama.

Mulai dengan **lima simpul** pada interval 30 menit. Horizon 30 menit menghubungkan dua tetangga; horizon dua jam menghubungkan simpul pertama dan kelima. Tidak perlu nilai RH atau tanggal buatan.

Kode visual: level awal berupa lingkaran kosong abu; estimasi increment berupa hubungan putus-putus dengan label horizon; hasil rekonsiliasi berupa lingkaran isi merah dan lintasan tinta/merah. Bentuk tetap berbeda ketika dicetak tanpa warna.

### Storyboard 75 detik

| Detik video | Adegan dan gerak | Teks layar | Cue VO dari script |
|---|---|---|---|
| 0–7 | Catatan sensor terbuka. Satu sumber bercabang menjadi dua jalur; judul dan arah waktu diam | `Level Prediction` / `Increment Prediction` | “Dari data sensor yang sama…” |
| 7–17 | Lima titik level muncul satu per satu, lalu diam. Masing-masing menempati posisi berbeda sepanjang waktu | `Nilai pada setiap waktu` | “Jalur pertama… nilai kelembapan…” |
| 17–27 | Hubungan tetangga 30 menit digambar. Hubungan dua jam muncul lebih tinggi, melintasi empat interval | `30 menit` / `2 jam` | “Jalur kedua… perubahan…” |
| 27–38 | Kamera mendekat ke dua simpul. Selisih posisi level dan perkiraan increment ditunjukkan sebagai dua ukuran yang berbeda; bracket merah menandai mismatch | `Dua estimasi belum konsisten` | “Selisih antara dua prediksi level…” |
| 38–48 | Kamera kembali. Bingkai optimasi mencakup seluruh simpul. Dua kriteria muncul berurutan, bukan sebagai matriks padat | `Weighted Least Squares`; `Dekat dengan level`; `Sesuai dengan perubahan` | “Mencari satu lintasan…” |
| 48–62 | Semua titik final bergerak **bersama** ke kompromi. Posisi level awal tetap sebagai lingkaran abu. Sebagian titik naik, sebagian turun; hubungan antartitik ikut diperbarui | `Seluruh titik disesuaikan bersama` | “Melalui optimasi ini…” |
| 62–69 | Gerak selesai. Tahan pasangan titik awal/final beserta hubungan 30 menit dan dua jam. Perlihatkan posisi dan dinamika sama-sama dipertimbangkan | `Posisi + dinamika perubahan` | “Prediksi level menjaga posisi…” |
| 69–75 | Kamera melebar. Diagram berubah menjadi representasi rantai simpul yang lebih panjang, tanpa skala RH. Angka 734 muncul. Tahan akhir | `734 titik, satu lintasan terhubung` | “Kini 734 titik…” |

Frame akhir harus tetap terlihat sepanjang transisi presenter menuju slide 11. Durasi keseluruhan slide: pengantar 5 detik, video 75 detik, transisi sekitar 5 detik, sesuai script.

### Detail yang membuat mekanisme tepat

1. Pada close-up mismatch, bandingkan selisih level dengan estimasi increment pada pasangan waktu yang sama. Jangan membandingkan dua titik dari interval berbeda.
2. Prediksi increment digambarkan sebagai perubahan, bukan sebagai titik level kedua yang ditempatkan pada sumbu RH.
3. Titik level awal tidak hilang ketika rekonsiliasi dimulai. Tether tipis memperlihatkan seberapa jauh hasil bergeser dari sumber awal.
4. Jangan mengubah semua titik dengan offset yang sama atau membuat lintasan menjadi garis datar. Tujuannya bukan sekadar koreksi bias atau smoothing.
5. Weighted Least Squares menghasilkan kompromi. Tidak semua hubungan harus dipenuhi persis, dan tidak ada klaim error menjadi nol.
6. Untuk produksi, posisi akhir contoh dihitung dari satu contoh WLS yang dibekukan, bukan dipilih agar kurva tampak lebih mulus. Nilai contoh dilabeli skematis dan tidak dianggap hasil kompetisi.
7. Perpindahan menuju posisi akhir adalah interpolasi visual untuk menjelaskan perubahan. Jangan memberi label “iterasi 1, 2, 3” karena itu dapat menggambarkan algoritma yang berbeda dari penyelesaian yang digunakan.
8. Rantai 734 pada akhir adalah visual hubungan simpul. Jika memakai kurva prediksi aktual, ambil dari submission yang tepat dan beri label `Prediksi`; tidak menampilkan aktual target test.

### Audio, playback, dan editability

VO mengikuti script. Efek bunyi bersifat opsional dan sangat ringan: kertas dibuka saat awal, klik halus saat hubungan ditandai. Narasi harus tetap paling jelas; tidak perlu musik dramatis sepanjang penjelasan optimasi.

Video diputar sekali, tanpa loop. Native diagram slide 10 tetap disimpan sebagai fallback yang editable. MP4 adalah media raster; untuk mengubah isi animasinya, sumber komposisi perlu diedit dan dirender ulang. Jangan mengklaim titik dalam MP4 dapat diedit langsung sebagai objek PowerPoint.

Jika diproduksi dengan HyperFrames, gunakan satu timeline yang dapat di-seek, posisi deterministik, serta sumber data yang dibekukan. Kertas/alat investigasi memakai aset ilustrasi; grafik dan angka dibuat secara deterministik agar konsisten antarframe.

## Slide 3 — Memperlihatkan satu titik diperiksa

**Pilihan:** native animation, rangkaian sekitar 20 detik dengan empat build yang dapat ditahan presenter. Jika berupa klip, tanpa VO tambahan; presenter berbicara langsung.

**Komposisi:** kiri 65% untuk grafik suhu; kanan 30% untuk tiga rasio residual. Sumbu dan posisi empat tetangga tidak bergeser. Nilai asli merah dan perkiraan kosong berada pada x yang sama.

| Waktu lokal | Visual | Cue narasi |
|---|---|---|
| 0–4 | Kurva muncul, satu spike dilingkari. Rasio kanan belum dibuka | “Beberapa angka terlihat tidak masuk akal…” |
| 4–8 | Titik pusat asli memudar menjadi ghost; empat tetangga ditonjolkan, dua sebelum dan dua sesudah | “Satu titik kami sembunyikan…” |
| 8–12 | Kurva kuadratik dari tetangga digambar. Lingkaran kosong menunjukkan perkiraan titik pusat | “…menggunakan pola empat titik…” |
| 12–16 | Titik asli dibuka kembali. Bracket vertikal muncul antara asli dan perkiraan | “Selisih… disebut residual” |
| 16–20 | Rasio 5,75 / 6,86 / 1,20 dibuka. Callout `Hampel selektif` menyusul pada cue filtering | “Gangguan ekstrem lebih dominan…” |

Rasio tetap menjadi grafik native dengan sumber laporan. Pada contoh Hampel, ganti hanya titik yang ditandai; titik lain tidak ikut bergeser. Jangan membuat animasi menyingkirkan semua pembacaan yang tampak berbeda sebelum pemeriksaan.

Urutan grafik kuadratik harus menggunakan titik pusat yang disembunyikan **hanya sebagai pembanding setelah perkiraan selesai**. Ini pesan utama yang hilang ketika semua titik terlihat sejak awal.

**Frame akhir:** diagram asli/perkiraan/residual lengkap, tiga rasio terlihat, caption ilustrasi jelas. Juri dapat membaca frame akhir saat presenter masuk ke transisi.

## Slide 7 — Satu fold menjadi sembilan pengujian

**Pilihan:** native animation sekitar 20 detik. Playback tidak boleh menunggu otomatis hingga seluruh script selesai; presenter mengontrol tiap kelompok.

**Komposisi:** awalnya satu timeline besar. Training gelap berhenti di origin; validation merah tepat sesudahnya. Label `15 hari` menempel pada bracket yang lebarnya tetap. Di fase kedua timeline mengecil menjadi baris pertama dari sembilan baris yang sejajar.

| Waktu lokal | Visual | Cue narasi |
|---|---|---|
| 0–5 | Training tumbuh dari awal rekaman ke satu origin. Validation belum muncul | “Model dilatih menggunakan data masa lalu…” |
| 5–9 | Validation muncul setelah origin dengan bracket 15 hari | “…diuji pada 15 hari berikutnya” |
| 9–14 | Timeline bergeser ke origin kedua dan ketiga; panjang validation tetap | “Proses ini diulang…” |
| 14–18 | Tampilkan sembilan baris ringkasan; asal training sama dan akhir bergeser | “…sembilan titik awal berbeda” |
| 18–20 | Highlight overlap tanggal antarjendela dan buka caveat | “Jendela… saling tumpang tindih” |

Visual OOF: hasil prediksi pada blok validation bergerak ke lembar kecil bertanda `OOF`, kemudian menuju `Mempelajari penggabungan`. Jangan mengambil titik dari training untuk ilustrasi OOF. Jangan menunjukkan target test asli untuk membangun meta-model.

Tidak perlu kalender tanggal atau angka skor baru. RMSE ditampilkan sesudah mekanisme origin dipahami, sebagai teks/rumus yang stabil.

**Frame akhir:** semua sembilan fold terlihat, horizon sama, caveat tumpang tindih tetap terbaca. Hindari sembilan checkmark yang dapat terbaca sebagai hasil menang; hasil fold baru dibahas pada penutup.

## Slide 8 — Mengapa bobot berubah menurut waktu?

**Pilihan:** native animation sekitar 22 detik; video pendek hanya jika mekanisme tidak dapat dieksekusi dengan jelas dalam PowerPoint.

**Komposisi:** lima sumber prediksi di kiri, tiga pita waktu di tengah, dua batang kontrol di kanan. Gunakan bus masukan bersama yang bercabang ke tiga penggabungan paralel. Jangan membuat output NNLS pita pertama menjadi input NNLS pita kedua.

| Waktu lokal | Visual | Cue narasi |
|---|---|---|
| 0–4 | Lima strip prediksi masuk ke penggabungan. Line style dan warna mengidentifikasi sumber | “Model yang bagus pada satu bagian hari…” |
| 4–9 | Pita 1, 2, 3 dibuka. Sorot satu pita pada satu waktu; label vektor bobot berbeda per pita | “…belum tentu… di bagian hari yang lain” |
| 9–13 | `NNLS` dan `bobot ≥ 0` muncul. Sumber tetap lima, tidak bertambah | “Bobotnya tidak negatif” |
| 13–17 | Label `Shrinkage` masuk; gerak kecil pada cue regularisasi mereda dan berhenti | “…agar tidak terlalu mengikuti data validasi” |
| 17–20 | Cabang kontrol acak muncul dalam area audit yang terpisah, berlabel `Kompleksitas setara` | “Equal-Parameter Random Control” |
| 20–22 | Batang hasil muncul: penurunan RMSE 0,080 dan 0,007. Tahan angka | “Informasi waktu memang membantu” |

**Detail bobot:** boleh memakai label `w₁`, `w₂`, `w₃` untuk menandai vektor per pita. Jika ketebalan aliran atau ukuran kontribusi diubah, harus memakai bobot implementasi yang benar, atau diberi label `Ilustrasi bobot`. Pilihan yang lebih aman adalah highlight pita dan label vektor tanpa mengarang besar kontribusi model.

**Detail shrinkage:** jangan mengklaim target regularisasi tertentu sebelum dicocokkan dengan implementasi. Cue spring menjelaskan adanya pembatasan/regularisasi; tidak perlu menampilkan bobot bergerak menuju nilai buatan.

**Detail kontrol:** acak merujuk pada pengelompokan untuk ensemble dengan parameter setara, bukan random train/validation split. Label `Audit validasi bersarang` tetap ada. Batang berawal dari nol dengan skala sama; 0,007 panjangnya 8,75% dari batang 0,080. Kedua angka adalah magnitudo penurunan, bukan skor absolut atau persentase.

**Frame akhir:** diagram mekanisme dan chart kontrol sama-sama lengkap. Tidak ada garis yang terus bergerak di dekat angka hasil.

## Slide 9 — Momen penemuan pola

**Pilihan:** native animation sekitar 16 detik. Inilah jembatan emosional menuju video slide 10.

**Komposisi:** grafik residual dominan di kiri, ≈0,93 besar di kanan, cue level/increment di bawah. Garis nol tetap sepanjang adegan.

| Waktu lokal | Visual | Cue narasi |
|---|---|---|
| 0–4 | Residual ditampilkan dari kiri ke kanan dengan sumbu waktu tetap | “Kami memeriksa pola residual…” |
| 4–8 | Satu titik negatif disorot, lalu tetangga negatif berikutnya menyusul. Bracket menandai rentetan | “Titik-titik di sekitarnya cenderung…” |
| 8–11 | ≈0,93 muncul langsung, diikuti `lag-1` dan `Galat model level` | “Autokorelasi… sekitar 0,93” |
| 11–16 | Cue satu titik `Level` berubah menjadi pasangan titik `Increment`; link 30 menit lalu bracket dua jam muncul | “Seberapa besar kelembapan berubah…” |

Tidak perlu memperbesar kaca hingga menutupi seluruh grafik. Fokusnya pada pola bertetangga, bukan pada efek lensa. Residual negatif konsisten dengan `prediksi − aktual` dan prediksi terlalu rendah.

**Transisi ke slide 10:** gunakan posisi lima simpul increment yang sama sebagai titik awal video. Link dan simpul terasa berlanjut dari halaman investigasi ke halaman rekonstruksi. Hindari transisi yang mengubah waktu atau jumlah interval.

## Slide 2 — Reveal ketersediaan data

**Pilihan:** native build 10 detik, manfaat cukup besar dengan produksi sederhana.

0–3 detik: train beserta angka 2.933 muncul. 3–5: test dan 734 dibuka. 5–8: target pada test tetap kosong dengan tanda tanya, sementara pita sensor lain menerus. 8–10: kurung `24 kanal sensor` muncul dan seluruh frame ditahan.

Yang bergerak adalah **ketersediaan catatan**, bukan nilai kelembapan. Jangan mengisi target test lalu menghapusnya karena dapat menyiratkan label pernah diketahui. Baris visual pendamping merupakan kelompok kanal, bukan hanya empat sensor.

## Slide 4 — Membuka informasi dari rumus

**Pilihan:** native build 18 detik. Dua rumus dan hubungan fisika memerlukan perhatian yang dapat ditahan, sehingga tidak perlu video mandiri.

0–4: notebook dan tujuh indeks muncul. 4–9: highlight rerata/maksimum, kemudian jalur invers pertama. 9–13: highlight CHU, lalu jalur kedua. 13–16: kedua hasil bertemu pada `Tmin`; 0,047°C serta label `SD selisih dua rekonstruksi` muncul. 16–18: alur proksi titik embun, tekanan uap, dan persamaan RH dibuka.

Gunakan garis penghubung yang tumbuh dari input ke hasil. Rumus tidak ikut memutar atau terbang. Jika kurva dua rekonstruksi ditampilkan, sumbernya harus hasil rekonstruksi atau berlabel ilustrasi.

Angka 0,047 menunjukkan kesesuaian dua jalur, bukan galat pengukuran titik embun. Peralihan Tmin ke dew point tetap berlabel **proksi**, bukan tanda sama dengan.

## Slide 12 — Memisahkan diagnosis dan koreksi

**Pilihan:** native build 18 detik. Manfaat utama adalah mencegah salah tafsir bahwa koreksi diambil langsung dari −2,89.

0–4: marker in-sample dan −0,006 %RH muncul dekat nol. 4–8: batang audit maju turun dari nol dan berhenti pada −2,89 %RH; caption prediksi cenderung rendah muncul. 8–12: area diagnosis diredupkan sedikit dan area koreksi dibuka **dari envelope OOF yang berbeda**. 12–15: `50% estimasi koreksi` muncul, lalu panah ke prediksi CatBoost. 15–18: dua negative control dibuka dengan cap `Tidak membaik`.

Tidak ada panah dari batang −2,89 langsung menuju 50%. Jangan menggerakkan batang audit tepat separuh menuju nol. Besar offset hasil OOF berbeda dari angka audit; titik bias setelah koreksi tidak digambar tanpa hasil yang benar.

**Frame akhir:** kedua domain lengkap dan terpisah, dengan catatan `Angka audit bukan besar koreksi` terlihat jelas.

## Slide yang cukup dengan reveal ringan

- **1:** map terbuka pada cue “734 nilai”, log kosong disorot, lalu tahan. Pak Anton tidak perlu berjalan atau bercakap dalam video baru.
- **5:** buka train, test, lalu catatan irigasi. Mean adalah perbandingan periode; jangan memakai morph yang menyiratkan satu suhu teramati bergerak dari 27,51 ke 24,64 secara real-time.
- **6:** anggota muncul sesuai script; sorot CatBoost pada bagian model diversity; konektor gabungan baru dibuka setelah seluruh peran dijelaskan.
- **11:** Bukti 1 muncul dahulu, lalu Bukti 2. Angka final muncul langsung dan diam. Jangan membuat kurva aktual test rekaan sebagai bukti video.
- **13:** hasil memburuk dibuka, paket tambahan dicap REJECTED, lalu batas penerapan. Cap tidak mengenai pipeline yang tetap diterapkan.
- **14:** hasil publik, validasi, kemudian cap penutup. Semua angka bertahan untuk Q&A. Tidak perlu count-up skor atau kebun berubah sehat.

## Catatan substansi sebelum rekaman

Pada Bagian V-D laporan, RMSE increment dua jam tertulis **3,57 versus 3,52** dari level. Artinya, model increment dua jam tidak menunjukkan keunggulan seperti horizon 30 menit. Script slide 11 menyebut keunggulannya lebih kecil; wording tersebut perlu diselaraskan sebelum rekaman.

Arahan visual yang aman: jelaskan adanya dua horizon dan bahwa 30 menit mendapat bobot relatif lebih besar. Jangan memberi dua tanda kemenangan yang menyiratkan increment unggul pada keduanya. Rekomendasi kalimat: `Pada horizon dua jam, model increment tidak memberikan keunggulan yang sama, sehingga informasi 30 menit diberi bobot relatif lebih besar.` Script asli belum diubah oleh dokumen ini.

## Urutan produksi dan pemeriksaan

1. Produksi video slide 10 dari VO final dan contoh mekanisme yang dibekukan. Pastikan close-up mismatch serta penyesuaian bersama sudah terbaca sebelum menambah efek.
2. Buat build slide 3 dan 7. Keduanya memperjelas prosedur yang menjadi dasar kepercayaan pada model.
3. Buat build slide 8 dan 9, dengan layout simpul yang menyambung ke video.
4. Tambahkan reveal slide 2, 4, 12 bila rehearsal menunjukkan manfaat.
5. Simpan setiap slide sebagai frame akhir statis yang lengkap. Pertahankan native chart/diagram pada PPTX sebagai bahan edit dan fallback.
6. Uji playback lokal, audio, klik presenter, dan waktu seluruh presentasi. Uji slide 10 dari awal dan dari seek di tengah agar animasi tidak bergantung pada state frame sebelumnya.

Kriteria keberhasilan bukan jumlah efek: penonton bisa menjelaskan kembali leave-one-out, rolling-origin, alasan ensemble per waktu, serta perbedaan level/increment setelah melihat animasinya.
