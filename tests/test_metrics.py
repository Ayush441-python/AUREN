import pandas as pd
import pytest
from engine.metrics import (
    concentration,
    volatility,
    max_drawdown,
    correlation,
    high_pairs,
    sector_exposure,
    group_exposure,
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


def test_group_exposure_tech():
    # Thematic group: NVDA 50% + MSFT 50% gives Big Tech = 100%
    w = pd.Series([0.5, 0.5], index=["NVDA", "MSFT"])
    exp = group_exposure(w)
    assert exp.get("Big Tech", 0) == pytest.approx(1.0)


def test_sector_exposure_industry_semiconductors():
    # Economic sector: NVDA 50% + AMD 50% gives 100% Semiconductors (fixes #67)
    w = pd.Series([0.5, 0.5], index=["NVDA", "AMD"])
    exp = sector_exposure(w)
    assert exp.get("Semiconductors", 0) == pytest.approx(1.0)


def test_sector_exposure_diversified_tech():
    # Economic sectors: NVDA 30% + MSFT 25% + AAPL 20% + AMZN 25% are in separate industries
    w = pd.Series([0.30, 0.25, 0.20, 0.25], index=["NVDA", "MSFT", "AAPL", "AMZN"])
    exp = sector_exposure(w)
    assert exp.get("Semiconductors", 0) == pytest.approx(0.30)
    assert exp.get("Software", 0) == pytest.approx(0.25)
    assert exp.get("Consumer Technology", 0) == pytest.approx(0.20)
    assert exp.get("E-Commerce & Cloud", 0) == pytest.approx(0.25)
    assert float(exp.max()) <= 0.50  # Must not trigger single sector penalty


def test_stress_scenario():
    # Day 11 test from playbook: 50% NVDA + 50% GLD in "Big Tech falls 20%" = -10%
    w = pd.Series([0.5, 0.5], index=["NVDA", "GLD"])
    shocks = {"Big Tech": -0.20}
    assert stress(w, shocks) == pytest.approx(-0.10)
