# -*- coding: utf-8 -*-
"""Isi seluruh tabel naskah.

Bentuk setiap tabel: (judul, baris, bobot_lebar_kolom, perataan_kolom).
Baris pertama adalah header. Perataan: 'l' kiri, 'c' tengah, 'r' kanan.

Angka di sini harus dapat ditemukan di keluaran `make_figures.py` atau di log
eksperimen yang disebut pada komentar. Jangan mengetik angka dari ingatan.
Untuk tanda kurang pakai U+2212 (−), bukan hyphen, supaya lebarnya sejajar
dengan angka di dalam kolom.
"""

# --------------------------------------------------------------- TABEL I
# Sumber: make_figures.py -> angka_anatomi()
T1 = ("Anatomi Dataset", [
    ["Butir", "Latih", "Uji"],
    ["Jumlah baris", "2.933", "734"],
    ["Awal", "29 Jun 2023 06.00", "29 Agu 2023 15.00"],
    ["Akhir", "29 Agu 2023 14.30", "13 Sep 2023 21.30"],
    ["Rentang", "61,4 hari", "15,3 hari"],
    ["Selang waktu", "30 mnt, 1 lompatan 7 j", "30 mnt, sempurna"],
    ["Kanal eksogen", "24", "24"],
    ["Kolom target", "ada", "**tidak ada**"],
    ["Nilai hilang, kanal inti", "9,0–10,8 %", "8,6–17,6 %"],
    ["`env_battery` hilang", "98,0 %", "98,0 %"],
    ["`water_volume_*`", "bervariasi", "**konstan**"],
], [1.30, 1.00, 1.00], ['l', 'c', 'c'])

# --------------------------------------------------------------- TABEL II
# Sumber: make_figures.py -> gambar_02_residu_loo(); notebook Bagian 3.2
T2 = ("Audit Korupsi lewat Residu Tinggalkan-Satu", [
    ["Kolom", "sd", "sd robus", "Rasio", "Tafsir"],
    ["`air_humidity`", "1,71", "1,42", "**1,20**", "ekor hampir normal"],
    ["`air_temperature`", "2,72", "0,47", "**5,75**", "lonjakan suntikan"],
    ["`pressure`", "1,58", "0,23", "**6,86**", "lonjakan suntikan"],
    ["`co2`", "23,33", "10,63", "2,20", "sebagian terlonjaki"],
    ["`soil_temp_line1`", "0,07", "0,07", "1,04", "bersih"],
], [1.18, 0.52, 0.62, 0.55, 1.25], ['l', 'r', 'r', 'r', 'l'])

# --------------------------------------------------------------- TABEL III
# Sumber: make_figures.py -> kurva_oracle()
T3 = ("Batas Oracle Tekanan Uap", [
    ["Resolusi pengetahuan tentang *e*", "RMSE (%RH)"],
    ["satu rerata per hari agronomi", "8,37"],
    ["dihaluskan 24 jam", "7,61"],
    ["dihaluskan 12 jam", "4,53"],
    ["dihaluskan 6,5 jam", "2,96"],
    ["**model kami (2,827) mendarat di sini**", "**≈ 6,1 jam**"],
    ["dihaluskan 2,5 jam", "1,60"],
    ["dihaluskan 1,5 jam", "1,16"],
], [1.75, 0.85], ['l', 'r'])

# --------------------------------------------------------------- TABEL IV
# Sumber: make_figures.py -> gambar_11_despiking()
T4 = ("Efek Despiking Hampel pada `air_temperature`", [
    ["Ukuran", "Sebelum", "Sesudah"],
    ["sd residu tinggalkan-satu", "2,715", "**0,515**"],
    ["sd robus residu tinggalkan-satu", "0,472", "0,408"],
    ["ekskursi residu > 2,5 °C", "57", "**5**"],
    ["… di antaranya di jendela uji", "5", "**0**"],
    ["nilai < 5 °C atau > 45 °C", "16", "**0**"],
    ["nilai yang benar-benar diubah", "–", "16 (0,49 %)"],
], [1.35, 0.75, 0.85], ['l', 'r', 'r'])

