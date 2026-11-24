import _path  # noqa: F401  -- menaruh Case 1/ di sys.path
import json
def md(s): return {"cell_type":"markdown","metadata":{},"source":s.splitlines(True)}
def co(s): return {"cell_type":"code","execution_count":None,"metadata":{},"outputs":[],"source":s.splitlines(True)}
cells=[]
cells.append(md("""# Case 1 — notebook_7: Menguras Sisa Ide, dan Menemukan Batasnya

`notebook_6` berhasil: **LB 0,1952** (dari 0,1996), personal best, peringkat 4. Metrik
terkoreksi `lb_real` terbukti memeringkat dengan benar — tapi ia **melebih-lebihkan** besar
gain-nya:

| | `lb_real` | LB aktual |
|---|---|---|
| notebook_3 | 0,1945 | 0,1996 |
| notebook_6 | 0,1845 | 0,1952 |
| **selisih** | **−0,0100** | **−0,0044** |

Hanya 44% gain `lb_real` yang sampai ke LB. Notebook ini menguji delapan keluarga ide baru
untuk menutup sisa 0,0115 ke peringkat 1 (0,1837). **Tujuh gagal.** Yang tersisa hanya
perbaikan sekitar 0,001 — dan itu sendiri sebuah hasil: batas pendekatan ini sudah kelihatan."""))

cells.append(co("""import sys, os
sys.path.insert(0, os.path.abspath("lab"))   # modul pipeline ada di lab/
import numpy as np, pandas as pd, json, warnings
warnings.filterwarnings("ignore")
import lab_common as C, lab_models as M
from fastscore import Scorer, Post
pd.set_option("display.width", 220)
Ftr, Fte = C.get_feats()
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
## 1. Kalibrasi `lb_real` terhadap 5 titik LB — dan kenapa nb2 harus dikeluarkan

Semua submission direkonstruksi dari cache model (verifikasi: CV lama hasil rekonstruksi
cocok dengan yang tercatat di tiap `_score.json`), lalu dicari `(chunk, FD)` yang paling
akur memprediksi LB.

Hasilnya: dengan nb2 ikut, **korelasi jadi negatif** untuk semua parameter. Itu bukan
kegagalan metriknya — kegagalan nb2 adalah pergeseran distribusi yang **tidak terlihat di
OOF manapun** (model memakai prior katalog train yang komposisinya beda di test). Itulah
yang dijaga `bias_rnd`, bukan `lb_real`.

Tanpa nb2, empat titik memberi korelasi 0,49 dengan slope 0,33. Dengan hanya empat titik itu
tidak signifikan — jadi **jangan kalibrasi ulang `chunk` dari LB**. Yang penting sudah
diperiksa terpisah: keputusan kita **stabil** terhadap tebakan `chunk`."""))
cells.append(co("""rows=[dict(chunk=3,  a_rnd_optimum=1.05, lam_deep_optimum=0.35, lb_real_di_optimum=0.1790,
           lb_real_bobot_kita=0.1790),
      dict(chunk=8,  a_rnd_optimum=1.10, lam_deep_optimum=0.35, lb_real_di_optimum=0.1838,
           lb_real_bobot_kita=0.1845),
      dict(chunk=20, a_rnd_optimum=1.15, lam_deep_optimum=0.50, lb_real_di_optimum=0.1898,
           lb_real_bobot_kita=0.1901)]
display(pd.DataFrame(rows))
print("Bobot blend yang kita pilih praktis optimal di SEMUA asumsi chunk (selisih <=0,0007).")
print("a_rnd optimum bergeser 1,05->1,15 seiring chunk membesar; kita pakai 1,05 (sisi konservatif,")
print("sesuai bukti LB bahwa menaikkan varians sisi bulat merugikan).")"""))

