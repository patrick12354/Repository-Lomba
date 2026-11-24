"""Pengintai: cari letak lesi sub-654 di layar viewer (1440x900) dari overlay kunci jawaban.

Akun pengintai DEMO0004 mengerjakan kasus asal-asalan di DB lokal, lalu overlay "Kunci jawaban (mask ahli)"
dinyalakan dan tiap slice dipotret. Piksel hijau overlay = letak lesi -> .scratch/lesi_sub-654.json.
Hanya dipakai untuk mengarahkan kuas di rekaman demo; penilaian di rekaman tetap dari server.
"""
import json, re
import numpy as np
from PIL import Image
from io import BytesIO
from playwright.sync_api import sync_playwright
from rekam_lib import ROOT, BASE, login, new_context, launch

CASE = "sub-654"

with sync_playwright() as p:
    b = launch(p)
    r = login("mahasiswa", "DEMO0004")
    ctx = new_context(b, r["token"])
    pg = ctx.new_page()
    pg.goto(f"{BASE}/latihan?kasus={CASE}")
    pg.wait_for_selector(".vp-overlay.tl")
    pg.wait_for_timeout(4000)
    vp = pg.locator(".viewport").bounding_box()
    print("viewport", vp)
    cx, cy = vp["x"] + vp["width"] / 2, vp["y"] + vp["height"] / 2
    txt = lambda: pg.locator(".vp-overlay.tl").inner_text()
    print("awal:", txt())
    pg.mouse.move(cx, cy)
    pg.mouse.wheel(0, 120); pg.wait_for_timeout(400); print("wheel +120:", txt())
    pg.mouse.wheel(0, -120); pg.wait_for_timeout(400); print("wheel -120:", txt())
    # coretan kecil supaya bisa submit
    pg.keyboard.press("b")
    pg.mouse.move(cx, cy); pg.mouse.down(); pg.mouse.move(cx + 20, cy + 10, steps=5); pg.mouse.up()
    pg.get_by_role("button", name="Kirim jawaban").click()
    pg.wait_for_selector("text=Hasil penilaian otomatis", timeout=30000)
    pg.wait_for_timeout(1500)
    pg.get_by_label("Kunci jawaban (mask ahli)", exact=False).check()
    pg.get_by_label("Jawaban saya", exact=False).uncheck()
    pg.wait_for_timeout(800)
    pg.mouse.move(cx, cy)
    # ke slice 1 dulu (roda ke bawah = slice turun)
    cur = int(re.search(r"slice (-?\d+)/", txt()).group(1))
    for _ in range(cur - 1):
        pg.mouse.wheel(0, 120); pg.wait_for_timeout(80)
    res = {"viewport": vp, "slices": {}}
    for _ in range(30):
        pg.wait_for_timeout(350)
        t = txt()
        m = re.search(r"slice (-?\d+)/(\d+)", t)
        if not m:
            print("overlay:", repr(t))
            pg.screenshot(path=str(ROOT / ".scratch" / "scout_fail.png"))
            break
        k = int(m.group(1))
        png = pg.screenshot(clip=vp)
        a = np.asarray(Image.open(BytesIO(png)).convert("RGB")).astype(int)
        g = (a[..., 1] > 150) & (a[..., 0] < 120) & (a[..., 2] < 170)  # hijau overlay kunci
        ys, xs = np.nonzero(g)
        if len(xs) > 30:
            sc = vp["width"] / a.shape[1]
            res["slices"][k] = {
                "n": int(len(xs)),
                "cx": float(vp["x"] + xs.mean() * sc), "cy": float(vp["y"] + ys.mean() * sc),
                "x0": float(vp["x"] + xs.min() * sc), "x1": float(vp["x"] + xs.max() * sc),
                "y0": float(vp["y"] + ys.min() * sc), "y1": float(vp["y"] + ys.max() * sc),
                "pts": [[float(vp["x"] + x * sc), float(vp["y"] + y * sc)] for x, y in zip(xs[::97], ys[::97])],
            }
        if k >= int(m.group(2)):
            break
        pg.mouse.wheel(0, -120)
    out = ROOT / ".scratch" / f"lesi_{CASE}.json"
    out.write_text(json.dumps(res, indent=1))
    print({k: (v["n"], round(v["cx"]), round(v["cy"])) for k, v in res["slices"].items()})
    b.close()
