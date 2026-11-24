# Berkas yang dikumpulkan, NSC 2026 Penyisihan Data Science

Tim **Heisenberg** (`NSC26-DS042`). Isi folder ini adalah salinan final yang
diunggah ke panitia, dengan penamaan sesuai ketentuan.

| berkas | tujuan | dasar |
|---|---|---|
| `NSC26-DS042_Heisenberg_Notebook Data Science.ipynb` | Google Form | juknis 2.e |
| `NSC26-DS042_Heisenberg_File Data Science.pkl` | Google Form | juknis 2.e |
| `NSC26-DS042_Heisenberg_Data Science.pdf` | Google Form | juknis 3.e |
| `NSC26-DS042_Heisenberg_Submission Data Science.csv` | arsip berkas yang di-submit ke Kaggle | tidak diminta |

## Angka kunci

- RMSE papan peringkat publik **2,82744**
- md5 berkas yang dikirim ke Kaggle `70666a36066bb25b03ee4dce1b7fedcd`
- md5 berkas yang ditulis ulang notebook `a4658c492e2e16b951466d144d9226bb`

Cara memeriksa kesesuaian skor: jalankan notebook, ambil
`submission_nsc26_air_humidity.csv` yang ditulisnya, unggah ke Kaggle
Competition, lalu bandingkan skornya. Notebook sengaja tidak memasang pemeriksa
mandiri, karena kesamaan sampai bit terakhir bukan kriteria yang benar di sini:
penyelesai jarang menggeser satu baris sebesar 1e-15 antar-jalankan, dan build
LightGBM atau CatBoost yang berbeda menggeser prediksi sebesar RMS 0,29 %RH
tanpa memindahkan skor. Bagian 11.5 notebook dan Lampiran I laporan memuat
angkanya.

## Keadaan notebook saat dikumpulkan

77 sel (36 kode, 41 markdown) · 14 gambar · dieksekusi penuh dari atas ke bawah,
`execution_count` 1–36 berurutan, **0 error** · runtime ~25 menit · hanya membaca
`train.csv`, `test.csv`, dan `sample_submission.csv`.

## Laporan

16 halaman: badan Bagian I–VII bersama daftar pustaka berakhir di **halaman 10**
sesuai batas juknis 3.b, lampiran ditambahkan menurut 3.d mulai halaman 11.
Template IEEE A4 dengan border NSC di seluruh halaman.

## Membangun ulang

Notebook: jalankan dari atas ke bawah dengan `Dataset/` di sampingnya.
Laporan: `python make_figures.py` lalu `python build.py` dari `../paper/script/`.
Jangan menyunting DOCX atau PDF-nya langsung, keduanya ditimpa setiap build.
Setelah build, periksa hasilnya dari teks PDF dan bukan dari timestamp: Word
pernah menulis PDF bertimestamp baru dengan isi lama.
