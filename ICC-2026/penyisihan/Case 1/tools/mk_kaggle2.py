# -*- coding: utf-8 -*-
"""Generator batch Kaggle ke-2 (sesudah LB notebook_9 = 0,1856).

Batch pertama menutup keluarga "arsitektur CNN 1D baru atas waveform yang sama" (4 dari 5
gagal karena redundan, korelasi 0,92-0,96 terhadap `cnn3_avg`) dan set-transformer terbukti
gagal di LB. Yang tersisa hanyalah membuat model deep **lebih akurat per-record** — bukan
arsitektur baru, bukan post-processing, bukan grouping.

Tiga notebook di sini semuanya menyerang sumbu itu, dan semuanya lewat diagnostik ke-4
(uji sisi-desimal) yang ditambahkan ke `verdikt()` setelah kegagalan nb9.

Jalankan:  python "Case 1/tools/mk_kaggle2.py"
"""
import _path  # noqa: F401
import json
import mk_kaggle as K

OUT = _path.ROOT / "belum_run"
OUT.mkdir(exist_ok=True)

md, co, nb = K.md, K.co, K.nb

HEAD2 = """
---

## Kenapa batch ini ada: pelajaran dari `notebook_9` (LB 0,1856, GAGAL)

`notebook_9` memperbaiki `lb_real` **−0,0044**, menang **12/12** belahan holdout, dan
ketiga diagnostik transfer lama semuanya aman. LB-nya tetap **memburuk** (0,1849 → 0,1856).

Sebabnya: **`lb_real` memperbaiki BOBOT metrik, bukan LABEL-nya.** `make_ev_real` memecah
pseudo-event raksasa supaya bobot per-event realistis, tapi `y` tetap identik untuk semua
record yang berbagi `(depth, magnitude)`. Di train, **24% pasangan** di dalam satu grup
depth bulat punya label identik — jadi metode apa pun yang **menyeragamkan prediksi di
dalam grup depth** mendapat gain gratis yang tidak ada di LB.

Buktinya paling terang di pemecahan per sisi:

| sisi | pseudo-event | nb8 | nb9 |
|---|---|---|---|
| desimal | **event nyata** (98% murni) | 0,1437 | 0,1443 ❌ rugi |
| bulat | artefak katalog | 0,2074 | 0,1982 |

Seluruh gain ada di satu-satunya sisi yang labelnya tidak bisa dipercaya.

### Konsekuensi untuk notebook di batch ini

1. **Diagnostik ke-4 sekarang wajib** dan sudah dipasang di `verdikt()`: **gain di sisi
   desimal harus negatif juga.** Kandidat yang cuma menang di sisi bulat DITOLAK.
2. **Jangan ajukan ide yang mekanismenya "rapatkan prediksi dalam grup"** — smoothing,
   attention antar-record, agregasi grup, pooling posterior. Keluarga itu tertutup.
3. Yang tersisa: **akurasi per-record**. Ketiga notebook di sini semuanya ke sana.
4. Ambang `bias_rnd` diturunkan 0,08 → **0,05** (nb5 rugi di LB pada +0,056).
5. `LB ≈ lb_real + 0,0096`, tapi offset 4 titik itu **tidak stabil** (sd 0,0036). Pakai
   untuk memeringkat, jangan untuk menjanjikan angka.
"""


def prelude(judul, deskripsi, waktu):
    cells = K.prelude_cells(
        judul, deskripsi,
        "\n**Perkiraan waktu di GPU Kaggle (T4): %s.** Notebook mencetak sisa waktu setiap "
        "fold selesai, jadi progresnya kelihatan sejak fold pertama.\n" % waktu)
    cells.insert(2, md(HEAD2))
    return cells


def blend_cell(key, judul_blend):
    return co(
        'if REF is None:\n'
        '    print("nb8_ref.npz tidak ditemukan -- verdikt blend dilewati.")\n'
        'else:\n'
        '    Oref, Eref = ref_stack()\n'
        '    ref_oof = post_tr(REF["__w__"] @ Oref)\n'
        '    print("acuan notebook_8: lb_real=%%.4f   [LB aktual 0,1849]"%%sc(ref_oof))\n'
        '    names = CAND + ["%s"]\n'
        '    Otr = np.vstack([Oref, oof[None,:]]); Ote = np.vstack([Eref, pte[None,:]])\n'
        '    res = blend_search(names, Otr, Ote, ref_oof)\n'
        '    print("\\nbobot:", dict(zip(names, np.round(res["w"],3))))\n'
        '    print("bobot model baru: %%.3f\\n"%%res["w"][-1])\n'
        '    est = verdikt(res, "%s")\n'
        '    simpan("blend_%s", res["oof"], res["pte"], res)\n' % (key, judul_blend, key))


def lapor_cell(key, pembanding):
    return co(
        'simpan("%s", oof, pte)\n'
        'print("\\n%s selesai dalam %%.0f menit"%%((time.time()-t0)/60))\n'
        'print("  lb_real  %%.4f"%%lb_real(oof))\n'
        'print("  dec %%.4f   rnd %%.4f   bias_rnd %%+.3f"\n'
        '      %%(part_real(oof,True), part_real(oof,False), bias_rnd(oof)))\n'
        'print("\\npembanding model TUNGGAL: %s")\n'
        'if REF is not None:\n'
        '    print()\n'
        '    for n in CAND:\n'
        '        print("  korelasi vs %%-10s %%.3f"%%(n, np.corrcoef(oof, REF[n+"__oof"])[0,1]))\n'
        '    print("\\nKorelasi RENDAH lebih berharga daripada skor tunggal yang bagus.")\n'
        % (key, key, pembanding))


