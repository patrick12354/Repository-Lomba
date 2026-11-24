"""Procedural walnut desk top for slide 14 (top-down, planks run horizontally).
Run: py -3 make_desk.py <out_dir>"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter

out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
rng = np.random.default_rng(1434)
W, H = 2880, 1620

def fbm(h, w, octaves=6, base=4, sx=1.0):
    acc = np.zeros((h, w)); amp = 1.0; tot = 0
    for o in range(octaves):
        s = base * 2 ** o
        g = rng.random((s + 1, int(s * sx * w / h) + 2))
        img = Image.fromarray((g * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
        acc += amp * (np.asarray(img) / 255.0); tot += amp; amp *= 0.55
    return acc / tot

yy, xx = np.mgrid[0:H, 0:W].astype(float)
planks = [0, 300, 640, 930, 1270, 1620]
lum = np.zeros((H, W))
for i in range(len(planks) - 1):
    a, b = planks[i], planks[i + 1]
    m = (yy >= a) & (yy < b)
    warp = fbm(H, W, 5, 2, 0.35) * 420 + np.sin(xx / (520 + 140 * i) + i) * 60
    per = 26 + 18 * fbm(H, W, 3, 2, 0.3)
    rings = np.sin((yy - a + warp) / per * 2 * np.pi * 0.5 + i * 3.1)
    rings = np.clip(rings * 1.6, -1, 1) * 0.5 + 0.5
    streak = np.asarray(Image.fromarray((rng.random((H, W // 60)) * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC).filter(ImageFilter.GaussianBlur(1.0))) / 255.0
    tone = 0.9 + 0.2 * rng.random()
    lum[m] = (tone * (0.6 - 0.09 * rings + 0.16 * (streak - 0.5)))[m]
    lum[(yy >= a) & (yy < a + 4)] = 0.18  # seam
lum += (fbm(H, W, 6, 3) - 0.5) * 0.18
pores = np.asarray(Image.fromarray((rng.random((H // 3, W)) * 255).astype(np.uint8)).resize((W, H), Image.BILINEAR).filter(ImageFilter.GaussianBlur(0.7))) / 255.0
lum += (pores - 0.5) * 0.10
img = np.stack([lum * 118, lum * 74, lum * 44], -1)
# scratches + a coffee ring
for _ in range(60):
    x0, y0 = rng.integers(0, W), rng.integers(0, H)
    ang = rng.normal(0.05, 0.4); ln = rng.integers(60, 340)
    t = np.linspace(0, 1, ln)
    xs = np.clip((x0 + np.cos(ang) * t * ln).astype(int), 0, W - 1); ys = np.clip((y0 + np.sin(ang) * t * ln).astype(int), 0, H - 1)
    img[ys, xs] += rng.uniform(10, 22)
r = np.hypot(xx - 2470, yy - 1380)
img -= (np.exp(-((r - 118) ** 2) / (2 * 5 ** 2)) * 26 + np.exp(-((r - 112) ** 2) / (2 * 14 ** 2)) * 8)[..., None]
img = np.clip(img, 0, 255).astype(np.uint8)
Image.fromarray(img).filter(ImageFilter.GaussianBlur(0.5)).save(out / "desk.jpg", quality=88)
print("ok", out)
