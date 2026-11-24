# Naskah presentasi Sparekit untuk juri

Naskah ini ditulis untuk dibacakan sambil membuka web. Setiap bagian menyebut halaman yang sedang ditampilkan di layar, lalu apa yang perlu ditunjuk dan diucapkan. Angka diambil dari web per data 30 Sep 2026.

Durasi demo sekitar 8 sampai 10 menit, ditambah tanya jawab.

**Wajib sebelum submit (5 Nov 06:00):**
- [ ] Vercel → project **app** → Settings → Deployment Protection: matikan Vercel Authentication. Domain `app-raphaeladikaras-projects.vercel.app` saat ini mengarah ke login SSO Vercel, jadi juri tidak bisa masuk.
- [ ] Buka URL produksi di jendela incognito. Harus muncul halaman login Sparekit, bukan login Vercel. Ambil screenshot timestamp deploy terbaru.
- [ ] Samakan angka deck dengan bagian 9c. Hapus 435, 98%, 85 vs 61, dan 94%.
- [ ] Buat zip dengan `git archive -o sparekit-source.zip HEAD`. **Jangan zip folder secara manual:** `app/.env` berisi API key asli.

**Persiapan sebelum mulai:**
- Login sebagai Nadia (planner).
- Buka semua halaman sekali dan tutup tutorialnya, supaya tidak muncul saat demo.
- Di halaman **To do**, tekan **Reset demo**.
- Di **Plant map**, pastikan tombol Size ada di **Same as last** dan Supplier delay di **+0 days**.

---

## 1. Pembuka: masalahnya

**Layar:** halaman **Stock**.

> "Bayangkan pabrik sedang shutdown besar. Teknisi butuh satu gasket, tapi raknya kosong. Padahal di gudang yang sama ada ratusan miliar rupiah barang yang hampir tidak pernah dipakai. Itulah masalah yang diangkat di case ini."

> "Di halaman Stock ini kita langsung melihat masalahnya. Ada **Rp 414 miliar** stok yang melebihi batas maksimum di SAP, dan itu baru dihitung dari part yang punya harga purchase order. Tapi di saat yang sama, ada **115 part kritis** yang biasa distok, stoknya nol padahal masih dipakai pabrik, dan **205** lagi sudah di bawah Min. Lebih parah lagi, **36%** dari belanja purchase order justru mengalir ke part yang sekarang sudah kelebihan stok."

> "Kenapa bisa begini? Karena batas Min dan Max di SAP dibuat untuk bulan-bulan biasa. Saat turnaround, pemakaian part melonjak berkali lipat dalam beberapa minggu. Contohnya, ada **79 part** yang dalam satu turnaround saja sudah memakai lebih banyak dari batas Max-nya, misalnya Max-nya 25 tapi terpakai 200."

---

## 2. Solusinya dalam satu kalimat

**Layar:** tunjuk menu samping.

> "Solusi kami namanya Sparekit. Intinya sederhana: untuk setiap part, Sparekit memberi tahu **berapa yang kita punya, berapa yang akan kita butuhkan, apa yang harus dilakukan, dan kapan**."

> "Menu di samping kami susun mengikuti pertanyaan yang ada di kepala seorang planner. Pertama, *apakah kita siap untuk turnaround?* Kedua, *apa yang akan kita butuhkan?* Ketiga, *apa yang harus kita lakukan?* Pertanyaan kedua menjawab Key Question 1, dan pertanyaan ketiga menjawab Key Question 2."

---

## 3. Apakah kita siap? Halaman Plant map

**Layar:** halaman **Plant map**, peta 3D pabrik.

> "Kita mulai dari halaman Plant map. Di sini user langsung melihat seberapa siap pabrik untuk turnaround berikutnya, yang kami asumsikan tanggal 1 Juni 2027."

> "Kami memutar ulang turnaround terakhir terhadap stok hari ini, ditambah pemakaian normal sampai hari turnaround. Hasilnya, kalau kita tidak memesan apa-apa, hanya **36%** part kritis yang akan siap. Kalau semua order keluar tepat waktu, angkanya bisa naik ke **96%**. Tapi ada **18 part** yang sudah terlambat, karena hari terakhir aman untuk memesannya sudah lewat."

**Tunjuk:** label "Furnaces 86 of 119 parts short".

> "Setiap label mesin dibaca seperti ini: furnace memakai 119 jenis part di turnaround terakhir, dan 86 di antaranya stoknya tidak akan cukup. Warna merah di peta menunjukkan area dengan kekurangan paling banyak."

**Tunjuk:** tombol tanggal, Size, dan Supplier delay.

> "Planner juga bisa mensimulasikan: bagaimana kalau turnaround dimajukan, ukurannya lebih besar, atau supplier telat 30 hari? Semua angka langsung dihitung ulang."

