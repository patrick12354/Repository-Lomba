# -*- coding: utf-8 -*-
"""Isi naskah technical report SENDI - GEMASTIK XIX Penambangan Data."""

JUDUL = ("SENDI: Analisis Sentimen Berita Keuangan Berbahasa Indonesia Berbasis "
         "Leksikon dan IndoBERT serta Dampaknya pada Imbal Hasil Saham BEI")

PENULIS = [
    ("Timotius Christopher Patrick Sihombing", "164241005",
     "timotius.christopher.patrick-2024@ftmm.unair.ac.id"),
    ("Aqila Malfa Zahira", "164231036",
     "aqila.malfa.zahira-2023@ftmm.unair.ac.id"),
    ("Raphael Angelo Adikara Purnama", "164251055",
     "raphael.angelo.adikara-2024@ftmm.unair.ac.id"),
]
PRODI = "Program Studi Teknologi Sains Data"
FAKULTAS = "Fakultas Teknologi Maju dan Multidisiplin"
UNIV = "Universitas Airlangga, Surabaya, Indonesia"

INTISARI = (
    "Domain keuangan berbahasa Indonesia tidak punya sumber daya pemrosesan bahasa alaminya "
    "sendiri, sehingga kajian sentimen berita pasar modal di Indonesia menumpang pada perkakas "
    "berbahasa Inggris yang menyandikan konvensi pasar Amerika. Kami membangun SENDI, rangkaian "
    "sumber daya dan *pipeline* penambangan teks keuangan Bahasa Indonesia, dari korpus 40.009 "
    "judul berita Januari 2022 sampai Agustus 2026 yang menyisakan 32.863 judul unik setelah "
    "deduplikasi SimHash. Enam sumber daya kami rilis terbuka dan belum kami temukan padanan "
    "publiknya, yaitu leksikon sentimen keuangan 495 istilah, kamus *slang* investor 204 entri, "
    "daftar 147 kode emiten yang bertabrakan dengan kata umum, *knowledge graph* relasi "
    "antaremiten, korpus judul berlabel reaksi harga, dan *gold standard* pengenalan kode saham. "
    "*Gazetteer* 942 emiten di antaranya menaikkan F1 pengenalan kode saham dari 0,1227 ke 0,8827 "
    "atas model NER umum. Penilai leksikon yang lahir darinya mencapai akurasi 66,00% dan "
    "*macro-F1* 0,6378 terhadap anotasi tiga pemeriksa independen, berjalan tanpa GPU dan tanpa "
    "pelatihan, dan pada satu hari bursa memangkas 348 judul menjadi 54 judul berarah beserta "
    "istilah pemicunya. Memindahkan label lemah dari tingkat dokumen ke tingkat aspek menaikkan "
    "*macro-F1* IndoBERT dari 0,4358 ke 0,6026 tanpa mengubah apa pun selain labelnya. Pada sisi "
    "pasar, hasilnya memberatkan sistem kami sendiri dan tetap kami laporkan utuh. Berita positif "
    "diikuti *cumulative abnormal return* +0,906% (uji BMP z = 10,11, bertahan setelah koreksi "
    "Holm), tetapi strategi perdagangan yang memakai sinyal itu merugi 34,82% pada periode "
    "*out-of-sample* 2025-2026, masih merugi ketika biaya transaksinya dinolkan, dan tidak dapat "
    "dibedakan dari sepuluh tarikan sinyal acak. Cakupan berita juga timpang sehingga 19,8% "
    "emiten tidak pernah diberitakan. Kami berpendapat klaim “AI trading” yang beredar di "
    "kalangan investor ritel perlu dihadapkan pada bukti setingkat ini sebelum dipercaya."
)

KATA_KUNCI = ("penambangan teks, sentimen keuangan, Bahasa Indonesia, Bursa Efek Indonesia, "
              "IndoBERT")

# ----------------------------------------------------------------------------
# I. PENDAHULUAN
# ----------------------------------------------------------------------------

PENDAHULUAN_LATAR = [
    "Pendalaman pasar keuangan termasuk agenda ekonomi Indonesia yang sudah lama tertunda. Rasio "
    "kapitalisasi pasar terhadap produk domestik bruto masih tertinggal dari negara tetangga di "
    "kawasan, dan sebagian besar tabungan rumah tangga masih mengendap di instrumen perbankan. "
    "Satu dekade terakhir mengubah gambaran itu dari sisi yang tidak diduga. Pembukaan rekening "
    "efek secara daring, penurunan satuan perdagangan, dan masuknya aplikasi sekuritas ke telepon "
    "genggam mendorong jumlah investor ritel di Bursa Efek Indonesia (BEI) naik berlipat-lipat, "
    "dengan mayoritas pendatang baru berusia muda dan bermodal kecil, sehingga pasar yang dahulu "
    "dihuni institusi kini dihuni jutaan orang yang menanggung risikonya sendiri.",

    "Pertumbuhan itu tidak diiringi pertumbuhan perkakas untuk memahami pasarnya. Bursa mencatat "
    "942 emiten pada periode penelitian ini, dan aliran berita keuangan berbahasa Indonesia yang "
    "menyertainya jauh melampaui yang sanggup dibaca satu orang dalam satu hari. Investor "
    "institusi mengatasinya dengan berlangganan terminal data profesional seharga ribuan dolar "
    "per bulan, yang sudah memuat ringkasan sentimen berita secara otomatis. Investor ritel "
    "menghadapi aliran yang sama tanpa alat apa pun, dan membaca beritanya satu per satu atau "
    "tidak membacanya sama sekali.",

    "Akibatnya menjalar ke kualitas keputusan. Ketika membaca seluruh berita bukan pilihan yang "
    "masuk akal, yang tersisa adalah potongan informasi yang kebetulan lewat di linimasa media "
    "sosial, ditambah rekomendasi dari pihak yang kepentingannya tidak selalu sejalan. Celah itu "
    "juga menjadi lahan subur bagi produk yang menjanjikan keuntungan dari analisis berita "
    "otomatis. Klaim semacam itu beredar luas tanpa bukti yang dapat diperiksa, sementara yang "
    "menanggung akibatnya adalah investor pemula yang sulit menilai kebenarannya.",

    "Penambangan teks sudah lama menawarkan jawaban untuk persoalan ini, dan sebagian besar "
    "perkakasnya sudah matang. Leksikon Loughran-McDonald [1] menunjukkan bahwa sentimen "
    "keuangan menuntut kamus khusus domain, Financial PhraseBank [2] menyediakan korpus "
    "berlabel manusia, dan FinBERT [3], [4] memindahkan pendekatan itu ke *transformer*. Di "
    "sisi Bahasa Indonesia, IndoBERT dan IndoLEM [5] serta *benchmark* IndoNLU [6] menyediakan "
    "model bahasa pra-latih beserta tolok ukurnya.",

    "Kedua garis pekerjaan itu tidak pernah bertemu. Sumber daya keuangan yang matang seluruhnya "
    "berbahasa Inggris, disusun dari laporan 10-K dan komunikasi korporasi Amerika, sehingga "
    "menyandikan konvensi pasar yang tidak selalu berlaku di Indonesia. Sebaliknya, sumber daya "
    "Bahasa Indonesia yang tersedia bersifat umum dan tidak memuat satu pun tugas domain "
    "keuangan. Di antara keduanya ada pula hambatan teknis yang khas Indonesia. Dari 942 kode "
    "emiten BEI, 147 di antaranya juga merupakan kata yang lazim dipakai sehari-hari, misalnya "
    "BANK, LABA, NAIK, DATA, KOTA, HOME, dan GOOD. Sistem pengenalan entitas bernama umum tidak "
    "dirancang menghadapi tabrakan semacam itu, dan tidak punya cara memetakan “Bank Central "
    "Asia” ke kode BBCA selama daftar emitennya tidak lengkap.",

    "Celah kedua terletak pada cara bidang ini melaporkan hasilnya, bukan pada bahasanya. "
    "Publikasi prediksi harga berbasis teks pada umumnya menyajikan satu angka keberhasilan pada "
    "satu periode sampel, tanpa pembanding klasik, tanpa selang kepercayaan, dan tanpa kontrol "
    "acak. Bailey dkk. [28] menunjukkan bahwa praktik semacam itu membuat strategi yang "
    "sesungguhnya tidak bernilai tetap terlihat menguntungkan di atas kertas, sehingga pembaca "
    "yang paling membutuhkan bukti justru paling sedikit terlindungi olehnya.",

    "Laporan ini menutup kedua celah tersebut dengan SENDI, rangkaian sumber daya dan "
    "*pipeline* penambangan teks keuangan berbahasa Indonesia yang dibangun dari korpus 40.009 "
    "judul berita Januari 2022 sampai Agustus 2026. Enam sumber dayanya kami rilis terbuka, "
    "dan seluruh pengujiannya dijalankan dengan protokol yang sengaja dibuat sulit dilewati. "
    "Setiap pengukuran memakai data yang belum pernah dilihat model, setiap perbandingan "
    "disertai kontrol acak dan selang kepercayaan, dan hasil yang memberatkan sistem kami "
    "sendiri tetap dilaporkan utuh.",
]

KONTRIBUSI = [
    "Kontribusinya bertumpu pada enam hal yang saling menyambung. Hal pertama berupa enam sumber "
    "daya NLP keuangan berbahasa Indonesia yang dirilis terbuka dan belum kami temukan padanan "
    "publiknya, mencakup leksikon sentimen 495 istilah, kamus *slang* investor 204 entri, daftar "
    "147 kode emiten ambigu, *knowledge graph* relasi antaremiten, korpus 32.863 judul berlabel "
    "reaksi harga, dan *gold standard* pengenalan kode saham berisi 6.000 kalimat. Dari sumber "
    "daya itu lahir kontribusi kedua, yaitu penilai sentimen berbasis leksikon yang mencapai "
    "akurasi 66,00% dan *macro-F1* 0,6378 terhadap anotasi tiga pemeriksa manusia, dan berjalan "
    "di CPU tanpa pelatihan maupun langganan data berbayar. Kontribusi ketiga bersifat "
    "metodologis, berupa bukti terkendali bahwa yang mengikat kinerja model sentimen adalah "
    "tingkat labelnya dan bukan kapasitasnya. Memindahkan label lemah dari tingkat dokumen ke "
    "tingkat aspek, dengan arsitektur, hiperparameter, dan *seed* ditahan tetap, menaikkan "
    "*macro-F1* IndoBERT dari 0,4358 ke 0,6026 dan TF-IDF dari 0,4024 ke 0,5810. Perubahan itu "
    "juga memindahkan IndoBERT dari tidak dapat dibedakan dari penebak konstan (p = 1,0000) "
    "menjadi mengunggulinya (p = 0,000215), dan prosedurnya tidak terikat pada domain keuangan.",

    "Tiga kontribusi berikutnya berada di sisi pasar. Kami menjalankan pengujian empiris "
    "terbuka pertama atas hubungan sentimen berita berbahasa Indonesia dan imbal hasil BEI "
    "dengan *holdout out-of-time*, uji BMP, serta koreksi Holm-Bonferroni, lalu menunjukkan "
    "secara terukur bahwa hubungan yang ditemukan itu tidak dapat dieksploitasi strategi "
    "sederhana, lengkap dengan eliminasi biaya transaksi dan mekanika strategi sebagai "
    "penyebabnya. Terakhir, ketimpangan cakupan berita antaremiten kami ukur beserta *null "
    "model* acaknya, dan hasilnya memetakan 186 emiten atau 19,8% dari seluruh emiten BEI di "
    "luar jangkauan alat berbasis berita mana pun.",
]

PENDAHULUAN_TUJUAN = [
    "Penelitian ini memiliki tiga tujuan yang saling bergantung.",
]