# --------------------------------------------------------------- TABEL V
# Sumber: final_pipeline.py, definisi blok fitur
T5 = ("Lima Blok Fitur dan Pertanyaan Fisis yang Dijawabnya", [
    ["Blok", "Isi", "Pertanyaan fisis"],
    ["dasar", "level sensor; rerata terpusat 1 j / 6 j / 24 j; anomali terhadap "
              "rerata itu; sd 6 j; geseran ±2 j; kemiringan; harmonik jam-hari; "
              "*e*_{s}(*T*); silang suhu–tanah; indeks agronomi",
     "keadaan sesaat dan konteks lokalnya pada tiga skala waktu"],
    ["`tmin`", "min / maks / rentang bergulir 18 j / 48 j / 96 j atas suhu, dan "
               "100·*e*_{s}(*T*_{min})/*e*_{s}(*T*)",
     "proksi titik embun bebas-parameter, Persamaan ({E:proksi})"],
    ["`tend`", "tendensi tekanan 24 j dan 48 j, sd tekanan, tendensi CO₂ 24 j",
     "rezim sinoptik: tekanan turun mendahului adveksi lembap"],
    ["`ordstat`", "min / maks / rentang CO₂ 9 j dan 24 j",
     "CO₂ sebagai penjejak laju ventilasi"],
    ["`qblock`", "persentil 5 dan 95 bergulir atas suhu dan CO₂, plus RH-proksi "
                 "dari persentil-5",
     "minimum keras melaporkan satu sampel terdingin; persentil-5 melaporkan "
     "letak *massa* dingin, dan celah keduanya adalah sinyal tersendiri"],
], [0.42, 1.55, 1.35], ['l', 'l', 'l'])

# --------------------------------------------------------------- TABEL VI
# Sumber: final_pipeline.py; bobot dari make_figures.py -> MEASURED_BIAS
T6 = ("Enam Anggota dan Alasan Masing-Masing Ada", [
    ["Anggota", "Model", "Bobot", "Mengapa ia ada"],
    ["`hbt`", "LightGBM, huber α = 2, 900 pohon, 15 daun", "0,489",
     "pekerja utama; huber menahan pengaruh baris yang tersisa berderau"],
    ["`cat`", "CatBoost, `Huber:delta=4`, 1.200 iterasi, kedalaman 6", "0,217",
     "**sengaja salah-spesifikasi**; korelasi residu terhadap `hbt` hanya 0,64, "
     "terendah dari semua pohon. Yang dibeli *blend* adalah dekorelasi"],
    ["`enet`", "elastic-net terstandardisasi", "0,194",
     "anggota linear; mengekstrapolasi mulus ke suhu di luar dukungan"],
    ["`ridge_e`", "ridge di ruang tekanan uap, dikonversi balik", "0,050",
     "satu-satunya anggota yang terdekorelasi secara **fisis**: ia meminimumkan "
     "galat pada *e*, bukan pada RH"],
    ["`l2`", "LightGBM, kerugian kuadrat", "0,050",
     "metriknya RMSE; anggota ini mengembalikan sensitivitas terhadap residu besar"],
    ["`ridge`", "ridge biasa", "**dibuang**",
     "kontribusi *drop-one* negatif; bobot NNLS nol di 18 dari 18 lipatan; "
     "−0,012 RMSE saat dibuang"],
], [0.44, 1.20, 0.42, 1.60], ['l', 'l', 'r', 'l'])