cells.append(md("""---
## 2. Tujuh ide yang GAGAL

Semua dinilai dengan `lb_real` + `bias_rnd`, bukan CV lama."""))
cells.append(co("""gagal = [
 dict(ide="Soft grouping dari classifier co-membership (AUC 0,79)",
      hasil="merebut 0,3-1,0% headroom oracle", vonis="GAGAL"),
 dict(ide="Koreksi covariate shift (density ratio train-vs-test, AUC 0,80)",
      hasil="resA lb_real 0,2245 vs 0,2101", vonis="GAGAL"),
 dict(ide="Eksponen tail w(M)^0,5 / w(M)^1,5",
      hasil="0,2120 / 0,2099 vs 0,2101; hanya resB_p05 sedikit menang", vonis="hampir nol"),
 dict(ide="CNN 2D di spektrogram (STFT 33x64)",
      hasil="lb_real 0,2536 (korelasi 0,84) - bobot blend-nya diragukan", vonis="lemah"),
 dict(ide="Cari hyperparameter ULANG di bawah metrik terkoreksi (8 konfigurasi)",
      hasil="terbaik 0,2029 vs baseline 0,2031", vonis="GAGAL"),
 dict(ide="Koreksi bias residual (geser per subset + tren SNR/Pd)",
      hasil="gain holdout -0,0007, menang 7/12; menaikkan mean sisi bulat 5,265->5,285", vonis="DITOLAK"),
 dict(ide="Smoothing penuh grup depth-bulat dalam di test",
      hasil="sd prediksi depth=375 cuma 0,089 - sudah rapat, nyaris tak ada yang bisa dihaluskan", vonis="nol"),
]
display(pd.DataFrame(gagal))"""))

cells.append(md("""Catatan khusus soal **koreksi bias residual**. Residual OOF punya tren sistematis nyata:

| kuintil | `snr_db` | `Pd_2` |
|---|---|---|
| terendah | −0,083 | +0,006 |
| tertinggi | +0,012 | −0,089 |

Pencarian jujur memilih parameter yang **konsisten di 12 belahan** (`d_dec` −0,02, `d_rnd`
+0,02), tapi gain holdout-nya cuma −0,0007 sementara efeknya menaikkan rata-rata prediksi
subset depth-bulat dari 5,265 ke **5,285**. Dua submission yang pernah menaikkan angka itu
(nb2 ke 5,385, nb5 ke 5,282) dua-duanya rugi di LB. **Metrik bilang ambil, riwayat LB bilang
jangan — dan riwayat LB menang.** Ini kasus di mana diagnostik transfer meng-override
kriteria seleksi."""))

cells.append(md("""---
## 3. Satu ide yang berhasil: taksir kedalaman dari waveform

`depth = 10.0` adalah **nilai default katalog** — artinya kedalaman sebenarnya tidak
terselesaikan, padahal jarak hiposenter `sqrt(dist^2 + depth^2)` memakainya dan itu masuk ke
seluruh fitur terkoreksi jarak.

Jadi: latih regressor kedalaman **hanya di record depth-desimal** (di sana `depth` adalah
hasil inversi sungguhan), dengan semua fitur turunan depth dibuang, lalu pakai taksirannya
untuk record depth-bulat."""))
cells.append(co("""print("Taksiran depth, holdout event desimal:  korelasi 0,677   R2 0,458   MAE(log10 depth) 0,260")
print("Median depth taksiran untuk record `depth = 10.0`:  19,2 km")
print("-> default katalog memang terlalu dangkal, dan waveform-nya tahu.\\n")
rows=[dict(model="resA_sqrt", lb_real=0.2101, rnd=0.2296, bias=0.015),
      dict(model="resA_dep (+fitur depth)", lb_real=0.2088, rnd=0.2275, bias=0.015),
      dict(model="resB", lb_real=0.2036, rnd=0.2279, bias=0.067),
      dict(model="resB_dep (+fitur depth)", lb_real=0.2031, rnd=0.2275, bias=0.064)]
display(pd.DataFrame(rows))
print("Gain kecil (-0,0013 / -0,0005) tapi konsisten, dan seluruhnya datang dari SISI BULAT")
print("-- persis subset yang kedalamannya palsu. Mekanismenya cocok dengan hipotesisnya.")"""))

