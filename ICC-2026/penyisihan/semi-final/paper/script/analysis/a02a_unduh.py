"""A02a: unduh DWI (TRACE) + ADC untuk subjek SOOP tambahan sebagai data latih segmentasi.

30 subjek sampel (sample_subjects.txt) TIDAK ikut diunduh ulang dan TIDAK dipakai untuk training,
supaya bisa menjadi test set held-out di a02_segmentasi.py.
Subjek dipilih acak (seed 42) dari pasien yang punya lesion mask akut tidak kosong.
Sumber: bucket publik OpenNeuro ds004889 (CC0). +-1,2 MB per subjek.

Output: data/train_extra/sub-*/dwi/*.nii.gz, data/train_extra/subjects.txt
Waktu jalan: +-5 menit (tergantung koneksi).
"""
import sys, urllib.request
from concurrent.futures import ThreadPoolExecutor
import nibabel as nib
import numpy as np
from _common import DATA

N = int(sys.argv[1]) if len(sys.argv) > 1 else 250
URL = "https://s3.amazonaws.com/openneuro.org/ds004889/{s}/dwi/{s}_rec-{r}_dwi.nii.gz"
OUT = DATA / "train_extra"

sampel = set(open(DATA / "sample_subjects.txt").read().split())
kandidat = []
for d in sorted((DATA / "derivatives/lesion_masks").iterdir()):
    f = d / "dwi" / f"{d.name}_space-TRACE_desc-lesionAcute_mask.nii.gz"
    if d.name not in sampel and f.exists() and (np.asanyarray(nib.load(f).dataobj) > 0).any():
        kandidat.append(d.name)
pilih = list(np.random.default_rng(42).permutation(kandidat))


def unduh(s):
    try:
        for r in ["TRACE", "ADC"]:
            p = OUT / s / "dwi" / f"{s}_rec-{r}_dwi.nii.gz"
            if not p.exists():
                p.parent.mkdir(parents=True, exist_ok=True)
                urllib.request.urlretrieve(URL.format(s=s, r=r), p)
        return s
    except Exception as e:                        # sebagian subjek tidak punya ADC/TRACE
        print("lewat", s, e, flush=True)
        return None


ok = []
with ThreadPoolExecutor(8) as ex:
    for s in ex.map(unduh, pilih[: int(N * 1.3)]):
        if s and len(ok) < N:
            ok.append(s)
open(OUT / "subjects.txt", "w").write("\n".join(ok))
print(f"{len(kandidat)} kandidat, {len(ok)} subjek terunduh -> {OUT}")