TUJUAN_ITEMS = [
    "Membangun dan merilis sumber daya NLP keuangan berbahasa Indonesia yang sebelumnya "
    "tidak tersedia dalam bentuk siap pakai, mencakup leksikon sentimen, kamus *slang* "
    "investor, daftar kode ambigu, *gazetteer* emiten beserta aliasnya, *knowledge graph* relasi "
    "antaremiten, dan korpus judul berlabel.",

    "Membangun *pipeline* penambangan teks yang lengkap dari pengumpulan berita sampai "
    "pembentukan sinyal, agar rangkaian sumber daya tadi dapat diuji dalam konteks pemakaian "
    "yang sebenarnya alih-alih sebagai artefak yang berdiri sendiri.",

    "Menguji secara empiris apakah sentimen berita berbahasa Indonesia berhubungan dengan "
    "imbal hasil saham BEI, dan seandainya hubungan itu ada, apakah investor ritel dapat "
    "mengubahnya menjadi keuntungan.",
]

PENDAHULUAN_MANFAAT = [
    "Tema GEMASTIK XIX adalah penambangan data untuk solusi yang berdampak, inklusif, dan "
    "berkelanjutan. Kami menjawab ketiga kata itu dengan angka yang dapat diperiksa, dimulai dari "
    "manfaat yang sudah siap dipakai.",

    "Manfaat yang sudah siap dipakai berupa penyaring berita harian. Penilai sentimen berbasis "
    "leksikon SENDI mencapai akurasi 66,00% dan *macro-F1* 0,6378 terhadap anotasi tiga pemeriksa "
    "manusia (Bagian IV-J), dan berjalan di laptop biasa tanpa GPU, tanpa pelatihan, serta tanpa "
    "langganan data berbayar. Bentuk keluarannya ada pada Gambar 9, diambil dari hari bursa "
    "terakhir pada korpus. Pada 13 Agustus 2026 penilai memangkas 348 judul yang terbit hari itu "
    "menjadi 54 judul bersentimen berarah, sehingga beban baca turun ke 15,5%. Setiap baris yang "
    "tersisa membawa istilah leksikon yang memicunya, sehingga pembaca dapat membantah "
    "penilaiannya dan tidak perlu menerimanya begitu saja. Investor ritel dan jurnalis pasar "
    "modal termasuk pemakai yang langsung terbantu.",

    "Peneliti NLP Bahasa Indonesia mendapat bahan mentahnya. Enam sumber daya pada Tabel II "
    "selama ini harus dibangun ulang sendiri oleh setiap kelompok yang menyentuh teks keuangan "
    "Indonesia, termasuk leksikon domain dan *gold standard* pertama untuk tugas ini. *Gazetteer* "
    "942 emiten dengan 3.585 alias menaikkan F1 pengenalan kode saham dari 0,1227 menjadi 0,8827 "
    "dibandingkan model NER umum, dan kenaikan itu berasal dari datanya, bukan dari algoritmanya.",

    "Manfaat yang berdampak di sini berbentuk perlindungan. Strategi sentimen sederhana merugi "
    "pada seluruh 12 kombinasi parameter yang diuji. Kerugiannya bertahan ketika biaya transaksi "
    "dinolkan, berada di dalam sebaran sepuluh sinyal acak, dan tidak hilang pada periode yang "
    "belum pernah dilihat model. Klaim “AI trading” yang beredar luas perlu dihadapkan pada bukti "
    "setingkat ini sebelum dipercaya, dan temuan semacam itu jarang diterbitkan karena berlawanan "
    "dengan kepentingan pihak yang menjual sistem prediksi.",

    "Untuk kata inklusif, jawaban yang mudah datang dari lisensinya. Seluruh kode dan sumber daya "
    "SENDI berlisensi MIT, sehingga siapa pun boleh memakainya. Jawaban yang lebih jujur datang "
    "dari Bagian IV-F. Cakupan berita antaremiten sangat timpang, dan 19,8% emiten BEI tidak "
    "pernah disebut satu kali pun pada subhimpunan korpus yang sah dipakai menaksir perhatian "
    "media. Untuk emiten tersebut, alat berbasis berita buatan siapa pun tidak akan menolong, dan "
    "batas struktural itu baru dapat dibicarakan setelah diukur.",

    "Sisi berkelanjutannya terletak pada umur pakai sumber dayanya, yang tidak ikut usang ketika "
    "arsitektur model berganti. Leksikon, kamus *slang*, daftar kode ambigu, *gazetteer*, dan "
    "korpus berlabel dapat dipakai ulang untuk tugas yang sama sekali berbeda, misalnya "
    "pengelompokan berita, penarikan informasi aksi korporasi, atau penelitian linguistik korpus, "
    "dan kegunaannya tidak bergantung pada kelangsungan sistem SENDI sendiri.",
]

PENDAHULUAN_BATASAN = [
    "Batasan berikut berlaku dan perlu dibaca bersama seluruh angka yang dilaporkan.",
]
BATASAN_ITEMS = [
    "*Universe* evaluasi finansial dibatasi pada LQ45, yaitu 45 emiten paling likuid, karena "
    "hanya di sana data harga harian cukup rapat untuk *event study* dan *backtest*.",
    "Korpus berisi judul berita saja. Hanya 177 dari 32.863 judul unik (0,54%) yang badan "
    "teksnya berhasil diambil.",
    "Berita dikumpulkan lewat agregator, sehingga cakupan antaremiten tidak merata dan "
    "kepadatan korpus antartahun berbeda jauh.",
    "Label sentimen untuk pelatihan berasal dari dua sumber otomatis yang diaudit terhadap "
    "sampel beranotasi manusia, tanpa anotasi manusia skala penuh.",
    "*Backtest* tidak memodelkan *slippage* maupun dampak pasar, sehingga hasilnya merupakan "
    "batas atas kinerja strategi dan bukan taksiran realistis.",
    "Keanggotaan indeks memakai komposisi terkini sehingga terkena *survivorship bias*.",
    "Dua komponen pemodelan yang ada di dalam repositori, yaitu graf neural temporal dan "
    "News-LSTM, tidak dilatih dan tidak menyumbang satu angka pun pada laporan ini, sedangkan "
    "*ensemble* yang benar-benar berjalan menggabungkan empat komponen berbasis aturan.",
]

# ----------------------------------------------------------------------------
# II. KAJIAN TERKAIT
# ----------------------------------------------------------------------------

KAJIAN = [
    ("Sumber daya sentimen keuangan",
     ["Loughran dan McDonald [1] menunjukkan bahwa leksikon sentimen umum salah arah ketika "
      "dipakai pada teks keuangan, karena kata seperti *liability*, *tax*, atau *cost* terbaca negatif "
      "oleh kamus umum padahal netral dalam laporan keuangan. Temuan itu melahirkan leksikon "
      "khusus domain yang sampai sekarang menjadi rujukan. Malo dkk. [2] menyusun Financial "
      "PhraseBank, korpus sentimen keuangan berlabel manusia yang menjadi tolok ukur banyak "
      "pekerjaan berikutnya. Araci [3] dan Yang dkk. [4] memindahkan pendekatan itu ke "
      "*transformer* lewat dua varian FinBERT.",
      "Seluruhnya berbahasa Inggris. Kami menelusuri Hugging Face Hub, Kaggle, Zenodo, dan GitHub "
      "pada Agustus 2026 dengan kombinasi kata kunci sentimen, keuangan, saham, dan Bahasa "
      "Indonesia, lalu memeriksa daftar tugas pada IndoNLU [6] dan IndoLEM [5] satu per satu. "
      "Kami tidak menemukan leksikon sentimen keuangan Bahasa Indonesia yang dipublikasikan "
      "terbuka, maupun kamus *slang* investor Indonesia yang memuat istilah seperti "
      "*ARA*, *ARB*, *nyangkut*, atau *cuan*. Celah inilah yang ditutup Bagian III-B."]),

    ("Pemrosesan bahasa alami Bahasa Indonesia",
     ["Koto dkk. [5] merilis IndoLEM dan IndoBERT, yakni adaptasi arsitektur BERT [8] ke "
      "Bahasa Indonesia, sementara Wilie dkk. [6] merilis *benchmark* IndoNLU. Keduanya menjadi "
      "fondasi hampir seluruh pekerjaan NLP Bahasa Indonesia berbasis *transformer*. Aji dkk. "
      "[7] memetakan tantangan bahasa dan dialek di Indonesia yang masih kurang terwakili.",
      "*Benchmark* tersebut bersifat umum. Analisis sentimen di dalamnya berbasis ulasan produk "
      "dan komentar media sosial, jauh dari berita pasar modal. Tidak satu pun menangani "
      "persoalan kode emiten yang bertabrakan dengan kata umum, padahal itulah hambatan "
      "pertama ketika teks keuangan Indonesia diproses secara otomatis."]),

    ("Prediksi pergerakan harga berbasis teks",
     ["Bollen dkk. [9] mengaitkan suasana hati agregat di Twitter dengan indeks Dow Jones. "
      "Ding dkk. [10] memakai *event embedding* untuk memprediksi arah harga. Hu dkk. [11] dan "
      "Xu serta Cohen [12] mengembangkan arsitektur perhatian atas berita dan cuitan, "
      "sementara Sawhney dkk. [13] menambahkan korelasi antarperusahaan.",
      "Hampir seluruh pekerjaan tersebut dijalankan di pasar maju berbahasa Inggris. Replikasi "
      "pada pasar berkembang dengan struktur likuiditas yang berbeda jarang dilakukan, dan yang "
      "melaporkan hasil negatif lebih jarang lagi. Pertanyaan yang belum terjawab adalah apakah "
      "hubungan sentimen dan imbal hasil yang dilaporkan di sana "
      "bertahan di BEI ketika diuji dengan protokol yang sama ketatnya."]),

    ("Efisiensi pasar dan metodologi *event study*",
     ["Fama [14] merumuskan hipotesis pasar efisien, dan Fama dkk. [15] memperkenalkan "
      "kerangka *event study* yang dipakai sampai sekarang. Brown dan Warner [16] membakukan "
      "penggunaannya pada imbal hasil harian, sementara Boehmer dkk. [17] mengusulkan uji "
      "standardized cross-sectional (BMP) yang tahan terhadap ragam yang berubah akibat "
      "peristiwa dan terhadap penggerombolan peristiwa pada tanggal yang sama; MacKinlay [18] "
      "merangkum keseluruhannya. Tetlock [19], [20] menghubungkan nada media dengan imbal "
      "hasil dan fundamental perusahaan.",
      "Pengujian setara pada BEI dengan sumber berita berbahasa Indonesia belum dilakukan "
      "secara terbuka dan dapat direproduksi. Laporan ini menjalankan uji t dan uji BMP "
      "berdampingan, lalu mengoreksi keduanya untuk pengujian ganda."]),

    ("*Weak supervision* dan reliabilitas anotasi",
     ["Mintz dkk. [21] memperkenalkan *distant supervision*, dan Ratner dkk. [22] serta Zhang "
      "dkk. [23] mengembangkannya menjadi *weak supervision* terprogram. Pelabelan berbasis "
      "reaksi harga yang dipakai di sini termasuk keluarga itu, karena labelnya diturunkan "
      "dari sinyal eksternal alih-alih dari penilaian manusia.",
      "Audit atas derau pengaitan yang menyertainya jarang dikerjakan. Krippendorff [24] dan "
      "Artstein serta Poesio [25] menyediakan kerangka mengukur reliabilitas antar-anotator. Kami "
      "memakainya untuk menaksir seberapa tinggi batas atas "
      "yang dapat dicapai model terhadap label otomatis semacam itu."]),

    ("Model bahasa besar dan metodologi *backtest*",
     ["Lopez-Lira dan Tang [26] menguji ChatGPT sebagai penilai sentimen berita saham, dan Wu "
      "dkk. [27] melatih BloombergGPT khusus domain keuangan. Pembandingan setara antara "
      "model *zero-shot* dan model ter-*fine-tune* pada bahasa selain Inggris masih jarang.",
      "Di sisi evaluasi strategi, Bailey dkk. [28], Harvey dkk. [29], dan Lopez de Prado [30] "
      "menunjukkan bagaimana pemilihan konfigurasi terbaik dari banyak percobaan menghasilkan "
      "kinerja semu. Argumen mereka mendasari keputusan kami melaporkan seluruh 12 kombinasi "
      "parameter beserta kontrol acaknya alih-alih yang terbaik saja, serta memakai koreksi "
      "Holm [31] pada setiap kelompok pengujian."]),
]

