# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

React + TypeScript + Vite on Vercel, with Vercel Functions (`prototype/api`), Supabase (Postgres, Auth, Storage) and the OpenAI API (gpt-6.1-sol, gpt-6-luna). v1 data is extracted offline by Python (openpyxl, numpy, python-pptx); the bundled JSON still powers the offline demo (`?offline=1`). Weekly analytics jobs run in GitHub Actions. Sign-in is off during the trial phase (`AUTH_MODE=open`).

## Users

Primary: a reliability engineer at a petrochemical plant reviewing an equipment incident and deciding the next accountable action. Secondary (design roles, not confirmed org structure): maintenance planner / discipline owner, operations, plant manager, data owner. Evaluators: CALIBER 2026 judges (Case 2: Intelligence Manufacturing), viewing on a laptop and in a ≤3-minute demo video.

## Product Purpose

PlantPulse is an evidence-backed reliability decision and follow-up workspace. It links each equipment issue to its source evidence, uncertainties, owner, and completion criteria, so engineers make traceable decisions and verify that corrective and preventive actions are actually completed — not just that the machine recovered.

## Positioning

Not "alert → recommendation → action" (SAP APM already does that). The defensible focus: evidence reconciliation before decisions (loss types, units, threshold versions, incident identity never silently merged); AI that shows the limits of its evidence; completion states gated by evidence (repaired ≠ recovered ≠ prevention done ≠ verified effective); open evaluation against simple baselines.

## Operating Context

Source files from the competition: Incident Database (380 rows, 12 plants), Equipment Performance (5 equipment × 26 weekly readings), Production Data (5 × 720 hourly rows), 5 RCA decks. Review date for the snapshot: 2 Oct 2026. Main demo case: KO-3201 cracked gas compressor (repair Closed, sensor install In Progress past plan date, retube Open, roll-out Open).

## Capabilities and Constraints

Four screens: Overview, Problem Queue & Evidence, Investigation, Actions & Verification. Data foundation and energy-proxy forecasting live inside Overview/Evidence. All UI in English. Every factual number links to its source location. No invented savings, probabilities, or detection-lead claims. Energy is a current-based proxy, never kWh. HE-3301 excluded from motor-energy demo. Simulated actions are labeled and kept apart from snapshot status. AI briefs are pre-generated from recorded runs and labeled internal review: recorded runs now come from the OpenAI models in `server/ai/client.ts`, and the KO-3201 brief run is labelled as recorded in the authoring session.

AI diagnosis layer (internal evidence in `evaluation/results.md` section F): a forecast window to act in (not a failure date); differential diagnosis (ranked by code, explained by AI, RCA hidden); effectiveness check and sister assets; reminders with escalation; and a labelled example business scenario.

## Evidence on Hand

docs/rancangan_solusi_plantpulse.md (audit numbers, conflict list, claims allowed/forbidden). Supporting Data/Case 2_ Intelligence Manufacturing/. No user study, no pilot, no measured time savings, no domain-expert review exists — must not be fabricated.

## Product Principles

1. Every fact carries its source, time, unit, and quality status.
2. Show conflicts; never resolve them silently.
3. Separate observation, documented finding, hypothesis, and simulation.
4. Closure requires evidence and a reviewer, not a button.
5. Claim only what has been measured.