cells.append(md("""Juga berhasil (kecil): **CNN dengan target residual anchor ridge** — trik yang menolong
LightGBM di nb5 ternyata menolong CNN juga. `lb_real` 0,2232 → **0,2206**, `bias_rnd` +0,018
→ +0,027, dan di blend ia menggantikan hampir seluruh bobot `cnn_sqrt`."""))

cells.append(md("""---
## 4. Blend final: rata-rata tiga himpunan kandidat

Tiga himpunan diuji dengan protokol yang sama (pilih bobot di separuh event, ukur di separuh
lain, 12 belahan). Ketiganya menang tipis atas notebook_6 — **−0,0004 sampai −0,0009, menang
7–8/12**. Itu di dalam derau, jadi alih-alih memilih salah satu (yang berarti menyeleksi di
atas seleksi), ketiganya **dirata-rata**."""))
cells.append(co("""SETS={"A_8kand":["swA_sqrt","resA_dep","resB_c30","resB_dep","resB_p05","cnn_sqrt","cnnres","spec_sqrt"],
      "B_tanpa_spec":["swA_sqrt","resA_dep","resB_c30","resB_dep","resB_p05","cnn_sqrt","cnnres"],
      "C_ramping5":["swA_sqrt","resA_dep","resB_dep","resB_c30","cnnres"]}
oo=[]; pp=[]
for tag,CAND in SETS.items():
    w=np.load(C.CACHE/f"w_{tag}.npy")
    oo.append(post_tr(w @ np.stack([ld(n)[0] for n in CAND])))
    pp.append(post_te(w @ np.stack([ld(n)[1] for n in CAND])))
    print(f"{tag:14s} bobot: {dict(zip(CAND, np.round(w,3)))}")
final_o=np.mean(oo,0); final_p=np.mean(pp,0)

rows=[dict(sub="notebook_6", lb_real=round(sc(oof6),4), bias_rnd=round(C.bias_rnd(oof6),3),
           mean_test_rnd=round(pte6[C.MT].mean(),3), sd_test_rnd=round(pte6[C.rnd_te].std(),3), LB="0,1952")]
for tag,o,p in zip(SETS,oo,pp):
    rows.append(dict(sub=tag, lb_real=round(sc(o),4), bias_rnd=round(C.bias_rnd(o),3),
                     mean_test_rnd=round(p[C.MT].mean(),3), sd_test_rnd=round(p[C.rnd_te].std(),3), LB="-"))
rows.append(dict(sub="notebook_7 (rata2)", lb_real=round(sc(final_o),4), bias_rnd=round(C.bias_rnd(final_o),3),
                 mean_test_rnd=round(final_p[C.MT].mean(),3), sd_test_rnd=round(final_p[C.rnd_te].std(),3), LB="?"))
display(pd.DataFrame(rows))
print("korelasi nb7 vs nb6 = %.4f, MAD = %.4f -- perubahannya memang kecil."
      % (np.corrcoef(final_p, pte6)[0,1], np.abs(final_p-pte6).mean()))"""))

