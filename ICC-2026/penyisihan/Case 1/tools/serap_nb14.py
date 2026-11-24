# -*- coding: utf-8 -*-
"""Serap hasil `11_pseudo_label.ipynb` — TANPA GPU.

Notebook 11 sudah mencetak verdiktnya sendiri di Kaggle, **tapi verdikt itu tetap wajib
dihitung ulang di sini.** Alasannya tercatat mahal: notebook 01 melabeli `bias_rnd` +0,059
sebagai AMAN (ambangnya kelonggaran), dan notebook 09 mencetak "verdikt tidak bisa
dipercaya" lalu menjalankan verdiktnya sampai selesai. Verdikt yang dicetak notebook adalah
bahan mentah, bukan kesimpulan.

## Pakai

    python "Case 1/tools/serap_nb14.py" <folder-atau-zip-hasil-Kaggle>

Butuh **dua** file dari `/kaggle/working/` (keduanya ada di `hasil_cnn14_pl.zip`):

    cnn14a.npz   arm A — KONTROL, resep cnn3 apa adanya
    cnn14b.npz   arm B — + pseudo-label

**`cnn14a.npz` sama wajibnya dengan `cnn14b.npz`.** Tanpa arm A, UJI 2 tidak bisa dihitung
dan verdiktnya jatuh kembali ke perbandingan lintas-lingkungan yang sudah terbukti salah
di notebook 09.

## Yang dicetak, dan urutan membacanya

1. **KOLAPS TEST** — gerbang pembatal. Kalau prediksi test arm B jauh lebih mirip arm A
   daripada OOF-nya, label-semu bocor ke prediksi test dan seluruh verdikt blend di
   bawahnya tidak sah, berapa pun bagus skornya. **Baca ini dulu.**
2. **Kontrol lingkungan** — arm A harus mendarat di 0,1898 (`lb_real` SETELAH `post_tr`).
3. **Efek terisolasi PL** — dan apakah gain-nya menumpuk di sisi bulat seperti klaim
   mekanismenya. Kalau tidak, yang bekerja bukan komposisi.
4. **UJI 1 / UJI 2** — verdikt blend. UJI 2 yang menentukan.
"""
import _path  # noqa: F401
import os
import sys
import glob
import zipfile
import numpy as np

import lab_common as C
from serap_nb12 import blend, post_tr, sc, CAND_NB8, ganti_slot, cetak

ARM = {"cnn14a": "arm A - KONTROL (resep cnn3)", "cnn14b": "arm B - + pseudo-label"}
KONTROL_POST = 0.1898     # lb_real cnn3 lokal SETELAH post_tr (mentahnya 0,2091)
CNN3AVG_POST = 0.1888     # cnn3_avg lokal, 6 seed, setelah post_tr


def cari(argv):
    sumber = list(argv) or [str(C.CACHE), os.path.expanduser("~/Downloads"),
                            str(_path.ROOT / "sudah_run" / "hasil")]
    ketemu = {}
    for src in sumber:
        if not os.path.exists(src):
            continue
        if src.endswith(".zip"):
            with zipfile.ZipFile(src) as zf:
                for nm in zf.namelist():
                    b = os.path.basename(nm)[:-4]
                    if b in ARM and b not in ketemu:
                        dst = C.CACHE / f"{b}.npz"
                        dst.write_bytes(zf.read(nm))
                        ketemu[b] = str(dst)
            continue
        if os.path.isfile(src):
            b = os.path.basename(src)[:-4]
            if b in ARM:
                ketemu.setdefault(b, src)
            continue
        for tag in ARM:
            if tag in ketemu:
                continue
            hit = glob.glob(os.path.join(src, "**", f"{tag}.npz"), recursive=True)
            if hit:
                ketemu[tag] = hit[0]
    return ketemu


def ld(p):
    z = np.load(p)
    return z["oof"], z["pte"]


