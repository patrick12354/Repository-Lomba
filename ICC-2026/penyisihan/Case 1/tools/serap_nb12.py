# -*- coding: utf-8 -*-
"""Serap hasil `09_tta_klip.ipynb` dari dua file `*_syms.npz` — TANPA GPU.

Notebook 09 mati di sel verdikt (`simpan()` melempar `ValueError` waktu menulis
`_score.json`; sudah diperbaiki di `mk_kaggle.py`), jadi `.npz` per-kandidat tidak
pernah ditulis. Tapi dua file yang penting **sudah tersimpan sebelum crash**:

    /kaggle/working/cnn12a_syms.npz    run A (resep nb8 apa adanya)
    /kaggle/working/cnn12b_syms.npz    run B (+ bobot loss record clipped)

Isinya `oof_s`/`pte_s` berbentuk (8, n) — prediksi per elemen grup simetri. Keempat
kandidat (`cnn12a`, `cnn12a_tta`, `cnn12b`, `cnn12b_tta`) bisa direkonstruksi dari situ
dengan merata-ratakan K elemen pertama. Tidak ada yang perlu dilatih ulang.

## Kenapa skrip ini ada, dan bukan `serap_hasil.py`

Verdikt blend notebook 09 **membandingkan apel dengan jeruk**. Kandidat `cnn12*` dilatih
di Kaggle; delapan kandidat pembanding nb8 dilatih di lokal. Diukur di
`experiments/exp50_kontrol_nb12.py`, dua lingkungan itu berselisih **+0,0049** untuk resep
yang identik — 8x derau antar-paket seed. Jadi setiap kandidat Kaggle masuk ke pencarian
bobot sambil membawa handicap 0,0049 yang tidak ada hubungannya dengan idenya.

Skrip ini menjalankan DUA uji:

  UJI 1 (seperti nb09)      pembanding = blend nb8 (slot CNN diisi `cnn3_avg` LOKAL)
                            -> handicap lingkungan ikut terukur sebagai kerugian ide
  UJI 2 (gap dinetralkan)   pembanding = blend nb8 dgn slot `cnn3_avg` diganti `cnn12a`
                            -> pembanding DAN kandidat dua-duanya dari Kaggle

UJI 2 yang menentukan apakah TTA + bobot clipped benar-benar memperbaiki resepnya.
UJI 1 tetap dicetak supaya bisa dibandingkan dengan angka yang sudah terlanjur tercatat.

## Pakai

    python "Case 1/tools/serap_nb12.py" <folder-atau-zip-berisi-cnn12*_syms.npz>

Tanpa argumen, ia mencari di `cache/` dan di `Downloads`.
"""
import _path  # noqa: F401
import os
import sys
import glob
import zipfile
import numpy as np

import lab_common as C
from fastscore import Scorer, Post

POST_ARGS = (0.95, 0.5, 150, 1.15, 1.05)     # persis notebook Kaggle & lab_blend.search
CAND_NB8 = ["swA_sqrt", "resA_dep", "resB_dep", "resB_c30", "resB_p05",
            "cnnres", "cnn3_avg", "cnn3_dir"]
K_SWEEP = [1, 2, 4, 8]

post_tr = Post(C.d_tr, *POST_ARGS)
post_te = Post(C.d_te, *POST_ARGS)
sc = Scorer(C.EVR, np.ones(len(C.y), bool))


# --------------------------------------------------------------------- menemukan file
def cari_syms(argv):
    """Kembalikan {'cnn12a': path, 'cnn12b': path}. Menerima folder, zip, atau file."""
    kandidat_dir = list(argv) or [
        str(C.CACHE),
        os.path.expanduser("~/Downloads"),
        str(_path.ROOT / "sudah_run" / "hasil"),
    ]
    ketemu = {}
    for src in kandidat_dir:
        if not os.path.exists(src):
            continue
        if src.endswith(".zip"):
            with zipfile.ZipFile(src) as zf:
                for nm in zf.namelist():
                    for tag in ("cnn12a", "cnn12b"):
                        if os.path.basename(nm) == f"{tag}_syms.npz" and tag not in ketemu:
                            dst = C.CACHE / f"{tag}_syms.npz"
                            dst.write_bytes(zf.read(nm))
                            ketemu[tag] = str(dst)
            continue
        if os.path.isfile(src):
            base = os.path.basename(src)
            for tag in ("cnn12a", "cnn12b"):
                if base == f"{tag}_syms.npz":
                    ketemu.setdefault(tag, src)
            continue
        for tag in ("cnn12a", "cnn12b"):
            if tag in ketemu:
                continue
            hit = glob.glob(os.path.join(src, "**", f"{tag}_syms.npz"), recursive=True)
            if hit:
                ketemu[tag] = hit[0]
    return ketemu