KAJIAN_ANTARA = (
    "Enam kelompok di atas memetakan tempat penelitian ini berdiri. Tiga subbagian berikut "
    "beralih ke perkakasnya, yaitu ketiga penilai sentimen yang nanti diadu berdampingan pada "
    "Bagian IV-J. Urutannya menaik menurut kebutuhan komputasi, dari kamus tanpa pelatihan sampai "
    "*transformer*. Rumus yang dituliskan mengikuti implementasi yang benar-benar dipakai, bukan "
    "bentuk umumnya di literatur."
)

# --- II-G  Leksikon -----------------------------------------------------------

KAJIAN_LEKSIKON = [
    "Pendekatan leksikon menilai sentimen dengan mencocokkan istilah bermuatan terhadap kamus "
    "berbobot, tanpa pelatihan dan tanpa data berlabel. Loughran dan McDonald [1] menegaskan "
    "bahwa kamus umum tidak dapat dipakai langsung pada teks keuangan, sehingga bobotnya harus "
    "disusun ulang di dalam domain. Kelemahan klasiknya adalah kebutaan terhadap konteks, dan "
    "tiga lapisan di bawah ditambahkan untuk menutupnya.",

    "Untuk sebuah judul *d*, penjelajah kamus menghasilkan himpunan pemicu *H*(*d*), yaitu "
    "seluruh istilah leksikon yang cocok, dengan pencocokan frasa terpanjang didahulukan agar "
    "“melampaui ekspektasi” tidak dipecah menjadi “melampaui”. Setiap pemicu ke-*i* membawa "
    "bobot dasar *β* dari kamus, lalu dikoreksi oleh konteks empat token di depannya "
    "seperti pada Persamaan (1) dan (2).",
]

EQ_LEKSIKON_1 = [
    "*w*_{i} = (−0,8)^{[neg]} · *m*_{i} · *β*(*t*_{i})",
    "*m*_{i} = ∏_{j=1}^{4} *λ*(*u*_{ij})",
]

KAJIAN_LEKSIKON_2 = [
    "Indikator [neg] bernilai 1 ketika ada kata negasi di dalam jendela tersebut. Faktor −0,8 "
    "dipakai alih-alih −1 karena menyangkal kabar baik tidak sekuat menegaskan kabar buruk; "
    "“tidak untung” lebih lemah daripada “rugi”. Fungsi *λ* memberi nilai penguat intensitas "
    "untuk token penguat, dan 1 − 0,1*j* untuk kata negasi yang berjarak *j* token, sehingga "
    "negasi yang jauh melemah dengan sendirinya. Token lain memberi *λ* = 1.",

    "Skor judul kemudian dinormalisasi dan diredam seperti pada Persamaan (3) dan (4).",
]

EQ_LEKSIKON_2 = [
    "*s*(*d*) = clip( ∑ *w*_{i} / √|*H*| , −1, 1 ) · *ρ*(*d*)",
    "*ρ*(*d*) = 0,3^{[spek]} · 0,5^{[anjur]}",
]

KAJIAN_LEKSIKON_3 = [
    "Pembagi √|*H*| dipilih menggantikan rerata. Membagi rata membuat teks panjang dengan "
    "banyak kata bermuatan tampak lebih netral daripada judul pendek bermuatan satu kata kuat, "
    "padahal yang sebaliknya lebih masuk akal. Peredam *ρ* menarik skor ke netral ketika judul "
    "tidak melaporkan peristiwa. Indikator [spek] menyala pada penanda spekulasi seperti "
    "*diprediksi*, *berpotensi*, atau *bocoran*, sedangkan [anjur] menyala pada penanda "
    "anjuran dan daftar seperti *simak*, *deretan*, atau *rekomendasi*. Keduanya dipilih "
    "setelah pemeriksaan kesalahan pada himpunan pengembangan menunjukkan 76% kesalahan berupa "
    "polaritas yang dinyalakan pada judul yang dinilai netral oleh manusia.",

    "Pelabelan akhirnya memakai zona netral simetris pada Persamaan (5), dengan *τ* = 0,12 dan "
    "label *neutral* untuk seluruh skor di dalam zona itu.",
]

EQ_LEKSIKON_3 = [
    "*y*(*d*) = bullish bila *s* > *τ*,  bearish bila *s* < −*τ*",
]

KAJIAN_LEKSIKON_4 = [
    "Varian tingkat aspek yang dipakai pada laporan ini membatasi cakupannya lebih jauh. Untuk "
    "pasangan judul *d* dan emiten *e*, skor dihitung hanya atas kalimat yang memuat kode atau "
    "alias *e*, dan ketika tidak ada satu pun kalimat semacam itu penilaiannya ditahan pada "
    "*neutral* alih-alih jatuh ke skor dokumen. Aturan menahan diri itulah yang membedakan "
    "analisis sentimen berbasis aspek dari penjumlahan kata biasa, dan akibat terukurnya "
    "dilaporkan pada Bagian V-D."
]

# --- II-H  TF-IDF -------------------------------------------------------------

KAJIAN_TFIDF = [
    "*Baseline* terlatih yang dipakai di sini memakai pembobotan TF-IDF dengan regresi logistik "
    "multinomial. Perannya adalah pembanding jujur bagi *transformer* dan bukan kandidat model "
    "terbaik, karena keduanya dilatih pada label yang sama persis dan dinilai pada himpunan uji "
    "yang sama persis, sementara *baseline* ini selesai dalam hitungan detik di CPU.",

    "Judul diubah menjadi vektor *n-gram* satu sampai dua kata, dengan ambang kemunculan minimal "
    "dua dokumen dan batas 50.000 fitur. *Bigram* penting pada domain ini karena “gagal bayar”, "
    "“laba turun”, dan “rugi bersih” kehilangan polaritasnya bila dipecah. Bobot tiap fitur "
    "mengikuti Persamaan (6) dan (7), dengan frekuensi sublinear agar pengulangan kata yang "
    "sama tidak dihargai secara linear.",
]

EQ_TFIDF_1 = [
    "*x*_{td} = (1 + ln *tf*_{td}) · *idf*_{t}",
    "*idf*_{t} = ln((1 + *N*) / (1 + *n*_{t})) + 1",
]

KAJIAN_TFIDF_2 = [
    "Di sini *tf* adalah frekuensi fitur *t* pada judul *d*, *N* jumlah judul pada data latih, "
    "dan *n* jumlah judul yang memuat *t*. Vektor hasilnya dinormalisasi ke panjang satu, lalu "
    "masuk ke regresi logistik multinomial pada Persamaan (8) dan (9).",
]

EQ_TFIDF_2 = [
    "*z*_{k} = *w*_{k}^{⊤} *x* + *b*_{k}",
    "*P*(*y* = *k* | *x*) = exp(*z*_{k}) / ∑_{j} exp(*z*_{j})",
]

KAJIAN_TFIDF_3 = [
    "Parameternya ditaksir dengan meminimumkan Persamaan (10), yaitu galat entropi silang "
    "berbobot kelas ditambah penalti L2.",
]

EQ_TFIDF_3 = [
    "*L* = ∑_{i} *c*_{i} · ( −ln *P*(*y*_{i} | *x*_{i}) ) + ‖*W*‖² / 2*C*",
]

KAJIAN_TFIDF_4 = [
    "Bobot kelas pada suku pertamanya membagi jumlah seluruh contoh dengan hasil kali jumlah "
    "kelas dan jumlah contoh kelas bersangkutan, dengan jumlah kelas *K* = 3. Tanpa penyeimbangan "
    "itu *baseline* belajar mengabaikan kelas *bearish* yang paling jarang, padahal kelemahan "
    "itulah yang ingin diukur pada model neural.",
]

# --- II-I  Transformer dan IndoBERT ------------------------------------------

KAJIAN_TRANSFORMER = [
    "Model terlatih ketiga adalah IndoBERT [5], yaitu adaptasi arsitektur BERT [8] ke Bahasa "
    "Indonesia. Varian yang dipakai di sini, *indobenchmark/indobert-base-p1*, menumpuk "
    "*L* = 12 blok *encoder* dengan dimensi tersembunyi *d* = 768 dan *h* = 12 kepala perhatian, "
    "berjumlah sekitar 125 juta parameter. Susunannya ada pada Gambar 1.",

    "Judul dipecah menjadi subkata WordPiece, diapit token khusus [CLS] dan [SEP], lalu "
    "dipetakan menjadi matriks *X* berukuran *n* × *d* yang menjumlahkan *embedding* token, segmen, dan "
    "posisi. Inti setiap blok adalah perhatian diri berskala pada Persamaan (11), yang membuat "
    "setiap token menimbang seluruh token lain di judul yang sama.",
]

EQ_TRANSFORMER_1 = [
    "Attention(*Q*,*K*,*V*) = softmax(*QK*^{⊤} / √*d*_{k}) *V*",
    "MHA(*X*) = [head_{1} ; … ; head_{h}] *W*^{O}",
]

KAJIAN_TRANSFORMER_2 = [
    "Matriks *Q*, *K*, dan *V* adalah proyeksi linear dari masukan blok, sedangkan dimensi "
    "tiap kepala bernilai *d*/*h* = 64. Pembagi berupa akar dimensi kepala itu menjaga "
    "hasil kali titik tetap pada "
    "skala yang membuat gradien softmax-nya tidak jenuh. Perhatian dari *h* kepala digabung "
    "seperti pada Persamaan (12), lalu satu blok menyelesaikan pekerjaannya lewat dua "
    "sublapis berumpan-maju dengan sambungan residual dan normalisasi lapis pada Persamaan "
    "(13) dan (14).",
]

EQ_TRANSFORMER_2 = [
    "*X*′ = LN( *X*_{ℓ−1} + MHA(*X*_{ℓ−1}) )",
    "*X*_{ℓ} = LN( *X*′ + FFN(*X*′) )",
]

KAJIAN_TRANSFORMER_3 = [
    "FFN adalah dua lapis linear dengan aktivasi GELU dan dimensi antara 3.072. Sambungan "
    "residual itu yang membuat tumpukan sedalam dua belas blok tetap dapat dilatih. Untuk "
    "klasifikasi, vektor [CLS] dari blok terakhir dilewatkan *dropout* dan satu lapis linear tiga "
    "keluaran seperti pada Persamaan (15).",
]

EQ_TRANSFORMER_3 = [
    "*p* = softmax( *W h*_{[CLS]} + *b* )",
]

KAJIAN_TRANSFORMER_4 = [
    "Penerapan di sini berbeda dari resep bawaannya pada bagian galat. Setiap contoh latih "
    "membawa bobot *a* yang diturunkan dari keyakinan pelabelnya, sehingga contoh yang "
    "lemah tidak menyeret pelatihan sekuat contoh yang tegas, dan galat satu *batch* dihitung "
    "seperti pada Persamaan (16).",
]

EQ_TRANSFORMER_4 = [
    "*L* = ∑_{i} *a*_{i} · ℓ_{i} / ∑_{i} *a*_{i}",
]

KAJIAN_TRANSFORMER_5 = [
    "Suku ℓ adalah entropi silang satu contoh. Karena bobot per contoh itu tidak dapat disisipkan "
    "ke pemandu pelatihan bawaan tanpa menurunkan subkelas yang malah lebih panjang, loop "
    "pelatihannya ditulis langsung. Hiperparameternya dibiarkan pada nilai yang lazim, yaitu laju "
    "belajar 2 × 10⁻⁵, *batch* 16, panjang urutan maksimum 128, dan empat *epoch* dengan "
    "penghentian dini. Seluruh nilai itu ditahan tetap ketika percobaan pergantian tingkat label "
    "pada Bagian V-D dijalankan, sehingga selisih yang terukur di sana tidak dapat dijelaskan "
    "oleh penalaan.",
]

KAJIAN_PENUTUP = (
    "Kesembilan subbagian di atas meninggalkan celah yang sama. Bahasa Indonesia tidak memiliki "
    "sumber daya keuangannya, pasar Indonesia belum diuji dengan protokol yang sama ketatnya, dan "
    "hasil negatif nyaris tidak pernah dilaporkan. Bagian III-D menyatakan secara eksplisit di "
    "titik mana SENDI berbeda dari masing-masing celah tersebut."
)

