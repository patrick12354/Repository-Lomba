import _path  # noqa: F401  -- menaruh Case 1/ di sys.path
import numpy as np, pandas as pd
import lab_common as C
tr=C.train; ev=C.ev; y=C.y
df=pd.DataFrame({"ev":ev,"y":y,"d":C.d_tr,"rnd":C.rnd_tr})
g=df.groupby("ev").agg(n=("y","size"),m=("y","first"),rnd=("rnd","first"),d=("d","first"))
print("== struktur pseudo-event ==")
for lbl,msk in [("dec",~g.rnd),("rnd<100",g.rnd&(g.d<100)),("rnd>=100",g.rnd&(g.d>=100))]:
    s=g[msk]; w=C.mag_weight(s.m.values)
    print(f"{lbl:9s} n_event={len(s):4d} n_rec={s.n.sum():6d} median_size={s.n.median():5.1f} max={s.n.max():4d} "
          f"bobot_metrik={w.sum()/C.mag_weight(g.m.values).sum():.3f} frac_rec={s.n.sum()/len(y):.3f} "
          f"SWmass={ (C.SW[C.rnd_tr if 'rnd' in lbl else ~C.rnd_tr].sum()) :.2f}")
print("\nSW mass: dec=%.2f rnd<100=%.2f rnd>=100=%.2f"%(C.SW[~C.rnd_tr].sum(),C.SW[C.MR].sum(),C.SW[C.rnd_tr&(C.d_tr>=100)].sum()))
print("record frac: dec=%.3f rnd=%.3f"%((~C.rnd_tr).mean(),C.rnd_tr.mean()))
print("\ndistribusi ukuran grup depth (bukan event) di TEST:")
kt=pd.Series(C.d_te); vc=kt.value_counts()
print("  dec: n_uniq=%d, median rec/depth=%.1f"%((~C.rnd_te).sum() and len(set(C.d_te[~C.rnd_te])), pd.Series(C.d_te[~C.rnd_te]).value_counts().median()))
print("  rnd:", vc[[v for v in vc.index if np.isclose(v,round(v))]].to_dict())
print("\ndistribusi ukuran grup depth di TRAIN (rnd):")
kk=pd.Series(C.d_tr); v2=kk.value_counts()
print("  rnd:", {k:int(v) for k,v in v2.items() if np.isclose(k,round(k))})
