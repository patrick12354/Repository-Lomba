import _path
import numpy as np, time, lab_common as C, lab_cnn3 as N3
z=np.load(C.CACHE/"cnn_input.npz"); sw=C.make_sw(power=0.5)
t0=time.time()
oof,pte=N3.run(z["Wtr"],z["Str"],z["Wte"],z["Ste"],sw,seeds=(0,1,2),
               epochs=85,lr=2e-3,avg_last=12,arch=N3.Net8)
np.savez(C.CACHE/"cnn8.npz",oof=oof,pte=pte)
print("CNN8 %.0fs cv_lama=%.4f lb_real=%.4f dec=%.4f rnd=%.4f bias=%+.3f"
      %(time.time()-t0,C.eb_twmae(C.y,oof,C.ev),C.lb_real(oof),
        C.part_real(oof,True),C.part_real(oof,False),C.bias_rnd(oof)))
for m in ["cnn3_avg","cnn3_dir","cnn5","cnn6","resB_dep"]:
    try: print("  korelasi vs %s: %.3f"%(m,np.corrcoef(oof,np.load(C.CACHE/f"{m}.npz")["oof"])[0,1]))
    except FileNotFoundError: pass
