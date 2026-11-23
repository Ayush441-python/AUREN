from types import SimpleNamespace
from unittest.mock import patch
import pandas as pd
import pytest
import api


@pytest.fixture
def business_dates():
    return pd.bdate_range("2025-01-06", periods=30)


def test_liquidity_usd_control(business_dates):
    ticker = "AAPL"
    px = pd.DataFrame({ticker: 1000 / 150}, index=business_dates)
    vol = pd.DataFrame({ticker: 12000}, index=business_dates)
    meta = dict(sector="Technology", industry="Consumer Electronics", currency="USD")
    yf = SimpleNamespace(Ticker=lambda _: SimpleNamespace(info=meta))

    with patch.dict("sys.modules", {"yfinance": yf}), \
         patch.object(api, "load_prices", return_value=px), \
         patch.object(api, "load_volumes", return_value=vol):
        request = api.LiquidityRequest(
            weights={ticker: 100},
            portfolio_value=240000,
            adv_participation=0.10,
        )
        result = api.compute_liquidity(request)

    row = result["assets"][0]
    assert row["adv"] == 80000.0
    assert row["days_to_exit"] == 30.0
    assert result["max_days_to_exit"] == 30.0


def test_liquidity_fx_conversion_jpy(business_dates):
    ticker = "7203.T"
    px = pd.DataFrame({ticker: 1000, "JPY=X": 150}, index=business_dates)
    vol = pd.DataFrame({ticker: 12000}, index=business_dates)
    meta = dict(sector="Consumer Cyclical", industry="Auto Manufacturers", currency="JPY")
    yf = SimpleNamespace(Ticker=lambda _: SimpleNamespace(info=meta))

    with patch.dict("sys.modules", {"yfinance": yf}), \
         patch.object(api, "load_prices", return_value=px), \
         patch.object(api, "load_volumes", return_value=vol):
        request = api.LiquidityRequest(
            weights={ticker: 100},
            portfolio_value=240000,
            adv_participation=0.10,
        )
        result = api.compute_liquidity(request)

    row = result["assets"][0]
    # 12,000,000 JPY / 150 = $80,000 USD ADV
    assert row["adv"] == 80000.0
    # $240,000 / (0.10 * 80,000) = 30 sessions
    assert row["days_to_exit"] == 30.0
    assert result["max_days_to_exit"] == 30.0


def test_liquidity_missing_fx_reports_unavailable(business_dates):
    ticker = "7203.T"
    px = pd.DataFrame({ticker: 1000}, index=business_dates)
    vol = pd.DataFrame({ticker: 12000}, index=business_dates)
    meta = dict(sector="Consumer Cyclical", industry="Auto Manufacturers", currency="JPY")
    yf = SimpleNamespace(Ticker=lambda _: SimpleNamespace(info=meta))

    with patch.dict("sys.modules", {"yfinance": yf}), \
         patch.object(api, "load_prices", return_value=px), \
         patch.object(api, "load_volumes", return_value=vol):
        request = api.LiquidityRequest(
            weights={ticker: 100},
            portfolio_value=240000,
            adv_participation=0.10,
        )
        result = api.compute_liquidity(request)

    row = result["assets"][0]
    assert row["adv"] is None
    assert row["days_to_exit"] is None
    assert result["max_days_to_exit"] == 0.0
