Reformulasi Fisis dan Rekonsiliasi Lintasan untuk Peramalan
Kelembapan Udara Multivariat 15 Hari ke Depan
Timotius Christopher Patrick Sihombing Raphael Angelo Adikara Purnama
NIM 164241005 NIM 164241055
Program Studi Teknologi Sains Data Program Studi Teknologi Sains Data
Fakultas Teknologi Maju dan Multidisiplin Fakultas Teknologi Maju dan Multidisiplin
Universitas Airlangga, Surabaya, Indonesia Universitas Airlangga, Surabaya, Indonesia
timotius.christopher.patrick-2024@ftmm.unair.ac.id raphael.angelo.adikara-2024@ftmm.unair.ac.id
Yang membentuk seluruh rancangan solusi adalah bentuk
Abstrak—Peramalan kelembapan udara bernilai operasional pemisahan latih dan uji. Jendela uji adalah blok kontigu 15,3 hari
langsung bagi pertanian presisi. Kami meramalkan 734 titik tepat setelah jendela latih berakhir, bukan cuplikan acak. Tidak
setengah-jaman selama 15,3 hari ke depan dari 2.933 baris latih ada satu pun label di dalamnya, sehingga tidak ada suku
dan 24 kanal sensor eksogen yang juga tersedia sepanjang jendela autoregresif yang boleh dipakai; namun seluruh 24 kanal
uji, 11 di antaranya bertahan sampai matriks fitur akhir. Yang eksogen tersedia pada setiap baris uji. Ini bukan peramalan buta
menentukan hasilnya adalah penulisan ulang persoalannya, dan bukan pula interpolasi: ini rekonstruksi kelembapan dari
bukan pemilihan model: karena kelembapan relatif adalah rasio jejak sensor lengkap pada rezim iklim yang belum pernah dilihat
tekanan uap aktual terhadap tekanan uap jenuh sedangkan suhu model. Perbedaan itu menentukan fitur apa yang sah, protokol
diketahui persis pada waktu uji, seluruh ketidaktahuan berpindah
validasi apa yang tidak berbohong, dan komponen mana yang
ke tekanan uap. Kurva oracle mengubahnya jadi pengukuran:
akhirnya membayar.
tekanan uap harian yang sempurna pun hanya memberi RMSE
8,37, sedangkan stack kami setara mengetahuinya pada resolusi Tulisan ini memberi empat kontribusi yang masing-masing
6,1 jam. Di atas enam anggota yang dipadukan lewat kuadrat- dibayar dengan angka, bukan dengan klaim:
terkecil non-negatif per pita waktu-hari, satu langkah
1) Reformulasi fisis yang terukur. Kami menulis ulang
memperlakukan jendela uji sebagai deret waktu: rekonsiliasi
lintasan atas 734 baris lewat satu solve jarang, bernilai −0,160 persoalan dari meramalkan RH menjadi menduga tekanan
RMSE atau tujuh kali perbaikan blending terbaik. Temuan tak uap air, lalu membangun kurva oracle yang menyatakan
terduga: bias level maju −2,89 %RH pada satu anggota yang di berapa RMSE yang dihasilkan kalau tekanan uap diketahui
dalam sampelnya tak bias, tak terlihat oleh komponen pipeline sempurna pada resolusi waktu tertentu. Kurva itu memberi
mana pun. Seluruh pemilihan model dilakukan pada validasi ukuran objektif untuk seluruh sisa pekerjaan dan langsung
silang titik-asal bergulir; papan peringkat tidak pernah dipakai mematikan satu keluarga arsitektur yang tampak paling
memilih model, dan tiga koreksi pasca-model yang lolos validasi wajar.
internal justru ditolak olehnya. Pada sembilan lipatan titik-asal
2) Rekonsiliasi lintasan sebagai satu-satunya komponen
bergulir yang sama, stack ini 15,8 % lebih baik daripada satu
deret waktu. Kami menunjukkan bahwa seluruh pipeline
LightGBM tunggal dan unggul di kesembilannya. RMSE publik
berbasis baris meninggalkan informasi di atas meja karena
akhir 2,82744, dari garis dasar naif 18,0.
galat modelnya berautokorelasi 0,93, dan bahwa mengikat
734 baris uji lewat satu solve kuadrat-terkecil jarang
Kata kunci—peramalan kelembapan udara, gradient boosting,
memanen informasi itu dengan −0,160 RMSE.
rekonsiliasi ramalan, tekanan uap air, kalibrasi model, validasi
silang deret waktu 3) Cacat kalibrasi yang tidak terlihat instrumen mana pun.
Kami melaporkan bias level maju −2,89 %RH pada satu
I. PENDAHULUAN anggota blend yang bias di dalam sampelnya −0,006,
Kelembapan udara adalah salah satu peubah lingkungan menjelaskan mengapa tidak satu pun komponen pipeline
yang paling banyak dipakai dan paling sedikit diramalkan berbentuk cukup untuk melihatnya, dan memperlihatkan
dengan baik pada skala petak. Bersama suhu ia menentukan bahwa koreksi satu-skalar atasnya bernilai −0,022 RMSE.
defisit tekanan uap, besaran yang mengendalikan laju transpirasi 4) Batas kegunaan validasi silang, diukur dan bukan
tanaman sekaligus membuka atau menutup jendela infeksi bagi didalilkan. Validasi silang memeringkat perubahan pada
patogen jamur. Rumah kaca dan lahan hortikultura modern model dengan andal, tetapi untuk koreksi yang diterapkan
memakainya untuk menjadwalkan ventilasi, pengabutan, dan setelah model ia perlu dan tidak cukup: tiga koreksi lolos
irigasi beberapa jam sampai beberapa hari di muka. Sensor validasi internal, satu di antaranya menang di 13 dari 13
kelembapan sendiri, di sisi lain, adalah komponen yang paling lipatan, lalu tetap merugikan pada jendela uji. Kami
sering gagal dan paling cepat melenceng kalibrasinya pada satu melaporkan mekanisme kegagalannya satu per satu dan
stasiun iklim mikro. Kemampuan merekonstruksi kelembapan menarik aturan yang dapat dipakai ulang darinya.
dari kanal-kanal lain yang masih hidup karena itu adalah bentuk Arah-arah yang gagal, beserta alasan terukurnya, ada di
redundansi yang murah, bukan latihan akademis. Bagian VI-E.
Tema cabang lomba ini, Transforming Present Multivariate
II. AKUISISI DAN EKSPLORASI DATA
Insights to Shape the Future of Predictive Analytics, menyebut
dua hal yang persis menjadi bentuk persoalan kami: masukan A. Anatomi Dataset
yang multivariat dan keluaran yang prediktif. Kami memakai 24
Data berasal dari satu stasiun pemantauan lingkungan
kanal sensor eksogen yang terekam serempak dengan target
pertanian: sebuah logger iklim mikro (CO₂, tekanan barometrik,
(iklim mikro cepat, tiga jalur probe tanah, tiga penghitung
suhu udara, kelembapan udara) yang dipasangkan dengan tiga
volume irigasi, dan tujuh indeks agronomi harian) untuk
jalur probe tanah (konduktivitas listrik, kelembapan, suhu), tiga
meramalkan 734 titik setengah-jaman ke depan.
penghitung volume air irigasi, dan tujuh indeks agronomi harian

yang diturunkan dari suhu. Tabel A.VII di lampiran merangkum Tiga hal langsung terbaca dari anatomi itu. Nilai hilang
anatominya. berkisar 9,0–10,8 % pada belahan latih dan 8,6–17,6 % pada
belahan uji, tersebar dan bukan berbentuk blok mati alat,
Kisi waktu latih tidak sempurna: selangnya 30 menit di
sehingga dapat ditambal tanpa mengarang rezim. Kolom
2.931 dari 2.932 transisi, dengan satu lompatan tunggal selama
env_battery praktis kosong (98 % hilang) dan seluruh nilai
7 jam, sementara kisi uji sempurna. Akibatnya setiap operator
yang ada bernilai 100, jadi ia dibuang. Dan blok tanah serta
berbasis geseran di seluruh pipeline dibangun di atas kisi
irigasi runtuh di jendela uji: water_volume_* benar-benar
setengah-jaman yang sudah dilengkapi, bukan di atas nomor
konstan di sana.
baris; kalau tidak, geseran empat langkah akan berarti “empat
baris”, bukan “dua jam”, tepat di sekitar lompatan itu. Atas B. Bentuk Pemisahan Latih–Uji
alasan yang sama, penambalan lubang memakai interpolasi
terhadap indeks waktu.
Gambar 1. Tugas dan cacatnya dalam satu tarikan napas. (a) Deret target sepanjang kalender; blok terarsir adalah 734 baris uji yang seluruh labelnya ditahan. (b)
Suhu udara mentah pada sumbu waktu yang sama; 16 titik merah adalah nilai di luar rentang 5–45 °C, yang secara fisis mustahil pada stasiun ini dan karena itu
merupakan korupsi, bukan cuaca.
Gambar 1(a) memperlihatkan target sepanjang kalender tetangganya pada t−2, t−1, t+1, dan t+2, lalu memprediksi titik
beserta blok yang harus diramalkan. Amplitudo diurnalnya itu sendiri. Sinyal mulus memberi residu kecil; derau putih
41,13 %RH terhadap simpangan baku keseluruhan 18,00 %RH, memberi residu besar berekor pendek; lonjakan yang
jadi hampir seluruh ragam target adalah ayunan harian. Gambar disuntikkan memberi residu besar berekor sangat panjang.
1(b) memperlihatkan sesuatu yang lebih mengganggu: suhu Perbandingan simpangan baku biasa terhadap simpangan baku
udara mentah, prediktor tunggal terkuat kami, memuat 16 nilai robus, 1,4826 kali median deviasi absolut, memisahkan dua
yang secara fisis mustahil, dari −6,33 °C sampai +60,64 °C, di kemungkinan terakhir.
dalam deret yang median hariannya 27 °C. Karena ∂RH/∂T
Gambar 2 dan Tabel I memuat hasilnya, dan pemisahannya
sekitar −3,6 %RH per °C pada RH 60 %, satu lonjakan suhu 20
tegas. Target memberi rasio 1,20, ekor yang hampir normal,
°C yang lolos menghasilkan prediksi yang meleset puluhan
tanpa tanda lonjakan suntikan. Suhu udara memberi 5,75 dan
persen pada baris tersebut. Bagian IV menanganinya.
tekanan barometrik 6,86, keduanya berekor sangat berat.
C. Uji Derau Target dan Korupsi Prediktor Targetnya bersih; prediktornyalah yang dikorupsi. Dua
konsekuensi mengalir dari sini dan keduanya membentuk sisa
Sebelum satu model pun dipasang, ada satu pertanyaan yang
pekerjaan. Pertama, tidak ada lantai derau label, sehingga RMSE
harus dijawab lebih dulu: apakah targetnya sendiri berderau?
rendah memang dapat dicapai secara prinsip dan tidak ada
Kalau air_humidity mengandung derau putih sebesar σ,
alasan berhenti pada angka tertentu. Kedua, nilai sebenarnya
maka RMSE tidak akan pernah turun di bawah σ dan seluruh
dari pra-pemrosesan di sini adalah merekonstruksi sinyal
usaha pemodelan punya lantai yang tidak dapat ditembus.
masukan, bukan membersihkan target. Itulah satu-satunya
Ujinya adalah residu interpolasi kuadratik tinggalkan-satu: alasan langkah despiking di Bagian IV ada.
untuk setiap titik kami memasang parabola pada empat
Gambar 2. Sebaran residu interpolasi kuadratik tinggalkan-satu, dinormalkan terhadap simpangan baku robusnya, sumbu tegak berskala log. Garis putus-putus
menandai ±6 sd robus. Target berekor hampir normal; kedua prediktor memuat massa yang jelas terpisah di luar ±10 sd robus, tanda tangan lonjakan yang
disuntikkan, bukan derau alami.

Korupsinya juga selektif per kolom, bukan derau seragam  sebenarnya,  konstruksi  ini  tidak  dapat  dipakai  untuk
yang  ditebar  ke  seluruh  berkas.  soil_temp_line1,  deret  memprediksi apa pun; ia dipakai sebagai penggaris.
paling mulus di dataset, memberi rasio 1,04 dan tidak dilonjaki
Gambar 3 memuat kurvanya. Bacaannya keras. Bahkan
sama sekali.
dengan tekanan uap harian yang sempurna, RMSE-nya 8,37,
TABEL I.  AUDIT KORUPSI LEWAT RESIDU TINGGALKAN-SATU  tiga kali lebih buruk daripada solusi yang akhirnya kami bangun.
Kolom  sd  sd robus  Rasio  Tafsir  Setiap  arsitektur  yang  memodelkan  level  harian  lalu
menempelkan bentuk diurnal generik dibatasi oleh angka itu,
| air_humidity |     | 1,71  | 1,42  1,20  | ekor hampir normal  |     |              |           |           |                   |     |       |
| ------------ | --- | ----- | ----------- | ------------------- | --- | ------------ | --------- | --------- | ----------------- | --- | ----- |
|              |     |       |             |                     |     | berapa  pun  | bagusnya  | komponen  | pembelajarannya.  |     | Kami  |
|              |     | 2,72  | 0,47  5,75  | lonjakan suntikan   |     |              |           |           |                   |     |       |
air_temperature mengetahui ini sebelum melatih model pertama.

| pressure |     | 1,58  | 0,23  6,86  | lonjakan suntikan  |     |     |     |     |     |     |     |
| -------- | --- | ----- | ----------- | ------------------ | --- | --- | --- | --- | --- | --- | --- |
co2   23,33  10,63  2,20  sebagian terlonjaki  Sebaliknya,  model  akhir  kami  dengan  RMSE  2,827
  0,07  0,07  1,04  bersih  mendarat di antara oracle 4,5 jam dan 6,5 jam, yaitu setara
soil_temp_line1
mengetahui tekanan uap yang sebenarnya pada resolusi sekitar

6,1 jam. Ruang yang tersisa karena itu bersifat sub-harian: untuk
III.  METODE ANALISIS  turun ke RMSE 2,3 kami perlu mengetahui e sekitar 1,5 jam
lebih halus lagi. Itulah alasan struktural mengapa rekonsiliasi
| Bagian  | ini  memuat  | kerangka  | analisis  | yang  mendahului  |     |     |     |     |     |     |     |
| ------- | ------------ | --------- | --------- | ----------------- | --- | --- | --- | --- | --- | --- | --- |
lintasan di Bagian V-D ada, dan mengapa ia bernilai jauh lebih
| seluruh  | pemodelan:  | identitas  | termodinamika  | yang  | menulis  |     |     |     |     |     |     |
| -------- | ----------- | ---------- | -------------- | ----- | -------- | --- | --- | --- | --- | --- | --- |
besar daripada perubahan lain mana pun.
ulang persoalan, batas oracle yang mengukur seberapa jauh
penulisan ulang itu bisa membawa kami, dua penduga fisis
bebas-parameter yang lahir darinya, audit pergeseran distribusi,
dan protokol validasi.
A.  Kerangka Fisis: yang Diramalkan Sebenarnya Bukan RH
Kelembapan relatif bukan besaran keadaan yang berdiri
sendiri. Ia adalah rasio antara tekanan uap air aktual dan tekanan
uap jenuh pada suhu yang sama,
|     | RH(t) = 100 · e(t) / e(T(t))  |     |     |     | (1)  |     |     |     |     |     |     |
| --- | ----------------------------- | --- | --- | --- | ---- | --- | --- | --- | --- | --- | --- |
s