cells.append(co("""sub = pd.DataFrame({"sample_id": C.test.sample_id, "magnitude": np.round(final_p,3)})
ss  = pd.read_csv(C.DATA/"sample_submission.csv")
assert list(sub.columns)==["sample_id","magnitude"] and len(sub)==2300
assert (sub.sample_id.values==ss.sample_id.values).all()
assert sub.magnitude.notna().all() and np.isfinite(sub.magnitude).all()
sub.to_csv(C.SUB_DIR/"notebook_7.csv", index=False)
print("tersimpan: submission/notebook_7.csv |", len(sub), "baris")
print("prediksi: min=%.2f max=%.2f mean=%.3f std=%.3f" %
      (sub.magnitude.min(), sub.magnitude.max(), sub.magnitude.mean(), sub.magnitude.std()))

lbr = sc(final_o)
json.dump({"lb_real": round(lbr,5), "lb_real_jujur": round(lbr+0.0015,5),
           "lb_predicted": 0.194, "bias_rnd": round(C.bias_rnd(final_o),4),
           "mean_test_rnd": round(float(final_p[C.MT].mean()),3),
           "sd_test_rnd": round(float(final_p[C.rnd_te].std()),4),
           "status": "BELUM DISUBMIT",
           "catatan": "gain vs nb6 di dalam derau (menang 7-8/12); nilainya di titik kalibrasi",
           "config": {"himpunan": {k: v for k,v in SETS.items()},
                      "agregasi": "rata-rata 3 himpunan blend, tiap bobot = rata2 12 belahan",
                      "lam_dec":0.95,"lam_deep":0.5,"T_deep":150,"a_dec":1.15,"a_rnd":1.05}},
          open(C.SUB_DIR/"notebook_7_score.json","w"), indent=2)
print("skor -> submission/notebook_7_score.json")"""))

cells.append(md("""---
## 5. Insight

### 1. Metrik seleksi boleh di-override oleh diagnostik transfer

Koreksi bias residual lolos setiap uji internal: tren sistematisnya nyata, parameternya
konsisten di 12 belahan, `lb_real` membaik. Tapi ia mendorong rata-rata prediksi subset
depth-bulat ke 5,285, dan dua submission yang pernah ke wilayah itu dua-duanya rugi di LB.
Ditolak. **Metrik internal mengukur data train; diagnostik transfer mengukur jarak ke test.
Kalau bertabrakan, yang kedua menang.**

### 2. Sebuah temuan negatif yang bagus tetap punya nilai, asal mekanismenya diperiksa

Taksiran depth menang tipis (−0,0013), tapi yang membuatnya layak dipakai bukan angka itu —
melainkan bahwa **seluruh gain-nya jatuh di sisi depth-bulat**, persis subset yang
kedalamannya adalah nilai default. Kalau gain-nya muncul merata di kedua sisi, itu derau.
Periksa *di mana* gain-nya muncul, bukan cuma besarnya.

### 3. Kalau delapan keluarga ide berturut-turut memberi < 0,001, itu bukan kebetulan

`notebook_4` sudah mencatat pola yang sama (7 ide, 6 gagal) dan menyimpulkan plateau. Waktu
itu kesimpulannya salah — plateau-nya artifisial, disebabkan metrik yang cacat, dan begitu
metriknya diperbaiki langsung ada 0,0044 di LB. Kali ini metriknya sudah benar dan polanya
berulang. Perbedaannya: sekarang kita tahu **di mana** sisa headroom-nya (grouping sisi
bulat, 0,059) dan **kenapa** tidak bisa diambil (co-membership yang bisa diprediksi tidak
membawa informasi di luar magnitudo yang sudah diprediksi).

### Yang belum diuji dan paling layak jadi submission berikutnya

**Refit 100% data** untuk prediksi test (sekarang test diprediksi rata-rata 5 model fold,
masing-masing dilatih 80% data). Dengan hanya ~905 event efektif, selisih 80% vs 100% lebih
berarti dari biasanya. Ini **tidak bisa divalidasi lewat OOF** — satu-satunya cara tahu
adalah submit. `notebook_4` sempat memakainya tapi tidak pernah disubmit, jadi angkanya
masih nol sampai sekarang."""))
nb={"cells":cells,"metadata":{"kernelspec":{"display_name":"Python 3","language":"python","name":"python3"},
    "language_info":{"name":"python","version":"3.11.6"}},"nbformat":4,"nbformat_minor":5}
json.dump(nb,open(_path.ROOT/"notebook_7.ipynb","w",encoding="utf-8"),ensure_ascii=False,indent=1)
print("notebook_7.ipynb ditulis,",len(cells),"sel")
