"""Generate the TATAP cadre-facing report mockup (Lampiran F).

Dua layar: (a) laporan sesi ketika satu modalitas dikeluarkan quality gate,
(b) layar penahanan keputusan ketika cabang pandangan gagal. Isinya ilustrasi
rancangan antarmuka, bukan hasil pengukuran.

Satuan data: 2 unit per inci, sehingga lebar satu karakter pada fontsize f
kira-kira 0.0139 * f unit. Semua teks diperiksa agar tetap di dalam panel.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch, Rectangle

BLUE = "#0f6f9f"
BLUE_FILL = "#e8f3f9"
ORANGE = "#c7460a"
GREEN = "#1d7a4c"
GREY = "#61707a"
LINE = "#c3ccd2"
INK = "#1c2b33"

FIGW, FIGH = 5.60, 3.15
UNIT = 2.0
XMAX, YMAX = FIGW * UNIT, FIGH * UNIT

fig, ax = plt.subplots(figsize=(FIGW, FIGH))
ax.set_xlim(0, XMAX)
ax.set_ylim(0, YMAX)
ax.axis("off")

PW = 5.34          # lebar panel
PX = [0.06, 5.80]  # tepi kiri tiap panel
PY, PH = 0.34, 5.72


def txt(x, y, s, size=5.4, color=INK, weight="normal", ha="left", style="normal"):
    ax.text(x, y, s, fontsize=size, color=color, fontweight=weight, ha=ha,
            va="center", style=style, zorder=5)


def bar(x, y, w, h, frac, color):
    ax.add_patch(Rectangle((x, y), w, h, linewidth=0, facecolor="#e6ebee", zorder=4))
    ax.add_patch(Rectangle((x, y), w * frac, h, linewidth=0, facecolor=color, zorder=5))


def panel(i, title, subtitle):
    x = PX[i]
    ax.add_patch(FancyBboxPatch(
        (x, PY), PW, PH, boxstyle="round,pad=0.0,rounding_size=0.16",
        linewidth=1.3, edgecolor="#8fa0ab", facecolor="white", zorder=1))
    ax.add_patch(Rectangle((x, PY + PH - 0.72), PW, 0.72, linewidth=0,
                           facecolor=BLUE_FILL, zorder=2))
    txt(x + 0.26, PY + PH - 0.26, title, 6.3, BLUE, "bold")
    txt(x + 0.26, PY + PH - 0.54, subtitle, 5.1, GREY)
    return x


def modality_rows(x, y, rows):
    for name, q, col, status in rows:
        txt(x + 0.30, y, name, 5.1)
        bar(x + 1.62, y - 0.085, 1.02, 0.17, q, col)
        txt(x + 2.78, y, f"q = {q:.2f}", 4.9, GREY)
        txt(x + 3.60, y, status, 4.9, col, "bold")
        y -= 0.34
    return y


# ============================ (a) laporan sesi ============================
xa = panel(0, "TATAP  •  Laporan Sesi", "Anak P-0412  •  24 bulan  •  Posyandu Melati 3")

ax.add_patch(FancyBboxPatch((xa + 0.26, 4.62), 2.30, 0.50,
                            boxstyle="round,pad=0.02,rounding_size=0.08",
                            linewidth=1.0, edgecolor=ORANGE, facecolor="#fff0e9",
                            zorder=4))
txt(xa + 1.41, 4.87, "DISARANKAN DIRUJUK", 5.6, ORANGE, "bold", ha="center")
txt(xa + 2.70, 4.87, "skor risiko 0,71", 5.6, INK, "bold")
txt(xa + 0.26, 4.34, "Bukan diagnosis. Keputusan akhir pada tenaga kesehatan.",
    4.9, GREY, style="italic")

txt(xa + 0.26, 4.00, "Kualitas sinyal per modalitas", 5.4, INK, "bold")
y = modality_rows(xa, 3.70, [
    ("Pandangan", 0.93, GREEN, "dipakai"),
    ("Kepala/wajah", 0.78, GREEN, "dipakai"),
    ("Vokalisasi", 0.31, ORANGE, "dikeluarkan"),
])
txt(xa + 0.30, y + 0.02, "Mikrofon tertutup. Bobot dua modalitas tersisa", 4.9, GREY,
    style="italic")
txt(xa + 0.30, y - 0.20, "dinormalisasi ulang.", 4.9, GREY, style="italic")

txt(xa + 0.26, 2.06, "Pola pandangan sesi ini", 5.4, INK, "bold")
rng = np.random.default_rng(7)
gx, gy = np.meshgrid(np.linspace(-1.6, 1.6, 70), np.linspace(-1.2, 1.2, 52))
dens = (np.exp(-((gx + 0.78) ** 2 + (gy - 0.12) ** 2) / 0.26)
        + 0.82 * np.exp(-((gx - 0.88) ** 2 + (gy + 0.38) ** 2) / 0.31)
        + 0.30 * np.exp(-(gx ** 2 + gy ** 2) / 1.9))
dens += 0.05 * rng.standard_normal(dens.shape)
ax.imshow(dens, extent=(xa + 0.30, xa + 2.20, 0.86, 1.84), aspect="auto",
          cmap="magma", origin="lower", zorder=4)
ax.add_patch(Rectangle((xa + 0.30, 0.86), 1.90, 0.98, linewidth=0.8, edgecolor=LINE,
                       facecolor="none", zorder=5))
txt(xa + 0.30, 0.70, "terang = sering dipandang", 4.7, GREY, style="italic")

txt(xa + 2.42, 1.76, "Waktu pada zona wajah", 5.1)
txt(xa + 2.42, 1.48, "31%", 7.4, ORANGE, "bold")
txt(xa + 3.10, 1.46, "rentang tipikal", 4.9, GREY)
txt(xa + 3.10, 1.28, "48–66%", 4.9, GREY)
txt(xa + 2.42, 1.04, "Sebaran pandangan lebih luas", 5.0)
txt(xa + 2.42, 0.86, "dan merata daripada rentang", 5.0)
txt(xa + 2.42, 0.68, "tipikal seusianya", 5.0)

txt(xa + 0.30, 0.50, "model v1.2  •  stimulus ID-a  •  22/07/2026", 4.7, GREY)
txt(xa + PW / 2, 0.08, "(a) laporan sesi", 5.6, INK, "bold", ha="center")

# ========================= (b) keputusan ditahan =========================
xb = panel(1, "TATAP  •  Sesi Ditahan", "Anak P-0417  •  18 bulan  •  Posyandu Melati 3")

ax.add_patch(FancyBboxPatch((xb + 0.26, 4.62), 2.86, 0.50,
                            boxstyle="round,pad=0.02,rounding_size=0.08",
                            linewidth=1.0, edgecolor=GREY, facecolor="#eef1f3",
                            zorder=4))
txt(xb + 1.69, 4.87, "SKOR TIDAK DIKELUARKAN", 5.6, INK, "bold", ha="center")
txt(xb + 0.26, 4.34, "Ditahan, bukan dinyatakan normal.", 4.9, GREY, style="italic")

txt(xb + 0.26, 4.00, "Alasan", 5.4, INK, "bold")
y = modality_rows(xb, 3.70, [
    ("Pandangan", 0.42, ORANGE, "gagal"),
    ("Kepala/wajah", 0.71, GREEN, "lolos"),
    ("Vokalisasi", 0.66, GREEN, "lolos"),
])
txt(xb + 0.30, y + 0.02, "Wajah terdeteksi pada 54% bingkai, ambang 85%.", 4.9, GREY,
    style="italic")
txt(xb + 0.30, y - 0.20, "Aturan: cabang pandangan wajib lolos dan minimal", 4.9, INK)
txt(xb + 0.30, y - 0.40, "dua modalitas memenuhi ambang kualitas.", 4.9, INK)

txt(xb + 0.26, 1.98, "Langkah yang disarankan", 5.4, INK, "bold")
steps = [
    "1. Dudukkan anak menghadap cahaya, bukan membelakangi.",
    "2. Atur jarak tablet sekitar 40–50 cm dari wajah anak.",
    "3. Ulangi sesi. Bila gagal dua kali, catat dan lanjutkan",
    "     alur SDIDTK biasa; anak tetap masuk daftar pantau.",
]
yy = 1.70
for s in steps:
    txt(xb + 0.30, yy, s, 5.0)
    yy -= 0.26

ax.add_patch(FancyBboxPatch((xb + 0.26, 0.44), PW - 0.52, 0.38,
                            boxstyle="round,pad=0.02,rounding_size=0.08",
                            linewidth=0.9, edgecolor=LINE, facecolor="#f6f8f9",
                            zorder=4))
txt(xb + 0.40, 0.63, "Kegagalan sesi tercatat untuk audit kualitas per Posyandu.",
    4.9, GREY)
txt(xb + PW / 2, 0.08, "(b) keputusan ditahan", 5.6, INK, "bold", ha="center")

fig.tight_layout(pad=0.05)
output = Path(__file__).with_name("mockup.pdf")
fig.savefig(output, bbox_inches="tight", pad_inches=0.02)
plt.close(fig)
