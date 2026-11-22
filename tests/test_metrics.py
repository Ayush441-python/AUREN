import pandas as pd
import pytest
from engine.metrics import (
    concentration,
    volatility,
    max_drawdown,
    correlation,
    high_pairs,
    sector_exposure,
)
from engine.score import risk_score
from engine.stress import stress


def test_equal_weights_effective_assets():
    w = pd.Series([0.25] * 4, index=list("ABCD"))
    assert concentration(w)["effective_assets"] == pytest.approx(4)


def test_drawdown_known_case():
    pr = pd.Series([0.10, -0.50, 0.20])  # 1.10 -> 0.55 -> 0.66
    assert max_drawdown(pr) == pytest.approx(-0.5)


def test_no_swings_no_volatility():
    assert volatility(pd.Series([0.01] * 10)) == pytest.approx(0)


def test_perfectly_correlated_assets():
    prices = pd.DataFrame(
        {"A": [100, 101, 103, 102, 105], "B": [200, 202, 206, 204, 210]}
    )  # B = 2 x A
    corr = correlation(prices, ["A", "B"])
    assert corr.loc["A", "B"] == pytest.approx(1.0)


def test_high_pairs_finds_the_pair():
    prices = pd.DataFrame(
        {"A": [100, 101, 103, 102, 105], "B": [200, 202, 206, 204, 210]}
    )
    corr = correlation(prices, ["A", "B"])
    assert high_pairs(corr) == [("A", "B", 1.0)]


def test_safe_portfolio_scores_zero():
    conc = {"top_weight": 0.10, "effective_assets": 10}
    score, level, hits = risk_score(conc, 0.10, -0.05, [], 0.20)
    assert score == 0 and level == "Low" and hits == []


def test_worst_case_scores_100():
    conc = {"top_weight": 0.60, "effective_assets": 1.5}
    pairs = [("A", "B", 0.9), ("A", "C", 0.8)]
    score, level, hits = risk_score(conc, 0.50, -0.50, pairs, 0.80)
    assert score == 100 and level == "High"


def test_single_rule_adds_its_points():
    conc = {"top_weight": 0.40, "effective_assets": 10}
    score, _, hits = risk_score(conc, 0.10, -0.05, [], 0.20)
    assert score == 20 and len(hits) == 1


def test_sector_exposure_tech():
    # Day 9 test from playbook: NVDA 50% + MSFT 50% gives Big Tech = 100%
    w = pd.Series([0.5, 0.5], index=["NVDA", "MSFT"])
    exp = sector_exposure(w)
    assert exp.get("Big Tech", 0) == pytest.approx(1.0)


def test_stress_scenario():
    # Day 11 test from playbook: 50% NVDA + 50% GLD in "Big Tech falls 20%" = -10%
    w = pd.Series([0.5, 0.5], index=["NVDA", "GLD"])
    shocks = {"Big Tech": -0.20}
    assert stress(w, shocks) == pytest.approx(-0.10)


def test_exit_time_precision():
    """Test that ExitTime preserves exact precision while providing rounded display."""
    from engine.data import ExitTime
    
    # Test exact value preservation
    exact = 1.002
    et = ExitTime(exact)
    assert et.exact_value == exact
    assert et.rounded_value == 1.00  # Rounded to 2 decimal places
    assert et.display_value == "1.002"  # 3 decimal places for display
    
    # Test comparison operations
    et1 = ExitTime(1.002)
    et2 = ExitTime(0.998)
    assert et1 > et2
    assert et2 < et1
    assert et1 != et2
    
    # Test edge cases
    et_zero = ExitTime(0.0)
    assert et_zero.exact_value == 0.0
    assert et_zero.rounded_value == 0.0
    
    # Test string representation
    assert str(et1) == "1.002"
    assert repr(et1) == "ExitTime(exact_value=1.002, rounded=1.0)"


def test_find_slowest_ticker():
    """Test finding the slowest ticker using exact values."""
    from engine.data import ExitTime
    from engine.liquidity import find_slowest_ticker
    
    # Create test assets with different exit times
    assets = [
        {"ticker": "MSFT", "days_to_exit": ExitTime(0.998)},
        {"ticker": "AAPL", "days_to_exit": ExitTime(1.002)},
        {"ticker": "GOOGL", "days_to_exit": ExitTime(1.5)},
    ]
    
    # Find the slowest
    slowest = find_slowest_ticker(assets)
    assert slowest is not None
    assert slowest["ticker"] == "GOOGL"
    assert slowest["days_to_exit"].exact_value == 1.5
    
    # Test with tie (should return first encountered with max value)
    assets_tie = [
        {"ticker": "MSFT", "days_to_exit": ExitTime(1.002)},
        {"ticker": "AAPL", "days_to_exit": ExitTime(1.002)},
    ]
    slowest_tie = find_slowest_ticker(assets_tie)
    assert slowest_tie is not None
    assert slowest_tie["ticker"] == "MSFT"  # First one with max value


def test_max_days_to_exit():
    """Test calculating maximum days to exit using exact values."""
    from engine.data import ExitTime
    from engine.liquidity import max_days_to_exit
    
    # Create test assets
    assets = [
        {"ticker": "MSFT", "days_to_exit": ExitTime(0.998)},
        {"ticker": "AAPL", "days_to_exit": ExitTime(1.002)},
        {"ticker": "GOOGL", "days_to_exit": ExitTime(1.5)},
    ]
    
    # Calculate max days
    max_days = max_days_to_exit(assets)
    assert max_days == 1.5  # Should use exact value
    
    # Test with empty list
    assert max_days_to_exit([]) == 0.0
