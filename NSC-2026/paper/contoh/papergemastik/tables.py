# -*- coding: utf-8 -*-
"""Isi tabel - seluruh angka bersumber dari reports/angka.json dan docs/paper/tabel.md."""

T1 = ("Komposisi Korpus Judul Berita Keuangan", [
    ["Ukuran", "Nilai"],
    ["Judul terkumpul", "40.009"],
    ["Judul unik setelah deduplikasi SimHash", "32.863"],
    ["Duplikat terbuang", "7.146 (17,86%)"],
    ["- tahun 2022", "4.174"],
    ["- tahun 2023", "4.932"],
    ["- tahun 2024", "5.601"],
    ["- tahun 2025", "7.771"],
    ["- tahun 2026 (s.d. Agustus)", "10.385"],
    ["Judul dengan badan teks", "177 (0,54%)"],
    ["Entitas emiten terekstrak", "54.343"],
    ["Skor sentimen", "72.066"],
    ["Baris harga OHLCV", "54.613"],
], [0.62, 0.38], ['l', 'r'])

T2 = ("Sumber Daya dan Paket Dataset yang Dirilis Terbuka", [
    ["Sumber daya", "Ukuran", "Padanan publik"],
    ["**Sumber daya bahasa**", "", ""],
    ["Leksikon sentimen keuangan Indonesia", "495 istilah", "belum ada"],
    ["Kamus *slang* investor Indonesia", "204 entri", "belum ada"],
    ["Daftar kode saham ambigu BEI", "147 kode", "belum ada"],
    ["*Knowledge graph* relasi BEI", "152 simpul; 1.807 sisi (515 kurasi manual)", "belum ada"],
    ["*Gold standard* NER kode saham", "6.000 kalimat; 551 kode unik", "belum ada"],
    ["**Paket dataset**", "", ""],
    ["Korpus judul berlabel reaksi harga", "32.863 judul unik", "belum ada"],
    ["Dataset sentimen tingkat aspek, berlabel leksikon",
     "26.467 contoh judul-emiten", "belum ada"],
    ["**Turunan**", "", ""],
    ["Master emiten BEI", "942 emiten; 3.585 alias aktif", "Wikipedia (CC BY-SA)"],
], [0.40, 0.34, 0.26], ['l', 'l', 'l'])

T3 = ("Pembagian Data Kronologis dengan *Holdout Out-of-Time*", [
    ["Bagian", "Rentang", "Jumlah", "Komposisi label"],
    ["Latih", "Jan 2022 - Des 2024", "9.862", "leksikon 6.395 + reaksi harga 3.467"],
    ["Validasi", "Jan - Jun 2025", "995", "100% reaksi harga"],
    ["**Uji**", "**Jul 2025 - Agu 2026**", "**6.082**", "**100% reaksi harga**"],
], [0.15, 0.26, 0.13, 0.46], ['l', 'l', 'r', 'l'])

T4 = ("Perbedaan dengan Solusi Sebelumnya", [
    ["Aspek", "Penelitian terdahulu", "SENDI"],
    ["Bahasa", "Inggris", "Indonesia"],
    ["Sumber daya sentimen", "tersedia (LM, FinBERT)", "dibangun dan dirilis"],
    ["Kode emiten ambigu", "tidak dibahas", "diukur, ditangani, hipotesisnya dibantah"],
    ["Sumber label", "anotasi manual atau leksikon", "reaksi harga, diaudit terhadap verifikasi manusia"],
    ["Pembagian data", "sering acak", "**holdout out-of-time**, acak sebagai pembanding"],
    ["*Baseline*", "sering hanya leksikon", "leksikon, TF-IDF, dan IndoBERT"],
    ["Ketidakpastian", "angka titik", "selang kepercayaan *bootstrap*, uji berpasangan"],
    ["Kontrol", "jarang ada", "10 tarikan sinyal acak pada strategi yang sama"],
    ["Sensitivitas biaya", "jarang", "tujuh titik, 0% sampai 0,8%"],
    ["Stabilitas kesimpulan", "satu periode", "dua periode, pembalikan arahnya dilaporkan"],
    ["Ketimpangan cakupan", "tidak diukur", "Gini + kurva Lorenz dengan *null model* acak"],
    ["Pelaporan hasil negatif", "jarang", "eksplisit dan menyeluruh"],
], [0.24, 0.32, 0.44], ['l', 'l', 'l'])

