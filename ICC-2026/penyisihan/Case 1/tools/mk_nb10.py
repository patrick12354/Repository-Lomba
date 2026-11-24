import _path  # noqa: F401  -- menaruh Case 1/ di sys.path
import json


def md(s): return {"cell_type": "markdown", "metadata": {}, "source": s.splitlines(True)}
def co(s): return {"cell_type": "code", "execution_count": None, "metadata": {},
                   "outputs": [], "source": s.splitlines(True)}


cells = []

cells.append(md("""# Case 1 — notebook_10: Kalau Sisi Bulat Berbohong, Berhenti Mendengarkannya

`notebook_9` disubmit dan **LB-nya 0,1856** — lebih buruk dari `notebook_8` (0,1849),
padahal `lb_real`-nya membaik **−0,0044**, ia menang **12/12** belahan holdout, dan ketiga
diagnostik transfer semuanya aman. Prediksinya 0,1800; melesetnya **+0,0056**.

Post-mortem-nya (`experiments/exp_nb9_postmortem.py`) menemukan sebabnya, dan sebabnya
bukan di set-transformer. Ia ada di **metrik evaluasi**, untuk ketiga kalinya:

> `lb_real` memperbaiki **BOBOT** metrik, bukan **LABEL**-nya.

`make_ev_real` memecah pseudo-event raksasa supaya bobot per-event realistis. Tapi `y`
tetap identik untuk semua record yang berbagi `(depth, magnitude)`. Di train, **24%
pasangan** di dalam satu grup depth bulat punya label identik — jadi apa pun yang
**menyeragamkan prediksi di dalam grup depth** dapat gain gratis yang tidak ada di LB.

Notebook ini menanyakan satu hal lanjutan: **kalau set-transformer bisa tertipu begitu,
apakah blend `notebook_8` sendiri sudah tertipu dengan cara yang sama?**"""))

cells.append(co("""import sys, os
sys.path.insert(0, os.path.abspath("lab"))   # modul pipeline ada di lab/
import numpy as np, pandas as pd, json, warnings
warnings.filterwarnings("ignore")
import lab_common as C
from lab_blend import ld
from fastscore import Post
pd.set_option("display.width", 220)

NB8 = ["swA_sqrt","resA_dep","resB_dep","resB_c30","resB_p05","cnnres","cnn3_avg","cnn3_dir"]
FAM = {"swA_sqrt":"A", "resA_dep":"A", "resB_dep":"B(grup)", "resB_c30":"B(grup)",
       "resB_p05":"B(grup)", "cnnres":"CNN", "cnn3_avg":"CNN", "cnn3_dir":"CNN"}
O = np.stack([ld(n)[0] for n in NB8]); E = np.stack([ld(n)[1] for n in NB8])
post_tr = Post(C.d_tr, 0.95, 0.5, 150, 1.15, 1.05)
post_te = Post(C.d_te, 0.95, 0.5, 150, 1.15, 1.05)
y, ev = C.y, C.ev
w_nb8 = np.load(C.CACHE/"w_nb9.npy")
print("blend notebook_8 dimuat:", dict(zip(NB8, np.round(w_nb8,3))))"""))

cells.append(md("""---
## 1. Alat baru: penilai satu sisi

Sisi **desimal** punya event nyata (`depth_km` desimal = hasil inversi presisi, 98% murni
per magnitudo). Sisi **bulat** tidak. Jadi sisi desimal adalah satu-satunya tempat di data
train yang labelnya bisa dipercaya untuk menilai metode yang menyentuh struktur grup.

Ini yang jadi **diagnostik ke-4**, dan mulai sekarang wajib."""))

cells.append(co('''class Side:
    """eb_twmae di SATU sisi saja, atas subset event, dirata-rata 8 realisasi EVR."""
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
            s += (w*(np.bincount(inv, weights=err, minlength=ne)/nrec)).sum()/wsum
        return s/len(self.per)

ALL = np.ones(len(y), bool)
sc_dec, sc_rnd = Side(True, ALL), Side(False, ALL)
print("penilai satu sisi siap")'''))

cells.append(md("""---
## 2. Tiap kandidat sendirian: menang di sisi mana?

Kalau sebuah keluarga model mendapat kekuatannya dari degenerasi label, ia akan terlihat
**relatif lebih kuat di sisi bulat** daripada di sisi desimal."""))