# ==================================================================== 06 augmentasi
AUG_SRC = '''def run_aug(Wtr,Str,Wte,Ste, sw, seeds=(0,1,2), epochs=110, bs=128, lr=2.5e-3,
            avg_last=12, p_jit=0.7, p_drop=0.3, p_cut=0.4, p_scale=0.6, mixup=0.3):
    """CNN v3 persis notebook_8, HANYA augmentasinya yang berubah.

    notebook_8 memakai tiga augmentasi: rotasi horizontal, flip vertikal, tempel derau
    pre-P. Lima yang ditambahkan di sini, semuanya dipilih karena meniru ragam FISIK yang
    memang ada antar-stasiun, bukan sekadar derau acak:

    1. `p_jit`  -- geser jendela +-40 sampel (0,2 s) di sekitar P. Waktu tiba P di dataset
       ini adalah hasil PICKER, dan picker punya galat. Model sekarang boleh mengandalkan
       P jatuh tepat di indeks 200; di test galat picker menggesernya.
    2. `p_drop` -- matikan satu komponen (E/N/Z) secara acak. Memaksa jaringan tidak
       bergantung pada satu kanal, dan meniru stasiun berkomponen cacat.
    3. `p_cut`  -- cutout: nolkan satu potongan waktu 20-80 sampel. Meniru dropout telemetri.
    4. `p_scale`-- jitter skala amplitudo: kalikan waveform dengan `s` DAN geser skalar
       `log10(peak)` sebesar `log10(s)`. Ini yang paling penting dan paling halus: input
       CNN gaya MagNet memisahkan BENTUK (dinormalisasi) dari SKALA (skalar). Menjitter
       keduanya secara konsisten mengajarkan hubungan bentuk-skala yang benar tanpa
       merusak informasi amplitudo absolut -- prediktor fisik utama magnitudo.
    5. `mixup`  -- interpolasi pasangan record beserta targetnya. Dengan hanya ~905 event
       efektif, ini regularizer yang murah.

    Jadwal ikut dipanjangkan 80 -> 110 epoch: augmentasi lebih berat butuh waktu lebih
    lama untuk konvergen, dan menaikkannya tanpa memanjangkan jadwal akan terbaca sebagai
    "augmentasi tidak menolong" padahal yang terjadi underfit."""
    Xa=Ftr[A_BASE].values.astype(np.float64); Xa_te=Fte[A_BASE].values.astype(np.float64)
    dep_t=np.log10(d_tr+1).astype(np.float32); dep_ok=(~rnd_tr).astype(np.float32)
    noise=Wtr[:,:,:200].copy()
    PAD=48                                   # ruang untuk time-jitter
    oof=np.zeros(len(y)); pte=np.zeros(len(Wte))
    Xte_t=torch.tensor(Wte).to(DEV); Ste_t=torch.tensor(Ste).to(DEV)
    nf=0; t0=time.time()
    for seed in seeds:
        torch.manual_seed(seed); np.random.seed(seed)
        for ti,vi in GroupKFold(5).split(Wtr,y,ev):
            rg=Ridge(alpha=1.0).fit(Xa[ti],y[ti],sample_weight=sw[ti])
            tgt=(y-rg.predict(Xa)).astype(np.float32)
            off_v=rg.predict(Xa[vi]); off_t=rg.predict(Xa_te)
            net=Net3(Str.shape[1]).to(DEV)
            opt=torch.optim.AdamW(net.parameters(),lr=lr,weight_decay=2e-2)
            sch=torch.optim.lr_scheduler.OneCycleLR(opt,max_lr=lr,
                    total_steps=epochs*max(1,len(ti)//bs),pct_start=0.2)
            Xt=torch.tensor(np.pad(Wtr[ti],((0,0),(0,0),(PAD,PAD))))
            St=torch.tensor(Str[ti]); Nz=torch.tensor(noise[ti])
            tt=torch.tensor(tgt[ti]); wt=torch.tensor(sw[ti],dtype=torch.float32)
            dt=torch.tensor(dep_t[ti]); dk=torch.tensor(dep_ok[ti])
            Xv=torch.tensor(Wtr[vi]).to(DEV); Sv=torch.tensor(Str[vi]).to(DEV)
            L=Wtr.shape[2]
            av=np.zeros(len(vi)); at=np.zeros(len(Wte))
            for ep in range(epochs):
                net.train(); perm=torch.randperm(len(ti))
                for i in range(0,len(ti)-bs+1,bs):
                    b=perm[i:i+bs]; nb_=len(b)
                    # --- time-jitter: potong jendela panjang L dari yang sudah di-pad ---
                    if torch.rand(1).item()<p_jit:
                        sh=torch.randint(PAD-40,PAD+41,(1,)).item()
                    else:
                        sh=PAD
                    xb=Xt[b][:,:,sh:sh+L].clone()
                    sb=St[b].clone()
                    # --- rotasi horizontal (nb8) ---
                    th=torch.rand(nb_)*2*np.pi; cs,sn=torch.cos(th),torch.sin(th)
                    for k in (0,3,6):
                        e_,n_=xb[:,k].clone(),xb[:,k+1].clone()
                        xb[:,k]=cs[:,None]*e_-sn[:,None]*n_; xb[:,k+1]=sn[:,None]*e_+cs[:,None]*n_
                    # --- flip vertikal (nb8) ---
                    if torch.rand(1).item()<0.5:
                        for k in (2,5,8): xb[:,k]*=-1
                    # --- tempel derau pre-P (nb8) ---
                    if torch.rand(1).item()<0.5:
                        j=torch.randint(0,len(ti),(nb_,))
                        amp=(torch.rand(nb_,1,1)*0.6)
                        xb=xb+amp*Nz[j].repeat(1,1,5)[:,:,:L]
                    # --- BARU: channel dropout ---
                    if torch.rand(1).item()<p_drop:
                        c=torch.randint(0,3,(1,)).item()
                        for k in (c,c+3,c+6): xb[:,k]=0
                    # --- BARU: cutout ---
                    if torch.rand(1).item()<p_cut:
                        w_=torch.randint(20,81,(1,)).item()
                        st=torch.randint(0,L-w_,(1,)).item()
                        xb[:,:,st:st+w_]=0
                    # --- BARU: jitter skala, BENTUK dan SKALAR digeser bersama ---
                    if torch.rand(1).item()<p_scale:
                        lg=(torch.rand(nb_,1)*0.5-0.25)          # +-0,25 dekade
                        sb[:,0:3]=sb[:,0:3]+lg                   # tiga skalar log10(peak)
                    tb=tt[b].clone(); wb=wt[b].clone()
                    db=dt[b].clone(); dkb=dk[b].clone()
                    # --- BARU: mixup ---
                    if mixup>0 and torch.rand(1).item()<0.5:
                        lam=float(np.random.beta(mixup,mixup))
                        pm_=torch.randperm(nb_)
                        xb=lam*xb+(1-lam)*xb[pm_]; sb=lam*sb+(1-lam)*sb[pm_]
                        tb=lam*tb+(1-lam)*tb[pm_]
                        db=lam*db+(1-lam)*db[pm_]; dkb=torch.minimum(dkb,dkb[pm_])
                    xb=xb.to(DEV); sb=sb.to(DEV)
                    pm,pdep=net(xb,sb)
                    wbd=wb.to(DEV)
                    lm=(wbd*(pm-tb.to(DEV)).abs()).sum()/wbd.sum()
                    dkd=dkb.to(DEV)
                    ld=((pdep-db.to(DEV)).abs()*dkd).sum()/(dkd.sum()+1e-6)
                    opt.zero_grad(); (lm+0.15*ld).backward(); opt.step(); sch.step()
                if ep>=epochs-avg_last:
                    net.eval()
                    with torch.no_grad():
                        av+=net(Xv,Sv)[0].cpu().numpy()
                        at+=np.concatenate([net(Xte_t[i:i+512],Ste_t[i:i+512])[0].cpu().numpy()
                                            for i in range(0,len(Wte),512)])
            oof[vi]+=(av/avg_last+off_v)/len(seeds)
            pte+=(at/avg_last+off_t)/(5*len(seeds))
            nf+=1
            print("    fold %2d/%d selesai  (%.0f menit terpakai, ~%.0f menit tersisa)"
                  %(nf,5*len(seeds),(time.time()-t0)/60,
                    (time.time()-t0)/nf*(5*len(seeds)-nf)/60), flush=True)
    return oof,pte
'''


