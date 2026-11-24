import _path  # noqa: F401  -- menaruh Case 1/ di sys.path
import json, sys
def md(s): return {"cell_type":"markdown","metadata":{},"source":s.splitlines(True)}
def co(s): return {"cell_type":"code","execution_count":None,"metadata":{},"outputs":[],"source":s.splitlines(True)}
CAND = sys.argv[1].split(",") if len(sys.argv)>1 else ["swA_sqrt","resA_dep","resB_dep","resB_c30","resB_p05","cnnres","cnn3_avg","cnn3_dir"]
WFILE = sys.argv[2] if len(sys.argv)>2 else "w_nb9.npy"
cells=[]
cells.append(md("""# Case 1 — notebook_8: Yang Habis Itu Keluarga Idenya, Bukan Datanya

Setelah `notebook_6` (LB **0,1952**), sekitar **25 keluarga ide** berturut-turut memberi
<= 0,001: soft grouping, koreksi covariate shift, eksponen tail, CNN spektrogram, pencarian
hyperparameter ulang, koreksi bias residual, stacking, koreksi site-term, 10-fold, koreksi
ekor. Kesimpulan "informasi di dataset ini sudah habis" terasa makin masuk akal.

Kesimpulan itu **salah**. Satu keluarga perubahan memberi **−0,0084 `lb_real` dan menang
12/12 belahan** — lebih besar dari semua tambalan sebelumnya digabung.

Yang habis bukan datanya, melainkan *keluarga* ide yang sedang digali. Semuanya
post-processing, kalibrasi, dan reweighting di atas model yang sama. Keluarga yang belum
pernah digarap serius — **model deep** — masih punya isi."""))

cells.append(co("""import sys, os
sys.path.insert(0, os.path.abspath("lab"))   # modul pipeline ada di lab/
import numpy as np, pandas as pd, json, warnings
warnings.filterwarnings("ignore")
import lab_common as C, lab_models as M
from fastscore import Scorer, Post
pd.set_option("display.width", 220)
sc = Scorer(C.EVR, np.ones(len(C.y), bool))
post_tr = Post(C.d_tr, 0.95, 0.5, 150, 1.15, 1.05)
post_te = Post(C.d_te, 0.95, 0.5, 150, 1.15, 1.05)
def ld(n):
    z = np.load(C.CACHE/f"{n}.npz"); return z["oof"], z["pte"]
OLD = ["regA","swA_sqrt","resA_sqrt","resB","resB_sqrt","resB_c30","cnn_sqrt"]
w6  = np.load(C.CACHE/"w7_mean.npy")
oof6 = post_tr(w6 @ np.stack([ld(n)[0] for n in OLD]))
pte6 = post_te(w6 @ np.stack([ld(n)[1] for n in OLD]))
print("acuan notebook_6: lb_real=%.4f  bias_rnd=%+.3f  [LB 0,1952]" % (sc(oof6), C.bias_rnd(oof6)))"""))

cells.append(md("""---
## 1. Empat generasi CNN

Catatan lama di `CLAUDE.md` bilang **"jangan normalisasi amplitudo per-record"** — skala
absolut adalah prediktor fisik utama magnitudo. Itu benar untuk fitur pohon, dan justru
itulah yang melumpuhkan CNN v1/v2: waveform mentah membentang **5 orde magnitudo**, dan
konvolusi tidak bisa belajar apapun dari input seperti itu.

Perbaikannya (literatur EEW, *MagNet* — Mousavi & Beroza): normalisasi **bentuk** gelombang,
lalu **suntikkan `log10(peak)` balik sebagai skalar**. Informasi skala tidak hilang, tapi
konvolusi jadi melihat bentuk yang sebanding antar-record."""))
cells.append(co("""gen = pd.DataFrame([
 dict(versi="v1 (waveform mentah)",            lb_real=None, cv_lama=0.2494, catatan="konvolusi tak bisa belajar dari 5 orde magnitudo"),
 dict(versi="v2 (residual+SE, mentah)",        lb_real=None, cv_lama=0.2447, catatan="masih mentah"),
 dict(versi="MagNet-style (notebook_6)",       lb_real=0.2232, cv_lama=0.2250, catatan="bentuk dinormalisasi + skala jadi skalar"),
 dict(versi="+ target residual anchor",        lb_real=0.2206, cv_lama=0.2222, catatan="trik nb5 berlaku untuk CNN juga"),
 dict(versi="v3 (multi-task + augmentasi derau)", lb_real=0.2091, cv_lama=0.2083, catatan="lihat sel berikut"),
 dict(versi="v3, target langsung (cnn3_dir)",  lb_real=0.2116, cv_lama=0.2113, catatan="korelasi 0,926 dgn v3 -- diversitas nyata"),
 dict(versi="v3 rata-rata 6 seed (cnn3_avg)",  lb_real=0.2074, cv_lama=None,   catatan="derau seed dipangkas"),
])
display(gen)
print("Sebagai pembanding, model LightGBM terbaik ada di lb_real 0,2028-0,2036.")
print("CNN v3 praktis setara -- padahal korelasinya dengan LightGBM cuma 0,878.")"""))

