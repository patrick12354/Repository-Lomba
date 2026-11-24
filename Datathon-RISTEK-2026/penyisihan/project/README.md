# TATAP — triase skrining dini autisme berbasis kamera tablet

> ⚠️ **TATAP bukan alat diagnosis.** Keluarannya adalah skor risiko dan rekomendasi rujukan
> untuk kader Posyandu. Keputusan klinis tetap sepenuhnya pada tenaga kesehatan.

Datathon RISTEK Fasilkom UI 2026 — University Track, babak semifinal.

TATAP menyisip pada alur SDIDTK yang sudah berjalan di Posyandu. Anak usia 16–30 bulan
menonton stimulus adegan sosial ±2 menit di tablet Android biasa; kamera depan
mengestimasi arah pandang, sistem mengekstraksi geometri scanpath, lalu mengeluarkan skor
risiko beserta alasan yang bisa dibaca kader. Seluruh inferensi berjalan **luring di
perangkat**, karena wilayah dengan akses spesialis paling rendah justru wilayah dengan
konektivitas paling terbatas.

---

## 🚧 Status

Repo ini sedang dikerjakan untuk babak semifinal (30 Juli – 10 Agustus 2026).
Rencana lengkap: [`docs/rencana_semifinal.md`](docs/rencana_semifinal.md).

| Komponen | Status |
|---|---|
| POC pandangan (bukti empiris) | ✅ selesai, angka di `poc_hasil.json` |
| Concept paper preliminary | ✅ `paper/Rizzz_ConceptPaper.pdf` |
| Ablasi set fitur | ✅ `research/01_ablasi_fitur.ipynb` |
| Model produk + ekspor | 🚧 sedang dikerjakan |
| Studi degradasi domain | 🚧 sedang dikerjakan |
| Aplikasi PWA | 🚧 belum dimulai |
| Paper 12 halaman + Results | 🚧 belum dimulai |

**Cakupan bukti saat ini:** hanya cabang pandangan. Cabang gerak kepala/wajah dan
vokalisasi ada dalam rancangan arsitektur tetapi **belum punya model terlatih**, karena
belum ada kohort prospektif berpasangan. Ini ditulis eksplisit, bukan disembunyikan.

---

## Instalasi

Butuh Python 3.11+.

```bash
python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
```

Daftarkan kernel Jupyter (sekali saja):

```bash
python -m ipykernel install --user --name dataton --display-name "Dataton (.venv)"
```

## Menjalankan

Jalankan uji unit:

```bash
python -m pytest -q
```

Reproduksi angka POC preliminary di luar notebook (butuh beberapa menit):

```bash
cd poc && python recompute_metrics.py && python recompute_protokol.py
```

Notebook riset semifinal ada di `research/`. Buka lalu **Restart Kernel + Run All** —
tiap notebook menulis hasilnya ke `research/hasil/*.json`, sehingga setiap angka yang
dikutip di paper bisa dilacak balik ke berkas.

```bash
jupyter lab research/01_ablasi_fitur.ipynb
```

---

## Struktur

```
data/              dataset mentah
  autism eye tracking dataset/    anchor bukti empiris (real)
  Multimodal Autism Dataset/      ⚠️ sintetis, ilustrasi arsitektur saja

research/          kode & eksperimen semifinal
  features.py        ekstraksi 19 fitur scanpath — satu sumber kebenaran
  evaluate.py        helper CV group-aware, bootstrap, titik kerja, PPV
  late_fusion.py     weighted late fusion + quality gate
  01_ablasi_fitur.ipynb
  hasil/             keluaran notebook (JSON + cache fitur)

poc/               artefak preliminary — beku, jangan diubah
  poc_eyetracking.ipynb, poc_hasil.json
  recompute_metrics.py, recompute_protokol.py

paper/             concept paper (sumber LaTeX di paper/sumber/)
figs/              gambar paper + skrip generatornya
tests/             pytest
docs/              rencana semifinal, aturan lomba, riset impact
```

---

## Data

**Autism Eye Tracking Dataset** — 547 citra scanpath dari 54 partisipan
([Kaggle](https://www.kaggle.com/datasets/aqilamalfa/autism-eye-tracking), asal:
Carette dkk., DOI [10.5220/0007402601030112](https://doi.org/10.5220/0007402601030112)).
Ini satu-satunya sumber validasi empiris.

Dua hal yang wajib diperhatikan siapa pun yang memakainya:

- **Nama berkas `T{C,S}###_PP.png` — `PP` adalah ID partisipan.** Satu anak menyumbang
  banyak citra, jadi setiap pemisahan data **wajib** memakai GroupKFold per partisipan.
  Split acak menggelembungkan AUC sebesar 0,048 pada dataset ini.
- **Partisipan rata-rata berusia 7,88 tahun — anak usia sekolah, bukan balita.** Dataset
  ini memvalidasi *prinsip* bahwa geometri scanpath diskriminatif, bukan performa pada
  populasi sasaran produk. Asumsi transfer ini dinyatakan eksplisit di paper.

**Multimodal Autism Dataset** — ⚠️ terverifikasi **sintetis**: rata-rata fitur tiap
modalitas identik di keempat kelas. Dipakai **hanya** sebagai ilustrasi rancangan
arsitektur; tidak ada satu pun angka performa yang diambil darinya.

Bobot model dan dataset turunan akan diunggah ke Hugging Face dan ditautkan di sini.

---

## Catatan reproduksibilitas

Seluruh evaluasi memakai GroupKFold per partisipan, dan metrik utama dihitung pada
**unit anak** — bukan unit citra — karena itulah unit keputusan produk. Seed tetap di
`RANDOM_STATE = 42`. Notebook di-commit beserta output-nya supaya hasilnya bisa dibaca
tanpa menjalankan ulang.