def nb_aug():
    cells = prelude(
        "kaggle 06 — Augmentasi agresif untuk CNN v3",
        "Notebook **paling murah dan paling mungkin berhasil** di batch ini, jadi "
        "jalankan duluan kalau kuota GPU terbatas.\n\n"
        "CNN v3 (`notebook_8`, LB 0,1849) memakai tiga augmentasi saja: rotasi horizontal, "
        "flip vertikal, dan tempel derau pre-P. Yang ketiga adalah bagian dari terobosan "
        "−0,0084 di nb8, jadi keluarga ini sudah **terbukti membayar di case ini** — tapi "
        "belum pernah digarap sampai habis.\n\n"
        "Dengan hanya **~905 event efektif** (bukan 10.505 record), regularisasi lewat "
        "augmentasi adalah salah satu dari sedikit cara menambah data efektif tanpa "
        "menyentuh grouping. Dan tidak seperti set-transformer, mekanismenya **murni "
        "per-record** — jadi ia tidak bisa gagal lewat jalur nb9.",
        "~130 menit")
    cells.append(md(
        "---\n## 1. Lima augmentasi baru\n\n"
        "Arsitektur, target residual, kepala kedua kedalaman, jumlah seed, dan bobot "
        "sample **tidak diubah sama sekali** dari `notebook_8`. Yang berubah hanya isi "
        "loop augmentasi — supaya kalau hasilnya bergerak, penyebabnya tidak ambigu.\n\n"
        "| augmentasi | p | apa yang ditiru |\n|---|---|---|\n"
        "| time-jitter ±40 sampel | 0,70 | galat picker P — dataset ini P-nya hasil "
        "picker, dan model sekarang boleh mengandalkan P jatuh tepat di indeks 200 |\n"
        "| channel dropout | 0,30 | stasiun berkomponen cacat |\n"
        "| cutout 20–80 sampel | 0,40 | dropout telemetri |\n"
        "| jitter skala konsisten | 0,60 | ragam kopling situs–instrumen |\n"
        "| mixup | 0,30 | regularizer untuk 905 event efektif |\n\n"
        "**Yang paling halus adalah jitter skala.** Input CNN gaya MagNet memisahkan "
        "BENTUK gelombang (dinormalisasi per-record) dari SKALA (`log10(peak)` sebagai "
        "skalar). Menjitter keduanya **bersama-sama** — kalikan waveform dengan `s`, geser "
        "skalarnya `log10(s)` — mengajarkan hubungan bentuk↔skala yang benar **tanpa** "
        "merusak amplitudo absolut, yang merupakan prediktor fisik utama magnitudo. "
        "Menjitter salah satunya saja akan merusak sinyal itu.\n\n"
        "Jadwal dipanjangkan **80 → 110 epoch**. Ini bukan detail: augmentasi lebih berat "
        "butuh konvergensi lebih lama, dan menaikkannya tanpa memanjangkan jadwal akan "
        "terbaca sebagai *\"augmentasi tidak menolong\"* padahal yang terjadi underfit. "
        "Pola itu sudah dua kali menipu di repo ini (CNN v3 di nb7, set-transformer di "
        "nb8→nb9)."))
    cells.append(co(AUG_SRC))
    cells.append(md("---\n## 2. Training\n\n15 fold (3 seed × 5 GroupKFold berbasis event)."))
    cells.append(co('sw = make_sw(power=0.5)\nt0 = time.time()\n'
                    'oof, pte = run_aug(Wtr, Str, Wte, Ste, sw, seeds=(0,1,2), epochs=110)\n'))
    cells.append(lapor_cell("cnn9_aug", "cnn3_avg 0,2074 | cnn3_dir 0,2116 | LightGBM terbaik 0,2030"))
    cells.append(md(
        "---\n## 3. Blend + verdikt\n\nPerhatikan **diagnostik ke-4 (gain sisi desimal)**. "
        "Kalau ia positif, tolak kandidatnya berapa pun bagus `lb_real`-nya — itu persis "
        "cara `notebook_9` lolos semua uji lama lalu rugi di LB."))
    cells.append(blend_cell("cnn9_aug", "notebook_8 + CNN v3 augmentasi agresif"))
    cells.append(md("---\n## 4. Bungkus hasil jadi satu zip"))
    cells.append(co('bundel("hasil_cnn9_aug")\n'))
    return nb(cells)


