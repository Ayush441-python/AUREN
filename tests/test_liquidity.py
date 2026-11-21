import numpy as np
import pandas as pd
import pytest
from engine.liquidity import avg_daily_value, days_to_exit


def test_days_to_exit_short_positions():
    """Short positions must have non-negative liquidation duration based on absolute value."""
    position_values = pd.Series({"AAPL": -100_000.0, "MSFT": 200_000.0})
    adv = pd.Series({"AAPL": 1_000_000.0, "MSFT": 1_000_000.0})

    result = days_to_exit(position_values, adv, participation=0.10)

    assert result["AAPL"] == pytest.approx(1.0)
    assert result["MSFT"] == pytest.approx(2.0)
    assert (result >= 0).all()


def test_days_to_exit_pure_short_portfolio():
    """Portfolio with multiple short positions yields positive exit horizons."""
    position_values = pd.Series({"TSLA": -500_000.0, "NVDA": -200_000.0})
    adv = pd.Series({"TSLA": 2_000_000.0, "NVDA": 1_000_000.0})

    result = days_to_exit(position_values, adv, participation=0.10)

    # TSLA: 500k / (0.10 * 2M) = 500k / 200k = 2.5 days
    # NVDA: 200k / (0.10 * 1M) = 200k / 100k = 2.0 days
    assert result["TSLA"] == pytest.approx(2.5)
    assert result["NVDA"] == pytest.approx(2.0)


def test_days_to_exit_zero_position():
    """A zero position requires 0 days to unwind."""
    position_values = pd.Series({"AAPL": 0.0, "MSFT": -100_000.0})
    adv = pd.Series({"AAPL": 1_000_000.0, "MSFT": 1_000_000.0})

    result = days_to_exit(position_values, adv, participation=0.10)

    assert result["AAPL"] == pytest.approx(0.0)
    assert result["MSFT"] == pytest.approx(1.0)


def test_days_to_exit_zero_or_nan_adv():
    """Zero or missing ADV should result in NaN."""
    position_values = pd.Series({"AAPL": -100_000.0, "MSFT": 200_000.0, "GOOGL": -50_000.0})
    adv = pd.Series({"AAPL": 0.0, "MSFT": 1_000_000.0})  # GOOGL missing, AAPL zero

    result = days_to_exit(position_values, adv, participation=0.10)

    assert np.isnan(result["AAPL"])
    assert result["MSFT"] == pytest.approx(2.0)
    assert np.isnan(result["GOOGL"])


def test_days_to_exit_custom_participation():
    """Verify days to exit scales inversely with participation rate."""
    position_values = pd.Series({"AAPL": -100_000.0})
    adv = pd.Series({"AAPL": 1_000_000.0})

    # At 5% participation: 100k / 50k = 2.0 days
    res_5pct = days_to_exit(position_values, adv, participation=0.05)
    assert res_5pct["AAPL"] == pytest.approx(2.0)

    # At 20% participation: 100k / 200k = 0.5 days
    res_20pct = days_to_exit(position_values, adv, participation=0.20)
    assert res_20pct["AAPL"] == pytest.approx(0.5)


def test_avg_daily_value():
    """Verify average daily traded value calculation for stocks and crypto."""
    prices = pd.DataFrame({
        "AAPL": [150.0, 152.0, 154.0],
        "BTC-USD": [50_000.0, 51_000.0, 52_000.0],
    })
    volumes = pd.DataFrame({
        "AAPL": [1_000.0, 2_000.0, 3_000.0],
        "BTC-USD": [10_000_000.0, 20_000_000.0, 30_000_000.0],
    })

    adv = avg_daily_value(prices, volumes, window=2)

    # AAPL last 2 days: (152*2000 + 154*3000)/2 = (304000 + 462000)/2 = 383,000
    assert adv["AAPL"] == pytest.approx(383_000.0)
    # BTC-USD is crypto (-USD), so volume is already dollar volume: (20M + 30M)/2 = 25,000,000
    assert adv["BTC-USD"] == pytest.approx(25_000_000.0)
