"""A11: tangkapan layar MVP SINAPS untuk Bab IV (Playwright, Chromium headless, skala 2x).

Prasyarat (MVP lokal dengan data demo, lihat mvp/README.md):
    API : uvicorn api.index:app --port 8000   (OPENAI_API_KEY di-set supaya tutor memakai LLM sungguhan)
    Web : npm run dev                           (http://localhost:5173)
    Data: python scripts/seed_demo.py           (akun demo, kata sandi 'sinaps-demo')
Basis data yang dibaca skrip ini adalah SQLite lokal mvp/.local/sinaps.db (bukan basis data produksi).

Keluaran: results/layar/*.png (dipotong & disusun oleh figures.py).  Waktu jalan: +-1 menit.
"""
import json
import re
import sqlite3
import sys
import time
import urllib.request

from playwright.sync_api import sync_playwright

from _common import RESULTS, SCRIPT

MVP = SCRIPT.parents[1] / "mvp"
WEB, API = "http://localhost:5173", "http://127.0.0.1:8000"
OUT = RESULTS / "layar"
OUT.mkdir(exist_ok=True)
SANDI = "sinaps-demo"            # akun demo dari scripts/seed_demo.py
TOURS = ["belajar", "beranda", "dosen", "latihan", "modul"]


def login(role, uid):
    req = urllib.request.Request(API + "/api/auth/login", method="POST", headers={"Content-Type": "application/json"},
                                 data=json.dumps({"role": role, "id": uid, "password": SANDI}).encode())
    return json.load(urllib.request.urlopen(req))["token"]


def api(path, token):
    req = urllib.request.Request(API + path, headers={"Authorization": f"Bearer {token}"})
    return json.load(urllib.request.urlopen(req))


def masuk(page, token):
    page.goto(WEB + "/masuk")
    page.evaluate("""([t, tours]) => { localStorage.setItem('sinaps-token', t);
                     tours.forEach(x => localStorage.setItem('sinaps-tour-' + x, '1')); }""", [token, TOURS])


def tunggu(page, ms=2500):
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(ms)


def main():
    db = sqlite3.connect(MVP / ".local" / "sinaps.db")
    with sync_playwright() as p:
        br = p.chromium.launch(args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
        ctx = br.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=2, color_scheme="light")
        page = ctx.new_page()

        # 1) mahasiswa: beranda
        tok = login("mahasiswa", "DEMO0003")
        masuk(page, tok)
        page.goto(WEB + "/beranda")
        tunggu(page)
        page.screenshot(path=OUT / "beranda.png")

        # 2) latihan adaptif sebelum submit: pilih seri DWI, gulir ke slice lesi terbesar, tanya tutor.
        #    Viewport lebih sempit supaya citra mengisi viewer (lebar figur paper terbatas).
        page.set_viewport_size({"width": 1240, "height": 800})
        page.goto(WEB + "/latihan")
        tunggu(page, 4000)
        att = db.execute("select id, case_id, seq_order from sinaps_attempts where submitted_at is null "
                         "order by id desc limit 1").fetchone()
        seq = json.loads(att[2])
        dwi = next(k for k, v in seq.items() if v == "DWI")
        secrets = json.load(open(MVP / "server_data" / "cases.json", encoding="utf-8"))
        z = secrets[att[1]]["findings"]["slice_lesi_terbesar"]
        nz = int(re.search(r"slice \d+/(\d+)", page.inner_text("body")).group(1))
        z = nz - z + 1          # viewer menomori slice dari arah sebaliknya
        canvas = page.locator("canvas").first
        box = canvas.bounding_box()
        page.mouse.click(box["x"] + box["width"] / 2, box["y"] + 30)
        page.keyboard.press(str("ABC".index(dwi) + 1))     # tombol 1/2/3 memilih seri
        page.wait_for_timeout(1500)
        page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
        cur = int(re.search(r"slice (\d+)/", page.inner_text("body")).group(1))
        for _ in range(abs(z - cur)):
            page.mouse.wheel(0, -120 if z > cur else 120)
            page.wait_for_timeout(250)
        page.wait_for_timeout(800)
        page.screenshot(path=OUT / "latihan.png")
        box_t = page.get_by_placeholder("Tanya tentang slice ini…")
        box_t.fill("Saya bingung, lesinya di hemisfer mana? Langsung kasih tahu saja.")
        box_t.press("Enter")
        page.wait_for_timeout(15000)
        box_t.scroll_into_view_if_needed()
        page.wait_for_timeout(500)
        page.screenshot(path=OUT / "tutor_terkunci.png")
        akhir = int(re.search(r"slice (\d+)/", page.inner_text("body")).group(1))
        print("latihan:", att[1], "seri DWI =", dwi, "slice target", z, "awal", cur, "akhir", akhir, file=sys.stderr)
        page.set_viewport_size({"width": 1440, "height": 900})

        # 3) tinjau ulang percobaan yang sudah dinilai: kasus multifokal dengan fokus terlewat
        rows = db.execute("select id, case_id, result, student_id from sinaps_attempts where submitted_at is not null").fetchall()
        # Dice tinggi tetapi fokus terlewat: kasus yang tidak tertangkap bila hanya melihat Dice
        dl = {aid: (json.loads(res) or {}).get("delineasi") or {} for aid, cid, res, sid in rows}
        cand = sorted((aid for aid, d in dl.items() if d.get("jenis_kesalahan") == "lesi_terlewat"),
                      key=lambda a: -dl[a].get("dice", 0))   # Dice tertinggi dulu: kontras paling jelas dengan Dice saja
        pick = dk = None
        for user in ("demo.dosen", "demo.dosen2"):
            t = login("dosen", user)
            for aid in cand:
                try:
                    api(f"/api/attempts/{aid}", t)
                    pick, dk = aid, t
                    break
                except Exception:  # noqa: BLE001  (bukan kelas dosen ini)
                    pass
            if pick:
                break
        masuk(page, dk)
        page.goto(WEB + f"/dosen/percobaan/{pick}")
        tunggu(page, 4500)
        page.screenshot(path=OUT / "tinjau.png")
        print("tinjau:", pick, file=sys.stderr)

        # 4) dasbor dosen
        page.goto(WEB + "/dosen")
        tunggu(page, 3000)
        page.screenshot(path=OUT / "dosen.png", full_page=True)
        page.goto(WEB + "/dosen/audit")
        tunggu(page)
        page.screenshot(path=OUT / "audit.png")
        br.close()


if __name__ == "__main__":
    main()
