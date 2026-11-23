from engine.score import risk_score


def test_risk_drivers_sorted_by_impact():
    # Synthetic inputs: top_weight 40% (20 pts), effective_assets 3.3 (15 pts), vol 45% (20 pts)
    score, level, hits = risk_score(
        {"top_weight": 0.4, "effective_assets": 10 / 3},
        0.45,
        -0.10,
        [],
        0.4,
    )
    raw_points = [pts for pts, _ in hits]
    assert raw_points == [20, 15, 20]

    # Sorted descending by score impact
    sorted_hits = sorted(hits, key=lambda h: h[0], reverse=True)
    sorted_points = [pts for pts, _ in sorted_hits]
    assert sorted_points == [20, 20, 15]
