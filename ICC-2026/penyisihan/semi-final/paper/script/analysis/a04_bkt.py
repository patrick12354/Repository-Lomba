"""A04: simulasi personalisasi berbasis Bayesian Knowledge Tracing (BKT).

Belum ada data log mahasiswa, jadi ini SIMULASI: 1.000 mahasiswa sintetis dengan parameter BKT
acak mengerjakan 60 kasus. Dua kebijakan pemilihan kasus dibandingkan:
  - acak     : kasus diambil acak dari bank kasus (setara modul latihan statis)
  - adaptif  : sistem memilih kasus yang melatih KC dengan estimasi mastery terendah
               yang prasyaratnya sudah dikuasai (estimasi pakai BKT standar, bukan parameter asli)
Output: results/bkt.json (kurva rata-rata penguasaan per langkah)
Waktu jalan: +-3 menit (termasuk analisis sensitivitas).
"""
import json
import numpy as np
from _common import RESULTS

rng = np.random.default_rng(42)
KC = ["Sekuens", "Deteksi DWI", "Konfirmasi ADC", "Teritori vaskular", "Usia lesi", "Delineasi"]
K, N, T = len(KC), 1000, 60
PRASYARAT = {0: [], 1: [0], 2: [1], 3: [1], 4: [2], 5: [3]}
# bank kasus: tiap kasus melatih 1 KC utama (+ KC prasyaratnya ikut teruji)
BANK = np.repeat(np.arange(K), 20)
G, S = 0.2, 0.1                                 # guess, slip
EST = dict(L0=0.15, T=0.15)                     # parameter yang dipakai sistem (bukan asli)


def update(pl, benar, G=G, S=S):
    post = pl * (1 - S) / (pl * (1 - S) + (1 - pl) * G) if benar else pl * S / (pl * S + (1 - pl) * (1 - G))
    return post + (1 - post) * EST["T"]


def jalan(kebijakan, N=N, PENALTI=0.25, G=G, S=S):
    kurva = np.zeros((N, T + 1))
    for n in range(N):
        L0 = rng.uniform(.02, .3, K); PT = rng.uniform(.06, .22, K)
        tahu = rng.random(K) < L0
        est = np.full(K, EST["L0"])
        kurva[n, 0] = tahu.mean()
        for t in range(T):
            if kebijakan == "acak":
                k = int(rng.choice(BANK))
            else:
                siap = [k for k in range(K) if est[k] < .95 and all(est[p] >= .95 for p in PRASYARAT[k])]
                k = min(siap, key=lambda k: est[k]) if siap else int(np.argmin(est))
            # belajar hanya efektif bila prasyarat benar-benar dikuasai (zone of proximal development)
            siap_asli = all(tahu[p] for p in PRASYARAT[k])
            benar = (rng.random() > S) if tahu[k] else (rng.random() < G)
            est[k] = update(est[k], benar, G, S)
            if not tahu[k] and rng.random() < PT[k] * (1.0 if siap_asli else PENALTI):
                tahu[k] = True
            kurva[n, t + 1] = tahu.mean()
    return kurva


hasil = {}
for kb in ["acak", "adaptif"]:
    c = jalan(kb)
    hasil[kb] = dict(mean=c.mean(0).tolist(), q25=np.percentile(c, 25, 0).tolist(), q75=np.percentile(c, 75, 0).tolist(),
                     kasus_80=float(np.nanmedian([np.argmax(r >= .8) if (r >= .8).any() else np.nan for r in c])),
                     frac_capai_80=float(np.mean([(r >= .8).any() for r in c])),
                     tuntas_akhir=float((c[:, -1] == 1).mean()))
    print(kb, {k: v for k, v in hasil[kb].items() if not isinstance(v, list)}, "akhir", round(c[:, -1].mean(), 3), "@30", round(c[:, 30].mean(), 3))
# analisis sensitivitas: besarnya selisih bergantung pada asumsi prasyarat (PENALTI = laju belajar relatif
# bila prasyarat belum dikuasai; 1,0 = prasyarat tidak berpengaruh sama sekali) dan pada guess/slip.
sens = []
for pen in [0.25, 0.5, 0.75, 1.0]:
    for g_, s_ in [(0.1, 0.05), (0.2, 0.1), (0.3, 0.15)]:
        a, d = jalan("acak", 400, pen, g_, s_), jalan("adaptif", 400, pen, g_, s_)
        sens.append(dict(penalti=pen, G=g_, S=s_, acak=float(a[:, -1].mean()), adaptif=float(d[:, -1].mean()),
                         tuntas_acak=float((a[:, -1] == 1).mean()), tuntas_adaptif=float((d[:, -1] == 1).mean())))
        print(sens[-1], flush=True)
hasil["sensitivitas"] = sens
hasil["KC"] = KC; hasil["N"] = N; hasil["T"] = T
json.dump(hasil, open(RESULTS / "bkt.json", "w"))
