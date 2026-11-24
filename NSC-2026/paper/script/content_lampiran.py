# -*- coding: utf-8 -*-
"""Teks lampiran naskah NSC 2026.

Dipisahkan dari `content.py` supaya batas antara badan naskah dan lampiran
terlihat dari susunan berkas, bukan hanya dari komentar.

Juknis 3d membolehkan lampiran, dan juknis 3b membatasi laporan pada 10 halaman
termasuk daftar pustaka. Kedua pasal itu tidak menyatakan secara eksplisit
apakah lampiran ikut dihitung. Sikap yang diambil di sini adalah yang aman untuk
kedua pembacaan: **badan naskah beserta daftar pustaka dijaga tepat 10 halaman
dan berdiri sendiri**, sehingga tidak ada satu pun argumen di Bagian I-VII yang
menuntut pembaca membuka lampiran. Lampiran murni tambahan. Kalau juri membaca
batas 10 halaman secara ketat, laporan tetap memenuhinya.

Markup sama dengan `content.py`; lihat README bagian 4.
"""

LAMPIRAN_PEMBUKA = [
    "Badan laporan berakhir bersama daftar pustaka pada halaman 10, sesuai batas juknis pasal "
    "3.b. Lampiran berikut ditambahkan menurut pasal 3.d dan memuat bahan pendukung yang tidak "
    "muat di badan naskah: enam gambar yang menjelaskan kerangka analisis lebih pelan, katalog "
    "blok fitur, tangga skor papan peringkat selengkapnya, dua tabel katalog kegagalan, kontrak "
    "reproduksibilitas, dan audit per kanal untuk seluruh 24 kolom eksogen. Tidak ada argumen di "
    "Bagian I–VII yang bergantung pada isi lampiran; seluruhnya memperdalam, bukan melengkapi."
]

# ---------------------------------------------------------------- Lampiran A
LAMP_DEKOMPOSISI = [
    "Persamaan ({E:rh}) menyatakan bahwa kelembapan relatif adalah rasio, dan Gambar "
    "{G:dekomposisi} memperlihatkan apa arti pernyataan itu pada data yang sebenarnya. Ketiga "
    "panel memuat sepuluh hari yang sama.",

    "Panel (a) adalah target: berayun 40 %RH setiap hari, berpuncak menjelang subuh dan berlembah "
    "pada sore hari. Panel (b) adalah tekanan uap jenuh *e*_{s}(*T*), yang berayun sama tajamnya "
    "dan **berlawanan fase**, dan yang diketahui persis pada setiap baris uji karena suhu "
    "termasuk kanal yang disediakan panitia. Panel (c) adalah tekanan uap aktual *e*, satu-satunya "
    "besaran yang harus diduga.",

    "Yang perlu diperhatikan adalah perbedaan **bentuk**, dan bukan hanya skala. Panel (a) dan (b) "
    "adalah deret bergerigi dengan struktur harian yang tajam; panel (c) jauh lebih tenang, dengan "
    "penggal datar yang bertahan setengah hari dan transisi yang berlangsung beberapa jam. Massa "
    "udara berganti perlahan; suhu berganti cepat. Itulah seluruh isi keputusan untuk memodelkan "
    "*e* dan bukan RH.",

    "Namun panel (c) juga memperingatkan bahwa penyederhanaan yang paling menggoda tidak berlaku. "
    "*e* memang lebih tenang daripada RH, tetapi ia **tidak** konstan di dalam satu hari: "
    "simpangan bakunya di dalam hari 2,56 hPa terhadap 2,91 hPa antar-hari. Pendekatan “satu "
    "tingkat kelembapan per hari, lalu bagi dengan *e*_{s}(*T*)” karena itu membuang hampir "
    "separuh sinyal sejak awal, dan Bagian III-B mengukur harganya sebagai RMSE 8,37.",
]


