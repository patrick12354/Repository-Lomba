# pipeline — Excel → `app/data/partpulse.db`

```
py pipeline/build_db.py                 # Windows
.venv/bin/python pipeline/build_db.py   # mac (uv venv .venv; uv pip install -r pipeline/requirements.txt)
```
Rebuilds the db from scratch in about 30 s (6.3 MB) and then runs `pipeline/app_tables.py` (Orang 2: `material_location`, `app_facts`). Control output is in `pipeline/build_output.txt`.

PR PO is de-duplicated on load (`analysis/load.py`): 5,420 of 11,609 lines were exact copies, 6,189 remain (PR + item unique). Every number below uses the de-duplicated data.

Service levels in `build_db.py` are the lean set, A/B/C/S = 95/90/85/80%. To rebuild while a server holds the database open, set `PARTPULSE_DB` to another path and copy it in with SQLite's backup API.

## What each table holds
| Table | Rows | Logic |
|---|---|---|
| materials | 7,481 | `build_mat.build()` + price fallback (PO → category×unit → category), lead-time fallback (material → category → global), Syntetos-Boylan class, health, trust_score |
| forecast | 7,481 | **Who moves:** LightGBM classifier. **How much:** LightGBM Tweedie, blended 50/50 with last-90-day run rate. Both are trained on stacked monthly 90-day folds (Jun-25..Jul-26, recent folds weighted with a 3-month half-life), so shutdown-season and normal windows are in one training set. Features: installed base, PM/notif load on its FLs, history and last-90-day momentum, lead time, category. `event_qty` = last TA kit × `ta_scale` only if the next TA falls within 180 d (with the default 2027-06-01 it does not, so it is 0); the turnaround layer in `policy` is independent of that horizon. q50/q90/q95 = compound Poisson simulation. `ltd_var = L·σd² + d²·σL²` |
| policy | 7,481 | SS = z(SL)·√ltd_var, ROP = ltd_mean + SS (p_move < 0.3 → compound Poisson quantile). Max = ROP + EOQ (capped at 1 yr of demand; A-critical stock items keep Max ≥ 1). Action rules and order-by date follow the ORANG_1 brief, plus REORDER when A/B stock < ROP. Turnaround: parts with stock < TA need + ROP get a TA order-by date (next TA − LT P90 − 14 d); they become REORDER only when that date is within 30 days, and REDUCE never cuts below the TA need |
| ta_kit | 360 | E1 replay of 2030 orders Nov-25..Jan-26 |
| frontier | 83 | 80 points on the budget-vs-risk convex frontier + `current`, `optimized`, `lean` (cheapest frontier point with risk ≤ current). Candidate levels per part include the policy ROP and the current Min, and all three points use the new lot size, so `current` and `optimized` can never fall below the curve |
| material_code | 10,524 | every part's equipment code from its BoM functional location (`PX_PP-490A-M` -> PP, line numbers -> PIPE) with its maintenance section. Feeds the To do code filter and task routing |
| ltd_quantiles | 7,481 | simulated lead-time-demand quantiles q80…q995 per part, for the service-level slider |
| twins / dq_issues / backtest / meta | | E4 groups, data-quality register, backtest (old `analysis/backtest_output.txt` + rolling validation below), all assumptions |
| consumption_monthly | 5,910 | issued qty per material × month (`ym` = `YYYY-MM`). `qty_event` = the 2030/2090 part. Sparse: a missing month means 0 |

## Forecast validation (rolling origin, 90-day routine demand)
At each origin the model is retrained only on folds that ended before that origin, then forecasts the next 90 days.

| Origin | AUC | AUC cold-start | AUC naive | Bias | Bias naive | MAE | MAE naive | q95 covers movers | q95 covers all |
|---|---|---|---|---|---|---|---|---|---|
| Apr-26 | 0.911 | 0.841 | 0.822 | +132% | +150% | 30.4 | 34.1 | 75.5% | 98.3% |
| May-26 | 0.912 | 0.844 | 0.828 | +59% | +13% | 23.9 | 20.7 | 74.4% | 98.1% |
| Jun-26 | 0.916 | 0.847 | 0.836 | −22% | −29% | 17.8 | 18.1 | 56.0% | 96.8% |
| Jul-26 | 0.925 | 0.860 | 0.855 | −7% | −17% | 16.8 | 17.0 | 63.5% | 97.5% |
| **Mean** | **0.916** | **0.848** | 0.835 | \|bias\| 55% | \|bias\| 52% | 22.2 | 22.5 | 67.4% | 97.7% |

