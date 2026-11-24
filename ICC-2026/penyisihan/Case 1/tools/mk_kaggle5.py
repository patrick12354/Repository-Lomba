# -*- coding: utf-8 -*-
"""Generator batch Kaggle ke-4 — pseudo-labeling test, satu-satunya sumbu yang tersisa.

## Kenapa ini, dan kenapa ini BUKAN ide daur ulang

Setelah batch 1-3, hampir semuanya tertutup: arsitektur CNN baru (7 dari 8 gagal),
grouping (2 usaha), post-processing (menang 1/12), input gabungan (nb10, `bias_rnd`
+0,115), TTA + bobot clipped (UJI 2, menang 6/12), dan bobot blend nb8 (nb9 dan nb10
dua-duanya merugi di LB).

Pseudo-labeling **tidak ada di daftar mana pun.** `experiments/exp34_pseudo.py` cuma
pernah menghitung label-nya (`cache/pseudo_te.npy`) lalu berhenti — trainingnya butuh GPU
dan tidak pernah dijalankan. Nol vonis tercatat di `CLAUDE.md`.

Mekanismenya spesifik untuk case ini, bukan "coba trik populer":

    proporsi depth-bulat   32% di train   vs   51% di test

Setiap model di repo ini dilatih pada komposisi yang salah. Menambahkan record test
berlabel-semu menggeser distribusi training ke arah test, **dan** memberi CNN akses ke
grup depth sisi test yang sebenarnya — bukan cuma bobot yang digeser.

**Beda dari koreksi density-ratio nb7 yang gagal:** itu memberi bobot lebih pada record
train yang sudah ada (`lb_real` resA 0,2245 vs 0,2101 — arahnya salah). Ini menambah
record baru dari distribusi target. Reweighting tidak bisa menciptakan record depth-bulat
yang belum ada; PL bisa.

**Beda dari pra-latih SSL yang gagal (nb07):** SSL memakai waveform test **tanpa label**
untuk belajar representasi, dan hasilnya 0,2112 vs 0,2074 — hipotesis "kurang data" mati.
PL memakai waveform test **dengan target**, jadi yang ditambah bukan data mentah melainkan
sinyal supervisi pada komposisi yang benar. Kegagalan SSL tidak memvonis ini.

## Jebakan yang HARUS ditutup, dan ini yang membuat notebook-nya mahal

Kalau record test ikut dilatih dengan pseudo-label dari blend nb8, model akan mencocokkan
record itu — jadi **prediksi test-nya runtuh ke arah nb8**, sementara OOF (train) tetap
terlihat beragam. Pencarian bobot blend membaca diversitas dari OOF, lalu menerapkannya
pada prediksi test yang diam-diam sudah kolaps. Itu kerusakan senyap: tidak ada diagnostik
yang ada sekarang bisa menangkapnya.

Penutupnya: **test dibelah dua menurut `depth_km`** (supaya record satu event tidak
terpisah), dan tiap fold melatih DUA model —

    model 1: train[ti] + test[belahan 0 berlabel-semu]  ->  memprediksi test[belahan 1]
    model 2: train[ti] + test[belahan 1 berlabel-semu]  ->  memprediksi test[belahan 0]

Tidak ada record test yang pernah diprediksi oleh model yang melihat label-semunya
sendiri. Ongkosnya 2x, dan itu sebabnya arm PL makan ~170 menit.

## Tiga arm

| arm | isi | waktu (T4) |
|---|---|---|
| A | KONTROL — resep `cnn3` apa adanya, tanpa PL | ~85 mnt |
| B | + pseudo-label, `PL_W = 1,0` | ~170 mnt |

Arm A wajib: ia pembanding se-lingkungan untuk protokol UJI 2 (`tools/serap_nb12.py`),
sekaligus penjawab gap lingkungan 0,0049 yang masih terbuka. Tanpa arm A, verdikt blend
akan mengadu kandidat Kaggle melawan kandidat lokal — kesalahan yang sudah memakan
notebook 09.

Jalankan:  python "Case 1/tools/mk_kaggle5.py"
"""
import _path  # noqa: F401
import json
import mk_kaggle as K

OUT = _path.ROOT / "belum_run"
OUT.mkdir(exist_ok=True)

md, co, nb = K.md, K.co, K.nb


