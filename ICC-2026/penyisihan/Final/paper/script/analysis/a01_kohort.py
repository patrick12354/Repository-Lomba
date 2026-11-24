"""A01: statistik kohort SOOP (participants.tsv) + morfologi semua lesion mask.

Output: results/kohort_mask.csv (satu baris per subjek ber-mask), results/kohort.json
Waktu jalan: +-2 menit (membaca 1.456 mask).
"""
import json
import nibabel as nib
import numpy as np
import pandas as pd
from scipy import ndimage
from _common import DATA, RESULTS

FOKUS_MIN = 0.1  # ml; fokus lebih kecil dari ini dianggap bintik, tidak dihitung sebagai fokus bermakna

part = pd.read_csv(DATA / "participants.tsv", sep="\t", na_values="n/a")
part["age"] = pd.to_numeric(part.age.astype(str).str.replace("+", ""), errors="coerce")  # "89+" -> 89
rows = []
for d in sorted((DATA / "derivatives/lesion_masks").glob("sub-*")):
    f = d / "dwi" / f"{d.name}_space-TRACE_desc-lesionAcute_mask.nii.gz"
    if not f.exists():
        f = d / "dwi" / f"{d.name}_space-TRACE_desc-lesion_mask.nii.gz"
    if not f.exists():
        continue
    im = nib.load(f)
    m = np.asanyarray(im.dataobj) > 0
    vox_ml = float(np.prod(im.header.get_zooms()[:3])) / 1000.0
    lab, n = ndimage.label(m, structure=np.ones((3, 3, 3)))  # konektivitas 26
    fv = ndimage.sum(m, lab, range(1, n + 1)) * vox_ml if n else np.array([])
    z = np.where(m.any(axis=(0, 1)))[0]
    rows.append(dict(participant_id=d.name, vol_ml=m.sum() * vox_ml, n_foci=n, n_foci_sig=int((fv >= FOKUS_MIN).sum()),
                     n_slice=len(z), slice_mm=float(im.header.get_zooms()[2]),
                     acute=f.name.endswith("lesionAcute_mask.nii.gz")))
mk = pd.DataFrame(rows)
# indeks kesulitan komposit: lesi makin kecil dan makin banyak fokus bermakna -> makin sulit.
# D = -log10(volume total) + log2(jumlah fokus bermakna); tingkat dibagi per tersil D.
pos_mk = mk.vol_ml > 0
mk["D"] = np.nan
mk.loc[pos_mk, "D"] = -np.log10(mk.vol_ml[pos_mk]) + np.log2(mk.n_foci_sig[pos_mk].clip(lower=1))
t1, t2 = mk.D.quantile([1 / 3, 2 / 3])
mk["tingkat"] = np.where(mk.D <= t1, "mudah", np.where(mk.D <= t2, "sedang", "sulit"))
df = part.merge(mk, on="participant_id", how="right")
df.to_csv(RESULTS / "kohort_mask.csv", index=False)

pos = df[df.vol_ml > 0]
out = dict(
    n_participants=int(len(part)),
    n_mask=int(len(mk)),
    n_mask_nonempty=int((mk.vol_ml > 0).sum()),
    n_nihss=int(part.nihss.notna().sum()),
    n_rankin=int(part.gs_rankin_6isdeath.notna().sum()),
    vol_median=float(pos.vol_ml.median()),
    vol_q1=float(pos.vol_ml.quantile(.25)),
    vol_q3=float(pos.vol_ml.quantile(.75)),
    frac_vol_lt1=float((pos.vol_ml < 1).mean()),
    frac_vol_gt50=float((pos.vol_ml > 50).mean()),
    frac_multifocal=float((pos.n_foci > 1).mean()),
    n_acute_mask=int(mk.acute.sum()),
    foci_median=float(pos.n_foci.median()),
    age_median=float(part.age.median()),
    nihss_median=float(part.nihss.median()),
    spearman_vol_nihss=float(pos[["vol_ml", "nihss"]].dropna().corr("spearman").iloc[0, 1]),
    n_vol_nihss=int(pos[["vol_ml", "nihss"]].dropna().shape[0]),
    frac_multifocal_sig=float((pos.n_foci_sig > 1).mean()),
    D_t1=float(t1), D_t2=float(t2),
    tingkat={t: dict(n=int((g := pos[pos.tingkat == t]).shape[0]), vol_median=float(g.vol_ml.median()),
                     foci_median=float(g.n_foci_sig.median()), frac_lt1=float((g.vol_ml < 1).mean()))
             for t in ["mudah", "sedang", "sulit"]},
)
json.dump(out, open(RESULTS / "kohort.json", "w"), indent=1)
print(json.dumps(out, indent=1))
