import math
from types import SimpleNamespace
from unittest.mock import patch
import pandas as pd
import pytest

from engine.liquidity import avg_daily_value, days_to_exit
import api


def test_avg_daily_value_usd_default():
    """Verify standard USD assets retain original calculations."""
    idx = pd.bdate_range("2025-01-01", periods=10)
    prices = pd.DataFrame({"AAPL": [100.0] * 10}, index=idx)
    volumes = pd.DataFrame({"AAPL": [1000.0] * 10}, index=idx)

    adv = avg_daily_value(prices, volumes, window=10)
    assert adv["AAPL"] == pytest.approx(100000.0)


def test_avg_daily_value_crypto_usd():
    """Crypto tickers ending with -USD treat volume as dollar volume."""
    idx = pd.bdate_range("2025-01-01", periods=10)
    prices = pd.DataFrame({"BTC-USD": [50000.0] * 10}, index=idx)
    volumes = pd.DataFrame({"BTC-USD": [1000000.0] * 10}, index=idx)

    adv = avg_daily_value(prices, volumes, window=10)
    assert adv["BTC-USD"] == pytest.approx(1000000.0)


def test_avg_daily_value_non_usd_missing_fx_reports_nan():
    """Non-USD quoted asset without FX rate must report NaN to avoid understatement."""
    idx = pd.bdate_range("2025-01-01", periods=10)
    prices = pd.DataFrame({"7203.T": [1000.0] * 10}, index=idx)
    volumes = pd.DataFrame({"7203.T": [12000.0] * 10}, index=idx)

    adv = avg_daily_value(prices, volumes, window=10, currencies={"7203.T": "JPY"})
    assert math.isnan(adv["7203.T"])


def test_avg_daily_value_non_usd_with_fx_conversion():
    """Non-USD asset with scalar FX rate converts turnover accurately to USD."""
    idx = pd.bdate_range("2025-01-01", periods=10)
    prices = pd.DataFrame({"7203.T": [1000.0] * 10}, index=idx)
    volumes = pd.DataFrame({"7203.T": [12000.0] * 10}, index=idx)

    # 1 USD = 150 JPY -> rate = 1/150 USD per JPY
    adv = avg_daily_value(
        prices,
        volumes,
        window=10,
        currencies={"7203.T": "JPY"},
        fx_rates={"JPY": 1.0 / 150.0},
    )
    # Daily turnover = 1,000 * 12,000 / 150 = 80,000 USD
    assert adv["7203.T"] == pytest.approx(80000.0)


def test_avg_daily_value_non_usd_with_fx_series():
    """Non-USD asset with time-varying FX series applies per-session rate."""
    idx = pd.bdate_range("2025-01-01", periods=2)
    prices = pd.DataFrame({"7203.T": [1000.0, 1000.0]}, index=idx)
    volumes = pd.DataFrame({"7203.T": [10000.0, 10000.0]}, index=idx)
    # Day 1: 100 JPY/USD (rate=0.01), Day 2: 200 JPY/USD (rate=0.005)
    fx_series = pd.Series([0.01, 0.005], index=idx)

    adv = avg_daily_value(
        prices,
        volumes,
        window=2,
        currencies={"7203.T": "JPY"},
        fx_rates={"JPY": fx_series},
    )
    # Day 1 turnover: 100,000 USD, Day 2 turnover: 50,000 USD -> Mean: 75,000 USD
    assert adv["7203.T"] == pytest.approx(75000.0)


def test_liquidity_issue_226_reproduction_and_fix():
    """Exact reproduction of Issue #226: 7203.T vs USD control AAPL."""
    idx = pd.bdate_range("2025-01-06", periods=30)
    vol = pd.DataFrame({"7203.T": [12000] * 30, "AAPL": [12000] * 30}, index=idx)
    px = pd.DataFrame({"7203.T": [1000.0] * 30, "AAPL": [1000.0 / 150.0] * 30}, index=idx)

    def mock_ticker(t):
        if t == "7203.T":
            return SimpleNamespace(info={"sector": "Consumer Cyclical", "currency": "JPY"})
        return SimpleNamespace(info={"sector": "Technology", "currency": "USD"})

    with patch.object(api, "load_prices", return_value=px), \
         patch.object(api, "load_volumes", return_value=vol), \
         patch.dict("sys.modules", {"yfinance": SimpleNamespace(Ticker=mock_ticker)}):

        # 1. USD Control
        req_usd = api.LiquidityRequest(weights={"AAPL": 100}, portfolio_value=240000, adv_participation=0.10)
        res_usd = api.compute_liquidity(req_usd)
        asset_usd = res_usd["assets"][0]
        assert asset_usd["adv"] == pytest.approx(80000.0)
        assert asset_usd["days_to_exit"] == pytest.approx(30.0)
        assert res_usd["max_days_to_exit"] == pytest.approx(30.0)

        # 2. JPY asset with explicit fx_rates
        req_jpy = api.LiquidityRequest(
            weights={"7203.T": 100},
            portfolio_value=240000,
            adv_participation=0.10,
            fx_rates={"JPY": 1.0 / 150.0},
        )
        res_jpy = api.compute_liquidity(req_jpy)
        asset_jpy = res_jpy["assets"][0]
        assert asset_jpy["adv"] == pytest.approx(80000.0)
        assert asset_jpy["days_to_exit"] == pytest.approx(30.0)
        assert res_jpy["max_days_to_exit"] == pytest.approx(30.0)

        # 3. JPY asset missing FX data reports null/unavailable safely
        req_missing = api.LiquidityRequest(weights={"7203.T": 100}, portfolio_value=240000, adv_participation=0.10)
        res_missing = api.compute_liquidity(req_missing)
        asset_missing = res_missing["assets"][0]
        assert asset_missing["adv"] is None
        assert asset_missing["days_to_exit"] is None
        assert res_missing["max_days_to_exit"] == 0.0
