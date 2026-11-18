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


def test_avg_daily_value_aligns_crypto_to_prices_index():
    from engine.liquidity import avg_daily_value
    all_dates = pd.date_range("2026-11-09", periods=7, freq="D")  # Mon..Sun
    trading_dates = all_dates[:5]  # Mon..Fri only in aligned prices
    prices = pd.DataFrame(
        {"NVDA": [100.0] * 5, "ETH-USD": [3000.0] * 5},
        index=trading_dates,
    )
    volumes = pd.DataFrame(
        {
            "NVDA": [10.0, 10.0, 10.0, 10.0, 10.0, float("nan"), float("nan")],
            "ETH-USD": [1000.0, 1000.0, 1000.0, 1000.0, 1000.0, 100.0, 100.0],
        },
        index=all_dates,
    )
    adv = avg_daily_value(prices, volumes, window=5)
    assert adv["NVDA"] == pytest.approx(1000.0)
    assert adv["ETH-USD"] == pytest.approx(1000.0)


def test_avg_daily_value_prevents_crypto_lookahead_on_sliced_prices():
    from engine.liquidity import avg_daily_value
    dates = pd.date_range("2026-10-01", periods=10, freq="D")
    prices_full = pd.DataFrame({"ETH-USD": [2500.0] * 10}, index=dates)
    volumes_full = pd.DataFrame(
        {"ETH-USD": [500.0] * 5 + [999999.0] * 5},
        index=dates,
    )
    adv_historical = avg_daily_value(prices_full.iloc[:5], volumes_full, window=5)
    assert adv_historical["ETH-USD"] == pytest.approx(500.0)
