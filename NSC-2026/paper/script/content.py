# -*- coding: utf-8 -*-
"""Seluruh teks naskah NSC 2026 - Prediksi Kelembapan Udara.

Ini satu-satunya berkas yang perlu disunting untuk mengubah kalimat mana pun di
naskah. Angka di dalamnya harus dapat ditemukan di keluaran `make_figures.py`;
jangan mengetik angka dari ingatan.

Markup: **tebal**, *miring*. Untuk tanda kurang pakai U+2212 (−), bukan hyphen.
Markup rumus (hanya berlaku di daftar EQ_*): *v* memiringkan variabel,
_{k} subskrip, ^{2} superskrip.
"""

JUDUL = ("Reformulasi Fisis dan Rekonsiliasi Lintasan untuk Peramalan "
         "Kelembapan Udara Multivariat 15 Hari ke Depan")

PENULIS = [
    ("Timotius Christopher Patrick Sihombing", "164241005",
     "timotius.christopher.patrick-2024@ftmm.unair.ac.id"),
    ("Raphael Angelo Adikara Purnama", "164241055",
     "raphael.angelo.adikara-2024@ftmm.unair.ac.id"),
]
PRODI = "Program Studi Teknologi Sains Data"
FAKULTAS = "Fakultas Teknologi Maju dan Multidisiplin"
UNIV = "Universitas Airlangga, Surabaya, Indonesia"

NAMA_TIM = "Heisenberg"

INTISARI = (
    "Peramalan kelembapan udara bernilai operasional langsung bagi pertanian presisi. Kami meramalkan 734 titik "
    "setengah-jaman selama 15,3 hari ke depan dari 2.933 baris latih dan 24 kanal sensor eksogen "
    "yang juga tersedia sepanjang jendela uji, 11 di antaranya bertahan sampai matriks fitur "
    "akhir. Yang menentukan hasilnya adalah penulisan ulang persoalannya, bukan pemilihan model: "
    "karena kelembapan relatif adalah rasio tekanan uap aktual terhadap tekanan uap jenuh "
    "sedangkan suhu diketahui persis pada waktu uji, seluruh ketidaktahuan berpindah ke tekanan "
    "uap. Kurva *oracle* mengubahnya jadi pengukuran: tekanan uap harian yang sempurna "
    "pun hanya memberi RMSE 8,37, sedangkan *stack* kami setara mengetahuinya pada resolusi 6,1 jam. Di atas enam anggota yang dipadukan lewat kuadrat-terkecil non-negatif per "
    "pita waktu-hari, satu langkah memperlakukan jendela uji sebagai deret waktu: rekonsiliasi "
    "lintasan atas 734 baris lewat satu solve jarang, bernilai −0,160 RMSE atau tujuh kali "
    "perbaikan *blending* terbaik. Temuan tak terduga: bias level maju −2,89 %RH pada satu "
    "anggota yang di dalam sampelnya tak bias, tak terlihat oleh komponen pipeline mana pun. Seluruh pemilihan model dilakukan pada validasi silang titik-asal bergulir; papan peringkat "
    "tidak pernah dipakai memilih model, dan tiga koreksi pasca-model yang lolos validasi "
    "internal justru ditolak olehnya. Pada sembilan lipatan titik-asal bergulir yang sama, "
    "*stack* ini 15,8 % lebih baik daripada satu LightGBM tunggal dan unggul di kesembilannya. RMSE publik akhir 2,82744, dari garis dasar naif 18,0."
)

KATA_KUNCI = ("peramalan kelembapan udara, gradient boosting, rekonsiliasi ramalan, "
              "tekanan uap air, kalibrasi model, validasi silang deret waktu")

# ============================================================================
# I. PENDAHULUAN
# ============================================================================

PENDAHULUAN_LATAR = [
    "Kelembapan udara adalah salah satu peubah lingkungan yang paling banyak dipakai dan paling "
    "sedikit diramalkan dengan baik pada skala petak. Bersama suhu ia menentukan defisit tekanan "
    "uap, besaran yang mengendalikan laju transpirasi tanaman sekaligus membuka atau menutup "
    "jendela infeksi bagi patogen jamur. Rumah kaca dan lahan hortikultura modern memakainya "
    "untuk menjadwalkan ventilasi, pengabutan, dan irigasi beberapa jam sampai beberapa hari di "
    "muka. Sensor kelembapan sendiri, di sisi lain, adalah komponen yang paling sering gagal dan "
    "paling cepat melenceng kalibrasinya pada satu stasiun iklim mikro. Kemampuan merekonstruksi "
    "kelembapan dari kanal-kanal lain yang masih hidup karena itu adalah bentuk redundansi yang "
    "murah, bukan latihan akademis.",

    "Tema cabang lomba ini, *Transforming Present Multivariate Insights to Shape the Future of "
    "Predictive Analytics*, menyebut dua hal yang persis menjadi bentuk persoalan kami: masukan "
    "yang multivariat dan keluaran yang prediktif. Kami memakai 24 kanal sensor eksogen yang "
    "terekam serempak dengan target (iklim mikro cepat, tiga jalur probe tanah, tiga penghitung "
    "volume irigasi, dan tujuh indeks agronomi harian) untuk meramalkan 734 titik setengah-jaman "
    "ke depan.",

    "Yang membentuk seluruh rancangan solusi adalah bentuk pemisahan latih dan uji. Jendela uji "
    "adalah blok kontigu 15,3 hari tepat setelah jendela latih berakhir, bukan cuplikan acak. "
    "Tidak ada satu pun label di dalamnya, sehingga tidak ada suku autoregresif yang boleh "
    "dipakai; namun seluruh 24 kanal eksogen tersedia pada setiap baris uji. Ini bukan peramalan "
    "buta dan bukan pula interpolasi: ini rekonstruksi kelembapan dari jejak sensor lengkap pada "
    "rezim iklim yang belum pernah dilihat model. Perbedaan itu menentukan fitur apa yang sah, "
    "protokol validasi apa yang tidak berbohong, dan komponen mana yang akhirnya membayar.",
]

KONTRIBUSI_PEMBUKA = [
    "Tulisan ini memberi empat kontribusi yang masing-masing dibayar dengan angka, bukan dengan "
    "klaim:",
]

KONTRIBUSI_ITEMS = [
    "**Reformulasi fisis yang terukur.** Kami menulis ulang persoalan dari meramalkan RH menjadi "
    "menduga tekanan uap air, lalu membangun *kurva oracle* yang menyatakan berapa RMSE yang "
    "dihasilkan kalau tekanan uap diketahui sempurna pada resolusi waktu tertentu. Kurva itu "
    "memberi ukuran objektif untuk seluruh sisa pekerjaan dan langsung mematikan satu keluarga "
    "arsitektur yang tampak paling wajar.",

    "**Rekonsiliasi lintasan sebagai satu-satunya komponen deret waktu.** Kami menunjukkan bahwa "
    "seluruh pipeline berbasis baris meninggalkan informasi di atas meja karena galat modelnya "
    "berautokorelasi 0,93, dan bahwa mengikat 734 baris uji lewat satu solve kuadrat-terkecil "
    "jarang memanen informasi itu dengan −0,160 RMSE.",

    "**Cacat kalibrasi yang tidak terlihat instrumen mana pun.** Kami melaporkan bias level maju "
    "−2,89 %RH pada satu anggota *blend* yang bias di dalam sampelnya −0,006, menjelaskan mengapa "
    "tidak satu pun komponen pipeline berbentuk cukup untuk melihatnya, dan memperlihatkan bahwa "
    "koreksi satu-skalar atasnya bernilai −0,022 RMSE.",

    "**Batas kegunaan validasi silang, diukur dan bukan didalilkan.** Validasi silang memeringkat "
    "perubahan pada model dengan andal, tetapi untuk koreksi yang diterapkan *setelah* model ia "
    "perlu dan tidak cukup: tiga koreksi lolos validasi internal, satu di antaranya menang di 13 "
    "dari 13 lipatan, lalu tetap merugikan pada jendela uji. Kami melaporkan mekanisme "
    "kegagalannya satu per satu dan menarik aturan yang dapat dipakai ulang darinya.",
]

KONTRIBUSI_PENUTUP = [
    "Arah-arah yang gagal, beserta alasan terukurnya, ada di Bagian VI-E."
]

# ============================================================================
# II. AKUISISI DAN EKSPLORASI DATA
# ============================================================================