dengan e diberikan oleh parameterisasi Magnus–Bolton [1]
s
|     | e(T) = 6,112 · exp( 17,67 T / (T + 243,5) )  |     |     |     | (2)  |     |     |     |     |     |     |
| --- | -------------------------------------------- | --- | --- | --- | ---- | --- | --- | --- | --- | --- | --- |
|     | s                                            |     |     |     |      |     |     |     |     |     |     |

Gambar 3.  Kurva oracle. Setiap titik menyatakan RMSE yang dicapai kalau
yang menghasilkan hPa untuk suhu dalam derajat Celsius.  tekanan  uap  diketahui  sempurna  pada  resolusi  waktu  tersebut.  Bintang
Bentuk (1) tampak sepele, tetapi implikasinya tidak. Penyebut  menandai tempat model kami mendarat.
e(T(t)) diketahui persis pada setiap baris uji, karena suhu udara
| s   |     |     |     |     |     | C.  Proksi Titik Embun Bebas-Parameter  |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --------------------------------------- | --- | --- | --- | --- | --- |
termasuk kanal eksogen yang disediakan sepanjang jendela uji.
Seluruh ketidaktahuan karena itu berpindah ke pembilang.  Identitas  (1)  juga  melahirkan  satu  penduga  yang  tidak
memuat satu pun parameter terpasang. Udara lembap yang
Perpindahan itu mengubah pertanyaannya secara mendasar.  mendingin  semalam  akan  turun  sampai  mencapai  titik
“Berapa RH besok pukul 03.00” adalah pertanyaan tentang
embunnya lalu berhenti di sana, karena kalor laten kondensasi
besaran yang bergerak 41 %RH dalam sehari; “berapa tekanan
|     |     |     |     |     |     | menahan  | pendinginan  | lebih  | lanjut.  Suhu  | minimum  | harian  |
| --- | --- | --- | --- | --- | --- | -------- | ------------ | ------ | -------------- | -------- | ------- |
uap massa udara besok” adalah pertanyaan tentang besaran yang
|     |     |     |     |     |     | karena  itu  | adalah  | pendekatan  | titik  | embun  | [2],  dan  |
| --- | --- | --- | --- | --- | --- | ------------ | ------- | ----------- | ------ | ------ | ---------- |
hanya berubah oleh adveksi, kondensasi, evapotranspirasi, dan  mensubstitusikannya ke (1) memberi
| ventilasi. RH dan e(T) berayun tajam dan berlawanan fase,  |     | s   |     |     |     |     |     |     |     |     |     |
| ---------------------------------------------------------- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
sedangkan e bergerak jauh lebih tenang: simpangan bakunya di  RH(t) ≈ 100 · e(T ) / e(T(t))  (4)
|     |     |     |     |     |     |     |     | s   | min s |     |     |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | ----- | --- | --- |
dalam satu hari 2,56 hPa dibanding 2,91 hPa antar-hari.

Angka kedua itu penting dan sering diabaikan. Ragam e di
Gambar A.2 memperlihatkan perilakunya. Satu rumus tanpa
dalam satu hari hampir sebesar ragamnya antar-hari. Pendekatan  parameter apa pun, dibangun hanya dari suhu, sudah berkorelasi
yang  tampak  paling  wajar,  yaitu  menebak  satu  tingkat  0,908 dengan target dan mencapai RMSE mentah 9,1 %RH.
kelembapan  per  hari  lalu  membaginya  dengan  e (T)  untuk  Angka itu menetapkan garis dasar fisis yang harus dikalahkan
s
memperoleh bentuk diurnalnya, karena itu kehilangan hampir
|     |     |     |     |     |     | setiap  model  | pembelajaran  |     | mesin  di  sini,  | dan  | menjelaskan  |
| --- | --- | --- | --- | --- | --- | -------------- | ------------- | --- | ----------------- | ---- | ------------ |
separuh sinyal sejak awal. Sub-bagian berikut mengukur berapa
mengapa blok fitur terpenting pada Bagian IV-B seluruhnya
persisnya harga pendekatan itu.  berupa  statistik  urutan  atas  suhu,  bukan  statistik  atas
kelembapan. Versi jendela-bergulir 18 jam, 48 jam, dan 96 jam
B.  Batas Oracle: Resolusi yang Benar-Benar Berguna
memberi model tiga pandangan terhadap massa udara yang
| Kami  | membangun  | keluarga  | oracle:  | penduga  | yang  |     |     |     |     |     |     |
| ----- | ---------- | --------- | -------- | -------- | ----- | --- | --- | --- | --- | --- | --- |
sama pada tiga skala waktu.
mengetahui e yang sebenarnya, tetapi hanya pada resolusi waktu
tertentu. Untuk jendela w titik, oracle-nya adalah  D.  Rekayasa Balik Blok Agronomi
Tujuh kolom “harian” tampak seperti pembacaan per-baris
|     | RHoracle(t) = 100 · ⟨e⟩ |     | (T(t))  |     | (3)  |     |     |     |     |     |     |
| --- | ----------------------- | --- | ------- | --- | ---- | --- | --- | --- | --- | --- | --- |
w (t) / e s karena  nilainya  berubah  di  setiap  baris.  Ternyata  tidak.
|     |     |     |     |     |     | Menyapu  | batas  | hari  dari  | 00.00  | sampai  | 23.00  dan  |
| --- | --- | --- | --- | --- | --- | -------- | ------ | ----------- | ------ | ------- | ----------- |
meminimumkan ragam di dalam hari menempatkan batasnya
| dengan  | tanda kurung  | sudut menyatakan  |     | rerata bergerak  |     |     |     |     |     |     |     |
| ------- | ------------- | ----------------- | --- | ---------------- | --- | --- | --- | --- | --- | --- | --- |
terpusat sepanjang w titik. Karena e dihitung dari target yang  pada pukul 22.00: blok itu konstan sepanjang hari agronomi

22.00-ke-22.00, dengan derau 0,055–0,111 °C ditambahkan di dengan hati-hati, karena model linear mengekstrapolasi tanpa
atasnya. Dua di antaranya adalah salinan afin persis dari dua batas ke luar dukungan; salah satu di antaranya akhirnya
yang lain; daily_max − daily_max_above_Tbase = 9,999 dibuang dari blend justru karena alasan ini, dan pembuangannya
± 0,157 dan daily_mean_temperature − memang membayar di papan peringkat (Bagian V-B).
standard_day_degree = 10,002 ± 0,109.
F. Desain Validasi
Konsekuensi pertamanya menyangkut kesahihan. Blok Bagian ini paling menentukan hasil akhir dan paling mudah
harian dilaporkan pada setiap baris hari itu, sehingga pada pukul dikerjakan dengan salah.
02.00 berkas sudah menyatakan berapa maksimum hari itu
nanti. Ini informasi yang sah karena panitia menyediakannya di Validasi silang acak akan berbohong di sini. Baris pada
test.csv; artinya indeks agronomi adalah ringkasan seluruh dataset ini punya autokorelasi 0,979 pada lag satu. Lipatan acak
hari, bukan fitur masa lalu, dan harus diperlakukan sebagai menempatkan tetangga langsung sebuah baris di sisi latih,
ringkasan. sehingga skornya mengukur interpolasi, bukan peramalan.
Ukuran sampel efektifnya sekitar 62 hari, bukan 2.933 baris, dan
Konsekuensi keduanya jauh lebih berguna. Identitas itu membatasi apa saja yang bisa dipelajari pada skala harian.
daily_mean_temperature = (T + T )/2 berlaku persis,
maks min
sehingga rerata harian T̄ dan maksimum harian T memberi Protokol yang kami pakai adalah titik-asal bergulir [4].
maks
Setiap lipatan dilatih pada segala sesuatu sebelum satu titik
T = 2 · T̄ − T (5) potong lalu divalidasi pada 15 hari berikutnya, bentuk yang
min hari maks
persis sama dengan tugas sebenarnya. Sembilan lipatan, langkah
dua hari, minimum 30 hari data latih.
Dan indeks Ontario Crop Heat Unit [3], yang didefinisikan
sebagai rerata dua suku Y = 3,33(T − 10) − 0,084(T − Dua peran harus dipisahkan. Prediksi luar-lipatan dipakai
maks maks maks
10)² dan Y = 1,8(T − 4,4), dapat dipecahkan secara aljabar untuk memasang bobot blend dan sekaligus untuk mengukur
min min
untuk memberi jalur kedua yang sepenuhnya bebas dari yang galat. Keduanya harus memakai baris yang sama tetapi tidak
pertama, boleh saling mencemari, karena parameter yang dipasang pada
baris yang sama dengan yang dinilai akan tampak lebih baik
T = (2 · CHU − Y ) / 1,8 + 4,4 (6) daripada yang sebenarnya. Karena itu setiap parameter meta di
min maks
pipeline ini (bobot NNLS, koreksi bias diurnal, offset de-bias
level) dipasang hanya pada baris luar-lipatan, lalu diterapkan
Kedua rekonstruksi itu berkorelasi 0,99986 dan sepakat
tanpa perubahan pada jendela uji.
sampai simpangan baku 0,047 °C sepanjang 76 hari. Namun
keduanya berbeda dari minimum yang teramati sensor dengan Protokol inilah yang memilih model, bukan papan
simpangan baku 0,43 °C setelah sensor dibersihkan, dan hanya peringkat. Setiap anggota, blok fitur, hiperparameter, dan bobot
berkorelasi 0,45 terhadap minimum sensor mentah. Selisih itu blend dipilih pada sembilan lipatan di atas. Skor papan peringkat
bukan galat rekonstruksi: blok agronomi dihitung sebelum baru dibaca setelah sebuah konfigurasi dikapalkan, dan hanya
korupsi disuntikkan, sehingga ia adalah versi bersih dari besaran menyentuh satu keluarga keputusan: koreksi yang diterapkan
yang sama. setelah model, seperti kalibrasi level dan dispersi. Bagian VI-E
mencatat tiga koreksi yang lolos validasi internal lalu tetap
Jadi dataset ini memuat dua pengukuran atas suhu minimum
ditolak di sana; anggota l2 mencatat kebalikannya,
harian, satu berderau dari sensor dan satu bersih dari indeks
dipertahankan meskipun papan peringkat sedikit lebih buruk
agronomi. Karena minimum harian adalah proksi titik embun
dengannya, karena bukti internalnya positif.
kami lewat (4), nilai 0,43 °C itu diterjemahkan langsung menjadi
sekitar 1,5 %RH derau pada prediktor fisis terkuat yang kami IV. PRA-PEMROSESAN
punya. Blok agronomi masuk ke matriks fitur justru karena
alasan ini, bukan karena ia kebetulan tersedia. A. Despiking Hampel
Dua langkah pra-pemrosesan, dan keduanya dibenarkan oleh
E. Pergeseran Distribusi Latih ke Uji
pengukuran di Bagian II-C, bukan oleh kebiasaan.
Validasi silang mengukur galat di dalam rezim latih.
Despiking Hampel. Penapis Hampel terpusat [5] menandai
Kompetisi ini menilai pada blok 15 hari sesudahnya, di musim
titik yang menyimpang lebih dari k kali skala robus lokal dari
yang lebih dingin dan dengan irigasi yang berhenti. Kami
median bergeraknya,
mengukur pergeseran itu sebelum satu model pun dipasang,
karena besar-kecilnya menentukan seberapa jauh validasi silang
tolak x(t) jika | x(t) − med (t) | > k · s(t) (7)
boleh dipercaya. w
Jendela uji jelas berada di luar rezim. Suhu rata-rata turun
dengan med_w median bergerak terpusat w titik dan s(t)
dari 27,51 °C ke 24,64 °C, dan 48,0 % baris uji jatuh di kuartil
skala robus. Dua pilihan di dalamnya penting, dan Lampiran C
terdingin data latih dibanding 25 % secara definisi di data latih.
menguraikan keduanya: skalanya diambil dari IQR bergulir 289
Pendinginannya tidak simetris: rerata minimum harian turun
titik agar penggal yang kebetulan tenang tidak menandai setiap
3,17 °C sementara rerata maksimum harian hanya turun 1,37 °C,
riak sebagai pencilan, dan ambangnya sengaja longgar pada k =
sehingga ayunan diurnalnya melebar. Audit dukungan per
6 karena yang dikejar adalah ekskursi yang secara fisis mustahil,
kolom, yang dimuat Gambar A.4 di lampiran, mencatat 13
bukan transisi cepat yang asli.
kolom kehilangan lebih dari sepertiga sebaran latihnya.
Gambar A.3 memperlihatkan hasilnya pada penggal dengan
Dua keputusan mengalir dari sini. Blok tanah dan irigasi
penolakan terpadat, dan angkanya ada di Tabel A.I di lampiran.
dibuang seluruhnya dari matriks fitur: statistik bergulirnya di
Penapis menyentuh 0,49 % nilai, membuang seluruh 16 nilai
jendela uji hampir tidak punya dukungan latih, sehingga pohon
yang di luar rentang 5–45 °C, dan menghapus 52 dari 57
akan mengekstrapolasi ke daun yang dipelajari pada rezim
ekskursi residu di atas 2,5 °C tanpa menyisakan satu pun di
irigasi yang sudah tidak ada. Anggota linear diperlakukan

jendela uji. Simpangan baku residu tinggalkan-satu turun dari  Ada  satu pilihan  desain yang harus  dinyatakan terbuka
2,715 ke 0,515, sementara simpangan baku robus-nya nyaris  karena sekilas ia terlihat seperti kebocoran. Jendela bergulir di
tidak bergerak, 0,472 ke 0,408. Itu tanda tangan dari membuang  pipeline  ini  terpusat,  bukan  kausal.  Pada  baris  uji,  rerata
ekor sambil mempertahankan badan; kalau penapis meratakan  bergerak 24 jam merata-ratakan pembacaan sensor dari baris uji
dinamika yang asli, kedua angka akan turun bersama-sama.  tetangga, termasuk yang sesudah baris tersebut. Itu adalah data
fitur masa depan, dan ia sah di sini karena tiga alasan: panitia
|     | Interpolasi terhadap waktu.  |     |     |     | Setelah  | despiking,  | lubang  |     |     |     |     |     |     |     |     |
| --- | ---------------------------- | --- | --- | --- | -------- | ----------- | ------- | --- | --- | --- | --- | --- | --- | --- | --- |
menyediakan seluruh kanal eksogen untuk seluruh jendela uji;
ditambal dengan interpolasi terhadap indeks waktu dan bukan
tidak satu pun nilai target masa depan masuk ke mana pun; dan
nomor baris, sehingga lompatan 7 jam pada data latih tidak
skenario yang dimodelkan memang “stasiun tetap merekam
diperlakukan sebagai selang 30 menit. Kolom kumulatif gdd
|      |                 |     |           |     |         |          |         |     | sepanjang  periode  | uji,  | rekonstruksi  |     | kelembapannya”,  |     | bukan  |
| ---- | --------------- | --- | --------- | --- | ------- | -------- | ------- | --- | ------------------- | ----- | ------------- | --- | ---------------- | --- | ------ |
| dan  | water_volume_*  |     | tambahan  |     | dijaga  | monoton  | dengan  |     |                     |       |               |     |                  |     |        |
“ramalkan besok tanpa apa-apa”. Yang dilarang keras adalah
| cummax  |     | lalu  diubah  | menjadi  | laju  | 24  jam,  | karena  | tingkat  |     |     |     |     |     |     |     |     |
| ------- | --- | ------------- | -------- | ----- | --------- | ------- | -------- | --- | --- | --- | --- | --- | --- | --- | --- |
nilai RH mana pun dari jendela validasi atau uji masuk sebagai
| kumulatifnya  |     | sendiri  | hanyalah  | tren  | yang  | tidak  | punya  | arti  |     |     |     |     |     |     |     |
| ------------- | --- | -------- | --------- | ----- | ----- | ------ | ------ | ----- | --- | --- | --- | --- | --- | --- | --- |
masukan, dan larangan itu diverifikasi secara mekanis di Bagian
prediktif lintas rezim.
V-E.
B.  Rekayasa Fitur dan Batas Kebocoran
V.  PEMODELAN
Matriks fitur dibangun dari lima blok: dasar untuk keadaan
sesaat dan konteks lokalnya pada tiga skala waktu, tmin untuk  A.  Enam Anggota dan Alasan Masing-Masing Ada
proksi titik embun Persamaan (4), tend untuk rezim sinoptik,  Enam anggota dilatih, lima di antaranya bertahan sampai
ordstat untuk laju ventilasi lewat CO₂, dan qblock untuk
konfigurasi akhir. Tiga di antaranya adalah model pohon ter-
persentil suhu. Setiap blok menjawab satu pertanyaan fisis; tidak  boost (dua LightGBM [6] dan satu CatBoost [7]), dan tiga
ada blok yang ditambahkan dengan alasan “lebih banyak fitur  sisanya  linear.  Tabel  II  memuat  keenamnya  beserta  alasan
biasanya membantu”, dan Tabel A.II di lampiran memerincinya.  masing-masing ada. Yang perlu ditekankan adalah bahwa dua di
Blok tanah  dibuang  seluruhnya  karena  alasan dukungan  di  antara mereka ada bukan karena akurasi solonya.
Bagian III-E.
TABEL II.  ENAM ANGGOTA DAN ALASAN MASING-MASING ADA
|     | Anggota  |     |     |     | Model  |     |     | Bobot  |     |     | Mengapa ia ada  |     |     |     |     |
| --- | -------- | --- | --- | --- | ------ | --- | --- | ------ | --- | --- | --------------- | --- | --- | --- | --- |
  LightGBM, huber α = 2, 900 pohon, 15 daun  0,489  pekerja utama; huber menahan pengaruh baris yang tersisa berderau