**Tunjuk:** daftar "Deal with these first".

> "Dan supaya tidak berhenti di peta, ada daftar lima part yang harus diurus paling dulu. Warnanya langsung memberi tahu tingkat urgensinya: merah artinya sudah terlambat atau part kritis yang raknya kosong, oranye artinya masih sempat dipesan."

> "Halaman ini membantu manajemen menjawab satu pertanyaan besar dalam beberapa detik: *apakah kita aman untuk shutdown berikutnya, dan kalau tidak, di mana masalahnya?*"

---

## 4. Key Question 1: Halaman Forecast

**Layar:** halaman **Forecast**.

> "Key question pertama adalah: **bagaimana perusahaan bisa memprediksi kebutuhan spare part yang pemakaiannya tidak teratur?** Kami menjawabnya di halaman Forecast."

**Tunjuk:** alur panah di atas.

> "Di halaman ini, user langsung melihat alurnya dari kiri ke kanan. Dari **7.481** part di katalog, kami memperkirakan sekitar **846** akan terpakai sampai akhir Maret. Angka ini masuk akal, karena enam bulan terakhir ada **807** part yang terpakai pada pekerjaan normal. **583** di antaranya lebih mungkin terpakai daripada tidak, dan **267** dari 583 itu stoknya tidak akan cukup. Lalu ada turnaround di atasnya: **230 dari 360** part turnaround akan kurang."

**Tunjuk:** tabel di bawahnya, buka grup Gasket lalu Sheet.

> "Di bawahnya, user bisa melihat jawabannya part per part. Part dikelompokkan per jenis, misalnya Gasket, lalu per sub-jenis seperti Sheet, Ring, atau Spiral Wound. Setiap baris berwarna, jadi tanpa membaca angka pun user langsung tahu mana yang merah dan harus segera diurus. Di setiap baris ada tiga angka: berapa yang kita punya, berapa yang akan dipakai, dan berapa yang dibutuhkan untuk turnaround."

**Tunjuk:** bagian "How we predict parts that are used irregularly".

> "Lalu bagaimana kami memprediksi part yang pemakaiannya tidak teratur? Rata-rata tidak bisa diandalkan di sini. Jadi model kami memisahkan dua pertanyaan: dipakai atau tidak, dan kalau dipakai berapa banyak. Lalu kami menyimulasikan 2.000 kemungkinan, sehingga hasilnya berupa rentang, bukan satu angka. Enam pola di layar menunjukkan seperti apa part-part itu, dan modelnya tetap satu. Yang berubah adalah sandarannya. Part yang rutin bersandar pada pemakaian terbaru. Part yang belum pernah dipakai, ada **5.551** part, bersandar pada jumlah yang terpasang dan seberapa sering peralatannya rusak. Turnaround kami hitung tersendiri sebagai kejadian terencana."

**Tunjuk:** kartu bukti di bagian bawah.

> "Apakah prediksinya bisa dipercaya? Kami mengujinya di bulan-bulan yang tidak pernah dilihat model. Dari 100 pasang part, satu yang terpakai dan satu yang tidak, model kami menebak benar **92 kali**, sementara cara sederhana hanya **84 kali**. Untuk part yang belum pernah dipakai, di bulan uji yang sama, model kami benar **84 kali**, rumus klasik spare part hanya **61 kali**."

**Layar:** tekan **Play it month by month**, atau buka **Replay** di menu kiri, lalu tekan **Play**.

> "Sekarang bukti yang paling penting. Kami memutar ulang pemakaian nyata dari Maret sampai September 2026, hanya untuk part kritis yang memang disimpan di rak. Part Non Stock tidak kami hitung, karena dibeli per pekerjaan. Dengan Min dan Max hari ini, part tersedia saat diminta **53%**. Dengan Sparekit, **98%**. Hari rak kosong turun dari **8.905 ke 2.239**. Untuk uangnya, kami hitung seluruh **3.656 part yang distok**: stok rata-rata turun dari **Rp 1.005 miliar ke Rp 310 miliar**, karena uang ditarik dari part yang menganggur dan dipindah ke part yang benar-benar dipakai."

**Tunjuk:** panel **The limits move every month**, lalu klik Jun dan Jul.

> "Inilah yang kami maksud dinamis. Setiap tanggal 1, model dilatih ulang hanya dengan kejadian sampai hari itu, lalu menetapkan batas baru. Setiap bulan ada **740 sampai 1.668** part yang batasnya berubah, ke dua arah. Di Juni kebanyakan Min turun, di Juli kebanyakan naik."

**Tunjuk:** panel **One part, month by month**, dua grafik berdampingan.

