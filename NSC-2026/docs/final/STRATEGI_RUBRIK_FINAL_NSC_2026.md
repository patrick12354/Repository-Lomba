# Strategi rubrik Grand Final NSC 2026

Disusun 11 Oktober 2026 dari PDF yang diminta pengguna: **f15702c4-786c-4330-8f50-b340ce839074.pdf** di akar workspace.

Ketiga halaman dibaca; tabel rubrik diperiksa melalui render halaman 2. SHA-256 identik dengan salinan Downloads yang sebelumnya dibaca: D73A8B0AA7B5FDA6043086E1590F7550FFAE4408FF984BC5FAEC4E32C07E32E9. Tidak ada perubahan rubrik antar kedua berkas.

Dokumen ini melengkapi **SCRIPT_FINAL_DETECTIVE_NSC_2026.md**. Isi script tetap empat babak TKP–Suspect–Bukti–Pelaku; keputusan produksi mengikuti strategi di bawah.

## 1. Kontrak final yang harus dipenuhi

- Materi analisis/pemodelan yang dikerjakan pada penyisihan, §1.a.
- Susunan kreatif diperbolehkan, tetapi tetap sesuai ketentuan dan batas waktu.
- Presentasi **15 menit**, Q&A **24 menit**, §1.g.
- File **.pptx** paling lambat **17 Oktober 2026, 23.59 WIB**, §1.c.
- Nama: **NSC26-DS042_Heisenberg_PPT Grand Final Data Science.pptx**.
- Dilarang memakai atribut/identitas instansi dan menyebut asal instansi, §1.h–i.
- Juknis 3 halaman ini **tidak menentukan batas slide, rasio layar, durasi video, atau ukuran unggahan**. Rekomendasi teknis bukan aturan panitia. Cek informasi TM/LO untuk ketentuan tambahan.

## 2. Bobot total dan prioritas

| Rubrik resmi | Bobot internal | Kontribusi total |
|---|---:|---:|
| Presentasi: struktur dan keruntutan | 15% dari 60 | 9 |
| Penguasaan materi dan pemahaman data | 25% dari 60 | 15 |
| Ketepatan metode dan interpretasi hasil | 25% dari 60 | 15 |
| Visualisasi data dan penyampaian insight | 20% dari 60 | 12 |
| Waktu, intonasi, ekspresi, sikap | 15% dari 60 | 9 |
| Q&A: kejelasan, ketepatan, logika | 35% dari 40 | 14 |
| Q&A: penguasaan metode, data, hasil | 40% dari 40 | 16 |
| Q&A: pertanggungjawaban keputusan | 25% dari 40 | 10 |
| **Total** | | **100** |

**70 poin** terkait penguasaan data/metode, interpretasi, dan kualitas serta pertanggungjawaban jawaban: 15 + 15 + 14 + 16 + 10. Narasi detektif membantu mengantar bukti untuk aspek tersebut; ia bukan pengganti bukti.

## 3. Mengubah rubric menjadi perilaku yang dapat dinilai

