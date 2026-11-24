"""Inline the sources into one curation page, design/ui-revamp/sparekit-ui-revamp.html."""
import base64
import io
from pathlib import Path

from PIL import Image

HERE = Path(__file__).parent
SRC = HERE / "src"


def jpeg_uri(path: Path) -> str:
    im = Image.open(path).convert("RGB")
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=84, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


html = (SRC / "index.src.html").read_text(encoding="utf8")
parts = {
    "/*__CSS__*/": (SRC / "styles.css").read_text(encoding="utf8"),
    "/*__DATA__*/": (SRC / "data.js").read_text(encoding="utf8"),
    "/*__SCENES__*/": (SRC / "scenes.js").read_text(encoding="utf8"),
    "/*__APP__*/": (SRC / "app.js").read_text(encoding="utf8"),
    "__BEFORE_SHUTDOWN__": jpeg_uri(SRC / "before" / "shutdown.png"),
    "__BEFORE_TODO__": jpeg_uri(SRC / "before" / "todo.png"),
}
for key, value in parts.items():
    html = html.replace(key, value)
out = HERE / "sparekit-ui-revamp.html"
out.write_text("<!doctype html>\n" + html, encoding="utf8")
(HERE / "src" / "publish.html").write_text(html, encoding="utf8")
print(out.name, round(out.stat().st_size / 1024), "KB")
