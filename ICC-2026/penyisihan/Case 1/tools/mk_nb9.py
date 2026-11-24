import _path  # noqa: F401  -- menaruh Case 1/ di sys.path
import json

def md(s): return {"cell_type":"markdown","metadata":{},"source":s.splitlines(True)}
def co(s): return {"cell_type":"code","execution_count":None,"metadata":{},"outputs":[],"source":s.splitlines(True)}

cells = []

cells.append(md("""# Case 1 — notebook_9: Demean di Training Tidak Cukup, Paksakan Saat Apply

`notebook_8` (LB **0,1849**, peringkat 2) menutup keluarga post-processing dan keluarga
non-deep. Lima notebook GPU lalu dijalankan di Kaggle — empat arsitektur CNN baru dan satu
set-transformer. **Empat CNN gagal semua**, set-transformer berhasil.

Tapi verdikt yang dicetak notebook Kaggle-nya **tidak boleh dipakai apa adanya**: ia memilih
setelan yang mendorong `bias_rnd` ke **+0,059**, dan `notebook_5` rugi di LB pada +0,056.

Notebook ini melakukan dua hal: mendokumentasikan kenapa keempat CNN gagal, lalu memperbaiki
koreksi set-transformer sehingga gain-nya tetap utuh tanpa menyentuh diagnostik transfer."""))

cells.append(co("""import sys, os
sys.path.insert(0, os.path.abspath("lab"))   # modul pipeline ada di lab/
import numpy as np, pandas as pd, json, warnings
warnings.filterwarnings("ignore")
import lab_common as C
from fastscore import Scorer, Post
pd.set_option("display.width", 220)

sc      = Scorer(C.EVR, np.ones(len(C.y), bool))
post_tr = Post(C.d_tr, 0.95, 0.5, 150, 1.15, 1.05)
post_te = Post(C.d_te, 0.95, 0.5, 150, 1.15, 1.05)

# Acuan notebook_8: blend 8 kandidat dengan bobotnya, disimpan di belum_run/ref/ supaya
# notebook Kaggle (yang tidak punya cache/) memakai angka yang sama persis.
R    = np.load("belum_run/ref/nb8_ref.npz", allow_pickle=True)
CAND = [str(x) for x in R["__cand__"]]
btr  = R["__w__"] @ np.stack([R[f"{n}__oof"].astype(np.float64) for n in CAND])
bte  = R["__w__"] @ np.stack([R[f"{n}__pte"].astype(np.float64) for n in CAND])
base, baset = post_tr(btr), post_te(bte)

print("acuan notebook_8: lb_real=%.4f  bias_rnd=%+.3f  mean_te=%.3f  sd_te=%.3f   [LB 0,1849]"
      % (sc(base), C.bias_rnd(base), baset[C.MT].mean(), baset[C.rnd_te].std()))"""))

cells.append(md("""---
## 1. Empat arsitektur CNN baru — semuanya gagal, dan sebabnya bukan \"lemah\"

Hipotesis di balik keempatnya: CNN v3 memberi terobosan −0,0070 di `notebook_8`, jadi
arsitektur lain di atas waveform yang sama mestinya menambah diversitas.

Yang terjadi sebaliknya. Tak satu pun mengalahkan `cnn3_avg` (0,2074) sebagai model tunggal,
tapi itu bukan sebab utamanya — `cnn3_dir` juga kalah (0,2116) dan tetap berguna. Sebab
sesungguhnya ada di kolom terakhir tabel: **korelasi 0,92–0,96 terhadap `cnn3_avg`.**"""))

cells.append(co("""gen = pd.DataFrame([
 dict(notebook="02 Inception 1D multi-skala", tunggal=0.2169, gain=+0.0014, menang="0/12", korelasi=0.955, menit=86),
 dict(notebook="03 TCN dilatasi tanpa pooling", tunggal=0.2106, gain=+0.0016, menang="1/12", korelasi=0.950, menit=124),
 dict(notebook="04 v3 diperlebar (w=80, 6 blok)", tunggal=0.2103, gain=+0.0012, menang="2/12", korelasi=0.963, menit=202),
 dict(notebook="05 konvolusi + transformer", tunggal=0.2253, gain=+0.0015, menang="0/12", korelasi=0.922, menit=108),
])
display(gen)
print("pembanding: cnn3_avg 0,2074 (korelasi 0,878) | cnn3_dir 0,2116 | LightGBM terbaik 0,2030")"""))