DATA_ANATOMI = [
    "Data berasal dari satu stasiun pemantauan lingkungan pertanian: sebuah *logger* iklim mikro "
    "(CO₂, tekanan barometrik, suhu udara, kelembapan udara) yang dipasangkan dengan tiga jalur "
    "probe tanah (konduktivitas listrik, kelembapan, suhu), tiga penghitung volume air irigasi, "
    "dan tujuh indeks agronomi harian yang diturunkan dari suhu. Tabel {T:anatomi} di lampiran "
    "merangkum anatominya.",

    "Kisi waktu latih tidak sempurna: selangnya 30 menit di 2.931 dari 2.932 transisi, dengan "
    "satu lompatan tunggal selama 7 jam, sementara kisi uji sempurna. Akibatnya setiap operator "
    "berbasis geseran di seluruh pipeline dibangun di atas kisi setengah-jaman yang sudah "
    "dilengkapi, bukan di atas nomor baris; kalau tidak, geseran empat langkah akan berarti "
    "“empat baris”, bukan “dua jam”, tepat di sekitar lompatan itu. Atas alasan yang sama, "
    "penambalan lubang memakai interpolasi terhadap indeks waktu.",

    "Tiga hal langsung terbaca dari anatomi itu. Nilai hilang berkisar 9,0–10,8 % pada belahan latih "
    "dan 8,6–17,6 % pada belahan uji, tersebar dan bukan berbentuk blok mati alat, sehingga dapat "
    "ditambal tanpa mengarang rezim. Kolom `env_battery` praktis kosong (98 % hilang) dan seluruh "
    "nilai yang ada bernilai 100, jadi ia dibuang. Dan blok tanah serta irigasi runtuh di jendela "
    "uji: `water_volume_*` benar-benar konstan di sana.",
]

DATA_PEMISAHAN = [
    "Gambar {G:target}(a) memperlihatkan target sepanjang kalender beserta blok yang harus diramalkan. "
    "Amplitudo diurnalnya 41,13 %RH terhadap simpangan baku keseluruhan 18,00 %RH, jadi hampir "
    "seluruh ragam target adalah ayunan harian. Gambar {G:target}(b) memperlihatkan sesuatu yang lebih "
    "mengganggu: suhu udara mentah, prediktor tunggal terkuat kami, memuat 16 nilai yang secara "
    "fisis mustahil, dari −6,33 °C sampai +60,64 °C, di dalam deret yang median hariannya 27 °C. "
    "Karena ∂RH/∂T sekitar −3,6 %RH per °C pada RH 60 %, satu lonjakan suhu 20 °C yang lolos "
    "menghasilkan prediksi yang meleset puluhan persen pada baris tersebut. Bagian IV menanganinya.",
]

DATA_KORUPSI = [
    "Sebelum satu model pun dipasang, ada satu pertanyaan yang harus dijawab lebih dulu: apakah "
    "targetnya sendiri berderau? Kalau `air_humidity` mengandung derau putih sebesar σ, maka RMSE "
    "tidak akan pernah turun di bawah σ dan seluruh usaha pemodelan punya lantai yang tidak dapat "
    "ditembus.",

    "Ujinya adalah residu interpolasi kuadratik tinggalkan-satu: untuk setiap titik kami memasang "
    "parabola pada empat tetangganya pada *t*−2, *t*−1, *t*+1, dan *t*+2, lalu memprediksi titik "
    "itu sendiri. Sinyal mulus memberi residu kecil; derau putih memberi residu besar berekor "
    "pendek; lonjakan yang disuntikkan memberi residu besar berekor sangat panjang. Perbandingan "
    "simpangan baku biasa terhadap simpangan baku robus, 1,4826 kali median deviasi absolut, "
    "memisahkan dua kemungkinan terakhir.",

    "Gambar {G:residu} dan Tabel {T:korupsi} memuat hasilnya, dan pemisahannya tegas. Target memberi rasio 1,20, ekor "
    "yang hampir normal, tanpa tanda lonjakan suntikan. Suhu udara memberi 5,75 dan tekanan "
    "barometrik 6,86, keduanya berekor sangat berat. **Targetnya bersih; prediktornyalah yang "
    "dikorupsi.** Dua konsekuensi mengalir dari sini dan keduanya membentuk sisa pekerjaan. "
    "Pertama, tidak ada lantai derau label, sehingga RMSE rendah memang dapat dicapai secara "
    "prinsip dan tidak ada alasan berhenti pada angka tertentu. Kedua, nilai sebenarnya dari "
    "pra-pemrosesan di sini adalah merekonstruksi sinyal *masukan*, bukan membersihkan target. "
    "Itulah satu-satunya alasan langkah *despiking* di Bagian IV ada.",

    "Korupsinya juga selektif per kolom, bukan derau seragam yang ditebar ke seluruh berkas. "
    "`soil_temp_line1`, deret paling mulus di dataset, memberi rasio 1,04 dan tidak dilonjaki "
    "sama sekali.",
]

# ============================================================================
# III. METODE ANALISIS
# ============================================================================

METODE_PEMBUKA = [
    "Bagian ini memuat kerangka analisis yang mendahului seluruh pemodelan: identitas "
    "termodinamika yang menulis ulang persoalan, batas *oracle* yang mengukur seberapa jauh "
    "penulisan ulang itu bisa membawa kami, dua penduga fisis bebas-parameter yang lahir "
    "darinya, audit pergeseran distribusi, dan protokol validasi."
]

METODE_FISIS = [
    "Kelembapan relatif bukan besaran keadaan yang berdiri sendiri. Ia adalah rasio antara "
    "tekanan uap air aktual dan tekanan uap jenuh pada suhu yang sama,",

    "dengan *e*_{s} diberikan oleh parameterisasi Magnus–Bolton {R:bolton}",

    "yang menghasilkan hPa untuk suhu dalam derajat Celsius. Bentuk ({E:rh}) tampak sepele, tetapi "
    "implikasinya tidak. Penyebut *e*_{s}(*T*(*t*)) diketahui persis pada setiap baris uji, "
    "karena suhu udara termasuk kanal eksogen yang disediakan sepanjang jendela uji. Seluruh "
    "ketidaktahuan karena itu berpindah ke pembilang.",

    "Perpindahan itu mengubah pertanyaannya secara mendasar. “Berapa RH besok pukul 03.00” adalah "
    "pertanyaan tentang besaran yang bergerak 41 %RH dalam sehari; “berapa tekanan uap massa "
    "udara besok” adalah pertanyaan tentang besaran yang hanya berubah oleh adveksi, kondensasi, "
    "evapotranspirasi, dan ventilasi. RH dan *e*_{s}(*T*) berayun tajam dan berlawanan fase, "
    "sedangkan *e* bergerak jauh lebih tenang: simpangan bakunya di dalam satu hari 2,56 hPa "
    "dibanding 2,91 hPa antar-hari.",

    "Angka kedua itu penting dan sering diabaikan. Ragam *e* di dalam satu hari hampir sebesar "
    "ragamnya antar-hari. Pendekatan yang tampak paling wajar, yaitu menebak satu tingkat "
    "kelembapan per hari lalu membaginya dengan *e*_{s}(*T*) untuk memperoleh bentuk diurnalnya, "
    "karena itu kehilangan hampir separuh sinyal sejak awal. Sub-bagian berikut mengukur berapa persisnya "
    "harga pendekatan itu.",
]

METODE_ORACLE = [
    "Kami membangun keluarga *oracle*: penduga yang mengetahui *e* yang sebenarnya, tetapi hanya "
    "pada resolusi waktu tertentu. Untuk jendela *w* titik, oracle-nya adalah",

    "dengan tanda kurung sudut menyatakan rerata bergerak terpusat sepanjang *w* titik. Karena "
    "*e* dihitung dari target yang sebenarnya, konstruksi ini tidak dapat dipakai untuk "
    "memprediksi apa pun; ia dipakai sebagai penggaris.",

    "Gambar {G:oracle} memuat kurvanya. Bacaannya keras. Bahkan dengan "
    "tekanan uap harian yang sempurna, RMSE-nya 8,37, tiga kali lebih buruk daripada solusi "
    "yang akhirnya kami bangun. Setiap arsitektur yang memodelkan level harian lalu menempelkan "
    "bentuk diurnal generik dibatasi oleh angka itu, berapa pun bagusnya komponen "
    "pembelajarannya. Kami mengetahui ini sebelum melatih model pertama.",

    "Sebaliknya, model akhir kami dengan RMSE 2,827 mendarat di antara *oracle* 4,5 jam dan 6,5 jam, "
    "yaitu setara mengetahui tekanan uap yang sebenarnya pada resolusi sekitar **6,1 jam**. "
    "Ruang yang tersisa karena itu bersifat sub-harian: untuk turun ke RMSE 2,3 kami perlu "
    "mengetahui *e* sekitar 1,5 jam lebih halus lagi. Itulah alasan struktural mengapa "
    "rekonsiliasi lintasan di Bagian V-D ada, dan mengapa ia bernilai jauh lebih besar daripada "
    "perubahan lain mana pun.",
]

