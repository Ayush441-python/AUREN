import numpy as np
import pandas as pd
import pytest

from engine.liquidity import avg_daily_value, days_to_exit, observed_sessions


def test_issue_154_reproduction_in_window_equality():
    """Ensure older trades outside the window are never pulled in when volume is missing.

    Specifically:
    - Row 1: 30 days at 10 shares, old trade of 100,000 -> ADV = $1,000, days = 40
    - Row 2: 29 days at 10 shares, 1 day missing, old trade of 10 -> ADV = $1,000, days = 40
    - Row 3: 29 days at 10 shares, 1 day missing, old trade of 100,000 -> ADV = $1,000, days = 40
    - Row 4: 30 days missing, old trade of 100,000 -> ADV is NaN, days is NaN (estimate unknown)
    """
    dates = pd.bdate_range("2026-01-05", periods=31)
    prices = pd.DataFrame({"NVDA": [100.0] * 31}, index=dates)
    position = pd.Series({"NVDA": 4000.0})

    results = []
    for old, missing in [(100000, 0), (10, 1), (100000, 1), (100000, 30)]:
        volume = pd.DataFrame({"NVDA": [float(old)] + [10.0] * 30}, index=dates)
        if missing:
            volume.loc[dates[-missing:], "NVDA"] = float("nan")
        adv = avg_daily_value(prices, volume, window=30)
        days = days_to_exit(position, adv, participation=0.10)
        results.append((adv["NVDA"], days["NVDA"]))

    # Row 1
    assert results[0][0] == pytest.approx(1000.0)
    assert results[0][1] == pytest.approx(40.0)

    # Row 2
    assert results[1][0] == pytest.approx(1000.0)
    assert results[1][1] == pytest.approx(40.0)

    # Row 3 must match Row 2 despite old=100000 before window
    assert results[2][0] == pytest.approx(1000.0)
    assert results[2][1] == pytest.approx(40.0)

    # Row 4 with zero observed sessions inside window must be NaN
    assert np.isnan(results[3][0])
    assert np.isnan(results[3][1])


def test_observed_sessions_and_return_counts():
    """Verify observation counts reporting for full, partial, and zero coverage."""
    dates = pd.bdate_range("2026-01-05", periods=31)
    prices = pd.DataFrame({"NVDA": [100.0] * 31}, index=dates)

    # Full coverage (30 observations)
    vol_full = pd.DataFrame({"NVDA": [100000.0] + [10.0] * 30}, index=dates)
    adv_full, cnt_full = avg_daily_value(prices, vol_full, window=30, return_counts=True)
    assert cnt_full["NVDA"] == 30
    assert observed_sessions(prices, vol_full, window=30)["NVDA"] == 30

    # Partial coverage (29 observations, 1 missing)
    vol_part = vol_full.copy()
    vol_part.loc[dates[-1], "NVDA"] = np.nan
    adv_part, cnt_part = avg_daily_value(prices, vol_part, window=30, return_counts=True)
    assert cnt_part["NVDA"] == 29
    assert observed_sessions(prices, vol_part, window=30)["NVDA"] == 29

    # Zero coverage (all 30 missing)
    vol_zero = vol_full.copy()
    vol_zero.loc[dates[-30:], "NVDA"] = np.nan
    adv_zero, cnt_zero = avg_daily_value(prices, vol_zero, window=30, return_counts=True)
    assert cnt_zero["NVDA"] == 0
    assert observed_sessions(prices, vol_zero, window=30)["NVDA"] == 0
    assert np.isnan(adv_zero["NVDA"])


def test_distinct_missing_vs_observed_zero():
    """A missing observation and an observed zero are distinct."""
    dates = pd.bdate_range("2026-01-05", periods=31)
    prices = pd.DataFrame({"NVDA": [100.0] * 31}, index=dates)

    # 29 days of 10 shares, 1 missing -> mean of 29 observed = 1000.0
    vol_missing = pd.DataFrame({"NVDA": [100000.0] + [10.0] * 29 + [np.nan]}, index=dates)
    adv_missing, cnt_missing = avg_daily_value(prices, vol_missing, window=30, return_counts=True)
    assert cnt_missing["NVDA"] == 29
    assert adv_missing["NVDA"] == pytest.approx(1000.0)

    # 29 days of 10 shares, 1 observed 0 -> mean of 30 observed = (29 * 1000 + 0) / 30 = 966.67
    vol_zero = pd.DataFrame({"NVDA": [100000.0] + [10.0] * 29 + [0.0]}, index=dates)
    adv_zero, cnt_zero = avg_daily_value(prices, vol_zero, window=30, return_counts=True)
    assert cnt_zero["NVDA"] == 30
    assert adv_zero["NVDA"] == pytest.approx(966.6666667)
    assert adv_zero["NVDA"] != adv_missing["NVDA"]

    # All 30 observed zeros -> ADV is 0.0, days to exit is NaN (cannot exit)
    vol_all_zero = pd.DataFrame({"NVDA": [100000.0] + [0.0] * 30}, index=dates)
    adv_all_zero = avg_daily_value(prices, vol_all_zero, window=30)
    assert adv_all_zero["NVDA"] == pytest.approx(0.0)
    days = days_to_exit(pd.Series({"NVDA": 4000.0}), adv_all_zero, participation=0.10)
    assert np.isnan(days["NVDA"])


def test_crypto_adv_volume_in_usd():
    """Crypto tickers (-USD) volume is already reported in USD and not multiplied by price."""
    dates = pd.date_range("2026-01-01", periods=35)
    prices = pd.DataFrame({"ETH-USD": [2000.0] * 35}, index=dates)
    # 5 older days of 1e9, 30 days of 50,000 USD
    volumes = pd.DataFrame({"ETH-USD": [1e9] * 5 + [50000.0] * 30}, index=dates)

    adv = avg_daily_value(prices, volumes, window=30)
    assert adv["ETH-USD"] == pytest.approx(50000.0)

    # 1 day missing inside the window does not pull older 1e9 trade
    volumes.loc[dates[-1], "ETH-USD"] = np.nan
    adv_missing = avg_daily_value(prices, volumes, window=30)
    assert adv_missing["ETH-USD"] == pytest.approx(50000.0)


def test_date_alignment_and_timezone_handling():
    """Test alignment when volume series has different/unaligned dates or timezones."""
    p_dates = pd.date_range("2026-01-01", periods=30, tz="UTC")
    v_dates = pd.date_range("2025-12-01", periods=60)  # tz-naive and wider range

    prices = pd.DataFrame({"AAPL": [150.0] * 30}, index=p_dates)
    volumes = pd.DataFrame({"AAPL": [1000.0] * 60}, index=v_dates)

    adv = avg_daily_value(prices, volumes, window=30)
    assert adv["AAPL"] == pytest.approx(150.0 * 1000.0)


def test_edge_cases():
    """Test empty dataframes, non-matching tickers, and non-positive windows."""
    prices = pd.DataFrame({"AAPL": [150.0] * 10})
    volumes = pd.DataFrame({"MSFT": [1000.0] * 10})

    # Ticker in prices not in volumes
    adv = avg_daily_value(prices, volumes, window=10)
    assert "AAPL" not in adv

    # Empty inputs
    assert avg_daily_value(pd.DataFrame(), pd.DataFrame()).empty

    # Non-positive window
    adv_zero_win = avg_daily_value(prices, pd.DataFrame({"AAPL": [1000.0] * 10}), window=0)
    assert np.isnan(adv_zero_win["AAPL"])
