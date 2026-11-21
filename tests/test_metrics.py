import pandas as pd
import pytest
from engine.metrics import (
    concentration,
    volatility,
    max_drawdown,
    correlation,
    high_pairs,
    sector_exposure,
    common_prices,
    portfolio_returns,
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


def test_common_prices_aligns_overlapping_dates():
    dates = pd.date_range("2024-01-01", periods=5, freq="D")
    prices = pd.DataFrame(
        {
            "A": [10.0, 11.0, 12.0, 13.0, 14.0],
            "B": [float("nan"), float("nan"), 20.0, 21.0, 22.0],
        },
        index=dates,
    )
    aligned = common_prices(prices, ["A", "B"])
    assert len(aligned) == 3
    assert list(aligned.index) == list(dates[2:])
    assert aligned.columns.tolist() == ["A", "B"]


def test_common_prices_missing_ticker_returns_empty():
    prices = pd.DataFrame({"A": [1.0, 2.0, 3.0]})
    assert common_prices(prices, ["A", "MISSING"]).empty


def test_same_window_comparison_removes_phantom_risk_reduction():
    # Issue 145: MSFT has 60 dates (falls from 100 to 60 in first 10-20 dates).
    # AAPL only has quotes for the last 40 dates, remaining constant at 60.
    dates = pd.date_range("2024-01-01", periods=60, freq="D")
    prices = pd.DataFrame(
        {
            "MSFT": [100.0] * 10 + [60.0] * 50,
            "AAPL": [float("nan")] * 20 + [60.0] * 40,
        },
        index=dates,
    )
    w_msft = pd.Series({"MSFT": 1.0})
    w_aapl = pd.Series({"AAPL": 1.0})

    # On separate histories: MSFT has high vol and drawdown, AAPL has none.
    pr_msft_full = portfolio_returns(prices[["MSFT"]], w_msft)
    pr_aapl_full = portfolio_returns(prices[["AAPL"]], w_aapl)
    score_msft_full, level_msft_full, _ = risk_score(
        concentration(w_msft),
        volatility(pr_msft_full),
        max_drawdown(pr_msft_full),
        [],
        1.0,
    )
    score_aapl_full, level_aapl_full, _ = risk_score(
        concentration(w_aapl),
        volatility(pr_aapl_full),
        max_drawdown(pr_aapl_full),
        [],
        1.0,
    )
    assert score_msft_full == 85 and level_msft_full == "High"
    assert score_aapl_full == 50 and level_aapl_full == "Medium"
    # Separate history delta was -35 pts
    assert score_aapl_full - score_msft_full == -35

    # On common window:
    common = common_prices(prices, ["MSFT", "AAPL"])
    assert len(common) == 40
    pr_msft_common = portfolio_returns(common, w_msft)
    pr_aapl_common = portfolio_returns(common, w_aapl)
    assert len(pr_msft_common) == len(pr_aapl_common) == 39
    assert volatility(pr_msft_common) == pytest.approx(0.0)
    assert volatility(pr_aapl_common) == pytest.approx(0.0)
    assert max_drawdown(pr_msft_common) == pytest.approx(0.0)
    assert max_drawdown(pr_aapl_common) == pytest.approx(0.0)

    score_msft_common, level_msft_common, _ = risk_score(
        concentration(w_msft),
        volatility(pr_msft_common),
        max_drawdown(pr_msft_common),
        [],
        1.0,
    )
    score_aapl_common, level_aapl_common, _ = risk_score(
        concentration(w_aapl),
        volatility(pr_aapl_common),
        max_drawdown(pr_aapl_common),
        [],
        1.0,
    )
    assert score_msft_common == 50 and level_msft_common == "Medium"
    assert score_aapl_common == 50 and level_aapl_common == "Medium"
    # Delta on common window is 0 pts
    assert score_aapl_common - score_msft_common == 0

