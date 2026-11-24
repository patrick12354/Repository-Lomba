"""A07: uji fungsional ujung ke ujung terhadap kode MVP SINAPS (Final/mvp) yang sama dengan yang di-deploy.

API FastAPI dijalankan in-process (TestClient) dengan basis data SQLite sementara, lalu lima akun mahasiswa
uji mengerjakan seluruh bank kasus latihan lewat endpoint yang sama dengan yang dipanggil peramban:
  /api/next  -> kasus dipilih BKT     /api/submit -> dinilai terhadap lesion mask ahli
Setiap akun mewakili satu jenis kesalahan anotasi; anotasinya dibuat dari mask ahli dengan operasi geometris yang
sama dengan pipeline/eval_error_rules.py (bukan anotasi mahasiswa sungguhan).

Yang diukur:
  1. keberhasilan panggilan API (status 200) dan konsistensi siklus (kasus tidak berulang, BKT diperbarui)
  2. kebocoran kunci jawaban: respons sebelum submit tidak boleh memuat temuan/mask; folder publik tidak boleh
     memuat mask
  3. akurasi jenis kesalahan dengan ambang BAWAAN yang dipakai aplikasi (bukan ambang yang disetel per fold)
  4. kecocokan pemilih kasus dengan aturan "KC terlemah yang prasyaratnya terpenuhi" dan pembaruan BKT dengan
     persamaan (3)-(4)
  5. waktu proses server per endpoint (in-process, tanpa jaringan)
  6. latensi jaringan ke deployment Vercel (GET publik /api/health dan /api/kc, tanpa login)

Keluaran: results/mvp_e2e.json.  Waktu jalan: +-2 menit.
"""
import json
import os
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

import numpy as np
from scipy import ndimage

from _common import RESULTS, SCRIPT

MVP = SCRIPT.parents[1] / "mvp"
TMP = Path(tempfile.mkdtemp(prefix="sinaps_e2e_"))
os.environ["DATABASE_URL"] = f"sqlite:///{(TMP / 'e2e.db').as_posix()}"
os.environ.pop("OPENAI_API_KEY", None)          # tutor tidak diuji di sini (lihat a08)
sys.path.insert(0, str(MVP))

from fastapi.testclient import TestClient  # noqa: E402
from api.index import TEACHING, app  # noqa: E402
from sinaps import bkt, cases, db  # noqa: E402
from sinaps.grading import ADC_BINS, adc_bin  # noqa: E402
from sinaps.lesion import foci  # noqa: E402

DEPLOY = "https://mvp-lemon-ten.vercel.app"
TYPES = ["hampir_benar", "terlalu_luas", "terlalu_sempit", "lesi_terlewat", "salah_lokasi"]
INPLANE = np.zeros((3, 3, 3), bool)
INPLANE[:, :, 1] = ndimage.generate_binary_structure(2, 1)
rng = np.random.default_rng(7)
P_BENAR = {"K1": 0.85, "K2": 0.75, "K3": 0.6}  # peluang mahasiswa uji menjawab benar


def synth(g, spacing, kind):
    """Sama dengan pipeline/eval_error_rules.py: satu anotasi sintetis per jenis kesalahan."""
    if kind == "hampir_benar":
        edge = g & ~ndimage.binary_erosion(g, INPLANE)
        ring = ndimage.binary_dilation(g, INPLANE) & ~g
        p = g.copy()
        p[edge & (rng.random(g.shape) < rng.uniform(0.1, 0.3))] = False
        p[ring & (rng.random(g.shape) < rng.uniform(0.1, 0.3))] = True
        return p
    if kind == "terlalu_luas":
        return ndimage.binary_dilation(g, INPLANE, iterations=int(rng.integers(2, 5)))
    if kind == "terlalu_sempit":
        return ndimage.binary_erosion(g, INPLANE, iterations=int(rng.integers(2, 5)))
    if kind == "lesi_terlewat":
        labels, fs = foci(g, spacing)
        if len(fs) < 2:
            return None
        p = g.copy()
        for f in fs[-int(rng.integers(1, len(fs))):]:
            p[labels == f["label"]] = False
        return p
    ang, d = rng.uniform(0, 2 * np.pi), rng.uniform(8, 16)
    return ndimage.shift(g.astype(np.uint8), (d * np.cos(ang), d * np.sin(ang), 0), order=0) > 0


def timed(store, name, fn, *a, **kw):
    t0 = time.perf_counter()
    r = fn(*a, **kw)
    store.setdefault(name, []).append((time.perf_counter() - t0) * 1000)
    return r


