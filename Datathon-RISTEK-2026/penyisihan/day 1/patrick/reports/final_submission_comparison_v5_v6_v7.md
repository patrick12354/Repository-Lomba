# Final Submission Comparison — V5 vs V6 vs V7

## Recommendation

Submit **V7 `submission_v7.csv`** as the primary entry. Keep **V5** as the backup/diversity entry. Do not prioritize V6 because its final prediction is almost identical to V5 and its comparable diagnostic is slightly worse.

The local numbers below are not all directly comparable because each notebook uses a different validation protocol. Validation strength must be considered together with MSE.

## Evaluation comparison

| Version | Main local result | Validation design | Evidence strength | Interpretation |
|---|---:|---|---|---|
| V5 | test-weighted diagnostic **31.0305** | One randomized purged-day holdout; architecture, early stopping, and simplex weights use the same holdout | Lowest | Best-looking number, but most optimistic |
| V6 | primary cross-fitted weighted **31.2587**; robust diagnostic 31.1688 | Same randomized holdout; ensemble weights calibrated across two halves, but model/candidate selection still sees the full holdout | Medium | More honest weights, but final output does not improve materially over V5 |
| V7 | development OOF **31.1223**; locked audit **32.0414** | Three grouped-day development folds plus a fully locked fourth audit fold; rank, architecture, epoch, and beta frozen before audit | Highest | Strongest evidence of real generalization |

V7 improves its DirectLR anchor from 31.6777 to 31.1223 on development OOF and from 32.5591 to 32.0414 on locked audit. The residual correction wins on all 28 development validation days.

## Method comparison

| Version | Low-rank component | Neural component | Text/global context | Ensemble/control |
|---|---|---|---|---|
| V5 | Single direct PCA latent model, rank 64, alpha 100 | Absolute-speed Global FiLM + EMA + soft-MoE GNN, two seeds | TF-IDF/SVD text and regime context | Same-fold non-negative blend |
| V6 | Rank 48/64/80 sweep, alpha 30/100/300, soft local residual | Same absolute-speed GNN as V5, two seeds | Same as V5 | Split-calibrated robust weights |
| V7 | Fold-local DirectLR rank 48, alpha 30, soft local residual | Zero-initialized compact directed GNN predicts anchor residual, one seed | No text, FiLM, EMA, or MoE | Cross-fitted horizon damping plus locked acceptance gate |

## What V7 proved

- Rank 48 beats rank 64 on every reported fold.
- Soft local residual improves pure DirectLR on every fold.
- Directed graph residual model beats temporal-only and road-embedding variants on the development selection fold.
- Raw residual target narrowly beats normalized residual target: 31.7767 versus 31.7975.
- Cross-fitted damping decreases sensibly by horizon: 0.880, 0.795, 0.648.
- Development horizon gains are about 1.081 MSE at h5, 0.435 at h10, and 0.151 at h15.
- Locked audit gain is 0.518 MSE and development daily win rate is 100%.

## Submission similarity and diversity

| Pair | Correlation | MAE difference | Delta RMSE |
|---|---:|---:|---:|
| V5 vs V6 | 0.999669 | 0.3338 km/h | 0.4995 km/h |
| V5 vs V7 | 0.997893 | 0.7438 km/h | 1.2651 km/h |
| V6 vs V7 | 0.997762 | 0.7592 km/h | 1.3040 km/h |
| V7 anchor vs V7 hybrid | 0.998756 | 0.5584 km/h | 0.9709 km/h |

V5 and V6 are effectively the same submission family. V7 is meaningfully different while still highly correlated enough to look structurally safe.

## Final submission order

1. **Primary:** `submissions/datathon_task1_v7_directlr_residual_gnn.csv`
2. **Backup/second final selection:** `submissions/datathon_task1_v5_rapid_hybrid.csv`
3. **Archive only:** `submissions/datathon_task1_v6_stable_multirank.csv`

If Kaggle permits several submissions, submit V7 and V5 separately. Do not blend them without a common locked validation because the current local protocols are different. If final selection permits two entries, choose V7 plus whichever of V5/V6 obtains the better actual public score; before leaderboard evidence, V5 is the preferred backup.

## Stop decision

Do not build V8 before submitting. V7 has passed the intended locked gate, runtime is only about seven minutes, and further tuning would reuse the audit signal and weaken its value as an untouched estimate. The next useful information is the actual leaderboard score.