hbt
  CatBoost, Huber:delta=4, 1.200 iterasi, kedalaman 6  0,217  s e n g a j a  sa l a h -s p e s if ik a s i;   k o r e la s i  re s id u  t e r h a d a p   h b t   hanya 0,64, terendah
cat d a ri  s e m u a  p o h o n .  Y a n g  d i b e l i  b le n d  a d a la h   d e k o r e l a s i
  elastic-net terstandardisasi  0,194  anggota linear; mengekstrapolasi mulus ke suhu di luar dukungan
enet
  ridge di ruang tekanan uap, dikonversi balik  0,050  s a t u - s a t u n y a   a n g g o t a  ya ng terdekorelasi secara fisis: ia meminimumkan galat
|     | ridge_e |     |     |     |     |     |     |     |                   |                        |     |     |     |     |     |
| --- | ------- | --- | --- | --- | --- | --- | --- | --- | ----------------- | ---------------------- | --- | --- | --- | --- | --- |
|     |         |     |     |     |     |     |     |     | p a d a   e ,   b | u k a n   p a d a  R H |     |     |     |     |     |
  LightGBM, kerugian kuadrat  0,050  metriknya RMSE; anggota ini mengembalikan sensitivitas terhadap residu besar
l2
  ridge biasa  dibuang  k o nt ri b u si   d ro p -o n e  negatif; bobot NNLS nol di 18 dari 18 lipatan; −0,012
|     | ridge |     |     |     |     |     |     |     |              |                  |     |     |     |     |     |
| --- | ----- | --- | --- | --- | --- | --- | --- | --- | ------------ | ---------------- | --- | --- | --- | --- | --- |
|     |       |     |     |     |     |     |     |     | R M S E   sa | a t  d ib u an g |     |     |     |     |     |
Anggota cat sengaja dibiarkan salah-spesifikasi: solonya  dimasukkan dengan tangan. Kerangka umumnya adalah stacked
lebih buruk 0,9 RMSE daripada CatBoost berkerugian kuadrat,  generalization [10].
tetapi korelasi residunya terhadap anggota utama hanya 0,64,
Bobot per pita waktu-hari. Anggota tidak sama baiknya
terendah dari seluruh anggota pohon. Yang dibeli blend darinya
sepanjang jam. Dipasang per tiga pita yang tepinya adalah
dekorelasi, bukan akurasi. Anggota ridge_e dipasang di ruang
kuantil jam-hari, ridge_e naik dari lantainya 0,05 di malam
| tekanan  | uap  | lalu  dikonversi  |     | balik  | lewat  | (1),  sehingga  |     | ia  |     |     |     |     |     |     |     |
| -------- | ---- | ----------------- | --- | ------ | ------ | --------------- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
hari menjadi 0,15 di tengah hari, tepat ketika e(T) terbesar dan
| meminimumkan galat pada e dan bukan pada RH.  |     |     |     |     |     |     |     |     |     |     |     |     |     | s   |     |
| --------------------------------------------- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
parameterisasi tekanan uap paling berarti; cat justru naik di
Pemilihan kerugian pada anggota utama juga bukan pilihan  sore hari. Satu vektor bobot global merata-ratakan rezim itu.
sembarang. Kerugian Huber [8] berperilaku kuadratik di dekat  Perbaikannya −0,080 pada validasi bersarang, dan kontrol yang
nol dan linear di ekornya, sehingga baris berderau berat tidak  mengondisikan pada peubah acak dengan jumlah parameter
menarik model sekuat pada L2. Kami menyapu parameter huber  bebas yang sama hanya membeli −0,007. Jadi yang diukur
α dari 1 sampai kuadrat murni: α = 1 memburukkan blok utama  adalah sinyal, bukan kapasitas tambahan.
sebesar +0,537 dan kuadrat murni +0,185, sedangkan α = 2
|     |     |     |     |     |     |     |     |     | Koreksi  | bias  diurnal.  |     | Bobot  | NNLS  | non-negatif  | dan  |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | -------- | --------------- | --- | ------ | ----- | ------------ | ---- |
sampai 6 adalah dataran datar. Intuisi “metriknya RMSE maka
|     |     |     |     |     |     |     |     |     | ternormalisasi,  | sehingga  | blend  | tidak  | punya  | intersep  | dan  |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | ---------------- | --------- | ------ | ------ | ------ | --------- | ---- |
pasangkan kerugian L2” salah lebar di sini, dan alasannya sudah
pembobotan ulang per pita meninggalkan offset per pita tak
| terbaca  | di  | Bagian  II-C:  | prediktornya  |     | masih  | berderau  | berat  |     |                     |      |        |                  |     |        |         |
| -------- | --- | -------------- | ------------- | --- | ------ | --------- | ------ | --- | ------------------- | ---- | ------ | ---------------- | --- | ------ | ------- |
|          |     |                |               |     |        |           |        |     | tersentuh.  Offset  | itu  | besar  | dan  konsisten:  |     | blend  | kurang  |
meskipun targetnya bersih.
memprediksi puncak kelembapan sekitar pukul 04.00 dan lebih
B.  Blending: NNLS, Pita Waktu-Hari, dan Bias Diurnal  memprediksi lembah sekitar pukul 15.00 pada 18 dari 18 lipatan
Bobot blend berasal dari kuadrat-terkecil non-negatif [9]  bersarang. Itu tanda tangan pemadatan amplitudo oleh kerugian
pada prediksi luar-lipatan,  huber  dan  perata-rataan  pohon.  Level  global  sengaja
dikurangkan keluar dari koreksi ini dan ditangani terpisah di
sub-bagian berikutnya.
|     |     | ŵ = arg min ‖ P w − y ‖2,   w ≥ 0  |     |     |     |     | (8)  |     |          |                |     |           |             |     |           |
| --- | --- | ---------------------------------- | --- | --- | --- | --- | ---- | --- | -------- | -------------- | --- | --------- | ----------- | --- | --------- |
|     |     |                                    |     |     |     |     |      |     | Mengapa  | satu  anggota  |     | dibuang.  | Kontribusi  |     | drop-one  |
lalu ditarik sebesar 25 % ke arah pembobotan seragam  anggota  ridge  negatif,  artinya  membuangnya  justru
sebagai lantai penyusutan. Tidak ada satu pun angka bobot yang  membantu. Bobot NNLS globalnya persis nol pada 18 dari 18
lipatan, dan ia adalah anggota yang paling dirusak oleh blok

tekanan  yang  kehilangan  dukungan  di  jendela  uji.  anggota yang biasnya +0,05 membeli +0,017, yakni tidak ada
Membuangnya bernilai −0,012 RMSE di papan peringkat.  apa-apa. Di papan peringkat nilainya −0,022.
C.  De-bias Level per Anggota  D.  Rekonsiliasi Lintasan Berbasis Increment
Temuan berikut muncul dari mencetak satu angka yang  Ini komponen tunggal paling berharga di seluruh solusi, jadi
belum pernah kami cetak selama 46 sesi eksperimen: rerata galat  rasionalnya ditulis lengkap. Seluruh pipeline sampai titik ini
bertanda setiap anggota blend pada blok validasi maju. Gambar  menilai 734 baris uji satu per satu, padahal galat model level
4 memuat hasilnya.  punya autokorelasi lag-satu 0,93: pada satu penggal waktu ia
salah dengan besaran yang hampir sama sepanjang penggal itu.
Kurangkan dua prediksi bertetangga dan sebagian besar galat itu
|     |     |     |     |     |     |     | saling  | meniadakan. Tiga  |     | angka  | menyatakan  |     | seberapa besar  |     |
| --- | --- | --- | --- | --- | --- | --- | ------- | ----------------- | --- | ------ | ----------- | --- | --------------- | --- |
peluang yang tersisa di sana, ketiganya diukur pada 6.471 baris
luar-lipatan yang sama: perubahan RH 30 menit punya sinyal
|     |     |     |     |     |     |     | sebesar  | RMSE  | 3,55;  | prediksi  | level  | stack  | sendiri  | sudah  |
| --- | --- | --- | --- | --- | --- | --- | -------- | ----- | ------ | --------- | ------ | ------ | -------- | ------ |
menyiratkan perubahan itu dengan RMSE 1,91; dan model
|     |     |     |     |     |     |     | perubahan  | khusus  | mencapai  |     | 1,81.  | Pada  | horizon  | 2  jam  |
| --- | --- | --- | --- | --- | --- | --- | ---------- | ------- | --------- | --- | ------ | ----- | -------- | ------- |
keunggulan itu hilang, 3,57 lawan 3,52, dan itulah alasan bobot
rekonsiliasinya 4 : 1 dan bukan seimbang.
Kedua sumber informasi itu dapat digabungkan secara tepat.
Kami mencari satu lintasan z yang tetap dekat dengan prediksi
level p sekaligus mengikuti dinamika yang dipelajari,

Gambar 4.  Rerata galat bertanda setiap anggota blend pada blok validasi maju,
|     |     |     |     |     |     |     |     | min  ‖ z − p ‖2 + Σ | z   | h  λ ‖ D z − d ‖2  | h h | h   |     | (9)  |
| --- | --- | --- | --- | --- | --- | --- | --- | ------------------- | --- | ------------------ | --- | --- | --- | ---- |
dibanding rerata galat bertanda di dalam sampel. Satu anggota berada jauh di
| luar kelompok, dan bias dalam-sampelnya tetap nol.  |     |     |     |     |     |     |     |     |     |     |     |     |     |     |
| --------------------------------------------------- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
yang diselesaikan sekali dengan penyelesai jarang: tanpa
Lima anggota berada di dalam ±0,8 %RH. Anggota cat
iterasi, tanpa parameter bebas di luar dua bobot yang sudah
berada di −2,89 %RH, memegang 0,217 bobot blend, dan
|     |     |     |     |     |     |     | dibekukan  |     | sebelum  | eksperimen  |     | ini  | ada.  | Kerangka  |
| --- | --- | --- | --- | --- | --- | --- | ---------- | --- | -------- | ----------- | --- | ---- | ----- | --------- |
menyeret seluruh stack ke bawah sekitar 1 %RH. Bias di dalam
|     |     |     |     |     |     |     | konseptualnya  |     | adalah  | rekonsiliasi  | ramalan  |     | sebagai  | proyeksi  |
| --- | --- | --- | --- | --- | --- | --- | -------------- | --- | ------- | ------------- | -------- | --- | -------- | --------- |
sampel-nya −0,006, jadi ini murni sifat maju dan bukan artefak
|     |     |     |     |     |     |     | kuadrat-terkecil  |     | [11],  | dipindahkan  |     | dari  hierarki  |     | agregasi  ke  |
| --- | --- | --- | --- | --- | --- | --- | ----------------- | --- | ------ | ------------ | --- | --------------- | --- | ------------- |
pemasangan. Angka −2,89 diukur pada cache tiga blok validasi
hierarki temporal.
maju 15 hari; pada baris luar-lipatan, instrumen berbeda yang
dicetak  notebook,  anggota  yang  sama  memberi  −1,86.  ( I + Σ  λ D⊤ D ) z = p + Σ  λ D⊤ d   (10)
|           |          |       |        |      |                   |      |     |     | h h h | h   | h   | h h | h   |     |
| --------- | -------- | ----- | ------ | ---- | ----------------- | ---- | --- | --- | ----- | --- | --- | --- | --- | --- |
| Keduanya  | sepakat  | pada  | tanda  | dan  | urutan  anggota,  | dan  |     |     |       |     |     |     |     |     |