BOCOR = ["findings", "gt_rle", "pred_rle", "hemisfer", "volume_ml", "jumlah_fokus", "slice_lesi_terbesar", "luaran"]


def main():
    c = TestClient(app)
    lat, status, bocor = {}, [], []
    # kunci jawaban tidak boleh ada di folder yang disajikan publik
    pub_files = [p.name for p in (MVP / "public" / "cases").rglob("*") if p.is_file()]
    mask_publik = [f for f in pub_files if f.endswith((".npz", ".nii", ".nii.gz")) or "mask" in f.lower()]

    r = c.post("/api/auth/register-dosen", json=dict(nama="Dosen Uji", username="dosen.uji", password="uji-e2e-01",
                                                     kode_dosen=os.environ.get("DOSEN_KEY") or "SINAPS2026"))
    dk = {"Authorization": f"Bearer {r.json()['token']}"}
    kode = c.post("/api/dosen/kelas", json={"nama": "Kelas Uji E2E"}, headers=dk).json()["kode"]

    n_practice = len([x for x in cases.all_cases() if x["id"] not in TEACHING])
    hasil, cek_target, cek_bkt, ulang, mastery_akhir = [], 0, 0, 0, []
    n_target = n_bkt = 0
    for si, kind in enumerate(TYPES):
        r = c.post("/api/auth/register", json=dict(nama=f"Mahasiswa Uji {si + 1}", nim=f"E2E{si:04d}",
                                                   password="uji-e2e-01", jenjang="klinik", kode_kelas=kode))
        status.append(r.status_code)
        h = {"Authorization": f"Bearer {r.json()['token']}"}
        seen = set()
        for _ in range(n_practice):
            r = timed(lat, "next", c.get, "/api/next", params={"baru": True}, headers=h)
            status.append(r.status_code)
            att = r.json()
            teks = json.dumps(att)
            bocor += [k for k in BOCOR if f'"{k}"' in teks]
            cid = att["case"]["id"]
            ulang += cid in seen
            seen.add(cid)
            # pemilih kasus: KC target harus sama dengan aturan di bkt.choose_target pada mastery saat itu
            exp_k, _ = bkt.choose_target(att["mastery"])
            n_target += 1
            cek_target += att["target_kc"] == exp_k
            # jawaban: K2 titik di pusat fokus terbesar, K6 anotasi sintetis
            g = cases.masks(cid)["gt"]
            sp = cases.spacing(cid)
            f = cases.secrets()[cid]["findings"]
            p = synth(g, sp, kind)
            k_eff = kind
            if p is None:                       # satu fokus: lesi_terlewat tidak bisa dibuat -> terlalu_sempit
                p, k_eff = synth(g, sp, "terlalu_sempit"), "terlalu_sempit"
            fz = np.argwhere(g)
            lab, n = ndimage.label(g)
            big = np.argwhere(lab == (np.bincount(lab.ravel())[1:].argmax() + 1))
            pt = big[np.argmin(((big - big.mean(0)) ** 2).sum(1))].tolist()
            # mahasiswa uji menjawab K1-K3 benar dengan peluang P_BENAR; bila salah, jawabannya dibuat keliru
            truth = db.get_attempt(att["attempt_id"])["seq_order"]
            k1 = dict(truth) if rng.random() < P_BENAR["K1"] else dict(zip(truth, list(truth.values())[1:] + list(truth.values())[:1]))
            hemi = f["hemisfer"] if rng.random() < P_BENAR["K2"] else {"kiri": "kanan"}.get(f["hemisfer"], "kiri")
            abin = adc_bin(f["adc_relatif_lesi"])
            if rng.random() >= P_BENAR["K3"]:
                abin = [b for b, _, _ in ADC_BINS if b != abin][int(rng.integers(0, 3))]
            body = dict(attempt_id=att["attempt_id"], k1=k1, k2_point=pt, k2_hemisfer=hemi, k3_adc_bin=abin,
                        k3_restriksi=f["restriksi_sejati"], mask_rle=cases.rle_encode(p))
            r = timed(lat, "submit", c.post, "/api/submit", json=body, headers=h)
            status.append(r.status_code)
            res = r.json()
            # BKT: mastery_after harus sama dengan persamaan (3)-(4) diterapkan pada mastery_before
            for k, v in res["kc"].items():
                n_bkt += 1
                cek_bkt += abs(res["mastery_after"][k] - bkt.update(res["mastery_before"][k], v["benar"])) < 1e-9
            d = res["delineasi"]
            hasil.append(dict(akun=si, kasus=cid, tier=att["tier"], target=att["target_kc"], jenis=k_eff,
                              pred=d["jenis_kesalahan"], dice=d["dice"], recall=d["lesion_recall"], vol_err=d["vol_err"],
                              k6=res["kc"]["K6"]["benar"],
                              k2=res["kc"]["K2"]["benar"], k3=res["kc"]["K3"]["benar"], k1=res["kc"]["K1"]["benar"],
                              n_fokus=len(fz) and f["jumlah_fokus"],
                              mastery={k: round(v, 4) for k, v in res["mastery_after"].items()}))
        # tutor sebelum submit (templat offline): tidak boleh menyebut hemisfer
        att = c.get("/api/next", params={"baru": True}, headers=h).json()
        r = timed(lat, "tutor_offline", c.post, "/api/tutor", headers=h,
                  json=dict(attempt_id=att["attempt_id"], mode="sokratik", message="Lesinya di hemisfer mana?"))
        status.append(r.status_code)
        mastery_akhir.append(c.get("/api/me", headers=h).json().get("mastery"))
        print(kind, "selesai", len(seen), "kasus", flush=True)

    r = timed(lat, "dosen_overview", c.get, "/api/dosen/overview", headers=dk)
    status.append(r.status_code)
    ov = r.json()

    benar = [h["jenis"] == h["pred"] for h in hasil]
    per_jenis = {}
    for t in TYPES:
        rows = [h for h in hasil if h["jenis"] == t]
        if rows:
            per_jenis[t] = dict(n=len(rows), recall=float(np.mean([h["pred"] == t for h in rows])),
                                dice_median=float(np.median([h["dice"] for h in rows])))
    conf = {t: {u: sum(1 for h in hasil if h["jenis"] == t and h["pred"] == u) for u in TYPES} for t in TYPES}

    # latensi jaringan ke deployment (endpoint publik, tanpa data pribadi)
    net = {}
    for ep in ["/api/health", "/api/kc"]:
        ms = []
        for i in range(15):
            t0 = time.perf_counter()
            try:
                with urllib.request.urlopen(DEPLOY + ep, timeout=30) as resp:
                    resp.read()
                    ok = resp.status == 200
            except Exception as e:  # noqa: BLE001
                print("  gagal", ep, e)
                ok = False
            if ok:
                ms.append((time.perf_counter() - t0) * 1000)
        net[ep] = dict(n=len(ms), pertama_ms=ms[0] if ms else None,
                       median_ms=float(np.median(ms[1:])) if len(ms) > 1 else None,
                       p95_ms=float(np.percentile(ms[1:], 95)) if len(ms) > 1 else None)

    out = dict(
        n_akun=len(TYPES), n_kasus_latihan=n_practice, n_submit=len(hasil), n_panggilan=len(status),
        n_status_200=int(sum(s == 200 for s in status)), kasus_berulang=int(ulang),
        kebocoran_sebelum_submit=sorted(set(bocor)), mask_di_folder_publik=mask_publik, n_file_publik=len(pub_files),
        target_sesuai_aturan=cek_target / n_target, n_target=n_target,
        bkt_sesuai_persamaan=cek_bkt / n_bkt, n_bkt=n_bkt,
        akurasi_jenis=float(np.mean(benar)), per_jenis=per_jenis, confusion=conf,
        k1_benar=float(np.mean([h["k1"] for h in hasil])), k2_benar=float(np.mean([h["k2"] for h in hasil])),
        k3_benar=float(np.mean([h["k3"] for h in hasil])),
        latensi_server_ms={k: dict(n=len(v), median=float(np.median(v)), p95=float(np.percentile(v, 95)),
                                   maks=float(np.max(v))) for k, v in lat.items()},
        latensi_vercel=net,
        dosen_overview_keys=sorted(ov.keys()) if isinstance(ov, dict) else None,
        urutan_target=[h["target"] for h in hasil if h["akun"] == 0],
        target_per_akun={i: [h["target"] for h in hasil if h["akun"] == i] for i in range(len(TYPES))},
        mastery_akhir=mastery_akhir,
        urutan_tier=[h["tier"] for h in hasil if h["akun"] == 0],
        rows=hasil,
    )
    json.dump(out, open(RESULTS / "mvp_e2e.json", "w"), indent=1)
    print(json.dumps({k: v for k, v in out.items() if k not in ("rows", "confusion")}, indent=1))


if __name__ == "__main__":
    main()
