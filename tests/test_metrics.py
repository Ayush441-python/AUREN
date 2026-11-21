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
from engine.stress import custom_shock_feedback, stress


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


def test_offsetting_sector_shocks_calculation():
    # Issue #127 case: MSFT (Big Tech) 50% + COST (Consumer & Retail) 50%
    weights = pd.Series({"MSFT": 0.5, "COST": 0.5})
    cases = [
        ({"Big Tech": 0.0, "Consumer & Retail": 0.0}, 0.0),
        ({"Big Tech": -0.10, "Consumer & Retail": 0.10}, 0.0),
        ({"Big Tech": -0.10, "Consumer & Retail": 0.0}, -0.05),
        ({"Big Tech": 0.0, "Consumer & Retail": 0.10}, 0.05),
    ]
    for shocks, expected in cases:
        net = stress(weights, shocks)
        assert net == pytest.approx(expected)


def test_custom_shock_feedback_all_sliders_zero():
    shocks = {"Big Tech": 0.0, "Consumer & Retail": 0.0}
    msg, opts = custom_shock_feedback(0.0, 0.0, shocks)
    assert msg == "Move the sliders to see hypothetical stress test impact."
    assert opts.get("muted") is True


def test_custom_shock_feedback_offsetting_shocks():
    shocks = {"Big Tech": -0.10, "Consumer & Retail": 0.10}
    msg, opts = custom_shock_feedback(0.0, 0.0, shocks)
    assert msg == "Under this custom shock, the selected shocks offset."
    assert "selected shocks offset" in msg
    assert opts.get("muted") is True


def test_custom_shock_feedback_with_weights_series():
    weights = pd.Series({"MSFT": 0.5, "COST": 0.5})
    shocks = {"Big Tech": -0.10, "Consumer & Retail": 0.10}
    msg, opts = custom_shock_feedback(weights, shocks)
    assert msg == "Under this custom shock, the selected shocks offset."
    assert opts.get("muted") is True


def test_custom_shock_feedback_negative_and_positive():
    shocks_neg = {"Big Tech": -0.10, "Consumer & Retail": 0.0}
    msg_neg, opts_neg = custom_shock_feedback(-0.05, -500.0, shocks_neg)
    assert "declines" in msg_neg
    assert "$500" in msg_neg
    assert opts_neg.get("danger") is True

    shocks_pos = {"Big Tech": 0.0, "Consumer & Retail": 0.10}
    msg_pos, opts_pos = custom_shock_feedback(0.05, 500.0, shocks_pos)
    assert "gains" in msg_pos
    assert "$500" in msg_pos
    assert opts_pos.get("danger") is not True