besarannya berbeda karena blok maju menuntut ekstrapolasi
lebih jauh.  Kebersihan target dijaga di dua tempat. Kedua ujung setiap
selisih latih wajib merupakan baris latih berlabel, sehingga tidak
Mekanismenya spesifik dan dapat diverifikasi. Kerugian  ada  selisih  yang  menyeberangi  titik  asal  peramalan.  Dan
Huber:delta=4 pada target dengan simpangan baku 18 %RH  inferensinya hanya membaca kolom eksogen, sehingga tidak
| memotong  | gradien  | di  | atas  | 4  %RH,  | sehingga  | anggota  itu  |     |     |     |     |     |     |     |     |
| --------- | -------- | --- | ----- | -------- | --------- | ------------- | --- | --- | --- | --- | --- | --- | --- | --- |
ada RH jendela uji yang menjadi masukan dan tidak ada umpan
menjejak median bersyarat dan mendarat rendah begitu diminta
balik rekursif. Model perubahannya sendiri menangkap R² =
| memprediksi  | ke  | luar  | jendela  | latihnya.  | Sapuan  | kerugian  |     |     |     |     |     |     |     |     |
| ------------ | --- | ----- | -------- | ---------- | ------- | --------- | --- | --- | --- | --- | --- | --- | --- | --- |
0,74 pada 30 menit dan 0,90 pada 2 jam.
mengonfirmasinya pada satu split terkendali, dipasang pada 46
Gambar 5 memperlihatkan hasilnya pada tiga blok validasi
| hari  pertama  | lalu  | dinilai  | pada  | 15  hari  | berikutnya:  | dengan  |     |     |     |     |     |     |     |     |
| -------------- | ----- | -------- | ----- | --------- | ------------ | ------- | --- | --- | --- | --- | --- | --- | --- | --- |
kerugian  kuadrat  bias  maju  CatBoost  −0,04,  sedangkan  maju, dan di papan peringkat nilainya −0,160 RMSE, tujuh kali
Huber:delta=4 −1,62 pada split yang sama.  lipat perbaikan blending terbaik.
| Yang  | membuat  | temuan  |     | ini  layak  | dilaporkan  | adalah  |     |     |     |     |     |     |     |     |
| ----- | -------- | ------- | --- | ----------- | ----------- | ------- | --- | --- | --- | --- | --- | --- | --- | --- |
mengapa ia bisa bertahan selama itu, bukan besarnya. Tidak
ada satu pun komponen di pipeline yang berbentuk cukup untuk
melihatnya. Bobot NNLS non-negatif dan ternormalisasi, jadi
blend tidak punya intersep. Koreksi bias diurnal memasang
| intersep  | lalu  | sengaja  | membuangnya.  |     | Gerbang  | validasi  |     |     |     |     |     |     |     |     |
| --------- | ----- | -------- | ------------- | --- | -------- | --------- | --- | --- | --- | --- | --- | --- | --- | --- |
melaporkan RMSE, dan RMSE tidak memisahkan bias dari
ragam. Offset itu tidak terlihat oleh instrumen mana pun yang
sudah ada.
Koreksinya dibuat sekecil mungkin: satu skalar, yaitu rerata
galat luar-lipatan anggota itu sendiri, diterapkan pada kekuatan
0,5. Ia diukur pada baris yang hanya berasal dari masa lalu setiap
lipatan, jadi ia pengukuran maju atas besaran yang sama yang
akan ditunjukkan jendela uji. Pada blok maju nilainya −0,077
Gambar 5.  RMSE pada tiga blok validasi maju, sebelum dan sesudah
RMSE terkumpul dengan lima dari enam blok membaik. Dua
rekonsiliasi lintasan. Perbaikannya konsisten pada ketiga blok.
kontrol yang didaftarkan sebelum angkanya dibaca berperilaku
E.  Bukti Buta-Target dan Reproduksibilitas
| persis  seperti  | yang  | disyaratkan  |     | mekanisme:  | menambahkan  |     |     |     |     |     |     |     |     |     |
| ---------------- | ----- | ------------ | --- | ----------- | ------------ | --- | --- | --- | --- | --- | --- | --- | --- | --- |
offset, bukan menguranginya, kalah +0,162 dengan nol dari  Sebelum  satu  model  pun  dipasang,  kami  membuktikan
enam blok membaik, dan mengarahkan mesin yang sama ke  secara mekanis bahwa tidak satu pun fitur bergantung pada

target: seluruh matriks fitur dibangun ulang dari kisi yang kolom  karena kesamaan sampai bit terakhir bukan kriteria yang benar
targetnya sudah dihapus, lalu dibandingkan bit per bit dengan  di sini: penyelesai jarang pada (10) menggeser satu baris sebesar
matriks yang dipakai produksi. Hal yang sama dilakukan untuk  10⁻¹⁵ antar-jalankan, dan penjumlahan histogram di LightGBM
matriks desain increment. Keduanya lolos.  maupun  CatBoost  bergantung  urutan  thread  sehingga  versi
pustaka yang sama pada mesin berbeda menggeser prediksi orde
Satu-satunya sumber keacakan di seluruh pipeline adalah
0,3 %RH. Lapisan pra-pemrosesan dan kedua anggota linear
penanaman pohon; ansambelnya merata-ratakan seed 0–2 di
reproduksi sampai digit terakhir. Lampiran I memuat angkanya.
dalam validasi silang dan 0–4 pada pemasangan akhir, dengan
seed increment tetap. Seluruh pipeline berjalan di atas tumpukan
VI.  EVALUASI DAN PEMBAHASAN
Python yang versinya dicatat Tabel A.VI: NumPy [12] dan
A.  Pembanding Sejawat
pandas [13] untuk kisi dan matriks fitur, scikit-learn [14] untuk
kedua anggota linear beserta pra-pemrosesannya, SciPy [15]  Sebelum  membahas  apa  yang  memindahkan  skor,  ada
untuk penyelesai kuadrat-terkecil non-negatif pada (8) sekaligus  pertanyaan yang lebih dasar: apakah arsitektur sepanjang ini
penyelesai jarang pada (10), dan Matplotlib [16] untuk seluruh  memang diperlukan. Kami menjawabnya dengan menilai enam
gambar di naskah ini. Notebook menuliskan berkas submission
metode pembanding pada protokol yang persis sama. Setiap
dan  memeriksa  bentuknya  terhadap  metode dipasang hanya pada baris sebelum titik potong tiap
sample_submission.csv,  lalu  mencetak  md5-nya  lipatan, lalu dinilai pada 15 hari berikutnya, sehingga angkanya
berdampingan dengan md5 dan skor publik berkas yang benar- lahir dari sembilan lipatan dan 6.480 baris luar-lipatan yang
benar  dikirim.  Verifikasinya  ditempuh  dengan mengunggah  identik dengan yang dipakai memasang bobot blend. Tabel III
berkas itu ke Kaggle, bukan oleh pemeriksa di dalam notebook,
dan Gambar 6 memuat hasilnya.
TABEL III.  PEMBANDING SEJAWAT PADA SEMBILAN LIPATAN TITIK-ASAL BERGULIR YANG SAMA
|                                     |     |     | Metode   |     |       | Kelas   | RMSE terkumpul |         | Rerata lipatan |         |
| ----------------------------------- | --- | --- | -------- | --- | ----- | ------- | -------------- | ------- | -------------- | ------- |
|                                     |     |     |          |     |       |         |                |         |                |         |
| Rerata latih                        |     |     |          |     | naif  |         |                | 18,82   |                | 18,81   |
|                                     |     |     |          |     |       |         |                |         |                |         |
| Persistensi profil hari terakhir    |     |     |          |     | naif  |         |                | 13,38   |                | 13,06   |
|                                     |     |     |          |     |       |         |                |         |                |         |
| Proksi titik embun, tanpa parameter |     |     |          |     | fisis |         |                | 10,93   |                | 10,91   |
| Klimatologi jam-hari                |     |     |          |     | naif  |         |                | 10,16   |                | 10,06   |
Regresi linear berganda, 24 kanal   statistik   8,08   7,84
|                                    |     |     |     |     |         |     |     |      |     |      |
| ---------------------------------- | --- | --- | --- | --- | ------- | --- | --- | ---- | --- | ---- |
| LightGBM tunggal, parameter bawaan |     |     |     |     | mesin   |     |     | 5,71 |     | 5,63 |
|                                    |     |     |     |     |         |     |     |      |     |      |
| Stack lengkap (naskah ini)         |     |     |     |     | kami    |     |     | 4,81 |     | 4,69 |
|                                    |     |     |     |     |         |     |     |      |     |      |
| LightGBM tunggal, jendela kausal   |     |     |     |     | kendali |     |     | 8,22 |     | 8,03 |
Empat hal terbaca dari ladder itu. Pertama, klimatologi jam- Ketiga, regresi linear berganda atas 24 kanal mencapai 8,08
hari  (10,16)  hampir  menyamai  proksi  titik  embun  (10,93)  sedangkan satu LightGBM dengan parameter bawaan mencapai
padahal yang satu tanpa fisika dan yang lain tanpa pelatihan:  5,71. Lompatan 2,37 %RH itu adalah harga nonlinearitas dan
keduanya menyentuh sisi berbeda dari struktur yang sama.  interaksi, dan ia jauh lebih besar daripada seluruh sisa pekerjaan
Kedua, persistensi profil hari terakhir hanya 13,38, jauh di  kami. Keempat, stack lengkap mencapai 4,81 terhadap 5,71
belakang klimatologi. Pada horizon 15 hari, hari kemarin adalah  milik LightGBM tunggal, yaitu perbaikan 15,8 %. Angka itu
penduga yang lebih buruk daripada rerata semua hari, dan  adalah ukuran yang paling jujur atas kontribusi tulisan ini,
persoalan ini karena itu bukan persoalan ekstrapolasi jangka  karena pembandingnya bukan tebakan rerata, tetapi apa yang
pendek.  diperoleh siapa pun yang melemparkan satu model gradient
boosting ke matriks fitur yang sama.

Gambar 6.  Tujuh metode pada sembilan lipatan titik-asal bergulir dan 6.480 baris luar-lipatan yang sama. (a) RMSE terkumpul; warna menandai kelas metode. (b)
RMSE per lipatan untuk tiga metode teratas; ketiganya tidak pernah berpotongan, sehingga urutannya bukan hasil undian satu jendela.
Panel (b) Gambar 6 memperlihatkan urutan ketiga metode  pengamatan bebas: lipatan kami tumpang tindih (Lampiran G),
teratas sama di sembilan lipatan tanpa satu pun perpotongan, dan  galat  antar-lipatan  berkorelasi,  dan  setiap  uji  yang
konsistensi itu dapat dinyatakan sebagai uji. Stack mengungguli  mengandaikan  kebebasan  akan  terlalu  longgar.  Uji-t
LightGBM  tunggal  pada  sembilan  dari  sembilan  lipatan,  berpasangan atas data yang sama memberi p < 10⁻⁵, dan sengaja
dengan selisih rerata 0,939 %RH (simpangan baku 0,169) dan  tidak kami pakai sebagai bukti. Yang kami klaim hanya ini: pada
perbaikan relatif 11,2 sampai 27,4 % per lipatan; uji peringkat  protokol dan baris yang sama, urutannya tidak pernah terbalik.
bertanda Wilcoxon berpasangan memberi p = 0,0039, identik
dengan uji tanda karena seluruh selisihnya searah [17]. Angka
| itu  mengukur  | konsistensi  |     | arah,  bukan  bukti  | dari  sembilan  |     |     |     |     |     |     |
| -------------- | ------------ | --- | -------------------- | --------------- | --- | --- | --- | --- | --- | --- |

B. Hasil Menyeluruh Angka 2,827 mengalahkan ketiga garis dasar yang dipasang
lebih dulu: rerata latih 18,0, proksi titik embun (4) 9,1, dan batas
Metrik resmi kompetisi adalah RMSE atas 734 baris uji.
oracle harian 8,37. Menurut Gambar 3 ia setara dengan
Tabel A.IV di lampiran memuat tangga skor papan peringkat
mengetahui tekanan uap yang sebenarnya pada resolusi 6,1 jam.
publik secara lengkap, termasuk perubahan yang merugikan,
dan Gambar 7 menggambarkannya. Angka itu juga perlu dibaca dalam satuan yang dipakai orang
yang mengelola petak, bukan hanya dalam satuan metrik lomba.
RMSE 2,83 %RH adalah 6,9 % dari amplitudo diurnal target
(41,13 %RH) dan 15,7 % dari simpangan bakunya.
Diterjemahkan lewat identitas (1) pada suhu rerata jendela uji
24,64 °C, ia setara dengan galat defisit tekanan uap sebesar
0,088 kPa, dan lewat ∂RH/∂T ≈ −3,6 %RH per °C ia setara
dengan salah membaca termometer sebesar 0,79 °C. Untuk
penjadwalan ventilasi dan pengabutan, yang biasanya bekerja
pada beda VPD orde 0,3 sampai 0,5 kPa, ketelitian sebesar itu
memadai. Yang tidak dijamin olehnya adalah keputusan yang
bergantung pada satu ambang tajam, misalnya ambang RH
untuk jendela infeksi jamur, karena di dekat ambang galat 2,83
%RH masih dapat membalik sisi keputusan; di sana keluaran
model sebaiknya dipakai sebagai peringkat risiko, bukan
Gambar 7. Tangga skor papan peringkat publik untuk konfigurasi yang
berturut-turut diadopsi. Bintang menandai satu-satunya perubahan struktural. sebagai saklar.
Bentuk tangganya adalah temuan tersendiri. Satu tambahan C. Anatomi Galat yang Tersisa
struktural bernilai −0,160, sementara empat perbaikan blending Di mana galat yang tersisa berada menentukan apa yang
terbaik yang digabungkan hanya bernilai −0,077. Perbaikan mungkin dilakukan berikutnya, jadi kami membedahnya pada
terbesar di antara yang kedua, yaitu bias diurnal per pita, bernilai baris luar-lipatan, satu-satunya tempat kebenaran tersedia.
−0,024 atau sepertujuh dari yang pertama. Polanya tidak halus: Gambar 8 memuat tiga panelnya, dan ketiganya dibaca dari
mekanisme baru mengalahkan penyetelan mekanisme lama frame yang sama, yaitu 6.480 baris yang juga menghasilkan
dengan selisih satu orde besaran. Itulah yang akan kami kejar Tabel III.
lebih dulu kalau ada waktu tambahan.
Gambar 8. Pembedahan galat pada baris luar-lipatan. (a) Bagian jumlah kuadrat galat per pita jam. (b) Galat bertanda pada pita yang sama; dua pita terburuk juga
yang paling bias. (c) Pemisahan galat menjadi komponen offset per hari dan komponen bentuk di dalam hari, masing-masing dengan kemiringan kalibrasinya.
Panel (a) memperlihatkan galat menumpuk di pita gelap. Kemiringan harian itu, sayangnya, tidak dapat diduga.
Tiga pita antara pukul 21.00 dan 06.00 menyumbang 53,4 % dari Memasangnya memerlukan sampel tingkat-hari, dan satu
seluruh jumlah kuadrat galat, sedangkan dua pita paling terang jendela hanya punya 13 sampai 23 hari. Ketika kami
antara 09.00 dan 15.00 hanya menyumbang 16,5 %. Panel (b) mengukurnya, dugaan dan realisasinya tidak berkorelasi sama
memperlihatkan penyebabnya berbentuk bias, dan bukan hanya sekali. Itu alasan struktural mengapa 39 % galat tersebut
ragam: pita 00.00 dan 21.00 membawa galat bertanda −1,05 dan terdiagnosis tetapi tidak terpecahkan.
−1,04 %RH, sementara pita 09.00 dan 12.00 membawa +0,97
D. Diagnostik Pasca-Model: Kalibrasi Level dan Dispersi
dan +1,11. Model masih memadatkan ayunan harian, meskipun
koreksi bias diurnal di Bagian V-B sudah memangkas sebagian Sub-bagian ini adalah pemeriksaan penutup, bukan metode
besarnya. pemilihan model. Dua konfigurasi yang sudah dikapalkan
kebetulan berbeda dari pendahulunya hampir hanya pada satu
Panel (c) memuat pemisahan yang paling menentukan.
momen distribusi, sehingga selisih skornya dapat dibaca ulang
Sekitar 39 % galat adalah offset per hari, yaitu satu bilangan
untuk menjawab satu pertanyaan: apakah koreksi level dan
per hari yang salah dan tidak berubah sepanjang hari itu. Sisa 61
dispersi masih menyisakan sesuatu. Perlu dinyatakan terbuka
% adalah bentuk di dalam hari. Dan seluruh pemadatan
apa yang tidak dikerjakan di sini: kedua berkas adalah keluaran
amplitudo berada di tingkat harian: kemiringan kalibrasi pada
model apa adanya, tidak ada satu baris pun yang nilainya
rerata harian adalah 1,147, sedangkan di dalam hari ia 1,054.
ditetapkan dengan tangan, dan tidak ada nilai target yang
Kemiringan per-baris 1,063 hanyalah angka pertama yang
direkonstruksi. Yang dibaca hanya dua skalar agregat atas
diencerkan oleh ragam di dalam hari yang jauh lebih besar.
seluruh slice publik.
Bentuk diurnalnya sudah berukuran benar; yang salah ukuran
adalah tingkat hariannya.

