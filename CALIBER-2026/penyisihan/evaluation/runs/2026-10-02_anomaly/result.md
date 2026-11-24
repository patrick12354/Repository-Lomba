# Anomaly detection on hourly PI data — internal run

Date: 2026-10-02 · Detector: `analytics/anomaly.py` (robust median/MAD z-scores over running hours, RMS-combined, reference = first 168 h, threshold 4.0 sustained 3 h; motor current excluded). Input: bundled snapshot `prototype/src/data/case2.json`.

Five series, one shutdown each. This is a per-series description, not a detection rate.

| Series | Events | First flag | First OFF hour | Lead before OFF (h) | Top contributor (z) | Events with no shutdown after |
|---|---|---|---|---|---|---|
| PU2101B | 1 | 2026-03-11 10:00:00 | 2026-03-12 03:00:00 | 17 | PU2101B_VIB (10.22) | 0 |
| KO3201 | 1 | 2026-04-27 09:00:00 | 2026-04-29 07:00:00 | 46 | KO3201_VIB (170.62) | 0 |
| PM4405B | 0 | — | 2026-07-08 14:00:00 | — | — | 0 |
| HE3301 | 1 | 2026-05-21 05:00:00 | 2026-05-21 09:00:00 | 4 | HE3301_FEED (-9.68) | 0 |
| BL5702 | 1 | 2026-06-16 01:00:00 | 2026-06-17 05:00:00 | 28 | BL5702_VIB (23.25) | 0 |

PM4405B produced no event above the threshold before its shutdown: a miss, reported as such. Lead times are measured from the file, not claimed in general.
