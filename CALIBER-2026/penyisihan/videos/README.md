# Videos

Video production for the CALIBER 2026 submission. Each video is its own [HyperFrames](https://hyperframes.heygen.com) project
(HTML + GSAP compositions rendered to MP4). Everything needed to rebuild or revise a video lives in its folder.

| Folder | What it is |
|---|---|
| `plantpulse-demo/` | The ≤3-minute demo video (deliverable #2). 1920×1080, 174 s, light "Pipo" theme, narration in Patrick's ElevenLabs voice clone (multilingual_v2), word-pop captions, music, SFX. |

---

## `plantpulse-demo/` — folder structure

```
plantpulse-demo/
├── BRIEF.md               What the video must say, for whom, and the rules (no invented claims, English only, ≤180 s)
├── STORYBOARD.md          The 12-scene plan: what each scene shows and its exact voiceover line
├── frame.md               Design system for the video (colours, fonts, motion), taken from prototype/DESIGN.md
├── index.html             GENERATED root timeline. Do not edit by hand; run scripts/build.mjs
├── compositions/
│   ├── s00-plant.html … s12-lockup.html  One file per scene (hand-written HTML + GSAP). Edit these for visuals.
│   ├── atmos.html         The paper + Pipo bloom ground under the whole film (mood blooms keyed to scene cues)
│   ├── case-tag.html      The KO-3201 tag shown top-right from scene 5 to 11 (band changes colour in scene 10)
│   ├── captions.html      GENERATED captions (from the voice word timings)
│   └── grain.html         Film-grain overlay
├── assets/
│   ├── pp.css             Shared styles: fonts, colours, tag plate, chips, callouts (linked by every scene)
│   ├── fonts/             IBM Plex Sans + IBM Plex Mono, the web app's light-theme fonts (embedded, so renders are offline-safe)
│   ├── art/               Shared SVG art (compressor.svgfrag), inlined into scenes by scripts/inline-art.mjs
│   ├── captures/          Compressed stills of the live app used in scenes (made by scripts/stage-assets.sh)
│   ├── clips/             Frame-exact recordings of the live 3D views: machine.mp4, replay.mp4, site.mp4
│   ├── voice/             Raw ElevenLabs lines per scene (NN-name.wav) + word timings (NN-name.words.json)
│   ├── voice-src/         Voice samples used for the clones (patrick-clean.wav = current; git-ignored)
│   ├── audio/vo/          Loudness-normalised voice (-16 LUFS) — what the video actually plays
│   ├── audio/music/       act1.wav (tense drone, scenes 1-3) and act2.wav (main bed, from the logo onward)
│   └── sfx/               Sound effects
├── capture/               Raw 2x screenshots of the app (input to stage-assets.sh; git-ignored, rebuild with the capture scripts)
├── .media/                Media cache/manifest from `hyperframes media-use` (source music + SFX downloads)
├── scripts/               Every script used to make the video (see below)
└── renders/               Rendered MP4s (git-ignored)
```

### Scripts (`plantpulse-demo/scripts/`)

| Script | Does | When to run it |
|---|---|---|
| `timeline.json` | Scene order, scene lengths, when each voice line starts, and every sound-effect cue (scene-local seconds). | Edit for any timing, length or SFX change. |
| `build.mjs` | Builds `index.html` + `compositions/captions.html` from `timeline.json` and the voice word timings. Also sets music ducking under the voice. | After **any** change to `timeline.json` or the voice. |
| `voice-lines.json` | The narration text per scene, spelled for the TTS (e.g. "K O thirty-two oh one"). | Edit to change what the narrator says. |
| `make-voice-11labs.mjs` | Generates voice lines with the ElevenLabs clone of Patrick's voice (voice id, model and settings in `voice-lines.json` → `elevenlabs`; key `ELEVEN_LABS` in `videos/.env`). `node scripts/make-voice-11labs.mjs 05-overview` redoes one line. | After editing `voice-lines.json`. |
| `warp.mjs` | Re-syncs every scene to the current voice. s05–s11 are authored against the v3 voice (`scripts/authoring/`), s00–s03 against Raphael's v4 voice (`scripts/authoring/v4/`); anchors are the words both voices share (LCS), so reworded lines still sync. s04 and s12 (tagline) are timed straight from the current word starts. Also warps SFX, atmos mood keys and music cues. Keep the authoring folders. | After any voice change, or a `dur`/`voAt` change. Then `build.mjs`. |
| `inline-art.mjs` | Copies `assets/art/*.svgfrag` into scenes between `<!-- art:name:prefix -->` markers. | After editing the compressor drawing. |
| `make-voice.mjs` | Old HeyGen TTS generator (v3 voice), kept for reference. | — |
| `prep-audio.sh` | Normalises voice to -16 LUFS and builds the two music beds. | After `make-voice-11labs.mjs`. |
| `capture-lib.mjs` | Shared Playwright setup (1920×1080 @2x). `PP_URL` = app (default local dev `http://localhost:5173/`), `PP_THEME` = light/dark (default light). | — |
| `capture-pages.mjs` | Screenshots every workspace page (viewport + full page) into `capture/`. | When the app UI changes. |
| `capture-states.mjs` | Screenshots the app states the scenes use (AI tabs, drawers, conflict register, missing-source test…). | When the app UI changes. |
| `capture-actions.mjs` | Walks the real closure gate in `?offline=1` (create action → refused → evidence → reviewer ≠ owner). | When the Actions page changes. |
| `record-3d.mjs` | Records the three.js views frame-by-frame with a fake clock into `assets/clips/`. | When the 3D views change. |
| `stage-assets.sh` | Converts/crops `capture/` into `assets/captures/*.jpg`. | After any capture script. |
| `measure.mjs` | Prints element boxes on a page (CSS px) so callouts can be placed exactly on a capture. | When re-positioning a callout. |
| `explore.mjs` | Lists the clickable labels on a page (to write new capture steps). | When adding a new capture. |

Setup once: `cd plantpulse-demo/scripts && npm install` (Playwright; it uses the Chromium already cached by Playwright).
Voice: ElevenLabs Starter plan, ~2.4k characters for the whole script, so a full regenerate is cheap. The clone lives in the ElevenLabs account as "Patrick (PlantPulse)" (settings: stability 0.55, style 0.15, speed 1.0). eleven_v3 was tried and drifts the accent; stay on multilingual_v2.

---

## How to revise

All commands run inside `videos/plantpulse-demo/`.

**Preview while editing**

```bash
npx hyperframes preview --background
```

Opens HyperFrames Studio with a scrubbable timeline. Stop it with `npx hyperframes preview --stop`.

**Common revisions**

| I want to… | Do this |
|---|---|
| Change on-screen text, layout or animation in one scene | Edit `compositions/sNN-*.html` (timeline times inside a scene are scene-local seconds). |
| Change colours/fonts everywhere | Edit `assets/pp.css` (tokens at the top). |
| Make a scene longer/shorter, or move when its voice starts | Edit `dur` / `voAt` in `scripts/timeline.json`, then `node scripts/build.mjs`. Animations inside the scene keep their own times, so check that scene again. |
| Change what the narrator says | Edit the line in `scripts/voice-lines.json` → `node scripts/make-voice-11labs.mjs <id>` → `sh scripts/prep-audio.sh` → `node scripts/warp.mjs` → `node scripts/build.mjs`. For s05–s11, `warp.mjs` re-syncs automatically as long as the words are unchanged (it stops with an error if they differ). For s00–s04 and s12, re-check the scene's cue times by hand. |
| Fix a caption's wording | Captions come from the spoken words. Add a display mapping in `MERGE` / `DISPLAY` in `scripts/build.mjs`, then rebuild. |
| Add/remove/move a sound effect | Edit the scene's `sfx` list in `scripts/timeline.json` (`t` = scene-local seconds, `f` = file in `assets/sfx/`, `v` = volume), then rebuild. |
| Music louder/quieter | `music.lo` (under voice) / `music.hi` (gaps) in `scripts/timeline.json`, then rebuild. |
| Update a screenshot after an app change | Re-run the relevant capture script → `sh scripts/stage-assets.sh`. If the layout moved, re-place callouts with `node scripts/measure.mjs`. |

**Before rendering, always:**

```bash
node scripts/build.mjs
npx hyperframes check
```

`check` must end with "Check passed" (lint, layout, motion and contrast).

**Render**

```bash
npx hyperframes render -q delivery -f 30 --video-frame-format png -o renders/plantpulse-demo-v4.mp4
```

The full render takes several minutes. Upload the MP4 to YouTube (unlisted), as the technical meeting recommended. The 10 MB limit applies only to the deck PDF.

## Rules the video follows

- Every product shot is a real capture or recording of the app in its light theme, taken from the local dev build (bundled snapshot, 2 Oct 2026 data). Actions shown in scene 10 are the app's own offline simulation.
- Numbers come from the app or `docs/rancangan_solusi_plantpulse.md` §2.3/§5. AI test results are labelled **internal** (`docs/bukti_ai_diagnosis.md`).
- No savings, avoided-loss or "predicts failures" claims (see `docs/rancangan_solusi_plantpulse.md` §16).
- Hard cap 180 s. The current cut is 174.1 s. Tagline: "Check the pulse, not just the patch."
- The opening machine is an illustration (no stock footage). Its readings are the real E2 weekly values.