cells.append(md("""Pelajaran `notebook_8` — *\"korelasi rendah lebih berharga daripada skor tunggal yang
bagus\"* — di sini berlaku terbalik. CNN v3 mendapat bobot blend 0,404 semata karena
korelasinya 0,878. Keempat arsitektur baru ini pada dasarnya **melihat hal yang sama**
dengan CNN v3, cuma lewat jalan yang berbeda.

Sebelum menyimpulkan, keempatnya diuji lagi sebagai kandidat blend — sendiri maupun
bersama-sama — dengan protokol 12 belahan yang sama. Kalau ada diversitas tersembunyi,
pencarian bobot akan menemukannya."""))

cells.append(co("""gab = pd.DataFrame([
 dict(kandidat="nb8 + keempat CNN baru", lb_real=0.1756, jujur=0.1771, gain=+0.0012, menang="4/12",
      bobot_baru="cnn5 0,122 | cnn7 0,087 | cnn6 0,014 | cnn8 0,015"),
 dict(kandidat="nb8 + cnn5 + cnn7",      lb_real=0.1755, jujur=0.1769, gain=+0.0008, menang="4/12",
      bobot_baru="cnn5 0,131 | cnn7 0,087"),
 dict(kandidat="nb8 + cnn7 saja",        lb_real=0.1757, jujur=0.1775, gain=+0.0016, menang="1/12",
      bobot_baru="cnn7 0,136"),
])
display(gab)
print("Tidak ada yang menang. Keluarga 'arsitektur CNN 1D baru atas waveform yang sama' DITUTUP.")
print("Reproduksi: experiments/exp50_cnn_gabungan.py")"""))

cells.append(md("""Perhatikan `lb_real` ketiganya (0,1755–0,1757) terlihat **lebih baik** dari nb8 (0,1762).
Itu justru contoh kenapa `lb_real` data-penuh tidak boleh dipakai sendirian: begitu bobot
dicari di separuh event dan diukur di separuh lain, gain-nya berbalik jadi positif dan
menang cuma 1–4 dari 12. Selisihnya murni optimisme seleksi (+0,0012 s/d +0,0018)."""))

cells.append(md("""---
## 2. Set-transformer: gain-nya nyata, verdikt Kaggle-nya tidak

Ide set-transformer: alih-alih median grup depth yang buta, biarkan attention memutuskan
record mana yang saling co-belong. Set dibentuk **hanya dari record yang tersedia di
himpunan yang sedang dinilai** (fold validasi untuk OOF, test untuk test), supaya meniru
kondisi test-time.

Waktu diuji lokal sebelumnya, separuh gain-nya ternyata **pergeseran rata-rata sisi
depth-bulat** — persis prior katalog train (depth bulat rata-rata M 5,45 vs desimal 5,19)
yang membuat `notebook_2` dan `notebook_5` rugi di LB. Proporsi depth-bulat **32% di train
tapi 51% di test**, jadi prior itu selalu merugi.

Obatnya waktu itu: latih dengan target yang sudah **di-demean per subset**, supaya model
tidak punya cara mempelajari prior tersebut. Versi Kaggle memakai `demean=True`.

**Itu tidak cukup.** Koreksi yang dihasilkan tetap bermean **+0,0556** di subset depth-bulat
dangkal. Model punya cukup fitur untuk memulihkan prior yang dibuang dari label."""))

cells.append(co("""Z = np.load(C.CACHE/"set2.npz")          # dari sudah_run/hasil/01_set_transformer.zip
corr, cte = Z["corr"].astype(np.float64), Z["cte"].astype(np.float64)

def demean(c, rnd):
    \"\"\"buang rata-rata per subset -- dipaksakan di titik PENERAPAN, bukan di target training\"\"\"
    c = c.copy()
    for m in (rnd, ~rnd): c[m] -= c[m].mean()
    return c

ctr_d, cte_d = demean(corr, C.rnd_tr), demean(cte, C.rnd_te)
print("koreksi mentah (sudah demean=True saat training):")
print("   mean di subset bulat<100km = %+.4f   <- prior katalog kembali lewat fitur"
      % corr[C.MR].mean())
print("   sd = %.4f" % corr.std())"""))

cells.append(md("""### Sapuan `lam`, kedua versi berdampingan

Kolom yang menentukan bukan `lb_real`, melainkan `bias_rnd`. Aturan repo ini sudah tiga kali
terbukti: **`lb_real` mengukur data train; `bias_rnd` dan mean/sd prediksi sisi bulat
mengukur jarak ke test. Kalau bertabrakan, yang kedua menang.**"""))

