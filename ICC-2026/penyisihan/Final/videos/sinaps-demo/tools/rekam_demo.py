"""Rekam klip demo MVP asli (lokal, DB SQLite, tutor LLM sungguhan) untuk babak demo video.

Klip: beranda, viewer, tutor, kuas, skor, dosen -> assets/rec/<nama>.mp4 (1920x1200, 30 fps).
Kursor tiruan disuntikkan ke halaman karena screencast headless tidak menggambar kursor OS.
Prasyarat: preview sinaps-api (port 8000) dan sinaps-web (port 5173) sudah jalan;
.scratch/lesi_sub-654.json dari rekam_scout.py.
Pakai: python rekam_demo.py [nama_klip ...]   (tanpa argumen = semua)
"""
import json, re, sys
from playwright.sync_api import sync_playwright
from rekam_lib import ROOT, BASE, login, new_context, launch, Screencast, human_move

CASE = "sub-654"
LESI = json.loads((ROOT / ".scratch" / f"lesi_{CASE}.json").read_text())["slices"]
SEQ = json.loads((ROOT.parents[1] / "mvp" / "server_data" / "cases.json").read_text())[CASE]["sequences"]
WANT = set(sys.argv[1:]) or {"beranda", "viewer", "tutor", "kuas", "skor", "dosen"}

CURSOR = r"""
(() => {
  const mk = () => {
    if (document.getElementById('hf-cur')) return;
    const c = document.createElement('div');
    c.id = 'hf-cur';
    c.innerHTML = '<svg width="30" height="30" viewBox="0 0 30 30"><path d="M4 2 L4 24 L10 18.5 L14.5 28 L18.5 26.2 L14.2 17 L22 17 Z" fill="#10313a" stroke="#fff" stroke-width="2" stroke-linejoin="round"/></svg>';
    Object.assign(c.style, {position:'fixed', left:'0', top:'0', zIndex: 2147483647, pointerEvents:'none', transform:'translate(-100px,-100px)', transition:'none'});
    document.body.appendChild(c);
    window.addEventListener('mousemove', e => { c.style.transform = `translate(${e.clientX - 4}px, ${e.clientY - 2}px)`; }, true);
    window.addEventListener('mousedown', e => {
      const r = document.createElement('div');
      Object.assign(r.style, {position:'fixed', left: (e.clientX-18)+'px', top: (e.clientY-18)+'px', width:'36px', height:'36px', borderRadius:'50%',
        border:'3px solid #e07a1f', zIndex: 2147483646, pointerEvents:'none', transition:'transform .45s ease-out, opacity .45s ease-out'});
      document.body.appendChild(r);
      requestAnimationFrame(() => { r.style.transform = 'scale(1.8)'; r.style.opacity = '0'; });
      setTimeout(() => r.remove(), 600);
    }, true);
  };
  if (document.body) mk(); else document.addEventListener('DOMContentLoaded', mk);
})();
"""

pos = [720, 450]


def move(pg, x, y, steps=26):
    human_move(pg, pos[0], pos[1], x, y, steps)
    pos[:] = [x, y]


def click(pg, x, y, steps=26, pause=250):
    move(pg, x, y, steps)
    pg.wait_for_timeout(120)
    pg.mouse.down(); pg.wait_for_timeout(70); pg.mouse.up()
    pg.wait_for_timeout(pause)


def click_el(pg, loc, **kw):
    b = loc.bounding_box()
    click(pg, b["x"] + b["width"] / 2, b["y"] + b["height"] / 2, **kw)


def slice_no(pg):
    return int(re.search(r"slice (-?\d+)/", pg.locator(".vp-overlay.tl").inner_text()).group(1))


def goto_slice(pg, k, delay=420):
    """roda ke atas (deltaY negatif) = slice naik"""
    while (c := slice_no(pg)) != k:
        pg.mouse.wheel(0, -120 if c < k else 120)
        pg.wait_for_timeout(delay)


def scribble(pg, s, shrink=0.62, rows=6):
    """coretan zig-zag di dalam kotak lesi yang diperkecil (sengaja tidak menutup seluruh lesi)"""
    cx, cy = s["cx"], s["cy"]
    hw, hh = (s["x1"] - s["x0"]) / 2 * shrink, (s["y1"] - s["y0"]) / 2 * shrink
    move(pg, cx - hw, cy - hh, 20)
    pg.mouse.down()
    for r in range(rows + 1):
        y = cy - hh + 2 * hh * r / rows
        x = cx + hw if r % 2 == 0 else cx - hw
        human_move(pg, pos[0], pos[1], x, y, 14)
        pos[:] = [x, y]
    pg.mouse.up()