METODE_PROKSI = [
    "Identitas ({E:rh}) juga melahirkan satu penduga yang tidak memuat satu pun parameter terpasang. "
    "Udara lembap yang mendingin semalam akan turun sampai mencapai titik embunnya lalu berhenti "
    "di sana, karena kalor laten kondensasi menahan pendinginan lebih lanjut. Suhu minimum harian "
    "karena itu adalah pendekatan titik embun {R:fao56}, dan mensubstitusikannya ke ({E:rh}) memberi",

    "Gambar {G:proksi} memperlihatkan perilakunya. Satu rumus tanpa parameter apa pun, dibangun hanya dari "
    "suhu, sudah berkorelasi 0,908 dengan target dan mencapai RMSE mentah 9,1 %RH. Angka itu "
    "menetapkan garis dasar fisis yang harus dikalahkan setiap model pembelajaran mesin di sini, "
    "dan menjelaskan mengapa blok fitur terpenting pada Bagian IV-B seluruhnya berupa statistik "
    "urutan atas suhu, bukan statistik atas kelembapan. Versi jendela-bergulir 18 jam, "
    "48 jam, dan 96 jam memberi model tiga pandangan terhadap massa udara yang sama pada tiga "
    "skala waktu.",
]

METODE_AGRO = [
    "Tujuh kolom “harian” tampak seperti pembacaan per-baris karena nilainya berubah di setiap "
    "baris. Ternyata tidak. Menyapu batas hari dari 00.00 sampai 23.00 dan meminimumkan ragam di "
    "dalam hari menempatkan batasnya pada pukul 22.00: blok itu konstan sepanjang hari "
    "agronomi 22.00-ke-22.00, dengan derau 0,055–0,111 °C ditambahkan di atasnya. Dua di antaranya "
    "adalah salinan afin persis dari dua yang lain; `daily_max` − `daily_max_above_Tbase` = "
    "9,999 ± 0,157 dan `daily_mean_temperature` − `standard_day_degree` = 10,002 ± 0,109.",

    "Konsekuensi pertamanya menyangkut kesahihan. Blok harian dilaporkan pada *setiap* baris hari "
    "itu, sehingga pada pukul 02.00 berkas sudah menyatakan berapa maksimum hari itu nanti. Ini "
    "informasi yang sah karena panitia menyediakannya di `test.csv`; artinya indeks agronomi "
    "adalah ringkasan seluruh hari, bukan fitur masa lalu, dan harus diperlakukan sebagai "
    "ringkasan.",

    "Konsekuensi keduanya jauh lebih berguna. Identitas `daily_mean_temperature` = "
    "(*T*_{maks} + *T*_{min})/2 berlaku persis, sehingga rerata harian *T̄* dan maksimum harian "
    "*T*_{maks} memberi",

    "Dan indeks *Ontario Crop Heat Unit* {R:chu}, yang didefinisikan sebagai rerata dua suku "
    "*Y*_{maks} = 3,33(*T*_{maks} − 10) − 0,084(*T*_{maks} − 10)² dan "
    "*Y*_{min} = 1,8(*T*_{min} − 4,4), dapat "
    "dipecahkan secara aljabar untuk memberi jalur kedua yang sepenuhnya bebas dari yang pertama,",

    "Kedua rekonstruksi itu berkorelasi 0,99986 dan sepakat sampai simpangan baku 0,047 °C "
    "sepanjang 76 hari. Namun keduanya berbeda dari minimum yang teramati sensor dengan simpangan "
    "baku 0,43 °C setelah sensor dibersihkan, dan hanya berkorelasi 0,45 terhadap minimum "
    "sensor mentah. Selisih itu bukan galat rekonstruksi: blok agronomi dihitung sebelum "
    "korupsi disuntikkan, sehingga ia adalah versi bersih dari besaran yang sama.",

    "Jadi dataset ini memuat dua pengukuran atas suhu minimum harian, satu berderau dari "
    "sensor dan satu bersih dari indeks agronomi. Karena minimum harian adalah proksi titik embun "
    "kami lewat ({E:proksi}), nilai 0,43 °C itu diterjemahkan langsung menjadi sekitar 1,5 %RH derau pada "
    "prediktor fisis terkuat yang kami punya. Blok agronomi masuk ke matriks fitur justru karena "
    "alasan ini, bukan karena ia kebetulan tersedia.",
]

METODE_GESER = [
    "Validasi silang mengukur galat *di dalam* rezim latih. Kompetisi ini menilai pada blok "
    "15 hari sesudahnya, di musim yang lebih dingin dan dengan irigasi yang berhenti. Kami "
    "mengukur pergeseran itu sebelum satu model pun dipasang, karena besar-kecilnya menentukan "
    "seberapa jauh validasi silang boleh dipercaya.",

    "Jendela uji jelas berada di luar rezim. Suhu rata-rata turun dari 27,51 °C ke 24,64 °C, dan "
    "48,0 % baris uji jatuh di kuartil terdingin data latih dibanding 25 % secara definisi di "
    "data latih. Pendinginannya tidak simetris: rerata minimum harian turun 3,17 °C sementara "
    "rerata maksimum harian hanya turun 1,37 °C, sehingga ayunan diurnalnya melebar. Audit dukungan "
    "per kolom, yang dimuat Gambar {G:dukungan} di lampiran, mencatat 13 kolom kehilangan lebih "
    "dari sepertiga sebaran latihnya.",

    "Dua keputusan mengalir dari sini. **Blok tanah dan irigasi dibuang seluruhnya** dari matriks "
    "fitur: statistik bergulirnya di jendela uji hampir tidak punya dukungan latih, sehingga "
    "pohon akan mengekstrapolasi ke daun yang dipelajari pada rezim irigasi yang sudah tidak ada. "
    "**Anggota linear diperlakukan dengan hati-hati**, karena model linear mengekstrapolasi tanpa "
    "batas ke luar dukungan; salah satu di antaranya akhirnya dibuang dari *blend* justru karena "
    "alasan ini, dan pembuangannya memang membayar di papan peringkat (Bagian V-B).",
]

METODE_VALIDASI = [
    "Bagian ini paling menentukan hasil akhir dan paling mudah dikerjakan dengan salah.",

    "**Validasi silang acak akan berbohong di sini.** Baris pada dataset ini punya autokorelasi "
    "0,979 pada lag satu. Lipatan acak menempatkan tetangga langsung sebuah baris di sisi latih, "
    "sehingga skornya mengukur interpolasi, bukan peramalan. Ukuran sampel efektifnya sekitar "
    "62 hari, bukan 2.933 baris, dan itu membatasi apa saja yang bisa dipelajari pada "
    "skala harian.",

    "**Protokol yang kami pakai adalah titik-asal bergulir** {R:bergmeir}. "
    "Setiap lipatan dilatih pada segala sesuatu sebelum satu titik potong lalu divalidasi pada "
    "15 hari berikutnya, bentuk yang persis sama dengan tugas sebenarnya. Sembilan lipatan, "
    "langkah dua hari, minimum 30 hari data latih.",

    "**Dua peran harus dipisahkan.** Prediksi luar-lipatan dipakai untuk memasang bobot *blend* dan "
    "sekaligus untuk mengukur galat. Keduanya harus memakai baris yang sama tetapi tidak boleh "
    "saling mencemari, karena parameter yang dipasang pada baris yang sama dengan yang dinilai "
    "akan tampak lebih baik daripada yang sebenarnya. Karena itu setiap parameter meta di "
    "pipeline ini (bobot NNLS, koreksi bias diurnal, offset de-bias level) dipasang hanya pada "
    "baris luar-lipatan, lalu diterapkan tanpa perubahan pada jendela uji.",

    "**Protokol inilah yang memilih model, bukan papan peringkat.** Setiap anggota, blok fitur, "
    "hiperparameter, dan bobot *blend* dipilih pada sembilan lipatan di atas. Skor papan "
    "peringkat baru dibaca setelah sebuah konfigurasi dikapalkan, dan hanya menyentuh satu "
    "keluarga keputusan: koreksi yang diterapkan setelah model, seperti kalibrasi level dan "
    "dispersi. Bagian VI-E mencatat tiga koreksi yang lolos validasi internal lalu tetap ditolak "
    "di sana; anggota `l2` mencatat kebalikannya, dipertahankan meskipun papan peringkat sedikit "
    "lebih buruk dengannya, karena bukti internalnya positif.",
]

# ============================================================================
# IV. PRA-PEMROSESAN
# ============================================================================

