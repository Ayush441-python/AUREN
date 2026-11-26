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


def test_risk_score_ignores_low_correlation_pairs():
    conc = {"top_weight": 0.10, "effective_assets": 10}
    pairs = [(0.0,), (0.0,), ("A", "B", 0.7)]
    score, level, hits = risk_score(
        conc, vol=0.31, mdd=-0.05, pairs=pairs, sector_max=0.10
    )
    assert score == 20
    assert level == "Low"
    assert len(hits) == 1


def test_risk_score_counts_only_pairs_above_correlation_threshold():
    conc = {"top_weight": 0.10, "effective_assets": 10}
    # Only 1 pair > 0.7 -> should not trigger the >= 2 pairs rule
    one_strong = [("A", "B", 0.85), ("A", "C", 0.30), ("B", "C", 0.70)]
    score, level, hits = risk_score(conc, 0.10, -0.05, one_strong, 0.20)
    assert score == 0 and level == "Low" and hits == []

    # 2 pairs > 0.7 plus 1 weak pair -> should trigger and report exactly 2 pairs
    two_strong = [("A", "B", 0.85), ("A", "C", 0.75), ("B", "C", 0.20)]
    score, level, hits = risk_score(conc, 0.10, -0.05, two_strong, 0.20)
    assert score == 15
    assert level == "Low"
    assert hits == [(15, "2 pairs of assets move closely together")]


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
