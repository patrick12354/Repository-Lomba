# Bukti untuk deck: lapisan AI diagnosis PlantPulse

Semua angka di sini berasal dari uji internal kami (folder `evaluation/runs/`). Ini bukan hasil uji pilot, dan belum ditinjau ahli pabrik.

## 1. Kenapa kami tidak membuat "peramal kerusakan"

Kami menguji dulu: apakah sejarah kerusakan bisa menebak keluarga kerusakan berikutnya? Kami bagi data jadi "masa lalu" dan "masa depan" pada tiga tanggal.

| Tanggal potong | Kejadian setelahnya | Tertebak oleh 10 keluarga teratas | Porsi 10 keluarga teratas dari semua keluarga |
|---|---|---|---|
| 2025-01-01 | 232 | 12 (5,2%) | 5,6% |
| 2025-07-01 | 158 | 7 (4,4%) | 5,6% |
| 2026-01-01 | 84 | 4 (4,8%) | 5,6% |

Artinya: tebakan dari sejarah hanya sebaik tebakan acak. Dari 380 catatan, pasangan (pabrik, tag) yang berulang: 0. Hanya ada 5 kerusakan dengan data lengkap. Model peramal dari 5 kejadian akan terlihat bagus di demo, tetapi palsu.

## 2. Apa yang dilakukan AI kami

AI kami bekerja seperti dokter mesin:

1. Melihat gejala (bacaan sensor dan catatan mingguan).
2. Menyusun dugaan penyebab, diurutkan dari yang paling mungkin.
3. Menyarankan tes termurah untuk membedakan dugaan.
4. Menyarankan tindakan.
5. Setelah tindakan, memeriksa apakah mesin benar-benar pulih (bukti efektif).

Urutan dugaan dihitung dengan aturan yang bisa diulang dan diperiksa. AI bahasa hanya menjelaskan, dan boleh tidak setuju asalkan menyebut sumbernya.

## 3. Hasil pencocok gejala

Kami menjalankan pencocok minggu demi minggu pada 5 mesin. Setiap huruf adalah satu minggu (mulai minggu ke-7): `.` = belum jelas, `T` = penyebab tercatat ada di daftar teratas, `U` = penyebab tercatat menjadi satu-satunya peringkat 1, `X` = salah.

| Mesin | Pola per minggu |
|---|---|
| PU-2101B | `..TUUUUUUUUUUU` |
| KO-3201 | `.TUUUUUUUUUUUU` |
| PM-4405B | `..UUUUUUUUUUUU` |
| HE-3301 | `.UUUUUUUUUUUUU` |
| BL-5702 | `.XUUUUUUUUUUUU` |

Penyebab yang tercatat di RCA menjadi satu-satunya dugaan peringkat 1 pada 11 sampai 13 minggu sebelum mesin trip. Pada 4 dari 5 mesin, ini terjadi sebelum label ALARM pertama. BL-5702 sempat salah selama 1 minggu.

Batasan yang harus kami sebut jujur: daftar penyebab (library) kami tulis setelah membaca RCA, dan datasetnya memilih sensor yang cocok dengan penyebabnya. Jadi ini bukti bahwa alurnya jalan, bukan bukti akurasi di pabrik lain.

## 4. Uji AI investigator dengan RCA disembunyikan

Kami menyembunyikan RCA, lalu meminta AI menyusun dugaan dari data yang tersedia saat itu. Kunci jawaban dikunci sebelum AI dijalankan. Ini uji internal.

- Peringkat 1 benar: 7 dari 9.
- Jawaban benar ada di 3 teratas: 9 dari 9.
- Pemeriksa bisa membedakan jawaban benar: 8 dari 9.
- Kebocoran RCA ke AI: 0.

Dua kasus yang meleset adalah minggu 8 KO-3201 dan minggu 8 BL-5702. Keduanya minggu awal yang memang masih ambigu.

## 5. Ramalan kondisi (Chronos-2)

Kami uji ramalan mingguan pada 160 kasus (horizon 8 minggu).

| Ukuran | Chronos-2 | Tren linear |
|---|---|---|
| Rata-rata selisih minggu | 1,38 minggu | 1,55 minggu |
| Kasus tanpa perkiraan melewati batas | 89 dari 160 | 62 dari 160 |
| Pita (P90 sampai P10) memuat minggu trip sebenarnya | 64% | tidak ada |

Data kami hampir linear, jadi tren linear sudah sangat kuat. Selisih Chronos terlihat lebih kecil hanya karena dihitung pada lebih sedikit kasus. Karena itu angka utama di aplikasi adalah perkiraan linear, dan Chronos dipakai sebagai pita ketidakpastian. Untuk data per jam, pita Chronos menyala 13 sampai 24 kali per mesin, jadi detektor MAD yang sudah ada tetap yang utama.

Ramalan energi (arus motor, 168 jam uji), galat WAPE Chronos-2 dibanding tebakan sederhana terbaik: PU-2101B 2,31% vs 3,03%, KO-3201 25,65% vs 25,47%, PM-4405B 2,35% vs 3,33%, BL-5702 2,34% vs 2,64%. Hanya KO-3201 yang tidak lebih baik.

## 6. Efektivitas tindakan

- KO-3201: kondisi sudah pulih, tetapi baru 5 dari 8 minggu pengamatan, dan 5 tindakan sumber belum berstatus Closed.
- HE-3301: belum pulih (Cold Outlet Temp masih di bawah batas normal).

## 7. Pilihan model

| Topik | Keputusan | Alasan singkat |
|---|---|---|
| Model peramal kerusakan | Tidak dibuat | Data terlalu sedikit (bagian 1) |
| Model deret waktu | Chronos-2 | Tanpa pelatihan, bisa jalan lokal di CPU sehingga data pabrik tetap di dalam |
| Pembanding | Toto 2.0 (opsional) | Uji kami sendiri yang menentukan, bukan peringkat publik |
| JEPA | Peta jalan tahun ke-2 | Butuh data historian bertahun-tahun; kami hanya punya 3.600 baris per jam |
| Jev | Tidak dipakai | Model klasifikasi, bukan deret waktu; API tertutup dan hanya cloud; hasil uji dilaporkan sendiri |
| Peringkat penyebab | Aturan pasti yang menghitung, AI menjelaskan | Hasil harus bisa diulang dan diaudit |

## 8. Kalimat kunci untuk deck

Kalau kita bikin AI "peramal kerusakan", hasilnya pasti kelihatan bagus di demo tapi palsu, dan juri yang engineer bisa membongkarnya.

Versi slide (Inggris): "A failure 'predictor' on five failures would look great in a demo and be fake. Engineers would see through it. We built the AI the data can support."
