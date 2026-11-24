#!/bin/sh
# Rebuild every board project's index.html and copy the shared kit.
cd "$(dirname "$0")"
sh sync.sh
sh assemble.sh slide03-bukti 70 "Slide 3 — Contaminated Evidence"
sh assemble.sh slide04-petunjuk 60 "Slide 4 — The Hidden Clue" assets/tmin.js
sh assemble.sh slide08-ensemble 55 "Slide 8 — Combining the Evidence"
sh assemble.sh slide09-pola 55 "Slide 9 — The Pattern Nobody Noticed"
# slide14-case-closed (v2) is a standalone composition: edit its index.html + scene.js directly