HEAD5 = """
---

## Kenapa pseudo-labeling, setelah tiga batch gagal

Sumbu yang sudah tertutup dengan bukti:

| sumbu | vonis |
|---|---|
| arsitektur CNN 1D baru | 7 dari 8 notebook gagal, korelasi 0,89–0,97 vs CNN v3 |
| grouping / co-membership | 2 usaha independen, panen 0,3–1,0% headroom |
| post-processing / kalibrasi / koreksi ekor | menang 1/12; koreksi ekor terbukti terbalik arah |
| 196 fitur masuk ke dalam CNN | nb10: `bias_rnd` +0,115, menang 0/12 |
| TTA + bobot record clipped | UJI 2: gain +0,00029, menang 6/12 |
| menggeser bobot blend nb8 | nb9 dan nb10 dua-duanya rugi di LB |

**Pseudo-labeling tidak ada di daftar itu.** `experiments/exp34_pseudo.py` berhenti setelah
menghitung labelnya; trainingnya tidak pernah dijalankan.

### Mekanismenya, dalam satu angka

```
proporsi record depth-bulat:   32% di TRAIN   vs   51% di TEST
```

Semua model di repo ini dilatih pada komposisi yang salah, dan sisi depth-bulat adalah
tempat **seluruh** headroom yang tersisa (dec 0,1437 sudah melewati oracle-nya; rnd 0,2074).
Pseudo-label menambah 2.300 record dari distribusi yang benar — 22% tambahan, dan
proporsinya condong persis ke sisi yang kurang terwakili.

### Kenapa dua kegagalan yang mirip TIDAK memvonis ini

**Density-ratio nb7 (gagal, `lb_real` 0,2245 vs 0,2101).** Itu memberi bobot lebih besar ke
record train yang sudah ada. Reweighting tidak bisa menciptakan record depth-bulat yang
tidak ada di train; ia cuma memperbesar suara record yang sama. PL menambah record baru.

**Pra-latih SSL nb07 (gagal, 0,2112 vs 0,2074).** Itu memakai waveform test **tanpa label**
— hipotesis "kurang data mentah" dan hipotesis itu memang mati. PL menambah **sinyal
supervisi** pada komposisi target, bukan data mentah. Pertanyaannya berbeda.

## Jebakan senyap yang ditutup notebook ini

Kalau record test dilatih dengan pseudo-label dari blend nb8, model mencocokkan record itu,
jadi **prediksi test-nya runtuh ke arah nb8** — sementara OOF (train) tetap terlihat
beragam. Pencarian bobot membaca diversitas dari OOF lalu menerapkannya ke prediksi test
yang sudah kolaps. **Tidak satu pun diagnostik yang ada sekarang bisa menangkap itu.**

Penutupnya: test dibelah dua menurut `depth_km` (record satu event tidak terpisah), dan
tiap fold melatih dua model bersilang —

```
model 1: train[ti] + test[belahan 0 berlabel-semu]  ->  memprediksi test[belahan 1]
model 2: train[ti] + test[belahan 1 berlabel-semu]  ->  memprediksi test[belahan 0]
```

Tidak ada record test yang diprediksi oleh model yang pernah melihat label-semunya sendiri.
Ongkosnya 2x training, dan itu memang dibayar.

**Diagnostik penentu untuk jebakan ini** (dicetak di sel 5): korelasi `pte` kandidat baru
terhadap `pte` blend nb8. Kalau ia melonjak jauh di atas korelasi `oof`-nya, kolapsnya
terjadi dan verdikt blend tidak sah — berapa pun bagus `lb_real`-nya.

## Arm A adalah KONTROL, dan itu wajib

Resepnya identik `cnn3`, jadi `lb_real` di K=1 harus mendarat di **0,1898**
(angka **SETELAH** `post_tr`; `lb_real` mentahnya 0,2091 — jangan tertukar, itu yang
merusak verdikt notebook 09).

Arm A menjawab dua hal sekaligus:

1. **Pembanding se-lingkungan.** Verdikt blend nb09 mengadu kandidat Kaggle melawan
   8 kandidat lokal, dan gap lingkungan 0,0049 masuk sebagai kerugian ide. Dengan arm A
   di slot CNN, kandidat dan pembanding sama-sama dari Kaggle.
2. **Gap lingkungan itu sendiri**, yang sampai sekarang belum dijelaskan: korelasi OOF
   resep identik cuma 0,9722, padahal antar-paket 3-seed lokal 0,9875. Sel Setup sekarang
   mencetak **sidik jari input** (jumlah |.| Wtr/Str/Wte/Ste/A_BASE) terhadap acuan lokal.
   Kalau cocok, inputnya identik dan selisihnya lahir di training; kalau tidak, sebaliknya.

## Yang harus diabaikan di notebook ini

Baris **"gain sisi desimal"** dicetak sebagai informasi, **bukan kriteria seleksi**. Aturan
lama "gain sisi desimal harus negatif" sudah DICABUT — `notebook_10` dibangun untuk
memaksimalkannya dan LB-nya rugi 0,0022.

## Kalibrasi sebelum bersemangat

LB publik cuma 30% data test; sd selisih dua submission berbeda **0,0038**. LB terbaik
0,1849, peringkat 1 0,1835 — selisih 0,0014 = **0,4 sigma**. Target LB 0,1800 menuntut
`lb_real` **0,1714**, yaitu **−0,0048** dari 0,1762. Belum ada satu ide pun setelah nb8
yang tembus segitu. Dan **hanya ada satu submission final** — tidak ada lindung nilai.
"""


