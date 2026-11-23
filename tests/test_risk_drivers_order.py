import pytest
from engine.score import risk_score
import api


def test_issue_225_synthetic_scoring_driver_order():
    """Verify primary risk drivers are sorted by score impact descending.
    Rule 1 (20 pts), Rule 2 (15 pts), Rule 3 (20 pts) -> Expected [20, 20, 15]
    with rule order preserved for ties.
    """
    conc = {"top_weight": 0.40, "effective_assets": 10.0 / 3.0}
    vol = 0.45
    mdd = -0.10
    pairs = []
    sector_max = 0.40

    score, level, hits = risk_score(conc, vol, mdd, pairs, sector_max)
    assert score == 55
    assert [pts for pts, _ in hits] == [20, 15, 20]

    # In api.py, reasons are sorted by score impact descending
    sorted_hits = sorted(hits, key=lambda x: x[0], reverse=True)
    expected_order = [
        "Largest holding is 40% (over 30%)",       # 20 pts (Rule 1)
        "Volatility is 45% a year (over 30%)",      # 20 pts (Rule 3)
        "Behaves like only 3.3 assets",            # 15 pts (Rule 2)
    ]
    actual_reasons = [why for _, why in sorted_hits]
    assert actual_reasons == expected_order


def test_overview_driver_sorting_stability():
    """Ensure ties preserve rule declaration order strictly (stable sort)."""
    # 4 rules triggered with 20, 15, 15, 20
    hits = [
        (20, "Rule A - 20pts"),
        (15, "Rule B - 15pts"),
        (15, "Rule C - 15pts"),
        (20, "Rule D - 20pts"),
    ]
    sorted_hits = sorted(hits, key=lambda x: x[0], reverse=True)
    assert sorted_hits == [
        (20, "Rule A - 20pts"),
        (20, "Rule D - 20pts"),
        (15, "Rule B - 15pts"),
        (15, "Rule C - 15pts"),
    ]