# ----------------------------------------------------------------------------
# III. SOLUSI USULAN
# ----------------------------------------------------------------------------

SOL_DESKRIPSI = [
    "SENDI dirancang sebagai *pipeline* enam lapis yang dapat dijalankan ujung ke ujung dengan "
    "satu rangkaian perintah. Gambar 2 menunjukkan susunannya.",

    "*Lapis 1, pengumpulan.* Lapis ini menarik umpan RSS dari sepuluh media keuangan untuk "
    "berita terkini, lalu menjelajahi arsip mesin pencari berita dengan operator rentang "
    "tanggal untuk membangun korpus historisnya. Data harga harian diambil untuk 45 emiten "
    "LQ45 beserta IHSG, dan deduplikasinya memakai SimHash 64-bit [35].",

    "*Lapis 2, pemrosesan bahasa.* Judul yang masuk dinormalisasi dan dikembalikan ke bentuk "
    "dasarnya, kode emitennya dikenali lewat *gazetteer* beserta lapisan disambiguasi "
    "kontekstual, sentimennya dinilai leksikon pada tingkat aspek, dan penanda aksi "
    "korporasinya ditarik.",

    "*Lapis 3, fitur dan graf.* Lapis ini menyusun fitur teks dan fitur teknikal, meluruhkan "
    "skor sentimen menurut jarak waktunya, lalu memakai *knowledge graph* relasi antaremiten "
    "untuk merambatkan sentimen ke emiten yang terkait.",

    "*Lapis 4, pemodelan.* Tiga penilai dijalankan berdampingan, yaitu IndoBERT yang "
    "di-*fine-tune* untuk klasifikasi tiga kelas, TF-IDF dengan regresi logistik sebagai "
    "*baseline* terlatih, dan leksikon sebagai *baseline* tanpa pelatihan.",

    "*Lapis 5, keluaran.* Keluarannya berupa skor sentimen per pasangan judul-emiten, "
    "kontribusi faktor yang menyusun setiap skor, dan narasi penjelas yang menyebutkan istilah "
    "leksikon pemicu penilaian tersebut.",

    "*Lapis 6, evaluasi.* Seluruh pengujian yang dilaporkan pada Bagian IV berjalan di "
    "lapis ini dan menuliskan hasilnya ke berkas yang sama yang menjadi sumber setiap angka "
    "di naskah ini.",

    "Batas evaluasinya perlu dinyatakan terus terang. Modul graf neural temporal dan News-LSTM "
    "tersedia sebagai kode di dalam repositori, tetapi tidak pernah dilatih dan tidak menyumbang "
    "angka apa pun pada laporan ini. *Ensemble* yang berjalan menggabungkan empat komponen "
    "berbasis aturan, bukan empat model terlatih.",
]

SOL_DATASET = [
    "Kebaruan penelitian ini terutama terletak pada datasetnya. Enam sumber daya kami rilis "
    "terbuka, dan seluruhnya dapat diperiksa ulang oleh penguji. Tabel I merinci komposisi "
    "korpus, sedangkan Tabel II merinci sumber daya yang dirilis beserta padanan publiknya.",

    "Dua paket dataset dirilis berdampingan, dan keduanya dibangun dari korpus judul yang sama. "
    "Paket pertama berlabel reaksi harga di tingkat dokumen, dipakai mempelajari reaksi pasar "
    "terhadap berita. Paket kedua berlabel leksikon di tingkat aspek, yaitu satu contoh untuk "
    "setiap pasangan judul dan emiten, dipakai melatih model sentimen. Keduanya kami rilis karena "
    "selisih di antara keduanya mengukur seberapa besar cara pelabelan menentukan hasil, dengan "
    "segala hal lain ditahan tetap; kalau yang dirilis hanya satu, selisih itu tinggal klaim yang "
    "tidak dapat diperiksa ulang orang lain. Ukuran dan pembagian paket kedua dirinci pada Tabel "
    "XVII, dan akibat pergantian tingkat labelnya dilaporkan pada Bagian V-D.",

    "Korpus dikumpulkan sepanjang Januari 2022 sampai Agustus 2026. Dari 40.009 judul yang "
    "terkumpul, deduplikasi SimHash menyisakan 32.863 judul unik; 7.146 sisanya (17,86%) "
    "adalah duplikat lintas media, yang lazim terjadi karena banyak media menerbitkan ulang "
    "rilis kantor berita. Kepadatan korpus tidak merata antartahun, dengan 2026 menyumbang 10.385 "
    "judul sedangkan 2022 hanya 4.174, karena mesin pencari mengembalikan hasil yang jauh "
    "lebih lengkap untuk periode terkini. Kami menyebut ketidakmerataan ini di muka karena ia "
    "memengaruhi setiap perbandingan antarperiode yang muncul kemudian, terutama pada Bagian "
    "V-G.",

    "Korpus yang kami kumpulkan berisi judul, sementara artikel utuhnya sebagian besar tidak "
    "terambil; badan teks hanya berhasil diambil untuk 177 judul (0,54%). Seluruh model dan "
    "seluruh sinyal pada laporan ini karena itu bekerja atas judul.",

    "Master data emiten memuat 942 emiten BEI dengan 3.585 alias aktif dan diturunkan dari "
    "Wikipedia Bahasa Indonesia (CC BY-SA 4.0). Sumber daya lain berlisensi MIT. *Knowledge "
    "graph*-nya berisi 1.807 sisi, 515 di antaranya ditulis tangan (relasi grup usaha, rantai "
    "pasok, kompetitor, dan regulator), sedangkan 1.292 sisanya dibangkitkan otomatis dari kolom "
    "sektor dan keanggotaan grup. Kami membedakan keduanya agar angka 515 tidak terbaca sebagai "
    "keseluruhan graf.",
]

SOL_METODE_PENGUMPULAN = [
    "**Pengumpulan dan deduplikasi.** Umpan RSS ditarik berkala dari sepuluh media keuangan. "
    "Korpus historis dibangun dengan menjelajah arsip mesin pencari berita memakai kombinasi "
    "(emiten LQ45 × bulan) sebagai kueri. Kedua cara pengumpulan ini punya konsekuensi "
    "metodologis yang dibahas pada Bagian IV-F. Sebaran emiten pada hasil arsip dibentuk oleh "
    "rancangan kuerinya sendiri, sehingga tidak sah dipakai menaksir perhatian media. "
    "Deduplikasi memakai SimHash 64-bit dengan ambang jarak Hamming terkalibrasi.",

    "**Pengenalan kode saham.** Pengenalan bertumpu pada *gazetteer* 942 emiten dengan 3.585 "
    "alias aktif, ditambah lapisan disambiguasi berbasis konteks yang menimbang bentuk "
    "kapitalisasi, kehadiran penanda domain di sekitar kandidat, dan daftar 147 kode yang "
    "diketahui bertabrakan dengan kata umum. *Gold standard* untuk mengevaluasinya berisi 6.000 kalimat dari korpus "
    "nyata dengan 551 kode unik, dibangun lewat *distant supervision* [21] lalu diperiksa.",

    "**Pelabelan.** Dua sumber otomatis dipakai bersama satu lapis verifikasi manusia. "
    "*Weak supervision leksikon* memberi label pada tingkat dokumen dari skor kamus. "
    "*Pelabelan reaksi harga* memasangkan judul dengan *abnormal return* hari perdagangan "
    "berikutnya, dihitung dari harga penutupan tersesuaikan terhadap IHSG dengan penjaga jeda "
    "hari bursa; label ini bersifat tingkat aspek karena selalu terikat pada satu emiten yang "
    "kehadirannya dikonfirmasi NER. *Verifikasi manusia* dikerjakan pada sampel 800 judul oleh "
    "tiga pemeriksa independen dalam dua putaran, dipakai untuk menaksir derau label dan "
    "menjadi rujukan pembanding pada Bagian IV-J. Seluruh 800 judul tersebut dikeluarkan dari "
    "bagian latih dan validasi sebelum model mana pun dilatih.",

    "**Pembagian data.** Pembagian bersifat kronologis dengan *holdout out-of-time*, seperti "
    "dirinci Tabel III: latih sampai 31 Desember 2024, validasi semester pertama 2025, dan uji "
    "1 Juli 2025 sampai 13 Agustus 2026. Seluruh data uji terjadi setelah data latih berakhir, "
    "sehingga tidak ada kebocoran masa depan ke dalam pemilihan model maupun ke dalam sinyal. "
    "Pembagian acak tetap dijalankan sebagai pembanding untuk mengukur besarnya kebocoran yang "
    "dihindari.",

    "**Klasifikasi.** IndoBERT *indobenchmark/indobert-base-p1* di-*fine-tune* untuk tiga kelas "
    "dengan bobot kelas seimbang; *checkpoint* dipilih pada set validasi. *Baseline* terlatih "
    "berupa TF-IDF dengan regresi logistik pada data latih yang sama persis, dan *baseline* "
    "tanpa pelatihan berupa leksikon.",

    "**Evaluasi finansial.** *Event study* memakai model pasar OLS dengan jendela penaksiran 120 "
    "hari, jeda 10 hari, dan *event window* [-1, +5], diuji dengan uji t serta uji BMP [17]. "
    "*Backtest* memakai biaya transaksi ritel BEI, yakni 0,15% beli dan 0,25% jual, dan "
    "dijalankan pada dua periode, yaitu 2022-2024 yang sebagian *in-sample* dan 2025-2026 "
    "yang seluruhnya *out-of-sample*.",
]

SOL_PERBEDAAN = [
    "Panduan lomba menyebut unsur ini secara eksplisit. Tabel IV membandingkan SENDI dengan "
    "praktik yang lazim dijumpai pada penelitian terdahulu yang dibahas di Bagian II.",
    "Enam baris terakhir tabel tersebut memuat perbedaan yang paling menentukan. Laporan ini "
    "menyatakan bahwa strategi sederhana gagal pada 12 dari 12 kombinasi parameter, bahwa "
    "kegagalannya bukan akibat biaya transaksi, bahwa kegagalan itu bertahan pada periode yang "
    "belum pernah dilihat model, bahwa model *transformer*-nya tidak terbukti mengungguli "
    "*baseline* klasik, dan bahwa arah asimetri yang ditemukan pada satu periode berbalik ketika "
    "periodenya diperluas. Setiap temuan itu kemudian dijelaskan sebabnya di Bagian V.",
]

SOL_METRIK = [
    "Tabel V merangkum metrik yang dipakai di setiap aspek pengujian. Tiga keputusan metrik di "
    "bawah perlu diberi alasan tersendiri.",
    "Pertama, *macro-F1* dipakai sebagai metrik utama pada perbandingan terhadap rujukan "
    "manusia, bukan akurasi, karena sebaran kelas pada sampel beranotasi timpang dan akurasi "
    "memberi kredit besar pada perilaku menebak satu kelas terus-menerus.",
    "Kedua, selisih antarmodel diuji dengan uji berpasangan, yakni *bootstrap* berpasangan "
    "[32] atas selisih *weighted-F1* dan uji McNemar binomial eksak [36] atas kebenaran per "
    "judul. Menyandingkan dua angka akurasi belum merupakan uji, sebab ketiga penilai dinilai "
    "pada judul yang persis sama sehingga kesalahannya berkorelasi [33].",
    "Ketiga, setiap kelompok pengujian dikoreksi Holm-Bonferroni [31], dan hasil yang "
    "tidak bertahan setelah koreksi tetap dilaporkan.",
]

# ----------------------------------------------------------------------------
# IV. HASIL
# ----------------------------------------------------------------------------

HASIL_PEMBUKA = (
    "Bagian ini melaporkan hasil tanpa menafsirkannya; tafsir seluruhnya ditempatkan pada "
    "Bagian V. Seluruh angka dibangkitkan oleh kode dan tersimpan pada berkas hasil yang "
    "menyertai repositori, sehingga setiap angka di bawah dapat ditelusuri ke keluaran "
    "programnya."
)

