"""Diversitas LINTAS-LINGKUNGAN: sumbu yang baru terbuka gara-gara gap Kaggle 0,0049.

Temuan yang memicu ini: `cnn12a` (Kaggle) dan `cnn3` (lokal) memakai resep yang **identik**
tapi korelasi OOF-nya cuma **0,9722** — padahal dua paket 3-seed di lokal berkorelasi
**0,9875**. Jadi lingkungan Kaggle menghasilkan model yang berbeda lebih jauh dari yang
bisa dihasilkan seed baru.

Selama ini gap itu dibaca sebagai kerugian. Tapi blend tidak peduli sebuah kandidat "lebih
baik" — ia peduli kandidat itu **salah di tempat yang berbeda**. Dekorelasi 0,972 vs 0,988
adalah diversitas gratis yang tidak bisa dibeli dengan seed tambahan, dan modelnya **sudah
dilatih** — tidak ada GPU yang perlu dibayar lagi.

Yang diuji (semua lewat protokol 12-belahan, gain holdout jujur vs blend nb8):

  1. rata-rata lintas-env di slot CNN   mean(cnn3_avg, cnn12X) menggantikan cnn3_avg
  2. sapuan bobot rata-rata itu          alpha 0,2 ... 0,8
  3. kandidat ke-9                       cnn12X ditambahkan, bukan menggantikan
  4. ganti slot cnn3_dir                 kalau-kalau slot yang benar bukan cnn3_avg

    python "Case 1/experiments/exp51_lintas_env.py"
"""
import _path  # noqa: F401
import sys
import os
import numpy as np

import lab_common as C

sys.path.insert(0, str(_path.ROOT / "tools"))
from serap_nb12 import blend, post_tr, CAND_NB8, sc  # noqa: E402

NEW = ["cnn12a", "cnn12a_tta", "cnn12b", "cnn12b_tta"]


def ld(n):
    z = np.load(C.CACHE / f"{n}.npz")
    return z["oof"], z["pte"]


def stack8():
    O = np.stack([ld(n)[0] for n in CAND_NB8])
    E = np.stack([ld(n)[1] for n in CAND_NB8])
    return O, E


def swap(O, E, slot, nama, o, p):
    keep = [i for i, n in enumerate(CAND_NB8) if n != slot]
    return ([CAND_NB8[i] for i in keep] + [nama],
            np.vstack([O[keep], o[None, :]]), np.vstack([E[keep], p[None, :]]))


def tambah(O, E, nama, o, p):
    return CAND_NB8 + [nama], np.vstack([O, o[None, :]]), np.vstack([E, p[None, :]])


def cetak(tag, r):
    tanda = "  <== LOLOS" if (r["gain"] < 0 and r["menang"] >= 7) else ""
    print("%-34s lb_real %.4f  jujur %.4f  gain %+.5f  menang %2d/12  bias %+.3f%s"
          % (tag, r["lb_real"], r["jujur"], r["gain"], r["menang"], r["bias"], tanda))
    return r


def main():
    hilang = [n for n in NEW if not (C.CACHE / f"{n}.npz").exists()]
    if hilang:
        print("kandidat belum ada di cache:", hilang)
        print('jalankan dulu: python "Case 1/tools/serap_nb12.py" <zip-Kaggle>')
        return 1

    O, E = stack8()
    w8 = np.load(C.CACHE / "w_nb9.npy")
    ref = post_tr(w8 @ O)
    print("acuan notebook_8: lb_real=%.4f   [LB aktual 0,1849]" % sc(ref))
    print("ambang: gain < 0 DAN menang >= 7/12\n")

    oA, pA = ld("cnn3_avg")

    # -- korelasi: apakah diversitasnya memang lebih besar dari diversitas seed
    print("=" * 92)
    print("KORELASI OOF terhadap cnn3_avg (pembanding: antar-paket 3-seed lokal = 0,9875)")
    print("=" * 92)
    for n in ["cnn3", "cnn3_s2", "cnn3_dir"] + NEW:
        if not (C.CACHE / f"{n}.npz").exists():
            continue
        print("  %-12s %.4f" % (n, float(np.corrcoef(oA, ld(n)[0])[0, 1])))

    hasil = {}

    # -- 1+2. rata-rata lintas-env di slot cnn3_avg, disapu bobotnya
    print("\n" + "=" * 92)
    print("UJI 1 -- mean(cnn3_avg, cnn12X) MENGGANTIKAN cnn3_avg  (jumlah kandidat tetap 8)")
    print("=" * 92)
    for n in NEW:
        o2, p2 = ld(n)
        for a in (0.3, 0.4, 0.5, 0.6):
            o = (1 - a) * oA + a * o2
            p = (1 - a) * pA + a * p2
            nm, Otr, Ote = swap(O, E, "cnn3_avg", f"mix_{n}_{a:g}", o, p)
            hasil[f"mix {n} a={a:g}"] = cetak("mean(cnn3_avg,%s) a=%.1f" % (n, a),
                                              blend(nm, Otr, Ote, ref))
        print()

    # -- 3. kandidat ke-9
    print("=" * 92)
    print("UJI 2 -- cnn12X DITAMBAHKAN sebagai kandidat ke-9 (cnn3_avg tetap di dalam)")
    print("=" * 92)
    for n in NEW:
        o, p = ld(n)
        nm, Otr, Ote = tambah(O, E, n, o, p)
        hasil[f"tambah {n}"] = cetak("+ %s (ke-9)" % n, blend(nm, Otr, Ote, ref))

    # -- 4. slot cnn3_dir
    print("\n" + "=" * 92)
    print("UJI 3 -- cnn12X menggantikan cnn3_dir (bukan cnn3_avg)")
    print("=" * 92)
    for n in NEW:
        o, p = ld(n)
        nm, Otr, Ote = swap(O, E, "cnn3_dir", n, o, p)
        hasil[f"ganti_dir {n}"] = cetak("%s -> slot cnn3_dir" % n, blend(nm, Otr, Ote, ref))

    # -- ringkasan
    print("\n" + "=" * 92)
    print("RINGKASAN")
    print("=" * 92)
    urut = sorted(hasil.items(), key=lambda kv: kv[1]["gain"])
    for k, r in urut[:6]:
        print("  %-28s gain %+.5f  menang %2d/12  bias %+.3f"
              % (k, r["gain"], r["menang"], r["bias"]))
    best_k, best = urut[0]
    lolos = best["gain"] < 0 and best["menang"] >= 7 and best["bias"] <= 0.05
    print()
    if lolos:
        print("  LOLOS: %s  (gain %+.5f, menang %d/12, bias %+.3f)"
              % (best_k, best["gain"], best["menang"], best["bias"]))
        print("  lb_real %.4f -> estimasi LB %.4f" % (best["lb_real"], best["lb_real"] + 0.0086))
        np.savez(C.CACHE / "exp51_best.npz", oof=best["oof"], pte=best["pte"], w=best["w"])
        print("  disimpan: cache/exp51_best.npz")
    else:
        print("  TIDAK ADA yang lolos. Terbaik: %s gain %+.5f menang %d/12"
              % (best_k, best["gain"], best["menang"]))
        print("  Diversitas lintas-lingkungan TIDAK cukup untuk menembus penyerapan blend.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
