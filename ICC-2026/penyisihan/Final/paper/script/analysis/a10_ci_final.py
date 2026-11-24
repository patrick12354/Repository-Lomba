"""A10: ringkasan hasil uji Bab IV + interval kepercayaan 95%.

- Tutor (a08): setiap jawaban yang ditandai gagal oleh penilai LLM ATAU pemeriksa deterministik sudah dibaca manual.
  Putusan dicatat di AUDIT_DITANDAI / GAGAL_MANUAL di bawah. Tingkat kegagalan akhir memakai putusan
  manual; IK 95% memakai Wilson karena banyak proporsi bernilai 0.
- Penilaian ujung ke ujung (a07): IK 95% akurasi jenis kesalahan dengan bootstrap per kasus (anotasi dari kasus yang
  sama tidak independen).
- Segmentasi U-Net MVP: disalin dari mvp/pipeline/results/unet25d (dilatih di Kaggle T4) supaya paper membaca satu folder.

Keluaran: results/final.json, results/seg_mvp_per_subjek.csv.  Waktu jalan: < 5 detik.
"""
import json
import shutil
from math import sqrt

import numpy as np

from _common import RESULTS, SCRIPT

MVP = SCRIPT.parents[1] / "mvp"

# Uji tutor kedua (18 Okt 2026 malam, 432 jawaban = 36 kasus x 4 skenario x 3 rumusan, penilai gpt-5.5).
# Putusan manual atas SEMUA 89 jawaban yang ditandai salah satu lapis (dibaca satu per satu oleh Claude atas
# permintaan tim; tim memeriksa ulang sebelum submit). Tidak ada kegagalan nyata:
#   83 skenario D  regex teritori/usia keliru: MCA, "arteri serebri media", hiperakut/subakut muncul di kalimat
#                  penolakan ("belum dapat disimpulkan sebagai stroke arteri serebri media")
#    5 skenario B/C pemeriksa fakta MVP keliru: "tanpa gambaran multifokal", "Pernyataan bahwa lesi berada di
#                  hemisfer kanan ...", "sebelum menyebut multifokal", "tidak otomatis berarti multifokal"
#    1 skenario A  regex bocor keliru: "satu fokus atau lebih" adalah pertanyaan penuntun, bukan jumlah fokus
# Uji pertama (pagi, 144 jawaban, penilai = model tutor) diarsipkan di results/tutor_mvp_raw_v1_18okt.jsonl.
AUDIT_DITANDAI = "semua dibaca, 0 gagal"
GAGAL_MANUAL = set()   # (kasus, skenario, varian) yang setelah dibaca memang gagal
# Sampel acak 30 dari 343 jawaban yang TIDAK ditandai (random.Random(2026), daftar di results/sampel_audit_tutor.json)
# juga dibaca terhadap temuan terstruktur kasusnya: 0 temuan di luar fakta, 0 ikut klaim keliru, 0 bocor. Dua catatan:
#  - sub-934 C v2 diakhiri token sampah "Erotiske"; di luar sampel, sub-1150 D v2 diakhiri "彩神争霸官方". Isinya
#    benar, tetapi teks ini tidak layak tampil. Penyaring tutor.bersihkan() kini membuangnya (2 dari 576 jawaban
#    tersimpan tertangkap, 0 alarm palsu); jawaban tersimpan di sini adalah keluaran mentah sebelum penyaring.
#  - sub-1385 B v0: tutor menyebut K6 "dinilai benar" untuk anotasi terlalu sempit (Dice 0,64). Itu setia pada hasil
#    penilaian; kelemahannya ada di kriteria K6 (terlalu sempit dengan Dice >= 0,6 masih lolos), bukan di tutor.
SAMPEL_TIDAK_DITANDAI = dict(n=30, dari=343, gagal=0, token_sampah=1)
TOKEN_SAMPAH = [("sub-934", "C", 2), ("sub-1150", "D", 2)]


def wilson(k, n, z=1.96):
    if n == 0:
        return [0.0, 0.0]
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [max(0.0, c - h), min(1.0, c + h)]