HASIL_KORPUS = [
    "Komposisi korpus disajikan pada Tabel I dan sebaran bulanannya pada Gambar 3. Dari "
    "40.009 judul terkumpul, tersisa 32.863 judul unik setelah deduplikasi SimHash, dengan "
    "7.146 duplikat (17,86%). Sebaran per tahun menaik tajam, dari 4.174 pada 2022, 4.932 pada "
    "2023, 5.601 pada 2024, 7.771 pada 2025, sampai 10.385 pada 2026 hingga pertengahan Agustus. "
    "Dari korpus tersebut diekstrak 54.343 entitas emiten dan 72.066 skor sentimen, "
    "berdampingan dengan 54.613 baris harga harian.",
]

HASIL_NER = [
    "Tabel VI membandingkan empat metode pengenalan kode saham pada *gold standard* 6.000 "
    "kalimat, seluruhnya dengan selang kepercayaan *bootstrap* 1.000 ulangan.",
    "Selang kepercayaan di sini lebih informatif daripada angka titiknya. Selang SENDI [0,8728; "
    "0,8925] dan selang pencocokan kode mentah [0,8717; 0,8913] bertumpang tindih hampir "
    "sempurna, sehingga selisih 0,0011 di antara keduanya tidak membawa arti. Sebaliknya, selang "
    "NER Bahasa Indonesia pra-latih [0,1080; 0,1357] terpisah jauh dari ketiganya, sehingga "
    "selisih sekitar 0,76 itu nyata. *Baseline* pra-latih sendiri sudah dibantu dalam evaluasi "
    "ini, sebab keluarannya dipetakan ke kode emiten memakai *gazetteer* SENDI; tanpa bantuan "
    "tersebut skornya nol.",
]

HASIL_SENTIMEN = [
    "Tabel VII melaporkan klasifikasi sentimen pada *holdout out-of-time*, yaitu 6.082 contoh "
    "yang seluruhnya terjadi setelah data latih berakhir dan seluruhnya berlabel reaksi harga.",
    "Tabel ini paling mudah disalahbaca, jadi rujukan kebenarannya perlu dipegang lebih dulu. "
    "Rujukan kebenaran di sini adalah label reaksi harga, sedangkan Tabel XIII nanti memakai "
    "anotasi manusia sebagai rujukan. Keduanya bukan sumbu yang sebanding, sebab label reaksi "
    "harga sendiri hanya cocok 36,22% dengan penilaian manusia (Bagian IV-I). Model yang sama "
    "karena itu dapat terlihat sangat berbeda tergantung diukur terhadap apa. IndoBERT tingkat "
    "aspek mencapai *macro-F1* 0,6026 terhadap anotasi manusia pada Tabel XIII, tetapi hanya "
    "cocok 37,34% dengan label reaksi harga pada himpunan yang persis sama. Angka 0,33-0,36 di "
    "bawah karena itu mengukur kesesuaian dengan reaksi harga H+1, bukan kemampuan membaca "
    "sentimen judul.",
    "Uji *bootstrap* berpasangan atas selisih *weighted-F1* memberi dua kesimpulan yang berbeda. "
    "Terhadap leksikon, keunggulan IndoBERT nyata, dengan selisih +0,0219 dan selang [+0,0101; "
    "+0,0346] yang tidak memuat nol. Terhadap TF-IDF, tidak ada bukti keunggulan, karena "
    "selisihnya -0,0104 dengan selang [-0,0214; +0,0011] yang memuat nol dan tandanya bahkan "
    "negatif.",
    "Ketiga penilai itu berkerumun pada pita sempit 0,33 sampai 0,36 meski pendekatannya sangat "
    "berbeda, mulai dari kamus tanpa pelatihan sampai *transformer* 125 juta parameter, dan "
    "kerumunan itu yang perlu diperhatikan. Data latihnya juga campuran dan bukan murni label "
    "reaksi harga, yaitu 6.395 contoh berlabel leksikon tingkat dokumen dan 3.467 contoh berlabel "
    "reaksi harga tingkat aspek, dengan pangsa bobot berturut-turut 63,4% dan 36,6%. Model "
    "dipilih pada set validasi yang 100% berlabel reaksi harga.",
]

HASIL_ASOSIASI = [
    "Hubungan antara sentimen dan *abnormal return* diukur pada seluruh 18.194 pasangan "
    "judul-emiten tanpa penyaringan apa pun berdasarkan besar pergerakan harga. Kelompok "
    "*bullish* (n = 9.323) memiliki rata-rata *abnormal return* H+1 sebesar +0,265%, kelompok "
    "*neutral* (n = 4.557) sebesar +0,267%, dan kelompok *bearish* (n = 4.314) sebesar +0,055%. "
    "Uji Welch antara *bullish* dan *bearish* memberi t = 3,035 dengan p = 0,0024.",
    "Dua hal perlu dicatat. Pertama, selisihnya signifikan tetapi kecil, sekitar 0,21 poin "
    "persentase. Kedua, pada korpus yang diperluas ini kelompok *bearish* sudah tidak lagi "
    "bertanda negatif, berbeda dari pengukuran versi 2022-2024 yang memberi *bullish* +0,28% "
    "berbanding *bearish* -0,31%.",
]

HASIL_EVENT = [
    "*Event study* dijalankan atas 11.963 peristiwa dengan model pasar OLS. Hasilnya pada Tabel "
    "VIII, dan kurva CAAR-nya pada Gambar 4. Peristiwa yang dilewati berjumlah 6.234 karena "
    "sentimen terlalu lemah, 4.442 karena riwayat harga tidak cukup untuk penaksiran, dan 270 "
    "karena jendela peristiwanya tidak lengkap.",
    "Berita bersentimen positif diikuti mean CAR +0,906% yang signifikan pada uji t maupun uji "
    "BMP (z = 10,110). Berita bersentimen negatif memberi mean CAR -0,467% yang signifikan "
    "pada uji t (p = 0,0025) tetapi gagal lolos uji BMP (z = -0,951; p = 0,3415). Uji "
    "selisih antara kedua kelompok memberi t = 7,224 dengan p < 0,0001.",
    "Koreksi Holm-Bonferroni atas kelima uji tersebut disajikan pada bagian bawah Tabel VIII. "
    "Empat uji bertahan, sedangkan uji BMP pada berita negatif tidak, dan uji yang gugur itu "
    "tetap dicantumkan.",
    "Uji yang sama pernah kami jalankan pada korpus yang lebih pendek, yaitu Januari 2022 sampai "
    "Desember 2024, dan angkanya kami cantumkan di sini karena Bagian V-F membahasnya. Pada "
    "korpus tersebut jumlah peristiwanya 3.461 dan yang berdampak signifikan adalah kelompok "
    "negatif, dengan mean CAR -0,91% dan p = 0,0036, sementara kelompok positif tidak signifikan. "
    "Kedua pengukuran memakai model pasar, jendela, dan prosedur uji yang sama persis; yang "
    "berbeda hanya rentang korpusnya.",
]

HASIL_CAKUPAN = [
    "Pengukuran ketimpangan cakupan menjawab pertanyaan siapa sebenarnya yang dapat ditolong "
    "sistem seperti ini. Pengukuran dipisah menurut cara pengumpulan, karena hanya sebagian "
    "yang sah dipakai menaksir perhatian media. Tabel IX menyajikan ketiganya dan Gambar 5 "
    "menampilkan kurva Lorenz-nya.",
    "Subhimpunan arsip per kueri dikumpulkan dengan menjelajah kombinasi emiten × "
    "bulan, sehingga sebaran emitennya dibentuk oleh rancangan pengumpulan itu sendiri. "
    "Menghitung ketimpangan di sana lalu menyebutnya sebagai perhatian media adalah kesalahan "
    "penalaran, dan baris tersebut kami tandai tidak sah dikutip. Subhimpunan RSS langsung "
    "tidak bias tetapi hanya memuat 222 sebutan untuk 942 emiten, terlalu jarang untuk "
    "menyimpulkan apa pun. Subhimpunan yang sah dipakai ialah sebutan insidental, yaitu emiten yang "
    "muncul pada artikel yang tidak dikueri atas namanya; jumlahnya 11.338 sebutan, sekitar 51 "
    "kali lipat RSS langsung.",
    "Kolom harapan acak wajib dibaca bersama kolom Gini. Menyebar 222 sebutan ke 942 emiten "
    "menghasilkan Gini 0,81 bahkan ketika prosesnya benar-benar merata, semata karena "
    "sebutannya lebih sedikit daripada emitennya. Pada subhimpunan insidental, Gini teramati "
    "0,8045 berbanding harapan acak 0,1617, sehingga kelebihannya +0,6428 dan ketimpangan itu "
    "nyata, bukan artefak kelangkaan data.",
    "Pada subhimpunan insidental, dari 942 emiten terdaftar hanya 756 yang pernah disebut, "
    "sehingga 186 emiten (19,8%) tidak pernah diberitakan. Sepuluh persen emiten teratas "
    "menguasai 73,1% seluruh sebutan, satu persen teratas menguasai 22,5%, dan median sebutan per "
    "emiten hanya 2.",
]

HASIL_BACKTEST = [
    "*Backtest* dilaporkan pada dua periode berdampingan, seperti pada Tabel X, dan "
    "perbandingan *total return* kedua periode pada Gambar 6. Periode kedua seluruhnya terjadi setelah data "
    "latih model berakhir pada 31 Desember 2024, sehingga tidak ada kebocoran masa depan yang "
    "dapat menjelaskan hasilnya ke arah mana pun.",
    "Pada 2022-2024 strategi merugi 48,94% sementara IHSG naik 6,22%. Pada 2025-2026 "
    "strategi merugi 34,82% sementara IHSG turun 12,03%. Strategi kalah dari *benchmark* pada "
    "kedua periode, termasuk ketika *benchmark* itu sendiri sedang turun.",
]

HASIL_KETAHANAN = [
    "Tiga pengujian tambahan dijalankan untuk memisahkan sebab kerugian tersebut, dan "
    "hasilnya dirangkum pada Tabel XI.",
    "**Ketahanan parameter.** Dua belas kombinasi lama tahan, *target profit*, *stop loss*, dan "
    "ambang keyakinan dijalankan seluruhnya. Tidak satu pun menguntungkan; *return* mediannya "
    "-66,59%, terbaik -46,27%, dan terburuk -84,87%. Seluruh dua belas kombinasi itu kami "
    "laporkan, termasuk yang terburuk.",
    "**Sensitivitas biaya.** Tujuh titik biaya diuji dari 0% sampai 0,8% per putaran, seperti "
    "pada Gambar 7. Pada biaya nol strategi tetap merugi 30,83%, dan tidak ada titik impas di "
    "sepanjang rentang yang diuji.",
    "**Kontrol acak.** Sepuluh tarikan skor sentimen acak dijalankan pada pasangan "
    "emiten-tanggal yang persis sama dengan strategi yang persis sama. Rata-ratanya "
    "-42,46% dengan rentang -56,90% sampai -29,31% dan simpangan baku 9,6 poin "
    "persentase. Hasil model, -48,94%, berada pada persentil 30 dari sebaran itu.",
]

HASIL_ANOTASI = [
    "Mutu pengaitan artikel-emiten diperiksa dari dua arah. Audit otomatis atas 19.820 "
    "pasangan menemukan bahwa 51,1% di antaranya menyebut emitennya secara tekstual di judul; "
    "untuk pasangan yang berasal dari kueri arsip angkanya hanya 11,5%, sedangkan untuk pasangan "
    "yang dikonfirmasi NER 99,6% sampai 100%. Sejak verifikasi NER diberlakukan pada pasangan "
    "kueri, 16.559 pasangan ditolak dan derau pengaitan yang diukur terhadap penandaan manusia "
    "turun dari 21,8% menjadi 0,72%.",
    "Verifikasi manusia memberi angka langsungnya. Dari 800 judul beranotasi, 92 judul (11,5%) "
    "ditandai pemeriksa sebagai tidak membicarakan emiten yang dilabelkan padanya. Putaran "
    "pertama menyumbang 87 dari 400 (21,8%); putaran kedua, yang sampelnya hanya ditarik dari "
    "pasangan terverifikasi NER, menambah 5 saja.",
    "Reliabilitas rujukan manusia itu sendiri disajikan pada Tabel XII dan menjadi prasyarat "
    "agar seluruh perbandingan pada Bagian IV-J bermakna. Tiga pemeriksa independen menilai 800 "
    "judul dengan Krippendorff's alpha 0,9029, di atas ambang 0,800 yang lazim disebut dapat "
    "diandalkan; 729 judul (91,1%) disepakati bulat dan tidak satu pun berakhir seri sempurna. "
    "Dua putaran terpisah memberi 0,8953 dan 0,9090, sehingga tingkat kesepakatan itu merupakan "
    "sifat tugasnya dan bukan kebetulan pada satu sampel.",
    "Sebagai pembanding pada rujukan yang sama, label reaksi harga H+1 hanya cocok 36,22% (n = "
    "798) dengan penilaian manusia. Penyebutnya 798, bukan 800, karena dua baris tidak memiliki "
    "label harga sama sekali akibat emitennya disuspensi atau harganya tidak tersedia; keduanya "
    "kami keluarkan dan tidak dihitung sebagai salah.",
]

