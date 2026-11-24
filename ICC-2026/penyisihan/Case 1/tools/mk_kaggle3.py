# -*- coding: utf-8 -*-
"""Generator batch Kaggle ke-3 — TTA + komposisi record clipped.

Dua batch sebelumnya menutup keluarga "model deep BARU atas waveform yang sama": 8 notebook
GPU, 7 gagal, semuanya mendarat di `lb_real` 0,208-0,232 dengan korelasi 0,89-0,97 terhadap
CNN v3. Notebook di sini sengaja TIDAK masuk keluarga itu — arsitekturnya `Net3` persis
notebook_8, tanpa satu baris pun diubah. Yang diuji adalah dua hal yang belum pernah
disentuh sama sekali di repo ini:

1. **Test-time augmentation.** Kata "TTA" nol kemunculan di `lab/`, `experiments/`,
   `tools/`, dan seluruh dokumen. CNN v3 dilatih dengan rotasi horizontal acak + flip
   vertikal, tapi saat inferensi cuma dilihat SATU orientasi. Merata-ratakan prediksi atas
   grup simetri itu memaksa keluarannya benar-benar invarian, bukan sekadar kira-kira.
   Mekanismenya **pengurangan varians**, bukan informasi baru — jadi vonis "plafon
   informasi 5 detik waveform" tidak berlaku untuknya.

2. **Bobot record `is_clipped`.** Diukur ulang di sesi ini (angkanya di HEAD3 di bawah):
   record clipped 1,68% di train tapi **3,78% di test**, dan MAE-nya 0,1838 vs 0,1338
   **setelah distribusi magnitudonya distandarisasi** — jadi selisihnya nyata, bukan efek
   komposisi. Ini subgrup 1,68% yang error-nya 37% lebih besar dan porsinya di test 2,25x.

Kenapa keduanya digabung dalam satu notebook padahal aturan repo "satu notebook = satu
ide": **TTA hanya menyentuh inferensi, jadi ia gratis untuk dipisahkan.** Dua kali training
(A = resep nb8 apa adanya, B = + bobot clipped) menghasilkan EMPAT kandidat karena tiap
bobot dievaluasi dua kali, dengan dan tanpa TTA. Matriks 2x2-nya lengkap dan tiap efek
tetap bisa diisolasi — justru lebih diagnostik daripada dua notebook terpisah.

Run A juga berfungsi sebagai **kontrol**: resepnya identik `cnn3`, jadi kalau `lb_real`-nya
tidak mendarat di ~0,2091 berarti ada yang salah di lingkungan Kaggle dan seluruh verdikt
notebook ini tidak bisa dipercaya. Itu dicetak eksplisit.

Jalankan:  python "Case 1/tools/mk_kaggle3.py"
"""
import _path  # noqa: F401
import json
import mk_kaggle as K

OUT = _path.ROOT / "belum_run"
OUT.mkdir(exist_ok=True)

md, co, nb = K.md, K.co, K.nb


