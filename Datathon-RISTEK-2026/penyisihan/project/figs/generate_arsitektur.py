"""Generate the TATAP late-fusion architecture figure.

Revisi 2026-07-22: quality gate dipecah. Blok awal hanya capture QC (kamera,
mikrofon, wajah, cahaya). Skor kualitas q_m dan kalibrasi probabilitas berada
pada masing-masing cabang, karena keduanya baru dapat dihitung setelah
modalitasnya diproses. Yang mengalir ke fusi adalah pasangan (p_m, q_m).

Tata letak dihitung otomatis: lebar tiap kotak diukur dari teks yang sudah
dirender, lalu kolom disusun kiri ke kanan. Dengan begitu teks tidak pernah
meluber keluar kotak dan kotak tidak pernah bertumpuk.
"""

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

BLUE = "#0f6f9f"
BLUE_FILL = "#e8f3f9"
ORANGE = "#c7460a"
ORANGE_FILL = "#fff0e9"
GREY = "#61707a"

FIGW, FIGH = 5.49, 2.52
UNIT = 2.0                      # unit data per inci
XMAX, YMAX = FIGW * UNIT, FIGH * UNIT
PADX, PADY = 0.11, 0.10
GAP = 0.20
LABEL_TOP, LABEL_BOT = 0.34, 0.30   # ruang untuk keterangan di atas dan bawah

fig, ax = plt.subplots(figsize=(FIGW, FIGH))
ax.set_xlim(0, XMAX)
ax.set_ylim(0, YMAX)
ax.axis("off")
fig.canvas.draw()
REND = fig.canvas.get_renderer()


def measure(text, fontsize, bold=False):
    t = ax.text(0, 0, text, ha="center", va="center", fontsize=fontsize,
                fontweight="bold" if bold else "normal")
    bb = t.get_window_extent(renderer=REND).transformed(ax.transData.inverted())
    t.remove()
    return bb.width + 2 * PADX, bb.height + 2 * PADY


class Node:
    def __init__(self, text, fontsize, *, edge=BLUE, fill=BLUE_FILL, dashed=False,
                 bold=False):
        self.text, self.fontsize, self.bold = text, fontsize, bold
        self.edge, self.fill, self.dashed = edge, fill, dashed
        self.w, self.h = measure(text, fontsize, bold)

    def place(self, x0, cy):
        self.x0, self.cy = x0, cy
        ax.add_patch(FancyBboxPatch(
            (x0, cy - self.h / 2), self.w, self.h,
            boxstyle="round,pad=0.0,rounding_size=0.09",
            linewidth=1.15, linestyle="--" if self.dashed else "-",
            edgecolor=self.edge, facecolor=self.fill, zorder=3))
        ax.text(x0 + self.w / 2, cy, self.text, ha="center", va="center",
                fontsize=self.fontsize,
                fontweight="bold" if self.bold else "normal", zorder=4)
        return self

    @property
    def x1(self):
        return self.x0 + self.w


def arrow(start, end, *, dashed=False):
    ax.add_patch(FancyArrowPatch(
        start, end, arrowstyle="-|>", mutation_scale=8, linewidth=0.9,
        color="#344955", linestyle="--" if dashed else "-", zorder=2))


SPEC = [
    ("capture", "Sesi 2 menit\nkamera, mikrofon", 5.9, {}),
    ("qc", "Capture QC\nwajah, cahaya,\naudio", 5.9, {}),
    ("gaze", "Pandangan: wajah/mata, pose\nkepala $\\rightarrow$ titik pandang layar\n"
             "$\\rightarrow$ scanpath, 19 fitur $\\rightarrow$ model\n"
             "+ kalibrasi $\\rightarrow p_1,\\ q_1$", 5.7, {}),
    ("head", "Kepala/wajah: gerak +\nrespons nama $\\rightarrow$ model\n"
             "+ kalibrasi $\\rightarrow p_2,\\ q_2$", 5.7, {"dashed": True}),
    ("voice", "Vokalisasi: latensi +\nprosodi $\\rightarrow$ model\n"
              "+ kalibrasi $\\rightarrow p_3,\\ q_3$", 5.7, {"dashed": True}),
    ("fusion", "Weighted\nlate fusion", 6.1,
     {"edge": ORANGE, "fill": ORANGE_FILL, "bold": True}),
    ("out", "Skor risiko\n+ laporan", 6.1,
     {"edge": ORANGE, "fill": ORANGE_FILL, "bold": True}),
]

# Perkecil serempak sampai seluruh kolom muat; mencegah kotak terpotong tepi.
scale = 1.0
while True:
    N = {k: Node(t, fs * scale, **kw) for k, t, fs, kw in SPEC}
    branch_w = max(N["gaze"].w, N["head"].w, N["voice"].w)
    total = (N["capture"].w + N["qc"].w + branch_w + N["fusion"].w + N["out"].w
             + 4 * GAP)
    if total <= XMAX - 0.10 or scale < 0.80:
        break
    scale -= 0.02

capture, qc = N["capture"], N["qc"]
gaze, head, voice = N["gaze"], N["head"], N["voice"]
fusion, out = N["fusion"], N["out"]
x = max(0.05, (XMAX - total) / 2)

vgap = max(0.12, (YMAX - LABEL_TOP - LABEL_BOT - gaze.h - head.h - voice.h) / 2)
MID = LABEL_BOT + voice.h + vgap + head.h / 2
top = MID + head.h / 2 + vgap + gaze.h / 2
bot = MID - head.h / 2 - vgap - voice.h / 2

capture.place(x, MID)
qc.place(capture.x1 + GAP, MID)
bx = qc.x1 + GAP
gaze.place(bx + (branch_w - gaze.w) / 2, top)
head.place(bx + (branch_w - head.w) / 2, MID)
voice.place(bx + (branch_w - voice.w) / 2, bot)
fusion.place(bx + branch_w + GAP, MID)
out.place(fusion.x1 + GAP, MID)

arrow((capture.x1, MID), (qc.x0, MID))
for b, dashed in [(gaze, False), (head, True), (voice, True)]:
    arrow((qc.x1, MID), (b.x0, b.cy), dashed=dashed)
    arrow((b.x1, b.cy), (fusion.x0, MID), dashed=dashed)
arrow((fusion.x1, MID), (out.x0, MID))

ax.text(bx + branch_w / 2, YMAX - 0.02,
        "cabang pandangan: rantai yang diuji studi jembatan",
        ha="center", va="top", fontsize=6.1, color=BLUE)
ax.text(bx + branch_w / 2, 0.01, "garis putus-putus: cabang prospektif",
        ha="center", va="bottom", fontsize=6.1, color=GREY, style="italic")
ax.text(fusion.x0 + fusion.w / 2, MID - fusion.h / 2 - 0.12,
        r"$p=\sum_m \alpha_m p_m$" "\n" r"$\alpha_m \propto w_m q_m$",
        ha="center", va="top", fontsize=6.0, color=GREY)

fig.tight_layout(pad=0.05)
output = Path(__file__).with_name("arsitektur.pdf")
fig.savefig(output, bbox_inches="tight", pad_inches=0.02)
plt.close(fig)
