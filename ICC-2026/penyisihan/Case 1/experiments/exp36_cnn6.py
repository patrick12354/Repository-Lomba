import _path
import numpy as np, time, lab_common as C, lab_cnn3 as N3
z=np.load(C.CACHE/"cnn_input.npz"); sw=C.make_sw(power=0.5)
t0=time.time()
oof,pte=N3.run(z["Wtr"],z["Str"],z["Wte"],z["Ste"],sw,seeds=(0,1,2),
               epochs=90,lr=1.5e-3,avg_last=12,arch=N3.Net6)
np.savez(C.CACHE/"cnn6.npz",oof=oof,pte=pte)
print("CNN6(TRF) %.0fs cv_lama=%.4f lb_real=%.4f dec=%.4f rnd=%.4f bias=%+.3f"
      %(time.time()-t0,C.eb_twmae(C.y,oof,C.ev),C.lb_real(oof),
        C.part_real(oof,True),C.part_real(oof,False),C.bias_rnd(oof)))
for n in ["cnn3_avg","cnn3_dir","cnn5","resB_dep"]:
    try: print("  korelasi vs %s: %.3f"%(n,np.corrcoef(oof,np.load(C.CACHE/f"{n}.npz")["oof"])[0,1]))
    except FileNotFoundError: pass