HEAD3 = """
---

## Kenapa batch ini ada, dan kenapa ia BUKAN "model deep baru"

Dua batch sebelumnya menjalankan 8 notebook GPU dan **7 gagal**. Tujuh arsitektur/regime
training berbeda — Inception, TCN dilatasi, konvolusi dalam, konvolusi+transformer,
augmentasi agresif, pra-latih SSL, kepala distribusi — semuanya mendarat di `lb_real`
**0,208–0,232** dengan korelasi **0,89–0,97** terhadap CNN v3. Kesimpulannya: itu plafon
yang bisa dicapai konvolusi 1D dari 5 detik waveform, dan **keluarga itu ditutup**.

Notebook ini tidak melanggar penutupan itu. `Net3` di sini **identik** dengan notebook_8 —
arsitektur, jadwal, augmentasi training, anchor ridge, semuanya. Yang diuji dua hal di luar
model:

### 1. Test-time augmentation (belum pernah dicoba sama sekali)

Kata "TTA" nol kemunculan di seluruh repo. CNN v3 dilatih dengan **rotasi horizontal acak**
(sudut kontinu pada pasangan kanal E/N) dan **flip vertikal** (kanal Z), karena orientasi
stasiun terhadap azimut sumber memang sembarang — itu simetri fisik yang sah. Tapi saat
inferensi model cuma dilihat satu orientasi, jadi ia hanya *kira-kira* invarian; sisa
ketidak-invarianannya masuk sebagai derau prediksi.

Merata-ratakan prediksi atas grup simetri itu menghilangkan derau tersebut **secara eksak**.
Ini bukan informasi baru dan bukan arsitektur baru — ini pengurangan varians, sumbu yang
belum pernah digarap. Ukuran efeknya bisa ditaksir dari sumbu varians yang sudah pernah
diukur: menambah 3 → 6 seed memberi CNN **−0,0017** (0,2091 → 0,2074), dengan korelasi
antar-paket 0,9875. TTA menyerang komponen varians yang **berbeda** dari seed.

Karena rotasi dan flip simetris, TTA **tidak bisa** menggeser mean prediksi subset
depth-bulat — jadi ia aman terhadap ketiga diagnostik transfer secara konstruksi. Itu
properti yang tidak dimiliki satu pun ide yang gagal di dua batch sebelumnya.

### 2. Bobot record `is_clipped` (diukur ulang, premisnya SUDAH dikoreksi)

Yang diukur di sesi ini pada OOF notebook_8:

| | train | test |
|---|---|---|
| proporsi `is_clipped` | 1,68% (n=176) | **3,78% (n=87)** |

| | MAE |
|---|---|
| record clipped | 0,1990 |
| record non-clipped | 0,1338 |
| **clipped, distandarisasi ke distribusi magnitudo non-clipped** | **0,1838** |

Standarisasi itu penting: record clipped magnitudonya memang lebih besar (5,65 vs 5,28),
jadi sebagian selisihnya bisa saja cuma komposisi. Ternyata bukan — **gap +0,050 bertahan**
setelah magnitudonya disamakan. Plafon teoretisnya `0,0378 × 0,050 ≈ 0,0019 lb_real`.

**Hipotesis yang SALAH dan sudah dibuang:** "kliping merusak amplitudo puncak, jadi latih
CNN dengan kliping sintetis." Diukur: record clipped asli di dataset ini cuma tersaturasi
**~5 dari 3000 sampel** (fraksi |a| ≥ 0,98·max: median 0,00167 vs 0,00133 di record normal).
Setara memotong di **c ≈ 0,90** — nyaris tidak mengubah waveform. Kliping sintetis akan jadi
augmentasi kosong. Ide itu dibatalkan sebelum menghabiskan kuota GPU.

**Yang tersisa dan diuji di sini:** subgrup ini **kurang terwakili 2,25×** relatif test.
Run B menaikkan bobot sampelnya ×2,25 di loss CNN (anchor ridge sengaja TIDAK diubah,
supaya efeknya terisolasi ke CNN).

> **Peringatan jujur soal run B.** *Importance weighting* komposisi secara global (record
> depth-bulat ×2,235) sudah pernah dicoba dan **gagal** — arahnya salah. Run B bentuknya
> sama, bedanya cuma sasarannya subgrup 1,68% alih-alih 32%, dan sasaran itu punya gap
> error terukur. Peluangnya sedang, bukan tinggi. Kalau gagal, **catat dan tutup**;
> jangan dicoba lagi dalam bentuk lain.

### Yang harus diabaikan di notebook ini

Baris **"gain sisi desimal"** dicetak sebagai informasi, **bukan kriteria seleksi**. Aturan
lama "gain sisi desimal harus negatif" sudah **DICABUT**: `notebook_10` dibangun untuk
memaksimalkannya dan LB-nya rugi 0,0022 (0,1849 → 0,1871). Sisi desimal sudah menyentuh
oracle (0,1437 vs ~0,1488).

### Kalibrasi angka LB — baca sebelum bersemangat

LB publik cuma **30% data test**. Diukur dengan bootstrap: sd selisih dua submission yang
korelasinya 0,999 adalah **0,0008**; untuk submission yang beda (corr 0,888) **0,0038**.
LB terbaik 0,1849, peringkat 1 di 0,1835 — selisih **0,0014**, yaitu **0,4 sigma**.
**Kita sudah efektif seri dengan peringkat 1.** Yang menentukan peringkat akhir adalah 70%
data yang belum terlihat, jadi kandidat dipilih dari generalisasi jujur (gain holdout,
menang n/12, diagnostik transfer) — **bukan** dengan mengoptimasi ke angka LB publik.
"""


