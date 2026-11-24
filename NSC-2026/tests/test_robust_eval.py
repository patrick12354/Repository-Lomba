import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from robust_eval import (  # noqa: E402
    block_descriptors,
    feature_groups,
    make_stress_splits,
    paired_summary,
    passes_gate,
    score_blocks_against_reference,
    support_fraction,
)


class RobustEvalTests(unittest.TestCase):
    def test_private_similarity_score_ranks_closest_block_first(self):
        blocks = pd.DataFrame({"pressure": [1000.0, 1015.0, 1020.0],
                               "temp_range": [10.0, 20.0, 30.0],
                               "missing": [0.1, 0.2, 0.3],
                               "season": [10.0, 20.0, 30.0]})
        reference = pd.Series({"pressure": 1016.0, "temp_range": 19.0,
                               "missing": 0.2, "season": 22.0})
        scores = score_blocks_against_reference(blocks, reference)
        self.assertEqual(scores.idxmax(), 1)
        self.assertTrue(np.isfinite(scores).all())

    def test_block_descriptors_summarise_complete_time_blocks(self):
        index = pd.date_range("2023-01-01", periods=48 * 6, freq="30min")
        features = pd.DataFrame({"pressure": np.r_[np.full(144, 1000.0), np.full(144, 1010.0)],
                                 "T_rng48": np.r_[np.full(144, 10.0), np.full(144, 20.0)]},
                                index=index)
        result = block_descriptors(features, block_days=3)
        self.assertEqual(len(result), 2)
        self.assertEqual(result.iloc[0].pressure, 1000.0)
        self.assertEqual(result.iloc[1].temp_range, 20.0)
        self.assertEqual(result.iloc[0].n_rows, 144)

    def test_support_fraction_treats_missing_as_neutral_and_flags_extrapolation(self):
        train = pd.DataFrame({"stable": np.arange(100), "shifted": np.arange(100)})
        other = pd.DataFrame({"stable": [20.0, 50.0, np.nan], "shifted": [200.0, 300.0, np.nan]})
        result = support_fraction(train, other)
        self.assertEqual(result["stable"], 1.0)
        self.assertEqual(result["shifted"], 1.0 / 3.0)

    def test_feature_groups_are_target_free_and_remove_named_shift_blocks(self):
        columns = ["air_humidity", "T", "tod", "pressure", "pressure_c24h",
                   "pressure_s-2", "pressure_s2", "pressure_sd6h", "pressure_slope",
                   "pressure_a24h", "T_rng48", "air_temperature_qrng96", "co2"]
        coverage = pd.Series({c: 1.0 for c in columns})
        coverage["co2"] = 0.80
        groups = feature_groups(columns, coverage, bar=0.916)
        self.assertNotIn("air_humidity", set().union(*map(set, groups.values())))
        self.assertNotIn("pressure", groups["no_pressure"])
        self.assertNotIn("pressure_c24h", groups["no_pressure"])
        self.assertNotIn("pressure_s-2", groups["no_pressure"])
        self.assertNotIn("pressure_s2", groups["no_pressure"])
        self.assertIn("pressure_sd6h", groups["no_pressure"])
        self.assertIn("pressure_slope", groups["no_pressure"])
        self.assertIn("pressure_a24h", groups["no_pressure"])
        self.assertNotIn("T_rng48", groups["no_shifted_range"])
        self.assertNotIn("air_temperature_qrng96", groups["no_shifted_range"])
        self.assertNotIn("co2", groups["stable_core"])
        self.assertTrue({"T", "tod", "pressure_a24h"}.issubset(groups["stable_core"]))

    def test_stress_splits_use_past_only_and_respect_embargo(self):
        index = pd.date_range("2023-01-01", periods=48 * 40, freq="30min")
        blocks = pd.date_range("2023-01-20", periods=4, freq="4D")
        descriptors = pd.DataFrame(
            {"stress_score": [0.1, 0.9, 0.7, 0.5], "block_end": blocks + pd.Timedelta(days=3)},
            index=blocks,
        )
        splits = make_stress_splits(index, descriptors, n=3, embargo_hours=96, min_train_rows=100)
        self.assertEqual(len(splits), 3)
        for train_idx, valid_idx in splits:
            self.assertTrue(set(train_idx).isdisjoint(valid_idx))
            self.assertLessEqual(train_idx.max(), valid_idx.min() - pd.Timedelta(hours=96))
            self.assertLess(valid_idx.max(), valid_idx.min() + pd.Timedelta(days=3))

    def test_paired_summary_rejects_duplicate_fold_timestamps(self):
        base = pd.DataFrame({"family": ["P", "P"], "fold": [0, 0],
                             "datetime": pd.to_datetime(["2023-01-01", "2023-01-01"]),
                             "y": [1.0, 1.0], "pred": [1.2, 1.2]})
        with self.assertRaisesRegex(ValueError, "duplicate"):
            paired_summary(base, base)

    def test_adoption_gate_requires_all_families_fold_majority_and_stress_gain(self):
        summary = pd.DataFrame({"family": ["P", "P", "Q", "Q", "R", "R"],
                                "fold": [0, 1, 0, 1, 0, 1],
                                "delta": [-0.1, -0.2, -0.1, -0.01, -0.2, 0.05]})
        stress = pd.DataFrame({"mean_delta": [-0.1], "worst_delta": [-0.01]})
        passed, reasons = passes_gate(summary, stress)
        self.assertTrue(passed)
        self.assertEqual(reasons, [])
        stress.loc[0, "worst_delta"] = 0.01
        passed, reasons = passes_gate(summary, stress)
        self.assertFalse(passed)
        self.assertTrue(any("stress" in reason.lower() for reason in reasons))


if __name__ == "__main__":
    unittest.main()
