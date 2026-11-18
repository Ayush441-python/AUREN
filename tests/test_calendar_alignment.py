import numpy as np
import pandas as pd
import pytest
from engine.metrics import portfolio_returns
from engine.stress import worst_periods


def test_mixed_portfolio_forward_fills_and_preserves_weekend_returns():
    """Verify that mixing equity and crypto does not drop weekend rows, preserving single-day weekend returns."""
    dates = pd.date_range("2026-11-06", periods=4, freq="D")  # Fri, Sat, Sun, Mon
    prices = pd.DataFrame(
        {
            "NVDA": [140.0, np.nan, np.nan, 142.0],
            "BTC-USD": [100.0, 102.0, 101.0, 104.0],
        },
        index=dates,
    )
    w = pd.Series({"NVDA": 0.5, "BTC-USD": 0.5})
    pr = portfolio_returns(prices, w)

    # Returns must have 3 days (Sat, Sun, Mon)
    assert len(pr) == 3
    assert list(pr.index) == list(dates[1:])

    # Sat: NVDA change is 0.0, BTC change is +2.0%
    assert pr.iloc[0] == pytest.approx(0.5 * 0.0 + 0.5 * (102.0 / 100.0 - 1))
    # Sun: NVDA change is 0.0, BTC change is -0.98%
    assert pr.iloc[1] == pytest.approx(0.5 * 0.0 + 0.5 * (101.0 / 102.0 - 1))
    # Mon: NVDA change is +1.43%, BTC change is +2.97% (not a 3-day aggregated move)
    assert pr.iloc[2] == pytest.approx(
        0.5 * (142.0 / 140.0 - 1) + 0.5 * (104.0 / 101.0 - 1)
    )


def test_worst_periods_calendar_window_scaling():
    """Verify that daily 7-day calendar series (>600 observations) use a 30-day window for worst_month."""
    # 700 daily observations simulating a 2-year calendar series
    pr_daily = pd.Series([0.005] * 700)
    pr_daily.iloc[100:130] = -0.01  # 30-day downturn

    wp_daily = worst_periods(pr_daily)
    expected_month_drop = (1 - 0.01) ** 30 - 1
    assert wp_daily["worst_month"] == pytest.approx(expected_month_drop)

    # Short / business-day series (e.g. 500 rows) keeps standard 21-day window
    pr_bday = pd.Series([0.005] * 500)
    pr_bday.iloc[50:71] = -0.01  # 21-day downturn
    wp_bday = worst_periods(pr_bday)
    expected_bday_drop = (1 - 0.01) ** 21 - 1
    assert wp_bday["worst_month"] == pytest.approx(expected_bday_drop)