**Headline for the deck:** "Knows which parts will move: AUC 0.92 vs 0.84 for the run-rate baseline. On parts with no history it reaches 0.85, where classic methods can only guess. On the two most recent origins, total demand is within −7 to −22%, and q95 covers about 97% of parts."

**Strict check (show next to the headline, e.g. in the appendix):** the main model uses the planner's current BoM Min/Max/MRP type as inputs. That is fine in production (they are known when the forecast runs), but the snapshot was read after the validation windows. Without those three inputs the same engine scores **AUC 0.892 (cold-start 0.773)**, MAE 22.1, mean |bias| 52%. That is still above the run-rate baseline (0.835) and SBA (0.61 on cold start). Wording for the deck: *"uses current planner Min/Max as input; strict variant without them: AUC 0.89."*

**Disclaimer (must be in the deck/appendix):**
- The data covers only 17 months, with one shutdown season. The first origins are trained mostly on the 2025 high-demand regime, so their bias is large (+59% to +132%). Bias settles once 2026 data enters training.
- The model configuration (Tweedie, blend, half-life, fold length) was chosen on these same 4 origins, so these metrics are slightly optimistic.
- Unit quantity is only on par with the naive run rate (MAE 22.2 vs 22.5). The edge is *who moves* and *cold start*, not volume.
- The dataset is dummy. Sell the mechanism.

Domain features (`pipeline/domain_features.py`: PM calendar, backlog, equipment class, siblings, kit partners, open PRs, twins) were ablation-tested and add no lift on this dataset. They are kept as planner context in `forecast.drivers` and in `reason`. Full decision log: `docs/04_MODEL_DECISIONS.md`.

Experiments tried and dropped: a single 180-day training window (validation bias +201%), per-class calibration (it captured seasonality and did not transfer), a TA-season flag (no effect), and rescaling to the recent level (bias got worse).

## Business metrics: policy backtest (`pipeline/policy_backtest.py`, table `policy_backtest`)
The actual goods issues of 1 Mar – 30 Sep 2026 (868 parts with demand, 720 of them A/B) are replayed against the current BoM Min–Max and against the PartPulse policy. The PartPulse policy is computed **point-in-time on 1 Mar 2026**: the forecast is trained only on folds that ended before that day, and lead times come only from earlier PRs. The simulation runs a daily (s, S) review. Unmet demand counts as lost (in reality an emergency buy). Every policy starts at its own Max. Replenishment lead times are drawn from each part's lead-time history, with the same draws for every policy.

| Policy | Fill rate, units (A/B) | Fill rate, issue lines A/B | Stockout-days A/B | Avg inventory value | of which PO-priced | POs |
|---|---|---|---|---|---|---|
| Current Min–Max | 35.9% (35.8%) | 66.9% | 57,055 | Rp 1,005 B | Rp 80 B | 616 |
| PartPulse high availability (SL 99/97/95/90%) | 96.2% (96.5%) | 98.6% | 2,830 (−95%) | Rp 1,401 B | Rp 514 B | 696 |
| **PartPulse lean, the recommended policy** (SL A/B/C/S = 95/90/85/80%) | **94.7% (95.0%)** | **97.5%** | **9,406 (−84%)** | **Rp 782 B (−22%)** | Rp 352 B | 654 |
| Strict forecast (no Min/Max/MRP), default / lean | 96.1% / 94.5% | 98.6% / 97.2% | 2,606 / 10,052 | Rp 1,586 B / 766 B | | |

**Headline:** *"Replaying Mar–Sep 2026: with 22% less inventory value, critical-part fill rate rises from 36% to 95% and A/B stockout-days fall 84% (on this dataset)."*

