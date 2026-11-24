"""Semua figur paper. Tiap fungsi fig_* menyimpan satu PNG ke figures/ dan mengembalikan path-nya.

Angka diambil dari results/*.json (hasil skrip analysis/), bukan diketik ulang, supaya figur
dan teks selalu sinkron. Ukuran: COL = lebar satu kolom IEEE (3,38 in), FULL = lebar halaman.

Setelah tiap figur dibuat, check_overlap() mencari teks yang saling tumpang-tindih atau
keluar kanvas. Peringatannya tercetak saat build; tetap lihat PNG-nya secara visual.
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mp
import nibabel as nib
import numpy as np
import pandas as pd
from matplotlib.colors import ListedColormap

HERE = Path(__file__).resolve().parent
RES = HERE / "results"
OUT = HERE / "figures"
OUT.mkdir(exist_ok=True)
DATA = HERE.parents[1] / "data"

COL, FULL = 3.38, 7.0
TINGKAT = {"mudah": "Mudah", "sedang": "Sedang", "sulit": "Sulit"}
NAVY, TEAL, ORANGE, GOLD, RED, GREY, LIGHT = "#1F3A5F", "#2A9D8F", "#E76F51", "#E9C46A", "#C0392B", "#6B7280", "#EEF2F7"
plt.rcParams.update({
    "font.family": "Times New Roman", "font.size": 7.5, "axes.titlesize": 8, "axes.labelsize": 7.5,
    "xtick.labelsize": 7, "ytick.labelsize": 7, "legend.fontsize": 6.8, "axes.spines.top": False,
    "axes.spines.right": False, "axes.linewidth": 0.6, "savefig.dpi": 300, "figure.dpi": 100,
    "axes.formatter.use_locale": False,
})


def J(name):
    return json.load(open(RES / f"{name}.json"))


def idn(x, nd=1):
    """Format angka gaya Indonesia: koma desimal."""
    return f"{x:.{nd}f}".replace(".", ",")


_BOXES = []   # (teks, patch) dari box(); dicek apakah teks muat di dalam kotaknya


def check_overlap(fig, name):
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    W, H = fig.bbox.width, fig.bbox.height
    texts = [t for t in fig.findobj(matplotlib.text.Text) if t.get_visible() and t.get_text().strip()]
    boxes = [(t, matplotlib.text.Text.get_window_extent(t, r)) for t in texts]  # teks saja, tanpa panah anotasi
    warn = []
    # catatan: tidak mengecek "keluar kanvas" karena savefig(bbox_inches="tight") memperluas kanvas
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            a, b = boxes[i][1], boxes[j][1]
            ox = min(a.x1, b.x1) - max(a.x0, b.x0); oy = min(a.y1, b.y1) - max(a.y0, b.y0)
            if ox > 2 and oy > 2:
                warn.append(f"tumpang-tindih: '{boxes[i][0].get_text()[:25]}' x '{boxes[j][0].get_text()[:25]}'")
    for t, pa in _BOXES:
        if t.figure is not fig:
            continue
        tb, pb = matplotlib.text.Text.get_window_extent(t, r), pa.get_window_extent(r)
        if tb.x0 < pb.x0 - 1 or tb.x1 > pb.x1 + 1 or tb.y0 < pb.y0 - 1 or tb.y1 > pb.y1 + 1:
            warn.append(f"teks keluar kotak: '{t.get_text()[:30]}'")
    _BOXES.clear()
    for w in warn:
        print(f"  [figur {name}] {w}")
    return warn


def save(fig, name):
    check_overlap(fig, name)
    p = OUT / f"{name}.png"
    fig.savefig(p, bbox_inches="tight", pad_inches=0.03, facecolor="white")
    plt.close(fig)
    return p


def box(ax, x, y, w, h, text, fc=LIGHT, ec=NAVY, fs=7, bold=False, tc="black", lw=0.8, r=0.02, ha="center"):
    pa = ax.add_patch(mp.FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={r}", fc=fc, ec=ec, lw=lw))
    tx = x + w / 2 if ha == "center" else x + 0.012
    t = ax.text(tx, y + h / 2, text, ha=ha, va="center", fontsize=fs, color=tc, fontweight="bold" if bold else "normal",
                linespacing=1.15)
    if text.strip():
        _BOXES.append((t, pa))
    return pa


def arrow(ax, x0, y0, x1, y1, c=GREY, lw=0.9, style="-|>", rad=0.0):
    ax.annotate("", xy=(x1, y1), xytext=(x0, y0),
                arrowprops=dict(arrowstyle=style, color=c, lw=lw, shrinkA=0, shrinkB=0,
                                connectionstyle=f"arc3,rad={rad}", mutation_scale=7))


# ---------------------------------------------------------------- Bab 1
def fig_masalah():
    """Kepadatan radiolog + beban stroke (angka dari sumber yang disitasi di teks)."""
    fig, (a, b) = plt.subplots(1, 2, figsize=(COL, 1.75), gridspec_kw=dict(width_ratios=[1.05, 1], wspace=0.55))
    lab = ["Indo-\nnesia", "UE\nmin.", "UE\nrerata", "UE\nmaks."]
    val = [0.8, 5.1, 12.7, 27.0]
    bars = a.bar(range(4), val, color=[ORANGE, "#9DB4CF", NAVY, "#9DB4CF"], width=0.66)
    for i, v in enumerate(val):
        a.text(i, v + 0.6, idn(v), ha="center", va="bottom", fontsize=6.8, fontweight="bold" if i == 0 else "normal")
    a.set_xticks(range(4)); a.set_xticklabels(lab, fontsize=5.8)
    a.set_ylabel("Radiolog per 100.000 penduduk", fontsize=6.5)
    a.set_ylim(0, 31)
    a.set_title("(a) Ketersediaan radiolog", fontsize=7.2, loc="left")
    a.annotate("16x lebih\nsedikit", xy=(0.12, 3.6), xytext=(0.9, 21), fontsize=6.3, color=ORANGE, ha="center",
               arrowprops=dict(arrowstyle="-|>", color=ORANGE, lw=0.7, mutation_scale=6))

    b.axis("off"); b.set_xlim(0, 1); b.set_ylim(0, 1)
    b.set_title("(b) Beban stroke di Indonesia", fontsize=7.2, loc="left")
    items = [("18,5%", "dari seluruh kematian\nnasional"), ("8,3‰", "prevalensi stroke\n(SKI 2023)"),
               ("Rp5,2 T", "biaya pengobatan\nstroke tahun 2023"), ("1,9 juta", "neuron hilang per menit\nstroke tanpa terapi")]
    for i, (big, small) in enumerate(items):
        y = 0.86 - i * 0.245
        b.add_patch(mp.FancyBboxPatch((0.0, y - 0.1), 1.0, 0.2, boxstyle="round,pad=0,rounding_size=0.03",
                                      fc=LIGHT, ec="none"))
        b.text(0.03, y, big, fontsize=7.4, fontweight="bold", color=NAVY if i != 3 else RED, va="center")
        b.text(0.5, y, small, fontsize=5.5, va="center", linespacing=1.05)
    return save(fig, "f_masalah")


def fig_pohon_masalah():
    fig, ax = plt.subplots(figsize=(COL, 2.35))
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    # dampak (atas)
    ax.text(0.5, 0.975, "DAMPAK", ha="center", fontsize=6.5, color=GREY, fontweight="bold")
    dampak = ["Mahasiswa tidak percaya\ndiri membaca MRI/CT", "Kemajuan belajar\ntidak terukur", "Lulusan ragu membaca\ncitra, terapi tertunda"]
    for i, t in enumerate(dampak):
        box(ax, 0.005 + i * 0.335, 0.80, 0.325, 0.13, t, fc="#FDEDE8", ec=ORANGE, fs=5.6)
        arrow(ax, 0.5, 0.66, 0.005 + i * 0.335 + 0.1625, 0.80, c=ORANGE, lw=0.7)
    box(ax, 0.02, 0.5, 0.96, 0.16, "MASALAH INTI\nMahasiswa kedokteran sulit berlatih membaca MRI\nstroke secara mandiri dengan umpan balik yang benar",
        fc=NAVY, ec=NAVY, fs=6.1, tc="white", bold=True)
    ax.text(0.5, 0.005, "AKAR MASALAH", ha="center", fontsize=6.5, color=GREY, fontweight="bold")
    akar = ["Perangkat\nradiologi\nrumit", "Materi statis\n(potongan\ngambar)", "Mentor ahli\nterbatas", "Latihan tanpa\numpan balik\nper voxel", "AI umum\nberhalusinasi"]
    for i, t in enumerate(akar):
        x = 0.005 + i * 0.2
        box(ax, x, 0.07, 0.19, 0.28, t, fc="#E6F4F2", ec=TEAL, fs=5.7)
        arrow(ax, x + 0.095, 0.35, 0.5 + (x + 0.095 - 0.5) * 0.55, 0.5, c=TEAL, lw=0.7)
    return save(fig, "f_pohon_masalah")


# ---------------------------------------------------------------- Bab 2
def fig_llm_bertingkat():
    """Akurasi GPT-4V makin turun saat tugas makin spesifik (Brin dkk.), plus rentang VLLM lain."""
    fig, ax = plt.subplots(figsize=(COL, 1.55))
    lab = ["Mengenali\nmodalitas", "Mengenali\nregio anatomi", "Mengenali\npatologi", "Diagnosis tepat\n(7 VLLM, rentang)"]
    v = [100, 87.1, 35.2]
    ax.bar(range(3), v, color=[TEAL, TEAL, ORANGE], width=0.6)
    ax.bar(3, 29.2 - 8.1, bottom=8.1, color=RED, width=0.6, alpha=0.85)
    for i, x in enumerate(v):
        ax.text(i, x + 3, idn(x) + "%", ha="center", fontsize=6.8)
    ax.text(3, 32.2, "8,1% s.d. 29,2%", ha="center", fontsize=6.8)
    ax.set_xticks(range(4)); ax.set_xticklabels(lab, fontsize=6.2)
    ax.set_ylim(0, 118); ax.set_ylabel("Akurasi (%)")
    ax.axvline(2.5, color=GREY, lw=0.5, ls=":")
    ax.text(1.0, 108, "GPT-4V, 230 gambar", ha="center", fontsize=6.3, color=GREY)
    ax.text(3.0, 108, "180 gambar klinis", ha="center", fontsize=6.3, color=GREY)
    return save(fig, "f_llm")


def fig_positioning():
    fig, ax = plt.subplots(figsize=(COL, 2.3))
    ax.set_xlim(0, 10); ax.set_ylim(0, 10)
    ax.set_xlabel("Adaptivitas terhadap kemampuan mahasiswa  →")
    ax.set_ylabel("Umpan balik berbasis kunci jawaban citra  →")
    ax.set_xticks([]); ax.set_yticks([])
    ax.axhline(5, color=GREY, lw=0.5, ls="--"); ax.axvline(5, color=GREY, lw=0.5, ls="--")
    pts = [
        (2.0, 2.2, "Atlas & e-modul statis\n(Radiopaedia, slide kuliah)", GREY),
        (2.0, 4.4, "Viewer medis\n(3D Slicer, OHIF)", GREY),
        (6.8, 2.2, "Chatbot LLM umum\n(ChatGPT, Gemini)", ORANGE),
        (7.4, 4.4, "ITS klasik (BKT), bank soal\nadaptif (pilihan ganda)", GREY),
        (3.3, 6.9, "Simulasi kasus 2D\n(ImageSim)", GREY),
        (1.9, 9.1, "Latihan kontur + Dice\n(eContour, iContour)", GREY),
        (7.9, 8.4, "SINAPS (usulan)", TEAL),
    ]
    for x, y, t, c in pts:
        big = c == TEAL
        ax.scatter(x, y, s=130 if big else 38, color=c, zorder=3, edgecolor="white", lw=0.8, marker="*" if big else "o")
        ax.text(x, y - (0.45 if not big else -0.6), t, ha="center", va="top" if not big else "baseline",
                fontsize=6.0 if not big else 7.2, fontweight="bold" if big else "normal",
                color=NAVY if big else "black", linespacing=1.05)
    ax.text(7.9, 7.35, "celah yang kami isi", ha="center", va="top", fontsize=6, color=TEAL, style="italic")
    return save(fig, "f_positioning")


# ---------------------------------------------------------------- Bab 3
def fig_arsitektur():
    fig, ax = plt.subplots(figsize=(FULL, 2.55))
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    # lapisan pengguna
    box(ax, 0.01, 0.80, 0.22, 0.17, "Mahasiswa\n(peramban, laptop/tablet)", fc="#FFF6DD", ec=GOLD, fs=7.2, bold=True)
    box(ax, 0.77, 0.80, 0.22, 0.17, "Dosen / pembimbing\ndasbor kelas & verifikasi", fc="#FFF6DD", ec=GOLD, fs=7.2, bold=True)
    box(ax, 0.27, 0.78, 0.46, 0.21,
        "1. VIEWER WEB (Cornerstone3D)\ngeser slice, window/level, ukur, kuas segmentasi,\ntombol Capture, panel tanya-jawab, kartu umpan balik",
        fc="#E8EEF6", ec=NAVY, fs=7, bold=False)
    arrow(ax, 0.23, 0.885, 0.27, 0.885, c=NAVY); arrow(ax, 0.73, 0.885, 0.77, 0.885, c=NAVY, style="<|-")
    # orkestrator
    box(ax, 0.25, 0.58, 0.5, 0.12, "API ORKESTRATOR (FastAPI)\nsesi, login kampus, antrean inferensi, log anonim",
        fc=NAVY, ec=NAVY, fs=6.5, tc="white", bold=True)
    arrow(ax, 0.5, 0.78, 0.5, 0.70, c=NAVY, style="<|-|>")
    # modul
    mods = [
        ("2. BANK KASUS", "SOOP ds004889\nDWI, ADC, FLAIR, T1\nlesion mask = kunci\njawaban, NIHSS, mRS", "#F3F4F6", GREY),
        ("3. MODUL VISI", "nnU-Net (pra-anotasi\nkasus baru) + atlas\nteritori arteri\n→ temuan terstruktur", "#E6F4F2", TEAL),
        ("4. PENILAIAN", "Dice, recall per lesi,\ngalat volume, HD95\n→ jenis kesalahan\n→ skor rubrik", "#E6F4F2", TEAL),
        ("5. ADAPTASI", "BKT per kompetensi\n(6 KC) + pemilih\nkasus berikutnya\nsesuai tingkat", "#E6F4F2", TEAL),
        ("6. TUTOR LLM", "GPT-5.6 Luna (OpenAI)\n+ temuan terstruktur\n+ RAG (PNPK, SKDI)\nmode Sokratik", "#FDEDE8", ORANGE),
    ]
    w, gap = 0.18, 0.0225
    for i, (h, t, fc, ec) in enumerate(mods):
        x = 0.01 + i * (w + gap) + 0.0
        box(ax, x, 0.14, w, 0.31, "", fc=fc, ec=ec, lw=1.0)
        ax.text(x + w / 2, 0.41, h, ha="center", va="center", fontsize=6.6, fontweight="bold", color=ec if ec != GREY else NAVY)
        ax.text(x + w / 2, 0.255, t, ha="center", va="center", fontsize=6.6, linespacing=1.2)
        arrow(ax, x + w / 2, 0.45, 0.27 + (x + w / 2) * 0.46, 0.58, c=GREY, lw=0.8, style="<|-|>")
    # alur data antar modul
    for i in range(4):
        x0 = 0.01 + i * (w + gap) + w
        arrow(ax, x0, 0.20, x0 + gap, 0.20, c=TEAL, lw=1.0)
    # penyimpanan
    box(ax, 0.01, 0.005, 0.98, 0.09,
        "PENYIMPANAN:  citra NIfTI/DICOMweb (hanya-baca)  |  log jawaban & jejak penguasaan (pseudonim, UU PDP 27/2022)  |  korpus RAG bahasa Indonesia",
        fc="white", ec=GREY, fs=5.8)
    return save(fig, "f_arsitektur")


def fig_siklus():
    fig, ax = plt.subplots(figsize=(COL, 2.3))
    ax.set_xlim(-1.75, 1.75); ax.set_ylim(-1.2, 1.2); ax.axis("off")
    langkah = [("1. Pilih kasus", "BKT memilih kasus\nuntuk KC terlemah"),
                 ("2. Baca & tandai", "mahasiswa menjawab\ndan menyegmentasi"),
                 ("3. Nilai otomatis", "dibandingkan dengan\nlesion mask"),
                 ("4. Umpan balik", "tutor menjelaskan\nkesalahan spesifik"),
                 ("5. Perbarui KC", "P(dikuasai) tiap KC\ndihitung ulang")]
    n, bw, bh = len(langkah), 1.05, 0.5
    pos = [(1.22 * np.cos(np.pi / 2 - 2 * np.pi * i / n), 0.86 * np.sin(np.pi / 2 - 2 * np.pi * i / n)) for i in range(n)]
    for i, ((h, t), (x, y)) in enumerate(zip(langkah, pos)):
        box(ax, x - bw / 2, y - bh / 2, bw, bh, "", fc=TEAL if i != 3 else ORANGE, ec="none", r=0.08)
        ax.text(x, y + 0.1, h, ha="center", va="center", fontsize=6.0, color="white", fontweight="bold")
        ax.text(x, y - 0.1, t, ha="center", va="center", fontsize=5.3, color="white", linespacing=1.0)
    for i in range(n):
        (x0, y0), (x1, y1) = pos[i], pos[(i + 1) % n]
        # panah pendek di tengah garis antar kotak supaya tidak menimpa teks
        ax.annotate("", xy=(x0 + 0.62 * (x1 - x0), y0 + 0.62 * (y1 - y0)), xytext=(x0 + 0.38 * (x1 - x0), y0 + 0.38 * (y1 - y0)),
                    arrowprops=dict(arrowstyle="-|>", color=GREY, lw=1.0, mutation_scale=8))
    ax.text(0, -0.02, "siklus\nlatihan\nterarah", ha="center", va="center", fontsize=6.6, color=NAVY, fontweight="bold")
    return save(fig, "f_siklus")


def _slice(sub, z=None):
    t = np.asanyarray(nib.load(DATA / sub / "dwi" / f"{sub}_rec-TRACE_dwi.nii.gz").dataobj).squeeze().astype(float)
    a = np.asanyarray(nib.load(DATA / sub / "dwi" / f"{sub}_rec-ADC_dwi.nii.gz").dataobj).squeeze().astype(float)
    m = np.asanyarray(nib.load(DATA / "derivatives/lesion_masks" / sub / "dwi" /
                               f"{sub}_space-TRACE_desc-lesionAcute_mask.nii.gz").dataobj) > 0
    if z is None:
        z = int(m.sum((0, 1)).argmax())
    return t[..., z].T, a[..., z].T, m[..., z].T


def _crop(*ims, pad=4):
    b = ims[0] > np.percentile(ims[0], 60)
    ys, xs = np.where(b)
    y0, y1, x0, x1 = max(ys.min() - pad, 0), ys.max() + pad, max(xs.min() - pad, 0), xs.max() + pad
    return [im[y0:y1, x0:x1] for im in ims]


def fig_mri():
    """Contoh kasus nyata SOOP: DWI, ADC, kunci jawaban, dan contoh anotasi mahasiswa (simulasi)."""
    from scipy import ndimage
    sub = "sub-1010"
    t, a, m = _slice(sub)
    t, a, m = _crop(t, a, m.astype(float)); m = m > 0.5
    stud = ndimage.binary_erosion(m, np.ones((3, 3)), iterations=4)
    lab, n = ndimage.label(stud)
    if n > 1:
        stud = lab == (np.argmax(ndimage.sum(stud, lab, range(1, n + 1))) + 1)
    d = 2 * (stud & m).sum() / (stud.sum() + m.sum())
    fig, axs = plt.subplots(1, 4, figsize=(FULL, 2.05), gridspec_kw=dict(wspace=0.04))
    vmax_t = np.percentile(t, 99.5)
    kw = dict(origin="lower", interpolation="bilinear")
    axs[0].imshow(t, cmap="gray", vmax=vmax_t, **kw); axs[0].set_title("(a) DWI: lesi terang", fontsize=7.2)
    axs[1].imshow(a, cmap="gray", vmax=np.percentile(a, 99.5), **kw); axs[1].set_title("(b) ADC: lesi gelap", fontsize=7.2)
    axs[2].imshow(t, cmap="gray", vmax=vmax_t, **kw)
    axs[2].imshow(np.ma.masked_where(~m, m), cmap=ListedColormap([TEAL]), alpha=0.55, **kw)
    axs[2].set_title("(c) Kunci jawaban", fontsize=7.2)
    axs[3].imshow(t, cmap="gray", vmax=vmax_t, **kw)
    axs[3].contour(m, levels=[0.5], colors=[TEAL], linewidths=0.8)
    axs[3].imshow(np.ma.masked_where(~stud, stud), cmap=ListedColormap([ORANGE]), alpha=0.6, **kw)
    axs[3].set_title("(d) Jawaban mahasiswa (simulasi)", fontsize=7.2)
    axs[3].text(0.03, 0.04, f"Dice {idn(d, 2)}\nsegmentasi kurang\n(tepi lesi terlewat)", transform=axs[3].transAxes,
                fontsize=6.2, color="white", va="bottom", bbox=dict(fc=NAVY, ec="none", alpha=0.85, pad=1.5))
    for x in axs:
        x.set_xticks([]); x.set_yticks([])
        for s in x.spines.values():
            s.set_visible(False)
    axs[0].text(0.02, 0.97, "R", transform=axs[0].transAxes, color="white", fontsize=6.5, va="top")
    axs[0].text(0.98, 0.97, "L", transform=axs[0].transAxes, color="white", fontsize=6.5, va="top", ha="right")
    return save(fig, "f_mri")


def fig_kohort():
    df = pd.read_csv(RES / "kohort_mask.csv")
    k = J("kohort")
    d = df[df.vol_ml > 0]
    fig, (a0, a1) = plt.subplots(1, 2, figsize=(COL, 1.9), gridspec_kw=dict(width_ratios=[1.35, 1], wspace=0.42))
    warna = {"mudah": TEAL, "sedang": GOLD, "sulit": ORANGE}
    rng = np.random.default_rng(0)
    for t, c in warna.items():
        g = d[d.tingkat == t]
        y = g.n_foci_sig.clip(lower=1) * np.exp(rng.uniform(-0.12, 0.12, len(g)))
        a0.scatter(g.vol_ml, y, s=1.4, color=c, alpha=0.55, lw=0, rasterized=True)
    xs = np.logspace(-2, 3, 200)
    for tt in (k["D_t1"], k["D_t2"]):   # garis batas tersil: log2 F = D + log10 V
        a0.plot(xs, 2 ** (tt + np.log10(xs)), color=GREY, lw=0.7, ls="--")
    a0.set_xscale("log"); a0.set_yscale("log", base=2)
    a0.set_xlim(0.01, 700); a0.set_ylim(0.8, 90)
    a0.set_xticks([0.01, 0.1, 1, 10, 100]); a0.set_xticklabels([idn(v, n) for v, n in [(0.01, 2), (0.1, 1), (1, 0), (10, 0), (100, 0)]])
    a0.set_yticks([1, 2, 4, 8, 16, 32, 64]); a0.set_yticklabels(["1", "2", "4", "8", "16", "32", "64"])
    a0.set_xlabel("Volume lesi total (ml)"); a0.set_ylabel("Fokus bermakna (\u2265 0,1 ml)")
    a0.set_title("(a) Indeks kesulitan D", fontsize=7.5)
    nm = ["mudah", "sedang", "sulit"]
    ti = k["tingkat"]
    vm = [ti[t]["vol_median"] for t in nm]; fm = [ti[t]["foci_median"] for t in nm]
    a1.bar(range(3), vm, color=[warna[t] for t in nm], width=0.62)
    for i, t in enumerate(nm):
        a1.text(i, vm[i] + 0.6, f"{idn(vm[i])} ml\n{int(fm[i])} fokus", ha="center", va="bottom", fontsize=6)
    a1.set_xticks(range(3)); a1.set_xticklabels([f"{TINGKAT[t]}\nn={ti[t]['n']}" for t in nm], fontsize=6.5)
    a1.set_ylabel("Median volume (ml)"); a1.set_ylim(0, max(vm) * 1.45)
    a1.set_title("(b) Profil tiap tingkat", fontsize=7.5)
    return save(fig, "f_kohort")


def fig_segmentasi():
    df = pd.read_csv(RES / "segmentasi.csv")
    s = J("segmentasi")
    fig, ax = plt.subplots(figsize=(COL, 1.8))
    ax.scatter(df.vol_ml, df.dice_rule, s=13, color=GREY, label=f"Aturan ambang (rerata {idn(s['dice_rule_mean'], 2)})", zorder=3)
    ax.scatter(df.vol_ml, df.dice_unet, s=15, color=TEAL, label=f"U-Net 2.5D, pasien uji (rerata {idn(s['dice_unet_mean'], 2)})", zorder=4)
    for _, r in df.iterrows():
        ax.plot([r.vol_ml] * 2, [r.dice_rule, r.dice_unet], color="#CBD5E1", lw=0.5, zorder=2)
    ax.set_xscale("log"); ax.set_ylim(-0.03, 1.02)
    ax.axvline(5, color=ORANGE, lw=0.7, ls=":")
    ax.text(4.3, 0.97, "lesi < 5 ml", ha="right", fontsize=6.2, color=ORANGE, va="top")
    ax.set_xlabel("Volume lesi (ml, skala log)"); ax.set_ylabel("Dice terhadap lesion mask")
    ax.set_xticks([1, 10, 100]); ax.set_xticklabels(["1", "10", "100"])
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=1, frameon=False, handletextpad=0.2)
    return save(fig, "f_segmentasi")


def fig_contoh_seg():
    z = np.load(RES / "contoh_segmentasi.npz")
    df = pd.read_csv(RES / "segmentasi.csv").set_index("participant_id")
    # kasus supratentorial (zf 0,35 s.d. 0,85), volume 10 s.d. 80 ml, Dice U-Net tertinggi
    ok = [s for s in df.index if 0.35 <= float(z[f"{s}__zf"]) <= 0.85 and 10 <= df.loc[s, "vol_ml"] <= 80]
    s = df.loc[ok].dice_unet.idxmax()
    dwi, gt, un, ru = (z[f"{s}__{k}"] for k in ("dwi", "gt", "unet", "rule"))
    gt, un, ru = gt > 0, un > 0, ru > 0
    # potong ke area otak supaya slice tidak kecil di tengah bingkai hitam
    ys, xs = np.where(dwi > -0.5)
    sl = (slice(max(ys.min() - 2, 0), ys.max() + 3), slice(max(xs.min() - 2, 0), xs.max() + 3))
    dwi, gt, un, ru = dwi[sl], gt[sl], un[sl], ru[sl]
    fig, axs = plt.subplots(1, 3, figsize=(COL, 1.45), gridspec_kw=dict(wspace=0.04))
    ttl = ["Kunci jawaban", f"U-Net (Dice {idn(df.loc[s, 'dice_unet'], 2)})", f"Aturan (Dice {idn(df.loc[s, 'dice_rule'], 2)})"]
    for ax, msk, t, c in zip(axs, [gt, un, ru], ttl, [TEAL, "#3B82F6", ORANGE]):
        # array berorientasi (x, y) LAS: transpose + origin bawah = orientasi radiologis
        ax.imshow(dwi.T, cmap="gray", vmin=-1.5, vmax=np.percentile(dwi, 99.7), origin="lower")
        ax.imshow(np.ma.masked_where(~msk.T, msk.T), cmap=ListedColormap([c]), alpha=0.6, origin="lower")
        if msk is not gt:
            ax.contour(gt.T, levels=[0.5], colors=[TEAL], linewidths=0.6, origin="lower")
        ax.set_title(t, fontsize=6.6); ax.set_xticks([]); ax.set_yticks([])
        for sp in ax.spines.values():
            sp.set_visible(False)
    fig_contoh_seg.subjek = s
    return save(fig, "f_contoh_seg")


def fig_penilaian():
    p = J("penilaian")
    order = ["hampir_benar", "over", "under", "lesi_terlewat", "geser"]
    lab = {"hampir_benar": "Hampir benar", "over": "Terlalu luas", "under": "Terlalu sempit",
             "lesi_terlewat": "Lesi kecil terlewat", "geser": "Salah lokasi"}
    met = [("dice", "Dice"), ("recall_lesi", "Recall\nper lesi"),
           ("galat_vol", "Galat\nvolume"), ("hd95", "HD95\n(mm)")]
    M = np.array([[p["per_jenis"][o][m] for m, _ in met] for o in order])
    # warna: "baik" hijau, "buruk" oranye, per kolom
    good = np.column_stack([M[:, 0], M[:, 1], 1 - np.clip(np.abs(M[:, 2]), 0, 1), 1 - np.clip(M[:, 3] / 10, 0, 1)])
    fig, ax = plt.subplots(figsize=(COL, 1.75))
    from matplotlib.colors import LinearSegmentedColormap
    cm = LinearSegmentedColormap.from_list("gb", [ORANGE, "#FFF6DD", TEAL])
    ax.imshow(good, cmap=cm, vmin=0, vmax=1, aspect="auto")
    for i in range(M.shape[0]):
        for j in range(M.shape[1]):
            v = M[i, j]
            s = (("+" if v > 0 else ("\u2212" if v < 0 else "")) + idn(abs(v) * 100, 0) + "%") if j == 2 else idn(v, 2 if j < 2 else 1)
            ax.text(j, i, s, ha="center", va="center", fontsize=6.8)
    ax.set_xticks(range(4)); ax.set_xticklabels([m[1] for m in met], fontsize=6.5)
    ax.set_yticks(range(5)); ax.set_yticklabels([lab[o] for o in order], fontsize=6.8)
    ax.xaxis.tick_top()
    for s in ax.spines.values():
        s.set_visible(False)
    ax.tick_params(length=0)
    return save(fig, "f_penilaian")


def fig_bkt():
    b = J("bkt")
    fig, ax = plt.subplots(figsize=(COL, 1.7))
    t = np.arange(b["T"] + 1)
    for k, c, l in [("acak", GREY, "Urutan acak (modul statis)"), ("adaptif", TEAL, "Adaptif berbasis BKT")]:
        m, lo, hi = np.array(b[k]["mean"]), np.array(b[k]["q25"]), np.array(b[k]["q75"])
        ax.plot(t, m * 100, color=c, lw=1.4, label=l)
        ax.text(t[-1] + 0.8, m[-1] * 100, f"{idn(m[-1] * 100, 0)}%", color=c, fontsize=6.8, va="center", fontweight="bold")
    ax.set_xlim(0, b["T"] + 6); ax.set_ylim(0, 102)
    ax.set_xlabel("Kasus yang dikerjakan"); ax.set_ylabel("KC yang dikuasai (%)")
    ax.legend(loc="upper left", frameon=False)
    ax.text(0.99, 0.04, "simulasi, rerata " + f"{b['N']:,}".replace(",", ".") + " mahasiswa sintetis", transform=ax.transAxes,
            ha="right", va="bottom", fontsize=5.8, color=GREY)
    return save(fig, "f_bkt")


def fig_mockup():
    """Rancangan antarmuka SINAPS memakai slice nyata SOOP (sub-1660)."""
    from scipy import ndimage
    sub = "sub-1660"
    t, a, m = _slice(sub)
    t, m = _crop(t, m.astype(float)); m = m > 0.5
    lab, n = ndimage.label(m)
    sz = ndimage.sum(m, lab, range(1, n + 1))
    stud = ndimage.binary_erosion(lab == (np.argmax(sz) + 1), np.ones((3, 3)), iterations=1)
    dice = 2 * (stud & m).sum() / (stud.sum() + m.sum())
    n_big = int((sz >= 40).sum())   # abaikan bintik < 40 piksel
    kasus = pd.read_csv(DATA / "participants.tsv", sep="\t").set_index("participant_id").loc[sub]
    fig = plt.figure(figsize=(FULL, 2.95))
    ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    ax.add_patch(mp.FancyBboxPatch((0.005, 0.01), 0.99, 0.975, boxstyle="round,pad=0,rounding_size=0.015", fc="#0F172A", ec="#334155"))
    ax.add_patch(mp.Rectangle((0.005, 0.92), 0.99, 0.065, fc="#1E293B", ec="none"))
    for i, c in enumerate(["#EF4444", "#F59E0B", "#22C55E"]):
        ax.add_patch(mp.Circle((0.02 + i * 0.013, 0.953), 0.0045, color=c))
    ax.text(0.07, 0.953, f"SINAPS  |  Kasus 14/60: laki-laki {kasus.age} tahun, stroke iskemik akut, NIHSS {int(float(kasus.nihss))}", color="white", fontsize=6.8, va="center")
    ax.text(0.985, 0.953, "Level: mahasiswa klinik", color="#94A3B8", fontsize=6.3, va="center", ha="right")
    # toolbar
    tools = ["Slice", "W/L", "Ukur", "Kuas", "Hapus", "DWI|ADC", "Capture"]
    for i, tl in enumerate(tools):
        y = 0.86 - i * 0.105
        hl = tl in ("Kuas", "Capture")
        ax.add_patch(mp.FancyBboxPatch((0.015, y - 0.035), 0.06, 0.07, boxstyle="round,pad=0,rounding_size=0.008",
                                       fc=TEAL if hl else "#334155", ec="none"))
        ax.text(0.045, y, tl, color="white", fontsize=5.8, ha="center", va="center")
    # viewer
    iax = fig.add_axes([0.085, 0.05, 0.36, 0.84])
    iax.imshow(t, cmap="gray", vmax=np.percentile(t, 99.5), origin="lower")
    iax.imshow(np.ma.masked_where(~stud, stud), cmap=ListedColormap([ORANGE]), alpha=0.55, origin="lower")
    iax.set_xticks([]); iax.set_yticks([])
    for s in iax.spines.values():
        s.set_color("#334155")
    iax.text(0.02, 0.98, "DWI b1000  slice 12/26\nW 820  L 410", transform=iax.transAxes, color="#E2E8F0", fontsize=5.8, va="top")
    iax.text(0.98, 0.02, "anotasi Anda", transform=iax.transAxes, color=ORANGE, fontsize=5.8, ha="right")
    # panel umpan balik
    ax.add_patch(mp.FancyBboxPatch((0.46, 0.53), 0.215, 0.37, boxstyle="round,pad=0,rounding_size=0.01", fc="#1E293B", ec="none"))
    ax.text(0.47, 0.875, "Hasil penilaian otomatis", color="white", fontsize=6.8, fontweight="bold", va="top")
    gv = (stud.sum() - m.sum()) / m.sum() * 100
    rows = [("Dice", idn(dice, 2), GOLD), ("Lesi ditemukan", f"1 dari {n_big}", ORANGE),
            ("Galat volume", "\u2212" + idn(abs(gv), 0) + "%", ORANGE),
            ("Jenis kesalahan", "lesi terlewat", ORANGE)]
    for i, (k, v, c) in enumerate(rows):
        y = 0.8 - i * 0.062
        ax.text(0.47, y, k, color="#CBD5E1", fontsize=6.2, va="center")
        ax.text(0.668, y, v, color=c, fontsize=6.4, va="center", ha="right", fontweight="bold")
    ax.text(0.47, 0.55, f"{n_big - 1} fokus lesi lain belum ditandai", color="#94A3B8", fontsize=5.6, va="bottom")
    # mastery
    ax.add_patch(mp.FancyBboxPatch((0.46, 0.05), 0.215, 0.45, boxstyle="round,pad=0,rounding_size=0.01", fc="#1E293B", ec="none"))
    ax.text(0.47, 0.475, "Penguasaan kompetensi (BKT)", color="white", fontsize=6.8, fontweight="bold", va="top")
    kc = [("Sekuens", .96), ("Deteksi DWI", .91), ("Cek ADC", .74), ("Teritori vaskular", .48), ("Usia lesi", .31), ("Delineasi", .42)]
    for i, (k, v) in enumerate(kc):
        y = 0.405 - i * 0.056
        ax.text(0.47, y, k, color="#CBD5E1", fontsize=5.9, va="center")
        ax.add_patch(mp.Rectangle((0.565, y - 0.012), 0.08, 0.024, fc="#334155", ec="none"))
        ax.add_patch(mp.Rectangle((0.565, y - 0.012), 0.08 * v, 0.024, fc=TEAL if v >= .95 else (GOLD if v > .6 else ORANGE), ec="none"))
        ax.text(0.668, y, f"{int(v * 100)}%", color="#CBD5E1", fontsize=5.6, va="center", ha="right")
    # chat
    ax.add_patch(mp.FancyBboxPatch((0.685, 0.05), 0.3, 0.85, boxstyle="round,pad=0,rounding_size=0.01", fc="#1E293B", ec="none"))
    ax.text(0.695, 0.875, "Tutor (mode Sokratik)", color="white", fontsize=6.8, fontweight="bold", va="top")
    chat = [
        ("m", "Kenapa area ini terang di DWI?"),
        ("t", "Coba bandingkan dengan ADC di slice\nyang sama. Kalau di ADC area itu gelap,\napa artinya bagi gerak molekul air?"),
        ("m", "Difusinya terbatas, jadi infark akut?"),
        ("t", "Tepat. Lesi di dekat insula sudah\nbenar, tapi masih ada area lain yang\ndifusinya terbatas. Coba telusuri\nbagian posterior hemisfer kiri."),
    ]
    y = 0.8
    for who, txt in chat:
        nl = txt.count("\n") + 1
        h = 0.035 + 0.047 * nl
        x0, w = (0.78, 0.195) if who == "m" else (0.695, 0.255)
        ax.add_patch(mp.FancyBboxPatch((x0, y - h), w, h, boxstyle="round,pad=0,rounding_size=0.012",
                                       fc="#0EA5E9" if who == "m" else "#334155", ec="none"))
        ax.text(x0 + 0.008, y - h / 2, txt, color="white", fontsize=5.9, va="center", linespacing=1.15)
        y -= h + 0.03
    ax.add_patch(mp.FancyBboxPatch((0.695, 0.07), 0.28, 0.06, boxstyle="round,pad=0,rounding_size=0.01", fc="#0F172A", ec="#475569", lw=0.6))
    ax.text(0.703, 0.1, "Tanya tentang slice ini... (gambar terlampir)", color="#64748B", fontsize=5.9, va="center")
    return save(fig, "f_mockup")


def fig_llm_uji():
    k = J("llm")
    kond = [("tanpa_fakta", "Tanpa fakta", GREY), ("dengan_fakta", "Dengan fakta", TEAL)]
    met = [("akurasi", "Klaim\nbenar"), ("klaim_salah", "Klaim\nkeliru"), ("abstain", "Tidak\nmenjawab"),
             ("klaim_teritori_tanpa_dasar", "Teritori\nditebak")]
    tekan = "tanpa_fakta_tekanan" in k
    fig, ax = plt.subplots(figsize=(COL, 1.8))
    w = 0.36
    n = len(met) + tekan
    for i, (kk, lab, c) in enumerate(kond):
        v = [100 * k[kk][m] for m, _ in met]
        if tekan:                     # kelompok ke-5: kondisi mahasiswa mendorong klaim keliru
            v.append(100 * k[kk + "_tekanan"]["ikut_saran_salah"])
        xs = np.arange(n) + (i - 0.5) * w
        ax.bar(xs, v, w * 0.95, color=c, label=lab)
        for x, y in zip(xs, v):
            ax.text(x, y + 2, f"{idn(y, 0)}", ha="center", va="bottom", fontsize=5.8)
    lbl = [m[1] for m in met] + (["Ikut saran\nmahasiswa*"] if tekan else [])
    ax.set_xticks(range(n)); ax.set_xticklabels(lbl, fontsize=5.9)
    ax.set_ylim(0, 110); ax.set_yticks([0, 25, 50, 75, 100]); ax.set_ylabel("Persentase (%)")
    ax.legend(frameon=False, loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=2)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    return save(fig, "f_llm_uji")


def fig_gantt():
    import datetime as dt
    d0 = dt.date(2026, 10, 1)
    task = [
        ("Bank kasus & pipeline data SOOP", "2026-10-01", "2026-10-09", NAVY, "MVP"),
        ("Model segmentasi + atlas teritori", "2026-10-05", "2026-10-17", TEAL, "MVP"),
        ("Modul penilaian & rubrik", "2026-10-08", "2026-10-17", TEAL, "MVP"),
        ("Tutor LLM, RAG, BKT", "2026-10-10", "2026-10-21", ORANGE, "MVP"),
        ("Integrasi & uji internal (demo final)", "2026-10-18", "2026-10-28", GOLD, "MVP"),
        ("Survei kebutuhan mahasiswa (baseline)", "2026-11-02", "2026-11-20", GOLD, "pilot"),
        ("Validasi konten & label oleh radiolog", "2026-11-02", "2026-11-30", NAVY, "pilot"),
        ("Uji crossover di FK mitra", "2026-12-01", "2027-02-15", TEAL, "pilot"),
        ("Analisis & penyempurnaan model", "2027-02-01", "2027-03-31", ORANGE, "pilot"),
    ]
    fig, ax = plt.subplots(figsize=(COL, 2.1))
    for i, (n, a, b, c, _) in enumerate(task):
        a, b = dt.date.fromisoformat(a), dt.date.fromisoformat(b)
        ax.barh(i, (b - a).days, left=(a - d0).days, color=c, height=0.62)
    ax.set_yticks(range(len(task))); ax.set_yticklabels([t[0] for t in task], fontsize=6.1)
    ax.invert_yaxis()
    ms = [("2026-10-01", "Okt"), ("2026-11-01", "Nov"), ("2026-12-01", "Des"), ("2027-01-01", "Jan"), ("2027-02-01", "Feb"), ("2027-03-01", "Mar")]
    ax.set_xticks([(dt.date.fromisoformat(m) - d0).days for m, _ in ms]); ax.set_xticklabels([l for _, l in ms])
    ax.set_xlim(0, (dt.date(2027, 3, 31) - d0).days)
    for x, l in [((dt.date(2026, 10, 23) - d0).days, "final submission"), ((dt.date(2026, 10, 28) - d0).days, "")]:
        ax.axvline(x, color=RED, lw=0.7, ls="--")
    ax.text((dt.date(2026, 10, 30) - d0).days, 1.5, "23 & 28 Okt:\nberkas + demo final", fontsize=5.8, color=RED, va="center")
    ax.grid(axis="x", color="#E5E7EB", lw=0.5); ax.set_axisbelow(True)
    return save(fig, "f_gantt")


ALL = [fig_masalah, fig_pohon_masalah, fig_llm_bertingkat, fig_positioning, fig_arsitektur, fig_siklus,
       fig_mri, fig_kohort, fig_segmentasi, fig_contoh_seg, fig_penilaian, fig_bkt, fig_mockup, fig_llm_uji, fig_gantt]


def build_all(only=None):
    out = {}
    for f in ALL:
        if only and f.__name__ not in only:
            continue
        try:
            out[f.__name__] = f()
        except FileNotFoundError as e:
            print(f"  [figur {f.__name__}] dilewati, hasil analisis belum ada: {e.filename}")
    return out


if __name__ == "__main__":
    import sys
    build_all(sys.argv[1:] or None)