PRA_DESPIKE = [
    "Dua langkah pra-pemrosesan, dan keduanya dibenarkan oleh pengukuran di Bagian II-C, bukan "
    "oleh kebiasaan.",

    "**Despiking Hampel.** Penapis Hampel terpusat {R:hampel} menandai titik yang menyimpang lebih dari "
    "*k* kali skala robus lokal dari median bergeraknya,",

    "dengan med_w median bergerak terpusat *w* titik dan *s*(*t*) skala robus. Dua pilihan di "
    "dalamnya penting, dan Lampiran C menguraikan keduanya: skalanya diambil dari IQR bergulir "
    "289 titik agar penggal yang kebetulan tenang tidak menandai setiap riak sebagai pencilan, "
    "dan ambangnya sengaja longgar pada *k* = 6 karena yang dikejar adalah ekskursi yang secara "
    "fisis mustahil, bukan transisi cepat yang asli.",

    "Gambar {G:despiking} memperlihatkan hasilnya pada penggal dengan penolakan terpadat, dan angkanya ada di "
    "Tabel {T:despiking} di lampiran. Penapis menyentuh 0,49 % nilai, membuang seluruh 16 nilai yang di luar rentang "
    "5–45 °C, dan menghapus 52 dari 57 ekskursi residu di atas 2,5 °C tanpa menyisakan satu pun "
    "di jendela uji. Simpangan baku residu tinggalkan-satu turun dari 2,715 ke 0,515, sementara "
    "simpangan baku robus-nya nyaris tidak bergerak, 0,472 ke 0,408. Itu tanda tangan dari "
    "membuang ekor sambil mempertahankan badan; kalau penapis meratakan dinamika yang asli, kedua "
    "angka akan turun bersama-sama.",

    "**Interpolasi terhadap waktu.** Setelah *despiking*, lubang ditambal dengan interpolasi "
    "terhadap indeks waktu dan bukan nomor baris, sehingga lompatan 7 jam pada data latih tidak "
    "diperlakukan sebagai selang 30 menit. Kolom kumulatif `gdd` dan `water_volume_*` tambahan "
    "dijaga monoton dengan `cummax` lalu diubah menjadi laju 24 jam, karena tingkat kumulatifnya "
    "sendiri hanyalah tren yang tidak punya arti prediktif lintas rezim.",
]

PRA_FITUR = [
    "Matriks fitur dibangun dari lima blok: `dasar` untuk keadaan sesaat dan konteks lokalnya "
    "pada tiga skala waktu, `tmin` untuk proksi titik embun Persamaan ({E:proksi}), `tend` "
    "untuk rezim sinoptik, `ordstat` untuk laju ventilasi lewat CO₂, dan `qblock` untuk "
    "persentil suhu. Setiap blok menjawab satu pertanyaan fisis; tidak ada blok yang "
    "ditambahkan dengan alasan “lebih banyak fitur biasanya membantu”, dan Tabel {T:fitur} di "
    "lampiran memerincinya. Blok tanah dibuang seluruhnya karena alasan dukungan di Bagian "
    "III-E.",

    "Ada satu pilihan desain yang harus dinyatakan terbuka karena sekilas ia terlihat seperti "
    "kebocoran. Jendela bergulir di pipeline ini terpusat, bukan kausal. Pada baris uji, "
    "rerata bergerak 24 jam merata-ratakan pembacaan sensor dari baris uji tetangga, termasuk yang "
    "*sesudah* baris tersebut. Itu adalah data fitur masa depan, dan ia sah di sini karena tiga "
    "alasan: panitia menyediakan seluruh kanal eksogen untuk seluruh jendela uji; tidak satu pun "
    "nilai target masa depan masuk ke mana pun; dan skenario yang dimodelkan memang “stasiun tetap "
    "merekam sepanjang periode uji, rekonstruksi kelembapannya”, bukan “ramalkan besok tanpa "
    "apa-apa”. Yang dilarang keras adalah nilai RH mana pun dari jendela validasi atau uji masuk "
    "sebagai masukan, dan larangan itu diverifikasi secara mekanis di Bagian V-E.",
]

# ============================================================================
# V. PEMODELAN
# ============================================================================

MODEL_ANGGOTA = [
    "Enam anggota dilatih, lima di antaranya bertahan sampai konfigurasi akhir. Tiga di antaranya "
    "adalah model pohon ter-*boost* (dua LightGBM {R:lgbm} dan satu CatBoost {R:catboost}), dan "
    "tiga sisanya linear. Tabel {T:anggota} memuat "
    "keenamnya beserta alasan masing-masing ada. Yang perlu ditekankan adalah bahwa dua di antara "
    "mereka ada bukan karena akurasi solonya.",

    "Anggota `cat` sengaja dibiarkan salah-spesifikasi: solonya lebih buruk 0,9 RMSE daripada "
    "CatBoost berkerugian kuadrat, tetapi korelasi residunya terhadap anggota utama hanya 0,64, "
    "terendah dari seluruh anggota pohon. Yang dibeli *blend* darinya dekorelasi, bukan akurasi. "
    "Anggota `ridge_e` dipasang di ruang tekanan uap lalu dikonversi balik lewat ({E:rh}), "
    "sehingga ia meminimumkan galat pada *e* dan bukan pada RH.",

    "Pemilihan kerugian pada anggota utama juga bukan pilihan sembarang. Kerugian Huber {R:huber} "
    "berperilaku kuadratik di dekat nol dan linear di ekornya, sehingga baris berderau berat tidak "
    "menarik model sekuat pada L2. Kami menyapu parameter "
    "huber α dari 1 sampai kuadrat murni: α = 1 memburukkan blok utama sebesar +0,537 dan kuadrat "
    "murni +0,185, sedangkan α = 2 sampai 6 adalah dataran datar. Intuisi “metriknya RMSE maka "
    "pasangkan kerugian L2” salah lebar di sini, dan alasannya sudah terbaca di Bagian II-C: "
    "prediktornya masih berderau berat meskipun targetnya bersih.",
]

MODEL_BLEND = [
    "Bobot *blend* berasal dari kuadrat-terkecil non-negatif {R:nnls} pada prediksi luar-lipatan,",

    "lalu ditarik sebesar 25 % ke arah pembobotan seragam sebagai lantai penyusutan. Tidak ada "
    "satu pun angka bobot yang dimasukkan dengan tangan. Kerangka umumnya adalah *stacked "
    "generalization* {R:wolpert}.",

    "**Bobot per pita waktu-hari.** Anggota tidak sama baiknya sepanjang jam. Dipasang per tiga "
    "pita yang tepinya adalah kuantil jam-hari, `ridge_e` naik dari lantainya 0,05 di malam hari "
    "menjadi 0,15 di tengah hari, tepat "
    "ketika *e*_{s}(*T*) terbesar dan parameterisasi tekanan uap paling berarti; `cat` justru naik "
    "di sore hari. Satu vektor bobot global merata-ratakan rezim itu. Perbaikannya −0,080 "
    "pada validasi bersarang, dan kontrol yang mengondisikan pada peubah acak dengan jumlah "
    "parameter bebas yang sama hanya membeli −0,007. Jadi yang diukur adalah sinyal, bukan "
    "kapasitas tambahan.",

    "**Koreksi bias diurnal.** Bobot NNLS non-negatif dan ternormalisasi, sehingga *blend* tidak "
    "punya intersep dan pembobotan ulang per pita meninggalkan offset per pita tak tersentuh. "
    "Offset itu besar dan konsisten: *blend* kurang memprediksi puncak kelembapan sekitar pukul "
    "04.00 dan lebih memprediksi lembah sekitar pukul 15.00 pada 18 dari 18 lipatan bersarang. "
    "Itu tanda tangan pemadatan amplitudo oleh kerugian huber dan perata-rataan pohon. Level global "
    "sengaja dikurangkan keluar dari koreksi ini dan ditangani terpisah di sub-bagian berikutnya.",

    "**Mengapa satu anggota dibuang.** Kontribusi *drop-one* anggota `ridge` negatif, artinya "
    "membuangnya justru membantu. Bobot NNLS globalnya persis nol pada 18 dari 18 lipatan, dan ia "
    "adalah anggota yang paling dirusak oleh blok tekanan yang kehilangan dukungan di jendela uji. "
    "Membuangnya bernilai −0,012 RMSE di papan peringkat.",
]