PL_SRC = '''# ---------------------------------------------------------------------------------
# Pseudo-label: prediksi test dari blend notebook_8, sudah lewat post_te.
#
# Ini SATU-SATUNYA sumber label untuk record test. Kualitasnya = kualitas nb8
# (lb_real 0,1762 / LB 0,1849), jadi PL tidak bisa mengajarkan sesuatu yang nb8 tidak
# tahu -- yang ia ubah adalah KOMPOSISI data training, bukan isi pengetahuannya.
# ---------------------------------------------------------------------------------
assert REF is not None, "nb8_ref.npz wajib ada: pseudo-label dihitung dari blend nb8."
_Oref, _Eref = ref_stack()
PL = post_te(REF["__w__"] @ _Eref)
print("pseudo-label test: mean %.3f  sd %.3f  (train y: mean %.3f sd %.3f)"
      %(PL.mean(), PL.std(), y.mean(), y.std()))
print("proporsi depth-bulat (per record): train %.1f%%  test %.1f%%  -> gabungan %.1f%%"
      %(100*rnd_tr.mean(), 100*rnd_te.mean(),
        100*(rnd_tr.sum()+rnd_te.sum())/(len(y)+len(PL))))

# Bobot sampel untuk record test, dibangun MENIRU konstruksi train: w(M)/cnt, dengan
# cnt = ukuran grup (depth, magnitudo). Magnitudo test tidak diketahui, jadi dipakai
# pseudo-label yang dibulatkan ke grid 0,1 -- magnitudo katalog memang diskrit.
_plb = np.round(PL, 1)
_gte = pd.DataFrame({"d": d_te, "m": _plb}).groupby(["d", "m"]).ngroup().values
_cte = pd.Series(_gte).map(pd.Series(_gte).value_counts()).values
SW_PL = mag_weight(PL) / _cte
print("bobot PL: mean %.4f vs bobot train mean %.4f  (rasio %.2f)"
      %(SW_PL.mean(), SW.mean(), SW_PL.mean()/SW.mean()))

# Yang benar-benar dilihat loss adalah proporsi BERBOBOT, bukan per record -- loss-nya
# weighted L1. Ini angka yang menentukan seberapa besar mekanisme "geser komposisi"
# sebenarnya bekerja; kalau kecil, gain apa pun yang muncul bukan dari mekanisme ini.
_wr_tr = SW[rnd_tr].sum()/SW.sum()
_wr_all = (SW[rnd_tr].sum()+SW_PL[rnd_te].sum())/(SW.sum()+SW_PL.sum())
print("proporsi depth-bulat (BERBOBOT, yang dilihat loss): train %.1f%% -> +PL %.1f%%"
      %(100*_wr_tr, 100*_wr_all))
print("  porsi bobot total yang dipegang record PL: %.1f%%"
      %(100*SW_PL.sum()/(SW.sum()+SW_PL.sum())))

# Belahan test untuk mencegah kebocoran label-semu ke dirinya sendiri.
#
# Dibelah menurut depth_km supaya record dari satu gempa tidak terpisah -- kalau terpisah,
# model yang melihat setengah gempa akan "mengenali" setengah lainnya lewat grup depth.
#
# TAPI membelah nilai depth 50:50 menghasilkan 1633 vs 667 record, karena depth = 10,0
# sendirian memuat ~745 record. Itu cacat: kedua model jadi punya paparan label-semu yang
# sangat berbeda, sehingga separuh prediksi test dihasilkan model ber-PL kuat dan separuh
# lagi model ber-PL lemah. Jadi nilai depth dialokasikan GREEDY menurut jumlah record:
# yang terbesar duluan, selalu ke belahan yang saat itu lebih kosong.
_cnt_d = pd.Series(d_te).value_counts()
_half = {}; _tot = [0, 0]
for _d, _n in _cnt_d.items():
    _s = 0 if _tot[0] <= _tot[1] else 1
    _half[_d] = _s; _tot[_s] += _n
PL_HALF = pd.Series(d_te).map(_half).values.astype(int)
print("belahan test: %d vs %d record  (%d vs %d nilai depth)"
      %((PL_HALF==0).sum(), (PL_HALF==1).sum(),
        (np.array(list(_half.values()))==0).sum(), (np.array(list(_half.values()))==1).sum()))
assert pd.DataFrame({"d": d_te, "h": PL_HALF}).groupby("d").h.nunique().max() == 1, \\
    "belahan memecah grup depth -- record satu gempa tidak boleh terpisah"


def run_pl(Wtr, Str, Wte, Ste, sw, pl=None, pl_w=1.0, seeds=(0,1,2), epochs=80,
           bs=128, lr=2.5e-3, avg_last=10, tag=""):
    """`Net3` + loop training notebook_8 PERSIS. Satu-satunya perubahan: kalau `pl`
    diberikan, record test berlabel-semu ikut masuk ke himpunan training tiap fold.

    `pl=None`   -> arm A, kontrol. Harus mereproduksi cnn3 (post: 0,1898).
    `pl=PL`     -> arm B. Tiap fold melatih DUA model bersilang atas belahan test,
                   supaya tidak ada record test yang diprediksi model yang melihat
                   label-semunya sendiri.

    Anchor ridge SELALU difit di record train saja. Kalau anchor ikut berubah, gain/rugi
    tidak bisa dipisahkan antara "CNN belajar lain" dan "baseline linearnya bergeser" --
    pelajaran dari run B notebook 09."""
    Xa = Ftr[A_BASE].values.astype(np.float64); Xa_te = Fte[A_BASE].values.astype(np.float64)
    dep_t = np.log10(d_tr+1).astype(np.float32); dep_ok = (~rnd_tr).astype(np.float32)
    dep_t_te = np.log10(d_te+1).astype(np.float32); dep_ok_te = (~rnd_te).astype(np.float32)
    oof = np.zeros(len(y)); pte = np.zeros(len(Wte))
    Xte_t = torch.tensor(Wte).to(DEV); Ste_t = torch.tensor(Ste).to(DEV)
    # kalau pakai PL, tiap fold melatih 2 model -> pembagi prediksi OOF ikut 2x
    n_arm = 1 if pl is None else 2
    nf = 0; ntot = 5*len(seeds)*n_arm; t0 = time.time()

    for seed in seeds:
        torch.manual_seed(seed); np.random.seed(seed)
        for ti, vi in GroupKFold(5).split(Wtr, y, ev):
            rg = Ridge(alpha=1.0).fit(Xa[ti], y[ti], sample_weight=sw[ti])
            tgt = (y - rg.predict(Xa)).astype(np.float32)
            off_v = rg.predict(Xa[vi]); off_t = rg.predict(Xa_te)
            tgt_te = (pl - off_t).astype(np.float32) if pl is not None else None

            for arm in range(n_arm):
                if pl is None:
                    idx_te = np.zeros(0, dtype=int)       # tidak ada record test di training
                    pred_te = np.arange(len(Wte))          # prediksi seluruh test
                else:
                    idx_te = np.where(PL_HALF == arm)[0]   # yang IKUT dilatih
                    pred_te = np.where(PL_HALF != arm)[0]  # yang DIPREDIKSI (tidak dilatih)

                Xt = torch.tensor(np.concatenate([Wtr[ti], Wte[idx_te]]))
                St = torch.tensor(np.concatenate([Str[ti], Ste[idx_te]]))
                tt = torch.tensor(np.concatenate([tgt[ti], tgt_te[idx_te]])
                                  if pl is not None else tgt[ti])
                wt = torch.tensor(np.concatenate([sw[ti], SW_PL[idx_te]*pl_w])
                                  if pl is not None else sw[ti], dtype=torch.float32)
                dt = torch.tensor(np.concatenate([dep_t[ti], dep_t_te[idx_te]])
                                  if pl is not None else dep_t[ti])
                dk = torch.tensor(np.concatenate([dep_ok[ti], dep_ok_te[idx_te]])
                                  if pl is not None else dep_ok[ti])
                Nz = torch.tensor(np.ascontiguousarray(Xt.numpy()[:, :, :200]))
                n = len(Xt)

                net = Net3(Str.shape[1]).to(DEV)
                opt = torch.optim.AdamW(net.parameters(), lr=lr, weight_decay=2e-2)
                sch = torch.optim.lr_scheduler.OneCycleLR(
                    opt, max_lr=lr, total_steps=epochs*max(1, n//bs), pct_start=0.2)
                Xv = torch.tensor(Wtr[vi]).to(DEV); Sv = torch.tensor(Str[vi]).to(DEV)
                av = np.zeros(len(vi)); at = np.zeros(len(pred_te))

                for ep in range(epochs):
                    net.train(); perm = torch.randperm(n)
                    for i in range(0, n-bs+1, bs):
                        b = perm[i:i+bs]; xb = Xt[b].clone(); sb = St[b].to(DEV)
                        th = torch.rand(len(b))*2*np.pi; cs, sn = torch.cos(th), torch.sin(th)
                        for k in (0, 3, 6):
                            e_, n_ = xb[:, k].clone(), xb[:, k+1].clone()
                            xb[:, k] = cs[:, None]*e_ - sn[:, None]*n_
                            xb[:, k+1] = sn[:, None]*e_ + cs[:, None]*n_
                        if torch.rand(1).item() < 0.5:
                            for k in (2, 5, 8): xb[:, k] *= -1
                        if torch.rand(1).item() < 0.5:
                            j = torch.randint(0, n, (len(b),))
                            amp = (torch.rand(len(b), 1, 1)*0.6)
                            xb = xb + amp*Nz[j].repeat(1, 1, 5)[:, :, :xb.shape[2]]
                        xb = xb.to(DEV)
                        pm, pdep = net(xb, sb)
                        wb = wt[b].to(DEV)
                        lm = (wb*(pm - tt[b].to(DEV)).abs()).sum()/wb.sum()
                        dkb = dk[b].to(DEV)
                        ld = ((pdep - dt[b].to(DEV)).abs()*dkb).sum()/(dkb.sum()+1e-6)
                        opt.zero_grad(); (lm + 0.15*ld).backward(); opt.step(); sch.step()
                    if ep >= epochs - avg_last:
                        net.eval()
                        with torch.no_grad():
                            av += net(Xv, Sv)[0].cpu().numpy()
                            at += np.concatenate([
                                net(Xte_t[pred_te][i:i+512], Ste_t[pred_te][i:i+512])[0]
                                .cpu().numpy() for i in range(0, len(pred_te), 512)])

                oof[vi] += (av/avg_last + off_v)/(len(seeds)*n_arm)
                pte[pred_te] += (at/avg_last + off_t[pred_te])/(5*len(seeds))
                nf += 1
                print("    %sfold %2d/%d selesai  (%.0f menit terpakai, ~%.0f menit tersisa)"
                      % (tag, nf, ntot, (time.time()-t0)/60,
                         (time.time()-t0)/nf*(ntot-nf)/60), flush=True)
    return oof, pte
'''