HASIL_PENILAI = [
    "Seluruh penilai diadu pada himpunan uji terkunci berisi 400 judul yang tidak pernah "
    "dipakai menala apa pun dan seluruhnya dikeluarkan dari data latih maupun validasi. "
    "Hasilnya pada Tabel XIII dan Gambar 8.",
    "Leksikon v1.1 mencapai *macro-F1* 0,6378 terhadap rujukan manusia. IndoBERT dengan label "
    "tingkat aspek mencapai 0,6026 dan TF-IDF tingkat aspek 0,5810. Versi tingkat dokumen dari "
    "kedua model terlatih jauh di bawahnya, 0,4358 dan 0,4024. Label reaksi harga itu sendiri "
    "hanya mencapai 0,3179 pada himpunan yang sama, dan penebak konstan “*bullish*” "
    "memperoleh akurasi 47,50% dengan *macro-F1* hanya 0,2147.",
    "Angka terakhir itu menjelaskan mengapa *macro-F1* dipakai sebagai metrik utama di sini. "
    "Penebak konstan memperoleh akurasi yang tampak tinggi semata karena sebaran kelasnya "
    "timpang, sementara *macro-F1*-nya nol pada dua dari tiga kelas.",
    "Karena kelima penilai dinilai pada judul yang persis sama, selisihnya diuji berpasangan "
    "dengan McNemar binomial eksak. Lima belas uji dijalankan pada data yang sama dan "
    "seluruhnya dikoreksi Holm-Bonferroni; Tabel XIV memuat sebelas baris yang paling "
    "menentukan beserta status bertahannya.",
    "Baris terpenting pada tabel itu adalah IndoBERT tingkat dokumen melawan penebak konstan. Di "
    "sana 70 judul hanya benar di IndoBERT dan 69 hanya benar di penebak konstan, selisih satu "
    "judul dari 400, dengan p = 1,0000. Sebaliknya, IndoBERT tingkat aspek mengungguli penebak "
    "konstan dengan 122 berbanding 70 judul diskordan dan p = 0,000215 yang bertahan setelah "
    "koreksi. Selisih antara leksikon dan IndoBERT tingkat aspek tidak bertahan koreksi (p = "
    "0,012775 terhadap ambang 0,008333), sehingga keduanya seri secara statistik.",
]

# ----------------------------------------------------------------------------
# V. ANALISIS
# ----------------------------------------------------------------------------

AN_NER = [
    "F1 sebesar 0,1227 untuk model NER Bahasa Indonesia pra-latih menandakan kegagalan yang "
    "bersebab struktural, dan tiga hal menjelaskannya.",
    "Pertama, tugasnya memang berbeda. NER umum dilatih menandai rentang teks berlabel ORG, PER, "
    "atau LOC, dan tidak pernah dilatih memetakan entitas ke pengenal kanonik; kode saham berada "
    "di luar kategori yang dikenalnya. Kedua, kode empat huruf tidak menyerupai nama organisasi "
    "dalam data pelatihan model umum, sehingga jarang ditandai. Ketiga, memetakan nama perusahaan "
    "ke kode emiten memerlukan pengetahuan domain yang tidak dimiliki model umum. Bahkan ketika "
    "ia berhasil menandai “Bank Central Asia” sebagai organisasi, tidak ada jalan menurunkan BBCA "
    "dari situ tanpa daftar emiten.",
    "Temuan ini mengubah cara membaca kontribusi penelitian kami. Sumber daya domainnyalah "
    "yang benar-benar menolong, yaitu daftar 942 emiten dengan 3.585 alias yang sebelumnya "
    "tidak tersedia dalam bentuk siap pakai, sementara algoritma disambiguasinya hampir tidak "
    "berperan.",
]

AN_DISAMBIGUASI = [
    "Hipotesis awal kami adalah bahwa 147 kode emiten yang bertabrakan dengan kata umum akan "
    "menghasilkan banyak positif palsu, sehingga lapisan disambiguasi kontekstual akan memberi "
    "keunggulan terukur. Pengukuran membantah hipotesis itu.",
    "Sebabnya sederhana dan hanya terlihat setelah diukur pada korpus nyata. Kode emiten selalu "
    "ditulis dengan huruf besar seluruhnya sedangkan kata biasa tidak, dan judul berita yang "
    "berkapital penuh kurang dari 0,1% korpus. Bentuk kapitalisasi itu sendiri sudah menjadi "
    "penanda disambiguasi yang kuat, sehingga lapisan tambahan hampir tidak punya pekerjaan "
    "tersisa. Akronim bisnis yang juga menjadi kode BEI pun hanya ditemukan dua, yakni CARS dan "
    "CASA.",
    "Perbedaan itu membawa pelajaran metodologis. Himpunan uji buatan tangan yang kalimatnya "
    "dikarang oleh penulis sistem memberi F1 1,000 dan menyesatkan, sedangkan *gold standard* "
    "yang ditarik dari korpus nyata memberi 0,8827 dan menunjukkan bahwa *baseline* sederhana "
    "sama baiknya. Kami menilai pengukuran yang membantah hipotesis penulisnya sendiri lebih "
    "berguna daripada himpunan uji yang menguntungkan penulisnya.",
]

AN_TRANSFORMER = [
    "*Transformer* 125 juta parameter yang tidak mengungguli regresi logistik, padahal yang kedua "
    "selesai dalam hitungan detik di CPU, adalah hasil yang menuntut penjelasan, dan kami "
    "mengajukan tiga penjelasan yang terakhirnya dapat diuji.",
    "Penjelasan pertama, judul berita pendek dan formulaik, sehingga kosakata domainnya "
    "terbatas dan *n-gram* sudah menangkap sebagian besar sinyal permukaannya. Penjelasan kedua, "
    "rasio sinyal terhadap derau memang rendah; ketika tiga pendekatan yang sangat berbeda "
    "berkerumun pada pita 0,33-0,36, arsitektur sudah bukan lagi faktor yang membedakan.",
    "Penjelasan ketiga paling menentukan: batasnya ada pada label, bukan pada model. Susunan "
    "sinyal latih sudah menjelaskan sebagian besarnya, dan Tabel XV merincinya. Dua pertiga bobot "
    "latih berasal dari label leksikon tingkat dokumen yang tidak membawa emiten, dan hanya 6,6% "
    "di antaranya berlabel netral, padahal evaluasinya dilakukan terhadap anotasi manusia yang "
    "bertingkat aspek dan kelas netral paling sering dipilih manusia pada judul tak berarah. "
    "Sepertiga sisanya bertingkat aspek tetapi berderau, karena label reaksi harga hanya cocok "
    "33,83% dengan manusia pada himpunan uji terkunci. Kesadaran aspek dengan demikian hanya "
    "datang dari sepertiga yang berderau, kesadaran sentimen hanya datang dari dua pertiga yang "
    "buta aspek, dan tidak ada satu pun saluran sinyal yang memberi model persis apa yang "
    "ditanyakan evaluasinya.",
    "Uji McNemar pada Tabel XIV menajamkan pernyataan itu. IndoBERT tingkat dokumen tidak dapat "
    "dibedakan dari menjawab “*bullish*” untuk setiap judul, dengan p = 1,0000. Arah "
    "sebaliknya menuntut kehati-hatian. TF-IDF tingkat dokumen memang berada di bawah penebak "
    "konstan pada 76 berbanding 100 judul diskordan, tetapi p = 0,0827 tidak bertahan setelah "
    "koreksi, sehingga yang sah dinyatakan hanyalah “tidak terbukti melewatinya”.",
]

AN_UJI_LABEL = [
    "Kesimpulan bahwa yang mengikat adalah label akan tetap berupa dugaan selama labelnya tidak "
    "benar-benar diperbaiki dan akibatnya diukur. Karena itu, kami menjalankan satu percobaan "
    "tambahan. Label lemah dibangkitkan ulang per emiten yang disebut di judul, alih-alih satu "
    "skor per dokumen. Arsitektur, hiperparameter, dan *seed* dibiarkan sama persis, sehingga "
    "tepat satu hal yang berubah.",
    "Hasilnya pada Tabel XVI. IndoBERT naik dari *macro-F1* 0,4358 ke 0,6026 dan TF-IDF naik dari "
    "0,4024 ke 0,5810. Dua hal perlu dibaca dari situ. Pertama, kedua arsitektur naik dengan "
    "besaran yang mirip. Seandainya hanya *transformer* yang naik, penjelasan yang wajar adalah "
    "kapasitas model; karena regresi logistik ikut naik sebesar itu, penjelasannya kembali ke "
    "label. Kedua, IndoBERT tingkat aspek berpindah dari tidak dapat dibedakan dari penebak "
    "konstan (p = 1,0000) menjadi mengunggulinya secara signifikan (p = 0,000215, bertahan Holm "
    "atas 15 uji). Model dan *baseline*-nya sama, tetapi kesimpulannya berbalik arah.",
    "Model tingkat aspek itu dilatih atas himpunan yang berbeda dari himpunan pada Tabel XV, "
    "dan bedanya perlu disebut supaya kedua tabel tidak terbaca sebagai satu data yang sama. "
    "Tabel XVII merincinya.",

    "Contoh dibangkitkan per pasangan judul dan emiten, bukan per judul. Satu judul yang menyebut "
    "dua emiten karena itu menghasilkan dua contoh, dan keduanya boleh berlabel berlawanan bila "
    "reaksi harga kedua emiten itu berlawanan. Sebaliknya, judul yang tidak menyebut emiten mana "
    "pun tidak menghasilkan contoh sama sekali. Aturan itu membuang sebagian korpus, tetapi yang "
    "dibuang adalah bagian yang tidak dapat diberi label aspek yang benar, sebab tidak ada emiten "
    "yang menjadi sasaran labelnya.",

    "Himpunan validasinya berlabel leksikon, bukan reaksi harga, dan konsekuensinya kami nyatakan "
    "terus terang. Angka validasi itu mengukur kesetiaan model pada guru yang lemah, bukan "
    "kemampuannya membaca nada. Ukuran yang berlaku ada di lembar anotasi manusia, dan lembar itu "
    "tidak pernah menyentuh pelatihan maupun pemilihan *checkpoint*. Pilihan ini punya dua sisi. "
    "Memilih *checkpoint* sentimen lewat label reaksi harga berarti memilih model yang paling "
    "pandai menebak arah harga, bukan yang paling pandai membaca nada, dan itu tugas yang "
    "berbeda. Memilihnya lewat anotasi manusia berarti membocorkan rujukan kebenaran ke dalam "
    "pelatihan, sehingga angka pada Tabel XIII berhenti sah. Pilihan yang tersisa ialah guru "
    "lemah, dan kami memakainya sambil menyebut batasnya.",

    "Tidak satu pun dari 800 label manusia dipakai melatih model maupun memilih *checkpoint*. "
    "Varian yang memakainya memberi angka sedikit lebih tinggi tetapi kami buang, karena bobot "
    "campurannya tidak dapat ditala secara sah. Himpunan pengembangan sudah ikut dilatih, dan "
    "himpunan uji tidak boleh dibuka untuk menala apa pun.",
    "Tiga upaya lain gagal dan layak disebut agar tidak dicoba ulang. Ensembel leksikon dengan "
    "model memberi bobot optimal 1,0 pada leksikon murni. Menyisipkan kode emiten ke dalam input "
    "model malah menurunkan angka. Penalaan ambang keyakinan leksikon antara 0,30 dan 0,45 pun "
    "tidak berpengaruh sama sekali.",
]

