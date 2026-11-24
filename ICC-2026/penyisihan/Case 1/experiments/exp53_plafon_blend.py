"""PLAFON strategi "tambah kandidat": seberapa jauh blend BISA sampai, dengan 70 kandidat?

Pertanyaan yang membatasi semua sisa pekerjaan, dan belum pernah ditanyakan langsung:

    Target LB 0,1800 butuh lb_real 0,1714 (dari 0,1762 sekarang).
    Kalau SELURUH kandidat yang pernah dilatih di repo ini dibobot SEOPTIMAL MUNGKIN,
    sampai berapa?

Kalau plafon oracle-nya sendiri masih jauh di atas 0,1714, maka "tambah kandidat ke-N"
adalah strategi yang mati — bukan karena idenya jelek, tapi karena ruang yang dijangkau
kombinasi linear kandidat-kandidat ini memang tidak memuat 0,1714. Itu vonis yang jauh
lebih berguna daripada satu lagi notebook GPU yang gagal.

Dua angka dihitung:

  ORACLE   bobot dicari dan diukur di DATA YANG SAMA. Ini batas atas yang tidak mungkin
           dilampaui oleh metode seleksi apa pun. Angka ini OPTIMIS dan tidak bisa
           disubmit -- gunanya cuma sebagai plafon.
  JUJUR    bobot dicari di separuh event, diukur di separuh lain, 12 belahan. Ini yang
           benar-benar bisa diharapkan.

Selisih keduanya = optimisme seleksi, dan ia tumbuh seiring jumlah kandidat. Itu sebabnya
"masukkan semua kandidat sekaligus" bukan jawaban: 70 kandidat memberi plafon oracle yang
lebih rendah tapi optimisme yang jauh lebih besar.

Metodenya greedy forward selection dengan pengembalian (Caruana et al.) — untuk himpunan
kandidat sebesar ini, sampling Dirichlet tidak akan pernah menemukan optimumnya.

    python "Case 1/experiments/exp53_plafon_blend.py"
"""
import _path  # noqa: F401
import glob
import os
import sys
import numpy as np

import lab_common as C
from fastscore import Scorer, Post

POST_ARGS = (0.95, 0.5, 150, 1.15, 1.05)
post_tr = Post(C.d_tr, *POST_ARGS)
sc = Scorer(C.EVR, np.ones(len(C.y), bool))

NB8 = ["swA_sqrt", "resA_dep", "resB_dep", "resB_c30", "resB_p05",
       "cnnres", "cnn3_avg", "cnn3_dir"]

# Kandidat yang HARUS dikeluarkan: bukan model, melainkan hasil blend atau model rusak.
# `blend_nb9` adalah blend jadi (memasukkannya = membocorkan jawaban ke dalam pencarian).
# `cnn13_join` lb_real 0,3730 dengan bias_rnd +0,378 -- rusak, dan kandidat rusak terbukti
# tetap diberi bobot oleh pencarian bobot (MLP divergen di nb5 dapat 0,36).
BUANG = {"blend_nb9", "cnn13_join"}


def semua_kandidat():
    ok = []
    for f in sorted(glob.glob(str(C.CACHE / "*.npz"))):
        n = os.path.basename(f)[:-4]
        if n in BUANG or n.endswith("_syms"):
            continue
        try:
            z = np.load(f)
        except Exception:
            continue
        if "oof" in z and "pte" in z and len(z["oof"]) == len(C.y) and len(z["pte"]) == 2300:
            ok.append(n)
    return ok


def greedy(O, scorer, n_iter=60, init=None):
    """Caruana forward selection dengan pengembalian.

    Mulai dari kandidat tunggal terbaik (atau `init`), lalu ulang: tambahkan kandidat mana
    pun -- termasuk yang sudah dipakai -- yang paling menurunkan skor rata-rata berjalan.
    Boleh mengulang kandidat, dan itu yang membuat bobotnya bisa tidak seragam."""
    m = len(O)
    if init is None:
        v = [scorer(post_tr(O[i])) for i in range(m)]
        pilih = [int(np.argmin(v))]
    else:
        pilih = list(init)
    jml = O[pilih].sum(0)
    best = scorer(post_tr(jml / len(pilih)))
    for _ in range(n_iter):
        kand = [(scorer(post_tr((jml + O[i]) / (len(pilih) + 1))), i) for i in range(m)]
        v, i = min(kand)
        if v >= best - 1e-6:
            break
        best = v
        pilih.append(i)
        jml = jml + O[i]
    w = np.bincount(pilih, minlength=m).astype(float)
    return w / w.sum(), best


