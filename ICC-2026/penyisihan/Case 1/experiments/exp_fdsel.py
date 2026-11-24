"""Sapuan bobot objektif seleksi: seberapa jauh kita percaya sisi bulat?

`lb_real = 0,49*dec + 0,51*rnd` menimbang kedua sisi menurut KOMPOSISI TEST. Tapi nb9
membuktikan sisi bulat sebagian ilusi: label pseudo-event-nya palsu, jadi gain di sana
tidak transfer. Sapuan ini memakai objektif seleksi `FD_sel*dec + (1-FD_sel)*rnd` dengan
FD_sel dari 0,49 (nb8) sampai 1,0 (desimal saja), dan melihat ke mana bobot blend bergerak.

Skor yang DILAPORKAN tetap `lb_real` apa adanya -- yang diubah cuma objektif pemilihan.
"""
import _path, numpy as np, pandas as pd
import lab_common as C
from lab_blend import ld
from fastscore import Post

NB8 = ["swA_sqrt", "resA_dep", "resB_dep", "resB_c30", "resB_p05",
       "cnnres", "cnn3_avg", "cnn3_dir"]
FAM = {"swA_sqrt": "A", "resA_dep": "A", "resB_dep": "B", "resB_c30": "B",
       "resB_p05": "B", "cnnres": "CNN", "cnn3_avg": "CNN", "cnn3_dir": "CNN"}
O = np.stack([ld(n)[0] for n in NB8]); E = np.stack([ld(n)[1] for n in NB8])
post_tr = Post(C.d_tr, 0.95, 0.5, 150, 1.15, 1.05)
post_te = Post(C.d_te, 0.95, 0.5, 150, 1.15, 1.05)
y, ev = C.y, C.ev


class Side:
    def __init__(self, dec, keep):
        m = keep & ((~C.rnd_tr) if dec else C.rnd_tr)
        self.idx = np.where(m)[0]; self.per = []
        for e in C.EVR:
            _, inv = np.unique(e[self.idx], return_inverse=True)
            nrec = np.bincount(inv).astype(float)
            mm = np.zeros(len(nrec)); mm[inv] = y[self.idx]
            w = C.mag_weight(mm); self.per.append((inv, nrec, w, w.sum(), len(nrec)))

    def __call__(self, p):
        err = np.abs(y[self.idx] - p[self.idx]); s = 0.0
        for inv, nrec, w, wsum, ne in self.per:
            s += (w * (np.bincount(inv, weights=err, minlength=ne) / nrec)).sum() / wsum
        return s / len(self.per)


rng = np.random.RandomState(0)
W = np.vstack([rng.dirichlet(np.ones(len(NB8)) * 0.6, size=8000), np.eye(len(NB8))])
Q = np.stack([post_tr(x @ O) for x in W])

uev = np.unique(ev)
splits = []
for rep in range(6):
    h1 = np.isin(ev, np.random.RandomState(100 + rep).permutation(uev)[:len(uev) // 2])
    for keep in (h1, ~h1):
        splits.append((Side(True, keep), Side(False, keep),
                       Side(True, ~keep), Side(False, ~keep)))

# skor tiap kandidat blend di tiap belahan, sekali saja
print("pra-hitung skor per belahan ...", flush=True)
PRE = []
for sd_, sr_, shd, shr in splits:
    PRE.append((np.array([sd_(q) for q in Q]), np.array([sr_(q) for q in Q]),
                np.array([shd(q) for q in Q]), np.array([shr(q) for q in Q])))

w_nb8 = np.load(C.CACHE / "w_nb9.npy")
p_nb8_tr = post_tr(w_nb8 @ O); p_nb8_te = post_te(w_nb8 @ E)
ref_dec = [shd(p_nb8_tr) for _, _, shd, _ in splits]
ref_all = [C.FD * shd(p_nb8_tr) + (1 - C.FD) * shr(p_nb8_tr) for _, _, shd, shr in splits]

rows = []
WS = {}
for fd in [0.49, 0.60, 0.70, 0.80, 0.90, 1.00]:
    ws, gd, ga = [], [], []
    for k, (vd, vr, hd, hr) in enumerate(PRE):
        i = int((fd * vd + (1 - fd) * vr).argmin())
        ws.append(W[i]); gd.append(hd[i] - ref_dec[k])
        ga.append(C.FD * hd[i] + (1 - C.FD) * hr[i] - ref_all[k])
    wm = np.mean(ws, 0); wm /= wm.sum(); WS[fd] = wm
    o = post_tr(wm @ O); p = post_te(wm @ E)
    fam = pd.Series(wm, index=[FAM[n] for n in NB8]).groupby(level=0).sum()
    rows.append(dict(FD_sel=fd, w_A=fam["A"], w_B=fam["B"], w_CNN=fam["CNN"],
                     lb_real=C.lb_real(o), dec=C.part_real(o, True), rnd=C.part_real(o, False),
                     gain_dec=np.mean(gd), menang_dec=sum(g < 0 for g in gd),
                     gain_all=np.mean(ga),
                     bias=C.bias_rnd(o), mean_te=p[C.MT].mean(), sd_te=p[C.rnd_te].std(),
                     korel_nb8=np.corrcoef(p, p_nb8_te)[0, 1]))

df = pd.DataFrame(rows)
pd.set_option("display.width", 200)
print()
print(df.round(4).to_string(index=False))
print()
print("baris FD_sel=0,49 adalah notebook_8 apa adanya (sanity check).")
np.savez(C.CACHE / "fdsel.npz", **{("w%d" % int(k * 100)): v for k, v in WS.items()})