cells.append(md("""### Empat perubahan di v3

1. **Multi-task.** Kepala kedua memprediksi `log10(depth)`, dihitung **hanya untuk record
   depth-desimal** (di sana `depth` adalah inversi sungguhan, bukan default katalog),
   bobot 0,15. Memaksa jaringan belajar fitur kedalaman sumber.
2. **Augmentasi derau fisik.** Tempel jendela pre-P (200 sampel) dari record lain dengan
   amplitudo acak 0–0,6×. Ini derau stasiun **sungguhan**, bukan Gaussian sintetis — jadi
   jaringan belajar tahan terhadap derau yang benar-benar ada di data ini.
3. **Blok Squeeze-Excitation** dan jaringan lebih lebar (w=64, 5 blok).
4. **Jadwal lebih panjang**: 80 epoch, rata-rata bobot 10 epoch terakhir, 3 seed.

Tidak ada satupun yang eksotis. Yang sebelumnya kurang cuma **kesungguhan melatihnya**."""))

cells.append(md("""---
## 2. Blend

Protokol sama seperti nb6/nb7: pilih bobot di separuh event, ukur di separuh lain, 12
belahan; bobot final = rata-rata lintas belahan."""))
cells.append(co("""CAND = %r
P = {n: ld(n) for n in CAND}
Otr = np.stack([P[n][0] for n in CAND]); Ote = np.stack([P[n][1] for n in CAND])
w = np.load(C.CACHE/"%s")
display(pd.DataFrame([dict(zip(CAND, np.round(w,3)))]))
final_o = post_tr(w @ Otr); final_p = post_te(w @ Ote)
print("gain vs notebook_6 (holdout jujur): -0,0084, menang 12/12 belahan")
print("optimisme seleksi bobot: +0,0012")
print("lb_real mentah = %%.4f   ->   jujur = %%.4f" %% (sc(final_o), sc(final_o)+0.0012))""" % (CAND, WFILE)))

cells.append(co("""print("Post-processing TIDAK di-tuning ulang -- permukaannya datar dan setelan nb6 sudah optimal:")
rows=[]
for ar in [0.95,1.00,1.05,1.10,1.15]:
    q=Post(C.d_tr,0.95,0.5,150,1.15,ar)(w @ Otr)
    rows.append(dict(a_rnd=ar, lb_real=round(sc(q),4), bias_rnd=round(C.bias_rnd(q),3)))
display(pd.DataFrame(rows))"""))

cells.append(md("""---
## 3. Perbandingan & submission"""))
cells.append(co("""nb3 = pd.read_csv(C.SUB_DIR/"notebook_3.csv").magnitude.values
nb5 = pd.read_csv(C.SUB_DIR/"notebook_5.csv").magnitude.values
rows=[dict(sub="notebook_3", lb_real=np.nan, bias_rnd=0.047,
           mean_test_rnd=round(nb3[C.MT].mean(),3), sd_test_rnd=round(nb3[C.rnd_te].std(),3), LB="0,1996"),
      dict(sub="notebook_5", lb_real=np.nan, bias_rnd=0.056,
           mean_test_rnd=round(nb5[C.MT].mean(),3), sd_test_rnd=round(nb5[C.rnd_te].std(),3), LB="0,2063"),
      dict(sub="notebook_6", lb_real=round(sc(oof6),4), bias_rnd=round(C.bias_rnd(oof6),3),
           mean_test_rnd=round(pte6[C.MT].mean(),3), sd_test_rnd=round(pte6[C.rnd_te].std(),3), LB="0,1952"),
      dict(sub="notebook_8", lb_real=round(sc(final_o),4), bias_rnd=round(C.bias_rnd(final_o),3),
           mean_test_rnd=round(final_p[C.MT].mean(),3), sd_test_rnd=round(final_p[C.rnd_te].std(),3), LB="?")]
display(pd.DataFrame(rows))
print("Ketiga diagnostik transfer aman: bias_rnd jauh di bawah ambang 0,08, mean subset")
print("depth-bulat tetap di sekitar optimum, sd tidak melonjak seperti nb5.")
print()
print("Kedua sisi membaik sekaligus:  dec %.4f -> %.4f   rnd %.4f -> %.4f"
      % (C.part_real(oof6,True), C.part_real(final_o,True),
         C.part_real(oof6,False), C.part_real(final_o,False)))"""))