LAMP_PROKSI = [
    "Persamaan ({E:proksi}) menduga kelembapan relatif dari suhu saja, tanpa satu pun parameter "
    "yang dipasang pada data. Gambar {G:proksi} memperlihatkan seberapa jauh dugaan sepolos itu "
    "membawa kita.",

    "Panel (a) adalah sebaran gabungan penduga terhadap target pada seluruh baris latih. "
    "Korelasinya 0,908 dan RMSE mentahnya 9,1 %RH, dicapai tanpa pelatihan apa pun. Titik-titik "
    "berkumpul rapat di sekitar garis identitas pada rentang menengah dan melebar di kedua ujung, "
    "yang wajar: pada RH tinggi udara mendekati jenuh sehingga proksi menabrak langit-langit, "
    "sedangkan pada RH rendah minimum harian bukan lagi pendekatan titik embun yang baik karena "
    "udara tidak pernah cukup dingin untuk mengembun.",

    "Panel (b) menempatkan kedua deret berdampingan pada sepuluh hari. Bacaan yang penting ada "
    "pada pemisahan bentuk dan tingkat: fase dan sebagian besar amplitudo diurnal sudah benar, "
    "dan yang meleset adalah tingkat hariannya. Pola kesalahan itu bertahan sampai ke model akhir, "
    "dan Bagian VI-C mengukurnya sebagai 39 % galat yang berupa offset per hari.",

    "Dua konsekuensi mengalir ke rekayasa fitur. Karena penduga terbaik yang tersedia secara "
    "cuma-cuma dibangun dari statistik urutan atas suhu, blok fitur terpenting pada Bagian "
    "IV-B seluruhnya berupa statistik urutan atas suhu dan bukan atas kelembapan. Dan karena "
    "kualitas penduga bergantung pada jendela tempat minimum diambil, versinya dihitung pada tiga "
    "jendela bergulir, yaitu 18 jam, 48 jam, dan 96 jam, sehingga model memperoleh tiga pandangan "
    "terhadap massa udara yang sama pada tiga skala waktu."
]

LAMP_DESPIKE = [
    "Bagian IV-A melaporkan efek penapis Hampel sebagai angka; Gambar {G:despiking} "
    "memperlihatkan bentuknya pada penggal dua minggu dengan penolakan terpadat.",

    "Empat dari 16 nilai di luar rentang 5–45 °C berada di jendela ini, dan ketiganya "
    "berdiri sebagai paku tunggal setinggi 20 sampai 35 °C di atas deret yang median hariannya "
    "27 °C. Paku setinggi itu bukan cuaca. Yang perlu diperhatikan justru bagian yang **tidak** "
    "berubah: seluruh transisi diurnal yang asli, termasuk kenaikan pagi yang curam dan lembah "
    "malam yang dalam, dilewati penapis tanpa disentuh.",

    "Itulah yang dikejar oleh dua pilihan pada Persamaan ({E:hampel}). Skala robusnya diambil dari "
    "IQR bergulir sepanjang 289 titik, sekitar enam hari, sehingga penggal yang kebetulan tenang "
    "tidak membuat setiap riak kecil ditandai sebagai pencilan. Dan ambangnya sengaja longgar pada "
    "*k* = 6, karena yang harus dibuang adalah ekskursi yang secara fisis mustahil, bukan "
    "transisi cepat yang asli. Ventilasi yang terbuka dan awan yang lewat menghasilkan lompatan "
    "tajam yang nyata, dan lompatan itu justru informatif bagi model."
]


LAMP_DUKUNGAN = [
    "Bagian III-E melaporkan bahwa 13 kanal kehilangan lebih dari sepertiga sebaran latihnya di "
    "jendela uji. Gambar {G:dukungan} memuat auditnya per kolom, sebagai rasio simpangan baku uji "
    "terhadap simpangan baku latih.",

    "Kolom yang rasionya mendekati satu berperilaku sama di kedua belahan dan aman dipakai. Yang "
    "mendekati nol runtuh. Ketiga kolom `water_volume_*` benar-benar konstan di jendela uji "
    "sehingga rasionya persis nol, karena irigasi berhenti sepanjang periode itu. Blok probe "
    "tanah mengikuti, sebab kelembapan dan konduktivitas tanah berhenti berfluktuasi begitu tidak "
    "ada air yang masuk.",

    "Dua keputusan di badan naskah bersandar pada gambar ini. Blok tanah dan irigasi dibuang "
    "seluruhnya dari matriks fitur, karena pohon yang dilatih pada rezim irigasi aktif akan "
    "mengekstrapolasi ke daun yang rezimnya sudah tidak ada di jendela uji. Dan anggota linear "
    "diperlakukan dengan hati-hati, karena model linear mengekstrapolasi tanpa batas ke luar "
    "dukungan; salah satu di antaranya akhirnya dibuang dari *blend* justru karena alasan ini."
]

