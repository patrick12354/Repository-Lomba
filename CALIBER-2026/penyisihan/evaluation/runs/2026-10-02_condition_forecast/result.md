# Condition forecast (Chronos-2, zero-shot) — internal
Weekly trip-crossing backtest, cutoffs from week 6 to the week before trip, horizon 8 weeks: 160 cases.
- Chronos-2 window coverage (P90→P10 contains the actual week): 0.64
- Chronos-2 likely (P50) mean abs error: 1.38 weeks; missed: 89 (P50 never crosses within 8 weeks)
- Linear 6-week trend mean abs error: 1.55 weeks; missed: 62
Hourly band exceedance vs MAD detector (4/5; leads 46/28/17/4 h, PM-4405B missed): first sustained exceedance lead PU-2101B 73 h, KO-3201 482 h, HE-3301 280 h, BL-5702 188 h, PM-4405B none before shutdown. Bands also fire repeatedly well before the fault window (13 to 24 events per asset), so the long leads include early or false exceedances and are not comparable to the MAD leads without a false-alarm check.
Energy (motor current, 168 h test): Chronos-2 WAPE vs best naive per asset: PU-2101B 2.31% vs 3.03%, KO-3201 25.65% vs 25.47%, PM-4405B 2.35% vs 3.33%, BL-5702 2.34% vs 2.64%.
Reading: the synthetic weekly series are near-linear, so a linear trend is a strong baseline. Chronos-2's value here is the uncertainty band, not a better point estimate. The P50 MAE is lower than linear only because it is computed over fewer cases (it misses 89 vs 62); on coverage of the actual week it is 64%.
Display rule outcome: linear_mae (1.55) is not lower than mae_likely (1.38), so the Chronos P50 is the headline, with the linear estimate shown beside it.

Correction: the P50 MAE (1.38 weeks) looks better than linear (1.55) only because it is scored on fewer cases; Chronos P50 forecast no crossing within 8 weeks in 89 of 160 cases, linear in 62. Read both numbers together: the headline is the linear point estimate, and Chronos is the uncertainty band (64% window coverage). The display rule now picks linear when it misses fewer crossings, not only when its MAE is lower. Hourly Chronos bands fire 13 to 24 times per asset, so the existing MAD detector stays primary for hourly anomalies.
