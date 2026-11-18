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


def test_weekend_crypto_move_counts_per_calendar_day():
    """Issue #63: a Sat/Sun crypto crash must not hide inside Monday's return.

    Equity (NVDA) is NaN at the weekend in prices, as yfinance/CACHE store it.
    Old code: dropna() left only Friday/Monday rows, so the 3-day crypto
    decline Friday->Monday was reported as one "day". New code: every calendar
    day is one observation.
    """
    dates = pd.date_range("2024-11-15", periods=8, freq="D")  # Fri..Fri
    #            Fri     Sat     Sun     Mon     Tue     Wed     Thu     Fri
    prices = pd.DataFrame({
        "NVDA": [100.0, np.nan, np.nan, 100.0, 100.0, 100.0, 100.0, 100.0],
        "ETH-USD": [100.0, 50.0, 50.0, 50.0, 50.0, 50.0, 50.0, 50.0],
    }, index=dates)
    w = pd.Series({"NVDA": 0.5, "ETH-USD": 0.5})
    pr = portfolio_returns(prices, w)
    # Daily calendar: the -50% Saturday crash shows up on Saturday and never
    # folds into Monday; the first daily return is Sat's, not a 3-day move.
    assert pr.index[0] == dates[1]
    assert pr.iloc[0] == pytest.approx(-0.25)   # Sat: 0.5*0 + 0.5*(-0.5)
    assert pr.iloc[1] == pytest.approx(0.0)     # Sun: no weekend move left
    assert pr.iloc[2] == pytest.approx(0.0)     # Mon: crash already counted


def test_worst_month_window_is_21_calendar_days_for_crypto_and_mixed():
    """Issue #63: rolling(21) must span 21 calendar days, not 21 sessions."""
    prices = pd.read_csv("data/prices.csv", index_col=0, parse_dates=True)
    crypto = pd.Series({"BTC-USD": 0.5, "ETH-USD": 0.5})
    mixed = pd.Series({"BTC-USD": 0.45, "ETH-USD": 0.45, "NVDA": 0.10})

    pr_crypto = portfolio_returns(prices, crypto)
    pr_mixed = portfolio_returns(prices, mixed)

    # Both books now run on the same calendar: their 21-observation windows
    # reach the same dates (21 calendar days apart), not 21 days for crypto
    # vs ~31 calendar days for the mixed book (issue #63).
    assert pr_crypto.index[20] - pr_crypto.index[0] == pd.Timedelta(days=20)
    assert pr_mixed.index[20] - pr_mixed.index[0] == pd.Timedelta(days=20)
    # From the first equity close onward the two books share index dates.
    assert pr_crypto.index[1:].equals(pr_mixed.index[1:])
