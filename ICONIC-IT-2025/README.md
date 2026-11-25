# ICONIC IT 2025 Data Science Competition

🥈 **Juara 2** · Sep – Okt 2025 · Tim **Necrokeep**

**Nusantara Reef-Guardian**: prediksi risiko stres termal terumbu karang Indonesia dengan deep learning spatio-temporal. Data suhu permukaan laut harian NOAA Coral Reef Watch (5 km) dipotong ke wilayah Indonesia, dimasking dengan peta sebaran terumbu karang, lalu dipakai melatih model ConvLSTM2D yang memprediksi peta risiko ke depan. Hasilnya ditampilkan di dasbor Streamlit supaya konservasi bisa bergerak proaktif, bukan reaktif.

## Isi

| Berkas | Isi |
|---|---|
| `Dataset/Data Acquisition and Preprocessing.ipynb` | Unduh data NOAA CRW, potong wilayah, masking terumbu karang, simpan jadi array bulanan |
| `Model/Model.ipynb` | Training ConvLSTM2D dengan data generator hemat RAM |
| `Model/Evaluate Model.ipynb` | Evaluasi model |
| `Model/nusantara_reef_guardian_model.h5` | Bobot model hasil training |
| `app/` | Dasbor Streamlit: `app.py`, `generate output.py` (membuat `latest_prediction_data.csv`), peta terumbu karang Indonesia (shapefile), `requirements.txt` |
| `terumbu_karang_uts_2024_final.gpkg` | Layer GIS hasil prediksi |
| `Laporan_Necrokeep.pdf` | Laporan proyek (19 halaman) |
| `PPT Iconic IT.pdf` | Slide presentasi (versi terkompresi) |

Menjalankan dasbor:

```bash
cd app
pip install -r requirements.txt
python "generate output.py"
streamlit run app.py
```

## Tidak ikut di repo

Data mentah dan hasil preprocessing terlalu besar untuk GitHub (±4 GB). Buat ulang lewat `Dataset/Data Acquisition and Preprocessing.ipynb`:

- `Dataset/monthly_data/data_2024_01.npy` … `data_2024_12.npy` (250–300 MB per file)
- `Dataset/processed_masked_data.npz` (440 MB)

## Tim

Khairunnisa Keisha A., Raphael Angelo Adikara P., Timotius Christopher Patrick Sihombing
