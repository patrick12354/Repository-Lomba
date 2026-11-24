import _path  # noqa: F401  -- menaruh Case 1/ di sys.path
import numpy as np, itertools, glob, os
import lab_common as C
def ld(n):
    z=np.load(C.CACHE/f"{n}.npz"); return z["oof"],z["pte"]
names=[os.path.basename(f)[:-4] for f in glob.glob(str(C.CACHE/"*.npz")) if "cnn_input" not in f]
print(f"{'kandidat':>16}{'cv_lama':>9}{'cv_real':>9}{'dec':>8}{'rnd':>8}{'lb_real':>9}{'bias':>8}")
P={}
for n in sorted(names):
    o,p=ld(n); P[n]=(o,p)
    print(f"{n:>16}{C.eb_twmae(C.y,o,C.ev):9.4f}{C.cv_real(o):9.4f}{C.part_real(o,True):8.4f}"
          f"{C.part_real(o,False):8.4f}{C.lb_real(o):9.4f}{C.bias_rnd(o):+8.3f}")

def post(o,dep,lam_deep=0.35,ad=1.15,ar=1.05):
    return C.expand_subset(C.smooth_gen(o,dep,0.95,lam_deep,100),dep,ad,ar)
print("\n=== blend 2-3 kandidat (setelah post-processing, kriteria lb_real) ===")
base=["regA","regB","resA","resB","swA_sqrt","swB_cap30","swA_cap30"]
base=[b for b in base if b in P]
res=[]
for k in (2,3):
    for combo in itertools.combinations(base,k):
        for w in (itertools.product([0,.15,.25,.35,.5,.65,.85,1],repeat=k) if k==2 else
                  itertools.product([0,.2,.35,.5,.65],repeat=k)):
            s=sum(w)
            if s==0: continue
            w=np.array(w)/s
            o=sum(wi*P[n][0] for wi,n in zip(w,combo))
            q=post(o,C.d_tr)
            res.append((C.lb_real(q),C.bias_rnd(q),combo,tuple(np.round(w,2))))
res.sort()
for r in res[:15]: print(f"  lb_real={r[0]:.4f} bias={r[1]:+.3f} {r[2]} {r[3]}")
# baseline nb3
o=post(0.65*P["regA"][0]+0.35*P["regB"][0],C.d_tr,0.0,1.15,1.15)
print(f"\nreferensi nb3 (lam_deep=0,a=1.15/1.15): lb_real={C.lb_real(o):.4f} bias={C.bias_rnd(o):+.3f}  [LB aktual 0.1996]")