DIAG_SRC = '''def diagnosa(oof, pte, nama, ref_o=None, ref_p=None):
    """Diagnostik yang menentukan nasib kandidat PL, dicetak SEBELUM blend apa pun.

    Yang paling penting bukan skornya, melainkan baris KOLAPS TEST. Pseudo-labeling bisa
    membuat prediksi test runtuh ke arah nb8 sementara OOF tetap terlihat beragam; kalau
    itu terjadi, pencarian bobot blend membaca diversitas yang tidak ada di test."""
    po = post_tr(oof)
    print("\\n--- %s ---" % nama)
    print("  lb_real %.4f  dec %.4f  rnd %.4f  bias_rnd %+.3f"
          % (lb_real(po), part_real(po, True), part_real(po, False), bias_rnd(po)))
    print("  (pembanding LOKAL, semua SETELAH post: cnn3 0,1898 | cnn3_avg 0,1888)")
    if ref_o is not None:
        c_o = float(np.corrcoef(oof, ref_o)[0, 1])
        c_p = float(np.corrcoef(pte, ref_p)[0, 1])
        print("\\n  KOLAPS TEST -- korelasi terhadap kandidat KONTROL se-lingkungan:")
        print("    oof  %.4f" % c_o)
        print("    pte  %.4f" % c_p)
        print("    selisih pte-oof %+.4f" % (c_p - c_o))
        if c_p - c_o > 0.02:
            print("    BAHAYA: prediksi test jauh lebih mirip daripada OOF-nya.")
            print("    Label-semu bocor ke prediksi test. Verdikt blend di bawah TIDAK sah")
            print("    -- bobot dipilih dari diversitas OOF yang tidak ada di test.")
        else:
            print("    AMAN: diversitas OOF dan test sebanding, tidak ada kolaps.")
    e = np.abs(oof - y)
    print("\\n  MAE per subset:  desimal %.4f | bulat-dangkal %.4f | bulat-dalam %.4f"
          % (e[~rnd_tr].mean(), e[MR].mean(), e[rnd_tr & (d_tr >= 150)].mean()))
    return po
'''