def main():
    f = cari(sys.argv[1:])
    if len(f) < 2:
        print("TIDAK KETEMU: butuh cnn14a.npz DAN cnn14b.npz.")
        print("  yang ketemu:", f or "(tidak ada)")
        print("""
Ambil `hasil_cnn14_pl.zip` dari panel Output notebook Kaggle `11_pseudo_label`,
lalu jalankan ulang:

    python "Case 1/tools/serap_nb14.py" <folder-unduhan>

cnn14a (KONTROL) sama wajibnya dengan cnn14b. Tanpa arm A, UJI 2 tidak bisa
dihitung dan verdiktnya jatuh ke perbandingan lintas-lingkungan yang sudah
terbukti salah di notebook 09.""")
        return 1

    oA, pA = ld(f["cnn14a"])
    oB, pB = ld(f["cnn14b"])
    clip = C.train.is_clipped.values.astype(bool)

    # ---------------------------------------------------------------- 1. KOLAPS TEST
    c_o = float(np.corrcoef(oB, oA)[0, 1])
    c_p = float(np.corrcoef(pB, pA)[0, 1])
    kolaps = (c_p - c_o) > 0.02
    print("=" * 78)
    print("1. KOLAPS TEST -- gerbang pembatal, baca ini dulu")
    print("=" * 78)
    print("  korelasi arm B vs arm A:  oof %.4f | pte %.4f | selisih %+.4f"
          % (c_o, c_p, c_p - c_o))
    if kolaps:
        print("  BAHAYA: prediksi test jauh lebih mirip daripada OOF-nya. Label-semu bocor")
        print("  ke prediksi test -- bobot blend dipilih dari diversitas OOF yang tidak ada")
        print("  di test. VERDIKT DI BAWAH TIDAK SAH, berapa pun angkanya.")
    else:
        print("  AMAN: diversitas OOF dan test sebanding, tidak ada kolaps.")

    # ---------------------------------------------------- 2. kontrol lingkungan
    poA, poB = post_tr(oA), post_tr(oB)
    gap = sc(poA) - KONTROL_POST
    print("\n" + "=" * 78)
    print("2. KONTROL LINGKUNGAN -- arm A harus mereproduksi cnn3")
    print("=" * 78)
    print("  arm A  %.4f  vs  cnn3 lokal %.4f  ->  gap %+.4f"
          % (sc(poA), KONTROL_POST, gap))
    print("  " + ("COCOK -- Kaggle mereproduksi run lokal."
                  if abs(gap) < 0.004 else
                  "TIDAK COCOK. UJI 2 tetap sah (pembandingnya se-lingkungan), tapi kalau\n"
                  "  kandidatnya menang, JALANKAN ULANG DI LOKAL sebelum submit -- file\n"
                  "  Kaggle-nya membawa handicap ini. Bandingkan sidik jari input di sel Setup."))
    print("  nb09 mencatat gap +0,0049 dengan korelasi OOF resep-identik 0,9722")
    print("  (antar-paket 3-seed lokal: 0,9875). Korelasi arm A vs cnn3 sekarang: %.4f"
          % float(np.corrcoef(oA, np.load(C.CACHE / "cnn3.npz")["oof"])[0, 1]))

    # ------------------------------------------------------- 3. efek terisolasi
    print("\n" + "=" * 78)
    print("3. EFEK TERISOLASI PSEUDO-LABEL (positif = membaik)")
    print("=" * 78)
    print("  %-14s %9s %9s %9s %9s" % ("", "lb_real", "dec", "rnd", "bias"))
    for nm, po in [("arm A", poA), ("arm B", poB)]:
        print("  %-14s %9.4f %9.4f %9.4f %+9.3f"
              % (nm, sc(po), C.part_real(po, True), C.part_real(po, False), C.bias_rnd(po)))
    print("  %-14s %9.4f %9.4f %9.4f" %
          ("efek PL", sc(poA) - sc(poB),
           C.part_real(poA, True) - C.part_real(poB, True),
           C.part_real(poA, False) - C.part_real(poB, False)))
    print("  pembanding LOKAL (setelah post): cnn3 %.4f | cnn3_avg %.4f"
          % (KONTROL_POST, CNN3AVG_POST))
    d_rnd = C.part_real(poA, False) - C.part_real(poB, False)
    d_tot = sc(poA) - sc(poB)
    if d_tot > 0.0005:
        porsi = 0.51 * d_rnd / d_tot if d_tot else 0
        print("\n  porsi gain yang datang dari sisi bulat: %.0f%%" % (100 * porsi))
        print("  " + ("KONSISTEN dengan mekanisme komposisi (32%%->51%% depth-bulat)."
                      if porsi > 0.6 else
                      "TIDAK konsisten dengan mekanisme komposisi. Yang bekerja kemungkinan\n"
                      "  DISTILASI (guru nb8 0,1762 vs murid CNN 0,1888), bukan pergeseran\n"
                      "  komposisi -- yang berbobot cuma bergeser 34,3%% -> 39,9%%. Catat ini."))
    print("\n  MAE per subset:  %-12s %-12s %-12s" % ("desimal", "bulat-dangkal", "clipped"))
    for nm, o in [("arm A", oA), ("arm B", oB)]:
        e = np.abs(o - C.y)
        print("  %-16s %-12.4f %-12.4f %-12.4f"
              % (nm, e[~C.rnd_tr].mean(), e[C.MR].mean(), e[clip].mean()))

    # ----------------------------------------------------------- 4. verdikt blend
    O8 = np.stack([np.load(C.CACHE / f"{n}.npz")["oof"] for n in CAND_NB8])
    E8 = np.stack([np.load(C.CACHE / f"{n}.npz")["pte"] for n in CAND_NB8])
    ref_nb8 = post_tr(np.load(C.CACHE / "w_nb9.npy") @ O8)
    print("\n" + "=" * 78)
    print("4. VERDIKT BLEND   (acuan nb8: lb_real %.4f, LB aktual 0,1849)" % sc(ref_nb8))
    print("=" * 78)
    print("UJI 1 -- pembanding blend nb8 apa adanya (gap lingkungan ikut terhitung)")
    nm1, O1, E1 = ganti_slot(CAND_NB8, O8, E8, "cnn3_avg", "cnn14b", oB, pB)
    r1 = cetak("cnn14b (ganti)", blend(nm1, O1, E1, ref_nb8))

    print("\nUJI 2 -- pembanding = blend nb8 dgn cnn3_avg DIGANTI arm A  <== MENENTUKAN")
    nmA, OA, EA = ganti_slot(CAND_NB8, O8, E8, "cnn3_avg", "cnn14a", oA, pA)
    rA = blend(nmA, OA, EA, ref_nb8)
    print("  pembanding internal (arm A di slot CNN): lb_real %.4f" % rA["lb_real"])
    r2 = cetak("cnn14b (vs arm A)", blend(nm1, O1, E1, rA["oof"]))

    # ------------------------------------------------------------------ verdikt
    lolos = (not kolaps and r2["gain"] < 0 and r2["menang"] >= 7 and r2["bias"] <= 0.05)
    print("\n" + "=" * 78)
    print("VERDIKT")
    print("=" * 78)
    print("  ambang: KOLAPS TEST aman DAN gain < 0 DAN menang >= 7/12 DAN bias <= 0,05")
    print("  hasil : kolaps %s | gain %+.5f | menang %d/12 | bias %+.3f"
          % ("BAHAYA" if kolaps else "aman", r2["gain"], r2["menang"], r2["bias"]))
    print("  estimasi LB (lb_real + 0,0086): %.4f   [nb8 = 0,1849]"
          % (r2["lb_real"] + 0.0086))
    if kolaps:
        print("""
  DIBATALKAN oleh gerbang KOLAPS TEST. Jangan tafsirkan angka blend di atas.
  Yang bisa dicatat cuma efek terisolasi di bagian 3.""")
    elif lolos:
        np.savez(C.CACHE / "blend_cnn14.npz", oof=r2["oof"], pte=r2["pte"], w=r2["w"])
        print("""
  LOLOS PROTOKOL. Langkah berikutnya, BERURUTAN:
    1. Kalau gap kontrol di bagian 2 > 0,004, jalankan ulang arm A+B di LOKAL
       (~2,8 jam RTX 4060). File Kaggle membawa handicap lingkungan itu.
    2. Tulis notebook_11.ipynb di root `Case 1/` yang mereproduksi blend ini,
       beserta submission/notebook_11.csv.
    3. Catat di submission/LEADERBOARD.md SEBELUM tahu skor LB-nya.
  Bobot tersimpan di cache/blend_cnn14.npz.""")
    else:
        print("""
  TIDAK LOLOS -- notebook_8.csv tetap submission terbaik.
  Catat di sudah_run/README.md dan CLAUDE.md BESERTA ALASANNYA, dan sertakan
  jawaban bagian 3: apakah gain-nya menumpuk di sisi bulat seperti klaim
  mekanismenya, atau tidak. Yang gagal tanpa catatan pasti dicoba ulang.""")
    print("""
  Ingat: hanya ADA SATU submission final. Selisih ke peringkat 1 (0,0014) ada di
  dalam derau LB publik (sd ~0,004 untuk model berbeda), jadi kandidat yang cuma
  menang tipis BUKAN alasan cukup untuk menggeser notebook_8.""")
    return 0


if __name__ == "__main__":
    sys.exit(main())