cells.append(co("""grid = [0.0, 0.1, 0.15, 0.2, 0.25, 0.3, 0.4, 0.5, 0.6, 0.75]
rows = []
for tag, ct, ce in (("mentah", corr, cte), ("demean-apply", ctr_d, cte_d)):
    for l in grid:
        q, p = post_tr(btr + l*ct), post_te(bte + l*ce)
        rows.append(dict(versi=tag, lam=l, lb_real=round(sc(q),4),
                         dec=round(C.part_real(q,True),4), rnd=round(C.part_real(q,False),4),
                         bias_rnd=round(C.bias_rnd(q),3),
                         mean_te=round(float(p[C.MT].mean()),3),
                         sd_te=round(float(p[C.rnd_te].std()),3)))
sweep = pd.DataFrame(rows)
display(sweep.pivot(index="lam", columns="versi", values=["lb_real","bias_rnd","mean_te"]))"""))

cells.append(md("""Bacanya: di versi **mentah**, `bias_rnd` naik monoton bersama `lam` — +0,031 di lam 0
sampai +0,073 di lam 0,75. Di versi **demean-apply** ia **datar di +0,029/+0,031 sepanjang
sapuan**, dan `lb_real`-nya cuma tertinggal ~0,0004.

Notebook Kaggle memilih lam 0,50 pada baris mentah dan melabeli `bias_rnd = +0,059` sebagai
**AMAN**, karena ambangnya dipasang di 0,08. Ambang itu salah — dan tercatat di
`LEADERBOARD.md`: `notebook_5` rugi di LB dengan `bias_rnd` hanya **+0,056**."""))

cells.append(md("""---
## 3. Seleksi `lam` yang jujur

`lam` dipilih di separuh event lalu diukur di separuh **lain**, 12 belahan. Angka yang
dilaporkan adalah gain di belahan yang tidak dipakai memilih."""))

cells.append(co("""Q = np.stack([post_tr(btr + l*ctr_d) for l in grid])
uev = np.unique(C.ev); sel = []; gains = []
for rep in range(6):
    h1 = np.isin(C.ev, np.random.RandomState(100+rep).permutation(uev)[:len(uev)//2])
    for keep in (h1, ~h1):
        ss, sh = Scorer(C.EVR, keep), Scorer(C.EVR, ~keep)
        i = int(np.array([ss(q) for q in Q]).argmin())
        sel.append(grid[i]); gains.append(sh(Q[i]) - sh(base))
lam = float(np.median(sel))
print("lam terpilih per belahan :", sorted(sel))
print("lam final (median)       : %.2f" % lam)
print("gain holdout jujur       : %+.5f   (menang %d/12)" % (np.mean(gains), sum(g<0 for g in gains)))"""))

cells.append(md("""Sebaran `lam`-nya **0,4–0,6** di seluruh 12 belahan — puncaknya lebar, bukan satu titik
sempit yang kebetulan menang. Itu yang membedakannya dari sapuan 729 konfigurasi
post-processing di sesi sebelumnya, yang parameter terpilihnya berhamburan dan gain
jujurnya +0,0014 dengan menang 1/12."""))

cells.append(md("""---
## 4. Verdikt dan submission"""))

