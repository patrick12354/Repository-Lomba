import _path  # noqa: F401  -- menaruh Case 1/ di sys.path
import numpy as np, time, lab_common as C, lab_cnn3 as N3
z=np.load(C.CACHE/"cnn_input.npz")
sw=C.make_sw(power=0.5); t0=time.time()
oof,pte=N3.run(z["Wtr"],z["Str"],z["Wte"],z["Ste"],sw)
np.savez(C.CACHE/"cnn3.npz",oof=oof,pte=pte)
print(f"CNN3 {time.time()-t0:.0f}s cv_lama={C.eb_twmae(C.y,oof,C.ev):.4f} lb_real={C.lb_real(oof):.4f} "
      f"dec={C.part_real(oof,True):.4f} rnd={C.part_real(oof,False):.4f} bias={C.bias_rnd(oof):+.3f}")
for n in ["cnnres","regA"]:
    print(f"  korelasi vs {n}: {np.corrcoef(oof,np.load(C.CACHE/f'{n}.npz')['oof'])[0,1]:.3f}")
print("pembanding: cnnres lb_real=0.2206 | cnn_sqrt 0.2232")
