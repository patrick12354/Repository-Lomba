# Datathon Task 1 — V1 Kaggle Run Analysis

## Status

**Technically successful and validation-positive.** Notebook ran in full mode on CUDA, completed training and refit, and produced a structurally valid submission. This does not guarantee leaderboard performance because test labels are unavailable.

## Run configuration

| Item | Value |
|---|---:|
| Fast mode | `False` |
| Device | CUDA |
| Batch size | 16 |
| Maximum validation epochs | 12 |
| Training stride | 2 |
| Training windows | 5,213 + 2,153 = 7,366 |
| Validation windows | 705 + 705 = 1,410 |
| Best GNN epoch | 9 |
| Full-refit epochs | 9 |

The roughly two-minute runtime is reasonable. Each validation epoch took about four seconds, the validation stage about 50 seconds, and the full refit about 36 seconds. The model is intentionally compact and uses sparse graph message passing.

## Validation result

| Horizon | AR MSE | GNN MSE | GNN blend weight | Blend MSE | Blend improvement vs AR |
|---|---:|---:|---:|---:|---:|
| h5 (+20 min) | 26.4689 | 24.7776 | 0.8608 | 24.7321 | 6.56% |
| h10 (+40 min) | 30.0597 | 28.1663 | 0.7766 | 27.9955 | 6.87% |
| h15 (+60 min) | 33.4695 | 31.2688 | 0.7384 | 30.9529 | 7.52% |
| **Mean** | **29.9994** | **28.0709** | — | **27.8935** | **7.02%** |

Interpretation:

- GNN beat AR at every horizon, so graph/history/text model learned useful corrections.
- The blend beat both individual models at every horizon, confirming partially complementary errors.
- The GNN weight decreases with horizon. AR becomes relatively more useful as uncertainty increases.
- Validation reached its best value at epoch 9. Epochs 10–12 did not improve, so blindly adding epochs is unlikely to help without another change.

## Submission audit

The CSV contains exactly 2,041,200 unique IDs, no missing predictions, and correct boundaries from `test_00000_h5_r0` to `test_00539_h15_r1259`.

| Horizon | Mean | Std | Min | Max | Exact zeros | Correlation with mean-last-3 |
|---|---:|---:|---:|---:|---:|---:|
| h5 | 52.7128 | 19.5392 | 0.0 | 101.4833 | 16,535 | 0.9899 |
| h10 | 52.7250 | 19.4167 | 0.0 | 101.4539 | 18,913 | 0.9866 |
| h15 | 52.7494 | 19.3464 | 0.0 | 101.2645 | 22,235 | 0.9844 |

The predictions are conservative:

- Mean absolute correction from mean-last-3 is only 1.68, 1.87, and 1.97 km/h for h5, h10, and h15.
- Mean absolute differences are 0.30 km/h between h5 and h10, 0.19 between h10 and h15, and 0.47 between h5 and h15.
- This is safe for MSE but suggests that horizon-specific dynamics may still be underfit.
- Exact zeros increase with horizon, primarily because final predictions are clipped at zero. This may be correct for closures/missing regimes, but it deserves an ablation.

## What remains unknown

The current run proves that the combined GNN is useful, but it does not isolate why. There is no validation ablation for:

- speed-only neural model;
- speed + road embedding;
- speed + graph;
- speed + graph + text.

Therefore, graph and text contributions cannot yet be claimed independently.

## Recommended V2 experiments, in priority order

### 1. Add ablations and rolling validation

Run at least two temporal folds and compare speed-only, `+graph`, and `+text`. This is more valuable than immediately increasing model size because it reveals which signal actually generalizes.

### 2. Average three random seeds

The run is cheap. Train seeds 42, 2026, and 3407, then average GNN predictions before blending with AR. Seed ensembling commonly reduces neural variance with minimal engineering risk.

### 3. Use every training window

Change `TRAIN_STRIDE=2` to `1`. This doubles highly overlapping data, so expected gains may be modest, but runtime should remain manageable. Keep early stopping; do not simply force more epochs.

### 4. Add a third low-rank spatial model

Fit PCA/low-rank Ridge on city-wide speed states and predict residuals from AR. A local experiment reduced average MSE from about 30.0 to 29.3. Its errors may complement the graph model, making a three-way validation blend useful.

### 5. Preserve graph direction

Instead of merging `A` and `A.T`, aggregate incoming and outgoing neighbors through separate linear layers. Traffic propagation is directional, and the supplied adjacency is asymmetric.

### 6. Strengthen road-specific text interaction

The current text vector is broadcast globally. Add a bilinear gate between text features and learned road embeddings, or parse `(event_type, location)` before road-level conditioning. Validate against the no-text ablation.

### 7. Model the zero regime explicitly

Add an auxiliary head predicting whether future speed is zero, alongside positive-speed regression. This could help with the large distribution shift in zero rate between train blocks.

### 8. Increase capacity only after the above

Try hidden size 64 and three graph blocks after ablations. More epochs alone are not the first choice because validation already plateaued after epoch 9.

## Practical recommendation

Keep the V1 submission as a safe entry. The highest-value next run is **stride 1 + three seeds + ablation logging**, followed by a validation-selected ensemble with AR and optionally PCA residuals.