# ==================================================================== training + TTA
TTA_SRC = '''# ---------------------------------------------------------------------------------
# Grup simetri: SAMA PERSIS dengan yang dipakai augmentasi training notebook_8.
# Rotasi horizontal bekerja pada pasangan kanal (E,N) di tiap trio A/V/D -> indeks
# (0,1), (3,4), (6,7). Flip vertikal membalik kanal Z -> indeks 2, 5, 8.
#
# Urutan sengaja dibuat supaya PREFIX-nya bermakna, sehingga sapuan K bisa dilakukan
# gratis dari satu kali inferensi:
#   K=1  -> identitas saja (= tanpa TTA, dipakai sebagai kontrol)
#   K=2  -> + flip vertikal
#   K=4  -> + rotasi 180 derajat
#   K=8  -> + rotasi 90 dan 270
# ---------------------------------------------------------------------------------
SYMS = [(0.0, 1.0), (0.0, -1.0),
        (np.pi, 1.0), (np.pi, -1.0),
        (np.pi/2, 1.0), (np.pi/2, -1.0),
        (3*np.pi/2, 1.0), (3*np.pi/2, -1.0)]
K_SWEEP = [1, 2, 4, 8]

def apply_sym(x, ang, flip):
    """Terapkan satu elemen grup simetri pada batch bentuk (n, 9, T)."""
    x = x.clone()
    cs, sn = float(np.cos(ang)), float(np.sin(ang))
    if ang != 0.0:
        for k in (0, 3, 6):
            e_, n_ = x[:, k].clone(), x[:, k+1].clone()
            x[:, k] = cs*e_ - sn*n_
            x[:, k+1] = sn*e_ + cs*n_
    if flip < 0:
        for k in (2, 5, 8):
            x[:, k] = -x[:, k]
    return x

def predict_syms(net, Xt, St, bs=512):
    """Prediksi terpisah untuk TIAP elemen simetri -> array (len(SYMS), n).

    Disimpan per-elemen, bukan langsung dirata-ratakan, supaya K=1/2/4/8 bisa dibaca
    dari satu kali inferensi. Biaya tambahannya cuma inferensi, bukan training."""
    out = np.zeros((len(SYMS), len(Xt)))
    net.eval()
    with torch.no_grad():
        for j, (a, f) in enumerate(SYMS):
            acc = []
            for i in range(0, len(Xt), bs):
                acc.append(net(apply_sym(Xt[i:i+bs], a, f), St[i:i+bs])[0].cpu().numpy())
            out[j] = np.concatenate(acc)
    return out

def run_tta(Wtr, Str, Wte, Ste, sw, sw_loss=None, seeds=(0,1,2), epochs=80, bs=128,
            lr=2.5e-3, avg_last=10, tag=""):
    """`Net3` + loop training notebook_8 PERSIS, satu-satunya perubahan: saat evaluasi,
    prediksi dikumpulkan untuk tiap elemen grup simetri, bukan cuma orientasi kanonik.

    `sw`      -> bobot untuk anchor ridge (SELALU resep nb8, jangan diubah)
    `sw_loss` -> bobot untuk loss CNN (None = sama dengan `sw`)

    Memisahkan keduanya penting untuk run B: kalau anchor ikut berubah, gain/ruginya tidak
    bisa dipisahkan antara "CNN belajar lain" dan "baseline linearnya bergeser"."""
    if sw_loss is None:
        sw_loss = sw
    Xa = Ftr[A_BASE].values.astype(np.float64); Xa_te = Fte[A_BASE].values.astype(np.float64)
    dep_t = np.log10(d_tr+1).astype(np.float32); dep_ok = (~rnd_tr).astype(np.float32)
    noise = Wtr[:, :, :200].copy()
    oof_s = np.zeros((len(SYMS), len(y))); pte_s = np.zeros((len(SYMS), len(Wte)))
    Xte_t = torch.tensor(Wte).to(DEV); Ste_t = torch.tensor(Ste).to(DEV)
    nf = 0; t0 = time.time()
    for seed in seeds:
        torch.manual_seed(seed); np.random.seed(seed)
        for ti, vi in GroupKFold(5).split(Wtr, y, ev):
            # anchor ridge: target residual (trik nb5, dipakai nb8) -- pakai sw ASLI
            rg = Ridge(alpha=1.0).fit(Xa[ti], y[ti], sample_weight=sw[ti])
            tgt = (y - rg.predict(Xa)).astype(np.float32)
            off_v = rg.predict(Xa[vi]); off_t = rg.predict(Xa_te)
            net = Net3(Str.shape[1]).to(DEV)
            opt = torch.optim.AdamW(net.parameters(), lr=lr, weight_decay=2e-2)
            sch = torch.optim.lr_scheduler.OneCycleLR(
                opt, max_lr=lr, total_steps=epochs*max(1, len(ti)//bs), pct_start=0.2)
            Xt = torch.tensor(Wtr[ti]); St = torch.tensor(Str[ti]); Nz = torch.tensor(noise[ti])
            tt = torch.tensor(tgt[ti])
            wt = torch.tensor(sw_loss[ti], dtype=torch.float32)
            dt = torch.tensor(dep_t[ti]); dk = torch.tensor(dep_ok[ti])
            Xv = torch.tensor(Wtr[vi]).to(DEV); Sv = torch.tensor(Str[vi]).to(DEV)
            av = np.zeros((len(SYMS), len(vi))); at = np.zeros((len(SYMS), len(Wte)))
            for ep in range(epochs):
                net.train(); perm = torch.randperm(len(ti))
                for i in range(0, len(ti)-bs+1, bs):
                    b = perm[i:i+bs]; xb = Xt[b].clone(); sb = St[b].to(DEV)
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
                    pm, pdep = net(xb, sb)
                    wb = wt[b].to(DEV)
                    lm = (wb*(pm - tt[b].to(DEV)).abs()).sum()/wb.sum()
                    dkb = dk[b].to(DEV)
                    ld = ((pdep - dt[b].to(DEV)).abs()*dkb).sum()/(dkb.sum()+1e-6)
                    opt.zero_grad(); (lm + 0.15*ld).backward(); opt.step(); sch.step()
                if ep >= epochs - avg_last:
                    av += predict_syms(net, Xv, Sv)
                    at += predict_syms(net, Xte_t, Ste_t)
            oof_s[:, vi] += (av/avg_last + off_v[None, :])/len(seeds)
            pte_s += (at/avg_last + off_t[None, :])/(5*len(seeds))
            nf += 1
            print("    %sfold %2d/%d selesai  (%.0f menit terpakai, ~%.0f menit tersisa)"
                  % (tag, nf, 5*len(seeds), (time.time()-t0)/60,
                     (time.time()-t0)/nf*(5*len(seeds)-nf)/60), flush=True)
    return oof_s, pte_s

def tta_k(oof_s, pte_s, k):
    """Rata-rata atas K elemen simetri pertama. k=1 berarti TANPA TTA."""
    return oof_s[:k].mean(0), pte_s[:k].mean(0)
'''


