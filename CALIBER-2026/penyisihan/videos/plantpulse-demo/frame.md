# frame.md — PlantPulse demo, "Pipo" (light)

Source of truth: `prototype/DESIGN.md` and `prototype/src/styles.css` (`:root[data-theme="light"]`). The video wears the
product's own light skin. (The first cut was dark "control room"; it lives in git history at 9dadc5f.)

## Concept

Engineering drawings on paper. One continuous paper ground runs under the whole film (`compositions/atmos.html`): the
app's Pipo bloom mesh (apricot `#E6B093`, sky blue `#A3CEFF`, paper `#FAF9EF`) drifting from one clock, so the light never
resets at a cut. Act 1 (the problem) sits on quiet, near-bare paper with mood blooms keyed to the story: a red flare on
the TRIP, green on "reads normal", amber when it cracks. On "PlantPulse" in the thesis the mesh wakes to full colour and
stays awake for the proof. Real captures sit on frosted white plates with soft navy shadows; designed type is navy ink.

## Palette (by role)

| Role | Hex | Use |
|---|---|---|
| ground | #faf8ee | paper (atmos layer) |
| panel | #ffffff | plates, cards, labels, chips |
| line | rgba(24,38,72,.11) / .20 | hairlines, borders |
| ink-hi | #0b1426 | display type |
| ink | #15213a | body type |
| ink-3 | #56647d | secondary labels |
| accent | #2f62e0 / #2450bf | the one interactive accent, cursor ring, "evidence" |
| danger | #d63c43 / ink #a41f27 | TRIP, conflict, missing evidence |
| caution | #d48a06 / ink #835200 | follow-up, past plan |
| ok | #1d9a63 / ink #0d6a42 | normal, passed, verified |
| info | #0a8cc4 / ink #06658e | observed fact / source chips |
| ai | #7656ec / ink #5332c2 | model output only |
| shadow | rgba(38,48,78,a) | every drop shadow (navy, never black) |

Status colours never decorate; each always ships with its word (TRIP, NORMAL, MISSING…). Light grounds wash glows out,
so callouts are a crisp ring plus a soft tinted halo, never a bloom.

## Type

- One family, exactly as the web app's light theme UI (`--font` / `--font-mono` in prototype/src/styles.css).
- Headlines: **IBM Plex Sans** 700, tracking −0.035em. 76–132px. (v3 used Archivo expanded; removed in v4 so nothing reads as a second typeface.)
- The product name is set as text, never the rounded logo wordmark image: "Plant" in ink, "Pulse" in accent.
- UI/body: **IBM Plex Sans** 400/500/600, tabular figures. Body ≥ 28px in video.
- Mono: **IBM Plex Mono** 500 — equipment tags, source IDs (L3, E2, R2), units, timestamps.

## Brand object — the equipment tag

A white enamel nameplate: lit top lip, navy stamped mono number, punched hole showing the paper behind, and a lit status
band at the bottom (TRIP red → NORMAL green → FOLLOW-UP amber → EVIDENCE REQUIRED blue). It is the film's spine.

## Motion

- Easing: `cubic-bezier(0.16,1,0.3,1)` (expo-out) for entrances; `power2.inOut` for camera moves.
- State transitions 0.15–0.25s; panel rises 0.5s; camera punch-ins 0.9–1.4s.
- Evidence lines: hairline paths drawing from a fact to its source chip, 0.6s.
- Ambient: the Pipo mesh drifts (slower in act 1, app speed after the logo). No bouncy springs, no neon bloom.

## Bans

No gradient text, no purple-blue hero gradients, no fake UI (only captures or faithful rebuilds of the app),
no invented numbers, no stock footage, no slideshow (static card per beat), no screensaver motion.
