"""Path bersama untuk skrip analisis. Semua path relatif terhadap folder paper/script."""
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1]
DATA = SCRIPT.parents[1] / "data"          # semi-final/data (tidak di-commit)
RESULTS = SCRIPT / "results"
RESULTS.mkdir(exist_ok=True)
