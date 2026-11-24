import _path  # noqa: F401  -- menaruh Case 1/ di sys.path
import numpy as np, torch, time
import lab_common as C, lab_cnn as N
cw=C.CACHE/"spec_input.npz"
if cw.exists():
    z=np.load(cw); Wtr,Str,Wte,Ste=z["Wtr"],z["Str"],z["Wte"],z["Ste"]
else:
    Wtr,Str=N.build_spec(np.load(C.DATA/"train"/"train_waveforms.npy"),C.train)
    Wte,Ste=N.build_spec(np.load(C.DATA/"test"/"test_waveforms.npy"),C.test)
    np.savez(cw,Wtr=Wtr,Str=Str,Wte=Wte,Ste=Ste)
print("spec input",Wtr.shape,flush=True)
sw=C.make_sw(power=0.5); t0=time.time()
oof,pte=N.run_spec(Wtr,Str,Wte,Ste,C.y,sw,seeds=(0,1))
np.savez(C.CACHE/"spec_sqrt.npz",oof=oof,pte=pte)
print(f"SPEC {time.time()-t0:.0f}s cv_lama={C.eb_twmae(C.y,oof,C.ev):.4f} lb_real={C.lb_real(oof):.4f} bias={C.bias_rnd(oof):+.3f}")
for n in ["regA","cnn_sqrt"]:
    print(f"  korelasi vs {n}: {np.corrcoef(oof,np.load(C.CACHE/f'{n}.npz')['oof'])[0,1]:.3f}")
