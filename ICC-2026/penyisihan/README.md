# Satu Data 2026 — AI Innovation Case

> Babak penyisihan & semifinal Innovation Case Competition (ICC), Campus Data Week 2026 (hasil akhir: 🥈 Juara 2 dari 100 tim). Repo asli: [patrick12354/satu-data-all](https://github.com/patrick12354/satu-data-all)

Repo pengerjaan kompetisi Satu Data 2026. Tim: **Rizzz**.

Snapshot leaderboard di bawah diambil dari papan peringkat publik platform kompetisi.

---

## Case Task 1 — Seismic Magnitude Prediction

Prediksi magnitudo gempa dari waveform seismik. Metrik: **EB-TWMAE** (makin kecil makin baik).

| # | Team | Members | Score | Entries | Last |
|---:|---|---:|---:|---:|---|
| 1 | Letdown | 3 | 0.1835 | 7 | 1h |
| 2 | Kingpul | 3 | 0.1837 | 2 | 2d |
| **3** | **Rizzz** 👈 | **2** | **0.1849** | **8** | **9m** |
| 4 | EspressoCampurRedbull | 1 | 0.1860 | 3 | 1d |
| 5 | suka suka gw | 3 | 0.1905 | 7 | 2h |
| 6 | cupuu | 4 | 0.1998 | 7 | 12m |
| 7 | Mio Mberrr | 3 | 0.2040 | 3 | 9h |
| 8 | hansen bilang meong aja | 4 | 0.2109 | 2 | 1d |
| 9 | IRIS kata HQ ini lomba trakhir | 4 | 0.2112 | 5 | 1h |
| 10 | AMAX+ kw | 3 | 0.2147 | 5 | 15h |
| 11 | Nasi Cumi Hitam Pak Kris | 3 | 0.2172 | 6 | 1d |
| 12 | 2W2H | 4 | 0.2221 | 5 | 20h |

> Submission terakhir **Rizzz** memperoleh 0.1871; skor terbaik tetap **0.1849** (`notebook_8.csv`).

Log lengkap tiap submission (CV, `lb_real`, estimasi, LB aktual, dan apa yang berubah) ada di
[`Case 1/submission/LEADERBOARD.md`](Case%201/submission/LEADERBOARD.md).

---

## Case Task 2 — Compiler Classification

Klasifikasi compiler. Metrik: skor akurasi (makin besar makin baik).

| # | Team | Members | Score | Entries | Last |
|---:|---|---:|---:|---:|---|
| **1** | **Rizzz** 👈 | **3** | **0.611** | **9** | **1h** |
| 2 | Letdown | 3 | 0.609 | 9 | 13h |
| 3 | 2W2H | 4 | 0.608 | 10 | 1h |
| 4 | cupuu | 4 | 0.604 | 8 | 14h |
| 5 | hansen bilang meong aja | 4 | 0.603 | 5 | 7h |
| 6 | EspressoCampurRedbull | 1 | 0.603 | 3 | 3d |
| 7 | suka suka gw | 3 | 0.601 | 9 | 1d |
| 8 | Nasi Cumi Hitam Pak Kris | 3 | 0.601 | 9 | 6h |
| 9 | blind leading the blind aja | 4 | 0.599 | 7 | 1d |
| 10 | IRIS kata HQ ini lomba trakhir | 4 | 0.599 | 7 | 16h |

> Submission terakhir **Rizzz** memperoleh 0.601; skor terbaik tetap **0.611** (peringkat 1).

---

## Struktur repo

Detail teknis, konvensi, dan environment ada di [`CLAUDE.md`](CLAUDE.md) dan
[`Case 1/CLAUDE.md`](Case%201/CLAUDE.md).

```
Satu Data/
├── Case 1/   prediksi magnitudo gempa dari waveform seismik
└── Case 2/   klasifikasi compiler
```

Dataset mentah tidak di-commit (lihat `.gitignore`) — unduh ulang dari platform kompetisi.