| Kriteria | Yang harus terlihat/didengar | Implementasi konkret | Tanda belum siap |
|---|---|---|---|
| Struktur, 9 | Setiap temuan membawa keputusan berikutnya | Label babak konsisten; EDA 3–5 → peran model 6 → aturan 7 → kontrol 8 → residual 9 → video 10 → evaluation 11 → audit bias 12 → batas 13 → kesimpulan 14 | Slide dapat dipindah tanpa mengubah cerita |
| Pemahaman data, 15 | Tim memahami detail yang mengubah desain | Slide 3 audit selektif; 4 dua rekonstruksi indeks harian; 5 perubahan sebaran; A1 gap 7 jam; slide 2 kontrak eksogen | EDA hanya mengatakan “data dibersihkan” |
| Metode/interpretasi, 15 | Alasan, alternatif, pengujian, dan batas | Huber untuk masukan ekstrem; CatBoost untuk residual berbeda; NNLS dari OOF; kontrol acak pada 8; kontrol koreksi pada 12 | Nama metode tanpa alasan atau angka tanpa konteks |
| Visualisasi, 12 | Insight dapat ditemukan tanpa mencari-cari | Grafik dengan label temuan langsung; evidence/decision callout; satu exhibit; video mengungkap mekanisme baru | Screenshot padat, dekorasi lebih jelas dari bukti |
| Delivery, 9 | Presenter memandu pemahaman dan selesai tepat waktu | Slot 13:40; tiga jeda; maksimal dua perpindahan; satu angka utama diucapkan per temuan bila memungkinkan | Ucapan dipercepat untuk mengejar waktu |
| Q&A logika, 14 | Jawaban langsung, relevan, runtut | Kalimat pertama menjawab pertanyaan, lalu bukti, lalu batas | Mengulang semua isi paper sebelum menjawab |
| Q&A penguasaan, 16 | Kedua anggota mengerti instrumen dan setup | Bedakan CV/publik/OOF/audit maju; tahu target tiap anggota; A1–A8 terindeks | Satu anggota hanya mengerti UI/cerita |
| Q&A keputusan, 10 | Tim dapat mempertahankan pilihan dan mengakui tradeoff | Jelaskan baseline, kontrol, kandidat gagal, peran feedback publik, batas causal deployment | “Karena hasilnya paling bagus” menjadi satu-satunya alasan |

Tidak ada prediksi skor juri. Kesiapan ditentukan oleh bukti dan kemampuan menjelaskan, bukan checklist yang otomatis bernilai penuh.

## 4. Penajaman script utama

Tambahan ini sudah dimasukkan ke script utama:

1. **Slide 5 menuju 6:** dua sifat data menghasilkan kebutuhan model: sisa pembacaan ekstrem dan perubahan kondisi. Suspect mempunyai tugas, bukan sekadar nama.
2. **Slide 6 menuju 7:** “Kami memilih mereka dari karakter data; lalu menguji apakah setiap pilihan memang dibayar oleh hasil.”
3. **Slide 8:** kontrol acak dengan kapasitas sama menunjukkan manfaat struktur waktu, bukan hanya tambahan parameter.
4. **Slide 11:** bukti lebih baik pada perubahan 30 menit diukur pada baris yang sama; manfaat dua jam lebih kecil. Pisahkan RMSE perubahan, audit maju, dan publik.
5. **Slide 12:** kontrol arah salah dan anggota hampir tak bias menjaga koreksi tetap berbasis mekanisme.
6. **Slide 14:** 15,8% dibanding baseline kompeten pada protokol sama; publik 2,82744 merupakan konteks lain.

Untuk setiap slide analitis, beri penanda kecil **Temuan → Keputusan**. Untuk slide pengujian, gunakan **Dugaan → Pengujian → Hasil**. Bentuknya konsisten dan tidak menambah paragraf panjang di layar.

## 5. Bukti yang harus siap di appendix

| Bukti | Appendix | Sumber yang perlu dibuka saat produksi |
|---|---|---|
| Rasio audit 5,75/6,86/1,20; preprocessing selektif | A1 | paper/script/tables.py T2; content.py DATA_KORUPSI/PRA_DESPIKE |
| Gap 7 jam dan kisi waktu lengkap | A1 | content.py DATA_ANATOMI; implementasi fitur waktu |
| Pergeseran suhu 27,51 → 24,64; irigasi konstan | A1 | content.py METODE_GESER; figures/05-audit-dukungan.png |
| Peran anggota dan kontribusi berbeda | A3 | tables.py T6; content.py MODEL_ANGGOTA/MODEL_BLEND |
| Dua rekonstruksi suhu, SD selisih 0,047 °C | A4 | content.py METODE_AGRO; indeks agronomi dari dataset |
| Kontrol bobot waktu −0,080 vs acak −0,007 | A3 | content.py MODEL_BLEND; audit nested terkait |
| Residual ≈0,93; perubahan 1,91 vs 1,81 | A5 | content.py MODEL_INCREMENT; audit dengan 6.471 OOF rows terkait |
| Bias maju −2,89 vs OOF −1,86 | A6 | content.py MODEL_DEBIAS; member_bias pada final_pipeline.py |
| Kontrol koreksi: arah salah/anggota lain | A6 | content.py MODEL_DEBIAS; audit enam blok maju |
| Baseline 5,71 vs 4,81; menang 9/9 | A8 | tables.py T10; content.py pembanding; baselines_summary.json untuk baseline |
| Ledger publik termasuk kandidat gagal | A7 | tables.py T7; artefak submission terkait |
| Reproduksi nilai, bukan kesamaan byte mutlak | A8 | notebook bagian reproduksi; digest nilai enam desimal |