> "Contohnya O-ring ini. Pita hijau adalah rentang Min sampai Max, dan garis biru adalah isi rak. Di kiri, pita SAP datar di 4 sampai 11, dan titik merah menunjukkan permintaan yang tidak terlayani penuh: 14 dari 34 unit gagal. Di kanan, pita Sparekit bergerak setiap bulan, dan semua permintaan terlayani. Tabel di bawahnya menunjukkan apa yang dilihat model pada setiap pembaruan. User juga bisa mencari part lain, dan grafik yang sama ada di halaman tiap part."

> "Jadi halaman Forecast membantu planner berhenti menebak. Mereka tahu part mana yang akan dibutuhkan, berapa banyak, dan kapan, termasuk part yang belum pernah dipakai sebelumnya. Ini yang menyelesaikan masalah kebutuhan yang tidak bisa diprediksi."

---

## 5. Key Question 2: tiga langkah keputusan

> "Key question kedua adalah: **bagaimana mengatur stok secara dinamis, sambil menyeimbangkan biaya, ketersediaan, dan risiko?** Kami menjawabnya dengan tiga langkah yang berurutan, dan terlihat di bagian atas setiap halaman: pilih kebijakan stok, lihat dampaknya ke rak, lalu eksekusi."

### Langkah 1: Halaman What if

**Layar:** halaman **What if**.

> "Langkah pertama di halaman What if. Di sini user memilih seberapa banyak stok yang mau disimpan, dan langsung melihat biayanya dalam setahun."

> "Grafik ini menunjukkan dua biaya yang saling tarik-menarik. Biru adalah biaya menyimpan stok, yang naik kalau stok makin banyak. Oranye adalah biaya kalau part habis, yang naik kalau stok makin sedikit. Titik paling murah ada di tengah."

> "Menurut model, setelah kebijakan ini stabil, stok rata-rata cukup **Rp 186 miliar**, bukan **Rp 458 miliar** dengan Min hari ini, dan hari kekurangan part turun **85%**. Kenapa bisa? Karena hari ini uangnya ada di part yang salah. Uang yang sama, kalau ditaruh di part yang paling berisiko, hasilnya jauh lebih aman."

> "Tapi model saja tidak cukup. Di bawahnya ada hasil replay pada pemakaian nyata Maret sampai September: part kritis yang distok tersedia saat diminta naik dari **53% ke 98%**, sementara stok rata-rata seluruh part yang distok **69%** lebih rendah. Angka ini yang kami pegang, karena diuji pada kejadian nyata."

**Tunjuk:** dua slider.

> "Biaya downtime tidak ada di data, jadi kami tidak mengarangnya. User bisa menggeser asumsinya sendiri, dan rekomendasinya ikut menyesuaikan. Dengan satu klik, AI juga menulis memo kebijakan ini untuk bagian finance."

### Langkah 2: Halaman Stock

**Layar:** halaman **Stock**.

> "Langkah kedua di halaman Stock. Setelah kebijakannya dipilih, user langsung melihat part mana yang terlalu sedikit dan mana yang terlalu banyak."

**Tunjuk:** kotak "What to deal with first".

> "Kotak ini membagi part berdasarkan seberapa penting dan seberapa banyak stoknya. Pojok kiri atas, **320 part kritis yang stoknya terlalu sedikit**, harus diurus sekarang. Pojok kanan bawah, **918 part yang kurang kritis tapi stoknya berlebih**, adalah uang yang bisa dilepas. Setiap kotak bisa diklik dan langsung membuka daftar tugasnya."

**Tunjuk:** tab Slow and dead stock.

> "Kami juga melihat ke depan. Dalam tiga bulan, **154 part** akan menjadi stok lambat dan **205 part** menjadi stok mati kalau tidak dipakai. Kami juga membandingkan stok dengan umur simpan yang disarankan pabrikan, misalnya bearing sekitar tiga tahun. Hasilnya, ada **768 part senilai Rp 230 miliar** yang kemungkinan rusak di rak sebelum sempat terpakai."

### Langkah 3: Halaman To do

**Layar:** halaman **To do**.

> "Langkah terakhir adalah eksekusi, di halaman To do. Semua rekomendasi tadi berubah menjadi tugas untuk orang yang tepat. Saat ini ada **255 tugas mendesak**. Total saran pembelian **Rp 131 miliar**, angka yang sama dengan kotak To order di halaman Stock, dan stok berlebih **Rp 443 miliar** yang bisa dilepas. Kedua rupiah ini hanya menghitung part yang punya harga purchase order."

**Lakukan:** buka satu part dari Forecast, tekan **Review in To do**.

> "Misalnya dari halaman part tadi, saya tekan Review in To do. Papan langsung menyaring ke part itu saja, lengkap dengan alasannya."

**Lakukan:** tekan **Approve and email Bima**.