# ------------------------------------------------------------- TABEL PEMBANDING
# Sumber: outputs/baselines_summary.json (enam baris pertama, dihitung oleh
# script/baselines pada protokol yang sama) dan notebook Bagian 11.3 (*stack*).
# Setiap metode dipasang hanya pada baris sebelum titik potong tiap lipatan dan
# dinilai pada 15 hari berikutnya, di 6.480 baris luar-lipatan yang identik.
T10 = ("Pembanding Sejawat pada Sembilan Lipatan Titik-Asal Bergulir yang Sama", [
    ["Metode", "Kelas", "RMSE terkumpul", "Rerata lipatan"],
    ["Rerata latih", "naif", "18,82", "18,81"],
    ["Persistensi profil hari terakhir", "naif", "13,38", "13,06"],
    ["Proksi titik embun, tanpa parameter", "fisis", "10,93", "10,91"],
    ["Klimatologi jam-hari", "naif", "10,16", "10,06"],
    ["Regresi linear berganda, 24 kanal", "statistik", "8,08", "7,84"],
    ["LightGBM tunggal, parameter bawaan", "mesin", "5,71", "5,63"],
    ["**Stack lengkap (naskah ini)**", "**kami**", "**4,81**", "**4,69**"],
    ["LightGBM tunggal, jendela kausal", "kendali", "8,22", "8,03"],
], [1.44, 0.46, 0.56, 0.52], ['l', 'l', 'r', 'r'])


# --------------------------------------------------------------- TABEL VII
# Sumber: make_figures.py -> MEASURED_LB dan README proyek
T7 = ("Tangga Skor Papan Peringkat Publik, Termasuk yang Merugikan", [
    ["Perubahan", "RMSE", "Δ"],
    ["dasar: 5 anggota, *blending* NNLS", "3,04904", "–"],
    ["bobot *blend* per pita waktu-hari", "3,02942", "−0,01962"],
    ["koreksi bias diurnal per pita", "3,00589", "−0,02353"],
    ["kemiringan dispersi + fitur terpotong", "3,28564", "**+0,23700**"],
    ["anggota LightGBM L2 keenam", "3,02586", "+0,00300"],
    ["lantai penyusutan NNLS dilepas", "3,05372", "+0,02786"],
    ["**rekonsiliasi lintasan increment**", "**2,86595**", "**−0,15991**"],
    ["tiga penghalusan *increment* sekaligus", "2,93028", "+0,06433"],
    ["anggota `ridge` dibuang", "2,85383", "−0,01212"],
    ["bentuk pita menggantikan harmonik", "2,84953", "−0,00430"],
    ["de-bias level anggota `cat`", "**2,82744**", "**−0,02209**"],
    ["kemiringan dispersi, kekuatan ¼", "2,83299", "+0,00555"],
], [1.62, 0.60, 0.66], ['l', 'r', 'r'])

# --------------------------------------------------------------- TABEL VIII
# Sumber: notebook Bagian 12.2; outputs/audit_v21_s47, audit_v21_s48
T8 = ("Diagnostik Kalibrasi Pasca-Model pada Slice Publik", [
    ["Besaran jendela uji", "Dugaan internal", "**Terukur**", "Sisa"],
    ["galat level rerata (%RH)", "−0,98", "**−0,4145**", "−0,008"],
    ["kemiringan kalibrasi", "1,031", "**1,0050**", "−0,002"],
], [1.15, 0.90, 0.85, 0.55], ['l', 'r', 'r', 'r'])

