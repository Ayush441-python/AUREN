import numpy as np
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
from engine.stress import stress, worst_periods


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


def test_portfolio_returns_missing_ticker_raises_keyerror():
    w = pd.Series([0.6, 0.4], index=["NVDA", "ETH-USD"])
    prices = pd.DataFrame({"NVDA": [120.0, 122.0, 121.0]})
    with pytest.raises(KeyError) as exc_info:
        portfolio_returns(prices, w)
    assert "Historical price series unavailable for:" in str(exc_info.value)
    assert "ETH-USD" in str(exc_info.value)


def test_portfolio_returns_empty_prices():
    w = pd.Series([0.5, 0.5], index=["A", "B"])
    prices = pd.DataFrame(columns=["A", "B"])
    res = portfolio_returns(prices, w)
    assert res.empty


def test_max_drawdown_empty_series_returns_zero():
    empty_pr = pd.Series([], dtype=float)
    mdd = max_drawdown(empty_pr)
    assert mdd == 0.0
    assert not np.isnan(mdd)


def test_max_drawdown_nan_series_returns_zero():
    nan_pr = pd.Series([np.nan, np.nan])
    mdd = max_drawdown(nan_pr)
    assert mdd == 0.0
    assert not np.isnan(mdd)


def test_volatility_empty_and_single_observation_return_zero():
    assert volatility(pd.Series([], dtype=float)) == 0.0
    assert volatility(pd.Series([0.05])) == 0.0
    assert volatility(pd.Series([np.nan, np.nan])) == 0.0


def test_worst_periods_empty_and_short_series():
    # Empty series
    wp_empty = worst_periods(pd.Series([], dtype=float))
    assert wp_empty == {"worst_day": 0.0, "worst_month": 0.0}
    assert not np.isnan(wp_empty["worst_day"])
    assert not np.isnan(wp_empty["worst_month"])

    # Short series (< 21 days)
    short = pd.Series([-0.05, 0.02, 0.01])
    wp_short = worst_periods(short)
    assert wp_short["worst_day"] == pytest.approx(-0.05)
    assert wp_short["worst_month"] == 0.0
    assert not np.isnan(wp_short["worst_month"])

    # Long series (>= 21 days)
    long_pr = pd.Series([-0.01] * 25)
    wp_long = worst_periods(long_pr)
    assert wp_long["worst_day"] == pytest.approx(-0.01)
    assert wp_long["worst_month"] < 0.0
    assert not np.isnan(wp_long["worst_month"])