MODEL_DEBIAS = [
    "Temuan berikut muncul dari mencetak satu angka yang belum pernah kami cetak selama 46 sesi "
    "eksperimen: rerata galat bertanda setiap anggota *blend* pada blok validasi maju. Gambar {G:bias} "
    "memuat hasilnya.",

    "Lima anggota berada di dalam ±0,8 %RH. Anggota `cat` berada di **−2,89 %RH**, memegang 0,217 "
    "bobot *blend*, dan menyeret seluruh *stack* ke bawah sekitar 1 %RH. Bias di dalam sampel-nya "
    "−0,006, jadi ini murni sifat maju dan bukan artefak pemasangan. Angka −2,89 diukur pada "
    "cache tiga blok validasi maju 15 hari; pada baris luar-lipatan, instrumen berbeda yang "
    "dicetak notebook, anggota yang sama memberi −1,86. Keduanya sepakat pada tanda dan urutan "
    "anggota, dan besarannya berbeda karena blok maju menuntut ekstrapolasi lebih jauh.",

    "Mekanismenya spesifik dan dapat diverifikasi. Kerugian `Huber:delta=4` pada target dengan "
    "simpangan baku 18 %RH memotong gradien di atas 4 %RH, sehingga anggota itu menjejak median "
    "bersyarat dan mendarat rendah begitu diminta memprediksi ke luar jendela latihnya. Sapuan "
    "kerugian mengonfirmasinya pada satu split terkendali, dipasang pada 46 hari pertama lalu "
    "dinilai pada 15 hari berikutnya: dengan kerugian kuadrat bias maju CatBoost −0,04, "
    "sedangkan `Huber:delta=4` −1,62 pada split yang sama.",

    "Yang membuat temuan ini layak dilaporkan adalah **mengapa ia bisa bertahan selama itu**, "
    "bukan besarnya. Tidak ada satu pun komponen di pipeline yang berbentuk cukup untuk melihatnya. "
    "Bobot NNLS non-negatif dan ternormalisasi, jadi *blend* tidak punya intersep. Koreksi bias "
    "diurnal memasang intersep lalu sengaja membuangnya. Gerbang validasi melaporkan RMSE, dan "
    "RMSE tidak memisahkan bias dari ragam. Offset itu tidak terlihat oleh instrumen mana pun "
    "yang sudah ada.",

    "Koreksinya dibuat sekecil mungkin: satu skalar, yaitu rerata galat luar-lipatan anggota itu "
    "sendiri, diterapkan pada kekuatan 0,5. Ia diukur pada baris yang hanya berasal dari masa lalu "
    "setiap lipatan, jadi ia pengukuran maju atas besaran yang sama yang akan ditunjukkan jendela "
    "uji. Pada blok maju nilainya −0,077 RMSE terkumpul dengan lima dari enam blok membaik. Dua kontrol yang "
    "didaftarkan sebelum angkanya dibaca berperilaku persis seperti yang disyaratkan "
    "mekanisme: menambahkan offset, bukan menguranginya, kalah +0,162 dengan nol dari enam blok "
    "membaik, dan mengarahkan mesin yang sama ke anggota yang biasnya +0,05 membeli +0,017, yakni "
    "tidak ada apa-apa. Di papan peringkat nilainya **−0,022**.",
]

MODEL_INCREMENT = [
    "Ini komponen tunggal paling berharga di seluruh solusi, jadi rasionalnya ditulis lengkap. "
    "Seluruh pipeline sampai titik ini menilai 734 baris uji satu per satu, padahal galat model "
    "level punya autokorelasi lag-satu 0,93: pada satu penggal waktu ia salah dengan besaran "
    "yang hampir sama sepanjang penggal itu. Kurangkan dua prediksi bertetangga dan sebagian "
    "besar galat itu saling meniadakan. Tiga angka menyatakan seberapa besar peluang yang "
    "tersisa di "
    "sana, ketiganya diukur pada 6.471 baris luar-lipatan yang sama: perubahan RH 30 menit punya "
    "sinyal sebesar RMSE 3,55; prediksi level *stack* sendiri sudah menyiratkan perubahan itu "
    "dengan RMSE 1,91; dan model perubahan khusus mencapai 1,81. Pada horizon 2 jam keunggulan "
    "itu hilang, 3,57 lawan 3,52, dan itulah alasan bobot rekonsiliasinya 4 : 1 dan bukan "
    "seimbang.",

    "Kedua sumber informasi itu dapat digabungkan secara tepat. Kami mencari satu lintasan *z* "
    "yang tetap dekat dengan prediksi level *p* sekaligus mengikuti dinamika yang dipelajari,",

    "dengan *D*_{h} operator selisih *h*-langkah jarang dan *d*_{h} prediksi perubahan "
    "*h*-langkah. "
    "Kami memakai *h* ∈ {1, 4}, yaitu 30 menit dan 2 jam, dengan λ₁ = 4 dan λ₄ = 1. Kondisi "
    "orde-pertamanya memberi satu sistem simetris definit-positif jarang,",

    "yang diselesaikan sekali dengan penyelesai jarang: tanpa iterasi, tanpa parameter bebas di luar "
    "dua bobot yang sudah dibekukan sebelum eksperimen ini ada. Kerangka konseptualnya adalah "
    "rekonsiliasi ramalan sebagai proyeksi kuadrat-terkecil {R:hyndman}, dipindahkan dari hierarki "
    "agregasi ke hierarki temporal.",

    "Kebersihan target dijaga di dua tempat. Kedua ujung setiap selisih latih wajib merupakan "
    "baris latih berlabel, sehingga tidak ada selisih yang menyeberangi titik asal peramalan. Dan "
    "inferensinya hanya membaca kolom eksogen, sehingga tidak ada RH jendela uji yang menjadi "
    "masukan dan tidak ada umpan balik rekursif. Model perubahannya sendiri menangkap "
    "*R*² = 0,74 pada 30 menit dan 0,90 pada 2 jam.",

    "Gambar {G:increment} memperlihatkan hasilnya pada tiga blok validasi maju, dan di papan peringkat "
    "nilainya **−0,160 RMSE**, tujuh kali lipat perbaikan *blending* terbaik.",
]

MODEL_BUTA = [
    "Sebelum satu model pun dipasang, kami membuktikan secara mekanis bahwa tidak satu pun fitur "
    "bergantung pada target: seluruh matriks fitur dibangun ulang dari kisi yang kolom targetnya "
    "sudah dihapus, lalu dibandingkan bit per bit dengan matriks yang dipakai produksi. Hal yang "
    "sama dilakukan untuk matriks desain *increment*. Keduanya lolos.",

    "Satu-satunya sumber keacakan di seluruh pipeline adalah penanaman pohon; ansambelnya "
    "merata-ratakan *seed* 0–2 di dalam validasi silang dan 0–4 pada pemasangan akhir, dengan *seed* "
    "*increment* tetap. Seluruh pipeline berjalan di atas tumpukan Python yang versinya dicatat "
    "Tabel {T:repro}: NumPy {R:numpy} dan pandas {R:pandas} untuk kisi dan matriks fitur, "
    "scikit-learn {R:sklearn} untuk kedua anggota linear beserta pra-pemrosesannya, SciPy {R:scipy} "
    "untuk penyelesai kuadrat-terkecil non-negatif pada ({E:nnls}) sekaligus penyelesai jarang pada "
    "({E:normal}), dan Matplotlib {R:matplotlib} untuk seluruh gambar di naskah ini. "
    "Notebook menuliskan berkas *submission* dan memeriksa bentuknya terhadap "
    "`sample_submission.csv`, lalu mencetak md5-nya berdampingan dengan md5 dan skor publik "
    "berkas yang benar-benar dikirim. Verifikasinya ditempuh dengan mengunggah berkas itu ke "
    "Kaggle, bukan oleh pemeriksa di dalam notebook, karena kesamaan sampai bit terakhir bukan "
    "kriteria yang benar di sini: penyelesai jarang pada ({E:normal}) menggeser satu baris "
    "sebesar 10⁻¹⁵ antar-jalankan, dan penjumlahan histogram di LightGBM maupun CatBoost "
    "bergantung urutan thread sehingga versi pustaka yang sama pada mesin berbeda menggeser "
    "prediksi orde 0,3 %RH. Lapisan pra-pemrosesan dan kedua anggota linear reproduksi sampai "
    "digit terakhir. Lampiran I memuat angkanya.",
]

# ============================================================================
# VI. EVALUASI DAN PEMBAHASAN
# ============================================================================

