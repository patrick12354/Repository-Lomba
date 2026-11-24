"""Checks for the session-16 additions. Runs under pytest or as a plain script.

Covers the two things that could silently go wrong: the robust-core column selector
consulting the target, and the shrinkage argument not actually reaching both layers.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "src")]
import final_pipeline as fp  # noqa: E402
from chu_block import chu_daily, day_key, dejitter_daily  # noqa: E402


def _grid():
    return fp.load_grid()


def test_stable_core_is_target_free():
    """Wiping the target must not change which columns the robust core selects."""
    g = _grid()
    F = fp.make_features(g)
    is_tr = (g.is_test == 0).values
    is_te = (g.is_test == 1).values
    a = fp.stable_core(F, is_tr, is_te)

    g2 = g.copy()
    g2[fp.TARGET] = np.nan
    b = fp.stable_core(fp.make_features(g2), is_tr, is_te)

    assert a == b, "robust-core selection depends on the target"
    assert fp.TARGET not in a
    assert 0 < len(a) < F.shape[1]


def test_stable_core_excludes_the_two_named_blocks():
    g = _grid()
    F = fp.make_features(g)
    core = set(fp.stable_core(F, (g.is_test == 0).values, (g.is_test == 1).values))
    for c in ("pressure", "pressure_c24h", "pressure_s-4", "pressure_s4"):
        assert c not in core, c
    for c in ("T_rng18", "T_rng48", "T_rng96", "esT_ratio_daily"):
        assert c not in core, c
    # bounded anomalies and time of day are kept, so information is not removed wholesale
    for c in ("pressure_a24h", "tod", "T"):
        assert c in core, c


def test_base_model_maps_the_robust_member_to_hbt():
    assert fp.base_model(fp.ROBUST) == "hbt"
    for m in fp.MODELS_L2:
        assert fp.base_model(m) == m


def test_blend_shrink_reaches_the_band_layer():
    """tod_blend_weights used to hard-code BLEND_SHRINK; at 0.0 no band weight may sit
    on the uniform floor unless NNLS actually put it there."""
    rng = np.random.default_rng(0)
    n = 3000
    tod = rng.uniform(0, 24, n)
    y = 60 + 10 * np.sin(2 * np.pi * tod / 24) + rng.normal(0, 2, n)
    O = pd.DataFrame({"tod": tod, "y": y})
    models = ["good", "useless"]
    O["good"] = y + rng.normal(0, 1, n)
    O["useless"] = rng.normal(60, 20, n)
    w = np.array([1.0, 0.0])

    _, W025 = fp.tod_blend_weights(O, w, models=models, blend_shrink=0.25)
    _, W000 = fp.tod_blend_weights(O, w, models=models, blend_shrink=0.0)
    floor025 = min(v[1] for v in W025.values())
    floor000 = min(v[1] for v in W000.values())
    # at 0.25 the useless member is held up by the uniform floor; at 0.0 it keeps only
    # whatever NNLS actually gave it, which for pure noise is two orders of magnitude less
    assert floor025 > 0.05, floor025
    assert floor000 < floor025 / 50, (floor000, floor025)


def test_day_key_anchors_at_22h_and_daily_columns_are_constant_within_it():
    g = _grid()
    c = fp.clean_exog(g)
    k = day_key(c.index)
    assert (k.hour == 0).all()
    # the daily block varies far less inside a 22h-day than inside a calendar day
    inside = c.groupby(k)[fp.DAILY].std().mean().mean()
    calendar = c.groupby(c.index.normalize())[fp.DAILY].std().mean().mean()
    assert inside < calendar / 2, (inside, calendar)


def test_dejitter_is_idempotent_and_removes_within_day_variation():
    g = _grid()
    c = fp.clean_exog(g)
    d1 = dejitter_daily(c, fp.DAILY)
    d2 = dejitter_daily(d1, fp.DAILY)
    for col in fp.DAILY:
        assert np.allclose(d1[col].values, d2[col].values, equal_nan=True), col
    k = day_key(d1.index)
    assert float(d1.groupby(k)[list(fp.DAILY)].std().max().max()) < 1e-9


def test_chu_inversion_recovers_the_daily_minimum():
    g = _grid()
    c = fp.clean_exog(g)
    b = chu_daily(c)
    obs = c.groupby(day_key(c.index)).agg(
        tmin=("air_temperature", "min"), n=("air_temperature", "size")
    )
    j = b.join(obs)
    j = j[j.n >= 46]
    assert len(j) > 60
    assert np.corrcoef(j.Tmin, j.tmin)[0, 1] > 0.97
    assert (j.Tmin - j.tmin).std() < 0.7


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    bad = 0
    for fn in fns:
        try:
            fn()
            print("PASS %s" % fn.__name__)
        except AssertionError as exc:
            bad += 1
            print("FAIL %s: %s" % (fn.__name__, exc))
    print("\n%d passed, %d failed" % (len(fns) - bad, bad))
    raise SystemExit(1 if bad else 0)
