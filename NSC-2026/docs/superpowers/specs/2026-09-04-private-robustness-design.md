# Private-Leaderboard Robustness Design

## Objective

Improve the NSC air-humidity model for robust private-leaderboard performance without
optimising against public-leaderboard noise. A new submission is produced only if it beats
the strongest existing baseline under ordinary time-blocked validation and under a separate
out-of-distribution stress evaluation.

The frozen references are:

- `v12_harmbias`: the best-validated five-member stack before the L2 addition, nested RMSE
  4.7593.
- `v16_l2member`: `v12_harmbias` plus a plain-L2 LightGBM member, nested RMSE 4.7464 and the
  current conservative candidate.
- `v11_seed5`: the last submission with a known private result, public 3.00589 and private
  approximately 3.6.

## Problem Diagnosis

The present bottleneck is not ordinary model capacity. The existing work already tested
feature expansion, target reparameterisation, alternative learner families, residual models,
self-training, blend subset searches, seed averaging, and several post-model corrections.
The remaining failure is transfer: the private period contains substantially more
out-of-support pressure and temperature-range features than the public period, while the
standard rolling-origin folds remain inside the warmer training regime.

The existing low-support experiment removed the suspect columns from every member. It greatly
improved the linear members but barely improved the final blend because the stack is dominated
by trees. It did not test whether a deliberately stable feature subset is useful as an
additional, differently biased member. It also did not test training-time feature-group
perturbation or temporal-subset ensembles.

## Proposed Evaluation Architecture

### Frozen baseline reproduction

First reproduce the existing `v12` and `v16` predictions and validation results. Verify row
counts, datetime alignment, feature count, deterministic hashes, fold membership, and absence
of duplicate timestamps in pooled analyses. Existing artifacts may accelerate checks, but any
final candidate must be reproducible from the three official CSV files alone.

### Standard validation

Retain fold families P, Q, and R and nested leave-one-fold-out estimation of blend weights and
the harmonic correction. Report per-family mean, worst fold, fold wins, and a paired bootstrap
interval. Never pool overlapping fold rows as independent timestamps.

### OOD stress validation

Add a diagnostic evaluation made only from training targets:

1. Compute block-level descriptors for pressure level, temperature range, feature support,
   missingness, and season position.
2. Identify complete validation blocks that most resemble the private test feature regime.
3. Keep validation blocks temporally intact and apply an embargo at rolling-feature boundaries.
4. Fit every preprocessing statistic and model only on the training side of each split.
5. Report stress mean, worst block, bias, and error on rows outside the training 1--99 percent
   feature bands.

The private test features may describe the direction of stress, but private labels are never
used or inferred. Public leaderboard scores are excluded from model selection.

## Candidate Model Families

### 1. Robust-core member

Train an additional model on a stable subset that removes the shifted pressure-level block,
temperature-range features with the largest public-to-private separability jump, and any
feature failing the predefined support threshold. Keep bounded anomalies and time-of-day
features so useful information is not removed wholesale. Add this model to the existing stack
and let nested blending determine whether its different failure mode is useful.

### 2. Feature-group bagging

Train a small ensemble of LightGBM models on predefined sensor groups: full accepted features,
no pressure levels, no shifted temperature-range block, and stable core only. Average or blend
these predictions using weights learned inside each outer fold. Groups are defined from
target-free support diagnostics before scoring, preventing target-guided feature selection.

### 3. Temporal bagging

Train otherwise identical models on several historical windows: all available history, a
minimum-size recent window, and a model excluding the earliest regime. Combine them using
nested weights. This tests concept-drift robustness without recency weighting individual rows,
which previously failed. The experiment is rejected if reduced sample size dominates or if a
window helps only one fold family.

These candidates are screened in that order. The robust-core member is cheapest and most
directly targets the diagnosed private failure. Temporal bagging is last because it sacrifices
training data.

## Adoption Gate

A candidate may replace `v16` only when all conditions hold:

- negative mean delta in each of P, Q, and R;
- a majority of folds won overall and no catastrophic family reversal;
- improved or equal OOD stress mean and worst-block RMSE;
- paired uncertainty evidence that is stronger than a best-of-many search artifact;
- no new test-support, occupancy, or dispersion warning;
- no target leakage, overlapping-timestamp memorisation, external data, leaderboard probing,
  or hand-tuned row-level post-processing;
- deterministic reproduction from the official files.

If no candidate clears every gate, `v16_l2member` remains the recommendation. A negative result
is considered successful completion because it prevents a less robust submission from
replacing the current baseline.

## Code and Artifact Boundaries

- Keep `final_pipeline.py` as the self-contained production entry point.
- Put the new reusable stress-fold and scoring helpers in one focused module under `src/`.
- Put each candidate experiment in a separate script so results remain attributable.
- Cache expensive per-fold member predictions under `outputs/`, keyed by configuration and
  fold identity.
- Append measured results and decisions to `progress.md` after baseline reproduction, after
  stress-harness validation, and after each candidate family.
- Generate `outputs/submissions/v17_robust.csv` only if the adoption gate passes.

## Failure Handling

Stop an experiment when fold membership overlaps incorrectly, a cache key does not match the
current feature configuration, a validation block has insufficient training history, or a
candidate changes more than one hypothesis at once. Preserve failed results in the log with
their exact configuration and do not stack further changes on an unconfirmed result.

## Verification

Verification includes baseline reproduction, unit checks for split isolation and feature-group
selection, a deliberately failing overlap test, full P/Q/R and stress comparisons, submission
schema checks, target-wipe feature invariance, deterministic reruns, and a final comparison
against both `v12` and `v16`.

