# -*- coding: utf-8 -*-
"""Generator batch Kaggle ke-3 — model gabungan waveform + 196 fitur rekayasa.

Ini satu-satunya keluarga yang tersisa dengan bentuk peluang "terobosan", bukan "naik
tipis". Alasannya satu angka:

    fitur yang dilihat LightGBM : 196
    skalar yang dilihat CNN     :   8

**Belum pernah ada satu model pun di case ini yang melihat keduanya sekaligus.** LightGBM
melihat fitur, CNN melihat waveform, dan mereka cuma disatukan lewat blend LINEAR. Korelasi
keduanya 0,878 — itu justru bukti mereka melihat hal yang berbeda, dan blend linear tidak
bisa mempelajari interaksi apa pun di antaranya.

Kenapa ini BUKAN pelanggaran atas keluarga yang sudah ditutup: ketujuh notebook deep yang
gagal (Inception, TCN, konvolusi dalam, konvolusi+transformer, augmentasi agresif, SSL,
kepala distribusi) semuanya memakai **8 skalar yang sama**. Yang divariasikan cuma
arsitektur di atas input yang identik. Notebook ini mengubah **input**-nya, dan itu satu-
satunya sumbu yang belum pernah digeser.

Peluang jujurnya: bisa saja model gabungan cuma menginterpolasi keduanya sehingga
korelasinya naik ke ~0,99 dan tidak berguna di blend. Notebook mencetak korelasi itu
eksplisit sebagai diagnostik utama kedua setelah gain holdout.

Jalankan:  python "Case 1/tools/mk_kaggle4.py"
"""
import _path  # noqa: F401
import json
import mk_kaggle as K

OUT = _path.ROOT / "belum_run"
OUT.mkdir(exist_ok=True)

md, co, nb = K.md, K.co, K.nb


