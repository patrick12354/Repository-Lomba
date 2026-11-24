# Private-Leaderboard Robustness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Evaluate and, only if justified, integrate a feature-stable ensemble that improves private-regime robustness over `v16_l2member`.

**Architecture:** A reusable evaluation module defines leakage-safe folds, target-free feature groups, nested blending, and adoption gates. Separate experiment scripts reproduce the baseline, add a robust-core member, test feature-group bagging, and test temporal bagging. `final_pipeline.py` changes only after a candidate passes both P/Q/R validation and OOD stress validation.

**Tech Stack:** Python 3.11, pandas, NumPy, LightGBM, CatBoost, scikit-learn, SciPy NNLS, pytest.

---

## File structure

- Create `src/robust_eval.py`: split isolation, block descriptors, stress-fold selection,
  feature-group selection, nested scoring, and adoption-gate helpers.
- Create `tests/test_robust_eval.py`: deterministic unit tests for all target-free selectors,
  timestamp isolation, embargoes, and gates.
- Create `src/exp43_robust_baseline.py`: reproduce `v12`/`v16` and materialise one canonical
  fold cache for subsequent experiments.
- Create `src/exp44_robust_core.py`: evaluate a stable-feature LightGBM as a seventh member.
- Create `src/exp45_feature_bag.py`: evaluate predefined feature-group LightGBM members.
- Create `src/exp46_temporal_bag.py`: evaluate fixed historical-window members.
- Modify `final_pipeline.py`: integrate only the winning configuration, if one passes.
- Modify `progress.md`: append checkpoints and final measured results.

### Task 1: Evaluation primitives and leakage tests

**Files:**
- Create: `src/robust_eval.py`
- Create: `tests/test_robust_eval.py`

- [ ] **Step 1: Write failing tests for stable feature groups**

```python
def test_feature_groups_are_target_free_and_nested():
    groups = feature_groups(COLUMNS, coverage=COVERAGE, bar=0.916)
    assert "air_humidity" not in set().union(*map(set, groups.values()))
    assert set(groups["stable_core"]) < set(groups["full"])
    assert not any(c in groups["no_pressure"] for c in PRESSURE_LEVELS)
```

- [ ] **Step 2: Write failing tests for temporal isolation and embargo**

```python
def test_stress_splits_have_no_overlap_and_respect_embargo():
    for train_idx, valid_idx in make_stress_splits(INDEX, DESCRIPTORS, n=3, embargo_hours=96):
        assert set(train_idx).isdisjoint(valid_idx)
        assert max(train_idx) <= min(valid_idx) - pd.Timedelta(hours=96)
```

- [ ] **Step 3: Run tests and verify failure**

Run: `.venv\Scripts\python.exe -m pytest tests/test_robust_eval.py -q`

Expected: collection fails because `src.robust_eval` does not exist.

- [ ] **Step 4: Implement deterministic selectors and gates**

Implement these public functions with typed docstrings:

