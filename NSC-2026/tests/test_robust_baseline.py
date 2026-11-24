import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from exp43_robust_baseline import assemble_long, fit_meta_predict, score_stack  # noqa: E402


class RobustBaselineTests(unittest.TestCase):
    def test_fit_meta_predict_preserves_perfect_members(self):
        tod = np.arange(0, 24, 0.5)
        target = 50 + 10 * np.sin(2 * np.pi * tod / 24)
        meta = pd.DataFrame({"tod": tod, "y": target,
                             "hbt": target, "cat": target, "ridge": target,
                             "enet": target, "ridge_e": target, "l2": target})
        valid = meta.drop(columns="y").copy()
        pred, _ = fit_meta_predict(meta, valid, ["hbt", "cat", "ridge", "enet", "ridge_e", "l2"])
        self.assertLess(np.abs(pred - target).max(), 1e-10)

    def test_assemble_long_aligns_members_and_rejects_duplicate_index(self):
        idx = pd.date_range("2023-01-01", periods=4, freq="30min")
        members = ["hbt", "cat", "ridge", "enet", "ridge_e"]
        base = {("P", 0, "base"): pd.DataFrame(1.0, index=idx, columns=members)}
        l2 = {("P", 0): pd.Series(1.0, index=idx)}
        y = pd.Series(1.0, index=idx)
        frame = assemble_long(base, l2, y)
        self.assertEqual(len(frame), 4)
        self.assertEqual(frame.groupby(["family", "fold", "datetime"]).size().max(), 1)
        self.assertTrue({*members, "l2", "y", "tod"}.issubset(frame.columns))

        duplicate = base.copy()
        duplicate[("P", 0, "base")] = pd.concat(
            [duplicate[("P", 0, "base")], duplicate[("P", 0, "base")].iloc[[0]]]
        )
        with self.assertRaisesRegex(ValueError, "duplicate"):
            assemble_long(duplicate, l2, y)

    def test_score_stack_is_exact_for_perfect_members(self):
        rows = []
        for family in ("P", "Q", "R"):
            for fold in range(2):
                idx = pd.date_range("2023-01-01", periods=48, freq="30min") + pd.Timedelta(days=fold)
                target = 50 + 10 * np.sin(2 * np.pi * (idx.hour + idx.minute / 60) / 24)
                for dt, value in zip(idx, target):
                    rows.append({"family": family, "fold": fold, "datetime": dt,
                                 "y": value, "tod": dt.hour + dt.minute / 60,
                                 "hbt": value, "cat": value, "ridge": value,
                                 "enet": value, "ridge_e": value, "l2": value})
        frame = pd.DataFrame(rows)
        scored, folds = score_stack(frame, ["hbt", "cat", "ridge", "enet", "ridge_e", "l2"])
        self.assertLess(folds.rmse.max(), 1e-10)
        self.assertLess(np.abs(scored.pred - scored.y).max(), 1e-10)


if __name__ == "__main__":
    unittest.main()