SWEEP_SRC = '''def sapu_tta(oof_s, pte_s, nama):
    """Kurva TTA: apakah efeknya nyata dan apakah sudah jenuh di K=8.

    Kalau K=1 -> K=8 tidak menggerakkan angka, TTA ditutup sebagai keluarga dan tidak perlu
    dicoba lagi dengan K lebih besar. Kalau bergerak tapi belum datar di K=8, itu argumen
    untuk K=16 -- dan itu murah, karena tidak butuh training ulang."""
    rows = []
    for k in K_SWEEP:
        o, p = tta_k(oof_s, pte_s, k)
        po = post_tr(o)
        rows.append(dict(K=k, lb_real=round(lb_real(po), 4),
                         dec=round(part_real(po, True), 4),
                         rnd=round(part_real(po, False), 4),
                         bias_rnd=round(bias_rnd(po), 3),
                         mean_te=round(float(post_te(p)[MT].mean()), 3)))
    df = pd.DataFrame(rows)
    print("\\n--- kurva TTA: %s ---" % nama)
    print(df.to_string(index=False))
    d = df.lb_real.iloc[0] - df.lb_real.iloc[-1]
    print("  K=1 -> K=8 : %+.4f  %s" % (-d, "BERGERAK" if abs(d) >= 0.0008 else "datar"))
    print("  bias_rnd bergeser %+.3f  (rotasi/flip simetris -> harusnya ~0)"
          % (df.bias_rnd.iloc[-1] - df.bias_rnd.iloc[0]))
    return df
'''