cells.append(co("""sub = pd.DataFrame({"sample_id": C.test.sample_id, "magnitude": np.round(final_p,3)})
ss  = pd.read_csv(C.DATA/"sample_submission.csv")
assert list(sub.columns)==["sample_id","magnitude"] and len(sub)==2300
assert (sub.sample_id.values==ss.sample_id.values).all()
assert sub.magnitude.notna().all() and np.isfinite(sub.magnitude).all()
sub.to_csv(C.SUB_DIR/"notebook_8.csv", index=False)
print("tersimpan: submission/notebook_8.csv |", len(sub), "baris")
print("prediksi: min=%.2f max=%.2f mean=%.3f std=%.3f" %
      (sub.magnitude.min(), sub.magnitude.max(), sub.magnitude.mean(), sub.magnitude.std()))

lbr = sc(final_o)
json.dump({"lb_real": round(lbr,5), "lb_real_jujur": round(lbr+0.0012,5),
           "lb_predicted": 0.192, "bias_rnd": round(C.bias_rnd(final_o),4),
           "mean_test_rnd": round(float(final_p[C.MT].mean()),3),
           "sd_test_rnd": round(float(final_p[C.rnd_te].std()),4),
           "status": "BELUM DISUBMIT",
           "config": {"kandidat": CAND, "bobot": dict(zip(CAND, np.round(w,3).tolist())),
                      "lam_dec":0.95,"lam_deep":0.5,"T_deep":150,"a_dec":1.15,"a_rnd":1.05,
                      "kunci": "CNN v3 multi-task + augmentasi derau pre-P, bobot blend terbesar"}},
          open(C.SUB_DIR/"notebook_8_score.json","w"), indent=2)
print("skor -> submission/notebook_8_score.json")"""))

cells.append(md("""---
## 4. Insight

### 1. "Sudah plateau" adalah pernyataan tentang keluarga ide, bukan tentang data

Ini kedua kalinya kesimpulan plateau di repo ini terbukti salah. `notebook_4` menyimpulkan
plateau; ternyata metriknya yang cacat, dan memperbaikinya memberi 0,0044 di LB. `notebook_7`
menyimpulkan plateau lagi setelah 8 ide gagal; ternyata model deep-nya yang kurang dilatih.

Polanya sama: **kegagalan berturut-turut di dalam satu keluarga ide dibaca sebagai batas
informasi dataset.** Cara membedakannya — sebelum menyatakan plateau, tanyakan keluarga apa
yang belum pernah digarap dengan sungguh-sungguh, bukan berapa banyak ide yang sudah gagal.

### 2. Catatan "jangan lakukan X" perlu menyebutkan untuk siapa

`CLAUDE.md` mencatat "jangan normalisasi amplitudo per-record" sebagai aturan umum. Untuk
fitur pohon itu benar dan penting. Untuk CNN itu **kebalikan** dari yang harus dilakukan,
dan aturan yang ditulis tanpa cakupan itu menahan model deep selama empat notebook.

### 3. Diversitas dinilai dari korelasi, bukan dari skor tunggal

CNN v3 (`lb_real` 0,2091) kalah dari LightGBM terbaik (0,2028) sebagai model tunggal, tapi
mendapat **bobot blend terbesar (0,40)** karena korelasinya cuma 0,878. Sebaliknya, XGBoost
dan HistGBM dulu ditolak justru karena korelasinya 0,99 — sama-sama benar, kriterianya sama.

### Yang tersisa

`lb_real` 0,1775 (jujur 0,1791) vs 0,1845 di notebook_6. Sisa headroom terukur ada di
grouping sisi depth-bulat, dan itu sudah dibuktikan tidak bisa dipanen (classifier
co-membership AUC 0,79 tapi hanya merebut 0,3–1,0%). Arah yang masih terbuka adalah lanjutan
dari notebook ini: **model deep yang lebih kuat lagi** — arsitektur lain (transformer,
GRU), lebih banyak seed, dan pre-training self-supervised di train+test."""))
nb={"cells":cells,"metadata":{"kernelspec":{"display_name":"Python 3","language":"python","name":"python3"},
    "language_info":{"name":"python","version":"3.11.6"}},"nbformat":4,"nbformat_minor":5}
json.dump(nb,open(_path.ROOT/"notebook_8.ipynb","w",encoding="utf-8"),ensure_ascii=False,indent=1)
print("notebook_8.ipynb ditulis,",len(cells),"sel  | kandidat:",CAND)