# ------------------------------------------------------------------- protokol blend
def blend(names, Otr, Ote, ref_oof, nsamp=8000, alpha=0.6, seed=0):
    """Protokol nb6/nb8: bobot dicari di separuh event, diukur di separuh lain, 12 belahan.

    Bobot final = rata-rata lintas belahan. Optimisme seleksi diukur, tidak diasumsikan nol.
    Ini salinan `lab_blend.search` yang menerima array alih-alih nama file cache."""
    rng = np.random.RandomState(seed)
    W = np.vstack([rng.dirichlet(np.ones(len(names)) * alpha, size=nsamp), np.eye(len(names))])
    Q = np.stack([post_tr(x @ Otr) for x in W])
    uev = np.unique(C.ev)
    gains, opt, ws = [], [], []
    for rep in range(6):
        r = np.random.RandomState(100 + rep)
        perm = r.permutation(uev)
        h1 = np.isin(C.ev, perm[:len(perm) // 2])
        for keep in (h1, ~h1):
            ss = Scorer(C.EVR, keep)
            sh = Scorer(C.EVR, ~keep)
            v = np.array([ss(q) for q in Q])
            i = int(v.argmin())
            gains.append(sh(Q[i]) - sh(ref_oof))
            opt.append(sh(Q[i]) - v[i])
            ws.append(W[i])
    wm = np.mean(ws, 0)
    wm /= wm.sum()
    o = post_tr(wm @ Otr)
    p = post_te(wm @ Ote)
    om = float(np.mean(opt)) / np.sqrt(2)
    return dict(w=wm, names=names, oof=o, pte=p,
                lb_real=float(sc(o)), jujur=float(sc(o)) + om, optimisme=om,
                gain=float(np.mean(gains)), menang=int(sum(g < 0 for g in gains)),
                bias=C.bias_rnd(o), dec=C.part_real(o, True), rnd=C.part_real(o, False),
                mean_rnd_te=float(p[C.MT].mean()), sd_rnd_te=float(p[C.rnd_te].std()))


def ganti_slot(base_names, base_O, base_E, slot, nama_baru, o_baru, p_baru):
    """Tukar satu kandidat di dalam himpunan blend. Jumlah kandidat tetap 8.

    Protokol 'ganti' (bukan 'tambah') wajib untuk kandidat yang merupakan versi lebih baik
    dari kandidat yang sudah ada: 'tambah' membuat blend memegang dua salinan berkorelasi
    ~0,99, dan di situlah pencarian bobot mulai menipu diri sendiri."""
    keep = [i for i, n in enumerate(base_names) if n != slot]
    names = [base_names[i] for i in keep] + [nama_baru]
    return names, np.vstack([base_O[keep], o_baru[None, :]]), \
        np.vstack([base_E[keep], p_baru[None, :]])


def cetak(tag, r):
    print("%-26s lb_real %.4f  jujur %.4f  gain %+.5f  menang %2d/12  bias %+.3f"
          % (tag, r["lb_real"], r["jujur"], r["gain"], r["menang"], r["bias"]))


# ------------------------------------------------------------------------------ main
def main():
    syms = cari_syms(sys.argv[1:])
    if len(syms) < 2:
        print("TIDAK KETEMU: butuh cnn12a_syms.npz DAN cnn12b_syms.npz.")
        print("  yang ketemu:", syms or "(tidak ada)")
        print("""
Ambil dua file itu dari panel Output notebook Kaggle `09_tta_klip`
(/kaggle/working/), lalu jalankan ulang:

    python "Case 1/tools/serap_nb12.py" <folder-unduhan>

Kalau sesi Kaggle-nya sudah mati dan filenya hilang, run itu harus diulang —
pakai `belum_run/11_tta_klip_v2.ipynb` yang konstanta kontrolnya sudah benar.""")
        return 1

    print("file:", {k: os.path.basename(v) for k, v in syms.items()}, "\n")

    # -------- rekonstruksi 4 kandidat dari prediksi per-elemen-simetri
    kand = {}
    for tag, path in sorted(syms.items()):
        z = np.load(path)
        o_s, p_s = z["oof_s"], z["pte_s"]
        assert o_s.shape[0] == 8, f"{tag}: harusnya 8 elemen simetri, dapat {o_s.shape[0]}"
        for k in K_SWEEP:
            nama = tag if k == 1 else (f"{tag}_tta" if k == 8 else f"{tag}_k{k}")
            kand[nama] = (o_s[:k].mean(0), p_s[:k].mean(0))

    print("=" * 78)
    print("KANDIDAT TUNGGAL (semua sudah lewat post_tr -- sebanding dengan kolom 'post')")
    print("=" * 78)
    lokal = {n: np.load(C.CACHE / f"{n}.npz")["oof"] for n in ["cnn3", "cnn3_avg"]
             if (C.CACHE / f"{n}.npz").exists()}
    print("%-14s %9s %9s %9s %9s" % ("kandidat", "lb_real", "dec", "rnd", "bias"))
    for n, o in lokal.items():
        po = post_tr(o)
        print("%-14s %9.4f %9.4f %9.4f %+9.3f  <- LOKAL"
              % (n, sc(po), C.part_real(po, True), C.part_real(po, False), C.bias_rnd(po)))
    for n in sorted(kand):
        if n.endswith(("_k2", "_k4")):
            continue
        po = post_tr(kand[n][0])
        print("%-14s %9.4f %9.4f %9.4f %+9.3f"
              % (n, sc(po), C.part_real(po, True), C.part_real(po, False), C.bias_rnd(po)))

    # -------- di mana gap lingkungan itu hidup
    if "cnn3" in lokal and "cnn12a" in kand:
        oL, oK = lokal["cnn3"], kand["cnn12a"][0]
        pL, pK = post_tr(oL), post_tr(oK)
        clip = C.train.is_clipped.values.astype(bool)
        print("\n" + "=" * 78)
        print("GAP LINGKUNGAN: cnn12a (Kaggle) vs cnn3 (lokal) -- resep IDENTIK")
        print("=" * 78)
        print("  lb_real      %+.4f   (positif = Kaggle lebih buruk)" % (sc(pK) - sc(pL)))
        print("  sisi desimal %+.4f" % (C.part_real(pK, True) - C.part_real(pL, True)))
        print("  sisi bulat   %+.4f   <- kalau jauh lebih besar, curigai anchor ridge/fitur,"
              % (C.part_real(pK, False) - C.part_real(pL, False)))
        print("                          bukan bobot konvolusinya")
        print("  korelasi OOF  %.4f" % float(np.corrcoef(oL, oK)[0, 1]))
        print("  MAE clipped  %+.4f | non-clipped %+.4f"
              % (np.abs(oK - C.y)[clip].mean() - np.abs(oL - C.y)[clip].mean(),
                 np.abs(oK - C.y)[~clip].mean() - np.abs(oL - C.y)[~clip].mean()))

    # -------- dua uji blend
    O8 = np.stack([np.load(C.CACHE / f"{n}.npz")["oof"] for n in CAND_NB8])
    E8 = np.stack([np.load(C.CACHE / f"{n}.npz")["pte"] for n in CAND_NB8])
    w8 = np.load(C.CACHE / "w_nb9.npy")
    ref_nb8 = post_tr(w8 @ O8)
    print("\nacuan notebook_8: lb_real=%.4f   [LB aktual 0,1849]" % sc(ref_nb8))

    print("\n" + "=" * 78)
    print("UJI 1 -- pembanding = blend nb8 apa adanya (SEPERTI nb09; gap ikut terhitung)")
    print("=" * 78)
    for key in ["cnn12a_tta", "cnn12b", "cnn12b_tta"]:
        o, p = kand[key]
        nm, Otr, Ote = ganti_slot(CAND_NB8, O8, E8, "cnn3_avg", key, o, p)
        cetak(key + " (ganti)", blend(nm, Otr, Ote, ref_nb8))

    print("\n" + "=" * 78)
    print("UJI 2 -- pembanding = blend nb8 dgn cnn3_avg DIGANTI cnn12a (gap dinetralkan)")
    print("=" * 78)
    oa, pa = kand["cnn12a"]
    nmA, OtrA, OteA = ganti_slot(CAND_NB8, O8, E8, "cnn3_avg", "cnn12a", oa, pa)
    refA = blend(nmA, OtrA, OteA, ref_nb8)
    print("  pembanding internal (cnn12a di slot CNN): lb_real %.4f" % refA["lb_real"])
    print()
    hasil = {}
    for key in ["cnn12a_tta", "cnn12b", "cnn12b_tta"]:
        o, p = kand[key]
        nm, Otr, Ote = ganti_slot(CAND_NB8, O8, E8, "cnn3_avg", key, o, p)
        r = blend(nm, Otr, Ote, refA["oof"])
        hasil[key] = r
        cetak(key + " (vs cnn12a)", r)

    # -------- verdikt
    best = min(hasil.values(), key=lambda r: r["gain"])
    nama = [k for k, v in hasil.items() if v is best][0]
    print("\n" + "=" * 78)
    print("VERDIKT")
    print("=" * 78)
    lolos2 = best["gain"] < 0 and best["menang"] >= 7
    print("  terbaik di UJI 2: %s  gain %+.5f  menang %d/12"
          % (nama, best["gain"], best["menang"]))
    if lolos2:
        print("""
  LOLOS. TTA + bobot clipped memang memperbaiki RESEPNYA -- kegagalan nb09 disebabkan
  gap lingkungan 0,0049, bukan idenya. Langkah berikutnya BUKAN submit file Kaggle ini
  (ia tetap membawa handicap 0,0049), melainkan menerapkan kedua perubahan itu di
  pipeline LOKAL tempat baselinenya 0,1888 -- lalu jalankan protokol blend biasa.""")
    else:
        print("""
  TIDAK LOLOS. Bahkan setelah gap lingkungan dinetralkan, TTA + bobot clipped tidak
  mengalahkan pembandingnya sendiri di holdout jujur. Tutup kedua sumbu ini dan catat
  di CLAUDE.md -- jangan dicoba lagi dalam bentuk lain.""")
    print("""
  Yang TIDAK berubah oleh skrip ini: `notebook_8.csv` tetap submission terbaik
  (LB 0,1849). Tidak ada file submission yang ditulis di sini -- itu keputusan manusia,
  dan kompetisi ini cuma mengizinkan SATU submission final.""")
    return 0


if __name__ == "__main__":
    sys.exit(main())
