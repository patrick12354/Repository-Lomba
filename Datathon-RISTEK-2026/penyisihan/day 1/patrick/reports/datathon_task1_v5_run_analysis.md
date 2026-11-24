# Datathon Task 1 — V5 Full Run Analysis

## Outcome

V5 completed successfully on Kaggle T4 in 579 seconds (9m39s), with no notebook exception. The generated submission is structurally valid and safe to submit.

| Candidate | h5 | h10 | h15 | Balanced mean | Test-weighted mean |
|---|---:|---:|---:|---:|---:|
| AR | 36.4796 | 45.4011 | 52.6538 | 44.8448 | — |
| PCA residual | 33.4529 | 38.0610 | 40.8571 | 37.4570 | — |
| Direct Low-Rank | 30.6459 | 32.7328 | 34.6271 | 32.6686 | — |
| GNN two-seed average | 27.7485 | 31.4545 | 34.2498 | 31.1509 | 33.5191 |
| V5 blend | **26.5988** | **29.1804** | **31.0176** | **28.9323** | **31.0305** |

Compared with Malfa's matching validation design, V5 improves inferred-test-weighted MSE from 32.5292 to 31.0305: a reduction of 1.4987 MSE or 4.61%.

## What worked

- Direct Low-Rank is the breakthrough component. Its ensemble weight rises from 0.403 at h5 to 0.596 at h15.
- The GNN remains useful, but its weight falls from 0.466 at h5 to 0.293 at h15. Local/nonlinear dynamics matter most at the near horizon; low-rank city-state dynamics dominate farther ahead.
- PCA residual retains a stable 0.111–0.131 weight and supplies a small complementary signal.
- AR receives zero weight at every horizon and should not receive more tuning budget.

## Validation caveat

The submission has no target leakage or formatting bug. However, 31.0305 is a same-holdout diagnostic: architecture/epoch selection and final simplex weights all use the same randomized-day holdout. Therefore it is optimistic as an absolute public-score estimate. The comparison against Malfa is more informative because both use essentially the same validation design.

A rough transfer of Malfa's local-to-public gap suggests about 35.6 public MSE for V5, but this is only a heuristic and must not be presented as guaranteed.

## Submission audit

- 2,041,200 rows: 540 samples × 3 horizons × 1,260 roads.
- ID order exactly matches `sample_submission.csv`.
- No duplicate IDs, NaN, or infinity.
- Prediction range: 0 to 99.0485 km/h.
- Prediction correlation with V3 is 0.9956, but mean absolute difference is 1.126 km/h, so V5 is meaningfully different without looking structurally broken.

## Next experiment

V6 should focus on the proven low-rank signal: multi-rank/multi-alpha direct forecasting, road-local residual persistence, a third neural seed, and split-calibrated ensemble weights. It should retain the V5 backbone and avoid another expensive architecture search.
