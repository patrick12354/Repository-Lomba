# Gelar Rasa 2025 Data Science Competition

🥈 **Juara 2** · Okt – Nov 2025 · Tim **Dauntless**

Studi kasus FMCG personal care: dataset sintetis 1 juta transaksi (2020–2025) beserta data produk, kampanye marketing, dan ulasan pelanggan. Tujuannya *innovation radar*, *trend forecasting*, dan analisis kanibalisasi produk.

Dari EDA, penjualan harian ternyata tidak punya tren maupun musiman (pola *random walk*, ACF datar), jadi model time-series biasa tidak cocok. Penjualan bereaksi pada kampanye, diskon, dan sentimen. Pendekatannya:

1. **NLP ulasan**: BERTopic + IndoBERT untuk topik dan sentimen sebagai fitur.
2. **Master table** yang menggabungkan penjualan, marketing, dan fitur ulasan.
3. **Baseline XGBoost** dengan transformasi log pada target (MAPE turun dari 54% ke 48%).
4. **Model hibrida GNN + MLP**: graf antarproduk untuk menangkap efek kanibalisasi, digabung dengan fitur tabular.

## Isi

| Berkas | Isi |
|---|---|
| `DSC2025_Dauntless_Timotius Christopher Patrick Sihombing.ipynb` | Notebook final yang dikumpulkan |
| `DSC2025_Dauntless_Timotius Christopher Patrick Sihombing.pdf` / `.pptx` | Slide presentasi |
| `gelar-rasa.ipynb` | Notebook kerja |
| `Kerangka Kerja Proyek GENESIS_ Simulasi Kausal.pdf` | Kerangka kerja proyek |
| `BOOKLET STUDY CASE DSC.pdf` | Booklet studi kasus |
| `Dataset/` | `products.csv`, `marketing.csv`, `reviews.csv`, dan README dataset |

## Tidak ikut di repo

- `Dataset/sales.csv` (96 MB, 1 juta baris), terlalu besar untuk GitHub. Tautan unduhan resmi ada di booklet: bit.ly/DatasetDSCGelarRasa2025.

## Tim

Ketua: Timotius Christopher Patrick Sihombing
