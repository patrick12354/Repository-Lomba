import _path  # noqa: F401  -- menaruh Case 1/ di sys.path
import numpy as np, pandas as pd
import lab_common as C
from fastscore import Post
def ld(n):
    z=np.load(C.CACHE/f"{n}.npz"); return z["oof"],z["pte"]
OLD=["regA","swA_sqrt","resA_sqrt","resB","resB_sqrt","resB_c30","cnn_sqrt"]
w=np.load(C.CACHE/"w7_mean.npy")
oof=w@np.stack([ld(n)[0] for n in OLD]); pte=w@np.stack([ld(n)[1] for n in OLD])

print("=== A. grup depth-bulat DALAM di test: satu gempa atau banyak? ===")
print("pembanding sebaran prediksi DALAM event nyata (sisi desimal train, grup >=20 record):")
d=pd.DataFrame({"e":C.ev,"p":oof,"d":C.d_tr})[~C.rnd_tr]
g=d.groupby("e").filter(lambda s: len(s)>=20).groupby("e")["p"]
print(f"  n_event={g.ngroups}  median sd dalam-event={g.std().median():.3f}  p90={g.std().quantile(0.9):.3f}")
print("grup test:")
for dv in [243.0,375.0,10.0,35.0]:
    m=np.isclose(C.d_te,dv)
    if m.sum()<5: continue
    print(f"  depth={dv:6.1f} n={m.sum():4d} sd_prediksi={pte[m].std():.3f} "
          f"range={pte[m].min():.2f}-{pte[m].max():.2f} mean={pte[m].mean():.2f}")
# pembanding: grup depth-bulat dangkal train (pasti banyak event)
m=np.isclose(C.d_tr,10.0); print(f"  [train d=10.0 n={m.sum()}] sd_prediksi={oof[m].std():.3f}  <- pasti banyak event")

print("\n=== B. sisa sistematis di residual OOF? ===")
res=C.y-oof
F,_=C.get_feats()
for col,bins in [("logdist",5),("snr_db",5),("is_clipped",2),("depth_km",5),("Pd_2",5)]:
    v=F[col].values
    q=pd.qcut(v,bins,duplicates="drop") if bins>2 else pd.Series(v).astype(int)
    t=pd.DataFrame({"q":q,"r":res}).groupby("q",observed=True)["r"].agg(["mean","count"])
    print(f"  {col:11s}", " | ".join(f"{m:+.3f}(n={int(n)})" for m,n in t.values))
