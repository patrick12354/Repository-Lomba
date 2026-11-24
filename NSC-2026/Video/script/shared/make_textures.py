"""Procedural surface plates for both videos: aged ivory paper and charcoal ground.
Run: py -3 make_textures.py <out_dir>"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter

out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
rng = np.random.default_rng(734)

def fbm(h, w, octaves=6, base=4):
    acc = np.zeros((h, w)); amp = 1.0; tot = 0
    for o in range(octaves):
        s = base * 2 ** o
        g = rng.random((s + 1, int(s * w / h) + 2))
        img = Image.fromarray((g * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
        acc += amp * (np.asarray(img) / 255.0); tot += amp; amp *= 0.55
    return acc / tot

def paper(w=2400, h=1400):
    base = np.array([239, 229, 207], float)
    n = fbm(h, w, 7, 3)
    stains = fbm(h, w, 3, 2)
    stains = np.clip((stains - 0.55) * 3.0, 0, 1)
    fib = rng.random((h, w)); fibimg = Image.fromarray((fib * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.6))
    fib = np.asarray(fibimg) / 255.0
    # long fibres: streaks
    streak = Image.fromarray((rng.random((h // 8, w)) * 255).astype(np.uint8)).resize((w, h), Image.BILINEAR).filter(ImageFilter.GaussianBlur(1.2))
    streak = np.asarray(streak) / 255.0
    img = np.zeros((h, w, 3))
    for c in range(3):
        img[..., c] = base[c] * (0.93 + 0.09 * n) - stains * [26, 34, 48][c] + (fib - 0.5) * 9 + (streak - 0.5) * 7
    # soft crease
    yy, xx = np.mgrid[0:h, 0:w]
    crease = np.exp(-((xx - w * 0.62 + (yy - h / 2) * 0.08) ** 2) / (2 * 6 ** 2)) * 10
    img -= crease[..., None]
    # vignette
    v = ((xx / w - 0.5) ** 2 + (yy / h - 0.5) ** 2)
    img *= (1 - 0.22 * np.clip(v * 2.2, 0, 1) ** 1.6)[..., None]
    Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save(out / "paper.png", optimize=True)

def charcoal(w=1920, h=1080):
    n = fbm(h, w, 7, 3)
    m = fbm(h, w, 3, 2)
    g = rng.random((h, w)); g = np.asarray(Image.fromarray((g * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.7))) / 255.0
    lum = 19 + 10 * (n - 0.5) + 8 * (m - 0.5) + (g - 0.5) * 6
    # scratches
    sc = np.zeros((h, w))
    for _ in range(90):
        x0, y0 = rng.integers(0, w), rng.integers(0, h)
        ang = rng.normal(0.3, 0.6); ln = rng.integers(40, 260)
        t = np.linspace(0, 1, ln)
        xs = np.clip((x0 + np.cos(ang) * t * ln).astype(int), 0, w - 1); ys = np.clip((y0 + np.sin(ang) * t * ln).astype(int), 0, h - 1)
        sc[ys, xs] = rng.uniform(4, 11)
    sc = np.asarray(Image.fromarray(np.clip(sc * 20, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.8))) / 20.0
    lum = lum + sc
    img = np.stack([lum * 1.04, lum * 1.0, lum * 0.95], -1)
    Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save(out / "charcoal.png", optimize=True)

paper(); charcoal()
print("ok", out)