Jumlah OOF rows, instrumen, dan setup tidak boleh disatukan seolah semua bukti berasal dari satu eksperimen. Catat sumber dan ruang lingkup di caption.

## 6. Bank jawaban Q&A yang siap dibawakan

Jawaban berikut merupakan **jawaban awal**, sekitar 30–60 detik setelah latihan; durasi belum diukur. Tidak wajib langsung membuka appendix bila satu kalimat dan satu bukti cukup.

### Q1 — Mengapa target tidak ikut dibersihkan?

“Kami memeriksa penyimpangan lokal dan membandingkan skala yang peka terhadap lonjakan dengan skala robust. Karakternya berbeda: suhu dan tekanan menunjukkan ekor ekstrem yang jauh lebih kuat daripada target. Itu alasan penanganan diarahkan ke masukan tertentu, bukan meratakan target. Temuan ini bukan bukti seluruh label tanpa noise; ia membatasi tindakan yang layak berdasarkan audit.”

**Buka A1** bila diminta detail residual, skala robust, atau Hampel.

### Q2 — Dua rekonstruksi suhu sepakat, apakah artinya suhu pasti benar?

“Tidak. Itu pemeriksaan konsistensi dua perhitungan dari indeks yang tersedia, bukan ground truth independen. Keduanya hampir sepakat, dengan SD selisih 0,047 derajat. Hasil tersebut mendukung penggunaan informasi suhu yang lebih stabil dan relevan secara fisis. Proksi minimum suhu terhadap titik embun tetap mempunyai asumsi dan tidak selalu berlaku.”

**A4.** Hindari “dua sumber independen membuktikan akurasi”.

### Q3 — Bukankah centered window dan indeks harian memakai masa depan?

“Ya, beberapa fitur memakai pembacaan sensor setelah titik yang diprediksi. Dalam kontrak lomba, eksogen sepanjang periode memang tersedia. Yang tidak masuk adalah target kelembapan pada jendela uji. Karena itu kami menyebut hasilnya sesuai tugas rekonstruksi dengan eksogen diketahui. Untuk penggunaan langsung tanpa eksogen masa depan, pipeline perlu diubah dan diuji lagi.”

**A1/A4/A8.** Mengakui akses fitur masa depan lebih tepat daripada menyangkalnya.

### Q4 — Mengapa tidak memakai satu model saja?

“Kami tetap memakai model tunggal sebagai pembanding. Solusi lengkap mencapai RMSE validasi 4,81 dibanding satu LightGBM 5,71 pada protokol yang sama. Anggota dipilih untuk memberi fungsi dan pola residual berbeda, bukan sekadar menambah jumlah. Anggota ridge biasa yang tidak cukup membantu justru dikeluarkan. Perbaikannya terbatas pada evaluasi yang kami lakukan.”

**A3/A8.**

### Q5 — Mengapa memilih Huber padahal dinilai dengan RMSE?

