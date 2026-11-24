# PlantPulse prototype — evaluation results (2 Oct 2026)

Everything here is an **internal check by the team's build session**. No independent domain reviewer, user study or pilot has run yet.

## A. Data invariants — `pipeline/validate_case2.py`

23 of 23 reproduction checks pass against the design audit (Appendix A/B of `docs/rancangan_solusi_plantpulse.md`). Details: `data/generated/validation_report.md`.

## Reference tasks G01–G10 (design §10.6)

| ID | Expected behaviour | How it was checked | Result |
|---|---|---|---|
| G01 | Actual US$61,886,460 and potential US$5,307,970 stay separate | `domain.test.ts` + Overview ledger | pass |
| G02 | 226 `n/a` AR rows stay distinct incidents | `domain.test.ts` (V03, unique snapshot IDs) | pass |
| G03 | KO-3201 repair Closed does not close sensor, retube or roll-out | `domain.test.ts`; Queue and Actions show due states | pass |
| G04 | Retube (31 Oct 2026) is not overdue on 2 Oct | `domain.test.ts`; badge "Not yet due" | pass |
| G05 | Weekly micron and hourly MM/S vibration are never overlaid | Separate charts; conflict CF-06; validation V17 | pass |
| G06 | Closing the sensor action with cooler-repair evidence is blocked | `domain.test.ts` + scripted UI run in the browser (hold message lists the missing evidence and why the repair record does not count) | pass |
| G07 | `Dominant Failure Mode` never reaches the masked run | Allowlist in `input_manifest.json`; `domain.test.ts` checks the evidence text | pass |
| G08 | Without the RCA, no definite "cooler tube leak" conclusion | Masked brief lists the water source as speculative; forbidden-string check passes | pass, **but the run is contaminated** (see below) |
| G09 | Filtering to one plant changes the counts and the denominator | `domain.test.ts` (ZCU → 62 records) + Overview filter | pass |
| G10 | Strict replay excludes sources with unknown availability time | Strict replay view lists every source as `available_at unknown` and runs no brief or similar-RCA lookup | pass |

## B. AI briefs — `pipeline/generate_briefs.py`

| Run | Structural check | Claim support (internal) | Validity |
|---|---|---|---|
| `2026-10-02_ko3201_snapshot_review` | pass, 35 citations, all inside the allowlist | 15 of 15 factual statements supported by the cited excerpt | Valid as a post-incident summary. Recorded in the build session, not through the API |
| `2026-10-02_ko3201_masked_diagnostic` | pass, 25 citations, no target strings | 4 of 4 supported | **Contaminated.** The generating model had read the target RCA earlier in the session, so it does not count as a blind diagnostic test |

Not done yet: a B0/B1/B2 comparison, a fresh API run for the masked test, perturbation runs through the model itself (the UI's missing-source test only shows the citation-withholding behaviour), and any independent review.

## C. Task timing and D. pilot

Not run. No time-saving or downtime figure may be quoted until they are.

## E. v2 AI platform (2 Oct 2026, internal, OpenAI models)

| Feature | Measure | Result | Run |
|---|---|---|---|
| TS ingestion port | Field-for-field parity with the validated Python output (incident register, 5 equipment, 5 production, 5 RCA decks) | 16 of 16 files identical | `prototype/server/ingest/*.test.ts` |
| Anomaly detection | Series flagged before their shutdown (one shutdown per series) | 4 of 5. KO-3201 flagged 46 h before the first OFF hour, BL-5702 28 h, PU-2101B 17 h, HE-3301 4 h. PM-4405B **missed**. No event without a following shutdown. | `runs/2026-10-02_anomaly/` |
| Failure-pattern clustering | Families over 380 records | 16 families, each over 7–12 plants. Coherence per human review: **not reviewed yet** | `runs/2026-10-02_patterns/` |
| RCA auditor (gpt-6.1-sol) | Hand-found KO-3201 conflicts found (CF-01 to CF-05), plus a prompt-injection case | **3 of 5** (CF-01, CF-02, CF-05 found; CF-03 duration and CF-04 supply pressure missed). Injection case passed: 0 planted claims, conflicts still found. Other decks: PU-2101B 4, PM-4405B 0, HE-3301 0, BL-5702 4 conflicts, **not yet human-reviewed**. Cost US$0.25 for all five decks. | `runs/2026-10-02_rca_auditor/` |
| Copilot + Evidence Guard (gpt-6.1-sol) | Reference questions G01, G03–G05, G09 and a savings trap | First run **5 of 6** (G05 failed: the copilot had no tool for hourly data, and the guard misread the asset tag KO-3201 as a number). After adding the `get_hourly` tool and fixing the guard (the eval patterns were not changed): **6 of 6**, 0 unsupported sentences. Cost US$0.05 per six questions. | `runs/2026-10-02_copilot_g_tasks/` (second run) |
| Evidence reader (gpt-6.1-sol) | 4 synthetic fixtures (wrong action, right document, wrong asset, undated) | **3 of 4**. All four were classified as the right kind. The commissioning record still produced warnings (the model listed the missing signal validation and alarm config, which belong to other documents), so the "no warning" expectation failed. | `runs/2026-10-02_evidence_reader/` |

Deterministic layers around the AI features are unit-tested without network calls: claim checker (7 tests on real KO-3201 records), verbatim-quote filter, Evidence Guard structural pass, evidence-rule interpretation, RCA draft sanitising, action guards and authorization.

## F. AI diagnosis layer (2-3 Oct 2026, internal)

| Item | Measure | Result | Run |
|---|---|---|---|
| Fleet predictability | Later incidents hit by top-10 earlier families (cutoffs 2025-01-01, 2025-07-01, 2026-01-01) | 5.2%, 4.4%, 4.8% vs 5.6% family share; 0 repeating (plant, tag) pairs of 380 | `runs/2026-10-02_fleet_predictability/` |
| Matcher lock-on | Weeks before trip when the documented cause is the unique leading hypothesis | 11 to 13 weeks on all 5 assets; 4 of 5 before the first ALARM label; BL-5702 wrong for 1 week. Library written after reading the RCAs | `runs/2026-10-02_diagnosis_masked/` |
| Masked investigator | RCA hidden, gold pre-registered, 9 runs | Top-1 7 of 9, top-3 9 of 9, check separates gold 8 of 9, 0 leakage. Misses: KO-3201 week 8, BL-5702 week 8 | `runs/2026-10-02_diagnosis_masked/` |
| Chronos-2 weekly backtest | 160 cutoffs, 8-week horizon | Band coverage 64%; P50 MAE 1.38 weeks (89 missed) vs linear 1.55 weeks (62 missed). Headline is the linear estimate | `runs/2026-10-02_condition_forecast/` |
| Hourly bands | Chronos bands vs MAD detector | Bands fire 13 to 24 times per asset; MAD stays primary | `runs/2026-10-02_condition_forecast/` |
| Energy forecast | WAPE vs best naive, 168 h | PU-2101B 2.31% vs 3.03%, KO-3201 25.65% vs 25.47%, PM-4405B 2.35% vs 3.33%, BL-5702 2.34% vs 2.64% | `runs/2026-10-02_condition_forecast/` |
| Coverage (all open records) | Open records with a candidate failure mode / a data-quality flag | 41 of 220 get at least one register-level candidate; 5 get a DQ flag | `prototype/src/domain/coverage.test.ts` |
