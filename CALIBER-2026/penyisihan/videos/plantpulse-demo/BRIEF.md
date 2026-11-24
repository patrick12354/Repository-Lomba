---
workflow: general-video
flow: companion
storyboard: yes
message: "A repair is not a fix until the evidence says so — PlantPulse takes one incident from KPI to root cause to verified action in one workspace."
destination: youtube
aspect: 1920x1080
language: en
audience: CALIBER 2026 judges (Chandra Asri operations, IT and OT engineers)
length: 180s max (target ~175s)
angle: follow one incident (KO-3201) end to end
voice: elevenlabs-clone (Raphael)
---

## Intent

The mandatory ≤3-minute demo video for CALIBER 2026 Case 2 (Intelligence Manufacturing), Team Heisenberg.
It must explain and demonstrate how PlantPulse works and "sell" it (judges score pacing, narration, and
whether the solution lands in 3 minutes). User asked to go all out as a motion designer and video editor.
Judging weight is heaviest on Solution Design & Prototype Quality: show a *proven* solution (input →
expected output), not just UI. The flow judges expect: dashboard shows KPI hit/miss → AI explains cause
with supporting analysis → corrective + preventive action recommendations based on past incidents.

## Assets

- capture/*.png — 2x captures of the live app (https://caliber-2026-heisenberg.vercel.app/), dark theme, every page.
- ../../prototype/DESIGN.md — the product's design system; frame.md is derived from it.
- ../../docs/rancangan_solusi_plantpulse.md §2.3, §5, §16 — the only allowed numbers and claim wording.
- ../../docs/bukti_ai_diagnosis.md — internal AI test results (label as internal).

## Customizations

- Narration: English voiceover in Raphael's cloned voice (ElevenLabs instant voice clone, v4) with word-synced captions.
- Opening (v4): explain the case to a general viewer first: what a compressor is and why a stop matters, then the trip, then why the cause is hard to find, in plain words. Real machine drawn (illustration), never stock footage.
- Visuals: hybrid — real captures of the live app staged inside motion-designed scenes (punch-ins, callouts, cursor), plus designed problem / thesis / close scenes.
- Angle: follow KO-3201 end to end; answer all three Key Questions on screen (KQ1 data foundation, KQ2 executive overview, KQ3 problem tank → root cause → actions).
- Music bed + sound design (trip alarm, UI ticks, whooshes).

## Notes

- All copy in English. No faces required.
- Never claim savings, avoided loss, downtime reduction, or "AI predicts failures". Use §16 wording.
- AI test numbers are internal ("internal blind test").
- Energy is a current-based proxy, never kWh.
