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


def test_drawdown_first_period_loss():
    prices = pd.DataFrame({"NVDA": [100.0, 50.0, 55.0]})
    w = pd.Series({"NVDA": 1.0})
    pr = portfolio_returns(prices, w)
    assert max_drawdown(pr) == pytest.approx(-0.5)


@pytest.mark.parametrize(
    "returns,expected",
    [
        ([-0.5], -0.5),
        ([-0.5, 0.1], -0.5),
        ([-0.5, 0.0], -0.5),
        ([0.1, -0.5, 0.2], -0.5),  # existing positive-first-return control
        ([0.1, 0.2], 0.0),
        ([-1.0, 0.0], -1.0),
    ],
)
def test_drawdown_regression_cases(returns, expected):
    pr = pd.Series(returns, dtype=float)
    assert max_drawdown(pr) == pytest.approx(expected)


def test_drawdown_synthetic_price_drop_risk_score():
    prices = pd.DataFrame({"NVDA": [100.0] + [60.0] * 504})
    w = pd.Series({"NVDA": 1.0})
    pr = portfolio_returns(prices, w)
    mdd = max_drawdown(pr)
    assert mdd == pytest.approx(-0.4)
    vol = volatility(pr)
    assert vol == pytest.approx(0.2828427, rel=1e-4)
    conc = concentration(w)
    exp = sector_exposure(w)
    score, level, hits = risk_score(conc, vol, mdd, [], float(exp.max()))
    assert score == 65
    assert level == "High"
    assert any("Worst past fall was -40%" in why for _, why in hits)


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
