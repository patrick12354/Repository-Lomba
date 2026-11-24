#!/usr/bin/env bash
# Daftarkan venv yang sudah ada sebagai kernel Jupyter bernama "dataton".
# Jalankan sekali saja:  bash setup_kernel.sh
set -euo pipefail
VENV="/Users/timotiuspatrick/Documents/Patrick/Kuliah & Coding/.venv"
PY="$VENV/bin/python"
[ -x "$PY" ] || { echo "Tidak menemukan python di: $PY"; exit 1; }
"$PY" -m pip install --quiet --upgrade ipykernel numpy pandas pillow scikit-learn matplotlib
"$PY" -m ipykernel install --user --name dataton --display-name "Dataton (.venv)"
echo "Selesai. Di notebook pilih kernel: Dataton (.venv)"