HEAD4 = """
---

## Kenapa notebook ini ada — dan kenapa ia BUKAN "model deep baru" yang ke-8

Dua batch sebelumnya menjalankan 8 notebook GPU dan **7 gagal**. Tujuh arsitektur berbeda
semuanya mendarat di `lb_real` **0,208–0,232** dengan korelasi **0,89–0,97** terhadap CNN
v3. Kesimpulan yang diambil: itu plafon konvolusi 1D atas 5 detik waveform.

Kesimpulan itu benar **untuk input yang dipakai ketujuhnya**. Dan di situ letak masalahnya:

```
fitur yang dilihat LightGBM : 196
skalar yang dilihat CNN     :   8
```

Ketujuh notebook yang gagal memvariasikan **arsitektur** di atas **8 skalar yang sama**
(3 × log10(peak), logdist, logdep, loghypo, snr/40, is_clipped). Tidak satu pun mengubah
input. CNN tidak pernah melihat 188 fitur sisanya — rasio pita spektral, `tau_c`/`tau_p`,
eigenvalue polarisasi (`rectilin`, `planarity`), waktu-energi kumulatif (`tE10`…`tE90`),
rise time, koreksi jarak `C*`, gradien antar-window `g*`.

LightGBM dan CNN saat ini cuma disatukan lewat **blend linear**, korelasi **0,878**.
Korelasi serendah itu berarti mereka benar-benar melihat hal berbeda — dan blend linear
tidak bisa mempelajari **interaksi** apa pun di antara keduanya. Model yang melihat
dua-duanya bisa.

**Itu satu-satunya sumbu input yang belum pernah digeser di seluruh case ini.**

### Peluang jujurnya — baca ini sebelum berharap

Mode kegagalan yang paling mungkin: model gabungan cuma **menginterpolasi** kedua sumber,
skornya bagus sendirian tapi korelasinya naik ke ~0,99 terhadap kandidat yang sudah ada,
sehingga **tidak berguna di blend**. Itu persis vonis CNN+BiGRU di nb8 (0,2101 sendirian,
setara CNN v3, tapi korelasi 0,967 → menang 1/12 → ditolak).

Karena itu diagnostik utama notebook ini ada **dua**, dan keduanya wajib lolos:

1. gain holdout negatif DAN menang >= 7/12 belahan;
2. **korelasi maksimum terhadap 8 kandidat nb8 < 0,95.** Kalau ia lebih tinggi dari itu,
   model ini cuma salinan mahal dari yang sudah ada, berapa pun bagus skor tunggalnya.

### BAHAYA UTAMA: `bias_rnd` — ini pernah meledak persis di situasi ini

**Stacking** (meta-LightGBM di atas prediksi OOF + fitur konteks) membuat `bias_rnd`
melonjak **+0,027 → +0,095**: stacker memakai `is_rnd`/`depth_km` untuk menghafal prior
katalog train, yaitu mode kegagalan `notebook_2` (LB 0,2262, kegagalan terburuk di case
ini). Blend linear aman justru karena ia **tidak bisa** mengkondisikan pada fitur.

Model gabungan ini **bisa** mengkondisikan pada fitur. Jadi risikonya nyata dan sama.

Yang menahannya, dan kenapa risikonya masih layak diambil:

- `get_feats()` mengembalikan **196 fitur per-record saja — TANPA agregat grup**
  (`add_group_feats` tidak dipanggil). Jadi penanda tipe depth paling terang — `grp_size`
  yang `NaN` untuk depth bulat, pembunuh `notebook_2` — **tidak ada di sini**.
- LightGBM sudah melihat 196 fitur yang sama persis selama 8 notebook tanpa `bias_rnd`
  meledak (Model A +0,040, Model B +0,064). Yang meledak cuma stacker, dan bedanya stacker
  melihat **prediksi OOF** plus konteks.

Notebook mencetak `bias_rnd` di setiap tahap dan **menolak kandidat di atas +0,05**
(ambang jujur; `notebook_5` rugi di LB pada +0,056).

### Dua hal wajib untuk fitur yang masuk jaringan saraf

1. **`nan_to_num`.** `kurt` punya 9 nilai non-finite di train. LightGBM menelan NaN secara
   native jadi ini tidak terlihat selama 8 notebook, tapi di jaringan saraf **satu NaN
   merambat ke seluruh batch** dan seluruh run jadi sampah tanpa error.
2. **Standardisasi memakai statistik FOLD TRAINING saja.** Menghitung mean/sd di seluruh
   data adalah kebocoran. Notebook ini menghitungnya di dalam fold dan menerapkannya ke
   validasi + test.

Keduanya diverifikasi di sel Setup dan dicetak, bukan diasumsikan.

### Kalibrasi angka LB — supaya tidak salah baca hasilnya

LB publik cuma **30% data test**. Sd selisih dua submission berkorelasi 0,999 adalah
**0,0008**; untuk submission berbeda (corr 0,888) **0,0038**. LB terbaik 0,1849, peringkat 1
di 0,1835 — selisih **0,0014 = 0,4 sigma**. **Kita sudah efektif seri dengan peringkat 1**,
dan kompetisi ini **cuma mengizinkan SATU submission final** — tidak ada lindung nilai.

Konsekuensinya: kandidat yang cuma menang tipis di `lb_real` **bukan** alasan cukup untuk
menggeser `notebook_8`. Yang menentukan peringkat akhir adalah 70% data yang belum terlihat.
"""