T5 = ("Metrik Evaluasi per Aspek Pengujian", [
    ["Aspek", "Metrik"],
    ["NER kode saham", "*precision*, *recall*, F1 pada *gold standard*; CI *bootstrap*"],
    ["Klasifikasi sentimen", "*accuracy*, *macro-F1*, *weighted-F1*; CI *bootstrap*"],
    ["Perbandingan antarmodel", "*bootstrap* berpasangan; uji McNemar binomial eksak"],
    ["Reliabilitas anotasi", "Krippendorff's alpha nominal; kesepakatan berpasangan"],
    ["Hubungan sentimen-imbal hasil", "uji t Welch tanpa bias seleksi"],
    ["Dampak berita", "AR, CAR, CAAR; uji t, uji BMP, uji tanda"],
    ["Pengujian ganda", "koreksi Holm-Bonferroni"],
    ["Kinerja strategi", "*total return*, Sharpe, *win rate*, *max drawdown*, *information ratio*"],
    ["Ketimpangan cakupan", "koefisien Gini, kurva Lorenz, harapan acak"],
    ["Kontrol", "10 tarikan sinyal acak pada pasangan emiten-tanggal yang sama"],
], [0.33, 0.67], ['l', 'l'])

T6 = ("Deteksi Kode Saham pada *Gold Standard* 6.000 Kalimat", [
    ["Metode", "Prec.", "Rec.", "F1", "CI 95% F1"],
    ["SENDI (*gazetteer* + disambiguasi)", "0,7905", "0,9994", "**0,8827**", "[0,8728; 0,8925]"],
    ["Pencocokan kode mentah", "0,7885", "0,9997", "0,8816", "[0,8717; 0,8913]"],
    ["*Gazetteer* tanpa konteks", "0,7291", "1,0000", "0,8433", "[0,8326; 0,8540]"],
    ["NER Indonesia pra-latih", "0,3038", "0,0769", "0,1227", "[0,1080; 0,1357]"],
], [0.34, 0.13, 0.13, 0.13, 0.27], ['l', 'r', 'r', 'r', 'c'])

T7 = ("Klasifikasi Sentimen pada *Holdout Out-of-Time*, Diukur terhadap Label Reaksi Harga "
      "(n = 6.082). Bandingkan Tabel XIII yang Diukur terhadap Anotasi Manusia", [
    ["Model", "Kesesuaian dengan reaksi harga H+1", "*Macro-F1* vs reaksi harga",
     "*Weighted-F1* vs reaksi harga", "CI 95% *weighted-F1*"],
    ["Leksikon (tanpa pelatihan)", "0,3464", "0,3255", "0,3300", "[0,3180; 0,3421]"],
    ["TF-IDF + regresi logistik", "0,3678", "0,3594", "**0,3624**", "[0,3499; 0,3743]"],
    ["IndoBERT *fine-tuned*", "0,3724", "0,3464", "0,3519", "[0,3389; 0,3648]"],
    ["Tebakan acak (acuan)", "≈0,333", "-", "-", "-"],
], [0.26, 0.19, 0.17, 0.17, 0.21], ['l', 'r', 'r', 'r', 'c'])

T7B = ("Uji *Bootstrap* Berpasangan atas Selisih *Weighted-F1*", [
    ["Perbandingan", "Selisih", "CI 95%", "Kesimpulan"],
    ["IndoBERT - leksikon", "+0,0219", "[+0,0101; +0,0346]", "berbeda dari nol"],
    ["IndoBERT - TF-IDF", "-0,0104", "[-0,0214; +0,0011]", "tidak dapat dibedakan dari nol"],
], [0.24, 0.14, 0.26, 0.36], ['l', 'r', 'c', 'l'])

T8 = ("*Event Study* atas 11.963 Peristiwa dan Koreksi Holm-Bonferroni", [
    ["Kelompok", "n", "Mean CAR", "p (uji t)", "z (BMP)", "p (BMP)"],
    ["Sentimen positif", "8.146", "+0,906%", "0,0000", "+10,110", "0,0000"],
    ["Sentimen negatif", "3.817", "-0,467%", "0,0025", "-0,951", "0,3415"],
], [0.26, 0.13, 0.16, 0.15, 0.15, 0.15], ['l', 'r', 'r', 'r', 'r', 'r'])

T8B = ("", [
    ["Uji", "p", "Ambang Holm", "Bertahan"],
    ["CAR positif (uji t)", "0,000000", "0,010000", "ya"],
    ["CAR positif (BMP)", "0,000000", "0,012500", "ya"],
    ["Selisih positif-negatif", "0,000000", "0,016667", "ya"],
    ["CAR negatif (uji t)", "0,002515", "0,025000", "ya"],
    ["CAR negatif (BMP)", "0,341485", "0,050000", "**tidak**"],
], [0.36, 0.22, 0.24, 0.18], ['l', 'r', 'r', 'c'])