Misalkan  kita  mengapalkan  perubahan  d  pada  vektor  tertutup karena itu berlaku dengan syarat slice publik mewakili
| prediksi p, dengan galat e = p − y. Maka perubahan MSE-nya  |     |     |     |     |     |     |     | sisanya.  |     |     |     |     |     |     |     |
| ----------------------------------------------------------- | --- | --- | --- | --- | --- | --- | --- | --------- | --- | --- | --- | --- | --- | --- | --- |
persis
E.  Katalog Kegagalan
Δ MSE = 2 · mean(d · e) + mean(d2)  (11)  Sebagian besar yang layak diketahui tentang dataset ini
adalah mengapa sesuatu tidak bekerja. Tabel A.III di lampiran

|        |               |     |            |             |     |       |          | memuat  | arah-arah  | yang  | ditolak  | berdasarkan  |     | pengukuran  |     |
| ------ | ------------- | --- | ---------- | ----------- | --- | ----- | -------- | ------- | ---------- | ----- | -------- | ------------ | --- | ----------- | --- |
| Kalau  | d  dirancang  |     | mendekati  | konstanta,  |     | suku  | pertama  |         |            |       |          |              |     |             |     |
internal, masing-masing diukur pada protokol maju yang sama
menjadi 2·d̄·ē, dan skor yang kembali dari papan peringkat
dan dengan kontrolnya. Satu di antaranya layak disebut di sini:
memberi rerata galat level jendela uji secara langsung. Kalau d
analog tetangga terdekat gagal karena pasangan yang keadaan
dirancang sebagai penskalaan murni di sekitar rerata, skor yang
sensornya mirip ternyata berbagi RH jauh lebih erat (r = 0,81)
| kembali  | memberi  | kemiringan  |     | kalibrasinya.  |     | Kebetulan  | dua  |     |     |     |     |     |     |     |     |
| -------- | -------- | ----------- | --- | -------------- | --- | ---------- | ---- | --- | --- | --- | --- | --- | --- | --- | --- |
daripada berbagi tekanan uap (r = 0,47), sehingga kemiripan
| konfigurasi  | terakhir  | yang  | kami  | kapalkan  | berbentuk  |     | persis  |     |     |     |     |     |     |     |     |
| ------------ | --------- | ----- | ----- | --------- | ---------- | --- | ------- | --- | --- | --- | --- | --- | --- | --- | --- |
sensor tidak menyiratkan kemiripan massa udara.
seperti itu.
Kelompok kedua lebih instruktif, dan ia menghasilkan satu
| Yang  | pertama  | adalah  | de-bias  | level  | anggota  | cat,  | yang  |         |                  |     |          |            |     |        |        |
| ----- | -------- | ------- | -------- | ------ | -------- | ----- | ----- | ------- | ---------------- | --- | -------- | ---------- | --- | ------ | ------ |
|       |          |         |          |        |          |       |       | aturan  | yang  membentuk  |     | seluruh  | keputusan  |     | akhir  | kami:  |
d̄
| perubahannya  |     | hampir  | murni  pergeseran  |     | level  | dengan  | =   |     |     |     |     |     |     |     |     |
| ------------- | --- | ------- | ------------------ | --- | ------ | ------- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
perubahan yang buktinya kuat secara internal dan tetap salah di
+0,20244. MSE bergerak dari 8,11982 ke 7,99442, jadi ΔMSE
|     |     |     |     |     |     |     |     | papan  peringkat.  |     | Kemiringan  |     | kalibrasi  | dispersi  | versi  | awal  |
| --- | --- | --- | --- | --- | --- | --- | --- | ------------------ | --- | ----------- | --- | ---------- | --------- | ------ | ----- |
= −0,12540. Membalik (11) memberi
menang di 13 dari 13 lipatan pada tiga keluarga lipatan yang
berbeda lalu kalah +0,237, karena sebaran prediksi uji ternyata
| ē = ( ΔMSE − mean(d2) ) / ( 2 d̄ ) = −0,4145 %RH  |     |     |     |     |     |     | (12)  |     |     |     |     |     |     |     |     |
| ------------------------------------------------- | --- | --- | --- | --- | --- | --- | ----- | --- | --- | --- | --- | --- | --- | --- | --- |
berada di atas setiap lipatan validasi silang sehingga pemadatan
|     |     |     |     |     |     |     |     | yang hendak dibatalkan tidak ada di sana. Membuang lantai  |     |     |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | --- | ---------------------------------------------------------- | --- | --- | --- | --- | --- | --- | --- |
yaitu  galat  level  sesungguhnya  pada  slice  publik.  penyusutan NNLS menang −0,058 pada validasi bersarang lalu
Konfigurasi kedua memberi hal yang sama untuk momen kedua  kalah  +0,028.  Koreksi  pita-rentang-lebar  mengukur
dan memberi kemiringan kalibrasi s* = 1,0050.  mekanismenya dengan arah yang benar lalu kalah +0,126 karena
biasnya membalik tanda di jendela uji. Dari tiga penghalusan
TABEL IV.  DIAGNOSTIK KALIBRASI PASCA-MODEL PADA SLICE  increment yang diadopsi secara internal, nol yang menang di
PUBLIK
papan peringkat.
| Besaran jendela uji  |     |     | Dugaan internal  |     | Terukur  |     | Sisa  |     |     |     |     |     |     |     |     |
| -------------------- | --- | --- | ---------------- | --- | -------- | --- | ----- | --- | --- | --- | --- | --- | --- | --- | --- |
galat level rerata (%RH)  −0,98  −0,4145  −0,008  Aturan  yang  kami  tarik:  validasi  silang  memeringkat
|                       |     |     |     |        |         |     |         | perubahan  | pada  | model.  | Untuk  | apa  | pun  yang  | diterapkan  |     |
| --------------------- | --- | --- | --- | ------ | ------- | --- | ------- | ---------- | ----- | ------- | ------ | ---- | ---------- | ----------- | --- |
| kemiringan kalibrasi  |     |     |     | 1,031  | 1,0050  |     | −0,002  |            |       |         |        |      |            |             |     |
setelah model (kalibrasi, ekspansi, koreksi bias) bukti validasi

silang perlu tetapi tidak cukup. Besaran yang dikoreksi harus
| Tabel  | IV  menempatkan  |     | kedua  | angka  | itu  | berdampingan  |     |     |     |     |     |     |     |     |     |
| ------ | ---------------- | --- | ------ | ------ | ---- | ------------- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
juga terlihat sama pada fitur uji, atau koreksi itu tidak boleh
dengan dugaan instrumen internal kami, dan perbandingannya
diterapkan.
| adalah  | kalibrasi  | yang  | berguna.  |     | Instrumen  |     | internal  |     |     |     |     |     |     |     |     |
| ------- | ---------- | ----- | --------- | --- | ---------- | --- | --------- | --- | --- | --- | --- | --- | --- | --- | --- |
F.  Keterbatasan
mendapatkan tandanya dengan benar tetapi besarannya
terlalu besar secara konsisten, sekitar 2 sampai 6 kali. Blok  1) Kalender tunggal, dan sampel efektif yang kecil. Seluruh
validasi maju kami adalah jendela Juli–Agustus yang galat  bukti internal berasal dari satu musim 62 hari; blok validasi
tingkat-hariannya lebih besar daripada jendela uji, dan setiap
maju kami tumpang tindih dan seluruhnya Juli–Agustus, dan
statistik level mewarisi undian tingkat-hari blok itu sendiri.  Bagian VI-D menunjukkan mereka melebih-lebihkan galat
Aturan yang kami tarik: ambil tandanya, potong besarannya.  tingkat-level 2 sampai 6 kali. Autokorelasi lag-satu 0,979
membuat 2.933 baris setara sekitar 62 sampel harian bebas,
Setelah kedua koreksi diterapkan, sisa pada sumbu level
dan justru pada skala itulah 39 % galat berada. Setiap angka
tinggal −0,008 RMSE dan pada sumbu dispersi −0,002. Kedua
internal di tulisan ini karena itu harus dibaca dengan tanda
keluarga koreksi pasca-model tertutup secara kuantitatif.
yang benar dan besaran yang dipotong.
| Tidak  ada  | lagi  | yang  | bisa  dipanen  |     | dari  menggeser  |     | atau  |              |           |     |           |               |     |      |       |
| ----------- | ----- | ----- | -------------- | --- | ---------------- | --- | ----- | ------------ | --------- | --- | --------- | ------------- | --- | ---- | ----- |
|             |       |       |                |     |                  |     |       | 2)  Jendela  | terpusat  |     | bersifat  | transduktif,  |     | dan  | kami  |
menskalakan prediksi; perbaikan berikutnya harus datang dari
mengukur harganya. Fitur pada baris uji membaca sensor
prediksi bersyarat yang benar-benar lebih baik.
dari baris uji tetangga. Ini sah menurut rancangan kompetisi
| Konfigurasi  |     | kedua  | merugi  | 0,006  | dan  karena  |     | itu  tidak  |     |     |     |     |     |     |     |     |
| ------------ | --- | ------ | ------- | ------ | ------------ | --- | ----------- | --- | --- | --- | --- | --- | --- | --- | --- |
dan tidak pernah menyentuh target, tetapi ia bukan operasi
dikapalkan; kami tetap melaporkannya sebagai hasil. Informasi  kausal waktu-nyata: model ini merekonstruksi kelembapan
yang dibelinya, yaitu bahwa model sudah terkalibrasi dispersi  dari jejak sensor yang lengkap, bukan meramalkannya secara
pada jendela uji, menutup sumbu yang kalau s ternyata 1,05  daring. Daripada menyerahkan pertanyaan itu sebagai catatan
akan bernilai −0,14 RMSE. Membayar 0,006 untuk mengetahui
kaki, kami membangun ulang seluruh matriks fitur dengan
itu adalah pertukaran yang benar, dan submission* terbaik
setiap jendela bergulir diubah menjadi ekor-belakang dan 12
tetap tersimpan.
|     |     |     |     |     |     |     |     | kolom  | yang  | melihat  | ke  | depan  | dibuang,  | lalu  | melatih  |
| --- | --- | --- | --- | --- | --- | --- | --- | ------ | ----- | -------- | --- | ------ | --------- | ----- | -------- |
LightGBM yang sama pada sembilan lipatan yang sama.
Dua batas perlu dinyatakan terbuka. Kedua besaran di Tabel
RMSE-nya bergerak dari 5,71 ke 8,22, yaitu +2,51 atau 44
IV adalah properti slice publik, bukan seluruh 734 baris, dan
%, dan baris terakhir Tabel III mencatatnya sebagai kendali.
| membaca  | dua  | belas  skor  | dari  | papan  | yang  | sama  | berisiko  |     |     |     |     |     |     |     |     |
| -------- | ---- | ------------ | ----- | ------ | ----- | ----- | --------- | --- | --- | --- | --- | --- | --- | --- | --- |
menyesuaikan diri pada slice itu. Keduanya membentuk cara  Besaran itu sendiri adalah temuan: 8,22 lebih buruk
daripada regresi linear berganda atas jendela terpusat
kami memakainya: papan peringkat hanya untuk dua momen
|     |     |     |     |     |     |     |     | yang  | mencapai  | 8,08,  | jadi  | sebagian  | besar  | keunggulan  |     |
| --- | --- | --- | --- | --- | --- | --- | --- | ----- | --------- | ------ | ----- | --------- | ------ | ----------- | --- |
distribusi yang mekanismenya sudah terukur lebih dulu pada
|     |     |     |     |     |     |     |     | pendekatan  |     | berbasis  | pohon  | di  | sini  bersumber  |     | dari  |
| --- | --- | --- | --- | --- | --- | --- | --- | ----------- | --- | --------- | ------ | --- | ---------------- | --- | ----- |
blok validasi maju, tidak pernah untuk menyetel model, dan
|     |     |     |     |     |     |     |     | kemampuan  |     | membaca  | sensor  | serempak  |     | dan  bukan  | dari  |
| --- | --- | --- | --- | --- | --- | --- | --- | ---------- | --- | -------- | ------- | --------- | --- | ----------- | ----- |
berkas yang dikapalkan adalah konfigurasi berskor terbaik alih-
alih  yang  terakhir  diuji.  Kesimpulan  bahwa  kedua  sumbu  kapasitas  modelnya.  Sistem  daring  yang  benar-benar
meramal ke depan karena itu tidak akan mewarisi angka 2,83,
|     |     |     |     |     |     |     |     | dan  | usaha  | berikutnya  | untuk  | kasus  | daring  | sebaiknya  |     |
| --- | --- | --- | --- | --- | --- | --- | --- | ---- | ------ | ----------- | ------ | ------ | ------- | ---------- | --- |

