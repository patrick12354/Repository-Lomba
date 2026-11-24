# V3 Public Leaderboard Gap Analysis

## Observed result

- Local balanced validation: 26.2185.
- Local inferred-test-weighted validation: 27.1327.
- Kaggle public leaderboard: **38.639**.

Submission format, IDs, horizon order, tensor reshape, and MSE formula were re-audited and found correct. The gap is caused primarily by an unrepresentative validation period, not a broken submission.

## Root cause

V3 validates only the last 705 forecast origins of each train block, approximately the last two days. Those days are unusually easy.

Mean-last-3 MSE:

| Evaluation population | MSE |
|---|---:|
| Tail validation, balanced 50/50 | 34.3788 |
| Tail validation, test-like 68.9/31.1 | 35.6338 |
| All valid train origins, natural-weighted | 49.1895 |

V3 improves the test-like tail baseline by 23.86%. Applying the same relative improvement to the full-period baseline predicts 37.45, close to public 38.639. This strongly explains the gap without requiring a code bug.

Daily mean-last-3 MSE is highly nonstationary:

- m1 mean 55.30, standard deviation 11.29, range 35.57–72.13;
- m2 mean 35.66, standard deviation 4.59, range 27.62–41.32;
- the selected tail days sit near the easiest end in both blocks.

## Corrected validation design

Use 5-fold purged day-block cross-validation:

1. group forecast origins by full day (`t // 360`);
2. hold out contiguous day groups from both m1 and m2;
3. purge at least 15 timesteps around each validation boundary;
4. fit TF-IDF/SVD, global scaler, regime context, and model only on each fold's training rows;
5. save out-of-fold predictions for every held-out day;
6. aggregate naturally across all rows, which already approximates the 69/31 test composition;
7. learn ensemble weights from OOF predictions, not the same single tail used for architecture selection;
8. keep one final untouched fold or use nested selection for an honest final estimate.

A lighter development protocol can use three representative folds, but final ranking should use all five.

## Route toward stronger scores

Reaching public MSE near 20 requires roughly halving current error and is not a small tuning task. Priorities:

1. Add inferred cyclical time-of-day. A quick 5-fold day-blocked model inferred phase with median error about 34 minutes, showing useful signal exists even though test timestamps are absent.
2. Replace whole-document TF-IDF compression with clause-level event encoding and road-conditioned attention.
3. Replace flattened per-road MLP + late graph aggregation with a compact diffusion temporal graph network or Graph WaveNet using physical and adaptive adjacency.
4. Train the model jointly on speed residual, future network-level state, and soft phase; retain Global FiLM as conditioning.
5. Use OOF seed/model ensembles only after all candidates are evaluated on the corrected folds.

Nearest-text/history lookup is not a promising shortcut: nearest text cosine median is about 0.75, but the best history among ten text neighbors has median RMSE 8.29 km/h and no near-exact matches.
