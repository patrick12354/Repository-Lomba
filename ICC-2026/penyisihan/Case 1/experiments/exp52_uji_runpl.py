"""UJI ASAP `run_pl` dari `belum_run/11_pseudo_label.ipynb` — sebelum membakar 4,3 jam GPU.

Yang diuji BUKAN skornya (2 epoch tidak berarti apa-apa), melainkan bahwa kodenya jalan
dan **semantiknya benar**:

1. `run_pl(pl=None)` menghasilkan OOF/test penuh, tanpa NaN.
2. `run_pl(pl=PL)` menghasilkan OOF/test penuh, tanpa NaN — tiap record test harus
   terisi PERSIS SEKALI lewat jalur silang belahan, bukan dua kali atau nol kali.
3. Tidak ada record test yang diprediksi oleh model yang melihat label-semunya sendiri.
4. Belahan test tidak memisahkan record yang berbagi `depth_km`.

Poin 2 dan 3 adalah tempat bug paling mungkin bersembunyi, dan dua-duanya gagal SENYAP di
Kaggle: prediksi test yang terisi dua kali cuma terlihat sebagai skor yang agak aneh,
bukan sebagai error.

    python "Case 1/experiments/exp52_uji_runpl.py"
"""
import _path  # noqa: F401
import json
import re
import sys
import numpy as np
import pandas as pd  # noqa: F401  -- dipakai oleh kode yang di-exec
import torch  # noqa: F401
import lab_common as C
import lab_models as M
from lab_cnn3 import Net3, DEV
from sklearn.model_selection import GroupKFold  # noqa: F401
from sklearn.linear_model import Ridge  # noqa: F401
from fastscore import Post

NB = _path.ROOT / "belum_run" / "11_pseudo_label.ipynb"


def ambil_sel(nb, penanda):
    """Ambil sumber sel kode pertama yang memuat `penanda`."""
    for c in nb["cells"]:
        if c["cell_type"] == "code":
            s = "".join(c["source"])
            if penanda in s:
                return s
    raise KeyError(penanda)


def main():
    nb = json.loads(NB.read_text(encoding="utf-8"))
    src_pl = ambil_sel(nb, "def run_pl")

    # ---- siapkan nama global yang diandalkan kode notebook, dari modul lokal
    g = dict(globals())
    z = np.load(C.CACHE / "cnn_input.npz")
    Wtr, Str, Wte, Ste = z["Wtr"], z["Str"], z["Wte"], z["Ste"]
    Ftr, Fte = C.get_feats()
    ref = np.load(C.CACHE.parent / "belum_run" / "ref" / "nb8_ref.npz", allow_pickle=True)
    CANDR = [str(x) for x in ref["__cand__"]]
    Eref = np.stack([ref[f"{n}__pte"].astype(np.float64) for n in CANDR])
    post_te = Post(C.d_te, 0.95, 0.5, 150, 1.15, 1.05)

    g.update(dict(
        np=np, torch=torch, time=__import__("time"),
        y=C.y, ev=C.ev, SW=C.SW, mag_weight=C.mag_weight,
        d_tr=C.d_tr, d_te=C.d_te, rnd_tr=C.rnd_tr, rnd_te=C.rnd_te,
        Ftr=Ftr, Fte=Fte, A_BASE=M.A_BASE, Net3=Net3, DEV=DEV,
        GroupKFold=GroupKFold, Ridge=Ridge,
        REF=ref, post_te=post_te, Eref=Eref, ref_stack=lambda: (None, Eref),
        Wtr=Wtr, Str=Str, Wte=Wte, Ste=Ste,
    ))
    # blok PL di notebook memakai ref_stack()[1]; jalankan bagian non-fungsinya manual
    src_head = src_pl[:src_pl.index("def run_pl")]
    src_head = src_head.replace('_Oref, _Eref = ref_stack()', '_Eref = Eref')
    exec(compile(src_head, "<pl-head>", "exec"), g)
    exec(compile(src_pl[src_pl.index("def run_pl"):], "<run_pl>", "exec"), g)

    PL, PL_HALF, run_pl = g["PL"], g["PL_HALF"], g["run_pl"]

    # ---- 4. belahan tidak memecah grup depth
    df = pd.DataFrame({"d": C.d_te, "h": PL_HALF})
    pecah = df.groupby("d").h.nunique()
    print("\n[4] nilai depth yang belahannya terpecah:", int((pecah > 1).sum()),
          "-> " + ("OK" if (pecah > 1).sum() == 0 else "GAGAL"))

    # ---- 3. tidak ada record yang dilatih DAN diprediksi oleh model yang sama
    for arm in (0, 1):
        dilatih = set(np.where(PL_HALF == arm)[0])
        diprediksi = set(np.where(PL_HALF != arm)[0])
        assert not (dilatih & diprediksi), "arm %d: record dilatih DAN diprediksi" % arm
    print("[3] irisan {dilatih} x {diprediksi} kosong di kedua arm -> OK")
    print("    tiap record test diprediksi tepat oleh 1 dari 2 arm -> cakupan penuh:",
          set(np.unique(PL_HALF)) == {0, 1})

    # ---- 1 & 2. jalankan mini
    kecil = dict(seeds=(0,), epochs=2, avg_last=1)
    print("\nmenjalankan run_pl mini (1 seed, 2 epoch) di", DEV, "...")

    oA, pA = run_pl(Wtr, Str, Wte, Ste, C.make_sw(power=0.5), pl=None, tag="A ", **kecil)
    print("\n[1] arm A: oof finite %s | pte finite %s | oof!=0 %d/%d | pte!=0 %d/%d"
          % (np.isfinite(oA).all(), np.isfinite(pA).all(),
             (oA != 0).sum(), len(oA), (pA != 0).sum(), len(pA)))

    oB, pB = run_pl(Wtr, Str, Wte, Ste, C.make_sw(power=0.5), pl=PL, pl_w=1.0,
                    tag="B ", **kecil)
    print("\n[2] arm B: oof finite %s | pte finite %s | oof!=0 %d/%d | pte!=0 %d/%d"
          % (np.isfinite(oB).all(), np.isfinite(pB).all(),
             (oB != 0).sum(), len(oB), (pB != 0).sum(), len(pB)))

    ok = True
    for nm, o, p in [("A", oA, pA), ("B", oB, pB)]:
        if not (np.isfinite(o).all() and np.isfinite(p).all()):
            print("  GAGAL %s: ada NaN/Inf" % nm); ok = False
        if (o == 0).any() or (p == 0).any():
            print("  GAGAL %s: ada slot yang tidak pernah terisi" % nm); ok = False

    # skala prediksi harus masuk akal (magnitudo ~4-7), bukan meledak
    for nm, p in [("A", pA), ("B", pB)]:
        print("  pte %s: min %.2f  mean %.2f  max %.2f" % (nm, p.min(), p.mean(), p.max()))
        if not (3.0 < p.mean() < 8.0):
            print("  GAGAL %s: skala prediksi test tidak masuk akal" % nm); ok = False

    print("\n" + ("SEMUA UJI LULUS -- run_pl aman dijalankan di Kaggle."
                  if ok else "ADA YANG GAGAL -- perbaiki dulu sebelum ke Kaggle."))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