diarahkan ke ramalan cuaca numerik sebagai masukan [2] R. G. Allen, L. S. Pereira, D. Raes, and M. Smith, Crop Evapotranspiration:
eksogen, bukan ke model yang lebih besar. Rekonsiliasi Guidelines for Computing Crop Water Requirements, FAO Irrigation and
Drainage Paper 56. Rome, Italy: FAO, 1998.
lintasan di Bagian V-D tetap berlaku pada rezim kausal,
[3] Ontario Ministry of Agriculture, Food and Rural Affairs, "Crop Heat Units for
karena ia hanya mengikat prediksi satu sama lain dan tidak
Corn and Other Warm-Season Crops in Ontario," Factsheet 93-119, Guelph,
pernah membaca target.
ON, Canada, 1993.
3) Blok tanah dan irigasi dibuang. Kami membuangnya [4] C. Bergmeir and J. M. Benítez, "On the Use of Cross-Validation for Time
karena hilangnya dukungan di jendela uji dan memverifikasi Series Predictor Evaluation," Information Sciences, vol. 191, pp. 192–213,
bahwa memulihkannya merugikan. Pada penyebaran dengan 2012.
irigasi aktif kolom-kolom itu membawa informasi [5] F. R. Hampel, "The Influence Curve and Its Role in Robust Estimation,"
evapotranspirasi yang nyata, sehingga keputusan ini khusus Journal of the American Statistical Association, vol. 69, no. 346, pp. 383–393,
1974.
untuk jendela uji ini.
[6] G. Ke et al., "LightGBM: A Highly Efficient Gradient Boosting Decision
Tree," in Advances in Neural Information Processing Systems 30, Long Beach,
VII. KESIMPULAN
CA, USA, 2017, pp. 3146–3154.
Reformulasi fisis adalah keputusan tunggal yang paling [7] L. Prokhorenkova, G. Gusev, A. Vorobev, A. V. Dorogush, and A. Gulin,
berpengaruh. Menulis Persamaan (1) dan menyadari bahwa "CatBoost: Unbiased Boosting with Categorical Features," in Advances in
penyebutnya diketahui persis pada waktu uji mengubah masalah Neural Information Processing Systems 31, Montréal, QC, Canada, 2018, pp.
6638–6648.
peramalan deret waktu menjadi masalah pendugaan tekanan
[8] P. J. Huber, "Robust Estimation of a Location Parameter," Annals of
uap. Setiap blok fitur yang bertahan sampai versi akhir, dari
Mathematical Statistics, vol. 35, no. 1, pp. 73–101, 1964.
proksi titik embun atas minimum bergulir sampai persentil suhu,
[9] C. L. Lawson and R. J. Hanson, Solving Least Squares Problems. Englewood
penjejak ventilasi CO₂, dan tendensi tekanan sinoptik, adalah
Cliffs, NJ, USA: Prentice-Hall, 1974.
usaha menduga e. Kurva oracle memberi ukuran objektif
[10] D. H. Wolpert, "Stacked Generalization," Neural Networks, vol. 5, no. 2, pp.
seberapa jauh usaha itu berhasil: stack ini setara dengan
241–259, 1992.
mengetahui tekanan uap yang sebenarnya pada resolusi 6,1 jam.
[11] R. J. Hyndman, R. A. Ahmed, G. Athanasopoulos, and H. L. Shang, "Optimal
Combination Forecasts for Hierarchical Time Series," Computational Statistics
Memperlakukan jendela uji sebagai deret waktu bernilai
& Data Analysis, vol. 55, no. 9, pp. 2579–2589, 2011.
tujuh kali lipat apa pun yang lain. Setiap komponen lain
[12] C. R. Harris et al., "Array Programming with NumPy," Nature, vol. 585, no.
menilai baris satu per satu; rekonsiliasi lintasan adalah satu-
7825, pp. 357–362, 2020.
satunya yang menghubungkan seluruh 734 baris lewat satu
[13] The pandas development team, "pandas-dev/pandas: Pandas," Zenodo, 2020.
sistem linear, dan satu-satunya perubahan yang bernilai lebih doi: 10.5281/zenodo.3509134.
dari 0,03 RMSE. [14] F. Pedregosa et al., "Scikit-learn: Machine Learning in Python," Journal of
Machine Learning Research, vol. 12, pp. 2825–2830, 2011.
Cacat kalibrasi bisa bertahan lama justru karena tidak
[15] P. Virtanen et al., "SciPy 1.0: Fundamental Algorithms for Scientific
ada yang mencetak angkanya. Bias level −2,89 %RH pada
Computing in Python," Nature Methods, vol. 17, no. 3, pp. 261–272, 2020.
satu anggota blend bertahan puluhan iterasi karena tidak satu
[16] J. D. Hunter, "Matplotlib: A 2D Graphics Environment," Computing in Science
pun instrumen (NNLS, koreksi bias diurnal, maupun gerbang & Engineering, vol. 9, no. 3, pp. 90–95, 2007.
validasi berbasis RMSE) punya bentuk yang bisa melihatnya. Ia
[17] J. Demšar, "Statistical Comparisons of Classifiers over Multiple Data Sets,"
ditemukan dengan mencetak rerata galat bertanda per anggota, Journal of Machine Learning Research, vol. 7, pp. 1–30, 2006.
satu baris kode, dan bernilai −0,022 RMSE.
Validasi silang memeringkat perubahan pada model;
untuk koreksi setelah model ia perlu tetapi tidak cukup. Tiga
koreksi pasca-model lolos validasi internal, satu di antaranya
menang di 13 dari 13 lipatan, lalu tetap merugikan pada jendela
uji. Aturannya: besaran yang hendak dikoreksi harus terlihat
sama pada fitur uji, atau koreksi itu tidak diterapkan. Diagnostik
penutup di Bagian VI-D mengonfirmasi kedua sumbu koreksi
memang sudah tertutup, dengan sisa di bawah 0,01 RMSE.
Skor akhir RMSE publik 2,82744, dari garis dasar naif 18,0
dan garis dasar fisis bebas-parameter 9,1. Kesenjangan yang
tersisa sudah terdiagnosis: 39 % galat adalah offset per hari
dengan kemiringan pemadatan 1,147 yang tidak dapat diduga
dari 13 sampai 23 hari sejarah. Pekerjaan berikutnya yang kami
anggap paling menjanjikan karena itu adalah mekanisme baru
pada skala harian, bukan penyetelan lebih lanjut atas mekanisme
yang ada.
Notebook yang dikumpulkan membangun ulang seluruh
hasil di tulisan ini dari data mentah dengan seed tetap, lalu
memverifikasi prediksinya terhadap berkas yang benar-benar
dikirim ke papan peringkat. Tidak ada data eksternal, model
pretrained, maupun kode eksternal yang dipakai.
DAFTAR PUSTAKA
[1] D. Bolton, "The Computation of Equivalent Potential Temperature," Monthly
Weather Review, vol. 108, no. 7, pp. 1046–1053, 1980.

LAMPIRAN Panel (a) adalah target: berayun 40 %RH setiap hari,
berpuncak menjelang subuh dan berlembah pada sore hari.
Badan laporan berakhir bersama daftar pustaka pada
Panel (b) adalah tekanan uap jenuh e(T), yang berayun sama
halaman 10, sesuai batas juknis pasal 3.b. Lampiran berikut s
tajamnya dan berlawanan fase, dan yang diketahui persis pada
ditambahkan menurut pasal 3.d dan memuat bahan pendukung
setiap baris uji karena suhu termasuk kanal yang disediakan
yang tidak muat di badan naskah: enam gambar yang
panitia. Panel (c) adalah tekanan uap aktual e, satu-satunya
menjelaskan kerangka analisis lebih pelan, katalog blok fitur,
besaran yang harus diduga.
tangga skor papan peringkat selengkapnya, dua tabel katalog
kegagalan, kontrak reproduksibilitas, dan audit per kanal untuk Yang perlu diperhatikan adalah perbedaan bentuk, dan
seluruh 24 kolom eksogen. Tidak ada argumen di Bagian I–VII bukan hanya skala. Panel (a) dan (b) adalah deret bergerigi
yang bergantung pada isi lampiran; seluruhnya memperdalam, dengan struktur harian yang tajam; panel (c) jauh lebih tenang,
bukan melengkapi. dengan penggal datar yang bertahan setengah hari dan transisi
yang berlangsung beberapa jam. Massa udara berganti perlahan;
A. Dekomposisi Fisis Kelembapan Relatif
suhu berganti cepat. Itulah seluruh isi keputusan untuk
Persamaan (1) menyatakan bahwa kelembapan relatif adalah memodelkan e dan bukan RH.
rasio, dan Gambar A.1 memperlihatkan apa arti pernyataan itu
pada data yang sebenarnya. Ketiga panel memuat sepuluh hari Namun panel (c) juga memperingatkan bahwa
yang sama. penyederhanaan yang paling menggoda tidak berlaku. e
memang lebih tenang daripada RH, tetapi ia tidak konstan di
dalam satu hari: simpangan bakunya di dalam hari 2,56 hPa
terhadap 2,91 hPa antar-hari. Pendekatan “satu tingkat
kelembapan per hari, lalu bagi dengan e(T)” karena itu
s
membuang hampir separuh sinyal sejak awal, dan Bagian III-B
mengukur harganya sebagai RMSE 8,37.
B. Proksi Titik Embun Bebas-Parameter
Persamaan (4) menduga kelembapan relatif dari suhu saja,
tanpa satu pun parameter yang dipasang pada data. Gambar A.2
memperlihatkan seberapa jauh dugaan sepolos itu membawa
kita.
Gambar A.1. Dekomposisi Persamaan (1) pada sepuluh hari yang sama.
Ayunan tajam pada (a) berasal dari (b); (c) bergerak jauh lebih lambat.
Gambar A.2. Penduga Persamaan (4) tanpa satu pun parameter yang dipasang. (a) Sebaran gabungan terhadap target, garis putus-putus adalah identitas. (b) Kedua
deret berdampingan pada sepuluh hari; proksi menangkap fase dan sebagian besar amplitudo, dan meleset terutama pada tingkat hariannya.
Panel (a) adalah sebaran gabungan penduga terhadap target Panel (b) menempatkan kedua deret berdampingan pada
pada seluruh baris latih. Korelasinya 0,908 dan RMSE sepuluh hari. Bacaan yang penting ada pada pemisahan bentuk
mentahnya 9,1 %RH, dicapai tanpa pelatihan apa pun. Titik-titik dan tingkat: fase dan sebagian besar amplitudo diurnal sudah
berkumpul rapat di sekitar garis identitas pada rentang benar, dan yang meleset adalah tingkat hariannya. Pola
menengah dan melebar di kedua ujung, yang wajar: pada RH kesalahan itu bertahan sampai ke model akhir, dan Bagian VI-C
tinggi udara mendekati jenuh sehingga proksi menabrak langit- mengukurnya sebagai 39 % galat yang berupa offset per hari.
langit, sedangkan pada RH rendah minimum harian bukan lagi
Dua konsekuensi mengalir ke rekayasa fitur. Karena
pendekatan titik embun yang baik karena udara tidak pernah
penduga terbaik yang tersedia secara cuma-cuma dibangun dari
cukup dingin untuk mengembun.
statistik urutan atas suhu, blok fitur terpenting pada Bagian IV-

B seluruhnya berupa statistik urutan atas suhu dan bukan atas transisi cepat yang asli. Ventilasi yang terbuka dan awan yang
kelembapan. Dan karena kualitas penduga bergantung pada lewat menghasilkan lompatan tajam yang nyata, dan lompatan
jendela tempat minimum diambil, versinya dihitung pada tiga itu justru informatif bagi model.
jendela bergulir, yaitu 18 jam, 48 jam, dan 96 jam, sehingga
D. Audit Dukungan per Kanal
model memperoleh tiga pandangan terhadap massa udara yang
sama pada tiga skala waktu. Bagian III-E melaporkan bahwa 13 kanal kehilangan lebih
dari sepertiga sebaran latihnya di jendela uji. Gambar A.4
C. Despiking Hampel pada Penggal Terburuk
memuat auditnya per kolom, sebagai rasio simpangan baku uji
Bagian IV-A melaporkan efek penapis Hampel sebagai terhadap simpangan baku latih.
angka; Gambar A.3 memperlihatkan bentuknya pada penggal
dua minggu dengan penolakan terpadat.
Gambar A.3. Penapis Hampel pada penggal dengan penolakan terpadat. Empat
dari 16 nilai yang ditolak berada di jendela ini; transisi diurnal yang asli tidak Gambar A.4. Rasio simpangan baku uji terhadap latih untuk setiap kanal
tersentuh. eksogen. Ketiga kolom water_volume_* benar-benar konstan di jendela uji,
sehingga rasionya nol.
TABEL A.I. EFEK DESPIKING HAMPEL PADA AIR_TEMPERATURE
Ukuran Sebelum Sesudah Kolom yang rasionya mendekati satu berperilaku sama di
sd residu tinggalkan-satu 2,715 0,515
kedua belahan dan aman dipakai. Yang mendekati nol runtuh.
sd robus residu tinggalkan-satu 0,472 0,408
Ketiga kolom water_volume_* benar-benar konstan di
ekskursi residu > 2,5 °C 57 5
jendela uji sehingga rasionya persis nol, karena irigasi berhenti
… di antaranya di jendela uji 5 0
sepanjang periode itu. Blok probe tanah mengikuti, sebab
kelembapan dan konduktivitas tanah berhenti berfluktuasi
nilai < 5 °C atau > 45 °C 16 0
begitu tidak ada air yang masuk.
nilai yang benar-benar diubah – 16 (0,49 %)
Dua keputusan di badan naskah bersandar pada gambar ini.
Blok tanah dan irigasi dibuang seluruhnya dari matriks fitur,
Empat dari 16 nilai di luar rentang 5–45 °C berada di jendela
karena pohon yang dilatih pada rezim irigasi aktif akan
ini, dan ketiganya berdiri sebagai paku tunggal setinggi 20
mengekstrapolasi ke daun yang rezimnya sudah tidak ada di
sampai 35 °C di atas deret yang median hariannya 27 °C. Paku
jendela uji. Dan anggota linear diperlakukan dengan hati-hati,
setinggi itu bukan cuaca. Yang perlu diperhatikan justru bagian
karena model linear mengekstrapolasi tanpa batas ke luar
yang tidak berubah: seluruh transisi diurnal yang asli, termasuk
dukungan; salah satu di antaranya akhirnya dibuang dari blend
kenaikan pagi yang curam dan lembah malam yang dalam,
justru karena alasan ini.
dilewati penapis tanpa disentuh.
E. Katalog Blok Fitur
Itulah yang dikejar oleh dua pilihan pada Persamaan (7).
Skala robusnya diambil dari IQR bergulir sepanjang 289 titik, Bagian IV-B menerangkan logika kelima blok fitur; Tabel
sekitar enam hari, sehingga penggal yang kebetulan tenang tidak A.II memerinci isinya kolom per kolom beserta pertanyaan fisis
membuat setiap riak kecil ditandai sebagai pencilan. Dan yang dijawab masing-masing.
ambangnya sengaja longgar pada k = 6, karena yang harus
dibuang adalah ekskursi yang secara fisis mustahil, bukan
TABEL A.II. LIMA BLOK FITUR DAN PERTANYAAN FISIS YANG DIJAWABNYA
Blok Isi Pertanyaan fisis
dasar
l
±
e
2
v e
j;
l
k
se
e
n
m
s
i
o
r
r
in
;
g
re
a
r
n
a
;
t a
h a
te
rm
rp
o
u
n
s
i
a
k
t 1
ja
j
m
/
-
6
h a
j
r
/
i ;
2
e
4
s (
j
T
;
)
a
;
n
s
o
il
m
an
a
g
li
s
te
u
r
h
h
u
a
–
d
t
a
a
p
n a
r
h
er
;
a
i
t
n
a
d
i
e
t
k
u
s
; s
a
d
g r
6
o n
j;
o
g
m
e
i
s eran
keadaan sesaat dan konteks lokalnya pada tiga skala waktu
tmin min / maks / rentang bergulir 18 j / 48 j / 96 j atas suhu, dan 100·es(Tmin)/es(T) proksi titik embun bebas-parameter, Persamaan (4)
tend tendensi tekanan 24 j dan 48 j, sd tekanan, tendensi CO₂ 24 j rezim sinoptik: tekanan turun mendahului adveksi lembap
ordstat min / maks / rentang CO₂ 9 j dan 24 j CO₂ sebagai penjejak laju ventilasi
qblock persentil 5 dan 95 bergulir atas suhu dan CO₂, plus RH-proksi dari persentil-5
m
let
i
a
n
k
im
m
u
a
m
ss
k
a
e
d
ra
in
s
g
m
in
e
,
l a
d
p
a
o
n
r
c
k
e
a
l
n
a h
s a
k
tu
ed
s
u
a
a
m
n
p
y
e
a
l
a
t
d
e
a
rd
la
in
h
g
s
i
i
n
n
;
y
p
a
e
l
r
t
s
e
e
r
n
se
ti
n
l-
d
5
ir
m
i
elaporkan
Yang perlu diperhatikan pada tabel ini adalah kolom contoh paling jelas. Minimum keras dan persentil-5 atas jendela
terakhir. Setiap blok masuk karena ada satu pertanyaan fisis yang sama tampak seperti dua versi besaran yang sama, tetapi
yang ingin dijawab, dan pertanyaan itulah yang menentukan yang pertama melaporkan satu sampel terdingin sedangkan yang
bentuk operatornya, bukan sebaliknya. Blok qblock adalah kedua melaporkan letak massa dinginnya, dan celah di antara

