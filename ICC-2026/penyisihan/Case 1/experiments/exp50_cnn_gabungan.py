"""exp50 — apakah keempat CNN Kaggle baru menolong kalau di-blend? TIDAK.
Berempat sekaligus: gain +0,0012, menang 4/12. Korelasinya 0,92-0,96 vs cnn3_avg."""
import sys, os, numpy as np
sys.path.insert(0, os.path.abspath("lab"))
import lab_common as C
from fastscore import Scorer, Post

post_tr = Post(C.d_tr, 0.95, 0.5, 150, 1.15, 1.05)
post_te = Post(C.d_te, 0.95, 0.5, 150, 1.15, 1.05)
sc = Scorer(C.EVR, np.ones(len(C.y), bool))
R = np.load("belum_run/ref/nb8_ref.npz", allow_pickle=True)
CAND = [str(x) for x in R["__cand__"]]
O = np.stack([R[f"{n}__oof"].astype(np.float64) for n in CAND])
E = np.stack([R[f"{n}__pte"].astype(np.float64) for n in CAND])
btr = R["__w__"] @ O; bte = R["__w__"] @ E
base = post_tr(btr)

X = "belum_run/hasil run/_x"
NEW = {n: np.load(f"{X}/hasil_{d}/{n}.npz") for n, d in
       [("cnn5","cnn5"),("cnn6","cnn6"),("cnn7","cnn7"),("cnn8","cnn8")]}

uev = np.unique(C.ev)
SPLITS = []
for rep in range(6):
    h1 = np.isin(C.ev, np.random.RandomState(100+rep).permutation(uev)[:len(uev)//2])
    for keep in (h1, ~h1): SPLITS.append((Scorer(C.EVR,keep), Scorer(C.EVR,~keep)))

def honest(Q, ref):
    g=[]
    for ss,sh in SPLITS:
        v=np.array([ss(q) for q in Q]); i=int(v.argmin()); g.append(sh(Q[i])-sh(ref))
    return float(np.mean(g)), sum(x<0 for x in g)

def demean(c, rnd):
    c=c.copy()
    for m in (rnd,~rnd): c[m]-=c[m].mean()
    return c

Z=np.load(f"{X}/hasil_set_transformer/set2.npz")
cd_tr=demean(Z["corr"].astype(np.float64),C.rnd_tr)
cd_te=demean(Z["cte"].astype(np.float64),C.rnd_te)
grid=[0.0,0.1,0.15,0.2,0.25,0.3,0.4,0.5,0.6,0.75]
Q=np.stack([post_tr(btr+l*cd_tr) for l in grid])
g,w = honest(Q, base)
print("SET demean-apply : gain holdout %+.5f  menang %d/12" % (g,w))

# --- blend 8 nb8 candidates + all 4 new CNNs at once
def search(names, Otr, Ote, ref, nsamp=8000, alpha=0.6, seed=0):
    rng=np.random.RandomState(seed)
    W=np.vstack([rng.dirichlet(np.ones(len(names))*alpha,size=nsamp),np.eye(len(names))])
    Q=np.stack([post_tr(x@Otr) for x in W])
    gains=[];opt=[];ws=[]
    for ss,sh in SPLITS:
        v=np.array([ss(q) for q in Q]); i=int(v.argmin())
        gains.append(sh(Q[i])-sh(ref)); opt.append(sh(Q[i])-v[i]); ws.append(W[i])
    wm=np.mean(ws,0); wm/=wm.sum()
    o=post_tr(wm@Otr); p=post_te(wm@Ote)
    return dict(w=wm,names=names,oof=o,pte=p,lb_real=float(sc(o)),
                opt=float(np.mean(opt))/np.sqrt(2), bias=C.bias_rnd(o),
                mean=float(p[C.MT].mean()), sd=float(p[C.rnd_te].std()),
                gain=float(np.mean(gains)), menang=sum(x<0 for x in gains))

for label, extra in [("nb8 + 4 CNN baru", ["cnn5","cnn6","cnn7","cnn8"]),
                     ("nb8 + cnn5,cnn7",  ["cnn5","cnn7"]),
                     ("nb8 + cnn7",       ["cnn7"])]:
    nm = CAND + extra
    Otr = np.vstack([O]+[NEW[n]["oof"].astype(np.float64)[None] for n in extra])
    Ote = np.vstack([E]+[NEW[n]["pte"].astype(np.float64)[None] for n in extra])
    r = search(nm, Otr, Ote, base)
    print("\n%-20s lb_real=%.4f (jujur %.4f) gain %+.5f menang %d/12 bias %+.3f mean %.3f sd %.3f"
          % (label, r["lb_real"], r["lb_real"]+r["opt"], r["gain"], r["menang"], r["bias"], r["mean"], r["sd"]))
    print("   bobot baru:", {n: round(float(x),3) for n,x in zip(nm,r["w"]) if n in extra})
    np.savez(f"C:/Users/timot/AppData/Local/Temp/claude/C--Patrick-Satu-Data/abf13cc6-51cd-44dc-81b8-f2d6c368c965/scratchpad/blend_{len(extra)}.npz", **{"w":r["w"],"oof":r["oof"],"pte":r["pte"]})
