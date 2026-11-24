#!/bin/sh
# Build <project>/index.html from the shared skeleton. Usage: shared/assemble.sh <project> <seconds> "<title>"
# The scene itself lives in <project>/scene.js; the board kit in <project>/assets/board.js (shared/sync.sh).
cd "$(dirname "$0")/.."
p="$1"; d="$2"; t="$3"; extra="$4"
{
  echo '<!doctype html>'
  echo '<html lang="id">'
  echo '  <head>'
  echo "    <title>$t</title>"
  cat shared/skeleton.head.html
  echo '  </head>'
  echo '  <body>'
  echo "    <div id=\"root\" data-composition-id=\"main\" data-start=\"0\" data-duration=\"$d\" data-width=\"1920\" data-height=\"1080\" data-fps=\"30\">"
  cat shared/skeleton.body.html
  echo '    </div>'
  [ -n "$extra" ] && echo "    <script src=\"$extra\"></script>"
  echo '    <script src="assets/board.js"></script>'
  echo '    <script src="scene.js"></script>'
  echo '    <script>'
  echo '      window.__timelines = window.__timelines || {};'
  echo '      window.__timelines["main"] = window.SCENE_TL;'
  echo '    </script>'
  echo '  </body>'
  echo '</html>'
} > "$p/index.html"
