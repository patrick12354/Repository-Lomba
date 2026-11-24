import _path
import numpy as np, time, lab_common as C, lab_cnn3 as N3
z=np.load(C.CACHE/"cnn_input.npz"); sw=C.make_sw(power=0.5)
t0=time.time()
oof,pte=N3.run(z["Wtr"],z["Str"],z["Wte"],z["Ste"],sw,seeds=(0,1,2),
               epochs=100,lr=2e-3,avg_last=12,arch=N3.Net5)
np.savez(C.CACHE/"cnn5.npz",oof=oof,pte=pte)
print("CNN5 %.0fs cv_lama=%.4f lb_real=%.4f dec=%.4f rnd=%.4f bias=%+.3f"
      %(time.time()-t0,C.eb_twmae(C.y,oof,C.ev),C.lb_real(oof),
        C.part_real(oof,True),C.part_real(oof,False),C.bias_rnd(oof)))
for n in ["cnn3_avg","cnn3_dir","resB_dep"]:
    print("  korelasi vs %s: %.3f"%(n,np.corrcoef(oof,np.load(C.CACHE/f"{n}.npz")["oof"])[0,1]))
print("pembanding: cnn3 0.2091 | cnn3_avg 0.2074 | cnn3_dir 0.2116")
