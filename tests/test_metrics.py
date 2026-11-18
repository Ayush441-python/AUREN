import pandas as pd
import pytest
from engine.metrics import (
    concentration,
    portfolio_returns,
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


def test_drawdown_exact_30_percent_boundary():
    # Exactly -30.00% must NOT be evaluated as deeper than -30% (fixes #49)
    # Tested on boundary closes: 70.01 (-29.99%), 70.00 (-30.00%), 69.99 (-30.01%)
    w = pd.Series({"NVDA": 1.0})
    conc = concentration(w)

    # 1. 70.01 -> -29.99% drawdown -> score 50 (Medium), hits do not include drawdown
    prices_7001 = pd.DataFrame(
        {"NVDA": [99.0, 100.0] * 250 + [70.01]},
        index=pd.bdate_range("2024-01-02", periods=501),
    )
    r_7001 = portfolio_returns(prices_7001, w)
    mdd_7001 = max_drawdown(r_7001)
    score_7001, level_7001, hits_7001 = risk_score(
        conc, volatility(r_7001), mdd_7001, [], float(sector_exposure(w).max())
    )
    assert score_7001 == 50 and level_7001 == "Medium"
    assert not any("Worst past fall" in why for _, why in hits_7001)

    # 2. 70.00 -> exact -30.00% drawdown -> must remain score 50 (Medium), NOT High
    prices_7000 = pd.DataFrame(
        {"NVDA": [99.0, 100.0] * 250 + [70.00]},
        index=pd.bdate_range("2024-01-02", periods=501),
    )
    r_7000 = portfolio_returns(prices_7000, w)
    mdd_7000 = max_drawdown(r_7000)
    score_7000, level_7000, hits_7000 = risk_score(
        conc, volatility(r_7000), mdd_7000, [], float(sector_exposure(w).max())
    )
    assert score_7000 == 50 and level_7000 == "Medium"
    assert not any("Worst past fall" in why for _, why in hits_7000)

    # 3. 69.99 -> -30.01% drawdown -> deeper than -30%, adds 15 points -> score 65 (High)
    prices_6999 = pd.DataFrame(
        {"NVDA": [99.0, 100.0] * 250 + [69.99]},
        index=pd.bdate_range("2024-01-02", periods=501),
    )
    r_6999 = portfolio_returns(prices_6999, w)
    mdd_6999 = max_drawdown(r_6999)
    score_6999, level_6999, hits_6999 = risk_score(
        conc, volatility(r_6999), mdd_6999, [], float(sector_exposure(w).max())
    )
    assert score_6999 == 65 and level_6999 == "High"
    assert any("Worst past fall" in why for _, why in hits_6999)

