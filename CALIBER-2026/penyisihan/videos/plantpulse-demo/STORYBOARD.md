---
format: 1920x1080
duration: 177s
message: "A repair is not a fix until the evidence says so — PlantPulse takes one incident from KPI to root cause to verified action in one workspace."
arc: The plant (what a compressor is) → Trip → Why is hard to find → False finish → Thesis → Proof walk KQ2 → KQ3 → KQ1 → Trust → Lockup
audience: CALIBER 2026 judges (Chandra Asri operations, IT and OT engineers)
mode: collaborative
version: v4 (plain-language opening, ElevenLabs clone of Raphael's voice, one type family, recaptured 3 Oct 2026)
---

# PlantPulse demo — storyboard v4

## v4 changes (3 Oct 2026)

- **Opening rewritten for a general audience.** v3 opened on "KO-3201 trips", microns vs mm/s and alert limits; a viewer who
  is not a reliability engineer could not tell what the machine was or why it mattered. v4 first shows the plant and the
  machine (Frame 0), then the trip in plain words ("shaking a little harder… crossed its safety limit and shut itself
  down"), then why the cause is hard to find (files that disagree, 60 vs 45 only), then the false finish in plain words.
- **Illustrated machine.** One shared navy-ink compressor drawing (`assets/art/compressor.svgfrag`, inlined by
  `scripts/inline-art.mjs`) appears in Frames 0, 1 and 3: flow runs in its pipes, the shaft stripes turn, the DE bearing
  shakes and throws vibration rings, the status lamp goes green → amber → red. It matches the app's own 3D compressor.
- **Voice:** ElevenLabs instant clone of Raphael's voice (`scripts/make-voice-11labs.mjs`, speed 1.1).
- **Re-sync without hand re-timing:** s05–s11 keep their authored (v3) cue times; `scripts/warp.mjs` wraps each scene
  timeline in a word-anchored time-warp so every move still lands on its word with the new voice. s12 keeps authored time
  (its mascot is a video) with word reveals re-timed by hand.
- **Type:** one family, as the web app's light theme UI: IBM Plex Sans for every word (headlines 700, −0.035em) and IBM
  Plex Mono for tags/sources/units. Archivo and the rounded logo wordmark image are gone; the name is set as text,
  "Plant" in ink and "Pulse" in accent.
- **Mascot ring fix:** the thesis ping rings are centred on the dial (measured on `assets/mascot/mascot-figure.png`, a
  crop of the mascot to its figure so the transparent padding no longer pushes it off-centre).

## Decisions

- **Message:** A repair is not a fix until the evidence says so.
- **Audience / arc:** engineering judges. Pain → turn → proof (follow KO-3201 through the four workflow screens) → trust → logo.
- **Format:** 1920×1080, ~175 s (hard cap 180 s), AI voiceover (EN), music bed + sound design, word-synced captions in the bottom 17% (content stays in the top ~83%).
- **Spine:** the **KO-3201 equipment tag** (the app's brand object: mono tag on a plate with a punched hole and a lit status band). It trips red in the cold open, rides in the top-right corner of every proof scene as the "case file", and its band changes state with the story: TRIP → NORMAL → FOLLOW-UP → EVIDENCE REQUIRED. The final lockup is the tag itself.
- **Second device — evidence lines:** whenever a number appears, a hairline draws from it to a mono source chip (L3, E2, R2…). Every fact carries its source, visually.
- **Mascot:** the PlantPulse gauge mascot (logo art + generated wave clip, assets/mascot/). Keyed off its cream ground by `scripts/key-mascot.py` (connectivity key + un-mix against the cream, so the cream dial face stays opaque and no halo shows on navy), lit with a back halo, floor pool and a pale rim so the navy outline reads. Appears only twice: brand intro (Frame 4) and sign-off (Frame 12). The logo wordmark is used reversed to white (assets/mascot/wordmark-white.png).
- **Brand:** frame.md (from prototype/DESIGN.md, light "Pipo" theme): paper #faf8ee under the drifting Pipo bloom mesh (compositions/atmos.html), accent #2f62e0, danger #d63c43, caution #d48a06, ok #1d9a63, info #0a8cc4, ai #7656ec; IBM Plex Sans (every word; headlines 700), IBM Plex Mono (tags/sources/units). Act 1 sits on quiet paper with story-keyed mood blooms (TRIP red, NORMAL green, FOLLOW-UP amber); the mesh wakes on "PlantPulse". v1 was dark (git 9dadc5f).
- **Truthfulness:** every product screen is a real capture of the live app (caliber-2026-heisenberg.vercel.app, published snapshot 2 Oct 2026). Every number comes from the app or docs §2.3/§5. AI test numbers are labeled "internal". No savings claims.
- **Bans:** no fake UI, no gradient text, no neon bloom, no stock footage, no slideshow (every scene moves a camera or builds state), no screensaver motion.
- **Held frame:** Frame 04 — the thesis line sits still on paper for 1.5 s after it lands.
- **Seam direction:** the camera always travels right / deeper into the case (left-to-right push), matching the app's workflow stepper (Overview → Problem Tank → Investigation → Actions).

## Frame 0 — The plant (0–10s)

- scene: A petrochemical skyline draws itself in navy ink (columns, cracker furnaces, compressor house, spheres, flare, pipe rack with product flowing). The camera dives into the compressor house; the compressor is drawn up behind a scan line and its parts are named (compressor, motor, coupling, bearing, gas in/out), lamp green "RUNNING". It shrinks into one tile of a field of ~170 machine tiles joined by product lanes; a PRODUCTION meter fills. On "when it stops" our tile trips red; lanes and machines downstream stall, the meter drains to STOPPED. Dive into the stopped tile.
- src: compositions/s00-plant.html
- voiceover: "This is a compressor in a petrochemical plant. It is one of hundreds of machines that keep the plant running, and when it stops, production stops with it."
- audio: drawing scan, machine hum (synthesised), label ticks, bass hit + spin-down on the stop

## Frame 1 — Trip (10–25.3s)

- scene: The same compressor running on the left, shaking harder week by week (vibration rings off the DE bearing, "VIBRATION SENSOR" label). Right: the week label, a NORMAL/ALARM/TRIP gauge driven by the real weekly E2 readings (28.9 → 76.5 µm, plain caption "How hard the machine shakes, measured at its bearing") and the weekly trace. "29 APR 2026" lands; on "crossed its safety limit" the needle hits red, red flash, "SAFETY LIMIT CROSSED"; on "shut itself down" the shaft spins down and the machine greys, the KO-3201 tag slams in with TRIP. "32 h offline" (clock races, L3 · row 5), "US$1,584,000 recorded loss" counts up (L3 · R2). Tag travels to centre.
- src: compositions/s01-trip.html
- voiceover: "For weeks, compressor K O thirty-two oh one had been shaking a little harder. On April twenty-ninth, twenty twenty-six, it crossed its safety limit and shut itself down. Thirty-two hours offline. One point five eight million dollars of recorded loss."

## Frame 2 — Why is hard to find (25.3–37.2s)

- scene: "Why did it trip?" over the tag. Four real source files burst out (file-type badges: two spreadsheets, the PI sensor export, the RCA slide deck); a magnifier digs from file to file as each kind is named. "They don't even agree": the RCA deck's "Alert was 60 micron" and the equipment file's "alarm 45 micron" light up and two sticky notes, 60 and 45, slam in with a red ≠. Everything collapses back into the tag.
- src: compositions/s02-scatter.html
- voiceover: "To find out why, an engineer has to dig through four different sources: spreadsheets, sensor logs, and a slide deck. And they don't even agree. One says the alarm limit is sixty. Another says forty-five."

## Frame 3 — False finish (37.2–45.8s)

- scene: The stopped, greyed compressor; a wrench works on the bearing (REPAIRED); colour returns, the shaft spins up, lamp green (RUNNING AGAIN), tag band NORMAL, five normal post-repair weeks (E2). "Case closed?" with a green check — on "But" the check cracks, the line is struck, band FOLLOW-UP REVIEW. The machine steps aside; two open actions rise in plain words: "Install an online oil-quality sensor · In progress · Past plan date" and "Replace the leaking cooler tubes · Still open" (R2). Verdict: "Recovered ≠ prevented".
- src: compositions/s03-false-finish.html
- voiceover: "So the machine gets repaired, it runs fine again, and the case looks closed. But the fixes that would stop it from happening again are still not done."

## Frame 4 — Thesis (45.8–53.8s)

- scene: Paper. The rule builds word by word in IBM Plex Sans 700; "evidence" in accent with an underline. Held still ~1 s. The line lifts, the mascot springs up (stretch, squash, settle), two rings ping out of the centre of its dial, and the name wipes in beside it as text ("Plant" ink, "Pulse" accent).
- src: compositions/s04-thesis.html
- voiceover: "PlantPulse is built on one rule. A repair is not a fix, until the evidence says so."
- audio: music bed enters as the mascot lands

## Frame 5 — Single pane (KQ2) (53.8–68.05s)

- scene: The real Executive Overview capture flies in as a tilted glass plate and flattens. Camera punches in on the KPI row: "US$61.89M actual" and "US$5.31M potential" get separate callouts ("never mixed"). Pan down to the 3D site (12 plants, light columns) and the five-machine condition gauges (KPI hit/miss). Corner chip: "KQ2 · Executive view".
- duration: 14.0s
- transition_in: push-right
- status: animated
- src: compositions/s05-overview.html
- blueprint: device-surface-showcase (floating-window push-scroll) + camera-journey
- voiceover: "One executive overview brings together all three hundred eighty incidents across twelve plants and all five RCA cases. Actual and potential loss are never mixed, and each machine is shown against its own limits."
- audio: soft whoosh on the plate landing, ticks on each callout

Tag in the top-right corner (band FOLLOW-UP). Constraint: callouts point at real pixels in the capture.

## Frame 6 — Problem Tank (KQ3) (68.05–81.21s)

- scene: Problem Tank capture. Camera glides across the 220-cell priority strip (cells light as the camera passes), then lands on the five evidence-package cards; cursor clicks KO-3201 (#1, "4 past plan"). Callout: "Recorded values only — no invented risk score."
- duration: 13.8s
- transition_in: push-right
- status: animated
- src: compositions/s06-queue.html
- blueprint: cursor-ui-demo + camera-journey
- voiceover: "The Problem Tank ranks all two hundred twenty open records by lifecycle, risk class and due date, using recorded values only. KO-3201 is first in line, with four actions past plan."
- audio: strip scan swish, click

## Frame 7 — Evidence & conflicts (81.21–91.04s)

- scene: An evidence drawer (real capture) slides over; a fact row ("DE radial vibration 76.5 µm, wk 21") draws an evidence line to its source chip "E2 · Condition History · row 21". Then a conflict card stamps in: "Alert limit: 60 µm (RCA R2) vs 45 µm (Equipment Info E2) — owner decides, not AI."
- duration: 11.2s
- transition_in: push-right
- status: animated
- src: compositions/s07-evidence.html
- blueprint: panel-edit-live-sync (drawer bound to its source) + kinetic-type-beats
- voiceover: "Every fact opens to its exact source row. And where the sources disagree, PlantPulse shows the conflict and assigns an owner, instead of quietly picking a side."
- audio: drawer slide, stamp thud

Exact drawer content to be taken from the live app at capture time.

## Frame 8 — Machine checkup (91.04–104.81s)

- scene: Investigation capture; camera dives into the 3D machine view (recorded clip of the real three.js model rotating) with its numbered pins. The checklist ticks: 4 readings ✓ green, then action rows ✗ red. Gauge counts up to "5 / 11 checks passed".
- duration: 13.8s
- transition_in: push-right
- status: animated
- src: compositions/s08-checkup.html
- blueprint: agent-progress-theater (checklist checks off) + dataviz-countup (gauge)
- voiceover: "In Investigation, a machine checkup pins every reading to the part where it is measured. All four readings are inside their limits. But only one of six RCA actions is closed. Five of eleven checks pass."
- audio: four soft ticks (pass), two dull knocks (fail)

## Frame 9 — AI investigator + Evidence Guard (104.81–128.61s)

- scene: Split stage on the real captures: left, the ranked differential (causes as bars, #1 "water ingress via lube-oil cooler tube leak" in --ai violet); right, the AI brief streams in sentence by sentence, each sentence gets a green "supported" chip with a source ref; one deliberately bad sentence gets a red "unsupported — number not in cited excerpt" and is struck out. Then a stat card: "Internal blind test, RCA hidden: top-1 7/9 · top-3 9/9".
- duration: 24.2s
- transition_in: push-right
- status: animated
- src: compositions/s09-ai.html
- blueprint: prompt-type-submit-generate (streaming answer) + agent-progress-theater
- voiceover: "The AI investigator ranks probable causes with repeatable rules, finds similar past incidents, and drafts the brief. Then an Evidence Guard checks every sentence: each number has to appear in the source it cites, or the sentence is flagged. In our internal blind test, with the RCA hidden, the recorded cause ranked first in seven of nine runs, and in the top three every time."
- audio: soft typing texture, green ticks, one red buzz on the flagged sentence

As built: the "flagged" moment is the app's real Missing-source test (EV-03 withheld → claim struck through, cannot be approved).

## Frame 10 — Action & closure gate (128.61–147.96s)

- scene: Actions & verification capture. Cursor fills the action card: owner "REL-05", due date, evidence needed (3 rows MISSING in red). Cursor hits "Close" → the card shakes, a stamp: "Can't close — 3 evidence items missing." Evidence attaches (rows flip green), status → "Ready for verification"; a second avatar "Reviewer ≠ owner" signs; follow-up pipeline bar advances Draft → Verified; a hash-chain strip clicks closed.
- duration: 18.5s
- transition_in: push-right
- status: animated
- src: compositions/s10-actions.html
- blueprint: cursor-ui-demo (one workflow end to end onto the action button)
- voiceover: "Then insight becomes action. Every corrective and preventive step gets an owner, a due date, and the evidence required to close it. Try to close it without that evidence, and PlantPulse refuses. A reviewer who is not the owner signs off, and every decision is written to a tamper-evident log."
- audio: typing, click, error thud, three green ticks, signature swish, chain click

Tag band ends at "READY FOR VERIFICATION", never "VERIFIED": the demo action is simulated and labeled, and we never fake a verified outcome.

## Frame 11 — Foundation & trust (KQ1) (147.96–165.84s)

- scene: Data foundation capture: the 4-column source map (Sources → Quality gates → Governed entities → Views) lights column by column, "23 / 23 reproduction checks" counts up. Then three trust chips stack: "Read-only to the plant — no DCS / SAP writes", "Human sign-off on every decision", "Claims only what it measured". Then the three KQ chips tick: KQ1 Data foundation ✓ · KQ2 Executive view ✓ · KQ3 Root cause → action ✓.
- duration: 18.2s
- transition_in: push-right
- status: animated
- src: compositions/s11-trust.html
- blueprint: grid-card-assemble + dataviz-countup
- voiceover: "Underneath, sixteen source files map through six quality gates into one governed model, and every headline number is reproduced from its source: twenty-three of twenty-three checks pass. PlantPulse is read-only toward the plant, keeps a human in every decision, and claims only what it has measured."
- audio: column ticks, count-up whirr

## Frame 12 — Lockup (165.84–176.84s)

- scene: Split lockup. Right: the KO-3201 tag returns with its band lit "EVIDENCE REQUIRED", flips away on "PlantPulse" and the name (Plex Sans text, "Pulse" in accent) wipes in where it stood, a pulse line drawing under it; the rule builds word by word; URL + team footer. Left: one keyed take of the mascot walks in, settles on a pool of light, reacts to the rule, waves goodbye, then jumps (ring + sparks on landing) and ends on a wink as the frame fades to paper.
- duration: 11.0s
- transition_in: crossfade
- status: animated
- src: compositions/s12-lockup.html
- blueprint: logo-assemble-lockup
- voiceover: "PlantPulse. A repair is not a fix until the evidence says so."
- audio: music resolves on the last chord

Callback to Frame 1 (the tag) and Frame 4 (the line).

Total (as built): **176.84 s** (cap 180 s). Timings regenerate from `scripts/timeline.json`; s05–s11 follow the voice through `scripts/warp.mjs`.