keduanya adalah sinyal tersendiri tentang seberapa panjang ekor F. Struktur Diurnal Kanal Iklim Mikro
dingin malam itu.
Gambar A.5 memuat klimatologi diurnal ketiga kanal iklim
mikro yang cepat, dirata-ratakan atas seluruh baris latih dengan
pita ±1 simpangan baku.
Gambar A.5. Klimatologi diurnal pada baris latih: rerata per jam-hari dengan pita ±1 simpangan baku. RH dan suhu berlawanan fase; CO₂ berpuncak bersama RH
menjelang subuh karena keduanya menjejak lapisan batas malam yang sama.
Tiga hal terbaca. Jam-hari saja menjelaskan 62,8 %
ragam target, dengan amplitudo rerata harian 41,13 %RH
terhadap simpangan baku keseluruhan 18,00 %RH, jadi hampir
seluruh ragam target adalah ayunan harian yang sama, berulang.
RH dan suhu adalah bayangan cermin, berkorelasi −0,871,
konsekuensi langsung Persamaan (1). Dan CO₂ berpuncak
menjelang subuh, tepat ketika RH berpuncak, karena keduanya
menjejak besaran fisis yang sama: lapisan batas malam yang
dangkal dan tenang memerangkap uap air sekaligus CO₂
respirasi. Itulah alasan blok fitur ordstat memakai statistik
urutan CO₂ sebagai penjejak laju ventilasi.
Konsekuensi praktisnya menyangkut rekayasa fitur. Waktu-
hari masuk sebagai harmonik sinus/kosinus yang kontinu, bukan
sebagai penanda kategorik per setengah jam. Penanda kategorik
memberi model 48 parameter bebas yang dapat menghafal hari
tertentu di dalam data latih; harmonik memaksanya mempelajari
bentuk yang mulus dan berlaku umum. Gambar A.6. Sembilan lipatan titik-asal bergulir. Baris paling bawah adalah
tugas yang sebenarnya; kemiripan bentuknya dengan kesembilan lipatan di
G. Protokol Validasi Titik-Asal Bergulir atasnya adalah alasan protokol ini dipilih.
Gambar A.6 menggambarkan protokol validasi yang dipakai
Baris paling bawah adalah tugas yang sebenarnya, dan
di seluruh tulisan ini. Setiap batang adalah satu lipatan: bagian
kemiripan bentuknya dengan sembilan baris di atasnya adalah
gelap adalah data latihnya, bagian terang adalah 15 hari
seluruh alasan protokol ini dipilih. Setiap lipatan meniru
berikutnya yang dinilai. Titik potongnya bergerak maju dua hari
hubungan yang sama antara data latih dan blok yang dinilai:
setiap lipatan, dengan minimum 30 hari data latih, sehingga
kontigu, maju, dan tanpa satu pun label di sisi yang dinilai.
terbentuk sembilan lipatan.
Bandingkan dengan lipatan acak. Dengan autokorelasi 0,979
pada lag satu, lipatan acak menempatkan tetangga langsung
sebuah baris di sisi latih, sehingga skornya mengukur seberapa
baik model menginterpolasi di antara dua titik yang sudah
diketahui. Itu persoalan yang jauh lebih mudah, dan bukan
persoalan yang dinilai kompetisi.
Perhatikan juga bahwa lipatan di sini tumpang tindih. Itu
disengaja, karena 61 hari data tidak cukup untuk sembilan blok
yang saling lepas, tetapi ia berarti kesembilan skornya
berkorelasi dan tidak boleh diperlakukan sebagai sembilan
pengamatan bebas. Bagian VI-D memperlihatkan akibatnya
secara kuantitatif: blok maju kami melebih-lebihkan besaran
galat tingkat-level 2 sampai 6 kali.
H. Katalog Kegagalan Selengkapnya
Bagian VI-E meringkas katalog kegagalan; Tabel A.III
memuat versi lengkapnya untuk arah yang ditolak berdasarkan
pengukuran internal. Setiap baris diukur pada protokol maju

yang sama dengan yang menilai konfigurasi yang akhirnya
dikapalkan, sehingga angkanya sebanding satu sama lain.
TABEL A.III.  ARAH YANG DITOLAK BERDASARKAN PENGUKURAN INTERNAL
|     |      |     |     |               |     |     |     |     |           |     |     |     |
| --- | ---- | --- | --- | ------------- | --- | --- | --- | --- | --------- | --- | --- | --- |
|     | Arah |     |     | Hasil terukur |     |     |     |     | Pelajaran |     |     |     |
Analog / tetangga terdekat: cocokkan keadaan sensor, transpor  pasangan analog berbagi RH (r = 0,81) jauh lebih baik daripada berbagi
RH lewat rasio es   tekanan uap (r = 0,47)   kemiripan sensor tidak menyiratkan kemiripan massa udara
Prior kelengkungan pada e: penalti selisih-kedua bebas-   lintasan model sudah 2× lebih mulus daripada kebenaran (rasio 0,47)   penalti kehalusan mendorong ke arah yang sudah salah
parameter
  model 24 j mencapai RMSE 7,76 vs garis dasar 11,46, tetapi level stack  kendala hanya membantu kalau ia lebih baik daripada yang
| Horizon increment lebih panjang: 6 j, 12 j, 24 j |     |                                 |     |     |     |     |                |     |     |     |     |     |
| ------------------------------------------------ | --- | ------------------------------- | --- | --- | --- | --- | -------------- | --- | --- | --- | --- | --- |
|                                                  |     | sudah menyiratkannya lebih baik |     |     |     |     | sudah tersirat |     |     |     |     |     |
Reparameterisasi termodinamika increment   sinyal menyusut 3,54 → 2,23, galat tetap 1,80 → 1,80   pembelajar sudah menangani bagian bentuk-tertutup
|     |     |     |     |     |     |     | dengan sempurna                                            |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | ---------------------------------------------------------- | --- | --- | --- | --- | --- |
|     |     |     |     |     |     |     |   kemiringan tingkat-hari tidak dapat diduga dari sejarah  |     |     |     |     |     |
Ekspansi level harian ke kemiringan terpasang dugaan dan realisasi tidak berkorelasi (13–23 hari sampel); −0,006 saja
sependek ini
2.933 baris terlalu sedikit untuk keduanya; representasi
Jaring saraf, kernel, dan model urutan: MLP 128×64, kernel    8,75 dan 16,45 RMSE solo; model urutan membawa informasi level tetapi    urutan menemukan dinamika, tetapi bukan jenis yang
ridge RBF, ridge atas bank konvolusi acak sepanjang 193 titik bukan informasi perubahan, dan lebih buruk di keenam blok
dibutuhkan penyelesai
  hanya n_estimators yang memindahkan skor; kombinasi dua pemenang  urutan pada layar penyaringan adalah deskripsi, bukan
Penyapuan hiperparameter hbt, 11 titik di sekitar incumbent tunggal gagal, +0,012 dan +0,072   mekanisme yang dapat dikomposisikan
Kolom ketiga adalah yang paling berharga. Ia menyebut  TABEL A.IV.  TANGGA SKOR PAPAN PERINGKAT PUBLIK,
pelajaran yang dibawa kegagalan itu, dan bukan hanya mencatat  TERMASUK YANG MERUGIKAN
|     |     |     |     |     |     |     |     |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
bahwa arahnya buntu, dan beberapa di antaranya membentuk  Perubahan RMSE Δ
keputusan lain di naskah ini. Temuan bahwa lintasan model  dasar: 5 anggota, blending NNLS   3,04904   –
sudah  dua  kali  lebih  mulus  daripada  kebenaran,  misalnya,  bobot blend per pita waktu-hari   3,02942   −0,01962
adalah alasan rekonsiliasi lintasan di Bagian V-D dirancang
|     |     |     |     |     | koreksi bias diurnal per pita |     |     |     |     | 3,00589 | −0,02353 |     |
| --- | --- | --- | --- | --- | ----------------------------- | --- | --- | --- | --- | ------- | -------- | --- |
mengikat  prediksi  perubahan  yang  dipelajari  dan  bukan
|                                              |     |     |     |     | kemiringan dispersi + fitur terpotong |     |     |     |     | 3,28564   | +0,23700 |     |
| -------------------------------------------- | --- | --- | --- | --- | ------------------------------------- | --- | --- | --- | --- | --------- | -------- | --- |
| memasang penalti kehalusan bebas-parameter.  |     |     |     |     |                                       |     |     |     |     |           |          |     |
|                                              |     |     |     |     | anggota LightGBM L2 keenam            |     |     |     |     | 3,02586   | +0,00300 |     |
|                                              |     |     |     |     | lantai penyusutan NNLS dilepas        |     |     |     |     | 3,05372   | +0,02786 |     |
Gambar 7 di badan naskah menggambarkan tangga skor
|     |     |     |     |     | rekonsiliasi lintasan increment |     |     |     |     | 2,86595   | −0,15991 |     |
| --- | --- | --- | --- | --- | ------------------------------- | --- | --- | --- | --- | --------- | -------- | --- |
papan peringkat publik. Tabel A.IV memuat angkanya lengkap,
|     |     |     |     |     |     |     |     |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
termasuk empat konfigurasi yang justru merugikan dan tetap  tiga penghalusan increment sekaligus 2,93028 +0,06433
|     |     |     |     |     |     |     |     |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
kami laporkan. Setiap baris adalah satu berkas submission yang  anggota ridge dibuang 2,85383 −0,01212
|     |     |     |     |     |                                   |     |     |     |     |         |          |     |
| --- | --- | --- | --- | --- | --------------------------------- | --- | --- | --- | --- | ------- | -------- | --- |
|     |     |     |     |     | bentuk pita menggantikan harmonik |     |     |     |     | 2,84953 | −0,00430 |     |
benar-benar dikirim, dan skornya adalah yang dikembalikan
|     |     |     |     |     | de-bias level anggota cat |     |     |     |     | 2,82744   | −0,02209 |     |
| --- | --- | --- | --- | --- | ------------------------- | --- | --- | --- | --- | --------- | -------- | --- |
papan peringkat atas berkas itu, bukan dugaan internal.
|     |     |     |     |     | kemiringan dispersi, kekuatan ¼ |     |     |     |     | 2,83299   | +0,00555 |     |
| --- | --- | --- | --- | --- | ------------------------------- | --- | --- | --- | --- | --------- | -------- | --- |

Tabel A.V memerinci kelompok kegagalan yang paling
instruktif, yang di badan naskah hanya diringkas pada Bagian
VI-E: perubahan yang bukti internalnya kuat, sebagian bahkan
|     |     |     |     |     | menang  | di  seluruh  | lipatan,  | dan  | tetap  merugikan  |     | di  | papan  |
| --- | --- | --- | --- | --- | ------- | ------------ | --------- | ---- | ----------------- | --- | --- | ------ |
peringkat.
TABEL A.V.  PERUBAHAN YANG DITOLAK PAPAN PERINGKAT SETELAH LOLOS VALIDASI INTERNAL
|     |     |     |     |     |     |     |     |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
Perubahan Bukti internal Mengapa ia tetap salah Δ papan peringkat
sebaran prediksi uji (18,8) berada di atas setiap lipatan validasi silang
kemiringan kalibrasi dispersi (versi awal)   menang di 13 /13 lipatan, tiga keluarga lipatan  (16,2–17,5), sehingga pemadatan yang hendak dibatalkan tidak ada di  +0,23700
|     |     | yang berbeda   |     |     |     |     |     |     |     |     |     |     |
| --- | --- | -------------- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
jendela uji
    bersarangnya berbagi label antar-lipatan; pada protokol yang diperbaiki
membuang lantai penyusutan NNLS −0,058 pada validasi bersarang responsnya monoton ke arah sebaliknya   +0,02786
|     |     |     |     |     |     |     |     |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
koreksi pita-rentang-lebar mekanisme terukur, arah benar pada blok maju biasnya membalik tanda di jendela uji +0,12600
penghalusan increment: de-shrink, prior  tiga-tiganya diadopsi secara internal   ketiganya menyetel komponen yang sudah terkalibrasi; nol dari tiga  +0,06433
| fisis, lag tambahan |     |                                               |     |     | menang   |     |     |     |     |     |     |     |
| ------------------- | --- | --------------------------------------------- | --- | --- | -------- | --- | --- | --- | --- | --- | --- | --- |
|                     |     |   membaik di keenam blok maju, pada dua blok  |     |     |          |     |     |     |     |     |     |     |
kapasitas hbt dinaikkan ke 2.400 pohon   ditolak pada gerbang tekanan luar-rezim sebelum dikapalkan tidak dikapalkan
seed
Kolom  ketiga  adalah  yang  paling  berharga,  karena  ia  perbaikan  blending  terbaik  kami  dan  satu  setengah  kali
menyebut  mekanisme  kegagalannya  dan  bukan  sekadar  perbaikan  terbesar  kami.  Sebabnya  dapat  diperiksa  tanpa
mencatat  bahwa  skornya  memburuk.  Polanya  sama  pada  papan  peringkat  sama  sekali:  simpangan  baku  prediksi
keempat baris pertama: besaran yang dikoreksi memang ada di  jendela uji 18,8, sementara setiap lipatan validasi silang berada
blok validasi, tetapi tidak ada di jendela uji, atau ada dengan  di 16,2–17,5. Pemadatan amplitudo yang hendak dibatalkan
tanda yang berlawanan. Validasi silang mengukur besaran itu  koreksi  itu  tidak  ada  di  jendela  uji.  Satu  perbandingan
dengan benar di tempat ia diukur; yang salah adalah anggapan  simpangan baku sudah cukup untuk menolaknya, dan kami tidak
bahwa besaran yang sama menunggu di jendela uji.  melakukannya.
Baris pertama layak dibaca dua kali. Kemiringan kalibrasi  I.  Kontrak Reproduksibilitas
dispersi menang di 13 dari 13 lipatan pada tiga keluarga lipatan  Juknis pasal 2.e menjadikan ketidaksesuaian antara skor
yang dibangun berbeda-beda, lalu kalah +0,237. Itu kerugian  notebook dan skor Kaggle sebagai alasan diskualifikasi, bukan
terbesar yang pernah kami alami, hampir sepuluh kali lipat

pengurangan  nilai.  Tabel  A.VI  memuat  seluruh  butir  yang  lintas mesin: menjalankan notebook pada Python, NumPy, dan
membuat kesesuaian itu dapat diperiksa pihak ketiga tanpa perlu  SciPy yang lebih baru, dengan versi LightGBM dan CatBoost
mempercayai  kami:  jalankan  notebook,  ambil  berkas  yang  yang persis sama, menggeser prediksi sebesar RMS 0,29 %RH
ditulisnya, unggah ke Kaggle, dan bandingkan skornya dengan  dengan maksimum 0,87 %RH. Penyebabnya dapat dipersempit:
yang tercantum di sana.  audit residu, klimatologi, dan kedua anggota linear reproduksi
sampai digit terakhir, sedangkan ketiga anggota pohon bergeser,
TABEL A.VI.  KONTRAK REPRODUKSIBILITAS
|     |     |     |     |     |     |     |     | karena  | kedua  | pustaka  | itu  | menyusun  histogramnya  |     | dengan  |
| --- | --- | --- | --- | --- | --- | --- | --- | ------- | ------ | -------- | ---- | ----------------------- | --- | ------- |
|     |     |     |     |     |     |     |     |         |        |          |      |                         |     |         |
Butir Nilai penjumlahan yang bergantung urutan thread. Pemeriksa yang
  gagal  karena  derau  sebesar  itu  akan  mengubah  selisih  tak
| Sumber keacakan |     |     |     |     |     |     |     |     |     |     |     |     |     |     |
| --------------- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
berpengaruh menjadi notebook yang berhenti dengan galat,
| seed OOF (dirata-ratakan di dalam validasi    |     |     |     | 0, 1, 2   |     |     |     |     |     |     |     |     |     |     |
| --------------------------------------------- | --- | --- | --- | --------- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
silang) padahal  juknis  2.e  justru  menuntut  eksekusi  tanpa  galat.
|     |     |     |     |     |     |     |     |     |     |     |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
seed pemasangan akhir 0, 1, 2, 3, 4 Notebook karena itu hanya memeriksa bentuk berkasnya dan
seed dasar model increment   20260905, 5 seed   mencetak  md5  beserta  skor  publiknya;  kesesuaian  skor
RNG global yang dipakai jalur kode mana  diperiksa dengan mengunggah berkas itu ke Kaggle.
|     |     |     |     | tidak ada |     |     |     |     |     |     |     |     |     |     |
| --- | --- | --- | --- | --------- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
pun
Masukan: hanya tiga berkas resmi     J.  Audit Seluruh Kanal Eksogen