```python
def support_fraction(train: pd.DataFrame, other: pd.DataFrame) -> pd.Series:
    lo, hi = train.quantile(0.01), train.quantile(0.99)
    return (((other >= lo) & (other <= hi)) | other.isna()).mean()

def feature_groups(columns: list[str], coverage: pd.Series,
                   bar: float = 0.916) -> dict[str, list[str]]:
    full = [c for c in columns if c != "air_humidity"]
    pressure_levels = [c for c in full if c == "pressure" or c.startswith("pressure_c")
                       or c.startswith("pressure_s")]
    shifted_range = [c for c in full if c.startswith("T_rng")
                     or "air_temperature_qrng" in c or c == "esT_ratio_daily"]
    no_pressure = [c for c in full if c not in pressure_levels]
    no_range = [c for c in full if c not in shifted_range]
    stable = [c for c in full if float(coverage.get(c, 0.0)) >= bar
              and c not in pressure_levels and c not in shifted_range]
    return {"full": full, "no_pressure": no_pressure,
            "no_shifted_range": no_range, "stable_core": stable}

def block_descriptors(features: pd.DataFrame, block_days: int = 3) -> pd.DataFrame:
    key = features.index.floor(f"{block_days}D")
    out = pd.DataFrame(index=pd.Index(sorted(key.unique()), name="block"))
    grouped = features.groupby(key)
    out["pressure"] = grouped["pressure"].median()
    out["temp_range"] = grouped["T_rng48"].median()
    out["missing"] = grouped.apply(lambda d: d.isna().mean().mean(), include_groups=False)
    out["season"] = (out.index - features.index.min()).total_seconds() / 86400.0
    return out

def make_stress_splits(index: pd.DatetimeIndex, descriptors: pd.DataFrame,
                       n: int = 3, embargo_hours: int = 96):
    chosen = descriptors.sort_values("stress_score", ascending=False).head(n)
    splits = []
    width = pd.Timedelta(days=3)
    embargo = pd.Timedelta(hours=embargo_hours)
    for start in chosen.index.sort_values():
        valid = index[(index >= start) & (index < start + width)]
        train = index[index <= start - embargo]
        if len(valid) and len(train):
            splits.append((train, valid))
    return splits

def paired_summary(base: pd.DataFrame, candidate: pd.DataFrame) -> pd.DataFrame:
    keys = ["family", "fold", "datetime", "y"]
    merged = base[keys + ["pred"]].merge(
        candidate[keys + ["pred"]], on=keys, suffixes=("_base", "_candidate"))
    merged["se_base"] = (merged.pred_base - merged.y) ** 2
    merged["se_candidate"] = (merged.pred_candidate - merged.y) ** 2
    return merged.groupby(["family", "fold"]).agg(
        base=("se_base", lambda x: float(np.sqrt(x.mean()))),
        candidate=("se_candidate", lambda x: float(np.sqrt(x.mean()))),
    ).reset_index().assign(delta=lambda d: d.candidate - d.base)

def passes_gate(summary: pd.DataFrame, stress: pd.DataFrame):
    reasons = []
    for family, rows in summary.groupby("family"):
        if rows.delta.mean() >= 0:
            reasons.append(f"family {family} mean did not improve")
    if (summary.delta < 0).sum() <= len(summary) / 2:
        reasons.append("no overall fold majority")
    if stress.mean_delta.iloc[0] > 0 or stress.worst_delta.iloc[0] > 0:
        reasons.append("OOD stress score regressed")
    return not reasons, reasons
```

Feature groups are fixed by names and target-free coverage: `full`, `no_pressure`,
`no_shifted_range`, and `stable_core`. Stress blocks are ranked by target-free distance to
private descriptors, but validation labels always come exclusively from `train.csv`.

- [ ] **Step 5: Run tests**

Run: `.venv\Scripts\python.exe -m pytest tests/test_robust_eval.py -q`

Expected: all tests pass.

### Task 2: Frozen baseline reproduction

**Files:**
- Create: `src/exp43_robust_baseline.py`
- Modify: `progress.md`

- [ ] **Step 1: Write a baseline audit test**

Assert 118 features, 2933 train rows, 734 test rows, nine P folds, and matching `v16` output
schema. Assert no duplicate `(family, fold, timestamp)` rows in the canonical cache.

- [ ] **Step 2: Implement baseline runner**

Import feature construction and model definitions from `final_pipeline.py`; reproduce nested
five- and six-member scores using the exact P/Q/R definitions from `src/an_l2member.py`.
Write `outputs/robust_baseline.pkl` and `outputs/robust_baseline.json` with configuration hashes.

- [ ] **Step 3: Run baseline reproduction**

Run: `.venv\Scripts\python.exe src/exp43_robust_baseline.py`

Expected: five-member nested mean approximately 4.7593, six-member mean approximately 4.7464,
with the six-member delta negative in P, Q, and R.

- [ ] **Step 4: Record checkpoint**

Append the exact reproduced means, fold counts, cache hash, and any discrepancy to Session 15
in `progress.md`.

### Task 3: Robust-core member

**Files:**
- Create: `src/exp44_robust_core.py`
- Modify: `progress.md`

- [ ] **Step 1: Add a failing configuration test**

