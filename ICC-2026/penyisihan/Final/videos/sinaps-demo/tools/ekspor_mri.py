"""Ekspor citra MRI asli (bank kasus MVP, SOOP) + lesion mask ahli menjadi PNG untuk video.

Sumber: ../../mvp/public/cases (volume uint8) dan ../../mvp/server_data (sekuens + mask gt/pred).
Keluaran: assets/mri/<sub>/{dwi,adc,flair}_zNN.png, mask_zNN.png (oranye transparan),
pred_zNN.png (teal transparan), dan assets/mri/wall/*.png (satu slice per subjek).
"""
import gzip, json, sys
from pathlib import Path
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
MVP = ROOT.parents[1] / "mvp"
OUT = ROOT / "assets" / "mri"
idx = {c["id"]: c for c in json.loads((MVP / "public/cases/index.json").read_text())["cases"]}
srv = json.loads((MVP / "server_data/cases.json").read_text())


def vol(sub, seq):
    c = idx[sub]
    x, y, z = c["dimensions"]
    buf = (MVP / "public/cases" / sub / f"{srv[sub]['sequences'][seq]}.bin").read_bytes()
    if buf[:2] == bytes([0x1F, 0x8B]):  # berkas disimpan ter-gzip
        buf = gzip.decompress(buf)
    raw = np.frombuffer(buf, dtype=np.uint8)
    return raw.reshape(z, y, x)


def gray(a):
    # volume disimpan pada rentang 0-200 (window bawaan viewer), regangkan ke 0-255
    return Image.fromarray(np.clip(a.astype(np.float32) * 255 / 200, 0, 255).astype(np.uint8), "L")


def overlay(m, rgb, alpha=200):
    h, w = m.shape
    o = np.zeros((h, w, 4), np.uint8)
    o[m > 0] = (*rgb, alpha)
    return Image.fromarray(o, "RGBA")


def ekspor(sub, size=512):
    d = OUT / sub
    d.mkdir(parents=True, exist_ok=True)
    vs = {s.lower(): vol(sub, s) for s in ("DWI", "ADC", "FLAIR")}
    npz = np.load(MVP / "server_data/cases" / f"{sub}.npz")
    gt, pred = npz["gt"], npz["pred"]
    z = vs["dwi"].shape[0]
    print(sub, "vol", vs["dwi"].shape, "mask", gt.shape)
    for k in range(z):
        for s, v in vs.items():
            gray(v[k]).resize((size, size), Image.LANCZOS).save(d / f"{s}_z{k:02d}.png")
        # mask bisa beda ukuran (crop/pad) -> samakan ke ukuran citra lewat resize nearest
        for name, m, rgb in (("mask", gt, (240, 154, 108)), ("pred", pred, (95, 179, 191))):
            mk = m[:, :, k].T if m.shape[0] != z else m[k]
            overlay(mk, rgb).resize((size, size), Image.NEAREST).save(d / f"{name}_z{k:02d}.png")
    return srv[sub]["findings"]


def wall(n_size=160):
    d = OUT / "wall"
    d.mkdir(parents=True, exist_ok=True)
    for i, sub in enumerate(sorted(srv)):
        v = vol(sub, "DWI")
        k = srv[sub]["findings"].get("slice_lesi_terbesar", v.shape[0] // 2)
        gray(v[k]).resize((n_size, n_size), Image.LANCZOS).save(d / f"w{i:02d}.png")


if __name__ == "__main__":
    for sub in sys.argv[1:] or ["sub-1517"]:
        f = ekspor(sub)
        print(json.dumps({k: f[k] for k in ("volume_ml", "jumlah_fokus", "hemisfer", "slice_lesi_terbesar")}))
    wall()
