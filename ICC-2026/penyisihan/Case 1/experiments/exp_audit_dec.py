"""Audit pasca-nb9: apakah blend nb8 sendiri ikut mengeksploitasi degenerasi label?

Pelajaran nb9: metode yang menyeragamkan prediksi di dalam grup depth dibayar berlebihan
oleh `lb_real` di sisi bulat, karena record dari gempa berbeda berbagi `y` di sana.
Model B memakai FITUR AGREGAT GRUP -- persis kanal yang sama. Kalau ia over-weight, itu
kerugian LB yang bisa dipanen hari ini tanpa model baru.

Uji: cari bobot blend dengan holdout jujur yang hanya menilai SISI DESIMAL (event nyata,
98% murni), lalu bandingkan bobotnya dengan bobot nb8 yang dipilih di kedua sisi.
"""
import _path, numpy as np, pandas as pd
import lab_common as C
from lab_blend import ld
from fastscore import Post

NB8 = ["swA_sqrt", "resA_dep", "resB_dep", "resB_c30", "resB_p05",
       "cnnres", "cnn3_avg", "cnn3_dir"]
FAM = {"swA_sqrt": "A", "resA_dep": "A", "resB_dep": "B(grup)", "resB_c30": "B(grup)",
       "resB_p05": "B(grup)", "cnnres": "CNN", "cnn3_avg": "CNN", "cnn3_dir": "CNN"}

O = np.stack([ld(n)[0] for n in NB8])
post = Post(C.d_tr, 0.95, 0.5, 150, 1.15, 1.05)
y, ev = C.y, C.ev


class SideScorer:
    """eb_twmae di SATU sisi saja, atas subset event, dirata-rata 8 realisasi EVR."""
    def __init__(self, dec, keep):
        m = keep & ((~C.rnd_tr) if dec else C.rnd_tr)
        self.idx = np.where(m)[0]
        self.per = []
        for e in C.EVR:
            _, inv = np.unique(e[self.idx], return_inverse=True)
            nrec = np.bincount(inv).astype(float)
            mm = np.zeros(len(nrec)); mm[inv] = y[self.idx]
            w = C.mag_weight(mm)
            self.per.append((inv, nrec, w, w.sum(), len(nrec)))

    def __call__(self, p):
        err = np.abs(y[self.idx] - p[self.idx]); s = 0.0
        for inv, nrec, w, wsum, ne in self.per:
            s += (w * (np.bincount(inv, weights=err, minlength=ne) / nrec)).sum() / wsum
        return s / len(self.per)


ALL = np.ones(len(y), bool)
sc_dec, sc_rnd = SideScorer(True, ALL), SideScorer(False, ALL)

print("=" * 76)
print("1. TIAP KANDIDAT SENDIRIAN: menang di sisi mana?")
print("=" * 76)
rows = []
for i, n in enumerate(NB8):
    p = post(O[i])
    rows.append((n, FAM[n], sc_dec(p), sc_rnd(p)))
df = pd.DataFrame(rows, columns=["kandidat", "keluarga", "desimal", "bulat"])
df["rasio"] = df.bulat / df.desimal
print(df.round(4).to_string(index=False))
print()
print("  rasio tinggi = relatif lebih kuat di sisi DESIMAL (event nyata)")
print("  rasio rendah = relatif lebih kuat di sisi BULAT (label degenerate) <- curigai")

print()
print("=" * 76)
print("2. BOBOT BLEND: dipilih di KEDUA sisi (nb8) vs hanya SISI DESIMAL")
print("=" * 76)
rng = np.random.RandomState(0)
W = np.vstack([rng.dirichlet(np.ones(len(NB8)) * 0.6, size=8000), np.eye(len(NB8))])
Q = np.stack([post(x @ O) for x in W])

uev = np.unique(ev)
res = {}
for tag, mkscore in (("dec+rnd (nb8)", None), ("dec saja", "dec")):
    ws, gains = [], []
    for rep in range(6):
        h1 = np.isin(ev, np.random.RandomState(100 + rep).permutation(uev)[:len(uev) // 2])
        for keep in (h1, ~h1):
            if mkscore == "dec":
                ss, sh = SideScorer(True, keep), SideScorer(True, ~keep)
            else:
                sd_, sr_ = SideScorer(True, keep), SideScorer(False, keep)
                shd, shr = SideScorer(True, ~keep), SideScorer(False, ~keep)
                ss = lambda p, a=sd_, b=sr_: C.FD * a(p) + (1 - C.FD) * b(p)
                sh = lambda p, a=shd, b=shr: C.FD * a(p) + (1 - C.FD) * b(p)
            v = np.array([ss(q) for q in Q]); i = int(v.argmin())
            ws.append(W[i]); gains.append(sh(Q[i]))
    wm = np.mean(ws, 0); wm /= wm.sum()
    res[tag] = wm

out = pd.DataFrame({"kandidat": NB8, "keluarga": [FAM[n] for n in NB8],
                    "w_nb8": np.load(C.CACHE / "w_nb9.npy"),
                    "w_dec+rnd": res["dec+rnd (nb8)"], "w_dec_saja": res["dec saja"]})
out["selisih"] = out.w_dec_saja - out.w_nb8
print(out.round(3).to_string(index=False))
print()
print("per keluarga:")
print(out.groupby("keluarga")[["w_nb8", "w_dec_saja"]].sum().round(3).to_string())

print()
print("=" * 76)
print("3. APA SKOR BLEND BOBOT-DESIMAL DI KEDUA SISI?")
print("=" * 76)
for tag, w in (("bobot nb8", np.load(C.CACHE / "w_nb9.npy")),
               ("bobot dec-saja", res["dec saja"])):
    p = post(w @ O)
    print("  %-16s lb_real %.4f   dec %.4f   rnd %.4f   bias_rnd %+.3f"
          % (tag, C.lb_real(p), C.part_real(p, True), C.part_real(p, False), C.bias_rnd(p)))