def bobot_ke_skor(w, O, scorer):
    return scorer(post_tr(w @ O))


def jalankan(nama, names, O, n_iter=60):
    """Hitung ORACLE dan JUJUR untuk satu himpunan kandidat."""
    w_or, s_or = greedy(O, sc, n_iter=n_iter)

    uev = np.unique(C.ev)
    hasil, ws = [], []
    for rep in range(6):
        r = np.random.RandomState(100 + rep)
        perm = r.permutation(uev)
        h1 = np.isin(C.ev, perm[:len(perm) // 2])
        for keep in (h1, ~h1):
            ss = Scorer(C.EVR, keep)
            sh = Scorer(C.EVR, ~keep)
            w, _ = greedy(O, ss, n_iter=n_iter)
            hasil.append(bobot_ke_skor(w, O, sh))
            ws.append(w)
    wm = np.mean(ws, 0); wm /= wm.sum()
    s_ju = float(np.mean(hasil))
    s_rata = bobot_ke_skor(wm, O, sc)

    aktif = [(names[i], round(float(wm[i]), 3)) for i in np.argsort(-wm)[:8] if wm[i] > 0.01]
    print("\n%-34s n=%d" % (nama, len(names)))
    print("  ORACLE (bobot & ukur di data sama) : %.4f   <- batas atas, TIDAK bisa disubmit"
          % s_or)
    print("  JUJUR  (12 belahan, ukur di luar)  : %.4f" % s_ju)
    print("  bobot rata-rata lintas belahan     : %.4f  (dipakai di data penuh)" % s_rata)
    print("  optimisme seleksi                  : %+.4f" % (s_ju - s_or))
    print("  kandidat aktif:", aktif)
    return dict(nama=nama, n=len(names), oracle=s_or, jujur=s_ju, rata=s_rata, w=wm)


def main():
    semua = semua_kandidat()
    O_all = np.stack([np.load(C.CACHE / f"{n}.npz")["oof"] for n in semua])
    print("kandidat tersedia: %d  (dibuang: %s)" % (len(semua), sorted(BUANG)))

    O8 = np.stack([np.load(C.CACHE / f"{n}.npz")["oof"] for n in NB8])
    w8 = np.load(C.CACHE / "w_nb9.npy")
    print("\nacuan notebook_8 (bobot terpasang): lb_real %.4f   [LB 0,1849]"
          % sc(post_tr(w8 @ O8)))
    print("target LB 0,1800 -> butuh lb_real 0,1714")
    print("target peringkat 1 (LB 0,1837) -> butuh lb_real 0,1751")

    print("\n" + "=" * 78)
    print("PLAFON")
    print("=" * 78)
    R = [jalankan("8 kandidat nb8", NB8, O8),
         jalankan("SEMUA kandidat", semua, O_all)]

    print("\n" + "=" * 78)
    print("VONIS")
    print("=" * 78)
    plafon = min(r["oracle"] for r in R)
    jujur = min(r["jujur"] for r in R)
    print("  plafon ORACLE terbaik : %.4f" % plafon)
    print("  hasil JUJUR terbaik   : %.4f" % jujur)
    for tgt, nm in [(0.1751, "peringkat 1 (LB 0,1837)"), (0.1714, "LB 0,1800")]:
        st = ("TERCAPAI" if jujur <= tgt else
              "di luar jangkauan (bahkan oracle meleset %+.4f)" % (plafon - tgt)
              if plafon > tgt else
              "hanya oracle yang mencapainya -- artinya butuh KANDIDAT BARU, bukan bobot baru")
        print("  %-26s butuh %.4f  -> %s" % (nm, tgt, st))
    print("""
  Cara membaca: kalau ORACLE saja tidak mencapai target, tidak ada cara membobot
  kandidat yang SUDAH ADA untuk sampai ke sana -- seluruh sisa jalan harus datang
  dari kandidat yang belum pernah dilatih. Kalau oracle mencapainya tapi JUJUR
  tidak, yang kurang adalah data untuk memilih bobot, bukan kandidatnya.""")
    return 0


if __name__ == "__main__":
    sys.exit(main())