# ==================================================================== 07 SSL
SSL_SRC = '''class Encoder(nn.Module):
    """Badan Net3 tanpa kepala -- supaya bobotnya bisa dipindahkan utuh setelah pra-latih."""
    def __init__(s, w=64):
        super().__init__()
        s.body=nn.Sequential(Blk(9,w),Blk(w,w*2),Blk(w*2,w*3),Blk(w*3,w*4,k=5,pool=2),
                             Blk(w*4,w*4,k=3,pool=2))
    def forward(s,x): return s.body(x)

class MAE(nn.Module):
    """Masked autoencoder 1D: sebagian jendela waktu dinolkan, jaringan merekonstruksinya.

    Dekodernya sengaja RINGAN (dua conv transpose + conv). Kalau dekoder terlalu kuat ia
    yang mengerjakan rekonstruksi dan encoder-nya tidak dipaksa belajar apa-apa."""
    def __init__(s, w=64):
        super().__init__()
        s.enc=Encoder(w)
        s.dec=nn.Sequential(
            nn.ConvTranspose1d(w*4,w*2,8,stride=8), nn.SiLU(),
            nn.ConvTranspose1d(w*2,w,8,stride=8), nn.SiLU(),
            nn.Conv1d(w,9,5,padding=2))
    def forward(s,x):
        h=s.enc(x)
        r=s.dec(h)
        if r.shape[-1]!=x.shape[-1]:
            r=nn.functional.interpolate(r,size=x.shape[-1],mode="linear",align_corners=False)
        return r

def pretrain(Wall, epochs=60, bs=192, lr=2e-3, mask_frac=0.35, seg=50, seed=0):
    """Pra-latih encoder di SELURUH waveform train+test (12.805), tanpa label.

    Ini transduktif dan sah: waveform test memang tersedia, dan tidak ada label yang
    disentuh. Ini satu-satunya cara menambah data efektif di case ini -- ukuran sampel
    efektif untuk supervised learning adalah ~905 EVENT, bukan 10.505 record, dan itulah
    yang membatasi kapasitas model sejak awal. Untuk rekonstruksi, tiap record berdiri
    sendiri, jadi ukuran sampel efektifnya benar-benar 12.805."""
    torch.manual_seed(seed); np.random.seed(seed)
    net=MAE().to(DEV)
    opt=torch.optim.AdamW(net.parameters(),lr=lr,weight_decay=1e-2)
    n=len(Wall); L=Wall.shape[2]
    sch=torch.optim.lr_scheduler.OneCycleLR(opt,max_lr=lr,
            total_steps=epochs*max(1,n//bs),pct_start=0.15)
    X=torch.tensor(Wall)
    t0=time.time()
    for ep in range(epochs):
        net.train(); perm=torch.randperm(n); tot=0.0; nb_=0
        for i in range(0,n-bs+1,bs):
            b=perm[i:i+bs]; xb=X[b].to(DEV)
            m=torch.ones_like(xb[:,:1,:])
            nseg=int(mask_frac*L/seg)
            for _ in range(nseg):
                st=torch.randint(0,L-seg,(1,)).item()
                m[:,:,st:st+seg]=0
            xin=xb*m
            r=net(xin)
            # rugi HANYA di bagian yang ditutup -- kalau tidak, jaringan cukup menyalin
            loss=((r-xb).abs()*(1-m)).sum()/((1-m).sum()*9+1e-6)
            opt.zero_grad(); loss.backward(); opt.step(); sch.step()
            tot+=loss.item(); nb_+=1
        if ep%10==0 or ep==epochs-1:
            print("    pretrain ep %3d/%d  loss %.5f  (%.0f menit)"
                  %(ep,epochs,tot/max(nb_,1),(time.time()-t0)/60), flush=True)
    return net.enc.state_dict()

def run_ssl(Wtr,Str,Wte,Ste, sw, enc_sd, seeds=(0,1,2), epochs=80, bs=128, lr=2.5e-3,
            avg_last=10, lr_enc_mult=0.3):
    """CNN v3 persis notebook_8, HANYA bobot awal badannya yang berasal dari pra-latih.

    `lr_enc_mult` menurunkan learning rate badan yang sudah terlatih supaya fine-tuning
    tidak langsung menghapus apa yang dipelajari (discriminative fine-tuning)."""
    Xa=Ftr[A_BASE].values.astype(np.float64); Xa_te=Fte[A_BASE].values.astype(np.float64)
    dep_t=np.log10(d_tr+1).astype(np.float32); dep_ok=(~rnd_tr).astype(np.float32)
    noise=Wtr[:,:,:200].copy()
    oof=np.zeros(len(y)); pte=np.zeros(len(Wte))
    Xte_t=torch.tensor(Wte).to(DEV); Ste_t=torch.tensor(Ste).to(DEV)
    nf=0; t0=time.time()
    for seed in seeds:
        torch.manual_seed(seed); np.random.seed(seed)
        for ti,vi in GroupKFold(5).split(Wtr,y,ev):
            rg=Ridge(alpha=1.0).fit(Xa[ti],y[ti],sample_weight=sw[ti])
            tgt=(y-rg.predict(Xa)).astype(np.float32)
            off_v=rg.predict(Xa[vi]); off_t=rg.predict(Xa_te)
            net=Net3(Str.shape[1]).to(DEV)
            net.body.load_state_dict(enc_sd)                     # <-- transfer
            head=[p for n_,p in net.named_parameters() if not n_.startswith("body")]
            body=[p for n_,p in net.named_parameters() if n_.startswith("body")]
            opt=torch.optim.AdamW([{"params":body,"lr":lr*lr_enc_mult},
                                   {"params":head,"lr":lr}],weight_decay=2e-2)
            sch=torch.optim.lr_scheduler.OneCycleLR(opt,
                    max_lr=[lr*lr_enc_mult,lr],
                    total_steps=epochs*max(1,len(ti)//bs),pct_start=0.2)
            Xt=torch.tensor(Wtr[ti]); St=torch.tensor(Str[ti]); Nz=torch.tensor(noise[ti])
            tt=torch.tensor(tgt[ti]); wt=torch.tensor(sw[ti],dtype=torch.float32)
            dt=torch.tensor(dep_t[ti]); dk=torch.tensor(dep_ok[ti])
            Xv=torch.tensor(Wtr[vi]).to(DEV); Sv=torch.tensor(Str[vi]).to(DEV)
            av=np.zeros(len(vi)); at=np.zeros(len(Wte))
            for ep in range(epochs):
                net.train(); perm=torch.randperm(len(ti))
                for i in range(0,len(ti)-bs+1,bs):
                    b=perm[i:i+bs]; xb=Xt[b].clone(); sb=St[b].to(DEV)
                    th=torch.rand(len(b))*2*np.pi; cs,sn=torch.cos(th),torch.sin(th)
                    for k in (0,3,6):
                        e_,n_=xb[:,k].clone(),xb[:,k+1].clone()
                        xb[:,k]=cs[:,None]*e_-sn[:,None]*n_; xb[:,k+1]=sn[:,None]*e_+cs[:,None]*n_
                    if torch.rand(1).item()<0.5:
                        for k in (2,5,8): xb[:,k]*=-1
                    if torch.rand(1).item()<0.5:
                        j=torch.randint(0,len(ti),(len(b),))
                        amp=(torch.rand(len(b),1,1)*0.6)
                        xb=xb+amp*Nz[j].repeat(1,1,5)[:,:,:xb.shape[2]]
                    xb=xb.to(DEV)
                    pm,pdep=net(xb,sb)
                    lm=(wt[b].to(DEV)*(pm-tt[b].to(DEV)).abs()).sum()/wt[b].sum().to(DEV)
                    dkb=dk[b].to(DEV)
                    ld=((pdep-dt[b].to(DEV)).abs()*dkb).sum()/(dkb.sum()+1e-6)
                    opt.zero_grad(); (lm+0.15*ld).backward(); opt.step(); sch.step()
                if ep>=epochs-avg_last:
                    net.eval()
                    with torch.no_grad():
                        av+=net(Xv,Sv)[0].cpu().numpy()
                        at+=np.concatenate([net(Xte_t[i:i+512],Ste_t[i:i+512])[0].cpu().numpy()
                                            for i in range(0,len(Wte),512)])
            oof[vi]+=(av/avg_last+off_v)/len(seeds)
            pte+=(at/avg_last+off_t)/(5*len(seeds))
            nf+=1
            print("    fold %2d/%d selesai  (%.0f menit terpakai, ~%.0f menit tersisa)"
                  %(nf,5*len(seeds),(time.time()-t0)/60,
                    (time.time()-t0)/nf*(5*len(seeds)-nf)/60), flush=True)
    return oof,pte
'''