“Metrik evaluasi dan cara belajar tidak harus identik. Masukan masih mempunyai gangguan ekstrem, sehingga pengaruh titik tertentu perlu dibatasi. Pilihan Huber didukung pemeriksaan loss dalam proyek ini. Namun kami juga mempertahankan anggota L2 agar sensitivitas terhadap kesalahan besar tetap terwakili. Keputusan tersebut bukan klaim Huber selalu paling baik.”

**A3.**

### Q6 — CatBoost sendirinya lebih buruk, mengapa dipertahankan?

“Kontribusi terhadap gabungan tidak sama dengan skor solo. Pada audit, residual CatBoost berbeda dari anggota utama; korelasinya sekitar 0,64, terendah di antara anggota pohon yang dibandingkan. Keragaman ini mempunyai alasan untuk diuji dalam gabungan. Anggotanya tetap diperiksa, termasuk bias maju yang kemudian dikoreksi, sehingga kami tidak mengabaikan kelemahannya.”

**A3/A6.**

### Q7 — Apakah sembilan pengujian berarti sembilan bukti independen?

“Tidak. Jendela validasinya tumpang tindih. Kemenangan 9/9 menunjukkan arah yang konsisten pada setup tersebut, tetapi tidak kami perlakukan sebagai sembilan pengamatan bebas. Kami melaporkan hasilnya dengan batas ini dan menggunakan audit maju serta kontrol sesuai pertanyaan komponen. Pengujian periode atau lokasi tambahan tetap dibutuhkan.”

**A2/A8.**

### Q8 — OOF sudah cukup untuk evaluasi gabungan?

“OOF menjaga agar prediksi model dasar berasal dari model yang tidak belajar dari target baris tersebut. Tetapi ketika prediksi itu dipakai memasang bobot atau koreksi, mengevaluasi kembali pada baris yang sama bisa optimistis. Karena itu kami membedakan skor pembanding, fitting komponen meta, dan audit nested atau maju yang relevan. Kami tidak menyatakan semua skor bebas optimisme hanya karena disebut OOF.”

**A2.** Tunjukkan harness yang sesuai bila diminta; jangan menamai seluruh skor sebagai nested.

### Q9 — Rekonsiliasi itu hanya smoothing?

“Bukan sekadar membuat garis lebih halus. Model level memprediksi angka, sedangkan model increment memprediksi perubahan yang dipelajari dari data. Objective mencari satu lintasan yang dekat dengan level dan mengikuti perubahan tersebut. Rangkaian tetap bisa naik-turun. Kami menguji apakah informasi perubahan lebih baik dari yang tersirat pada level sebelum menggabungkannya.”

**A5.** Video 75 detik tidak perlu diputar ulang kecuali diminta.

### Q10 — Mengapa 30 menit dan dua jam, serta bobot 4:1?

“Kedua horizon membawa skala dinamika berbeda. Pada pengukuran yang sama, model perubahan 30 menit lebih baik daripada selisih yang tersirat dari level. Keuntungan dua jam jauh lebih kecil. Itu memberi alasan untuk kekuatan yang berbeda; setup memakai bobot 4:1. Kami tidak menyebutnya optimum universal atau hasil optimasi yang membuktikan tidak ada bobot lain lebih baik.”

**A5.** Angka sumber 1,91 vs 1,81; dua jam 3,57 vs 3,52.

### Q11 — Offset CatBoost berasal dari test?

“Koreksi dipasang dari rerata kesalahan OOF anggota, lalu diterapkan dengan kekuatan setengah. Nilai −2,89 adalah hasil audit maju yang berbeda, bukan angka yang langsung ditambahkan ke semua prediksi. Arah koreksi juga diperiksa dengan kontrol arah terbalik dan anggota hampir tak bias. Target uji tidak dipakai memasang offset.”

**A6.** Fitting train/OOF berbeda dari feedback publik untuk keputusan koreksi.

### Q12 — Apakah leaderboard memengaruhi pilihan akhir?

