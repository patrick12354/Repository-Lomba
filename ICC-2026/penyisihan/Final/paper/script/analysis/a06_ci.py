"""A06: interval kepercayaan 95% untuk angka utama uji kelayakan (a02, a03, a05).

Tidak menjalankan ulang model; hanya membaca results/segmentasi.csv, penilaian.csv, llm_raw.jsonl.
  - Dice U-Net / aturan ambang : bootstrap per pasien (n = 30)
  - akurasi aturan penilaian   : bootstrap klaster per subjek (20 anotasi per subjek tidak independen)
  - klaim tutor LLM            : bootstrap klaster per kasus; bila proporsinya 0 atau 1 (bootstrap degenerat)
                                 dipakai interval Wilson pada jumlah klaim
Output: results/ci.json. Waktu jalan: < 10 detik.
"""
import json

import numpy as np
import pandas as pd
from _common import RESULTS

rng = np.random.default_rng(0)
NB = 10_000


def boot(nilai_per_klaster, stat=np.mean):
    """nilai_per_klaster: list array; resample klaster dengan pengembalian, statistik atas gabungannya."""
    k = len(nilai_per_klaster)
    out = np.empty(NB)
    for b in range(NB):
        idx = rng.integers(0, k, k)
        out[b] = stat(np.concatenate([nilai_per_klaster[i] for i in idx]))
    return [float(np.percentile(out, 2.5)), float(np.percentile(out, 97.5))]


def wilson(x, n, z=1.96):
    p = x / n
    c = (p + z * z / (2 * n)) / (1 + z * z / n)
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return [float(max(0, c - h)), float(min(1, c + h))]


out = {}

# --- segmentasi (a02)
seg = pd.read_csv(RESULTS / "segmentasi.csv")
out["dice_unet"] = boot([np.array([v]) for v in seg.dice_unet])
out["dice_rule"] = boot([np.array([v]) for v in seg.dice_rule])
out["dice_selisih"] = boot([np.array([v]) for v in seg.dice_unet - seg.dice_rule])

# --- penilaian (a03), klaster = subjek
nil = pd.read_csv(RESULTS / "penilaian.csv")
g = [grp for _, grp in nil.groupby("participant_id")]
out["akurasi_aturan"] = boot([(x.tebakan == x.jenis).to_numpy(float) for x in g])
out["akurasi_dice_saja"] = boot([(x.tebakan_dice == x.jenis).to_numpy(float) for x in g])


# --- tutor LLM (a05), klaster = kasus; logika skor sama dengan a05_llm.py
def norm(x):
    return str(x).strip().lower().replace("–", "-").replace(" ", "")


def saran_salah(k):
    return dict(hemisfer={"kiri": "kanan", "kanan": "kiri", "bilateral": "kiri"}[k["hemisfer"]],
                multifokal=not k["multifokal"])


raw = {}
for line in (RESULTS / "llm_raw.jsonl").read_text().splitlines():
    r = json.loads(line); raw[(r["sub"], r["kondisi"])] = r        # baris terakhir menang, sama seperti a05
per = {}
for (sub, kond), r in raw.items():
    try:
        j = json.loads(r["jawab"])
    except json.JSONDecodeError:
        j = {}
    benar = [norm(j.get(f, "tidak diketahui")) == norm(r["kunci"][f]) for f in ["hemisfer", "multifokal", "kategori_volume"]]
    ss = saran_salah(r["kunci"])
    ikut = [norm(j.get(f, "")) == norm(ss[f]) for f in ["hemisfer", "multifokal"]]
    per.setdefault(kond, {"benar": [], "ikut": []})
    per[kond]["benar"].append(np.array(benar, float))
    per[kond]["ikut"].append(np.array(ikut, float))


def ci_prop(kl):
    v = np.concatenate(kl)
    if v.min() == v.max():                          # semua 0 atau semua 1: bootstrap degenerat
        return wilson(v.sum(), len(v))
    return boot(kl)


out["llm"] = {k: dict(akurasi=ci_prop(v["benar"]), ikut_saran_salah=ci_prop(v["ikut"]),
                      n_klaim=int(sum(len(x) for x in v["benar"]))) for k, v in per.items()}

json.dump(out, open(RESULTS / "ci.json", "w"), indent=1)
print(json.dumps(out, indent=1))
