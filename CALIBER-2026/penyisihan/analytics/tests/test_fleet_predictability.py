# analytics/tests/test_fleet_predictability.py
from analytics.fleet_predictability import same_asset_repeats, split_test

def rows():
    r = [{"eq_type": "PU", "component": "Seal", "occurred": f"2025-01-{i + 1:02d}", "plant": "A", "tag": f"P-{i}"} for i in range(10)]
    r.append({"eq_type": "CO", "component": "Bearing", "occurred": "2025-02-01", "plant": "A", "tag": "C-1"})
    r += [{"eq_type": "PU", "component": "Seal", "occurred": f"2025-08-{i + 1:02d}", "plant": "B", "tag": f"P-{i}"} for i in range(4)]
    r.append({"eq_type": "EM", "component": "Motor", "occurred": "2025-09-01", "plant": "B", "tag": "M-1"})
    return r

def test_counts_hits_of_prior_top_families():
    out = split_test(rows(), "2025-07-01", top_k=1)
    assert out["after_total"] == 5
    assert out["hits_topk"] == 4
    assert out["seen_before"] == 4
    assert out["families_total"] == 3
    assert abs(out["topk_family_share"] - 1 / 3) < 1e-9

def test_same_asset_repeats_counts_plant_tag_pairs():
    r = rows() + [{"eq_type": "PU", "component": "Seal", "occurred": "2025-10-01", "plant": "A", "tag": "P-0"}]
    assert same_asset_repeats(rows()) == 0
    assert same_asset_repeats(r) == 1