EVAL_PEMBANDING = [
    "Sebelum membahas apa yang memindahkan skor, ada pertanyaan yang lebih dasar: apakah "
    "arsitektur sepanjang ini memang diperlukan. Kami menjawabnya dengan menilai enam metode "
    "pembanding pada protokol yang persis sama. Setiap metode dipasang hanya pada baris sebelum "
    "titik potong tiap lipatan, lalu dinilai pada 15 hari berikutnya, sehingga angkanya lahir "
    "dari sembilan lipatan dan 6.480 baris luar-lipatan yang identik dengan yang dipakai memasang "
    "bobot *blend*. Tabel {T:pembanding} dan Gambar {G:pembanding} memuat hasilnya.",

    "Empat hal terbaca dari ladder itu. Pertama, klimatologi jam-hari (10,16) hampir menyamai "
    "proksi titik embun (10,93) padahal yang satu tanpa fisika dan yang lain tanpa pelatihan: "
    "keduanya menyentuh sisi berbeda dari struktur yang sama. Kedua, persistensi profil hari "
    "terakhir hanya 13,38, jauh di belakang klimatologi. Pada horizon 15 hari, hari kemarin "
    "adalah penduga yang lebih buruk daripada rerata semua hari, dan persoalan ini karena itu "
    "bukan persoalan ekstrapolasi jangka pendek.",

    "Ketiga, regresi linear berganda atas 24 kanal mencapai 8,08 sedangkan satu LightGBM dengan "
    "parameter bawaan mencapai 5,71. Lompatan 2,37 %RH itu adalah harga nonlinearitas dan "
    "interaksi, dan ia jauh lebih besar daripada seluruh sisa pekerjaan kami. Keempat, *stack* "
    "lengkap mencapai 4,81 terhadap 5,71 milik LightGBM tunggal, yaitu perbaikan 15,8 %. Angka "
    "itu adalah ukuran yang paling jujur atas kontribusi tulisan ini, karena pembandingnya bukan "
    "tebakan rerata, tetapi apa yang diperoleh siapa pun yang melemparkan satu model *gradient "
    "boosting* ke matriks fitur yang sama.",

    "Panel (b) Gambar {G:pembanding} memperlihatkan urutan ketiga metode teratas sama di "
    "sembilan lipatan tanpa satu pun perpotongan, dan konsistensi itu dapat dinyatakan sebagai "
    "uji. *Stack* mengungguli LightGBM tunggal pada **sembilan dari sembilan lipatan**, dengan "
    "selisih rerata **0,939 %RH** (simpangan baku 0,169) dan perbaikan relatif 11,2 sampai "
    "27,4 % per lipatan; uji peringkat bertanda Wilcoxon berpasangan memberi *p* = 0,0039, "
    "identik dengan uji tanda karena seluruh selisihnya searah {R:demsar}. Angka itu mengukur "
    "konsistensi arah, bukan bukti dari sembilan pengamatan bebas: lipatan kami tumpang tindih "
    "(Lampiran G), galat antar-lipatan berkorelasi, dan setiap uji yang mengandaikan kebebasan "
    "akan terlalu longgar. Uji-t berpasangan atas data yang sama memberi *p* < 10⁻⁵, dan "
    "sengaja tidak kami pakai sebagai bukti. Yang kami klaim hanya ini: pada protokol dan baris "
    "yang sama, urutannya tidak pernah terbalik.",

    "Seluruh angka pada tabel itu diukur pada baris luar-lipatan dan bukan pada seluruh "
    "data latih, sehingga garis dasar naif di sana 18,82 sedangkan angka "
    "18,0 yang dikutip di tempat lain dihitung atas seluruh baris latih.",
]

EVAL_HASIL = [
    "Metrik resmi kompetisi adalah RMSE atas 734 baris uji. Tabel {T:tangga} di lampiran memuat tangga skor papan "
    "peringkat publik secara lengkap, termasuk perubahan yang merugikan, dan Gambar {G:tangga} "
    "menggambarkannya.",

    "Bentuk tangganya adalah temuan tersendiri. Satu tambahan struktural bernilai −0,160, "
    "sementara empat perbaikan *blending* terbaik yang digabungkan hanya bernilai −0,077. Perbaikan "
    "terbesar di antara yang kedua, yaitu bias diurnal per pita, bernilai −0,024 atau sepertujuh "
    "dari yang pertama. Polanya tidak halus: mekanisme baru mengalahkan penyetelan mekanisme lama "
    "dengan selisih satu orde besaran. Itulah yang akan kami kejar lebih dulu kalau ada waktu "
    "tambahan.",

    "Angka 2,827 mengalahkan ketiga garis dasar yang dipasang lebih dulu: rerata latih 18,0, "
    "proksi titik embun ({E:proksi}) 9,1, dan batas *oracle* harian 8,37. Menurut Gambar "
    "{G:oracle} ia setara dengan mengetahui tekanan uap yang sebenarnya pada resolusi 6,1 jam.",

    "Angka itu juga perlu dibaca dalam satuan yang dipakai orang yang mengelola petak, bukan "
    "hanya dalam satuan metrik lomba. RMSE 2,83 %RH adalah 6,9 % dari amplitudo diurnal target "
    "(41,13 %RH) dan 15,7 % dari simpangan bakunya. Diterjemahkan lewat identitas ({E:rh}) pada suhu "
    "rerata jendela uji 24,64 °C, ia setara dengan galat defisit tekanan uap sebesar 0,088 kPa, "
    "dan lewat ∂RH/∂*T* ≈ −3,6 %RH per °C ia setara dengan salah membaca termometer sebesar "
    "0,79 °C. Untuk penjadwalan ventilasi dan pengabutan, yang biasanya bekerja pada beda VPD "
    "orde 0,3 sampai 0,5 kPa, ketelitian sebesar itu memadai. Yang tidak dijamin olehnya adalah "
    "keputusan yang bergantung pada satu ambang tajam, misalnya ambang RH untuk jendela infeksi "
    "jamur, karena di dekat ambang galat 2,83 %RH masih dapat membalik sisi keputusan; di sana "
    "keluaran model sebaiknya dipakai sebagai peringkat risiko, bukan sebagai saklar.",
]

EVAL_ANATOMI = [
    "Di mana galat yang tersisa berada menentukan apa yang mungkin dilakukan berikutnya, jadi kami "
    "membedahnya pada baris luar-lipatan, satu-satunya tempat kebenaran tersedia. Gambar {G:anatomi} "
    "memuat tiga panelnya, dan ketiganya dibaca dari frame yang sama, yaitu 6.480 baris yang juga "
    "menghasilkan Tabel {T:pembanding}.",

    "Panel (a) memperlihatkan galat menumpuk di pita gelap. Tiga pita antara pukul 21.00 dan 06.00 "
    "menyumbang 53,4 % dari seluruh jumlah kuadrat galat, sedangkan dua pita paling terang antara "
    "09.00 dan 15.00 hanya menyumbang 16,5 %. Panel (b) memperlihatkan penyebabnya berbentuk bias, "
    "dan bukan hanya ragam: pita 00.00 dan 21.00 membawa galat bertanda −1,05 dan −1,04 %RH, "
    "sementara pita 09.00 dan 12.00 membawa +0,97 dan +1,11. Model masih memadatkan ayunan harian, "
    "meskipun koreksi bias diurnal di Bagian V-B sudah memangkas sebagian besarnya.",

    "Panel (c) memuat pemisahan yang paling menentukan. Sekitar **39 % galat adalah offset per "
    "hari**, yaitu satu bilangan per hari yang salah dan tidak berubah sepanjang hari itu. Sisa "
    "61 % adalah bentuk di dalam hari. Dan seluruh pemadatan amplitudo berada di tingkat harian: "
    "kemiringan kalibrasi pada rerata harian adalah **1,147**, sedangkan di dalam hari ia "
    "**1,054**. Kemiringan per-baris 1,063 hanyalah angka pertama yang diencerkan oleh ragam di "
    "dalam hari yang jauh lebih besar. Bentuk diurnalnya sudah berukuran benar; yang salah ukuran "
    "adalah tingkat hariannya.",

    "Kemiringan harian itu, sayangnya, tidak dapat diduga. Memasangnya memerlukan sampel "
    "tingkat-hari, dan satu jendela hanya punya 13 sampai 23 hari. Ketika kami mengukurnya, dugaan "
    "dan realisasinya tidak berkorelasi sama sekali. Itu alasan struktural mengapa 39 % galat "
    "tersebut terdiagnosis tetapi tidak terpecahkan.",
]