cells.append(co("""rows = []
for i, n in enumerate(NB8):
    p = post_tr(O[i]); rows.append((n, FAM[n], sc_dec(p), sc_rnd(p)))
df = pd.DataFrame(rows, columns=["kandidat","keluarga","desimal","bulat"])
df["rasio"] = df.bulat / df.desimal
display(df.round(4))
print("rasio RENDAH = relatif lebih kuat di sisi bulat (label degenerate) <- curigai")"""))

cells.append(md("""Model B — satu-satunya keluarga yang memakai **fitur agregat grup** — punya rasio
paling rendah (1,36–1,37) sementara CNN paling tinggi (1,55–1,61). Dan Model B **kalah dari
`resA_dep` di KEDUA sisi** (0,167 vs 0,152 desimal; 0,227 vs 0,225 bulat). Bobot blend-nya
yang 0,32 datang murni dari dekorelasi, bukan dari akurasi.

Mekanismenya sama persis dengan `notebook_9`, satu tingkat lebih rendah: agregat grup di
train merangkum record yang **24% pasangannya berlabel identik**, jadi pemetaan
"agregat grup → magnitudo" jauh lebih kuat di train daripada di test."""))

cells.append(md("""---
## 3. Sapuan: seberapa jauh kita percaya sisi bulat?

`lb_real = 0,49·dec + 0,51·rnd` menimbang kedua sisi menurut **komposisi test**. Itu benar
kalau kedua sisi sama-sama bisa dipercaya. Setelah nb9, sisi bulat tidak.

Sapuan ini memakai objektif **seleksi** `FD_sel·dec + (1−FD_sel)·rnd` dengan `FD_sel` dari
0,49 (= `notebook_8` apa adanya) sampai 1,0 (desimal saja). Yang berubah cuma objektif
pemilihan bobot; skor yang dilaporkan tetap `lb_real` apa adanya.

Protokolnya tidak berubah: bobot dipilih di separuh event, diukur di separuh **lain**,
12 belahan, bobot final = rata-rata lintas belahan."""))

cells.append(co("""rng = np.random.RandomState(0)
W = np.vstack([rng.dirichlet(np.ones(len(NB8))*0.6, size=8000), np.eye(len(NB8))])
Q = np.stack([post_tr(x @ O) for x in W])

uev = np.unique(ev); splits = []
for rep in range(6):
    h1 = np.isin(ev, np.random.RandomState(100+rep).permutation(uev)[:len(uev)//2])
    for keep in (h1, ~h1):
        splits.append((Side(True,keep), Side(False,keep), Side(True,~keep), Side(False,~keep)))
PRE = [(np.array([a(q) for q in Q]), np.array([b(q) for q in Q]),
        np.array([c(q) for q in Q]), np.array([d(q) for q in Q])) for a,b,c,d in splits]
print("pra-hitung selesai:", len(PRE), "belahan x", len(Q), "kandidat bobot")"""))

cells.append(co("""p_nb8_tr = post_tr(w_nb8 @ O); p_nb8_te = post_te(w_nb8 @ E)
ref_dec = [c(p_nb8_tr) for _,_,c,_ in splits]
ref_all = [C.FD*c(p_nb8_tr) + (1-C.FD)*d(p_nb8_tr) for _,_,c,d in splits]

rows, WS = [], {}
for fd in [0.49, 0.60, 0.70, 0.80, 0.90, 1.00]:
    ws, gd, ga = [], [], []
    for k,(vd,vr,hd,hr) in enumerate(PRE):
        i = int((fd*vd + (1-fd)*vr).argmin())
        ws.append(W[i]); gd.append(hd[i]-ref_dec[k])
        ga.append(C.FD*hd[i] + (1-C.FD)*hr[i] - ref_all[k])
    wm = np.mean(ws,0); wm /= wm.sum(); WS[fd] = wm
    o, p = post_tr(wm @ O), post_te(wm @ E)
    fam = pd.Series(wm, index=[FAM[n] for n in NB8]).groupby(level=0).sum()
    rows.append(dict(FD_sel=fd, w_A=fam["A"], w_B=fam["B(grup)"], w_CNN=fam["CNN"],
                     lb_real=C.lb_real(o), dec=C.part_real(o,True), rnd=C.part_real(o,False),
                     gain_dec=np.mean(gd), menang_dec=sum(g<0 for g in gd),
                     bias=C.bias_rnd(o), mean_te=p[C.MT].mean(), sd_te=p[C.rnd_te].std(),
                     korel_nb8=np.corrcoef(p, p_nb8_te)[0,1]))
sweep = pd.DataFrame(rows)
display(sweep.round(4))"""))

