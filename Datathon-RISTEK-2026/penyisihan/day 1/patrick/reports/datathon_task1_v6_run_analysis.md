# Datathon Task 1 — V6 Full Run Analysis

## Outcome

V6 completed successfully on Kaggle T4 in 601 seconds (10m01s). All 12 code cells executed without exception and the submission passed the complete structural audit.

| Candidate | h5 | h10 | h15 | Balanced mean | Test-weighted mean |
|---|---:|---:|---:|---:|---:|
| AR | 36.4796 | 45.4011 | 52.6538 | 44.8448 | — |
| PCA residual | 33.4529 | 38.0610 | 40.8571 | 37.4570 | — |
| DirectLR r48/a30/resid-soft | 28.3292 | 30.1429 | 31.7825 | 30.0848 | 32.2494 |
| DirectLR r64/a30/resid-soft | 28.2311 | 30.1708 | 31.8250 | 30.0756 | 32.2550 |
| GNN two-seed average | 27.7485 | 31.4545 | 34.2498 | 31.1509 | 33.5191 |
| V6 primary cross-fitted blend | **26.9014** | **29.3777** | **31.2049** | **29.1613** | **31.2587** |
| V6 robust-weight diagnostic | **26.8921** | **29.3368** | **31.0330** | **29.0873** | **31.1688** |

## What improved

The low-rank sweep worked. V5 DirectLR balanced MSE was 32.6686; V6's best selected variant is 30.0756, a reduction of 2.5929 MSE or 7.94%. Both selected variants use alpha 30 and the soft local residual scales `(0.30, 0.15, 0.05)`. Rank 48 and rank 64 are effectively tied; rank 80 is slightly worse.

The combined DirectLR weight rises by horizon:

- h5: 44.63%
- h10: 62.21%
- h15: 66.21%

This confirms that low-rank city-state forecasting becomes more important as the forecast horizon grows.

## What did not improve

The final robust diagnostic is 31.1688, versus V5's same-fold 31.0305. V6 is worse by 0.1384 MSE or about 0.45% on that optimistic comparison. V5 has no cross-fitted-weight score, so its 31.0305 cannot be compared fairly with V6's primary 31.2587.

V6 and V5 submissions remain extremely similar: correlation 0.999669, MAE 0.3338 km/h, and prediction-difference RMSE 0.4995 km/h. Therefore V6 changes the internal decomposition more than the final forecast and should not be called a public-score breakthrough before submission.

## Weight stability

Calibration-half A versus B L1 weight differences are 0.1065, 0.1248, and 0.2042 for h5/h10/h15. The cross-fitted-to-diagnostic gap is only 0.0899 MSE. Weight overfitting is therefore present but modest; h15 is the least stable horizon.

Small positive AR weights appear at h10/h15 despite weak standalone performance. They may represent error complementarity, but they are also a possible symptom of split noise. More AR tuning is not justified.

## Submission audit

- 2,041,200 rows with IDs in exact sample-submission order.
- No duplicate IDs, NaN, or infinity.
- Prediction range 0 to 99.1477 km/h.
- Mean 52.8388 and standard deviation 19.4197 km/h.

## Decision

Submit V6 as a separate entry, while retaining V5. A rough Malfa-gap transfer points to the mid-35 public range, but this remains only a heuristic.

The next high-value experiment is not another seed or wider rank sweep. Use the best V6 low-rank anchor, then train a zero-initialized compact directed GNN on its normalized residual with cross-fitted horizon damping, following the strongest transferable result from Raphael V2. Skip text and Global FiLM unless a clean OOF ablation proves otherwise.