cells.append(co("""o = post_tr(btr + lam*ctr_d); p = post_te(bte + lam*cte_d)
res = dict(lam=lam, lb_real=float(sc(o)), dec=C.part_real(o,True), rnd=C.part_real(o,False),
           gain=float(np.mean(gains)), menang=int(sum(g<0 for g in gains)),
           bias_rnd=C.bias_rnd(o), mean_rnd_te=float(p[C.MT].mean()),
           sd_rnd_te=float(p[C.rnd_te].std()), est_lb=float(sc(o))+0.0082,
           basis="notebook_8 blend + koreksi set-transformer di-demean per subset saat apply")

print("="*66)
print("VERDIKT -- notebook_9")
print("="*66)
print("  lb_real      %.4f   (notebook_8 = 0,1762)" % res["lb_real"])
print("  gain vs nb8  %+.4f  (menang %d/12 belahan)" % (res["gain"], res["menang"]))
print("  dec %.4f  rnd %.4f   (nb8: 0,1437 / 0,2074)" % (res["dec"], res["rnd"]))
print("  --- diagnostik transfer ---")
print("  bias_rnd            %+.3f   nb8 +0,031  -> tidak bergerak       AMAN" % res["bias_rnd"])
print("  mean test bulat<100 %.3f    nb8 5,259, optimum ~5,272          AMAN" % res["mean_rnd_te"])
print("  sd test sisi bulat  %.3f    nb8 0,396  -> naik +0,008           AWAS" % res["sd_rnd_te"])
print("  ESTIMASI LB = lb_real + 0,0082 = %.4f   (sd 0,0028)" % res["est_lb"])
print("  peringkat 1 (Kingpul) 0,1837 -> selisih %+.4f" % (res["est_lb"]-0.1837))
print("="*66)

sub = pd.read_csv("submission/notebook_8.csv")
sub["magnitude"] = np.round(p, 3)
sub.to_csv("submission/notebook_9.csv", index=False)
json.dump(res, open("submission/notebook_9_score.json","w"), indent=2)
np.savez(C.CACHE/"blend_nb9.npz", oof=o, pte=p, lam=lam)
print("tertulis: submission/notebook_9.csv (%d baris)" % len(sub))"""))

cells.append(md("""### Satu diagnostik yang memburuk, dicatat terbuka

`sd` prediksi sisi bulat naik **0,396 -> 0,404**. Kenaikan sd pernah menyertai kerugian LB
di `notebook_5`, jadi ini tidak boleh disembunyikan. Yang membedakan: di nb5 lompatannya
0,424 -> 0,447 (**+0,023**) sementara di sini **+0,008**, dan nb5 satu-satunya submission
yang rugi *tanpa* `bias_rnd` melonjak. Di sini dua diagnostik lain justru sedikit membaik
(`bias_rnd` +0,031 -> +0,029, mean 5,259 -> 5,253).

Risikonya diterima, tapi kalau LB meleset dari 0,1800, **inilah tersangka pertamanya** —
dan jalan mundurnya `lam` 0,30 (`lb_real` 0,1726, sd 0,400).

---

## Yang dipelajari

### 1. Demean di dalam training bukan jaminan

Kalau sebuah koreksi tidak boleh menggeser rata-rata subset, **paksakan di titik
penerapan**, bukan cuma di target training. Model punya cukup fitur untuk merekonstruksi
prior yang dibuang dari label. Ongkos memaksakannya di sini: **0,0004 `lb_real`**.

### 2. Ambang diagnostik harus diturunkan dari kegagalan nyata, bukan dikarang

Notebook Kaggle memakai ambang `bias_rnd > 0,08` dan karenanya melabeli +0,059 sebagai
AMAN. Angka 0,08 itu tidak berasal dari mana-mana. Titik kegagalan nyata yang tercatat di
`LEADERBOARD.md` adalah **+0,056** (nb5) dan +0,076/+0,137 (nb1/nb2), sementara semua
submission yang menang ada di +0,027…+0,047. Ambang yang jujur ada di sekitar **+0,05**.

### 3. \"Kurang dilatih\" terulang untuk ketiga kalinya

Versi demean yang diukur lokal dulu cuma menahan −0,0011, dan hampir membuat ide ini
dibuang. Versi Kaggle — **3 seed, 60 epoch** — menahan **−0,0042** dengan diagnostik yang
sama. Pola persis sama dengan CNN v3 di `notebook_8`: kesimpulan negatif tentang model deep
yang ternyata cuma kesimpulan tentang anggaran training.

### Yang tersisa

`lb_real` 0,1718. Keluarga arsitektur CNN 1D ditutup notebook ini, dua usaha memulihkan
grouping sudah gagal, dan post-processing sudah dikonfirmasi habis. Yang belum pernah
diuji di LB sama sekali: **refit 100% data** untuk prediksi test — sekarang test diprediksi
rata-rata 5 model fold yang masing-masing dilatih 80% data, dan dengan cuma ~905 event
efektif selisihnya lebih berarti dari biasanya. Itu **tidak bisa divalidasi lewat OOF**;
satu-satunya cara tahu adalah submit."""))

nb = {"cells": cells,
      "metadata": {"kernelspec": {"display_name":"Python 3","language":"python","name":"python3"},
                   "language_info": {"name":"python","version":"3.11.6"}},
      "nbformat": 4, "nbformat_minor": 5}
json.dump(nb, open(_path.ROOT/"notebook_9.ipynb", "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("notebook_9.ipynb ditulis,", len(cells), "sel")