train.csv (494.807 bait)   efab54394fee7848983b3f27f44c2489 Tabel A.VII merangkum anatomi kedua belahan dataset
test.csv (117.567 bait)   e339e5aaa4c42bd8a948b9c2226951ed   berdampingan.  Ia  dirujuk  dari  Bagian  II-A  dan  sengaja
sample_submission.csv (18.373 bait)     ditempatkan di sini bersama audit per kanal, karena keduanya
7338feec8ef625b60f448afe27d2fd8a
menjawab pertanyaan yang sama pada dua tingkat kerincian.
| data eksternal · model pretrained · kode  |     |     |     | tidak ada · tidak ada · tidak ada |     |     |     |     |     |     |     |     |     |     |
| ----------------------------------------- | --- | --- | --- | --------------------------------- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
eksternal
|     |     |     |     |     |     |     |     |     |     | TABEL A.VII.  ANATOMI DATASET  |     |     |     |     |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | ------------------------------ | --- | --- | --- | --- |
Kesesuaian skor (juknis 2.e)
|                                        |     |     |     |                                           |     |     |     |               | Butir  |     |                    | Latih      |                    | Uji        |
| -------------------------------------- | --- | --- | --- | ----------------------------------------- | --- | --- | --- | ------------- | ------ | --- | ------------------ | ---------- | ------------------ | ---------- |
| md5 berkas yang di-submit ke Kaggle    |     |     |     | 70666a36066bb25b03ee4dce1b7fedcd          |     |     |     |               |        |     |                    |            |                    |            |
|                                        |     |     |     |                                           |     |     |     | Jumlah baris  |        |     |                    | 2.933      |                    | 734        |
| md5 berkas yang ditulis ulang notebook |     |     |     | a4658c492e2e16b951466d144d9226bb          |     |     |     |               |        |     |                    |            |                    |            |
|                                        |     |     |     |                                           |     |     |     | Awal          |        |     | 29 Jun 2023 06.00  |            | 29 Agu 2023 15.00  |            |
| skor publik terkait                    |     |     |     | 2,82744                                   |     |     |     |               |        |     |                    |            |                    |            |
|                                        |     |     |     |                                           |     |     |     | Akhir         |        |     | 29 Agu 2023 14.30  |            | 13 Sep 2023 21.30  |            |
| cara memeriksa                         |     |     |     | unggah berkas keluaran notebook ke Kaggle |     |     |     |               |        |     |                    |            |                    |            |
|                                        |     |     |     |                                           |     |     |     | Rentang       |        |     |                    | 61,4 hari  |                    | 15,3 hari  |
|                                        |     |     |     |                                           |     |     |     |               |        |     |                    |            |                    |            |
Lingkungan eksekusi
|                                   |     |     |     |                                            |     |     |     | Selang waktu              |     |     | 30 mnt, 1 lompatan 7 j  |             | 30 mnt, sempurna  |             |
| --------------------------------- | --- | --- | --- | ------------------------------------------ | --- | --- | --- | ------------------------- | --- | --- | ----------------------- | ----------- | ----------------- | ----------- |
| Python · NumPy · pandas           |     |     |     | 3.11.6 · 2.4.6 · 2.2.3                     |     |     |     |                           |     |     |                         |             |                   |             |
|                                   |     |     |     |                                            |     |     |     | Kanal eksogen             |     |     |                         | 24          |                   | 24          |
| scikit-learn · SciPy · Matplotlib |     |     |     | 1.9.0 · 1.17.1 · 3.11.1                    |     |     |     |                           |     |     |                         |             |                   |             |
|                                   |     |     |     |                                            |     |     |     | Kolom target              |     |     |                         | ada         |                   | tidak ada   |
|                                   |     |     |     |                                            |     |     |     |                           |     |     |                         |             |                   |             |
| LightGBM · CatBoost               |     |     |     | 4.7.0 · 1.2.10                             |     |     |     |                           |     |     |                         |             |                   |             |
|                                   |     |     |     |                                            |     |     |     | Nilai hilang, kanal inti  |     |     |                         | 9,0–10,8 %  |                   | 8,6–17,6 %  |
| runtime notebook end-to-end       |     |     |     | ≈ 9 menit, CPU 8 inti                      |     |     |     |                           |     |     |                         |             |                   |             |
|                                   |     |     |     |                                            |     |     |     | env_battery hilang        |     |     |                         | 98,0 %      |                   | 98,0 %      |
|                                   |     |     |     | terikat lingkungan di atas; anggota pohon  |     |     |     |                           |     |     |                         |             |                   |             |
kesamaan sampai digit terakhir bergantung urutan thread     bervariasi  konstan
water_volume_*

Mengapa md5 berkas bukan kriterianya. Kami mula-
Baris yang paling menentukan adalah tiga yang terakhir.
mula memakai md5 berkas mentah sebagai pemeriksa internal,
Nilai hilang berada pada tingkat yang sama di kedua belahan dan
dan ia gagal pada eksekusi penuh pertama. Penyebabnya satu  tersebar,  bukan  berbentuk  blok  mati  alat,  sehingga
baris yang berbeda sebesar 3,55 × 10⁻¹⁵: penyelesai jarang pada  penambalannya tidak mengarang rezim. env_battery praktis
Persamaan (10) tidak reproducible sampai bit terakhir antar-
kosong di keduanya dan seluruh nilai yang ada bernilai 100,
| jalankan  | karena  | penjadwalan  |     | pustaka  | aljabar  |     | linear  di  |           |     |        |          |            |      |            |
| --------- | ------- | ------------ | --- | -------- | -------- | --- | ----------- | --------- | --- | ------ | -------- | ---------- | ---- | ---------- |
|           |         |              |     |          |          |     |             | sehingga  | ia  | tidak  | membawa  | informasi  | apa  | pun.  Dan  |
bawahnya. Perbedaan sebesar itu tidak dapat menggeser skor
water_volume_* yang bervariasi di latih tetapi konstan di uji
pada presisi mana pun yang dilaporkan Kaggle, tetapi cukup
adalah sinyal paling awal bahwa jendela uji berada pada rezim
untuk mengubah satu karakter teks CSV dan karenanya md5  irigasi yang berbeda, jauh sebelum audit dukungan di Lampiran
berkasnya. Kedua nilai md5 karena itu dicantumkan apa adanya
D mengukurnya.
di Tabel A.VI, termasuk fakta bahwa keduanya berbeda.
|      |          |     |           |        |            |     |          | Tabel  | A.VIII  | memuat  |     | audit  lengkap  | seluruh  | 24  kanal  |
| ---- | -------- | --- | --------- | ------ | ---------- | --- | -------- | ------ | ------- | ------- | --- | --------------- | -------- | ---------- |
| Dan  | mengapa  |     | notebook  | tidak  | memeriksa  |     | dirinya  |        |         |         |     |                 |          |            |
eksogen, yang di badan naskah hanya diringkas sebagai Gambar
sendiri. Kami sempat memakai digest atas nilai prediksi yang  A.4. Kolom terakhir menyatakan apakah kanal itu masuk ke
| dibulatkan  | ke  | enam  | desimal,  | yang  | kebal  | terhadap  | derau  |     |     |     |     |     |     |     |
| ----------- | --- | ----- | --------- | ----- | ------ | --------- | ------ | --- | --- | --- | --- | --- | --- | --- |
matriks fitur akhir.
penyelesai jarang. Ia cocok di mesin yang sama, tetapi tidak

TABEL A.VIII.  AUDIT KELENGKAPAN DAN DUKUNGAN SELURUH 24 KANAL EKSOGEN
Kanal   Hilang latih   Hilang uji   Rerata latih   Rerata uji   sd uji / sd latih   Dipakai
|     |                 |     |     |     |     |        |     |        |         |         |             |
| --- | --------------- | --- | --- | --- | --- | ------ | --- | ------ | ------- | ------- | ----------- |
|     | env_id          |     |     |     |     | 0 %    |     | 0 %    | 95732,5 | 190968  | 0,26 tidak  |
|     |                 |     |     |     |     |        |     |        |         |         |             |
|     | co2             |     |     |     |     | 9,3 %  |     | 8,6 %  | 481,49  | 478,55  | 0,88 ya     |
|     |                 |     |     |     |     |        |     |        |         |         |             |
|     | pressure        |     |     |     |     | 9,9 %  |     | 9,4 %  | 1008,88 | 1013,28 | 0,87 ya     |
|     |                 |     |     |     |     |        |     |        |         |         |             |
|     | air_temperature |     |     |     |     | 10,4 % |     | 9,8 %  | 27,56   | 24,58   | 1,09 ya     |
|     | env_battery     |     |     |     |     | 98 %   |     | 98 %   | 100     | 100     | 0   tidak   |
soil_ec_line1   9,3 %   12 %   361,23   228,98   0,66   tidak
|     |                     |     |     |     |     |        |     |        |        |        |            |
| --- | ------------------- | --- | --- | --- | --- | ------ | --- | ------ | ------ | ------ | ---------- |
|     | soil_humidity_line1 |     |     |     |     | 10,3 % |     | 11,2 % | 26,32  | 24,54  | 0,59 tidak |
|     |                     |     |     |     |     |        |     |        |        |        |            |
|     | soil_temp_line1     |     |     |     |     | 9,8 %  |     | 11,7 % | 23,83  | 21,56  | 0,48 tidak |
|     |                     |     |     |     |     |        |     |        |        |        |            |
|     | soil_ec_line2       |     |     |     |     | 9,7 %  |     | 10,6 % | 408,42 | 182,14 | 0,24 tidak |

soil_humidity_line2 9 %   8,7 %   26,85   20,28   0,21   tidak
soil_temp_line2   9,8 %   11,2 %   24,7   22,24   0,44   tidak
|     |     |     |     |     |     | 10,8 %   |     | 11 %   | 481,81   | 225,4   | 0,23   tidak   |
| --- | --- | --- | --- | --- | --- | -------- | --- | ------ | -------- | ------- | -------------- |
soil_ec_line3
|     |                     |     |     |     |     |        |     |       |         |       |            |
| --- | ------------------- | --- | --- | --- | --- | ------ | --- | ----- | ------- | ----- | ---------- |
|     | soil_humidity_line3 |     |     |     |     | 9,4 %  |     | 11 %  | 26,9    | 21,73 | 0,15 tidak |
|     |                     |     |     |     |     |        |     |       |         |       |            |
|     | soil_temp_line3     |     |     |     |     | 10,2 % |     | 9,8 % | 24,78   | 22,58 | 0,46 tidak |
|     |                     |     |     |     |     |        |     |       |         |       |            |
|     | water_volume_line1  |     |     |     |     | 9,7 %  |     | 9,8 % | 19552,4 | 38280 | 0 tidak    |
water_volume_line2   9,5 %   10,2 %   13258,4   25028   0   tidak
water_volume_line3   9,3 %   10,1 %   8618,84   15094   0   tidak
|     |                        |     |     |     |     |        |     |        |        |       |         |
| --- | ---------------------- | --- | --- | --- | --- | ------ | --- | ------ | ------ | ----- | ------- |
|     | gdd                    |     |     |     |     | 10,2 % |     | 15,5 % | 405,53 | 841,7 | 0,14 ya |
|     |                        |     |     |     |     |        |     |        |        |       |         |
|     | standard_day_degree    |     |     |     |     | 9,9 %  |     | 15,4 % | 17,57  | 15,53 | 0,69 ya |
|     |                        |     |     |     |     |        |     |        |        |       |         |
|     | daily_mean_temperature |     |     |     |     | 9,6 %  |     | 16,9 % | 27,53  | 25,4  | 0,69 ya |

daily_max_above_Tbase 10,3 %   17,4 %   26,74   25,92   0,76   ya
|     | daily_max |     |     |     |     | 9,4 %   |     | 17,6 %   | 36,78   | 35,85   | 0,75   ya   |
| --- | --------- | --- | --- | --- | --- | ------- | --- | -------- | ------- | ------- | ----------- |
|     |           |     |     |     |     | 9,9 %   |     | 14,7 %   | 16,7    | 17,69   | 0,78   ya   |
daily_max_reduction
|     |               |     |     |     |     |        |     |      |       |      |         |
| --- | ------------- | --- | --- | --- | --- | ------ | --- | ---- | ----- | ---- | ------- |
|     | ontario_units |     |     |     |     | 10,4 % |     | 15 % | 26,36 | 24,2 | 0,61 ya |
Blok tanah dan irigasi runtuh. Ketiga water_volume_*
benar-benar konstan di jendela uji sehingga rasio simpangan
bakunya nol, dan probe tanah turun ke 0,15–0,66 kali sebaran
latihnya. Irigasi berhenti, atau pencatatannya berhenti, selama
jendela uji. Statistik bergulir dari blok ini karena itu berada jauh
di luar dukungan latih, dan pohon yang membacanya akan
mengekstrapolasi ke daun yang dipelajari pada rezim yang
sudah tidak ada.
|     | Dua  | kanal  | tidak  | membawa  | informasi  | sama  | sekali.  |     |     |     |     |
| --- | ---- | ------ | ------ | -------- | ---------- | ----- | -------- | --- | --- | --- | --- |
env_battery hilang pada 98 % baris dan seluruh nilai yang
| ada  | bernilai  | 100.  | env_id  | adalah  | pengenal  | rekaman  | yang  |     |     |     |     |
| ---- | --------- | ----- | ------- | ------- | --------- | -------- | ----- | --- | --- | --- | --- |
reratanya melonjak dari 95.732 di data latih menjadi 190.968 di
data uji; ia menandai penomoran berkas, bukan besaran fisis,
dan memasukkannya berarti memberi model penanda waktu
terselubung yang tidak berlaku di luar rentang ini.
Kanal yang dipertahankan bergeser, tetapi tetap punya
| dukungan.  |     | Suhu  | udara,  | CO₂,  | dan  | tekanan  | barometrik  |     |     |     |     |
| ---------- | --- | ----- | ------- | ----- | ---- | -------- | ----------- | --- | --- | --- | --- |
seluruhnya berada di rasio 0,87–1,09, jadi sebaran ujinya masih
| sebanding  |     | dengan  | sebaran  | latihnya  | meskipun  |     | rerata-nya  |     |     |     |     |
| ---------- | --- | ------- | -------- | --------- | --------- | --- | ----------- | --- | --- | --- | --- |
bergeser: suhu turun dari 27,56 °C ke 24,58 °C. Itu pergeseran
lokasi, bukan hilangnya dukungan, dan pergeseran lokasi dapat
ditangani model asalkan bentuk sebarannya bertahan. Indeks
agronomi berada di 0,61–0,78, batas yang masih dapat diterima,
dan blok itu tetap dipakai karena alasan di Bagian III-D: ia
memuat versi bersih dari suhu minimum harian, prediktor fisis
terkuat yang kami punya.
Perhatikan juga bahwa kelengkapan data justru memburuk
di jendela uji, khusus pada blok agronomi, dari sekitar 10 %
hilang menjadi 15–17,6 %. Karena blok itu konstan sepanjang
hari agronomi 22.00-ke-22.00, lubangnya dapat ditambal dari
baris lain di hari yang sama tanpa kehilangan informasi apa pun.
Itu salah satu alasan rekayasa balik di Bagian III-D bernilai
praktis dan bukan hanya menarik.