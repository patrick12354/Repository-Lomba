"""Protokol blend nb6/nb8, dipakai ulang: cari bobot di separuh event, ukur di separuh
lain, 12 belahan; bobot final = rata-rata lintas belahan; optimisme seleksi diukur."""
import numpy as np
import lab_common as C
from fastscore import Scorer, Post

def ld(n):
    z = np.load(C.CACHE/f"{n}.npz"); return z["oof"], z["pte"]

def search(names, ref_oof=None, nsamp=8000, alpha=0.6, seed=0,
           post_args=(0.95, 0.5, 150, 1.15, 1.05), verbose=True):
    post   = Post(C.d_tr, *post_args)
    postte = Post(C.d_te, *post_args)
    P  = {n: ld(n) for n in names}
    On = np.stack([P[n][0] for n in names])
    Oe = np.stack([P[n][1] for n in names])
    sc = Scorer(C.EVR, np.ones(len(C.y), bool))
    rng = np.random.RandomState(seed)
    W = np.vstack([rng.dirichlet(np.ones(len(names))*alpha, size=nsamp), np.eye(len(names))])
    Q = np.stack([post(x @ On) for x in W])
    uev = np.unique(C.ev); gains=[]; opt=[]; ws=[]
    for rep in range(6):
        r = np.random.RandomState(100+rep); perm = r.permutation(uev)
        h1 = np.isin(C.ev, perm[:len(perm)//2])
        for keep in (h1, ~h1):
            ss = Scorer(C.EVR, keep); sh = Scorer(C.EVR, ~keep)
            v = np.array([ss(q) for q in Q]); i = v.argmin()
            if ref_oof is not None: gains.append(sh(Q[i]) - sh(ref_oof))
            opt.append(sh(Q[i]) - v[i]); ws.append(W[i])
    wm = np.mean(ws, 0); wm /= wm.sum()
    qm = post(wm @ On); pte = postte(wm @ Oe)
    o_half = float(np.mean(opt)/np.sqrt(2))
    res = dict(w=wm, oof=qm, pte=pte, lb_real=float(sc(qm)), jujur=float(sc(qm))+o_half,
               optimisme=o_half, bias=C.bias_rnd(qm),
               dec=C.part_real(qm, True), rnd=C.part_real(qm, False),
               mean_rnd_te=float(pte[C.MT].mean()), sd_rnd_te=float(pte[C.rnd_te].std()),
               gain=float(np.mean(gains)) if gains else None,
               menang=sum(g < 0 for g in gains) if gains else None)
    if verbose:
        print("bobot:", dict(zip(names, np.round(wm, 3))))
        if gains: print("  gain vs acuan %+.4f (menang %d/12)" % (res["gain"], res["menang"]))
        print("  lb_real=%.4f jujur=%.4f optimisme=%+.4f bias=%+.3f dec=%.4f rnd=%.4f"
              % (res["lb_real"], res["jujur"], o_half, res["bias"], res["dec"], res["rnd"]))
        print("  test: mean_rnd=%.3f sd_rnd=%.3f  -> estimasi LB %.4f"
              % (res["mean_rnd_te"], res["sd_rnd_te"], res["lb_real"]+0.0082))
    return res

def nb8_ref():
    NB8 = ["swA_sqrt","resA_dep","resB_dep","resB_c30","resB_p05","cnnres","cnn3_avg","cnn3_dir"]
    post = Post(C.d_tr, 0.95, 0.5, 150, 1.15, 1.05)
    return post(np.load(C.CACHE/"w_nb9.npy") @ np.stack([ld(n)[0] for n in NB8]))