EVAL_INSTRUMEN = [
    "Sub-bagian ini adalah pemeriksaan penutup, bukan metode pemilihan model. Dua konfigurasi "
    "yang sudah dikapalkan kebetulan berbeda dari pendahulunya hampir hanya pada satu momen "
    "distribusi, sehingga selisih skornya dapat dibaca ulang untuk menjawab satu pertanyaan: "
    "apakah koreksi level dan dispersi masih menyisakan sesuatu. Perlu dinyatakan terbuka apa "
    "yang tidak dikerjakan di sini: kedua berkas adalah keluaran model apa adanya, tidak ada "
    "satu baris pun yang nilainya ditetapkan dengan tangan, dan tidak ada nilai target yang "
    "direkonstruksi. Yang dibaca hanya dua skalar agregat atas seluruh slice publik.",

    "Misalkan kita mengapalkan perubahan *d* pada vektor prediksi *p*, dengan galat *e* = *p* − *y*. "
    "Maka perubahan MSE-nya persis",

    "Kalau *d* dirancang mendekati konstanta, suku pertama menjadi 2·*d̄*·*ē*, dan skor yang "
    "kembali dari papan peringkat memberi rerata galat level jendela uji secara langsung. Kalau "
    "*d* dirancang sebagai penskalaan murni di sekitar rerata, skor yang kembali memberi "
    "kemiringan kalibrasinya. Kebetulan dua konfigurasi terakhir yang kami kapalkan berbentuk "
    "persis seperti itu.",

    "Yang pertama adalah de-bias level anggota `cat`, yang perubahannya hampir murni pergeseran "
    "level dengan *d̄* = +0,20244. MSE bergerak dari 8,11982 ke 7,99442, jadi ΔMSE = −0,12540. "
    "Membalik ({E:dmse}) memberi",

    "yaitu galat level sesungguhnya pada *slice* publik. Konfigurasi kedua memberi hal yang sama untuk "
    "momen kedua dan memberi kemiringan kalibrasi *s** = 1,0050.",

    "Tabel {T:instrumen} menempatkan kedua angka itu berdampingan dengan dugaan instrumen internal kami, "
    "dan perbandingannya adalah kalibrasi yang berguna. **Instrumen internal mendapatkan tandanya "
    "dengan benar tetapi besarannya terlalu besar secara konsisten, sekitar 2 sampai 6 kali.** "
    "Blok validasi maju kami adalah jendela Juli–Agustus yang galat tingkat-hariannya lebih besar "
    "daripada jendela uji, dan setiap statistik level mewarisi undian tingkat-hari blok itu "
    "sendiri. Aturan yang kami tarik: ambil tandanya, potong besarannya.",

    "Setelah kedua koreksi diterapkan, sisa pada sumbu level tinggal −0,008 RMSE dan pada sumbu "
    "dispersi −0,002. **Kedua keluarga koreksi pasca-model tertutup secara kuantitatif.** Tidak "
    "ada lagi yang bisa dipanen dari menggeser atau menskalakan prediksi; perbaikan berikutnya "
    "harus datang dari prediksi bersyarat yang benar-benar lebih baik.",

    "Konfigurasi kedua **merugi** 0,006 dan karena itu tidak dikapalkan; kami tetap melaporkannya sebagai "
    "hasil. Informasi yang dibelinya, yaitu bahwa model sudah terkalibrasi dispersi pada "
    "jendela uji, menutup sumbu yang kalau *s** ternyata 1,05 akan bernilai −0,14 "
    "RMSE. Membayar 0,006 untuk mengetahui itu adalah pertukaran yang benar, dan *submission* "
    "terbaik tetap tersimpan.",

    "Dua batas perlu dinyatakan terbuka. Kedua besaran di Tabel {T:instrumen} adalah properti "
    "**slice publik**, bukan seluruh 734 baris, dan membaca dua belas skor dari papan yang "
    "sama berisiko menyesuaikan diri pada slice itu. Keduanya membentuk cara kami memakainya: "
    "papan peringkat hanya untuk dua momen distribusi yang mekanismenya sudah terukur lebih "
    "dulu pada blok validasi maju, tidak pernah untuk menyetel model, dan berkas yang "
    "dikapalkan adalah konfigurasi berskor terbaik alih-alih yang terakhir diuji. Kesimpulan bahwa "
    "kedua sumbu tertutup karena itu berlaku dengan syarat slice publik mewakili sisanya.",
]

EVAL_KEGAGALAN = [
    "Sebagian besar yang layak diketahui tentang dataset ini adalah *mengapa* sesuatu tidak "
    "bekerja. Tabel {T:gagal_internal} di lampiran memuat arah-arah yang ditolak berdasarkan "
    "pengukuran internal, masing-masing diukur pada protokol maju yang sama dan dengan "
    "kontrolnya. Satu di antaranya layak disebut di sini: analog tetangga terdekat gagal "
    "karena pasangan yang keadaan sensornya mirip ternyata berbagi RH jauh lebih erat "
    "(*r* = 0,81) daripada berbagi tekanan uap (*r* = 0,47), sehingga kemiripan sensor tidak "
    "menyiratkan kemiripan massa udara.",

    "Kelompok kedua lebih instruktif, dan ia menghasilkan satu aturan yang membentuk seluruh "
    "keputusan akhir kami: perubahan yang buktinya kuat secara internal dan tetap salah di "
    "papan peringkat. Kemiringan kalibrasi dispersi versi awal menang di 13 dari 13 lipatan pada "
    "tiga keluarga lipatan yang berbeda lalu kalah +0,237, karena sebaran prediksi uji ternyata "
    "berada di atas setiap lipatan validasi silang sehingga pemadatan yang hendak dibatalkan tidak "
    "ada di sana. Membuang lantai penyusutan NNLS menang −0,058 pada validasi bersarang lalu kalah "
    "+0,028. Koreksi pita-rentang-lebar mengukur mekanismenya dengan arah yang benar lalu kalah "
    "+0,126 karena biasnya membalik tanda di jendela uji. Dari tiga penghalusan *increment* yang "
    "diadopsi secara internal, nol yang menang di papan peringkat.",

    "Aturan yang kami tarik: **validasi silang memeringkat perubahan pada model.** Untuk apa pun "
    "yang diterapkan *setelah* model (kalibrasi, ekspansi, koreksi bias) bukti validasi silang "
    "perlu tetapi tidak cukup. Besaran yang dikoreksi harus juga terlihat sama pada fitur uji, "
    "atau koreksi itu tidak boleh diterapkan.",
]

EVAL_BATAS = [
    "**Kalender tunggal, dan sampel efektif yang kecil.** Seluruh bukti internal berasal dari "
    "satu musim 62 hari; blok validasi maju kami tumpang tindih dan seluruhnya Juli–Agustus, "
    "dan Bagian VI-D menunjukkan mereka melebih-lebihkan galat tingkat-level 2 sampai 6 kali. "
    "Autokorelasi lag-satu 0,979 membuat 2.933 baris setara sekitar 62 sampel harian bebas, "
    "dan justru pada skala itulah 39 % galat berada. Setiap angka internal di tulisan ini "
    "karena itu harus dibaca dengan tanda yang benar dan besaran yang dipotong.",

    "**Jendela terpusat bersifat transduktif, dan kami mengukur harganya.** Fitur pada baris uji "
    "membaca sensor dari baris uji tetangga. Ini sah menurut rancangan kompetisi dan tidak pernah "
    "menyentuh target, tetapi ia bukan operasi kausal waktu-nyata: model ini merekonstruksi "
    "kelembapan dari jejak sensor yang lengkap, bukan meramalkannya secara daring. Daripada "
    "menyerahkan pertanyaan itu sebagai catatan kaki, kami membangun ulang seluruh matriks fitur "
    "dengan setiap jendela bergulir diubah menjadi ekor-belakang dan 12 kolom yang melihat ke "
    "depan dibuang, lalu melatih LightGBM yang sama pada sembilan lipatan yang sama. RMSE-nya "
    "bergerak dari 5,71 ke **8,22**, yaitu +2,51 atau 44 %, dan baris terakhir Tabel "
    "{T:pembanding} mencatatnya sebagai kendali. **Besaran itu sendiri adalah temuan:** 8,22 "
    "**lebih buruk daripada regresi linear berganda atas jendela terpusat** yang mencapai 8,08, "
    "jadi sebagian besar keunggulan pendekatan berbasis pohon di sini bersumber dari kemampuan "
    "membaca sensor serempak dan bukan dari kapasitas modelnya. Sistem daring yang benar-benar "
    "meramal ke depan karena itu tidak akan mewarisi angka 2,83, dan usaha berikutnya untuk "
    "kasus daring sebaiknya diarahkan ke ramalan cuaca numerik sebagai masukan eksogen, bukan "
    "ke model yang lebih besar. "
    "Rekonsiliasi lintasan di Bagian V-D tetap berlaku pada rezim kausal, karena ia hanya "
    "mengikat prediksi satu sama lain dan tidak pernah membaca target.",

    "**Blok tanah dan irigasi dibuang.** Kami membuangnya karena hilangnya dukungan di jendela uji "
    "dan memverifikasi bahwa memulihkannya merugikan. Pada penyebaran dengan irigasi aktif "
    "kolom-kolom itu membawa informasi evapotranspirasi yang nyata, sehingga "
    "keputusan ini khusus untuk jendela uji ini.",
]

# ============================================================================
# VII. KESIMPULAN
# ============================================================================

