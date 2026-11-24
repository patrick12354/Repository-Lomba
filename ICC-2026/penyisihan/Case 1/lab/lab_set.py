"""Set-transformer atas record yang berbagi depth key.

Smoothing tangan memakai median seluruh grup depth dengan bobot lam tetap. Untuk
`depth = 10.0` grup itu mencampur 1.633 record dari 21 gempa berbeda, jadi median-nya
derau -- karena itu sisi depth-bulat dangkal tidak di-smooth sama sekali dan tertinggal
di lb_real 0,207 sementara sisi desimal ada di 0,144.

Model ini membiarkan attention yang memutuskan record mana yang saling co-belong.
Beda dari classifier co-membership nb7 (yang cuma memanen 0,3-1% headroom): itu pairwise
dan smoothing-nya berbasis probabilitas; ini set-level dan dilatih end-to-end.

TARGET DI-DEMEAN PER SUBSET. Tanpa itu model belajar prior katalog train (depth bulat
rata-rata M 5,45 vs desimal 5,19) dan mendorong `bias_rnd` +0,031 -> +0,044 -- persis
mekanisme yang membuat notebook_2 dan notebook_5 rugi di LB.

Set dibentuk HANYA dari record yang tersedia di himpunan yang sedang dinilai (fold
validasi, atau test), meniru kondisi test-time.
"""
import numpy as np, torch, torch.nn as nn
from sklearn.model_selection import GroupKFold
import lab_common as C

DEV = "cuda" if torch.cuda.is_available() else "cpu"
FCOL = ["Cd_2","Cv_2","Ca_4","logdist","loghypo","logE","snr_db","tauc","cent_a",
        "lhr_a","tE50","rectilin","Pd_4","Pv_4","Pa_4","gd_0.5_4","depth_km",
        "PdH_2","PdV_2","rmsd_2","fdom_a","kurt","is_clipped","hv_d"]

class SetNet(nn.Module):
    def __init__(s, nf, h=128, nl=3):
        super().__init__()
        s.emb = nn.Sequential(nn.Linear(nf,h), nn.SiLU(), nn.Linear(h,h))
        enc = nn.TransformerEncoderLayer(h, 4, h*2, dropout=0.1, batch_first=True, norm_first=True)
        s.tr = nn.TransformerEncoder(enc, nl)
        s.out = nn.Sequential(nn.LayerNorm(h), nn.Linear(h,64), nn.SiLU(), nn.Linear(64,1))
    def forward(s, x, mask):
        h = s.emb(x); h = s.tr(h, src_key_padding_mask=~mask)
        return s.out(h).squeeze(-1)

def _feats(F, blend, dep, mu, sd):
    # `kurt` punya 9 nilai non-finite di train; LightGBM menelan NaN secara native jadi
    # ini tak pernah terlihat, tapi di jaringan NaN merambat ke seluruh batch.
    Z = np.nan_to_num(F[FCOL].values.astype(np.float32), nan=0.0, posinf=0.0, neginf=0.0)
    Z = np.clip((Z - mu) / sd, -8, 8)
    b = blend.astype(np.float32)
    # prediksi relatif terhadap grup depth-nya sendiri: sinyal yang dilihat attention
    gm = np.zeros_like(b)
    for d in np.unique(dep):
        m = dep == d; gm[m] = np.median(b[m])
    return np.concatenate([b[:,None], (b-gm)[:,None], gm[:,None], Z], 1).astype(np.float32)

def _sets(idx, dep, maxn, rng=None):
    out = []
    for d in np.unique(dep[idx]):
        g = idx[dep[idx] == d]
        if rng is not None: g = rng.permutation(g)
        for k in range(0, len(g), maxn):
            if len(g[k:k+maxn]) >= 2: out.append(g[k:k+maxn])
    return out

def _pad(sets, X, maxn):
    B = len(sets)
    xb = np.zeros((B,maxn,X.shape[1]), np.float32); mk = np.zeros((B,maxn), bool)
    ids = np.zeros((B,maxn), np.int64)
    for i,s in enumerate(sets):
        n = len(s); xb[i,:n] = X[s]; mk[i,:n] = True; ids[i,:n] = s
    return xb, mk, ids

def run(blend_tr, blend_te, seeds=(0,1,2), epochs=60, lr=2e-3, maxn=40, bs=8,
        demean=True, nrep=6):
    Ftr, Fte = C.get_feats()
    Z0 = np.nan_to_num(Ftr[FCOL].values.astype(np.float32), nan=0.0, posinf=0.0, neginf=0.0)
    mu, sd = Z0.mean(0), Z0.std(0)+1e-6
    Xtr = _feats(Ftr, blend_tr, C.d_tr, mu, sd)
    Xte = _feats(Fte, blend_te, C.d_te, mu, sd)
    NF = Xtr.shape[1]

    res = (C.y - blend_tr).astype(np.float32)
    if demean:                       # buang prior katalog per subset
        for m in (C.rnd_tr, ~C.rnd_tr): res[m] -= res[m].mean()
    tgt_t = torch.tensor(res).to(DEV)
    sw_t  = torch.tensor(C.SW.astype(np.float32)).to(DEV)

    corr = np.zeros(len(C.y)); ncr = np.zeros(len(C.y))
    cte  = np.zeros(len(blend_te)); nte = np.zeros(len(blend_te))

    def infer(net, idx, X, dep, acc, nacc, seedbase):
        net.eval()
        with torch.no_grad():
            for r in range(nrep):
                rr = np.random.RandomState(seedbase+r)
                ss = _sets(idx, dep, maxn, rr)
                for k in range(0, len(ss), 16):
                    bb = ss[k:k+16]
                    xb, mk, ids = _pad(bb, X, maxn)
                    pc = net(torch.tensor(xb).to(DEV), torch.tensor(mk).to(DEV)).cpu().numpy()
                    for i,s in enumerate(bb):
                        acc[s] += pc[i,:len(s)]; nacc[s] += 1

    te_idx = np.arange(len(blend_te))
    for seed in seeds:
        torch.manual_seed(seed); rng = np.random.RandomState(seed)
        for ti, vi in GroupKFold(5).split(Xtr, C.y, C.ev):
            net = SetNet(NF).to(DEV)
            opt = torch.optim.AdamW(net.parameters(), lr=lr, weight_decay=1e-2)
            nst = epochs * max(1, len(_sets(ti, C.d_tr, maxn, rng))//bs)
            sch = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=lr, total_steps=nst+10, pct_start=0.25)
            for ep in range(epochs):
                net.train()
                ss = _sets(ti, C.d_tr, maxn, rng); rng.shuffle(ss)
                for k in range(0, len(ss), bs):
                    bb = ss[k:k+bs]
                    xb, mk, ids = _pad(bb, Xtr, maxn)
                    xb_t = torch.tensor(xb).to(DEV); mk_t = torch.tensor(mk).to(DEV)
                    id_t = torch.tensor(ids).to(DEV)
                    pc = net(xb_t, mk_t)
                    ww = sw_t[id_t] * mk_t
                    loss = ((pc - tgt_t[id_t]).abs() * ww).sum() / (ww.sum()+1e-8)
                    opt.zero_grad(); loss.backward()
                    nn.utils.clip_grad_norm_(net.parameters(), 1.0)
                    opt.step()
                    if sch.last_epoch < nst: sch.step()
            infer(net, vi, Xtr, C.d_tr, corr, ncr, 1000)          # set dibentuk di dalam fold val
            infer(net, te_idx, Xte, C.d_te, cte, nte, 2000)       # set dibentuk di dalam test
    return corr/np.maximum(ncr,1), cte/np.maximum(nte,1)
