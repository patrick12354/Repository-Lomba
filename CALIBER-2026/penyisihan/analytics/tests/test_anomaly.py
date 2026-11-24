
import numpy as np
from analytics.anomaly import detect

def series(n=240, shift_at=200):
    rng = np.random.default_rng(0)
    vib = 29 + rng.normal(0, 0.3, n); vib[shift_at:] += np.linspace(0, 40, n - shift_at)
    temp = 65 + rng.normal(0, 1, n)
    run = ["ON"] * (n - 10) + ["OFF"] * 10
    return {"VIB": vib.tolist(), "TEMP": temp.tolist()}, run, [f"2026-04-01T{h:02d}" for h in range(n)]

def test_flags_sustained_rise_before_shutdown():
    s, run, t = series()
    ev = detect(s, run, t, reference_hours=168, threshold=4.0, sustain=3)
    assert ev and ev[0]["start_index"] >= 200
    assert ev[0]["contributors"][0]["tag"] == "VIB"
    assert ev[0]["lead_hours"] > 0

def test_off_rows_are_never_scored():
    s, run, t = series(shift_at=235)
    assert all(e["start_index"] < 230 for e in detect(s, run, t, reference_hours=168))

def test_quiet_series_has_no_events():
    s, run, t = series(shift_at=240)
    assert detect(s, run, t, reference_hours=168) == []
