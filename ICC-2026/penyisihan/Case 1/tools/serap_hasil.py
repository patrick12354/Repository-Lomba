# -*- coding: utf-8 -*-
"""Serap hasil notebook Kaggle dari `kaggle/` dan beri verdikt gabungan.

Pakai:
    python tools/serap_hasil.py <zip/folder> [<zip/folder> ...]
    python tools/serap_hasil.py ~/Downloads          # auto-cari hasil_*.zip di situ

Yang dikerjakan:
  1. ekstrak semua .npz dari zip ke `cache/`
  2. kenali kandidat baru (cnn5/cnn6/cnn7/cnn8) dan koreksi set-transformer (set2)
  3. jalankan protokol blend 12-belahan dengan SEMUA kandidat baru sekaligus
  4. cetak verdikt terhadap target LB + tiga diagnostik transfer
  5. tulis submission kalau verdiktnya aman

Notebook Kaggle sudah memberi verdikt per-model. Skrip ini menjawab pertanyaan yang
tidak bisa dijawab notebook manapun sendirian: **berapa hasilnya kalau semuanya
digabung**, karena tiap notebook cuma melihat modelnya sendiri + 8 kandidat nb8.
"""
import _path  # noqa: F401
import sys, glob, zipfile, os
from pathlib import Path
import numpy as np, pandas as pd
import lab_common as C
import lab_blend as B
from fastscore import Scorer, Post

NB8 = ["swA_sqrt", "resA_dep", "resB_dep", "resB_c30", "resB_p05",
       "cnnres", "cnn3_avg", "cnn3_dir"]
BARU = ["cnn5", "cnn6", "cnn7", "cnn8"]          # kandidat blend biasa
sc = Scorer(C.EVR, np.ones(len(C.y), bool))
post_tr = Post(C.d_tr, 0.95, 0.5, 150, 1.15, 1.05)
post_te = Post(C.d_te, 0.95, 0.5, 150, 1.15, 1.05)
TARGET = [("peringkat 1 (Kingpul)", 0.1837), ("0,1800", 0.1800),
          ("0,1750", 0.1750), ("0,1700", 0.1700), ("0,1600", 0.1600)]


def ekstrak(sumber):
    """Ekstrak .npz dari tiap zip ke cache/. Terima path zip atau folder."""
    zips = []
    for s in sumber:
        p = Path(s)
        if p.is_dir():
            zips += sorted(glob.glob(str(p/"hasil_*.zip"))) + sorted(glob.glob(str(p/"*.zip")))
        elif p.suffix == ".zip":
            zips.append(str(p))
        elif p.suffix == ".npz":
            dst = C.CACHE/p.name
            if p.resolve() != dst.resolve(): dst.write_bytes(p.read_bytes())
            print("  salin", p.name)
    for z in dict.fromkeys(zips):
        with zipfile.ZipFile(z) as zf:
            for n in zf.namelist():
                if n.endswith(".npz"):
                    (C.CACHE/os.path.basename(n)).write_bytes(zf.read(n))
                    print("  ekstrak %-22s <- %s" % (os.path.basename(n), os.path.basename(z)))


def ada(n): return (C.CACHE/f"{n}.npz").exists()


def diagnostik(oof, pte, nama, gain=None, menang=None, optimisme=0.0):
    est = sc(oof) + 0.0082
    b = C.bias_rnd(oof); mr = float(pte[C.MT].mean()); sd = float(pte[C.rnd_te].std())
    ok = (b <= 0.08, abs(mr-5.272) <= 0.03, sd <= 0.42)
    print("=" * 70); print("VERDIKT -- %s" % nama); print("=" * 70)
    print("  lb_real        %.4f   (notebook_8 = 0,1762)" % sc(oof))
    if optimisme: print("  lb_real jujur  %.4f   (+optimisme seleksi %.4f)" % (sc(oof)+optimisme, optimisme))
    if gain is not None:
        print("  gain vs nb8    %+.4f  (menang %s/12 belahan)" % (gain, menang))
    print("  dec %.4f  rnd %.4f   (nb8: 0,1437 / 0,2074)"
          % (C.part_real(oof, True), C.part_real(oof, False)))
    print()
    print("  --- diagnostik transfer ---")
    print("  bias_rnd            %+.3f   %s  (tolak kalau > 0,08; nb8 +0,031)"
          % (b, "AMAN " if ok[0] else "BAHAYA"))
    print("  mean test bulat<100 %.3f    %s  (optimum ~5,272; nb8 5,259)"
          % (mr, "AMAN " if ok[1] else "AWAS  "))
    print("  sd test sisi bulat  %.3f    %s  (naik = LB memburuk; nb8 0,396)"
          % (sd, "AMAN " if ok[2] else "AWAS  "))
    print()
    print("  ESTIMASI LB = %.4f   (sd 0,0028)" % est)
    for nm, t in TARGET:
        d = est - t
        print("    %-22s %.4f   %s (selisih %+.4f)"
              % (nm, t, "TERCAPAI" if d <= 0 else "belum   ", d))
    print("=" * 70)
    if not all(ok):
        print("PERINGATAN: diagnostik transfer tidak aman. `lb_real` mengukur data TRAIN;")
        print("`bias_rnd` dan mean subset mengukur JARAK KE TEST. Kalau bertabrakan, yang")
        print("kedua menang -- nb2 dan nb5 dua-duanya CV-nya membaik lalu LB-nya memburuk.")
    return est, all(ok)


