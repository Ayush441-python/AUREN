import itertools
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


def test_concentration_order_invariance():
    # Identical weights in different key orders should yield exact 4.0 effective assets
    first = {"NVDA": 0.40, "GLD": 0.15, "JPM": 0.15, "XOM": 0.15, "AMGN": 0.15}
    for order in itertools.permutations(first.keys()):
        w = pd.Series({k: first[k] for k in order})
        conc = concentration(w)
        assert conc["hhi"] == 0.25
        assert conc["effective_assets"] == 4.0
        score, level, hits = risk_score(conc, 0.10, -0.05, [], 0.20)
        assert score == 20
        assert level == "Low"
        assert not any("Behaves like only" in why for _, why in hits)


def test_concentration_threshold_sensitivity():
    # Moving 0.1 percentage point:
    # 0.1% higher concentration (effective assets < 4) triggers rule (+15 pts)
    w_more = pd.Series({"NVDA": 0.401, "GLD": 0.149, "JPM": 0.15, "XOM": 0.15, "AMGN": 0.15})
    conc_more = concentration(w_more)
    assert conc_more["effective_assets"] < 4.0
    score, level, hits = risk_score(conc_more, 0.10, -0.05, [], 0.20)
    assert score == 35
    assert level == "Medium"
    assert any("Behaves like only" in why for _, why in hits)

    # 0.1% lower concentration (effective assets >= 4) does not trigger rule
    w_less = pd.Series({"NVDA": 0.399, "GLD": 0.151, "JPM": 0.15, "XOM": 0.15, "AMGN": 0.15})
    conc_less = concentration(w_less)
    assert conc_less["effective_assets"] >= 4.0
    score, level, hits = risk_score(conc_less, 0.10, -0.05, [], 0.20)
    assert score == 20
    assert level == "Low"
    assert not any("Behaves like only" in why for _, why in hits)

