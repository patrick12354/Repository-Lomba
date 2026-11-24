"""Post-mortem notebook_9: gain lb_real -0,0044 tapi LB +0,0007. Kenapa nol transfer."""
import _path, numpy as np, pandas as pd
import lab_common as C
from lab_blend import ld
from fastscore import Post, Scorer

NB8 = ["swA_sqrt","resA_dep","resB_dep","resB_c30","resB_p05","cnnres","cnn3_avg","cnn3_dir"]
w = np.load(C.CACHE/"w_nb9.npy")
O = np.stack([ld(n)[0] for n in NB8]); E = np.stack([ld(n)[1] for n in NB8])
btr, bte = w @ O, w @ E
post_tr = Post(C.d_tr, 0.95, 0.5, 150, 1.15, 1.05)
post_te = Post(C.d_te, 0.95, 0.5, 150, 1.15, 1.05)

Z = np.load(C.CACHE/"set2.npz")
corr, cte = Z["corr"].astype(np.float64), Z["cte"].astype(np.float64)

def demean(c, rnd):
    c = c.copy()
    for m in (rnd, ~rnd): c[m] -= c[m].mean()
    return c

ctr_d, cte_d = demean(corr, C.rnd_tr), demean(cte, C.rnd_te)
y, ev, d_tr, d_te = C.y, C.ev, C.d_tr, C.d_te
LAM = 0.5

print("=" * 72)
print("1. UKURAN PSEUDO-EVENT: label degenerasi hanya di sisi bulat")
print("=" * 72)
sz = pd.Series(ev).map(pd.Series(ev).value_counts()).values
for nm, m in [("desimal", ~C.rnd_tr), ("bulat<100km", C.MR),
              ("bulat>=100km", C.rnd_tr & (d_tr >= 100))]:
    print("  %-13s n=%5d  ukuran pseudo-event: median %3.0f  max %4d"
          % (nm, m.sum(), np.median(sz[m]), sz[m].max()))

print()
print("=" * 72)
print("2. APA YANG DIPELAJARI KOREKSI: residual sejati atau tarik-ke-median grup?")
print("=" * 72)
resid = y - btr
gm = np.zeros_like(btr)
for dv in np.unique(d_tr):
    m = d_tr == dv
    gm[m] = np.median(btr[m])
pull = gm - btr
for nm, m in [("desimal", ~C.rnd_tr), ("bulat<100km", C.MR)]:
    print("  %-12s  vs residual sejati %+.3f   vs tarik-ke-median-grup %+.3f"
          % (nm, np.corrcoef(ctr_d[m], resid[m])[0, 1],
             np.corrcoef(ctr_d[m], pull[m])[0, 1]))

print()
print("=" * 72)
print("3. KEPADATAN CO-MEMBER di dalam grup depth (train)")
print("=" * 72)
print("  Fraksi pasangan di dalam satu grup depth yang punya LABEL SAMA.")
print("  Tinggi = 'tarik ke tetangga' hampir selalu benar di train.")
rows = []
for dv in np.unique(d_tr[C.MR]):
    m = (d_tr == dv) & C.MR
    n = int(m.sum())
    if n < 20: continue
    _, cts = np.unique(y[m], return_counts=True)
    rows.append((dv, n, (cts * (cts - 1)).sum() / (n * (n - 1))))
df = pd.DataFrame(rows, columns=["depth", "n", "frac_selabel"]).sort_values("n", ascending=False)
print(df.head(8).to_string(index=False))
print("  rata-rata berbobot record: %.3f" % np.average(df.frac_selabel, weights=df.n))
print("  >> di TEST grup yang sama berisi ~n/8 gempa terpisah -> fraksi selabel jauh lebih kecil.")

print()
print("=" * 72)
print("4. EFEK KOREKSI DI TEST: seberapa kuat ia merapatkan grup?")
print("=" * 72)
p8, p9 = post_te(bte), post_te(bte + LAM * cte_d)
for nm, mm in [("bulat<100km", C.MT), ("desimal", ~C.rnd_te)]:
    s8, s9 = [], []
    for dv in np.unique(d_te[mm]):
        m = (d_te == dv) & mm
        if m.sum() < 5: continue
        s8.append(p8[m].std()); s9.append(p9[m].std())
    print("  %-12s sd dalam-grup: nb8 %.4f -> nb9 %.4f  (%+.1f%%)"
          % (nm, np.mean(s8), np.mean(s9), 100 * (np.mean(s9) / np.mean(s8) - 1)))

print()
print("=" * 72)
print("5. GAIN lb_real DIPECAH PER SISI")
print("=" * 72)
o8, o9 = post_tr(btr), post_tr(btr + LAM * ctr_d)
for nm, dec in [("desimal (event NYATA)", True), ("bulat (pseudo-event PALSU)", False)]:
    a, b = C.part_real(o8, dec), C.part_real(o9, dec)
    print("  %-28s %.4f -> %.4f  (%+.4f)" % (nm, a, b, b - a))
print("  %-28s %.4f -> %.4f  (%+.4f)"
      % ("lb_real", C.lb_real(o8), C.lb_real(o9), C.lb_real(o9) - C.lb_real(o8)))
