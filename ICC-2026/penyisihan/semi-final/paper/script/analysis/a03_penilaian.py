"""A03: simulasi penilaian otomatis segmentasi mahasiswa.

Anotasi mahasiswa belum ada, jadi disimulasikan dari lesion mask 30 subjek sampel dengan
5 pola kesalahan yang umum pada pemula,
4 anotasi per pola per subjek dengan tingkat keparahan acak (600 anotasi). Tujuannya menguji apakah metrik (Dice, recall per lesi,
galat volume, HD95) cukup membedakan jenis kesalahan untuk umpan balik yang spesifik.

Output: results/penilaian.csv, results/penilaian.json
Waktu jalan: +-1 menit.
"""
import json
import nibabel as nib
import numpy as np
import pandas as pd
from scipy import ndimage
from _common import DATA, RESULTS

rng = np.random.default_rng(42)
ST = np.ones((3, 3, 1), bool)                 # erosi/dilasi in-plane (slice 6 mm)


def hd95(a, b, sp):
    if not a.any() or not b.any():
        return np.nan
    da = ndimage.distance_transform_edt(~a, sampling=sp)
    db = ndimage.distance_transform_edt(~b, sampling=sp)
    sa = a ^ ndimage.binary_erosion(a); sb = b ^ ndimage.binary_erosion(b)
    return float(np.percentile(np.concatenate([db[sa], da[sb]]), 95))


def metrik(p, g, sp, vml):
    lab, n = ndimage.label(g, structure=np.ones((3, 3, 3)))
    hit = sum((p & (lab == i)).any() for i in range(1, n + 1))
    s = p.sum() + g.sum()
    return dict(dice=2 * (p & g).sum() / s if s else 1.0,
                recall_lesi=hit / n if n else 1.0,
                galat_vol=(p.sum() - g.sum()) / max(g.sum(), 1),
                hd95=hd95(p, g, sp))


def pola(g, jenis):
    """Satu anotasi sintetis. Tingkat keparahan diacak supaya sinyal metrik tidak seragam."""
    if jenis == "hampir_benar":       # tepi meleset acak: 15-40% voxel tepi dalam/luar dibalik
        tepi = ndimage.binary_dilation(g, ST) ^ ndimage.binary_erosion(g, ST)
        return g ^ (tepi & (rng.random(g.shape) < rng.uniform(.15, .4)))
    if jenis == "under":              # hanya inti lesi yang ditandai
        return ndimage.binary_erosion(g, ST, iterations=int(rng.integers(2, 5)))
    if jenis == "over":               # ikut menandai edema/tepi
        return ndimage.binary_dilation(g, ST, iterations=int(rng.integers(2, 7)))
    if jenis == "geser":              # posisi salah (salah lokalisasi), arah dan jarak acak
        return np.roll(g, int(rng.integers(8, 17)) * int(rng.choice([-1, 1])), axis=int(rng.integers(0, 2)))
    if jenis == "lesi_terlewat":      # hanya lesi terbesar yang ditandai
        lab, n = ndimage.label(g, structure=np.ones((3, 3, 3)))
        if n < 2:
            return np.zeros_like(g)   # lesi tunggal terlewat total
        sz = ndimage.sum(g, lab, range(1, n + 1))
        return lab == (np.argmax(sz) + 1)
    raise ValueError(jenis)


JENIS = ["hampir_benar", "under", "over", "geser", "lesi_terlewat"]
ULANG = 4                             # anotasi sintetis per jenis per subjek
rows = []
for s in open(DATA / "sample_subjects.txt").read().split():
    im = nib.load(DATA / "derivatives/lesion_masks" / s / "dwi" / f"{s}_space-TRACE_desc-lesionAcute_mask.nii.gz")
    g = np.asanyarray(im.dataobj) > 0
    if not g.any():
        continue
    sp = im.header.get_zooms()[:3]
    for j in JENIS:
        for u in range(ULANG):
            rows.append(dict(participant_id=s, jenis=j, **metrik(pola(g, j), g, sp, 0)))
df = pd.DataFrame(rows)
df.to_csv(RESULTS / "penilaian.csv", index=False)


# Aturan umpan balik: pohon keputusan tetap (transparan, bisa dijelaskan ke mahasiswa) dengan 5 ambang.
# Ambang DIPELAJARI di subjek latih dan DIUJI di subjek yang tidak pernah dilihat (5-fold per subjek),
# jadi akurasi yang dilaporkan bukan lagi batas atas dari data yang sama.
def aturan(r, th):
    d_gsr, v_gsr, v_over, v_under, rec = th
    if r.dice < d_gsr and abs(r.galat_vol) < v_gsr:
        return "geser"             # volume pas tapi tumpang-tindih rendah: salah lokasi
    if r.galat_vol > v_over:
        return "over"
    if r.galat_vol < v_under:
        return "under"
    if r.recall_lesi < rec:
        return "lesi_terlewat"
    return "hampir_benar"


GRID = [(a, b, c, d, e) for a in (.3, .4, .5, .6) for b in (.15, .25, .35) for c in (.2, .3, .5)
        for d in (-.25, -.35, -.5) for e in (.9, .99)]


def fit(tr):
    X = list(tr.itertuples())
    return max(GRID, key=lambda th: np.mean([aturan(r, th) == r.jenis for r in X]))


# pembanding: hanya Dice (nearest-centroid pada median Dice tiap jenis di data latih)
def dice_saja(tr, te):
    c = tr.groupby("jenis").dice.median()
    return te.dice.apply(lambda v: (c - v).abs().idxmin())


subs = np.random.default_rng(0).permutation(df.participant_id.unique())
df["tebakan"] = ""; df["tebakan_dice"] = ""; ths = []
for te_s in np.array_split(subs, 5):
    te = df.participant_id.isin(te_s)
    th = fit(df[~te]); ths.append(th)
    df.loc[te, "tebakan"] = [aturan(r, th) for r in df[te].itertuples()]
    df.loc[te, "tebakan_dice"] = dice_saja(df[~te], df[te]).values
df.to_csv(RESULTS / "penilaian.csv", index=False)
ringkas = df.groupby("jenis")[["dice", "recall_lesi", "galat_vol", "hd95"]].median()
th_all = fit(df)
out = dict(n_subjek=int(df.participant_id.nunique()), n_kasus=len(df), ulang=ULANG,
           akurasi_aturan=float((df.tebakan == df.jenis).mean()),
           akurasi_dice_saja=float((df.tebakan_dice == df.jenis).mean()),
           akurasi_latih=float(np.mean([aturan(r, th_all) == r.jenis for r in df.itertuples()])),
           ambang_final=dict(zip(["dice_geser", "vol_geser", "vol_over", "vol_under", "recall"], th_all)),
           ambang_stabil=float(np.mean([t == th_all for t in ths])),
           recall_per_jenis=df.assign(b=df.tebakan == df.jenis).groupby("jenis").b.mean().round(3).to_dict(),
           per_jenis=ringkas.round(3).to_dict(orient="index"),
           konfusi=pd.crosstab(df.jenis, df.tebakan).to_dict(orient="index"))
json.dump(out, open(RESULTS / "penilaian.json", "w"), indent=1, default=float)
print(json.dumps(out, indent=1, default=float))
