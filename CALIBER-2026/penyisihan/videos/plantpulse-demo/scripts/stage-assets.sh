#!/bin/sh
# Converts raw captures (capture/) into the compressed stills the scenes use (assets/captures/).
# Re-run after any capture script. Crops are in 2x pixels (CSS px * 2).
set -e
cd "$(dirname "$0")/.."
C=capture; O=assets/captures; mkdir -p $O
j() { ffmpeg -loglevel error -y -i "$1" ${3:+-vf "$3"} -q:v 2 "$O/$2.jpg"; }
j $C/overview.png        ov-top
j $C/overview-full.png   ov-gauges   "crop=3840:860:0:3990"
j $C/queue.png           queue
j $C/states/queue-conflicts.png ev-charts
j $C/states/queue-drawer.png ev-drawer
j $C/states/queue-conflicts-tab.png ev-conflicts
j $C/investigation.png   inv-top
j $C/investigation-full.png inv-full
j $C/states/inv-causes.png inv-causes
j $C/states/inv-brief.png  inv-brief
j $C/states/inv-similar.png inv-similar
j $C/states/inv-withheld.png inv-withheld
j $C/states/inv-unwithheld.png inv-unwithheld
j $C/actions.png         act-top
j $C/foundation.png      found
j $C/states/foundation-checks.png found-checks
j $C/aiquality.png       aiq
j $C/landing.png         landing
for f in 01-draft 02-filled 03-refused 05-attached 06-ready 07-reviewer-is-owner 08-reviewer-named; do j $C/actions/$f-card.png act-$f; done
echo staged