> "Sebagai planner, Nadia tinggal menekan Approve and email Bima. Email-nya sudah ditulis, lengkap dengan angka dari sistem, dan baru terkirim setelah dibaca dan ditekan Send. Begitu terkirim, tugasnya pindah ke kolom Approved dan menjadi tanggung jawab Bima di bagian procurement."

**Lakukan:** di kartu lain, tekan tombol **X (Reject)**. Ketik di kolom "Or say it in your own words": *this furnace was replaced last year*, lalu tekan **Sort it**.

> "Kalau Nadia tidak setuju, sistem tidak cuma mencatat 'ditolak'. Nadia boleh menulis alasannya dengan bahasa sendiri, dan AI mengelompokkannya ke salah satu dari lima alasan. Di sini AI memilih *Machine retired or replaced*. Di bawahnya terlihat aturan yang direncanakan untuk alasan itu: part ini berhenti dibeli dan masuk review disposal. Di prototipe ini alasannya sudah tercatat, dan mesin hitung mulai membacanya pada fase seluruh kilang."

**Lakukan:** tekan **Reject**.

**Lakukan:** ganti peran ke Bima.

> "Kalau kita lihat dari sisi Bima, tugas ini muncul di bagian Your next steps. Bima tinggal meminta penawaran ke supplier, dan saat barang datang, tekan Mark done. Semua langkah tercatat."

**Tunjuk:** tombol **Send to SAP**.

> "Dan karena perusahaan memakai SAP, batas Min dan Max yang baru bisa diunduh dalam format yang siap dimasukkan ke SAP sekaligus."

> "Jadi tiga langkah ini menjawab Key Question 2. Planner memilih kebijakan berdasarkan biaya dan risiko, melihat dampaknya part per part, lalu mengeksekusinya bersama tim. Stok jadi lebih sedikit, tapi part kritis lebih aman."

---

## 6. Satu part dari dekat: Halaman part

**Layar:** buka **Firebrick insul 28** dari Forecast.

> "Semua halaman tadi bermuara ke halaman ini, yaitu satu part. Di bagian paling atas, user langsung melihat jawabannya. Kita punya **0**, kita butuh **50.637** sampai turnaround, jadi kurang **50.637**. Tindakannya: pesan sekarang, karena pengirimannya bisa sampai 173 hari."

> "Bar di bawahnya menunjukkan dari mana kebutuhan itu datang. Abu-abu adalah pemakaian normal sampai turnaround, oranye adalah pekerjaan turnaround itu sendiri. Kalau user ingin tahu alasannya, kartu di bawahnya menjelaskan riwayat pemakaian, batas stok, biaya, dan kualitas datanya."

---

## 7. Kenapa angkanya bisa dipercaya: Halaman Data check

**Layar:** halaman **Data check**.

> "Terakhir, rekomendasi hanya sebaik datanya. Di halaman Data check, kami menunjukkan **9 masalah** yang kami temukan di data dan cara menanganinya. Contohnya, **5.420 baris** purchase order ternyata tercatat ganda, jadi kami hapus sebelum menghitung harga dan waktu kirim."

> "Setiap part juga punya skor kepercayaan data. Kalau catatan stoknya tidak masuk akal, sistem menyarankan hitung ulang raknya dulu sebelum memesan. Semua asumsi, seperti tanggal turnaround, kami tulis terbuka."

**Tunjuk:** panel **How Sparekit keeps learning**.

> "Min dan Max yang statis lama-lama basi. Sparekit dibangun di atas tiga loop, dan di setiap loop kami tulis sejauh mana sudah berjalan. **Setiap bulan**, model dilatih ulang dan forecast dinilai terhadap kejadian nyata. Ini sudah kami jalankan pada bulan-bulan lalu, skornya 91 sampai 92, dan hasilnya tadi kita lihat di Replay. **Setiap keputusan**, alasan penolakan planner sudah tercatat, dan mesin hitung mulai membacanya pada fase seluruh kilang. **Setiap turnaround**, kit berikutnya dimulai dari pemakaian nyata turnaround terakhir, lalu diperbarui setelah turnaround selesai."

> "Di bawahnya kami tulis juga apa yang dilakukan AI dan apa yang **tidak** dilakukannya. AI tidak pernah memesan atau mengubah SAP sendiri, tidak mengarang angka, dan tidak mengubah criticality. Setiap langkah tetap disetujui orang."

**Tunjuk:** panel **Choices we made, and why**.

> "Terakhir, semua pertanyaan yang kami ajukan ke diri sendiri ada di sini, termasuk hal yang sengaja tidak kami lakukan beserta alasannya. Contohnya kenapa kami tidak memodelkan musim: datanya hanya 17 bulan, jadi baru ada satu siklus."

---

## 8. Penutup

