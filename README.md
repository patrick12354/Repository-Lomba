# Repository Lomba

Kumpulan kode dan deliverable dari lomba-lomba yang pernah kami ikuti. Satu lomba satu folder; tiap folder punya README sendiri.

| Lomba | Hasil | Waktu | Proyek | Folder | Repo asli |
|---|---|---|---|---|---|
| Chandra Asri Innovation and Business Strategy Challenge (CALIBER) 2026 | 🥇 **Juara 1** dari 120 tim | Okt – Nov 2026 | **PlantPulse** (penyisihan) dan **Sparekit** (final): perencanaan spare part dengan forecast LightGBM + Monte Carlo dan Min-Max dinamis | [`CALIBER-2026`](CALIBER-2026) | [Penyisihan](https://github.com/raphaeladikara/Caliber-2026-Heisenberg) · [Final](https://github.com/raphaeladikara/caliber-final) |
| National Statistics Challenge (NSC) 2026 (Universitas Brawijaya) | 🥈 **Juara 2** dari 70 tim | Okt 2026 | Forecast 734 nilai kelembapan setengah-jaman lewat tekanan uap air, stacking 6 model, rekonsiliasi lintasan; RMSE 2,827 | [`NSC-2026`](NSC-2026) | [patrick12354/NSC_2026_Heisenberg](https://github.com/patrick12354/NSC_2026_Heisenberg) |
| Innovation Case Competition (ICC), Campus Data Week 2026 (Universitas Airlangga) | 🥈 **Juara 2** dari 100 tim | Agu – Okt 2026 | Case seismik & compiler (penyisihan) dan **SINAPS** (final): tutor MRI stroke adaptif | [`ICC-2026`](ICC-2026) | [Penyisihan](https://github.com/patrick12354/satu-data-all) · [Final](https://github.com/raphaeladikara/satu-data-final) |
| Hackathon Informatics Festival (IFest) 2026 (Universitas Padjadjaran) | 🥈 **Juara 2** dari 90 tim | Sep 2026 | **Nyambung**: papan AAC offline-first untuk anak autis nonverbal + dashboard terapis | [`IFest-2026`](IFest-2026) | [MikaelAdikara/Nyambung](https://github.com/MikaelAdikara/Nyambung) |
| AI Innovation Challenge, COMPFEST 18 (Universitas Indonesia) | 🥇 **Juara 1** dari 600 tim | Agu – Sep 2026 | **Deciqo**: ulasan pelanggan seller online jadi daftar masalah prioritas + draf listing yang ditahan sampai fakta dikonfirmasi | [`COMPFEST-18`](COMPFEST-18) | [MikaelAdikara/Deciqo](https://github.com/MikaelAdikara/Deciqo) |
| RISTEK Fasilkom UI Datathon 2026 | 🥈 **Juara 2** dari 250 tim | Agu 2026 | **Neurogaze**: PWA tablet luring untuk triase skrining autisme dari scanpath pandangan | [`Datathon-RISTEK-2026`](Datathon-RISTEK-2026) | [Penyisihan](https://github.com/patrick12354/Dataton-2026---Rizzz) · [Final](https://github.com/raphaeladikara/Dataton_Project_Rizzz) |
| SPARC 2026 Data Science Competition (Universitas Ciputra) | 🥇 **Juara 1** dari 130 tim | Feb – Mar 2026 | Prediksi prioritas follow-up repeat order di industri otomotif | [`SPARC-2026`](SPARC-2026) | [patrick12354/Sparc2026](https://github.com/patrick12354/Sparc2026) |
| Intelecta Cup 2025, Data Mining | 🥇 **Juara 1** | Okt – Nov 2025 | Prediksi suhu dengan ensemble CatBoost + LightGBM untuk MAPE (penyisihan) dan klasifikasi audio 31 spesies mamalia laut dengan EfficientNet-B2 + model spesialis PCEN (final) | [`Intelecta-Cup-2025`](Intelecta-Cup-2025) | – |
| Gelar Rasa 2025 Data Science Competition | 🥈 **Juara 2** | Okt – Nov 2025 | Forecast penjualan FMCG personal care: topik & sentimen ulasan (BERTopic + IndoBERT) dan model hibrida GNN + MLP untuk efek kanibalisasi produk | [`Gelar-Rasa-2025`](Gelar-Rasa-2025) | – |
| ICONIC IT 2025 Data Science Competition | 🥈 **Juara 2** | Sep – Okt 2025 | **Nusantara Reef-Guardian**: prediksi risiko stres termal terumbu karang Indonesia dengan ConvLSTM + dasbor Streamlit | [`ICONIC-IT-2025`](ICONIC-IT-2025) | [Dasbor](https://github.com/raphaeladikara/nusantara-reef-guardian) |
| SRIFOTON 2025 Machine Learning Competition | 🥇 **Juara 1** | Sep 2025 | Klasifikasi rontgen dada 5 kelas (pneumonia, COVID-19, TBC, normal) dengan EfficientNet-B4 | [`Srifoton-2025`](Srifoton-2025) | – |

## Struktur

```
.
├── CALIBER-2026/
│   ├── penyisihan/           # PlantPulse
│   └── final/                # Sparekit
├── NSC-2026/                 # Prediksi kelembapan udara
├── ICC-2026/
│   ├── penyisihan/           # Case seismik & compiler, paper semifinal
│   └── final/                # SINAPS
├── IFest-2026/               # Nyambung
├── COMPFEST-18/              # Deciqo
├── Datathon-RISTEK-2026/
│   ├── penyisihan/           # Concept paper TATAP + 2 task Kaggle
│   └── final/                # Neurogaze
├── SPARC-2026/               # Notebook EDA & modeling
├── Intelecta-Cup-2025/
│   ├── penyisihan/           # Prediksi suhu (MAPE)
│   └── final/                # Klasifikasi audio mamalia laut
├── Gelar-Rasa-2025/          # Forecast penjualan FMCG
├── ICONIC-IT-2025/           # Nusantara Reef-Guardian
└── Srifoton-2025/            # Klasifikasi rontgen dada
```

Isi tiap folder adalah salinan repo aslinya (tanpa riwayat git). Folder lomba 2025 disalin dari arsip lokal karena tidak punya repo sendiri. Sebagian repo asli bersifat private, jadi tautannya mungkin tidak bisa dibuka publik.

## Catatan

- Enam CSV submission Task 1 (`Datathon-RISTEK-2026/penyisihan/day 1/patrick/submissions/datathon_task1_v*.csv`, 57–73 MB per file) tidak ikut di repo ini karena ukurannya. File-file itu ada di [repo asli penyisihan](https://github.com/patrick12354/Dataton-2026---Rizzz/tree/main/day%201/patrick/submissions).
- Di folder lomba 2025, file yang terlalu besar untuk GitHub tidak ikut: data mentah ICONIC IT (±4 GB), `sales.csv` Gelar Rasa, dan bobot model Srifoton. Daftarnya ada di README masing-masing folder.
- Semua proyek dikerjakan dalam tim; nama anggota ada di README masing-masing folder.