def prelude(judul, deskripsi, waktu):
    cells = K.prelude_cells(
        judul, deskripsi,
        "\n**Perkiraan waktu di GPU Kaggle (T4): %s.** Notebook mencetak sisa waktu setiap "
        "fold selesai, jadi progresnya kelihatan sejak fold pertama.\n" % waktu)
    cells.insert(2, md(HEAD3))
    return cells


def nb_tta():
    cells = prelude(
        "TTA + komposisi record clipped — `Net3` notebook_8 tanpa diubah",
        "Dua sumbu yang belum pernah disentuh di repo ini, dan **tidak satu pun** masuk\n"
        "keluarga \"model deep baru\" yang sudah ditutup oleh 7 kegagalan:\n\n"
        "1. **Test-time augmentation** atas grup simetri yang sama dengan augmentasi\n"
        "   training (rotasi horizontal + flip vertikal). Mekanismenya pengurangan\n"
        "   varians. Aman terhadap diagnostik transfer **secara konstruksi**.\n"
        "2. **Bobot record `is_clipped` ×2,25** untuk menyamakan komposisi train (1,68%)\n"
        "   dengan test (3,78%). Gap MAE-nya +0,050 bahkan setelah distribusi magnitudo\n"
        "   distandarisasi.\n\n"
        "Dua kali training menghasilkan **empat kandidat** karena TTA hanya menyentuh\n"
        "inferensi, jadi tiap set bobot dievaluasi dua kali:\n\n"
        "| | tanpa TTA | dengan TTA |\n|---|---|---|\n"
        "| A: resep nb8 apa adanya | `cnn12a` (kontrol, harus ≈ 0,2091) | `cnn12a_tta` |\n"
        "| B: + bobot clipped ×2,25 | `cnn12b` | `cnn12b_tta` |\n\n"
        "Matriks 2×2-nya lengkap, jadi efek TTA dan efek bobot clipped tetap terisolasi\n"
        "meski satu notebook — justru lebih diagnostik daripada dua notebook terpisah.",
        "~3–3,5 jam (2 run × 15 fold; TTA menambah ~12 menit inferensi total)")

    cells.append(md(
        "---\n## 1. Grup simetri + loop training\n\n"
        "`Net3` dan seluruh loop training disalin **apa adanya** dari notebook_8. Satu-"
        "satunya perubahan: saat evaluasi, prediksi dikumpulkan per elemen grup simetri "
        "alih-alih hanya orientasi kanonik. Karena disimpan per-elemen, sapuan K=1/2/4/8 "
        "keluar dari satu kali inferensi tanpa training ulang."))
    cells.append(co(TTA_SRC))
    cells.append(co(SWEEP_SRC))

    cells.append(md(
        "---\n## 2. Run A — kontrol: resep notebook_8 apa adanya\n\n"
        "**Ini uji kewarasan lingkungan, bukan cuma baseline.** Resepnya identik `cnn3` "
        "(3 seed, 80 epoch, `sw = w(M)/sqrt(cnt)`), jadi `lb_real` di K=1 harus mendarat "
        "di **~0,1898**. Kalau tidak, ada yang beda di Kaggle dan **seluruh verdikt "
        "notebook ini tidak bisa dipercaya** — hentikan dan periksa dulu.\n\n"
        "> **Konstanta ini pernah salah dan memakan satu run penuh (160 menit GPU).**\n"
        "> Versi pertama memakai **0,2091**, yaitu `lb_real` cnn3 **MENTAH**. Tapi\n"
        "> `sapu_tta()` menghitung `lb_real(post_tr(o))` — sudah lewat post-processing.\n"
        "> Post memangkas ~0,019, jadi gerbangnya membandingkan angka post terhadap angka\n"
        "> mentah dan melaporkan \"gain\" 0,0144 yang sepenuhnya artefak. Angka post yang\n"
        "> benar: cnn3 **0,1898**, cnn3_avg **0,1888** (lihat\n"
        "> `experiments/exp50_kontrol_nb12.py`). **Setiap konstanta pembanding di notebook\n"
        "> Kaggle wajib dicek jenisnya — mentah atau post — sebelum dipasang.**"))
    cells.append(co(
        'sw = make_sw(power=0.5)\n'
        't0 = time.time()\n'
        'oofA_s, pteA_s = run_tta(Wtr, Str, Wte, Ste, sw, tag="A ")\n'
        'np.savez(catat(OUT/"cnn12a_syms.npz"), oof_s=oofA_s, pte_s=pteA_s)\n'
        'print("\\nrun A selesai %.0f menit"%((time.time()-t0)/60))\n'
        '\n'
        'dfA = sapu_tta(oofA_s, pteA_s, "A = resep nb8")\n'
        'base = dfA.lb_real.iloc[0]\n'
        '# KONTROL_POST = lb_real cnn3 SETELAH post_tr. JANGAN ganti dengan 0,2091 --\n'
        '# angka itu lb_real MENTAH, dan sapu_tta() melaporkan angka post.\n'
        'KONTROL_POST = 0.1898\n'
        'print("\\nKONTROL: K=1 lb_real %.4f   (cnn3 lokal, SETELAH post = %.4f)"\n'
        '      %(base, KONTROL_POST))\n'
        'print("  " + ("COCOK -- lingkungan Kaggle mereproduksi run lokal."\n'
        '              if abs(base-KONTROL_POST) < 0.004 else\n'
        '              "TIDAK COCOK -- selisih %+.4f. Verdikt blend di bawah membandingkan\\n'
        '  kandidat Kaggle dengan kandidat LOKAL, jadi selisih ini masuk sebagai kerugian\\n'
        '  ide. Baca verdiktnya sebagai batas bawah, dan serap hasilnya lewat\\n'
        '  tools/serap_nb12.py yang menetralkan gap ini."%(base-KONTROL_POST)))\n'))

    cells.append(md(
        "---\n## 3. Run B — bobot record `is_clipped` ×2,25\n\n"
        "`sw_loss` dinaikkan ×2,25 khusus record clipped supaya bobot efektifnya di loss "
        "CNN sepadan dengan porsinya di test (1,68% → 3,78%). **Anchor ridge tetap memakai "
        "`sw` asli** — kalau anchor ikut bergeser, gain/ruginya tidak bisa dipisahkan "
        "antara \"CNN belajar lain\" dan \"baseline linearnya bergeser\".\n\n"
        "> Ingat peringatannya: *importance weighting* komposisi global (depth-bulat "
        "×2,235) sudah pernah gagal. Bedanya di sini sasarannya subgrup 1,68% dengan gap "
        "error terukur, bukan 32% populasi. Kalau gagal juga, **tutup keluarga ini**."))
    cells.append(co(
        'clip_tr = train.is_clipped.values.astype(bool)\n'
        'clip_te = test.is_clipped.values.astype(bool)\n'
        'rasio = clip_te.mean()/clip_tr.mean()\n'
        'print("clipped: train %.2f%% (n=%d) | test %.2f%% (n=%d) | rasio %.2fx"\n'
        '      %(clip_tr.mean()*100, clip_tr.sum(), clip_te.mean()*100, clip_te.sum(), rasio))\n'
        'sw_b = sw.copy(); sw_b[clip_tr] *= rasio\n'
        'print("bobot loss CNN: record clipped x%.2f  (anchor ridge TIDAK diubah)"%rasio)\n'
        '\n'
        't0 = time.time()\n'
        'oofB_s, pteB_s = run_tta(Wtr, Str, Wte, Ste, sw, sw_loss=sw_b, tag="B ")\n'
        'np.savez(catat(OUT/"cnn12b_syms.npz"), oof_s=oofB_s, pte_s=pteB_s)\n'
        'print("\\nrun B selesai %.0f menit"%((time.time()-t0)/60))\n'
        '\n'
        'dfB = sapu_tta(oofB_s, pteB_s, "B = + bobot clipped")\n'))

    cells.append(md(
        "---\n## 4. Matriks 2×2 + MAE khusus record clipped\n\n"
        "Dua pertanyaan terpisah, dan keduanya harus dijawab dari sini:\n\n"
        "- **Apakah TTA menolong?** Bandingkan kolom (K=1 vs K=8) di dalam tiap baris.\n"
        "- **Apakah bobot clipped menolong?** Bandingkan baris A vs B — dan yang paling "
        "  menentukan, lihat **MAE khusus record clipped**. Kalau run B tidak memperbaiki "
        "  angka itu, ia gagal pada mekanismenya sendiri dan `lb_real` yang kebetulan "
        "  membaik cuma derau."))
    cells.append(co(
        'kand = {}\n'
        'rows = []\n'
        'for nm, (o_s, p_s) in [("A", (oofA_s, pteA_s)), ("B", (oofB_s, pteB_s))]:\n'
        '    for k, lbl in [(1, ""), (8, "_tta")]:\n'
        '        o, p = tta_k(o_s, p_s, k)\n'
        '        key = "cnn12%s%s" % (nm.lower(), lbl)\n'
        '        kand[key] = (o, p)\n'
        '        po = post_tr(o)\n'
        '        e = np.abs(o - y)\n'
        '        rows.append(dict(kandidat=key, K=k,\n'
        '                         lb_real=round(lb_real(po), 4),\n'
        '                         dec=round(part_real(po, True), 4),\n'
        '                         rnd=round(part_real(po, False), 4),\n'
        '                         bias_rnd=round(bias_rnd(po), 3),\n'
        '                         MAE_clip=round(float(e[clip_tr].mean()), 4),\n'
        '                         MAE_non=round(float(e[~clip_tr].mean()), 4)))\n'
        'dfM = pd.DataFrame(rows)\n'
        'print(dfM.to_string(index=False))\n'
        'print("\\npembanding notebook_8: cnn3_avg 0,2074 | cnn3_dir 0,2116 | LightGBM terbaik 0,2030")\n'
        'print("MAE clipped pada blend nb8 (bukan CNN tunggal): 0,1990 vs non-clipped 0,1338")\n'
        '\n'
        'gA = dfM[dfM.kandidat=="cnn12a"].lb_real.iloc[0] - dfM[dfM.kandidat=="cnn12a_tta"].lb_real.iloc[0]\n'
        'gB = dfM[dfM.kandidat=="cnn12b"].lb_real.iloc[0] - dfM[dfM.kandidat=="cnn12b_tta"].lb_real.iloc[0]\n'
        'gC = dfM[dfM.kandidat=="cnn12a"].lb_real.iloc[0] - dfM[dfM.kandidat=="cnn12b"].lb_real.iloc[0]\n'
        'dC = dfM[dfM.kandidat=="cnn12a"].MAE_clip.iloc[0] - dfM[dfM.kandidat=="cnn12b"].MAE_clip.iloc[0]\n'
        'print("\\n--- efek terisolasi (positif = membaik) ---")\n'
        'print("  TTA di run A            %+.4f"%gA)\n'
        'print("  TTA di run B            %+.4f"%gB)\n'
        'print("  bobot clipped (K=1)     %+.4f"%gC)\n'
        'print("  bobot clipped: MAE record clipped %+.4f  <- mekanismenya sendiri"%dC)\n'
        'if dC <= 0:\n'
        '    print("  RUN B GAGAL PADA MEKANISMENYA. MAE record clipped tidak membaik, jadi")\n'
        '    print("  perubahan lb_real apa pun di run B adalah derau. Tutup keluarga ini.")\n'))

    cells.append(md(
        "---\n## 5. Blend — dua protokol, dan yang kedua yang lebih tepat\n\n"
        "Semua batch sebelumnya cuma **menambahkan** kandidat ke-9 ke blend nb8. Untuk "
        "kandidat di sini itu protokol yang salah bentuknya: `cnn12a_tta` bukan model baru "
        "melainkan **versi lebih baik dari `cnn3_avg` yang sudah ada di dalam blend**. "
        "Menambahkannya sebagai kandidat ke-9 berarti blend memegang dua salinan model "
        "yang sama dengan korelasi ~0,99 — persis situasi yang membuat pencarian bobot "
        "menipu diri sendiri.\n\n"
        "Jadi diuji dua-duanya:\n\n"
        "- **tambah** — kandidat ke-9, seperti batch sebelumnya (untuk kesebandingan).\n"
        "- **ganti** — `cnn3_avg` dikeluarkan, kandidat baru masuk menggantikannya. "
        "  Jumlah kandidat tetap 8, jadi tidak ada inflasi dari menambah derajat bebas.\n\n"
        "Kriterianya tetap sama dan tidak dilonggarkan: **gain holdout negatif DAN menang "
        "≥ 7/12 belahan DAN ketiga diagnostik transfer aman DAN `lb_real` < 0,1762.**"))
    cells.append(co(
        'def uji(key, mode):\n'
        '    """mode="tambah" -> kandidat ke-9 | mode="ganti" -> gantikan cnn3_avg."""\n'
        '    o, p = kand[key]\n'
        '    if mode == "ganti":\n'
        '        keep = [i for i, n in enumerate(CAND) if n != "cnn3_avg"]\n'
        '        names = [CAND[i] for i in keep] + [key]\n'
        '        Otr = np.vstack([Oref[keep], o[None, :]])\n'
        '        Ote = np.vstack([Eref[keep], p[None, :]])\n'
        '    else:\n'
        '        names = CAND + [key]\n'
        '        Otr = np.vstack([Oref, o[None, :]])\n'
        '        Ote = np.vstack([Eref, p[None, :]])\n'
        '    r = blend_search(names, Otr, Ote, ref_oof)\n'
        '    r["_nama"] = "%s (%s)" % (key, mode)\n'
        '    r["_names"] = names\n'
        '    return r\n'
        '\n'
        'if REF is None:\n'
        '    print("nb8_ref.npz tidak ditemukan -- verdikt blend dilewati.")\n'
        '    hasil = []\n'
        'else:\n'
        '    Oref, Eref = ref_stack()\n'
        '    ref_oof = post_tr(REF["__w__"] @ Oref)\n'
        '    print("acuan notebook_8: lb_real=%.4f   [LB aktual 0,1849]\\n"%sc(ref_oof))\n'
        '    hasil = []\n'
        '    for key in ["cnn12a_tta", "cnn12b_tta", "cnn12b"]:\n'
        '        for mode in ["tambah", "ganti"]:\n'
        '            r = uji(key, mode)\n'
        '            hasil.append(r)\n'
        '            print("%-24s lb_real %.4f  jujur %.4f  gain %+.5f  menang %2d/12  bias %+.3f"\n'
        '                  %(r["_nama"], r["lb_real"], r["jujur"], r["gain"], r["menang"], r["bias"]))\n'))

    cells.append(md(
        "---\n## 6. Verdikt\n\n"
        "Kandidat terbaik dipilih dari **gain holdout jujur**, bukan `lb_real` mentah — "
        "kandidat ke-N selalu bisa menurunkan angka di data tempat bobotnya dipilih "
        "(CNN+GRU menurunkan 0,1762 → 0,1756 tapi menang 1/12, dan menolaknya benar)."))
    cells.append(co(
        'if hasil:\n'
        '    best = min(hasil, key=lambda r: r["gain"])\n'
        '    print("kandidat terbaik menurut gain holdout: %s\\n"%best["_nama"])\n'
        '    print("bobot:", dict(zip(best["_names"], np.round(best["w"], 3))))\n'
        '    print("bobot model baru: %.3f\\n"%best["w"][-1])\n'
        '    est = verdikt(best, best["_nama"])\n'
        '    simpan("blend_cnn12", best["oof"], best["pte"], best)\n'
        '    lolos = (best["gain"] < 0 and best["menang"] >= 7 and best["bias"] <= 0.05\n'
        '             and best["lb_real"] < LB_JUARA)\n'
        '    print()\n'
        '    print("LOLOS PROTOKOL -- layak jadi kandidat submission." if lolos else\n'
        '          "TIDAK LOLOS -- notebook_8 tetap submission terbaik. Catat kegagalannya\\n'
        '  di sudah_run/README.md beserta ALASANNYA; yang gagal justru yang paling sering\\n'
        '  dicoba ulang kalau tidak dicatat.")\n'
        '    print()\n'
        '    print("Ingat: hanya ADA SATU submission final. Selisih ke peringkat 1 (0,0014)")\n'
        '    print("ada di dalam derau LB publik (sd selisih ~0,004 untuk model berbeda),")\n'
        '    print("jadi kandidat yang cuma menang tipis di lb_real BUKAN alasan cukup untuk")\n'
        '    print("menggeser notebook_8. Ambangnya harus gain holdout jujur, bukan angka LB.")\n'))

    cells.append(md(
        "---\n## 7. Simpan kandidat + bungkus jadi satu zip\n\n"
        "Keempat kandidat disimpan supaya blend gabungan bisa diuji ulang di lokal — "
        "pertanyaan yang tidak bisa dijawab notebook ini sendirian."))
    cells.append(co(
        'for key, (o, p) in kand.items():\n'
        '    simpan(key, o, p)\n'
        'bundel("hasil_cnn12_tta")\n'))
    return nb(cells)


# ---------------------------------------------------------------- tulis
files = {"09_tta_klip.ipynb": nb_tta()}
for nama, obj in files.items():
    (OUT / nama).write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")
    print("tertulis:", OUT / nama)
