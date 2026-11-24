"""Procedural cork-board plate + grain for slide 10 (seeded). Run: py -3 make_cork.py <out_dir>"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter

out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
rng = np.random.default_rng(7341)

def fbm(h, w, octaves=6, base=4):
    acc = np.zeros((h, w)); amp = 1.0; tot = 0
    for o in range(octaves):
        s = base * 2 ** o
        g = rng.random((s + 1, int(s * w / h) + 2))
        img = Image.fromarray((g * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
        acc += amp * (np.asarray(img) / 255.0); tot += amp; amp *= 0.55
    return acc / tot

def cork(w=2880, h=1620):
    base = np.array([158, 112, 70], float)
    n = fbm(h, w, 6, 4)
    # granules: many small dark/light specks of varied size
    spec = np.zeros((h, w))
    for size, count, amp in [(1, 260000, 1.0), (2, 60000, 0.8), (3, 14000, 0.7), (5, 3000, 0.6)]:
        ys = rng.integers(0, h, count); xs = rng.integers(0, w, count); v = rng.normal(0, 1, count) * amp
        for dy in range(size):
            for dx in range(size):
                spec[np.clip(ys + dy, 0, h - 1), np.clip(xs + dx, 0, w - 1)] += v
    spec = np.asarray(Image.fromarray(np.clip(128 + spec * 40, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.9))) / 255.0 - 0.5
    blot = fbm(h, w, 3, 3)
    img = np.zeros((h, w, 3))
    for c in range(3):
        img[..., c] = base[c] * (0.86 + 0.22 * n) + spec * [230, 190, 140][c] - np.clip(blot - 0.6, 0, 1) * [40, 34, 26][c]
    # old pin holes
    for _ in range(140):
        x, y = rng.integers(0, w), rng.integers(0, h)
        img[max(0, y - 1):y + 2, max(0, x - 1):x + 2] *= 0.45
    yy, xx = np.mgrid[0:h, 0:w]
    v = ((xx / w - 0.5) ** 2 + (yy / h - 0.5) ** 2)
    img *= (1 - 0.28 * np.clip(v * 2.0, 0, 1) ** 1.4)[..., None]
    Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save(out / "cork.jpg", quality=90)

def grain(w=480, h=270):
    g = rng.normal(128, 40, (h, w))
    Image.fromarray(np.clip(g, 0, 255).astype(np.uint8)).save(out / "grain.png")

def chart(w=2000, h=1100):
    # chart-recorder paper: ivory with fine pinkish grid
    base = np.array([243, 236, 219], float)
    n = fbm(h, w, 5, 3)
    img = np.zeros((h, w, 3))
    for c in range(3):
        img[..., c] = base[c] * (0.95 + 0.06 * n)
    Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save(out / "chartpaper.jpg", quality=90)

cork(); grain(); chart()
print("ok", out)