> "Jadi, Sparekit mengubah Min dan Max yang statis menjadi keputusan per part: punya berapa, butuh berapa, harus apa, dan kapan. Semuanya dibuktikan dengan data perusahaan sendiri, mencatat alasan setiap keputusan planner, dan hasilnya bisa langsung kembali ke SAP."

> "Dua angka yang kami harap diingat. Pertama, kesiapan turnaround bisa naik dari **36% ke 96%** kalau order keluar tepat waktu. Kedua, di replay pemakaian nyata Maret sampai September, part kritis yang distok tersedia saat diminta naik dari **53% ke 98%**, sementara stok seluruh gudang **69%** lebih rendah. Terima kasih."

---

## 9. Jawaban untuk pertanyaan juri

| Pertanyaan | Jawaban |
|---|---|
| Datanya kan dummy? | "Betul, ini data case study. Karena itu kami fokus menunjukkan cara kerjanya dan membuktikannya di data yang sama, bukan klaim rupiah absolut." |
| Kenapa tidak pakai deep learning? | "Datanya berupa tabel 17 bulan, dan 74% part tidak punya riwayat pemakaian, sedangkan model sekuensial butuh riwayat panjang per part. Dua model gradient boosting ditambah simulasi lebih stabil, mudah dijelaskan ke planner, dan sudah mengalahkan pembanding." |
| Biaya downtime dari mana? | "Tidak ada di data, jadi kami jadikan asumsi yang bisa diatur di halaman What if: Rp 5 juta per hari untuk satu part A yang kosong, bukan biaya seluruh kilang berhenti. Rencana yang kami sarankan menyimpan stok lebih sedikit dan lebih jarang kehabisan daripada hari ini, jadi tetap lebih murah di nilai berapa pun. Slider hanya memindahkan titik termurah." |
| Tanggal turnaround dari mana? | "Itu asumsi perencanaan, 1 Juni 2027, dan bisa diganti langsung di Plant map." |
| Bagaimana masuk ke SAP? | "Tombol Send to SAP menghasilkan file Min dan Max baru untuk update massal, plus draft purchase request untuk order yang sudah disetujui." |
| Kenapa Non Stock tidak dihitung di replay? | "Karena dibeli per pekerjaan, jadi rak kosong itu normal. Kalau dihitung, hasilnya gagal 0% hanya karena Max-nya 0, dan itu tidak adil. Kalau semua part Non Stock kritis ikut distok, ketersediaan semua part kritis menjadi 95% dengan stok Rp 782 miliar. Itu skenario terpisah." |
| Replay mulai dari Max. Kenyataannya gudang kan penuh? | "Betul. Karena itu kami tulis terbuka: stok baru jadi uang setelah kelebihannya diretur, dipindahkan, atau dihapus, dan itu keputusan kilang. Kalau replay dimulai dari rak yang tercatat, ketersediaan tetap naik dari 60% ke 93%, tapi stoknya bertahan. Jadi manfaat ketersediaan datang lebih dulu, uangnya menyusul." |
| Apa bedanya pembaruan bulanan dengan sekali set? | "Dibandingkan sekali set di bulan Maret, hari rak kosong 15% lebih sedikit dengan stok 2% lebih banyak. Ketersediaannya kurang lebih sama, 97,7% dibanding 97,9%. Manfaat terbesarnya datang dari batas yang tepat. Pembaruan bulanan menjaganya tetap tepat." |
| Max O-ring 58, padahal pemakaiannya 34 dalam 7 bulan. Kebanyakan? | "Pemakaiannya setara sekitar 58 per tahun, dan harganya hanya Rp 15 ribu, jadi ukuran pesanannya dibuat besar, dibatasi paling banyak setahun perkiraan pemakaian. Max yang penuh hanya bernilai sekitar Rp 875 ribu. Untuk part mahal, ukuran pesanannya jauh lebih kecil." |
| Kenapa rak Sparekit sempat kosong? | "Karena sedang menunggu kiriman. O-ring itu kosong sekitar 35 hari, dan kebetulan tidak ada permintaan saat itu. Karena itu kami juga menampilkan hari rak kosong, bukan hanya ketersediaan." |
| Non Stock katanya dibeli per pekerjaan, kok ada di daftar beli? | "Dari Rp 130,9 miliar, Rp 49,8 miliar untuk part yang distok, Rp 33,3 miliar untuk part Non Stock yang dibutuhkan turnaround, dan Rp 47,8 miliar untuk part Non Stock yang menurut forecast akan terpakai. Yang terakhir kami beri catatan di board dan ada file daftarnya: menyimpannya berarti memindahkannya ke Stock dulu, dan itu keputusan kilang. Karena itu angka utama replay hanya menghitung part yang distok." |
| Angka persetujuan planner itu dari mana? | "Dari keputusan contoh di demo, dan web menuliskannya begitu. Di produksi, angka ini menjadi salah satu syarat sebelum diterapkan ke seluruh kilang." |
| Unit-nya kan didominasi barang curah? | "Betul, 10 part menyumbang lebih dari separuh unit. Kalau dihitung per permintaan, naik dari 85% ke 98%, dan angka itu juga kami tampilkan." |
| What if bilang stok turun 59%, replay 69%. Mana yang benar? | "Dua-duanya, beda cakupan. What if memodelkan semua part setelah kebijakan stabil, termasuk part Non Stock yang akan mulai disimpan. Replay memakai part yang sudah distok, pada pemakaian nyata 7 bulan: ketersediaan diukur di 495 part kritis yang dipakai, nilai stok di seluruh 3.656 part yang distok. Untuk satu angka, kami pakai replay: turun 69%." |
| Kenapa nilai stok part yang punya harga PO malah naik di replay? | "Karena uangnya pindah. Part ber-harga PO adalah part yang memang dibeli dan dipakai, jadi stoknya naik dari Rp 80 miliar ke Rp 184 miliar. Penurunan datang dari part yang menganggur. Total turun 69%, tapi 84% part pakai harga perkiraan dari jenis part yang sama." |
| Stok 495 part kritis itu sendiri naik atau turun? | "Naik, dari Rp 31 miliar ke Rp 136 miliar. Ketersediaan 53% ke 98% memang perlu stok lebih di part yang dipakai. Angka −69% adalah seluruh 3.656 part yang distok, dan penghematannya datang dari part yang menganggur. Sebagian kenaikan karena batas bulan Maret dihitung tepat setelah turnaround dan simulasi mulai penuh di Max, jadi pesanan Maret itu perlu dipangkas planner." |
| Kenapa part kritis kosong 115, bukan 435? | "435 termasuk 320 part Non Stock, yang memang dibeli per pekerjaan dan normalnya kosong. Yang benar-benar celah adalah 115 part stok yang kosong, ditambah 205 di bawah Min." |
| Datanya cuma 17 bulan, bagaimana dengan musim? | "Dengan satu siklus, musim tidak bisa diestimasi secara statistik. Jadi kami tidak memodelkan musim kalender. Lonjakan yang jelas, yaitu turnaround, kami pisahkan sebagai kejadian terencana. Pergeseran level 2025 ke 2026 ditangani dengan bobot data terbaru dan uji bergulir. Musim baru masuk model setelah ada minimal dua sampai tiga tahun data, dan itu ada di roadmap." |
| Apakah AI-nya benar-benar perlu? | "Kami uji pilihan terbaik tanpa AI: target dan waktu kirim sama, rumus klasik dari 180 hari terakhir, diperbarui tiap bulan. Ketersediaannya 93%, stoknya Rp 1.066 miliar, dan hari rak kosongnya 3.490. Sparekit 98%, Rp 310 miliar, 2.239 hari. Sebagian selisih stok terjadi karena rumus itu mempertahankan batas lama untuk part yang belakangan tidak terpakai, dan kami tulis itu terbuka." |
| Apakah sistemnya belajar? | "Sebagian sudah, sebagian kami rencanakan, dan web menulisnya terbuka. Latih ulang bulanan sudah kami uji pada bulan-bulan lalu, tinggal dijadwalkan saat uji coba. Alasan penolakan sudah tercatat dan disortir AI, tapi mesin hitung baru membacanya pada fase seluruh kilang. Pembaruan kit dilakukan setelah turnaround berikutnya." |
| Apa beda metode tiap pola pemakaian? | "Modelnya satu. Enam pola itu menggambarkan part-nya. Bedanya ada di sandaran: part rutin memakai pemakaian 90 hari terakhir untuk separuh taksiran, jumlah per pemakaian diambil dari riwayat part kalau ada minimal 3 kali, kalau tidak dari jenis part. Reorder point memakai rumus normal kalau peluang pakai minimal 0,3, dan memakai kuantil simulasi kalau di bawah itu." |
| Kalau AI salah mengelompokkan alasan? | "Planner melihat pilihannya sebelum menekan Reject dan bisa menggantinya. Kalau AI mati, sistem memakai pencocokan kata kunci dan menandainya." |
| Pompa A/B kan ada cadangannya? | "Benar, dan itu kami tampilkan di halaman part sebagai standby unit. Kami tidak menurunkan criticality-nya, karena itu keputusan pabrik dan urutannya ditetapkan panitia." |
| Ada lead time lebih dari setahun? | "Itu dari tanggal PR ke tanggal kirim di PO, yang untuk part turnaround bisa sengaja dibuat jauh. Kami tidak memotongnya sendiri. Part seperti itu diberi tanda supaya dicek ke procurement." |
| Harganya tidak lengkap? | "Hanya sekitar 1 dari 6 part yang punya harga dari purchase order. Total rupiah kami hanya menghitung part itu, jadi angka sebenarnya lebih besar." |