def main(sumber):
    if sumber:
        print("== ekstrak ==")
        ekstrak(sumber)
        print()

    hilang = [n for n in NB8 if not ada(n)]
    if hilang:
        sys.exit("kandidat nb8 tidak lengkap di cache/: %s" % hilang)

    ref = B.nb8_ref()
    print("acuan notebook_8: lb_real=%.4f   [LB aktual 0,1849, peringkat 2]\n" % sc(ref))

    punya = [n for n in BARU if ada(n)]
    print("== kandidat baru yang ketemu ==")
    if not punya:
        print("  (tidak ada cnn5/cnn6/cnn7/cnn8)")
    for n in punya:
        o = np.load(C.CACHE/f"{n}.npz")["oof"]
        kor = [np.corrcoef(o, np.load(C.CACHE/f"{m}.npz")["oof"])[0, 1] for m in NB8]
        print("  %-6s lb_real %.4f  bias %+.3f  korelasi maks vs nb8 %.3f%s"
              % (n, C.lb_real(o), C.bias_rnd(o), max(kor),
                 "   <- korelasi rendah = berharga" if max(kor) < 0.93 else ""))
    print()

    final_oof, final_pte, judul = ref, post_te(
        np.load(C.CACHE/"w_nb9.npy") @ np.stack([B.ld(n)[1] for n in NB8])), "notebook_8"
    layak_gain, layak_menang, aman = 0.0, 0, True

    if punya:
        print("== blend 12-belahan, semua kandidat sekaligus ==")
        res = B.search(NB8 + punya, ref_oof=ref)
        final_oof, final_pte = res["oof"], res["pte"]
        judul = "notebook_8 + " + " + ".join(punya)
        print()
        _, aman = diagnostik(res["oof"], res["pte"], judul, res["gain"], res["menang"], res["optimisme"])
        layak_gain, layak_menang = res["gain"], res["menang"]
        if res["menang"] < 7:
            print("\nCATATAN: menang %d/12 -- itu di dalam derau. Kandidat ke-N SELALU bisa"
                  % res["menang"])
            print("menurunkan lb_real mentah di data tempat bobotnya dipilih; yang menentukan")
            print("gain holdout dan berapa belahan yang dimenangkan. CNN+GRU ditolak persis")
            print("karena pola ini (menang 1/12).")
        print()

    if ada("set2") or (C.CACHE/"set2.npz").exists():
        z = np.load(C.CACHE/"set2.npz")
        if "corr" in z:
            print("== koreksi set-transformer di atas blend akhir ==")
            corr, cte = z["corr"], z["cte"]
            raw = final_oof.copy()
            grid = [0.0, 0.1, 0.15, 0.2, 0.25, 0.3, 0.4, 0.5]
            Q = np.stack([post_tr(final_oof + l*corr) for l in grid])
            uev = np.unique(C.ev); gains = []; sel = []
            for rep in range(6):
                r = np.random.RandomState(100+rep); perm = r.permutation(uev)
                h1 = np.isin(C.ev, perm[:len(perm)//2])
                for keep in (h1, ~h1):
                    ss = Scorer(C.EVR, keep); sh = Scorer(C.EVR, ~keep)
                    v = np.array([ss(q) for q in Q]); i = v.argmin()
                    gains.append(sh(Q[i]) - sh(raw)); sel.append(grid[i])
            lam = float(np.median(sel))
            print("  gain holdout jujur %+.5f (menang %d/12), lam median %.2f"
                  % (np.mean(gains), sum(g < 0 for g in gains), lam))
            if np.mean(gains) < 0 and lam > 0:
                final_oof = post_tr(final_oof + lam*corr)
                final_pte = post_te(final_pte + lam*cte)
                judul += " + set2(lam=%.2f)" % lam
                print()
                _, aman = diagnostik(final_oof, final_pte, judul, float(np.mean(gains)),
                                     sum(g < 0 for g in gains))
                layak_gain = min(layak_gain, float(np.mean(gains)))
                layak_menang = max(layak_menang, sum(g < 0 for g in gains))
            else:
                print("  koreksi set TIDAK dipakai (gain tidak negatif atau lam=0).")
            print()

    if judul == "notebook_8":
        print("tidak ada kandidat baru -- tidak ada yang ditulis.")
        return
    if not (layak_gain < 0 and layak_menang >= 7):
        print("=" * 70)
        print("TIDAK ADA SUBMISSION DITULIS.")
        print("=" * 70)
        print("Gain holdout %+.5f, menang %d/12 -- belum melewati ambang (gain negatif"
              % (layak_gain, layak_menang))
        print("DAN menang >= 7/12). notebook_8 tetap yang terbaik; jangan ganti submission")
        print("berdasarkan lb_real mentah saja.")
        return
    if not aman:
        print("=" * 70)
        print("TIDAK ADA SUBMISSION DITULIS -- diagnostik transfer tidak aman.")
        print("=" * 70)
        return
    out = C.SUB_DIR/"notebook_9.csv"
    pd.DataFrame({"sample_id": C.test.sample_id,
                  "magnitude": np.round(final_pte, 3)}).to_csv(out, index=False)
    print("submission ditulis:", out)
    print("konfigurasi:", judul)
    print("\nCatat skornya di submission/LEADERBOARD.md begitu keluar -- hubungan CV<->LB")
    print("di case ini tidak lurus, jadi titik LB nyata adalah informasi paling berharga.")


if __name__ == "__main__":
    main(sys.argv[1:])