Verify the robust-core columns are determined without `air_humidity`, exclude pressure levels
and shifted range columns, retain `tod` and bounded anomalies, and are identical when the target
is wiped.

- [ ] **Step 2: Fit the candidate in every P/Q/R fold**

Use the exact L2 and Huber LightGBM settings already present in `final_pipeline.py`. Cache each
fold immediately in `outputs/robust_core_oof.pkl` with feature-list and fold hashes.

- [ ] **Step 3: Score as an additional member**

Run nested LOO global weights, time-of-day weights, and harmonic correction for baseline versus
baseline plus robust-core. Do not replace the original members.

- [ ] **Step 4: Score OOD stress splits**

Compare mean, worst block, bias, and out-of-support-row RMSE using identical preprocessing.

- [ ] **Step 5: Record the verdict**

Append exact P/Q/R deltas, fold wins, bootstrap interval, stress metrics, and gate failures or
success to `progress.md`.

### Task 4: Feature-group bagging

**Files:**
- Create: `src/exp45_feature_bag.py`
- Modify: `progress.md`

- [ ] **Step 1: Define the fixed group ensemble**

Fit one candidate on each target-free group: `full`, `no_pressure`, `no_shifted_range`, and
`stable_core`. Use the same learner settings so only the feature view changes.

- [ ] **Step 2: Fit and checkpoint P/Q/R predictions**

Run: `.venv\Scripts\python.exe src/exp45_feature_bag.py --fit`

Expected: `outputs/feature_bag_oof.pkl` contains every family/fold/group key exactly once.

- [ ] **Step 3: Compare aggregation schemes without in-sample selection**

Evaluate equal averaging and nested NNLS learned on other folds. The group definitions remain
fixed; no best-subset scan is allowed.

- [ ] **Step 4: Run stress evaluation and gate**

Reject the family if it improves normal CV but worsens stress mean or worst block.

- [ ] **Step 5: Record the verdict**

Append full metrics and the selected/rejected aggregation scheme to `progress.md`.

### Task 5: Temporal bagging

**Files:**
- Create: `src/exp46_temporal_bag.py`
- Modify: `progress.md`

- [ ] **Step 1: Define windows before scoring**

For every outer fold use: all history, the latest 45 days when available, and history excluding
the earliest 20 percent. Enforce at least 1,000 labelled rows per member.

- [ ] **Step 2: Fit and checkpoint predictions**

Run: `.venv\Scripts\python.exe src/exp46_temporal_bag.py --fit`

Expected: each window produces predictions for every eligible fold; ineligible windows are
explicitly logged rather than silently replaced.

- [ ] **Step 3: Score fixed equal and nested aggregation**

Compare against `v16` on P/Q/R and stress splits. Do not tune window lengths after seeing target
scores.

- [ ] **Step 4: Record the verdict**

Append metrics and any sample-starvation failure to `progress.md`.

### Task 6: Final integration and verification

**Files:**
- Modify: `final_pipeline.py` only if a candidate passes
- Modify: `progress.md`
- Create: `outputs/submissions/v17_robust.csv` only if a candidate passes

- [ ] **Step 1: Select strictly by the written gate**

Run all candidates through `passes_gate`; preserve `v16` if none passes.

- [ ] **Step 2: Add the winning deterministic path**

Expose one explicit CLI flag in `final_pipeline.py`, keep falsified flags off, and ensure the
new feature-group definitions depend only on official exogenous columns.

- [ ] **Step 3: Run regression and self-tests**

Run:

```powershell
.venv\Scripts\python.exe -m pytest tests -q
.venv\Scripts\python.exe final_pipeline.py --selftest --tod-blend --harm-bias --l2-member
```

Expected: tests pass; baseline output remains deterministic and schema-valid.

- [ ] **Step 4: Verify a passing candidate twice**

Generate the candidate twice, compare SHA-256 hashes, check 734 rows, exact datetime equality,
no missing values, no duplicates, finite values, and physical range [5, 100].

- [ ] **Step 5: Finish Session 15**

Record the complete error analysis, what worked, what failed, the final recommendation, exact
reproduction command, and why the choice is expected to be more robust on private data.
