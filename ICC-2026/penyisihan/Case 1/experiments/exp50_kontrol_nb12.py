"""Kenapa gerbang kontrol `09_tta_klip.ipynb` gagal — dan kenapa itu BUKAN soal lingkungan.

Notebook 09 mencetak:

    KONTROL: K=1 lb_real 0.1947   (cnn3 di lokal = 0,2091)
    TIDAK COCOK -- selisih > 0,004 dari cnn3.

Selisihnya 0,0144 dan arahnya "Kaggle jauh lebih baik", yang mustahil untuk resep identik.
Sebabnya bukan lingkungan: **konstanta pembandingnya yang salah jenis.**

    `sapu_tta()` menghitung  po = post_tr(o)  lalu  lb_real(po)   -> SUDAH di-post-process
    konstanta 0,2091 di `CLAUDE.md` adalah  lb_real(oof) MENTAH   -> BELUM di-post-process

Post-processing (smoothing per event + ekspansi varians) memangkas ~0,019 di sisi desimal,
jadi membandingkan angka post terhadap angka mentah menghasilkan "gain" 0,0144 yang murni
artefak. Skrip ini menghitung kedua versi untuk semua kandidat cnn3 supaya konstanta yang
benar tercatat dan tidak terulang.

Konsekuensinya membalik verdikt: run A ternyata **lebih buruk 0,0050** dari cnn3, bukan
lebih baik 0,0144. Rincian di `CLAUDE.md` bagian "Gerbang kontrol nb12".

    python "Case 1/experiments/exp50_kontrol_nb12.py"
"""
import _path  # noqa: F401
import numpy as np
import lab_common as C
from fastscore import Post

# Parameter Post PERSIS default kelas Post di notebook Kaggle dan di lab_blend.search.
# fastscore.Post punya default LAIN (lam_deep 0,35 / T_deep 100) -- jangan pakai itu di
# sini, selisihnya kecil tapi cukup untuk menggeser perbandingan 0,0010.
POST_ARGS = (0.95, 0.5, 150, 1.15, 1.05)
post = Post(C.d_tr, *POST_ARGS)

# Angka yang dicetak notebook 09 di Kaggle, semuanya SUDAH lewat post_tr.
KAGGLE = {
    "A K=1  (= resep cnn3)": (0.1947, 0.1457, 0.2417, +0.032),
    "A K=8  (+TTA)":         (0.1936, 0.1458, 0.2396, +0.032),
    "B K=1  (+klip)":        (0.1914, 0.1443, 0.2366, +0.038),
    "B K=8  (+TTA+klip)":    (0.1904, 0.1429, 0.2359, +0.037),
}


def baris(nama, raw, po):
    return "%-22s %9.4f %9.4f %9.4f %9.4f %+9.3f" % (
        nama, C.lb_real(raw), C.lb_real(po), C.part_real(po, True),
        C.part_real(po, False), C.bias_rnd(po))


def main():
    print("Post: lam_dec 0,95 | lam_deep 0,5 | T_deep 150 | a_dec 1,15 | a_rnd 1,05\n")
    print("%-22s %9s %9s %9s %9s %9s" % ("kandidat", "MENTAH", "post", "dec", "rnd", "bias"))
    print("-" * 74)

    lokal = {}
    for n in ["cnn3", "cnn3_s2", "cnn3_avg", "cnn3_dir"]:
        p = C.CACHE / f"{n}.npz"
        if not p.exists():
            print("%-22s (tidak ada di cache/)" % n)
            continue
        o = np.load(p)["oof"]
        lokal[n] = (C.lb_real(o), C.lb_real(post(o)))
        print(baris(n, o, post(o)))

    print("\n%-22s %9s %9s %9s %9s %9s" % ("Kaggle nb09", "-", "post", "dec", "rnd", "bias"))
    print("-" * 74)
    for k, (lb, dec, rnd, b) in KAGGLE.items():
        print("%-22s %9s %9.4f %9.4f %9.4f %+9.3f" % (k, "-", lb, dec, rnd, b))

    if "cnn3" not in lokal:
        print("\ncache/cnn3.npz tidak ada -- tidak bisa menyimpulkan.")
        return

    raw3, post3 = lokal["cnn3"]
    gap = KAGGLE["A K=1  (= resep cnn3)"][0] - post3
    print("\n" + "=" * 74)
    print("KONSTANTA KONTROL YANG BENAR")
    print("=" * 74)
    print("  yang dipakai notebook 09 : %.4f  (lb_real MENTAH cnn3)   <- SALAH JENIS" % raw3)
    print("  yang seharusnya          : %.4f  (lb_real cnn3 SETELAH post_tr)" % post3)
    print("  selisih dua jenis itu    : %.4f  -- inilah 'gain' semu 0,0144" % (raw3 - post3))
    print()
    print("  gap lingkungan sebenarnya: %+.4f  (run A vs cnn3, dua-duanya post)" % gap)
    print("  %s" % ("run A LEBIH BURUK -- Kaggle tidak mereproduksi run lokal."
                    if gap > 0 else "run A lebih baik."))

    if "cnn3_s2" in lokal:
        spread = abs(lokal["cnn3"][1] - lokal["cnn3_s2"][1])
        print("  derau antar-paket 3-seed : %.4f  (cnn3 vs cnn3_s2, lokal)" % spread)
        print("  gap = %.1fx derau itu -- %s" % (
            gap / spread if spread else float("nan"),
            "terlalu besar untuk derau seed." if gap > 3 * spread else "masih mungkin derau."))

    if "cnn3_avg" in lokal:
        print()
        print("PERBANDINGAN YANG BENAR untuk kandidat terbaik nb09:")
        print("  cnn3_avg (lokal, 6 seed) : %.4f" % lokal["cnn3_avg"][1])
        print("  cnn12b_tta (Kaggle)      : %.4f  -> %+.4f" % (
            KAGGLE["B K=8  (+TTA+klip)"][0],
            KAGGLE["B K=8  (+TTA+klip)"][0] - lokal["cnn3_avg"][1]))
        print("  Konsisten dengan verdikt blend nb09 (gain +0,0004, menang 4/12).")

    print()
    print("EFEK TERISOLASI (internal Kaggle, gap lingkungan saling meniadakan):")
    a1 = KAGGLE["A K=1  (= resep cnn3)"][0]
    print("  TTA          : %+.4f" % (a1 - KAGGLE["A K=8  (+TTA)"][0]))
    print("  bobot klip   : %+.4f" % (a1 - KAGGLE["B K=1  (+klip)"][0]))
    print("  keduanya     : %+.4f" % (a1 - KAGGLE["B K=8  (+TTA+klip)"][0]))
    print("  Angka-angka ini SAH -- lewat jalur kode yang sama, tanpa konstanta lokal.")


if __name__ == "__main__":
    main()
