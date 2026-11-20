import pandas as pd
import numpy as np
import pytest
from engine.liquidity import days_to_exit, avg_daily_value


def test_days_to_exit_long_positions():
    positions = pd.Series({"AAPL": 100000.0, "MSFT": 50000.0})
    adv = pd.Series({"AAPL": 1000000.0, "MSFT": 500000.0})
    # 100,000 / (0.10 * 1,000,000) = 100,000 / 100,000 = 1.0 day
    # 50,000 / (0.10 * 500,000) = 50,000 / 50,000 = 1.0 day
    result = days_to_exit(positions, adv, participation=0.10)
    assert pytest.approx(result["AAPL"]) == 1.0
    assert pytest.approx(result["MSFT"]) == 1.0


def test_days_to_exit_short_positions_strictly_non_negative():
    """Short positions must calculate positive time to liquidate / cover."""
    positions = pd.Series({"TSLA": -200000.0, "NVDA": -50000.0})
    adv = pd.Series({"TSLA": 1000000.0, "NVDA": 250000.0})
    # TSLA: |-200,000| / (0.10 * 1,000,000) = 200,000 / 100,000 = 2.0 days
    # NVDA: |-50,000| / (0.10 * 250,000) = 50,000 / 25,000 = 2.0 days
    result = days_to_exit(positions, adv, participation=0.10)
    assert pytest.approx(result["TSLA"]) == 2.0
    assert pytest.approx(result["NVDA"]) == 2.0
    assert (result >= 0).all()


def test_days_to_exit_mixed_portfolio():
    positions = pd.Series({"LONG_STOCK": 50000.0, "SHORT_STOCK": -50000.0, "ZERO_STOCK": 0.0})
    adv = pd.Series({"LONG_STOCK": 500000.0, "SHORT_STOCK": 500000.0, "ZERO_STOCK": 500000.0})
    result = days_to_exit(positions, adv, participation=0.10)
    assert pytest.approx(result["LONG_STOCK"]) == 1.0
    assert pytest.approx(result["SHORT_STOCK"]) == 1.0
    assert pytest.approx(result["ZERO_STOCK"]) == 0.0


def test_days_to_exit_zero_adv_returns_nan():
    positions = pd.Series({"ILLIQUID": 10000.0})
    adv = pd.Series({"ILLIQUID": 0.0})
    result = days_to_exit(positions, adv, participation=0.10)
    assert np.isnan(result["ILLIQUID"])


def test_days_to_exit_invalid_participation_rate():
    positions = pd.Series({"AAPL": 10000.0})
    adv = pd.Series({"AAPL": 100000.0})
    with pytest.raises(ValueError, match="participation rate must be positive"):
        days_to_exit(positions, adv, participation=0.0)
    with pytest.raises(ValueError, match="participation rate must be positive"):
        days_to_exit(positions, adv, participation=-0.05)


def test_avg_daily_value_stocks_and_crypto():
    dates = pd.date_range("2026-01-01", periods=5)
    prices = pd.DataFrame({
        "AAPL": [150.0, 150.0, 150.0, 150.0, 150.0],
        "BTC-USD": [50000.0, 50000.0, 50000.0, 50000.0, 50000.0]
    }, index=dates)
    volumes = pd.DataFrame({
        "AAPL": [1000.0, 1000.0, 1000.0, 1000.0, 1000.0],  # 150 * 1000 = 150,000 USD
        "BTC-USD": [2000000.0, 2000000.0, 2000000.0, 2000000.0, 2000000.0]  # Already in USD
    }, index=dates)
    result = avg_daily_value(prices, volumes, window=5)
    assert pytest.approx(result["AAPL"]) == 150000.0
    assert pytest.approx(result["BTC-USD"]) == 2000000.0