---

## 9b. Catatan untuk slide Roadmap (ide gate dari M3C)

Roadmap ditulis sebagai fase dengan **gate**: fase berikutnya hanya jalan kalau angka gate tercapai, dan kalau gagal kerugiannya terbatas.

| Fase | Isi | Gate untuk lanjut |
|---|---|---|
| F0 · Pilot 3 bulan | Satu area (furnace), Min/Max Sparekit lewat file SAP, latih ulang bulanan terjadwal, planner memakai To do | Fill A/B di area pilot >= 90% dan nilai stok tidak naik, dibandingkan 3 bulan sebelumnya |
| F1 · Seluruh plant | Semua area, export SAP rutin, mesin hitung membaca alasan reject | Lebih dari 80% saran disetujui planner, dan forecast bulanan tetap >= 85 dari 100 |
| F2 · Turnaround 2027 | Kit TA dari Sparekit, order-by date jadi gate T-180/T-120/T-90 | Kesiapan A/B >= 95% di T-30. Setelah TA, kit diperbarui dari pemakaian nyata |

Data tambahan yang diusulkan (satu saja, dengan justifikasi bisnis sesuai casebook): **jam operasi dan throughput per mesin dari process historian kilang**. Enam berkas baseline tidak memuat kondisi produksi dan operasi. Suku cadang yang aus mengikuti jam operasi, bukan kalender, dan tidak perlu sensor baru. Data ini baru masuk model kalau mengalahkan skor saat ini pada simulasi ulang yang sama. Masuk di F1.

