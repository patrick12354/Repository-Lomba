#!/bin/sh
# Copy shared/board.js into every board-based project (slides 3, 4, 8, 9).
cd "$(dirname "$0")/.."
for p in slide03-bukti slide04-petunjuk slide08-ensemble slide09-pola; do
  cp shared/board.js "$p/assets/board.js"
done