T9 = ("Ketimpangan Cakupan Berita Antaremiten", [
    ["Subhimpunan", "Sebutan", "Gini", "Harapan acak", "Kelebihan", "Sah dikutip?"],
    ["**Sebutan insidental**", "11.338", "0,8045", "0,1617", "+0,6428", "**ya**"],
    ["RSS langsung saja", "222", "0,9702", "0,8102", "+0,1600", "ya, lemah"],
    ["Arsip per kueri", "23.617", "0,8863", "0,1121", "+0,7742", "**tidak**"],
], [0.24, 0.15, 0.13, 0.18, 0.15, 0.15], ['l', 'r', 'r', 'r', 'r', 'c'])

T9B = ("", [
    ["Ukuran pada subhimpunan sebutan insidental", "Nilai"],
    ["Emiten terdaftar", "942"],
    ["Emiten pernah disebut", "756"],
    ["**Emiten tidak pernah diberitakan**", "**186 (19,8%)**"],
    ["Pangsa 10% emiten teratas", "73,1%"],
    ["Pangsa 1% emiten teratas", "22,5%"],
    ["Median sebutan per emiten", "2"],
], [0.66, 0.34], ['l', 'r'])

T10 = ("*Backtest In-Period* dan *Out-of-Sample*", [
    ["Metrik", "2022-2024 (sebagian *in-sample*)", "**2025-2026 (out-of-sample)**"],
    ["*Total return*", "-48,94%", "**-34,82%**"],
    ["*Benchmark* IHSG", "+6,22%", "**-12,03%**"],
    ["*Annualized return*", "-20,14%", "-23,35%"],
    ["*Sharpe ratio*", "-1,5524", "-1,1598"],
    ["*Win rate*", "39,88%", "39,08%"],
    ["*Max drawdown*", "-50,95%", "-47,24%"],
    ["Jumlah transaksi", "805", "714"],
], [0.30, 0.36, 0.34], ['l', 'r', 'r'])

T11 = ("Ketahanan Parameter, Ablasi Sinyal, dan Kontrol Acak (2022-2024)", [
    ["Pengujian", "Hasil"],
    ["12 kombinasi parameter", "0 menguntungkan; median -66,59%; terbaik -46,27%; terburuk -84,87%"],
    ["Ablasi IndoBERT (acuan)", "805 transaksi; -48,94%; *win rate* 39,88%; Sharpe -1,5524"],
    ["Ablasi leksikon saja", "682 transaksi; -48,31%; *win rate* 39,30%; Sharpe -1,8463"],
    ["Ablasi keyakinan ≥ 0,90", "804 transaksi; -44,25%; *win rate* 40,67%; Sharpe -1,4289"],
    ["**Kontrol acak (10 tarikan)**", "**rata-rata -42,46%; rentang -56,90% s.d. -29,31%; model pada persentil 30**"],
    ["Sensitivitas biaya (7 titik)", "biaya 0%: -30,83%; tarif ritel 0,40%: -48,94%; 0,80%: -73,34%; tanpa titik impas"],
], [0.30, 0.70], ['l', 'l'])

T12 = ("Reliabilitas Antar-Anotator pada 800 Judul", [
    ["Ukuran", "Nilai"],
    ["Jumlah pemeriksa independen", "3"],
    ["Judul dinilai", "800"],
    ["**Krippendorff's alpha (nominal)**", "**0,9029**"],
    ["Kesepakatan Pemeriksa 1 vs 2", "93,13%"],
    ["Kesepakatan Pemeriksa 1 vs 3", "95,00%"],
    ["Kesepakatan Pemeriksa 2 vs 3", "94,13%"],
    ["Judul disepakati bulat", "729 (91,1%)"],
    ["Judul berakhir seri sempurna", "0"],
    ["Alpha putaran 1 (n = 400)", "0,8953"],
    ["Alpha putaran 2 (n = 400)", "0,9090"],
    ["Kesesuaian label reaksi harga H+1", "36,22% (n = 798)"],
], [0.62, 0.38], ['l', 'r'])