AN_AGREGAT = [
    "Akurasi per judul sebesar 37,24% hanya sedikit di atas tebakan acak, tetapi selisih "
    "*abnormal return* antara kelompok *bullish* dan *bearish* signifikan pada pengukuran tanpa "
    "seleksi (p = 0,0024). Kedua hasil itu tidak bertentangan.",
    "Imbal hasil harian didominasi faktor di luar berita, terutama kondisi pasar, aliran dana, "
    "dan likuiditas. Sentimen berita menyumbang komponen kecil yang tenggelam pada tingkat satu "
    "judul tetapi muncul ketika dirata-ratakan atas ribuan pengamatan. Hubungan yang nyata secara "
    "statistik karena itu tidak menjamin ketepatan prediksi pada kasus tunggal, dan di titik "
    "itulah banyak klaim berlebihan bermula.",
    "Kami sendiri pernah melaporkan besaran dampak yang terlalu besar, yakni *bullish* +2,92% "
    "berbanding *bearish* +1,16%. Angka itu diukur pada set uji yang dibentuk dengan menyeleksi "
    "artikel berdasarkan besar pergerakan harganya sendiri, yaitu *abnormal return* mutlak "
    "minimal 2%. Menghitung rata-rata pergerakan harga pada sampel yang dipilih justru karena "
    "harganya bergerak besar akan selalu menghasilkan angka besar. Diukur pada seluruh 18.194 "
    "pasangan tanpa seleksi, selisihnya menyusut menjadi sekitar 0,21 poin persentase. Bias "
    "seleksi pada variabel hasil mudah luput justru karena angkanya terlihat lebih meyakinkan.",
]

AN_ASIMETRI = [
    "Temuan pada bagian ini kami anggap paling berharga di seluruh laporan, sehingga kami uraikan "
    "tersendiri dan tidak sekadar dicatat sepintas.",
    "Kedua pengukuran yang dilaporkan pada Bagian IV-E berlawanan arah. Pada korpus 2022-2024 "
    "yang berdampak signifikan adalah kelompok negatif, sedangkan pada korpus yang diperluas "
    "sampai Agustus 2026 kelompok positif, dan jumlah peristiwanya naik dari 3.461 menjadi "
    "11.963.",
    "Di sini ada godaan untuk memilih salah satu periode lalu menuliskan penjelasan teoretis yang "
    "enak untuk arah tersebut, dan godaan itu kami tolak. Penjelasan seperti asimetri perhatian "
    "investor atau hambatan *short selling* di BEI tersedia untuk membenarkan arah mana pun, dan "
    "ketersediaan itulah persoalannya.",
    "Untuk pembalikan itu sendiri kami mengajukan tiga kemungkinan. *Rezim pasar berbeda.* "
    "Periode tambahan 2025-2026 merupakan pasar turun dengan IHSG -12,03%, sementara "
    "2022-2024 naik +6,22%, dan reaksi terhadap kabar baik maupun buruk sangat mungkin "
    "bergantung pada arah pasar keseluruhan. *Komposisi korpus berubah.* Periode 2025-2026 "
    "menyumbang sekitar 55% korpus unik karena mesin pencari mengembalikan hasil lebih lengkap "
    "untuk periode terkini. *Daya uji naik tajam.* Jumlah peristiwa lebih dari tiga kali lipat, "
    "sehingga efek kecil yang sebelumnya lolos dari deteksi kini tertangkap. Kemungkinan "
    "terakhir menjelaskan munculnya signifikansi, tetapi tidak menjelaskan pembalikan tandanya.",
    "Kesimpulan yang layak ditarik adalah bahwa arah asimetri reaksi berita di BEI tidak stabil "
    "terhadap periode sampel. Sebagian besar publikasi di bidang ini melaporkan satu periode, "
    "menemukan satu arah, lalu menyimpulkan mekanisme perilaku di baliknya. Laporan ini "
    "menunjukkan secara langsung mengapa praktik tersebut rapuh, dan dapat menunjukkannya karena "
    "pengukurannya diulang pada korpus yang diperluas.",
]

AN_STRATEGI = [
    "Empat penjelasan mungkin diajukan untuk kerugian *backtest*, dan dua di antaranya dapat "
    "dieliminasi dengan eksperimen.",
    "*Hipotesis A: biaya transaksi.* **Tereliminasi.** Kurva sensitivitas menunjukkan strategi "
    "tetap merugi 30,83% pada biaya nol. Biaya memperburuk hasil dari -30,83% ke "
    "-48,94%, tetapi bukan penyebabnya.",
    "*Hipotesis B: mekanika strategi.* **Sebagian besar penyebabnya.** Sepuluh tarikan sinyal "
    "acak pada pasangan emiten-tanggal yang sama menghasilkan *return* rata-rata "
    "-42,46%. Skema beli pada pembukaan lalu tahan sampai *target profit*, *stop loss*, atau "
    "batas waktu memang merugi pada *universe* LQ45 periode itu untuk sinyal apa pun.",
    "*Hipotesis C: arah sinyal salah.* **Didukung sebagian.** Hasil model -48,94% berada "
    "pada persentil 30 sebaran acak, lebih buruk daripada rata-rata acak meskipun masih di dalam "
    "satu simpangan baku.",
    "*Hipotesis D: kebocoran in-sample menutupi kegagalan sesungguhnya.* **Tereliminasi, dan ini "
    "yang paling penting.** *Backtest* 2022-2024 sebagian *in-sample* karena sinyalnya "
    "dihasilkan model yang sudah melihat periode yang sama, dan bias itu menguntungkan strategi "
    "sehingga kerugiannya bisa saja justru diremehkan. *Backtest out-of-sample* 2025-2026 "
    "menutup celah tersebut karena seluruhnya jatuh setelah data latih berakhir, dan hasilnya "
    "tetap merugi 34,82% serta tetap kalah dari IHSG yang turun 12,03%.",
    "Memisahkan keempat sebab itu hanya mungkin karena kontrol acak, kurva sensitivitas biaya, "
    "dan periode *out-of-sample* dijalankan bersama-sama. Satu *backtest* tunggal tidak dapat "
    "membedakan sinyal yang buruk dari mekanika strategi yang buruk.",
]

AN_IMPLIKASI = [
    "Hasil ini konsisten dengan hipotesis pasar efisien bentuk semi-kuat [14] pada saham LQ45, "
    "dalam arti informasi publik yang sudah diterbitkan media tidak dapat diubah menjadi "
    "keuntungan abnormal lewat strategi sederhana. Nilai sistem seperti SENDI karena itu terletak "
    "di tempat lain, yaitu memangkas waktu membaca ratusan artikel per hari, menyediakan "
    "penjelasan atas setiap penilaian, menyediakan sumber daya bahasa yang dapat dipakai ulang, "
    "dan memetakan batas siapa yang tidak dapat ditolong.",

    "**Yang sudah dapat dipakai sekarang.** Penilai leksikon SENDI mencapai akurasi 66,00% dan "
    "*macro-F1* 0,6378 terhadap anotasi tiga pemeriksa manusia, jauh di atas penebak konstan yang "
    "*macro-F1*-nya 0,2147, dan berjalan tanpa GPU maupun pelatihan. Untuk investor ritel dan "
    "jurnalis pasar modal, angka itu cukup untuk menyaring aliran berita harian menjadi daftar "
    "pendek yang layak dibaca manusia, dengan istilah leksikon pemicunya ikut ditampilkan sebagai "
    "alasan. Untuk peneliti NLP Bahasa Indonesia, keenam sumber daya di Tabel II adalah bahan "
    "yang selama ini harus dibangun ulang sendiri oleh setiap kelompok yang menyentuh teks "
    "keuangan Indonesia. *Gazetteer*-nya saja menaikkan F1 pengenalan kode saham dari 0,1227 "
    "menjadi 0,8827.",

    "Gambar 9 menunjukkan keluaran itu pada satu hari bursa, diambil apa adanya dari basis "
    "data proyek. Dari 348 judul unik yang terbit pada 13 Agustus 2026, penilai menautkan "
    "138 pasangan judul dan emiten untuk 50 emiten, lalu menyisakan 54 judul bersentimen "
    "berarah. Beban baca turun ke 15,5% aliran hari itu. Kolom pemicunya bahkan lebih berguna "
    "daripada rasio tersebut, sebab memuat entri seperti “jatuh -0,70”, “didepak -0,60”, dan “laba +0,55”. Pembaca "
    "melihat kata mana yang menggerakkan skor, lalu menolak penilaiannya kalau kata itu "
    "ternyata tidak relevan. Keluaran model yang hanya berupa satu angka tidak memberi "
    "kesempatan itu.",

    "**Bagi investor ritel.** Temuan utama laporan ini bersifat protektif. Strategi sentimen "
    "sederhana merugi pada 12 dari 12 kombinasi parameter, tetap merugi ketika biaya transaksinya "
    "dinolkan, tidak dapat dibedakan dari sinyal acak, dan tetap merugi pada periode yang belum "
    "pernah dilihat model. Klaim “AI trading” yang menjanjikan keuntungan dari analisis berita "
    "otomatis perlu dihadapkan pada bukti setingkat ini sebelum dipercaya. Temuan cakupan "
    "melengkapi gambaran itu. Seandainya pun sinyalnya bekerja, satu dari lima emiten BEI tidak "
    "memiliki jejak berita sehingga investor di saham lapis bawah tetap tidak terbantu.",

    "**Bagi peneliti berikutnya.** Tiga langkah berikut paling berdampak, berdasarkan apa yang "
    "terbukti mengikat di sini. Pengaitan artikel-emiten perlu diperbaiki sebelum model "
    "diperbesar, karena kapasitas tidak menolong ketika sebagian besar pasangan tidak menyebut "
    "emitennya. Pengukuran perlu diulang pada lebih dari satu periode, karena arah asimetri di "
    "sini berbalik. Kontrol acak juga perlu dijalankan, karena tanpa itu kerugian strategi "
    "tidak dapat dipisahkan dari kerugian mekanika strategi.",
]

# ----------------------------------------------------------------------------
# VI. KESIMPULAN
# ----------------------------------------------------------------------------