def nb_ssl():
    cells = prelude(
        "kaggle 07 — Pra-latih self-supervised di train+test",
        "Ide dengan **plafon tertinggi yang belum pernah dicoba sama sekali**, dan sudah "
        "berdiri sebagai prioritas 1 di `CLAUDE.md` sejak `notebook_8`.\n\n"
        "Batasan sesungguhnya di case ini bukan jumlah record melainkan jumlah **event**: "
        "~905 event efektif dari 10.505 record. Itulah yang membatasi kapasitas model dan "
        "kenapa 25 keluarga ide berturut-turut memberi ≤ 0,001.\n\n"
        "Rekonstruksi waveform tidak punya batasan itu. Untuk tugas *masked "
        "reconstruction*, tiap record berdiri sendiri, jadi ukuran sampel efektifnya "
        "benar-benar **12.805** (10.505 train + 2.300 test) — **14× lebih besar**. "
        "Encoder yang sudah belajar struktur gelombang seismik dari 12.805 contoh lalu "
        "di-fine-tune di 905 event adalah satu-satunya jalur di repo ini yang menambah "
        "data efektif tanpa menyentuh grouping.\n\n"
        "**Transduktif dan sah:** waveform test memang disediakan kompetisi, dan tidak ada "
        "label yang disentuh.",
        "~55 menit pra-latih + ~110 menit fine-tune = **~165 menit**")
    cells.append(md(
        "---\n## 1. Masked autoencoder + fine-tune\n\n"
        "**Pra-latih.** 35% jendela waktu dinolkan dalam potongan 50 sampel; encoder "
        "(badan Net3 apa adanya) + dekoder ringan merekonstruksinya. Dua keputusan yang "
        "menentukan berhasil-tidaknya:\n\n"
        "- **Rugi dihitung HANYA di bagian yang ditutup.** Kalau seluruh sinyal ikut "
        "dihitung, jaringan cukup menyalin input dan tidak belajar apa-apa.\n"
        "- **Dekodernya sengaja lemah** (dua `ConvTranspose1d` + satu conv). Dekoder yang "
        "kuat akan mengerjakan rekonstruksi sendiri dan membiarkan encoder-nya kosong.\n\n"
        "**Fine-tune.** Net3 persis `notebook_8` — target residual anchor ridge, kepala "
        "kedua `log10(depth)` bobot 0,15, tiga augmentasi lama, 80 epoch, 3 seed — "
        "satu-satunya perbedaan adalah `net.body` diisi bobot hasil pra-latih dan "
        "learning rate badan diturunkan **0,3×** (discriminative fine-tuning) supaya "
        "epoch-epoch awal tidak langsung menghapus yang sudah dipelajari.\n\n"
        "Bobot encoder disimpan (`enc_pretrain.pt`) supaya kalau fine-tune-nya perlu "
        "diulang dengan setelan lain, pra-latihnya tidak usah diulang."))
    cells.append(co(SSL_SRC))
    cells.append(md("---\n## 2. Pra-latih (tanpa label, train + test)"))
    cells.append(co(
        'Wall = np.concatenate([Wtr, Wte], 0)\n'
        'print("pra-latih di %d waveform (%d train + %d test), tanpa label"\n'
        '      %(len(Wall), len(Wtr), len(Wte)))\n'
        't0 = time.time()\n'
        'enc_sd = pretrain(Wall, epochs=60)\n'
        'torch.save(enc_sd, catat(OUT/"enc_pretrain.pt"))\n'
        'print("pra-latih selesai %.0f menit"%((time.time()-t0)/60))\n'))
    cells.append(md("---\n## 3. Fine-tune\n\n15 fold (3 seed × 5 GroupKFold berbasis event)."))
    cells.append(co('sw = make_sw(power=0.5)\nt0 = time.time()\n'
                    'oof, pte = run_ssl(Wtr, Str, Wte, Ste, sw, enc_sd, seeds=(0,1,2))\n'))
    cells.append(lapor_cell("cnn10_ssl", "cnn3_avg 0,2074 | cnn3_dir 0,2116 | LightGBM terbaik 0,2030"))
    cells.append(md(
        "---\n## 4. Blend + verdikt\n\n"
        "Dua hal yang bisa terjadi dan dua-duanya informatif: kalau `lb_real` tunggalnya "
        "**turun di bawah 0,2074**, pra-latih menambah akurasi per-record dan itu jalur "
        "yang harus dikejar lebih jauh (encoder lebih besar, pra-latih lebih lama). Kalau "
        "skornya setara tapi **korelasinya rendah**, nilainya ada di diversitas blend — "
        "persis pola CNN v3, yang kalah sebagai model tunggal tapi dapat bobot 0,404."))
    cells.append(blend_cell("cnn10_ssl", "notebook_8 + CNN v3 pra-latih SSL"))
    cells.append(md("---\n## 5. Bungkus hasil jadi satu zip"))
    cells.append(co('bundel("hasil_cnn10_ssl")\n'))
    return nb(cells)