ARCH4_SRC = '''# ---------------------------------------------------------------------------------
# Fitur untuk jaringan saraf: bersihkan, lalu standardisasi DI DALAM FOLD.
#
# `kurt` punya 9 nilai non-finite di train. LightGBM menelan NaN secara native, jaringan
# saraf tidak -- satu NaN merambat ke seluruh batch lewat batchnorm dan seluruh run jadi
# sampah TANPA memunculkan error. Ini diperiksa dan dicetak, bukan diasumsikan.
# ---------------------------------------------------------------------------------
FEAT_COLS = [c for c in Ftr.columns]
FTR_RAW = np.nan_to_num(Ftr[FEAT_COLS].values.astype(np.float32),
                        nan=0.0, posinf=0.0, neginf=0.0)
FTE_RAW = np.nan_to_num(Fte[FEAT_COLS].values.astype(np.float32),
                        nan=0.0, posinf=0.0, neginf=0.0)
_bad_tr = int((~np.isfinite(Ftr[FEAT_COLS].values.astype(np.float32))).sum())
_bad_te = int((~np.isfinite(Fte[FEAT_COLS].values.astype(np.float32))).sum())
print("fitur untuk jaringan: %d kolom" % len(FEAT_COLS))
print("  nilai non-finite dibersihkan: train %d, test %d" % (_bad_tr, _bad_te))
print("  (diukur di lokal 22 Agu 2026: 18 di train, dari `kurt`. Kalau NOL, berarti")
print("   dataset atau extract() berubah -- periksa, jangan diabaikan.)")
assert np.isfinite(FTR_RAW).all() and np.isfinite(FTE_RAW).all(), "masih ada non-finite!"

# sanity: 196 fitur ini adalah keluaran extract() saja -- TANPA agregat grup.
# Itu disengaja: `grp_size` yang NaN untuk depth bulat adalah penanda tipe depth paling
# terang dan pembunuh notebook_2 (LB 0,2262). Kalau suatu saat agregat grup ditambahkan
# ke sini, bias_rnd WAJIB diperiksa ulang dari nol.
assert not any("grp" in c for c in FEAT_COLS), "agregat grup bocor ke fitur jaringan!"

def fold_std(ti):
    """mean/sd dari fold TRAINING saja. Menghitungnya di seluruh data = kebocoran."""
    mu = FTR_RAW[ti].mean(0)
    sd = FTR_RAW[ti].std(0) + 1e-6
    return mu, sd


class Net13(nn.Module):
    """`Net3` notebook_8 dengan SATU perubahan: cabang skalar 8-dimensi diganti cabang
    fitur 196-dimensi yang punya kapasitas sendiri.

    Bagian konvolusinya (`Blk`, w=64, 5 blok, SE, dua kepala) disalin apa adanya dari
    notebook_8 -- kalau bagian itu ikut diubah, gain/ruginya tidak bisa dipisahkan antara
    "fitur menolong" dan "arsitektur beda".

    Kenapa cabang fitur butuh MLP sendiri dan tidak boleh sekadar di-concat: 196 fitur
    langsung disambung ke trunk akan didominasi oleh dimensinya (196 vs w*8 = 512 dari
    konvolusi masih sepadan, tapi 196 fitur mentah yang berkorelasi tinggi membuat lapisan
    pertama menghabiskan kapasitasnya untuk mendekorelasi). MLP 196 -> 128 -> 64 dengan
    dropout mengompresnya dulu, dan dropout-nya juga yang menahan model bersandar penuh
    pada fitur lalu mengabaikan waveform.

    `p_feat_drop` mematikan SELURUH cabang fitur secara acak saat training (modality
    dropout). Tanpa ini, jaringan cenderung memakai fitur -- yang sudah matang dan mudah
    dibaca -- lalu membiarkan konvolusinya kurang terlatih, dan hasilnya jadi LightGBM
    mahal dengan korelasi ~0,99 terhadap kandidat yang sudah ada. Itu mode kegagalan yang
    paling mungkin di notebook ini, jadi ditahan secara arsitektural."""
    def __init__(s, n_feat, w=64, p_feat_drop=0.15):
        super().__init__()
        s.body = nn.Sequential(Blk(9,w), Blk(w,w*2), Blk(w*2,w*3),
                               Blk(w*3,w*4,k=5,pool=2), Blk(w*4,w*4,k=3,pool=2))
        s.feat = nn.Sequential(
            nn.Linear(n_feat,128), nn.BatchNorm1d(128), nn.SiLU(), nn.Dropout(0.30),
            nn.Linear(128,64), nn.SiLU())
        s.trunk = nn.Sequential(nn.Linear(w*8+64,256), nn.SiLU(), nn.Dropout(0.25),
                                nn.Linear(256,96), nn.SiLU())
        s.mag = nn.Linear(96,1); s.dep = nn.Linear(96,1)
        s.p_feat_drop = p_feat_drop
    def forward(s, x, ft):
        h = s.body(x)
        f = s.feat(ft)
        if s.training and s.p_feat_drop > 0:
            keep = (torch.rand(f.shape[0], 1, device=f.device) >= s.p_feat_drop).float()
            f = f*keep
        h = torch.cat([h.mean(-1), h.amax(-1), f], dim=1)
        h = s.trunk(h)
        return s.mag(h).squeeze(-1), s.dep(h).squeeze(-1)


def run_joint(Wtr, Wte, sw, seeds=(0,1,2), epochs=80, bs=128, lr=2.5e-3, avg_last=10,
              p_feat_drop=0.15, tag=""):
    """Loop training notebook_8 apa adanya. Yang berubah hanya: cabang skalar -> cabang
    fitur, dan standardisasi fitur dihitung ulang di tiap fold.

    Augmentasi waveform tetap ketiganya (rotasi horizontal, flip vertikal, tempel derau
    pre-P). CATATAN PENTING: fitur TIDAK ikut diaugmentasi, karena fitur dihitung dari
    waveform ASLI. Itu memang tidak konsisten, dan disengaja -- menghitung ulang 196 fitur
    per batch teraugmentasi butuh Welch + filtfilt di dalam loop training dan biayanya
    ratusan kali lipat. Efek sampingnya: augmentasi jadi sedikit lebih lemah daripada di
    nb8, karena cabang fitur melihat versi yang tidak diubah. `p_feat_drop` sebagian
    mengimbanginya."""
    Xa = Ftr[A_BASE].values.astype(np.float64); Xa_te = Fte[A_BASE].values.astype(np.float64)
    dep_t = np.log10(d_tr+1).astype(np.float32); dep_ok = (~rnd_tr).astype(np.float32)
    noise = Wtr[:, :, :200].copy()
    oof = np.zeros(len(y)); pte = np.zeros(len(Wte))
    Xte_t = torch.tensor(Wte).to(DEV)
    nf = 0; t0 = time.time()
    for seed in seeds:
        torch.manual_seed(seed); np.random.seed(seed)
        for ti, vi in GroupKFold(5).split(Wtr, y, ev):
            # anchor ridge: target residual (trik nb5, dipakai nb8) -- tidak diubah
            rg = Ridge(alpha=1.0).fit(Xa[ti], y[ti], sample_weight=sw[ti])
            tgt = (y - rg.predict(Xa)).astype(np.float32)
            off_v = rg.predict(Xa[vi]); off_t = rg.predict(Xa_te)
            mu, sd = fold_std(ti)                      # <-- statistik fold training saja
            Ftr_z = (FTR_RAW - mu)/sd
            Fte_z = torch.tensor((FTE_RAW - mu)/sd).to(DEV)
            net = Net13(len(FEAT_COLS), p_feat_drop=p_feat_drop).to(DEV)
            opt = torch.optim.AdamW(net.parameters(), lr=lr, weight_decay=2e-2)
            sch = torch.optim.lr_scheduler.OneCycleLR(
                opt, max_lr=lr, total_steps=epochs*max(1, len(ti)//bs), pct_start=0.2)
            Xt = torch.tensor(Wtr[ti]); Gt = torch.tensor(Ftr_z[ti]); Nz = torch.tensor(noise[ti])
            tt = torch.tensor(tgt[ti]); wt = torch.tensor(sw[ti], dtype=torch.float32)
            dt = torch.tensor(dep_t[ti]); dk = torch.tensor(dep_ok[ti])
            Xv = torch.tensor(Wtr[vi]).to(DEV); Gv = torch.tensor(Ftr_z[vi]).to(DEV)
            av = np.zeros(len(vi)); at = np.zeros(len(Wte))
            for ep in range(epochs):
                net.train(); perm = torch.randperm(len(ti))
                for i in range(0, len(ti)-bs+1, bs):
                    b = perm[i:i+bs]; xb = Xt[b].clone(); gb = Gt[b].to(DEV)
                    th = torch.rand(len(b))*2*np.pi; cs, sn = torch.cos(th), torch.sin(th)
                    for k in (0, 3, 6):
                        e_, n_ = xb[:, k].clone(), xb[:, k+1].clone()
                        xb[:, k] = cs[:, None]*e_ - sn[:, None]*n_
                        xb[:, k+1] = sn[:, None]*e_ + cs[:, None]*n_
                    if torch.rand(1).item() < 0.5:
                        for k in (2, 5, 8): xb[:, k] *= -1
                    if torch.rand(1).item() < 0.5:
                        j = torch.randint(0, len(ti), (len(b),))
                        amp = (torch.rand(len(b), 1, 1)*0.6)
                        xb = xb + amp*Nz[j].repeat(1, 1, 5)[:, :, :xb.shape[2]]
                    xb = xb.to(DEV)
                    pm, pdep = net(xb, gb)
                    wb = wt[b].to(DEV)
                    lm = (wb*(pm - tt[b].to(DEV)).abs()).sum()/wb.sum()
                    dkb = dk[b].to(DEV)
                    ld = ((pdep - dt[b].to(DEV)).abs()*dkb).sum()/(dkb.sum()+1e-6)
                    opt.zero_grad(); (lm + 0.15*ld).backward(); opt.step(); sch.step()
                if ep >= epochs - avg_last:
                    net.eval()
                    with torch.no_grad():
                        av += net(Xv, Gv)[0].cpu().numpy()
                        at += np.concatenate([net(Xte_t[i:i+512], Fte_z[i:i+512])[0].cpu().numpy()
                                              for i in range(0, len(Wte), 512)])
            oof[vi] += (av/avg_last + off_v)/len(seeds)
            pte += (at/avg_last + off_t)/(5*len(seeds))
            nf += 1
            print("    %sfold %2d/%d selesai  (%.0f menit terpakai, ~%.0f menit tersisa)"
                  % (tag, nf, 5*len(seeds), (time.time()-t0)/60,
                     (time.time()-t0)/nf*(5*len(seeds)-nf)/60), flush=True)
    return oof, pte
'''


