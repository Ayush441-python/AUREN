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


def test_high_pairs_strict_boundary_700():
    # Exactly r=0.700 must NOT qualify under strict > 0.70 semantics
    c = pd.DataFrame(
        [[1.0, 0.700, 0.700], [0.700, 1.0, 0.0], [0.700, 0.0, 1.0]],
        index=list("ABC"),
        columns=list("ABC"),
    )
    pairs = high_pairs(c)
    assert pairs == []
    score, level, hits = risk_score(
        {"top_weight": 0.2, "effective_assets": 5}, 0.1, -0.05, pairs, 0.2
    )
    assert score == 0
    assert hits == []


def test_high_pairs_retains_precision_704():
    # r=0.704 strictly qualifies (> 0.70) and must retain full precision
    # so that the 15 risk points added are auditable from the returned pair data
    c = pd.DataFrame(
        [[1.0, 0.704, 0.704], [0.704, 1.0, 0.0], [0.704, 0.0, 1.0]],
        index=list("ABC"),
        columns=list("ABC"),
    )
    pairs = high_pairs(c)
    assert pairs == [("A", "B", 0.704), ("A", "C", 0.704)]
    assert all(val > 0.70 for _, _, val in pairs)
    score, level, hits = risk_score(
        {"top_weight": 0.2, "effective_assets": 5}, 0.1, -0.05, pairs, 0.2
    )
    assert score == 15
    assert hits == [(15, "2 pairs of assets move closely together")]


def test_high_pairs_optional_round_digits():
    c = pd.DataFrame(
        [[1.0, 0.704], [0.704, 1.0]],
        index=list("AB"),
        columns=list("AB"),
    )
    assert high_pairs(c, round_digits=2) == [("A", "B", 0.7)]



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
