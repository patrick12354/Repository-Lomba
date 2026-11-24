import _path  # noqa: F401  -- menaruh Case 1/ di sys.path
import numpy as np, torch, time, sys
import lab_common as C, lab_cnn as N, lab_models as M
print("device", N.DEV, torch.cuda.get_device_name(0) if N.DEV=="cuda" else "")
cw = C.CACHE/"cnn_input.npz"
if cw.exists():
    z=np.load(cw); Wtr,Str,Wte,Ste = z["Wtr"],z["Str"],z["Wte"],z["Ste"]
else:
    Wtr,Str = N.build_input(np.load(C.DATA/"train"/"train_waveforms.npy"), C.train)
    Wte,Ste = N.build_input(np.load(C.DATA/"test"/"test_waveforms.npy"),  C.test)
    np.savez(cw, Wtr=Wtr,Str=Str,Wte=Wte,Ste=Ste)
print("input", Wtr.shape, Str.shape)
SWNAME = sys.argv[1] if len(sys.argv)>1 else "cap8"
sw = {"cap8":C.make_sw(8),"sqrt":C.make_sw(power=0.5),"base":C.SW}[SWNAME]
t0=time.time()
oof,pte = N.run_cnn(Wtr,Str,Wte,Ste, C.y, sw, seeds=(0,1,2))
np.savez(C.CACHE/f"cnn_{SWNAME}.npz", oof=oof, pte=pte)
print(f"CNN({SWNAME}) {time.time()-t0:.0f}s  cv_lama={C.eb_twmae(C.y,oof,C.ev):.4f} "
      f"cv_real={C.cv_real(oof):.4f} dec={C.part_real(oof,True):.4f} rnd={C.part_real(oof,False):.4f} "
      f"lb_real={C.lb_real(oof):.4f} bias={C.bias_rnd(oof):+.3f}")
oA,_=M.cached("regA",None)
print("korelasi dgn regA:", np.corrcoef(oof,oA)[0,1].round(4))