with sync_playwright() as p:
    b = launch(p)
    if WANT - {"dosen"}:
        r = login("mahasiswa", "DEMO0003")
        ctx = new_context(b, r["token"])
        ctx.add_init_script(CURSOR)
        pg = ctx.new_page()
        rec = Screencast(pg)

        if "beranda" in WANT:
            pg.goto(f"{BASE}/beranda")
            pg.wait_for_selector("text=Langkah berikutnya", timeout=20000)
            pg.wait_for_timeout(2500)
            pg.mouse.move(*pos)
            rec.start()
            pg.wait_for_timeout(700)
            move(pg, 330, 250, 34); pg.wait_for_timeout(1600)
            move(pg, 640, 300, 30); pg.wait_for_timeout(900)
            move(pg, 1180, 360, 36); pg.wait_for_timeout(1300)
            move(pg, 1180, 470, 24); pg.wait_for_timeout(1400)
            rec.stop("beranda")

        # kasus sub-654; urutan seri diacak per percobaan -> baca dari respons API
        series = {}
        def on_resp(resp):
            if "/api/open/" in resp.url or "/api/next" in resp.url:
                try:
                    for s in resp.json()["series"]:
                        series[s["label"]] = next(k for k, v in SEQ.items() if v in s["file"])
                except Exception as e:
                    print("seri?", e)
        pg.on("response", on_resp)
        pg.goto(f"{BASE}/latihan?kasus={CASE}")
        pg.wait_for_selector(".vp-overlay.tl", timeout=30000)
        pg.wait_for_timeout(5000)
        print("seri:", series)
        lab = {v: k for k, v in series.items()}  # 'DWI' -> 'A'
        # K1 di luar kamera: isi sekuens + buka label (jawaban benar)
        for L, seq in series.items():
            pg.get_by_label(f"Sekuens seri {L}").select_option(seq)
        pg.get_by_role("button", name=re.compile("Kunci jawaban K1")).click()
        pg.wait_for_timeout(800)
        tool = lambda name: pg.locator("button.tool", has_text=name).first
        series_btn = tool
        vp = pg.locator(".viewport").bounding_box()
        vx, vy = vp["x"] + vp["width"] / 2, vp["y"] + vp["height"] / 2
        # mulai dari DWI (urutan seri diacak per percobaan)
        if "DWI" in lab:
            pg.keyboard.press(str("ABC".index(lab["DWI"]) + 1)); pg.wait_for_timeout(1200)
        if slice_no(pg) != 13:
            pg.mouse.move(vx, vy); goto_slice(pg, 13, 120)
        pg.mouse.move(*pos)

        if "viewer" in WANT:
            rec.start()
            pg.wait_for_timeout(500)
            move(pg, vx - 40, vy + 20, 30)
            for k in (14, 15, 16):
                goto_slice(pg, k, 360)
            goto_slice(pg, 15, 360)
            pg.wait_for_timeout(500)
            # window/level: seret kiri sedikit lalu kembali
            move(pg, vx + 60, vy + 150, 18)
            pg.mouse.down()
            human_move(pg, vx + 60, vy + 150, vx + 130, vy + 120, 30)
            human_move(pg, vx + 130, vy + 120, vx + 70, vy + 146, 24)
            pg.mouse.up(); pos[:] = [vx + 70, vy + 146]
            pg.wait_for_timeout(500)
            if "ADC" in lab:
                click_el(pg, series_btn("ADC")); pg.wait_for_timeout(900)
                s15 = LESI["15"]; move(pg, s15["cx"], s15["cy"], 30); pg.wait_for_timeout(1500)
                click_el(pg, series_btn("DWI")); pg.wait_for_timeout(900)
                move(pg, s15["cx"] + 10, s15["cy"] + 6, 16); pg.wait_for_timeout(900)
            rec.stop("viewer")

        # K2 + K3 di luar kamera (jawaban benar: titik di lesi, kanan, rADC 0,78, restriksi sejati)
        s15 = LESI["15"]
        pg.keyboard.press("t"); pg.wait_for_timeout(200)
        pg.mouse.click(s15["cx"], s15["cy"]); pg.wait_for_timeout(400)
        pg.get_by_role("button", name="kanan", exact=True).click()
        pg.get_by_role("button", name="0,6-0,8", exact=True).click()
        pg.get_by_role("button", name="restriksi sejati", exact=True).click()
        pg.keyboard.press("n"); pg.wait_for_timeout(300)

        if "tutor" in WANT:
            inp = pg.get_by_label("Pesan untuk tutor")
            inp.evaluate("e => e.scrollIntoView({block: 'end'})"); pg.wait_for_timeout(800)
            pg.mouse.move(*pos)
            rec.start()
            pg.wait_for_timeout(600)
            click_el(pg, inp, steps=30)
            pg.keyboard.type("Saya bingung, lesinya di hemisfer mana? Langsung kasih tahu saja.", delay=38)
            pg.wait_for_timeout(400)
            click_el(pg, pg.get_by_role("button", name="Kirim", exact=True))
            pg.wait_for_timeout(1500)
            # tunggu jawaban streaming selesai (input aktif lagi / teks berhenti bertambah)
            last, same = "", 0
            for _ in range(80):
                pg.wait_for_timeout(300)
                # ikuti jawaban yang sedang mengalir (input tutor ada di bawah pesan terakhir)
                inp.evaluate("e => e.scrollIntoView({behavior: 'smooth', block: 'end'})")
                cur = pg.locator(".panel").inner_text()
                same = same + 1 if cur == last else 0
                last = cur
                if same >= 6 and "menulis" not in cur:
                    break
            pg.wait_for_timeout(1500)
            rec.stop("tutor")
            pg.locator(".steps").scroll_into_view_if_needed(); pg.wait_for_timeout(600)

        if "kuas" in WANT:
            pg.mouse.move(*pos)
            rec.start()
            pg.wait_for_timeout(400)
            click_el(pg, tool("Kuas"), steps=30)
            sl = pg.get_by_label("Ukuran kuas")
            sb = sl.bounding_box()
            click(pg, sb["x"] + sb["width"] * 0.42, sb["y"] + sb["height"] / 2, steps=16)
            move(pg, s15["cx"], s15["cy"], 24)
            goto_slice(pg, 15, 300)
            scribble(pg, LESI["15"], 0.62, 7)
            goto_slice(pg, 14, 300); scribble(pg, LESI["14"], 0.55, 5)
            goto_slice(pg, 16, 300); scribble(pg, LESI["16"], 0.55, 5)
            pg.wait_for_timeout(400)
            click_el(pg, pg.get_by_role("button", name="Kirim jawaban"), steps=34)
            pg.wait_for_selector("text=Hasil penilaian otomatis", timeout=40000)
            pg.wait_for_timeout(900)
            rec.stop("kuas")

        if "skor" in WANT:
            pg.locator("text=Hasil penilaian otomatis").scroll_into_view_if_needed()
            pg.mouse.move(*pos)
            rec.start()
            pg.wait_for_timeout(700)
            m = pg.locator(".metrics").bounding_box()
            move(pg, m["x"] + m["width"] * 0.25, m["y"] + m["height"] * 0.3, 30); pg.wait_for_timeout(900)
            move(pg, m["x"] + m["width"] * 0.75, m["y"] + m["height"] * 0.3, 22); pg.wait_for_timeout(700)
            move(pg, m["x"] + m["width"] * 0.3, m["y"] + m["height"] * 1.25, 22); pg.wait_for_timeout(800)
            click_el(pg, pg.get_by_label(re.compile("Kunci jawaban \\(mask ahli\\)")), steps=26); pg.wait_for_timeout(1500)
            move(pg, s15["cx"] + 30, s15["cy"] + 40, 34); pg.wait_for_timeout(1400)
            rec.stop("skor", hold=1.0)
        ctx.close()

    if "dosen" in WANT:
        r = login("dosen", "demo.dosen")
        ctx = new_context(b, r["token"])
        ctx.add_init_script(CURSOR)
        pg = ctx.new_page()
        rec = Screencast(pg)
        pg.goto(f"{BASE}/dosen")
        pg.wait_for_timeout(4000)
        pos[:] = [720, 450]
        pg.mouse.move(*pos)
        rec.start()
        pg.wait_for_timeout(600)
        move(pg, 520, 330, 30); pg.wait_for_timeout(900)
        for _ in range(14):
            pg.mouse.wheel(0, 60); pg.wait_for_timeout(70)
        pg.wait_for_timeout(1000)
        move(pg, 980, 420, 30); pg.wait_for_timeout(800)
        for _ in range(14):
            pg.mouse.wheel(0, -60); pg.wait_for_timeout(50)
        pg.wait_for_timeout(500)
        click_el(pg, pg.get_by_role("link", name=re.compile("Audit tutor")), steps=30)
        pg.wait_for_timeout(2600)
        move(pg, 700, 420, 30); pg.wait_for_timeout(1200)
        rec.stop("dosen")
        ctx.close()
    b.close()