# ==================================================================== 08 head distribusi
DIST_SRC = '''class Net3D(nn.Module):
    """Net3 dengan kepala DISTRIBUSI: 41 bin residual, bukan satu angka.

    Metrik membobot event M>=6,5 sebesar 2,5x, jadi ekor mahal. Regresi L1 memprediksi
    MEDIAN kondisional, dan median adalah penduga yang paling menyusut ke tengah -- persis
    sifat yang salah untuk ekor. Kepala distribusi memisahkan dua hal: jaringan belajar
    SEBARAN penuh, lalu ringkasannya dipilih belakangan (mean, median, atau kuantil) tanpa
    melatih ulang.

    Kalibrasi berbin di nb7 sudah menunjukkan under-prediction nyata di ekor (+0,13 s/d
    +0,17 untuk prediksi > 6,0) yang tidak bisa dipanen dengan koreksi linear -- gain
    jujurnya cuma -0,0007. Kepala distribusi menyerang penyebabnya, bukan gejalanya."""
    def __init__(s, n_scalar, w=64, nbin=41, lo=-1.5, hi=1.5):
        super().__init__()
        s.body=nn.Sequential(Blk(9,w),Blk(w,w*2),Blk(w*2,w*3),Blk(w*3,w*4,k=5,pool=2),
                             Blk(w*4,w*4,k=3,pool=2))
        s.trunk=nn.Sequential(nn.Linear(w*8+n_scalar,256), nn.SiLU(), nn.Dropout(0.25),
                              nn.Linear(256,96), nn.SiLU())
        s.mag=nn.Linear(96,nbin); s.dep=nn.Linear(96,1)
        s.register_buffer("centers", torch.linspace(lo,hi,nbin))
        s.width=(hi-lo)/(nbin-1)
    def forward(s,x,sc_):
        h=s.body(x); h=torch.cat([h.mean(-1),h.amax(-1),sc_],dim=1); h=s.trunk(h)
        return s.mag(h), s.dep(h).squeeze(-1)

def soft_target(t, centers, width):
    """Label lunak segitiga: massa dibagi ke dua bin tetangga. Klasifikasi keras 32 kelas
    sudah dicoba di nb5 dan JAUH lebih buruk (0,2693 vs 0,2161) -- yang salah di sana
    label one-hot, yang membuang urutan antar-bin."""
    d=(t[:,None]-centers[None,:]).abs()/width
    w=torch.clamp(1-d,min=0)
    return w/(w.sum(1,keepdim=True)+1e-8)

def summarize(logit, centers, mode="mean"):
    p=torch.softmax(logit,dim=1)
    if mode=="mean": return (p*centers[None,:]).sum(1)
    cdf=p.cumsum(1)
    q=0.5 if mode=="median" else float(mode)
    idx=(cdf<q).sum(1).clamp(max=len(centers)-1)
    return centers[idx]

def run_dist(Wtr,Str,Wte,Ste, sw, seeds=(0,1,2), epochs=90, bs=128, lr=2.5e-3, avg_last=10):
    """Sama persis notebook_8 kecuali kepala + rugi. Keluarannya LOGIT per bin, disimpan
    utuh supaya ringkasannya (mean / median / kuantil) bisa dipilih SESUDAH training."""
    Xa=Ftr[A_BASE].values.astype(np.float64); Xa_te=Fte[A_BASE].values.astype(np.float64)
    dep_t=np.log10(d_tr+1).astype(np.float32); dep_ok=(~rnd_tr).astype(np.float32)
    noise=Wtr[:,:,:200].copy()
    NB=41
    oofl=np.zeros((len(y),NB)); ptel=np.zeros((len(Wte),NB))
    oof_off=np.zeros(len(y)); pte_off=np.zeros(len(Wte))
    Xte_t=torch.tensor(Wte).to(DEV); Ste_t=torch.tensor(Ste).to(DEV)
    nf=0; t0=time.time()
    for seed in seeds:
        torch.manual_seed(seed); np.random.seed(seed)
        for ti,vi in GroupKFold(5).split(Wtr,y,ev):
            rg=Ridge(alpha=1.0).fit(Xa[ti],y[ti],sample_weight=sw[ti])
            tgt=(y-rg.predict(Xa)).astype(np.float32)
            off_v=rg.predict(Xa[vi]); off_t=rg.predict(Xa_te)
            net=Net3D(Str.shape[1]).to(DEV)
            opt=torch.optim.AdamW(net.parameters(),lr=lr,weight_decay=2e-2)
            sch=torch.optim.lr_scheduler.OneCycleLR(opt,max_lr=lr,
                    total_steps=epochs*max(1,len(ti)//bs),pct_start=0.2)
            Xt=torch.tensor(Wtr[ti]); St=torch.tensor(Str[ti]); Nz=torch.tensor(noise[ti])
            tt=torch.tensor(tgt[ti]); wt=torch.tensor(sw[ti],dtype=torch.float32)
            dt=torch.tensor(dep_t[ti]); dk=torch.tensor(dep_ok[ti])
            Xv=torch.tensor(Wtr[vi]).to(DEV); Sv=torch.tensor(Str[vi]).to(DEV)
            av=np.zeros((len(vi),NB)); at=np.zeros((len(Wte),NB))
            for ep in range(epochs):
                net.train(); perm=torch.randperm(len(ti))
                for i in range(0,len(ti)-bs+1,bs):
                    b=perm[i:i+bs]; xb=Xt[b].clone(); sb=St[b].to(DEV)
                    th=torch.rand(len(b))*2*np.pi; cs,sn=torch.cos(th),torch.sin(th)
                    for k in (0,3,6):
                        e_,n_=xb[:,k].clone(),xb[:,k+1].clone()
                        xb[:,k]=cs[:,None]*e_-sn[:,None]*n_; xb[:,k+1]=sn[:,None]*e_+cs[:,None]*n_
                    if torch.rand(1).item()<0.5:
                        for k in (2,5,8): xb[:,k]*=-1
                    if torch.rand(1).item()<0.5:
                        j=torch.randint(0,len(ti),(len(b),))
                        amp=(torch.rand(len(b),1,1)*0.6)
                        xb=xb+amp*Nz[j].repeat(1,1,5)[:,:,:xb.shape[2]]
                    xb=xb.to(DEV)
                    logit,pdep=net(xb,sb)
                    st=soft_target(tt[b].to(DEV), net.centers, net.width)
                    ce=-(st*torch.log_softmax(logit,dim=1)).sum(1)
                    wbd=wt[b].to(DEV)
                    lm=(wbd*ce).sum()/wbd.sum()
                    dkb=dk[b].to(DEV)
                    ld=((pdep-dt[b].to(DEV)).abs()*dkb).sum()/(dkb.sum()+1e-6)
                    opt.zero_grad(); (lm+0.15*ld).backward(); opt.step(); sch.step()
                if ep>=epochs-avg_last:
                    net.eval()
                    with torch.no_grad():
                        av+=torch.softmax(net(Xv,Sv)[0],1).cpu().numpy()
                        at+=np.concatenate([torch.softmax(net(Xte_t[i:i+512],Ste_t[i:i+512])[0],1)
                                            .cpu().numpy() for i in range(0,len(Wte),512)])
            oofl[vi]+=av/avg_last/len(seeds); ptel+=at/avg_last/(5*len(seeds))
            oof_off[vi]+=off_v/len(seeds); pte_off+=off_t/(5*len(seeds))
            nf+=1
            print("    fold %2d/%d selesai  (%.0f menit terpakai, ~%.0f menit tersisa)"
                  %(nf,5*len(seeds),(time.time()-t0)/60,
                    (time.time()-t0)/nf*(5*len(seeds)-nf)/60), flush=True)
    ctr=np.linspace(-1.5,1.5,NB)
    return oofl, ptel, oof_off, pte_off, ctr
'''


