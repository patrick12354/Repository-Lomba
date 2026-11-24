"""Alat bantu rekaman layar MVP lokal: login lewat API, konteks Playwright, dan perekam CDP screencast.

Screencast CDP dipakai (bukan record_video Playwright) supaya teks UI tetap tajam: tiap frame JPEG
kualitas tinggi disimpan dengan timestamp-nya lalu dirangkai ffmpeg menjadi MP4 30 fps.
"""
import base64, json, shutil, subprocess, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MVP = ROOT.parents[1] / "mvp"
BASE = "http://localhost:5173"
API = "http://127.0.0.1:8000"
VIEW = {"width": 1440, "height": 900}
DSF = 4 / 3  # frame keluaran 1920x1200


def login(role, ident, pw="sinaps-demo"):
    body = json.dumps({"role": role, "id": ident, "password": pw}).encode()
    req = urllib.request.Request(API + "/api/auth/login", data=body, headers={"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req))


def new_context(browser, token):
    ctx = browser.new_context(viewport=VIEW, device_scale_factor=DSF)
    tours = ["beranda", "latihan", "belajar", "modul", "dosen"]
    ctx.add_init_script(
        f"localStorage.setItem('sinaps-token', {json.dumps(token)});"
        + "".join(f"localStorage.setItem('sinaps-tour-{t}','1');" for t in tours)
    )
    return ctx


def launch(p):
    # GPU asli (RTX 4060 lewat ANGLE D3D11); swiftshader terlalu lambat untuk dasbor 3D dosen
    return p.chromium.launch(args=["--use-angle=d3d11", "--ignore-gpu-blocklist", "--enable-gpu-rasterization", "--hide-scrollbars"])


class Screencast:
    """Rekam satu klip. start() -> aksi -> stop(nama) menulis assets/rec/<nama>.mp4"""

    def __init__(self, page):
        self.page = page
        self.cdp = page.context.new_cdp_session(page)
        self.frames = []
        self.cdp.on("Page.screencastFrame", self._on_frame)

    def _on_frame(self, ev):
        self.frames.append((ev["metadata"]["timestamp"], ev["data"]))
        try:
            self.cdp.send("Page.screencastFrameAck", {"sessionId": ev["sessionId"]})
        except Exception:
            pass

    def start(self):
        self.frames = []
        self.cdp.send("Page.startScreencast", {"format": "jpeg", "quality": 92, "maxWidth": 1920, "maxHeight": 1200, "everyNthFrame": 1})

    def stop(self, name, hold=0.6):
        self.page.wait_for_timeout(int(hold * 1000))
        self.cdp.send("Page.stopScreencast")
        out = ROOT / "assets" / "rec"
        tmp = out / f"_{name}"
        shutil.rmtree(tmp, ignore_errors=True)
        tmp.mkdir(parents=True)
        lines = []
        fr = self.frames
        for i, (ts, data) in enumerate(fr):
            f = tmp / f"{i:05d}.jpg"
            f.write_bytes(base64.b64decode(data))
            dur = (fr[i + 1][0] - ts) if i + 1 < len(fr) else hold
            lines.append(f"file '{f.name}'\nduration {max(dur, 0.001):.4f}")
        lines.append(f"file '{tmp.joinpath(f'{len(fr) - 1:05d}.jpg').name}'")
        (tmp / "list.txt").write_text("\n".join(lines))
        mp4 = out / f"{name}.mp4"
        subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", "list.txt",
             "-vf", "scale=1920:1200:flags=lanczos,fps=30,format=yuv420p", "-c:v", "libx264", "-crf", "16", "-preset", "slow",
             "-movflags", "+faststart", str(mp4)],
            cwd=tmp, check=True,
        )
        shutil.rmtree(tmp, ignore_errors=True)
        total = fr[-1][0] - fr[0][0] + hold if fr else 0
        print(f"rec {name}: {len(fr)} frame, {total:.1f}s -> {mp4.name}")
        return mp4


def human_move(page, x0, y0, x1, y1, steps=24):
    """Gerak kursor bertahap (easing) supaya terlihat seperti tangan manusia."""
    for k in range(1, steps + 1):
        t = k / steps
        e = t * t * (3 - 2 * t)
        page.mouse.move(x0 + (x1 - x0) * e, y0 + (y1 - y0) * e)
        page.wait_for_timeout(12)
