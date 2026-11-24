"""Jelajah cepat UI MVP lokal (screenshot) sebelum menulis skrip rekaman. Sekali pakai."""
import json, sys, urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE = "http://localhost:5173"
OUT = Path(__file__).resolve().parents[1] / ".scratch" / "jelajah"
OUT.mkdir(parents=True, exist_ok=True)


def login(role, ident, pw="sinaps-demo"):
    req = urllib.request.Request("http://127.0.0.1:8000/api/auth/login", data=json.dumps({"role": role, "id": ident, "password": pw}).encode(), headers={"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req))


if __name__ == "__main__":
    nim = sys.argv[1] if len(sys.argv) > 1 else "DEMO0003"
    r = login("mahasiswa", nim)
    print("user", r["user"])
    with sync_playwright() as p:
        b = p.chromium.launch(args=["--use-angle=swiftshader", "--enable-unsafe-swiftshader"])
        ctx = b.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=1)
        ctx.add_init_script(f"""localStorage.setItem('sinaps-token', {json.dumps(r['token'])});
          ['beranda','latihan','belajar','modul','dosen'].forEach(k => localStorage.setItem('sinaps-tour-'+k,'1'));""")
        pg = ctx.new_page()
        pg.on("console", lambda m: m.type == "error" and print("console:", m.text[:200]))
        pg.goto(BASE + "/beranda"); pg.wait_for_timeout(2500); pg.screenshot(path=OUT / "beranda.png")
        pg.goto(BASE + "/latihan?kasus=sub-654"); pg.wait_for_timeout(6000); pg.screenshot(path=OUT / "latihan.png")
        print(pg.url)
        b.close()