DIAG_SRC = '''def diagnosa(oof, pte, nama):
    """Diagnostik yang menentukan nasib model ini, dicetak sebelum blend apa pun.

    Skor tunggal BUKAN yang menentukan. CNN+BiGRU di nb8 skornya 0,2101 -- praktis setara
    CNN v3 -- lalu ditolak karena korelasinya 0,967. Kandidat ke-9 selalu bisa menurunkan
    angka di data tempat bobotnya dipilih; yang tidak bisa dipalsukan adalah korelasi."""
    po = post_tr(oof)
    print("\\n" + "="*70)
    print("DIAGNOSA MODEL TUNGGAL -- %s" % nama)
    print("="*70)
    print("  lb_real   %.4f   (cnn3_avg 0,2074 | cnn3_dir 0,2116 | LightGBM terbaik 0,2030)"
          % lb_real(po))
    print("  dec %.4f  rnd %.4f" % (part_real(po, True), part_real(po, False)))
    b = bias_rnd(po)
    print("  bias_rnd  %+.3f   %s" % (b, "AMAN" if b <= 0.05 else
          "BAHAYA -- ini mode kegagalan stacking (+0,095) dan notebook_2 (LB 0,2262)"))
    if REF is None:
        print("  (nb8_ref.npz tidak ada -- korelasi tidak bisa dihitung)")
        return None
    cors = {n: float(np.corrcoef(oof, REF[n+"__oof"])[0, 1]) for n in CAND}
    print()
    for n, c in sorted(cors.items(), key=lambda kv: -kv[1]):
        print("  korelasi vs %-10s %.3f" % (n, c))
    cmax = max(cors.values())
    print()
    print("  KORELASI MAKS %.3f  -- %s" % (cmax,
          "LOLOS (< 0,95): model ini melihat sesuatu yang lain." if cmax < 0.95 else
          "GAGAL (>= 0,95): salinan mahal dari kandidat yang sudah ada."))
    print("  Pembanding: CNN v3 menang di nb8 dengan korelasi 0,878. Keempat CNN batch 1")
    print("  gagal di 0,92-0,96, dan CNN+BiGRU ditolak di 0,967.")
    print("="*70)
    return cmax
'''


