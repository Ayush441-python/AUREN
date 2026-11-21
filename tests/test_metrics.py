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


def test_volatility_crypto_weight_scaling():
    pr = pd.Series([0.01, -0.02, 0.015, -0.005, 0.02])
    std = pr.std()

    # Default / pure equity convention: sqrt(252)
    vol_equity = volatility(pr)
    assert vol_equity == pytest.approx(float(std * np.sqrt(252.0)))
    assert volatility(pr, crypto_weight=0.0) == pytest.approx(vol_equity)

    # Pure crypto convention: sqrt(365)
    vol_crypto = volatility(pr, crypto_weight=1.0)
    assert vol_crypto == pytest.approx(float(std * np.sqrt(365.0)))

    # Verify ~16.91% underestimation proof: (sqrt(365) - sqrt(252)) / sqrt(365)
    underestimation = (vol_crypto - vol_equity) / vol_crypto
    assert underestimation == pytest.approx(0.1691, abs=1e-3)

    # 50/50 mixed portfolio: sqrt(365 * 0.5 + 252 * 0.5) = sqrt(308.5)
    vol_mixed = volatility(pr, crypto_weight=0.5)
    assert vol_mixed == pytest.approx(float(std * np.sqrt(308.5)))

    # Arbitrary weighting: 25% crypto + 75% equity
    vol_quarter = volatility(pr, crypto_weight=0.25)
    expected_days = 365.0 * 0.25 + 252.0 * 0.75
    assert vol_quarter == pytest.approx(float(std * np.sqrt(expected_days)))


def test_portfolio_returns_weekend_forward_fill_mixed():
    # Simulated weekend prices: Fri: 100, Sat: 102, Sun: 101, Mon: 104
    dates = pd.date_range("2026-11-06", periods=4)  # Fri, Sat, Sun, Mon
    df = pd.DataFrame(
        {
            "NVDA": [140.0, np.nan, np.nan, 142.0],
            "BTC-USD": [100.0, 102.0, 101.0, 104.0],
        },
        index=dates,
    )
    w = pd.Series({"NVDA": 0.5, "BTC-USD": 0.5})

    pr = portfolio_returns(df, w)

    # All 3 transition days (Sat, Sun, Mon) are preserved
    assert len(pr) == 3

    # Saturday: NVDA forward-filled from Fri (0% return), BTC (102-100)/100 = 2%
    assert pr.loc["2026-11-07"] == pytest.approx(0.5 * 0.0 + 0.5 * 0.02)

    # Sunday: NVDA forward-filled (0% return), BTC (101-102)/102 = -0.98%
    assert pr.loc["2026-11-08"] == pytest.approx(0.5 * 0.0 + 0.5 * ((101.0 - 102.0) / 102.0))

    # Monday: NVDA (142-140)/140 = 1.43%, BTC 24h return (104-101)/101 = 2.97% (NOT 72h jump of 4.0%)
    btc_mon_return = (104.0 - 101.0) / 101.0
    nvda_mon_return = (142.0 - 140.0) / 140.0
    assert pr.loc["2026-11-09"] == pytest.approx(0.5 * nvda_mon_return + 0.5 * btc_mon_return)


def test_portfolio_returns_pure_crypto():
    dates = pd.date_range("2026-11-06", periods=4)
    df = pd.DataFrame({"BTC-USD": [100.0, 102.0, 101.0, 104.0]}, index=dates)
    w = pd.Series({"BTC-USD": 1.0})

    pr = portfolio_returns(df, w)
    assert len(pr) == 3
    assert pr.loc["2026-11-07"] == pytest.approx(0.02)
    assert pr.loc["2026-11-08"] == pytest.approx((101.0 - 102.0) / 102.0)
    assert pr.loc["2026-11-09"] == pytest.approx((104.0 - 101.0) / 101.0)


def test_portfolio_returns_pure_equity():
    dates = pd.date_range("2026-11-02", periods=3)  # Mon, Tue, Wed
    df = pd.DataFrame({"NVDA": [100.0, 105.0, 102.0]}, index=dates)
    w = pd.Series({"NVDA": 1.0})

    pr = portfolio_returns(df, w)
    assert len(pr) == 2
    assert pr.iloc[0] == pytest.approx(0.05)
    assert pr.iloc[1] == pytest.approx((102.0 - 105.0) / 105.0)


def test_crypto_volatility_impact_on_risk_score():
    # std = 0.016 daily returns
    # Under equity 252 annualization: 0.016 * sqrt(252) = 0.254 (< 30%, 0 risk score)
    # Under crypto 365 annualization: 0.016 * sqrt(365) = 0.306 (> 30%, +20 risk score)
    daily_std = 0.016
    pr = pd.Series([daily_std, -daily_std] * 50)
    conc = {"top_weight": 0.10, "effective_assets": 10}

    # Old equity annualization: misses high volatility rule
    vol_equity = volatility(pr, crypto_weight=0.0)
    score_eq, _, hits_eq = risk_score(conc, vol_equity, -0.05, [], 0.20)
    assert vol_equity < 0.30
    assert score_eq == 0
    assert len(hits_eq) == 0

    # Correct crypto annualization: correctly triggers volatility rule (>30%)
    vol_crypto = volatility(pr, crypto_weight=1.0)
    score_cr, _, hits_cr = risk_score(conc, vol_crypto, -0.05, [], 0.20)
    assert vol_crypto > 0.30
    assert score_cr == 20
    assert len(hits_cr) == 1
    assert "Volatility is" in hits_cr[0][1]