LAMP_DIURNAL = [
    "Gambar {G:diurnal} memuat klimatologi diurnal ketiga kanal iklim mikro yang cepat, "
    "dirata-ratakan atas seluruh baris latih dengan pita ±1 simpangan baku.",

    "Tiga hal terbaca. **Jam-hari saja menjelaskan 62,8 % ragam target**, dengan amplitudo rerata "
    "harian 41,13 %RH terhadap simpangan baku keseluruhan 18,00 %RH, jadi hampir seluruh ragam "
    "target adalah ayunan harian yang sama, berulang. **RH dan suhu adalah bayangan cermin**, "
    "berkorelasi −0,871, konsekuensi langsung Persamaan ({E:rh}). Dan **CO₂ berpuncak menjelang "
    "subuh**, tepat ketika RH berpuncak, karena keduanya menjejak besaran fisis yang sama: lapisan "
    "batas malam yang dangkal dan tenang memerangkap uap air sekaligus CO₂ respirasi. Itulah "
    "alasan blok fitur `ordstat` memakai statistik urutan CO₂ sebagai penjejak laju ventilasi.",

    "Konsekuensi praktisnya menyangkut rekayasa fitur. Waktu-hari masuk sebagai harmonik "
    "sinus/kosinus yang kontinu, bukan sebagai penanda kategorik per setengah jam. Penanda "
    "kategorik memberi model 48 parameter bebas yang dapat menghafal hari tertentu di dalam data "
    "latih; harmonik memaksanya mempelajari bentuk yang mulus dan berlaku umum.",
]

LAMP_VALIDASI = [
    "Gambar {G:rolling} menggambarkan protokol validasi yang dipakai di seluruh tulisan ini. "
    "Setiap batang adalah satu lipatan: bagian gelap adalah data latihnya, bagian terang adalah "
    "15 hari berikutnya yang dinilai. Titik potongnya bergerak maju dua hari setiap lipatan, "
    "dengan minimum 30 hari data latih, sehingga terbentuk sembilan lipatan.",

    "Baris paling bawah adalah tugas yang sebenarnya, dan kemiripan bentuknya dengan sembilan "
    "baris di atasnya adalah **seluruh alasan protokol ini dipilih**. Setiap lipatan meniru "
    "hubungan yang sama antara data latih dan blok yang dinilai: kontigu, maju, dan tanpa satu pun "
    "label di sisi yang dinilai.",

    "Bandingkan dengan lipatan acak. Dengan autokorelasi 0,979 pada lag satu, lipatan acak "
    "menempatkan tetangga langsung sebuah baris di sisi latih, sehingga skornya mengukur seberapa "
    "baik model **menginterpolasi** di antara dua titik yang sudah diketahui. Itu persoalan yang "
    "jauh lebih mudah, dan bukan persoalan yang dinilai kompetisi.",

    "Perhatikan juga bahwa lipatan di sini **tumpang tindih**. Itu disengaja, karena 61 hari data "
    "tidak cukup untuk sembilan blok yang saling lepas, tetapi ia berarti kesembilan skornya "
    "berkorelasi dan tidak boleh diperlakukan sebagai sembilan pengamatan bebas. Bagian VI-D "
    "memperlihatkan akibatnya secara kuantitatif: blok maju kami melebih-lebihkan besaran galat "
    "tingkat-level 2 sampai 6 kali.",
]

# ---------------------------------------------------------------- Lampiran B


LAMP_FITUR = [
    "Bagian IV-B menerangkan logika kelima blok fitur; Tabel {T:fitur} memerinci isinya kolom per "
    "kolom beserta pertanyaan fisis yang dijawab masing-masing.",

    "Yang perlu diperhatikan pada tabel ini adalah kolom terakhir. Setiap blok masuk karena ada "
    "satu pertanyaan fisis yang ingin dijawab, dan pertanyaan itulah yang menentukan bentuk "
    "operatornya, bukan sebaliknya. Blok `qblock` adalah contoh paling jelas. Minimum keras dan "
    "persentil-5 atas jendela yang sama tampak seperti dua versi besaran yang sama, tetapi yang "
    "pertama melaporkan satu sampel terdingin sedangkan yang kedua melaporkan letak massa "
    "dinginnya, dan celah di antara keduanya adalah sinyal tersendiri tentang seberapa panjang "
    "ekor dingin malam itu."
]

LAMP_GAGAL_INTERNAL = [
    "Bagian VI-E meringkas katalog kegagalan; Tabel {T:gagal_internal} memuat versi lengkapnya "
    "untuk arah yang ditolak berdasarkan pengukuran internal. Setiap baris diukur pada protokol "
    "maju yang sama dengan yang menilai konfigurasi yang akhirnya dikapalkan, sehingga angkanya "
    "sebanding satu sama lain.",

    "Kolom ketiga adalah yang paling berharga. Ia menyebut pelajaran yang dibawa kegagalan itu, "
    "dan bukan hanya mencatat bahwa arahnya buntu, dan beberapa di antaranya membentuk keputusan "
    "lain di naskah ini. Temuan bahwa lintasan model sudah dua kali lebih mulus daripada "
    "kebenaran, misalnya, adalah alasan rekonsiliasi lintasan di Bagian V-D dirancang mengikat "
    "prediksi perubahan yang dipelajari dan bukan memasang penalti kehalusan bebas-parameter."
]