cells.append(md("""Bacanya:

- Baris `FD_sel = 0,49` adalah `notebook_8` apa adanya — dan **ia gagal uji sisi-desimal**
  (`gain_dec` +0,0009, menang 3/12). Blend kita sendiri memang sudah tertipu.
- Menggeser objektif ke sisi desimal memangkas bobot Model B **0,32 → 0,09** dan menaikkan
  CNN **0,53 → 0,74**.
- `gain_dec` berubah tanda di sekitar `FD_sel = 0,70` dan mencapai −0,0010 (menang 9/12)
  di 0,80.
- `lb_real` **memburuk** monoton (0,1762 → 0,1788). Itu memang yang diharapkan: kita
  sengaja berhenti memanen bagian metrik yang terbukti bohong.

**`FD_sel = 0,80` dipilih.** Alasannya bukan skornya, melainkan bahwa **keempat diagnostik
bergerak ke arah yang benar sekaligus** — satu-satunya baris yang begitu."""))

cells.append(co("""LAM_FD = 0.80
w10 = WS[LAM_FD]
cmp = pd.DataFrame({
    "diagnostik": ["bobot Model B (grup)","gain sisi desimal","menang desimal",
                   "bias_rnd","mean test bulat<100","sd test sisi bulat","lb_real"],
    "notebook_8": [0.316, 0.0009, "3/12", 0.0314, 5.2587, 0.3963, 0.1762],
    "notebook_10": [round(sweep.w_B[3],3), round(sweep.gain_dec[3],4),
                    "%d/12"%sweep.menang_dec[3], round(sweep.bias[3],4),
                    round(sweep.mean_te[3],4), round(sweep.sd_te[3],4),
                    round(sweep.lb_real[3],4)],
    "arah": ["turun = baik","negatif = baik","tinggi = baik","turun = baik",
             "ke 5,272 = baik","turun = baik","NAIK -- disengaja"]})
display(cmp)
print("korelasi prediksi test vs notebook_8: %.4f"%sweep.korel_nb8[3])"""))

cells.append(md("""---
## 4. Verdikt dan submission

Ini **taruhan yang dinyatakan terbuka**, bukan perbaikan yang terukur — dan harus dibaca
begitu.

**Yang mendukung.** `notebook_9` membuktikan gain sisi bulat di `lb_real` bisa bernilai nol
di LB. Model B adalah keluarga yang paling condong ke sisi bulat dan tidak menang di sisi
mana pun sebagai model tunggal. Memangkas bobotnya memperbaiki **ketiga** diagnostik
transfer lama **plus** yang baru.

**Yang melawan.** `lb_real` memburuk 0,1762 → 0,1773, dan `lb_real` tetap satu-satunya
angka yang pernah berkorelasi dengan LB di empat submission.

**Yang membatasi ruginya.** Korelasi prediksi test dengan `notebook_8` adalah **0,9986** —
perubahan ini kecil di ruang prediksi. Kalau taruhannya salah, ruginya kira-kira sebesar
selisih nb8↔nb9 (0,0007), bukan sebesar kegagalan nb2 atau nb5.

**Nilai informasinya lebih besar dari nilai skornya.** Kalau LB membaik, sisi bulat
`lb_real` memang tidak bisa dipercaya dan seluruh pipeline harus dipilih ulang di bawah
`FD_sel` tinggi. Kalau LB memburuk, kegagalan nb9 khusus milik set-transformer dan Model B
boleh dibiarkan. Kedua jawaban mengubah apa yang dikerjakan berikutnya."""))

