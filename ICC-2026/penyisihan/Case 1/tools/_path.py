"""Shim path untuk skrip di subfolder ini.

Modul pipeline (`lab_common`, `fastscore`, dll) tinggal di `Case 1/lab/`. Cukup
`import _path` di baris pertama, lalu import biasa. `_path.ROOT` menunjuk ke
`Case 1/` untuk path file yang harus relatif ke root case.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
for p in (ROOT / "lab", ROOT):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
