"""A02: studi kelayakan segmentasi lesi (DWI TRACE + ADC), dievaluasi pada 30 subjek sampel HELD-OUT.

Dua pembanding:
  - rule   : ambang relatif (DWI z > 2 dan ADC < 0,8 x median ADC otak), tanpa training
  - unet2d : U-Net 2.5D (3 slice bertetangga x DWI+ADC = 6 kanal), dilatih pada subjek tambahan dari
             a02a_unduh.py (data/train_extra, default 250 pasien) dan diuji pada 30 subjek sampel yang
             tidak pernah dilihat saat training (pemisahan per pasien).

Output: results/segmentasi.csv (Dice per subjek), results/segmentasi.json (ringkasan),
        results/contoh_segmentasi.npz (satu subjek untuk figur overlay)
Jalankan a02a_unduh.py dulu. Waktu jalan: lihat 'menit' di results/segmentasi.json (Apple M4, MPS). Jalankan ulang hanya kalau metodenya berubah.
"""
import json, time
import nibabel as nib
import numpy as np
import pandas as pd
import torch, torch.nn as nn, torch.nn.functional as F
from scipy import ndimage
from skimage.filters import threshold_otsu
from skimage.transform import resize
from _common import DATA, RESULTS

S = 128          # resolusi slice setelah resize
SEED = 42
torch.manual_seed(SEED); np.random.seed(SEED)
dev = "mps" if torch.backends.mps.is_available() else ("cuda" if torch.cuda.is_available() else "cpu")


def load(sub, root=DATA):
    t = np.asanyarray(nib.load(root / sub / "dwi" / f"{sub}_rec-TRACE_dwi.nii.gz").dataobj).squeeze().astype(np.float32)
    a = np.asanyarray(nib.load(root / sub / "dwi" / f"{sub}_rec-ADC_dwi.nii.gz").dataobj).squeeze().astype(np.float32)
    mf = DATA / "derivatives/lesion_masks" / sub / "dwi" / f"{sub}_space-TRACE_desc-lesionAcute_mask.nii.gz"
    im = nib.load(mf)
    m = np.asanyarray(im.dataobj) > 0
    vox_ml = float(np.prod(im.header.get_zooms()[:3])) / 1000
    # brain mask kasar: Otsu di TRACE, isi lubang, komponen terbesar per volume
    b = t > threshold_otsu(t)
    b = ndimage.binary_fill_holes(ndimage.binary_opening(b, iterations=2))
    lab, n = ndimage.label(b)
    if n > 1:
        b = lab == (np.argmax(ndimage.sum(b, lab, range(1, n + 1))) + 1)
    tz = (t - t[b].mean()) / (t[b].std() + 1e-6)
    ar = a / (np.median(a[b]) + 1e-6)              # ADC relatif: skala antar-scanner beda
    return tz, ar, b, m, vox_ml


def rule(tz, ar, b):
    p = (tz > 2.0) & (ar < 0.8) & b
    p = ndimage.binary_opening(p)
    lab, n = ndimage.label(p)
    if n:
        keep = ndimage.sum(p, lab, range(1, n + 1)) >= 10
        p = np.isin(lab, np.where(keep)[0] + 1)
    return p


def dice(p, g):
    s = p.sum() + g.sum()
    return 1.0 if s == 0 else 2 * (p & g).sum() / s


def to_slices(tz, ar, m):
    X = np.stack([resize(np.clip(tz, -3, 8), (S, S, tz.shape[2]), order=1, preserve_range=True),
                  resize(np.clip(ar, 0, 3), (S, S, ar.shape[2]), order=1, preserve_range=True)], 0)
    Y = resize(m.astype(np.float32), (S, S, m.shape[2]), order=0, preserve_range=True) > 0.5
    X = np.moveaxis(X, 3, 0)                                         # (z, 2, S, S)
    Xp = np.concatenate([X[:1], X, X[-1:]])                          # 2.5D: slice z-1, z, z+1
    X = np.concatenate([Xp[:-2], Xp[1:-1], Xp[2:]], 1)               # (z, 6, S, S)
    return X.astype(np.float32), np.moveaxis(Y, 2, 0)[:, None].astype(np.float32)


