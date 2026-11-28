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


def test_worst_periods_short_series_returns_finite_float():
    from engine.stress import worst_periods
    pr = pd.Series([-0.02, 0.01, -0.04, 0.005, -0.01])
    res = worst_periods(pr)
    assert res["worst_day"] == pytest.approx(-0.04)
    assert pd.notna(res["worst_month"])
    expected_cum = (1.0 - 0.02) * (1.0 + 0.01) * (1.0 - 0.04) * (1.0 + 0.005) * (1.0 - 0.01) - 1.0
    assert res["worst_month"] == pytest.approx(expected_cum)


def test_rebased_portfolio_index_starts_at_100_and_stays_in_convex_hull():
    from engine.metrics import portfolio_returns
    dates = pd.date_range("2026-01-01", periods=3, freq="D")
    # Asset A rises +100% then falls -50% back to 100; Asset B stays at 100
    prices = pd.DataFrame({"A": [100.0, 200.0, 100.0], "B": [100.0, 100.0, 100.0]}, index=dates)
    w = pd.Series({"A": 0.5, "B": 0.5})
    norm = prices / prices.iloc[0] * 100.0
    rebased_portfolio = norm[w.index] @ w
    assert rebased_portfolio.iloc[0] == pytest.approx(100.0)
    assert rebased_portfolio.iloc[-1] == pytest.approx(100.0)
    # Daily-rebalanced cumprod would drift to 112.5 outside both assets (100.0)
    pr = portfolio_returns(prices, w)
    daily_rebal = (1.0 + pr).cumprod() * 100.0
    assert daily_rebal.iloc[-1] == pytest.approx(112.5)