KESIMPULAN = [
    "**Reformulasi fisis adalah keputusan tunggal yang paling berpengaruh.** Menulis Persamaan "
    "({E:rh}) dan menyadari bahwa penyebutnya diketahui persis pada waktu uji mengubah "
    "masalah peramalan deret waktu menjadi masalah pendugaan tekanan uap. Setiap blok fitur yang "
    "bertahan sampai versi akhir, dari proksi titik embun atas minimum bergulir sampai persentil "
    "suhu, penjejak ventilasi CO₂, dan tendensi tekanan sinoptik, adalah usaha menduga *e*. Kurva *oracle* "
    "memberi ukuran objektif seberapa jauh usaha itu berhasil: *stack* ini setara dengan mengetahui "
    "tekanan uap yang sebenarnya pada resolusi 6,1 jam.",

    "**Memperlakukan jendela uji sebagai deret waktu bernilai tujuh kali lipat apa pun yang "
    "lain.** Setiap komponen lain menilai baris satu per satu; rekonsiliasi lintasan adalah "
    "satu-satunya yang menghubungkan seluruh 734 baris lewat satu sistem linear, dan "
    "satu-satunya perubahan yang bernilai lebih dari 0,03 RMSE.",

    "**Cacat kalibrasi bisa bertahan lama justru karena tidak ada yang mencetak angkanya.** Bias "
    "level −2,89 %RH pada satu anggota *blend* bertahan puluhan iterasi karena tidak satu pun "
    "instrumen (NNLS, koreksi bias diurnal, maupun gerbang validasi berbasis RMSE) punya bentuk "
    "yang bisa melihatnya. Ia ditemukan dengan mencetak rerata galat bertanda per anggota, satu "
    "baris kode, dan bernilai −0,022 RMSE.",

    "**Validasi silang memeringkat perubahan pada model; untuk koreksi setelah model ia perlu "
    "tetapi tidak cukup.** Tiga koreksi pasca-model lolos validasi internal, satu di antaranya "
    "menang di 13 dari 13 lipatan, lalu tetap merugikan pada jendela uji. Aturannya: besaran "
    "yang hendak dikoreksi harus terlihat sama pada fitur uji, atau koreksi itu tidak "
    "diterapkan. Diagnostik penutup di Bagian VI-D mengonfirmasi kedua sumbu koreksi memang "
    "sudah tertutup, dengan sisa di bawah 0,01 RMSE.",

    "Skor akhir RMSE publik **2,82744**, dari garis dasar naif 18,0 dan garis dasar fisis "
    "bebas-parameter 9,1. Kesenjangan yang tersisa sudah terdiagnosis: 39 % galat adalah offset "
    "per hari dengan kemiringan pemadatan 1,147 yang tidak dapat diduga dari 13 sampai 23 hari "
    "sejarah. Pekerjaan berikutnya yang kami anggap paling menjanjikan karena itu adalah "
    "mekanisme baru pada skala harian, bukan penyetelan lebih lanjut atas mekanisme yang ada.",

    "Notebook yang dikumpulkan membangun ulang seluruh hasil di tulisan ini dari data mentah "
    "dengan *seed* tetap, lalu memverifikasi prediksinya terhadap berkas yang benar-benar dikirim "
    "ke papan peringkat. Tidak ada data eksternal, model *pretrained*, maupun kode eksternal "
    "yang dipakai."
]

# ============================================================================
# RUMUS
# ============================================================================

EQ_RH = [
    "RH(*t*) = 100 · *e*(*t*) / *e*_{s}(*T*(*t*))",
]
EQ_ES = [
    "*e*_{s}(*T*) = 6,112 · exp( 17,67 *T* / (*T* + 243,5) )",
]
EQ_ORACLE = [
    "RH^{oracle}(*t*) = 100 · ⟨*e*⟩_{w}(*t*) / *e*_{s}(*T*(*t*))",
]
EQ_PROKSI = [
    "RH(*t*) ≈ 100 · *e*_{s}(*T*_{min}) / *e*_{s}(*T*(*t*))",
]
EQ_AGRO = [
    "*T*_{min} = 2 · *T̄*_{hari} − *T*_{maks}",
    "*T*_{min} = (2 · CHU − *Y*_{maks}) / 1,8 + 4,4",
]
EQ_HAMPEL = [
    "tolak *x*(*t*)   jika   | *x*(*t*) − med_{w}(*t*) | > *k* · *s*(*t*)",
]
EQ_NNLS = [
    "*ŵ* = arg min ‖ *P* *w* − *y* ‖^{2},   *w* ≥ 0",
]
EQ_RECON = [
    "min_{z}  ‖ *z* − *p* ‖^{2} + Σ_{h} λ_{h} ‖ *D*_{h} *z* − *d*_{h} ‖^{2}",
    "( *I* + Σ_{h} λ_{h} *D*_{h}^{⊤} *D*_{h} ) *z* = *p* + Σ_{h} λ_{h} *D*_{h}^{⊤} *d*_{h}",
]
EQ_DMSE = [
    "Δ MSE = 2 · mean(*d* · *e*) + mean(*d*^{2})",
]
EQ_LEVEL = [
    "*ē* = ( ΔMSE − mean(*d*^{2}) ) / ( 2 *d̄* ) = −0,4145 %RH",
]

# ============================================================================
# PUSTAKA (IEEE Style)
# ============================================================================
#
# Dikunci per slug, bukan per nomor. Nomor [1], [2], … diberikan build.py
# menurut urutan kemunculan pertama kunci {R:slug} di badan naskah, dan daftar
# ini dicetak dalam urutan itu, persis yang diminta IEEE Style dan juknis 3c.
#
# Konsekuensi yang disengaja: build berhenti kalau ada entri di sini yang tidak
# pernah disitasi, atau kunci disitasi tapi tidak ada entrinya. Urutan penulisan
# di bawah karena itu tidak menentukan apa pun; ia hanya dikelompokkan supaya
# enak dibaca.

PUSTAKA = {
    # -- perangkat lunak
    'lgbm':
    'G. Ke et al., "LightGBM: A Highly Efficient Gradient Boosting Decision Tree," in *Advances '
    'in Neural Information Processing Systems 30*, Long Beach, CA, USA, 2017, pp. 3146–3154.',

    'catboost':
    'L. Prokhorenkova, G. Gusev, A. Vorobev, A. V. Dorogush, and A. Gulin, "CatBoost: Unbiased '
    'Boosting with Categorical Features," in *Advances in Neural Information Processing Systems '
    '31*, Montréal, QC, Canada, 2018, pp. 6638–6648.',

    'sklearn':
    'F. Pedregosa et al., "Scikit-learn: Machine Learning in Python," *Journal of Machine '
    'Learning Research*, vol. 12, pp. 2825–2830, 2011.',

    'scipy':
    'P. Virtanen et al., "SciPy 1.0: Fundamental Algorithms for Scientific Computing in Python," '
    '*Nature Methods*, vol. 17, no. 3, pp. 261–272, 2020.',

    'numpy':
    'C. R. Harris et al., "Array Programming with NumPy," *Nature*, vol. 585, no. 7825, '
    'pp. 357–362, 2020.',

    'pandas':
    'The pandas development team, "pandas-dev/pandas: Pandas," Zenodo, 2020. '
    'doi: 10.5281/zenodo.3509134.',

    'matplotlib':
    'J. D. Hunter, "Matplotlib: A 2D Graphics Environment," *Computing in Science & Engineering*, '
    'vol. 9, no. 3, pp. 90–95, 2007.',

    # -- metode dan fisika
    'bolton':
    'D. Bolton, "The Computation of Equivalent Potential Temperature," *Monthly Weather Review*, '
    'vol. 108, no. 7, pp. 1046–1053, 1980.',

    'hampel':
    'F. R. Hampel, "The Influence Curve and Its Role in Robust Estimation," *Journal of the '
    'American Statistical Association*, vol. 69, no. 346, pp. 383–393, 1974.',

    'huber':
    'P. J. Huber, "Robust Estimation of a Location Parameter," *Annals of Mathematical '
    'Statistics*, vol. 35, no. 1, pp. 73–101, 1964.',

    'nnls':
    'C. L. Lawson and R. J. Hanson, *Solving Least Squares Problems*. Englewood Cliffs, NJ, USA: '
    'Prentice-Hall, 1974.',

    'wolpert':
    'D. H. Wolpert, "Stacked Generalization," *Neural Networks*, vol. 5, no. 2, pp. 241–259, 1992.',

    'hyndman':
    'R. J. Hyndman, R. A. Ahmed, G. Athanasopoulos, and H. L. Shang, "Optimal Combination '
    'Forecasts for Hierarchical Time Series," *Computational Statistics & Data Analysis*, '
    'vol. 55, no. 9, pp. 2579–2589, 2011.',

    'demsar':
    'J. Demšar, "Statistical Comparisons of Classifiers over Multiple Data Sets," *Journal of Machine Learning Research*, vol. 7, pp. 1–30, 2006.',

    'bergmeir':
    'C. Bergmeir and J. M. Benítez, "On the Use of Cross-Validation for Time Series Predictor '
    'Evaluation," *Information Sciences*, vol. 191, pp. 192–213, 2012.',

    'fao56':
    'R. G. Allen, L. S. Pereira, D. Raes, and M. Smith, *Crop Evapotranspiration: Guidelines for '
    'Computing Crop Water Requirements*, FAO Irrigation and Drainage Paper 56. Rome, Italy: FAO, '
    '1998.',

    'chu':
    'Ontario Ministry of Agriculture, Food and Rural Affairs, "Crop Heat Units for Corn and Other '
    'Warm-Season Crops in Ontario," Factsheet 93-119, Guelph, ON, Canada, 1993.',
}
