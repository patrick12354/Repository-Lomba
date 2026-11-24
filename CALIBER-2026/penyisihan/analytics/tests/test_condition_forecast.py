# analytics/tests/test_condition_forecast.py
from analytics.condition_forecast import actual_offset, crossing_window, exceed_events, linear_offset, score_windows

def test_crossing_window_high_limit_uses_p90_first():
    w = crossing_window(q10=[1, 2, 3, 4], q50=[2, 4, 6, 8], q90=[5, 7, 9, 11], limit=6, direction="high")
    assert w == {"earliest": 2, "likely": 3, "latest": None}

def test_crossing_window_low_limit_uses_p10_first():
    w = crossing_window(q10=[1.3, 1.0], q50=[1.5, 1.2], q90=[1.6, 1.5], limit=1.1, direction="low")
    assert w == {"earliest": 2, "likely": None, "latest": None}

def test_linear_and_actual_offsets():
    assert linear_offset([1, 2, 3, 4, 5, 6], limit=8, direction="high") == 2
    assert actual_offset([1, 2, 3, 9, 10], cutoff=1, limit=8, direction="high") == 2

def test_score_windows():
    cases = [{"actual": 3, "earliest": 2, "likely": 3, "latest": 5, "linear": 4},
             {"actual": 2, "earliest": 3, "likely": 4, "latest": None, "linear": None}]
    s = score_windows(cases, horizon=8)
    assert s["cases"] == 2 and s["coverage"] == 0.5 and s["mae_likely"] == 1.0 and s["linear_mae"] == 1.0 and s["linear_missed"] == 1

def test_exceed_events_needs_three_hours_and_running():
    actual = {"VIB": [1, 1, 9, 9, 9, 1, 9, 9]}
    lo = {"VIB": [0] * 8}; hi = {"VIB": [2] * 8}
    run = ["ON"] * 7 + ["OFF"]
    ev = exceed_events(actual, lo, hi, run, [f"t{i}" for i in range(8)], first_off=7)
    assert [(e["start_index"], e["end_index"], e["lead_hours"]) for e in ev] == [(2, 4, 5.0)]
