import pandas as pd
import pytest
from engine.metrics import (
    concentration,
    volatility,
    max_drawdown,
    correlation,
    high_pairs,
    sector_exposure,
    risk_contributions,
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


def test_risk_contributions_single_asset():
    # A single asset portfolio must contribute 100% of risk
    prices = pd.DataFrame({"A": [100.0, 102.0, 101.0, 104.0, 103.0]})
    w = pd.Series({"A": 1.0})
    rc = risk_contributions(prices, w)
    assert rc["A"] == pytest.approx(1.0)


def test_risk_contributions_euler_sum_to_one():
    # By Euler's theorem, sum of percentage risk contributions identically equals 1.0
    prices = pd.DataFrame(
        {
            "A": [100, 101, 103, 102, 105, 104, 108, 107],
            "B": [50, 48, 52, 49, 53, 51, 55, 54],
            "C": [10, 12, 11, 13, 12, 14, 13, 15],
        }
    )
    w = pd.Series({"A": 0.5, "B": 0.3, "C": 0.2})
    rc = risk_contributions(prices, w)
    assert sum(rc.values()) == pytest.approx(1.0, abs=1e-3)


def test_risk_contributions_volatile_asset_has_higher_risk_share():
    # Asset B is much more volatile than Asset A; with equal capital weight (50/50),
    # B must account for a significantly higher share of total portfolio volatility.
    prices = pd.DataFrame(
        {
            "A": [100.0, 100.5, 101.0, 100.8, 101.2, 101.5],  # Low volatility
            "B": [100.0, 105.0,  95.0, 110.0,  90.0, 115.0],  # High volatility
        }
    )
    w = pd.Series({"A": 0.5, "B": 0.5})
    rc = risk_contributions(prices, w)
    assert rc["B"] > rc["A"]
    assert rc["B"] > 0.50
    assert sum(rc.values()) == pytest.approx(1.0, abs=1e-3)