# --------------------------------------------------------------- TABEL IX
# Sumber: notebook Bagian 13.1; log eksperimen di outputs/
T9 = ("Arah yang Ditolak Berdasarkan Pengukuran Internal", [
    ["Arah", "Hasil terukur", "Pelajaran"],
    ["Analog / tetangga terdekat: cocokkan keadaan sensor, transpor RH lewat "
     "rasio *e*_{s}",
     "pasangan analog berbagi **RH** (*r* = 0,81) jauh lebih baik daripada "
     "berbagi tekanan uap (*r* = 0,47)",
     "kemiripan sensor tidak menyiratkan kemiripan massa udara"],
    ["Prior kelengkungan pada *e*: penalti selisih-kedua bebas-parameter",
     "lintasan model sudah 2× lebih mulus daripada kebenaran (rasio 0,47)",
     "penalti kehalusan mendorong ke arah yang sudah salah"],
    ["Horizon *increment* lebih panjang: 6 j, 12 j, 24 j",
     "model 24 j mencapai RMSE 7,76 vs garis dasar 11,46, tetapi level *stack* "
     "sudah menyiratkannya lebih baik",
     "kendala hanya membantu kalau ia lebih baik daripada yang sudah tersirat"],
    ["Reparameterisasi termodinamika *increment*",
     "sinyal menyusut 3,54 → 2,23, galat tetap 1,80 → 1,80",
     "pembelajar sudah menangani bagian bentuk-tertutup dengan sempurna"],
    ["Ekspansi level harian ke kemiringan terpasang",
     "dugaan dan realisasi tidak berkorelasi (13–23 hari sampel); −0,006 saja",
     "kemiringan tingkat-hari tidak dapat diduga dari sejarah sependek ini"],
    ["Jaring saraf, kernel, dan model urutan: MLP 128×64, kernel ridge RBF, "
     "ridge atas bank konvolusi acak sepanjang 193 titik",
     "8,75 dan 16,45 RMSE solo; model urutan membawa informasi **level** tetapi "
     "bukan informasi **perubahan**, dan lebih buruk di keenam blok",
     "2.933 baris terlalu sedikit untuk keduanya; representasi urutan menemukan "
     "dinamika, tetapi bukan jenis yang dibutuhkan penyelesai"],
    ["Penyapuan hiperparameter `hbt`, 11 titik di sekitar incumbent",
     "hanya `n_estimators` yang memindahkan skor; kombinasi dua pemenang "
     "tunggal gagal, +0,012 dan +0,072",
     "urutan pada layar penyaringan adalah deskripsi, bukan mekanisme yang "
     "dapat dikomposisikan"],
], [1.10, 1.30, 1.05], ['l', 'l', 'l'])



# ============================================================================
# LAMPIRAN
# Penomorannya terpisah (TABEL A.I, A.II, …) dan diatur `mode_lampiran()` di
# build.py. Juknis 3d membolehkan lampiran; badan naskah tetap dijaga di bawah
# 10 halaman sendirian, sehingga lampiran murni tambahan.
# ============================================================================

# --------------------------------------------------------------- TABEL A.I
# Sumber: notebook Bagian 13.2. Tabel ini semula berada di badan naskah dan
# dipindahkan ke lampiran saat naskah dipangkas ke 10 halaman; isinya tetap
# dirujuk dari Bagian VI-D.
TA1 = ("Perubahan yang Ditolak Papan Peringkat Setelah Lolos Validasi Internal", [
    ["Perubahan", "Bukti internal", "Mengapa ia tetap salah", "Δ papan peringkat"],
    ["kemiringan kalibrasi dispersi (versi awal)",
     "menang di 13/13 lipatan, tiga keluarga lipatan yang berbeda",
     "sebaran prediksi uji (18,8) berada **di atas** setiap lipatan validasi "
     "silang (16,2–17,5), sehingga pemadatan yang hendak dibatalkan tidak ada "
     "di jendela uji",
     "**+0,23700**"],
    ["membuang lantai penyusutan NNLS",
     "−0,058 pada validasi bersarang",
     "bersarangnya berbagi label antar-lipatan; pada protokol yang diperbaiki "
     "responsnya monoton ke arah sebaliknya",
     "+0,02786"],
    ["koreksi pita-rentang-lebar",
     "mekanisme terukur, arah benar pada blok maju",
     "biasnya membalik tanda di jendela uji",
     "+0,12600"],
    ["penghalusan *increment*: de-shrink, prior fisis, lag tambahan",
     "tiga-tiganya diadopsi secara internal",
     "ketiganya menyetel komponen yang sudah terkalibrasi; nol dari tiga menang",
     "+0,06433"],
    ["kapasitas `hbt` dinaikkan ke 2.400 pohon",
     "membaik di keenam blok maju, pada dua blok *seed*",
     "ditolak pada gerbang tekanan luar-rezim sebelum dikapalkan",
     "tidak dikapalkan"],
], [0.95, 1.05, 1.55, 0.62], ['l', 'l', 'l', 'r'])