LAMP_TANGGA = [
    "Gambar {G:tangga} di badan naskah menggambarkan tangga skor papan peringkat publik. "
    "Tabel {T:tangga} memuat angkanya lengkap, termasuk empat konfigurasi yang justru "
    "merugikan dan tetap kami laporkan. Setiap baris adalah satu berkas *submission* yang "
    "benar-benar dikirim, dan skornya adalah yang dikembalikan papan peringkat atas berkas "
    "itu, bukan dugaan internal."
]

LAMP_KEGAGALAN = [
    "Tabel {T:gagal_lb} memerinci kelompok kegagalan yang paling instruktif, yang di badan naskah "
    "hanya diringkas pada Bagian VI-E: perubahan yang bukti internalnya kuat, sebagian bahkan "
    "menang di **seluruh** lipatan, dan tetap merugikan di papan peringkat.",

    "Kolom ketiga adalah yang paling berharga, karena ia menyebut mekanisme kegagalannya dan bukan "
    "sekadar mencatat bahwa skornya memburuk. Polanya sama pada keempat baris pertama: besaran "
    "yang dikoreksi memang ada di blok validasi, tetapi **tidak ada di jendela uji**, atau ada "
    "dengan tanda yang berlawanan. Validasi silang mengukur besaran itu dengan benar di tempat ia "
    "diukur; yang salah adalah anggapan bahwa besaran yang sama menunggu di jendela uji.",

    "Baris pertama layak dibaca dua kali. Kemiringan kalibrasi dispersi menang di 13 dari 13 "
    "lipatan pada tiga keluarga lipatan yang dibangun berbeda-beda, lalu kalah +0,237. Itu "
    "kerugian terbesar yang pernah kami alami, hampir sepuluh kali lipat perbaikan *blending* terbaik "
    "kami dan satu setengah kali perbaikan terbesar kami. Sebabnya "
    "dapat diperiksa **tanpa papan peringkat sama sekali**: simpangan baku prediksi jendela uji "
    "18,8, sementara setiap lipatan validasi silang berada di 16,2–17,5. Pemadatan amplitudo yang "
    "hendak dibatalkan koreksi itu tidak ada di jendela uji. Satu perbandingan simpangan baku "
    "sudah cukup untuk menolaknya, dan kami tidak melakukannya.",
]

# ---------------------------------------------------------------- Lampiran C
LAMP_REPRO = [
    "Juknis pasal 2.e menjadikan ketidaksesuaian antara skor notebook dan skor Kaggle sebagai "
    "alasan **diskualifikasi**, bukan pengurangan nilai. Tabel {T:repro} memuat seluruh butir "
    "yang membuat kesesuaian itu dapat diperiksa pihak ketiga tanpa perlu mempercayai kami: "
    "jalankan notebook, ambil berkas yang ditulisnya, unggah ke Kaggle, dan bandingkan skornya "
    "dengan yang tercantum di sana.",

    "**Mengapa md5 berkas bukan kriterianya.** Kami mula-mula memakai md5 berkas mentah sebagai "
    "pemeriksa internal, dan ia gagal pada eksekusi penuh pertama. Penyebabnya satu baris yang "
    "berbeda sebesar 3,55 × 10⁻¹⁵: penyelesai jarang pada Persamaan ({E:normal}) tidak "
    "reproducible sampai bit terakhir antar-jalankan karena penjadwalan pustaka aljabar linear "
    "di bawahnya. Perbedaan sebesar itu tidak dapat menggeser skor pada presisi mana pun yang "
    "dilaporkan Kaggle, tetapi cukup untuk mengubah satu karakter teks CSV dan karenanya md5 "
    "berkasnya. Kedua nilai md5 karena itu dicantumkan apa adanya di Tabel {T:repro}, termasuk "
    "fakta bahwa keduanya berbeda.",

    "**Dan mengapa notebook tidak memeriksa dirinya sendiri.** Kami sempat memakai digest atas "
    "nilai prediksi yang dibulatkan ke enam desimal, yang kebal terhadap derau penyelesai "
    "jarang. Ia cocok di mesin yang sama, tetapi tidak lintas mesin: menjalankan notebook pada "
    "Python, NumPy, dan SciPy yang lebih baru, dengan versi LightGBM dan CatBoost yang persis "
    "sama, menggeser prediksi sebesar RMS 0,29 %RH dengan maksimum 0,87 %RH. Penyebabnya dapat "
    "dipersempit: audit residu, klimatologi, dan kedua anggota linear reproduksi sampai digit "
    "terakhir, sedangkan ketiga anggota pohon bergeser, karena kedua pustaka itu menyusun "
    "histogramnya dengan penjumlahan yang bergantung urutan thread. Pemeriksa yang gagal karena "
    "derau sebesar itu akan mengubah selisih tak berpengaruh menjadi notebook yang berhenti "
    "dengan galat, padahal juknis 2.e justru menuntut eksekusi tanpa galat. Notebook karena itu "
    "hanya memeriksa bentuk berkasnya dan mencetak md5 beserta skor publiknya; kesesuaian skor "
    "diperiksa dengan mengunggah berkas itu ke Kaggle.",
]