KESIMPULAN = [
    "Penelitian ini membangun SENDI, rangkaian sumber daya dan *pipeline* penambangan teks "
    "keuangan berbahasa Indonesia, lalu memakainya untuk menguji hubungan antara sentimen "
    "berita dan imbal hasil saham BEI. Ketiga tujuan yang dirumuskan pada Bagian I-B terjawab "
    "sebagai berikut.",

    "Enam sumber daya NLP keuangan berbahasa Indonesia dibangun dan dirilis terbuka, dan "
    "penelusuran atas Hugging Face Hub, Kaggle, Zenodo, GitHub, serta daftar tugas IndoNLU "
    "dan IndoLEM pada Agustus 2026 tidak menemukan padanan publiknya. Korpus 32.863 judul unik berlabel "
    "reaksi harga menjadi dasar evaluasi yang tidak sirkular dengan *holdout out-of-time*, yaitu "
    "model dilatih sampai Desember 2024 dan diuji pada Juli 2025 sampai Agustus 2026. Penilai "
    "leksikon yang lahir dari sumber daya itu mencapai akurasi 66,00% dan *macro-F1* 0,6378 "
    "terhadap anotasi manusia, dan dapat dipakai langsung tanpa pelatihan.",

    "Sentimen berita berhubungan signifikan dengan *abnormal return*, tetapi besarannya kecil dan "
    "jauh di bawah angka yang dihasilkan pengukuran yang terkena bias seleksi. Hubungan itu tidak "
    "dapat dieksploitasi strategi sederhana, dan kesimpulan tersebut bertahan pada data "
    "*out-of-sample*. Penyebabnya juga bukan biaya transaksi, sebab strategi merugi bahkan pada "
    "biaya nol, hasilnya berada di dalam sebaran sinyal acak, dan pada 2025-2026 ia tetap merugi "
    "sementara *benchmark*-nya juga turun.",

    "*Fine-tuning transformer* tidak terbukti mengungguli *baseline* TF-IDF terhadap label reaksi "
    "harga. Sampel 800 judul beranotasi menunjukkan sebabnya, yaitu mutu dan jenis label yang "
    "membatasi, sementara kapasitas model masih longgar. Uji McNemar berpasangan menempatkan "
    "IndoBERT tingkat dokumen tidak dapat dibedakan dari penebak konstan, sementara versi tingkat "
    "aspek dari model yang sama mengunggulinya secara signifikan setelah labelnya diperbaiki. "
    "Regresi logistik ikut naik sama besar dengan *transformer*-nya, sehingga yang terukur di "
    "sana adalah tingkat labelnya. Tidak ada bagian dari prosedur itu yang khusus untuk domain "
    "keuangan, meskipun kami belum mengujinya di luar tugas ini.",

    "Arah asimetri reaksi berita tidak stabil terhadap periode sampel, karena korpus 2022-2024 dan "
    "2022-2026 memberi arah berlawanan pada uji yang sama. Cakupan berita sangat timpang, "
    "sehingga 19,8% emiten BEI tidak pernah diberitakan dan tidak terjangkau alat berbasis "
    "berita mana pun. Pengujian pada korpus nyata juga membantah dua hipotesis awal kami "
    "sendiri. Tabrakan kode emiten jauh lebih kecil daripada dugaan, dan lapisan disambiguasi "
    "tidak memberi keunggulan terukur.",

    "Dalam konteks lomba, kontribusi yang kami anggap paling bernilai terletak pada cara "
    "mengukurnya, yakni *holdout out-of-time*, tiga *baseline*, kontrol acak, sensitivitas biaya, "
    "selang kepercayaan, uji berpasangan, dan koreksi uji ganda, dijalankan bersama pada satu "
    "pertanyaan dan dilaporkan seluruhnya, termasuk bagian yang memberatkan sistem kami sendiri.",
]

SARAN = [
    "Perluasan lembar anotasi melampaui 800 judul, sampai ukurannya cukup untuk melatih "
    "model pada label manusia, bukan sekadar mengujinya.",
    "Perbaikan pengaitan emiten-artikel dengan menyaring pasangan yang emitennya tidak "
    "disebut atau dengan mengambil badan artikel agar penyebutan dapat diverifikasi; ini "
    "pengungkit terbesar untuk mutu label.",
    "Pengukuran ulang pada beberapa rezim pasar yang dipisahkan, mengingat temuan pada Bagian "
    "V-G.",
    "Perluasan *universe* di luar LQ45, tempat likuiditas lebih rendah dan reaksi berita mungkin "
    "lebih lambat sehingga berpeluang lebih dapat dieksploitasi.",
    "Pemodelan *intraday*, karena reaksi terkuat terjadi pada H+0 dan H+1.",
    "Kalibrasi bobot propagasi *knowledge graph* terhadap data pergerakan harga.",
    "Pembungkusan *pipeline* menjadi layanan REST API, dasbor pemantauan, dan aturan "
    "peringatan otomatis, agar penilai leksikon yang sudah teruji pada Bagian IV-J dapat "
    "dipakai investor ritel tanpa menjalankan kode sendiri. Ketiganya berada di luar lingkup "
    "evaluasi laporan ini.",
]

KETERSEDIAAN = (
    "Seluruh kode, sumber daya bahasa, paket rilis dataset, berkas hasil evaluasi, dan skrip "
    "pembangkit setiap tabel serta gambar pada laporan ini tersedia di dalam repositori proyek. "
    "Setiap angka yang dikutip di naskah dapat ditelusuri ke berkas hasil yang dibangkitkan "
    "program, dan urutan perintah untuk mereproduksinya dari nol didokumentasikan di sana. "
    "Susunan tersebut mengikuti kriteria reproduksibilitas yang dirumuskan Gundersen dan "
    "Kjensmo [34], yakni ketersediaan metode, data, dan eksperimen sekaligus. Perangkat lunak "
    "dan sumber daya berlisensi MIT, kecuali master data emiten yang diturunkan dari Wikipedia "
    "Bahasa Indonesia dan mengikuti CC BY-SA 4.0."
)

REFERENSI = [
    "T. Loughran dan B. McDonald, “When is a liability not a liability? Textual analysis, "
    "dictionaries, and 10-Ks,” *The Journal of Finance*, vol. 66, no. 1, hlm. 35-65, 2011.",
    "P. Malo, A. Sinha, P. Korhonen, J. Wallenius, dan P. Takala, “Good debt or bad debt: "
    "Detecting semantic orientations in economic texts,” *Journal of the Association for "
    "Information Science and Technology*, vol. 65, no. 4, hlm. 782-796, 2014.",
    "D. Araci, “FinBERT: Financial sentiment analysis with pre-trained language models,” "
    "*arXiv preprint arXiv:1908.10063*, 2019.",
    "Y. Yang, M. C. S. Uy, dan A. Huang, “FinBERT: A pretrained language model for financial "
    "communications,” *arXiv preprint arXiv:2006.08097*, 2020.",
    "F. Koto, A. Rahimi, J. H. Lau, dan T. Baldwin, “IndoLEM and IndoBERT: A benchmark "
    "dataset and pre-trained language model for Indonesian NLP,” dalam *Proc. 28th Int. "
    "Conf. Computational Linguistics (COLING)*, 2020.",
    "B. Wilie dkk., “IndoNLU: Benchmark and resources for evaluating Indonesian natural "
    "language understanding,” dalam *Proc. 1st Conf. Asia-Pacific Chapter of the ACL "
    "(AACL-IJCNLP)*, 2020.",
    "A. F. Aji dkk., “One country, 700+ languages: NLP challenges for underrepresented "
    "languages and dialects in Indonesia,” dalam *Proc. 60th Annu. Meeting of the ACL*, 2022.",
    "J. Devlin, M.-W. Chang, K. Lee, dan K. Toutanova, “BERT: Pre-training of deep "
    "bidirectional transformers for language understanding,” dalam *Proc. NAACL-HLT*, 2019.",
    "J. Bollen, H. Mao, dan X. Zeng, “Twitter mood predicts the stock market,” *Journal "
    "of Computational Science*, vol. 2, no. 1, hlm. 1-8, 2011.",
    "X. Ding, Y. Zhang, T. Liu, dan J. Duan, “Deep learning for event-driven stock "
    "prediction,” dalam *Proc. 24th Int. Joint Conf. Artificial Intelligence (IJCAI)*, 2015.",
    "Z. Hu, W. Liu, J. Bian, X. Liu, dan T.-Y. Liu, “Listening to chaotic whispers: A deep "
    "learning framework for news-oriented stock trend prediction,” dalam *Proc. 11th ACM Int. "
    "Conf. Web Search and Data Mining (WSDM)*, 2018.",
    "Y. Xu dan S. B. Cohen, “Stock movement prediction from tweets and historical "
    "prices,” dalam *Proc. 56th Annu. Meeting of the ACL*, 2018.",
    "R. Sawhney, S. Agarwal, A. Wadhwa, dan R. R. Shah, “Deep attentive learning for stock "
    "movement prediction from social media text and company correlations,” dalam *Proc. "
    "EMNLP*, 2020.",
    "E. F. Fama, “Efficient capital markets: A review of theory and empirical work,” "
    "*The Journal of Finance*, vol. 25, no. 2, hlm. 383-417, 1970.",
    "E. F. Fama, L. Fisher, M. C. Jensen, dan R. Roll, “The adjustment of stock prices to new "
    "information,” *International Economic Review*, vol. 10, no. 1, hlm. 1-21, 1969.",
    "S. J. Brown dan J. B. Warner, “Using daily stock returns: The case of event "
    "studies,” *Journal of Financial Economics*, vol. 14, no. 1, hlm. 3-31, 1985.",
    "E. Boehmer, J. Musumeci, dan A. B. Poulsen, “Event-study methodology under conditions of "
    "event-induced variance,” *Journal of Financial Economics*, vol. 30, no. 2, hlm. "
    "253-272, 1991.",
    "A. C. MacKinlay, “Event studies in economics and finance,” *Journal of Economic "
    "Literature*, vol. 35, no. 1, hlm. 13-39, 1997.",
    "P. C. Tetlock, “Giving content to investor sentiment: The role of media in the stock "
    "market,” *The Journal of Finance*, vol. 62, no. 3, hlm. 1139-1168, 2007.",
    "P. C. Tetlock, M. Saar-Tsechansky, dan S. Macskassy, “More than words: Quantifying "
    "language to measure firms’ fundamentals,” *The Journal of Finance*, vol. 63, no. 3, "
    "hlm. 1437-1467, 2008.",
    "M. Mintz, S. Bills, R. Snow, dan D. Jurafsky, “Distant supervision for relation "
    "extraction without labeled data,” dalam *Proc. Joint Conf. 47th Annu. Meeting of the ACL "
    "and 4th IJCNLP*, 2009.",
    "A. Ratner, S. H. Bach, H. Ehrenberg, J. Fries, S. Wu, dan C. Ré, “Snorkel: Rapid "
    "training data creation with weak supervision,” *Proc. VLDB Endowment*, vol. 11, no. 3, "
    "hlm. 269-282, 2017.",
    "J. Zhang, C.-Y. Hsieh, Y. Yu, C. Zhang, dan A. Ratner, “A survey on programmatic weak "
    "supervision,” *arXiv preprint arXiv:2202.05433*, 2022.",
    "K. Krippendorff, *Content Analysis: An Introduction to Its Methodology*. Thousand Oaks, CA: "
    "Sage Publications, 2004.",
    "R. Artstein dan M. Poesio, “Inter-coder agreement for computational linguistics,” "
    "*Computational Linguistics*, vol. 34, no. 4, hlm. 555-596, 2008.",
    "A. Lopez-Lira dan Y. Tang, “Can ChatGPT forecast stock price movements? Return "
    "predictability and large language models,” *arXiv preprint arXiv:2304.07619*, 2023.",
    "S. Wu dkk., “BloombergGPT: A large language model for finance,” *arXiv preprint "
    "arXiv:2303.17564*, 2023.",
    "D. H. Bailey, J. M. Borwein, M. Lopez de Prado, dan Q. J. Zhu, “Pseudo-mathematics and "
    "financial charlatanism: The effects of backtest overfitting on out-of-sample "
    "performance,” *Notices of the AMS*, vol. 61, no. 5, hlm. 458-471, 2014.",
    "C. R. Harvey, Y. Liu, dan H. Zhu, “… and the cross-section of expected "
    "returns,” *The Review of Financial Studies*, vol. 29, no. 1, hlm. 5-68, 2016.",
    "M. Lopez de Prado, *Advances in Financial Machine Learning*. Hoboken, NJ: John Wiley & Sons, "
    "2018.",
    "S. Holm, “A simple sequentially rejective multiple test procedure,” *Scandinavian "
    "Journal of Statistics*, vol. 6, no. 2, hlm. 65-70, 1979.",
    "B. Efron dan R. J. Tibshirani, *An Introduction to the Bootstrap*. New York, NY: Chapman & "
    "Hall, 1993.",
    "R. Dror, G. Baumer, S. Shlomov, dan R. Reichart, “The hitchhiker’s guide to testing "
    "statistical significance in natural language processing,” dalam *Proc. 56th Annu. "
    "Meeting of the ACL*, 2018.",
    "O. E. Gundersen dan S. Kjensmo, “State of the art: Reproducibility in artificial "
    "intelligence,” dalam *Proc. 32nd AAAI Conf. Artificial Intelligence*, 2018.",
    "M. S. Charikar, “Similarity estimation techniques from rounding algorithms,” dalam "
    "*Proc. 34th Annu. ACM Symp. Theory of Computing (STOC)*, 2002, hlm. 380-388.",
    "Q. McNemar, “Note on the sampling error of the difference between correlated proportions "
    "or percentages,” *Psychometrika*, vol. 12, no. 2, hlm. 153-157, 1947.",
]