Risiko utama dan mitigasinya: data master yang salah (trust score dan count first), planner tidak percaya (alasan per saran dan loop reject), harga tidak lengkap (harga PO dulu, estimasi diberi label).

## 9c. Angka untuk deck, per slide (salin persis, sama dengan web)

| Slide | Angka | Basis yang wajib ditulis kecil di slide |
|---|---|---|
| 2 Background | Rp 414 miliar di atas Max · 115 part kritis (stok) kosong + 205 di bawah Min · 36% belanja PO ke part yang sudah di atas Max · 79 part stok (71 A/B) Max-nya di bawah kebutuhan satu turnaround | Rupiah hanya part ber-harga PO (1.229 dari 7.481). Jangan pakai 435 |
| 3 Solution | Forecast: 92 vs 84 (semua part), 84 vs 61 (part tanpa histori, uji yang sama) · model dua bagian + simulasi, 6 pola hanya sebagai gambaran part · turnaround sebagai kejadian terencana · alasan reject tercatat dan disortir AI | Tanpa Min/Max sebagai input: 89 dan 77 |
| 4 Business Impact | Kesiapan TA A/B 36% → 96% kalau order tepat waktu · 18 part sudah terlambat · Replay Mar–Sep 2026: ketersediaan 495 part kritis yang distok 53% → 98%, stok seluruh 3.656 part yang distok Rp 1.005 miliar → Rp 310 miliar (−69%), hari rak kosong 8.905 → 2.239 (−75%), per permintaan 85% → 98% · Pembanding tanpa AI: 93%, Rp 1.066 miliar, 3.490 hari · Batas diperbarui tiap bulan: 740–1.668 part berubah per bulan | Ketersediaan diukur di 495 part, nilai stok di seluruh 3.656 part yang distok (di 495 part itu sendiri stok naik Rp 31 M → Rp 136 M). Non Stock tidak dihitung karena dibeli per pekerjaan. Tiap rencana mulai dari Max-nya sendiri. Harga estimasi untuk part tanpa PO. Tanpa Min/Max sebagai input: 98%, 2.826 hari, Rp 320 miliar |
| 4 Success metrics | Fill A/B, hari rak kosong A/B, nilai stok rata-rata, kesiapan TA A/B, tingkat persetujuan saran oleh planner, skor forecast bulanan | — |
| 5 Roadmap & Risk | Tabel gate F0–F2 di bagian 9b · F0: jadwal latih ulang bulanan · F1: mesin hitung membaca alasan reject · F2: kit diperbarui dari pemakaian nyata | — |
| 7 Key technologies | LightGBM dua bagian (dipakai/berapa, Tweedie) · simulasi Monte Carlo lead-time demand · TreeSHAP untuk alasan · LLM untuk penjelasan, draft email, dan menyortir alasan reject (ada fallback template/kata kunci) · Next.js + SQLite di Vercel | — |

**Yang tidak boleh muncul di deck:** 36% → 95% dan stok −22% sebagai angka utama (itu termasuk Non Stock, sudah diganti 53% → 98% dan −69%), 57.055 → 9.406, 435 part kosong, "98% tertutup", 85 vs 61, "A parts on the shelf 94%", "enam metode", "sistem sudah belajar dari setiap penolakan", Rp 458 B → Rp 186 B sebagai angka utama (itu model; kalau dipakai, tulis "model, setelah stabil").

