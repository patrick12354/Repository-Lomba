# Intelecta Cup 2025, Data Mining

🥇 **Juara 1** · Okt – Nov 2025 · Tim **Dauntless** (Universitas Airlangga)

Dua babak dengan dua kasus berbeda:

| Babak | Kasus | Pendekatan |
|---|---|---|
| [`penyisihan/`](penyisihan) | Prediksi suhu rata-rata tahunan (`Suhu_Rata_Rata_C`) dari data agrikultur, lingkungan, dan geo-temporal. Metrik MAPE. | Winsorisasi + Yeo-Johnson, rekayasa fitur temporal dan interaksi, ensemble hibrida CatBoost + LightGBM dengan GroupKFold, dioptimasi khusus untuk MAPE yang meledak di nilai aktual dekat nol |
| [`final/`](final) | Klasifikasi audio bioakustik 31 spesies mamalia laut. | Mel-spectrogram ke EfficientNet-B2 (mixup, label smoothing, StratifiedGroupKFold), model spesialis berbasis PCEN untuk spesies langka seperti Weddell Seal dan paus bergigi, soft voting |

## Isi

### `penyisihan/`

| Berkas | Isi |
|---|---|
| `Dauntless_DataMining_Code_Qualifying.ipynb` (+ `.zip`) | Notebook final yang dikumpulkan |
| `Dauntless_DataMining_Report_Qualifying.pdf` | Makalah penyisihan |
| `intelecta-cup-eda.ipynb` | Eksplorasi data |
| `MAPE 87.ipynb`, `MAPE 100.ipynb` | Eksperimen dengan skor MAPE masing-masing |
| `Cek Submission.ipynb`, `cek mape.py` | Pengecekan submission dan metrik |
| `Dataset/`, `Dataset Asli.csv`, `kunci jawaban test.csv` | Dataset lomba dan kunci jawaban test |
| `Prediksi Suhu Masa Depan dengan Machine Learning.pdf` | Soal penyisihan |

### `final/`

| Berkas | Isi |
|---|---|
| `Dauntless_DataMining_FinalCode.ipynb` (+ `.zip`) | Notebook final yang dikumpulkan |
| `Dauntless_DataMining_FinalReport.pdf`, `Makalah Final.pdf` | Makalah final |
| `Dauntless_DataMining_Presentation_Final.pdf` | Slide presentasi final (`(2)` adalah versi terkompresi) |
| `EDA.ipynb`, `baseline-model.ipynb` | Eksplorasi data dan baseline |
| `0,9 (resnet).ipynb`, `0,92 (efficientnet).ipynb`, `0.94 (no weddell seal).ipynb`, `0,95 (Soft Voting).ipynb`, `0,95 (bias +0,25, sperm_whale F1 Macro 0.71).ipynb` | Eksperimen; nama berkas = skor F1 macro |
| `Petunjuk Teknis Final Intelecta Cup 2025.pdf` | Juknis final |

## Tim

Raphael Angelo Adikara P., Timotius Christopher Patrick Sihombing, M. Devian Rafi R. Z.