T13 = ("Penilai Sentimen terhadap Rujukan Manusia pada Himpunan Uji Terkunci (n = 400)", [
    ["Penilai", "Akurasi", "CI 95% akurasi", "*macro-F1*", "CI 95% *macro-F1*", "vs label harga"],
    ["Leksikon v1.1", "66,00%", "[61,50; 70,75]", "**0,6378**", "[0,5855; 0,6889]", "36,84%"],
    ["IndoBERT, label aspek", "60,50%", "[56,00; 65,25]", "0,6026", "[0,5520; 0,6531]", "37,34%"],
    ["TF-IDF, label aspek", "60,25%", "[55,25; 65,25]", "0,5810", "[0,5265; 0,6363]", "38,35%"],
    ["IndoBERT, label dokumen", "47,75%", "[42,50; 52,75]", "0,4358", "[0,3839; 0,4865]", "38,35%"],
    ["TF-IDF, label dokumen", "41,50%", "[36,50; 46,50]", "0,4024", "[0,3511; 0,4525]", "39,35%"],
    ["*Label reaksi harga sendiri*", "33,83%", "[29,32; 38,85]", "0,3179", "[0,2749; 0,3663]", "-"],
    ["*Penebak konstan “bullish”*", "47,50%", "-", "0,2147", "-", "-"],
], [0.24, 0.13, 0.18, 0.13, 0.18, 0.14], ['l', 'r', 'c', 'r', 'c', 'r'])

T14 = ("Uji McNemar Berpasangan, Dikoreksi Holm-Bonferroni atas 15 Uji", [
    ["Perbandingan (kiri vs kanan)", "Kiri", "Kanan", "p", "Bertahan"],
    ["Leksikon vs TF-IDF dokumen", "139", "41", "< 0,000001", "ya"],
    ["Leksikon vs IndoBERT dokumen", "112", "39", "< 0,000001", "ya"],
    ["Leksikon vs penebak konstan", "142", "68", "< 0,000001", "ya"],
    ["TF-IDF dokumen vs TF-IDF aspek", "35", "110", "< 0,000001", "ya"],
    ["TF-IDF dokumen vs IndoBERT aspek", "38", "114", "< 0,000001", "ya"],
    ["IndoBERT dokumen vs IndoBERT aspek", "36", "87", "0,000005", "ya"],
    ["**IndoBERT aspek vs penebak konstan**", "**122**", "**70**", "**0,000215**", "**ya**"],
    ["Leksikon vs IndoBERT aspek", "47", "25", "0,012775", "tidak"],
    ["TF-IDF dokumen vs penebak konstan", "76", "100", "0,082680", "tidak"],
    ["**IndoBERT dokumen vs penebak konstan**", "**70**", "**69**", "**1,000000**", "**tidak**"],
    ["TF-IDF aspek vs IndoBERT aspek", "37", "38", "1,000000", "tidak"],
], [0.40, 0.11, 0.11, 0.21, 0.17], ['l', 'r', 'r', 'r', 'c'])

T15 = ("Susunan Sinyal pada Data Latih (n = 9.862)", [
    ["Sumber label", "Contoh", "Pangsa bobot", "Proporsi netral", "Membawa emiten"],
    ["Leksikon (tingkat dokumen)", "6.395", "63,4%", "**6,6%**", "**0%**"],
    ["Reaksi harga (tingkat aspek)", "3.467", "36,6%", "40,2%", "100%"],
], [0.34, 0.14, 0.18, 0.18, 0.16], ['l', 'r', 'r', 'r', 'r'])

T16 = ("Akibat Memperbaiki Tingkat Label, Semua Hal Lain Ditahan Tetap", [
    ["Penilai", "*macro-F1* label dokumen", "*macro-F1* label aspek", "Selisih"],
    ["IndoBERT", "0,4358", "**0,6026**", "+0,167"],
    ["TF-IDF + regresi logistik", "0,4024", "**0,5810**", "+0,179"],
], [0.32, 0.24, 0.24, 0.20], ['l', 'r', 'r', 'r'])

T17 = ("Data Latih Model Sentimen Tingkat Aspek", [
    ["Ukuran", "Nilai"],
    ["Total contoh (pasangan judul-emiten)", "26.467"],
    ["Latih (Jan 2022 - Des 2024)", "8.560"],
    ["Validasi (Jan - Jun 2025)", "2.431"],
    ["Uji (Jul 2025 - Agu 2026)", "15.268"],
    ["Sebaran label *bullish*", "11.856"],
    ["Sebaran label *neutral*", "10.670"],
    ["Sebaran label *bearish*", "3.941"],
    ["Contoh yang membawa emiten", "100%"],
    ["Judul beranotasi yang dikeluarkan", "138 latih; 70 validasi"],
    ["Skala penyeimbang kelas", "*bearish* 2,98; *bullish* 0,82; *neutral* 0,69"],
], [0.58, 0.42], ['l', 'r'])
