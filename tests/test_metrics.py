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


def test_short_history_asset_does_not_affect_pairwise_correlation():
    dates = pd.bdate_range("2025-01-02", periods=161)
    signals = np.array([
        [1, -1, 1, -1, 1, -1, 1, -1],
        [1, 1, -1, -1, 1, 1, -1, -1],
        [1, 1, 1, 1, -1, -1, -1, -1],
        [1, -1, -1, 1, 1, -1, -1, 1],
        [1, -1, 1, -1, -1, 1, -1, 1],
    ])
    returns = np.empty((160, 5))
    for column, signal in enumerate(signals):
        first_signal = signals[0] if column < 3 else signal
        returns[:120, column] = np.tile(first_signal, 15) / 100
        returns[120:, column] = np.tile(signal, 5) / 100
    prices = pd.DataFrame(
        100 * np.vstack([np.ones(5), np.cumprod(1 + returns, axis=0)]),
        index=dates,
        columns=["NVDA", "AMD", "COST", "JPM", "GLD"],
    )
    prices.loc[dates[:120], "GLD"] = np.nan

    corr_4 = correlation(prices, ["NVDA", "AMD", "COST", "JPM"])
    corr_5 = correlation(prices, ["NVDA", "AMD", "COST", "JPM", "GLD"])

    # NVDA/AMD, NVDA/COST, and AMD/COST correlations should remain 0.75
    assert corr_4.loc["NVDA", "AMD"] == pytest.approx(0.75)
    assert corr_5.loc["NVDA", "AMD"] == pytest.approx(0.75)
    assert corr_5.loc["NVDA", "COST"] == pytest.approx(0.75)
    assert corr_5.loc["AMD", "COST"] == pytest.approx(0.75)

    pairs_4 = high_pairs(corr_4)
    pairs_5 = high_pairs(corr_5)
    assert pairs_4 == [("NVDA", "AMD", 0.75), ("NVDA", "COST", 0.75), ("AMD", "COST", 0.75)]
    assert pairs_5 == [("NVDA", "AMD", 0.75), ("NVDA", "COST", 0.75), ("AMD", "COST", 0.75)]

    # Four holdings with 25% each
    weights_4 = pd.Series({"NVDA": 0.25, "AMD": 0.25, "COST": 0.25, "JPM": 0.25})
    pr_4 = portfolio_returns(prices, weights_4)
    score_4, level_4, hits_4 = risk_score(
        concentration(weights_4),
        volatility(pr_4),
        max_drawdown(pr_4),
        pairs_4,
        float(sector_exposure(weights_4).max()),
    )

    # Adding 1% GLD should retain the 3 qualifying pairs and the 15 score
    weights_5 = pd.Series({"NVDA": 0.2475, "AMD": 0.2475, "COST": 0.2475, "JPM": 0.2475, "GLD": 0.01})
    pr_5 = portfolio_returns(prices, weights_5)
    score_5, level_5, hits_5 = risk_score(
        concentration(weights_5),
        volatility(pr_5),
        max_drawdown(pr_5),
        pairs_5,
        float(sector_exposure(weights_5).max()),
    )

    assert score_4 == 15 and level_4 == "Low"
    assert score_5 == 15 and level_5 == "Low"


def test_correlation_single_and_non_overlapping():
    prices = pd.DataFrame(
        {
            "A": [100.0, 101.0, 102.0, 103.0],
            "B": [np.nan, np.nan, 200.0, 202.0],
            "C": [300.0, 303.0, np.nan, np.nan],
        }
    )
    corr = correlation(prices, ["A", "B", "C"])
    assert corr.loc["A", "A"] == pytest.approx(1.0)
    assert np.isnan(corr.loc["A", "B"])
    assert np.isnan(corr.loc["B", "C"])
