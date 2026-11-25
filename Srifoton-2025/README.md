# SRIFOTON 2025 Machine Learning Competition

🥇 **Juara 1** · Sep 2025

Klasifikasi citra rontgen dada ke lima kelas: Bacterial Pneumonia, Corona Virus Disease, Normal, Tuberculosis, dan Viral Pneumonia. Model utama EfficientNet-B4 (`tf_efficientnet_b4_ns` dari timm) dengan weighted loss dan weighted sampler untuk menangani ketidakseimbangan kelas. Metrik F1.

## Isi

| Berkas | Isi |
|---|---|
| `srifoton.ipynb` | Notebook training dan inferensi (Kaggle) |
| `submission/Submission Maker.ipynb` | Penyusun berkas submission |
| `submission/submission*.csv` | Submission dari beberapa model dan varian (`model1`–`model3`, `two_stage`, `unet`, `sorted_final`); `submission.csv` adalah versi akhir |

## Tidak ikut di repo

- `best_model (1).pth` (68 MB), bobot model hasil training. Buat ulang dengan menjalankan `srifoton.ipynb`.