Read it honestly:
- The total inventory value includes category-estimated prices (84% of parts). Capital moves **out of parts that never move and into the parts that do**: PO-priced inventory rises from Rp 80 B to Rp 352 B. That is the point, but say it.
- Min/Max is held constant over the window. Lost-sales rule. The strict forecast gives the same picture, so the result does not depend on the snapshot.

Forecast-side business checks (rolling validation, mean of 4 origins):
- q95 covers 72.5% of moving **A/B** parts (67.4% of all movers; 97.7% of all parts).
- Rupiah-weighted WAPE: 1.86 vs 1.46 for the naive run rate. **Volume on expensive parts is the weak spot.** Do not headline it, and keep it in the appendix and Q&A.

## Control numbers (current run)
- Criticality order **A > B > C > S** (committee answer at TM, 4 Nov; S = special, lowest). "Critical" below means A/B.
- ta_kit: 360 / gap 154 (A/B 137, A 124) ✔. Gap value Rp 11.36 B on PO-priced parts.
- E1 wording (Orang 3): "For 79 stocked parts (71 A/B) the current Max is below one turnaround's need; 85 more kit parts have Max = 0 (82 kit parts are non-stock)." Do not quote "164 > Max" without this split.
- action: REDUCE 2,982 · MAINTAIN 2,113 · REORDER 1,698 · DISPOSE_REVIEW 546 · MONITOR 142. Only REORDER rows carry order_by_date = as_of; other dated rows fall later (order-by bug fixed, see decision log §J).
- Next 180 d routine forecast: 369 k units (next TA is outside the 180-day window). For comparison, the last 180 d had 336 k routine units, and the same window last year had 688 k.

## 5 numbers for Business Impact (on this dataset)
1. **TA readiness A/B** (next TA 2027-06-01, planning assumption, 244 days out): 58.7% today → 97.3% if every TA PR goes out by its order-by date (A only: 59.5% → 97.1%). Of 239 TA-short parts, 25 are already too late (19 A/B), 5 must be ordered this month, and 209 later.
2. **Releasable stock** (REDUCE + DISPOSE_REVIEW): Rp 421.6 B on PO-priced parts (207 parts). Including category-estimated prices it is Rp 5,546 B, but quote that only as an estimate.
3. **A/B parts at stockout risk** (P(lead-time demand > stock) > 1 − SL): 1,575 → 167 after REORDER.
4. **AUC who-moves:** rolling 0.916 vs naive 0.835. On cold-start parts: 0.848. Old backtest: 0.886 vs SBA 0.787, and on cold start 0.836 vs 0.613. Strict variant without Min/Max/MRP: 0.892 (cold 0.773).
5. **Rush PRs:** 17.8% of PRs ask for delivery in under half the normal lead time, and they arrive late 92.5% of the time vs 52.9% for normal PRs. An order-by date removes the rush request itself. (The old "88–93% preventable" claim is dropped: the same test gives 92% on non-rush PRs.)

Scenario (same lot size for all points, so they differ only by reorder level): current Min levels hold Rp 501 B of average inventory at risk index 7.51 M (A fill 94.2%). On the frontier, the same Rp 486–501 B buys risk 0.08 M (A fill 99.6%). The default policy (`optimized`) holds Rp 580 B, risk 0.52 M (−93%), A fill 99.1%. The lean point matches today's risk with Rp 71 B. Frontier columns are `fill_rate_A`, `fill_rate_B`.

## Assumptions (all in `meta`)
| Assumption | Value |
|---|---|
| as_of | 2026-09-30 |
| holding rate | 0.25 / yr |
| order cost | Rp 500 k per PR |
| service level A/B/C/S | 0.99 / 0.97 / 0.95 / 0.90 |
| downtime cost index A/B/C/S | 100 / 30 / 5 / 1 per day. This is an index, not IDR, so `risk_cost_yr` is in index units |
| downtime days | lt_p50 |
| next TA | 2027-06-01 (planning assumption, editable) |
| TA buffer | 14 d |
| `base_demand_scale` | 1.0 (app slider) |

Money is IDR. In English UI, write `Rp 11.35 B` (billion) or `Rp 850.0 M` (million).