def recall_lesi(p, g):
    lab, n = ndimage.label(g, structure=np.ones((3, 3, 3)))
    return np.nan if n == 0 else sum((p & (lab == i)).any() for i in range(1, n + 1)) / n


def blk(i, o):
    return nn.Sequential(nn.Conv2d(i, o, 3, padding=1), nn.BatchNorm2d(o), nn.ReLU(inplace=True),
                         nn.Conv2d(o, o, 3, padding=1), nn.BatchNorm2d(o), nn.ReLU(inplace=True))


class UNet(nn.Module):
    def __init__(s, c=16):
        super().__init__()
        s.e1, s.e2, s.e3, s.e4 = blk(6, c), blk(c, 2 * c), blk(2 * c, 4 * c), blk(4 * c, 8 * c)
        s.u3, s.d3 = nn.ConvTranspose2d(8 * c, 4 * c, 2, 2), blk(8 * c, 4 * c)
        s.u2, s.d2 = nn.ConvTranspose2d(4 * c, 2 * c, 2, 2), blk(4 * c, 2 * c)
        s.u1, s.d1 = nn.ConvTranspose2d(2 * c, c, 2, 2), blk(2 * c, c)
        s.out = nn.Conv2d(c, 1, 1)

    def forward(s, x):
        e1 = s.e1(x); e2 = s.e2(F.max_pool2d(e1, 2)); e3 = s.e3(F.max_pool2d(e2, 2)); e4 = s.e4(F.max_pool2d(e3, 2))
        d3 = s.d3(torch.cat([s.u3(e4), e3], 1)); d2 = s.d2(torch.cat([s.u2(d3), e2], 1)); d1 = s.d1(torch.cat([s.u1(d2), e1], 1))
        return s.out(d1)


def loss_fn(lg, y):
    p = torch.sigmoid(lg)
    d = 1 - (2 * (p * y).sum() + 1) / (p.sum() + y.sum() + 1)
    return F.binary_cross_entropy_with_logits(lg, y, pos_weight=torch.tensor(5.0, device=lg.device)) + d


subs = open(DATA / "sample_subjects.txt").read().split()               # test set held-out
EXTRA = DATA / "train_extra"
latih = open(EXTRA / "subjects.txt").read().split()
assert not set(latih) & set(subs), "subjek uji bocor ke data latih"
data, rows = {}, []
for s in subs:
    tz, ar, b, m, vml = load(s)
    pr = rule(tz, ar, b)
    X, Y = to_slices(tz, ar, m)
    data[s] = (X, Y)
    rows.append(dict(participant_id=s, vol_ml=m.sum() * vml, dice_rule=dice(pr, m),
                     kontras_dwi=float(np.median(tz[m])) if m.any() else np.nan,
                     adc_rel=float(np.median(ar[m])) if m.any() else np.nan))
    print(s, f"vol={m.sum()*vml:.1f}ml rule={rows[-1]['dice_rule']:.3f}", flush=True)
df = pd.DataFrame(rows).set_index("participant_id")

Xs, Ys = [], []
for s in latih:
    tz, ar, b, m, _ = load(s, EXTRA)
    X, Y = to_slices(tz, ar, m)
    Xs.append(X); Ys.append(Y)
Xtr, Ytr = torch.tensor(np.concatenate(Xs)), torch.tensor(np.concatenate(Ys))
print(f"latih: {len(latih)} pasien, {len(Xtr)} slice", flush=True)