def nb_pl():
    cells = K.prelude_cells(
        "Pseudo-labeling test — menggeser komposisi training ke distribusi test",
        "Satu-satunya sumbu yang belum pernah dijalankan setelah tiga batch Kaggle. "
        "`Net3` identik notebook_8; yang berubah cuma **himpunan record yang dilatih**.\n\n"
        "**Waktu: ~85 menit (arm A) + ~170 menit (arm B) = ~4,3 jam di T4.** Arm B dua kali "
        "lipat karena tiap fold melatih dua model bersilang atas belahan test — itu yang "
        "menutup kebocoran label-semu ke prediksi test.",
        extra_head=HEAD5)

    cells.append(md(
        "---\n## 1. Pseudo-label + bobot + belahan test\n\n"
        "Label-semu dihitung dari blend notebook_8 (`nb8_ref.npz`), sudah lewat `post_te`. "
        "Bobot sampelnya dibangun meniru konstruksi train (`w(M)/cnt`), dengan grup "
        "(depth, magnitudo dibulatkan ke 0,1) — magnitudo katalog memang diskrit.\n\n"
        "Belahan test dibuat menurut `depth_km`, **bukan** acak per record: record satu "
        "gempa berbagi nilai depth, dan kalau terpisah antar-belahan, model yang melihat "
        "separuh gempa bisa mengenali separuh lainnya lewat grup depth."))
    cells.append(co(PL_SRC))
    cells.append(co(DIAG_SRC))

    cells.append(md(
        "---\n## 2. Arm A — KONTROL: resep notebook_8 apa adanya\n\n"
        "**Uji kewarasan lingkungan, bukan cuma baseline.** `lb_real` harus mendarat di "
        "**0,1898** — angka **SETELAH `post_tr`**. Jangan bandingkan dengan 0,2091; itu "
        "`lb_real` MENTAH, dan tertukarnya dua jenis angka itulah yang merusak verdikt "
        "notebook 09.\n\n"
        "Arm ini juga jadi pembanding se-lingkungan untuk verdikt blend, sehingga gap "
        "Kaggle-vs-lokal 0,0049 tidak lagi terhitung sebagai kerugian ide."))
    cells.append(co(
        'sw = make_sw(power=0.5)\n'
        't0 = time.time()\n'
        'oofA, pteA = run_pl(Wtr, Str, Wte, Ste, sw, pl=None, tag="A ")\n'
        'simpan("cnn14a", oofA, pteA)\n'
        'print("\\narm A selesai %.0f menit"%((time.time()-t0)/60))\n'
        '\n'
        'poA = diagnosa(oofA, pteA, "arm A = KONTROL (resep cnn3)")\n'
        '\n'
        'KONTROL_POST = 0.1898   # lb_real cnn3 lokal SETELAH post_tr (mentahnya 0,2091)\n'
        '_gap = lb_real(poA) - KONTROL_POST\n'
        'print("\\nKONTROL: %.4f vs %.4f lokal  -> gap %+.4f"\n'
        '      %(lb_real(poA), KONTROL_POST, _gap))\n'
        'print("  " + ("COCOK -- lingkungan Kaggle mereproduksi run lokal."\n'
        '              if abs(_gap) < 0.004 else\n'
        '              "TIDAK COCOK. Verdikt blend tetap SAH karena arm B dibandingkan\\n'
        '  terhadap arm A (se-lingkungan), tapi catat angkanya: ini gap lingkungan yang\\n'
        '  belum dijelaskan. Bandingkan juga sidik jari input di sel Setup."))\n'))

    cells.append(md(
        "---\n## 3. Arm B — + pseudo-label\n\n"
        "2.300 record test masuk ke training tiap fold dengan label dari blend nb8. Tiap "
        "fold melatih **dua** model bersilang atas belahan test, jadi tidak ada record "
        "test yang diprediksi model yang melihat label-semunya sendiri.\n\n"
        "> **Baris yang paling menentukan bukan `lb_real`, melainkan KOLAPS TEST.** Kalau "
        "korelasi `pte` terhadap arm A melonjak jauh di atas korelasi `oof`-nya, label-semu "
        "bocor ke prediksi test dan verdikt blend tidak sah — berapa pun bagus skornya."))
    cells.append(co(
        't0 = time.time()\n'
        'oofB, pteB = run_pl(Wtr, Str, Wte, Ste, sw, pl=PL, pl_w=1.0, tag="B ")\n'
        'simpan("cnn14b", oofB, pteB)\n'
        'print("\\narm B selesai %.0f menit"%((time.time()-t0)/60))\n'
        '\n'
        'poB = diagnosa(oofB, pteB, "arm B = + pseudo-label", ref_o=oofA, ref_p=pteA)\n'
        '\n'
        'print("\\n--- efek terisolasi PL (positif = membaik) ---")\n'
        'print("  lb_real      %+.4f"%(lb_real(poA)-lb_real(poB)))\n'
        'print("  sisi bulat   %+.4f   <- ke sinilah PL seharusnya bekerja"\n'
        '      %(part_real(poA,False)-part_real(poB,False)))\n'
        'print("  sisi desimal %+.4f"%(part_real(poA,True)-part_real(poB,True)))\n'
        'print("  bias_rnd     %+.3f -> %+.3f  (ambang 0,05)"%(bias_rnd(poA), bias_rnd(poB)))\n'
        'print("\\nKalau gain-nya ADA tapi tidak menumpuk di sisi bulat, mekanisme yang")\n'
        'print("diklaim (komposisi 32%% -> 51%%) BUKAN yang bekerja -- catat itu.")\n'))

    cells.append(md(
        "---\n## 4. Verdikt blend — protokol UJI 2, pembanding se-lingkungan\n\n"
        "Dua uji dijalankan:\n\n"
        "- **UJI 1** — `cnn14b` menggantikan `cnn3_avg` di blend nb8. Pembandingnya blend "
        "nb8 apa adanya, jadi gap lingkungan ikut terhitung sebagai kerugian ide. Dicetak "
        "supaya sebanding dengan angka batch sebelumnya.\n"
        "- **UJI 2** — pembandingnya blend nb8 dengan slot `cnn3_avg` diisi **arm A**. "
        "Kandidat dan pembanding sama-sama dari Kaggle. **Ini yang menentukan.**\n\n"
        "Ambang: gain holdout **< 0** DAN menang **≥ 7/12** DAN `bias_rnd` ≤ 0,05."))
    cells.append(co(
        'def uji(nama, o, p, base_names, base_O, base_E, ref_oof):\n'
        '    keep = [i for i, n in enumerate(base_names) if n != "cnn3_avg"]\n'
        '    names = [base_names[i] for i in keep] + [nama]\n'
        '    Otr = np.vstack([base_O[keep], o[None, :]])\n'
        '    Ote = np.vstack([base_E[keep], p[None, :]])\n'
        '    r = blend_search(names, Otr, Ote, ref_oof)\n'
        '    r["_nama"] = nama; r["_names"] = names\n'
        '    return r\n'
        '\n'
        'Oref, Eref = ref_stack()\n'
        'ref_nb8 = post_tr(REF["__w__"] @ Oref)\n'
        'print("acuan notebook_8: lb_real=%.4f   [LB aktual 0,1849]\\n"%sc(ref_nb8))\n'
        '\n'
        'print("=== UJI 1 -- pembanding blend nb8 apa adanya ===")\n'
        'r1 = uji("cnn14b", oofB, pteB, CAND, Oref, Eref, ref_nb8)\n'
        'print("cnn14b (ganti)   lb_real %.4f  jujur %.4f  gain %+.5f  menang %2d/12  bias %+.3f"\n'
        '      %(r1["lb_real"], r1["jujur"], r1["gain"], r1["menang"], r1["bias"]))\n'
        '\n'
        'print("\\n=== UJI 2 -- pembanding = blend nb8 dgn cnn3_avg DIGANTI arm A ===")\n'
        'rA = uji("cnn14a", oofA, pteA, CAND, Oref, Eref, ref_nb8)\n'
        'print("  pembanding internal (arm A di slot CNN): lb_real %.4f"%rA["lb_real"])\n'
        'r2 = uji("cnn14b", oofB, pteB, CAND, Oref, Eref, rA["oof"])\n'
        'print("cnn14b (vs armA) lb_real %.4f  jujur %.4f  gain %+.5f  menang %2d/12  bias %+.3f"\n'
        '      %(r2["lb_real"], r2["jujur"], r2["gain"], r2["menang"], r2["bias"]))\n'))

    cells.append(md(
        "---\n## 5. Verdikt akhir\n\n"
        "Verdikt dibaca dari **UJI 2**. Kalau gerbang KOLAPS TEST di sel 3 menyala, "
        "verdikt ini tidak sah berapa pun angkanya — itu diperiksa lebih dulu."))
    cells.append(co(
        '_ck = float(np.corrcoef(pteB, pteA)[0,1]) - float(np.corrcoef(oofB, oofA)[0,1])\n'
        'kolaps = _ck > 0.02\n'
        'est = verdikt(r2, "cnn14b (vs arm A)")\n'
        'lolos = (r2["gain"] < 0 and r2["menang"] >= 7 and r2["bias"] <= 0.05\n'
        '         and not kolaps)\n'
        'print()\n'
        'if kolaps:\n'
        '    print("DIBATALKAN oleh gerbang KOLAPS TEST (selisih korelasi %+.4f > 0,02)."%_ck)\n'
        '    print("Label-semu bocor ke prediksi test: bobot blend dipilih dari diversitas")\n'
        '    print("OOF yang tidak ada di test. Angka di atas TIDAK bisa dipakai.")\n'
        'elif lolos:\n'
        '    print("LOLOS PROTOKOL -- layak jadi kandidat submission (notebook_11).")\n'
        '    print("Serap di lokal dengan tools/serap_nb12.py sebelum menulis submission.")\n'
        'else:\n'
        '    print("TIDAK LOLOS -- notebook_8 tetap submission terbaik.")\n'
        '    print("Catat kegagalannya di sudah_run/README.md BESERTA ALASANNYA, dan")\n'
        '    print("catat juga apakah gain-nya menumpuk di sisi bulat seperti yang")\n'
        '    print("diklaim mekanismenya. Yang gagal tanpa catatan pasti dicoba ulang.")\n'
        'print()\n'
        'print("Ingat: hanya ADA SATU submission final, dan selisih ke peringkat 1 (0,0014)")\n'
        'print("ada di dalam derau LB publik (sd ~0,004 untuk model berbeda). Kandidat yang")\n'
        'print("cuma menang tipis BUKAN alasan cukup untuk menggeser notebook_8.")\n'))

    cells.append(md(
        "---\n## 6. Bungkus jadi satu zip\n\n"
        "`cnn14a` (kontrol) **wajib** ikut diunduh, bukan cuma `cnn14b` — tanpa arm A, "
        "verdikt UJI 2 tidak bisa dihitung ulang di lokal."))
    cells.append(co('bundel("hasil_cnn14_pl")\n'))
    return nb(cells)


files = {"11_pseudo_label.ipynb": nb_pl()}
for nama, obj in files.items():
    (OUT / nama).write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")
    print("ditulis:", OUT / nama)
