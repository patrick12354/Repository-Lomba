from analytics.patterns import build_clusters

def test_clusters_are_deterministic_and_cover_every_record():
    rows = [{"id": f"L3-{i}", "plant": p, "eq_type": t, "component": c, "mechanism": m, "title": f"{c} failure",
             "actual_usd": 1000, "status": "RCA PROCESS"}
            for i, (p, t, c, m) in enumerate([("A", "PU", "Mechanical Seal", "Mechanical")] * 6 + [("B", "CO", "Journal Bearing", "High")] * 6)]
    a = build_clusters(rows, k_range=range(2, 4))
    b = build_clusters(rows, k_range=range(2, 4))
    assert a == b
    assert sorted(m for c in a for m in c["member_ids"]) == sorted(r["id"] for r in rows)
    seal = next(c for c in a if "L3-0" in c["member_ids"])
    assert set(seal["member_ids"]) == {f"L3-{i}" for i in range(6)}


def test_clusters_do_not_depend_on_row_order():
    rows = [{"id": f"L3-{i}", "plant": p, "eq_type": t, "component": c, "mechanism": m, "title": f"{c} failure",
             "actual_usd": 1000, "status": "RCA PROCESS"}
            for i, (p, t, c, m) in enumerate([("A", "PU", "Mechanical Seal", "Mechanical")] * 5 + [("B", "CO", "Journal Bearing", "High")] * 5 + [("C", "HE", "Tube Bundle", "Fouling")] * 5)]
    assert build_clusters(rows, k_range=range(2, 5)) == build_clusters(list(reversed(rows)), k_range=range(2, 5))
