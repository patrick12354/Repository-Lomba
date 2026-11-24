import _path  # noqa: F401  -- menaruh Case 1/ di sys.path
import numpy as np, time, lab_common as C, lab_cnn3 as N3
z=np.load(C.CACHE/"cnn_input.npz"); sw=C.make_sw(power=0.5)
t0=time.time()
oof,pte=N3.run(z["Wtr"],z["Str"],z["Wte"],z["Ste"],sw,seeds=(0,1,2),epochs=70,lr=2e-3,arch=N3.Net4)
np.savez(C.CACHE/"cnn4.npz",oof=oof,pte=pte)
print(f"CNN4(GRU) {time.time()-t0:.0f}s cv_lama={C.eb_twmae(C.y,oof,C.ev):.4f} lb_real={C.lb_real(oof):.4f} bias={C.bias_rnd(oof):+.3f}")
for n in ["cnn3_avg","cnn3_dir","regA"]:
    print(f"  korelasi vs {n}: {np.corrcoef(oof,np.load(C.CACHE/f'{n}.npz')['oof'])[0,1]:.3f}")