def prelude(judul, deskripsi, waktu):
    cells = K.prelude_cells(
        judul, deskripsi,
        "\n**Perkiraan waktu di GPU Kaggle (T4): %s.** Notebook mencetak sisa waktu setiap "
        "fold selesai, jadi progresnya kelihatan sejak fold pertama.\n" % waktu)
    cells.insert(2, md(HEAD4))
    return cells


def nb_joint():
    cells = prelude(
        "Model gabungan — waveform + 196 fitur rekayasa dalam satu jaringan",
        "Satu-satunya sumbu **input** yang belum pernah digeser di case ini.\n\n"
        "Ketujuh notebook deep yang gagal memvariasikan arsitektur di atas **8 skalar\n"
        "yang sama**. CNN tidak pernah melihat 188 fitur sisanya; LightGBM tidak pernah\n"
        "melihat waveform. Mereka cuma disatukan lewat **blend linear**, korelasi 0,878 —\n"
        "yang berarti mereka melihat hal berbeda, dan blend linear tidak bisa mempelajari\n"
        "interaksi apa pun di antaranya.\n\n"
        "Bagian konvolusi `Net3` disalin **apa adanya** dari notebook_8. Yang berubah\n"
        "hanya cabang skalar 8-dim → cabang fitur 196-dim ber-MLP sendiri.\n\n"
        "**Dua gerbang, keduanya wajib lolos:** gain holdout negatif + menang ≥ 7/12,\n"
        "**dan** korelasi maks terhadap kandidat nb8 **< 0,95**. Gerbang kedua itu yang\n"
        "membunuh CNN+BiGRU (0,967) meski skor tunggalnya setara CNN v3.",
        "~2–2,5 jam (15 fold; cabang fitur menambah <5% biaya per langkah)")

    cells.append(md(
        "---\n## 1. Fitur untuk jaringan + arsitektur gabungan\n\n"
        "Tiga hal yang diperiksa di sel ini, semuanya karena kegagalan nyata:\n\n"
        "1. **`nan_to_num`** — `kurt` punya 9 nilai non-finite. LightGBM menelannya secara "
        "native; jaringan saraf tidak, dan satu NaN merambat ke seluruh batch **tanpa "
        "memunculkan error**. Di-`assert`, bukan diasumsikan.\n"
        "2. **`assert` tidak ada agregat grup** — `grp_size` yang `NaN` untuk depth bulat "
        "adalah penanda tipe depth paling terang dan pembunuh `notebook_2` (LB 0,2262). "
        "`get_feats()` memang tidak memanggil `add_group_feats`, tapi itu dijaga eksplisit "
        "supaya tidak diam-diam berubah nanti.\n"
        "3. **Standardisasi di dalam fold** — mean/sd dihitung dari fold training saja."))
    cells.append(co(ARCH4_SRC))
    cells.append(co(DIAG_SRC))

    cells.append(md(
        "---\n## 2. Training\n\n"
        "`sw = w(M)/sqrt(cnt)`, 3 seed × 5 GroupKFold berbasis event, 80 epoch, rata-rata "
        "10 epoch terakhir — semuanya identik notebook_8, supaya angkanya sebanding."))
    cells.append(co(
        'sw = make_sw(power=0.5)\n'
        't0 = time.time()\n'
        'oof, pte = run_joint(Wtr, Wte, sw, tag="")\n'
        'print("\\ntraining selesai %.0f menit"%((time.time()-t0)/60))\n'
        'simpan("cnn13_join", oof, pte)\n'
        'cmax = diagnosa(oof, pte, "cnn13_join")\n'))

    cells.append(md(
        "---\n## 3. Varian modality-dropout lebih kuat — hanya kalau gerbang korelasi gagal\n\n"
        "Kalau korelasi maks ≥ 0,95, penyebab yang paling mungkin adalah jaringan bersandar "
        "penuh pada cabang fitur dan membiarkan konvolusinya kurang terlatih — hasilnya "
        "LightGBM mahal. Obatnya menaikkan `p_feat_drop` 0,15 → 0,40 sehingga jaringan "
        "**terpaksa** bisa memprediksi dari waveform saja di 40% langkah.\n\n"
        "Sel ini **dilewati kalau gerbang pertama sudah lolos** — tidak ada gunanya membayar "
        "satu jam GPU lagi untuk memperbaiki masalah yang tidak terjadi."))
    cells.append(co(
        'if cmax is not None and cmax >= 0.95:\n'
        '    print("korelasi %.3f >= 0,95 -- jalankan varian modality-dropout kuat.\\n"%cmax)\n'
        '    t0 = time.time()\n'
        '    oof2, pte2 = run_joint(Wtr, Wte, sw, p_feat_drop=0.40, tag="drop40 ")\n'
        '    print("\\nselesai %.0f menit"%((time.time()-t0)/60))\n'
        '    simpan("cnn13_drop40", oof2, pte2)\n'
        '    cmax2 = diagnosa(oof2, pte2, "cnn13_drop40")\n'
        'else:\n'
        '    oof2 = pte2 = cmax2 = None\n'
        '    print("gerbang korelasi LOLOS di varian pertama -- varian kedua DILEWATI.")\n'
        '    print("Menghemat ~1 jam GPU. Itu keputusan yang benar, bukan langkah terlupa.")\n'))

    cells.append(md(
        "---\n## 4. Blend + verdikt\n\n"
        "Dua protokol, karena keduanya menjawab pertanyaan berbeda:\n\n"
        "- **tambah** — kandidat ke-9 di samping 8 kandidat nb8. Ini yang dipakai semua "
        "batch sebelumnya.\n"
        "- **ganti** — kalau model gabungan memang menggantikan peran `cnn3_avg` **dan** "
        "`resA_dep` sekaligus (ia melihat kedua sumber), keduanya dikeluarkan dan jumlah "
        "kandidat turun jadi 7. Blend yang lebih ramping dengan skor sama lebih dipercaya, "
        "karena derajat bebas pencarian bobotnya lebih sedikit.\n\n"
        "Kriteria tidak dilonggarkan: **gain holdout negatif DAN menang ≥ 7/12 DAN "
        "`bias_rnd` ≤ +0,05 DAN `lb_real` < 0,1762.**"))
    cells.append(co(
        'def uji(key, o, p, mode):\n'
        '    if mode == "ganti":\n'
        '        buang = {"cnn3_avg", "resA_dep"}\n'
        '        keep = [i for i, n in enumerate(CAND) if n not in buang]\n'
        '        names = [CAND[i] for i in keep] + [key]\n'
        '        Otr = np.vstack([Oref[keep], o[None, :]])\n'
        '        Ote = np.vstack([Eref[keep], p[None, :]])\n'
        '    else:\n'
        '        names = CAND + [key]\n'
        '        Otr = np.vstack([Oref, o[None, :]])\n'
        '        Ote = np.vstack([Eref, p[None, :]])\n'
        '    r = blend_search(names, Otr, Ote, ref_oof)\n'
        '    r["_nama"] = "%s (%s)" % (key, mode); r["_names"] = names\n'
        '    return r\n'
        '\n'
        'hasil = []\n'
        'if REF is None:\n'
        '    print("nb8_ref.npz tidak ditemukan -- verdikt blend dilewati.")\n'
        'else:\n'
        '    Oref, Eref = ref_stack()\n'
        '    ref_oof = post_tr(REF["__w__"] @ Oref)\n'
        '    print("acuan notebook_8: lb_real=%.4f   [LB aktual 0,1849]\\n"%sc(ref_oof))\n'
        '    kand = [("cnn13_join", oof, pte)]\n'
        '    if oof2 is not None: kand.append(("cnn13_drop40", oof2, pte2))\n'
        '    for key, o_, p_ in kand:\n'
        '        for mode in ["tambah", "ganti"]:\n'
        '            r = uji(key, o_, p_, mode); hasil.append(r)\n'
        '            print("%-28s lb_real %.4f  jujur %.4f  gain %+.5f  menang %2d/12  bias %+.3f"\n'
        '                  %(r["_nama"], r["lb_real"], r["jujur"], r["gain"], r["menang"], r["bias"]))\n'))

    cells.append(co(
        'if hasil:\n'
        '    best = min(hasil, key=lambda r: r["gain"])\n'
        '    print("\\nkandidat terbaik menurut gain holdout: %s\\n"%best["_nama"])\n'
        '    print("bobot:", dict(zip(best["_names"], np.round(best["w"], 3))))\n'
        '    print("bobot model baru: %.3f\\n"%best["w"][-1])\n'
        '    verdikt(best, best["_nama"])\n'
        '    simpan("blend_cnn13", best["oof"], best["pte"], best)\n'
        '    lolos = (best["gain"] < 0 and best["menang"] >= 7 and best["bias"] <= 0.05\n'
        '             and best["lb_real"] < LB_JUARA and (cmax is None or cmax < 0.95))\n'
        '    print()\n'
        '    if lolos:\n'
        '        print("LOLOS KEDUA GERBANG -- layak jadi kandidat submission.")\n'
        '        print("Tetap ingat: hanya ADA SATU submission final, dan jarak ke peringkat 1")\n'
        '        print("(0,0014) ada di dalam derau LB publik. Ambangnya gain holdout jujur.")\n'
        '    else:\n'
        '        print("TIDAK LOLOS -- notebook_8 tetap submission terbaik.")\n'
        '        print("Catat di sudah_run/README.md: skor tunggal, korelasi maks, bias_rnd,")\n'
        '        print("gain, menang n/12. Yang gagal justru yang paling sering dicoba ulang")\n'
        '        print("kalau alasannya tidak dicatat.")\n'))

    cells.append(md("---\n## 5. Bungkus hasil jadi satu zip"))
    cells.append(co('bundel("hasil_cnn13_join")\n'))
    return nb(cells)


files = {"10_cnn_fitur_gabung.ipynb": nb_joint()}
for nama, obj in files.items():
    (OUT / nama).write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")
    print("tertulis:", OUT / nama)