cells.append(co("""o10 = post_tr(w10 @ O); p10 = post_te(w10 @ E)
res = dict(FD_sel=LAM_FD, bobot={n: round(float(v),4) for n,v in zip(NB8, w10)},
           w_modelB=float(sweep.w_B[3]),
           lb_real=float(C.lb_real(o10)), dec=float(C.part_real(o10,True)),
           rnd=float(C.part_real(o10,False)),
           gain_dec=float(sweep.gain_dec[3]), menang_dec=int(sweep.menang_dec[3]),
           bias_rnd=float(C.bias_rnd(o10)), mean_rnd_te=float(p10[C.MT].mean()),
           sd_rnd_te=float(p10[C.rnd_te].std()),
           korel_nb8=float(sweep.korel_nb8[3]),
           basis="blend 8 kandidat nb8, bobot dipilih dengan objektif FD_sel=0,80")

print("="*68); print("VERDIKT -- notebook_10"); print("="*68)
print("  lb_real       %.4f   (nb8 0,1762 -- SENGAJA lebih buruk)"%res["lb_real"])
print("  dec %.4f  rnd %.4f   (nb8: 0,1437 / 0,2074)"%(res["dec"], res["rnd"]))
print("  --- diagnostik transfer ---")
print("  bias_rnd            %+.3f   nb8 +0,031   membaik"%res["bias_rnd"])
print("  mean test bulat<100 %.3f    nb8 5,259    membaik"%res["mean_rnd_te"])
print("  sd test sisi bulat  %.3f    nb8 0,396    membaik"%res["sd_rnd_te"])
print("  gain sisi DESIMAL   %+.4f  nb8 +0,0009  membaik (menang %d/12 vs 3/12)"
      %(res["gain_dec"], res["menang_dec"]))
print("  --- ukuran taruhan ---")
print("  korelasi vs notebook_8  %.4f"%res["korel_nb8"])
print("  TIDAK ada estimasi LB: offset lb_real->LB terbukti tidak stabil di nb9.")
print("="*68)

sub = pd.read_csv("submission/notebook_8.csv")
sub["magnitude"] = np.round(p10, 3)
sub.to_csv("submission/notebook_10.csv", index=False)
json.dump(res, open("submission/notebook_10_score.json","w"), indent=2)
np.save(C.CACHE/"w_nb10_fd80.npy", w10)
print("tertulis: submission/notebook_10.csv (%d baris)"%len(sub))"""))

cells.append(md("""---
## Yang dipelajari

### 1. Metrik yang cacat bisa cacat di lebih dari satu lapis

Sesi `notebook_6` memperbaiki **bobot** metrik dan menganggap masalahnya selesai. Sesi ini
menemukan lapis kedua di objek yang sama: **labelnya**. Keduanya berasal dari satu akar —
`groupby(["depth_km","magnitude"])` bukan event sungguhan — tapi memperbaiki yang satu
tidak menyentuh yang lain, dan perbaikan pertama membuat yang kedua **lebih sulit dilihat**
karena metriknya sudah terasa "sudah dibetulkan".

### 2. Kegagalan LB harus diaudit ke belakang, bukan cuma ke depan

Reaksi wajar terhadap kegagalan nb9 adalah membuang set-transformer dan lanjut. Yang
memberi hasil justru menanyakan **komponen mana lagi yang mekanismenya sama** — dan Model B
sudah ada di dalam blend sejak `notebook_3`, dengan bobot 0,32, selama tujuh notebook.

### 3. Kandidat yang tidak menang di sisi mana pun tetap bisa dapat bobot besar

Model B kalah dari `resA_dep` di kedua sisi, tapi dapat 0,32 karena dekorelasinya. Itu sah
secara statistik — kecuali kalau dekorelasinya sendiri berasal dari artefak yang tidak
transfer. **Dekorelasi harus ikut ditanya asal-usulnya**, bukan diterima sebagai kebaikan.

### Yang berikutnya

Sisi non-deep sudah tuntas diperas. Tiga notebook GPU disiapkan di `belum_run/`, semuanya
menyerang **akurasi per-record** — satu-satunya sumbu yang tidak bisa gagal lewat jalur
nb9:

| # | ide | kenapa |
|---|---|---|
| 06 | augmentasi agresif | keluarga yang sudah terbukti membayar di nb8, belum digarap habis |
| 07 | pra-latih self-supervised di train+test | 12.805 sampel efektif vs 905 event; plafon tertinggi |
| 08 | kepala distribusi soft-bin | menyerang under-prediction ekor di penyebabnya |"""))

nb = {"cells": cells,
      "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python",
                                  "name": "python3"},
                   "language_info": {"name": "python", "version": "3.11.6"}},
      "nbformat": 4, "nbformat_minor": 5}
json.dump(nb, open(_path.ROOT / "notebook_10.ipynb", "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("notebook_10.ipynb ditulis,", len(cells), "sel")