“Fitting parameter gabungan dan koreksi berasal dari train serta OOF. Namun feedback publik ikut menentukan apakah beberapa koreksi pasca-model diterima atau ditolak. Kami melaporkan kandidat yang gagal dan tidak menyatakan seluruh keputusan akhir blind terhadap leaderboard. Angka publik juga tidak menjadi bukti generalisasi ke lokasi lain.”

**A7.**

### Q13 — Bisa direproduksi persis?

“Pipeline menggunakan data resmi dan seed yang dibekukan. Pemeriksaan reproduksi membandingkan nilai prediksi pada presisi enam desimal. Kami membedakannya dari hash byte file karena representasi floating-point dapat mengubah teks tanpa perbedaan prediksi yang bermakna. Bukti yang ditampilkan adalah keluaran eksekusi tersimpan; untuk klaim run terbaru, kami harus menjalankannya lagi.”

**A8.** Jangan menyebut tests/run lama sebagai pemeriksaan baru.

### Q14 — Apa manfaatnya bagi Pak Anton?

“Pak Anton adalah ilustrasi kebutuhan informasi kelembapan. Yang diuji adalah kemampuan prediksi pada data lomba dengan eksogen sepanjang jendela tersedia. Untuk membantu keputusan langsung di kebun, perlu evaluasi informasi yang tersedia saat itu dan pengujian dampaknya. Kami belum mengukur penurunan penyakit, penghematan air, atau hasil panen.”

**A8.**

## 7. Latihan yang menarget rubrik

**Latihan alur:** pendengar lintas bidang harus mampu menjawab empat hal tanpa melihat paper: masalahnya apa; mengapa memilih metode itu; perbaikannya berasal dari kesalahan apa; apa batas hasilnya. Catat bagian yang membuat mereka tersesat dan revisi kalimat, bukan menambah definisi.

**Latihan metode:** setiap anggota menjawab Q1–Q14. Jawaban pertama menyelesaikan pertanyaan sebelum membuka detail. Target awal 30–60 detik; jangan mengganti kecepatan bicara dengan durasi jawaban yang lebih pendek.

**Latihan tantangan:** minta partner menyela dengan “buktinya?”, “dibanding apa?”, “angka ini dari data mana?”, “apakah informasi ini tersedia saat prediksi?”. Gunakan appendix yang tepat; bila tidak ada bukti, nyatakan batasnya.

**Latihan waktu:** gunakan PPTX final dan video offline, ukur sampai slide 14. Sasaran 13:40, batas latihan 14 menit. Jika melewati, pangkas kalimat penjelas atau detail appendix; pertahankan kontrak data, metode, evaluation, error analysis, dan batas.

**Latihan delivery:** tiga jeda terarah pada kasus, pola residual, dan verdict. Dua perpindahan pembicara. Jangan memakai suara karikatur Pak Anton. Saat Q&A, metafora detektif berhenti.

## 8. Gerbang kesiapan

- [ ] File dan nama sesuai juknis; tidak identitas instansi.
- [ ] Empat babak dapat dikenali tanpa presenter menjelaskan tema.
- [ ] Semua angka utama punya konteks dan sumber yang dapat dibuka.
- [ ] Model aktif lima; ridge biasa jelas kandidat yang dibuang.
- [ ] CV/publik/OOF/audit maju tidak dicampur.
- [ ] Video mempunyai fungsi baru, satu slide, 75 detik setelah residual.
- [ ] Grafik memakai data nyata atau diberi label ilustrasi mekanisme.
- [ ] Kedua anggota mampu menjawab pertanyaan statistik dan ML.
- [ ] Jawaban leaderboard, leakage, overlap, dan evaluasi meta konsisten dengan artefak.
- [ ] Rehearsal dan playback sudah benar-benar dijalankan sebelum mengklaim siap tampil.

Status saat dokumen dibuat: sumber juknis dan rubrik sudah diverifikasi; strategi/script direvisi. Deck, grafik panggung, video, rehearsal, dan playback belum diverifikasi. Tidak ada skor prediksi juri.
