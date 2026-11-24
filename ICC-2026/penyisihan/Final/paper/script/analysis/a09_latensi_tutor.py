"""A09: latensi tutor LLM tanpa beban paralel (a08 memakai 8 utas sehingga latensinya bisa terlalu tinggi).

20 permintaan berurutan (10 mode sokratik sebelum submit, 10 mode penjelasan setelah submit) lewat tutor.ask() MVP.
Mencatat latensi total dan waktu sampai kata pertama tampil (jawaban dikirim bertahap sejak 18 Okt).
Keluaran: results/latensi_tutor.json.  Waktu jalan: +-3 menit.
"""
import json
import time

import numpy as np

import a08_tutor_mvp as A
from _common import RESULTS

ids = [c["id"] for c in A.cases.all_cases()][:10]
lat = {"sokratik": [], "penjelasan": []}
ttft = {"sokratik": [], "penjelasan": []}
for cid in ids:
    for sk, mode in (("A", "sokratik"), ("B", "penjelasan")):
        pub, sec = A.cases.public_case(cid), A.cases.secrets()[cid]
        g, sp = A.cases.masks(cid)["gt"], A.cases.spacing(cid)
        if sk == "A":
            facts = A.tutor.build_facts(pub, sec, "sebelum_submit", None, A.PROFIL)
        else:
            d = A.grading.grade_delineation(A.anotasi(g, sp), g, sp)
            facts = A.tutor.build_facts(pub, sec, "setelah_submit", {"delineasi": d, "kc": {}}, A.PROFIL)
        out = A.tutor.ask(mode, facts, A.pesan(sk, sec["findings"]))
        assert out["source"] == "llm", out["source"]
        lat[mode].append(out["latency_ms"] / 1000)
        ttft[mode].append(out["first_token_ms"] / 1000)
        print(cid, mode, out["latency_ms"], flush=True)
        time.sleep(1)
semua = lat["sokratik"] + lat["penjelasan"]
out = {m: dict(n=len(v), median=float(np.median(v)), p95=float(np.percentile(v, 95)), maks=float(max(v)))
       for m, v in {**lat, "semua": semua}.items()}
out["kata_pertama"] = {m: dict(n=len(v), median=float(np.median(v)), p95=float(np.percentile(v, 95)), maks=float(max(v)))
                      for m, v in {**ttft, "semua": ttft["sokratik"] + ttft["penjelasan"]}.items()}
out["model"] = A.tutor.MODEL
out["reasoning"] = A.tutor.REASONING
json.dump(out, open(RESULTS / "latensi_tutor.json", "w"), indent=1)
print(json.dumps(out, indent=1))
