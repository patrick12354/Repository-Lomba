"""Bahan scene U-Net (frame 11a): slice resolusi asli + prediksi U-Net asli dari satu kasus bank.

Sumber sama dengan ekspor_mri.py (volume MVP + mask prediksi U-Net di server_data). Keluaran di assets/mri/unet/:
  {dwi,adc}_z{13,14,15}.png   slice resolusi asli 224 px: tiga slice bertetangga = enam kanal masukan U-Net 2.5D
  pred_z14.png                prediksi U-Net (teal), resolusi asli
Jalankan: C:/Patrick/coding/.venv/Scripts/python.exe tools/ekspor_unet.py
"""
import numpy as np

from ekspor_mri import OUT, MVP, gray, overlay, vol

SUB, Z = "sub-1413", 14


def main():
    d = OUT / "unet"
    d.mkdir(parents=True, exist_ok=True)
    vs = {s.lower(): vol(SUB, s) for s in ("DWI", "ADC")}
    zn = vs["dwi"].shape[0]
    for k in (Z - 1, Z, Z + 1):
        for s, v in vs.items():
            gray(v[k]).save(d / f"{s}_z{k:02d}.png")
    pred = np.load(MVP / "server_data/cases" / f"{SUB}.npz")["pred"]
    pr = pred[:, :, Z].T if pred.shape[0] != zn else pred[Z]
    overlay(pr, (95, 179, 191), 255).save(d / f"pred_z{Z:02d}.png")


if __name__ == "__main__":
    main()
