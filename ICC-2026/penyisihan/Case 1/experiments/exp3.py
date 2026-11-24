import _path  # noqa: F401  -- menaruh Case 1/ di sys.path
import numpy as np, pandas as pd
import lab_common as C, lab_models as M
y,ev = C.y, C.ev

# 1. Berapa bobot metrik CV yang jatuh ke tail, sisi rnd?
df=pd.DataFrame({"ev":ev,"y":y,"rnd":C.rnd_tr,"d":C.d_tr})
g=df.groupby("ev").agg(n=("y","size"),m=("y","first"),rnd=("rnd","first"))
w=C.mag_weight(g.m.values)
for lbl,msk in [("dec",(~g.rnd).values),("rnd",g.rnd.values)]:
    ww=w[msk]; mm=g.m.values[msk]; nn=g.n.values[msk]
    # bobot CV (per pseudo-event) vs bobot 'nyata' (per record, ~ per event nyata)
    cvw = ww/ww.sum()
    rlw = (ww*nn)/(ww*nn).sum()
    tail = mm>=5.5
    print(f"{lbl}: bobot metrik pada event M>=5.5 -> CV {cvw[tail].sum():.3f} vs realistis {rlw[tail].sum():.3f}"
          f"   | M>=6.5: CV {cvw[mm>=6.5].sum():.3f} vs {rlw[mm>=6.5].sum():.3f}")

# 2. evaluasi realistis: pecah pseudo-event rnd jadi chunk ~7 record
def make_ev_real(seed, chunk=7):
    rng=np.random.RandomState(seed); e2=ev.copy(); nxt=ev.max()+1
    for eid in np.unique(ev[C.rnd_tr]):
        idx=np.where(ev==eid)[0]
        if len(idx)<=chunk*1.5: continue
        rng.shuffle(idx)
        k=max(2,int(round(len(idx)/chunk)))
        for j,part in enumerate(np.array_split(idx,k)):
            if j>0: e2[part]=nxt; nxt+=1
    return e2
EVR=[make_ev_real(s) for s in range(8)]
def part_real(p, dec):
    m=(~C.rnd_tr) if dec else C.rnd_tr
    return float(np.mean([C.eb_twmae(y[m],p[m],e[m]) for e in EVR]))
def lb_real(p): return C.FD*part_real(p,True)+(1-C.FD)*part_real(p,False)

Ftr,Fte=C.get_feats(); Gtr=C.add_group_feats(Ftr,C.train); Gte=C.add_group_feats(Fte,C.test)
oofA,pteA=M.cached("regA",None); oofB,pteB=M.cached("regB",None)
bo=0.65*oofA+0.35*oofB; bp=0.65*pteA+0.35*pteB
so=C.smooth_gen(bo,C.d_tr,0.95,0.0)
print("\n=== alpha_rnd: skor CV-lama vs skor REALISTIS (sisi rnd) ===")
print(f"{'a_rnd':>6}{'rnd_CVlama':>12}{'rnd_REAL':>10}{'lb_est_lama':>13}{'lb_REAL':>10}")
for ar in [0.85,0.95,1.00,1.05,1.15,1.30]:
    o=C.expand_subset(so,C.d_tr,1.15,ar)
    print(f"{ar:6.2f}{C.part_score(o,False):12.4f}{part_real(o,False):10.4f}{C.lb_estimate(o):13.4f}{lb_real(o):10.4f}")
