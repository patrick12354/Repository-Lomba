#!/bin/sh
# Loudness-normalises the raw TTS lines and builds the two music beds.
#   assets/voice/*.wav        raw HeyGen TTS (make-voice.mjs)   -> assets/audio/vo/*.wav at -16 LUFS
#   .media/audio/bgm/bgm_004  investigative pulse, 1.2-51.2 s (act 1, skips its slow fade-in) -> assets/audio/music/act1.wav at -22 LUFS
#   .media/audio/bgm/bgm_001  cinematic bed (act 2), lengthened by repeating a steady 13 s section
#                                                              -> assets/audio/music/act2.wav at -18 LUFS
set -e
cd "$(dirname "$0")/.."
mkdir -p assets/audio/vo assets/audio/music
for f in assets/voice/*.wav; do
  ffmpeg -loglevel error -y -i "$f" -af "loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000" -ar 48000 "assets/audio/vo/$(basename "$f")"
done
ffmpeg -loglevel error -y -i .media/audio/bgm/bgm_004.wav -af "atrim=1.2:51.2,asetpts=N/SR/TB,afade=t=in:d=0.3,afade=t=out:st=47:d=3,loudnorm=I=-22:TP=-2:LRA=11,aresample=48000" -ar 48000 assets/audio/music/act1.wav
ffmpeg -loglevel error -y -i .media/audio/bgm/bgm_001.wav -filter_complex \
  "[0]atrim=0:72,asetpts=N/SR/TB[a];[0]atrim=59.3:124,asetpts=N/SR/TB[b];[a][b]acrossfade=d=2.5:c1=tri:c2=tri,loudnorm=I=-18:TP=-2:LRA=11,aresample=48000" \
  -ar 48000 assets/audio/music/act2.wav
for f in assets/audio/music/*.wav; do printf "%s %ss\n" "$f" "$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$f")"; done
