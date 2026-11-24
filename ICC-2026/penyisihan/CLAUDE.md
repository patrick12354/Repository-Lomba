# Satu Data 2026 — Repo Kompetisi

Repo untuk pengerjaan kompetisi data Satu Data 2026. Dua case terpisah, masing-masing
berdiri sendiri dengan dataset dan notebook-nya.

```
Satu Data/
├── .vscode/settings.json     interpreter + kernel -> venv bersama
├── Case 1/                   prediksi magnitudo gempa dari waveform seismik
│   ├── seismic-dataset/      data mentah (TIDAK di-commit, lihat .gitignore)
│   ├── eda.ipynb             notebook EDA + baseline
│   ├── notebook_1.ipynb      iterasi 1 (CV 0,1826 -> LB 0,2005)
│   ├── notebook_2.ipynb      iterasi 2 GAGAL (CV 0,1789 -> LB 0,2262)
│   ├── notebook_3.ipynb      post-mortem + pipeline terkoreksi (CV 0,1855 -> LB 0,1996, TERBAIK)
│   ├── notebook_4.ipynb      7 ide diuji, 6 gagal; tidak disubmit
│   ├── notebook_5.ipynb      anchor ridge + bobot per-subset GAGAL (LB 0,2063)
│   ├── notebook_6.ipynb      metrik CV diperbaiki + blend 7 kandidat (LB 0,1952)
│   ├── notebook_7.ipynb      8 ide diuji, 7 gagal; tidak disubmit
│   ├── notebook_8.ipynb      CNN v3 multi-task (LB 0,1849, PERINGKAT 2)
│   ├── notebook_9.ipynb      koreksi set-transformer di-demean GAGAL (LB 0,1856)
│   ├── notebook_10.ipynb     bobot blend condong sisi desimal GAGAL (LB 0,1871)
│   ├── belum_run/            antrian run GPU panjang (>30 mnt) — KOSONG, + ref/ untuk Kaggle
│   ├── sudah_run/            arsip run yang selesai (10 notebook) + hasil/ (versi tereksekusi)
│   ├── lab/                  modul pipeline lab_*.py + fastscore.py (hasil model di-cache)
│   ├── experiments/          exp*.py — probe sekali-pakai per ide
│   ├── tools/                mk_nb*.py + mk_kaggle*.py generator, serap_*.py penyerap hasil
│   ├── cache/                OOF/test pred per model (TIDAK di-commit)
│   ├── submission/           notebook_N.csv, _score.json, LEADERBOARD.md
│   ├── penjelasan_case.md    analisis & strategi
│   └── CLAUDE.md             detail teknis Case 1
└── Case 2/                   (belum ada soal/data)
```

## Environment — venv bersama, jangan bikin baru

Semua pekerjaan pakai satu venv di luar repo:

```
C:\Patrick\coding\.venv\Scripts\python.exe      (Python 3.11.6)
```

Sudah berisi: numpy 1.26.4, pandas 2.3.3, scipy 1.17.1, scikit-learn 1.6.1,
matplotlib 3.7.5, seaborn 0.13.2, lightgbm 4.6.0, xgboost 3.0.3,
torch 2.6.0+cu124 (CUDA aktif), ipykernel 6.30.0.

**Jangan `python -m venv` di folder case manapun.** VS Code sudah diarahkan ke venv ini
lewat `.vscode/settings.json`, jadi tombol Run dan kernel notebook otomatis benar.

### Peringatan interpreter

`python` polos di PATH menunjuk ke **Python 3.14 sistem yang kosong** — numpy pun tidak ada.
Di terminal, selalu pakai path lengkap venv (atau aktifkan venv dulu):

```bash
C:/Patrick/coding/.venv/Scripts/python.exe -c "import numpy; print(numpy.__version__)"
```

### GPU

Mesin ini punya **NVIDIA RTX 4060 (8 GB VRAM)** dan `torch.cuda.is_available()` bernilai
`True`. Kalau ada run yang bisa dipercepat pakai GPU (training model torch, dll), **pakai
GPU** — jangan lupa `.to("cuda")` / device placement yang sesuai. Kalau memang cuma bisa
CPU (library tidak support GPU, model kecil sekali, dll), ya tidak apa-apa.

**Batasnya 30 menit — estimasi dulu sebelum menekan Run:**

| estimasi waktu | jalankan di mana |
|---|---|
| **< 30 menit** | **lokal**, langsung di sesi ini. Tidak perlu Kaggle. |
| **> 30 menit** | **Kaggle.** Bungkus jadi notebook mandiri, taruh di `belum_run/`, serahkan ke user. |

Alasannya bukan soal kecepatan kartunya, tapi soal sesi yang tersandera: RTX 4060 pernah
dipakai 3 jam untuk dua notebook lalu **dihentikan sebelum menghasilkan angka apa pun** —
waktunya nyata, hasilnya nol. Kaggle jalan di latar sementara pekerjaan lain lanjut, dan
kuotanya terpisah dari mesin ini.

Konvensi lengkap `belum_run/` -> `sudah_run/` (aturan penulisan notebook, pola path Kaggle,
checklist sel Setup) ada di [`Case 1/CLAUDE.md`](Case%201/CLAUDE.md) bagian **"Konvensi run
GPU panjang"** dan **"Path di notebook Kaggle"**.

## Menjalankan notebook dari CLI

```bash
C:/Patrick/coding/.venv/Scripts/python.exe -m jupyter nbconvert --to notebook --execute --inplace "Case 1/eda.ipynb"
```

`jupyter.notebookFileRoot` diset ke `${fileDirname}`, jadi notebook memakai **path relatif
terhadap foldernya sendiri** (mis. `seismic-dataset/...` dari dalam `Case 1/`). Pertahankan
konvensi ini saat menambah notebook baru.

## Data tidak masuk git

`train_waveforms.npy` berukuran 126 MB — di atas batas 100 MB per file GitHub. Seluruh
folder dataset di-ignore. Kalau clone di mesin baru, dataset harus diunduh ulang dari
platform kompetisi dan ditaruh di `Case 1/seismic-dataset/`.

## Konvensi

- Bahasa dokumen dan komentar: **Indonesia**. Istilah teknis (feature engineering,
  cross-validation, sample weighting) biarkan dalam bahasa Inggris.
- Setiap case punya `penjelasan_case.md` — analisis naratif dengan angka hasil pengukuran
  nyata, bukan asumsi. Kalau sebuah klaim belum diuji, tandai eksplisit.
- Notebook di-commit **beserta output**-nya supaya hasil bisa dibaca tanpa menjalankan ulang.
- Root tiap folder case hanya berisi `.md` dan `.ipynb`. Kode `.py` masuk subfolder
  (`lab/` modul pipeline, `experiments/` probe sekali-pakai, `tools/` generator).
  Notebook membuka dengan `sys.path.insert(0, os.path.abspath("lab"))`; skrip di
  subfolder cukup `import _path`.
- **Catat tiap skor LB di `Case 1/submission/LEADERBOARD.md`** begitu keluar. Hubungan
  CV↔LB di case ini tidak lurus (pernah berlawanan arah), jadi titik LB nyata adalah
  informasi paling berharga yang ada — jangan sampai hilang.
- File submission dinamai **sama dengan notebook yang menghasilkannya**
  (`notebook_1.ipynb` -> `submission/notebook_1.csv`), supaya tiap skor bisa dilacak
  balik ke notebook-nya. Folder `submission/` ikut di-commit; hanya dataset yang di-ignore.