# --------------------------------------------------------------- TABEL A.II
# Sumber: keluaran sel Bagian 1, 11.5, dan 11.6 notebook, diverifikasi ulang
# terhadap berkas di repositori. md5 dataset dan md5 berkas *submission* dihitung
# ulang dari berkas yang ada; digest nilai diverifikasi cocok.
TA2 = ("Kontrak Reproduksibilitas", [
    ["Butir", "Nilai"],
    ["**Sumber keacakan**", ""],
    ["*seed* OOF (dirata-ratakan di dalam validasi silang)", "0, 1, 2"],
    ["*seed* pemasangan akhir", "0, 1, 2, 3, 4"],
    ["*seed* dasar model *increment*", "20260905, 5 *seed*"],
    ["RNG global yang dipakai jalur kode mana pun", "tidak ada"],
    ["**Masukan: hanya tiga berkas resmi**", ""],
    ["`train.csv` (494.807 bait)", "`efab54394fee7848983b3f27f44c2489`"],
    ["`test.csv` (117.567 bait)", "`e339e5aaa4c42bd8a948b9c2226951ed`"],
    ["`sample_submission.csv` (18.373 bait)", "`7338feec8ef625b60f448afe27d2fd8a`"],
    ["data eksternal · model *pretrained* · kode eksternal", "tidak ada · tidak ada · tidak ada"],
    ["**Kesesuaian skor (juknis 2.e)**", ""],
    ["md5 berkas yang di-submit ke Kaggle", "`70666a36066bb25b03ee4dce1b7fedcd`"],
    ["md5 berkas yang ditulis ulang notebook", "`a4658c492e2e16b951466d144d9226bb`"],
    ["skor publik terkait", "**2,82744**"],
    ["cara memeriksa", "unggah berkas keluaran notebook ke Kaggle"],
    ["**Lingkungan eksekusi**", ""],
    ["Python · NumPy · pandas", "3.11.6 · 2.4.6 · 2.2.3"],
    ["scikit-learn · SciPy · Matplotlib", "1.9.0 · 1.17.1 · 3.11.1"],
    ["LightGBM · CatBoost", "4.7.0 · 1.2.10"],
    ["runtime notebook end-to-end", "≈ 9 menit, CPU 8 inti"],
    ["kesamaan sampai digit terakhir", "terikat lingkungan di atas; anggota pohon "
                                       "bergantung urutan thread"],
], [1.55, 1.65], ['l', 'l'])


def _tabel_kanal():
    """TABEL A.III dibangun dari `figures/tabel_kanal.json`.

    24 baris angka terlalu banyak untuk disalin dengan tangan tanpa salah ketik
    yang tidak akan pernah ketahuan, jadi `make_figures.py` menuliskannya dan
    berkas ini hanya memformatnya.
    """
    import json
    import os
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     '..', 'figures', 'tabel_kanal.json')
    if not os.path.exists(p):
        raise SystemExit('figures/tabel_kanal.json tidak ada. '
                         'Jalankan dulu: python make_figures.py')
    with open(p, encoding='utf-8') as f:
        data = json.load(f)

    def koma(x):
        return '–' if x is None else ('%g' % x).replace('.', ',')

    rows = [["Kanal", "Hilang latih", "Hilang uji", "Rerata latih", "Rerata uji",
             "sd uji / sd latih", "Dipakai"]]
    for r in data:
        rows.append([
            '`%s`' % r['kolom'],
            koma(r['hilang_latih']) + ' %',
            koma(r['hilang_uji']) + ' %',
            koma(r['rerata_latih']),
            koma(r['rerata_uji']),
            ('**%s**' % koma(r['rasio_sd'])) if r['rasio_sd'] < 0.65 else koma(r['rasio_sd']),
            'ya' if r['dipakai'] else '**tidak**',
        ])
    return ("Audit Kelengkapan dan Dukungan Seluruh 24 Kanal Eksogen", rows,
            [1.32, 0.62, 0.58, 0.68, 0.62, 0.72, 0.48],
            ['l', 'r', 'r', 'r', 'r', 'r', 'c'])


TA3 = _tabel_kanal()