# ---------------------------------------------------------------- Lampiran D

LAMP_ANATOMI = [
    "Tabel {T:anatomi} merangkum anatomi kedua belahan dataset berdampingan. Ia dirujuk dari "
    "Bagian II-A dan sengaja ditempatkan di sini bersama audit per kanal, karena keduanya "
    "menjawab pertanyaan yang sama pada dua tingkat kerincian.",

    "Baris yang paling menentukan adalah tiga yang terakhir. Nilai hilang berada pada tingkat "
    "yang sama di kedua belahan dan tersebar, bukan berbentuk blok mati alat, sehingga "
    "penambalannya tidak mengarang rezim. `env_battery` praktis kosong di keduanya dan seluruh "
    "nilai yang ada bernilai 100, sehingga ia tidak membawa informasi apa pun. Dan "
    "`water_volume_*` yang bervariasi di latih tetapi konstan di uji adalah sinyal paling awal "
    "bahwa jendela uji berada pada rezim irigasi yang berbeda, jauh sebelum audit dukungan di "
    "Lampiran D mengukurnya."
]

LAMP_KANAL = [
    "Tabel {T:kanal} memuat audit lengkap seluruh 24 kanal eksogen, yang di badan naskah hanya "
    "diringkas sebagai Gambar {G:dukungan}. Kolom terakhir menyatakan apakah kanal itu masuk ke "
    "matriks fitur akhir.",

    "**Blok tanah dan irigasi runtuh.** Ketiga `water_volume_*` benar-benar konstan di jendela uji "
    "sehingga rasio simpangan bakunya nol, dan probe tanah turun ke 0,15–0,66 kali sebaran "
    "latihnya. Irigasi berhenti, atau pencatatannya berhenti, selama jendela uji. Statistik "
    "bergulir dari blok ini karena itu berada jauh di luar dukungan latih, dan pohon yang "
    "membacanya akan mengekstrapolasi ke daun yang dipelajari pada rezim yang sudah tidak ada.",

    "**Dua kanal tidak membawa informasi sama sekali.** `env_battery` hilang pada 98 % baris dan "
    "seluruh nilai yang ada bernilai 100. `env_id` adalah pengenal rekaman yang reratanya melonjak "
    "dari 95.732 di data latih menjadi 190.968 di data uji; ia menandai penomoran berkas, bukan "
    "besaran fisis, dan memasukkannya berarti memberi model penanda waktu terselubung yang tidak "
    "berlaku di luar rentang ini.",

    "**Kanal yang dipertahankan bergeser, tetapi tetap punya dukungan.** Suhu udara, CO₂, dan "
    "tekanan barometrik seluruhnya berada di rasio 0,87–1,09, jadi sebaran ujinya masih sebanding "
    "dengan sebaran latihnya meskipun **rerata**-nya bergeser: suhu turun dari 27,56 °C ke "
    "24,58 °C. Itu pergeseran lokasi, bukan hilangnya dukungan, dan pergeseran lokasi dapat "
    "ditangani model asalkan bentuk sebarannya bertahan. Indeks agronomi berada di 0,61–0,78, "
    "batas yang masih dapat diterima, dan blok itu tetap dipakai karena alasan di Bagian III-D: ia "
    "memuat versi **bersih** dari suhu minimum harian, prediktor fisis terkuat yang kami punya.",

    "Perhatikan juga bahwa kelengkapan data justru **memburuk** di jendela uji, khusus pada blok "
    "agronomi, dari sekitar 10 % hilang menjadi 15–17,6 %. Karena blok itu konstan sepanjang hari "
    "agronomi 22.00-ke-22.00, lubangnya dapat ditambal dari baris lain di hari yang sama tanpa "
    "kehilangan informasi apa pun. Itu salah satu alasan rekayasa balik di Bagian III-D bernilai "
    "praktis dan bukan hanya menarik.",
]