EPOCH, BS, t0 = 25, 32, time.time()
ada_lesi = Ytr.flatten(1).any(1)
KOSONG = 0.25                     # tiap epoch: semua slice berlesi + 25% slice tanpa lesi (acak ulang)
net = UNet().to(dev); opt = torch.optim.AdamW(net.parameters(), 2e-3, weight_decay=1e-4)
n_ep = int(ada_lesi.sum() + KOSONG * (~ada_lesi).sum() * 1.1)
sch = torch.optim.lr_scheduler.OneCycleLR(opt, 3e-3, total_steps=EPOCH * ((n_ep + BS - 1) // BS))
for ep in range(EPOCH):
    net.train(); tot = 0
    idx = torch.where(ada_lesi | (torch.rand(len(Xtr)) < KOSONG))[0]
    for i in idx[torch.randperm(len(idx))].split(BS):
        x, y = Xtr[i].to(dev), Ytr[i].to(dev)
        if np.random.rand() < .5: x, y = x.flip(3), y.flip(3)
        if np.random.rand() < .5: x, y = x.flip(2), y.flip(2)
        if np.random.rand() < .5:                                    # augmentasi intensitas (variasi scanner)
            x = x * torch.empty(1, device=dev).uniform_(.85, 1.15)
        opt.zero_grad(); l = loss_fn(net(x), y); l.backward(); opt.step(); sch.step(); tot += l.item()
    print(f"epoch {ep}: loss {tot:.1f} ({time.time()-t0:.0f}s)", flush=True)

net.eval(); pred_store = {}
with torch.no_grad():
    for s in subs:
        X, Y = data[s]
        x = torch.tensor(X).to(dev)
        pb = (torch.sigmoid(net(x)) + torch.sigmoid(net(x.flip(3))).flip(3)) / 2       # TTA flip kiri-kanan
        p = pb.cpu().numpy() > 0.5
        df.loc[s, "dice_unet"] = dice(p, Y > 0.5)
        df.loc[s, "recall_lesi_unet"] = recall_lesi(p[:, 0], Y[:, 0] > 0.5)
        pred_store[s] = p
print(df[["vol_ml", "dice_rule", "dice_unet", "recall_lesi_unet"]].round(3), flush=True)

df.to_csv(RESULTS / "segmentasi.csv")
out = dict(n=len(df), n_latih=len(latih), n_slice_latih=len(Xtr), epoch=EPOCH, res=S, device=dev,
           recall_lesi_unet_mean=df.recall_lesi_unet.mean(),
           dice_rule_mean=df.dice_rule.mean(), dice_rule_median=df.dice_rule.median(),
           dice_unet_mean=df.dice_unet.mean(), dice_unet_median=df.dice_unet.median(),
           dice_unet_vol_ge5=df[df.vol_ml >= 5].dice_unet.mean(), n_vol_ge5=int((df.vol_ml >= 5).sum()),
           dice_unet_vol_lt5=df[df.vol_ml < 5].dice_unet.mean(),
           spearman_vol_dice=df[["vol_ml", "dice_unet"]].corr("spearman").iloc[0, 1],
           menit=(time.time() - t0) / 60)
json.dump(out, open(RESULTS / "segmentasi.json", "w"), indent=1)
print(json.dumps(out, indent=1))

# contoh untuk figur: simpan slice lesi terbesar tiap subjek (DWI, kunci, U-Net, aturan) + posisi
# relatif lesi di sumbu z (zf: 0 = slice otak terbawah, 1 = teratas) supaya figur bisa memilih
# kasus supratentorial yang representatif.
contoh = {}
for s in subs:
    X, Y = data[s]; P = pred_store[s]
    z = int(Y[:, 0].sum((1, 2)).argmax())
    tz, ar, b, m, _ = load(s)
    zb = np.where(b.any((0, 1)))[0]
    zf = (np.array(np.where(m))[2].mean() - zb.min()) / max(zb.max() - zb.min(), 1)
    ru = resize(rule(tz, ar, b)[..., z].astype(float), (S, S), order=0) > .5
    contoh[s] = dict(dwi=X[z, 0], gt=Y[z, 0] > .5, unet=P[z, 0], rule=ru, zf=zf)
np.savez_compressed(RESULTS / "contoh_segmentasi.npz",
                    **{f"{s}__{k}": v for s, d in contoh.items() for k, v in d.items()})