## 9d. WAJIB MASUK DECK: batasan yang sudah kami putuskan

Poin-poin ini dihitung selesai karena datanya memang tidak ada atau sudah diuji, tapi casebook menanyakannya. Kalau tidak tertulis di deck, juri akan menganggapnya terlewat. Kedua key question juga wajib terjawab di slide Solution atau Business Impact, jadi tulis judul pertanyaannya di sana.

| Poin casebook | Yang wajib tertulis | Slide |
|---|---|---|
| Kondisi produksi dan operasi | Tidak ada di 6 berkas. Data tambahan yang kami usulkan: jam operasi dan throughput per mesin dari process historian (tanpa sensor baru), masuk model hanya kalau mengalahkan skor saat ini di replay yang sama. Masuk fase F1 | 5 Roadmap |
| Musim | Data 17 bulan hanya berisi satu siklus, jadi musim tidak bisa diestimasi. Lonjakan terbesar, yaitu turnaround, direncanakan sebagai kejadian tersendiri. Musim masuk setelah ada data 2–3 tahun | 3 Solution atau 5 Roadmap |
| Downtime dan production loss | Tidak ada di data. Rp 5 juta per hari untuk satu part A adalah asumsi, B 30%, C 5%, S 1%. Rencana yang disarankan tetap lebih murah di nilai berapa pun | 4 Business Impact |
| Maintenance dan notifikasi sebagai sinyal waktu | Jumlahnya masuk model. Sinyal waktunya diuji dan tidak menambah skor (31,8% vs 31,1% bulan acak), dan berkas maintenance tidak mencantumkan part, jadi dipakai sebagai konteks untuk planner | 3 Solution atau Appendix |
| Biaya simpan dan biaya order | Asumsi: 25% per tahun dan Rp 500 ribu per PR | 4 Business Impact, catatan kecil |
| Tanggal turnaround | 1 Juni 2027 adalah asumsi perencanaan, bukan jadwal resmi, dan bisa diubah di Plant map | 4 Business Impact, catatan kecil |
| Harga part | Hanya 1.229 dari 7.481 part punya harga PO. Posisi hari ini hanya menghitung part itu | 2 Background, catatan kecil |
| Non Stock di daftar beli | Rp 130,9 miliar = Rp 49,8 miliar part distok + Rp 33,3 miliar Non Stock untuk turnaround + Rp 47,8 miliar Non Stock yang perlu dipindah ke Stock dulu, keputusan kilang | 4 Business Impact |
| Penghematan stok vs uang tunai | Stok baru menjadi uang setelah kelebihannya diretur, dipindahkan, atau dihapus. Replay mulai dari Max. Dari rak tercatat: ketersediaan 60% → 93%, stok bertahan | 4 Business Impact |

## 10. Catatan angka

- Semua angka per data **30 Sep 2026**, untuk turnaround **1 Jun 2027** dengan ukuran sama seperti turnaround terakhir dan tanpa keterlambatan supplier.
- **Asumsi:** tanggal turnaround, biaya simpan 25% per tahun, Rp 5 juta per hari kekurangan part A, umur simpan dari panduan pabrikan, dan harga part yang tidak punya purchase order.
- **Basis rupiah.** Posisi hari ini (di atas Max, to buy, to free, di rak) hanya menghitung 1.229 dari 7.481 part yang punya harga PO, jadi angka sebenarnya lebih besar. Perbandingan kebijakan (What if dan replay) memakai semua part, dengan harga median jenis part yang sama untuk part tanpa PO. Jangan membandingkan dua basis ini satu sama lain.
- **Ketersediaan part.** Satu-satunya angka ketersediaan yang dikutip adalah replay (53% → 98%, per unit yang diminta, 495 part A/B yang distok dan terpakai, batas diperbarui tiap bulan). Model di What if menampilkan hari kekurangan, bukan persen ketersediaan.
- **Akurasi.** 92 vs 84 adalah rata-rata 4 uji bulanan. 84 vs 61 untuk part tanpa histori adalah satu uji hold-out, satu-satunya tempat rumus klasik diuji. Estimasi tinggi 180 hari menutup pemakaian nyata 67% part yang benar-benar dipakai. Angka lama "98%" ikut menghitung part yang tidak dipakai, jadi tidak dipakai lagi.
- Kalau ukuran atau tanggal di Plant map diubah saat demo, tekan **Reset** sebelum pindah halaman. Jumlah tugas di To do bisa bergeser kalau ada yang menekan Approve, jadi tekan **Reset demo** sebelum presentasi.