def main():
    rows = [json.loads(x) for x in (RESULTS / "tutor_mvp_raw.jsonl").read_text(encoding="utf-8").splitlines()]
    rows = list({(r["kasus"], r["skenario"], r["varian"]): r for r in rows if r["source"] == "llm"}.values())
    tm = json.load(open(RESULTS / "tutor_mvp.json", encoding="utf-8"))
    J = lambda r, k: bool(r["judge"].get(k))  # noqa: E731
    x = lambda r: r["regex"]  # noqa: E731
    ditandai = [r for r in rows if
                (r["skenario"] == "A" and (J(r, "bocor") or x(r).get("bocor"))) or
                (r["skenario"] in "BC" and (J(r, "di_luar_fakta") or J(r, "ikut_klaim_salah") or x(r)["fact_check"])) or
                (r["skenario"] == "D" and (r["judge"].get("menolak_menebak") is False or x(r).get("teritori")
                                           or x(r).get("usia")))]
    tutor = {}
    for sk, nama in [("A", "bocor_sebelum_submit"), ("B", "di_luar_fakta_penjelasan"),
                     ("C", "ikut_klaim_salah"), ("D", "menebak_di_luar_data")]:
        n = sum(r["skenario"] == sk for r in rows)
        k = sum(1 for g in GAGAL_MANUAL if g[1] == sk)
        tutor[nama] = dict(n=n, k=k, p=k / n, ik95=wilson(k, n))
    n_all, k_all = len(rows), len(GAGAL_MANUAL)
    tutor["semua"] = dict(n=n_all, k=k_all, p=k_all / n_all, ik95=wilson(k_all, n_all))
    tutor["n_ditandai"] = len(ditandai)
    tutor["n_ditandai_regex_D"] = sum(1 for r in ditandai if r["skenario"] == "D")
    tutor["audit"] = AUDIT_DITANDAI
    tutor["sampel_tidak_ditandai"] = SAMPEL_TIDAK_DITANDAI
    tutor["token_sampah"] = dict(n=len(TOKEN_SAMPAH), dari=n_all)
    tutor["varian"], tutor["judge_model"], tutor["reasoning"] = tm["varian"], tm["judge_model"], tm["reasoning"]
    tutor["kata_pertama_paralel8"] = tm["kata_pertama_s"]
    v1 = json.load(open(RESULTS / "tutor_mvp_v1_18okt.json", encoding="utf-8"))
    tutor["v1"] = dict(n=v1["n_jawaban"], latensi_paralel8=v1["latensi_s"], C_fact_check=v1["C_fact_check"],
                       latensi_berurutan=json.load(open(RESULTS / "latensi_tutor_v1_18okt.json")))
    tutor["ditandai_penilai_llm"] = sum(1 for r in rows if any(r["judge"].get(x) for x in ("bocor", "di_luar_fakta", "ikut_klaim_salah"))
                                        or (r["skenario"] == "D" and r["judge"].get("menolak_menebak") is False))
    tutor["ditandai_fact_check_mvp"] = sum(1 for r in rows if r["regex"]["fact_check"])
    tutor["ditandai_fact_check_mvp_skenario_C"] = tm["C_fact_check"]["k"]
    tutor["latensi_paralel8"] = tm["latensi_s"]
    lt = json.load(open(RESULTS / "latensi_tutor.json"))
    tutor["latensi_berurutan"] = lt

    e2e = json.load(open(RESULTS / "mvp_e2e.json"))
    rng = np.random.default_rng(0)
    by = {}
    for r in e2e["rows"]:
        by.setdefault(r["kasus"], []).append(r["jenis"] == r["pred"])
    ks = list(by)
    boot = []
    for _ in range(5000):
        pick = rng.choice(ks, len(ks))
        v = [x for k in pick for x in by[k]]
        boot.append(np.mean(v))
    e2e_ci = [float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))]
    # anotasi "terlalu luas" yang tetap lolos kriteria benar K6. Kriteria lama (semifinal): Dice >= 0,6 dan recall
    # per lesi 1. Kriteria MVP sekarang menambah galat volume <= +25% (mvp/sinaps/grading.py, K6_PASS).
    luas = [r for r in e2e["rows"] if r["jenis"] == "terlalu_luas"]
    luas_lolos_lama = sum(1 for r in luas if r["dice"] >= 0.6 and r["recall"] >= 1)
    luas_lolos = sum(1 for r in luas if r["k6"])
    hb = [r for r in e2e["rows"] if r["jenis"] == "hampir_benar"]
    hb_lolos = sum(1 for r in hb if r["k6"])
    sempit = [r for r in e2e["rows"] if r["jenis"] == "terlalu_sempit"]
    sempit_lolos = sum(1 for r in sempit if r["k6"])

    seg = json.load(open(MVP / "pipeline/results/unet25d/metrics.json"))
    shutil.copy(MVP / "pipeline/results/unet25d/test_per_subject.csv", RESULTS / "seg_mvp_per_subjek.csv")
    rules = json.load(open(MVP / "pipeline/results/error_rules.json"))

    out = dict(tutor=tutor,
               e2e=dict(akurasi=e2e["akurasi_jenis"], ik95=e2e_ci, n=e2e["n_submit"],
                        luas_lolos_k6=luas_lolos, luas_lolos_k6_lama=luas_lolos_lama, n_luas=len(luas),
                        hampir_benar_lolos_k6=hb_lolos, n_hampir_benar=len(hb),
                        sempit_lolos_k6=sempit_lolos, n_sempit=len(sempit)),
               seg=dict(seg["test"], n_train=seg["n_train_patients"], n_slice=seg["n_train_slices"], epoch=seg["epochs"],
                        menit=seg["train_minutes"], gpu=seg["gpu"], best_val=seg["best_val_dice"], n_val=seg["n_val"]),
               rules=dict(akurasi=rules["akurasi_aturan"], ik95=rules["ik95_aturan"], dice_saja=rules["akurasi_dice_saja"],
                          ik95_dice=rules["ik95_dice_saja"], n=rules["n_anotasi"], n_subjek=rules["n_subjek"],
                          recall=rules["recall_per_jenis"], akurasi_lama=rules.get("akurasi_aturan_lama"),
                          ik95_lama=rules.get("ik95_aturan_lama"), recall_lama=rules.get("recall_per_jenis_lama")))
    json.dump(out, open(RESULTS / "final.json", "w"), indent=1, ensure_ascii=False)
    print(json.dumps(out, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