def nb_dist():
    cells = prelude(
        "kaggle 08 — Kepala distribusi (soft-bin) untuk CNN v3",
        "Notebook paling spekulatif di batch ini — jalankan terakhir.\n\n"
        "Metrik membobot event M ≥ 6,5 sebesar **2,5×**, jadi ekor mahal. Tapi rugi L1 "
        "memprediksi **median kondisional**, dan median adalah penduga yang paling "
        "menyusut ke tengah — persis sifat yang salah untuk ekor. Kalibrasi berbin di "
        "`notebook_7` sudah memperlihatkan gejalanya: prediksi > 6,0 **under-predict "
        "+0,13 s/d +0,17**. Koreksi linear atas gejala itu cuma memberi −0,0007.\n\n"
        "Kepala distribusi menyerang penyebabnya. Jaringan belajar **sebaran penuh** "
        "residual (41 bin), lalu ringkasannya — mean, median, atau kuantil — dipilih "
        "**setelah** training, tanpa melatih ulang. Logit disimpan utuh, jadi satu run "
        "menghasilkan seluruh keluarga kandidat sekaligus.\n\n"
        "**Kenapa ini bukan pengulangan kegagalan lama.** `notebook_5` mencoba klasifikasi "
        "ordinal 32 kelas dan hasilnya jauh lebih buruk (0,2693 vs 0,2161). Yang salah di "
        "sana adalah label **one-hot**, yang membuang urutan antar-bin sepenuhnya. Di sini "
        "labelnya **lunak segitiga** — massa dibagi ke dua bin tetangga — jadi urutannya "
        "terjaga, dan targetnya **residual anchor**, bukan magnitudo mentah.",
        "~120 menit")
    cells.append(md(
        "---\n## 1. Kepala 41-bin + label lunak\n\n"
        "Badan, augmentasi, target residual, kepala kedua kedalaman, seed, dan bobot "
        "sample **tidak diubah** dari `notebook_8`. Yang berubah: kepala magnitudo "
        "mengeluarkan 41 logit di rentang residual [−1,5, +1,5] (langkah 0,075), dan "
        "ruginya jadi cross-entropy berbobot terhadap label lunak segitiga.\n\n"
        "Yang disimpan adalah **matriks probabilitas penuh** (10.505 × 41 dan 2.300 × 41), "
        "bukan satu angka. Semua ringkasan diuji di sel berikutnya dari satu run yang sama."))
    cells.append(co(DIST_SRC))
    cells.append(md("---\n## 2. Training\n\n15 fold (3 seed × 5 GroupKFold berbasis event)."))
    cells.append(co('sw = make_sw(power=0.5)\nt0 = time.time()\n'
                    'oofl, ptel, oof_off, pte_off, ctr = run_dist(Wtr, Str, Wte, Ste, sw)\n'
                    'np.savez(catat(OUT/"cnn11_dist_raw.npz"), oofl=oofl, ptel=ptel,\n'
                    '         oof_off=oof_off, pte_off=pte_off, ctr=ctr)\n'
                    'print("\\ntraining selesai %.0f menit"%((time.time()-t0)/60))\n'))
    cells.append(md(
        "---\n## 3. Pilih ringkasan sebaran\n\n"
        "Satu run, banyak kandidat. Yang dicari bukan sekadar `lb_real` terkecil melainkan "
        "kandidat yang **`bias_rnd`-nya tidak melonjak** — menggeser ringkasan ke kuantil "
        "atas menaikkan seluruh prediksi, dan itu persis mode kegagalan `notebook_2`."))
    cells.append(co(
        'rows = []\n'
        'kand = {}\n'
        'for mode in ["mean","median","q0.55","q0.60","q0.65"]:\n'
        '    if mode == "mean":\n'
        '        o = (oofl*ctr[None,:]).sum(1); p = (ptel*ctr[None,:]).sum(1)\n'
        '    else:\n'
        '        q = 0.5 if mode=="median" else float(mode[1:])\n'
        '        o = ctr[(oofl.cumsum(1)<q).sum(1).clip(0,len(ctr)-1)]\n'
        '        p = ctr[(ptel.cumsum(1)<q).sum(1).clip(0,len(ctr)-1)]\n'
        '    o = o + oof_off; p = p + pte_off\n'
        '    kand[mode] = (o, p)\n'
        '    po = post_tr(o)\n'
        '    rows.append(dict(mode=mode, lb_real=round(lb_real(po),4),\n'
        '                     dec=round(part_real(po,True),4), rnd=round(part_real(po,False),4),\n'
        '                     bias_rnd=round(bias_rnd(po),3)))\n'
        'display(pd.DataFrame(rows))\n'
        'print("pembanding cnn3_avg (kepala regresi biasa): lb_real tunggal 0,2074")\n'))
    cells.append(md(
        "---\n## 4. Blend + verdikt\n\n"
        "Ringkasan dipilih dari tabel di atas: **`lb_real` terkecil di antara yang "
        "`bias_rnd`-nya ≤ +0,05.** Ambang itu bukan karangan — `notebook_5` rugi di LB "
        "pada +0,056."))
    cells.append(co(
        'ok = [r for r in rows if r["bias_rnd"] <= 0.05]\n'
        'best = min(ok or rows, key=lambda r: r["lb_real"])["mode"]\n'
        'print("ringkasan terpilih:", best)\n'
        'oof, pte = kand[best]\n'))
    cells.append(lapor_cell("cnn11_dist", "cnn3_avg 0,2074 | cnn3_dir 0,2116 | LightGBM terbaik 0,2030"))
    cells.append(blend_cell("cnn11_dist", "notebook_8 + CNN v3 kepala distribusi"))
    cells.append(md("---\n## 5. Bungkus hasil jadi satu zip"))
    cells.append(co('bundel("hasil_cnn11_dist")\n'))
    return nb(cells)


# ---------------------------------------------------------------- tulis
files = {
    "06_augmentasi_agresif.ipynb": nb_aug(),
    "07_ssl_pretrain.ipynb": nb_ssl(),
    "08_head_distribusi.ipynb": nb_dist(),
}
for nama, obj in files.items():
    (OUT / nama).write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")
    print("tertulis:", OUT / nama)
